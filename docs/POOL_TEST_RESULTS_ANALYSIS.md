# multiprocessing.Pool 测试结果分析

## 测试结果

✅ **成功完成36个任务**
✅ **进程数达到51个**（超过28个限制）
✅ **使用28个工作进程**

## 关键发现

### 1. 确实突破了28个限制

从测试日志可以看到：
- 初始28个工作进程全部创建成功 ✅
- 当提交30个任务时，**进程数达到51个**
- 这说明工作进程可以创建子进程，突破了主进程的28个限制

### 2. 当前行为：串行处理

从日志可以看到执行模式：
```
[Worker 17364] Completed task 2
[Worker 17364] Starting task 29  ← 工作进程完成一个任务后立即处理下一个
```

**这意味着**：
- 同时运行的任务数 = 工作进程数 = 28个
- 而不是同时运行36个任务
- 当28个任务完成后，工作进程会处理剩余任务

### 3. 要同时运行36个SUMO进程，需要不同策略

如果要**真正同时运行36个SUMO进程**，有两种方案：

#### 方案A：增加工作进程数到36（简单但可能受限）

```python
pool = Pool(processes=36)  # 而不是28
```

**问题**：
- 仍然可能受Windows限制（如果限制是针对主进程的子进程总数）
- 需要测试是否能创建36个工作进程

#### 方案B：每个工作进程创建多个SUMO子进程（复杂但更灵活）

```python
def worker_function(task_batch):
    """每个工作进程处理一批任务，同时运行多个SUMO"""
    processes = []
    for task in task_batch:
        proc = subprocess.Popen([sumo_binary, ...])
        processes.append(proc)
    
    # 等待所有完成
    for proc in processes:
        proc.wait()
```

**问题**：
- 每个工作进程需要管理多个子进程
- 复杂度较高
- 仍然可能受工作进程的子进程限制

## 实际SUMO场景分析

### 场景1：短任务（几秒到几分钟）

**串行模式（28个工作进程）效果**：
- ✅ 足够好：任务完成快，总耗时接近同时运行36个
- ✅ 资源占用稳定：始终只有28个SUMO进程
- ✅ 系统稳定：不会过载

### 场景2：长任务（10分钟以上）

**串行模式的问题**：
- ⚠️ 如果任务是28个一组提交，可能等待时间较长
- ⚠️ 不如同时运行36个快

**解决方案**：增加工作进程数到36

## 推荐策略

### 阶段1：测试36个工作进程（最简单）

修改配置，让Pool使用36个工作进程：

```python
# 在 batch_simulation_scheduler.py 中
max_concurrent = get_max_concurrent_simulations()  # 36
pool = Pool(processes=max_concurrent)  # 36个工作进程
```

**如果成功**：
- ✅ 同时运行36个SUMO任务
- ✅ 代码改动最小

**如果失败**（仍然只能创建28个工作进程）：
- ⚠️ 回到当前串行模式
- ⚠️ 或者考虑方案B

### 阶段2：如果36个工作进程失败，考虑混合模式

保持28个工作进程，但每个工作进程可以管理多个SUMO任务：

```python
def run_sumo_task_group(task_list):
    """每个工作进程运行多个SUMO任务"""
    procs = []
    for task in task_list:
        proc = subprocess.Popen([sumo_binary, ...])
        procs.append(proc)
    
    # 等待全部完成
    for proc in procs:
        proc.wait()
    return results

# 分配任务
with Pool(processes=28) as pool:
    # 每个工作进程处理多个任务
    pool.map(run_sumo_task_group, batched_tasks)
```

## 验证方法

### 测试36个工作进程

创建一个简单的测试：

```python
with Pool(processes=36) as pool:
    # 提交36个立即执行的任务
    results = pool.map(run_dummy_task, range(36))
    
# 在任务执行时，统计Python进程数
# 如果达到 36 + 36*N（N是每个任务创建的子进程数），说明成功
```

## 结论

**Pool方式确实可以突破28个限制**，但：
1. **当前实现**：28个工作进程串行处理（同时28个，不是36个）
2. **要同时36个**：需要36个工作进程或改变任务分配策略
3. **建议**：先测试36个工作进程是否可行

