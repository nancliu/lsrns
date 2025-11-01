# 参数表单数据流文档

**创建日期**: 2025-11-01
**变更ID**: refactor-strategy-parameter-configuration
**目的**: 记录 Step 2 → Step 3 数据传递方式和参数提取逻辑

## 工作流概览

策略创建工作流分为3个步骤:
1. **Step 1**: 选择策略模板 (VSS/DHS/TEC)
2. **Step 2**: 选择路段 (使用 EdgeSelector)
3. **Step 3**: 配置参数 (使用 parameter_form.js)

## Step 1 → Step 2: 模板传递

**数据传递方式**: 通过DOM元素的 `dataset` 属性

**关键代码位置**: `frontend/control/templates.html`

```javascript
// Step 1: 模板选择后设置
const templateCard = document.querySelector('.template-card');
templateCard.dataset.templateId = templateId;
templateCard.dataset.strategyType = strategyType;
```

## Step 2 → Step 3: 路段数据传递

**当前实现**: 通过全局对象 `EdgeSelector.state`

**关键数据结构**:
```javascript
EdgeSelector = {
    state: {
        currentResults: [],      // 查询结果（所有符合条件的路段）
        edgeSelectionSet: Set(), // 用户选中的路段 ID 集合
        isLoading: false,
        cacheTimestamp: null,
        queryFilters: {
            routeCode: null,
            minKm: null,
            maxKm: null,
            minLanes: null
        }
    }
}
```

**数据访问位置**: `frontend/control/js/edge_selector_embedded.js:9`

**Step 2使用示例**:
```javascript
// templates.html:3985-3992
const hasQueryResults = EdgeSelector.state.currentResults &&
                        EdgeSelector.state.currentResults.length > 0;

// 自动查询
EdgeSelector.query().then(() => {
    console.log(`找到 ${EdgeSelector.state.currentResults.length} 条路段`);
});
```

**Step 3读取方式**:
```javascript
// templates.html:2222-2224
const edgeDataCache = (typeof EdgeSelector !== 'undefined' && EdgeSelector.state)
    ? EdgeSelector.state.currentResults
    : [];
```

**问题**:
- ❌ 无明确的sessionStorage/localStorage持久化
- ❌ Step 3中仍显示旧的 `affected_edges` 输入框（需隐藏）
- ❌ 用户刷新页面后数据丢失（EdgeSelector.state 是内存对象）

## Step 3: 参数表单生成

**入口函数**: `generateFormFromTemplate(templateId)` (`parameter_form.js:105`)

**数据流程**:

### 1. 加载模板数据

```javascript
// parameter_form.js:110-116
const response = await fetch(`/api/v1/control/templates/${templateId}`);
const templateDetail = await response.json();
const template = templateDetail.data || templateDetail;
```

**模板结构**:
```javascript
{
    "template_id": "vss_time_based_v2",
    "strategy_type": "VSS",
    "parameters_schema": [
        {
            "parameter_name": "speed_steps",
            "parameter_type": "step_array",
            "display_name": "时间-速度步骤",
            "default_value": [
                {"time_hours": 7, "speed_kmh": 60},
                {"time_hours": 9, "speed_kmh": 80}
            ],
            "required": true,
            "constraints": {
                "min_value": 0,
                "max_value": 120
            }
        }
    ]
}
```

### 2. 渲染参数控件

```javascript
// parameter_form.js:129-145
for (const paramSchema of parametersSchema) {
    const paramControl = renderParameterControl(paramSchema, templateId);
    if (paramControl) {
        formHtml.appendChild(paramControl);
    }

    // [特殊处理] 在 restriction_mode 后插入车型控件
    if (paramSchema.parameter_name === 'restriction_mode') {
        const hasVehicleTypeParams = parametersSchema.some(p =>
            p.parameter_name === 'disallow_vehicle_types' ||
            p.parameter_name === 'allowed_vehicle_types'
        );
        if (hasVehicleTypeParams) {
            const unifiedControl = renderUnifiedVehicleTypeControl(template);
            formHtml.appendChild(unifiedControl);
        }
    }
}
```

