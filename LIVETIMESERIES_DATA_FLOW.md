# liveTimeSeries 数据流追踪

**生成日期**: 2025-10-30
**关键问题**: 如果 liveTimeSeries 未生成，曲线渲染函数无法工作
**现状**: 部分情况下无法生成，导致曲线显示为"仿真数据加载中..."

---

## 🎯 快速答案

### liveTimeSeries 是由哪个函数生成的？

**答案**: `_aggregate_live_time_series()` 方法

**位置**: `api/services/batch_optimization_service.py` 第445-552行

**完整调用链**:
```
前端轮询
  ↓
GET /api/v1/control/optimization/batch/{batch_id}/progress
  ↓
batch_optimization_routes.py
  ↓
batch_optimization_service.get_batch_progress()  (第607-655行)
  ↓
_aggregate_live_time_series()  ← 🔴 生成 liveTimeSeries 的地方
  ├─ _extract_summary_time_series()  ← 从summary.xml读数据
  └─ 返回 {time_points, total_running, ...}
  ↓
返回API响应
  ↓
前端 renderLiveCurve(liveTimeSeries)
```

---

## 📍 生成位置详细分析

### 1️⃣ 入口：`get_batch_progress()` 方法

**文件**: `api/services/batch_optimization_service.py`
**行号**: 607-655
**调用者**: API路由 `/control/optimization/batch/{batch_id}/progress`

```python
def get_batch_progress(self, case_id: str, batch_id: str) -> Dict[str, Any]:
    """获取批次进度（包含live_status和live_time_series）"""

    try:
        # 第1步: 读取批次进度
        progress_data = self.scheduler.get_batch_progress(case_id, batch_id)

        # 第2步: 为每个任务添加live_status
        for task_dict in progress_data["tasks"]:
            if task_dict.get('status') in ['running', 'completed']:
                live_status = self._get_simulation_live_status(...)
                task_dict['live_status'] = live_status

        # 第3步: 计算批次剩余时间
        batch_remaining_seconds = self._calculate_batch_remaining_time(...)

        # 🔴 第4步: 生成 liveTimeSeries (行639)
        live_time_series = self._aggregate_live_time_series(
            progress_data["tasks"],
            case_id,
            batch_id
        )

        # 第5步: 组装响应
        response = {
            **progress_data,
            "estimated_completion": estimated_completion,
            "estimated_remaining_seconds": batch_remaining_seconds,
            "live_time_series": live_time_series  # ← 放入响应
        }

        return response
```

**关键行号**:
- 第639行: 调用 `_aggregate_live_time_series()`
- 第652行: 放入响应的 `"live_time_series"` 字段

---

### 2️⃣ 核心生成函数：`_aggregate_live_time_series()`

**文件**: `api/services/batch_optimization_service.py`
**行号**: 445-552

**流程**:

```python
def _aggregate_live_time_series(self, tasks, case_id, batch_id):
    """汇总所有任务的时序数据，生成动态曲线数据"""

    # 第1步: 分类任务 (行473-481)
    running_tasks = [t for t in tasks if t.get('status') == 'running']
    completed_tasks = [t for t in tasks if t.get('status') == 'completed']

    # ❌ 问题：优先级逻辑有缺陷
    data_source_tasks = running_tasks if running_tasks else completed_tasks
    # 这意味着：
    # - 如果有running任务 → 只用running任务的数据
    # - 如果没有running任务 → 才用completed任务的数据
    # 导致：在running任务但summary.xml还未生成时，无法显示任何数据

    # 第2步: 检查是否有数据源 (行483-490)
    if not data_source_tasks:
        return {
            'time_points': [],
            'total_running': [],
            'task_count': 0,
            'last_update': datetime.now().isoformat()
        }

    # 第3步: 汇总所有任务的时序数据 (行492-527)
    aggregated_data = defaultdict(int)

    for task in data_source_tasks:
        # 获取任务信息
        plan_id = task.get('plan_id')
        seed = task.get('seed')

        # 构建summary.xml路径
        simulation_dir = (
            Path(self.cases_base_dir) / case_id / "simulations" / "plan_opti" /
            batch_id / plan_id / f"sim_{seed}"
        )
        summary_file = simulation_dir / "summary.xml"

        # ❌ 关键检查 (行517)
        if not summary_file.exists():
            logger.debug(f"File exists=False")
            continue  # 跳过这个任务

        # 提取时序数据 (行520)
        time_series = self._extract_summary_time_series(summary_file)

        # 汇总数据 (行524-527)
        for entry in time_series:
            time_step = entry['time']
            running_vehicles = entry['running']
            aggregated_data[time_step] += running_vehicles  # ← 求和

    # 第4步: 检查是否有聚合数据 (行532-539)
    if not aggregated_data:
        return {
            'time_points': [],
            'total_running': [],
            'task_count': len(data_source_tasks),
            'last_update': datetime.now().isoformat()
        }

    # 第5步: 转换为数组格式 (行541-552)
    sorted_times = sorted(aggregated_data.keys())
    time_points = sorted_times
    total_running = [aggregated_data[t] for t in sorted_times]

    return {
        'time_points': time_points,
        'total_running': total_running,
        'task_count': len(data_source_tasks),
        'last_update': datetime.now().isoformat()
    }
```

