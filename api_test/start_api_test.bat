@echo off
echo Starting API test environment...

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not detected. Please make sure Python is installed and added to PATH.
    pause
    exit /b
)

:: Display Python path information
echo.
echo Python environment information:
python -c "import sys; print('Python interpreter: ' + sys.executable)"
echo.

:: Check for required modules
echo Checking required Python modules...
python -c "import importlib.util; print('FastAPI installed:', importlib.util.find_spec('fastapi') is not None)" > temp.txt
set /p FASTAPI_INSTALLED=<temp.txt
python -c "import importlib.util; print('Uvicorn installed:', importlib.util.find_spec('uvicorn') is not None)" > temp.txt
set /p UVICORN_INSTALLED=<temp.txt
python -c "import importlib.util; print('Psycopg2 installed:', importlib.util.find_spec('psycopg2') is not None)" > temp.txt
set /p PSYCOPG2_INSTALLED=<temp.txt
del temp.txt

:: Check if all modules are installed
if "%FASTAPI_INSTALLED%"=="FastAPI installed: True" (
    if "%UVICORN_INSTALLED%"=="Uvicorn installed: True" (
        if "%PSYCOPG2_INSTALLED%"=="Psycopg2 installed: True" (
            echo All required modules are installed.
            goto StartServers
        )
    )
)

:: Install missing modules
echo Some required modules are missing. Installing...
pip install fastapi uvicorn psycopg2-binary pandas lxml
echo.

:StartServers
:: Get the project root directory (parent of api_test)
set PROJECT_ROOT=%~dp0..
set SIM_SCRIPTS=%PROJECT_ROOT%\sim_scripts

:: First, start the FastAPI server from sim_scripts directory
echo Starting FastAPI server from sim_scripts directory...
start cmd /k "cd %SIM_SCRIPTS% && python DLLtest2025_6_3.py"

:: Wait for FastAPI server to start
echo Waiting for FastAPI server to initialize (5 seconds)...
timeout /t 5 /nobreak >nul

:: Then start a simple HTTP server
echo Starting HTTP server for API test page...
start cmd /k "cd %PROJECT_ROOT% && python -m http.server 8080"

:: Wait for HTTP server to start
timeout /t 2 /nobreak >nul

:: Open browser to access the page
echo Opening browser...
start http://localhost:8080/api_test/

echo.
echo API test environment has been started!
echo.
echo - FastAPI server running at: http://127.0.0.1:7999/docs
echo - API test page running at: http://localhost:8080/api_test/
echo.
echo Press any key to exit this window...
pause >nul 