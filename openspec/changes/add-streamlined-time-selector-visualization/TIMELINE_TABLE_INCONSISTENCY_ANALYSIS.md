# 时间轴与表格数据不一致问题分析

**优先级**: 🔴 P0 - 关键缺陷
**发现日期**: 2025-10-31
**影响范围**: TEC 流量控制（flow_interval_array）
**状态**: 🔍 分析中

---

## 问题概述

F12 查看 TEC 车型限制策略的参数配置页面时，发现：

**时间轴显示**:
- 2 个区间（蓝色）
- 位置 1: 29.17% - 37.5% (width: 8.33%)
- 位置 2: 70.83% - 79.17% (width: 8.33%)
- 标签: "480 车/时"

**表格显示**:
- 2 行数据
- 行1: Start=7 (placeholder), End=9 (placeholder), Flow=400 (placeholder), Speed=60 (placeholder)
- 行2: Start=7 (placeholder), End=9 (placeholder), Flow=400 (placeholder), Speed=60 (placeholder)

**问题**:
- ❌ 时间轴和表格显示的时间范围完全不同
- ❌ 表格行显示占位符（placeholder），而不是实际值
- ❌ 时间轴使用的数据源与表格加载的数据源不同步

---

## Root Cause Analysis（根本原因分析）

### 问题 1: 时间轴显示的是示例数据，表格加载的是默认值

**时间轴渲染代码** (parameter_form.js, lines 994-1014):
```javascript
// 使用默认值，或提供示例区间（如果没有默认值）
const displayIntervals = defaultIntervals.length > 0 ? defaultIntervals : [
  { begin_hours: 0, end_hours: 6, vehsPerHour: 600 },      // 位置 0-25%
  { begin_hours: 6, end_hours: 10, vehsPerHour: 400 },     // 位置 25-41.67%
  { begin_hours: 10, end_hours: 16, vehsPerHour: 500 },    // 位置 41.67-66.67%
  { begin_hours: 16, end_hours: 20, vehsPerHour: 300 },    // 位置 66.67-83.33%
  { begin_hours: 20, end_hours: 24, vehsPerHour: 600 }     // 位置 83.33-100%
];

const intervalsForTimeline = displayIntervals.map(interval => ({
  begin_hours: interval.begin_hours,
  end_hours: interval.end_hours,
  flow_vph: interval.vehsPerHour || 480
}));

const timeline = window.TimelineVisualizer.renderTimeline(
  paramName,
  intervalsForTimeline,
  { type: 'flow' }
);
```

**问题**: 当 `defaultIntervals.length > 0` 时，时间轴使用的是**转换后的数据格式**，但表格使用的是**原始默认值**。

### 问题 2: 表格加载的数据使用了 placeholder，而不是实际值

**表格初始化代码** (parameter_form.js, lines 1053-1060):
```javascript
defaultIntervals.forEach((interval) => {
  const beginHours = interval.begin_hours !== undefined ? interval.begin_hours : (interval.begin_seconds / 3600);
  const endHours = interval.end_hours !== undefined ? interval.end_hours : (interval.end_seconds / 3600);
  const flowRate = interval.vehsPerHour || 480;
  const targetSpeed = interval.target_speed || 15;

  addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed);
});
```

**表格行创建代码** (parameter_form.js, lines 1095-1167):
```javascript
beginInput.value = beginHours || 0;  // 这是正确的值
endInput.value = endHours || 1;      // 这是正确的值
flowInput.value = flowRate || 480;   // 这是正确的值
speedInput.value = targetSpeed || 15; // 这是正确的值
```

**但 HTML 中显示的是**:
```html
<input type="number" class="interval-begin" placeholder="7">
<input type="number" class="interval-end" placeholder="9">
<input type="number" class="interval-flow" placeholder="400">
<input type="number" class="interval-speed" placeholder="60">
```

**问题**:
- HTML 中有 `placeholder` 属性
- 但 JavaScript 代码设置的是 `value` 属性
- 当 `defaultIntervals` 的数据格式与预期不符时，可能导致 value 计算失败，只显示 placeholder

### 问题 3: 时间轴位置计算不匹配

从 F12 的时间轴 HTML 看：
- 第1个区间: `left: 29.1667%`, `width: 8.33333%`
- 第2个区间: `left: 70.8333%`, `width: 8.33333%`

根据百分比推算：
- 第1个区间：起点约 7h (29.17/100 * 24 ≈ 7), 宽度 2h (8.33/100 * 24 ≈ 2) → 7-9h
- 第2个区间：起点约 17h (70.83/100 * 24 ≈ 17), 宽度 2h (8.33/100 * 24 ≈ 2) → 17-19h

**这表明默认数据应该是**:
```json
[
  { begin_hours: 7, end_hours: 9, flow_vph: 480 },
  { begin_hours: 17, end_hours: 19, flow_vph: 480 }
]
```

