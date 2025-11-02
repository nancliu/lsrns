# 并发数配置排查指南

## 问题：修改配置后仍然是18个并发任务

### 可能原因

1. **API服务未真正重启**
   - Python模块在导入时加载到内存
   - 需要完全停止并重启服务

2. **查看运行中的批次**
   - 旧的批次（修改配置前启动）仍使用旧的并发数
   - 只有新启动的批次才会使用新配置

3. **环境变量覆盖**
   - 检查是否有 `MAX_CONCURRENT_SIMULATIONS` 或 `MAX_CONCURRENT_SIMULATIONS_RATIO` 环境变量

### 排查步骤

#### 步骤1: 验证配置是否正确加载

```powershell
python -c "from shared.control_tools.batch_simulation_scheduler import get_max_concurrent_simulations; import logging; logging.basicConfig(level=logging.INFO); result = get_max_concurrent_simulations(); print(f'并发数: {result}')"
```

**期望输出**：
- 24核 × 1.0 = 24 个并发任务
- 如果看到18，说明仍在使用旧配置（0.75比例）

#### 步骤2: 检查环境变量

```powershell
# 检查是否有环境变量覆盖
$env:MAX_CONCURRENT_SIMULATIONS
$env:MAX_CONCURRENT_SIMULATIONS_RATIO

# 如果设置了，需要清除或修改
Remove-Item Env:\MAX_CONCURRENT_SIMULATIONS
Remove-Item Env:\MAX_CONCURRENT_SIMULATIONS_RATIO
```

#### 步骤3: 确认API服务重启

```powershell
# 检查Python进程的启动时间
Get-Process | Where-Object { $_.ProcessName -like "*python*" } | Select-Object Id, ProcessName, StartTime

# 如果启动时间在修改配置之前，需要重启服务
```

#### 步骤4: 创建新批次测试

1. **停止所有正在运行的批次**
2. **创建新批次**
3. **启动新批次**
4. **检查实际并发数**

新批次应该使用最新配置（24个并发任务）。

### 验证方法

创建新批次后，查看API日志，应该看到：

```
INFO: Loaded concurrent_simulations_ratio=1.0 from D:\projects\OD_SIM\config\system_config.json
INFO: Concurrency calculation: 24 CPUs * 1.0 = 24, clamped to [4, 80] -> 24
INFO: Starting batch batch_xxx with max 24 concurrent tasks
```

如果看到：
```
INFO: Concurrency calculation: 24 CPUs * 0.75 = 18, clamped to [4, 80] -> 18
```

说明仍在使用了旧配置（默认0.75），可能的原因：
- API服务未重启
- 配置文件路径错误
- 配置文件格式错误

### 快速修复

如果确认配置正确但仍看到18个任务：

1. **完全停止API服务**（关闭所有Python进程）
2. **清除环境变量**（如果有）
3. **验证配置文件**：
   ```powershell
   python -c "import json; config = json.load(open('config/system_config.json', 'r', encoding='utf-8')); print(config['batch_simulation']['concurrent_simulations_ratio'])"
   ```
   应该输出：`1`
4. **重启API服务**
5. **创建新批次测试**

