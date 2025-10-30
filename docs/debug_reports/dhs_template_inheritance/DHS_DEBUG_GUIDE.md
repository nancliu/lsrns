# DHS 时间轴问题排查指南

**问题描述**: 应急车道开放策略配置页面有表格但没有时间轴，生成策略实例失败（缺少 interval 参数）

**报告时间**: 2025-10-30

---

## 🔍 问题诊断步骤

### 问题 1: 时间轴没有渲染

#### 步骤 1: 检查 TimelineVisualizer 是否加载

1. **打开浏览器开发者工具**（F12）
2. **切换到 Console 标签**
3. **输入以下命令**:
   ```javascript
   window.TimelineVisualizer
   ```

**预期结果**:
```javascript
{renderTimeline: ƒ, updateTimeline: ƒ, utils: {...}}
```

**如果显示 `undefined`**:
- ❌ 说明 `timeline_visualizer.js` 未加载
- 📝 解决方案：检查 `templates.html` 是否包含脚本引用

**检查脚本引用**:
```bash
# 搜索 timeline_visualizer.js 引用
grep -n "timeline_visualizer.js" frontend/control/templates.html
```

**应该看到类似**:
```html
<script src="/static/control/js/timeline_visualizer.js"></script>
```

---

#### 步骤 2: 检查控制台错误

1. **刷新页面**（Ctrl+R 或 F5）
2. **观察控制台**，查找红色错误消息

**常见错误**:

**错误 A**: `Uncaught TypeError: Cannot read property 'renderTimeline' of undefined`
- **原因**: `window.TimelineVisualizer` 未定义
- **解决**: 确认 `timeline_visualizer.js` 已加载

**错误 B**: `Uncaught ReferenceError: TimelineVisualizer is not defined`
- **原因**: 脚本加载顺序错误
- **解决**: 确保 `timeline_visualizer.js` 在 `parameter_form.js` 之前加载

**错误 C**: `404 Not Found: /static/control/js/timeline_visualizer.js`
- **原因**: 文件路径错误或文件不存在
- **解决**: 检查文件是否存在于 `frontend/control/js/timeline_visualizer.js`

---

#### 步骤 3: 手动测试时间轴渲染

在控制台输入以下命令手动测试：

```javascript
// 测试数据
const testIntervals = [
  {begin_hours: 0, end_hours: 7, status: 'CLOSED'},
  {begin_hours: 7, end_hours: 9, status: 'OPEN'},
  {begin_hours: 9, end_hours: 17, status: 'CLOSED'},
  {begin_hours: 17, end_hours: 19, status: 'OPEN'},
  {begin_hours: 19, end_hours: 24, status: 'CLOSED'}
];

// 渲染时间轴
const timeline = window.TimelineVisualizer.renderTimeline(
  'test_intervals',
  testIntervals,
  { type: 'dhs', description: '测试DHS时间轴' }
);

// 添加到页面（临时测试）
document.body.appendChild(timeline);
```

**预期结果**:
- ✅ 页面底部出现时间轴
- ✅ 显示 5 个时间槽（红-绿-红-绿-红）
- ✅ OPEN 槽为绿色，CLOSED 槽为红色

**如果时间轴出现**:
- 说明 TimelineVisualizer 功能正常
- 问题可能在 `renderDHSIntervalControl()` 函数中

**如果仍然没有时间轴**:
- 检查 `timeline_visualizer.js` 中的 DHS 相关函数
- 检查浏览器兼容性

---

### 问题 2: 生成策略实例失败（缺少 interval 参数）

#### 步骤 1: 检查参数名称

DHS 模板中的参数名称应该是 `intervals`（复数），不是 `interval`（单数）。

**检查模板文件**:
```bash
# 查看 dhs_base.json 中的参数定义
cat templates/control_strategies/dynamic_hard_shoulder/dhs_base.json | grep -A 5 "parameter_name"
```

**应该看到**:
```json
"parameter_name": "intervals",
"parameter_type": "dhs_interval_array",
```

---

#### 步骤 2: 检查参数提取逻辑

1. **打开页面并填写参数**
2. **在生成策略实例前，打开控制台**
3. **添加断点或日志**:

