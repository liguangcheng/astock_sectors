#!/usr/bin/env bash
# =============================================================================
# A股行业龙头股 · 停止本地服务（bash 版）
#
# 原 PowerShell 方案的「停止」是手工执行：
#     Get-NetTCPConnection -LocalPort 3999 -State Listen | % { Stop-Process -Id $_.OwningProcess }
# 本脚本把它固化成可重复执行的命令，行为等价：
#   1) 按端口找监听进程（无监听 → 视为已停止，退出 0，可放心重复执行）
#   2) Windows 用 taskkill /T /F（结束进程树），Linux/mac 先 TERM 再 KILL
#   3) 复查端口，确认释放；失败退出 1
#
# 用法：
#   ./stop.sh                 # 停止 127.0.0.1:3999
#   ./stop.sh --dry-run       # 只显示将停止的进程
#   ./stop.sh --force         # 跳过优雅等待，直接强杀
#   ./stop.sh --timeout 10    # 等待端口释放的秒数（默认 5）
#   ./stop.sh --port 4000
#
# 端口来源：--port > 环境变量 ASTOCK_PORT > service/.env > 3999
# =============================================================================
set -uo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PORT="3999"

case "$(uname -s 2>/dev/null || echo unknown)" in
    MINGW* | MSYS* | CYGWIN*) OS_KIND=windows ;;
    *) OS_KIND=unix ;;
esac

DRY_RUN=0
FORCE=0
TIMEOUT=5
CLI_PORT=""

usage() {
    cat <<'EOF'
用法: ./stop.sh [选项]

选项:
  --port <端口>    指定端口（默认 3999，或 ASTOCK_PORT / service/.env）
  --dry-run        只显示将停止的进程，不实际结束
  --force          跳过优雅等待，直接强制结束
  --timeout <秒>   等待端口释放的秒数，默认 5
  -h, --help       显示本帮助
EOF
}

die() {
    echo "错误：$*" >&2
    exit 1
}

have() { command -v "$1" >/dev/null 2>&1; }

port_from_env_file() {
    local f="$ROOT/.env"
    [ -r "$f" ] || return 1
    sed -n 's/^[[:space:]]*ASTOCK_PORT[[:space:]]*=[[:space:]]*//p' "$f" 2>/dev/null \
        | tail -n 1 \
        | sed 's/[[:space:]]*#.*//' \
        | tr -d "\"' \r\t"
}

# netstat/ss/lsof 给出的都是「系统 PID」；
# Windows 上必须用 taskkill，不能直接 kill（MSYS 的 kill 认的是伪 PID，会误杀同号进程）。
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

port_listening() {
    local port="$1"
    [ -n "$(port_pids "$port")" ] && return 0
    [ -n "$PYTHON" ] || return 1
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

proc_name() {
    local pid="$1" name=""
    if [ "$OS_KIND" = windows ]; then
        name="$(tasklist //FI "PID eq $pid" //FO CSV //NH 2>/dev/null | tr -d '\r' \
            | cut -d, -f1 | tr -d '"' | head -n 1)"
        case "$name" in INFO* | '') name="" ;; esac
    else
        name="$(ps -p "$pid" -o comm= 2>/dev/null | tr -d '\r' | head -n 1)"
    fi
    echo "${name:-unknown}"
}

kill_pid() {
    local pid="$1"
    if [ "$OS_KIND" = windows ]; then
        # 先礼后兵：不带 /F 对控制台程序通常无效，失败就强杀进程树
        taskkill //PID "$pid" //T >/dev/null 2>&1 || taskkill //F //PID "$pid" //T >/dev/null 2>&1 || true
    else
        kill "$pid" 2>/dev/null || true
    fi
}

force_kill_pid() {
    local pid="$1"
    if [ "$OS_KIND" = windows ]; then
        taskkill //F //T //PID "$pid" >/dev/null 2>&1 || true
    else
        kill -9 "$pid" 2>/dev/null || true
    fi
}

# ---------------------------------------------------------------------------
# 参数
# ---------------------------------------------------------------------------
while [ $# -gt 0 ]; do
    case "$1" in
        --port) shift; CLI_PORT="${1:-}" ;;
        --port=*) CLI_PORT="${1#*=}" ;;
        --dry-run) DRY_RUN=1 ;;
        --force) FORCE=1 ;;
        --timeout) shift; TIMEOUT="${1:-5}" ;;
        --timeout=*) TIMEOUT="${1#*=}" ;;
        -h | --help) usage; exit 0 ;;
        *) usage >&2; die "未知参数：$1" ;;
    esac
    shift
done

case "$TIMEOUT" in
    '' | *[!0-9]*) die "timeout 必须是整数秒：$TIMEOUT" ;;
esac

# 优先 python（Windows 上 python3 常是 WindowsApps 存根）；找不到也不影响 netstat/ss 路径
PYTHON=""
for candidate in python python3; do
    if have "$candidate" && "$candidate" -c 'import sys' >/dev/null 2>&1; then
        PYTHON="$(command -v "$candidate")"
        break
    fi
done

PORT="${CLI_PORT:-${ASTOCK_PORT:-}}"
[ -n "$PORT" ] || PORT="$(port_from_env_file || true)"
PORT="${PORT:-3999}"
case "$PORT" in
    '' | *[!0-9]*) die "端口不合法：$PORT" ;;
esac
URL="http://127.0.0.1:$PORT"

pids="$(port_pids "$PORT")"
if [ -z "$pids" ]; then
    echo "服务未在运行（$URL 无监听）。"
    exit 0
fi

if [ "$DRY_RUN" -eq 1 ]; then
    echo "将停止以下进程（端口 $PORT）："
    for pid in $pids; do
        echo "  PID=$pid  进程=$(proc_name "$pid")"
    done
    exit 0
fi

echo "停止服务 $URL …"
for pid in $pids; do
    echo "  PID=$pid  进程=$(proc_name "$pid")"
    if [ "$FORCE" -eq 1 ]; then
        force_kill_pid "$pid"
    else
        kill_pid "$pid"
    fi
done

# 等待端口释放
i=0
while [ "$i" -lt "$TIMEOUT" ]; do
    port_listening "$PORT" || break
    sleep 1
    i=$((i + 1))
done

if port_listening "$PORT" && [ "$FORCE" -eq 0 ]; then
    echo "端口 $PORT 仍在监听，强制结束…"
    for pid in $(port_pids "$PORT"); do
        force_kill_pid "$pid"
    done
    sleep 1
fi

if port_listening "$PORT"; then
    echo "停止失败：端口 $PORT 仍被占用（PID: $(port_pids "$PORT" | tr '\n' ' ')）。" >&2
    echo '可重试： ./stop.sh --force' >&2
    exit 1
fi

echo "已停止，端口 $PORT 已释放。"
