# 检查并发任务配置脚本

Write-Host "=== 并发任务配置检查 ===" -ForegroundColor Cyan

# 1. 检查配置文件
Write-Host "`n1. 配置文件检查:" -ForegroundColor Yellow
$configPath = "config\system_config.json"
if (Test-Path $configPath) {
    $config = Get-Content $configPath | ConvertFrom-Json
    $ratio = $config.batch_simulation.concurrent_simulations_ratio
    Write-Host "  配置文件路径: $configPath" -ForegroundColor Green
    Write-Host "  配置比例: $ratio" -ForegroundColor Green
} else {
    Write-Host "  配置文件不存在: $configPath" -ForegroundColor Red
}

# 2. 检查环境变量
Write-Host "`n2. 环境变量检查:" -ForegroundColor Yellow
$envMax = $env:MAX_CONCURRENT_SIMULATIONS
$envRatio = $env:MAX_CONCURRENT_SIMULATIONS_RATIO
if ($envMax) {
    Write-Host "  MAX_CONCURRENT_SIMULATIONS = $envMax" -ForegroundColor Yellow
} else {
    Write-Host "  MAX_CONCURRENT_SIMULATIONS: 未设置" -ForegroundColor Green
}
if ($envRatio) {
    Write-Host "  MAX_CONCURRENT_SIMULATIONS_RATIO = $envRatio" -ForegroundColor Yellow
} else {
    Write-Host "  MAX_CONCURRENT_SIMULATIONS_RATIO: 未设置" -ForegroundColor Green
}

# 3. 使用Python验证配置
Write-Host "`n3. Python验证配置:" -ForegroundColor Yellow
$pythonCheck = python -c "from shared.control_tools.batch_simulation_scheduler import get_max_concurrent_simulations; import multiprocessing; cpu = multiprocessing.cpu_count(); result = get_max_concurrent_simulations(); print(f'CPU核心数: {cpu}'); print(f'配置的并发数: {result}'); print(f'使用的比例: {result/cpu:.2f}')" 2>&1
Write-Host $pythonCheck

# 4. 检查运行中的批次
Write-Host "`n4. 运行中的批次:" -ForegroundColor Yellow
$batchFiles = Get-ChildItem -Path "cases" -Recurse -Filter "batch_metadata.json" -ErrorAction SilentlyContinue | 
    Where-Object { 
        $content = Get-Content $_.FullName -Raw | ConvertFrom-Json
        $content.status -eq "running"
    } | 
    ForEach-Object {
        $content = Get-Content $_.FullName -Raw | ConvertFrom-Json
        [PSCustomObject]@{
            BatchID = $content.batch_id
            Status = $content.status
            StartedAt = $content.started_at
            MaxConcurrent = $content.max_concurrent
        }
    }

if ($batchFiles) {
    $batchFiles | Format-Table -AutoSize
    Write-Host "  注意: 运行中的批次使用的是启动时的配置，不会自动更新" -ForegroundColor Yellow
} else {
    Write-Host "  没有运行中的批次" -ForegroundColor Green
}

# 5. 建议
Write-Host "`n=== 建议 ===" -ForegroundColor Cyan
if ($batchFiles) {
    Write-Host "1. 当前有运行中的批次，它们使用的是旧配置" -ForegroundColor Yellow
    Write-Host "2. 等待当前批次完成，或取消并重新创建新批次" -ForegroundColor Yellow
    Write-Host "3. 新批次会使用最新配置（24个并发任务）" -ForegroundColor Green
} else {
    Write-Host "1. 创建新批次进行测试" -ForegroundColor Green
    Write-Host "2. 查看API日志，应该看到 '24 concurrent tasks'" -ForegroundColor Green
}