---

## ❌ 为什么 liveTimeSeries 无法生成？

### 根本原因链

```
时间线:

T=0秒: 仿真启动
  └─ progress.json 创建 ✓

T=2秒: 前端轮询 #1
  ├─ _aggregate_live_time_series() 执行
  ├─ 查找 summary.xml
  └─ 🔴 summary.xml 不存在（SUMO还未生成）
      └─ 返回: {'time_points': [], 'total_running': []}
      └─ 前端显示: "仿真数据加载中..."

T=5秒: SUMO 刚刚启动，开始写入 summary.xml
  └─ 但内容还不完整

T=6秒: 前端轮询 #2
  ├─ _aggregate_live_time_series() 执行
  ├─ 查找 summary.xml
  ├─ summary.xml 存在 ✓
  └─ _extract_summary_time_series() 尝试读取
      ├─ 🔴 XML 文件还在被 SUMO 写入（并发读写问题）
      ├─ 可能导致: XML 解析失败
      └─ 返回: 空数据 或异常
         └─ 返回: {'time_points': [], 'total_running': []}

T=10秒: SUMO 继续运行，summary.xml 累积更多数据
  └─ 但仍在写入中

T=300秒: SUMO 仿真完成，summary.xml 写入完成
  ├─ 前端轮询 #150
  └─ _extract_summary_time_series() 成功读取完整数据
      └─ 返回: 完整的 liveTimeSeries ✓
         └─ 前端显示: 完整的曲线 ✓✓✓

问题症状:
  ├─ T=2到T=300秒: 无法看到曲线
  └─ T=300秒后: 曲线才显示
```

### 三个关键问题

#### 问题1: summary.xml 生成延迟

**症状**: T=2秒时，summary.xml 还不存在

**原因**:
- SUMO 需要5-10秒初始化
- 初始化完成后才开始生成 summary.xml

**代码位置** (行517):
```python
if not summary_file.exists():
    logger.debug(f"File exists=False")
    continue  # 返回空数组
```

#### 问题2: 并发读写锁定

**症状**: summary.xml 存在但读取失败或数据不完整

**原因**:
- SUMO 持续写入 summary.xml
- Python 尝试读取同一文件
- 可能导致 XML 解析失败

**代码位置** (行520):
```python
time_series = self._extract_summary_time_series(summary_file)
# ❌ 如果 SUMO 正在写入，这可能失败
```

#### 问题3: 优先级逻辑缺陷

**症状**: 只看 running 任务，看不到 completed 任务的数据

**原因**:
```python
data_source_tasks = running_tasks if running_tasks else completed_tasks
# 这是一个 OR 逻辑，不是 AND

# 导致:
# - 如果有running任务但summary.xml未生成 → 无法显示
# - 应该改为: 同时使用running和completed任务的数据
```

**代码位置** (行477):
```python
data_source_tasks = running_tasks if running_tasks else completed_tasks
```

---

## 📊 返回值分析

### 成功时 (有数据)

