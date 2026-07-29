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
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from ststock.StockData import StockData
from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_sell_scores(symbol, row_t_minus_1, row_t):
	"""Tính % biến động Vol/Price và điểm cho điều kiện Sell."""
	prev_close = float(row_t_minus_1["Close"])
	curr_close = float(row_t["Close"])
	prev_vol = float(row_t_minus_1["Volume"])
	curr_vol = float(row_t["Volume"])

	price_vs_t_minus_1 = 0.0 if prev_close == 0 else ((curr_close - prev_close) / prev_close) * 100
	vol_vs_t_minus_1 = 0.0 if prev_vol == 0 else ((curr_vol - prev_vol) / prev_vol) * 100

	price_point = 0
	vol_point = 0
	if price_vs_t_minus_1 > 0 and vol_vs_t_minus_1 < 30:
		price_point = 1
		vol_point = 1
	elif price_vs_t_minus_1 < 0 and vol_vs_t_minus_1 > 0:
		price_point = 1
		vol_point = 1

	total_points = price_point + vol_point

	return {
		"symbol": symbol,
		"vol_vs_t_minus_1": vol_vs_t_minus_1,
		"price_vs_t_minus_1": price_vs_t_minus_1,
		"price_point": price_point,
		"vol_point": vol_point,
		"total_points": total_points,
	}


class SellDataFetcherThread(QThread):
	"""Thread fetch/update dữ liệu cho Sell để không block UI."""

	progress = pyqtSignal(dict)
	finished = pyqtSignal()

	def __init__(self, symbols, stock_data, mode="initial"):
		super().__init__()
		self.symbols = symbols
		self.stock_data = stock_data
		self.mode = mode

	def run(self):
		for symbol in self.symbols:
			try:
				if self.mode == "initial":
					self.stock_data.get_data(symbol, resl="1D")
				else:
					self.stock_data.update_data(symbol, resl="1D")

				df = self.stock_data.allData[symbol]
				if df is not None and len(df) >= 2:
					row_t_minus_1 = df.iloc[-2]
					row_t = df.iloc[-1]
					result = calculate_sell_scores(symbol, row_t_minus_1, row_t)
					self.progress.emit(result)
			except Exception as e:
				logger.error(f"Error fetching {symbol}: {e}")

		self.finished.emit()