在控制台输入：
```javascript
// 查找 DHS intervals 表格
const tbody = document.querySelector('.dhs-intervals-tbody[data-parameter-name="intervals"]');
console.log('Found tbody:', tbody);

// 检查表格行数
if (tbody) {
  const rows = tbody.querySelectorAll('.dhs-interval-row');
  console.log('Number of rows:', rows.length);

  // 提取数据
  const intervals = Array.from(rows).map(row => ({
    begin_hours: parseFloat(row.querySelector('.dhs-interval-begin').value),
    end_hours: parseFloat(row.querySelector('.dhs-interval-end').value),
    status: row.querySelector('.dhs-interval-status').value,
    allowed_vehicle_types: row.querySelector('.dhs-interval-vehicles').value
      .split(',').map(v => v.trim()).filter(v => v)
  }));

  console.log('Extracted intervals:', intervals);
}
```

**预期输出**:
```
Found tbody: <tbody class="dhs-intervals-tbody" data-parameter-name="intervals">...</tbody>
Number of rows: 5
Extracted intervals: [
  {begin_hours: 0, end_hours: 7, status: "CLOSED", allowed_vehicle_types: ["emergency", "authority"]},
  ...
]
```

**如果 `tbody` 为 `null`**:
- ❌ 说明选择器错误或表格未渲染
- 📝 检查 `data-parameter-name` 属性

**如果 `rows.length` 为 0**:
- ❌ 说明表格行未添加
- 📝 检查 `addDHSIntervalRow()` 函数是否被调用

---

#### 步骤 3: 检查策略创建请求

1. **打开开发者工具 Network 标签**
2. **点击"生成策略实例"按钮**
3. **查找 API 请求**（通常是 POST `/api/v1/control/strategies/instances`）
4. **查看请求 Payload**

**预期 Payload**:
```json
{
  "template_id": "dhs_peak_hours",
  "strategy_name": "测试DHS_G4202",
  "configured_params": {
    "affected_edges": [...],
    "intervals": [
      {"begin_hours": 0, "end_hours": 7, "status": "CLOSED", "allowed_vehicle_types": [...]},
      {"begin_hours": 7, "end_hours": 9, "status": "OPEN", "allowed_vehicle_types": [...]},
      ...
    ]
  }
}
```

**如果 `intervals` 缺失**:
- ❌ 参数提取逻辑有问题
- 📝 检查 `templates.html` 中的 `dhs_interval_array` case

**如果 `intervals` 为空数组 `[]`**:
- ❌ 表格数据未正确读取
- 📝 检查选择器匹配

---

## 🛠️ 快速修复方案

### 修复 1: 确保 timeline_visualizer.js 已加载

检查 `templates.html` 中是否有以下脚本引用（应该在 `<head>` 或 `<body>` 底部）:

```html
<script src="/static/control/js/timeline_visualizer.js"></script>
```

**如果没有，添加它**:
```bash
# 搜索现有的 parameter_form.js 引用位置
grep -n "parameter_form.js" frontend/control/templates.html
```

在 `parameter_form.js` **之前** 添加：
```html
<script src="/static/control/js/timeline_visualizer.js"></script>
<script src="/static/control/js/parameter_form.js"></script>
```

---

### 修复 2: 检查参数名称一致性

确保以下位置使用相同的参数名称：

1. **模板文件** (`dhs_base.json`):
   ```json
   "parameter_name": "intervals"
   ```

2. **渲染函数** (`parameter_form.js`):
   ```javascript
   tbody.dataset.parameterName = paramName; // 应该是 "intervals"
   ```

3. **参数提取** (`templates.html`):
   ```javascript
   const tbody = document.querySelector('.dhs-intervals-tbody[data-parameter-name="intervals"]');
   ```

---

### 修复 3: 添加调试日志

在 `renderDHSIntervalControl()` 函数开头添加日志：

```javascript
function renderDHSIntervalControl(paramName, schema) {
  console.log('[renderDHSIntervalControl] Called with:', paramName, schema);
  console.log('[renderDHSIntervalControl] window.TimelineVisualizer:', window.TimelineVisualizer);

  const container = document.createElement("div");
  container.className = "dhs-interval-control-enhanced";

  const defaultIntervals = schema.default_value || [];
  console.log('[renderDHSIntervalControl] defaultIntervals:', defaultIntervals);

  // ... 其余代码
}
```

刷新页面并查看控制台输出。

---

## 🔧 临时解决方案（如果时间轴无法显示）

如果时间轴功能暂时无法使用，可以先使用表格编辑器创建策略实例：

### 手动填写表格

1. 确保表格中至少有 1 行数据
2. 填写所有必填字段：
   - 开始时间（0-24）
   - 结束时间（0-24）
   - 状态（OPEN 或 CLOSED）
   - 允许车型（逗号分隔，如：`passenger,bus,truck,emergency`）

### 验证覆盖完整 24 小时

