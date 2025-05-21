from flask import Flask, render_template, request
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error
from plotly.subplots import make_subplots
from gpt_explainer import generate_insight_text
import plotly.graph_objs as go
import os

app = Flask(__name__)

def fetch_yahoo_ohlc(symbol, interval="1d", start=None, end=None):
    start_ts = int(pd.to_datetime(start).timestamp())
    end_ts = int(pd.to_datetime(end).timestamp())
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&period1={start_ts}&period2={end_ts}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    data = response.json()
    try:
        timestamps = data["chart"]["result"][0]["timestamp"]
        indicators = data["chart"]["result"][0]["indicators"]["quote"][0]
        df = pd.DataFrame({
            "Date": pd.to_datetime(timestamps, unit="s"),
            "Open": indicators["open"],
            "High": indicators["high"],
            "Low": indicators["low"],
            "Close": indicators["close"]
        }).dropna()
        df.set_index("Date", inplace=True)
        return df
    except:
        return pd.DataFrame()

def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_kd(df, n=9):
    low_min = df['Low'].rolling(n).min()
    high_max = df['High'].rolling(n).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
    df['K'] = rsv.ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()

def calculate_macd(df, fast=12, slow=26, signal=9):
    ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
    df['MACD'] = ema_fast - ema_slow
    df['Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()

@app.route('/')
def home():
    return render_template('index_advanced.html')
from math import sqrt
@app.route('/predict', methods=['POST'])
def predict():
    symbol = request.form['symbol']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    interval = request.form['interval']
    forecast_days = int(request.form['forecast_days'])

    df = fetch_yahoo_ohlc(symbol, interval, start=start_date, end=end_date)
    df['Date_ordinal'] = df.index.map(datetime.toordinal)
    X = df['Date_ordinal'].values.reshape(-1, 1)
    y = df['Close'].values.reshape(-1, 1)

    future_dates = pd.date_range(df.index[-1], periods=forecast_days + 1, freq='D')[1:]
    future_ordinals = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
    future_dates_str = [d.strftime('%Y-%m-%d') for d in future_dates]

    models = {
        "線性回歸": LinearRegression(),
        "隨機森林": RandomForestRegressor(),
        "SVR": SVR()
    }

    predictions = {}
    rmses = {}
    for name, model in models.items():
        model.fit(X, y.ravel())
        predictions[name] = model.predict(future_ordinals)
        rmses[name] = sqrt(mean_squared_error(y, model.predict(X))) 
    # 預測表格資料
    df_future = pd.DataFrame({'Date': future_dates_str})
    for name, pred in predictions.items():
        df_future[name] = pred

# 轉換為 HTML 表格
    prediction_table = df_future.to_html(classes="table", index=False)

    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    golden = (df['MA20'] > df['MA60']) & (df['MA20'].shift(1) <= df['MA60'].shift(1))
    death = (df['MA20'] < df['MA60']) & (df['MA20'].shift(1) >= df['MA60'].shift(1))
    df['RSI'] = calculate_rsi(df['Close'])
    calculate_kd(df)
    calculate_macd(df)

    support = df['Low'][-20:].min()
    resistance = df['High'][-20:].max()
    ai_insight = generate_insight_text(
    df,
    predictions,
    df['RSI'].iloc[-1],
    df['MACD'],
    df['Signal'],
    support,
    resistance
)

    
    subplot_titles = ["K 線圖"]
    subplot_rows = 1
    if request.form.get("show_rsi"):
        subplot_titles.append("RSI")
        subplot_rows += 1
    if request.form.get("show_kd"):
        subplot_titles.append("KD")
        subplot_rows += 1
    if request.form.get("show_macd"):
        subplot_titles.append("MACD")
        subplot_rows += 1

    fig = make_subplots(
        rows=subplot_rows, cols=1, shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.6] + [0.13] * (subplot_rows - 1),
        subplot_titles=subplot_titles
    )

    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name="K 線圖", increasing_line_color="green", decreasing_line_color="red"
    ), row=1, col=1)

    for name, pred in predictions.items():
        fig.add_trace(go.Scatter(
            x=future_dates_str, y=pred, name=f"{name} 預測", mode="lines+markers", line=dict(dash="dot")
        ), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name="MA20", line=dict(dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], name="MA60", line=dict(dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(
    x=df.index[golden],
    y=df['Close'][golden],
    mode='markers+text',
    name='🟢 買進 (黃金交叉)',
    marker=dict(symbol='triangle-up', color='limegreen', size=14),
    hovertemplate='黃金交叉：%{x}<br>收盤價：%{y:.2f}<extra></extra>'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
    x=df.index[death],
    y=df['Close'][death],
    mode='markers+text',
    name='🔴 賣出 (死亡交叉)',
    marker=dict(symbol='triangle-down', color='crimson', size=14),
    hovertemplate='死亡交叉：%{x}<br>收盤價：%{y:.2f}<extra></extra>'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=[df.index[0], df.index[-1]], y=[support, support], name="支撐區", line=dict(dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=[df.index[0], df.index[-1]], y=[resistance, resistance], name="壓力區", line=dict(dash="dot")), row=1, col=1)

    row_idx = 2
    if request.form.get("show_rsi"):
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI", line=dict(color="darkcyan")), row=row_idx, col=1)
        row_idx += 1
    if request.form.get("show_kd"):
        fig.add_trace(go.Scatter(x=df.index, y=df["K"], name="%K", line=dict(color="orange")), row=row_idx, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["D"], name="%D", line=dict(color="brown")), row=row_idx, col=1)
        row_idx += 1
    if request.form.get("show_macd"):
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD", line=dict(color="blue")), row=row_idx, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["Signal"], name="Signal", line=dict(color="red")), row=row_idx, col=1)

    fig.update_layout(
    title=f"{symbol} 預測圖",
    template='plotly_white',
    hovermode='x unified',
    dragmode=False,                       # ❌ 禁用拖曳
    xaxis_rangeslider_visible=False,      # ❌ 移除下方時間軸拉條
    height=900,
    width=1000
)

    fig.write_html("static/chart.html", include_plotlyjs='cdn')

    return render_template("result_advanced_interactive.html", 
                       symbol=symbol, 
                       rmses=rmses,
                       prediction_table=prediction_table,
                       ai_insight=ai_insight)


if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(host='0.0.0.0', port=5050, debug=True)
