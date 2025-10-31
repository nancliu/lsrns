# 批量仿真监控与管理 API 文档

**文档版本**: v1.1
**最后更新**: 2025-10-30
**适用系统版本**: v0.9.0+

---

## 📋 概述

本文档描述批量仿真监控与管理功能的API端点，包括：

1. **实时监控** - 查看运行中仿真的内部状态（在网车辆数、进度、剩余时间）
2. **批次管理** - 查询、删除、归档历史批次
3. **结果分析** - 获取批次汇总结果和时序数据

**新增功能** (v1.1, 2025-10-30):
- ✅ 实时监控运行中仿真的内部状态
- ✅ 动态在网车辆曲线（汇总所有运行中任务）
- ✅ 批次历史查询和管理
- ✅ 批次级和任务级剩余时间估算

---

## 🔑 核心端点

### 1. 获取批次进度（增强版）

获取批次的实时进度信息，包括运行中任务的内部状态监控。

**端点**: `GET /api/v1/control/batch-optimization/batch/{batch_id}/progress`

**路径参数**:
- `batch_id` (string, required): 批次ID

**查询参数**:
- 无

**响应** (200 OK):

```json
{
  "batch_id": "batch_20251030_123045",
  "case_id": "case_20251020_153045",
  "status": "running",
  "created_at": "2025-10-30T12:30:45",
  "started_at": "2025-10-30T12:31:00",
  "total_tasks": 9,
  "completed_tasks": 6,
  "running_tasks": 2,
  "failed_tasks": 0,
  "pending_tasks": 1,
  "progress_percent": 67,
  "estimated_remaining_seconds": 450,
  "tasks": [
    {
      "task_id": "task_001",
      "plan_id": "baseline_plan",
      "plan_name": "基准方案",
      "seed": 42,
      "status": "running",
      "progress": 75,
      "started_at": "2025-10-30T12:32:15",
      "simulation_id": "sim_20251030_123215_001",
      "live_status": {
        "current_step": 10800,
        "total_steps": 14400,
        "progress_percent": 75.0,
        "running_vehicles": 3245,
        "ended_vehicles": 8950,
        "mean_speed": 12.5,
        "estimated_remaining_seconds": 120
      }
    },
    {
      "task_id": "task_002",
      "plan_id": "plan_vss_001",
      "plan_name": "早高峰VSS限速",
      "seed": 42,
      "status": "completed",
      "progress": 100,
      "started_at": "2025-10-30T12:31:05",
      "completed_at": "2025-10-30T12:33:30",
      "duration_seconds": 145,
      "simulation_id": "sim_20251030_123105_002",
      "live_status": null
    },
    {
      "task_id": "task_003",
      "plan_id": "plan_dhs_001",
      "plan_name": "晚高峰DHS开放",
      "seed": 42,
      "status": "pending",
      "progress": 0,
      "simulation_id": null,
      "live_status": null
    }
  ],
  "live_time_series": {
    "time_points": [0, 60, 120, 180, 240, 300],
    "total_running_vehicles": [0, 1200, 2400, 3245, 3100, 2950],
    "task_count": 2,
    "last_updated": "2025-10-30T12:35:20"
  }
}
```

**字段说明**:

**批次级字段**:
- `batch_id`: 批次唯一标识符
- `status`: 批次状态（`pending`, `running`, `completed`, `failed`, `cancelled`）
- `progress_percent`: 整体进度百分比（基于已完成任务数）
- `estimated_remaining_seconds`: 批次预计剩余时间（秒）
  - 计算方法：基于已完成任务的平均时长 × 剩余任务数 + 运行中任务的剩余时间
  - 值为 `null` 表示无法估算（无已完成任务）

**任务级字段**:
- `task_id`: 任务唯一标识符
- `plan_id`: 关联的方案ID
- `seed`: 随机种子值
- `status`: 任务状态
- `progress`: 任务进度百分比（0-100）
- `simulation_id`: 对应的仿真ID（pending任务为null）

**实时监控字段** (`live_status`, 仅运行中任务):
- `current_step`: 当前仿真步数
- `total_steps`: 总仿真步数
- `progress_percent`: 仿真进度百分比（基于步数）
- `running_vehicles`: 当前在网车辆数
- `ended_vehicles`: 已完成车辆数
- `mean_speed`: 平均速度（m/s）
- `estimated_remaining_seconds`: 预计剩余时间（秒）
  - 计算方法：平均步长耗时 × 剩余步数
  - 动态更新，随仿真推进变化

**动态曲线字段** (`live_time_series`):
- `time_points`: 时间点数组（秒）
- `total_running_vehicles`: 汇总的在网车辆数（所有运行中任务的总和）
- `task_count`: 当前运行中任务数量
- `last_updated`: 最后更新时间

