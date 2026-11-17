# A股行业龙头股 · 本地服务启动脚本
# 推荐入口：start.cmd（会自动绕过 PowerShell 执行策略限制）
# 也可在本目录执行：powershell -ExecutionPolicy Bypass -File .\start.ps1
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$distIndex = Join-Path $frontend 'dist\index.html'
$url = 'http://127.0.0.1:3999'

Write-Host '=== A股行业龙头股月度行情服务 ===' -ForegroundColor Cyan

function Test-Service {
    try {
        $r = Invoke-WebRequest "$url/api/health" -UseBasicParsing -TimeoutSec 2
        return ($r.StatusCode -eq 200)
    } catch {
        return $false
    }
}

# 已经在运行：直接打开浏览器，避免重复启动
if (Test-Service) {
    Write-Host "服务已在运行：$url" -ForegroundColor Green
    Start-Process $url
    exit 0
}

if (-not (Test-Path $distIndex)) {
    Write-Host '[1/3] 首次运行，构建前端（约 30 秒）…' -ForegroundColor Yellow
    $env:TMP = Join-Path $root '.tmp'
    New-Item -ItemType Directory -Force -Path $env:TMP | Out-Null
    Push-Location $frontend
    try {
        & npm.cmd install --registry=https://registry.npmmirror.com --no-audit --no-fund
        & npm.cmd run build
    } finally {
        Pop-Location
    }
}

$listener = $null
try {
    $listener = Get-NetTCPConnection -LocalPort 3999 -State Listen -ErrorAction Stop
} catch {
    $listener = $null
}
if ($listener) {
    Write-Host '端口 3999 已被其他程序占用：' -ForegroundColor Red
    $listener | Select-Object LocalAddress, OwningProcess | Format-Table -AutoSize
    exit 1
}

$env:PYTHONIOENCODING = 'utf-8'
Write-Host '[2/3] 启动后端 127.0.0.1:3999 …' -ForegroundColor Yellow
$proc = Start-Process -FilePath 'python' -ArgumentList 'run.py' -WorkingDirectory $backend -PassThru -WindowStyle Hidden

$ok = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    if (Test-Service) { $ok = $true; break }
    if ($proc.HasExited) { break }
}

if (-not $ok) {
    Write-Host '服务启动失败。可能原因：端口被占用、Python 环境异常、依赖缺失。' -ForegroundColor Red
    Write-Host '请在前台运行以查看日志： cd backend; python run.py' -ForegroundColor DarkGray
    exit 1
}

Write-Host "[3/3] 就绪：$url   （Ctrl+C 或关闭本窗口停止）" -ForegroundColor Green
Start-Process $url
Write-Host "后端进程 PID=$($proc.Id)；日志输出在本窗口。" -ForegroundColor DarkGray
$proc.WaitForExit()