class SellScannerWindow(QMainWindow):
	fetch_completed = pyqtSignal()

	def __init__(self):
		super().__init__()

		central_widget = QWidget()
		self.setCentralWidget(central_widget)
		main_layout = QVBoxLayout(central_widget)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(0)

		group_box = QGroupBox("S")
		group_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
		group_layout = QVBoxLayout(group_box)
		group_layout.setContentsMargins(6, 6, 6, 6)
		group_layout.setSpacing(6)

		self.stock_data = StockData()
		self._is_first_load = True
		self._sort_state = 0
		self._symbol_results = {}
		self._symbol_order = []

		self.metric_labels = [
			"Syb",
			"Vol_vs_T-1",
			"Price_vs_T-1",
			"Tổng Điểm",
		]

		self.table = QTableWidget()
		self.table.setRowCount(len(self.metric_labels))
		self.table.setColumnCount(0)
		self.table.setVerticalHeaderLabels(self.metric_labels)
		self.table.setFont(QFont("Segoe UI", 9))
		self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

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

		self._fit_table_height()

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

		top_layout.addWidget(date_label)
		top_layout.addWidget(self.prev_date_btn)
		top_layout.addWidget(self.date_input)
		top_layout.addWidget(self.next_date_btn)
		top_layout.addWidget(self.check_date_btn)
		top_layout.addStretch()

		group_layout.addLayout(top_layout)
		group_layout.addWidget(self.table)
		main_layout.addWidget(group_box)
		main_layout.addStretch()

		self.load_symbols()

	def _fit_table_height(self):
		rows_height = self.table.verticalHeader().length()
		header_height = self.table.horizontalHeader().height() if self.table.horizontalHeader() else 0
		frame = self.table.frameWidth() * 2
		self.table.setFixedHeight(rows_height + header_height + frame + 2)

	def load_symbols(self):
		"""Đọc danh sách cổ phiếu từ backup/syb_scan.csv - chỉ lấy mã 3 ký tự."""
		try:
			df = pd.read_csv("backup/syb_hold_scan.csv")
			raw_symbols = df["syb"].astype(str).str.strip().str.upper().tolist()
			self.symbols = list(dict.fromkeys([syb for syb in raw_symbols if len(syb) == 3]))
		except Exception as e:
			logger.error(f"Error loading symbols: {e}")
			self.symbols = ["CTG", "VCB", "MBB"]

	def refresh_data(self):
		"""Fetch/update dữ liệu và cập nhật dần từng cột symbol."""
		self._sort_state = 0
		if self._is_first_load:
			self._symbol_results = {}
			self._symbol_order = []
			self.table.clearContents()
			self.table.setColumnCount(0)

		mode = "initial" if self._is_first_load else "update"
		self._is_first_load = False

		self.fetch_thread = SellDataFetcherThread(self.symbols, self.stock_data, mode=mode)
		self.fetch_thread.progress.connect(self.add_row)
		self.fetch_thread.finished.connect(self.on_fetch_finished)
		self.fetch_thread.start()

	def add_row(self, data):
		symbol = data["symbol"]
		self._symbol_results[symbol] = data
		if symbol not in self._symbol_order:
			self._symbol_order.append(symbol)

		if self._sort_state != 0:
			self._apply_sort_order()
			return

		self._upsert_symbol_column(symbol, data)

	def _upsert_symbol_column(self, symbol, data):
		existing_col = -1
		for col in range(self.table.columnCount()):
			item = self.table.item(0, col)
			if item and item.text() == symbol:
				existing_col = col
				break

		if existing_col >= 0:
			col_pos = existing_col
		else:
			col_pos = self.table.columnCount()
			self.table.insertColumn(col_pos)
			self.table.setHorizontalHeaderItem(col_pos, QTableWidgetItem(symbol))
			self.table.setColumnWidth(col_pos, 56)

		items = [
			data["symbol"],
			f"{float(data['vol_vs_t_minus_1']):.2f}%",
			f"{float(data['price_vs_t_minus_1']):.2f}%",
			str(data["total_points"]),
		]

		for row, item_text in enumerate(items):
			item = QTableWidgetItem(item_text)
			item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
			if row == 3 and data["total_points"] >= 2:
				item.setBackground(QColor(255, 235, 205))
				item.setFont(QFont(None, 10, QFont.Weight.Bold))
			self.table.setItem(row, col_pos, item)

	def _on_vertical_header_clicked(self, row):
		"""Click hàng Tổng Điểm để toggle sort theo cột symbol."""
		total_row = 3
		if row != total_row:
			return

		self._sort_state = (self._sort_state + 1) % 3
		self._apply_sort_order()

	def _apply_sort_order(self):
		if not self._symbol_order:
			return

		base_index = {syb: idx for idx, syb in enumerate(self._symbol_order)}

		if self._sort_state == 0:
			ordered_symbols = list(self._symbol_order)
		elif self._sort_state == 1:
			ordered_symbols = sorted(
				self._symbol_order,
				key=lambda syb: (-float(self._symbol_results.get(syb, {}).get("total_points", 0)), base_index[syb]),
			)
		else:
			ordered_symbols = sorted(
				self._symbol_order,
				key=lambda syb: (float(self._symbol_results.get(syb, {}).get("total_points", 0)), base_index[syb]),
			)

		self.table.clearContents()
		self.table.setColumnCount(0)
		for symbol in ordered_symbols:
			symbol_data = self._symbol_results.get(symbol)
			if symbol_data is not None:
				self._upsert_symbol_column(symbol, symbol_data)

	def on_fetch_finished(self):
		self._set_check_date_to_latest_available()
		self.fetch_completed.emit()
		logger.debug("Sell fetch data finished!")

	def _set_check_date_to_latest_available(self):
		latest_date = None
		for df in self.stock_data.allData.values():
			if df is None or df.empty or "Date" not in df.columns:
				continue

			date_series = pd.to_datetime(df["Date"], errors="coerce").dropna()
			if date_series.empty:
				continue

			symbol_latest = date_series.max()
			if latest_date is None or symbol_latest > latest_date:
				latest_date = symbol_latest

		if latest_date is not None:
			self.date_input.setText(latest_date.strftime("%d/%m/%Y"))

	def on_check_date(self):
		"""Logic check ngày chỉ dùng trong sell.py."""
		date_text = self.date_input.text().strip()
		if not date_text:
			logger.warning("Vui lòng nhập ngày")
			return

		try:
			check_date = datetime.strptime(date_text, "%d/%m/%Y")
			if hasattr(self, "fetch_thread") and self.fetch_thread.isRunning():
				logger.warning("Đang tải dữ liệu. Vui lòng chờ tải xong rồi Check ngày.")
				return

			target_date = pd.Timestamp(check_date.date())
			date_results = {}
			date_order = []

			for symbol in self.symbols:
				df = self.stock_data.allData.get(symbol)
				if df is None or len(df) < 2:
					continue

				date_series = pd.to_datetime(df["Date"], errors="coerce").dt.normalize()
				matched_rows = df.index[date_series == target_date]
				if len(matched_rows) == 0:
					continue

				idx_t = matched_rows[-1]
				if idx_t <= 0:
					continue

				row_t_minus_1 = df.iloc[idx_t - 1]
				row_t = df.iloc[idx_t]
				result = calculate_sell_scores(symbol, row_t_minus_1, row_t)
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

			if self._symbol_order:
				logger.info(
					f"Đã cập nhật bảng Sell theo ngày {check_date.strftime('%d/%m/%Y')} ({len(self._symbol_order)} mã)"
				)
			else:
				logger.warning(f"Không có dữ liệu cho ngày {check_date.strftime('%d/%m/%Y')}.")
		except ValueError:
			logger.error("Định dạng ngày không hợp lệ. Vui lòng nhập theo dd/mm/yyyy")

	def _shift_check_date(self, days):
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
		self._shift_check_date(-1)

	def on_next_date(self):
		self._shift_check_date(1)