确保区间覆盖完整的 0-24 小时，无间隙无重叠：
- ✅ 正确：[0-7], [7-9], [9-17], [17-19], [19-24]
- ❌ 错误：[0-7], [8-9], ... （7-8 有间隙）
- ❌ 错误：[0-7], [6-9], ... （6-7 重叠）

---

## 📝 完整诊断脚本

将以下脚本复制到浏览器控制台，一键诊断所有问题：

```javascript
// ========== DHS 时间轴诊断脚本 ==========
console.log('========== DHS Timeline Diagnostic ==========');

// 1. 检查 TimelineVisualizer
console.log('\n1. Checking TimelineVisualizer...');
if (typeof window.TimelineVisualizer !== 'undefined') {
  console.log('✅ TimelineVisualizer is loaded');
  console.log('   - renderTimeline:', typeof window.TimelineVisualizer.renderTimeline);
  console.log('   - updateTimeline:', typeof window.TimelineVisualizer.updateTimeline);
  console.log('   - getDHSColor:', typeof window.TimelineVisualizer.utils?.getDHSColor);
} else {
  console.error('❌ TimelineVisualizer is NOT loaded!');
  console.log('   Check if timeline_visualizer.js is included in templates.html');
}

// 2. 检查 DHS 表格
console.log('\n2. Checking DHS intervals table...');
const tbody = document.querySelector('.dhs-intervals-tbody');
if (tbody) {
  console.log('✅ DHS table found');
  console.log('   - data-parameter-name:', tbody.dataset.parameterName);

  const rows = tbody.querySelectorAll('.dhs-interval-row');
  console.log('   - Number of rows:', rows.length);

  if (rows.length > 0) {
    console.log('✅ Table has rows');

    // 提取数据
    try {
      const intervals = Array.from(rows).map(row => ({
        begin_hours: parseFloat(row.querySelector('.dhs-interval-begin')?.value),
        end_hours: parseFloat(row.querySelector('.dhs-interval-end')?.value),
        status: row.querySelector('.dhs-interval-status')?.value,
        allowed_vehicle_types: row.querySelector('.dhs-interval-vehicles')?.value
      }));
      console.log('✅ Extracted intervals:', intervals);
    } catch (e) {
      console.error('❌ Failed to extract intervals:', e);
    }
  } else {
    console.warn('⚠️ Table has no rows');
  }
} else {
  console.error('❌ DHS table NOT found!');
  console.log('   Looking for: .dhs-intervals-tbody');

  // 尝试查找其他可能的表格
  const allTables = document.querySelectorAll('tbody[class*="interval"]');
  console.log('   Found other interval tables:', allTables.length);
  allTables.forEach((t, i) => {
    console.log(`   [${i}] class="${t.className}", data-parameter-name="${t.dataset.parameterName}"`);
  });
}

// 3. 检查时间轴元素
console.log('\n3. Checking timeline element...');
const timeline = document.querySelector('.parameter-timeline[data-type="dhs"]');
if (timeline) {
  console.log('✅ Timeline element found');
  console.log('   - data-parameter-name:', timeline.dataset.parameterName);
  console.log('   - data-type:', timeline.dataset.type);

  const slots = timeline.querySelectorAll('.timeline-slot');
  console.log('   - Number of slots:', slots.length);
} else {
  console.error('❌ Timeline element NOT found!');
  console.log('   Looking for: .parameter-timeline[data-type="dhs"]');

  // 尝试查找任何时间轴
  const anyTimeline = document.querySelector('.parameter-timeline');
  if (anyTimeline) {
    console.log('   Found timeline with type:', anyTimeline.dataset.type);
  }
}

// 4. 检查容器
console.log('\n4. Checking DHS control container...');
const container = document.querySelector('.dhs-interval-control-enhanced');
if (container) {
  console.log('✅ DHS control container found');
  console.log('   Children:', container.children.length);
  Array.from(container.children).forEach((child, i) => {
    console.log(`   [${i}] ${child.tagName}.${child.className}`);
  });
} else {
  console.error('❌ DHS control container NOT found!');
  console.log('   Looking for: .dhs-interval-control-enhanced');
}

console.log('\n========== Diagnostic Complete ==========');
```

---

## 📞 报告问题时请提供

如果问题仍未解决，请提供以下信息：

1. **控制台截图**（包含错误消息）
2. **诊断脚本输出**（上面的完整脚本）
3. **Network 标签**（生成策略实例时的请求 Payload）
4. **页面截图**（显示表格但没有时间轴）

---

**文档创建时间**: 2025-10-30
**用于诊断**: DHS 时间轴渲染和策略创建问题
