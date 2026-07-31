import pandas as pd
from PyQt6.QtCore import QThread, pyqtSignal
from utils.logger import get_logger

logger = get_logger(__name__)


class DataFetcherThread(QThread):
	"""Generic thread fetch/update dữ liệu stock để không block UI.

	Args:
		symbols:   danh sách mã cổ phiếu
		stock_data: đối tượng StockData
		score_fn:  hàm tính điểm (symbol, row_t_minus_1, row_t) -> dict
		mode:      'initial' | 'update'
		setup_fn:  hàm chuẩn bị df trước khi tính điểm (df) -> None (optional)
	"""

	progress = pyqtSignal(dict)
	finished = pyqtSignal()

	def __init__(self, symbols, stock_data, score_fn, mode="initial", setup_fn=None):
		super().__init__()
		self.symbols = symbols
		self.stock_data = stock_data
		self.score_fn = score_fn
		self.mode = mode
		self.setup_fn = setup_fn

	def run(self):
		for symbol in self.symbols:
			try:
				if self.mode == "initial":
					self.stock_data.get_data(symbol, resl="1D")
				else:
					self.stock_data.update_data(symbol, resl="1D")

				df = self.stock_data.allData[symbol]
				if df is not None and len(df) >= 2:
					if self.setup_fn is not None:
						self.setup_fn(df)
					row_t_minus_1 = df.iloc[-2]
					row_t = df.iloc[-1]
					result = self.score_fn(symbol, row_t_minus_1, row_t)
					self.progress.emit(result)
			except Exception as e:
				logger.error(f"Error fetching {symbol}: {e}")

		self.finished.emit()


class StockDataManager:
	def __init__(self):
		self.symbols = []

	def load_symbols(self, filepath="backup/syb_scan.csv", default=None, sybs=None):
		"""Load danh sách symbols, ưu tiên sybs truyền vào, nếu không thì đọc từ 1 file CSV."""
		if sybs is not None:
			self.symbols = list(dict.fromkeys([str(s).strip().upper() for s in sybs]))
			return self.symbols

		try:
			df = pd.read_csv(filepath)
			raw_symbols = df["syb"].astype(str).str.strip().str.upper().tolist()
			self.symbols = list(dict.fromkeys(raw_symbols))
		except Exception as e:
			logger.error(f"Error loading symbols from {filepath}: {e}")
			self.symbols = default if default is not None else ["CTG", "PFL", "VCT"]

		return self.symbols

	def create_fetch_thread(self, stock_data, score_fn, mode="initial", setup_fn=None, symbols=None):
		"""Tạo DataFetcherThread dùng chung từ manager."""
		thread_symbols = symbols if symbols is not None else self.symbols
		return DataFetcherThread(
			thread_symbols,
			stock_data,
			score_fn=score_fn,
			mode=mode,
			setup_fn=setup_fn,
		)