# 参数配置系统 - 活跃代码流程图

## 🎯 完整执行流程（用户视角）

```
用户在步骤3参数配置页面
    ↓
页面加载：generateParamsForm(selectedTemplate)
    ├─ 📄 templates.html:1439
    └─ 遍历 template.parameters_schema
       ├─ 参数1: affected_edges (edge_array)
       │   └─ ⏭️  跳过 (步骤2已处理)
       │
       ├─ 参数2: speed_steps (step_array) ← VSS 关键参数
       │   ├─ ✅ 调用 window.renderStepArrayControl()
       │   │      📄 parameter_form.js:526-616
       │   │      ↓
       │   │   1️⃣  时间轴初始化
       │   │   └─ window.TimelineVisualizer.renderTimeline(
       │   │        "speed_steps",
       │   │        [{time_hours:7, speed_kmh:100}, ...],
       │   │        {type: 'speed'}  ← 关键！
       │   │      )
       │   │        📄 timeline_visualizer.js:223
       │   │        ├─ 验证输入数据
       │   │        ├─ 过滤有效区间
       │   │        │  (time_hours >= 0 && < 24)
       │   │        ├─ 类型分支
       │   │        │  if type === 'speed'
       │   │        │  └─ calculateStepSlots()  ✅ VSS专用
       │   │        │     📄 timeline_visualizer.js:179
       │   │        │     计算相邻步骤间的时间槽
       │   │        │     [
       │   │        │       {start:7, width:2, speed_kmh:100},
       │   │        │       {start:9, width:8, speed_kmh:80},
       │   │        │       ...
       │   │        │     ]
       │   │        ├─ 创建24小时时间轴UI
       │   │        │  小时标记: 00 01 02 ... 23
       │   │        └─ 渲染时间槽
       │   │           └─ 对每个槽调用 getSpeedColor()
       │   │              100 km/h → 🟢 绿
       │   │              80 km/h  → 🔵 蓝
       │   │              60 km/h  → 🟠 橙
       │   │              <60 km/h → 🔴 红
       │   │
       │   ├─ 2️⃣  表格编辑器
       │   │   └─ 创建 <table> 结构
       │   │      thead: Time | Speed | Action
       │   │      tbody:
       │   │        └─ 对每个 defaultStep 调用 addStepRow()
       │   │           📄 parameter_form.js:621-668
       │   │           ├─ 创建 <input type="number" class="step-time">
       │   │           ├─ 创建 <input type="number" class="step-speed">
       │   │           ├─ 创建删除按钮
       │   │           └─ 添加事件监听
       │   │              timeInput.addEventListener('input', () => {
       │   │                debouncedUpdateTimelineFromTable(tbody)
       │   │              })
       │   │              speedInput.addEventListener('input', () => {
       │   │                debouncedUpdateTimelineFromTable(tbody)
       │   │              })
       │   │
       │   └─ 3️⃣  操作按钮
       │       ├─ "+ Add Step" 按钮
       │       │   onclick → addStepRow() 创建新行
       │       │   触发 updateTimelineFromTable()
       │       └─ "Remove" 按钮（每行）
       │           onclick → row.remove()
       │           触发 updateTimelineFromTable()
       │
       └─ 其他参数继续处理
           (整数、字符串、布尔值等)


==============================================================================
           用户编辑表格中的速度步骤
==============================================================================

用户修改第2行: 时间从9改为10, 速度从80改为70
    ↓
input 事件触发
    ↓
debouncedUpdateTimelineFromTable(tbody) 调用（延迟300ms）
    📄 parameter_form.js:94
    ↓
等待300ms...（如果继续编辑则重置计时器）
    ↓
updateTimelineFromTable(tbody) 执行
    📄 parameter_form.js:39-91
    ├─ const tbody = ...  (获取表格体)
    ├─ const rows = tbody.querySelectorAll('.step-row')
    ├─ 提取表格数据
    │  rows.forEach(row => {
    │    steps.push({
    │      time_hours: parseFloat(row.querySelector('.step-time').value),
    │      speed_kmh: parseFloat(row.querySelector('.step-speed').value)
    │    })
    │  })
    │  结果: [{time_hours:7, speed_kmh:100},
    │         {time_hours:10, speed_kmh:70},
    │         {time_hours:17, speed_kmh:100},
    │         {time_hours:19, speed_kmh:80}]
    │
    ├─ 按时间排序: steps.sort()
    │
    └─ 重新渲染时间轴
       window.TimelineVisualizer.updateTimeline(timeline, steps, {type: 'speed'})
       📄 timeline_visualizer.js:294-336
       ├─ 清除旧时间槽: slotsContainer.innerHTML = ''
       ├─ 验证输入数据
       ├─ 过滤有效区间
       ├─ 重新计算时间槽
       │  calculateStepSlots(steps) 返回:
       │  [
       │    {start:7, width:3, speed_kmh:100},   ← 宽度变了！
       │    {start:10, width:7, speed_kmh:70},   ← 颜色变了！
       │    {start:17, width:2, speed_kmh:100},
       │    {start:19, width:5, speed_kmh:80}
       │  ]
       ├─ 重新着色
       │  70 km/h → getSpeedColor(70) → 🟠 橙色 (60-79范围)
       │
       └─ 更新DOM
          时间轴立即显示新的颜色和宽度


==============================================================================
              用户保存策略 - 点击"生成策略实例"按钮
==============================================================================

createStrategy() 函数执行
    📄 templates.html:2867+
    ├─ 遍历 selectedTemplate.parameters_schema
    │
    └─ 当处理到 speed_steps 参数
       if (param.parameter_type === 'step_array') {
         📄 templates.html:2941-2968
         ├─ 选择器: [data-parameter-name="speed_steps"] .steps-tbody
         ├─ 查找表格体
         │  const tbody = document.querySelector(
         │    '[data-parameter-name="speed_steps"] .steps-tbody'
         │  )
         │
         ├─ 提取行数据
         │  const rows = tbody.querySelectorAll('.step-row')
         │  const value = Array.from(rows).map(row => ({
         │    time_hours: parseFloat(row.querySelector('.step-time').value),
         │    speed_kmh: parseFloat(row.querySelector('.step-speed').value)
         │  }))
         │
         └─ 存储到配置对象
            configuredParams['speed_steps'] = [
              {time_hours: 7, speed_kmh: 100},
              {time_hours: 10, speed_kmh: 70},
              {time_hours: 17, speed_kmh: 100},
              {time_hours: 19, speed_kmh: 80}
            ]
       }

发送API请求: POST /api/v1/control/strategies/create
    ├─ strategy_name: "用户输入的策略名"
    ├─ strategy_description: "..."
    ├─ affected_edges: ["-8712", "-15452", ...]
    ├─ speed_steps: [  ← 从表格提取！
    │   {time_hours: 7, speed_kmh: 100},
    │   {time_hours: 10, speed_kmh: 70},
    │   {time_hours: 17, speed_kmh: 100},
    │   {time_hours: 19, speed_kmh: 80}
    │ ]
    └─ ... 其他参数

后端接收并保存 ✅
```

