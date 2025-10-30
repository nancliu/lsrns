# 批量仿真进度监测完整增强修复报告

## 问题诊断

### 初始症状
```
Has live_time_series: false
time_points: []
total_running: []
Tasks with live_status:
  - has_live_status: false
  - running_vehicles: undefined
```

### 根本原因（三层问题）

#### 问题1: Pydantic模型缺少字段定义
- **位置**: `api/models/control/responses/batch_response.py`
- **现象**: 后端计算的 `live_time_series` 和 `estimated_remaining_seconds` 字段在序列化时被丢弃
- **原因**: Pydantic会在序列化前验证响应模型，如果模型中没有定义的字段会被忽略

#### 问题2: 时序数据仅在运行中任务中收集
- **位置**: `api/services/batch_optimization_service.py` 中的 `_aggregate_live_time_series()`
- **现象**: 当批次完成后，`live_time_series` 返回空数组
- **原因**: 方法只查询运行中的任务，当所有任务完成后找不到任何running task
- **影响**: 批次完成后无法显示最终的动态曲线

#### 问题3: TaskModel缺少live_status字段
- **位置**: `api/models/control/entities/batch_simulation.py` 中的 `BatchSimulationTask`
- **现象**: 前端日志显示 `has_live_status: false`
- **原因**: Pydantic模型中没有定义 `live_status` 字段，导致后端设置的值被丢弃
- **影响**: 前端无法获取任务的实时运行状态和车辆数据

#### 问题4: 已完成任务的live_status为空
- **位置**: `api/services/batch_optimization_service.py` 中的 `get_batch_progress()`
- **现象**: 已完成任务的 `live_status` 为 null
- **原因**: 只为running状态的任务设置live_status，对于completed任务没有处理

#### 问题5: progress.json不包含车辆统计数据
- **位置**: `api/services/batch_optimization_service.py` 中的 `_get_simulation_live_status()`
- **现象**: 从progress.json读取时无法获取running_vehicles等数据
- **原因**: progress.json被设计为简单的进度文件，不包含详细的summary数据
- **解决**: 当progress.json中没有summary数据时，回退到summary.xml

## 修复方案

### 修复1: 扩展批次进度响应模型
**文件**: `api/models/control/responses/batch_response.py`

```python
# 新增LiveTimeSeries模型
class LiveTimeSeries(BaseModel):
    time_points: List[int]          # 时间点数组（秒）
    total_running: List[int]        # 每个时间点的总在网车辆数
    task_count: int                 # 数据来源任务数
    last_update: datetime           # 最后更新时间

# 扩展BatchProgressResponse
class BatchProgressResponse(BaseModel):
    # ... 现有字段 ...
    estimated_remaining_seconds: Optional[int]  # 预计剩余秒数
    live_time_series: Optional[LiveTimeSeries]  # 实时时间序列数据
```

### 修复2: 增强时序数据收集逻辑
**文件**: `api/services/batch_optimization_service.py`

修改 `_aggregate_live_time_series()` 方法，使其：
- 优先使用运行中任务的summary.xml数据（实时更新）
- 如果没有运行中任务，使用已完成任务的summary.xml数据（最终结果）
- 这样可以在整个生命周期内显示动态曲线

```python
# 优先级逻辑
running_tasks = [t for t in tasks if t.get('status') == 'running']
completed_tasks = [t for t in tasks if t.get('status') == 'completed']
data_source_tasks = running_tasks if running_tasks else completed_tasks
```

### 修复3: 为BatchSimulationTask添加live_status字段
**文件**: `api/models/control/entities/batch_simulation.py`

```python
class BatchSimulationTask(BaseModel):
    # ... 现有字段 ...
    live_status: Optional[Dict[str, Any]] = Field(
        default=None,
        description="实时运行状态（仅当status=running或completed时填充）"
    )
```

### 修复4: 扩展live_status数据源
**文件**: `api/services/batch_optimization_service.py`

修改 `get_batch_progress()` 方法：
- 为所有status为'running'或'completed'的任务添加live_status

修改 `_get_simulation_live_status()` 方法：
- 当progress.json不存在或不包含summary数据时，从summary.xml的最后一步提取数据
- 对于已完成任务，返回最后一步的在网车辆数、已完成车辆数、待加载车辆数

## 修复后的数据流

