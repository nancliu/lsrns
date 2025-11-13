# 场景浏览页面 - 创建案例与分析按键设计

**文档日期**: 2025-11-13
**版本**: v1.0
**状态**: 设计文档

---

## 场景浏览页面的两个操作路径

在 `scenario_browser.html` 中，每个场景行应该有两个主要操作按键：

```
┌─────────────────────────────────────────────────────────────┐
│ 场景ID | 事件类型 | 管控策略 | 操作                          │
├─────────────────────────────────────────────────────────────┤
│ scen_xx_vss | 事故 | VSS | [创建案例] [快速分析]           │
└─────────────────────────────────────────────────────────────┘
```

---

## 两个按键的详细设计

### 1. [创建案例] 按键

**功能**: 创建一个案例，用户后续可以在案例管理页面编排和执行仿真

**工作流**:
```
用户点击 [创建案例]
  ↓
弹出模态框:
  • 场景信息 (只读): scenario_id, event_type, control_strategy
  • 仿真参数 (可选):
    - simulation_duration_hours (1-24小时)
    - random_seed (可选)
    - output_config (edgedata, tripinfo, vehroute)
  ↓
用户填写参数，提交
  ↓
后端: POST /api/v1/case/create-from-scenario
  {
    "scenario_id": "scenario_12547_vss",
    "simulation_duration_hours": 2.5,
    "random_seed": 42,
    "output_config": { "generate_edgedata": true, ... }
  }
  ↓
后端返回: case_id
  ↓
前端跳转: case-simulation-center.html?case_id={case_id}
  ↓
用户进入案例管理页面，可以:
  • 查看案例信息
  • 查看已生成的仿真列表
  • 启动批量仿真
  • 查看仿真进度
  • 启动分析
  • 查看分析结果
```

**特点**:
- ✅ 是"创建"操作，需要用户参与
- ✅ 支持参数配置
- ✅ 一个场景可以创建多个案例 (参数不同)
- ✅ 适合需要精细控制的用户

---

### 2. [快速分析] 按键

**功能**: 一键启动场景的完整仿真和分析流程，无需进入案例管理页面

**工作流**:
```
用户点击 [快速分析]
  ↓
弹出模态框:
  • 场景信息 (只读): scenario_id, event_type, control_strategy
  • 案例配置:
    - 案例名称 (自动生成或用户输入)
    - 仿真参数 (duration, seed, output_config)
  • 分析重点 (可选):
    - [ ] EdgeData 分析 (推荐, 默认勾选)
    - [ ] TripInfo 分析
  • 对标场景:
    - [ ] 与无管控场景对比 (默认勾选)
  ↓
用户点击 [启动仿真分析]
  ↓
后端流程:
  1. 创建案例 (call POST /api/v1/case/create-from-scenario)
  2. 自动创建仿真
  3. 自动启动仿真 (call POST /api/v1/simulation/batch-start)
  4. 当仿真完成后，自动启动分析 (call POST /api/v1/analysis/run-batch)
  ↓
前端展示:
  • 显示进度: "正在创建案例..." → "仿真运行中..." → "分析进行中..." → "结果已就绪"
  • 完成后自动跳转到 analysis_viewer.html?batch_id={analysis_batch_id}
  ↓
用户直接看到分析结果，无需多步操作
```

**特点**:
- ✅ 是"一键启动"操作，自动完成所有步骤
- ✅ 适合快速了解场景影响的用户
- ✅ 后台自动串联: 创建 → 仿真 → 分析
- ✅ 减少用户操作步骤

---

## 两个按键的关系与区别

| 维度 | [创建案例] | [快速分析] |
|------|----------|----------|
| 用途 | 创建案例供后续编排 | 直接获取分析结果 |
| 操作复杂度 | 中等 (需配置参数) | 低 (自动完成) |
| 适用场景 | 需要细致控制/多次仿真 | 快速评估影响 |
| 流程长度 | 短 (仅创建案例) | 长 (创建+仿真+分析) |
| 用户参与度 | 高 (需选择参数) | 低 (主要是监控) |
| 跳转目标 | case-simulation-center.html | analysis_viewer.html |

