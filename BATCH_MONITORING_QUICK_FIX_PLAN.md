# 批量仿真进度监测 - 快速修复计划

**优先级**: P0 - 立即实施
**预估工作量**: 4-6小时
**难度**: 中等
**风险**: 低

---

## 快速概览

你提出了5个问题，我整理出来的关键问题是：

| 问题 | 优先级 | 修复时间 | 难度 |
|------|--------|--------|------|
| ❌ 剩余时间求和（应取最大值） | **P0** | 30分钟 | 低 |
| ❌ 曲线在运行中无法显示 | **P0** | 2小时 | 中 |
| ❌ 任务条信息冗余 | **P1** | 1小时 | 低 |
| ⏳ 模块冗余和冲突 | **P1** | 3天 | 高 |
| ✓ 总体架构评估 | 信息 | - | - |

---

## P0修复方案（今天实施）

### 修复1️⃣: 剩余时间计算错误（30分钟）

**文件**: `api/services/batch_optimization_service.py`
**行号**: 554-605
**问题**: 用 `sum()` 替代 `max()`

#### 修改代码

**原代码**（错误）:
```python
def _calculate_batch_remaining_time(self, tasks):
    """计算批次预计剩余时间"""

    remaining_times = []
    for task in tasks:
        if task.get('status') in ['running', 'pending']:
            live_status = task.get('live_status', {})
            remaining = live_status.get('estimated_remaining_seconds', 0)
            remaining_times.append(remaining)

    if remaining_times:
        total_remaining = sum(remaining_times)  # ❌ 错误：求和
        return total_remaining

    return None
```

**改进代码**（正确）:
```python
def _calculate_batch_remaining_time(self, tasks):
    """计算批次预计剩余时间（并行任务）"""

    remaining_times = []
    for task in tasks:
        if task.get('status') in ['running', 'pending']:
            live_status = task.get('live_status', {})
            remaining = live_status.get('estimated_remaining_seconds', 0)
            if remaining > 0:
                remaining_times.append(remaining)

    if remaining_times:
        # ✓ 正确：取最大值（并行任务同时执行）
        max_remaining = max(remaining_times)

        # 可选：添加日志
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Batch remaining time calculated: max={max_remaining}s "
            f"from {len(remaining_times)} tasks"
        )

        return max_remaining

    return None
```

#### 验证修改

```bash
# 添加测试
cd D:\projects\OD_SIM
python -c "
from api.services.batch_optimization_service import BatchOptimizationService

service = BatchOptimizationService()

# 测试1: 单任务
result = service._calculate_batch_remaining_time([
    {'status': 'running', 'live_status': {'estimated_remaining_seconds': 300}},
])
assert result == 300, f'Expected 300, got {result}'
print('✓ Test 1 passed: single task')

# 测试2: 多任务（应取最大值）
result = service._calculate_batch_remaining_time([
    {'status': 'running', 'live_status': {'estimated_remaining_seconds': 300}},
    {'status': 'running', 'live_status': {'estimated_remaining_seconds': 600}},
    {'status': 'pending', 'live_status': {'estimated_remaining_seconds': 180}},
])
assert result == 600, f'Expected 600, got {result}'
print('✓ Test 2 passed: multiple tasks (max value)')

# 测试3: 完成任务
result = service._calculate_batch_remaining_time([
    {'status': 'completed', 'live_status': {}},
])
assert result is None, f'Expected None, got {result}'
print('✓ Test 3 passed: completed tasks')

print('\\n✅ All tests passed!')
"
```

---

### 修复2️⃣: 曲线在运行中无法显示（2小时）

**问题分析**:
- SUMO 生成 summary.xml 需要5-10秒
- 在此之前，`_aggregate_live_time_series()` 无法生成数据
- 导致曲线显示 "仿真数据加载中..."

**解决方案**: 添加实时 JSON 缓存文件

#### 步骤1: 修改后端代码（1小时）

**文件**: `shared/control_tools/batch_simulation_scheduler.py`
**位置**: `_monitor_simulation_progress()` 方法
**行号**: 443-488

**添加新方法**:

