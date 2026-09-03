from __future__ import annotations

import argparse
import readchar  # Thư viện đọc một ký tự ngay lập tức
from datetime import datetime, timedelta

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

    t_minus_1_bullish_cond, t_minus_1_ema_cond, t_minus_1_vol_cond = get_score_t_minus_1(row_t_minus_1)
    t_bullish_cond, t_ema_cond, t_vol_cond = get_score_t(row_t)

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

    

     

    def cal_sum_score_sample1():
        return (
            # t_minus_1_bullish_cond : T-1 red candle
            # t_minus_1_ema_cond     : T-1 price below ema10
            # t_minus_1_vol_cond     : T-1 volume < ma20
            # t_bullish_cond         : T green candle
            # t_ema_cond             : T  price below ema10
            # t_vol_cond             : T volume < ma20 
            t_minus_1_bullish_cond
            + t_minus_1_ema_cond
            + t_minus_1_vol_cond
            + t_bullish_cond
            + t_ema_cond
            + t_vol_cond
        )
    def do_price_cov():
        if (prev_open_price > close_price > prev_close_price):
            return 1
        else:
            return 0

    vol_vs_t_minus_1_cond = 1 if vol_vs_t_minus_1 <= 100 else 0

    def cal_sum_score_sample2():
       # t_minus_1_bullish_cond : T-1 red candle
       # t_minus_1_ema_cond     : T-1 price below ema
       # t_bullish_cond         : T green candle
       # t_ema_cond             : T  price below ema
       return   t_minus_1_bullish_cond + \
                t_minus_1_ema_cond + \
                t_bullish_cond

    return {
        "symbol": symbol,
        # "t_minus_1_bullish_cond": t_minus_1_bullish_cond,
        # "t_minus_1_ema_cond": t_minus_1_ema_cond,
        # "t_minus_1_vol_cond": t_minus_1_vol_cond,
        # "Green": t_bullish_cond,
        # "P_lo_ema": t_ema_cond,
        # "V_lo_ema": t_vol_cond,
        # "P_cov": price_cover_t_minus_1_vs_t_cond,
        "Sam1": cal_sum_score_sample1(),
        "cov": do_price_cov(),
        "vol": vol_vs_t_minus_1_cond,
        "|": "|",
        "Sam2": cal_sum_score_sample2(),
        # 'vol2': vol_t_minus_1_more_t_cond,
        ":": ":",
        "T-1_P_C/0": price_t_minus_1_c_vs_o,
        "T-1_V_/M20": vol_t_minus_1_vs_ma20,
        "||": "||",
        "P_Chgd": pct_change,
        "V_Chgd": vol_vs_t_minus_1,
        "V_/M20": vol_vs_ma20,
        "P_O/C": price_o_vs_c,
        "P_H/L": price_h_vs_l,
        "Closed": close_price,
        
    }



def calculate_result_scores(symbol, row_t_next_2, row_t):
    next_2_close = float(row_t_next_2["Close"])
    curr_close = float(row_t["Close"])

    price_vs_t_minus_1 = 0.0 if curr_close == 0 else round(((next_2_close - curr_close) / curr_close) * 100, 2)

    return {
        "symbol": symbol,
        # "vol_vs_t_minus_1": vol_vs_t_minus_1,
        "Result": price_vs_t_minus_1,
    }


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


def _print_table( result_df, limit: int,  order, show_all: bool):
    if result_df is None or result_df.empty:
        print("Khong co du lieu.")
        return

    # if limit > 0:
    #     result_df = result_df.head(limit)

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)

    def bold_terminal(val, limit, less):
        if isinstance(val, (int, float))  and ((less and val <= limit) or (less == False and val >= limit)):
            return f"*{val}*" # \033[1m giúp in đậm, \033[0m để reset
        return str(val)
    
    result_df['V_Chgd'] = result_df['V_Chgd'].apply(lambda x: bold_terminal(x, 100, less=False))
    result_df['T-1_V_/M20'] = result_df['T-1_V_/M20'].apply(lambda x: bold_terminal(x, 95, less=False))
    result_df['V_/M20'] = result_df['V_/M20'].apply(lambda x: bold_terminal(x, 95, less=False))
    result_df['T-1_P_C/0'] = result_df['T-1_P_C/0'].apply(lambda x: bold_terminal(x, -2.5, less=True))

    # Highlight hàng Price: H_vs_L nếu biên độ >= 4%
    result_df['P_H/L'] = result_df['P_H/L'].apply(lambda x: bold_terminal(x, 4, less=False))

    result_df['P_Chgd'] = result_df['P_Chgd'].apply(lambda x: bold_terminal(x, 2, less=False))
    result_df['P_Chgd'] = result_df['P_Chgd'].apply(lambda x: bold_terminal(x, 0, less=True))

    name_sort = "Result"

    if order > 0:
        name_sort = f"Sam{order}"
    
    sort_columns = {
        0: ['Result'],
        1: [name_sort, 'cov', 'vol'],
        2: [name_sort, 'cov', 'vol']
    }

    max_value_dict = {
        "Result": 2,
        # "Sam1": 6,
        # "Sam2": 7,
        # "Sam3": 5,
        # "Sam4": 5,
    }
    

    with pd.option_context("display.max_columns", None, "display.width", 200):
        df_filtered = result_df
        try:
            if not show_all:                    
                max_value = max_value_dict.get(name_sort, result_df[name_sort].max())
                df_filtered = result_df[result_df[name_sort] >= max_value]
                print(f"\n{name_sort} > {max_value}: {(df_filtered['Result'] >= 0).sum()/ len(df_filtered) * 100:.2f}%")
            df_filtered = df_filtered.sort_values(by=sort_columns[order], ascending=[False] * len(sort_columns[order]))
            
        except Exception as e:
            print(f"Error filtering by {name_sort}: {e}")

        if limit > 0:
            df_filtered = df_filtered.head(limit)

        print(df_filtered.to_string(index=False))

        _print_table_with_good(df_filtered)