**轮询建议**:
- 推荐轮询间隔：**10秒**
- Backend缓存TTL：5秒（每2次轮询刷新一次数据）
- 仅在 `status == "running"` 时轮询

**错误响应** (404 Not Found):
```json
{
  "detail": "Batch not found: batch_20251030_999999"
}
```

---

### 2. 获取批次列表

查询案例下的所有批次，支持按状态筛选和分页。

**端点**: `GET /api/v1/control/batch-optimization/batches`

**查询参数**:
- `case_id` (string, optional): 案例ID筛选
- `status` (string, optional): 状态筛选（`running`, `completed`, `failed`, `cancelled`, `archived`）
- `page` (integer, optional, default=1): 页码
- `limit` (integer, optional, default=20): 每页数量（最大100）
- `sort_by` (string, optional, default="created_at"): 排序字段
- `order` (string, optional, default="desc"): 排序方向（`asc`, `desc`）

**请求示例**:
```
GET /api/v1/control/batch-optimization/batches?status=completed&limit=10
```

**响应** (200 OK):

```json
{
  "total": 45,
  "page": 1,
  "limit": 10,
  "total_pages": 5,
  "batches": [
    {
      "batch_id": "batch_20251030_123045",
      "case_id": "case_20251020_153045",
      "case_name": "早高峰G4202拥堵分析",
      "status": "completed",
      "created_at": "2025-10-30T12:30:45",
      "started_at": "2025-10-30T12:31:00",
      "completed_at": "2025-10-30T12:45:30",
      "total_tasks": 9,
      "completed_tasks": 9,
      "failed_tasks": 0,
      "plan_count": 3,
      "duration_seconds": 870
    },
    {
      "batch_id": "batch_20251029_183022",
      "case_id": "case_20251020_153045",
      "case_name": "早高峰G4202拥堵分析",
      "status": "completed",
      "created_at": "2025-10-29T18:30:22",
      "completed_at": "2025-10-29T18:50:15",
      "total_tasks": 12,
      "completed_tasks": 12,
      "failed_tasks": 0,
      "plan_count": 4,
      "duration_seconds": 1193
    }
  ]
}
```

**字段说明**:
- `total`: 符合筛选条件的批次总数
- `page`: 当前页码
- `limit`: 每页数量
- `total_pages`: 总页数
- `batches`: 批次摘要列表
  - `plan_count`: 包含的方案数量（不含baseline）
  - `duration_seconds`: 批次总耗时（秒）

---

### 3. 获取批次详情

获取批次的详细信息，包括完整的任务列表和配置。

**端点**: `GET /api/v1/control/batch-optimization/batches/{batch_id}/detail`

**路径参数**:
- `batch_id` (string, required): 批次ID

**响应** (200 OK):

```json
{
  "batch_id": "batch_20251030_123045",
  "case_id": "case_20251020_153045",
  "case_name": "早高峰G4202拥堵分析",
  "status": "completed",
  "created_at": "2025-10-30T12:30:45",
  "started_at": "2025-10-30T12:31:00",
  "completed_at": "2025-10-30T12:45:30",
  "total_tasks": 9,
  "completed_tasks": 9,
  "failed_tasks": 0,
  "config": {
    "num_seeds": 3,
    "base_seed": 42,
    "duration_hours": 3,
    "step_length": 1.0
  },
  "plans": [
    {
      "plan_id": "baseline_plan",
      "plan_name": "基准方案",
      "task_count": 3
    },
    {
      "plan_id": "plan_vss_001",
      "plan_name": "早高峰VSS限速",
      "task_count": 3
    },
    {
      "plan_id": "plan_dhs_001",
      "plan_name": "晚高峰DHS开放",
      "task_count": 3
    }
  ],
  "tasks": [
    {
      "task_id": "task_001",
      "plan_id": "baseline_plan",
      "seed": 42,
      "status": "completed",
      "started_at": "2025-10-30T12:31:05",
      "completed_at": "2025-10-30T12:33:30",
      "duration_seconds": 145
    }
    // ... 其他任务
  ]
}
```

---

### 4. 删除/归档批次

删除指定批次或将其归档（保留元数据，删除输出文件）。

**端点**: `DELETE /api/v1/control/batch-optimization/batches/{batch_id}`

**路径参数**:
- `batch_id` (string, required): 批次ID

**查询参数**:
- `archive` (boolean, optional, default=false): 是否归档（true=归档，false=删除）

**请求示例**:
```
DELETE /api/v1/control/batch-optimization/batches/batch_20251030_123045?archive=true
```

**响应** (200 OK):

```json
{
  "message": "Batch archived successfully",
  "batch_id": "batch_20251030_123045",
  "action": "archived",
  "files_deleted": 1250,
  "space_freed_mb": 456.8
}
```

