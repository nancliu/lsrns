# 事件批次仿真 - 两层进度监控实现指南

## 概述

事件批次仿真的进度监控采用**两层分层架构**：

1. **第一层（事件案例级）**：多个场景的汇总进度
2. **第二层（场景级）**：该场景下的simulation完成进度

---

## 架构设计

### 数据结构层级

```
事件批次 (Event Case / case_id)
├── 场景 1 (Scenario 1)
│   ├── Simulation 1.1
│   ├── Simulation 1.2
│   └── Simulation 1.3
├── 场景 2 (Scenario 2)
│   ├── Simulation 2.1
│   └── Simulation 2.2
└── 场景 3 (Scenario 3)
    └── Simulation 3.1
```

### 进度计算方法

#### Level 1: 事件案例级进度 (Event Case Progress)

**计算公式**：
```
EventProgress = (Total_Completed_Simulations / Total_Simulations) * 100

其中：
- Total_Completed_Simulations = 所有场景中 status='completed' 的 simulation 数量
- Total_Simulations = 所有场景的所有 simulation 总数
```

**示例**：
```
事件案例包含3个场景，共6个simulation：
- 场景1：3个simulation，1个已完成 → 33%
- 场景2：2个simulation，1个已完成 → 50%
- 场景3：1个simulation，0个已完成 → 0%

事件级进度 = (1+1+0) / (3+2+1) * 100 = 33%
```

**实现位置**：
- 后端计算：`api/services/simulation_service.py:760`
- 前端展示：`frontend/scenarios/case-simulation-center.html:1639`
- DOM 更新：`#progressPercent` 和 `#progressBar`

---

#### Level 2: 场景级进度 (Scenario Progress)

**计算公式**：
```
ScenarioProgress = (Completed_Simulations_In_Scenario / Total_Simulations_In_Scenario) * 100

其中：
- Completed_Simulations_In_Scenario = 该场景中 status='completed' 的 simulation 数量
- Total_Simulations_In_Scenario = 该场景的 simulation 总数
```

**示例**：
```
场景1包含3个simulation：
- Simulation 1.1: status='completed', progress=100%
- Simulation 1.2: status='running', progress=45%
- Simulation 1.3: status='queued', progress=0%

场景级进度 = (1/3) * 100 = 33%
（虽然1.2已进行到45%，但场景进度仍为33%，因为只有1个完全完成）
```

**实现位置**：
- 前端计算：`frontend/scenarios/case-simulation-center.html:1718`
- 表格显示：场景行（灰色背景 `#f5f5f5`）

---

### 详细进度（Simulation Individual Progress）

**数据来源**：每个 simulation 的 `progress.json` 文件

**字段名**：`sim.progress`（百分比值，0-100）

**显示位置**：
- 最细粒度的进度条（simulation 行）
- 格式：单个simulation的即时进度

**示例**：
```
Simulation ID: sim_10754_001
Status: running
Progress: 45% (从 progress.json 读取)
```

---

## 数据流

### 1. 后端数据准备 (Backend)

**位置**：`api/services/simulation_service.py:667-787`

**流程**：
```python
get_simulation_progress(case_id):
  1. 读取 cases/{case_id}/simulations/ 目录
  2. 对每个 simulation：
     a. 读取 progress.json (如果存在)
        - sim["progress"] = progress.json.percent
        - sim["status"] = progress.json.status
     b. 否则使用 metadata.json 中的状态
  3. 计算统计：
     - stats.total = len(simulations)
     - stats.completed = count(status='completed')
     - stats.in_progress = count(status='running'|'simulating')
     - stats.failed = count(status='failed')
     - stats.queued = count(status='queued')
  4. 计算事件级进度：
     - progress_percentage = (stats.completed / stats.total) * 100
  5. 返回数据结构：
     {
       "case_id": "case_event_10754",
       "simulations": [
         {
           "simulation_id": "...",
           "case_id": "case_event_10754",
           "scenario_id": "scenario_001",
           "status": "running|completed|failed|queued",
           "progress": 45,  # from progress.json
           "progress_message": "...",
           "batch_id": "...",
           ...
         },
         ...
       ],
       "progress_percentage": 33,  # 事件级进度
       "stats": {
         "total": 6,
         "completed": 2,
         "in_progress": 3,
         "failed": 0,
         "queued": 1
       }
     }
```

