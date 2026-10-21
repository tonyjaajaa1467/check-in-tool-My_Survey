# My_Survey 問卷式打卡工具

*輕量級表單提交與資料管理系統，基於 Flask + HTTPS*

---

## 目錄

1. [項目概述](#項目概述)
2. [快速開始](#快速開始)
3. [配置指南](#配置指南)
4. [資料儲存結構](#資料儲存結構)
5. [功能詳解](#功能詳解)
6. [API 參考](#api-參考)
7. [安全與權限](#安全與權限)
8. [WebDAV 遠端同步](#webdav-遠端同步)
9. [管理功能](#管理功能)
10. [故障排除](#故障排除)
11. [維護與備份](#維護與備份)

---

## 專案概述

My_Survey 是一個輕量級的表單提交與資料管理系統，適用於打卡、問卷、記錄收集等場景。本實例為 **My_Survey**，可作為獨立部署或雙重實例方案的一部分。

### 技術堆疊

- **後端**: Python 3 + Flask
- **前端**: 單文件 HTML + JavaScript（無框架依賴）
- **傳輸**: HTTPS（自簽名或正式憑證）
- **資料儲存**: CSV（易用）+ JSONL（串流）
- **選用擴充**: WebDAV 遠端備份

---

## 快速開始

### 1. 準備工作

『`bash
cd /home/$USER/My_Survey
```

確保 Python 3.8+ 和 pip 可用。

『`bash
sudo apt update
sudo apt install python3 python3-pip
```

### 2. 設定環境變數

複製範例配置並編輯：

『`bash
cp .env.example .env
```

`.env` 檔案至少需要設定：

『`bash
DOWNLOAD_PASSWORD=your_download_password
SSL_CERT_PATH=ssl/cert.pem
SSL_KEY_PATH=ssl/key.pem
PORT="5001"
```

### 3. 安裝依賴

『`bash
pip install -r requirements.txt
# 或僅安裝核心依賴
pip install flask
```

### 4. 啟動服務

『`bash
./run_backend.sh start
```

輸出範例：

```
📁 載入 .env 配置...
🚀 啟動後端...
✅ 後端已啟動 (PID 12345)
📍 路徑: /home/$USER/My_Survey/backend.py
🌐 位址: https://localhost:5001
```

### 5. 造訪頁面

瀏覽器開啟 `https://localhost:5001`（首次存取自簽名憑證需手動信任）。

---

## 設定指南

### 環境變數（.env）

| 變數名 | 必需 | 預設 | 說明 |
|--------|------|------|------|
| `DOWNLOAD_PASSWORD` | 是 | — | CSV 下載與匯出篩選的密碼 |
| `OPTIONS_PASSWORD` | 否 | — | 編輯 `options.json` 的管理密碼 |
| `FLASK_DEBUG` | 否 | `0` | 調試模式（生產設為 0） |
| `PORT` | 否 | `5001` | 後端監聽埠 |
| `SSL_CERT_PATH` | 否 | `ssl/cert.pem` | SSL 憑證路徑 |
| `SSL_KEY_PATH` | 否 | `ssl/key.pem` | SSL 私鑰路徑 |
| `WEBDAV_URL` | 否 | — | WebDAV 伺服器位址（啟用同步） |
| `WEBDAV_USER` | 條件 | — | WebDAV 使用者名稱（與 URL 同時設定） |
| `WEBDAV_PASS` | 條件 | — | WebDAV 密碼 |
| `WEBDAV_VERIFY` | 否 | `true` | SSL 驗證（自簽章設為 false） |

### 選項配置（static/data/options.json）

```json
{
 "names": ["Tony", "Dan", "Cheng"],
 "statuses": ["On Duty", "Annual Leave", "Sick Leave"],
 "work_types": ["Preventive Maintenance (PM)", "Corrective Maintenance (CM)"],
 "contracts": ["contract_1", "contract_2"]
}
```

修改後刷新頁面即生效。特殊值 `Other_Status`、`Other_Work`、`Other_Contract` 會自動觸發對應的 "Please specify" 文字方塊。

---

## 資料儲存結構

```
survey_data/
├── submissions.csv # 扁平化表格（列順序固定）
└── submissions.jsonl # 逐行 JSON（方便串流處理）
```

### CSV 表頭

```csv
timestamp,name,date,weekend_holiday,session,status,status_specify_others,location,work,work_specify_others,contract_no,contract_specify_others,comments,latitude,longitude,accuracy,region
```

字段說明：

| 字段 | 類型 | 說明 |
|------|------|------|
| timestamp | string | 提交時間（ISO 格式） |
| name | string | 姓名（從 options 選擇） |
| date | string | 日期（YYYY-MM-DD） |
| weekend_holiday | string | Weekend/Holiday (Yes/No) |
| session | string | 班次，分號分隔（AM;PM;Night） |
| status | string | 狀態 |
| status_specify_others | string | 狀態 - Please specify |
| location | string | 位置（In the Office / Outside） |
| work | string | 工作類型 |
| work_specify_others | string | Work - Please specify |
| contract_no | string | 合約編號 |
| contract_specify_others | string | Contract No. - Please specify |
| comments | string | 備註 |
| latitude | float | 緯度（可選） |
| longitude | float | 經度（可選） |
| accuracy | int | GPS 精準度（米，可選） |
| region | string | 地區（反向地理編碼） |

---

## 功能詳解

### 1. 表單填寫與提交

- **必填欄位**：姓名、日期、週末/假日、班次、狀態、位置
- **條件顯示**：
 - Status 選 `Other_Status` → 顯示狀態說明框
 - Work 選 `Other_Work` → 顯示工作說明框
 - Contract 選 `Other_Contract` → 顯示合約說明框
 - Location 選 `In the Office` → 第7-9項（GPS/Work/Contract）可跳過
- **提交回饋**：綠色成功提示（8秒自動消失），按鈕停用2秒防重複
- **速率限制**：每IP每小時最多20次提交

### 2. GPS 定位與位址轉換

- 點選"📍 取得目前位置"呼叫瀏覽器 Geolocation API
- 支援手動位址輸入，使用 OpenStreetMap Nominatim 轉換為座標
- 自動反向地理編碼取得地區名稱（顯示在地圖下方）
- 地圖使用 Leaflet.js 顯示，自動縮放

### 3. 提交記錄面板（Submission Panel）

**開啟方式**：點選主介面"📊 查看提交記錄"按鈕（需0.5秒內連續點擊5次，防誤觸）

面板功能：

- **搜尋**：全域關鍵字搜尋（即時防手震300ms）
- **日期範圍篩選**：開始日期 / 結束日期
- **分頁**：每頁20條，可翻頁
- **排序**：點選表格頭（支援日期、中文等）
- **刪除**：每行右側刪除按鈕（需輸入管理密碼）
- **匯出篩選結果**：將目前篩選/排序後的資料匯出為 CSV（新增）

### 4. 匯出篩選結果

在提交記錄面板，設定好搜尋和日期範圍後，點擊 **📥 匯出篩選結果** 按鈕。

流程：

1. 彈出密碼輸入框（輸入 `DOWNLOAD_PASSWORD`）
2. 前端發送 POST 請求到 `/api/submissions/export`，Body 包含：
 ```json
 {
 "search": "關鍵字",
 "start_date": "2025-06-01",
 "end_date": "2025-06-30",
 "sort_field": "date",
 "sort_asc": true,
 "password": "your_password"
 }
 ```
3. 後端驗證密碼 → 讀取 CSV → 應用篩選與排序 → 產生 CSV
4. 瀏覽器自動下載文件，命名格式：
 ```
 submissions_export_20250624_123456_42rows.csv
 ```

**注意**：目前匯出在記憶體中生成，適合中小資料量（<10000行）。超大資料集建議使用日期篩選縮小範圍。

---

## API 參考

### 公開介面（無需密碼）

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/` | 回傳問卷首頁（HTML） |
| POST | `/submit` | 接收表單提交，寫入 CSV/JSONL |
| GET | `/api/submissions` | 查詢提交記錄，支援 `?start_date=...&end_date=...` |
| GET | `/api/options` | 讀取 `options.json` 設定 |

### 管理介面（需要密碼）

| 方法 | 路徑 | 說明 | 參數/頭部 |
|------|------|------|-----------|
| GET/POST | `/download_csv` | 下載完整 `submissions.csv` | `password` (form/query) |
| POST | `/api/submissions/export` | 匯出篩選後的 CSV | JSON body + `password` |
| DELETE | `/api/submissions/<timestamp>` | 刪除單一記錄 | `X-Ad
