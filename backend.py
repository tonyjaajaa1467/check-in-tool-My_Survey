#!/usr/bin/env python3
"""
问卷后端收集服务器
功能：接收表单提交，储存至 CSV 和 JSONL，可选上传至 WebDAV
"""

import os
import json
import csv
import io
from datetime import datetime
from flask import Flask, request, jsonify, send_file, Response
import time
import fcntl

app = Flask(__name__)
rate_limit_store = {}  # IP 速率限制存储

# ================= 配置 =================
# 数据储存路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'survey_data')
os.makedirs(DATA_DIR, exist_ok=True)
CSV_FILE = os.path.join(DATA_DIR, 'submissions.csv')
JSONL_FILE = os.path.join(DATA_DIR, 'submissions.jsonl')

# 下载 CSV 的密码（必须通过环境变量设置，无默认值）
DOWNLOAD_PASSWORD = os.getenv('DOWNLOAD_PASSWORD')
if not DOWNLOAD_PASSWORD:
    raise RuntimeError("DOWNLOAD_PASSWORD 环境变数未设置，请设置后重新启动")

# WebDAV 配置（通过环境变量设置）
WEBDAV_URL = os.getenv('WEBDAV_URL', '')  # 从环境变量读取，空字符串表示禁用
WEBDAV_USER = os.getenv('WEBDAV_USER')
WEBDAV_PASS = os.getenv('WEBDAV_PASS')

# ================= 初始化 CSV =================
def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'name', 'date', 'weekend_holiday', 'session',
                'status', 'status_specify_others', 'location', 'work',
                'work_specify_others', 'contract_no', 'contract_specify_others',
                'comments', 'latitude', 'longitude', 'accuracy', 'region'
            ])

# ================= WebDAV 上传函数 =================
def upload_to_webdav(content_bytes: bytes, filename: str, content_type='application/json') -> tuple:
    """
    上传文件到 WebDAV 服务器
    返回 (成功, 消息)
    """
    if not all([WEBDAV_URL, WEBDAV_USER, WEBDAV_PASS]):
        return False, "WebDAV 未配置"
    try:
        import requests
        remote_url = f"{WEBDAV_URL.rstrip('/')}/{filename}"
        # SSL 验证：默认 True，可通过环境变量 WEBDAV_VERIFY 设置为 False（仅用于测试自签名）
        verify = os.getenv('WEBDAV_VERIFY', 'true').lower() != 'false'
        resp = requests.put(
            remote_url,
            data=content_bytes,
            auth=requests.auth.HTTPBasicAuth(WEBDAV_USER, WEBDAV_PASS),
            headers={'Content-Type': content_type},
            timeout=30,
            verify=verify
        )
        if resp.status_code in (200, 201, 204):
            return True, "上传成功"
        else:
            return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
    except Exception as e:
        return False, str(e)

# ================= 路由 =================


