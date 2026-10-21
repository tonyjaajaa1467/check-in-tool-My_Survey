# My_Survey 问卷式打卡工具

*轻量级表单提交与数据管理系统，基于 Flask + HTTPS*

---

## 目录

1. [项目概述](#项目概述)
2. [快速开始](#快速开始)
3. [配置指南](#配置指南)
4. [数据存储结构](#数据存储结构)
5. [功能详解](#功能详解)
6. [API 参考](#api-参考)
7. [安全与权限](#安全与权限)
8. [WebDAV 远程同步](#webdav-远程同步)
9. [管理功能](#管理功能)
10. [故障排除](#故障排除)
11. [维护与备份](#维护与备份)

---

## 项目概述

My_Survey 是一个轻量级的表单提交与数据管理系统，适用于打卡、问卷、记录收集等场景。本实例为 **My_Survey**，可作为独立部署或双实例方案的一部分。

### 技术栈

- **后端**: Python 3 + Flask
- **前端**: 单文件 HTML + JavaScript（无框架依赖）
- **传输**: HTTPS（自签名或正式证书）
- **数据存储**: CSV（易用）+ JSONL（流式）
- **可选扩展**: WebDAV 远程备份

---

## 快速开始

### 1. 准备工作

```bash
cd /home/$USER/My_Survey
```

确保 Python 3.8+ 和 pip 可用。

```bash
sudo apt update
sudo apt install python3 python3-pip
```

### 2. 配置环境变量

复制示例配置并编辑：

```bash
cp .env.example .env
```

`.env` 文件至少需要设置：

```bash
DOWNLOAD_PASSWORD=your_download_password
SSL_CERT_PATH=ssl/cert.pem
SSL_KEY_PATH=ssl/key.pem
PORT="5001"
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
# 或仅安装核心依赖
pip install flask
```

### 4. 启动服务

```bash
./run_backend.sh start
```

输出示例：

```
📁 加载 .env 配置...
🚀 启动后端...
✅ 后端已启动 (PID 12345)
📍 路径: /home/$USER/My_Survey/backend.py
🌐 地址: https://localhost:5001
```

### 5. 访问页面

浏览器打开 `https://localhost:5001`（首次访问自签名证书需手动信任）。

---

## 配置指南

### 环境变量（.env）

| 变量名 | 必需 | 默认 | 说明 |
|--------|------|------|------|
| `DOWNLOAD_PASSWORD` | 是 | — | CSV 下载和导出筛选的密码 |
| `OPTIONS_PASSWORD` | 否 | — | 编辑 `options.json` 的管理密码 |
| `FLASK_DEBUG` | 否 | `0` | 调试模式（生产设为 0） |
| `PORT` | 否 | `5001` | 后端监听端口 |
| `SSL_CERT_PATH` | 否 | `ssl/cert.pem` | SSL 证书路径 |
| `SSL_KEY_PATH` | 否 | `ssl/key.pem` | SSL 私钥路径 |
| `WEBDAV_URL` | 否 | — | WebDAV 服务器地址（启用同步） |
| `WEBDAV_USER` | 条件 | — | WebDAV 用户名（与 URL 同时设置） |
| `WEBDAV_PASS` | 条件 | — | WebDAV 密码 |
| `WEBDAV_VERIFY` | 否 | `true` | SSL 验证（自签名设为 false） |

### 选项配置（static/data/options.json）

```json
{
  "names": ["Tony", "Dan", "Cheng"],
  "statuses": ["On Duty", "Annual Leave", "Sick Leave"],
  "work_types": ["Preventive Maintenance (PM)", "Corrective Maintenance (CM)"],
  "contracts": ["contract_1", "contract_2"]
}
```

修改后刷新页面即生效。特殊值 `Other_Status`、`Other_Work`、`Other_Contract` 会自动触发对应的 "Please specify" 文本框。

---

## 数据存储结构

```
survey_data/
├── submissions.csv    # 扁平化表格（列顺序固定）
└── submissions.jsonl  # 逐行 JSON（便于流式处理）
```

### CSV 表头

```csv
timestamp,name,date,weekend_holiday,session,status,status_specify_others,location,work,work_specify_others,contract_no,contract_specify_others,comments,latitude,longitude,accuracy,region
```

字段说明：

| 字段 | 类型 | 说明 |
|------|------|------|
| timestamp | string | 提交时间（ISO 格式） |
| name | string | 姓名（从 options 选择） |
| date | string | 日期（YYYY-MM-DD） |
| weekend_holiday | string | Weekend/Holiday (Yes/No) |
| session | string | 班次，分号分隔（AM;PM;Night） |
| status | string | 状态 |
| status_specify_others | string | 状态 - Please specify |
| location | string | 位置（In the Office / Outside） |
| work | string | 工作类型 |
| work_specify_others | string | Work - Please specify |
| contract_no | string | 合同编号 |
| contract_specify_others | string | Contract No. - Please specify |
| comments | string | 备注 |
| latitude | float | 纬度（可选） |
| longitude | float | 经度（可选） |
| accuracy | int | GPS 精度（米，可选） |
| region | string | 地区（反向地理编码） |

---

## 功能详解

### 1. 表单填写与提交

- **必填字段**：姓名、日期、周末/假日、班次、状态、位置
- **条件显示**：
  - Status 选 `Other_Status` → 显示状态说明框
  - Work 选 `Other_Work` → 显示工作说明框
  - Contract 选 `Other_Contract` → 显示合同说明框
  - Location 选 `In the Office` → 第7-9项（GPS/Work/Contract）可跳过
- **提交反馈**：绿色成功提示（8秒自动消失），按钮禁用2秒防重复
- **速率限制**：每IP每小时最多20次提交

### 2. GPS 定位与地址转换

- 点击"📍 获取当前位置"调用浏览器 Geolocation API
- 支持手动地址输入，使用 OpenStreetMap Nominatim 转换为坐标
- 自动反向地理编码获取地区名称（显示在地图下方）
- 地图使用 Leaflet.js 显示，自动缩放

### 3. 提交记录面板（Submission Panel）

**打开方式**：点击主界面"📊 查看提交记录"按钮（需0.5秒内连续点击5次，防误触）

面板功能：

- **搜索**：全局关键词搜索（实时防抖300ms）
- **日期范围筛选**：开始日期 / 结束日期
- **分页**：每页20条，可翻页
- **排序**：点击表头（支持日期、中文等）
- **删除**：每行右侧删除按钮（需输入管理密码）
- **导出筛选结果**：将当前筛选/排序后的数据导出为 CSV（新增）

### 4. 导出筛选结果

在提交记录面板，设置好搜索和日期范围后，点击 **📥 导出筛选结果** 按钮。

流程：

1. 弹出密码输入框（输入 `DOWNLOAD_PASSWORD`）
2. 前端发送 POST 请求到 `/api/submissions/export`，Body 包含：
   ```json
   {
     "search": "关键词",
     "start_date": "2025-06-01",
     "end_date": "2025-06-30",
     "sort_field": "date",
     "sort_asc": true,
     "password": "your_password"
   }
   ```
3. 后端验证密码 → 读取 CSV → 应用筛选和排序 → 生成 CSV
4. 浏览器自动下载文件，命名格式：
   ```
   submissions_export_20250624_123456_42rows.csv
   ```

**注意**：当前导出在内存中生成，适合中小数据量（<10000行）。超大数据集建议使用日期筛选缩小范围。

---

## API 参考

### 公开接口（无需密码）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 返回问卷首页（HTML） |
| POST | `/submit` | 接收表单提交，写入 CSV/JSONL |
| GET | `/api/submissions` | 查询提交记录，支持 `?start_date=...&end_date=...` |
| GET | `/api/options` | 读取 `options.json` 配置 |

### 管理接口（需要密码）

| 方法 | 路径 | 说明 | 参数/头部 |
|------|------|------|-----------|
| GET/POST | `/download_csv` | 下载完整 `submissions.csv` | `password` (form/query) |
| POST | `/api/submissions/export` | 导出筛选后的 CSV | JSON body + `password` |
| DELETE | `/api/submissions/<timestamp>` | 删除单条记录 | `X-Admin-Password` 或 JSON `password` |
| POST | `/api/options` | 保存 `options.json` 配置 | `X-Admin-Password` 或 JSON `password` |

密码验证逻辑：

- 优先使用请求体 JSON 中的 `password` 字段
- 其次检查 `X-Admin-Password` 请求头
- 比对值为 `OPTIONS_PASSWORD` 或 `DOWNLOAD_PASSWORD`（优先前者）

---

## 安全与权限

- **密码保护**：所有管理操作需密码（下载、导出、删除、配置）
- **IP 速率限制**：每IP每小时最多20次提交（`/submit`）
- **文件锁**：`fcntl.flock` 确保 CSV/JSONL 写入原子性
- **CSRF 防护**：敏感操作需密码，不在 URL 中传递
- **SSL 加密**：强制 HTTPS（自签名或正式证书）

---

## WebDAV 远程同步

如果设置了 `WEBDAV_URL`，每次提交成功后会自动将完整的 `submissions.csv` 上传到远程服务器（覆盖更新）。

配置示例：

```bash
WEBDAV_URL=https://xxx.com
WEBDAV_USER=webdav_user
WEBDAV_PASS=webdav_password
WEBDAV_VERIFY=false   # 自签名证书需设为 false
```

上传日志会打印到后端控制台和 `backend.log`。

---

## 管理功能

### 1. 管理选项设置

点击右上角 **⚙️ 設定** 按钮：

- 批量编辑姓名、状态、工作类型、合约编号列表（每行一个）
- 输入管理密码（`OPTIONS_PASSWORD` 或 `DOWNLOAD_PASSWORD`）
- 保存后页面自动刷新，新选项立即生效
- 修改前自动备份（`.bak.YYYYMMDD_HHMMSS`）

### 2. 下载所有数据

点击 **📥 下载所有数据 (CSV)** 按钮，输入密码后下载完整 `submissions.csv`。

### 3. 查看与删除提交记录

打开提交记录面板：

- 点击 **📊 查看提交记录**（需5次点击防误触）
- 使用搜索/日期筛选/排序定位记录
- 点击行内 **删除** 按钮，输入密码确认后删除
- 删除同时清理 CSV 和 JSONL

---

## 故障排除

| 问题 | 可能原因 | 解决方法 |
|------|----------|----------|
| 无法启动 | `DOWNLOAD_PASSWORD` 未设置 | 检查 `.env` 文件 |
| SSL 错误 | 证书路径不正确或过期 | 确认 `ssl/cert.pem` 和 `ssl/key.pem` 存在且有效 |
| 提交失败 | 磁盘空间不足或权限问题 | 检查 `survey_data/` 可写性 |
| 403 下载/导出 | 密码错误 | 确认输入与 `.env` 一致 |
| WebDAV 上传失败 | 网络或凭证错误 | 检查 `WEBDAV_*` 配置与日志 |
| 选项不更新 | 浏览器缓存 | 强制刷新 (Ctrl+F5) |

---

## 维护与备份

### 服务管理

```bash
./run_backend.sh start    # 启动
./run_backend.sh stop     # 停止
./run_backend.sh restart # 重启
./run_backend.sh status   # 查看状态
```

### 日志查看

```bash
tail -f backend.log           # 实时日志
grep ERROR backend.log        # 查找错误
```

### 备份策略

- **自动备份**：修改 `options.json` 时生成 `.bak` 文件
- **项目备份**：定期复制整个项目目录或使用 `backup_*/` 归档
- **数据导出**：定期使用"导出筛选结果"功能下载 CSV 归档

### 恢复数据

- **恢复配置**：将 `.bak` 文件重命名为 `options.json`
- **恢复提交数据**：将备份的 `submissions.csv` 和 `submissions.jsonl` 覆盖原文件（注意格式一致）

---

## 版本历史

- **v2026.06.22**：初始版本
- **v2026.06.24**：新增"导出筛选结果"功能，按钮位置调整，密码使用 `DOWNLOAD_PASSWORD` 验证

---

## 许可证

内部使用，未经授权不得外传。
