# My_Survey 問卷式打卡工具

*輕量級表單提交與數據管理系統，基於 Python + Flask + HTTPS*

---

## 目錄

1. [項目概述](#項目概述)
2. [快速開始](#快速開始)
3. [配置指南](#配置指南)
4. [數據存儲結構](#數據存儲結構)
5. [功能詳解](#功能詳解)
6. [API 參考](#api-參考)
7. [安全與權限](#安全與權限)
8. [WebDAV 遠程同步](#webdav-遠程同步)
9. [管理功能](#管理功能)
10. [故障排除](#故障排除)
11. [維護與備份](#維護與備份)

---

## 項目概述

My_Survey 是女性或通用輕量級的表單提交與數據管理系統，適用於打卡、問卷、記錄收集等場景。本實例為 **My_Survey**，可作為獨立部署或雙實例方案的一部分。

### 技術棧

- **後端**: Python 3 + Flask
- **前端**: 單文件 HTML + JavaScript（無框架依賴）
- **傳輸**: HTTPS（自簽名或正式證書）
- **數據存儲**: CSV（易用）+ JSONL（流式）
- **可選擴展**: WebDAV 遠程備份

---

## 快速開始

### 1. 準備工作

確保 Python 3.8+ 和 pip 可用。

```bash
sudo apt update
sudo apt install python3 python3-pip
```

使用 git 下載腳本文件 (如沒有, 請運行 sudo apt install git 安裝):

```bash
git clone https://github.com/tonyjaajaa1467/check-in-tool-My_Survey.git My_Survey
cd My_Survey
```

### 2. 建立新的虛擬環境
```bash
python3 -m venv venv
```

### 3. 啟用虛擬環境
- **在 Bash 或 Zsh 中：**
  ```bash
  source venv/bin/activate
  ```
- **在 Fish shell 中：**
  ```bash
  source venv/bin/activate.fish
  ```
- **在 Windows Command Prompt 中：**
  ```cmd
  venv\Scripts\activate.bat
  ```
- **在 Windows PowerShell 中：**
  ```powershell
  venv\Scripts\Activate.ps1
  ```

啟用成功後，終端機提示符會顯示 `(venv)` 前綴，例如：
```
(venv) tony@host:~/My_Survey$
```

### 4. 安裝依賴套件
```bash
pip install -r requirements.txt
```
`requirements.txt` 檔案目前僅包含 `flask`（核心依賴），但若未來有更新，此步驟會確保安裝所有必要套件。

### 5. 驗證安裝
您可以透過以下指令檢查 Flask 是否已正確安裝：
```bash
pip list | grep flask
```
或執行：
```bash
python -c "import flask; print(flask.__version__)"
```

### 6. 配置環境變數

`.env` 文件至少需要設置：

```bash
DOWNLOAD_PASSWORD=your_download_password
SSL_CERT_PATH=ssl/cert.pem
SSL_KEY_PATH=ssl/key.pem
PORT="5001"
```

### 7. 執行權限 & 啟動服務

```bash
chmod +x run_backend.sh
./run_backend.sh start
```

輸出示例：

```
📁 加載 .env 配置...
🚀 啟動後端...
✅ 後端已啟動 (PID 12345)
📍 路徑: /home/$USER/My_Survey/backend.py
🌐 地址: https://localhost:5001
```

### 8. 訪問頁面

瀏覽器打開 `https://localhost:5001`（首次訪問自簽名證書需手動信任）。

---

## 配置指南

### 環境變數（.env）

| 變數名 | 必需 | 預設 | 說明 |
|--------|------|------|------|
| `DOWNLOAD_PASSWORD` | 是 | — | CSV 下載和導出篩選的密碼 |
| `OPTIONS_PASSWORD` | 否 | — | 編輯 `options.json` 的管理密碼 |
| `FLASK_DEBUG` | 否 | `0` | 調試模式（生產設為 0） |
| `PORT` | 否 | `5001` | 後端監聽埠 |
| `SSL_CERT_PATH` | 否 | `ssl/cert.pem` | SSL 證書路徑 |
| `SSL_KEY_PATH` | 否 | `ssl/key.pem` | SSL 私鑰路徑 |
| `WEBDAV_URL` | 否 | — | WebDAV 伺服器地址（啟用同步） |
| `WEBDAV_USER` | 條件 | — | WebDAV 用戶名（與 URL 同時設置） |
| `WEBDAV_PASS` | 條件 | — | WebDAV 密碼 |
| `WEBDAV_VERIFY` | 否 | `true` | SSL 驗證（自簽名設為 false） |

### 選項配置（static/data/options.json）

```json
{
  "names": ["Tony", "Dan", "Cheng"],
  "statuses": ["On Duty", "Annual Leave", "Sick Leave"],
  "work_types": ["Preventive Maintenance (PM)", "Corrective Maintenance (CM)"],
  "contracts": ["contract_1", "contract_2"]
}
```

修改後刷新頁面即生效。特殊值 `Other_Status`、`Other_Work`、`Other_Contract` 會自動觸發對應的 "Please specify" 文字框。

---

## 數據存儲結構

```
survey_data/
├── submissions.csv    # 扁平化表格（列順序固定）
└── submissions.jsonl  # 逐行 JSON（便於流式處理）
```

### CSV 表頭

```csv
timestamp,name,date,weekend_holiday,session,status,status_specify_others,location,work,work_specify_others,contract_no,contract_specify_others,comments,latitude,longitude,accuracy,region
```

欄位說明：

| 欄位 | 類型 | 說明 |
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
| accuracy | int | GPS 精度（公尺，可選） |
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
- **提交反饋**：綠色成功提示（8秒自動消失），按鈕禁用2秒防重複
- **速率限制**：每IP每小時最多20次提交

### 2. GPS 定位與地址轉換

- 點擊 "📍 獲取當前位置" 調用瀏覽器 Geolocation API
- 支援手動地址輸入，使用 OpenStreetMap Nominatim 轉換為坐標
- 自動反向地理編碼獲取地區名稱（顯示在地圖下方）
- 地圖使用 Leaflet.js 顯示，自動縮放

### 3. 提交記錄面板（Submission Panel）

**打開方式**：點擊主界面 "📊 查看提交記錄" 按鈕（需0.5秒內連續點擊5次，防誤觸）

面板功能：

- **搜尋**：全域關鍵字搜尋（即時防抖300ms）
- **日期範圍篩選**：開始日期 / 結束日期
- **分頁**：每頁20條，可翻頁
- **排序**：點擊表頭（支援日期、中文等）
- **刪除**：每行右側刪除按鈕（需輸入管理密碼）
- **導出篩選結果**：將當前篩選/排序後的數據導出為 CSV（新增）

### 4. 導出篩選結果

在提交記錄面板，設置好搜尋和日期範圍後，點擊 **📥 導出篩選結果** 按鈕。

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
3. 後端驗證密碼 → 讀取 CSV → 應用篩選和排序 → 生成 CSV
4. 瀏覽器自動下載文件，命名格式：
   ```
   submissions_export_20250624_123456_42rows.csv
   ```

**注意**：當前導出在記憶體中生成，適合中小數據量（<10000行）。超大數據集建議使用日期篩選縮小範圍。

---

## API 參考

### 公開介面（無需密碼）

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/` | 返回問卷首頁（HTML） |
| POST | `/submit` | 接收表單提交，寫入 CSV/JSONL |
| GET | `/api/submissions` | 查詢提交記錄，支援 `?start_date=...&end_date=...` |
| GET | `/api/options` | 讀取 `options.json` 配置 |

### 管理介面（需要密碼）

| 方法 | 路徑 | 說明 | 參數/標頭 |
|------|------|------|-----------|
| GET/POST | `/download_csv` | 下載完整 `submissions.csv` | `password` (form/query) |
| POST | `/api/submissions/export` | 導出篩選後的 CSV | JSON body + `password` |
| DELETE | `/api/submissions/<timestamp>` | 刪除單條記錄 | `X-Admin-Password` 或 JSON `password` |
| POST | `/api/options` | 保存 `options.json` 配置 | `X-Admin-Password` 或 JSON `password` |

密碼驗證邏輯：

- 優先使用請求體 JSON 中的 `password` 欄位
- 其次檢查 `X-Admin-Password` 請求標頭
- 比對值為 `OPTIONS_PASSWORD` 或 `DOWNLOAD_PASSWORD`（優先前者）

---

## 安全與權限

- **密碼保護**：所有管理操作需密碼（下載、導出、刪除、配置）
- **IP 速率限制**：每IP每小時最多20次提交（`/submit`）
- **檔案鎖**：`fcntl.flock` 確保 CSV/JSONL 寫入原子性
- **CSRF 防護**：敏感操作需密碼，不在 URL 中傳遞
- **SSL 加密**：強制 HTTPS（自簽名或正式證書）

---

## WebDAV 遠程同步

如果設置了 `WEBDAV_URL`，每次提交成功後會自動將完整的 `submissions.csv` 上傳到遠程伺服器（覆蓋更新）。

配置示例：

```bash
WEBDAV_URL=https://xxx.com
WEBDAV_USER=webdav_user
WEBDAV_PASS=webdav_password
WEBDAV_VERIFY=false   # 自簽名證書需設為 false
```

上傳日誌會列印到後端主控台和 `backend.log`。

---

## 管理功能

### 1. 管理選項設置

點擊右上角 **⚙️ 設定** 按鈕：

- 批量編輯姓名、狀態、工作類型、合約編號列表（每行一個）
- 輸入管理密碼（`OPTIONS_PASSWORD` 或 `DOWNLOAD_PASSWORD`）
- 保存後頁面自動刷新，新選項立即生效
- 修改前自動備份（`.bak.YYYYMMDD_HHMMSS`）

### 2. 下載所有數據

點擊 **📥 下載所有數據 (CSV)** 按鈕，輸入密碼後下載完整 `submissions.csv`。

### 3. 查看與刪除提交記錄

打開提交記錄面板：

- 點擊 **📊 查看提交記錄**（需5次點擊防誤觸）
- 使用搜尋/日期篩選/排序定位記錄
- 點擊行內 **刪除** 按鈕，輸入密碼確認後刪除
- 刪除同時清理 CSV 和 JSONL

---

## 故障排除

| 問題 | 可能原因 | 解決方法 |
|------|----------|----------|
| 無法啟動 | `DOWNLOAD_PASSWORD` 未設置 | 檢查 `.env` 文件 |
| SSL 錯誤 | 證書路徑不正確或過期 | 確認 `ssl/cert.pem` 和 `ssl/key.pem` 存在且有效 |
| 提交失敗 | 磁碟空間不足或權限問題 | 檢查 `survey_data/` 可寫性 |
| 403 下載/導出 | 密碼錯誤 | 確認輸入與 `.env` 一致 |
| WebDAV 上傳失敗 | 網路或憑證錯誤 | 檢查 `WEBDAV_*` 配置與日誌 |
| 選項不更新 | 瀏覽器快取 | 強制刷新 (Ctrl+F5) |

---

## 維護與備份

### 服務管理

```bash
./run_backend.sh start    # 啟動
./run_backend.sh stop     # 停止
./run_backend.sh restart # 重啟
./run_backend.sh status   # 查看狀態
```

### 日誌查看

```bash
tail -f backend.log           # 即時日誌
grep ERROR backend.log        # 尋找錯誤
```

### 備份策略

- **自動備份**：修改 `options.json` 時生成 `.bak` 文件
- **項目備份**：定期複製整個項目目錄或使用 `backup_*/` 歸檔
- **數據導出**：定期使用 "導出篩選結果" 功能下載 CSV 歸檔

### 恢復數據

- **恢復配置**：將 `.bak` 文件重新命名為 `options.json`
- **恢復提交數據**：將備份的 `submissions.csv` 和 `submissions.jsonl` 覆蓋原文件（注意格式一致）

---

## 版本歷史

- **v2026.06.22**：初始版本
- **v2026.06.24**：新增 "導出篩選結果" 功能，按鈕位置調整，密碼使用 `DOWNLOAD_PASSWORD` 驗證

---