### 3. 参数类型处理

**当前支持的参数类型** (`parameter_form.js:2005-2084`):

| 参数类型 | 数据结构 | 渲染方式 | 提取逻辑 |
|---------|---------|---------|---------|
| `enum_array` | `["value1", "value2"]` | 复选框组 | `.enum-checkbox:checked` |
| `step_array` | `[{time_hours, speed_kmh}]` | 表格 + 时间轴 | `.step-row` → `{time_hours, speed_kmh}` |
| `flow_interval_array` | `[{begin_hours, end_hours, vehsPerHour, target_speed}]` | 表格 | `.interval-row` |
| `edge_array` | `["edge1", "edge2"]` | 文本列表 | `.edge-id-input` |
| `array` (time_intervals) | `[{begin_hours, end_hours, status, allowed_vehicle_types}]` | 表格 | `.time-interval-row` |

### 4. 默认值加载（当前问题）

**当前状态**: ❌ **未实现**

```javascript
// parameter_form.js:129-133
for (const paramSchema of parametersSchema) {
    const paramControl = renderParameterControl(paramSchema, templateId);
    // ❌ 没有调用 initializeDefaultValues()
    // ❌ default_value 未被使用
}
```

**问题**:
- 表单打开时是空表格
- `paramSchema.default_value` 未被读取
- 用户需要手动添加每一行

**期望行为**:
```javascript
// 应该添加的逻辑
if (paramSchema.default_value !== null && paramSchema.default_value !== undefined) {
    initializeParameterValue(paramControl, paramSchema.default_value, paramSchema.parameter_type);
}
```

## Step 3: 参数提取与提交

**提取函数**: `extractFormParameters(form)` (`parameter_form.js:2005`)

**提取流程**:

### 1. 遍历所有 form-group

```javascript
const formGroups = form.querySelectorAll(".form-group");

for (const group of formGroups) {
    const paramName = group.dataset.parameterName;
    const paramType = group.dataset.parameterType;

    // 根据 paramType 提取不同格式的值
    let value;
    if (paramType === "enum_array") { ... }
    else if (paramType === "step_array") { ... }
    // ...

    parameters[paramName] = value;
}
```

### 2. 参数类型特定提取逻辑

**step_array 示例**:
```javascript
// parameter_form.js:2025-2039
else if (paramType === "step_array") {
    const tbody = group.querySelector(".steps-tbody");
    if (tbody) {
        const rows = tbody.querySelectorAll(".step-row");
        value = Array.from(rows).map((row) => ({
            time_hours: parseFloat(row.querySelector(".step-time").value),
            speed_kmh: parseFloat(row.querySelector(".step-speed").value)
        }));
    }
}
```

**flow_interval_array 示例**:
```javascript
// parameter_form.js:2040-2050
else if (paramType === "flow_interval_array") {
    const tbody = group.querySelector(".intervals-tbody");
    if (tbody) {
        value = Array.from(tbody.querySelectorAll(".interval-row")).map((row) => ({
            begin_hours: parseFloat(row.querySelector(".interval-begin").value),
            end_hours: parseFloat(row.querySelector(".interval-end").value),
            vehsPerHour: parseFloat(row.querySelector(".interval-flow").value),
            target_speed: parseFloat(row.querySelector(".interval-speed").value)
        }));
    }
}
```

**time_intervals (DHS/TEC) 示例**:
```javascript
// parameter_form.js:2062-2072
const tbody = group.querySelector(".time-intervals-tbody");
if (tbody) {
    value = Array.from(tbody.querySelectorAll(".time-interval-row")).map((row) => ({
        begin_hours: parseFloat(row.querySelector(".interval-begin").value),
        end_hours: parseFloat(row.querySelector(".interval-end").value),
        status: row.querySelector(".interval-status").value,
        allowed_vehicle_types: row.querySelector(".interval-vehicles").value
            .split(",")
            .map((v) => v.trim())
            .filter((v) => v)
    }));
}
```

