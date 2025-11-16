# 批次 ID 传递方式澄清 - 事件批次 vs 方案优化

**重要**: 本文档澄清事件场景批次仿真和方案优化批次仿真中 batch_id 的使用差异。

---

## 问题背景

在 Phase 2 实现中，有两种不同的批次管理方式：

1. **事件场景批次仿真** (Event-Scenario Batch)
   - 路由: `/api/batch/create-from-event`
   - 一个事件 = 一个批次
   - 包含多个场景 → 多个案例 → 多个仿真

2. **方案优化批次仿真** (Batch Optimization)
   - 路由: `/api/v1/simulation/batch-start`
   - 用户自定义仿真列表
   - 直接传递 simulation_ids 列表

这两种方式的 **batch_id 传递机制不同**。

---

## 对比详解

### 1. 事件场景批次 (Batch Routes)

#### 创建批次
```bash
POST /api/batch/create-from-event

Request:
{
  "event_id": "event_8210655",
  "scenario_ids": ["scenario_001", "scenario_002"],  # 可选，默认全部
  "simulation_config": {...}  # 可选
}

Response:
{
  "batch_id": "batch_event_8210655_20251115_100000",  # ← 批次ID格式
  "event_id": "event_8210655",
  "status": "created",
  "case_ids": ["case_001", "case_002"],              # ← 返回案例列表
  "simulation_ids": ["sim_001", "sim_002", ...],    # ← 返回仿真列表
  "total_simulations": 10,
  "created_at": "2025-11-15T10:00:00"
}
```

#### 启动批次
```bash
POST /api/batch/start-batch

Request:
{
  "batch_id": "batch_event_8210655_20251115_100000"  # ← 直接传递 batch_id
}

Response:
{
  "batch_id": "batch_event_8210655_20251115_100000",
  "status": "running",
  "started_at": "2025-11-15T10:05:00"
}
```

#### 特点

```
创建批次 → 返回 batch_id
              ↓
         保存 batch_id（案例/仿真映射已在后端）
              ↓
          启动批次 → 只需传递 batch_id
              ↓
      查询状态 → 通过 batch_id 查询全部仿真进度
```

**关键特点**:
- ✅ batch_id 是全局标识符（包含事件信息）
- ✅ 批次创建时已确定所有案例和仿真的关系
- ✅ 启动和查询都只需 batch_id（无需 simulation_ids 列表）
- ✅ 案例和仿真的映射在后端维护

---

### 2. 方案优化批次 (Simulation Routes)

#### 启动批次
```bash
POST /api/v1/simulation/batch-start

Request:
{
  "case_id": "case_20251112_001",
  "simulation_ids": ["sim_001", "sim_002", "sim_003"],  # ← 直接传递仿真ID列表
  "parallel_workers": 4,
  "auto_run_analysis": true,
  "analysis_types": ["accuracy", "edgedata"]
}

Response:
{
  "batch_id": "batch_20251112_100000",  # ← 返回 batch_id（为了追踪）
  "total_simulations": 3,
  "status": "queued",
  "started_at": "2025-11-16T10:00:00"
}
```

#### 特点

```
直接启动 → 需要传递 simulation_ids 列表
              ↓
         返回 batch_id（仅用于查询）
              ↓
      查询状态 → batch_id 或 case_id 都可以
```

**关键特点**:
- ✅ batch_id 是返回值（追踪用）
- ✅ 用户必须提供 simulation_ids 列表
- ✅ 无需提前创建批次
- ✅ 案例和仿真的关系由前端维护（在请求中明确指定）

---

## Phase 2 中的正确用法

### 场景 A：事件场景工作流（推荐）

使用事件场景批次方式：

