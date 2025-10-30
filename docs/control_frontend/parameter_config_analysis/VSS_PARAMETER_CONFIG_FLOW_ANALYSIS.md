# VSS 参数配置流程完整追踪分析

## 📋 执行摘要

通过追踪 VSS（可变限速）策略的完整参数配置流程，确认了**时间轴可视化器的正确性**以及参数配置各组件的起作用部分。

---

## 🔄 VSS 参数配置完整流程

### 第一步：模板定义
**文件**: `templates/control_strategies/variable_speed_sign/vss_moderate.json`

```json
{
  "template_id": "vss_moderate",
  "strategy_type": "VSS",
  "parameters_schema": [
    {
      "parameter_name": "affected_edges",
      "parameter_type": "edge_array",        // ← 路段选择（步骤2处理）
      "required": true
    },
    {
      "parameter_name": "speed_steps",
      "parameter_type": "step_array",        // ← 关键参数！
      "description": "时间-限速值序列",
      "required": true,
      "default_value": [
        {"time_hours": 7, "speed_kmh": 100},
        {"time_hours": 9, "speed_kmh": 80},
        {"time_hours": 17, "speed_kmh": 100},
        {"time_hours": 19, "speed_kmh": 80}
      ],
      "step_structure": {
        "time_display_unit": "hours",
        "speed_display_unit": "km/h",
        "speed_min": 30,
        "speed_max": 130
      }
    }
  ]
}
```

**关键字段**:
- `parameter_type: "step_array"` - 触发特殊处理逻辑
- `default_value` - 包含 4 个速度步骤
- `step_structure` - 定义时间和速度的显示单位、范围

---

### 第二步：参数表单生成
**函数**: `generateParamsForm(template)` - `templates.html:1439`

```javascript
// 核心逻辑（简化）
template.parameters_schema.forEach(param => {
  if (param.parameter_type === 'step_array') {
    // 1. 调用参数表单渲染函数
    inputHtml = window.renderStepArrayControl(param.parameter_name, param);
    // 参数名：speed_steps
  }
});
```

**处理流程**:
1. 遍历模板的 `parameters_schema`
2. 检测参数类型为 `step_array`
3. 跳过 `affected_edges`（在步骤2已处理）
4. 调用 `window.renderStepArrayControl()`

---

### 第三步：时间轴渲染（关键）
**函数**: `renderStepArrayControl(paramName, schema)` - `parameter_form.js:526-616`

#### 3.1 时间轴初始化
```javascript
// parameter_form.js:535-553
if (window.TimelineVisualizer && defaultSteps.length > 0) {
  const timeline = window.TimelineVisualizer.renderTimeline(
    paramName,                    // "speed_steps"
    defaultSteps,                 // [{time_hours: 7, speed_kmh: 100}, ...]
    { type: 'speed' }            // ← 重要：指定类型为 'speed'
  );
  container.appendChild(timeline);
}
```

**调用链**:
```
renderStepArrayControl()
  ↓
window.TimelineVisualizer.renderTimeline(
  "speed_steps",
  [{time_hours: 7, speed_kmh: 100}, ...],
  {type: 'speed'}
)
```

#### 3.2 时间轴核心实现
**文件**: `js/timeline_visualizer.js:223-286`

```javascript
function renderTimeline(parameterName, intervals, options) {
  // 1. 验证输入
  if (!Array.isArray(intervals) || intervals.length === 0) {
    return createEmptyTimeline(parameterName);
  }

  // 2. 过滤有效区间
  const validIntervals = intervals.filter(interval => {
    const start = interval.time_hours !== undefined
      ? interval.time_hours
      : interval.begin_hours;
    const end = interval.end_hours !== undefined ? interval.end_hours : 24;
    return start >= 0 && start < 24 && (end > start && end <= 24);
  });

  // 3. 根据类型计算时间槽
  let slots;
  if (options.type === 'speed') {
    slots = calculateStepSlots(validIntervals);  // ← VSS 特定逻辑
  } else {
    slots = calculateIntervalSlots(validIntervals);
  }

  // 4. 创建 24 小时时间轴
  // - 添加小时标记（0-23）
  // - 为每个步骤渲染颜色块
  // - 颜色基于速度值 (km/h)
}
```

#### 3.3 VSS 时间槽计算
**函数**: `calculateStepSlots(steps)` - `timeline_visualizer.js:179-195`

