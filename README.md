雲端股市預測系統 — 說明文件
 專案簡介
此程式碼為我的雲端股市開發系統，結合 Azure 所學，實作一個部署在虛擬機（VM）中的網頁式股價預測服務。
🔧 系統功能說明
1.	1. 多模型預測
使用線性回歸、隨機森林與 SVR 三種模型預測股價，並顯示 RMSE 供比較。
2.	2. 資料來源與預處理
從 Yahoo Finance 下載 OHLC 數據，支援日線、週線、月線，並轉換日期為序數。
3.	3. 技術指標計算
自動計算 MA20/MA60、RSI、KD、MACD，並偵測黃金交叉與死亡交叉。
4.	4. 預測與結果展示
K 線圖、預測曲線與均線圖，表格顯示各模型預測值，並整合 AI 助理解讀。
5.	5. 互動與視覺化
使用者可選擇是否顯示 RSI/KD/MACD，並支援 Plotly 動態圖表。
6.	6. 決策輔助
自動分析預測偏差最大日，並根據技術指標給出偏多/觀望/偏空建議。
專案檔案與目錄結構

stock_predictor/
├── app.py                     # 主程式：Flask Web 應用與預測邏輯
├── templates/
│   ├── index_advanced.html    # 使用者輸入頁面
│   └── result_advanced_interactive.html  # 結果與圖表顯示頁
├── static/
│   └── chart.html             # 預測圖表 (由 Plotly 動態產生)
├── gpt_explainer.py          # AI 助理解釋模組
├── requirements.txt          # Python 相依套件
└── upload_to_blob.py         # 上傳 chart.html 至 Azure Blob 的腳本

使用與部署說明
1. 建立 Azure VM 虛擬機並部署應用：

- 建立 Azure VM（Linux，Ubuntu 22.04）並開通 22 與 5050 port。
- 使用 SCP 或 Git 將 stock_predictor 專案上傳至 VM。
- SSH 登入後安裝相依套件並執行 python3 app.py 啟動 Flask 應用。

2. 建立 Azure Blob 儲存體帳戶並設定公開容器：

- 建立儲存帳戶，選 Azure Blob 儲存體服務，開啟「所有網路皆可讀取」。
- 建立容器，設為公開讀取層級（容器）。
- 使用 upload_to_blob.py 將 static/chart.html 上傳。

3. 學生專案應用建議：

本專案運用技巧：結合「虛擬化服務（VM）」與「雲端儲存服務（Blob Storage）」，
展示實務開發與 Azure 雲端整合成果。


