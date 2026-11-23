# WanderDesk｜旅遊探索與行前情報站

WanderDesk 是一個使用 Python 3.11+、Flask 與 Jinja2 製作的繁體中文旅遊資訊整合網站。使用者可以搜尋城市及天氣、探索目的地相關書目，並使用匯率換算器估算旅費。頁面以伺服器端模板呈現，匯率換算示範原生 JavaScript `fetch` 呼叫 Flask JSON API。

## 功能

- 城市地理編碼搜尋最多五筆地點，供選擇同名城市。
- 顯示地點國家、座標、目前氣溫、體感、濕度、風速，以及未來七日最高／最低溫。
- 依城市或自訂關鍵字搜尋最多九筆書目，顯示作者、出版年、前三個主題、封面及 Open Library 詳情連結。
- 支援 Frankfurter 幣別清單與匯率換算，預設包含台幣及常見旅遊幣別。
- 外部 HTTP 請求設有 8 秒逾時；短期快取存在記憶體中。快取不是永久儲存，Serverless 執行個體回收後會清除。
- 響應式卡片排版，手機與桌面皆可使用。

## 專案結構

```text
.
├── api/
│   └── index.py              # Flask 應用程式與 Vercel 進入點
├── services/
│   ├── __init__.py
│   ├── common.py             # HTTP 請求、逾時與記憶體 TTL 快取
│   ├── weather_service.py   # Open-Meteo
│   ├── book_service.py      # Open Library
│   └── currency_service.py  # Frankfurter
├── static/style.css          # 本機 Flask 靜態樣式
├── public/style.css          # Vercel CDN 靜態樣式
├── templates/
│   ├── base.html
│   └── index.html
├── .gitignore
├── .python-version
├── requirements.txt
├── vercel.json
└── README.md
```

## 本機啟動

建議使用 Python 3.11 或更新版本。在專案根目錄執行：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
```

macOS／Linux：

```bash
source .venv/bin/activate
```

安裝依賴並啟動 Flask：

```bash
pip install -r requirements.txt
flask --app api.index run --debug
```

瀏覽 <http://127.0.0.1:5000>。外部服務需要可連線的網路；若服務暫時無回應，頁面會顯示繁體中文錯誤訊息。

## API 路由

- `GET /`：首頁。
- `POST /explore`：以傳統表單查天氣或書籍，回傳伺服器渲染頁面。
- `GET /api/currencies`：取得支援幣別清單。
- `GET /api/convert?amount=1000&from=TWD&to=JPY`：取得 JSON 匯率換算結果。

## 資料來源與授權

- 天氣及地理編碼： [Open-Meteo Forecast API](https://open-meteo.com/en/docs)、[Geocoding API](https://open-meteo.com/en/docs/geocoding-api)。頁面依需求標註 **Data by Open-Meteo.com (CC BY 4.0)**；使用資料時請遵守 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 條款。
- 書目及封面： [Open Library Search API](https://openlibrary.org/developers/api) 與 [Covers API](https://openlibrary.org/dev/docs/api/covers)。書目頁連結至 Open Library 詳情頁。
- 匯率： [Frankfurter API](https://frankfurter.dev/)，屬參考匯率，並非即時交易報價。

## 從 GitHub 匯入 Vercel 部署

1. 將整個專案推送到 GitHub repository，確認 `api/`、`services/`、`templates/`、`public/`、`requirements.txt` 與 `vercel.json` 都已提交。
2. 登入 [Vercel](https://vercel.com/)，選擇 **Add New → Project**，匯入該 GitHub repository。
3. Framework Preset 選 **Flask**（若 Vercel 已自動偵測則保留偵測結果）；專案入口 `api/index.py` 匯出 Flask WSGI app，Vercel 會將請求交由 Flask 路由處理，不需要自訂 rewrite 或 `functions` 路徑規則。
4. 依 `requirements.txt` 安裝 Flask 與 Requests，然後選擇 **Deploy**。專案不需要資料庫或 API key。
5. 部署完成後開啟 Vercel 提供的網址，試用城市搜尋、書籍搜尋及匯率換算。之後推送到連接的 GitHub 分支即可觸發重新部署。

`vercel.json` 僅保留 schema 宣告，避免設定未被 Flask 專案使用的 Serverless Function 路徑。Vercel 會由根目錄 `public/` 提供 CSS；本機 Flask 則透過 `/style.css` 路由提供相同樣式。記憶體快取只在單一暖執行個體期間有效；部署平台可在不同請求間建立或回收執行個體。
