# multiprocessing.Pool vs subprocess.Popen 分析

## 当前实现方式

**架构**：
```
主进程 (Python API)
  ↓ 直接创建
子进程1 (SUMO) - subprocess.Popen
子进程2 (SUMO) - subprocess.Popen
子进程3 (SUMO) - subprocess.Popen
...
子进程28 (SUMO) - 达到限制 ❌
子进程29 (SUMO) - 无法创建，等待中...
```

**限制来源**：Windows系统限制**主进程直接创建的子进程数**约为28个。

## 使用 multiprocessing.Pool 的方式

**架构**：
```
主进程 (Python API)
  ↓ 创建进程池（固定数量工作进程，比如28个）
工作进程1 (Worker Process)
工作进程2 (Worker Process)
...
工作进程28 (Worker Process)
  ↓ 每个工作进程独立创建SUMO子进程
  工作进程1 → SUMO子进程1
  工作进程1 → SUMO子进程2 (工作进程1完成任务后创建新的)
  工作进程2 → SUMO子进程3
  ...
```

**关键区别**：
- **subprocess.Popen**：主进程直接管理所有SUMO子进程（受28个限制）
- **multiprocessing.Pool**：工作进程独立创建SUMO子进程（可能突破限制）

## 是否能突破28个限制？

### 理论分析

**情况1：限制是"主进程直接创建的子进程数"**
- ✅ **Pool可以突破**：工作进程是主进程的子进程，但它们可以各自创建SUMO子进程
- 28个工作进程 × 每个可创建SUMO = 可能超过28个

**情况2：限制是"系统中SUM子进程总数"**
- ❌ **Pool无法突破**：最终SUM子进程数量相同，只是创建方式不同

**情况3：限制是"文件句柄或其他资源"**
- ⚠️ **Pool可能有用**：进程池能更好地管理资源，减少泄露

### Windows实际情况

在Windows上，**multiprocessing.Pool 可能能够突破28个限制**，因为：

1. **工作进程独立地址空间**：每个工作进程是独立的进程，有独立的资源配额
2. **进程层级不同**：限制可能是针对"直接子进程"，而工作进程的子进程是"孙进程"
3. **资源管理更好**：Pool自动管理进程生命周期，减少资源泄露

## 预期效果

如果使用Pool：
- **工作进程数**：28个（固定）
- **每个工作进程创建SUM进程数**：理论上无限制（受系统总资源限制）
- **预期总并发SUM任务数**：可能达到36-48个或更多

## 实现方案

### 方案A：简单进程池（推荐测试）

创建工作进程池，每个工作进程负责创建和运行SUMO进程：

```python
from multiprocessing import Pool
import subprocess

def run_sumo_task(task_params):
    """工作进程函数：创建并运行SUMO进程"""
    # 在这个函数中创建SUMO子进程
    proc = subprocess.Popen([...sumo命令...])
    proc.wait()  # 等待完成
    return result

# 创建进程池
pool = Pool(processes=28)  # 28个工作进程
results = pool.map(run_sumo_task, task_list)
```

**优点**：
- 实现相对简单
- 可能突破28个限制
- 自动进程管理

**缺点**：
- 需要重构代码
- 进度监控更复杂
- 异步特性丢失（需要改为同步或混合）

### 方案B：混合模式（更复杂但灵活）

保持异步框架，但使用Pool作为执行器：

```python
# 在异步函数中使用进程池
async def _run_task(...):
    loop = asyncio.get_event_loop()
    with Pool(processes=28) as pool:
        result = await loop.run_in_executor(
            pool, run_sumo_task, task_params
        )
```

## 验证方法

### 测试步骤

1. **实现Pool版本**
2. **配置并发数为36**
3. **创建测试批次**
4. **监控实际运行的SUM进程数**：
   ```powershell
   Get-Process | Where-Object { $_.ProcessName -like "*sumo*" } | Measure-Object | Select-Object Count
   ```
5. **如果超过28个**：说明Pool成功突破限制 ✅
6. **如果仍然是28个**：说明限制是系统级别的，Pool无法突破 ❌

## 风险评估

### ✅ 优点

1. **可能突破28个限制**：工作进程可以创建自己的子进程
2. **更好的资源管理**：进程池自动管理进程生命周期
3. **减少句柄泄露**：进程池确保资源正确释放
4. **更稳定**：进程池处理进程崩溃和重启

### ⚠️ 风险

1. **代码重构工作量大**：需要修改核心执行逻辑
2. **进度监控复杂**：需要新的机制来监控工作进程中的任务
3. **异步特性丢失**：Pool是同步的，需要适配异步框架
4. **测试工作量大**：需要充分测试确保功能正常

## 推荐决策

### 如果目标是突破28个限制：

**推荐先尝试简单测试**：

1. 创建一个独立的测试脚本，使用Pool运行36个SUMO任务
2. 观察是否能突破28个限制
3. 如果能，再决定是否重构生产代码

### 如果28个已经足够：

**保持当前实现**：
- 当前代码已经稳定
- 28个并发已经充分利用24核CPU
- 重构风险大于收益

## 下一步

如果需要测试Pool方案，我可以：
1. 创建一个测试脚本验证Pool能否突破限制
2. 如果成功，提供重构方案
3. 如果失败，提供其他解决方案（如注册表修改）

