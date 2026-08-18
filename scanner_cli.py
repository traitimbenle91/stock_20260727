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
        # "T_minus_1_bullish": t_minus_1_bullish,
        # "T_minus_1_ema": t_minus_1_ema,
        # "T_minus_1_vol": t_minus_1_vol,
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

    price_vs_t_minus_1 = 0.0 if prev_close == 0 else round(((curr_close - prev_close) / prev_close) * 100, 2)
    vol_vs_t_minus_1 = 0.0 if prev_vol == 0 else round(((curr_vol - prev_vol) / prev_vol) * 100, 2)

    return {
        "symbol": symbol,
        "vol_vs_t_minus_1": vol_vs_t_minus_1,
        "price_vs_t_minus_1": price_vs_t_minus_1,
    }


def calculate_sell_scores(symbol, row_t_minus_1, row_t):
    return calculate_hold_scores(symbol, row_t_minus_1, row_t)


def _get_index_for_date(df: pd.DataFrame, check_date: str | None):
    if df is None or len(df) < 2:
        return None

    if not check_date:
        idx_t = len(df) - 1
        return idx_t

    target_date = pd.Timestamp(datetime.strptime(check_date, "%d/%m/%Y").date())
    date_series = pd.to_datetime(df["Date"], errors="coerce").dt.normalize()

    matched_rows = df.index[date_series == target_date]
    if len(matched_rows) == 0:
        return None

    idx_t = matched_rows[-1]
    if idx_t <= 0:
        return None
    return idx_t