**错误响应** (409 Conflict - 批次正在运行):
```json
{
  "detail": "Cannot delete running batch. Please cancel it first."
}
```

**删除 vs 归档**:

| 操作 | 元数据 | 仿真输出文件 | 结果数据 | 可恢复 |
|------|--------|-------------|---------|--------|
| 删除 (`archive=false`) | ❌ 删除 | ❌ 删除 | ❌ 删除 | ❌ 否 |
| 归档 (`archive=true`) | ✅ 保留 | ❌ 删除 | ✅ 保留 | ⚠️ 部分（需重新分析） |

**注意事项**:
- 正在运行的批次无法删除（需先取消）
- 归档后的批次可在批次列表中查看，但无法重新分析
- 删除操作不可逆，请谨慎使用

---

### 5. 获取批次结果

获取批次的汇总分析结果和时序数据。

**端点**: `GET /api/v1/control/optimization/batch/{batch_id}/results`

**路径参数**:
- `batch_id` (string, required): 批次ID

**查询参数**:
- `include_time_series` (boolean, optional, default=true): 是否包含时序数据

**响应** (200 OK):

```json
{
  "batch_id": "batch_20251030_123045",
  "case_id": "case_20251020_153045",
  "status": "completed",
  "plan_count": 3,
  "plan_results": [
    {
      "plan_id": "baseline_plan",
      "plan_name": "基准方案",
      "simulation_count": 3,
      "aggregated_metrics": {
        "mean_travel_time": {
          "mean": 1800.5,
          "std": 25.3,
          "min": 1775.0,
          "max": 1825.0
        },
        "mean_speed": {
          "mean": 45.2,
          "std": 2.1,
          "min": 43.1,
          "max": 47.3
        },
        "total_vehicles": {
          "mean": 12500,
          "std": 50,
          "min": 12450,
          "max": 12550
        },
        "peak_running_vehicles": {
          "mean": 3245,
          "std": 120,
          "min": 3125,
          "max": 3365
        }
      },
      "time_series": {
        "time": [0, 60, 120, 180, ...],
        "running_vehicles": {
          "mean": [0, 1200, 2400, 3200, ...],
          "std": [0, 50, 80, 100, ...],
          "min": [0, 1150, 2320, 3100, ...],
          "max": [0, 1250, 2480, 3300, ...]
        },
        "mean_speed": {
          "mean": [0, 12.5, 13.2, 11.8, ...],
          "std": [0, 0.5, 0.6, 0.7, ...],
          "min": [0, 12.0, 12.6, 11.1, ...],
          "max": [0, 13.0, 13.8, 12.5, ...]
        }
      }
    },
    {
      "plan_id": "plan_vss_001",
      "plan_name": "早高峰VSS限速",
      "simulation_count": 3,
      "aggregated_metrics": {
        "mean_travel_time": {
          "mean": 1650.0,
          "std": 22.0,
          "min": 1628.0,
          "max": 1672.0
        },
        "improvement_vs_baseline": {
          "mean_travel_time": -8.4,
          "mean_speed": 16.8,
          "peak_running_vehicles": -4.5
        }
      },
      "time_series": {
        // ... 时序数据
      }
    }
  ]
}
```

**字段说明**:

**聚合指标** (`aggregated_metrics`):
- `mean`: 平均值（多次仿真的平均）
- `std`: 标准差（评估结果稳定性）
- `min`: 最小值
- `max`: 最大值

**改善百分比** (`improvement_vs_baseline`):
- 正值：指标改善（例如：速度提高16.8%）
- 负值：指标下降（例如：旅行时间减少8.4%）

**时序数据** (`time_series`):
- `time`: 时间点数组（秒）
- 每个指标包含 `mean`, `std`, `min`, `max` 四个统计值

---

## 🔄 工作流示例

### 场景1：监控批量仿真进度

**目标**: 实时监控运行中的批量仿真，了解内部状态和预计完成时间

**步骤**:

1. **创建并启动批次**:
```bash
POST /api/v1/control/batch-optimization/create-batch
{
  "case_id": "case_20251020_153045",
  "plan_ids": ["plan_vss_001", "plan_dhs_001"],
  "num_seeds": 3
}

POST /api/v1/control/batch-optimization/start-batch/{batch_id}
```

2. **每10秒轮询进度**:
```bash
GET /api/v1/control/batch-optimization/batch/{batch_id}/progress
```

响应示例（运行中）:
```json
{
  "status": "running",
  "progress_percent": 67,
  "estimated_remaining_seconds": 450,
  "tasks": [
    {
      "status": "running",
      "live_status": {
        "progress_percent": 75.0,
        "running_vehicles": 3245,
        "estimated_remaining_seconds": 120
      }
    }
  ],
  "live_time_series": {
    "time_points": [0, 60, 120, 180, 240, 300],
    "total_running_vehicles": [0, 1200, 2400, 3245, 3100, 2950]
  }
}
```

