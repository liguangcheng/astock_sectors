#!/usr/bin/env bash
# =============================================================================
# 可重复执行的清理脚本（bash 版，等价于原 clean.ps1）
# 只删缓存与临时文件，不动数据、依赖、交付物。
#
# 用法：
#   ./clean.sh              # 执行清理
#   ./clean.sh --dry-run    # 只列出将删除的内容
# =============================================================================
set -uo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

DRY_RUN=0
case "${1:-}" in
    '') ;;
    -n | --dry-run | -dryrun | --dryrun) DRY_RUN=1 ;;
    -h | --help)
        cat <<'EOF'
用法: ./clean.sh [--dry-run]

  --dry-run   只列出将删除的内容，不实际删除
EOF
        exit 0
        ;;
    *)
        echo "未知参数：$1（可用 --dry-run）" >&2
        exit 2
        ;;
esac

# 固定目标（不存在则跳过）
targets=(
    "$ROOT/_tmp"
    "$ROOT/_mplcache"
    "$ROOT/service/.tmp"
    "$ROOT/service/.npm-cache"
    "$ROOT/service/backend/.mplcache"
)

# 递归找 __pycache__，跳过 node_modules 与 .git
pycache=()
while IFS= read -r d; do
    [ -n "$d" ] && pycache+=("$d")
done < <(
    find "$ROOT" \( -name node_modules -o -name .git \) -prune -o \
        -type d -name __pycache__ -print 2>/dev/null
)

all=()
for p in "${targets[@]}"; do
    [ -e "$p" ] && all+=("$p")
done
for p in "${pycache[@]}"; do
    all+=("$p")
done

if [ "${#all[@]}" -eq 0 ]; then
    echo '没有需要清理的缓存。'
    exit 0
fi

to_mb() {
    awk -v k="${1:-0}" 'BEGIN { printf "%.2f", k / 1024 }'
}

total_kb=0
for p in "${all[@]}"; do
    # 安全护栏：只允许删除项目目录内的路径
    case "$p" in
        "$ROOT"/*) ;;
        *)
            echo "跳过（不在项目内）：$p" >&2
            continue
            ;;
    esac
    size_kb="$(du -sk "$p" 2>/dev/null | awk '{ print $1 }')"
    size_kb="${size_kb:-0}"
    total_kb=$((total_kb + size_kb))
    label="${p#"$ROOT"/}"
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '[dry-run] %s  (%s MB)\n' "$label" "$(to_mb "$size_kb")"
    else
        rm -rf -- "$p" 2>/dev/null
        if [ -e "$p" ]; then
            echo "删除失败（可能被占用）：$label" >&2
            continue
        fi
        printf 'removed %s  (%s MB)\n' "$label" "$(to_mb "$size_kb")"
    fi
done

printf '\n%d 项，共 %s MB\n' "${#all[@]}" "$(to_mb "$total_kb")"
echo '注意：data/、交付/、vendor/、node_modules/ 不会被删除。'
