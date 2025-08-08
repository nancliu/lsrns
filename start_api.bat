@echo off
setlocal ENABLEEXTENSIONS

REM 设置控制台为UTF-8，避免中文乱码/误判
chcp 65001 >nul

REM 切换到脚本所在目录
cd /d %~dp0

REM 标题
title 启动OD数据处理与仿真系统API服务

echo(正在检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo(错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo(正在检查依赖包...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo(首次运行，正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo(错误: 依赖包安装失败
        pause
        exit /b 1
    )
)

echo(启动API服务...
python -X utf8 api/main.py

pause
exit /b 0 