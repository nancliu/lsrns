@echo off
echo ===== TAZ文件修复工具 =====
echo.

REM 设置Python路径
set PYTHON=python

REM 检查Python是否可用
%PYTHON% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python未找到，请确保Python已安装并添加到PATH环境变量中
    exit /b 1
)

echo 步骤1: 分析TAZ文件中的重复ID
%PYTHON% analyze_duplicate_taz.py
echo.

echo 步骤2: 修复TAZ文件中的重复定义并更新DLLtest2025_6_3.py
%PYTHON% fix_duplicate_taz.py
echo.

echo 处理完成!
echo 修复后的文件保存在: ..\sim_scripts\TAZ_5_fixed.add.xml
echo DLLtest2025_6_3.py已更新，使用修复后的TAZ文件
echo.

pause 