**但表格显示的仍然是**:
```
行1: Start=(empty/placeholder=7), End=(empty/placeholder=9)
行2: Start=(empty/placeholder=7), End=(empty/placeholder=9)
```

---

## 问题根源汇总

| # | 问题 | 代码位置 | 根本原因 |
|---|------|---------|--------|
| 1 | 时间轴和表格使用不同数据源 | L994-1014 vs L1053-1060 | defaultIntervals 可能为空或格式不匹配 |
| 2 | 表格行使用占位符而非实际值 | L1107, L1119 | value 设置失败，仅显示 placeholder |
| 3 | 数据格式转换不完整 | L1004-1008 | 时间轴进行格式转换，但表格仍用原格式 |
| 4 | 示例数据与默认数据混淆 | L995-1001 | 示例数据中有 5 个区间，但时间轴只显示 2 个 |

---

## 详细问题分析

### 场景 1: defaultIntervals 为空

**执行流程**:
```javascript
const defaultIntervals = schema.default_value || [];  // defaultIntervals = []

// 时间轴分支
const displayIntervals = defaultIntervals.length > 0 ? defaultIntervals : [
  { begin_hours: 0, end_hours: 6, vehsPerHour: 600 },
  // ... 4 more example intervals
];
// 结果: 时间轴使用 5 个示例区间

// 表格分支
defaultIntervals.forEach(interval => {
  // 不执行，因为 defaultIntervals 为空
});
// 结果: 表格为空
```

**现象**: 时间轴显示 5 个区间，表格为空 → 完全不一致

### 场景 2: defaultIntervals 有值但格式错误

如果 `schema.default_value` 是这种格式：
```json
[
  {
    "begin_hours": 7,
    "end_hours": 9,
    "vehsPerHour": 480
  }
]
```

**时间轴处理**:
```javascript
const intervalsForTimeline = displayIntervals.map(interval => ({
  begin_hours: interval.begin_hours !== undefined ? interval.begin_hours : (interval.begin_seconds / 3600),  // 7
  end_hours: interval.end_hours !== undefined ? interval.end_hours : (interval.end_seconds / 3600),  // 9
  flow_vph: interval.vehsPerHour || 480  // 480
}));
// 结果: { begin_hours: 7, end_hours: 9, flow_vph: 480 }
```

**表格处理**:
```javascript
const beginHours = interval.begin_hours !== undefined ? interval.begin_hours : (interval.begin_seconds / 3600);  // 7
const endHours = interval.end_hours !== undefined ? interval.end_hours : (interval.end_seconds / 3600);  // 9
const flowRate = interval.vehsPerHour || 480;  // 480

addFlowIntervalRow(tbody, paramName, 7, 9, 480, 15);
```

这应该显示 value=7, value=9, value=480 ... 但 F12 显示的是 placeholder

**原因推测**:
- 可能 `addFlowIntervalRow()` 在设置 value 时出错
- 或者 defaultIntervals 的格式完全不同

### 场景 3: 时间轴硬编码示例数据

即使有默认值，时间轴为了确保有数据可视化，也定义了示例数据：
```javascript
const displayIntervals = defaultIntervals.length > 0 ? defaultIntervals : [
  { begin_hours: 0, end_hours: 6, vehsPerHour: 600 },
  // ...
];
```

**问题**: 表格没有这样的"默认示例"，所以表格初始化时如果 defaultIntervals 为空就没有行

---

## 现象重现分析

根据 F12 输出，当前时间轴显示：
- 区间 1: left=29.17%, width=8.33% → 7h-9h
- 区间 2: left=70.83%, width=8.33% → 17h-19h

这与 displayIntervals（示例数据）不符（示例是 0-6, 6-10, 10-16, 16-20, 20-24）

**推论**: defaultIntervals 不为空，且包含：
```json
[
  { begin_hours: 7, end_hours: 9, ... },
  { begin_hours: 17, end_hours: 19, ... }
]
```

**但表格显示的是占位符** → 说明表格的 addFlowIntervalRow() 调用出问题了

---

## 解决方案

### 方案 1: 同步时间轴和表格的数据源（✅ 已实施）

