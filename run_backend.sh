#!/usr/bin/env bash
set -e

# 切换到脚本所在目录（确保在项目根目录执行）
cd "$(dirname "$0")"

# 加载 .env 配置（如果存在）
if [ -f ".env" ]; then
    echo "📁 加载 .env 配置..."
    set -a
    . .env
    set +a
else
    echo "❌ 未找到 .env 文件。请创建 .env 并设置必要的环境变量。"
    exit 1
fi

# 检查必需变量（可根据需要扩展）
if [ -z "$DOWNLOAD_PASSWORD" ]; then
    echo "❌ DOWNLOAD_PASSWORD 未设置。"
    exit 1
fi

PID_FILE="backend.pid"
LOG_FILE="backend.log"

start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "⚠️  后端已在运行 (PID $(cat $PID_FILE))，准备重启..."
        stop
    fi

    echo "🚀 启动后端..."
    PORT=${PORT:-5001}
    export PORT
    nohup ./venv/bin/python backend.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 1
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
            PROTO="https"
        else
            PROTO="http"
        fi
        echo "✅ 后端已启动 (PID $(cat $PID_FILE))"
        echo "📍 路径: $(pwd)/backend.py"
        echo "🌐 地址: ${PROTO}://localhost:$PORT"
    else
        echo "❌ 启动失败，请查看日志："
        tail -n 30 "$LOG_FILE" 2>/dev/null || echo "无日志文件"
        exit 1
    fi
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            sleep 0.5
            kill -0 "$PID" 2>/dev/null && kill -9 "$PID" || true
            rm -f "$PID_FILE"
            echo "🛑 已停止后端"
        else
            echo "⚠️  PID 文件存在但进程不存在，已清理"
            rm -f "$PID_FILE"
        fi
    else
        echo "❌ 未运行（无 PID 文件）"
    fi
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "✅ 后端运行中 (PID $(cat $PID_FILE))"
    else
        echo "❌ 后端未运行"
    fi
}

case "${1:-start}" in
    start)  start ;;
    stop)   stop ;;
    status) status ;;
    restart)
        stop
        sleep 1
        start
        ;;
    *) echo "用法: $0 [start|stop|restart|status]"; exit 1 ;;
esac