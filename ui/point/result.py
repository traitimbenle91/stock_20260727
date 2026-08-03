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
	QLabel,
	QHeaderView,
	QLineEdit,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from utils.logger import get_logger

logger = get_logger(__name__)


class ResultScannerWindow(QMainWindow):
	def __init__(self):
		super().__init__()

		central_widget = QWidget()
		self.setCentralWidget(central_widget)
		main_layout = QVBoxLayout(central_widget)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(0)

		group_box = QGroupBox("R")
		group_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
		group_layout = QVBoxLayout(group_box)
		group_layout.setContentsMargins(6, 6, 6, 6)
		group_layout.setSpacing(6)

		self.metric_labels = [
			"Syb",
			"Result",
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
		top_layout.addWidget(QLabel("B:"))
		self.buy_date_view = QLineEdit()
		self.buy_date_view.setReadOnly(True)
		self.buy_date_view.setMaximumWidth(120)
		top_layout.addWidget(self.buy_date_view)

		top_layout.addWidget(QLabel("S:"))
		self.sell_date_view = QLineEdit()
		self.sell_date_view.setReadOnly(True)
		self.sell_date_view.setMaximumWidth(120)
		top_layout.addWidget(self.sell_date_view)

		self.refresh_btn = QPushButton("Refresh")
		self.refresh_btn.setMaximumWidth(80)
		self.refresh_btn.clicked.connect(self.refresh_results)
		top_layout.addWidget(self.refresh_btn)
		top_layout.addStretch()

		group_layout.addLayout(top_layout)
		group_layout.addWidget(self.table)
		main_layout.addWidget(group_box)
		main_layout.addStretch()

		self.symbols = {}
		self._symbol_results = {}
		self._symbol_order = []

		self._buy_stock_data = None
		self._sell_stock_data = None
		self._get_buy_check_date: Optional[Callable[[], str]] = None
		self._get_sell_check_date: Optional[Callable[[], str]] = None

	def _fit_table_height(self):
		vertical_header = self.table.verticalHeader()
		horizontal_header = self.table.horizontalHeader()
		rows_height = vertical_header.length() if vertical_header is not None else 0
		header_height = horizontal_header.height() if horizontal_header is not None else 0
		frame = self.table.frameWidth() * 2
		self.table.setFixedHeight(rows_height + header_height + frame + 2)

	def configure_sources(
		self,
		symbols,
		buy_stock_data,
		sell_stock_data,
		get_buy_check_date: Callable[[], str],
		get_sell_check_date: Callable[[], str],
	):
		self.symbols = symbols or {}
		self._buy_stock_data = buy_stock_data
		self._sell_stock_data = sell_stock_data
		self._get_buy_check_date = get_buy_check_date
		self._get_sell_check_date = get_sell_check_date

	def _parse_date(self, date_text):
		if not date_text:
			return None
		try:
			return pd.Timestamp(datetime.strptime(date_text, "%d/%m/%Y").date())
		except ValueError:
			return None

	def _get_close_by_date(self, stock_data, symbol, target_date):
		if stock_data is None:
			return None

		df = stock_data.allData.get(symbol)
		if df is None or df.empty or "Date" not in df.columns or "Close" not in df.columns:
			return None

		date_series = pd.to_datetime(df["Date"], errors="coerce").dt.normalize()
		matched_rows = df.index[date_series == target_date]
		if len(matched_rows) == 0:
			return None

		idx = matched_rows[-1]
		try:
			return float(df.iloc[idx]["Close"])
		except (TypeError, ValueError):
			return None

	def refresh_results(self):
		if not callable(self._get_buy_check_date) or not callable(self._get_sell_check_date):
			logger.warning("Chưa cấu hình nguồn ngày check cho bảng R.")
			return

		buy_date_text = (self._get_buy_check_date() or "").strip()
		sell_date_text = (self._get_sell_check_date() or "").strip()
		self.buy_date_view.setText(buy_date_text)
		self.sell_date_view.setText(sell_date_text)

		buy_date = self._parse_date(buy_date_text)
		sell_date = self._parse_date(sell_date_text)
		if buy_date is None or sell_date is None:
			logger.warning("Ngày check B/S không hợp lệ để tính Result.")
			return

		date_results = {}
		date_order = []

		symbols_iter = (
			[(code, syb) for code, sybs in self.symbols.items() for syb in sybs]
			if isinstance(self.symbols, dict)
			else [(0, syb) for syb in self.symbols]
		)
		for code, symbol in symbols_iter:
			close_buy = self._get_close_by_date(self._buy_stock_data, symbol, buy_date)
			close_sell = self._get_close_by_date(self._sell_stock_data, symbol, sell_date)
			if close_buy is None or close_sell is None or close_sell == 0:
				continue

			result_pct = ((close_sell - close_buy) / close_sell) * 100
			result = {
				"symbol": symbol,
				"code": code,
				"result": result_pct,
			}
			key = (code, symbol)
			date_results[key] = result
			date_order.append(key)

		self._symbol_results = date_results
		self._symbol_order = date_order

		self.table.clearContents()
		self.table.setColumnCount(0)
		self.table.setHorizontalHeaderLabels([])

		for key in self._symbol_order:
			code, symbol = key
			self._upsert_symbol_column(symbol, self._symbol_results[key], code)

		# Đảm bảo horizontal header vẫn ẩn sau khi rebuild cột
		h = self.table.horizontalHeader()
		if h is not None:
			h.setVisible(False)

		if self._symbol_order:
			logger.info(
				f"Đã cập nhật bảng Result theo B={buy_date_text}, S={sell_date_text} ({len(self._symbol_order)} mã)"
			)
		else:
			logger.warning(f"Không có dữ liệu Result cho B={buy_date_text}, S={sell_date_text}.")

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
			f"{float(data['result']):.2f}%",
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

			if row == 1:
				result_val = float(data.get("result", 0.0))
				if result_val >= 0:
					item.setBackground(QColor(173, 216, 230))
				else:
					item.setBackground(QColor(255, 220, 220))

			self.table.setItem(row, col_pos, item)

	def apply_external_order(self, ordered_keys):
		if not self._symbol_results:
			return

		self.table.clearContents()
		self.table.setColumnCount(0)
		for key in ordered_keys:
			code, symbol = key
			symbol_data = self._symbol_results.get(key)
			if symbol_data is not None:
				self._upsert_symbol_column(symbol, symbol_data, code)

		for key in self._symbol_order:
			if key not in ordered_keys:
				code, symbol = key
				symbol_data = self._symbol_results.get(key)
				if symbol_data is not None:
					self._upsert_symbol_column(symbol, symbol_data, code)

		h = self.table.horizontalHeader()
		if h is not None:
			h.setVisible(False)
