# 批量仿真进度监测增强功能修复报告

## 问题诊断

### 症状
- 前端日志显示 `has_live_time_series: false` - 增强进度监测没有返回实时时间序列数据
- 动态在网车辆曲线图表无法显示
- 旧的基础进度监测仍在正常工作（能显示task进度百分比）

### 根本原因
**Pydantic模型字段缺失**：`BatchProgressResponse` 响应模型中缺少 `live_time_series` 和 `estimated_remaining_seconds` 字段定义，导致后端计算的这些数据在序列化时被丢弃。

## 修复内容

### 1. 添加 `LiveTimeSeries` 数据模型
**文件**: `api/models/control/responses/batch_response.py`

新增 `LiveTimeSeries` BaseModel，定义实时时间序列数据的结构：
```python
class LiveTimeSeries(BaseModel):
    """实时时间序列数据"""
    time_points: List[int]      # 时间点列表（秒数）
    total_running: List[int]    # 每个时间点的在网车辆总数
    task_count: int             # 贡献数据的运行中任务数
    last_update: datetime       # 最后更新时间
```

### 2. 扩展 `BatchProgressResponse` 响应模型
添加两个新字段：
- `estimated_remaining_seconds: Optional[int]` - 预计剩余秒数
- `live_time_series: Optional[LiveTimeSeries]` - 实时时间序列数据（用于动态曲线）

### 3. 添加调试日志
**文件**: `api/services/batch_optimization_service.py`

在 `_aggregate_live_time_series()` 方法中添加详细的调试日志，用于诊断时序数据收集的问题：
- 运行中任务数
- 每个任务的summary.xml文件位置和是否存在
- 每个任务提取的数据点数
- 最终汇总的数据点总数

## 修复后的效果

### API响应结构
```json
{
  "batch_id": "batch_20251029_155729",
  "status": "running",
  "progress": 0.91,
  "total_tasks": 3,
  "completed_tasks": 0,
  "running_tasks": 3,
  "tasks": [...],
  "estimated_completion": "2025-10-29T23:14:21.390834",
  "estimated_remaining_seconds": 900,
  "live_time_series": {
    "time_points": [0, 1, 2, ..., 14400],
    "total_running": [100, 150, 200, ..., 9103],
    "task_count": 3,
    "last_update": "2025-10-29T22:59:30.928381"
  }
}
```

### 前端显示改进
前端现在能够：
1. 检测到 `live_time_series` 数据存在（`has_live_time_series: true`）
2. 渲染动态在网车辆曲线（多任务并行时的总在网车辆数）
3. 实时显示运行中任务的车辆数趋势

## 验证步骤

1. 启动API服务器
2. 在前端创建并启动批量仿真
3. 打开浏览器开发者工具的Console
4. 观察日志中的进度更新：
   ```
   Has live_time_series: true ✅ (之前是 false)
   liveTimeSeries: {...} with time_points.length > 0 ✅
   ```
5. 动态曲线图表应该显示（之前被隐藏）

## 技术细节

### 数据流路径
```
batch_optimization_service.get_batch_progress()
  ├─ scheduler.get_batch_progress()         # 获取基础进度
  ├─ _get_simulation_live_status()          # 为每个running任务添加live_status
  ├─ _aggregate_live_time_series()          # 汇总所有running任务的summary.xml时序数据
  ├─ _calculate_batch_remaining_time()      # 计算剩余时间
  └─ 构造BatchProgressResponse()             # 返回完整响应（包含live_time_series）
       ↓
  前端batch_simulation.js收到响应
  └─ renderLiveCurve(data.live_time_series) # 绘制动态曲线
```

### summary.xml时序数据收集
- 每个运行中的任务对应一个 `summary.xml` 文件
- 文件路径: `cases/{case_id}/simulations/plan_opti/{batch_id}/{plan_id}/sim_{seed}/summary.xml`
- 包含格式: `<step time="X" running="Y" loaded="Z" ended="W" />`
- 聚合方式: 对于每个时间点，将所有任务的running车辆数相加

## 后续改进建议

1. **性能优化**：对于大规模批量仿真（100+ tasks），考虑：
   - 只保留最后N个时间点（例如最后1000个）
   - 采样时间序列（例如每10秒采样一次）
   - 缓存已计算的时序数据

2. **增强的时序分析**：
   - 显示per-plan的时序曲线（而不仅是总和）
   - 添加平均值、标准差、最大值的计算
   - 导出时序数据为CSV格式

3. **错误处理**：
   - 当某个任务的summary.xml损坏时，继续处理其他任务
   - 提供错误恢复机制

## 相关文件变更

- ✅ `api/models/control/responses/batch_response.py` - 添加LiveTimeSeries模型
- ✅ `api/services/batch_optimization_service.py` - 添加调试日志
- ✅ `frontend/control/js/batch_simulation.js` - 已支持live_time_series（无需修改）

## 测试验证

运行以下命令验证修复：
```bash
# 启动API服务器
python api/main.py

# 测试进度API（替换实际的batch_id）
curl http://localhost:8000/api/v1/control/optimization/batch/{batch_id}/progress

# 验证响应包含live_time_series字段和数据
```

---
**修复日期**: 2025-10-29
**修复人**: Claude Code
