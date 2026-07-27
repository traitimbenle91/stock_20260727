import os
import webbrowser

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from indicator.indicators import add_ema, add_bollinger, add_volume_ma, add_rsi, add_macd


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    chart_df = df.copy()
    chart_df["Date"] = pd.to_datetime(chart_df["Date"], errors="coerce")
    chart_df = chart_df.dropna(subset=["Date", "Open", "High", "Low", "Close", "Volume"]).copy()

    # Chuẩn hóa numeric trước khi tính chỉ báo và vẽ
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        chart_df[col] = pd.to_numeric(chart_df[col], errors="coerce")
    chart_df = chart_df.dropna(subset=["Open", "High", "Low", "Close", "Volume"]).copy()
    chart_df = chart_df.sort_values("Date").reset_index(drop=True)

    add_ema(chart_df, period=10, source_col="Close")
    add_bollinger(chart_df, period=20, std_factor=2.0, source_col="Close")
    add_volume_ma(chart_df, period=20, source_col="Volume")
    add_rsi(chart_df, period=14, source_col="Close")
    add_macd(chart_df, source_col="Close", fast=12, slow=26, signal=9)

    # Điểm mua B khi tổng điểm == 6 trên cùng khung thời gian
    chart_df["BUY_SCORE"] = 0
    red_t1 = (chart_df["Close"].shift(1) < chart_df["Open"].shift(1)).astype(int)
    ema_t1 = (chart_df["Close"].shift(1) < chart_df["EMA10"].shift(1)).astype(int)
    vol_t1 = (chart_df["Volume"].shift(1) < chart_df["VMA20"].shift(1)).astype(int)

    green_t = (chart_df["Close"] >= chart_df["Open"]).astype(int)
    ema_t = (chart_df["Close"] < chart_df["EMA10"]).astype(int)
    vol_t = (chart_df["Volume"] < chart_df["VMA20"]).astype(int)

    chart_df["BUY_SCORE"] = red_t1 + ema_t1 + vol_t1 + green_t + ema_t + vol_t
    chart_df["BUY_SIGNAL"] = chart_df["BUY_SCORE"] == 6

    return chart_df


def build_stock_plotly_figure(symbol: str, df: pd.DataFrame) -> go.Figure:
    chart_df = _prepare_dataframe(df)
    x_values = chart_df["Date"].dt.strftime("%Y-%m-%d")

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.2, 0.15, 0.15],
        subplot_titles=(
            f"{symbol} - Candlestick + EMA10 + Bollinger Bands",
            "Volume + VMA20",
            "RSI(14)",
            "MACD(12,26,9)",
        ),
    )

    # Panel 1: Candlestick + EMA10 + Bollinger
    fig.add_trace(
        go.Candlestick(
            x=x_values,
            open=chart_df["Open"],
            high=chart_df["High"],
            low=chart_df["Low"],
            close=chart_df["Close"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=chart_df["EMA10"],
            mode="lines",
            name="EMA10",
            line=dict(color="#ff8800", width=1.8),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=chart_df["BB_UPPER_20"],
            mode="lines",
            name="BB Upper",
            line=dict(color="#4b6cb7", width=1),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=chart_df["BB_MID_20"],
            mode="lines",
            name="BB Mid",
            line=dict(color="#6a89cc", width=1, dash="dot"),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=chart_df["BB_LOWER_20"],
            mode="lines",
            name="BB Lower",
            line=dict(color="#4b6cb7", width=1),
            fill="tonexty",
            fillcolor="rgba(75,108,183,0.08)",
        ),
        row=1,
        col=1,
    )

    # Đánh dấu điểm mua B màu xanh in đậm khi total score == 6
    buy_df = chart_df[chart_df["BUY_SIGNAL"]]
    if not buy_df.empty:
        fig.add_trace(
            go.Scatter(
                x=buy_df["Date"].dt.strftime("%Y-%m-%d"),
                y=buy_df["Low"] * 0.985,
                mode="text",
                text=["<b>B</b>"] * len(buy_df),
                textfont=dict(color="green", size=16),
                name="Buy (Score=6)",
            ),
            row=1,
            col=1,
        )

    # Panel 2: Volume + VMA20
    volume_colors = [
        "#2ca02c" if c >= o else "#d62728"
        for c, o in zip(chart_df["Close"], chart_df["Open"])
    ]
    fig.add_trace(
        go.Bar(
            x=x_values,
            y=chart_df["Volume"],
            name="Volume",
            marker_color=volume_colors,
            opacity=0.8,
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=chart_df["VMA20"],
            mode="lines",
            name="VMA20",
            line=dict(color="#1f77b4", width=1.6),
        ),
        row=2,
        col=1,
    )

    # Panel 3: RSI
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=chart_df["RSI14"],
            mode="lines",
            name="RSI14",
            line=dict(color="#8e44ad", width=1.8),
        ),
        row=3,
        col=1,
    )
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    # Panel 4: MACD
    hist_colors = ["#2ca02c" if v >= 0 else "#d62728" for v in chart_df["MACD_HIST"]]
    fig.add_trace(
        go.Bar(
            x=x_values,
            y=chart_df["MACD_HIST"],
            name="MACD Hist",
            marker_color=hist_colors,
            opacity=0.7,
        ),
        row=4,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=chart_df["MACD"],
            mode="lines",
            name="MACD",
            line=dict(color="#1f77b4", width=1.5),
        ),
        row=4,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=chart_df["MACD_SIGNAL"],
            mode="lines",
            name="Signal",
            line=dict(color="#ff7f0e", width=1.5),
        ),
        row=4,
        col=1,
    )

    fig.update_layout(
        title=f"{symbol} Technical Chart",
        template="plotly_white",
        height=1050,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
        margin=dict(l=50, r=20, t=70, b=40),
    )

    # Dùng category axis để bỏ khoảng trống ngày không giao dịch (T7/CN/lễ)
    fig.update_xaxes(type="category")

    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])
    fig.update_yaxes(title_text="MACD", row=4, col=1)

    return fig


