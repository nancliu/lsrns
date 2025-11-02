# batch-cancellation Specification

## Purpose

支持用户取消或删除批量仿真批次，提供灵活的操作选项：
- **取消**：停止运行，保留目录和文件，允许之后重新启动
- **删除**：完全移除批次目录和所有相关数据

## Requirements

### Requirement: 用户可以取消批量仿真批次

用户MUST能够取消任何运行中（status=running）或待运行（status=pending）的批次。系统MUST：
- 杀死所有运行中任务的 SUMO 进程
- 标记所有 pending 和 running 任务为 cancelled
- 更新批次状态为 cancelled
- 保留所有仿真目录和文件以便重新启动

**优先级**: P1
**状态**: 新增

#### Scenario: 用户取消运行中的批次

**Given**:
- 批次batch_001正在运行 (status="running")
- 包含6个任务，其中3个running，3个pending
- 所有running任务都有SUMO进程在执行

**When**:
- 用户发送 POST /api/v1/control/batch-optimization/batch/batch_001/cancel

**Then**:
- 系统从 progress.json 获取所有running任务的PID
- 系统对每个PID执行 taskkill /PID {pid} /F
- 系统更新 batch_metadata.json:
  - status: "cancelled"
  - cancelled_at: ISO timestamp
- 系统更新每个任务状态：
  - running → cancelled
  - pending → cancelled
- 系统更新 batch_progress.json:
  - status: "cancelled"
  - cancelled_tasks: 6 (所有任务)
  - running_tasks: 0
- 返回200响应
  - cancelled_count: 6
  - killed_count: 3 (实际杀死的进程数)
- 批次目录完全保留

---

#### Scenario: 取消pending状态的批次

**Given**:
- 批次batch_002状态为pending (尚未启动)
- 包含4个任务，都是pending状态
- 没有SUMO进程运行

**When**:
- 用户发送 POST /api/v1/control/batch-optimization/batch/batch_002/cancel

**Then**:
- 系统检查 progress.json 不存在（pending状态）
- 系统从 batch_metadata.json 重建任务列表
- 系统标记所有4个任务为cancelled
- 系统更新 batch_metadata.json 状态为cancelled
- 返回200响应
  - cancelled_count: 4
  - killed_count: 0 (没有进程)

---

#### Scenario: 尝试取消已完成的批次

**Given**:
- 批次batch_003已完成 (status="completed")

**When**:
- 用户发送 POST /api/v1/control/batch-optimization/batch/batch_003/cancel

**Then**:
- 系统检查状态为"completed"
- 系统返回400错误
- 错误信息："Cannot cancel batch with status: completed"
- 批次状态不变

---

#### Scenario: 幂等性 - 多次取消同一批次

**Given**:
- 批次batch_004已被取消过一次 (status="cancelled")

**When**:
- 用户再次发送 POST /api/v1/control/batch-optimization/batch/batch_004/cancel

**Then**:
- 系统检查状态已为"cancelled"
- 系统直接返回200
- 返回信息："Batch already cancelled"
- 不再执行取消操作
- 幂等性保证

---

### Requirement: 用户可以完全删除批次

用户MUST能够删除任何批次（除了运行中的）。系统MUST：
- 先调用 cancel_batch（如果还在运行）
- 然后删除整个批次目录
- 从 batches_index.json 中移除记录

**优先级**: P1
**状态**: 新增

#### Scenario: 用户删除已取消的批次

**Given**:
- 批次batch_005状态为cancelled
- 目录存在：cases/case_001/simulations/plan_opti/batch_005/

**When**:
- 用户发送 DELETE /api/v1/control/batch-optimization/batch/batch_005

**Then**:
- 系统尝试调用 cancel_batch（失败但继续）
- 系统执行 shutil.rmtree() 删除批次目录
- 系统从 batches_index.json 移除该批次记录
- 返回200响应
  - deleted: true
  - deleted_at: ISO timestamp
- 批次目录完全删除，不可恢复

---

#### Scenario: 删除运行中的批次

**Given**:
- 批次batch_006正在运行 (status="running")

**When**:
- 用户发送 DELETE /api/v1/control/batch-optimization/batch/batch_006

**Then**:
- 系统先调用 cancel_batch 取消运行中的任务
- 系统等待1秒让SUMO进程完全关闭
- 系统重试3次删除目录（每次间隔0.5秒）
- 系统删除成功或返回警告
- 返回200响应

---

#### Scenario: 目录删除失败但标记为已删除

**Given**:
- 批次目录中有文件仍被某个进程占用

**When**:
- 系统尝试3次删除，但全部失败
- 系统无法继续等待

**Then**:
- 系统更新 batches_index.json 标记该批次为已删除
- 系统返回200响应
  - deleted: true
  - warning: "目录删除失败，但批次已标记为已删除"
- 目录可能仍存在（留待手动清理）
- 但批次从索引中移除

---

### Requirement: 取消后的批次可以重新启动

系统MUST支持对已取消的批次调用 start API 来重新启动。系统MUST：
- 检查批次目录仍然存在
- 检查配置文件仍然存在
- 重新启动仿真执行

**优先级**: P1
**状态**: 新增

#### Scenario: 重新启动已取消的批次

**Given**:
- 批次batch_007已被取消 (status="cancelled")
- 批次目录和所有配置文件保留

**When**:
- 用户发送 POST /api/v1/control/batch-optimization/batch/batch_007/start

**Then**:
- 系统检查批次目录存在
- 系统检查批次元数据存在
- 系统更新批次状态为"running"
- 系统重新启动调度器执行任务
- 所有任务状态重置为pending
- 系统开始并发执行任务

