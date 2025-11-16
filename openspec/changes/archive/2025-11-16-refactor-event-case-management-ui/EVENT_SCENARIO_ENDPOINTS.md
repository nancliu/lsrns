# 事件场景仿真 - 专用端点和接口说明

**问题**: 事件场景仿真，是否在scenarios下实现了专用的端点或接口？

**答案**: ✅ 是的。系统实现了两层专用接口：
1. **`/api/v1/batch/*` 端点** - 事件批次管理（batch_routes.py）
2. **`/api/v1/scenario/*` 端点** - 场景管理（scenario_routes.py）

---

## 📋 端点总览

### 1️⃣ 事件批次管理端点（batch_routes.py）

这些端点**专门为事件场景仿真**实现：

#### A. 创建事件批次
```
POST /api/v1/batch/create-from-event
```

**功能**: 从事件创建一个批次，包含该事件的所有场景案例

**请求**:
```json
{
  "event_id": "8210655",
  "scenario_ids": ["scenario_001", "scenario_002"],  // 可选，默认全部
  "simulation_config": {
    "duration_minutes": 60,
    "output_config": ["tripinfo", "vehroute"]
  }
}
```

**响应**:
```json
{
  "batch_id": "batch_event_8210655_20251115_100000",
  "event_id": "8210655",
  "case_ids": ["case_event_8210655_001", "case_event_8210655_002"],
  "simulation_ids": ["sim_001", "sim_002", ...],
  "total_simulations": 10,
  "created_at": "2025-11-15T10:00:00"
}
```

**用途**: Phase 2 的起点 - 为事件创建所有需要的仿真

---

#### B. 启动事件批次
```
POST /api/v1/batch/start-event-batch
```

**功能**: 启动批次中的所有仿真

**请求**:
```json
{
  "batch_id": "batch_event_8210655_20251115_100000",
  "parallel_workers": 4,  // 1-8, 默认 4
  "auto_run_analysis": true
}
```

**响应**:
```json
{
  "batch_id": "batch_event_8210655_20251115_100000",
  "status": "running",
  "total_simulations": 10,
  "started_at": "2025-11-15T10:05:00"
}
```

**用途**: Phase 2 中 case-simulation-center.html 调用的核心端点

---

#### C. 获取事件批次状态
```
GET /api/v1/batch/event-batch-status/{batch_id}
```

**功能**: 实时查询批次中所有仿真的进度

**响应**:
```json
{
  "batch_id": "batch_event_8210655_20251115_100000",
  "event_id": "8210655",
  "status": "running",
  "progress_percentage": 45,
  "simulations": [
    {
      "simulation_id": "sim_001",
      "status": "completed",
      "progress": 100
    }
  ],
  "summary": {
    "total": 10,
    "completed": 4,
    "running": 2,
    "created": 4,
    "failed": 0
  }
}
```

**用途**: Phase 2 中展开/折叠进度监控面板的数据源（备选）

---

#### D. 列出事件批次
```
GET /api/v1/batch/list-event-batches?status=running&limit=50
```

**功能**: 列出所有事件批次，支持按状态过滤

**响应**:
```json
{
  "batches": [
    {
      "batch_id": "batch_event_8210655_...",
      "event_id": "8210655",
      "created_at": "2025-11-15T10:00:00",
      "status": "running",
      "progress_percentage": 45
    }
  ],
  "total_count": 5
}
```

**用途**: 事件列表或历史查询

---

#### E. 获取事件批次聚合结果
```
GET /api/v1/batch/event-batch-results/{batch_id}
```

**功能**: 获取批次中所有仿真的聚合分析结果（按控制策略分组）

**响应**:
```json
{
  "batch_id": "batch_event_8210655_...",
  "event_id": "8210655",
  "strategies": [
    {
      "strategy": "no_control",
      "avg_metrics": { "avg_speed": 45.2, "total_delay": 1234 }
    },
    {
      "strategy": "vss",
      "avg_metrics": { "avg_speed": 48.5, "total_delay": 890 },
      "improvement_vs_baseline": { "speed_increase": 7.3, "delay_reduction": 28 }
    }
  ]
}
```

**用途**: 对比分析页面的数据源（策略聚合对比）

---

#### F. 管理端点（辅助）
```
DELETE /api/v1/batch/delete-event-cases/{event_id}
DELETE /api/v1/batch/reset-scenario-mapping/{case_id}
DELETE /api/v1/batch/clear-scenario-cases/{scenario_id}
POST /api/v1/batch/reset-all-scenario-mappings
```

**用途**: 清理和重置（非前端常用）

---

### 2️⃣ 场景管理端点（scenario_routes.py）

这些端点提供了**事件和场景的查询接口**：

#### A. 列出场景
```
GET /api/v1/scenario/list
?event_type=01_accident&strategy=vss&page=1&page_size=20
```

**功能**: 列出所有可用场景，支持过滤

