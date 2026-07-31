import pandas as pd
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QLabel,
    QHeaderView,
    QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from ststock.StockData import StockData
from indicator.indicators import add_ema, add_volume_ma
from utils.logger import get_logger
from config import CODE_COLORS

logger = get_logger(__name__)

def calculate_scores(symbol, row_t_minus_1, row_t):
    """Tính điểm cho 2 nến T-1 và T."""
    def get_score_t_minus_1(row):
        red_candle = 1 if row['Close'] < row['Open'] else 0
        price_below_ema = 1 if row['Close'] < row['EMA10'] else 0
        vol_below_vma = 1 if row['Volume'] < row['VMA20'] else 0
        return red_candle, price_below_ema, vol_below_vma

    def get_score_t(row):
        green_candle = 1 if row['Close'] > row['Open'] else 0
        price_below_ema = 1 if row['Close'] < row['EMA10'] else 0
        vol_below_vma = 1 if row['Volume'] < row['VMA20'] else 0.5
        return green_candle, price_below_ema, vol_below_vma

    t_minus_1_bullish, t_minus_1_ema, t_minus_1_vol = get_score_t_minus_1(row_t_minus_1)
    t_bullish, t_ema, t_vol = get_score_t(row_t)

    total_points = t_minus_1_bullish + t_minus_1_ema + t_minus_1_vol + \
                   t_bullish + t_ema + t_vol

    prev_close = float(row_t_minus_1['Close'])
    curr_close = float(row_t['Close'])
    pct_change = 0.0 if prev_close == 0 else ((curr_close - prev_close) / prev_close) * 100

    prev_vol = float(row_t_minus_1['Volume'])
    curr_vol = float(row_t['Volume'])
    vol_vs_t_minus_1 = 0.0 if prev_vol == 0 else ((curr_vol - prev_vol) / prev_vol) * 100

    open_price = float(row_t['Open'])
    close_price = float(row_t['Close'])
    low_price = float(row_t['Low'])
    high_price = float(row_t['High'])

    price_o_vs_c = 0.0 if open_price == 0 else ((close_price - open_price) / open_price) * 100
    price_h_vs_l = 0.0 if low_price == 0 else ((high_price - low_price) / low_price) * 100

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
        'total_points': total_points,
        'pct_change': pct_change,
        'vol_vs_t_minus_1': vol_vs_t_minus_1,
        'price_o_vs_c': price_o_vs_c,
        'price_h_vs_l': price_h_vs_l
    }