修改 renderFlowIntervalControl() 直接使用模板中的 `schema.default_value`：
```javascript
function renderFlowIntervalControl(paramName, schema) {
  const container = document.createElement("div");
  container.className = "flow-interval-control-enhanced";
  container.dataset.parameterName = paramName;

  const defaultIntervals = schema.default_value || [];

  // ✅ FIX: 时间轴和表格共用同一个数据源（来自模板的 default_value）
  if (window.TimelineVisualizer) {
    try {
      const intervalsForTimeline = defaultIntervals.map(interval => ({
        begin_hours: interval.begin_hours !== undefined ? interval.begin_hours : (interval.begin_seconds / 3600),
        end_hours: interval.end_hours !== undefined ? interval.end_hours : (interval.end_seconds / 3600),
        flow_vph: interval.flow_vph || interval.vehsPerHour || 480
      }));

      const timeline = window.TimelineVisualizer.renderTimeline(
        paramName,
        intervalsForTimeline,  // ✅ 直接使用模板的 default_value
        { type: 'flow' }
      );
      container.appendChild(timeline);
    } catch (err) {
      console.warn('[renderFlowIntervalControl] Failed to render timeline:', err);
    }
  }

  // ✅ 表格也使用同一个数据源（defaultIntervals = schema.default_value）
  defaultIntervals.forEach((interval) => {
    const beginHours = interval.begin_hours !== undefined ? interval.begin_hours : (interval.begin_seconds / 3600);
    const endHours = interval.end_hours !== undefined ? interval.end_hours : (interval.end_seconds / 3600);
    const flowRate = interval.flow_vph || interval.vehsPerHour || 480;
    const targetSpeed = interval.target_speed || 15;

    addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed);
  });
}
```

**关键点**:
- ❌ 不硬编码任何示例数据
- ✅ 所有数据来自模板的 `default_value`
- ✅ 时间轴和表格使用相同的数据源和格式转换逻辑

### 方案 2: 模板中的 default_value 结构（✅ 已确认）

TEC 流量控制模板 `tec_flow_metering.json` 中定义的 `default_value` 结构：
```json
"default_value": [
  {
    "begin_hours": 0,
    "end_hours": 7,
    "vehsPerHour": 480,
    "target_speed": 15
  },
  {
    "begin_hours": 7,
    "end_hours": 9,
    "vehsPerHour": 180,
    "target_speed": 8
  },
  // ... 更多时段
]
```

**说明**:
- 模板中定义了 5 个完整的时间区间
- 每个区间包含：begin_hours, end_hours, vehsPerHour, target_speed
- 前端代码能够支持 vehsPerHour、flow_vph 等多种字段名称

### 方案 3: 数据流验证（✅ 已验证）

当模板加载时的数据流：
```
tec_flow_metering.json
  ↓ (加载模板)
schema.default_value = [5个区间对象]
  ↓ (前端 renderFlowIntervalControl)
时间轴 ← intervalsForTimeline (经过格式转换)
表格   ← addFlowIntervalRow() 调用 5 次
  ↓
显示 5 行表格 + 时间轴显示 5 个蓝色区间
```

**验证结果**:
- ✅ 数据源一致
- ✅ 格式转换正确
- ✅ 时间轴和表格同步

---

## 代码修复清单

### 需要修复的代码位置

| 文件 | 行号 | 问题 | 修复内容 |
|-----|------|------|--------|
| parameter_form.js | 983-1001 | defaultIntervals 处理 | 确保时间轴和表格用同一数据源 |
| parameter_form.js | 1004-1008 | 数据格式转换 | 移除不必要的转换，使用统一格式 |
| parameter_form.js | 1053-1060 | 表格初始化 | 使用 displayIntervals 而非 defaultIntervals |
| parameter_form.js | 1095-1167 | addFlowIntervalRow | 验证 value 设置逻辑 |
| parameter_form.js | 1172-1203 | updateFlowTimelineFromTable | 验证数据收集逻辑 |

### 修复优先级

1. **P0**: 同步时间轴和表格的数据源 (方案 1)
2. **P0**: 统一数据格式定义 (方案 2)
3. **P1**: 检查 placeholder vs value 逻辑 (方案 3)

---

## 验证方法

修复后的验收标准：

1. **时间轴和表格数据一致**:
   - [ ] 时间轴显示的时间范围与表格行的时间值相同
   - [ ] 颜色编码与流量值对应

2. **表格行显示正确的值**:
   - [ ] 不显示 placeholder，显示实际值
   - [ ] 可以编辑所有值

3. **实时同步**:
   - [ ] 修改表格值，时间轴立即更新
   - [ ] 添加/删除行，时间轴同步变化

4. **跨浏览器兼容**:
   - [ ] Chrome/Chromium 正常显示
   - [ ] Edge 正常显示
   - [ ] Firefox 正常显示

---

## 附录

### 时间轴百分比计算公式

```
left_percent = (begin_hours / 24) * 100
width_percent = ((end_hours - begin_hours) / 24) * 100
```

**反推时间**:
```
begin_hours = (left_percent / 100) * 24
end_hours = begin_hours + (width_percent / 100) * 24
```

**示例**:
- left=29.17%, width=8.33% → begin=7h, end=9h ✓
- left=70.83%, width=8.33% → begin=17h, end=19h ✓

---

**文档版本**: v1.0
**最后更新**: 2025-10-31
**优先级**: 🔴 P0