@app.route('/api/submissions')
def get_submissions():
    """获取提交的数据（可按日期范围筛选）"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    date_filter = request.args.get('date')  # 兼容旧参数
    if not os.path.exists(CSV_FILE):
        return jsonify({'success': False, 'error': '暂无提交数据', 'total': 0, 'rows': []}), 404
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # 按日期筛选
    if start_date or end_date:
        rows = [row for row in rows if (not start_date or row.get('date', '') >= start_date) and (not end_date or row.get('date', '') <= end_date)]
    elif date_filter:
        rows = [row for row in rows if row.get('date') == date_filter]
    
    return jsonify({
        'success': True,
        'total': len(rows),
        'date': date_filter or (start_date + ' ~ ' + end_date if start_date and end_date else ''),
        'rows': rows
    })

@app.route('/')
def index():
    """提供问卷首页"""
    return send_file(os.path.join(BASE_DIR, 'questionnaire.html'))

@app.route('/submit', methods=['POST'])
def submit():
    """接收表单提交"""
    # 速率限制检查（每个IP每小时最多20次提交）
    ip = request.remote_addr or request.headers.get('X-Forwarded-For', '127.0.0.1')
    now = time.time()
    window = 3600  # 1小时
    limit = 20      # 每个IP每窗口最多提交次数
    # 清理过期条目
    for stored_ip, (reset_ts, count) in list(rate_limit_store.items()):
        if now > reset_ts + window:
            del rate_limit_store[stored_ip]
    if ip in rate_limit_store:
        reset_ts, count = rate_limit_store[ip]
        if now > reset_ts + window:
            rate_limit_store[ip] = (now, 1)
        else:
            if count >= limit:
                return jsonify({'success': False, 'error': '请求过于频繁，请稍后再试'}), 429
            rate_limit_store[ip] = (reset_ts, count + 1)
    else:
        rate_limit_store[ip] = (now, 1)
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无 JSON 数据'}), 400

        timestamp = datetime.now().isoformat(sep=' ', timespec='seconds')
        
        # 准备 CSV 行
        csv_row = [
            timestamp,
            data.get('name', '').strip(),
            data.get('date', ''),
            data.get('weekend_holiday', ''),
            ';'.join(data.get('session', [])),
            data.get('status', ''),
            data.get('status_specify_others', '').strip(),
            ';'.join(data.get('location', [])) if isinstance(data.get('location'), list) else data.get('location', ''),
            data.get('work', ''),
            data.get('work_specify_others', '').strip(),
            data.get('contract_no', ''),
            data.get('contract_specify_others', '').strip(),
            data.get('comments', '').strip(),
            data.get('latitude', ''),
            data.get('longitude', ''),
            data.get('accuracy', ''),
            data.get('region', '')
        ]

        webdav_result = None
        webdav_result = None
        # 写入 CSV（追加，带文件锁和原子持久化）
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                writer = csv.writer(f)
                writer.writerow(csv_row)
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        # 同步上传整个 CSV 文件到 WebDAV（覆盖最新版本）
        # 同步上传整个 CSV 文件到 WebDAV（覆盖最新版本）
        if WEBDAV_URL:
            try:
                with open(CSV_FILE, 'rb') as f_csv:
                    csv_bytes = f_csv.read()
                success_csv, msg_csv = upload_to_webdav(csv_bytes, 'submissions.csv', 'text/csv')
                print(f"[WebDAV] 上传CSV: success={success_csv}, message={msg_csv}", flush=True)
                webdav_result = {'success': success_csv, 'message': msg_csv}
            except Exception as e:
                webdav_result = {'success': False, 'message': str(e)}
                print(f"[WebDAV] 上传CSV异常: {e}", flush=True)

        # 写入 JSONL（每行一条 JSON）
        jsonl_line = json.dumps({
            'timestamp': timestamp,
            'name': data.get('name', ''),
            'date': data.get('date', ''),
            'weekend_holiday': data.get('weekend_holiday', ''),
            'session': data.get('session', []),
            'status': data.get('status', ''),
            'status_specify_others': data.get('status_specify_others', ''),
            'location': data.get('location', ''),
            'work': data.get('work', ''),
            'work_specify_others': data.get('work_specify_others', ''),
            'contract_no': data.get('contract_no', ''),
            'contract_specify_others': data.get('contract_specify_others', ''),
            'comments': data.get('comments', ''), 'latitude': data.get('latitude', ''), 'longitude': data.get('longitude', ''), 'accuracy': data.get('accuracy', ''), 'region': data.get('region', '')
        }, ensure_ascii=False)
        # 写入 JSONL（每行一条 JSON，带文件锁和原子持久化）
        with open(JSONL_FILE, 'a', encoding='utf-8') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(jsonl_line + '\n')
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)



        return jsonify({
            'success': True,
            'local_saved': True,
            'webdav': webdav_result or '未启用',
            'submission_id': timestamp
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ================= 管理界面（可选） =================

@app.route('/api/options', methods=['GET'])
def get_options():
    """读取 options.json 配置"""
    options_path = os.path.join(BASE_DIR, 'static', 'data', 'options.json')
    if not os.path.exists(options_path):
        return jsonify({'success': False, 'error': '配置文件不存在'}), 404
    try:
        with open(options_path, 'r', encoding='utf-8') as f:
            options = json.load(f)
        return jsonify({'success': True, 'options': options})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/options', methods=['POST'])
def update_options():
    """保存 options.json 配置（密码保护）"""
    # 密码验证：优先使用 OPTIONS_PASSWORD，否则退回 DOWNLOAD_PASSWORD
    pwd = request.headers.get('X-Admin-Password') or request.form.get('password', '')
    options_password = os.getenv('OPTIONS_PASSWORD', DOWNLOAD_PASSWORD)
    if options_password and pwd != options_password:
        return jsonify({'success': False, 'error': '密码错误或未提供'}), 403
    try:
        new_options = request.get_json()
        if not isinstance(new_options, dict):
            return jsonify({'success': False, 'error': '无效的数据格式'}), 400
        options_path = os.path.join(BASE_DIR, 'static', 'data', 'options.json')
        # 备份原文件
        if os.path.exists(options_path):
            backup_path = options_path + f'.bak.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            import shutil
            shutil.copy2(options_path, backup_path)
        # 写入新配置
        with open(options_path, 'w', encoding='utf-8') as f:
            json.dump(new_options, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True, 'message': '配置已保存'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download_csv', methods=['GET', 'POST'])
def download_csv():
    """下载最新 submissions.csv（密码保护）"""
    if DOWNLOAD_PASSWORD:
        if request.method == 'POST':
            pwd = request.form.get('password', '')
        else:
            pwd = request.args.get('password', '')
        if pwd != DOWNLOAD_PASSWORD:
            return jsonify({'error': '密码错误或未提供'}), 403
    if not os.path.exists(CSV_FILE):
        return jsonify({'error': 'No submissions yet'}), 404
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return send_file(CSV_FILE, mimetype='text/csv', as_attachment=True, download_name=f'submissions_{timestamp}.csv')

# ================= 管理功能：删除提交记录 =================
def _verify_admin_password():
    """验证管理员密码。支持 Header 或 JSON body 中的 password。"""
    if request.json and 'password' in request.json:
        pwd = request.json['password']
    else:
        pwd = request.headers.get('X-Admin-Password')
    options_password = os.getenv('OPTIONS_PASSWORD', DOWNLOAD_PASSWORD)
    if options_password and pwd != options_password:
        return False
    return True

@app.route('/api/submissions/<timestamp>', methods=['DELETE'])
def delete_submission(timestamp):
    if not _verify_admin_password():
        return jsonify({'success': False, 'error': '密码错误或未提供'}), 403
    success_csv, msg_csv = _delete_csv_submission(timestamp)
    if not success_csv:
        return jsonify({'success': False, 'error': msg_csv}), 500
    try:
        _delete_jsonl_submission(timestamp)
    except Exception as e:
        print(f"[WARN] JSONL 删除失败: {e}", flush=True)
    return jsonify({'success': True, 'message': '记录已删除'})

def _delete_csv_submission(timestamp):
    try:
        import csv, tempfile
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            reader = csv.DictReader(f)
            rows = [row for row in reader if row.get('timestamp') != timestamp]
            fieldnames = reader.fieldnames
        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8', newline='', dir=DATA_DIR) as tmp:
            writer = csv.DictWriter(tmp, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp.name, CSV_FILE)
        return True, 'OK'
    except Exception as e:
        return False, f'删除失败: {str(e)}'

def _delete_jsonl_submission(timestamp):
    try:
        with open(JSONL_FILE, 'r', encoding='utf-8') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            lines = f.readlines()
        deleted = False
        new_lines = []
        for line in lines:
            try:
                obj = json.loads(line)
                if obj.get('timestamp') == timestamp:
                    deleted = True
                    continue
                new_lines.append(json.dumps(obj, ensure_ascii=False) + '\n')
            except json.JSONDecodeError:
                new_lines.append(line)
        if not deleted:
            return
        temp_path = JSONL_FILE + '.tmp'
        with open(temp_path, 'w', encoding='utf-8') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.writelines(new_lines)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, JSONL_FILE)
    except Exception as e:
        print(f"[ERROR] JSONL 删除失败: {e}", flush=True)
        raise


# ================= 管理功能：导出筛选结果 =================
@app.route('/api/submissions/export', methods=['POST'])
def export_submissions():
    """
    导出筛选后的提交记录为 CSV
    需要管理密码（X-Admin-Password 或 JSON body 中的 password）
    JSON body 参数：
    - search: 搜索关键词（可选）
    - start_date: 开始日期 YYYY-MM-DD（可选）
    - end_date: 结束日期 YYYY-MM-DD（可选）
    - sort_field: 排序字段（可选，如 'timestamp', 'date' 等）
    - sort_asc: 是否升序（可选，默认为 true）
    """
    # 密码验证
    pwd = request.headers.get('X-Admin-Password')
    if not pwd and request.json:
        pwd = request.json.get('password', '')
    options_password = os.getenv('OPTIONS_PASSWORD', DOWNLOAD_PASSWORD)
    if options_password and pwd != options_password:
        return jsonify({'error': '密码错误或未提供'}), 403

    try:
        # 读取筛选参数
        params = request.get_json() or {}
        search = params.get('search', '').strip().lower()
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        sort_field = params.get('sort_field')
        sort_asc = params.get('sort_asc', True)

        if not os.path.exists(CSV_FILE):
            return jsonify({'error': '暂无提交数据'}), 404

        # 读取所有数据
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames

        # 筛选
        filtered = rows
        if start_date or end_date:
            filtered = [r for r in filtered
                       if (not start_date or r.get('date', '') >= start_date)
                       and (not end_date or r.get('date', '') <= end_date)]

        if search:
            filtered = [r for r in filtered
                       if any(search in str(v).lower() for v in r.values())]

        # 排序
        if sort_field and sort_field in fieldnames:
            filtered.sort(key=lambda r: r.get(sort_field, ''), reverse=not sort_asc)

        # 生成 CSV 内容
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered)
        csv_content = output.getvalue()
        output.close()

        # 构建文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'submissions_export_{timestamp}_{len(filtered)}rows.csv'

        return Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'X-Total-Rows': str(len(filtered)),
                'Content-Length': str(len(csv_content.encode('utf-8')))
            }
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    init_csv()
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    port = int(os.getenv('PORT', '5001'))
    print(f"问卷后端启动于 https://localhost:{port}")
    print(f"数据目录：{DATA_DIR}")
    if WEBDAV_URL:
        print(f"WebDAV 上传：{WEBDAV_URL}")
    else:
        print("WebDAV 未配置（可设定环境变数)")
    app.run(host='0.0.0.0', port=port, debug=debug, ssl_context=(os.getenv('SSL_CERT_PATH', os.path.join(BASE_DIR, 'ssl', 'cert.pem')), os.getenv('SSL_KEY_PATH', os.path.join(BASE_DIR, 'ssl', 'key.pem'))))