```javascript
function calculateStepSlots(steps) {
  const slots = [];
  // 输入: [{time_hours: 7, speed_kmh: 100}, {time_hours: 9, speed_kmh: 80}, ...]

  for (let i = 0; i < steps.length; i++) {
    const start = steps[i].time_hours;
    const end = (i + 1 < steps.length)
      ? steps[i + 1].time_hours
      : 24;                              // ← 最后一个步骤延伸到午夜
    const width = end - start;

    if (width > 0) {
      slots.push({
        start: start,           // 开始时间
        width: width,           // 持续时长
        speed_kmh: steps[i].speed_kmh  // 当前速度（用于着色）
      });
    }
  }
  return slots;
}
```

**例子**（基于模板默认值）:
```
输入步骤:
[
  {time_hours: 7, speed_kmh: 100},
  {time_hours: 9, speed_kmh: 80},
  {time_hours: 17, speed_kmh: 100},
  {time_hours: 19, speed_kmh: 80}
]

计算的时间槽:
[
  {start: 7,  width: 2,  speed_kmh: 100},  // 07:00-09:00 速度 100 km/h
  {start: 9,  width: 8,  speed_kmh: 80},   // 09:00-17:00 速度 80 km/h
  {start: 17, width: 2,  speed_kmh: 100},  // 17:00-19:00 速度 100 km/h
  {start: 19, width: 5,  speed_kmh: 80}    // 19:00-24:00 速度 80 km/h
]
```

#### 3.4 颜色映射
**函数**: `getSpeedColor(speed_kmh)` - `timeline_visualizer.js:52-57`

```javascript
function getSpeedColor(speed_kmh) {
  if (speed_kmh >= 100) return '#10b981';  // 绿色 (≥100 km/h)
  if (speed_kmh >= 80)  return '#3b82f6';  // 蓝色 (80-99 km/h)
  if (speed_kmh >= 60)  return '#f59e0b';  // 橙色 (60-79 km/h)
  return '#ef4444';                         // 红色 (<60 km/h)
}
```

**模板示例的颜色**:
- 07:00-09:00: 100 km/h → 🟢 绿色
- 09:00-17:00: 80 km/h → 🔵 蓝色
- 17:00-19:00: 100 km/h → 🟢 绿色
- 19:00-24:00: 80 km/h → 🔵 蓝色

---

### 第四步：表格编辑器
**函数**: `renderStepArrayControl()` 继续 - `parameter_form.js:555-615`

```javascript
// 创建编辑表格
const table = document.createElement("table");
table.className = "steps-table";

// 表头: Time | Speed | Action
const thead = ...;

// 表体: 对每个 defaultStep 创建一行
const tbody = document.createElement("tbody");
tbody.className = "steps-tbody";
tbody.dataset.parameterName = "speed_steps";

defaultSteps.forEach((step, idx) => {
  addStepRow(tbody, paramName, step.time_hours, step.speed_kmh, stepStructure);
});

table.appendChild(tbody);
container.appendChild(table);

// 添加 "+ Add Step" 按钮
```

#### 4.1 行编辑逻辑
**函数**: `addStepRow()` - `parameter_form.js:621-668`

```javascript
function addStepRow(tbody, paramName, timeVal, speedVal, stepStructure) {
  const row = document.createElement("tr");
  row.className = "step-row";

  // 时间输入框
  const timeInput = document.createElement("input");
  timeInput.type = "number";
  timeInput.className = "step-time";
  timeInput.min = "0";
  timeInput.max = "24";
  timeInput.step = "0.5";
  timeInput.value = timeVal;

  // 速度输入框
  const speedInput = document.createElement("input");
  speedInput.type = "number";
  speedInput.className = "step-speed";
  speedInput.min = stepStructure.speed_min || 30;
  speedInput.max = stepStructure.speed_max || 130;
  speedInput.value = speedVal;

  // 删除按钮
  const removeBtn = ...;

  // 关键：监听输入变化→更新时间轴
  timeInput.addEventListener('input',
    () => debouncedUpdateTimelineFromTable(tbody));
  speedInput.addEventListener('input',
    () => debouncedUpdateTimelineFromTable(tbody));

  tbody.appendChild(row);
}
```

#### 4.2 实时时间轴更新
**函数**: `updateTimelineFromTable(tbody)` - `parameter_form.js:39-91`

```javascript
function updateTimelineFromTable(tbody) {
  const parameterName = tbody.dataset.parameterName;  // "speed_steps"
  const container = tbody.closest('.step-array-control-enhanced');
  const timeline = container.querySelector('.parameter-timeline');

  // 从表格提取当前步骤数据
  const rows = tbody.querySelectorAll('.step-row');
  const steps = [];

  rows.forEach(row => {
    const timeInput = row.querySelector('.step-time');
    const speedInput = row.querySelector('.step-speed');

    steps.push({
      time_hours: parseFloat(timeInput.value) || 0,
      speed_kmh: parseFloat(speedInput.value) || 0
    });
  });

  // 按时间排序
  steps.sort((a, b) => a.time_hours - b.time_hours);

  // 更新时间轴显示
  window.TimelineVisualizer.updateTimeline(timeline, steps, { type: 'speed' });
}

// 防抖版本（300ms 延迟，避免频繁更新）
const debouncedUpdateTimelineFromTable = debounce(updateTimelineFromTable, 300);
```

