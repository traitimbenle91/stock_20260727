from __future__ import annotations

import argparse
from datetime import datetime

import pandas as pd

from indicator.indicators import add_ema, add_volume_ma
from ststock.StockData import StockData
from ststock.StockDataManager import StockDataManager, flatten_symbols
from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_buy_scores(symbol, row_t_minus_1, row_t):
    def get_score_t_minus_1(row):
        red_candle = 1 if row["Close"] < row["Open"] else 0
        price_below_ema = 1 if row["Close"] < row["EMA10"] else 0
        vol_below_vma = 1 if row["Volume"] < row["VMA20"] else 0
        return red_candle, price_below_ema, vol_below_vma

    def get_score_t(row):
        green_candle = 1 if row["Close"] > row["Open"] else 0
        price_below_ema = 1 if row["Close"] < row["EMA10"] else 0
        vol_below_vma = 1 if row["Volume"] < row["VMA20"] else 0.5
        return green_candle, price_below_ema, vol_below_vma

    t_minus_1_bullish, t_minus_1_ema, t_minus_1_vol = get_score_t_minus_1(row_t_minus_1)
    t_bullish, t_ema, t_vol = get_score_t(row_t)

    prev_close = float(row_t_minus_1["Close"])
    curr_close = float(row_t["Close"])
    pct_change = 0.0 if prev_close == 0 else round(((curr_close - prev_close) / prev_close) * 100, 2)

    prev_vol = float(row_t_minus_1["Volume"])
    curr_vol = float(row_t["Volume"])
    vol_vs_t_minus_1 = 0.0 if prev_vol == 0 else round((curr_vol / prev_vol) * 100, 2)
    vma20 = float(row_t["VMA20"])
    vol_vs_ma20 = 0.0 if vma20 == 0 else round((curr_vol / vma20) * 100, 2)
    prev_vma20 = float(row_t_minus_1["VMA20"])
    vol_t_minus_1_vs_ma20 = 0.0 if prev_vma20 == 0 else round((prev_vol / prev_vma20) * 100, 2)

    open_price = float(row_t["Open"])
    close_price = float(row_t["Close"])
    low_price = float(row_t["Low"])
    high_price = float(row_t["High"])

    price_o_vs_c = 0.0 if open_price == 0 else round(((close_price - open_price) / open_price) * 100, 2)
    price_h_vs_l = 0.0 if low_price == 0 else round(((high_price - low_price) / low_price) * 100, 2)

    prev_open_price = float(row_t_minus_1["Open"])
    prev_close_price = float(row_t_minus_1["Close"])
    price_t_minus_1_c_vs_o = 0.0 if prev_close_price == 0 else round(((prev_close_price - prev_open_price) / prev_close_price) * 100, 2)

    price_cover_t_minus_1_vs_t = 1 if (
        (prev_open_price > open_price > prev_close_price)
        or (prev_open_price > close_price > prev_close_price)
    ) else 0

    total_points = (
        t_minus_1_bullish
        + t_minus_1_ema
        + t_minus_1_vol
        + t_bullish
        + t_ema
        + t_vol
        + price_cover_t_minus_1_vs_t
    )

    return {
        "symbol": symbol,
        "T_minus_1_bullish": t_minus_1_bullish,
        "T_minus_1_ema": t_minus_1_ema,
        "T_minus_1_vol": t_minus_1_vol,
        "T_bullish": t_bullish,
        "T_ema": t_ema,
        "T_vol": t_vol,
        "price_cover_t_minus_1_vs_t": price_cover_t_minus_1_vs_t,
        "total_points": total_points,
        "pct_change": pct_change,
        "vol_vs_t_minus_1": vol_vs_t_minus_1,
        "vol_t_minus_1_vs_ma20": vol_t_minus_1_vs_ma20,
        "vol_vs_ma20": vol_vs_ma20,
        "price_o_vs_c": price_o_vs_c,
        "price_h_vs_l": price_h_vs_l,
        "price_t_minus_1_c_vs_o": price_t_minus_1_c_vs_o,
    }


def calculate_hold_scores(symbol, row_t_minus_1, row_t):
    prev_close = float(row_t_minus_1["Close"])
    curr_close = float(row_t["Close"])
    prev_vol = float(row_t_minus_1["Volume"])
    curr_vol = float(row_t["Volume"])

    price_vs_t_minus_1 = 0.0 if prev_close == 0 else ((curr_close - prev_close) / prev_close) * 100
    vol_vs_t_minus_1 = 0.0 if prev_vol == 0 else ((curr_vol - prev_vol) / prev_vol) * 100

    price_point = 2 if price_vs_t_minus_1 > 0 else 0
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


def calculate_sell_scores(symbol, row_t_minus_1, row_t):
    return calculate_hold_scores(symbol, row_t_minus_1, row_t)