**API 端点**：
```
GET /api/v1/simulation/simulation_progress/{case_id}
```

### 2. 前端数据获取 (Frontend)

**位置**：`frontend/scenarios/case-simulation-center.html:1580-1660`

**函数**：`refreshBatchStatus()`

**流程**：
```javascript
refreshBatchStatus():
  1. 调用 API：GET /api/v1/simulation/simulation_progress/{case_id}
  2. 解析响应：
     - simulations = response.simulations
     - stats = 本地重新计算或使用 response.stats
  3. 更新顶部统计卡片：
     - #totalSims = stats.total
     - #completedSims = stats.completed
     - #runningCount = stats.in_progress
     - #failedCount = stats.failed
  4. 计算事件级进度：
     - progressPercent = (stats.completed / stats.total) * 100
  5. 更新事件级进度条：
     - #progressPercent.textContent = progressPercent + '%'
     - #progressBar.style.width = progressPercent + '%'
  6. 调用 renderSimulationTable(simulations) 渲染详细表格
```

### 3. 前端表格渲染 (Frontend - Table Rendering)

**位置**：`frontend/scenarios/case-simulation-center.html:1665-1825`

**函数**：`renderSimulationTable(simulations)`

**数据分组**：
```javascript
按照两层结构分组和渲染：

simulations
  ↓
  groupByCase {
    "case_event_10754": {
      "scenario_001": [sim1, sim2, sim3],
      "scenario_002": [sim4, sim5],
      "scenario_003": [sim6]
    }
  }
```

**渲染顺序**：

1. **事件案例行** (最后插入，显示在最前)
   - 背景色：`#e8f5e9` (浅绿)
   - 字体：粗体
   - 显示内容：
     ```
     📋 事件案例: case_event_10754
     | 总数: 6 | 进行: 3 | 完成: 2
     | [进度条] 33%
     ```

2. **场景行** (每个场景一行)
   - 背景色：`#f5f5f5` (灰色)
   - 缩进：40px
   - 显示内容：
     ```
     ├─ scenario_001
     | 总数: 3 | 进行: 2 | 完成: 1
     | [进度条] 33%
     ```

3. **Simulation 行** (每个 simulation 一行)
   - 背景色：白色（默认）
   - 缩进：80px
   - 显示内容：
     ```
     └─ sim_10754_001
     | status: 仿真中 (运行中)
     | [进度条] 45% (来自 progress.json)
     ```

**场景级进度计算**：
```javascript
// Line 1718-1719
const scenarioProgressPercent = scenarioStats.total > 0 ?
    Math.round((scenarioStats.completed / scenarioStats.total) * 100) : 0;
```

其中 `scenarioStats` 统计该场景所有 simulation 的状态：
```javascript
const scenarioStats = {
    total: sims.length,
    completed: sims.filter(s => s.status === 'completed').length,
    in_progress: sims.filter(s => s.status === 'running' || s.status === 'simulating').length,
    failed: sims.filter(s => s.status === 'failed').length,
    queued: sims.filter(s => s.status === 'queued').length
};
```

---

## 重要字段说明

| 字段名 | 来源 | 数据类型 | 说明 |
|--------|------|---------|------|
| `case_id` | 批次启动时指定 | string | 事件案例 ID，形如 `case_event_10754` |
| `scenario_id` | 从场景选择获取 | string | 场景 ID |
| `simulation_id` | 创建 simulation 时生成 | string | simulation 唯一标识 |
| `status` | progress.json 或 metadata | enum | 值：`completed`, `running`, `simulating`, `failed`, `queued` |
| `progress` | progress.json 的 `percent` | number | 0-100，单个 simulation 的即时进度 |
| `progress_percentage` | 后端计算 | number | 0-100，事件案例级的聚合进度 |
| `batch_id` | progress.json 或 metadata | string | 批次 ID，形如 `case_event_10754` |

---

## 关键代码位置

### 后端

| 文件 | 函数 | 行号 | 功能 |
|------|------|------|------|
| `api/services/simulation_service.py` | `get_simulation_progress()` | 667-787 | 获取案例下所有 simulation 的进度 |
| `api/services/simulation_service.py` | `get_case_simulations()` | - | 获取案例下的 simulation 列表 |
| `api/routes/simulation_routes.py` | `get_simulation_progress()` | 63-69 | 暴露进度查询 API |

