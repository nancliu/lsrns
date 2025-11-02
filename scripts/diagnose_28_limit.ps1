# 诊断28个任务限制问题

Write-Host "=== 28个SUMO任务限制诊断 ===" -ForegroundColor Cyan

# 1. 检查Python进程资源
Write-Host "`n1. Python进程资源使用:" -ForegroundColor Yellow
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcs) {
    foreach ($proc in $pythonProcs) {
        $threads = (Get-Process -Id $proc.Id).Threads.Count
        Write-Host "  PID: $($proc.Id) | 句柄数: $($proc.Handles) | 线程数: $threads | 内存: $([math]::Round($proc.WorkingSet/1MB, 2))MB"
    }
} else {
    Write-Host "  未找到Python进程" -ForegroundColor Red
}

# 2. 检查SUMO进程数
Write-Host "`n2. 当前SUMO进程数:" -ForegroundColor Yellow
$sumoCount = (Get-Process | Where-Object { $_.ProcessName -like "*sumo*" }).Count
Write-Host "  SUMO进程数: $sumoCount"

# 3. 检查系统句柄使用情况
Write-Host "`n3. 系统资源使用:" -ForegroundColor Yellow
$totalHandles = (Get-Process | Measure-Object -Property Handles -Sum).Sum
$avgHandles = (Get-Process | Measure-Object -Property Handles -Average).Average
Write-Host "  总句柄数: $totalHandles"
Write-Host "  平均句柄数: $([math]::Round($avgHandles, 0))"

# 4. 检查系统限制
Write-Host "`n4. Windows系统限制检查:" -ForegroundColor Yellow
Write-Host "  默认进程句柄限制: ~10,000 (64位系统)"
Write-Host "  默认文件句柄限制: ~2,048 每个进程"
Write-Host "  子进程创建限制: 通常受内存和句柄限制"

# 5. 诊断结果
Write-Host "`n5. 诊断结果:" -ForegroundColor Yellow
if ($pythonProcs) {
    $maxHandles = ($pythonProcs | Measure-Object -Property Handles -Maximum).Maximum
    if ($maxHandles -gt 1500) {
        Write-Host "  ⚠️  句柄数较高 ($maxHandles)，可能接近限制" -ForegroundColor Yellow
    } else {
        Write-Host "  ✅ 句柄数正常 ($maxHandles)" -ForegroundColor Green
    }
}

if ($sumoCount -eq 28) {
    Write-Host "  ⚠️  确实只有28个SUMO进程在运行" -ForegroundColor Yellow
    Write-Host "  可能原因: Windows子进程创建限制" -ForegroundColor Yellow
} elseif ($sumoCount -lt 28) {
    Write-Host "  ℹ️  当前SUMO进程数: $sumoCount (少于28)" -ForegroundColor Cyan
} else {
    Write-Host "  ✅ SUMO进程数: $sumoCount (超过28)" -ForegroundColor Green
}

# 6. 建议
Write-Host "`n=== 建议 ===" -ForegroundColor Cyan
Write-Host "1. 如果句柄数接近限制，考虑降低并发数到28:" -ForegroundColor Yellow
Write-Host "   config/system_config.json: `"concurrent_simulations_ratio`": 1.17" -ForegroundColor White
Write-Host "`n2. 如果需要超过28个，可以尝试:" -ForegroundColor Yellow
Write-Host "   - 修改Windows注册表增加句柄限制（需要管理员权限）" -ForegroundColor White
Write-Host "   - 检查是否有句柄泄露（确保进程正确终止）" -ForegroundColor White
Write-Host "`n3. 查看详细诊断文档:" -ForegroundColor Yellow
Write-Host "   docs/TROUBLESHOOTING_28_TASK_LIMIT.md" -ForegroundColor White