---

## 场景浏览页面的表格设计

### 表格结构
```html
<table class="scenario-table">
  <thead>
    <tr>
      <th>场景ID</th>
      <th>事件ID</th>
      <th>事件类型</th>
      <th>管控策略</th>
      <th>已创建案例</th>
      <th>操作</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>scenario_12547_vss</td>
      <td>12547</td>
      <td>事故</td>
      <td>VSS</td>
      <td>3</td>
      <td>
        <button class="btn-small" onclick="openCreateModal(scenarioId)">
          📋 创建案例
        </button>
        <button class="btn-small" onclick="openAnalysisModal(scenarioId)">
          🚀 快速分析
        </button>
      </td>
    </tr>
  </tbody>
</table>
```

---

## 模态框设计

### [创建案例] 模态框
```
┌────────────────────────────────┐
│  📋 快速创建案例               [×]
├────────────────────────────────┤
│ 场景ID      [scenario_12547_vss] (只读)
│ 案例名称    [                  ] (可选)
│ 事件类型    [事故            ] (只读)
│ 管控策略    [VSS             ] (只读)
│ 案例描述    [                  ] (可选, 多行)
├────────────────────────────────┤
│                  [取消] [创建案例]
└────────────────────────────────┘
```

**新增字段** (vs 现有的快速创建模态框):
- 仿真时长 (duration_hours) - 范围: 1-24
- 随机种子 (random_seed) - 可选
- 输出配置 (output_config) - EdgeData/TripInfo/VehRoute 复选框

### [快速分析] 模态框 (已在代码中)
```
┌────────────────────────────────┐
│  📊 仿真分析配置               [×]
├────────────────────────────────┤
│ 场景基本信息:
│   场景ID      [scenario_12547_vss] (只读)
│   事件类型    [事故            ] (只读)
│   管控策略    [VSS             ] (只读)
│
│ 仿真参数配置:
│   案例名称    [                  ]
│   对标场景    [✓] 与无管控场景对比
│
│ 分析重点:
│   [✓] 道路段分析 (EdgeData) - 推荐
│   [ ] 行程分析   (TripInfo)
│
│ 说明: 需要场景已创建对应的仿真案例
├────────────────────────────────┤
│          [取消] [🚀 启动仿真分析]
└────────────────────────────────┘
```

---

## 工作流集成

### 场景 1: 用户选择 [创建案例]
```
① scenario_browser.html
   ↓ [创建案例]
   ↓ POST /api/v1/case/create-from-scenario
   ↓ 获得 case_id
   ↓ 跳转

② case-simulation-center.html?case_id={case_id}
   ↓ (Tab 1: 案例列表 - 显示新创建的案例)
   ↓ (Tab 2: 仿真监控 - 可查看/启动仿真)
   ↓ [批量仿真]
   ↓ POST /api/v1/simulation/batch-start
   ↓ 获得 batch_id, 自动启动分析
   ↓ 轮询仿真进度

③ 分析完成时自动跳转

④ analysis_viewer.html?batch_id={batch_id}
   ↓ 显示分析进度 → 分析结果
```

### 场景 2: 用户选择 [快速分析]
```
① scenario_browser.html
   ↓ [快速分析]
   ↓ 后端自动流程:
   │  1. POST /api/v1/case/create-from-scenario
   │  2. 自动创建仿真
   │  3. POST /api/v1/simulation/batch-start
   │  4. 当仿真完成后，自动 POST /api/v1/analysis/run-batch
   │
   ↓ 前端显示进度页面

② analysis_viewer.html?batch_id={batch_id}
   ↓ 显示分析结果
```

**关键差异**:
- [创建案例]: 用户控制 = 多步操作
- [快速分析]: 系统自动 = 单步启动

---

## 后端实现要点

### Task 2.8 的改进: 支持"快速分析"流程