### 前端

| 文件 | 函数 | 行号 | 功能 |
|------|------|------|------|
| `frontend/scenarios/case-simulation-center.html` | `refreshBatchStatus()` | 1580-1660 | 定期刷新进度数据 |
| `frontend/scenarios/case-simulation-center.html` | `renderSimulationTable()` | 1665-1825 | 渲染分层表格 |
| `frontend/scenarios/case-simulation-center.html` | `showMonitoringPanel()` | 1077-1116 | 显示并启动监控面板 |

---

## 监控生命周期

### 启动流程

```
用户点击 "启动仿真"
  ↓
startBatch()
  ↓
调用 /api/v1/simulation/batch_start
  ↓
showMonitoringPanel()
  ↓
启动 monitoringInterval (每 1000ms 刷新一次)
  ↓
refreshBatchStatus() 循环调用
  ↓
renderSimulationTable() 更新表格
```

### 停止条件

监控在以下条件下自动停止：
```javascript
if (stats.queued === 0 && stats.in_progress === 0 && stats.total > 0) {
    clearInterval(monitoringInterval);
}
```

即：**所有任务都不在队列中，也没有运行中的任务时**

### 手动停止

用户点击 "取消批次" 按钮：
```javascript
cancelBatch()
  ↓
调用 /api/v1/simulation/cancel_batch/{case_id}
  ↓
等待后端取消
  ↓
resetCaseSimulationState()
  ↓
清空 sessionStorage 中的批次信息
  ↓
隐藏监控面板
```

---

## 常见问题排查

### Q1: 场景级进度显示为 0%，但有 simulation 在运行

**原因**：场景级进度基于 **completion count**，而非平均进度
- 只有当 simulation 的 status 变为 `completed` 时，场景进度才会增加
- 即使 simulation 显示 45% 的单个进度，场景进度仍为 0%（若都未完成）

**解决**：这是设计行为，用户需要等待 simulation 完全完成

### Q2: 事件级进度条与表格中的 completed 数字不匹配

**原因**：进度条计算方式：`(completed / total) * 100`，四舍五入可能导致显示差异

**解决**：这是正常的，进度条显示的是百分比取整后的结果

### Q3: progress.json 文件不存在会怎样

**后端处理** (simulation_service.py:741)：
```python
sim["progress"] = 100 if sim.get("status") == "completed" else 0
```
- 如果已完成：进度显示 100%
- 如果未完成：进度显示 0%

### Q4: 如何从 progress.json 获取进度

**progress.json 格式** (各 simulation 目录下)：
```json
{
    "status": "running",
    "percent": 45,
    "message": "已完成 45 步",
    "updated_at": "2025-11-16T10:30:00",
    "batch_id": "case_event_10754"
}
```

后端读取 `percent` 字段并赋值给 `sim.progress`

---

## 性能考虑

### 刷新频率
- **默认间隔**：1000ms (1秒)
- **位置**：`case-simulation-center.html` 的 `monitoringInterval`
- **调整方法**：修改 `setInterval(refreshBatchStatus, 1000)` 中的间隔值

### 优化建议
1. 对于大量 simulation（>100），考虑增加刷新间隔
2. 使用服务器端推送（WebSocket）替代轮询可提高实时性
3. 前端可缓存 simulation 列表，避免重复传输

---

## 隔离性声明

**事件批次仿真进度监控**与**管控方案仿真进度监控**完全隔离：

| 系统 | 位置 | 函数 | 备注 |
|------|------|------|------|
| 事件批次 | `frontend/scenarios/case-simulation-center.html` | `renderSimulationTable()` | 独立实现 |
| 管控方案 | `frontend/control/js/batch_simulation.js` | `renderTaskList()` | 独立实现 |

- ✅ 无交叉引用
- ✅ 独立 DOM 元素
- ✅ 独立 API 端点
- ✅ 互不影响

---

## 更新历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2025-11-16 | 初始实现：两层进度监控 |
| 1.1 | 2025-11-16 | 修复字段名：`progress_percent` → `progress` |