**响应**:
```json
{
  "scenarios": [
    {
      "scenario_id": "scenario_8210655_vss",
      "event_id": "8210655",
      "event_type": "01_accident",
      "strategy": "vss",
      "network_file": "network_2_lanes.net.xml",
      "created_cases": []
    }
  ],
  "total_count": 100,
  "page": 1
}
```

**用途**: 前端显示可用场景列表

---

#### B. 获取事件的所有场景
```
GET /api/v1/scenario/by-event/{event_id}
```

**功能**: 获取某个事件的所有场景变量（no_control, vss, tec, dhs 等）

**响应**:
```json
{
  "event_id": "8210655",
  "scenarios": [
    {
      "scenario_id": "scenario_8210655_no_control",
      "strategy": "no_control"
    },
    {
      "scenario_id": "scenario_8210655_vss",
      "strategy": "vss"
    },
    {
      "scenario_id": "scenario_8210655_tec",
      "strategy": "tec"
    }
  ],
  "total_count": 3
}
```

**用途**: 事件创建时获取该事件的所有可用场景

---

#### C. 获取单个场景
```
GET /api/v1/scenario/{scenario_id}
```

**功能**: 获取特定场景的详细信息

**响应**:
```json
{
  "scenario_id": "scenario_8210655_vss",
  "event_id": "8210655",
  "event_type": "01_accident",
  "strategy": "vss",
  "network_file": "network_2_lanes.net.xml",
  "created_cases": ["case_event_8210655_001"]
}
```

**用途**: 获取场景详情

---

#### D. 创建批量案例
```
POST /api/v1/scenario/create-case-batch
```

**功能**: 为事件的多个场景批量创建案例（Phase 2 的替代方案）

**请求**:
```json
{
  "event_id": "8210655",
  "scenario_ids": ["scenario_8210655_no_control", "scenario_8210655_vss"]
}
```

**响应**:
```json
{
  "event_id": "8210655",
  "case_ids": ["case_event_8210655_001", "case_event_8210655_002"],
  "scenarios_affected": 2
}
```

**用途**: 与 `/api/v1/batch/create-from-event` 功能类似

---

## 🔄 工作流示意

### Phase 2 推荐的工作流

```
┌─────────────────────────────────────────────┐
│  Step 1: 用户选择事件                        │
└─────────────────────────────────────────────┘
                    ↓
         GET /api/v1/scenario/by-event/{event_id}
                    ↓
         返回该事件的所有场景 (no_control, vss, tec...)
                    ↓
┌─────────────────────────────────────────────┐
│  Step 2: 创建批次                            │
└─────────────────────────────────────────────┘
                    ↓
    POST /api/v1/batch/create-from-event
    {
      "event_id": "8210655",
      "scenario_ids": ["scenario_8210655_vss", "scenario_8210655_tec"]
    }
                    ↓
    返回 batch_id 和 case_ids
                    ↓
┌─────────────────────────────────────────────┐
│  Step 3: 在 case-simulation-center.html      │
│  显示案例列表和批次控制（Phase 2）            │
└─────────────────────────────────────────────┘
                    ↓
         用户选择案例并启动
                    ↓
    POST /api/v1/batch/start-event-batch
    {
      "batch_id": "batch_event_8210655_...",
      "parallel_workers": 4,
      "auto_run_analysis": true
    }
                    ↓
┌─────────────────────────────────────────────┐
│  Step 4: 实时监控进度                        │
└─────────────────────────────────────────────┘
                    ↓
      GET /api/v1/simulation/simulation_progress/{case_id}
                 （定期查询）
                    ↓
    或者（备选）
                    ↓
      GET /api/v1/batch/event-batch-status/{batch_id}
                    ↓
         展示进度条和统计卡片
                    ↓
┌─────────────────────────────────────────────┐
│  Step 5: 查看分析和对比                      │
└─────────────────────────────────────────────┘
                    ↓
    跳转到 analysis_viewer.html
                    ↓
  GET /api/v1/analysis/comparison/{batch_id}?case_id=...
```

---

## 🎯 API 选择矩阵

| 操作 | 推荐 API | 替代方案 | 备注 |
|------|---------|---------|------|
| 获取事件的场景 | `GET /scenario/by-event/{event_id}` | - | 必需，获取该事件的所有可用场景 |
| 为事件创建批次 | `POST /batch/create-from-event` | `POST /scenario/create-case-batch` | 推荐前者，功能更完整 |
| 启动批次 | `POST /batch/start-event-batch` | - | 必需，启动所有仿真 |
| 查询进度（单案例） | `GET /simulation/simulation_progress/{case_id}` | - | 推荐用于 Phase 2 |
| 查询进度（整批） | `GET /batch/event-batch-status/{batch_id}` | - | 可选，聚合视图 |
| 获取对比数据 | `GET /analysis/comparison/{batch_id}` | - | 必需，对比分析 |
| 获取聚合结果 | `GET /batch/event-batch-results/{batch_id}` | - | 可选，按策略聚合 |

---

## 📌 关键设计原则