def _print_table( result_df, limit: int):
    if result_df is None or result_df.empty:
        print("Khong co du lieu.")
        return

    if limit > 0:
        result_df = result_df.head(limit)

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)

    def bold_terminal(val, limit, less):
        if isinstance(val, (int, float))  and ((less and val <= limit) or (less == False and val >= limit)):
            return f"*{val}*" # \033[1m giúp in đậm, \033[0m để reset
        return str(val)
    
    result_df['vol_vs_t_minus_1'] = result_df['vol_vs_t_minus_1'].apply(lambda x: bold_terminal(x, 75, less=True))
    result_df['vol_t_minus_1_vs_ma20'] = result_df['vol_t_minus_1_vs_ma20'].apply(lambda x: bold_terminal(x, 95, less=False))
    result_df['vol_vs_ma20'] = result_df['vol_vs_ma20'].apply(lambda x: bold_terminal(x, 95, less=False))
    result_df['price_t_minus_1_c_vs_o'] = result_df['price_t_minus_1_c_vs_o'].apply(lambda x: bold_terminal(x, -2.5, less=True))

    # Highlight hàng Price: H_vs_L nếu biên độ >= 4%
    result_df['price_h_vs_l'] = result_df['price_h_vs_l'].apply(lambda x: bold_terminal(x, 4, less=False))

    result_df['pct_change'] = result_df['pct_change'].apply(lambda x: bold_terminal(x, 2, less=False))
    result_df['pct_change'] = result_df['pct_change'].apply(lambda x: bold_terminal(x, 0, less=True))

    
    short_names = {
        'symbol': 'Sym',
        'total_points': 'Pts',
        'pct_change': '%Chg',
        'vol_vs_t_minus_1': 'V/T1',
        'vol_t_minus_1_vs_ma20': 'VT1/M20',
        'vol_vs_ma20': 'V/M20',
        'price_o_vs_c': 'O/C',
        'price_h_vs_l': 'H/L',
        'price_t_minus_1_c_vs_o': 'T1_C/O',
        'h_vol_vs_t_minus_1': 'H_V/T1',
        'h_price_vs_t_minus_1': 'H_P/T1',
        's_vol_vs_t_minus_1': 'S_V/T1',
        's_price_vs_t_minus_1': 'S_P/T1',
        'price_cover_t_minus_1_vs_t': 'T1_Cov/T',
    }
    for col, short_name in short_names.items():
        if col in result_df.columns:
            result_df = result_df.rename(columns={col: short_name})

    with pd.option_context("display.max_columns", None, "display.width", 200):
        # Lọc các cột cần thiết, đổi tên rồi in ra luôn mà không làm thay đổi DataFrame gốc
        # print(result_df[list(short_names.keys())].rename(columns=short_names).to_string(index=False))
        print(result_df.to_string(index=True))

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

        add_ema(df, period=10, source_col="Close")
        add_volume_ma(df, period=20, source_col="Volume")
        idx_t = _get_index_for_date(df, check_date)

        if idx_t is None:
            print(f"Khong tim thay du lieu cho symbol {symbol} vao ngay {check_date}.")
            continue
        try:
            if mode in ("buy", "all"):
                row_t_minus_1, row_t = df.iloc[idx_t - 1], df.iloc[idx_t]
                buy_rows.append({"code": code, **calculate_buy_scores(symbol, row_t_minus_1, row_t)})

            if mode in ("hold", "all"):
                row_t_minus_1, row_t = df.iloc[idx_t], df.iloc[idx_t+1]
                hold_rows.append({"code": code, **calculate_hold_scores(symbol, row_t_minus_1, row_t)})

            if mode in ("sell", "all"):
                row_t_minus_1, row_t = df.iloc[idx_t + 1], df.iloc[idx_t+2]
                sell_rows.append({"code": code, **calculate_sell_scores(symbol, row_t_minus_1, row_t)})
        except IndexError as e:
            pass
            # print("❌ Đã xảy ra lỗi: {symbol} {e}")
            # print("👉 Hướng xử lý: Chỉ số vượt quá số hàng hiện có của bảng!")

    sort_columns = ["total_points", "pct_change"]
    
    
    buy_df = pd.DataFrame(buy_rows)
    
    buy_df = buy_df.sort_values(by=sort_columns, ascending=[False] * len(sort_columns))
    buy_df = buy_df.drop(columns=["code"])
    buy_df = buy_df.drop_duplicates(subset=['symbol'])

    if hold_rows and mode in ("hold", "all"):
        hold_df = pd.DataFrame(hold_rows)
        buy_df['HOLD'] = '='
        hold_df = hold_df.drop_duplicates(subset=['symbol'])
        hold_df = hold_df.rename(columns={'vol_vs_t_minus_1': 'h_vol_vs_t_minus_1', 'price_vs_t_minus_1': 'h_price_vs_t_minus_1'})

        buy_df = buy_df.merge(hold_df[['symbol', 'h_vol_vs_t_minus_1', 'h_price_vs_t_minus_1']], on='symbol', how='left')

    if sell_rows and mode in ("sell", "all"):
        sell_df = pd.DataFrame(sell_rows)
        buy_df['SELL'] = '='
        hold_df = sell_df.drop_duplicates(subset=['symbol'])

        sell_df = sell_df.rename(columns={'vol_vs_t_minus_1': 's_vol_vs_t_minus_1', 'price_vs_t_minus_1': 's_price_vs_t_minus_1'})
        buy_df = buy_df.merge(sell_df[['symbol', 's_vol_vs_t_minus_1', 's_price_vs_t_minus_1']], on='symbol', how='left')
    _print_table(buy_df, limit)


def build_parser():
    parser = argparse.ArgumentParser(description="Stock scanner command line")
    parser.add_argument("-m", "--mode", choices=["buy", "hold", "sell", "all"], default="all")
    parser.add_argument("-s", "--symbols-file", default="backup/syb_scan.csv")
    parser.add_argument("-d", "--date", help="Ngay check theo dinh dang dd/mm/yyyy", default=None)
    parser.add_argument("-l", "--limit", type=int, default=500, help="So dong toi da moi bang. 0 de in tat ca")
    parser.add_argument("-r", "--refresh", action="store_true", help="Cap nhat them du lieu moi nhat tu web")
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
