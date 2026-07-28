import sys
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
                             QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QHeaderView)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont

from ststock.StockData import StockData
from indicator.indicators import add_ema, add_volume_ma
from utils.logger import get_logger

logger = get_logger(__name__)


class DataFetcherThread(QThread):
    """Thread để fetch/update dữ liệu stock mà không block UI"""
    progress = pyqtSignal(dict)  # Emit khi fetch xong 1 symbol
    finished = pyqtSignal()      # Emit khi xong hết
    
    def __init__(self, symbols, stock_data, mode='initial'):
        super().__init__()
        self.symbols = symbols
        self.stock_data = stock_data
        self.mode = mode  # 'initial' hoặc 'update'
    
    def run(self):
        for symbol in self.symbols:
            try:
                if self.mode == 'initial':
                    self.stock_data.get_data(symbol, resl='1D')
                else:  # mode == 'update'
                    self.stock_data.update_data(symbol, resl='1D')
                
                df = self.stock_data.allData[symbol]
                if df is not None and len(df) >= 2:
                    # Calculate indicators
                    add_ema(df, period=10, source_col="Close")
                    add_volume_ma(df, period=20, source_col="Volume")
                    
                    # Get last 2 rows (T-1 and T)
                    row_t_minus_1 = df.iloc[-2]
                    row_t = df.iloc[-1]
                    
                    # Calculate scores
                    result = self._calculate_scores(symbol, row_t_minus_1, row_t)
                    self.progress.emit(result)
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                
        self.finished.emit()
    
    def _calculate_scores(self, symbol, row_t_minus_1, row_t):
        """
        Tính điểm cho từng điều kiện:
        - nến xanh (bullish): Close >= Open = 1, else 0
        - <EMA10: Close < EMA10 = 1, else 0  
        - vol<VMA20: Volume < VMA20 = 1, else 0
        """
        def get_score_t_minus_1(row):
            # T-1: nến đỏ (Close < Open) = +1
            red_candle = 1 if row['Close'] < row['Open'] else 0
            price_below_ema = 1 if row['Close'] < row['EMA10'] else 0
            vol_below_vma = 1 if row['Volume'] < row['VMA20'] else 0
            return red_candle, price_below_ema, vol_below_vma

        def get_score_t(row):
            # T: nến xanh (Close >= Open) = +1
            green_candle = 1 if row['Close'] > row['Open'] else 0
            price_below_ema = 1 if row['Close'] < row['EMA10'] else 0
            vol_below_vma = 1 if row['Volume'] < row['VMA20'] else 0.5
            return green_candle, price_below_ema, vol_below_vma

        t_minus_1_bullish, t_minus_1_ema, t_minus_1_vol = get_score_t_minus_1(row_t_minus_1)
        t_bullish, t_ema, t_vol = get_score_t(row_t)
        
        total_points = t_minus_1_bullish + t_minus_1_ema + t_minus_1_vol + \
                       t_bullish + t_ema + t_vol
        
        vol_ma20 = int(row_t['VMA20'])
        
        return {
            'symbol': symbol,
            'T_minus_1_bullish': t_minus_1_bullish,
            'T_minus_1_ema': t_minus_1_ema,
            'T_minus_1_vol': t_minus_1_vol,
            'T_bullish': t_bullish,
            'T_ema': t_ema,
            'T_vol': t_vol,
            'vol_ma20': vol_ma20,
            'total_points': total_points
        }


class StockScannerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Table Scanner")
        self.setGeometry(100, 100, 1500, 650)
        
        # Tạo layout chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Table")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Khởi tạo StockData
        self.stock_data = StockData()
        self._is_first_load = True  # Flag để track lần đầu load
        self._sort_state = 0  # 0=mặc định, 1=giảm dần, 2=tăng dần
        self._symbol_results = {}
        self._symbol_order = []

        self.metric_labels = [
            'Syb',
            'T-1: Nến Đỏ',
            'T-1: <EMA10',
            'T-1: Vol<VMA20',
            'T: Nến Xanh',
            'T: <EMA10',
            'T: Vol<VMA20',
            'Tổng Điểm',
            'Chart'
        ]

        # Tạo bảng
        self.table = QTableWidget()
        self.table.setRowCount(len(self.metric_labels))
        self.table.setColumnCount(0)
        self.table.setVerticalHeaderLabels(self.metric_labels)
        self.table.setFont(QFont('Segoe UI', 9))

        # Khi transpose bảng: hàng là tiêu chí, cột là mã cổ phiếu
        vertical_header = self.table.verticalHeader()
        horizontal_header = self.table.horizontalHeader()
        if vertical_header is not None:
            vertical_header.setDefaultSectionSize(30)
            vertical_header.setMinimumWidth(130)
            vertical_header.setMaximumWidth(160)
            vertical_header.sectionClicked.connect(self._on_vertical_header_clicked)
        if horizontal_header is not None:
            horizontal_header.setVisible(False)
            horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            horizontal_header.setMinimumSectionSize(56)
            horizontal_header.setDefaultSectionSize(56)

        main_layout.addWidget(self.table)
        
        # Button layout
        button_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Làm mới dữ liệu")
        self.refresh_btn.clicked.connect(self.refresh_data)
        button_layout.addWidget(self.refresh_btn)
        
        self.save_btn = QPushButton("Lưu tất cả")
        self.save_btn.clicked.connect(self.save_all_data)
        button_layout.addWidget(self.save_btn)
        
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # Load data
        self.load_symbols()
        self.refresh_data()
    
    def load_symbols(self):
        """Đọc danh sách cổ phiếu từ backup/syb_scan.csv - chỉ lấy mã 3 ký tự"""
        try:
            df = pd.read_csv('backup/syb_scan.csv')

            # Chuẩn hóa + loại trùng để tránh hiển thị lặp cột
            raw_symbols = df['syb'].astype(str).str.strip().str.upper().tolist()
            self.symbols = list(dict.fromkeys([syb for syb in raw_symbols if len(syb) == 3]))
        except Exception as e:
            logger.error(f"Error loading symbols: {e}")
            self.symbols = ['CTG', 'PFL', 'VCT']  # Default symbols
    
    def refresh_data(self):
        """Fetch/update dữ liệu cho tất cả cổ phiếu"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Đang tải...")
        self._sort_state = 0
        self._symbol_results = {}
        self._symbol_order = []

        # Xóa bảng theo layout transpose trước mỗi lần tải
        self.table.clearContents()
        self.table.setColumnCount(0)
        self.table.setHorizontalHeaderLabels([])

        # Xác định mode: lần đầu dùng 'initial', sau đó dùng 'update'
        mode = 'initial' if self._is_first_load else 'update'
        self._is_first_load = False

        # Start fetch thread
        self.fetch_thread = DataFetcherThread(self.symbols, self.stock_data, mode=mode)
        self.fetch_thread.progress.connect(self.add_row)
        self.fetch_thread.finished.connect(self.on_fetch_finished)
        self.fetch_thread.start()
    
    def add_row(self, data):
        """Update hoặc thêm 1 cột (mỗi cột là 1 symbol) trong bảng transpose"""
        symbol = data['symbol']

        # Lưu dữ liệu mới nhất để phục vụ sort/rebuild theo cột
        self._symbol_results[symbol] = data
        if symbol not in self._symbol_order:
            self._symbol_order.append(symbol)

        if self._sort_state != 0:
            self._apply_sort_order()
            return

        self._upsert_symbol_column(symbol, data)

    def _upsert_symbol_column(self, symbol, data):
        """Thêm/cập nhật một cột symbol vào bảng hiện tại"""
        # Tìm xem symbol đã có trong cột nào chưa (row 0 là Syb)
        existing_col = -1
        for col in range(self.table.columnCount()):
            item = self.table.item(0, col)
            if item and item.text() == symbol:
                existing_col = col
                break

        # Nếu đã có cột này thì update, không thì thêm cột mới
        if existing_col >= 0:
            col_pos = existing_col
        else:
            col_pos = self.table.columnCount()
            self.table.insertColumn(col_pos)
            self.table.setHorizontalHeaderItem(col_pos, QTableWidgetItem(symbol))
            self.table.setColumnWidth(col_pos, 56)

        # Dữ liệu theo từng hàng tiêu chí
        items = [
            data['symbol'],
            str(data['T_minus_1_bullish']),
            str(data['T_minus_1_ema']),
            str(data['T_minus_1_vol']),
            str(data['T_bullish']),
            str(data['T_ema']),
            str(data['T_vol']),
            str(data['total_points'])
        ]

        for row, item_text in enumerate(items):
            item = QTableWidgetItem(item_text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Highlight ô tổng điểm cao
            if row == 7 and data['total_points'] >= 4:
                item.setBackground(QColor(200, 255, 200))  # Light green
                item.setFont(QFont(None, 10, QFont.Weight.Bold))

            self.table.setItem(row, col_pos, item)

        # Hàng button Show để mở biểu đồ Plotly theo symbol của cột
        show_btn = self.table.cellWidget(8, col_pos)
        if show_btn is None:
            show_btn = QPushButton('Show')
            show_btn.setFixedWidth(48)
            show_btn.clicked.connect(self._on_show_chart_clicked)
            self.table.setCellWidget(8, col_pos, show_btn)
        show_btn.setProperty('symbol', symbol)

    def _on_vertical_header_clicked(self, row):
        """Click vào hàng Tổng Điểm để toggle sort theo cột symbol"""
        TOTAL_ROW = 7
        if row != TOTAL_ROW:
            return

        self._sort_state = (self._sort_state + 1) % 3
        self._apply_sort_order()

    def _apply_sort_order(self):
        """Sắp xếp lại các cột symbol theo điểm tổng"""
        if not self._symbol_order:
            return

        base_index = {syb: idx for idx, syb in enumerate(self._symbol_order)}

        if self._sort_state == 0:
            ordered_symbols = list(self._symbol_order)
        elif self._sort_state == 1:
            ordered_symbols = sorted(
                self._symbol_order,
                key=lambda syb: (-float(self._symbol_results.get(syb, {}).get('total_points', 0)), base_index[syb])
            )
        else:
            ordered_symbols = sorted(
                self._symbol_order,
                key=lambda syb: (float(self._symbol_results.get(syb, {}).get('total_points', 0)), base_index[syb])
            )

        self.table.clearContents()
        self.table.setColumnCount(0)
        for symbol in ordered_symbols:
            symbol_data = self._symbol_results.get(symbol)
            if symbol_data is not None:
                self._upsert_symbol_column(symbol, symbol_data)
    
    def on_fetch_finished(self):
        """Hoàn tất fetch dữ liệu"""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Làm mới dữ liệu")
        logger.debug("Fetch data finished!")

    def save_all_data(self):
        """Lưu tất cả dữ liệu symbol vào CSV files"""
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Đang lưu...")
        
        saved_count = 0
        try:
            for symbol, df in self.stock_data.allData.items():
                if df is not None and not df.empty:
                    csv_path = f'.//backup//1D//{symbol}.csv'
                    df.to_csv(csv_path, index=True, encoding='utf-8')
                    saved_count += 1
                    logger.debug(f"Saved {symbol} to {csv_path}")
            
            logger.info(f"Lưu thành công {saved_count} file CSV!")
            self.save_btn.setText(f"✓ Lưu {saved_count} file")
        except Exception as e:
            logger.error(f"Lỗi khi lưu dữ liệu: {e}")
            self.save_btn.setText("Lỗi lưu dữ liệu")
        finally:
            self.save_btn.setEnabled(True)
            # Reset text sau 2 giây
            QTimer.singleShot(2000, lambda: self.save_btn.setText("Lưu tất cả"))

    def _on_show_chart_clicked(self):
        """Mở biểu đồ Plotly cho symbol của dòng được bấm Show"""
        button = self.sender()
        if button is None:
            return

        symbol = button.property('symbol')
        if not symbol:
            return

        df = self.stock_data.allData.get(symbol)
        if df is None or df.empty:
            logger.error(f"Không có dữ liệu để vẽ chart cho {symbol}")
            return

        try:
            from uiplotly.plotly_chart import show_stock_plotly_chart
            show_stock_plotly_chart(symbol, df)
        except ModuleNotFoundError:
            logger.error("Thiếu thư viện plotly. Hãy cài bằng lệnh: py -m pip install plotly")
        except Exception as e:
            logger.error(f"Lỗi khi mở chart Plotly cho {symbol}: {e}")


def main():
    app = QApplication(sys.argv)
    window = StockScannerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
