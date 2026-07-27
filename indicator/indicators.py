import pandas as pd
import numpy as np


def add_ma(df, period=20, source_col="Close"):
    """
    Tính Moving Average (MA).
    
    Args:
        df: DataFrame chứa dữ liệu
        period: Kỳ hạn tính MA (mặc định 20)
        source_col: Cột dữ liệu nguồn (mặc định "Close")
    
    Returns:
        Tên cột MA được thêm vào df
    """
    col_name = f"MA{period}"
    df[col_name] = df[source_col].rolling(window=period).mean()
    return col_name


def add_ema(df, period=20, source_col="Close"):
    """
    Tính Exponential Moving Average (EMA).
    
    Args:
        df: DataFrame chứa dữ liệu
        period: Kỳ hạn tính EMA (mặc định 20)
        source_col: Cột dữ liệu nguồn (mặc định "Close")
    
    Returns:
        Tên cột EMA được thêm vào df
    """
    col_name = f"EMA{period}"
    df[col_name] = df[source_col].ewm(span=period, adjust=False).mean()
    return col_name


def add_volume_ma(df, period=20, source_col="Volume"):
    """
    Tính Moving Average của Volume (VMA).
    
    Args:
        df: DataFrame chứa dữ liệu
        period: Kỳ hạn tính VMA (mặc định 20)
        source_col: Cột dữ liệu nguồn (mặc định "Volume")
    
    Returns:
        Tên cột VMA được thêm vào df
    """
    col_name = f"VMA{period}"
    df[col_name] = df[source_col].rolling(window=period).mean()
    return col_name


def add_bollinger(df, period=20, std_factor=2.0, source_col="Close"):
    """
    Tính Bollinger Bands.
    
    Args:
        df: DataFrame chứa dữ liệu
        period: Kỳ hạn tính Bollinger (mặc định 20)
        std_factor: Hệ số độ lệch chuẩn (mặc định 2.0)
        source_col: Cột dữ liệu nguồn (mặc định "Close")
    
    Returns:
        Tuple gồm (ma_col, upper_col, lower_col)
    """
    ma_col = f"BB_MID_{period}"
    up_col = f"BB_UPPER_{period}"
    low_col = f"BB_LOWER_{period}"

    rolling_mean = df[source_col].rolling(window=period).mean()
    rolling_std = df[source_col].rolling(window=period).std()

    df[ma_col] = rolling_mean
    df[up_col] = rolling_mean + (rolling_std * std_factor)
    df[low_col] = rolling_mean - (rolling_std * std_factor)
    return ma_col, up_col, low_col


def add_rsi(df, period=14, source_col="Close"):
    """
    Tính Relative Strength Index (RSI).
    
    Args:
        df: DataFrame chứa dữ liệu
        period: Kỳ hạn tính RSI (mặc định 14)
        source_col: Cột dữ liệu nguồn (mặc định "Close")
    
    Returns:
        Tên cột RSI được thêm vào df
    """
    col_name = f"RSI{period}"
    delta = df[source_col].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    df[col_name] = 100 - (100 / (1 + rs))
    return col_name


def add_macd(df, source_col="Close", fast=12, slow=26, signal=9):
    """
    Tính MACD (Moving Average Convergence Divergence).
    
    Args:
        df: DataFrame chứa dữ liệu
        source_col: Cột dữ liệu nguồn (mặc định "Close")
        fast: Kỳ hạn EMA nhanh (mặc định 12)
        slow: Kỳ hạn EMA chậm (mặc định 26)
        signal: Kỳ hạn tính đường signal (mặc định 9)
    
    Returns:
        Tuple gồm (macd_col, signal_col, hist_col)
    """
    macd_col = "MACD"
    signal_col = "MACD_SIGNAL"
    hist_col = "MACD_HIST"

    fast_ema = df[source_col].ewm(span=fast, adjust=False).mean()
    slow_ema = df[source_col].ewm(span=slow, adjust=False).mean()

    df[macd_col] = fast_ema - slow_ema
    df[signal_col] = df[macd_col].ewm(span=signal, adjust=False).mean()
    df[hist_col] = df[macd_col] - df[signal_col]
    return macd_col, signal_col, hist_col