---

## 📊 DHS 参数配置流程（对比）

```
用户在步骤3参数配置页面

参数: dhs_intervals (dhs_interval_array)
    ↓
✅ 调用 window.renderDHSIntervalControl()
   📄 parameter_form.js:674-773
   ├─ 时间轴初始化
   │  window.TimelineVisualizer.renderTimeline(
   │    "dhs_intervals",
   │    [{begin_hours:6, end_hours:10, status:'CLOSED'}, ...],
   │    {type: 'dhs'}  ← 类型：dhs
   │  )
   │  └─ calculateIntervalSlots() ✅ DHS专用
   │     使用 begin_hours 和 end_hours
   │
   ├─ 表格编辑器
   │  forEach interval → addDHSIntervalRow()
   │  📄 parameter_form.js:778-876
   │  ├─ 开始时间输入
   │  ├─ 结束时间输入
   │  ├─ 状态下拉框 (OPEN/CLOSED)
   │  ├─ 车型多选框 ← DHS特有
   │  └─ 监听变化 → debouncedUpdateDHSTimelineFromTable()
   │
   └─ 保存时
      查找 .dhs-intervals-tbody[data-parameter-name="dhs_intervals"]
      提取数据:
      [
        {begin_hours: 6, end_hours: 10, status: 'CLOSED', allowed_vehicle_types: ['emergency']},
        ...
      ]


⚠️ 备用方案（正常情况下永远不应触发）
    if (!window.renderDHSIntervalControl)  // 故障转移
      └─ window.renderTimeIntervalArrayControl()  ← 旧版本
         📄 parameter_form.js:1459-1506
         ├─ 无时间轴可视化 ❌
         ├─ 车型为文本输入 ❌
         └─ 功能简陋
```

---

## 🔍 代码执行路径对比

### ✅ VSS 完整路径（正常工作）

```
generateParamsForm()
  → param.parameter_type === 'step_array'
    → renderStepArrayControl()
      → TimelineVisualizer.renderTimeline(..., {type: 'speed'})
        → calculateStepSlots()      ✅ 正确选择
        → 创建时间轴UI
      → addStepRow() × N
        → 监听 input 事件
          → debouncedUpdateTimelineFromTable()
            → updateTimelineFromTable()
              → TimelineVisualizer.updateTimeline(..., {type: 'speed'})
                → calculateStepSlots()  ✅ 正确重新计算
                → 更新UI

createStrategy()
  → 查找 .steps-tbody
  → 提取 speed_steps 数据  ✅
  → 提交API
```

### ⚠️ DHS 完整路径 + 备用方案

