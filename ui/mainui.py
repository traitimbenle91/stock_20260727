import sys
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton

from indicator.indicators import add_ema, add_volume_ma
from ui.point.buy import BuyScannerWindow, calculate_scores
from ui.point.hold import HoldScannerWindow
from ui.point.sell import SellScannerWindow
from utils.logger import get_logger

logger = get_logger(__name__)


class DataFetcherThread(QThread):
    """Thread fetch/update dữ liệu stock để không block UI."""
    progress = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, symbols, stock_data, mode='initial'):
        super().__init__()
        self.symbols = symbols
        self.stock_data = stock_data
        self.mode = mode

    def run(self):
        for symbol in self.symbols:
            try:
                if self.mode == 'initial':
                    self.stock_data.get_data(symbol, resl='1D')
                else:
                    self.stock_data.update_data(symbol, resl='1D')

                df = self.stock_data.allData[symbol]
                if df is not None and len(df) >= 2:
                    add_ema(df, period=10, source_col='Close')
                    add_volume_ma(df, period=20, source_col='Volume')

                    row_t_minus_1 = df.iloc[-2]
                    row_t = df.iloc[-1]
                    result = calculate_scores(symbol, row_t_minus_1, row_t)
                    self.progress.emit(result)
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")

        self.finished.emit()

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
        action_layout.addWidget(self.refresh_btn)
        action_layout.addWidget(self.save_btn)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        self.buy_scanner_window = BuyScannerWindow()
        self.hold_scanner_window = HoldScannerWindow()
        self.sell_scanner_window = SellScannerWindow()
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        self.save_btn.clicked.connect(self.on_save_clicked)

        # Lấy nội dung scanner và gắn vào cửa sổ chính để hiển thị bảng
        self.buy_content = self.buy_scanner_window.takeCentralWidget()
        self.hold_content = self.hold_scanner_window.takeCentralWidget()
        self.sell_content = self.sell_scanner_window.takeCentralWidget()
        main_layout.addWidget(self.buy_content)
        main_layout.addWidget(self.hold_content)
        main_layout.addWidget(self.sell_content)

        # Initial load do mainui điều phối
        self.on_refresh_clicked()

    def on_refresh_clicked(self):
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Đang tải...")

        # Refresh Sell UI theo logic riêng trong sell.py
        self.hold_scanner_window.refresh_data()
        self.sell_scanner_window.refresh_data()

        # Giữ nguyên bảng hiện tại; mỗi symbol sẽ được update dần khi thread trả data.
        # Chỉ reset hoàn toàn ở lần tải đầu tiên.
        if self.buy_scanner_window._is_first_load:
            self.buy_scanner_window._sort_state = 0
            self.buy_scanner_window._symbol_results = {}
            self.buy_scanner_window._symbol_order = []
            self.buy_scanner_window.table.clearContents()
            self.buy_scanner_window.table.setColumnCount(0)

        mode = 'initial' if self.buy_scanner_window._is_first_load else 'update'
        self.buy_scanner_window._is_first_load = False

        self.fetch_thread = DataFetcherThread(
            self.buy_scanner_window.symbols,
            self.buy_scanner_window.stock_data,
            mode=mode,
        )
        self.fetch_thread.progress.connect(self.buy_scanner_window.add_row)
        self.fetch_thread.finished.connect(self._on_fetch_data_finished)
        self.fetch_thread.start()

    def _on_fetch_data_finished(self):
        self.buy_scanner_window.on_fetch_finished()
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