```python
def _sync_live_curve_data(self, simulation_dir, batch_id, task_id):
    """同步live_curve.json - 从summary.xml提取最新数据"""
    import json
    import xml.etree.ElementTree as ET
    from datetime import datetime

    summary_file = simulation_dir / "summary.xml"
    live_curve_file = simulation_dir / "live_curve.json"

    if not summary_file.exists():
        return False

    try:
        # 读取 summary.xml
        tree = ET.parse(summary_file)
        root = tree.getroot()

        # 提取所有step数据
        steps = root.findall('step')
        time_points = []
        total_running = []

        for step in steps:
            time = int(step.get('time', 0))
            running = int(step.get('running', 0))

            time_points.append(time)
            total_running.append(running)

        if time_points:
            # 构建 live_curve.json
            live_curve_data = {
                'batch_id': batch_id,
                'task_id': task_id,
                'time_points': time_points,
                'total_running': total_running,
                'data_point_count': len(time_points),
                'last_time_point': max(time_points) if time_points else 0,
                'max_running_vehicles': max(total_running) if total_running else 0,
                'updated_at': datetime.now().isoformat()
            }

            # 写入 live_curve.json
            with open(live_curve_file, 'w', encoding='utf-8') as f:
                json.dump(live_curve_data, f, ensure_ascii=False, indent=2)

            return True
    except Exception as e:
        print(f"Warning: Failed to sync live_curve.json: {e}")
        return False

    return False


def _monitor_simulation_progress(self, simulation_id, task_id, plan_id, seed, ...):
    """修改：添加live_curve.json同步"""

    summary_file = simulation_dir / "summary.xml"
    last_sync_time = 0
    sync_interval = 30  # 每30秒同步一次

    while task_running:
        current_time = time.time()

        # 每30秒同步一次live_curve.json
        if current_time - last_sync_time > sync_interval:
            if summary_file.exists():
                self._sync_live_curve_data(
                    simulation_dir,
                    batch_id,
                    task_id
                )
            last_sync_time = current_time

        # ... 现有监控逻辑 ...
```

#### 步骤2: 修改后端API（30分钟）

**文件**: `api/services/batch_optimization_service.py`
**方法**: `get_batch_progress()`
**行号**: 607-658

**修改**: 优先读取 live_curve.json

```python
def _aggregate_live_time_series(self, tasks, case_id, batch_id):
    """改进：先读live_curve.json，再读summary.xml"""

    from collections import defaultdict

    aggregated_data = defaultdict(int)
    has_any_data = False

    # 优先从live_curve.json读取实时数据
    running_tasks = [t for t in tasks if t.get('status') == 'running']

    for task in running_tasks:
        simulation_dir = # ... 构建路径
        live_curve_file = simulation_dir / "live_curve.json"

        # ✓ 优先读取 live_curve.json （实时更新）
        if live_curve_file.exists():
            try:
                with open(live_curve_file, 'r') as f:
                    curve_data = json.load(f)

                    # 直接使用缓存数据
                    time_points = curve_data.get('time_points', [])
                    total_running = curve_data.get('total_running', [])

                    if time_points:
                        return {
                            'time_points': time_points,
                            'total_running': total_running,
                            'task_count': len(running_tasks),
                            'last_update': curve_data.get('updated_at'),
                            'source': 'live_curve_cache'  # 标记数据来源
                        }
            except Exception as e:
                print(f"Warning: Failed to read live_curve.json: {e}")

    # 备选方案1: 从summary.xml读取（如果live_curve不存在）
    completed_tasks = [t for t in tasks if t.get('status') == 'completed']
    data_source_tasks = running_tasks if running_tasks else completed_tasks

    for task in data_source_tasks:
        simulation_dir = # ... 构建路径
        summary_file = simulation_dir / "summary.xml"

        if summary_file.exists():
            try:
                time_series = self._extract_summary_time_series(summary_file)

                # 汇总数据
                for entry in time_series:
                    time_step = entry['time']
                    running_vehicles = entry['running']
                    aggregated_data[time_step] += running_vehicles
                    has_any_data = True
            except Exception:
                continue

    # 返回结果
    if aggregated_data or has_any_data:
        sorted_times = sorted(aggregated_data.keys())
        return {
            'time_points': sorted_times,
            'total_running': [aggregated_data[t] for t in sorted_times],
            'task_count': len(data_source_tasks),
            'last_update': datetime.now().isoformat(),
            'source': 'summary_xml'  # 标记数据来源
        }

    # 都无数据
    return None
```

#### 步骤3: 修改前端代码（30分钟）

**文件**: `frontend/control/js/batch_simulation.js`
**方法**: `renderLiveCurve()`
**行号**: 518-649

**改进**: 显示数据来源和更新状态