---

## API Endpoints

### POST /api/v1/control/batch-optimization/batch/{batch_id}/cancel

**功能**: 取消批次，保留目录

**成功响应 (200)**:
```json
{
  "code": 200,
  "message": "批次已取消 (6 个任务被取消)",
  "data": {
    "batch_id": "batch_001",
    "status": "cancelled",
    "cancelled_count": 6,
    "killed_count": 3,
    "cancelled_at": "2025-11-02T10:15:30.123456"
  }
}
```

**失败响应 (400)**:
```json
{
  "code": 400,
  "message": "Cannot cancel batch with status: completed"
}
```

---

### DELETE /api/v1/control/batch-optimization/batch/{batch_id}

**功能**: 删除批次，删除目录

**成功响应 (200)**:
```json
{
  "code": 200,
  "message": "删除批次成功",
  "data": {
    "batch_id": "batch_001",
    "deleted": true,
    "deleted_at": "2025-11-02T10:20:00.123456"
  }
}
```

**警告响应 (200)**:
```json
{
  "code": 200,
  "message": "删除批次成功",
  "data": {
    "batch_id": "batch_001",
    "deleted": true,
    "deleted_at": "2025-11-02T10:20:00.123456",
    "warning": "目录删除失败，但批次已标记为已删除"
  }
}
```

---

## Data Structures

### batch_metadata.json 更新

```json
{
  "batch_id": "batch_001",
  "case_id": "case_001",
  "status": "cancelled",              // ← 新增状态
  "created_at": "2025-11-02T10:00:00.000000",
  "started_at": "2025-11-02T10:05:00.000000",
  "cancelled_at": "2025-11-02T10:15:30.123456",  // ← 新增
  "batch_params": {
    "plan_ids": ["baseline_plan", "plan_001"],
    "num_seeds": 3,
    "base_seed": 66
  }
}
```

### batch_progress.json 更新

```json
{
  "batch_id": "batch_001",
  "status": "cancelled",              // ← 已更新
  "progress": 1.0,                    // ← 100%（所有任务处理完毕）
  "total_tasks": 6,
  "completed_tasks": 0,
  "cancelled_tasks": 6,               // ← 新增字段
  "running_tasks": 0,                 // ← 已清零
  "failed_tasks": 0,
  "tasks": [
    {
      "task_id": "task_001",
      "status": "cancelled",          // ← 已更新
      "error": "Cancelled by user",   // ← 取消原因
      "progress": 0
    },
    ...
  ]
}
```

---

## Implementation Details

### 取消操作流程

1. **验证状态** - 检查批次是否允许取消
2. **获取任务列表** - 从progress.json或重建（pending状态）
3. **杀死进程** - 对每个running任务的SUMO进程执行taskkill
4. **更新任务** - 标记所有pending/running任务为cancelled
5. **更新元数据** - 更新batch_metadata.json和progress.json
6. **更新索引** - 更新batches_index.json中的状态
7. **清理资源** - 从活跃进程字典移除
8. **保留目录** - 所有文件保留以便重新启动

### 删除操作流程

1. **查找批次** - 从batch_id在所有case中查找
2. **取消任务** - 如果还在运行，先调用cancel_batch
3. **等待关闭** - 等待1秒让SUMO进程关闭
4. **重试删除** - 最多重试3次，间隔0.5秒
5. **更新索引** - 从batches_index.json移除
6. **优雅降级** - 如果删除失败，仍标记为已删除

### 进度计算（包含cancelled任务）

```
总进度 % = (completed + failed + cancelled) / total × 100
```

---

## Status Transition

```
           创建
            ↓
    ┌─────────────┐
    │   pending   │
    └──────┬──────┘
           │
       启动批次
           ↓
    ┌─────────────┐
    │   running   │
    └───┬──────┬──┴─────┐
        │      │        │
      取消   完成     失败
        ↓      ↓        ↓
    ┌────────┐ ┌──────┐ ┌─────┐
    │cancelled│ │compl.│ │fail.│
    │保留目录 │ │保留  │ │保留 │
    │可重启  │ │结果  │ │调试 │
    └────────┘ └──────┘ └─────┘
        │       │       │
        └───────┴───────┘
              │
          删除批次
              ↓
         archived (已删除)
```

---

## Related Specs

- [simulation-cancellation](../simulation-cancellation/spec.md) - 单个仿真取消
- [batch-optimization](../batch-optimization/spec.md) - 批量仿真优化

---

## Testing

### Unit Tests

- [ ] test_cancel_running_batch - 取消运行中的批次
- [ ] test_cancel_pending_batch - 取消待运行批次
- [ ] test_cancel_completed_batch - 尝试取消已完成批次（应失败）
- [ ] test_cancel_idempotent - 多次取消同一批次（幂等性）
- [ ] test_delete_cancelled_batch - 删除已取消的批次
- [ ] test_delete_with_retry - 删除失败重试机制
- [ ] test_batch_progress_calculation_with_cancelled - 进度计算包含cancelled任务

### Integration Tests

- [ ] test_cancel_and_restart_workflow - 取消→重启工作流
- [ ] test_kill_sumo_process - 验证SUMO进程被正确杀死
- [ ] test_directory_preserved_after_cancel - 验证取消后目录保留
- [ ] test_restart_cancelled_batch - 取消后重新启动

---

## Status

- **Started**: 2025-11-02
- **Completed**: 2025-11-02
- **Version**: 1.0