def _print_table_with_good(df):
    if df is None or df.empty:
        print("Khong co du lieu.")
        return

    df_filtered = df[~df['V_Chgd'].astype(str).str.contains('*', regex=False) & 
                     ~df['T-1_V_/M20'].astype(str).str.contains('*', regex=False) &
                     ~df['V_/M20'].astype(str).str.contains('*', regex=False) &
                     ~df['T-1_P_C/0'].astype(str).str.contains('*', regex=False) &
                     ~df['P_H/L'].astype(str).str.contains('*', regex=False) &
                     ~df['P_Chgd'].astype(str).str.contains('*', regex=False)
                   ]
    print("\n ============= Filter good symb ====================")
    try:
        print(f"Result: {(df_filtered['Result'] >= 0).sum()/ len(df_filtered) * 100:.2f}%\n")
    except Exception as e:
            print(f"Error filtering by : {e}")
    if len(df_filtered) <= 0:
        print("Empty df_filtered\n")
        return
    print(df_filtered.to_string(index=False))

    

prev_date = None
next_date = None

def get_prev_next_date(df, idx_t):
    global prev_date
    global next_date

    current_pos = df.index.get_loc(idx_t)

    previous_idx = df.index[current_pos - 1] if current_pos > 0 else None

    next_idx = df.index[current_pos + 1] if current_pos < len(df) - 1 else None

    if previous_idx:
        prev_date =  pd.to_datetime(df.Date[previous_idx]).strftime("%d/%m/%Y")

    if next_idx:
        next_date =  pd.to_datetime(df.Date[next_idx]).strftime("%d/%m/%Y")


def run_cli_scan(order: int, symbols_file: str, check_date: str | None, limit: int, refresh: bool, show_all: bool):
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
    result_rows = []

    for code, symbol in symbol_pairs:
        df = stock_data.allData.get(symbol)
        if df is None or df.empty:
            continue

        add_ema(df, period=10, source_col="Close")
        add_volume_ma(df, period=20, source_col="Volume")
        idx_t = _get_index_for_date(df, check_date)

        if idx_t is None:
            # print(f"Khong tim thay du lieu cho symbol {symbol} vao ngay {check_date}.")
            continue
        try:
            get_prev_next_date(df, idx_t)
            row_t_minus_1, row_t = df.iloc[idx_t - 1], df.iloc[idx_t]
            buy_rows.append({"code": code, **calculate_buy_scores(symbol, row_t_minus_1, row_t)})


            row_t_next_2, row_t = df.iloc[idx_t + 2], df.iloc[idx_t]
            result_rows.append({"code": code, **calculate_result_scores(symbol, row_t_next_2, row_t)})
        except IndexError as e:
            pass
            # print("❌ Đã xảy ra lỗi: {symbol} {e}")
            # print("👉 Hướng xử lý: Chỉ số vượt quá số hàng hiện có của bảng!")
    
    
    
    buy_df = pd.DataFrame(buy_rows)
    if buy_df.empty:
        print("\nKhong co du lieu.\n")
        return

    if result_rows:
        result_df = pd.DataFrame(result_rows)
        buy_df['|||'] = '|||'
        # result_df = result_df.drop_duplicates(subset=['symbol'])

        buy_df = buy_df.merge(result_df[['symbol', 'Result']], on='symbol', how='left')
    buy_df = buy_df.drop_duplicates(subset=['symbol'])
    buy_df  = buy_df.drop(columns=["code"])
    _print_table(buy_df, limit, order, show_all=show_all)


def build_parser():
    parser = argparse.ArgumentParser(description="Stock scanner command line")
    parser.add_argument("-s", "--symbols-file", default="backup/syb_scan.csv")
    parser.add_argument("-o", "--order", default=1, type=int, help="0: Sort following result, \
                         1: Sort following Same1 (Default), \
                         2: Sort following Same2 \
                        ")
    parser.add_argument("-d", "--date", default=datetime.now().strftime("%d/%m/%Y"), help="Ngay check theo dinh dang dd/mm/yyyy")
    parser.add_argument("-l", "--limit", type=int, default=200, help="So dong toi da moi bang. 0 de in tat ca")
    parser.add_argument("-r", "--refresh", action="store_true", help="Cap nhat them du lieu moi nhat tu web")
    parser.add_argument("-a", "--all", action="store_true", help="show all data, not only the filtered ones")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    while True:
        print(f"\n|||||||||||||||||||||||||||||||||||||||||||||| {args.date} ||||||||||||||||||||||||||||||||||||||||||||||")
        run_cli_scan(
			order=args.order,
			symbols_file=args.symbols_file,
			check_date=args.date,
			limit=args.limit,
			refresh=args.refresh,
			show_all=args.all,
		)
        print("Bấm phím 'n' or right arrow (Tiếp), 'p' or left arrow (Lùi), hoặc any key (Thoát)")
        key = readchar.readkey()
        
		
        current_date = datetime.strptime(args.date, "%d/%m/%Y").date()

        if key == 'n' or key == readchar.key.RIGHT:
            args.date = next_date
        elif key == 'p'  or key == readchar.key.LEFT:
            args.date = prev_date
        else:
            print("Đang thoát chương trình...")
            exit() # Dừng toàn bộ chương trình
        print(args.date)
        if args.date is None:
            args.date = current_date.strftime("%d/%m/%Y")
        args.refresh = None


if __name__ == "__main__":
    main()
