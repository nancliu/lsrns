# PowerShell script to replace timeline function calls
# Phase 2 Task 2.1 - Step 3

$filePath = "D:\projects\OD_SIM\frontend\control\js\parameter_form.js"

# Create backup
Copy-Item $filePath "$filePath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# Read file content
$content = Get-Content $filePath -Raw

# Replacement 1: VSS debounced
$content = $content -replace 'debouncedUpdateTimelineFromTable\(tbody\)', 'debouncedUpdateTimeline.vss(tbody)'

# Replacement 2: VSS direct
$content = $content -replace 'updateTimelineFromTable\(tbody\);', 'updateTimelineByType(tbody, ''vss'');'

# Replacement 3: DHS debounced
$content = $content -replace 'debouncedUpdateDHSTimelineFromTable\(tbody\)', 'debouncedUpdateTimeline.dhs(tbody)'

# Replacement 4: DHS direct
$content = $content -replace 'updateDHSTimelineFromTable\(tbody\);', 'updateTimelineByType(tbody, ''dhs'');'

# Replacement 5: Flow debounced
$content = $content -replace 'debouncedUpdateFlowTimelineFromTable\(tbody\)', 'debouncedUpdateTimeline.flow(tbody)'

# Replacement 6: Flow direct
$content = $content -replace 'updateFlowTimelineFromTable\(tbody\);', 'updateTimelineByType(tbody, ''flow'');'

# Replacement 7: TEC direct
$content = $content -replace 'updateTECTimelineFromTable\(tbody\);', 'updateTimelineByType(tbody, ''tec_simple'');'

# Write back
$content | Set-Content $filePath -NoNewline

Write-Host "✅ 替换完成！" -ForegroundColor Green
Write-Host ""
Write-Host "备份文件已创建在同目录下（.backup_* 文件）" -ForegroundColor Yellow
Write-Host ""
Write-Host "替换摘要：" -ForegroundColor Cyan
Write-Host "  1. debouncedUpdateTimelineFromTable → debouncedUpdateTimeline.vss"
Write-Host "  2. updateTimelineFromTable → updateTimelineByType(..., 'vss')"
Write-Host "  3. debouncedUpdateDHSTimelineFromTable → debouncedUpdateTimeline.dhs"
Write-Host "  4. updateDHSTimelineFromTable → updateTimelineByType(..., 'dhs')"
Write-Host "  5. debouncedUpdateFlowTimelineFromTable → debouncedUpdateTimeline.flow"
Write-Host "  6. updateFlowTimelineFromTable → updateTimelineByType(..., 'flow')"
Write-Host "  7. updateTECTimelineFromTable → updateTimelineByType(..., 'tec_simple')"
Write-Host ""
Write-Host "请运行验证测试：npx playwright test tests/e2e/test_strategy_creation_workflow.spec.js" -ForegroundColor Magenta
