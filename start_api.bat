@echo off
setlocal ENABLEEXTENSIONS

REM Set console to UTF-8 to avoid encoding issues
chcp 65001 >nul

REM Change to script directory
cd /d %~dp0

REM Title
title Starting OD Data Processing and Simulation System API Service

echo(Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo(Error: Python not found, please install Python 3.8+ first
    pause
    exit /b 1
)

echo(Checking dependencies...
REM Use consistent Python detection to avoid environment mismatch
python -c "import fastapi" >nul 2>&1
set "HAS_FASTAPI=%ERRORLEVEL%"
python -c "import uvicorn" >nul 2>&1
set "HAS_UVICORN=%ERRORLEVEL%"
set "NEED_INSTALL="
if not "%HAS_FASTAPI%"=="0" set "NEED_INSTALL=1"
if not "%HAS_UVICORN%"=="0" set "NEED_INSTALL=1"
if defined NEED_INSTALL (
    echo(First run or missing dependencies, installing packages...

    REM Priority: mamba, then conda; fallback to python -m pip
    where mamba >nul 2>&1
    if "%ERRORLEVEL%"=="0" (
        if defined CONDA_DEFAULT_ENV (
            echo(Detected mamba with Conda environment %CONDA_DEFAULT_ENV%, using mamba run...
            mamba run -n "%CONDA_DEFAULT_ENV%" python -m pip install -r requirements.txt
            set "INSTALL_EXIT=%ERRORLEVEL%"
        ) else (
            echo(Detected mamba but no active Conda environment, fallback to python -m pip...
            python -m pip install -r requirements.txt
            set "INSTALL_EXIT=%ERRORLEVEL%"
        )
    ) else (
        where conda >nul 2>&1
        if "%ERRORLEVEL%"=="0" (
            if defined CONDA_DEFAULT_ENV (
                echo(Detected conda environment %CONDA_DEFAULT_ENV%, using conda run...
                conda run -n "%CONDA_DEFAULT_ENV%" python -m pip install -r requirements.txt
                set "INSTALL_EXIT=%ERRORLEVEL%"
            ) else (
                echo(Detected conda but no active environment, fallback to python -m pip...
                python -m pip install -r requirements.txt
                set "INSTALL_EXIT=%ERRORLEVEL%"
            )
        ) else (
            echo(No mamba/conda detected, using python -m pip...
            python -m pip install -r requirements.txt
            set "INSTALL_EXIT=%ERRORLEVEL%"
        )
    )

    if not "%INSTALL_EXIT%"=="0" (
        echo(Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo(Starting API service with auto-reload...
set PYTHONUTF8=1
python -X utf8 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

pause
exit /b 0 