**更新流程**:
```
用户编辑表格
  ↓
input 事件触发
  ↓
debouncedUpdateTimelineFromTable()（延迟 300ms）
  ↓
extractIntervalsFromTable() - 从当前表格读取数据
  ↓
TimelineVisualizer.updateTimeline()
  ↓
重新计算时间槽和颜色
  ↓
在页面上实时更新时间轴可视化
```

---

### 第五步：数据提交
**函数**: `createStrategy()` - `templates.html:2941-2968`

```javascript
// 特殊处理 step_array 类型参数
if (param.parameter_type === 'step_array') {
  console.log('[createStrategy] Extracting step_array for:', param.parameter_name);

  // 查找表格 tbody（关键！必须匹配 renderStepArrayControl 创建的结构）
  const tbody = document.querySelector(
    `[data-parameter-name="${param.parameter_name}"] .steps-tbody`
  );

  if (tbody) {
    const rows = tbody.querySelectorAll('.step-row');

    if (!param.required && rows.length === 0) {
      return;  // 跳过可选但空的参数
    }

    // 提取数据：从表格行映射到对象
    const value = Array.from(rows).map(row => ({
      time_hours: parseFloat(row.querySelector('.step-time').value),
      speed_kmh: parseFloat(row.querySelector('.step-speed').value)
    }));

    configuredParams[param.parameter_name] = value;
    console.log('[createStrategy] Setting parameter:', param.parameter_name, '=', value);
  } else {
    console.error('[createStrategy] tbody not found for step_array!');
    alert(`无法找到参数 "${param.parameter_name}" 的配置表格`);
  }
  return;
}
```

**提交的数据结构**:
```json
{
  "strategy_name": "早高峰限速策略",
  "strategy_description": "...",
  "speed_steps": [
    {"time_hours": 7, "speed_kmh": 100},
    {"time_hours": 9, "speed_kmh": 80},
    {"time_hours": 17, "speed_kmh": 100},
    {"time_hours": 19, "speed_kmh": 80}
  ]
}
```

---

## ✅ 起作用部分总结

### 1. 模板定义层
- ✅ `vss_moderate.json` - 定义 `speed_steps` 为 `step_array` 类型
- ✅ `step_structure` - 提供时间/速度单位和范围信息

### 2. 表单生成层
- ✅ `generateParamsForm()` (`templates.html:1439`)
  - 遍历 `parameters_schema`
  - 识别 `step_array` 类型
  - 调用 `window.renderStepArrayControl()`

### 3. 渲染层（参数表单）
- ✅ `renderStepArrayControl()` (`parameter_form.js:526-616`)
  - 创建时间轴容器
  - 创建编辑表格
  - 添加操作按钮
  - **关键**: 初始化时间轴可视化

### 4. 时间轴可视化层（核心功能）
- ✅ `TimelineVisualizer.renderTimeline()` (`timeline_visualizer.js:223-286`)
  - 类型检测：`options.type === 'speed'`
  - 调用 `calculateStepSlots()` - VSS 专用时间槽计算
  - 创建 24 小时时间轴 UI
  - 渲染彩色时间块

- ✅ `calculateStepSlots()` (`timeline_visualizer.js:179-195`)
  - **重要逻辑**: 相邻步骤之间的时间间隔
  - 最后一个步骤延伸到 24 小时

- ✅ `getSpeedColor()` (`timeline_visualizer.js:52-57`)
  - 根据速度值返回颜色
  - 100+ km/h → 绿色
  - 80-99 km/h → 蓝色
  - 60-79 km/h → 橙色
  - <60 km/h → 红色

### 5. 实时更新层
- ✅ `updateTimelineFromTable()` (`parameter_form.js:39-91`)
  - 从表格提取最新步骤数据
  - 调用 `TimelineVisualizer.updateTimeline()` 重新渲染
  - 防抖处理避免过度更新

- ✅ `debouncedUpdateTimelineFromTable()` (`parameter_form.js:94`)
  - 300ms 防抖延迟

### 6. 数据提交层
- ✅ `createStrategy()` (`templates.html:2941-2968`)
  - 识别 `step_array` 参数
  - 从 `.steps-tbody .step-row` 提取数据
  - 映射为 `{time_hours, speed_kmh}` 对象数组

---

## 🔗 组件调用关系图