def _get_rows_for_date(df: pd.DataFrame, check_date: str | None):
    if df is None or len(df) < 2:
        return None

    if not check_date:
        idx_t = len(df) - 1
        return df.iloc[idx_t - 1], df.iloc[idx_t]

    target_date = pd.Timestamp(datetime.strptime(check_date, "%d/%m/%Y").date())
    date_series = pd.to_datetime(df["Date"], errors="coerce").dt.normalize()
    matched_rows = df.index[date_series == target_date]
    if len(matched_rows) == 0:
        return None

    idx_t = matched_rows[-1]
    if idx_t <= 0:
        return None

    return df.iloc[idx_t - 1], df.iloc[idx_t]


def _print_table(title: str, rows: list[dict], limit: int, sort_columns: list[str]):
    print(f"\n=== {title} ===")
    if not rows:
        print("Khong co du lieu.")
        return

    result_df = pd.DataFrame(rows)
    result_df = result_df.sort_values(by=sort_columns, ascending=[False] * len(sort_columns))
    if limit > 0:
        result_df = result_df.head(limit)

    # with pd.option_context("display.max_columns", None, "display.width", 200):
    #     print(result_df.to_string(index=False))

    # print(result_df[['symbol', 'total_points', 'pct_change', 'vol_vs_t_minus_1', 'vol_t_minus_1_vs_ma20', 'vol_vs_ma20', 'price_o_vs_c', 'price_h_vs_l', 'price_t_minus_1_c_vs_o']].to_string(index=False))
        # Tạo một dictionary để đổi tên các cột sang dạng viết ngắn gọn
    short_names = {
        'symbol': 'Sym',
        'total_points': 'Pts',
        'pct_change': '%Chg',
        'vol_vs_t_minus_1': 'V/T1',
        'vol_t_minus_1_vs_ma20': 'VT1/M20',
        'vol_vs_ma20': 'V/M20',
        'price_o_vs_c': 'O/C',
        'price_h_vs_l': 'H/L',
        'price_t_minus_1_c_vs_o': 'T1_C/O'
    }


    # Lọc các cột cần thiết, đổi tên rồi in ra luôn mà không làm thay đổi DataFrame gốc
    print(result_df[list(short_names.keys())].rename(columns=short_names).to_string(index=False))


def run_cli_scan(mode: str, symbols_file: str, check_date: str | None, limit: int, refresh: bool):
    manager = StockDataManager()
    manager.load_symbols(filepath=symbols_file)
    symbol_pairs = flatten_symbols(manager.symbols)

    unique_symbols = []
    seen = set()
    for _, symbol in symbol_pairs:
        if symbol not in seen:
            seen.add(symbol)
            unique_symbols.append(symbol)

    stock_data = StockData()
    for symbol in unique_symbols:
        stock_data.get_data(symbol, resl="1D")
        if refresh:
            stock_data.update_data(symbol, resl="1D")

    buy_rows = []
    hold_rows = []
    sell_rows = []

    for code, symbol in symbol_pairs:
        df = stock_data.allData.get(symbol)
        if df is None or df.empty:
            continue

       

        if mode in ("buy", "all"):
            add_ema(df, period=10, source_col="Close")
            add_volume_ma(df, period=20, source_col="Volume")
            rows = _get_rows_for_date(df, check_date)
            if rows is None:
                continue
            row_t_minus_1, row_t = rows
            buy_rows.append({"code": code, **calculate_buy_scores(symbol, row_t_minus_1, row_t)})

        if mode in ("hold", "all"):
            hold_rows.append({"code": code, **calculate_hold_scores(symbol, row_t_minus_1, row_t)})

        if mode in ("sell", "all"):
            sell_rows.append({"code": code, **calculate_sell_scores(symbol, row_t_minus_1, row_t)})
    

    if mode in ("buy", "all"):
        _print_table("BUY", buy_rows, limit, ["total_points", "pct_change"])
    if mode in ("hold", "all"):
        _print_table("HOLD", hold_rows, limit, ["total_points", "price_vs_t_minus_1"])
    if mode in ("sell", "all"):
        _print_table("SELL", sell_rows, limit, ["total_points", "price_vs_t_minus_1"])


def build_parser():
    parser = argparse.ArgumentParser(description="Stock scanner command line")
    parser.add_argument("--mode", choices=["buy", "hold", "sell", "all"], default="all")
    parser.add_argument("--symbols-file", default="backup/syb_scan.csv")
    parser.add_argument("--date", help="Ngay check theo dinh dang dd/mm/yyyy", default=None)
    parser.add_argument("--limit", type=int, default=20, help="So dong toi da moi bang. 0 de in tat ca")
    parser.add_argument("--refresh", action="store_true", help="Cap nhat them du lieu moi nhat tu web")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    run_cli_scan(
        mode=args.mode,
        symbols_file=args.symbols_file,
        check_date=args.date,
        limit=args.limit,
        refresh=args.refresh,
    )


if __name__ == "__main__":
    main()