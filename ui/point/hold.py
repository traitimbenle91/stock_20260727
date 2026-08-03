import pandas as pd
from datetime import datetime
from typing import Callable, Optional
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
	QCheckBox,
	QLabel,
	QHeaderView,
	QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from ststock.StockData import StockData
from ststock.StockDataManager import DataFetcherThread
from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_hold_scores(symbol, row_t_minus_1, row_t):
	"""Tính % biến động Vol/Price và điểm theo luật Hold."""
	prev_close = float(row_t_minus_1["Close"])
	curr_close = float(row_t["Close"])
	prev_vol = float(row_t_minus_1["Volume"])
	curr_vol = float(row_t["Volume"])

	price_vs_t_minus_1 = 0.0 if prev_close == 0 else ((curr_close - prev_close) / prev_close) * 100
	vol_vs_t_minus_1 = 0.0 if prev_vol == 0 else ((curr_vol - prev_vol) / prev_vol) * 100

	price_point = 0
	vol_point = 0

	if price_vs_t_minus_1 > 0:
		price_point = 2
		
	if vol_vs_t_minus_1 > 0:
		vol_point = 0

	total_points = price_point + vol_point

	return {
		"symbol": symbol,
		"vol_vs_t_minus_1": vol_vs_t_minus_1,
		"price_vs_t_minus_1": price_vs_t_minus_1,
		"price_point": price_point,
		"vol_point": vol_point,
		"total_points": total_points,
	}