def show_stock_plotly_chart(symbol: str, df: pd.DataFrame) -> str:
    fig = build_stock_plotly_figure(symbol, df)

    out_dir = os.path.join("uiplotly", "charts")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.abspath(os.path.join(out_dir, f"{symbol}_chart.html"))

    plot_html = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config={"scrollZoom": True, "displaylogo": False},
    )

    full_html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{symbol} Technical Chart</title>
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      height: 100%;
      background: #ffffff;
      font-family: Segoe UI, Tahoma, sans-serif;
    }}
    #wrap {{
      position: relative;
      height: 100vh;
      width: 100vw;
      overflow: hidden;
    }}
    #chart {{
      height: 100%;
      width: 100%;
    }}
    #vzoom-wrap {{
      position: absolute;
      right: 8px;
      top: 84px;
      bottom: 16px;
      width: 34px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255, 255, 255, 0.85);
      border: 1px solid #d8d8d8;
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      z-index: 10;
      user-select: none;
    }}
    #vzoom {{
      writing-mode: bt-lr;
      -webkit-appearance: slider-vertical;
      appearance: slider-vertical;
      width: 18px;
      height: 72%;
      cursor: ns-resize;
    }}
    #vzoom-label {{
      position: absolute;
      top: 8px;
      font-size: 11px;
      color: #444;
      text-align: center;
      width: 100%;
      pointer-events: none;
    }}
  </style>
</head>
<body>
  <div id=\"wrap\">
    <div id=\"chart\">{plot_html}</div>
    <div id=\"vzoom-wrap\" title=\"Vertical zoom for candlestick panel\">
      <div id=\"vzoom-label\">Y Zoom</div>
      <input id=\"vzoom\" type=\"range\" min=\"50\" max=\"300\" value=\"100\" step=\"5\" />
    </div>
  </div>

  <script>
    (function() {{
      var gd = document.querySelector('#chart .js-plotly-plot');
      var slider = document.getElementById('vzoom');
      if (!gd || !slider) return;

      var baseRange = null;

      function captureBaseRange() {{
        var y = gd._fullLayout && gd._fullLayout.yaxis;
        if (!y || !y.range || y.range.length !== 2) return;
        baseRange = [Number(y.range[0]), Number(y.range[1])];
      }}

      function applyVerticalZoom() {{
        if (!baseRange) captureBaseRange();
        if (!baseRange) return;

        var factor = Number(slider.value) / 100;
        var minY = baseRange[0];
        var maxY = baseRange[1];
        var mid = (minY + maxY) / 2;
        var half = (maxY - minY) / 2;

        var newHalf = half / factor;
        var newRange = [mid - newHalf, mid + newHalf];
        Plotly.relayout(gd, {{'yaxis.range': newRange, 'yaxis.autorange': false}});
      }}

      gd.on('plotly_afterplot', function() {{
        if (!baseRange) captureBaseRange();
      }});

      gd.on('plotly_relayout', function(ev) {{
        if (ev && (Object.prototype.hasOwnProperty.call(ev, 'yaxis.autorange') || Object.prototype.hasOwnProperty.call(ev, 'autosize'))) {{
          setTimeout(captureBaseRange, 0);
          slider.value = '100';
        }}
      }});

      slider.addEventListener('input', applyVerticalZoom);
      setTimeout(captureBaseRange, 100);
    }})();
  </script>
</body>
</html>
"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    webbrowser.open(f"file:///{out_path.replace(os.sep, '/')}")
    return out_path
