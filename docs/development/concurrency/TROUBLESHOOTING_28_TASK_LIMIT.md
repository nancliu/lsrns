# 28个SUMO任务限制问题诊断与解决

## 问题描述

在24核服务器上配置了36个并发任务（比例1.5），但实际只能同时启动**28个SUMO任务**，另外的任务显示"运行中"但进度为0%，等待其他任务完成才开始。

## 可能原因

### 1. Windows进程句柄限制（最可能）

Windows系统对每个进程创建的**子进程句柄数**有限制。虽然默认每个进程可以创建约10,000个句柄，但当创建大量子进程时，可能触及其他限制。

**检查方法**：
```powershell
# 查看当前Python进程的句柄数
Get-Process python | Select-Object Id, Handles, @{Name="Threads";Expression={(Get-Process -Id $_.Id).Threads.Count}}
```

### 2. 文件句柄限制

每个SUMO子进程需要打开多个文件（配置文件、输出文件等），可能触达文件句柄限制。

**Windows默认限制**：
- 每个进程默认约2,048个文件句柄
- 28个SUMO任务 × 每个约10-20个文件句柄 ≈ 280-560个文件句柄

### 3. 内存限制或碎片

虽然总内存充足，但创建新进程需要连续的地址空间，内存碎片可能导致无法创建更多进程。

### 4. Windows子进程创建策略

Windows可能在进程创建时进行节流，防止单个进程创建过多子进程导致系统不稳定。

## 解决方案

### 方案1: 增加Windows进程句柄限制（推荐）

修改Windows注册表以增加句柄限制（需要管理员权限）：

```powershell
# 注意：修改注册表前请备份！

# 1. 打开注册表编辑器
regedit

# 2. 导航到：
HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters

# 3. 创建或修改以下DWORD值：
# MaxUserPort: 65534 (增加TCP端口数)
# TcpNumConnections: 16777214 (增加TCP连接数)

# 或者使用PowerShell（管理员）:
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" -Name "MaxUserPort" -Value 65534 -PropertyType DWORD -Force
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" -Name "TcpNumConnections" -Value 16777214 -PropertyType DWORD -Force
```

**然后重启计算机**以使更改生效。

### 方案2: 使用进程池替代直接subprocess（代码层面）

将subprocess直接创建改为使用multiprocessing.Pool，这样可以更好地管理系统资源：

```python
# 需要修改 shared/data_processors/simulation_processor.py
# 使用进程池而不是直接subprocess.Popen
```

**优点**：
- 更好的资源管理
- 自动处理进程生命周期
- 减少句柄泄露风险

**缺点**：
- 需要重构代码
- 可能影响进度监控

### 方案3: 降低并发数到28（临时方案）

如果无法修改系统配置，可以暂时降低并发比例：

```json
{
  "batch_simulation": {
    "concurrent_simulations_ratio": 1.17,  // 24 × 1.17 ≈ 28
    "min_concurrent": 4,
    "max_concurrent": 80
  }
}
```

这样正好是28个并发任务，不会超出系统限制。

### 方案4: 检查并优化SUMO进程的资源使用

确保每个SUMO进程正确释放资源：

1. **检查进程是否正确终止**：
   ```powershell
   Get-Process | Where-Object { $_.ProcessName -like "*sumo*" } | Select-Object Id, Handles, WorkingSet
   ```

2. **检查是否有僵尸进程**：
   ```powershell
   Get-Process | Where-Object { $_.ProcessName -eq "" }  # 僵尸进程通常没有名称
   ```

3. **在代码中确保进程清理**：
   确保在任务完成后调用 `proc.terminate()` 和 `proc.wait()`。

## 诊断步骤

### 步骤1: 检查当前资源使用

```powershell
# 查看Python进程句柄数
Get-Process python | Format-Table Id, ProcessName, Handles, @{Name="Threads";Expression={(Get-Process -Id $_.Id).Threads.Count}}, WorkingSet -AutoSize

# 查看SUMO进程数
(Get-Process | Where-Object { $_.ProcessName -like "*sumo*" }).Count

# 查看所有进程的句柄数（按句柄数排序）
Get-Process | Sort-Object Handles -Descending | Select-Object -First 10 | Format-Table Id, ProcessName, Handles
```

### 步骤2: 检查系统事件日志

```powershell
# 查看是否有资源不足的错误
Get-EventLog -LogName System -Source "Windows" | Where-Object { $_.Message -like "*resource*" -or $_.Message -like "*handle*" } | Select-Object -First 10
```

### 步骤3: 实时监控

```powershell
# 监控句柄数变化
while ($true) {
    $python = Get-Process python -ErrorAction SilentlyContinue
    $sumo = Get-Process | Where-Object { $_.ProcessName -like "*sumo*" }
    Write-Host "$(Get-Date -Format 'HH:mm:ss') - Python句柄: $($python.Handles) | SUMO进程数: $($sumo.Count)"
    Start-Sleep -Seconds 2
}
```

## 预期结果

- **正常情况**：Python进程句柄数 < 2000，可以创建36个SUMO进程
- **受限情况**：Python进程句柄数接近限制，只能创建约28个SUMO进程

## 推荐方案

1. **短期**：使用方案3，降低并发数到28，确保系统稳定
2. **中期**：实施方案1，增加Windows句柄限制（需要管理员权限和重启）
3. **长期**：考虑方案2，重构代码使用进程池（需要开发工作）

## 验证方法

修改配置或系统后，创建新批次测试：

1. 配置并发数为36
2. 启动批次
3. 观察实际运行的SUMO进程数：
   ```powershell
   (Get-Process | Where-Object { $_.ProcessName -like "*sumo*" }).Count
   ```
4. 如果仍然是28个，说明系统限制仍在，需要进一步调整

