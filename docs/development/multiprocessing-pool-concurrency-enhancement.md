# 使用 multiprocessing.Pool 突破Windows 28任务限制 - 未来计划

## 状态

**状态**: 📋 未来计划  
**优先级**: P1（高价值，非紧急）  
**预估工作量**: 2-3周  
**依赖**: 无

## 问题背景

### 当前限制

在24核服务器上，使用 `subprocess.Popen` 直接创建SUM子进程时，存在**Windows系统级别的28个子进程限制**：

- 配置了36个并发任务（比例1.5）
- 实际只能同时启动28个SUM任务
- 剩余任务显示"运行中"但进度为0%，等待其他任务完成后才开始

### 根本原因

Windows系统限制**主进程直接创建的子进程数**约为28个：

```
主进程 (Python API)
  ↓ 直接创建（受限28个）
子进程1 (SUMO) - subprocess.Popen
子进程2 (SUMO) - subprocess.Popen
...
子进程28 (SUMO) - 达到限制 ❌
子进程29 (SUMO) - 无法创建，等待中...
```

## 解决方案：multiprocessing.Pool

### 方案原理

使用 `multiprocessing.Pool` 创建固定数量的**工作进程**，每个工作进程独立创建SUM子进程：

```
主进程 (Python API)
  ↓ 创建进程池（固定数量工作进程，比如36个）
工作进程1 (Worker Process)
工作进程2 (Worker Process)
...
工作进程36 (Worker Process)
  ↓ 每个工作进程独立创建SUM子进程
  工作进程1 → SUMO子进程1
  工作进程2 → SUMO子进程2
  ...
  工作进程36 → SUMO子进程36
```

**关键优势**：
- 工作进程是主进程的子进程，但它们是**独立进程**，有独立资源配额
- 工作进程创建的SUM子进程是"孙进程"，不受主进程的28个限制影响
- 理论上可以同时运行36-48个或更多SUM任务

### 测试验证结果

**测试日期**: 2025-11-02  
**测试脚本**: `scripts/test_36_workers.py`

**测试结果**：
- ✅ **成功创建36个工作进程**
- ✅ **使用36个不同的Worker PID**
- ✅ **所有36个任务完成**
- ✅ **进程数达到51个**（说明工作进程可以创建子进程）

**结论**：`multiprocessing.Pool` 确实可以突破28个限制，理论上可以同时运行36个SUM任务。

## 实施方案

### 架构变更

**当前架构** (`shared/control_tools/batch_simulation_scheduler.py`):
```python
# 异步方式 + semaphore控制
async def start_batch(...):
    max_concurrent = get_max_concurrent_simulations()  # 36
    self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async_tasks = []
    for task in tasks:
        async_task = self._run_task(...)
        async_tasks.append(async_task)
    
    await asyncio.gather(*async_tasks)
```

**目标架构**:
```python
# 混合模式：异步框架 + 进程池执行器
from multiprocessing import Pool
from concurrent.futures import ProcessPoolExecutor

async def start_batch(...):
    max_concurrent = get_max_concurrent_simulations()  # 36
    loop = asyncio.get_event_loop()
    
    # 使用ProcessPoolExecutor包装Pool
    with ProcessPoolExecutor(max_workers=max_concurrent) as executor:
        # 提交所有任务
        futures = [
            loop.run_in_executor(executor, run_sumo_task_sync, task)
            for task in tasks
        ]
        
        # 等待所有完成
        results = await asyncio.gather(*futures)
```

### 关键改动点

#### 1. 任务执行函数改为同步

```python
# shared/control_tools/batch_simulation_scheduler.py

def run_sumo_task_sync(
    case_id: str,
    batch_id: str,
    task_data: Dict[str, Any],
    base_dir: str,
    simulation_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    同步版本的SUM任务执行函数
    用于multiprocessing.Pool
    """
    # 1. 创建仿真目录
    # 2. 调用simulation_processor.run_simulation()（同步）
    # 3. 更新进度（通过文件写入）
    # 4. 返回结果
    pass
```

#### 2. 进度监控机制

**问题**：Pool工作进程无法直接访问主进程的状态  
**解决**：通过文件系统共享状态

```python
# 工作进程通过写入文件更新进度
progress_file = batch_dir / f"{task_id}_progress.json"
with open(progress_file, 'w') as f:
    json.dump({"progress": percent, ...}, f)

# 主进程定期读取文件更新UI
async def monitor_progress():
    while batch_running:
        # 读取所有任务的进度文件
        # 更新batch_progress.json
        await asyncio.sleep(2)
```

#### 3. 错误处理和取消机制

```python
# 支持任务取消
futures = {}
for task in tasks:
    future = executor.submit(run_sumo_task_sync, ...)
    futures[task.task_id] = future

# 取消任务
if task_id in futures:
    futures[task_id].cancel()
    # 终止对应的SUM进程
```

## 实施步骤

### Phase 1: 准备工作（1周）

1. **设计详细方案**
   - [ ] 设计同步任务执行函数接口
   - [ ] 设计文件系统的进度共享机制
   - [ ] 设计错误处理和取消流程

