#!/usr/bin/env bash
# Bash startup script for OD Data Processing and Simulation System

set -e

# Change to script directory
cd "$(dirname "$0")"

# Set UTF-8 encoding
export PYTHONUTF8=1
export LC_ALL=en_US.UTF-8

echo "[INFO] Current directory: $(pwd)"

# Check if service is already running on port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "[WARN] Service is already running on port 8000"
    PID=$(lsof -Pi :8000 -sTCP:LISTEN -t)
    echo "[INFO] Stopping existing process (PID: $PID)..."
    kill -15 "$PID" 2>/dev/null || true
    sleep 2
    # Force kill if still running
    if kill -0 "$PID" 2>/dev/null; then
        echo "[WARN] Process still running, force killing..."
        kill -9 "$PID" 2>/dev/null || true
        sleep 1
    fi
    echo "[INFO] Existing service stopped"
fi

# Check Conda environment (prevent running in base)
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "[WARN] No active Conda environment detected. Please activate a non-base environment first."
    exit 1
fi

if [ "$CONDA_DEFAULT_ENV" = "base" ]; then
    echo "[ERROR] Running in base environment is prohibited. Please activate a project environment (e.g., od_project)"
    exit 1
fi

# Check Python
if ! command -v python &> /dev/null; then
    echo "[ERROR] Python not found. Please install/configure Python first"
    exit 1
fi

echo "[INFO] Python version: $(python --version)"

# Check dependencies
NEED_INSTALL=false
if ! python -c "import fastapi" &> /dev/null; then
    NEED_INSTALL=true
fi
if ! python -c "import uvicorn" &> /dev/null; then
    NEED_INSTALL=true
fi

if [ "$NEED_INSTALL" = true ]; then
    echo "[INFO] Dependencies missing, installing (priority: mamba, then conda, fallback to pip)"

    ENV_NAME="$CONDA_DEFAULT_ENV"
    INSTALLED=false

    # Try mamba first
    if command -v mamba &> /dev/null; then
        echo "[INFO] Using mamba to install to environment: $ENV_NAME"
        if mamba install -n "$ENV_NAME" -c conda-forge fastapi uvicorn -y; then
            INSTALLED=true
        else
            echo "[WARN] mamba installation failed"
        fi
    fi

    # Try conda if mamba failed
    if [ "$INSTALLED" = false ] && command -v conda &> /dev/null; then
        echo "[INFO] Using conda to install to environment: $ENV_NAME"
        if conda install -n "$ENV_NAME" -c conda-forge fastapi uvicorn -y; then
            INSTALLED=true
        else
            echo "[WARN] conda installation failed"
        fi
    fi

    # Fallback to pip (only in non-base environment)
    if [ "$INSTALLED" = false ]; then
        if [ "$ENV_NAME" != "base" ]; then
            echo "[INFO] Using pip as fallback (environment: $ENV_NAME)"
            if python -m pip install --no-input fastapi uvicorn; then
                INSTALLED=true
            else
                echo "[ERROR] Dependency installation failed"
                exit 1
            fi
        else
            echo "[ERROR] pip installation in base environment is prohibited. Switch to project environment first."
            exit 1
        fi
    fi
fi

# Start API service
echo "[INFO] Starting API service (http://localhost:8000/)"
python -X utf8 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
