# batch-management Specification

## Purpose
TBD - created by archiving change enhance-batch-simulation-monitoring. Update Purpose after archive.
## Requirements
### Requirement: 用户可以查询历史批次列表

用户MUST能够通过API查询历史批次列表，支持按状态（running/completed/cancelled/failed）、时间范围、case_id筛选。系统返回批次摘要信息（batch_id、case_id、方案数、状态、创建/完成时间），支持分页。

**优先级**: P1
**状态**: 新增

#### Scenario: 查询所有已完成的批次

**Given**:
- 系统存在10个批次：
  - 3个completed
  - 2个running
  - 3个cancelled
  - 2个failed

**When**:
- 用户发送 `GET /api/v1/control/batch-optimization/batches?status=completed&limit=20`

**Then**:
- 返回200响应
- 返回3个completed批次的摘要：
  ```json
  {
    "batches": [
      {
        "batch_id": "batch_20251029_103000",
        "case_id": "case_001",
        "case_name": "成都绕城早高峰案例",
        "plan_count": 3,
        "total_tasks": 9,
        "status": "completed",
        "created_at": "2025-10-29T10:30:00",
        "started_at": "2025-10-29T10:31:00",
        "completed_at": "2025-10-29T11:15:00",
        "duration_seconds": 2640,
        "success_rate": 1.0
      },
      {
        "batch_id": "batch_20251028_150000",
        "case_id": "case_002",
        ...
      },
      ...
    ],
    "total": 3,
    "page": 1,
    "limit": 20
  }
  ```

---

#### Scenario: 按时间范围筛选批次

**Given**:
- 用户想查看2025-10-25到2025-10-28期间的批次

**When**:
- 用户发送 `GET /api/v1/control/batch-optimization/batches?start_date=2025-10-25&end_date=2025-10-28&limit=50`

**Then**:
- 返回符合时间范围的批次列表
- 按created_at降序排序（最新的在前）
- 包含该时间段内所有状态的批次

---

#### Scenario: 按case_id筛选批次

**Given**:
- 用户想查看case_001的所有批次

**When**:
- 用户发送 `GET /api/v1/control/batch-optimization/batches?case_id=case_001`

**Then**:
- 返回case_001的所有批次
- 包含running、completed、cancelled、failed等所有状态

---

#### Scenario: 查询正在运行的批次

**Given**:
- 系统有2个批次正在运行

**When**:
- 用户发送 `GET /api/v1/control/batch-optimization/batches?status=running`

**Then**:
- 返回2个running批次
- 包含当前进度百分比（progress字段）
- 包含estimated_completion_time

---

#### Scenario: 分页查询

**Given**:
- 系统有50个已完成的批次

**When**:
- 用户发送 `GET /api/v1/control/batch-optimization/batches?status=completed&page=1&limit=10`

**Then**:
- 返回第1页的10个批次
- 返回total=50
- 前端可根据total和limit计算总页数（5页）

---

### Requirement: 用户可以查看历史批次的详细信息

用户MUST能够通过batch_id查询历史批次的详细信息，包括批次元数据、任务列表、结果摘要（如已完成）。系统返回完整的批次配置和执行记录。

**优先级**: P1
**状态**: 新增

#### Scenario: 查看已完成批次的详细信息

**Given**:
- 批次batch_20251029_103000已完成

**When**:
- 用户发送 `GET /api/v1/control/batch-optimization/batches/batch_20251029_103000/detail`

**Then**:
- 返回200响应
- 返回批次详细信息：
  ```json
  {
    "batch_id": "batch_20251029_103000",
    "case_id": "case_001",
    "plan_ids": ["baseline_plan", "plan_001", "plan_002"],
    "num_seeds": 3,
    "base_seed": 66,
    "max_concurrent": 48,
    "status": "completed",
    "created_at": "2025-10-29T10:30:00",
    "started_at": "2025-10-29T10:31:00",
    "completed_at": "2025-10-29T11:15:00",
    "duration_seconds": 2640,
    "tasks": [
      {
        "task_id": "task_001",
        "plan_id": "baseline_plan",
        "seed": 66,
        "status": "completed",
        "simulation_id": "sim_001",
        "started_at": "2025-10-29T10:31:00",
        "completed_at": "2025-10-29T10:35:30",
        "duration_seconds": 270
      },
      ...
    ],
    "summary": {
      "total_tasks": 9,
      "completed_tasks": 9,
      "failed_tasks": 0,
      "success_rate": 1.0,
      "avg_task_duration_seconds": 293
    }
  }
  ```

---

### Requirement: 前端提供批次历史管理视图

批量仿真页面MUST添加"批次历史"Tab（第4个Tab），显示历史批次列表。用户可以按状态筛选、按时间排序、点击批次卡片查看详情或结果。

**优先级**: P1
**状态**: 新增

#### Scenario: 批次历史视图显示批次列表

**Given**:
- 用户打开批量仿真页面
- 系统存在10个历史批次

**When**:
- 用户点击"批次历史"Tab

**Then**:
- 切换到批次历史视图
- 显示批次列表（卡片或表格形式）
- 每个批次卡片显示：
  - batch_id（简化显示，如"batch_...3000"）
  - case_name
  - 方案数（3个方案）
  - 状态标签（完成✓、运行中⏳、已取消❌、失败✗）
  - 创建时间（相对时间，如"2小时前"）
  - 完成时间（如已完成）
  - 成功率（如"9/9任务成功"）
- 默认按创建时间降序排序

---

#### Scenario: 筛选和排序批次

**Given**:
- 批次历史视图已打开

**When**:
- 用户选择状态筛选器："已完成"
- 用户选择时间排序："最近完成"

