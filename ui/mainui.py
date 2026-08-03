import sys
import importlib
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QCheckBox

from indicator.indicators import add_ema, add_volume_ma
from ststock.StockDataManager import StockDataManager
from .point.buy import BuyScannerWindow, calculate_scores
from .point.hold import HoldScannerWindow, calculate_hold_scores
from .point.sell import SellScannerWindow, calculate_sell_scores
from utils.logger import get_logger

result_window = importlib.import_module("ui.point.result")

logger = get_logger(__name__)


def _buy_setup_fn(df):
    """Chuẩn bị indicators cho bảng Buy trước khi tính điểm."""
    add_ema(df, period=10, source_col='Close')
    add_volume_ma(df, period=20, source_col='Volume')


class MainScannerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Table Scanner")
        self.setGeometry(100, 100, 1500, 650)
        
        # Tạo layout chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        action_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Làm mới dữ liệu")
        self.save_btn = QPushButton("Lưu tất cả")
        self.follow_b_checkbox = QCheckBox("Follow B")
        self.combine_bars_checkbox = QCheckBox("Combine bars")
        self.hide_hs_checkbox = QCheckBox("Hide H&S")
        self.follow_b_checkbox.setChecked(True)
        self.combine_bars_checkbox.setChecked(True)
        self.hide_hs_checkbox.setChecked(True)
        action_layout.addWidget(self.refresh_btn)
        action_layout.addWidget(self.save_btn)
        action_layout.addWidget(self.follow_b_checkbox)
        action_layout.addWidget(self.combine_bars_checkbox)
        action_layout.addWidget(self.hide_hs_checkbox)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        self.buy_scanner_window = BuyScannerWindow()
        self.hold_scanner_window = HoldScannerWindow()
        self.sell_scanner_window = SellScannerWindow()
        self.result_scanner_window = result_window.ResultScannerWindow()

        self.stock_data_manager = StockDataManager()

        # Load symbols 1 lần duy nhất từ 1 file CSV, gán cho cả 3 bảng
        self.stock_data_manager.load_symbols('backup/syb_scan.csv', default=['CTG', 'PFL', 'VCT'])
        self.buy_scanner_window.symbols = self.stock_data_manager.symbols
        self.hold_scanner_window.symbols = self.stock_data_manager.symbols
        self.sell_scanner_window.symbols = self.stock_data_manager.symbols
        self.result_scanner_window.symbols = self.stock_data_manager.symbols
        # self.buy_scanner_window.codes = self.stock_data_manager.symbols

        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        self.save_btn.clicked.connect(self.on_save_clicked)
        self.combine_bars_checkbox.toggled.connect(self._on_combine_bars_toggled)
        self.hide_hs_checkbox.toggled.connect(self._on_hide_hs_toggled)
        self.buy_scanner_window.sort_order_changed.connect(self._on_buy_sort_order_changed)
        self.buy_scanner_window.check_date_changed.connect(self._on_buy_check_date_changed)
        self.hold_scanner_window.check_date_changed.connect(self._on_hold_check_date_changed)
        self.sell_scanner_window.check_date_changed.connect(self._on_sell_check_date_changed)
        self.hold_scanner_window._get_next_b_date = self.buy_scanner_window.get_next_available_date
        self.hold_scanner_window._get_buy_check_date = lambda: self.buy_scanner_window.date_input.text().strip()
        self.sell_scanner_window._get_next_h_date = self.hold_scanner_window.get_next_available_date
        self.sell_scanner_window._get_hold_check_date = lambda: self.hold_scanner_window.date_input.text().strip()
        # Hold và Sell dùng chung stock_data với Buy — dữ liệu OHLCV tải 1 lần duy nhất
        # Phải gán TRƯỚC configure_sources để result_scanner lưu đúng tham chiếu
        self.hold_scanner_window.stock_data = self.buy_scanner_window.stock_data
        self.sell_scanner_window.stock_data = self.buy_scanner_window.stock_data

        self.result_scanner_window.configure_sources(
            symbols=self.stock_data_manager.symbols,
            buy_stock_data=self.buy_scanner_window.stock_data,
            sell_stock_data=self.sell_scanner_window.stock_data,
            get_buy_check_date=lambda: self.buy_scanner_window.date_input.text().strip(),
            get_sell_check_date=lambda: self.sell_scanner_window.date_input.text().strip(),
        )

        # Lấy nội dung scanner và gắn vào cửa sổ chính để hiển thị bảng
        self.buy_content = self.buy_scanner_window.takeCentralWidget()
        self.hold_content = self.hold_scanner_window.takeCentralWidget()
        self.sell_content = self.sell_scanner_window.takeCentralWidget()
        self.result_content = self.result_scanner_window.takeCentralWidget()
        main_layout.addWidget(self.buy_content)
        main_layout.addWidget(self.hold_content)
        main_layout.addWidget(self.sell_content)
        main_layout.addWidget(self.result_content)

        # Áp dụng trạng thái mặc định ẩn bảng H và S
        self.hold_content.setVisible(not self.hide_hs_checkbox.isChecked())
        self.sell_content.setVisible(not self.hide_hs_checkbox.isChecked())

        self._is_syncing_bars = False
        self._scrollbars = {
            "B": self.buy_scanner_window.table.horizontalScrollBar(),
            "H": self.hold_scanner_window.table.horizontalScrollBar(),
            "S": self.sell_scanner_window.table.horizontalScrollBar(),
            "R": self.result_scanner_window.table.horizontalScrollBar(),
        }
        for source_key, scrollbar in self._scrollbars.items():
            scrollbar.valueChanged.connect(
                lambda value, key=source_key: self._on_horizontal_bar_changed(key, value)
            )

        # Initial load do mainui điều phối
        self.on_refresh_clicked()

    def _on_hide_hs_toggled(self, checked):
        self.hold_content.setVisible(not checked)
        self.sell_content.setVisible(not checked)

    def _on_combine_bars_toggled(self, checked):
        if not checked:
            return

        buy_scrollbar = self._scrollbars.get("B")
        if buy_scrollbar is None:
            return

        self._sync_horizontal_bars("B", buy_scrollbar.value())

    def _map_scroll_value(self, source_value, source_scrollbar, target_scrollbar):
        source_max = source_scrollbar.maximum()
        target_max = target_scrollbar.maximum()

        if source_max <= 0 or target_max <= 0:
            return 0

        ratio = source_value / source_max
        mapped = int(round(ratio * target_max))
        return min(max(mapped, 0), target_max)

    def _sync_horizontal_bars(self, source_key, source_value):
        if not self.combine_bars_checkbox.isChecked() or self._is_syncing_bars:
            return

        source_scrollbar = self._scrollbars.get(source_key)
        if source_scrollbar is None:
            return

        self._is_syncing_bars = True
        try:
            for target_key, target_scrollbar in self._scrollbars.items():
                if target_key == source_key:
                    continue

                mapped_value = self._map_scroll_value(source_value, source_scrollbar, target_scrollbar)
                if target_scrollbar.value() != mapped_value:
                    target_scrollbar.setValue(mapped_value)
        finally:
            self._is_syncing_bars = False

    def _on_horizontal_bar_changed(self, source_key, value):
        self._sync_horizontal_bars(source_key, value)

    def on_refresh_clicked(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Đang tải...")

        self.hold_scanner_window.refresh_data()
        self.sell_scanner_window.refresh_data()

        if self.buy_scanner_window._is_first_load:
            self.buy_scanner_window._sort_state = 0
            self.buy_scanner_window._symbol_results = {}
            self.buy_scanner_window._symbol_order = []
            self.buy_scanner_window.table.clearContents()
            self.buy_scanner_window.table.setColumnCount(0)

        mode = 'initial' if self.buy_scanner_window._is_first_load else 'update'
        self.buy_scanner_window._is_first_load = False

        self.fetch_thread = self.stock_data_manager.create_fetch_thread(
            self.buy_scanner_window.stock_data,
            score_configs=[
                ('B', calculate_scores),
                ('H', calculate_hold_scores),
                ('S', calculate_sell_scores),
            ],
            mode=mode,
            setup_fn=_buy_setup_fn,
            symbols=self.buy_scanner_window.symbols,
        )
        self.hold_scanner_window.fetch_thread = self.fetch_thread
        self.sell_scanner_window.fetch_thread = self.fetch_thread
        self.fetch_thread.progress.connect(self._on_fetch_progress)
        self.fetch_thread.finished.connect(self._on_fetch_data_finished)
        self.fetch_thread.start()

    def _on_fetch_progress(self, tag, data):
        if tag == 'B':
            self.buy_scanner_window.add_row(data)
        elif tag == 'H':
            self.hold_scanner_window.add_row(data)
        elif tag == 'S':
            self.sell_scanner_window.add_row(data)

    def _on_buy_sort_order_changed(self, ordered_symbols):
        """Khi bảng B sort theo Tổng Điểm, nếu Follow B được bật thì H và S cũng theo."""
        if self.follow_b_checkbox.isChecked():
            self.hold_scanner_window.apply_external_order(ordered_symbols)
            self.sell_scanner_window.apply_external_order(ordered_symbols)
            self.result_scanner_window.apply_external_order(ordered_symbols)

    def _on_buy_check_date_changed(self, date_text):
        """Khi ngày check của B đổi, cập nhật ngày kế tiếp cho H nếu đang bật Auto Next B."""
        if self.hold_scanner_window.auto_next_b_checkbox.isChecked() and self.hold_scanner_window.sync_to_next_buy_date(date_text):
            self.hold_scanner_window.on_check_date(skip_auto_sync=True)
        self.result_scanner_window.refresh_results()

    def _on_hold_check_date_changed(self, date_text):
        """Khi ngày check của H đổi, cập nhật ngày kế tiếp cho S nếu đang bật Auto Next H."""
        if self.sell_scanner_window.auto_next_h_checkbox.isChecked() and self.sell_scanner_window.sync_to_next_hold_date(date_text):
            self.sell_scanner_window.on_check_date(skip_auto_sync=True)

    def _on_sell_check_date_changed(self, _date_text):
        """Khi ngày check của S đổi, cập nhật bảng R."""
        self.result_scanner_window.refresh_results()

    def _on_fetch_data_finished(self):
        self.buy_scanner_window.on_fetch_finished()
        self.hold_scanner_window.on_fetch_finished()
        self.sell_scanner_window.on_fetch_finished()
        self.result_scanner_window.refresh_results()
        self.on_refresh_finished()

    def on_refresh_finished(self):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Làm mới dữ liệu")

    def on_save_clicked(self):
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Đang lưu...")
        try:
            saved_count = self.save_all_data()
            self.save_btn.setText(f"✓ Lưu {saved_count} file")
        except Exception:
            self.save_btn.setText("Lỗi lưu dữ liệu")
        finally:
            self.save_btn.setEnabled(True)
            QTimer.singleShot(2000, lambda: self.save_btn.setText("Lưu tất cả"))

    def save_all_data(self):
        """Lưu tất cả dữ liệu symbol vào CSV files."""
        saved_count = 0
        try:
            for symbol, df in self.buy_scanner_window.stock_data.allData.items():
                if df is not None and not df.empty:
                    csv_path = f'.//backup//1D//{symbol}.csv'
                    df.to_csv(csv_path, index=True, encoding='utf-8')
                    saved_count += 1
                    logger.debug(f"Saved {symbol} to {csv_path}")

            logger.info(f"Lưu thành công {saved_count} file CSV!")
            return saved_count
        except Exception as e:
            logger.error(f"Lỗi khi lưu dữ liệu: {e}")
            raise



def main():
    app = QApplication(sys.argv)
    window = MainScannerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