class BuyScannerWindow(QMainWindow):
    fetch_completed = pyqtSignal()
    sort_order_changed = pyqtSignal(list)  # Emits ordered symbol list after sort
    check_date_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        
        # Tạo layout chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Group box bao toàn bộ UI buy
        group_box = QGroupBox("B")
        group_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        group_layout = QVBoxLayout(group_box)
        group_layout.setContentsMargins(6, 6, 6, 6)
        group_layout.setSpacing(6)
        
        # Title
        # title = QLabel("Table")
        # title_font = QFont()
        # title_font.setPointSize(14)
        # title_font.setBold(True)
        # title.setFont(title_font)
        # main_layout.addWidget(title)
        
        # Khởi tạo StockData
        self.stock_data = StockData()
        self._is_first_load = True  # Flag để track lần đầu load
        self._sort_state = 0  # 0=mặc định, 1=giảm dần, 2=tăng dần
        self._symbol_results = {}
        self._symbol_order = []
        self.codes = {}

        self.metric_labels = [
            'Syb',
            'T-1: Nến Đỏ',
            'T-1: <EMA10',
            'T-1: Vol<VMA20',
            'T: Nến Xanh',
            'T: <EMA10',
            'T: Vol<VMA20',
            'Tổng Điểm',
            'Vol: T_vs_T-1',
            'Price: H_vs_L',
            'Price: C_vs_O',
            'Price: T_vs_T-1',
            'Chart'
        ]

        # Tạo bảng
        self.table = QTableWidget()
        self.table.setRowCount(len(self.metric_labels))
        self.table.setColumnCount(0)
        self.table.setVerticalHeaderLabels(self.metric_labels)
        self.table.setFont(QFont('Segoe UI', 9))
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

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

        # Fit chiều cao bảng đúng theo số hàng để tránh khoảng trống trong GroupBox.
        self._fit_table_height()

        # Top controls layout (cùng 1 hàng)
        top_layout = QHBoxLayout()
        date_label = QLabel("Ngày check:")
        self.prev_date_btn = QPushButton("<")
        self.prev_date_btn.setMaximumWidth(36)
        self.prev_date_btn.clicked.connect(self.on_prev_date)

        self.date_input = QLineEdit()
        self.date_input.setText("")
        self.date_input.setPlaceholderText("dd/mm/yyyy")
        self.date_input.setMaximumWidth(120)

        self.next_date_btn = QPushButton(">")
        self.next_date_btn.setMaximumWidth(36)
        self.next_date_btn.clicked.connect(self.on_next_date)
        
        self.check_date_btn = QPushButton("Check")
        self.check_date_btn.setMaximumWidth(80)
        self.check_date_btn.clicked.connect(self.on_check_date)

        self.score_ratio_view = QLineEdit()
        self.score_ratio_view.setReadOnly(True)
        self.score_ratio_view.setMaximumWidth(220)
        self.score_ratio_view.setText(">=5: 0/0 (0.00%)")
        
        top_layout.addWidget(date_label)
        top_layout.addWidget(self.prev_date_btn)
        top_layout.addWidget(self.date_input)
        top_layout.addWidget(self.next_date_btn)
        top_layout.addWidget(self.check_date_btn)
        top_layout.addWidget(self.score_ratio_view)
        top_layout.addStretch()

        group_layout.addLayout(top_layout)
        group_layout.addWidget(self.table)
        main_layout.addWidget(group_box)
        main_layout.addStretch()
        
        # symbols sẽ được gán từ mainui.py
        self.symbols = []

    def _fit_table_height(self):
        """Đặt chiều cao bảng vừa đủ hiển thị toàn bộ hàng hiện có."""
        rows_height = self.table.verticalHeader().length()
        header_height = self.table.horizontalHeader().height() if self.table.horizontalHeader() else 0
        frame = self.table.frameWidth() * 2
        self.table.setFixedHeight(rows_height + header_height + frame + 2)
    
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
        self._update_score_ratio_view()

    def _update_score_ratio_view(self):
        """Hiển thị tỷ lệ số mã có Tổng Điểm >= 5 so với tổng số mã."""
        total_symbols = len(self._symbol_results)
        if total_symbols == 0:
            self.score_ratio_view.setText("0/0 (0.00%)")
            return

        passing_symbols = sum(
            1
            for result in self._symbol_results.values()
            if float(result.get('total_points', 0)) >= 5
        )
        ratio = (passing_symbols / total_symbols) * 100
        self.score_ratio_view.setText(f"{passing_symbols}/{total_symbols} ({ratio:.2f}%)")

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
            str(data['total_points']),
            f"{float(data.get('vol_vs_t_minus_1', 0.0)):.2f}%",
            f"{float(data.get('price_h_vs_l', 0.0)):.2f}%",
            f"{float(data.get('price_o_vs_c', 0.0)):.2f}%",
            f"{float(data.get('pct_change', 0.0)):.2f}%"
        ]

        for row, item_text in enumerate(items):
            item = QTableWidgetItem(item_text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if row == 0:
                code = self.codes.get(symbol, 0)
                rgb = CODE_COLORS[code] if 0 <= code < len(CODE_COLORS) else CODE_COLORS[1 + (code % (len(CODE_COLORS) - 1))]
                if rgb is not None:
                    item.setBackground(QColor(*rgb))

            # Highlight ô tổng điểm cao
            if row == 7 and data['total_points'] >= 5:
                item.setBackground(QColor(200, 255, 200))  # Light green
                item.setFont(QFont(None, 10, QFont.Weight.Bold))

            self.table.setItem(row, col_pos, item)

        # Hàng button Show để mở biểu đồ Plotly theo symbol của cột
        chart_row = self.metric_labels.index('Chart')
        show_btn = self.table.cellWidget(chart_row, col_pos)
        if show_btn is None:
            show_btn = QPushButton('Show')
            show_btn.setFixedWidth(48)
            show_btn.clicked.connect(self._on_show_chart_clicked)
            self.table.setCellWidget(chart_row, col_pos, show_btn)
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
            self._update_score_ratio_view()
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

        self._update_score_ratio_view()

        self.sort_order_changed.emit(ordered_symbols)

    def on_fetch_finished(self):
        """Hoàn tất fetch dữ liệu"""
        self._set_check_date_to_latest_available()
        self.fetch_completed.emit()
        logger.debug("Fetch data finished!")

    def _set_check_date_to_latest_available(self):
        """Đặt ô ngày check theo ngày mới nhất đang có trong dữ liệu."""
        latest_date = None

        for df in self.stock_data.allData.values():
            if df is None or df.empty or 'Date' not in df.columns:
                continue

            date_series = pd.to_datetime(df['Date'], errors='coerce').dropna()
            if date_series.empty:
                continue

            symbol_latest = date_series.max()
            if latest_date is None or symbol_latest > latest_date:
                latest_date = symbol_latest

        if latest_date is not None:
            formatted_date = latest_date.strftime("%d/%m/%Y")
            self.date_input.setText(formatted_date)
            self.check_date_changed.emit(formatted_date)

    def get_next_available_date(self, base_date):
        """Lấy ngày giao dịch kế tiếp trong dữ liệu Buy sau một ngày gốc."""
        if base_date is None:
            return None

        target_date = pd.Timestamp(base_date).normalize()
        next_date = None

        for df in self.stock_data.allData.values():
            if df is None or df.empty or 'Date' not in df.columns:
                continue

            date_series = pd.to_datetime(df['Date'], errors='coerce').dropna().dt.normalize()
            future_dates = date_series[date_series > target_date]
            if future_dates.empty:
                continue

            symbol_next = future_dates.min()
            if next_date is None or symbol_next < next_date:
                next_date = symbol_next

        return next_date

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

    def on_check_date(self):
        """Xử lý khi bấm button Check ngày"""
        date_text = self.date_input.text().strip()
        if not date_text:
            logger.warning("Vui lòng nhập ngày")
            return
        
        try:
            # Validate định dạng ngày dd/mm/yyyy
            check_date = datetime.strptime(date_text, "%d/%m/%Y")
            if hasattr(self, 'fetch_thread') and self.fetch_thread.isRunning():
                logger.warning("Đang tải dữ liệu. Vui lòng chờ tải xong rồi Check ngày.")
                return

            target_date = pd.Timestamp(check_date.date())
            date_results = {}
            date_order = []

            for symbol in self.symbols:
                df = self.stock_data.allData.get(symbol)
                if df is None or len(df) < 2:
                    continue

                add_ema(df, period=10, source_col="Close")
                add_volume_ma(df, period=20, source_col="Volume")

                date_series = pd.to_datetime(df['Date'], errors='coerce').dt.normalize()
                matched_rows = df.index[date_series == target_date]
                if len(matched_rows) == 0:
                    continue

                idx_t = matched_rows[-1]
                if idx_t <= 0:
                    continue

                row_t_minus_1 = df.iloc[idx_t - 1]
                row_t = df.iloc[idx_t]
                result = calculate_scores(symbol, row_t_minus_1, row_t)

                date_results[symbol] = result
                date_order.append(symbol)

            self._sort_state = 0
            self._symbol_results = date_results
            self._symbol_order = date_order

            self.table.clearContents()
            self.table.setColumnCount(0)
            self.table.setHorizontalHeaderLabels([])

            for symbol in self._symbol_order:
                self._upsert_symbol_column(symbol, self._symbol_results[symbol])

            self._update_score_ratio_view()

            normalized_date_text = target_date.strftime("%d/%m/%Y")
            self.date_input.setText(normalized_date_text)
            self.check_date_changed.emit(normalized_date_text)

            if self._symbol_order:
                logger.info(
                    f"Đã cập nhật bảng theo ngày {check_date.strftime('%d/%m/%Y')} ({len(self._symbol_order)} mã)"
                )
            else:
                logger.warning(
                    f"Không có dữ liệu cho ngày {check_date.strftime('%d/%m/%Y')}."
                )
        except ValueError:
            logger.error(f"Định dạng ngày không hợp lệ. Vui lòng nhập theo dd/mm/yyyy")

    def _shift_check_date(self, days):
        """Lùi/tiến ngày check và tự động cập nhật bảng."""
        date_text = self.date_input.text().strip()
        if not date_text:
            logger.warning("Vui lòng nhập ngày")
            return

        try:
            base_date = datetime.strptime(date_text, "%d/%m/%Y")
            new_date = base_date + pd.Timedelta(days=days)
            self.date_input.setText(new_date.strftime("%d/%m/%Y"))
            self.on_check_date()
        except ValueError:
            logger.error("Định dạng ngày không hợp lệ. Vui lòng nhập theo dd/mm/yyyy")

    def on_prev_date(self):
        """Lùi về 1 ngày."""
        self._shift_check_date(-1)

    def on_next_date(self):
        """Tiến thêm 1 ngày."""
        self._shift_check_date(1)