```
API进度查询
  ↓
scheduler.get_batch_progress()  ← 获取基础进度和任务列表
  ↓
┌─ for each task:
│  ├─ if status in ['running', 'completed']:
│  │  └─ _get_simulation_live_status()  ← 填充live_status
│  │     ├─ 优先从progress.json读取
│  │     └─ 否则从summary.xml提取最后一步
│  └─ task_dict['live_status'] = live_status
│
├─ _aggregate_live_time_series()  ← 汇总时序数据
│  ├─ 从running任务的summary.xml收集（实时）
│  └─ 或从completed任务的summary.xml收集（完整）
│
├─ _calculate_batch_remaining_time()  ← 估算剩余时间
│
└─ 构造BatchProgressResponse
   ├─ batch_id, status, progress
   ├─ tasks[] with live_status
   ├─ estimated_remaining_seconds
   └─ live_time_series {time_points, total_running}
        ↓
前端batch_simulation.js接收
  ├─ 更新task表格（显示live_status中的vehicle数据）
  └─ renderLiveCurve(live_time_series)  ← 渲染动态曲线
```

## 验证结果

### API响应数据示例
```json
{
  "batch_id": "batch_20251029_230533",
  "status": "completed",
  "progress": 1.0,
  "total_tasks": 3,
  "running_tasks": 0,
  "completed_tasks": 3,
  "estimated_remaining_seconds": null,
  "live_time_series": {
    "time_points": [0, 1, 2, ..., 599],
    "total_running": [702, 708, 984, ..., 27438],
    "task_count": 3,
    "last_update": "2025-10-29T23:10:55.242730"
  },
  "tasks": [
    {
      "task_id": "task_001",
      "status": "completed",
      "live_status": {
        "current_step": 599,
        "total_steps": 14400,
        "progress_percent": 100.0,
        "running_vehicles": 9146,
        "ended_vehicles": 2612,
        "loaded_vehicles": 15006
      }
    },
    // ... 其他任务 ...
  ]
}
```

### 前端日志验证
```
Has live_time_series: true ✅  (之前是 false)
time_points length: 600 ✅      (之前是 0)
total_running length: 600 ✅    (之前是 0)
Task 0 live_status: {...} ✅   (包含running_vehicles: 9146)
```

## 修改的文件

1. **`api/models/control/responses/batch_response.py`** ✅
   - 新增 `LiveTimeSeries` 模型
   - 扩展 `BatchProgressResponse` 添加 `live_time_series` 和 `estimated_remaining_seconds` 字段

2. **`api/models/control/entities/batch_simulation.py`** ✅
   - 添加 `live_status` 字段到 `BatchSimulationTask` 模型

3. **`api/services/batch_optimization_service.py`** ✅
   - 修改 `_aggregate_live_time_series()` 支持已完成任务的时序数据
   - 修改 `get_batch_progress()` 为所有running/completed任务添加live_status
   - 修改 `_get_simulation_live_status()` 从summary.xml获取已完成任务的数据
   - 添加详细的调试日志

## 后续优化建议

### 性能优化
对于大规模批量仿真（100+ tasks），考虑：
1. **时序数据采样**: 只保留关键时间点（例如每10秒采样一次）
2. **增量计算**: 缓存已计算的时序数据，只在有新数据时更新
3. **分页返回**: 对于非常长的时序数据，考虑分页

### 功能增强
1. **Per-plan曲线**: 显示各方案独立的动态曲线
2. **统计信息**: 计算时序数据的平均值、标准差、峰值
3. **导出功能**: 允许下载时序数据为CSV/Excel

### 监控和调试
1. **性能监控**: 记录_aggregate_live_time_series()的执行时间
2. **数据质量**: 验证summary.xml中的数据一致性
3. **错误恢复**: 处理损坏或不完整的summary.xml文件

## 测试验证清单

- ✅ 批次运行中时，live_time_series显示实时数据
- ✅ 批次完成后，live_time_series显示完整的历史数据
- ✅ 每个任务都有正确的live_status数据
- ✅ 前端能成功渲染动态曲线
- ✅ API响应包含所有必需字段
- ✅ 数据格式符合Pydantic模型定义
- ✅ 没有数据丢失或序列化错误

---
**修复日期**: 2025-10-29
**修复版本**: v1.0 Complete
**状态**: ✅ 已验证和测试完成
