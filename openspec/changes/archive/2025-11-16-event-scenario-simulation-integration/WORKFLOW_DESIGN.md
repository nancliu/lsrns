# 事件场景仿真工作流设计文档

**日期**: 2025-11-13
**状态**: 设计阶段
**版本**: v1.0

---

## 工作流概览

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 2: 事件场景仿真集成工作流                                  │
└─────────────────────────────────────────────────────────────────┘

用户工作流:

① 仿真推演场景集 (scenario_browser.html)
   ↓
   ├─ [创建案例按键] ──→ 触发前端模态框
   │                    ↓
   │               场景选择 + 参数配置
   │                    ↓
   │               调用 POST /api/v1/case/create-from-scenario
   │                    ↓
   └────────────────→ 案例创建成功 (返回 case_id)

② 场景案例管理 (case-simulation-center.html)
   ├─ Tab 1: 案例列表
   │   ├─ 显示从场景生成的案例 (filter by source_scenario)
   │   └─ [批量仿真]按键 ──→ 启动仿真批处理
   │
   ├─ Tab 2: 仿真监控
   │   ├─ 显示运行中的仿真
   │   ├─ 实时进度条
   │   └─ 自动刷新状态 (polling)
   │
   └─ Tab 3: 批次管理
       ├─ 显示已完成的批次
       └─ 可查看批次详情

③ 影响分析 (analysis_viewer.html)
   ├─ 从案例/仿真自动启动分析
   ├─ 显示分析进度
   └─ 展示分析结果 (复用批量仿真分析功能)
