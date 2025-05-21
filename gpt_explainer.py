def generate_insight_text(df, predictions, rsi_value, macd_series, signal_series, support, resistance):
    insight = "📊 AI 助理觀察建議：\n"

    # 價格位置判斷（支撐壓力）
    latest_price = df['Close'].iloc[-1]
    if latest_price > resistance:
        insight += "目前股價逼近壓力區，需留意可能回檔。\n"
    elif latest_price < support:
        insight += "目前股價接近支撐區，可能有反彈機會。\n"
    else:
        insight += "股價位於支撐與壓力區之間，處於觀望區。\n"

    # RSI 解釋
    if rsi_value > 70:
        insight += "RSI 顯示市場可能過熱，有短期回檔風險。\n"
    elif rsi_value < 30:
        insight += "RSI 顯示市場處於超賣狀態，可能醞釀反彈。\n"
    else:
        insight += "RSI 處於中性，尚無明確方向。\n"

    # MACD 判斷（交叉）
    if macd_series.iloc[-1] > signal_series.iloc[-1] and macd_series.iloc[-2] <= signal_series.iloc[-2]:
        insight += "MACD 出現黃金交叉，有可能展開多頭趨勢。\n"
    elif macd_series.iloc[-1] < signal_series.iloc[-1] and macd_series.iloc[-2] >= signal_series.iloc[-2]:
        insight += "MACD 出現死亡交叉，需留意可能轉弱。\n"
    else:
        insight += "MACD 尚未出現明確交叉訊號。\n"

    # 預測偏差最大日分析（以線性回歸為主）
    if "線性回歸" in predictions:
        linear_pred = predictions["線性回歸"]
        actuals = df['Close'].iloc[-len(linear_pred):].values
        if len(actuals) == len(linear_pred):
            diffs = abs(actuals - linear_pred)
            max_idx = diffs.argmax()
            max_diff = diffs[max_idx]
            max_date = df.index[-len(linear_pred):][max_idx].strftime("%Y-%m-%d")
            insight += f"⚠️ 模型在 {max_date} 預測誤差最大，與實際收盤價差距約 {max_diff:.2f} 元。\n"

    # 結論綜合建議（偏多/觀望/偏空）
    if rsi_value < 30 and macd_series.iloc[-1] > signal_series.iloc[-1]:
        insight += "\n✅ 綜合評估：技術指標偏多，後市可偏多觀察。\n"
    elif rsi_value > 70 and macd_series.iloc[-1] < signal_series.iloc[-1]:
        insight += "\n⚠️ 綜合評估：技術指標偏空，建議保守應對。\n"
    else:
        insight += "\nℹ️ 綜合評估：尚無明確訊號，可續觀望。\n"

    return insight
