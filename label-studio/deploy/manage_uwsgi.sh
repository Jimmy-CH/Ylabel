#!/bin/bash

# ========== 配置变量 ==========
APP_NAME="ylabel"
APP_ROOT="/opt/application/ylabel"
APP_DIR="$APP_ROOT/label-studio"
VENV_BIN="$APP_ROOT/venv/bin"
UWSGI_BIN="$VENV_BIN/uwsgi"
UWSGI_INI="$APP_DIR/deploy/uwsgi.ini"
PID_FILE="$APP_ROOT/uwsgi.pid"
LOG_FILE="$APP_ROOT/logs/uwsgi.log"
# =============================

# 加载系统环境变量（可选）
source /etc/profile

# 检查 uwsgi 是否已在运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            return 0  # 正在运行
        else
            rm -f "$PID_FILE" 2>/dev/null  # 清理无效 PID 文件
        fi
    fi
    return 1  # 未运行
}

start() {
    echo "Starting $APP_NAME uWSGI server..."

    if is_running; then
        echo "Error: uWSGI is already running (PID: $(cat "$PID_FILE"))."
        exit 1
    fi

    # 确保日志目录存在
    mkdir -p "$(dirname "$LOG_FILE")"

    # 切换到应用目录（与 chdir 一致）
    cd "$APP_DIR" || { echo "Failed to cd to $APP_DIR"; exit 1; }

    # 启动 uWSGI
    "$UWSGI_BIN" --ini "$UWSGI_INI"

    # 等待启动完成（最多 5 秒）
    for i in {1..5}; do
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "uWSGI started successfully (PID: $(cat "$PID_FILE"))"
            echo "   Log file: $LOG_FILE"
            return 0
        fi
        sleep 1
    done

    echo "uWSGI may have failed to start (PID file not created). Check log: $LOG_FILE"
    exit 1
}

stop() {
    echo "Stopping $APP_NAME uWSGI server..."

    if ! is_running; then
        echo "uWSGI is not running."
        return 0
    fi

    local pid=$(cat "$PID_FILE")
    echo "Gracefully stopping uWSGI (PID: $pid)..."

    # 使用 uwsgi --stop 实现优雅退出（会触发 reload-mercy）
    "$UWSGI_BIN" --stop "$PID_FILE"

    # 等待最多 10 秒（比 worker-reload-mercy=3 更宽松）
    for i in {1..10}; do
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "uWSGI stopped gracefully."
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done

    # 超时后强制终止
    echo "Graceful stop timed out. Force killing PID $pid..."
    kill -9 "$pid" 2>/dev/null
    rm -f "$PID_FILE"
}

restart() {
    stop
    sleep 2
    start
}

# 主逻辑
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        if is_running; then
            echo "uWSGI is running (PID: $(cat "$PID_FILE"))."
        else
            echo "uWSGI is NOT running."
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
