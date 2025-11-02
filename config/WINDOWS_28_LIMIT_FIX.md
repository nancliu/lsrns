# Windows 28个任务限制解决方案

## 问题确认

在24核服务器上，配置了36个并发任务，但实际只能同时启动**28个SUMO任务**。这是Windows系统的子进程创建限制导致的。

## 快速解决方案

### 方案1: 将并发数设置为28（已应用）

已修改配置文件：
```json
{
  "batch_simulation": {
    "concurrent_simulations_ratio": 1.17,  // 24 × 1.17 = 28.08 ≈ 28
    "min_concurrent": 4,
    "max_concurrent": 80
  }
}
```

这样正好是28个并发任务，不会超出系统限制。

### 方案2: 增加Windows句柄限制（需要管理员权限）

如果需要超过28个任务，可以尝试修改Windows注册表：

```powershell
# 以管理员身份运行PowerShell

# 增加TCP连接数限制
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" `
    -Name "MaxUserPort" -Value 65534 -PropertyType DWORD -Force

New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" `
    -Name "TcpNumConnections" -Value 16777214 -PropertyType DWORD -Force

# 重启计算机使更改生效
```

**注意**：修改注册表有风险，请先备份，并确认了解后果。

## 验证

重启API服务后，运行诊断脚本：
```powershell
.\scripts\diagnose_28_limit.ps1
```

应该看到约28个SUMO进程在运行。

## 为什么是28？

这个限制可能是：
- Windows进程创建器的内部限制
- 文件句柄池的限制
- 系统资源管理器的保护机制

28 ≈ 24核心 + 4个额外进程（系统保留或缓冲）

## 长期解决方案

如果需要更多并发，考虑：
1. **使用Linux服务器**（通常限制更宽松）
2. **重构代码使用multiprocessing.Pool**（更好的资源管理）
3. **分布式部署**（多台服务器分担负载）

## 当前配置状态

- ✅ 并发比例：1.17
- ✅ 预期并发数：28个
- ✅ 适配系统限制：是

重启API服务后，新批次将使用28个并发任务。