2. **创建原型实现**
   - [ ] 实现 `run_sumo_task_sync()` 函数
   - [ ] 实现文件进度监控机制
   - [ ] 创建测试用例

3. **验证可行性**
   - [ ] 运行完整测试，验证36个任务同时运行
   - [ ] 验证进度监控正常工作
   - [ ] 验证错误处理正确

### Phase 2: 实现（1-2周）

1. **重构 batch_simulation_scheduler.py**
   - [ ] 实现 `start_batch_with_pool()` 方法
   - [ ] 保留原有的 `start_batch()` 作为备选
   - [ ] 添加配置开关选择使用哪种方式

2. **实现进度监控**
   - [ ] 实现文件系统的进度共享
   - [ ] 实现主进程的进度读取和更新
   - [ ] 集成到现有的进度API

3. **错误处理和取消**
   - [ ] 实现任务取消机制
   - [ ] 实现进程终止和清理
   - [ ] 错误日志和报告

### Phase 3: 测试和验证（1周）

1. **功能测试**
   - [ ] 测试36个任务同时运行
   - [ ] 测试进度监控准确性
   - [ ] 测试错误处理
   - [ ] 测试任务取消

2. **性能测试**
   - [ ] 对比28个任务 vs 36个任务的总耗时
   - [ ] 监控资源使用（CPU、内存）
   - [ ] 验证性能提升

3. **稳定性测试**
   - [ ] 长时间运行测试
   - [ ] 压力测试（大量批次）
   - [ ] 异常场景测试

## 风险评估

### 技术风险

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| 进度监控不准确 | 中 | 高 | 使用文件系统锁，增加重试机制 |
| 进程泄露 | 低 | 高 | 严格的生命周期管理，定期检查 |
| 错误传播问题 | 中 | 中 | 详细的异常处理和日志记录 |
| 性能未提升 | 低 | 中 | 先进行充分测试验证 |

### 代码质量风险

- **代码复杂度增加**：需要管理异步和同步两套逻辑
- **维护成本**：需要维护Pool版本和原版本
- **测试覆盖**：需要为新的执行路径编写测试

### 推荐缓解措施

1. **保留原实现**：作为fallback，通过配置开关切换
2. **渐进式部署**：先在测试环境验证，再逐步推广
3. **充分测试**：特别是进度监控和错误处理

## 预期收益

### 性能提升

假设36个任务同时运行：
- **总耗时**: 预计减少 20-30%（相比28个串行）
- **CPU利用率**: 从100%提升到150%
- **吞吐量**: 提升约28%

### 其他收益

- ✅ 突破Windows限制，支持更高并发
- ✅ 更稳定的进程管理（Pool自动处理崩溃）
- ✅ 更好的资源利用（充分利用多核CPU）

## 实施前提条件

1. **测试验证**：已完成 ✅
   - 已验证Pool可以创建36个工作进程
   - 已验证工作进程可以创建子进程

2. **需求确认**：
   - [ ] 确认是否需要超过28个并发
   - [ ] 确认性能提升是否值得实施成本

3. **资源准备**：
   - [ ] 分配开发时间（2-3周）
   - [ ] 准备测试环境

## 备选方案

### 如果Pool方案不可行

1. **修改Windows注册表**（需要管理员权限）
   - 增加系统句柄限制
   - 需要重启服务器

2. **使用Linux服务器**
   - Linux限制通常更宽松
   - 可能无需修改代码

3. **分布式部署**
   - 多台服务器分担负载
   - 需要额外的基础设施

## 参考文档

- **测试脚本**: `scripts/test_multiprocessing_pool.py`, `scripts/test_36_workers.py`
- **分析文档**: `docs/MULTIPROCESSING_POOL_ANALYSIS.md`, `docs/POOL_TEST_RESULTS_ANALYSIS.md`
- **问题诊断**: `docs/TROUBLESHOOTING_28_TASK_LIMIT.md`

## 决策建议

### 建议暂时不实施的理由

1. **当前方案已足够**：
   - 28个并发已经充分利用24核CPU（100%利用率）
   - 系统稳定，无重大问题

2. **实施成本较高**：
   - 需要2-3周开发时间
   - 增加代码复杂度
   - 需要充分测试

3. **收益有限**：
   - 36个并发虽然更快，但可能带来系统不稳定
   - 实际性能提升可能不如预期（受I/O限制）

### 建议实施的理由

1. **已验证可行**：测试证明Pool可以突破限制
2. **性能提升明显**：理论上可以提升20-30%吞吐量
3. **技术储备**：为未来更高并发需求做准备

## 决策时间点

**建议在以下情况考虑实施**：
- 批量仿真任务量显著增加
- 用户明确要求更快的执行速度
- 有充足的开发和测试时间
- 确认28个并发确实成为瓶颈

**当前状态**：记录为未来计划，暂不实施。

---

**文档创建日期**: 2025-11-02  
**最后更新**: 2025-11-02  
**维护者**: 开发团队

