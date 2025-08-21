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
REM 使用与当前 Python 一致的方式检测依赖，避免环境不一致
python -c "import fastapi" >nul 2>&1
set "HAS_FASTAPI=%ERRORLEVEL%"
python -c "import uvicorn" >nul 2>&1
set "HAS_UVICORN=%ERRORLEVEL%"
set "NEED_INSTALL="
if not "%HAS_FASTAPI%"=="0" set "NEED_INSTALL=1"
if not "%HAS_UVICORN%"=="0" set "NEED_INSTALL=1"
if defined NEED_INSTALL (
    echo(首次运行或依赖缺失，正在安装依赖包...

    REM 优先使用 mamba，其次 conda；若无可用，则回退到 python -m pip
    where mamba >nul 2>&1
    if "%ERRORLEVEL%"=="0" (
        if defined CONDA_DEFAULT_ENV (
            echo(检测到 mamba 与 Conda 环境 %CONDA_DEFAULT_ENV%，使用 mamba run 安装...
            mamba run -n "%CONDA_DEFAULT_ENV%" python -m pip install -r requirements.txt
            set "INSTALL_EXIT=%ERRORLEVEL%"
        ) else (
            echo(检测到 mamba，但无激活的 Conda 环境，回退使用 python -m pip...
            python -m pip install -r requirements.txt
            set "INSTALL_EXIT=%ERRORLEVEL%"
        )
    ) else (
        where conda >nul 2>&1
        if "%ERRORLEVEL%"=="0" (
            if defined CONDA_DEFAULT_ENV (
                echo(检测到 conda 环境 %CONDA_DEFAULT_ENV%，使用 conda run 安装...
                conda run -n "%CONDA_DEFAULT_ENV%" python -m pip install -r requirements.txt
                set "INSTALL_EXIT=%ERRORLEVEL%"
            ) else (
                echo(检测到 conda，但无激活的环境，回退使用 python -m pip...
                python -m pip install -r requirements.txt
                set "INSTALL_EXIT=%ERRORLEVEL%"
            )
        ) else (
            echo(未检测到 mamba/conda，使用 python -m pip 安装...
            python -m pip install -r requirements.txt
            set "INSTALL_EXIT=%ERRORLEVEL%"
        )
    )

    if not "%INSTALL_EXIT%"=="0" (
        echo(错误: 依赖包安装失败
        pause
        exit /b 1
    )
)

echo(启动API服务(启用自动重启)...
set PYTHONUTF8=1
python -X utf8 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

pause
exit /b 0 