在 POST /api/v1/case/create-from-scenario 中添加参数:
```python
class CreateCaseFromScenarioRequest(BaseModel):
    scenario_id: str

    # 仿真参数
    simulation_duration_hours: Optional[float] = None
    random_seed: Optional[int] = None
    output_config: Optional[dict] = None

    # 新增: 快速分析标志
    auto_create_simulation: bool = False  # 自动创建仿真
    auto_start_simulation: bool = False   # 自动启动仿真
    auto_run_analysis: bool = False       # 自动启动分析

    # 分析配置
    analysis_focus: Optional[List[str]] = None  # ["edgedata", "tripinfo"]
    baseline_scenario_id: Optional[str] = None
    comparison_enabled: bool = True       # 与无管控场景对比
```

### 后端流程
```python
@router.post("/case/create-from-scenario")
async def create_case_from_scenario(request: CreateCaseFromScenarioRequest):
    # 1. 创建案例
    case = case_service.create_case_from_scenario(request.scenario_id, ...)

    if request.auto_create_simulation:
        # 2. 自动创建仿真
        simulation = simulation_service.create_simulation(case_id, ...)

        if request.auto_start_simulation:
            # 3. 自动启动仿真
            batch_id = await orchestrator.batch_start_simulations(
                simulation_ids=[simulation.id],
                auto_run_analysis=request.auto_run_analysis
            )

            return {
                "case_id": case.id,
                "batch_id": batch_id,
                "auto_flow": True  # 标记: 自动流程进行中
            }

    return {
        "case_id": case.id,
        "auto_flow": False
    }
```

---

## 前端实现要点

### scenario_browser.js 的改进

```javascript
// 打开创建案例模态框
function openCreateModal(scenarioId) {
    // 1. 加载场景信息
    const scenario = getScenarioById(scenarioId);

    // 2. 填充模态框
    document.getElementById('selectedScenarioId').value = scenario.scenario_id;
    document.getElementById('selectedEventType').value = scenario.event_type;
    document.getElementById('selectedControlStrategy').value = scenario.control_strategy;

    // 3. 显示模态框
    document.getElementById('quickCreateModal').classList.add('show');
}

// 提交创建案例
async function submitQuickCreate() {
    const data = {
        scenario_id: document.getElementById('selectedScenarioId').value,
        simulation_duration_hours: parseFloat(document.getElementById('duration').value) || null,
        random_seed: document.getElementById('randomSeed').value ? parseInt(...) : null,
        output_config: {
            generate_edgedata: document.getElementById('genEdgeData').checked,
            generate_tripinfo: document.getElementById('genTripInfo').checked,
            generate_vehroute: document.getElementById('genVehRoute').checked
        }
    };

    try {
        const response = await api.request('/case/create-from-scenario', {
            method: 'POST',
            body: JSON.stringify(data)
        });

        // 跳转到案例管理页面
        window.location.href = `case-simulation-center.html?case_id=${response.data.case_id}`;
    } catch (error) {
        alert('创建案例失败: ' + error.message);
    }
}

// 打开快速分析模态框
function openAnalysisModal(scenarioId) {
    // 1. 加载场景信息
    const scenario = getScenarioById(scenarioId);

    // 2. 填充模态框
    document.getElementById('analysisScenarioId').value = scenario.scenario_id;
    document.getElementById('analysisEventType').value = scenario.event_type;
    document.getElementById('analysisControlStrategy').value = scenario.control_strategy;

    // 3. 显示模态框
    document.getElementById('analysisModal').classList.add('show');
}

// 提交快速分析
async function submitAnalysis() {
    const data = {
        scenario_id: document.getElementById('analysisScenarioId').value,
        simulation_duration_hours: parseFloat(document.getElementById('duration').value) || null,
        random_seed: document.getElementById('randomSeed').value ? parseInt(...) : null,
        output_config: { generate_edgedata: true, generate_tripinfo: true },

        // 快速分析标志
        auto_create_simulation: true,
        auto_start_simulation: true,
        auto_run_analysis: true,

        // 分析配置
        analysis_focus: [
            'edgedata',
            document.getElementById('analyzeTripInfo').checked ? 'tripinfo' : null
        ].filter(Boolean),
        comparison_enabled: document.getElementById('compareNoControl').checked
    };

    try {
        // 显示进度页面
        showProgressPage(scenarioId);

        // 启动快速分析流程
        const response = await api.request('/case/create-from-scenario', {
            method: 'POST',
            body: JSON.stringify(data)
        });

        // 保存 batch_id
        sessionStorage.setItem('current_batch_id', response.data.batch_id);

        // 跳转到分析结果页面
        window.location.href = `analysis_viewer.html?batch_id=${response.data.batch_id}`;
    } catch (error) {
        alert('启动分析失败: ' + error.message);
    }
}

// 显示进度页面 (过渡页面)
function showProgressPage(scenarioId) {
    const modal = document.createElement('div');
    modal.className = 'progress-modal';
    modal.innerHTML = `
        <div class="progress-content">
            <h2>🚀 启动仿真分析</h2>
            <div class="progress-steps">
                <div class="step active">1. 创建案例...</div>
                <div class="step">2. 运行仿真...</div>
                <div class="step">3. 执行分析...</div>
            </div>
            <p class="progress-message">正在为您准备分析，请稍候...</p>
        </div>
    `;
    document.body.appendChild(modal);
}
```

