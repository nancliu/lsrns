# simulation-cancellation Specification

## Purpose

支持用户取消运行中的单个仿真任务。系统能够优雅地终止 SUMO 进程，更新仿真状态，防止孤儿进程泄漏，并可在取消后重新启动仿真。

## Requirements

### Requirement: 用户可以取消运行中的仿真

用户MUST能够取消任何运行中（status=running）的仿真任务。系统MUST杀死对应的 SUMO 子进程，更新仿真状态为"cancelled"，并保留仿真目录和文件以便之后重新启动。

**优先级**: P1
**状态**: 新增

#### Scenario: 用户取消运行中的仿真

**Given**:
- Case case_001存在
- 仿真sim_001正在运行中 (status="running")
- SUMO进程正在执行 (PID: 12345)

**When**:
- 用户发送 POST /api/v1/simulation/cancel_simulation/
- 请求参数：case_id=case_001, simulation_id=sim_001

**Then**:
- 系统从 progress.json 获取SUMO进程的PID (12345)
- 系统执行 taskkill /PID 12345 /F 杀死进程
- 系统更新 simulation_metadata.json:
  - status: "cancelled"
  - cancelled_at: ISO timestamp
- 系统更新 progress.json:
  - status: "cancelled"
  - message: "仿真已取消"
  - pid: null
- 系统移除进程从活跃进程字典
- 返回200响应，包含成功信息
- 仿真目录保留，用户可以重新启动

---

#### Scenario: 用户尝试取消已完成的仿真

**Given**:
- 仿真sim_002已完成 (status="completed")

**When**:
- 用户发送 POST /api/v1/simulation/cancel_simulation/
- 请求参数：case_id=case_001, simulation_id=sim_002

**Then**:
- 系统检查仿真状态为"completed"
- 系统返回400错误
- 错误信息："仿真状态为 completed，无法取消"
- 仿真状态不变

---

#### Scenario: 取消仿真后可重新启动

**Given**:
- 仿真sim_003已被取消 (status="cancelled")
- 仿真目录和配置文件保留

**When**:
- 用户发送 POST /api/v1/simulation/start_simulation/
- 请求参数：case_id=case_001, simulation_id=sim_003

**Then**:
- 系统检查仿真目录存在
- 系统检查 simulation.sumocfg 存在
- 系统重新启动SUMO进程
- 系统更新仿真状态为"running"
- 仿真可以继续执行

---

### Requirement: 系统防止孤儿进程泄漏

系统MUST在应用程序级别跟踪所有活跃的仿真进程，并确保在进程完成或取消时立即清理。系统MUST支持两种进程查找方式（活跃进程字典和PID文件），以应对应用重启等情况。

**优先级**: P1
**状态**: 新增

#### Scenario: 应用重启后仍可取消仿真

**Given**:
- 仿真sim_004正在运行，PID: 54321
- 进度文件 progress.json 中记录了PID
- 应用意外重启

**When**:
- 应用重启后，用户发送取消请求
- 系统无法从活跃进程字典找到进程

**Then**:
- 系统从 progress.json 中读取PID (54321)
- 系统执行 taskkill /PID 54321 /F
- 仿真状态更新为"cancelled"
- 进程被成功杀死

---

### Requirement: 进度计算中正确处理失败和取消的任务

系统在计算批次总进度时MUST将失败和取消的任务视为"已处理完毕"，采用公式：
```
总进度 % = (已完成 + 已失败 + 已取消) / 总任务数 × 100
```

**优先级**: P1
**状态**: 新增

#### Scenario: 计算包含已取消任务的批次进度

**Given**:
- 批次包含6个任务
- 状态分布：2个completed, 1个cancelled, 1个running(50%), 2个pending

**When**:
- 系统计算批次总进度

**Then**:
- 系统计算：(2×100 + 1×100 + 1×50) / (6×100) = 66.7%
- 进度条显示66.7%
- cancelled任务被视为已处理，不再增加

---

## API Endpoints

### POST /api/v1/simulation/cancel_simulation/

**请求参数**:
```json
{
  "case_id": "case_001",
  "simulation_id": "sim_001"
}
```

**成功响应 (200)**:
```json
{
  "code": 200,
  "message": "仿真已成功取消",
  "data": {
    "success": true,
    "message": "仿真已成功取消",
    "simulation_id": "sim_001",
    "status": "cancelled"
  }
}
```

**失败响应 (400)**:
```json
{
  "code": 400,
  "message": "仿真状态为 completed，无法取消",
  "data": {
    "success": false,
    "message": "仿真状态为 completed，无法取消",
    "simulation_id": "sim_001"
  }
}
```

**失败响应 (404)**:
```json
{
  "code": 404,
  "message": "仿真目录不存在: sim_001",
  "data": null
}
```

---

## Data Structures

### simulation_metadata.json 更新

```json
{
  "simulation_id": "sim_001",
  "case_id": "case_001",
  "status": "cancelled",           // ← 新增状态
  "created_at": "2025-11-02T10:00:00.000000",
  "started_at": "2025-11-02T10:05:00.000000",
  "cancelled_at": "2025-11-02T10:15:30.123456",  // ← 新增
  "simulation_type": "microscopic",
  "simulation_params": {...}
}
```

### progress.json 更新

```json
{
  "status": "cancelled",          // ← 已更新
  "percent": 45,
  "message": "仿真已取消",
  "updated_at": "2025-11-02T10:15:30.123456",
  "pid": null,                    // ← 已清空
  "summary": {...}
}
```

---

## Implementation Details

### 进程管理策略

1. **进程追踪**
   - SimulationService.__init__() 初始化 active_processes 字典
   - 启动仿真时，将进程对象保存到字典
   - 进程完成时，从字典移除

2. **双重查找机制**
   - 优先从 active_processes 字典查找（内存中）
   - 备用：从 progress.json 读取 PID（文件中）
   - 支持应用重启后的进程恢复

3. **进程终止流程**
   - 调用 proc.terminate() 发送SIGTERM信号
   - 等待2秒让进程优雅关闭
   - 如果进程仍未关闭，调用 proc.kill() 强制杀死
   - Windows环境使用 taskkill 命令

### 状态转换

```
running
  ↓
[cancel_simulation() called]
  ↓
cancelled
  ↓
[可选：start_simulation()]
  ↓
running (重新启动)
```

---

## Related Specs

- [batch-cancellation](../batch-cancellation/spec.md) - 批次取消功能
- [batch-optimization](../batch-optimization/spec.md) - 批量仿真优化

---

## Testing

### Unit Tests

- [ ] test_cancel_running_simulation - 取消运行中的仿真
- [ ] test_cancel_pending_simulation - 尝试取消待运行仿真（应失败）
- [ ] test_cancel_completed_simulation - 尝试取消已完成仿真（应失败）
- [ ] test_process_cleanup_on_cancel - 验证进程被正确杀死
- [ ] test_directory_preserved_after_cancel - 验证目录保留
- [ ] test_restart_cancelled_simulation - 取消后重新启动

### Integration Tests

- [ ] test_cancel_and_restart_workflow - 取消→重启工作流
- [ ] test_app_restart_with_running_process - 应用重启后恢复进程

---

## Status

- **Started**: 2025-11-02
- **Completed**: 2025-11-02
- **Version**: 1.0