3. **观察实时监控数据**:
   - **批次级**: `progress_percent` = 67%, `estimated_remaining_seconds` = 450s（约7.5分钟）
   - **任务级**: `live_status.running_vehicles` = 3245（当前在网车辆数）
   - **动态曲线**: `live_time_series` 显示所有运行中任务的在网车辆数汇总

4. **批次完成后获取结果**:
```bash
GET /api/v1/control/optimization/batch/{batch_id}/results
```

---

### 场景2：查询历史批次并删除旧数据

**目标**: 清理已完成的旧批次以节省磁盘空间

**步骤**:

1. **查询已完成的批次**:
```bash
GET /api/v1/control/batch-optimization/batches?status=completed&limit=20
```

2. **查看批次详情**:
```bash
GET /api/v1/control/batch-optimization/batches/{batch_id}/detail
```

3. **归档不需要的批次**（保留元数据，删除输出文件）:
```bash
DELETE /api/v1/control/batch-optimization/batches/{batch_id}?archive=true
```

响应:
```json
{
  "message": "Batch archived successfully",
  "files_deleted": 1250,
  "space_freed_mb": 456.8
}
```

4. **完全删除过期批次**（删除所有数据）:
```bash
DELETE /api/v1/control/batch-optimization/batches/{batch_id}?archive=false
```

---

## 📊 数据结构说明

### 实时监控数据来源

**`live_status`字段数据来源**: 从运行中仿真的 `summary.xml` 文件实时提取

**提取方法**: 增量解析（从文件末尾读取最后4KB，提取最新的`<step>`元素）

**性能**: <10ms/文件（相比全文解析的50ms+）

**数据提取逻辑**:
```xml
<!-- summary.xml 最后一个 <step> 元素 -->
<step time="10800.00" loaded="12500" inserted="12500" running="3245"
      waiting="0" ended="8950" meanWaitingTime="0.0" meanTravelTime="1785.5"
      meanSpeed="12.5" meanSpeedRelative="0.83" .../>
```

提取字段映射:
- `time` → `current_step` (÷1.0 步长)
- `running` → `running_vehicles`
- `ended` → `ended_vehicles`
- `meanSpeed` → `mean_speed`（m/s）

**剩余时间估算**:
```python
avg_step_duration = elapsed_seconds / current_step
remaining_steps = total_steps - current_step
estimated_remaining_seconds = avg_step_duration * remaining_steps
```

---

### 批次状态转换

```
pending → running → completed
                 ↘ failed
                 ↘ cancelled → archived
```

**状态说明**:
- `pending`: 批次已创建但未启动
- `running`: 批次正在执行（至少1个任务在运行）
- `completed`: 所有任务成功完成
- `failed`: 至少1个任务失败且批次已停止
- `cancelled`: 用户手动取消
- `archived`: 已归档（仅元数据保留）

---

## ⚠️ 注意事项

### 性能考虑

1. **轮询频率**: 推荐10秒，不要低于5秒（避免过载）
2. **缓存机制**: Backend使用5秒TTL缓存，减少文件系统访问
3. **批次数量**: 单次查询批次列表建议 `limit <= 50`
4. **并发限制**: 同一案例下建议最多1个运行中批次

### 数据一致性

1. **live_status数据延迟**: 最多5秒（由于后端缓存）
2. **文件系统延迟**: summary.xml每秒更新一次
3. **进度百分比精度**: 基于步数计算，精度受步长影响

### 错误处理

1. **文件不存在**: `live_status`为 `null`（仿真刚启动时正常）
2. **解析失败**: `live_status`为 `null`，日志记录错误
3. **批次不存在**: 返回404错误
4. **批次正在运行**: 删除操作返回409错误

---

## 📚 相关文档

- [用户指南 - 批量优化仿真](../user_guide/batch_optimization.md)
- [开发指南 - 批量仿真监控架构](../development/batch_monitoring_architecture.md)
- [API总览 - 新架构API指南](新架构API指南.md)

---

## 📝 更新日志

### v1.1 (2025-10-30)

- ✅ 新增实时监控功能（`live_status`字段）
- ✅ 新增动态在网车辆曲线（`live_time_series`字段）
- ✅ 新增批次列表查询API
- ✅ 新增批次详情查询API
- ✅ 新增批次删除/归档API
- ✅ 增强进度估算（批次级和任务级剩余时间）
- ✅ 优化轮询建议（从2秒调整为10秒）

### v1.0 (2025-10-28)

- 初始版本发布
- 支持基础批次进度查询
- 支持批次结果汇总

---

**维护者**: OD_SIM 开发团队
**反馈**: 请在项目issue中提交API使用问题