---

## 完整的用户交互流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                    用户在场景浏览页面                             │
├─────────────────────────────────────────────────────────────────┤
│
│ 看到场景表格，每行有两个按键: [创建案例] 和 [快速分析]
│
├─────────────────────────────────────────────────────────────────┤
│ 路径 A: 用户选择 [创建案例]
│
│   ① 弹出模态框
│      - 显示场景信息 (只读)
│      - 用户填写: 仿真时长、随机种子、输出配置
│
│   ② 提交表单
│      - POST /api/v1/case/create-from-scenario
│      - 响应: case_id
│
│   ③ 跳转到案例管理页面
│      - case-simulation-center.html?case_id={case_id}
│      - 用户可查看案例、启动仿真、查看进度、启动分析
│
├─────────────────────────────────────────────────────────────────┤
│ 路径 B: 用户选择 [快速分析]
│
│   ① 弹出模态框
│      - 显示场景信息 (只读)
│      - 用户填写: 仿真参数、分析重点
│
│   ② 提交表单
│      - POST /api/v1/case/create-from-scenario (with auto_* flags)
│      - 响应: case_id + batch_id
│
│   ③ 显示进度过渡页面
│      - 正在创建案例...
│      - 正在运行仿真...
│      - 正在执行分析...
│
│   ④ 自动跳转到分析结果页面
│      - analysis_viewer.html?batch_id={batch_id}
│      - 用户直接看到分析结果
│
└─────────────────────────────────────────────────────────────────┘
```

---

## 数据库/元数据考虑

### Case Metadata 中的新字段

```json
{
  "case_id": "case_20251113_120000",
  "source_scenario": "scenario_12547_vss",
  "creation_method": "direct" | "quick_analysis",  // NEW
  "quick_analysis_batch_id": "analysis_batch_20251113_120000"  // NEW (if from quick_analysis)
}
```

**目的**:
- 区分创建方式 (直接创建 vs 快速分析)
- 快速关联对应的分析批次

---

## 总结

**两个按键的核心区别**:
1. **[创建案例]** = 创建案例供后续操作 (多步工作流)
2. **[快速分析]** = 直接启动完整流程 (单步启动)

**实现策略**:
- 前端: 两个模态框 + 两个提交函数
- 后端: 一个 API 端点 (参数决定流程)
- 工作流: 通过 URL 参数和自动跳转连接

**关键检查点**:
- [ ] 模态框表单验证
- [ ] API 参数正确传递
- [ ] 自动流程链正确串联
- [ ] 错误处理和重试机制
- [ ] 过渡页面用户体验

---

**设计完成。准备实现 Task 2.8-2.13。**