```javascript
// 步骤1：从事件创建批次
async function createEventBatch() {
  const response = await fetch('/api/batch/create-from-event', {
    method: 'POST',
    body: JSON.stringify({
      event_id: 'event_8210655',
      scenario_ids: ['scenario_001', 'scenario_002']
    })
  });

  const result = await response.json();
  const batchId = result.data.batch_id;  // ← 保存 batch_id

  // 保存到 sessionStorage 或状态管理
  sessionStorage.setItem('currentBatchId', batchId);

  return result.data;  // 包含 case_ids, simulation_ids
}

// 步骤2：启动批次
async function startEventBatch(batchId) {
  const response = await fetch('/api/batch/start-batch', {
    method: 'POST',
    body: JSON.stringify({
      batch_id: batchId  // ← 只需 batch_id
    })
  });

  return await response.json();
}

// 步骤3：查询进度（通过 case_id）
async function getProgress(caseId) {
  const response = await fetch(
    `/api/v1/simulation/simulation_progress/${caseId}`
  );

  return await response.json();
}

// 步骤4：获取对比分析（通过 batch_id）
async function getComparison(batchId, caseId) {
  const response = await fetch(
    `/api/v1/analysis/comparison/${batchId}?case_id=${caseId}`
  );

  return await response.json();
}
```

**流程**: 事件 → 创建批次 → 获得 batch_id + 案例 → 启动 → 查询

---

### 场景 B：用户手动选择仿真（备选）

使用方案优化批次方式（当用户在 UI 中手动选择仿真时）：

```javascript
// 步骤1：用户选择仿真列表
const selectedSimulationIds = [
  'sim_001',
  'sim_002',
  'sim_003'
];

// 步骤2：直接启动（无需预先创建）
async function startCustomBatch(caseId, simIds) {
  const response = await fetch('/api/v1/simulation/batch-start', {
    method: 'POST',
    body: JSON.stringify({
      case_id: caseId,
      simulation_ids: simIds,  // ← 直接传递列表
      parallel_workers: 4,
      auto_run_analysis: true
    })
  });

  const result = await response.json();
  const batchId = result.data.batch_id;  // ← 保存返回的 batch_id

  return batchId;
}

// 步骤3：查询进度
async function getProgress(caseId) {
  // 注意：这里仍然用 case_id，不用 batch_id
  const response = await fetch(
    `/api/v1/simulation/simulation_progress/${caseId}`
  );

  return await response.json();
}
```

**流程**: 用户选择 → 启动 → 获得 batch_id → 查询

---

## Phase 2 API 端点调整建议

### 现状

| 端点 | 类型 | 传参方式 | 备注 |
|------|------|---------|------|
| `/api/batch/create-from-event` | POST | event_id | 事件批次 |
| `/api/batch/start-batch` | POST | batch_id | 事件批次 |
| `/api/v1/simulation/batch-start` | POST | simulation_ids | 优化批次 |
| `/api/v1/simulation/simulation_progress/{case_id}` | GET | case_id | ✅ 推荐用 case_id |
| `/api/v1/analysis/comparison/{batch_id}` | GET | batch_id | ✅ 推荐用 batch_id |

### 改进建议

为了使事件场景批次和方案优化批次都能正常工作，**后端应支持**：

#### 建议 1：统一进度查询接口

```bash
# 当前（推荐保持）
GET /api/v1/simulation/simulation_progress/{case_id}

# 新增（可选）
GET /api/v1/simulation/batch-progress/{batch_id}
  Returns: 聚合该 batch_id 下的所有案例的进度统计
```

#### 建议 2：明确对比分析接口的 batch_id 来源

```bash
# 当前
GET /api/v1/analysis/comparison/{batch_id}?case_id=...

# 后端需要支持两种 batch_id：
# - batch_event_8210655_... (事件批次)
# - batch_20251112_100000 (优化批次)
```

#### 建议 3：前端需要知道来源

```javascript
// 前端在 case-simulation-center.html 中需要记录：
const batchContext = {
  type: 'event',  // 或 'optimization'
  batchId: 'batch_event_8210655_20251115_100000',  // 事件批次
  caseIds: ['case_001', 'case_002'],
  eventId: 'event_8210655'
  // 或
  type: 'optimization',  // 优化批次
  batchId: 'batch_20251112_100000',
  caseId: 'case_20251112_001',
  simulationIds: ['sim_001', 'sim_002']
};
```

---

## Phase 2 实现清单

### 前端需要做的