**Then**:
- 仅显示状态为"completed"的批次
- 按completed_at降序排序
- 批次列表动态更新

---

#### Scenario: 点击批次卡片查看结果

**Given**:
- 批次历史视图显示batch_001（已完成）

**When**:
- 用户点击batch_001的卡片

**Then**:
- 前端切换到"结果视图"Tab
- 加载batch_001的结果数据（调用GET /results API）
- 显示方案对比表、峰值曲线、指标卡片
- 提供"查看详细优化分析"按钮

---

#### Scenario: 点击运行中批次进入监控

**Given**:
- 批次历史视图显示batch_002（运行中）

**When**:
- 用户点击batch_002的卡片

**Then**:
- 前端切换到"进度视图"Tab
- 加载batch_002的实时进度（调用GET /progress API）
- 显示任务列表、进度条、实时状态

---

### Requirement: 用户可以删除历史批次

用户MUST能够删除已完成或已取消的批次，系统删除批次的所有仿真文件和元数据。系统SHOULD支持"归档"选项（保留元数据，删除仿真输出文件）以节省磁盘空间。

**优先级**: P2
**状态**: 新增

#### Scenario: 删除已完成批次

**Given**:
- 批次batch_001已完成
- 批次目录存在：cases/case_001/simulations/plan_opti/batch_001/
- 包含9个仿真目录和batch_metadata.json

**When**:
- 用户发送 `DELETE /api/v1/control/batch-optimization/batches/batch_001`

**Then**:
- 系统删除整个批次目录（递归删除）
- 系统从batches_index.json中移除batch_001记录
- 返回204响应
- 批次历史列表不再显示batch_001

---

#### Scenario: 归档批次（保留元数据）

**Given**:
- 批次batch_002已完成
- 用户想节省磁盘空间但保留元数据

**When**:
- 用户发送 `DELETE /api/v1/control/batch-optimization/batches/batch_002?archive=true`

**Then**:
- 系统删除所有仿真输出文件：
  - summary.xml, tripinfo.xml, edgedata.xml等
- 系统保留：
  - batch_metadata.json
  - batch_progress.json
  - batch_summary.json
  - simulation.sumocfg, control.add.xml（配置文件）
- 批次状态更新为"archived"
- 返回200响应："批次已归档"
- 批次历史列表显示batch_002，状态为"已归档"
- 结果视图显示摘要数据（从batch_summary.json读取），但无法重新分析

---

#### Scenario: 禁止删除运行中批次

**Given**:
- 批次batch_003状态为"running"

**When**:
- 用户发送 `DELETE /api/v1/control/batch-optimization/batches/batch_003`

**Then**:
- 返回409 Conflict错误
- 错误消息："无法删除运行中的批次，请先取消批次"
- 提示："使用POST /batch_003/cancel取消批次"

---

### Requirement: 系统维护批次索引文件

系统MUST在`cases/{case_id}/simulations/plan_opti/batches_index.json`维护批次索引，记录所有批次的基本信息。系统在创建、更新、删除批次时自动同步索引文件。

**优先级**: P1
**状态**: 新增

#### Scenario: 批次创建时更新索引

**Given**:
- 用户创建新批次batch_20251029_103000

**When**:
- 批次创建完成

**Then**:
- 系统读取batches_index.json（如不存在则创建）
- 系统添加新记录：
  ```json
  {
    "batch_id": "batch_20251029_103000",
    "case_id": "case_001",
    "plan_count": 3,
    "total_tasks": 9,
    "status": "pending",
    "created_at": "2025-10-29T10:30:00",
    "updated_at": "2025-10-29T10:30:00"
  }
  ```
- 系统保存batches_index.json

---

#### Scenario: 批次状态变更时更新索引

**Given**:
- 批次batch_001状态从"running"变为"completed"

**When**:
- 批次完成

**Then**:
- 系统更新batches_index.json中的batch_001记录：
  ```json
  {
    "batch_id": "batch_001",
    ...
    "status": "completed",
    "completed_at": "2025-10-29T11:15:00",
    "updated_at": "2025-10-29T11:15:00",
    "duration_seconds": 2640,
    "success_rate": 1.0
  }
  ```

---

#### Scenario: 批次删除时更新索引

**Given**:
- 用户删除batch_002

**When**:
- 删除操作完成

**Then**:
- 系统从batches_index.json中移除batch_002记录
- 或标记为"deleted"（软删除）
- 系统保存batches_index.json

---

### Requirement: 系统支持从历史批次恢复分析

用户MUST能够对已完成的历史批次重新运行结果分析，包括重新提取指标、重新生成对比图表。系统SHOULD在batch_summary.json缺失或损坏时自动触发重新分析。

**优先级**: P2
**状态**: 新增

#### Scenario: 重新分析历史批次

**Given**:
- 批次batch_001已完成
- batch_summary.json已删除或数据不完整

**When**:
- 用户发送 `POST /api/v1/control/batch-optimization/batches/batch_001/reanalyze`

**Then**:
- 系统重新扫描所有仿真目录
- 系统重新读取tripinfo.xml, summary.xml
- 系统重新提取指标和时序数据
- 系统重新生成batch_summary.json
- 返回200响应："分析完成"
- 批次详情显示最新分析结果

---

#### Scenario: 自动检测并触发重新分析

**Given**:
- 批次batch_002已完成
- batch_summary.json缺失

**When**:
- 用户查询批次结果：`GET /batches/batch_002/results`

**Then**:
- 系统检测到batch_summary.json不存在
- 系统自动触发重新分析
- 系统返回200响应（包含重新分析的结果）
- 系统记录日志："Auto-reanalyzed batch_002 due to missing summary"

---

