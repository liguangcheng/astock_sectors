#!/usr/bin/env bash
# =============================================================================
# A股行业龙头股 · 本地服务启动（bash 版，等价于原 start.ps1）
#
# 行为：
#   1) 服务已在运行 → 打开浏览器并退出 0（不会重复启动）
#   2) frontend/dist/index.html 缺失 → npm install && npm run build
#   3) 端口被其他程序占用 → 报错退出 1
#   4) 后台启动 python run.py，轮询 /api/health，就绪后打开浏览器
#   5) 前台等待；Ctrl+C / 关闭终端会连带停掉后端
#      （原 PS 版把后端放隐藏窗口，Ctrl+C 后可能残留，用 stop.sh 兜底）
#
# 用法：
#   ./start.sh                  # 默认 http://127.0.0.1:3999
#   ./start.sh --no-browser     # 不自动开浏览器（定时任务/无桌面环境）
#   ./start.sh --port 4000      # 临时换端口
#
# 端口来源（优先级从高到低）：--port > 环境变量 ASTOCK_PORT > service/.env > 3999
# 日志：service/data/service.log
# =============================================================================
set -uo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
DIST_INDEX="$FRONTEND/dist/index.html"
URL_HOST="127.0.0.1"
LOG="$ROOT/data/service.log"

NO_BROWSER=0
CLI_PORT=""
BACKEND_PID=""
LAUNCHED=0
SIGNALED=0
PORT="3999"

case "$(uname -s 2>/dev/null || echo unknown)" in
    MINGW* | MSYS* | CYGWIN*) OS_KIND=windows ;;
    *) OS_KIND=unix ;;
esac

usage() {
    cat <<'EOF'
用法: ./start.sh [选项]

选项:
  --no-browser    启动后不自动打开浏览器
  --port <端口>   临时指定端口（默认 3999，或 ASTOCK_PORT / service/.env）
  -h, --help      显示本帮助
EOF
}

die() {
    echo "错误：$*" >&2
    exit 1
}

have() { command -v "$1" >/dev/null 2>&1; }

# 从 service/.env 读 ASTOCK_PORT（config.py 会加载该文件）
port_from_env_file() {
    local f="$ROOT/.env"
    [ -r "$f" ] || return 1
    sed -n 's/^[[:space:]]*ASTOCK_PORT[[:space:]]*=[[:space:]]*//p' "$f" 2>/dev/null \
        | tail -n 1 \
        | sed 's/[[:space:]]*#.*//' \
        | tr -d "\"' \r\t"
}

pid_alive() {
    local pid="$1"
    [ -n "$pid" ] || return 1
    kill -0 "$pid" 2>/dev/null && return 0
    ps -p "$pid" >/dev/null 2>&1
}

# 列出监听指定端口的 PID（Linux: ss, macOS: lsof, Windows/MSYS: netstat）
port_pids() {
    local port="$1"
    {
        if have ss; then
            ss -ltnp 2>/dev/null \
                | awk -v p=":$port" '$4 ~ p"$" {print}' \
                | grep -o 'pid=[0-9]*' | cut -d= -f2
        elif have lsof; then
            lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null
        elif have netstat; then
            netstat -ano 2>/dev/null | tr -d '\r' \
                | awk -v p=":$port" '/LISTEN/ && $2 ~ p"$" {print $NF}'
        fi
    } | grep -E '^[0-9]+$' | sort -u
}

# 端口上是否有进程在监听（PID 解析失败时用一次 TCP 连接兜底）
port_listening() {
    local port="$1"
    [ -n "$(port_pids "$port")" ] && return 0
    "$PYTHON" - "$port" <<'PY' >/dev/null 2>&1
import socket, sys
s = socket.socket()
s.settimeout(0.5)
try:
    sys.exit(0 if s.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 1)
finally:
    s.close()
PY
}

health_ok() {
    local url="http://$URL_HOST:$PORT/api/health"
    if have curl; then
        curl -fsS --max-time 2 -o /dev/null "$url" 2>/dev/null
    else
        "$PYTHON" - "$url" <<'PY' >/dev/null 2>&1
import sys, urllib.request
try:
    with urllib.request.urlopen(sys.argv[1], timeout=2) as r:
        sys.exit(0 if r.status == 200 else 1)
except Exception:
    sys.exit(1)
PY
    fi
}

open_browser() {
    local url="$1"
    if [ "$NO_BROWSER" -eq 1 ]; then
        echo "（--no-browser：请手动打开 $url）"
        return 0
    fi
    case "$OS_KIND" in
        windows) cmd.exe //c start "" "$url" >/dev/null 2>&1 & ;;
        *)
            if [ "$(uname -s 2>/dev/null)" = Darwin ]; then
                open "$url" >/dev/null 2>&1 &
            elif have xdg-open; then
                xdg-open "$url" >/dev/null 2>&1 &
            else
                echo "未找到浏览器打开方式，请手动打开：$url"
            fi
            ;;
    esac
}

npm_bin() {
    if have npm; then
        echo npm
    elif have npm.cmd; then
        echo npm.cmd
    else
        return 1
    fi
}