class HoldScannerWindow(QMainWindow):
	fetch_completed = pyqtSignal()
	check_date_changed = pyqtSignal(str)

	def __init__(self):
		super().__init__()

		central_widget = QWidget()
		self.setCentralWidget(central_widget)
		main_layout = QVBoxLayout(central_widget)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(0)

		group_box = QGroupBox("H")
		group_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
		group_layout = QVBoxLayout(group_box)
		group_layout.setContentsMargins(6, 6, 6, 6)
		group_layout.setSpacing(6)

		self.stock_data = StockData()
		self._is_first_load = True
		self._symbol_results = {}
		self._symbol_order = []
		self.fetch_thread: Optional[DataFetcherThread] = None
		self.codes: dict = {}
		self._get_next_b_date: Optional[Callable[[datetime], Optional[pd.Timestamp]]] = None
		self._get_buy_check_date: Optional[Callable[[], str]] = None

		self.metric_labels = [
			"Syb",
			"Vol: T_vs_T-1",
			"Price: T_vs_T-1",
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
			vertical_header.setDefaultSectionSize(26)
			vertical_header.setMinimumWidth(130)
			vertical_header.setMaximumWidth(160)
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

		self.auto_next_b_checkbox = QCheckBox("Auto Next B")
		self.auto_next_b_checkbox.toggled.connect(self._on_auto_next_b_toggled)
		self.auto_next_b_checkbox.setChecked(True)

		top_layout.addWidget(date_label)
		top_layout.addWidget(self.prev_date_btn)
		top_layout.addWidget(self.date_input)
		top_layout.addWidget(self.next_date_btn)
		top_layout.addWidget(self.check_date_btn)
		top_layout.addWidget(self.auto_next_b_checkbox)
		top_layout.addStretch()

		group_layout.addLayout(top_layout)
		group_layout.addWidget(self.table)
		main_layout.addWidget(group_box)
		main_layout.addStretch()

		# symbols sẽ được gán từ mainui.py
		self.symbols = {}

	def _fit_table_height(self):
		vertical_header = self.table.verticalHeader()
		horizontal_header = self.table.horizontalHeader()
		rows_height = vertical_header.length() if vertical_header is not None else 0
		header_height = horizontal_header.height() if horizontal_header is not None else 0
		frame = self.table.frameWidth() * 2
		self.table.setFixedHeight(rows_height + header_height + frame + 2)

	def refresh_data(self) -> str:
		"""Reset trạng thái bảng, trả về mode fetch ('initial'|'update'). Thread do mainui tạo."""
		if self._is_first_load:
			self._symbol_results = {}
			self._symbol_order = []
			self.table.clearContents()
			self.table.setColumnCount(0)
		mode = "initial" if self._is_first_load else "update"
		self._is_first_load = False
		return mode

	def add_row(self, data):
		symbol = data["symbol"]
		code = data.get("code", 0)
		key = (code, symbol)
		self._symbol_results[key] = data
		if key not in self._symbol_order:
			self._symbol_order.append(key)
		self._upsert_symbol_column(symbol, data, code)

	def _upsert_symbol_column(self, symbol, data, code=0):
		key = (code, symbol)
		existing_col = -1
		for col in range(self.table.columnCount()):
			item = self.table.item(0, col)
			if item and item.data(Qt.ItemDataRole.UserRole) == key:
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
			if row == 0:
				item.setData(Qt.ItemDataRole.UserRole, key)
				from config import CODE_COLORS
				rgb = CODE_COLORS[code] if 0 <= code < len(CODE_COLORS) else None
				if rgb is not None:
					item.setBackground(QColor(*rgb))
			if row == 3 and data["total_points"] >= 2:
				item.setBackground(QColor(224, 255, 255))
				item.setFont(QFont(None, 10, QFont.Weight.Bold))
			self.table.setItem(row, col_pos, item)

	def apply_external_order(self, ordered_keys):
		"""Sắp xếp lại cột theo danh sách (code, symbol) từ bảng ngoài (e.g. B)."""
		if not self._symbol_results:
			return
		self.table.clearContents()
		self.table.setColumnCount(0)
		for key in ordered_keys:
			code, symbol = key
			symbol_data = self._symbol_results.get(key)
			if symbol_data is not None:
				self._upsert_symbol_column(symbol, symbol_data, code)
		# Append any keys not in ordered_keys
		for key in self._symbol_order:
			if key not in ordered_keys:
				code, symbol = key
				symbol_data = self._symbol_results.get(key)
				if symbol_data is not None:
					self._upsert_symbol_column(symbol, symbol_data, code)

		h = self.table.horizontalHeader()
		if h is not None:
			h.setVisible(False)

	def on_fetch_finished(self):
		self._set_check_date_to_latest_available()
		self.fetch_completed.emit()
		logger.debug("Hold fetch data finished!")

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
			formatted_date = latest_date.strftime("%d/%m/%Y")
			self.date_input.setText(formatted_date)
			self.check_date_changed.emit(formatted_date)

	def get_next_available_date(self, base_date):
		"""Lấy ngày giao dịch kế tiếp trong dữ liệu Hold sau một ngày gốc."""
		if base_date is None:
			return None

		target_date = pd.Timestamp(base_date).normalize()
		next_date = None

		for df in self.stock_data.allData.values():
			if df is None or df.empty or "Date" not in df.columns:
				continue

			date_series = pd.to_datetime(df["Date"], errors="coerce").dropna().dt.normalize()
			future_dates = date_series[date_series > target_date]
			if future_dates.empty:
				continue

			symbol_next = future_dates.min()
			if next_date is None or symbol_next < next_date:
				next_date = symbol_next

		return next_date

	def _on_auto_next_b_toggled(self, checked):
		if checked and self.sync_to_next_buy_date():
			self.on_check_date(skip_auto_sync=True)

	def sync_to_next_buy_date(self, buy_date_text=None):
		"""Đồng bộ ngày Hold sang ngày có dữ liệu kế tiếp sau ngày check của Buy."""
		if self._get_next_b_date is None:
			logger.warning("Chưa cấu hình nguồn ngày cho Auto Next B.")
			return False

		if buy_date_text is None:
			buy_date_text = self._get_buy_check_date() if callable(self._get_buy_check_date) else ""

		buy_date_text = (buy_date_text or "").strip()
		if not buy_date_text:
			logger.warning("Bảng B chưa có Ngày check để đồng bộ.")
			return False

		try:
			buy_date = datetime.strptime(buy_date_text, "%d/%m/%Y")
		except ValueError:
			logger.error("Ngày check của bảng B không hợp lệ. Vui lòng nhập theo dd/mm/yyyy")
			return False

		next_date = self._get_next_b_date(buy_date)
		if next_date is None:
			logger.warning(f"Không tìm thấy ngày dữ liệu kế tiếp sau {buy_date_text} trong bảng B.")
			return False

		self.date_input.setText(next_date.strftime("%d/%m/%Y"))
		return True

	def on_check_date(self, _checked=False, skip_auto_sync=False):
		"""Logic check ngày chỉ dùng trong hold.py."""
		if not skip_auto_sync and self.auto_next_b_checkbox.isChecked() and not self.sync_to_next_buy_date():
			return

		date_text = self.date_input.text().strip()
		if not date_text:
			logger.warning("Vui lòng nhập ngày")
			return

		try:
			check_date = datetime.strptime(date_text, "%d/%m/%Y")
			if self.fetch_thread is not None and self.fetch_thread.isRunning():
				logger.warning("Đang tải dữ liệu. Vui lòng chờ tải xong rồi Check ngày.")
				return

			target_date = pd.Timestamp(check_date.date())
			date_results = {}
			date_order = []

			symbols_iter = [
				(code, syb) for code, sybs in self.symbols.items() for syb in sybs
			]
			for code, symbol in symbols_iter:
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
				result = calculate_hold_scores(symbol, row_t_minus_1, row_t)
				result["code"] = code
				key = (code, symbol)
				date_results[key] = result
				date_order.append(key)

			self._sort_state = 0
			self._symbol_results = date_results
			self._symbol_order = date_order

			self.table.clearContents()
			self.table.setColumnCount(0)
			self.table.setHorizontalHeaderLabels([])

			for key in self._symbol_order:
				code, symbol = key
				self._upsert_symbol_column(symbol, self._symbol_results[key], code)

			h = self.table.horizontalHeader()
			if h is not None:
				h.setVisible(False)

			normalized_date_text = target_date.strftime("%d/%m/%Y")
			self.date_input.setText(normalized_date_text)
			self.check_date_changed.emit(normalized_date_text)

			if self._symbol_order:
				logger.info(
					f"Đã cập nhật bảng Hold theo ngày {check_date.strftime('%d/%m/%Y')} ({len(self._symbol_order)} mã)"
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