```python
{
    'time_points': [0, 1, 2, 3, ..., 300],
    'total_running': [100, 150, 200, 250, ..., 50],
    'task_count': 3,
    'last_update': '2025-10-30T10:25:00'
}
```

**前端处理**:
```javascript
function renderLiveCurve(liveTimeSeries) {
    const hasData = liveTimeSeries &&
                    liveTimeSeries.time_points &&
                    liveTimeSeries.time_points.length > 0;  // ← TRUE

    if (!hasData) return;  // 不执行

    // 绘制曲线 ✓
    const chart = new Chart(ctx, {
        data: {
            datasets: [{
                data: liveTimeSeries.total_running  // ✓ 显示
            }]
        }
    });
}
```

### 失败时 (无数据)

```python
{
    'time_points': [],
    'total_running': [],
    'task_count': 3,
    'last_update': '2025-10-30T10:25:00'
}
```

**前端处理**:
```javascript
function renderLiveCurve(liveTimeSeries) {
    const hasData = liveTimeSeries &&
                    liveTimeSeries.time_points &&
                    liveTimeSeries.time_points.length > 0;  // ← FALSE

    if (!hasData) {
        // 显示加载提示
        section.innerHTML = '<div>仿真数据加载中...</div>';
        return;  // ← 无法绘制曲线
    }
}
```

---

## 🔍 调试方法

### 后端调试

**添加日志**:
```python
def _aggregate_live_time_series(self, tasks, case_id, batch_id):
    # 添加日志输出
    logger.info(f"🔍 [DEBUG] _aggregate_live_time_series called")
    logger.info(f"   running_tasks: {len(running_tasks)}")
    logger.info(f"   completed_tasks: {len(completed_tasks)}")
    logger.info(f"   data_source_tasks: {len(data_source_tasks)}")

    for task in data_source_tasks:
        summary_file = simulation_dir / "summary.xml"
        logger.info(f"   Checking {summary_file}: {summary_file.exists()}")

        if summary_file.exists():
            logger.info(f"   File size: {summary_file.stat().st_size} bytes")
            logger.info(f"   Last modified: {datetime.fromtimestamp(summary_file.stat().st_mtime)}")
```

**查看API响应**:
```bash
curl -X GET "http://localhost:8000/api/v1/control/optimization/batch/batch_001/progress" \
  | python -m json.tool | grep -A 20 "live_time_series"
```

### 前端调试

**打开F12 Console**:
```javascript
// 观察 liveTimeSeries 的内容
在 batch_simulation.js 第384行添加:
console.log('=== liveTimeSeries ===', data.live_time_series);
console.log('  time_points:', data.live_time_series?.time_points?.length);
console.log('  total_running:', data.live_time_series?.total_running?.length);
console.log('  task_count:', data.live_time_series?.task_count);
```

### 文件系统检查

```bash
# 检查 summary.xml 是否存在
ls -la "D:\projects\OD_SIM\cases\case_001\simulations\plan_opti\batch_001\plan_001\sim_66\summary.xml"

# 检查文件大小（增长表示SUMO还在写）
watch -n 1 'ls -lh "D:\projects\OD_SIM\cases\case_001\simulations\plan_opti\batch_001\plan_001\sim_66\summary.xml"'

# 查看最近修改的summary.xml
find "D:\projects\OD_SIM\cases" -name "summary.xml" -type f -printf '%T@ %p\n' | sort -rn | head -5
```

---

## 🔧 改进方案

### 方案A: 添加重试机制 (简单)

```python
def _extract_summary_time_series(self, summary_file):
    """从summary.xml提取时序数据，支持重试"""

    max_retries = 3
    retry_delay = 0.5  # 秒

    for attempt in range(max_retries):
        try:
            tree = ET.parse(summary_file)
            root = tree.getroot()

            time_series = []
            for step in root.findall('step'):
                time_series.append({
                    'time': int(step.get('time')),
                    'running': int(step.get('running'))
                })

            return time_series

        except ET.ParseError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Parse error (attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to parse {summary_file} after {max_retries} attempts")
                return []
```

### 方案B: 使用 JSON 缓存 (推荐)

