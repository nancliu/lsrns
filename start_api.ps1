# PowerShell 启动脚本（建议以 UTF-8 无 BOM 保存）
param()

$ErrorActionPreference = 'Stop'

# 切到脚本所在目录
Set-Location -LiteralPath $PSScriptRoot

# 统一 UTF-8
$env:PYTHONUTF8 = '1'

Write-Host "[INFO] 当前目录: $PWD"

# 检查 Conda 环境（禁止在 base 安装/运行业务包）
if (-not $env:CONDA_DEFAULT_ENV) {
  Write-Warning '[WARN] 未检测到已激活的 Conda 环境。请先激活非 base 环境后再运行。'
  throw '未激活 Conda 环境'
}
if ($env:CONDA_DEFAULT_ENV -eq 'base') {
  throw '禁止在 base 环境下安装/运行业务包，请先激活业务环境（如 od_project）'
}

# 基础工具检查
try { python --version | Out-Null } catch { throw '未找到 Python，请先安装/配置 Python' }

# 依赖检查（先用当前 Python 试探导入）
$needInstall = $false
try { python -c "import fastapi" | Out-Null } catch { $needInstall = $true }
try { python -c "import uvicorn" | Out-Null } catch { $needInstall = $true }

if ($needInstall) {
  Write-Host "[INFO] 依赖缺失，开始安装（优先 mamba，其次 conda，最后 pip）" -ForegroundColor Yellow

  $envName = $env:CONDA_DEFAULT_ENV
  $installed = $false

  if (Get-Command mamba -ErrorAction SilentlyContinue) {
    try {
      Write-Host "[INFO] 使用 mamba 安装到环境: $envName"
      mamba install -n $envName -c conda-forge fastapi uvicorn -y | Out-Null
      $installed = $true
    } catch {
      Write-Warning "[WARN] mamba 安装失败: $($_.Exception.Message)"
    }
  }

  if (-not $installed -and (Get-Command conda -ErrorAction SilentlyContinue)) {
    try {
      Write-Host "[INFO] 使用 conda 安装到环境: $envName"
      conda install -n $envName -c conda-forge fastapi uvicorn -y | Out-Null
      $installed = $true
    } catch {
      Write-Warning "[WARN] conda 安装失败: $($_.Exception.Message)"
    }
  }

  if (-not $installed) {
    # 仅当非 base 环境时允许 pip 回退
    if ($envName -ne 'base') {
      try {
        Write-Host "[INFO] 使用 pip 回退安装（环境: $envName）"
        python -m pip install --no-input fastapi uvicorn | Out-Null
        $installed = $true
      } catch {
        throw "依赖安装失败：$($_.Exception.Message)"
      }
    } else {
      throw '禁止在 base 环境下使用 pip 安装依赖，请切换到业务环境后再试'
    }
  }
}

# 启动 API 服务
Write-Host '[INFO] 启动 API 服务（http://localhost:8000/docs）'
python -X utf8 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000


