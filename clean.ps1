# 可重复执行的清理脚本：只删缓存与临时文件，不动数据、依赖、交付物。
# 用法：  .\clean.ps1            （执行清理）
#         .\clean.ps1 -DryRun    （只列出将删除的内容）
param([switch]$DryRun)

$root = $PSScriptRoot
$targets = @(
    (Join-Path $root '_tmp'),
    (Join-Path $root '_mplcache'),
    (Join-Path $root 'service\.tmp'),
    (Join-Path $root 'service\.npm-cache'),
    (Join-Path $root 'service\backend\.mplcache')
)

# 递归清理 __pycache__（跳过 node_modules）
$pycache = Get-ChildItem $root -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\node_modules\\' }

$all = @($targets | Where-Object { Test-Path $_ }) + @($pycache.FullName)
if (-not $all) { Write-Host '没有需要清理的缓存。'; exit 0 }

$total = 0
foreach ($p in $all) {
    $size = (Get-ChildItem $p -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    if (-not $size) { $size = 0 }
    $total += $size
    $label = $p.Replace($root + '\', '')
    if ($DryRun) {
        Write-Host ("[dry-run] {0}  ({1:N2} MB)" -f $label, ($size / 1MB))
    } else {
        Remove-Item $p -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host ("removed {0}  ({1:N2} MB)" -f $label, ($size / 1MB))
    }
}
Write-Host ("`n{0} 项，共 {1:N2} MB" -f $all.Count, ($total / 1MB))
Write-Host '注意：data\、交付\、vendor\、node_modules\ 不会被删除。'