**创建 `live_curve.json`** 文件，由后端定期同步 summary.xml 的最新数据：

```python
def _aggregate_live_time_series(self, tasks, case_id, batch_id):
    """优先使用 live_curve.json，降级到 summary.xml"""

    for task in data_source_tasks:
        # 优先读取 live_curve.json (实时同步的缓存)
        live_curve_file = simulation_dir / "live_curve.json"

        if live_curve_file.exists():
            try:
                with open(live_curve_file, 'r') as f:
                    curve_data = json.load(f)
                    return {
                        'time_points': curve_data['time_points'],
                        'total_running': curve_data['total_running'],
                        'task_count': len(data_source_tasks),
                        'last_update': curve_data['updated_at'],
                        'source': 'live_curve_cache'
                    }
            except Exception:
                pass

        # 备选: 读取 summary.xml
        summary_file = simulation_dir / "summary.xml"
        if summary_file.exists():
            time_series = self._extract_summary_time_series(summary_file)
            # ... 汇总数据
```

### 方案C: 分离 running 和 completed 数据 (完整解决)

```python
def _aggregate_live_time_series(self, tasks, case_id, batch_id):
    """同时处理 running 和 completed 任务"""

    running_tasks = [t for t in tasks if t.get('status') == 'running']
    completed_tasks = [t for t in tasks if t.get('status') == 'completed']

    aggregated_data = defaultdict(int)

    # 方案C: 使用 running 和 completed 的并集
    all_tasks = running_tasks + completed_tasks  # ← 改这里

    for task in all_tasks:
        summary_file = # ... 构建路径

        if summary_file.exists():
            time_series = self._extract_summary_time_series(summary_file)

            for entry in time_series:
                aggregated_data[entry['time']] += entry['running']

    # 返回汇总结果
    if aggregated_data:
        sorted_times = sorted(aggregated_data.keys())
        return {
            'time_points': sorted_times,
            'total_running': [aggregated_data[t] for t in sorted_times],
            'task_count': len(all_tasks),
            'last_update': datetime.now().isoformat()
        }
    else:
        return {'time_points': [], 'total_running': [], ...}
```

---

## 📋 总结表

| 方面 | 现状 | 问题 | 改进 |
|------|------|------|------|
| **生成函数** | `_aggregate_live_time_series()` | - | - |
| **生成位置** | `batch_optimization_service.py:445-552` | - | - |
| **调用频率** | 每2秒（由前端轮询触发） | - | - |
| **数据来源** | summary.xml | ❌ 生成有延迟 | 使用live_curve.json |
| **返回格式** | {time_points, total_running} | ✓ 正确 | - |
| **无数据时** | 返回空数组 | ⚠️ 前端无法显示 | 添加重试或缓存 |
| **并发问题** | 可能读写冲突 | ❌ 导致解析失败 | 添加重试或锁定 |
| **优先级** | running OR completed | ❌ 应为AND | 同时处理两者 |

---

## 🎯 立即行动

### 问题排查清单

当曲线无法显示时，按顺序检查：

- [ ] **检查1**: 后端日志中有 `[_aggregate_live_time_series]` 的输出吗？
  ```bash
  # 查看API服务器日志中的这些行
  grep "_aggregate_live_time_series" api.log
  ```

- [ ] **检查2**: `File exists=True` 还是 `File exists=False`？
  ```
  存在？→ 问题可能是XML解析
  不存在？→ SUMO还未生成 summary.xml，需要等待
  ```

- [ ] **检查3**: 前端Console中的 `live_time_series` 是什么？
  ```javascript
  // 在F12中检查
  console.log(data.live_time_series);
  ```

- [ ] **检查4**: summary.xml 文件是否存在？
  ```bash
  ls -la cases/case_001/simulations/plan_opti/batch_001/plan_001/sim_66/summary.xml
  ```

### 快速修复（推荐）

**使用方案B**: 添加 `live_curve.json` 缓存

工作量: 2小时
风险: 低
效果: 立即显示曲线

详见: 《BATCH_MONITORING_QUICK_FIX_PLAN.md》第"修复2"部分