### 1. 事件 → 场景 → 案例 → 仿真的映射

```
事件 (event_id)
  ├─ 场景1 (scenario_id)
  │   └─ 案例1 (case_id)
  │       └─ 仿真列表 (simulation_ids)
  │
  ├─ 场景2 (scenario_id)
  │   └─ 案例2 (case_id)
  │       └─ 仿真列表 (simulation_ids)
  │
  └─ 场景N
      └─ 案例N
          └─ 仿真列表

一个事件 = 一个批次
```

### 2. batch_id 格式设计

```javascript
// 事件批次格式
batch_event_8210655_20251115_100000

含义：
- batch_event: 前缀，表示是事件批次
- 8210655: 事件 ID
- 20251115: 创建日期
- 100000: 时间戳（毫秒）
```

### 3. 场景与案例的一对一关系

```javascript
// 每个场景对应一个案例
1 Scenario → 1 Case → N Simulations

// 不是这样
1 Scenario → N Cases (❌ 不正确)
```

---

## ⚠️ Phase 2 中要注意的点

### 1. 不要混淆两个"create"接口

```javascript
✅ 推荐：POST /api/v1/batch/create-from-event
   用途：创建事件批次（包含案例和仿真）

⚠️ 可选：POST /api/v1/scenario/create-case-batch
   用途：仅创建案例（仿真在启动时创建）
   只在特殊情况下使用
```

### 2. case_id 的命名规范

```javascript
✅ 正确的事件案例 ID：
   case_event_8210655_001
   case_event_8210655_002

❌ 不要：
   case_8210655_001     (缺少 _event_)
   case_vss_001         (不包含事件 ID)
   case_scenario_001    (应该用事件 ID，不用场景 ID)
```

### 3. 进度查询的两种方式

```javascript
// 方式 1：查询单个案例（推荐用于 Phase 2）
GET /api/v1/simulation/simulation_progress/{case_id}
返回：该案例的所有仿真进度

// 方式 2：查询整个批次（可选）
GET /api/v1/batch/event-batch-status/{batch_id}
返回：该批次所有案例的聚合进度

// Phase 2 建议：优先使用方式 1（case_id），
// 如果需要跨案例聚合，使用方式 2
```

---

## 🚀 前端实现建议

### case-simulation-center.html 初始化

```javascript
// 初始化时：
async function initPage() {
  // 获取事件 ID
  const eventId = getEventIdFromUrl();

  // 获取该事件的所有场景
  const scenariosResponse = await fetch(
    `/api/v1/scenario/by-event/${eventId}`
  );
  const scenarios = await scenariosResponse.json();

  // 为该事件创建批次
  const createResponse = await fetch(
    '/api/v1/batch/create-from-event',
    {
      method: 'POST',
      body: JSON.stringify({
        event_id: eventId,
        scenario_ids: scenarios.scenarios.map(s => s.scenario_id)
      })
    }
  );

  const { batch_id, case_ids } = await createResponse.json();

  // 保存 batch_id 和 case_ids
  sessionStorage.setItem('currentBatchId', batch_id);
  sessionStorage.setItem('currentCaseIds', JSON.stringify(case_ids));

  // 显示案例列表
  displayCaseList(case_ids);
}
```

### 启动仿真

```javascript
async function startSimulations() {
  const batchId = sessionStorage.getItem('currentBatchId');

  const response = await fetch('/api/v1/batch/start-event-batch', {
    method: 'POST',
    body: JSON.stringify({
      batch_id: batchId,
      parallel_workers: 4,
      auto_run_analysis: true
    })
  });

  const result = await response.json();

  // 打开进度监控面板
  toggleMonitoringPanel(true);

  // 开始定时刷新进度
  startProgressPolling();
}
```

### 进度监控

```javascript
async function pollProgress() {
  const caseIds = JSON.parse(
    sessionStorage.getItem('currentCaseIds')
  );

  // 查询所有案例的进度
  const progressList = await Promise.all(
    caseIds.map(caseId =>
      fetch(`/api/v1/simulation/simulation_progress/${caseId}`)
        .then(r => r.json())
    )
  );

  // 聚合进度
  const totalProgress = aggregateProgress(progressList);

  // 更新 UI
  updateProgressBar(totalProgress.percentage);
  updateStatCards(totalProgress.summary);
  updateDetailTable(progressList);
}
```

---

## 📚 相关文档

- [API_ENDPOINTS_GUIDE.md](API_ENDPOINTS_GUIDE.md) - 所有 API 详细说明
- [BATCH_ID_CLARIFICATION.md](BATCH_ID_CLARIFICATION.md) - 批次 ID 的使用规范
- [CASE_SIMULATION_CENTER_SCOPE.md](CASE_SIMULATION_CENTER_SCOPE.md) - case-simulation-center.html 的范围

---

**版本**: 1.0
**日期**: 2025-11-16
**适用到**: Phase 2
**关键性**: 🔴 核心 - 定义了事件场景仿真的核心接口
