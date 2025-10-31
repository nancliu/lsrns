# CSS 颜色优化脚本
# 批量替换所有 CSS 文件中的硬编码颜色值为 CSS 变量

$cssDir = "frontend\control\css"
$files = @(
    "templates-layout.css",
    "templates-forms.css",
    "templates-results.css"
)

# 颜色替换映射（按出现频率排序）
$colorMappings = @{
    "#2c3e50" = "var(--color-dark)"
    "#7f8c8d" = "var(--color-secondary-hover)"
    "#3498db" = "var(--color-primary)"
    "#ecf0f1" = "var(--color-light-border)"
    "#e74c3c" = "var(--color-danger)"
    "#f8f9fa" = "var(--color-light-hover)"
    "#bdc3c7" = "var(--color-gray-200)"
    "#667eea" = "var(--color-info)"
    "#e9ecef" = "var(--color-border-light)"
    "#95a5a6" = "var(--color-secondary)"
    "#f9fafb" = "var(--color-gray-50)"
    "#34495e" = "var(--color-dark-hover)"
    "#2ecc71" = "var(--color-success)"
    "#f5f7fa" = "var(--color-light)"
}

Write-Host "=== CSS 颜色优化工具 ===" -ForegroundColor Cyan
Write-Host ""

foreach ($file in $files) {
    $filePath = Join-Path $cssDir $file

    if (Test-Path $filePath) {
        Write-Host "处理文件: $file" -ForegroundColor Yellow

        # 备份原文件
        $backupPath = "$filePath.backup"
        Copy-Item $filePath $backupPath -Force
        Write-Host "  ✓ 已备份到: $file.backup" -ForegroundColor Green

        # 读取文件内容
        $content = Get-Content $filePath -Raw
        $originalContent = $content
        $replacements = 0

        # 执行替换
        foreach ($color in $colorMappings.Keys) {
            $variable = $colorMappings[$color]
            $pattern = [regex]::Escape($color)
            $matches = [regex]::Matches($content, $pattern, "IgnoreCase")

            if ($matches.Count -gt 0) {
                $content = $content -replace $pattern, $variable
                $replacements += $matches.Count
                Write-Host "  ✓ 替换 $color → $variable ($($matches.Count) 次)" -ForegroundColor Gray
            }
        }

        # 写回文件
        if ($replacements -gt 0) {
            Set-Content $filePath $content -NoNewline
            Write-Host "  ✓ 完成! 总计替换 $replacements 处颜色值" -ForegroundColor Green
        } else {
            Write-Host "  - 未发现需要替换的颜色值" -ForegroundColor Gray
        }

        Write-Host ""
    } else {
        Write-Host "文件不存在: $file" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "=== 优化完成 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步建议:" -ForegroundColor Yellow
Write-Host "1. 在浏览器中测试所有页面" -ForegroundColor White
Write-Host "2. 检查控制台是否有错误" -ForegroundColor White
Write-Host "3. 验证视觉效果是否一致" -ForegroundColor White
