# 重新建立 My_Survey 虛擬環境指南

此文件說明如何為 My_Survey 專案重新建立 Python 虛擬環境（venv），適用於環境損毀、依賴衝突或需要乾淨重來的情況。

## 前提條件
- Python 3.8+ 已安裝且可於終端機中執行 `python3` 指令
- 您位於 My_Survey 專案根目錄（包含 `requirements.txt` 和 `run_backend.sh` 的目錄）

## 步驟

### 1. 進入專案目錄
```bash
cd /home/$USR/My_Survey
```

### 2. 刪除現有的虛擬環境（如果存在）
```bash
rm -rf venv
```
> ⚠️ 此操作會永久刪除 `venv` 目錄及其內所有套件。請確認您不需要保留目前的虛擬環境。

### 3. 建立新的虛擬環境
```bash
python3 -m venv venv
```
此指令會在專案目錄下建立一個名為 `venv` 的新虛擬環境。

### 4. 啟用虛擬環境
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

### 5. 安裝依賴套件
```bash
pip install -r requirements.txt
```
`requirements.txt` 檔案目前僅包含 `flask`（核心依賴），但若未來有更新，此步驟會確保安裝所有必要套件。

### 6. 驗證安裝
您可以透過以下指令檢查 Flask 是否已正確安裝：
```bash
pip list | grep flask
```
或執行：
```bash
python -c "import flask; print(flask.__version__)"
```

### 7. 後續操作
虛擬環境建立完成後，您可以使用專案提供的腳本啟動後端服務：
```bash
./run_backend.sh start
```
該腳本會自動偵測並使用目前啟用的虛擬環境。

## 重要備註
- 每次開啟新終端機視窗時，都需要重新啟用虛擬環境（執行 `source venv/bin/activate`）。
- 若您修改了 `requirements.txt`，請重新執行 `pip install -r requirements.txt` 以更新套件。
- 虛擬環境是專案獨立的，不會影響系統全域的 Python 安裝或其他專案。

## 疑難排解
- **錯誤：`python3: command not found`**  
  請確認您已安裝 Python 3 並將其加入 PATH。在 Ubuntu/Debian 上可執行 `sudo apt install python3-venv`。

- **錯誤：`Error: [Errno 13] Permission denied`**  
  您可能沒有刪除 `venv` 目錄或建立新目錄的權限。請使用 `sudo` 或確認您擁有該目錄的寫入權限。

- **錯誤：`Could not find a version that satisfies the requirement flask`**  
  檢查您的網路連接及 PyPI 可達性。亦可嘗試升級 pip：`pip install --upgrade pip`。

## 參考資料
- Python 官方文件：[venv — 建立虛擬環境](https://docs.python.org/3/library/venv.html)
- pip 使用指南：[pip install - Requirements Files](https://pip.pypa.io/en/stable/reference/requirements-file-format/)

--- 
*此指南最後更新於 $(date '+%Y-%m-%d')，適用於 My_Survey 專案。*