```
正常情况（首选）:
generateParamsForm()
  → param.parameter_type === 'dhs_interval_array'
    → window.renderDHSIntervalControl() 存在
      → renderDHSIntervalControl()  ✅ 推荐版本
        → TimelineVisualizer.renderTimeline(..., {type: 'dhs'})
          → calculateIntervalSlots()  ✅
        → addDHSIntervalRow() × N
          → 监听事件
            → debouncedUpdateDHSTimelineFromTable()
              → updateDHSTimelineFromTable()

故障转移情况（异常，不应出现）:
generateParamsForm()
  → param.parameter_type === 'dhs_interval_array'
    → window.renderDHSIntervalControl() 不存在
      → renderTimeIntervalArrayControl()  ❌ 备用版本
        ├─ 无时间轴
        └─ 功能受限

实际上：只要 parameter_form.js 被加载，
       window.renderDHSIntervalControl 总是被定义
       故障转移 100% 不会触发
```

---

## 🎨 关键的类型分支点

### TimelineVisualizer.renderTimeline() 中的类型判断

```javascript
// timeline_visualizer.js:271-275
if (options.type === 'speed') {
    slots = calculateStepSlots(validIntervals);
    // 使用 interval.time_hours
    // 计算: end = next_step.time_hours 或 24
} else {
    slots = calculateIntervalSlots(validIntervals);
    // 使用 interval.begin_hours 和 interval.end_hours
    // 计算: width = end_hours - begin_hours
}
```

**这就是时间轴正确工作的核心原因**

---

## 📋 数据流向跟踪

### VSS speed_steps 数据从入口到出口

```
模板定义 (vss_moderate.json)
  default_value: [
    {time_hours: 7, speed_kmh: 100},
    {time_hours: 9, speed_kmh: 80},
    {time_hours: 17, speed_kmh: 100},
    {time_hours: 19, speed_kmh: 80}
  ]
    ↓
generateParamsForm()
  template.parameters_schema.speed_steps
    ↓
renderStepArrayControl(paramName='speed_steps', schema={...})
  defaultSteps = [{...}, {...}, {...}, {...}]
    ├─ → TimelineVisualizer.renderTimeline(...defaultSteps...)
    │    时间轴可视化
    │
    └─ → addStepRow() 4 次
         每个默认值创建一行
         <input value=7 class="step-time">
         <input value=100 class="step-speed">
         ...
    ↓
用户在表格中编辑
    ↓
updateTimelineFromTable()
  读取表格: rows.querySelector('.step-time/step-speed').value
  → [{time_hours: 7, speed_kmh: 100}, ...（用户编辑后）]
    ↓
createStrategy()
  tbody = document.querySelector('[data-parameter-name="speed_steps"] .steps-tbody')
  rows = tbody.querySelectorAll('.step-row')
  value = rows.map(row => ({
    time_hours: parseFloat(row.querySelector('.step-time').value),
    speed_kmh: parseFloat(row.querySelector('.step-speed').value)
  }))
    ↓
POST /api/v1/control/strategies/create
  body: {
    speed_steps: [{time_hours: 7, speed_kmh: 100}, ...],
    ...
  }
    ↓
后端处理 ✅
```

---

## 🚫 完全未使用的代码路径

### 1. renderTimeIntervalArrayControl() 路径（从不执行）

```
condition: if (!window.renderDHSIntervalControl)
status: 永远 FALSE（因为 parameter_form.js 定义了它）
result: renderTimeIntervalArrayControl() 永不执行
impact: 可安全删除
```

### 2. addTimeIntervalRow() 函数（从不调用）

```
caller: renderTimeIntervalArrayControl()
status: 未被使用（由于 DHS 优先选择）
impact: 与上一项一起删除
```

---

## 💡 总结：起作用 vs 冗余

### ✅ 核心活跃路径（生产环境中真正运行）

```
templates.html:generateParamsForm()
  ├─ renderStepArrayControl()
  │   ├─ TimelineVisualizer.renderTimeline(type='speed')
  │   │   ├─ calculateStepSlots() ✅
  │   │   └─ getSpeedColor() ✅
  │   ├─ addStepRow() ✅
  │   └─ debouncedUpdateTimelineFromTable() ✅
  │       └─ updateTimelineFromTable() ✅
  │
  ├─ renderDHSIntervalControl()
  │   ├─ TimelineVisualizer.renderTimeline(type='dhs')
  │   │   ├─ calculateIntervalSlots() ✅
  │   │   └─ getDHSColor() ✅
  │   ├─ addDHSIntervalRow() ✅
  │   └─ debouncedUpdateDHSTimelineFromTable() ✅
  │       └─ updateDHSTimelineFromTable() ✅
  │
  └─ renderFlowIntervalControl() ✅

templates.html:createStrategy()
  ├─ 提取 step_array ✅
  ├─ 提取 dhs_interval_array ✅
  └─ 提取 flow_interval_array ✅
```

### ⚠️ 冗余但仍然存在（可删除）

```
renderTimeIntervalArrayControl()  ← 可删除
addTimeIntervalRow()  ← 可删除
故障转移条件判断  ← 可简化
```

### ❓ 待验证

```
renderFlowIntervalControl() 是否完整  ← 需要检查
```

