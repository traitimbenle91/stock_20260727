import sys
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
                             QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel)
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
            green_candle = 1 if row['Close'] >= row['Open'] else 0
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
        self.setGeometry(100, 100, 1400, 600)
        
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
        
        # Trạng thái sort cột Tổng Điểm: 0=mặc định, 1=giảm dần, 2=tăng dần
        self._sort_state = 0
        self._original_order = []  # Lưu thứ tự gốc để khôi phục

        # Tạo bảng
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            'Syb',
            'T-1: Nến Đỏ',
            'T-1: <EMA10',
            'T-1: Vol<VMA20',
            'T: Nến Xanh',
            'T: <EMA10',
            'T: Vol<VMA20',
            'Tổng Điểm',
            'Chart'
        ])

        # Set column widths
        self.table.setColumnWidth(0, 80)
        for i in range(1, 7):
            self.table.setColumnWidth(i, 110)
        self.table.setColumnWidth(7, 110)
        self.table.setColumnWidth(8, 90)

        # Set row height
        self.table.verticalHeader().setDefaultSectionSize(30)

        # Disable mặc định sort khi click header; tự xử lý toggle
        self.table.setSortingEnabled(False)
        self.table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

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

            # Chỉ quét mã cổ phiếu có đúng 3 ký tự, ví dụ CTG, VCB
            self.symbols = [syb for syb in df['syb'].astype(str).tolist() if len(syb) == 3]
        except Exception as e:
            logger.error(f"Error loading symbols: {e}")
            self.symbols = ['CTG', 'PFL', 'VCT']  # Default symbols
    
    def refresh_data(self):
        """Fetch/update dữ liệu cho tất cả cổ phiếu"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Đang tải...")
        
        # Reset trạng thái sort nhưng giữ lại dữ liệu bảng
        self._sort_state = 0
        self.table.horizontalHeader().setSortIndicatorShown(False)

        # Xác định mode: lần đầu dùng 'initial', sau đó dùng 'update'
        mode = 'initial' if self._is_first_load else 'update'
        self._is_first_load = False

        # Start fetch thread
        self.fetch_thread = DataFetcherThread(self.symbols, self.stock_data, mode=mode)
        self.fetch_thread.progress.connect(self.add_row)
        self.fetch_thread.finished.connect(self.on_fetch_finished)
        self.fetch_thread.start()
    
    def add_row(self, data):
        """Update hoặc thêm 1 dòng trong bảng"""
        symbol = data['symbol']
        
        # Tìm xem symbol đã có trong bảng không
        existing_row = -1
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text() == symbol:
                existing_row = row
                break
        
        # Nếu đã có dòng này, update; không thì insert mới
        if existing_row >= 0:
            row_pos = existing_row
        else:
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
        
        # Tạo items cho từng cột (bỏ cột VMA20)
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

        for col, item_text in enumerate(items):
            item = QTableWidgetItem(item_text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Highlight dòng có total_points cao
            if col == 7 and data['total_points'] >= 4:
                item.setBackground(QColor(200, 255, 200))  # Light green
                item.setFont(QFont(None, 10, QFont.Weight.Bold))

            self.table.setItem(row_pos, col, item)

        # Cột button Show để mở biểu đồ Plotly theo symbol của dòng
        show_btn = self.table.cellWidget(row_pos, 8)
        if show_btn is None:
            show_btn = QPushButton('Show')
            show_btn.clicked.connect(self._on_show_chart_clicked)
            self.table.setCellWidget(row_pos, 8, show_btn)
        show_btn.setProperty('symbol', symbol)
    
    def on_fetch_finished(self):
        """Hoàn tất fetch dữ liệu"""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Làm mới dữ liệu")
        logger.debug("Fetch data finished!")
        self._sort_state = 0
        
        # Rebuild _original_order từ thứ tự hiện tại trong bảng
        self._original_order = list(range(self.table.rowCount()))

    def _on_header_clicked(self, col):
        """Toggle sort 3 trạng thái trên cột Tổng Điểm (col 7):
        nhấn 1: giảm dần, nhấn 2: tăng dần, nhấn 3: về mặc định"""
        TOTAL_COL = 7
        if col != TOTAL_COL:
            return

        self._sort_state = (self._sort_state % 3) + 1

        if self._sort_state == 1:
            self.table.sortItems(TOTAL_COL, Qt.SortOrder.DescendingOrder)
        elif self._sort_state == 2:
            self.table.sortItems(TOTAL_COL, Qt.SortOrder.AscendingOrder)
        else:
            # Trả về thứ tự ban đầu (thứ tự thêm vào)
            self._sort_state = 0
            self.table.horizontalHeader().setSortIndicatorShown(False)
            rows = self.table.rowCount()
            # Đọc toàn bộ dữ liệu hiện tại
            all_rows = []
            for r in range(rows):
                row_data = [self.table.item(r, c).text() if self.table.item(r, c) else '' for c in range(self.table.columnCount())]
                all_rows.append(row_data)
            # Sắp xếp lại theo thứ tự syb gốc
            syb_order = {syb: i for i, syb in enumerate(self.symbols)}
            all_rows.sort(key=lambda r: syb_order.get(r[0], 9999))
            # Ghi lại vào bảng
            for r, row_data in enumerate(all_rows):
                for c, text in enumerate(row_data):
                    item = self.table.item(r, c)
                    if item:
                        item.setText(text)

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