- [ ] **case-simulation-center.html**
  - [ ] 识别当前批次类型（事件 or 优化）
  - [ ] 如果是事件批次，保存 batch_id 和 case_ids
  - [ ] 如果是优化批次，保存 batch_id 和 caseId
  - [ ] 进度监控：使用 case_id 查询 `/api/v1/simulation/simulation_progress/{case_id}`
  - [ ] 对比分析：使用 batch_id 查询 `/api/v1/analysis/comparison/{batch_id}`

- [ ] **analysis_viewer.html**
  - [ ] 接收 URL 参数 ?batch_id=... 或 ?case_id=...
  - [ ] 根据参数类型调用相应 API
  - [ ] 对比分析标签页使用 batch_id

### 后端需要做的

- [ ] **验证** `/api/v1/simulation/simulation_progress/{case_id}`
  - [ ] 能否处理多个案例
  - [ ] 是否需要支持 batch_id 作为参数

- [ ] **验证** `/api/v1/analysis/comparison/{batch_id}`
  - [ ] 是否支持事件批次的 batch_id 格式
  - [ ] 是否支持优化批次的 batch_id 格式

- [ ] **考虑添加** `/api/v1/simulation/batch-progress/{batch_id}`（可选）
  - [ ] 直接通过 batch_id 获取进度（不需要知道 case_id）

---

## 常见错误和修复

### 错误 1：混淆 simulation_ids 和 batch_id

❌ **错误做法**:
```javascript
// 错误：获取对比分析时用 simulation_ids
const response = await fetch(
  `/api/v1/analysis/comparison/${simulationIds.join(',')}`
);
```

✅ **正确做法**:
```javascript
// 正确：使用 batch_id
const response = await fetch(
  `/api/v1/analysis/comparison/${batchId}?case_id=${caseId}`
);
```

### 错误 2：事件批次启动时传递 simulation_ids

❌ **错误做法**:
```javascript
// 错误：事件批次启动时不应该再传 simulation_ids
await fetch('/api/batch/start-batch', {
  body: JSON.stringify({
    batch_id: batchId,
    simulation_ids: [...],  // ← 不需要！
  })
});
```

✅ **正确做法**:
```javascript
// 正确：事件批次只需 batch_id
await fetch('/api/batch/start-batch', {
  body: JSON.stringify({
    batch_id: batchId  // ← 就够了
  })
});
```

### 错误 3：进度查询用 batch_id 替代 case_id

❌ **错误做法**:
```javascript
// 错误：不能用 batch_id 替代 case_id
const progress = await fetch(
  `/api/v1/simulation/simulation_progress/${batchId}`
);
```

✅ **正确做法**:
```javascript
// 正确：进度查询用 case_id
const progress = await fetch(
  `/api/v1/simulation/simulation_progress/${caseId}`
);
```

---

## 决策矩阵

使用此表格决定应该调用哪个 API：

| 操作 | 使用 API | 参数 | 备注 |
|------|---------|------|------|
| 创建事件批次 | `/api/batch/create-from-event` | event_id | 返回 batch_id |
| 启动事件批次 | `/api/batch/start-batch` | batch_id | 事件方式 |
| 启动优化批次 | `/api/v1/simulation/batch-start` | simulation_ids | 优化方式 |
| 获取进度 | `/api/v1/simulation/simulation_progress/{case_id}` | case_id | **关键** |
| 获取对比 | `/api/v1/analysis/comparison/{batch_id}` | batch_id | **关键** |
| 获取仿真列表 | `/api/v1/simulation/simulations/{case_id}` | case_id | 列出全部 |

---

## 总结

| 方面 | 事件批次 | 优化批次 |
|------|--------|--------|
| 来源 | 事件 + 场景 | 用户选择 |
| 创建方式 | API 创建 | 直接启动 |
| batch_id 来源 | 创建响应 | 启动响应 |
| 进度查询 | case_id | case_id |
| 对比查询 | batch_id | batch_id |
| 支持场景 | 事件工作流 | 手动仿真选择 |

**关键点**:
- 🎯 **进度查询始终用 case_id**（不管是哪种批次）
- 🎯 **对比查询始终用 batch_id**（不管是哪种批次）
- 🎯 **不要混淆 simulation_ids 和 batch_id**

---

**文档版本**: 1.0
**最后更新**: 2025-11-16
**适用版本**: Phase 2 及以后