```javascript
function renderLiveCurve(liveTimeSeries) {
    const controlBar = document.getElementById('liveCurveControlBar');
    const section = document.getElementById('liveCurveSection');

    if (!controlBar || !section) return;

    // 检查数据
    const hasData = liveTimeSeries &&
                    liveTimeSeries.time_points &&
                    liveTimeSeries.time_points.length > 0;

    // 显示控制栏
    controlBar.style.display = 'block';

    if (!hasData) {
        // 无数据：显示加载提示
        section.style.display = liveCurveVisible ? 'block' : 'none';

        const message = `
            <div style="text-align: center; padding: 50px 20px; color: #999;">
                <p>仿真数据加载中...</p>
                <p style="font-size: 12px; margin-top: 10px;">
                    SUMO 需要 5-10 秒初始化，请稍候
                </p>
            </div>
        `;
        section.innerHTML = message;
        return;
    }

    // ✓ 有数据：绘制曲线
    section.style.display = liveCurveVisible ? 'block' : 'none';

    // 准备数据
    const timeLabels = liveTimeSeries.time_points.map(t => {
        const hours = Math.floor(t / 3600);
        const minutes = Math.floor((t % 3600) / 60);
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
    });

    // 销毁旧chart
    if (window.liveCurveChartInstance) {
        window.liveCurveChartInstance.destroy();
    }

    // 创建新chart
    const canvas = document.getElementById('liveCurveChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    window.liveCurveChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [{
                label: '总在网车辆数',
                data: liveTimeSeries.total_running,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: `实时在网车辆数 (数据来源: ${liveTimeSeries.source || 'unknown'}, 更新于 ${new Date().toLocaleTimeString()})`
                },
                tooltip: {
                    callbacks: {
                        title: function(tooltipItems) {
                            const index = tooltipItems[0].dataIndex;
                            const seconds = liveTimeSeries.time_points[index];
                            return `时间: ${timeLabels[index]} (${seconds}秒)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: '仿真时间' }
                },
                y: {
                    title: { display: true, text: '在网车辆数' },
                    beginAtZero: true
                }
            }
        }
    });

    // 更新按钮文本
    const toggleBtn = document.getElementById('toggleLiveCurveBtn');
    if (toggleBtn) {
        toggleBtn.textContent = liveCurveVisible ? '隐藏曲线' : '显示曲线';
    }

    // 输出日志
    console.log('Live curve rendered:', {
        dataPoints: liveTimeSeries.time_points.length,
        source: liveTimeSeries.source,
        maxVehicles: Math.max(...liveTimeSeries.total_running),
        lastUpdate: liveTimeSeries.last_update
    });
}
```

#### 测试修改

```bash
# 1. 启动API
.\start_api.ps1

# 2. 在浏览器中测试
# 打开 http://localhost:8000/index.html
# 进入 "控制管理" → "方案管理" → "批量仿真"
# 创建批量仿真配置
# 点击"启动仿真"

# 3. 在F12 Console中观察日志
# - 应该看到 "Live curve rendered: dataPoints: N, source: live_curve_cache" 或 "source: summary_xml"
# - 曲线应该在运行过程中逐步显示，而不是等到完成

# 4. 在文件系统中检查
# 查看 cases/{case_id}/simulations/plan_opti/{batch_id}/{plan_id}/sim_{seed}/live_curve.json
# 应该看到实时更新的数据
```

---

## P1改进方案（下周实施）

### 改进3️⃣: 简化任务条显示（1小时）

**文件**: `frontend/control/js/batch_simulation.js`
**方法**: `renderTaskList()`
**行号**: 414-495

**改进**: 隐藏低价值信息，突出关键指标

```javascript
// 改进前
if (task.status === 'running') {
    const liveStatus = task.live_status || {};
    const progressPct = liveStatus.progress_percent || task.progress || 0;
    const runningVeh = liveStatus.running_vehicles;
    const remainingSec = liveStatus.estimated_remaining_seconds;

    detailsHtml += `
        <div>${statusText}</div>
        <div>进度: ${progressPct}%</div>
        <div>在网: ${runningVeh}辆</div>
        <div>剩余: ${remainingTime}</div>
    `;
}

// 改进后 - 更紧凑的格式
if (task.status === 'running') {
    const liveStatus = task.live_status || {};
    const progressPct = liveStatus.progress_percent || task.progress || 0;
    const runningVeh = liveStatus.running_vehicles;
    const remainingSec = liveStatus.estimated_remaining_seconds;

    // 只显示关键信息
    detailsHtml += `
        <div class="task-bar">
            <div class="progress-bar" style="width: ${progressPct}%"></div>
            <span class="progress-text">${progressPct}%</span>
        </div>
        <div class="task-metrics">
            <span class="metric">🚗 ${runningVeh}</span>
            <span class="metric">⏱️ ${remainingTime}</span>
        </div>
    `;
}
```

**添加CSS**:
```css
.task-metrics {
    display: flex;
    gap: 20px;
    font-size: 0.95em;
    margin-top: 5px;
}

.task-metrics .metric {
    display: inline-flex;
    align-items: center;
    gap: 5px;
}