```

---

## 页面详细设计

### 1. 仿真推演场景集 (scenario_browser.html)

**核心功能**:
- 展示449个事件场景
- 二维分类筛选 (事件类型 × 管控策略)
- 创建案例入口

**创建案例的工作流逻辑**:

```javascript
// 场景浏览页面
function createCaseFromScenario(scenarioId) {
    // 1. 打开模态框
    showCreateCaseModal({
        scenario_id: scenarioId,
        event_type: scenario.event_type,
        control_strategy: scenario.control_strategy,
        // 其他场景信息...
    });

    // 2. 用户填写案例参数
    // - 仿真时长 (可选,默认场景配置)
    // - 随机种子 (可选,默认null)
    // - 输出配置 (可选,默认edgedata+summary)

    // 3. 提交创建
    async function submitCreateCase() {
        const payload = {
            scenario_id: document.getElementById('scenarioId').value,
            simulation_duration_hours: parseFloat(document.getElementById('duration').value) || null,
            random_seed: document.getElementById('randomSeed').value ? parseInt(...) : null,
            output_config: { ... }
        };

        const response = await api.request('/case/create-from-scenario', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        // 4. 成功后跳转到案例管理页面
        if (response.success) {
            window.location.href = `case-simulation-center.html?case_id=${response.data.case_id}`;
        }
    }
}
```

**UI改进**:
- 在场景表格中添加 [创建案例] 按键
- 支持批量选择 + 批量创建
- 显示已创建案例的数量

---

### 2. 场景案例管理 (case-simulation-center.html)

**核心功能**: 统一的案例和仿真管理中心

**Tab 设计**:

#### Tab 1: 案例列表
```
┌─────────────────────────────────────────────────────────────┐
│ 场景案例管理 > 案例列表                                       │
├─────────────────────────────────────────────────────────────┤
│ 筛选: [所有案例] [仿真中] [已完成] [失败]                     │
│       场景类型: [全部] [事故] [天气]... 搜索框                │
├─────────────────────────────────────────────────────────────┤
│ 统计: 总计: 150  |  仿真中: 5  |  已完成: 140  |  失败: 5   │
├─────────────────────────────────────────────────────────────┤
│ 案例ID | 源场景 | 状态 | 仿真数 | 操作                       │
├─────────────────────────────────────────────────────────────┤
│ case_1 | scen_xx_vss | ✓完成 | 3/3 | [查看] [重新仿真]       │
│ case_2 | scen_yy_dhs | ⚙运行 | 2/5 | [查看] [取消]          │
│ ...                                                          │
└─────────────────────────────────────────────────────────────┘

操作:
- 选择案例 → 显示该案例的仿真列表
- [批量仿真] 按键:
  ├─ 批量启动所有待仿真的simulation
  └─ 跳转到"仿真监控"Tab

- 筛选功能:
  ├─ 按源场景ID 筛选
  ├─ 按状态 筛选
  └─ 搜索 case_id/scenario_id
```

**场景筛选设计**:
```python
# 后端新增API: GET /api/v1/case/list-by-scenario
def list_cases_by_scenario(scenario_id: str):
    """获取从特定场景生成的所有案例"""
    # 查询: metadata.source_scenario_id == scenario_id
    # 返回: cases 列表
    return {
        "scenario_id": scenario_id,
        "cases": [
            {
                "case_id": "case_xxx",
                "case_name": "...",
                "source_scenario": {...},
                "status": "completed",
                "simulations": [...]
            }
        ]
    }
```

#### Tab 2: 仿真监控
```
┌─────────────────────────────────────────────────────────────┐
│ 场景案例管理 > 仿真监控                                       │
├─────────────────────────────────────────────────────────────┤
│ 批次进度:  总计: 150  完成: 85  运行: 5  失败: 3  等待: 57  │
│ 进度条: [=====>          ] 57%  预计完成: 2小时              │
├─────────────────────────────────────────────────────────────┤
│ 仿真ID | 案例 | 状态 | 进度 | 用时 | 预计完成 | 操作          │
├─────────────────────────────────────────────────────────────┤
│ sim_1  | case_1 | ✓ | 100% | 2h 15m | -- | [查看结果]        │
│ sim_2  | case_2 | ⚙ | 45%  | 1h 20m | 1h | [查看日志]        │
│ sim_3  | case_3 | ⏳ | 0%   | -- | -- | --                 │
└─────────────────────────────────────────────────────────────┘

实现细节:
- 使用 SimulationMonitor 组件
- Polling 间隔: 5秒 (已完成后停止)
- 显示 SUMO 日志的最后500行
```

#### Tab 3: 批次管理
```
┌─────────────────────────────────────────────────────────────┐
│ 场景案例管理 > 批次管理                                       │
├─────────────────────────────────────────────────────────────┤
│ 已完成的批次列表                                             │
├─────────────────────────────────────────────────────────────┤
│ 批次ID | 时间 | 案例数 | 仿真数 | 成功率 | 操作              │
├─────────────────────────────────────────────────────────────┤
│ batch_001 | 2025-11-12 10:00 | 30 | 150 | 100% | [分析] [导出]│
│ batch_002 | 2025-11-11 14:30 | 25 | 125 | 95%  | [分析] [导出]│
└─────────────────────────────────────────────────────────────┘

按键关联:
- [分析] ──→ 跳转到 analysis_viewer.html?batch_id=batch_001
```

**页面间导航**:
```javascript
// 从 scenario_browser.html 来
if (new URLSearchParams(window.location.search).has('case_id')) {
    // 自动切换到"仿真监控" Tab 并监听该案例的仿真
}

// 批量仿真流程
async function batchStartSimulations() {
    // 1. 收集所有待仿真的 simulation_ids
    // 2. 调用 POST /api/v1/simulation/batch-start
    // 3. 获得 batch_id
    // 4. 切换到"仿真监控" Tab
    // 5. 开始 polling /api/v1/simulation/batch-status/{batch_id}

    const response = await api.request('/simulation/batch-start', {
        method: 'POST',
        body: JSON.stringify({
            simulation_ids: selectedSimIds,
            parallel_workers: 4,
            auto_run_analysis: true
        })
    });

    // 保存 batch_id 到 sessionStorage
    sessionStorage.setItem('current_batch_id', response.data.batch_id);

    // 切换 Tab
    document.querySelector('[data-tab="monitoring"]').click();
}
```

---

### 3. 影响分析 (analysis_viewer.html)

**核心功能**: 展示分析结果，复用批量仿真分析功能

**设计原则**: **不创建新的分析逻辑，复用 shared/analysis_tools/batch_result_analyzer.py**

```javascript
// analysis_viewer.html 的工作流

// 1. 获取 batch_id 或 case_id
const batchId = new URLSearchParams(window.location.search).get('batch_id');
const caseId = new URLSearchParams(window.location.search).get('case_id');

// 2. 自动启动分析 (如果还未分析)
async function startAnalysisIfNeeded() {
    // 检查是否已有分析结果
    const hasAnalysis = await api.request(`/analysis/batch-progress/${batchId}`);

    if (!hasAnalysis.data) {
        // 启动新分析
        const response = await api.request('/analysis/run-batch', {
            method: 'POST',
            body: JSON.stringify({
                simulation_ids: simIds,
                case_id: caseId,
                baseline_scenario_id: baselineScenarioId,
                analysis_focus: ['edgedata', 'tripinfo', 'performance'],
                parallel_workers: 4
            })
        });

        batchId = response.data.batch_id;
    }
}

// 3. 实时显示分析进度
async function monitorAnalysisProgress() {
    const dashboard = new AnalysisResultsDashboard('analysisContainer', api);

    while (true) {
        const progress = await api.request(`/analysis/batch-progress/${batchId}`);

        dashboard.updateProgress({
            total: progress.data.total_tasks,
            completed: progress.data.completed,
            failed: progress.data.failed,
            current: progress.data.current_tasks[0]
        });

        if (progress.data.completed === progress.data.total_tasks) {
            // 分析完成，加载结果
            await loadAnalysisResults();
            break;
        }

        await delay(5000); // 5秒刷新
    }
}

// 4. 显示分析结果
async function loadAnalysisResults() {
    const results = await api.request(`/analysis/results/${batchId}`);

    const dashboard = new AnalysisResultsDashboard('analysisContainer', api);
    dashboard.render({
        edgedata: results.data.edgedata,
        tripinfo: results.data.tripinfo,
        performance: results.data.performance,
        comparison: results.data.comparison
    });
}
```

**UI 结构**:
```
┌──────────────────────────────────────────────────┐
│ 分析进度 (若正在进行)                              │
├──────────────────────────────────────────────────┤
│ [========>     ] 65% (104/160 任务)               │
│ 当前: sim_123 EdgeData 分析中 (进度: 72%)         │
│ 预计完成: 2025-11-13 16:45:00                    │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ 分析结果 Tab (分析完成后显示)                     │
├──────────────────────────────────────────────────┤
│ [概览] [路段分析] [对比分析] [详细指标] [导出]      │
│                                                 │
│ 概览标签页:                                      │
│ ┌─────────────────────────────────────────────┐ │
│ │ 总车辆数: 8,934                              │ │
│ │ 平均行程时间: 245.6 分钟                      │ │
│ │ 完成率: 98.7%                                │ │
│ │ 平均速度: 42.3 km/h                          │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ 路段分析:                                       │
│ ┌─────────────────────────────────────────────┐ │
│ │ [路段热力图] - 按平均速度着色                  │ │
│ │ 最拥堵路段: Edge_5 (平均25km/h)              │ │
│ │ 最畅通路段: Edge_120 (平均85km/h)            │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ 对比分析:                                       │
│ ┌─────────────────────────────────────────────┐ │
│ │ 指标        | 基准   | 事件无控  | 事件+控制  │ │
│ │ 平均速度    | 45 km/h | 25 km/h | 52 km/h ↑ │ │
│ │ 行程时间    | 200 min | 320 min | 185 min ↓ │ │
│ │ 拥堵指数    | 30%    | 75%    | 15% ↓↓     │ │
│ └─────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

**复用分析功能**:
```python
# 后端: AnalysisOrchestrationService 已提供
# 前端: AnalysisResultsDashboard 组件已提供
#
# analysis_viewer.html 只需:
# 1. 调用 /analysis/run-batch (启动分析)
# 2. 轮询 /analysis/batch-progress/{batch_id} (监听进度)
# 3. 调用 /analysis/results/{batch_id} (获取结果)
# 4. 使用 AnalysisResultsDashboard 渲染结果
```

---

## 数据流与API调用

### 场景浏览 → 案例管理 → 分析

```
┌─────────────────────────────┐
│ scenario_browser.html       │
│ [创建案例] ──────┐          │
└─────────────────┼──────────┘
                  │
                  ▼
          POST /api/v1/case/create-from-scenario
          {
              scenario_id: "scenario_12547_vss",
              simulation_duration_hours: 2.5,
              output_config: {...}
          }
                  │
                  ▼
┌─────────────────────────────┐
│ case-simulation-center.html │ ◄─ 自动跳转 + case_id
│ Tab 1: 案例列表              │
│ [批量仿真] ────┐            │
└─────────────────┼───────────┘
                  │
                  ▼
          POST /api/v1/simulation/batch-start
          {
              simulation_ids: [...],
              parallel_workers: 4,
              auto_run_analysis: true
          }
          返回: batch_id
                  │
                  ▼
│ Tab 2: 仿真监控              │
│ 轮询 batch-status          │
└─────────────────┬───────────┘
                  │ (仿真完成 + auto_run_analysis=true)
                  ▼
┌─────────────────────────────┐
│ analysis_viewer.html        │ ◄─ batch_id 从 sessionStorage
│ 分析进度 + 结果              │
│ 轮询 batch-progress        │
└─────────────────────────────┘
```

### 新增 API 端点

**GET /api/v1/case/list** (改进现有)
```json
Request:
  {
    "status": "completed|running|all",
    "source_scenario_id": "scenario_12547_vss" (可选)
  }

Response:
  {
    "cases": [
      {
        "case_id": "case_20251112_100000",
        "case_name": "...",
        "source_scenario": {
          "scenario_id": "scenario_12547_vss",
          "event_type": "01_accident"
        },
        "status": "completed",
        "created_at": "2025-11-12T10:00:00",
        "simulations_count": 5
      }
    ]
  }
```

**GET /api/v1/case/list-by-scenario?scenario_id=xxx**
```json
Response:
  {
    "scenario_id": "scenario_12547_vss",
    "cases": [
      {
        "case_id": "...",
        "simulations": [...]
      }
    ]
  }
```

**POST /api/v1/simulation/batch-start** (已存在)
```json
Request:
  {
    "simulation_ids": ["sim_1", "sim_2", ...],
    "parallel_workers": 4,
    "auto_run_analysis": true
  }

Response:
  {
    "batch_id": "batch_20251112_100000",
    "simulation_ids": [...],
    "total": 10
  }
```

---

## 实现优先级与顺序

### Phase 1: 核心功能 (第1周)
1. ✅ 实现 `scenario_browser.html` 的创建案例模态框和按键
2. ✅ 实现 `case-simulation-center.html` 的三个 Tab
3. ✅ 实现场景筛选逻辑 (Tab 1)
4. ✅ 集成 SimulationMonitor 组件 (Tab 2)

### Phase 2: 工作流连接 (第2周)
5. ✅ 实现页面间导航 (URL 参数传递)
6. ✅ 实现批量仿真启动和进度监控
7. ✅ 实现分析自动启动 (auto_run_analysis=true)
8. ✅ 实现分析结果展示

### Phase 3: 优化和测试 (第3周)
9. ⏳ 性能优化 (reduce polling frequency)
10. ⏳ 错误处理和重试逻辑
11. ⏳ 端到端测试

---

## 设计决策

### Q1: 创建案例在哪个页面?
**决策**: 在 scenario_browser.html 中
- **理由**: 用户需要先选择场景才能创建案例，与场景浏览流程一致
- **实现**: 在场景表格中添加 [创建案例] 按键，弹出模态框

### Q2: 案例管理和仿真监控如何分离?
**决策**: 使用 Tab 设计
- **理由**: 同一个页面避免切换成本，Tab 逻辑清晰
- **实现**:
  - Tab 1: 案例列表 (静态，支持筛选)
  - Tab 2: 仿真监控 (动态，实时更新)
  - Tab 3: 批次管理 (历史记录)

### Q3: 场景筛选如何实现?
**决策**: 后端新增 API 端点 + 前端缓存
- **理由**: 减少前端复杂性，利用后端元数据索引
- **实现**: GET /api/v1/case/list-by-scenario?scenario_id=xxx

### Q4: 分析如何自动启动?
**决策**: auto_run_analysis=true 参数
- **理由**: 减少用户操作，自动化工作流
- **实现**: SimulationOrchestrator 在所有仿真完成后自动启动分析

### Q5: 分析结果如何复用批量仿真分析?
**决策**: AnalysisOrchestrationService 作为适配器
- **理由**: 不修改现有分析服务，只创建适配层
- **实现**: 前端调用 /analysis/run-batch 和 /analysis/results/{batch_id}

---

## 技术栈

### 后端
- FastAPI (路由)
- SimulationOrchestrator (编排)
- AnalysisOrchestrationService (适配器)
- Pydantic (数据验证)

### 前端
- Vanilla JavaScript (ES6+)
- APIClient (API 调用)
- SimulationMonitor 组件 (进度监控)
- AnalysisResultsDashboard 组件 (结果展示)
- SessionStorage (跨页面数据传递)

---

## 完成清单

- [ ] scenario_browser.html: 创建案例模态框和按键
- [ ] case-simulation-center.html: 三个 Tab 实现
- [ ] 场景筛选 API 端点 (GET /api/v1/case/list-by-scenario)
- [ ] 案例列表 API 改进 (支持 source_scenario_id 筛选)
- [ ] 批量仿真启动和监控
- [ ] 分析自动启动和结果展示
- [ ] 页面间导航 (URL 参数)
- [ ] 错误处理和日志
- [ ] 端到端测试
- [ ] 用户文档

---

**设计文档完成。准备进入实现阶段。**