### 3. 路段数据提取（当前问题）

**问题**: 路段数据提取逻辑混乱

**当前实现**:
```javascript
// parameter_form.js:2051-2058
else if (paramType === "edge_array") {
    const edgesList = group.querySelector(".edges-list");
    if (edgesList) {
        value = Array.from(edgesList.querySelectorAll(".edge-id-input"))
            .map((input) => input.value)
            .filter((v) => v.trim());
    }
}
```

**实际数据来源**: 应该从 `EdgeSelector.state.edgeSelectionSet` 获取

**期望实现**:
```javascript
// Step 3 应该跳过 affected_edges 输入框渲染
if (paramName === 'affected_edges' || paramName === 'affected_segments') {
    continue; // 不渲染输入框
}

// 提交时从 EdgeSelector 获取
const selectedEdges = Array.from(EdgeSelector.state.edgeSelectionSet || []);
parameters['affected_edges'] = selectedEdges;
```

## 当前问题总结

### 1. 默认值加载缺失 ❌

**问题**: 表单打开时为空表格
**影响**: 用户体验差，需手动添加每行数据
**修复**: 创建 `initializeDefaultValues()` 函数

### 2. 路段数据来源混乱 ❌

**问题**: Step 2 和 Step 3 都有路段输入框
**影响**: 用户困惑于使用哪个来源
**修复**: Step 3 显示只读列表，从 EdgeSelector 获取数据

### 3. 车型配置位置错误 ❌

**问题**: 车型混在 DHS/TEC 时间区间表中
**影响**: 车型应是全局配置，不应按区间配置
**修复**: 创建独立的车型配置区域

### 4. 时间语义不明确 ❌

**问题**: VSS (时刻) 和 DHS/TEC (时段) UI 标签相同
**影响**: 用户不清楚填写时刻还是时段
**修复**: 更新列标签和 Hint

### 5. 代码重复严重 ❌

**问题**: 4个时间轴更新函数重复，3个行添加函数重复
**影响**: 维护困难，代码超过2258行
**修复**: 合并为统一的参数化函数

## 重构方向

### Phase 2: 代码重构（无功能变更）
- 合并时间轴更新函数
- 合并行添加函数
- 提取验证函数
- 添加代码分区注释

### Phase 4: 模板默认值加载
- 创建 `initializeDefaultValues()` 函数
- 在 `generateFormFromTemplate()` 中调用
- 支持所有参数类型的默认值初始化

### Phase 7: 路段来源统一
- 隐藏 Step 3 的 `affected_edges` 输入框
- 显示 Step 2 路段只读列表
- 从 `EdgeSelector.state.edgeSelectionSet` 提取路段数据

## 数据流图

```
┌─────────────────┐
│   Step 1:       │
│  选择模板        │
│  (template_id)  │
└────────┬────────┘
         │ dataset.templateId
         ▼
┌─────────────────┐
│   Step 2:       │
│  选择路段        │
│  (EdgeSelector) │
└────────┬────────┘
         │ EdgeSelector.state.edgeSelectionSet
         │ EdgeSelector.state.currentResults
         ▼
┌─────────────────┐
│   Step 3:       │
│  配置参数        │
└────────┬────────┘
         │ extractFormParameters()
         ▼
┌─────────────────┐
│  提交策略实例    │
│  POST /api/...  │
└─────────────────┘
```

## 相关文件

- `frontend/control/templates.html` - 主工作流页面
- `frontend/control/js/parameter_form.js` - 参数表单核心逻辑 (2258行)
- `frontend/control/js/edge_selector_embedded.js` - 路段选择器
- `frontend/control/js/timeline_visualizer.js` - 时间轴可视化

## 下一步

1. ✅ 已完成: E2E 测试基线建立
2. ✅ 已完成: CSS 变量扩展
3. ✅ 已完成: 数据流文档化
4. ⏳ 下一步: 开始 Phase 2 代码重构（合并时间轴更新函数）