.task-metrics .metric.active-vehicles {
    color: #27ae60;
    font-weight: bold;
}

.task-metrics .metric.remaining-time {
    color: #e74c3c;
    font-weight: bold;
}
```

---

## 实施检查清单

### 修复1: 剩余时间计算

- [ ] 打开 `api/services/batch_optimization_service.py`
- [ ] 定位到 `_calculate_batch_remaining_time()` 方法
- [ ] 将 `sum(remaining_times)` 改为 `max(remaining_times)`
- [ ] 添加日志输出
- [ ] 运行单元测试
- [ ] 提交代码

### 修复2: 曲线显示

**后端**:
- [ ] 打开 `shared/control_tools/batch_simulation_scheduler.py`
- [ ] 添加 `_sync_live_curve_data()` 方法
- [ ] 在 `_monitor_simulation_progress()` 中集成调用
- [ ] 打开 `api/services/batch_optimization_service.py`
- [ ] 修改 `_aggregate_live_time_series()` 优先读取 live_curve.json
- [ ] 添加 `source` 字段标记数据来源
- [ ] 运行集成测试

**前端**:
- [ ] 打开 `frontend/control/js/batch_simulation.js`
- [ ] 修改 `renderLiveCurve()` 函数
- [ ] 添加数据源和更新时间显示
- [ ] 浏览器测试
- [ ] 清除缓存 (Ctrl+F5)
- [ ] 验证曲线在运行中出现

---

## 验证方法

### 快速验证（10分钟）

```bash
# 1. 启动API
.\start_api.ps1

# 2. 打开浏览器
# http://localhost:8000/index.html

# 3. 创建并启动批量仿真

# 4. 在F12 Console中检查
# - 应该看到 "Live curve rendered: dataPoints: N"
# - 任务条应该显示在网车辆数和剩余时间
# - 剩余时间应该是运行最长任务的时间，而不是所有任务的和

# 5. 等待5-10秒后
# - 曲线应该出现，而不是 "仿真数据加载中..."
```

### 详细验证（30分钟）

```bash
# 1. 检查日志输出
# 后端日志应该显示：
# [INFO] Batch remaining time calculated: max=600s from 3 tasks

# 2. 检查文件
# cases/{case_id}/simulations/plan_opti/{batch_id}/{plan_id}/sim_{seed}/
# 应该有两个文件：
# - progress.json (运行中) 或 summary.xml (完成)
# - live_curve.json (新增，实时更新)

# 3. 检查live_curve.json内容
# 应该包含：
# {
#   "batch_id": "batch_001",
#   "task_id": "task_001",
#   "time_points": [0, 1, 2, 3, ...],
#   "total_running": [100, 150, 200, ...],
#   "updated_at": "2025-10-30T10:25:15"
# }

# 4. 前端检查
# F12 → Console 应该显示：
# Live curve rendered: {
#   dataPoints: 150,
#   source: "live_curve_cache",
#   maxVehicles: 450,
#   lastUpdate: "2025-10-30T10:25:15"
# }
```

---

## 预期效果

### 修复前 vs 修复后

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| **剩余时间准确性** | ❌ 3任务×10分 = 30分（实际10分） | ✅ max(10, 10, 10) = 10分 |
| **曲线显示延迟** | ❌ 需要等待SUMO生成summary.xml（5-10秒）+ 完全写入（300秒） | ✅ 每30秒更新live_curve.json，立即显示 |
| **用户体验** | ⚠️ 看不到进度，等待焦虑 | ✅ 立即看到曲线和准确的完成时间 |
| **数据可靠性** | ⚠️ 部分写入的XML可能解析失败 | ✅ 逐步累积的JSON，无并发读写冲突 |

---

## 回滚方案

如果出现问题，可以快速回滚：

### 回滚修复1（剩余时间）
```python
# 恢复原代码
total_remaining = sum(remaining_times)  # 改回求和
return total_remaining
```

### 回滚修复2（曲线显示）
```python
# 在 _aggregate_live_time_series() 中
# 删除优先读取 live_curve.json 的逻辑
# 保留原有的 summary.xml 读取逻辑
```

---

## 下一步行动

1. **今天**:
   - [ ] 实施修复1和修复2
   - [ ] 运行测试验证
   - [ ] 部署到开发环境

2. **明天**:
   - [ ] 用户验收测试
   - [ ] 收集反馈
   - [ ] 微调参数（同步间隔等）

3. **下周**:
   - [ ] 实施P1改进（简化任务条）
   - [ ] 规划P2改进（模块重构）

---

**文档生成**: 2025-10-30
**状态**: 准备实施
**联系人**: Claude Code