build_frontend() {
    echo '[1/3] 首次运行，构建前端（约 30 秒）…'
    local npm
    npm="$(npm_bin)" || die '找不到 npm：请安装 Node.js 18+，或在 frontend 目录手动 npm install && npm run build'
    export TMP="$ROOT/.tmp"
    export TEMP="$ROOT/.tmp"
    mkdir -p "$TMP"
    ( cd "$FRONTEND" && "$npm" install --registry=https://registry.npmmirror.com --no-audit --no-fund ) \
        && ( cd "$FRONTEND" && "$npm" run build ) \
        || die '前端构建失败，请到 frontend 目录手动执行 npm install && npm run build 查看报错'
}

cleanup() {
    local code=$?
    trap - INT TERM HUP EXIT
    # 只有本脚本真正拉起过后端才收尾，绝不能碰「已在运行」的那个服务
    if [ "$LAUNCHED" -eq 1 ] && pid_alive "${BACKEND_PID:-}"; then
        echo
        echo '正在停止后端…'
        # $! 是 MSYS 伪 PID，kill 会映射到真正的 Windows 进程
        kill "$BACKEND_PID" 2>/dev/null
        local i=0
        while [ "$i" -lt 10 ] && pid_alive "$BACKEND_PID"; do
            sleep 0.3
            i=$((i + 1))
        done
        if pid_alive "$BACKEND_PID"; then
            kill -9 "$BACKEND_PID" 2>/dev/null
        fi
    fi
    # 被 Ctrl+C 打断或启动失败时，Windows 上按端口再兜底一次
    if [ "$LAUNCHED" -eq 1 ] && [ "$OS_KIND" = windows ] \
        && { [ "$SIGNALED" -eq 1 ] || [ "$code" -ne 0 ]; }; then
        local p
        for p in $(port_pids "$PORT"); do
            taskkill //F //T //PID "$p" >/dev/null 2>&1 || true
        done
    fi
    exit "$code"
}

on_signal() {
    SIGNALED=1
    exit 130
}

# ---------------------------------------------------------------------------
# 参数
# ---------------------------------------------------------------------------
while [ $# -gt 0 ]; do
    case "$1" in
        --no-browser) NO_BROWSER=1 ;;
        --port) shift; CLI_PORT="${1:-}" ;;
        --port=*) CLI_PORT="${1#*=}" ;;
        -h | --help) usage; exit 0 ;;
        *) usage >&2; die "未知参数：$1" ;;
    esac
    shift
done

# 优先用 python（Windows 上 python3 可能是 WindowsApps 存根），并验证真能跑
PYTHON=""
for candidate in python python3; do
    if have "$candidate" && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info[0] >= 3 else 1)' >/dev/null 2>&1; then
        PYTHON="$(command -v "$candidate")"
        break
    fi
done
[ -n "$PYTHON" ] || die '找不到可用的 python（需要 3.11+）'

PORT="${CLI_PORT:-${ASTOCK_PORT:-}}"
[ -n "$PORT" ] || PORT="$(port_from_env_file || true)"
PORT="${PORT:-3999}"
case "$PORT" in
    '' | *[!0-9]*) die "端口不合法：$PORT" ;;
esac
URL="http://$URL_HOST:$PORT"

trap on_signal INT TERM HUP
trap cleanup EXIT

# ---------------------------------------------------------------------------
# 1. 已在运行 → 只开浏览器
# ---------------------------------------------------------------------------
echo '=== A股行业龙头股月度行情服务 ==='
if health_ok; then
    echo "服务已在运行：$URL"
    BACKEND_PID=""
    open_browser "$URL"
    exit 0
fi

# ---------------------------------------------------------------------------
# 2. 缺前端产物 → 构建
# ---------------------------------------------------------------------------
if [ ! -f "$DIST_INDEX" ]; then
    build_frontend
fi

# ---------------------------------------------------------------------------
# 3. 端口被别的程序占用
# ---------------------------------------------------------------------------
if port_listening "$PORT"; then
    echo "端口 $PORT 已被其他程序占用：" >&2
    echo "  PID: $(port_pids "$PORT" | tr '\n' ' ')" >&2
    echo "  用 ./stop.sh --port $PORT 停止，或改用 --port 其他端口。" >&2
    BACKEND_PID=""
    exit 1
fi

# ---------------------------------------------------------------------------
# 4. 后台启动后端 + 轮询健康检查
# ---------------------------------------------------------------------------
mkdir -p "$ROOT/data"
echo "[2/3] 启动后端 $URL_HOST:$PORT …"
echo "----- $(date '+%Y-%m-%d %H:%M:%S') start.sh -----" >>"$LOG"
( cd "$BACKEND" && exec env PYTHONIOENCODING=utf-8 "$PYTHON" run.py ) >>"$LOG" 2>&1 &
BACKEND_PID=$!
LAUNCHED=1

ok=0
i=0
# 最多等 90 秒：冷启动时首次 import pandas/baostock 可能要十几秒
# （原 PS 版只等 20 秒，冷启动偶发被自己判失败）
while [ "$i" -lt 180 ]; do
    sleep 0.5
    if health_ok; then
        ok=1
        break
    fi
    if ! pid_alive "$BACKEND_PID"; then
        break
    fi
    i=$((i + 1))
done

if [ "$ok" -ne 1 ]; then
    echo '服务启动失败。可能原因：端口被占用、Python 环境异常、依赖缺失。' >&2
    echo '请在前台运行以查看日志： cd backend; python run.py' >&2
    echo "后台日志： $LOG" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# 5. 就绪
# ---------------------------------------------------------------------------
echo "[3/3] 就绪：$URL   （Ctrl+C 停止）"
open_browser "$URL"
# netstat/tasklist 看到的是 Windows PID；$! 是 MSYS 伪 PID，优先显示真实 PID
SERVICE_PID="$(port_pids "$PORT" | head -n 1)"
echo "后端进程 PID=${SERVICE_PID:-$BACKEND_PID}；日志：$LOG"
wait "$BACKEND_PID"
exit $?
