import pandas as pd
from PyQt6.QtCore import QThread, pyqtSignal
from utils.logger import get_logger

logger = get_logger(__name__)


class DataFetcherThread(QThread):
	"""Generic thread fetch/update dữ liệu stock để không block UI.

	Args:
		symbols:      danh sách mã cổ phiếu
		stock_data:   đối tượng StockData dùng chung
		score_configs: list[(tag: str, score_fn)] – mỗi phần tử là 1 bộ (nhãn, hàm điểm)
		mode:         'initial' | 'update'
		setup_fn:     hàm chuẩn bị df trước khi tính điểm (df) -> None (optional)
	"""

	progress = pyqtSignal(str, dict)  # (tag, result)
	finished = pyqtSignal()

	def __init__(self, symbols, stock_data, score_configs, mode="initial", setup_fn=None):
		super().__init__()
		self.symbols = symbols
		self.stock_data = stock_data
		self.score_configs = score_configs  # [(tag, score_fn), ...]
		self.mode = mode
		self.setup_fn = setup_fn

	def run(self):
		"""Duyệt từng (code, syb) theo thứ tự dict.

		Fetch OHLCV mỗi syb 1 lần, emit cho mọi (code, syb) pair.
		"""
		ordered_pairs = [
			(code, syb)
			for code, sybs in self.symbols.items()
			for syb in sybs
		]

		# Fetch OHLCV chỉ 1 lần per unique symbol
		fetched: set = set()
		for code, symbol in ordered_pairs:
			try:
				if symbol not in fetched:
					if self.mode == "initial":
						self.stock_data.get_data(symbol, resl="1D")
					else:
						self.stock_data.update_data(symbol, resl="1D")
					fetched.add(symbol)

				df = self.stock_data.allData.get(symbol)
				if df is not None and len(df) >= 2:
					if self.setup_fn is not None:
						self.setup_fn(df)
					row_t_minus_1 = df.iloc[-2]
					row_t = df.iloc[-1]
					for tag, score_fn in self.score_configs:
						result = score_fn(symbol, row_t_minus_1, row_t)
						result["code"] = code  # inject code vào result để bảng biết nhóm
						self.progress.emit(tag, result)
			except Exception as e:
				logger.error(f"Error fetching {symbol} (code={code}): {e}")

		self.finished.emit()


class StockDataManager:
	def __init__(self):
		# symbols: dict[int, list[str]]  →  {code: [syb1, syb2, ...]}
		self.symbols: dict = {}

	def load_symbols(self, filepath="backup/syb_scan.csv", default=None, sybs=None):
		"""Load danh sách symbols từ CSV, trả về dict {code: [sybs]}.
		
		Mỗi mã có thể thuộc nhiều nhóm code khác nhau.
		"""
		if sybs is not None:
			return

		try:
			df = pd.read_csv(filepath)
			df["syb"] = df["syb"].astype(str).str.strip().str.upper()
			if "code" in df.columns:
				df["code"] = df["code"].astype(int)
				grouped: dict = {}
				for _, row in df.iterrows():
					code = int(row["code"])
					grouped.setdefault(code, []).append(row["syb"])
				self.symbols = grouped
			else:
				# Fallback: code=0 cho tất cả
				self.symbols = {0: df["syb"].tolist()}
		except Exception as e:
			logger.error(f"Error loading symbols from {filepath}: {e}")
			self.symbols = {0: (default if default is not None else ["CTG", "PFL", "VCT"])}

	def create_fetch_thread(self, stock_data, score_configs, mode="initial", setup_fn=None, symbols=None):
		"""Tạo DataFetcherThread dùng chung từ manager.

		Args:
			score_configs: list[(tag: str, score_fn)] – fetch dữ liệu 1 lần, tính điểm cho nhiều bảng.
		"""
		thread_symbols = symbols if symbols is not None else self.symbols
		return DataFetcherThread(
			thread_symbols,
			stock_data,
			score_configs=score_configs,
			mode=mode,
			setup_fn=setup_fn,
		)