```
generateParamsForm(template)
  ↓
检测 parameter_type === 'step_array'
  ↓
window.renderStepArrayControl(paramName, param)
  ├─ window.TimelineVisualizer.renderTimeline(paramName, defaultSteps, {type: 'speed'})
  │   ├─ calculateStepSlots(validIntervals) ← VSS 特定
  │   └─ createTimelineSlot() 渲染每个时间块
  │
  └─ 创建编辑表格
      ├─ addStepRow() × N 行
      │   └─ 监听 input 事件
      │       └─ debouncedUpdateTimelineFromTable()
      │           └─ window.TimelineVisualizer.updateTimeline()
      └─ Add/Remove 按钮
```

---

## 📊 时间轴状态追踪

### 初始状态（页面加载）
```
模板默认值:
[
  {time_hours: 7, speed_kmh: 100},
  {time_hours: 9, speed_kmh: 80},
  {time_hours: 17, speed_kmh: 100},
  {time_hours: 19, speed_kmh: 80}
]
    ↓
时间轴显示:
[0h - 7h]: 无显示（灰色）
[7h - 9h]: 🟢 绿色 (100 km/h)
[9h - 17h]: 🔵 蓝色 (80 km/h)
[17h - 19h]: 🟢 绿色 (100 km/h)
[19h - 24h]: 🔵 蓝色 (80 km/h)
```

### 用户编辑后
```
用户将第二步改为 {time_hours: 10, speed_kmh: 70}
    ↓
表格更新:
[7, 100], [10, 70], [17, 100], [19, 80]
    ↓
时间轴立即更新（300ms 后）:
[7h - 10h]: 🟢 绿色 (100 km/h)
[10h - 17h]: 🟠 橙色 (70 km/h) ← 颜色改变了！
[17h - 19h]: 🟢 绿色 (100 km/h)
[19h - 24h]: 🔵 蓝色 (80 km/h)
```

---

## 🚀 实际流程验证

### 脚本加载顺序（templates.html）
```html
<!-- 第 1 步：加载时间轴可视化库 -->
<script src="js/timeline_visualizer.js"></script>  <!-- 行 788 -->

<!-- 第 2 步：加载参数表单生成器 -->
<script src="js/parameter_form.js"></script>

<!-- 第 3 步：加载策略管理器（调用 generateParamsForm） -->
<script src="js/strategy_manager.js"></script>  <!-- 行 789 -->
```

**顺序保证**:
- ✅ `TimelineVisualizer` 全局对象在 `parameter_form.js` 之前定义
- ✅ `window.renderStepArrayControl` 在 `templates.html` 之前导出
- ✅ `generateParamsForm()` 可以安全调用两者

---

## 💡 核心发现

### 时间轴为什么正确工作

1. **类型分离** (`options.type`)
   - VSS: `calculateStepSlots()` - 计算相邻步骤间的间隔
   - DHS/TEC: `calculateIntervalSlots()` - 使用 `begin_hours` 和 `end_hours`

2. **数据流向清晰**
   ```
   模板默认值
     ↓ (parameters_schema)
   generateParamsForm()
     ↓
   renderStepArrayControl()
     ↓
   TimelineVisualizer.renderTimeline(..., {type: 'speed'})
     ↓
   calculateStepSlots() - 正确处理 time_hours
     ↓
   时间轴可视化（自动更新）
   ```

3. **实时同步机制**
   - 表格修改 → `debouncedUpdateTimelineFromTable()`
   - 提取表格数据 → 重新计算时间槽 → 更新 UI

---

## ❌ 非起作用部分

### 备用的时间区间控件
- ❌ `renderTimeIntervalArrayControl()` (`parameter_form.js:1459`)
  - 只用作 DHS 的备用方案（通过条件判断）
  - 功能不完整（无时间轴、车型为文本）
  - 应该删除或替换为 `renderDHSIntervalControl()`

### 重复的更新函数
- ⚠️ VSS 和 DHS 各有独立的更新函数
  - `updateTimelineFromTable()` - VSS
  - `updateDHSTimelineFromTable()` - DHS
  - 可以合并为一个泛型函数

---

## 📝 结论

**VSS 的参数配置流程完全正常工作**，包括：
1. ✅ 模板定义 (`step_array` 类型)
2. ✅ 表单生成 (`generateParamsForm`)
3. ✅ 渲染器 (`renderStepArrayControl`)
4. ✅ 时间轴 (`TimelineVisualizer` 正确类型)
5. ✅ 实时更新 (`debouncedUpdateTimelineFromTable`)
6. ✅ 数据提交 (`createStrategy`)

**时间轴显示正确的原因**：
- 正确使用 `calculateStepSlots()` 而非 `calculateIntervalSlots()`
- 时间轴可视化器有明确的类型区分逻辑
- 防抖机制保证了实时更新的性能

