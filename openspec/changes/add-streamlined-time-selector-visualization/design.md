# 设计文档：精简时间选择器可视化

**变更ID**: `add-streamlined-time-selector-visualization`

## 架构概述

本设计实现了一个模块化、可复用的时间轴可视化组件，与现有的参数表单系统集成，不修改核心表格编辑逻辑。

### 组件结构

```
frontend/control/js/
├── timeline_visualizer.js    [新增] - 核心时间轴渲染逻辑
└── parameter_form.js          [修改] - 集成点

frontend/control/css/
└── timeline.css              [新增] - 时间轴专用样式（或合并到 styles.css）
```

## 核心组件

### 1. 时间轴可视化模块 (`timeline_visualizer.js`)

**职责**：从参数数据渲染和更新24小时可视化时间轴。

**核心函数**：

```javascript
// 主渲染函数
function renderTimeline(parameterName, intervals, options)
  → 返回: HTMLElement (时间轴容器)

// 时间槽创建
function createTimelineSlot(interval, options)
  → 返回: HTMLElement (带颜色的时间段)

// 更新现有时间轴
function updateTimeline(timelineElement, intervals, options)
  → 修改现有时间轴 DOM

// 工具函数
function timeToPercentage(hours)           // 将小时(0-24)转换为百分比(0-100)
function getColorForValue(interval, type)  // 颜色映射逻辑
function getSlotLabel(interval, type)      // 标签生成
```

**选项对象结构**：

```javascript
{
  type: 'speed' | 'dhs' | 'flow',      // 策略类型
  height: 100,                          // 时间轴高度（像素）
  showLabels: true,                     // 在时间槽中显示文本标签
  colorScheme: {                        // 自定义颜色覆盖
    high: '#10b981',
    medium: '#3b82f6',
    low: '#f59e0b',
    veryLow: '#ef4444'
  }
}
```

### 2. 参数表单集成

**`parameter_form.js` 中的修改点**：

```javascript
// 现有函数: renderStepArrayControl()
function renderStepArrayControl(paramName, schema) {
  const container = document.createElement('div');

  // [新增] 添加时间轴可视化
  if (shouldShowTimeline(schema)) {
    const timeline = window.TimelineVisualizer.renderTimeline(
      paramName,
      schema.default_value || [],
      { type: 'speed' }
    );
    container.appendChild(timeline);
  }

  // [现有] 表格渲染（不变）
  const table = createStepTable(paramName, schema);
  container.appendChild(table);

  return container;
}

// 类似修改：
// - renderDHSIntervalControl()
// - renderFlowIntervalControl()
```

**更新事件绑定**：

```javascript
// 挂接到现有表格变化事件
function onStepChange(tbody, parameterName) {
  // [现有] 收集表格数据
  const steps = collectStepsFromTable(tbody);

  // [新增] 更新时间轴
  const timeline = tbody.closest('[data-parameter-name]')
    .querySelector('.parameter-timeline');
  if (timeline) {
    window.TimelineVisualizer.updateTimeline(timeline, steps, { type: 'speed' });
  }
}
```

## 数据流

```
用户输入（表格）
    ↓
onStepChange() / onIntervalChange()
    ↓
collectStepsFromTable() → 区间数组
    ↓
TimelineVisualizer.updateTimeline()
    ↓
DOM 更新（时间轴段重新渲染）
```

**关键原则**：从表格到时间轴的单向数据流（时间轴为只读可视化）。

## 视觉设计

### 时间轴结构

```
┌─────────────────────────────────────────────────────────────┐
│ 时间小时标记 (0-23)                                          │
│ [00][01][02][03]...[20][21][22][23]                         │
├─────────────────────────────────────────────────────────────┤
│ 时间槽（彩色段）                                             │
│ [██████ 100km/h ██████][█ 80km/h █][████ 60km/h ████]      │
└─────────────────────────────────────────────────────────────┘
```

### HTML 结构

```html
<div class="parameter-timeline" data-parameter-name="speed_steps">
  <!-- 小时标记 -->
  <div class="timeline-hours">
    <div class="timeline-hour">00</div>
    <div class="timeline-hour">01</div>
    <!-- ... 共24个 -->
  </div>

  <!-- 时间槽 -->
  <div class="timeline-slots">
    <div class="timeline-slot" style="left: 0%; width: 29.17%; background: #10b981;">
      <div class="timeline-slot-label">100 km/h</div>
    </div>
    <div class="timeline-slot" style="left: 29.17%; width: 8.33%; background: #3b82f6;">
      <div class="timeline-slot-label">80 km/h</div>
    </div>
    <!-- 更多时间槽... -->
  </div>
</div>
```

### CSS 布局策略

**关键技术**：

1. **Flexbox 用于小时标记**：24个小时的等宽分布
2. **绝对定位用于时间槽**：基于百分比的 left/width 实现精确时间映射
3. **CSS 过渡**：时间轴变化时的平滑更新

```css
.parameter-timeline {
  position: relative;
  height: 100px;
  background: #f3f4f6;
  border-radius: 8px;
  margin-bottom: 15px;
}

.timeline-hours {
  display: flex;              /* 等宽分布 */
  height: 25px;
  border-bottom: 1px solid #d1d5db;
}

.timeline-hour {
  flex: 1;                    /* 每个小时获得相等空间 */
  text-align: center;
  font-size: 10px;
}

.timeline-slots {
  position: relative;         /* 绝对子元素的容器 */
  height: 75px;
  padding: 5px;
}

.timeline-slot {
  position: absolute;         /* 精确定位 */
  height: 65px;
  border-radius: 4px;
  transition: all 0.2s;       /* 平滑更新 */
}
```

## 配色方案

### VSS（可变限速标志）

```javascript
const VSS_COLORS = {
  veryHigh: '#10b981',  // ≥100 km/h - 绿色
  high: '#3b82f6',      // 80-99 km/h - 蓝色
  medium: '#f59e0b',    // 60-79 km/h - 橙色
  low: '#ef4444'        // <60 km/h - 红色
};

function getSpeedColor(speed_kmh) {
  if (speed_kmh >= 100) return VSS_COLORS.veryHigh;
  if (speed_kmh >= 80) return VSS_COLORS.high;
  if (speed_kmh >= 60) return VSS_COLORS.medium;
  return VSS_COLORS.low;
}
```

### DHS（动态硬路肩）

```javascript
const DHS_COLORS = {
  open: '#10b981',      // OPEN 状态 - 绿色
  closed: '#ef4444'     // CLOSED 状态 - 红色
};

function getDHSColor(status) {
  return status === 'OPEN' ? DHS_COLORS.open : DHS_COLORS.closed;
}
```

### TEC（收费站入口控制）

```javascript
const TEC_COLORS = {
  high: '#ef4444',      // ≥400 vph - 红色（高拥堵）
  medium: '#f59e0b',    // 200-399 vph - 橙色
  low: '#10b981'        // <200 vph - 绿色（顺畅）
};

function getFlowColor(vehsPerHour) {
  if (vehsPerHour >= 400) return TEC_COLORS.high;
  if (vehsPerHour >= 200) return TEC_COLORS.medium;
  return TEC_COLORS.low;
}
```

## 算法细节

### 时间到百分比转换

将小时（0-24）映射到 CSS 百分比（0-100%）：

```javascript
function timeToPercentage(hours) {
  return (hours / 24) * 100;
}

// 示例：
// 0:00 → 0%
// 6:00 → 25%
// 12:00 → 50%
// 18:00 → 75%
// 24:00 → 100%
```

### 时间槽宽度计算

对于 VSS 速度步骤（单个时间点 → 延伸到下一个）：

```javascript
function calculateSlotWidths(steps) {
  const slots = [];
  for (let i = 0; i < steps.length; i++) {
    const start = steps[i].time_hours;
    const end = (i + 1 < steps.length) ? steps[i + 1].time_hours : 24;
    const width = end - start;

    slots.push({
      start: start,
      width: width,
      value: steps[i].speed_kmh
    });
  }
  return slots;
}
```

对于 DHS/TEC 区间（显式 begin/end）：

```javascript
function calculateIntervalSlots(intervals) {
  return intervals.map(interval => ({
    start: interval.begin_hours,
    width: interval.end_hours - interval.begin_hours,
    value: interval.status || interval.flow_vph
  }));
}
```

## 性能考虑

### 渲染优化

1. **批量 DOM 更新**：使用 DocumentFragment 创建多个时间槽
2. **节流更新**：对快速表格变化进行防抖（300ms）
3. **限制时间槽数量**：强制最多24个时间槽（每小时一个）

```javascript
// 防抖更新函数
const debouncedTimelineUpdate = debounce((timeline, data, options) => {
  updateTimeline(timeline, data, options);
}, 300);
```

### 内存管理

- 尽可能复用现有时间槽 DOM 元素（更新样式/内容而非重新创建）
- 时间轴销毁时移除事件监听器
- 模块中不存储全局状态（无状态函数）

## 错误处理

### 无效数据

```javascript
function renderTimeline(parameterName, intervals, options) {
  // 验证输入
  if (!Array.isArray(intervals) || intervals.length === 0) {
    return createEmptyTimeline(parameterName);
  }

  // 验证时间范围
  const validIntervals = intervals.filter(interval => {
    const start = interval.time_hours || interval.begin_hours;
    const end = interval.end_hours || 24;
    return start >= 0 && start < 24 && end > start && end <= 24;
  });

  if (validIntervals.length === 0) {
    return createEmptyTimeline(parameterName);
  }

  // 继续渲染...
}
```

### 浏览器兼容性

- **目标**：现代浏览器（Chrome 90+, Firefox 88+, Safari 14+, Edge 90+）
- **降级**：如果不支持 CSS Grid/Flexbox，优雅隐藏时间轴
- **特性检测**：渲染前检查 `CSS.supports()`

```javascript
if (!CSS.supports('display', 'flex')) {
  console.warn('时间轴可视化需要现代浏览器支持');
  return null; // 不渲染时间轴
}
```

## 测试策略

### 单元测试（Jest 或类似）

```javascript
describe('TimelineVisualizer', () => {
  test('timeToPercentage 正确转换小时', () => {
    expect(timeToPercentage(0)).toBe(0);
    expect(timeToPercentage(6)).toBe(25);
    expect(timeToPercentage(12)).toBe(50);
    expect(timeToPercentage(24)).toBe(100);
  });

  test('getSpeedColor 返回正确颜色', () => {
    expect(getSpeedColor(120)).toBe('#10b981');
    expect(getSpeedColor(85)).toBe('#3b82f6');
    expect(getSpeedColor(70)).toBe('#f59e0b');
    expect(getSpeedColor(40)).toBe('#ef4444');
  });

  test('renderTimeline 创建有效 DOM 结构', () => {
    const timeline = renderTimeline('test', [{time_hours: 0, speed_kmh: 100}], {type: 'speed'});
    expect(timeline.querySelector('.timeline-hours')).toBeTruthy();
    expect(timeline.querySelector('.timeline-slots')).toBeTruthy();
  });
});
```

### E2E 测试（Playwright）

```javascript
test('表格变化时时间轴更新', async ({ page }) => {
  await page.goto('http://localhost:8000/control/templates.html');

  // 使用 VSS 模板配置策略
  await page.selectOption('#template-select', 'vss_moderate');

  // 在表格中更改速度值
  await page.fill('input[name="speed_kmh"]', '80');

  // 验证时间轴槽颜色已更改
  const slotColor = await page.locator('.timeline-slot').first().evaluate(el =>
    window.getComputedStyle(el).backgroundColor
  );
  expect(slotColor).toBe('rgb(59, 130, 246)'); // 80 km/h 的蓝色
});
```

## 集成点

### 现有系统接触点

1. **`parameter_form.js`**
   - `renderStepArrayControl()` - 在表格前添加时间轴
   - `renderDHSIntervalControl()` - 在表格前添加时间轴
   - `renderFlowIntervalControl()` - 在表格前添加时间轴
   - `onStepChange()`, `onIntervalChange()` - 挂接时间轴更新

2. **`styles.css`**（或新的 `timeline.css`）
   - 添加时间轴组件样式
   - 确保与现有布局的响应式行为

3. **`templates.html`**
   - 加载新的 `timeline_visualizer.js` 脚本
   - 加载时间轴 CSS

### 向后兼容性

- **无破坏性变更**：时间轴是纯增量
- **优雅降级**：如果时间轴脚本加载失败，表格编辑仍然工作
- **特性检测**：时间轴仅在浏览器支持所需 CSS 时渲染

## 未来增强（不在范围内）

### 阶段2：交互式时间轴

- 点击时间槽高亮对应表格行
- 悬停提示显示详细信息
- 拖动时间槽边界调整时间

### 阶段3：验证覆盖层

- 重叠时间范围的红色边框
- 时间间隙的虚线
- 不完整24小时覆盖的警告图标

### 阶段4：高级功能

- 导出时间轴为 PNG 图像
- 复制/粘贴时间模式
- 常见模式的预设模板
- 多时间轴对比视图

## 开放问题

1. **时间轴应该可折叠吗？**（用户可以隐藏/显示）
   - 决策：是，在最终实现中添加折叠按钮

2. **移动端响应式优先级？**
   - 决策：桌面优先；移动端优化在阶段2

3. **标签的国际化（i18n）？**
   - 决策：使用中文标签（与现有 UI 一致）；i18n 推迟

## 参考资料

- 实施指南：`docs/control_frontend/ENHANCED_TIME_CONTROLS_GUIDE.md`
- 参考原型：`docs/control_frontend/universal-time-strategy-config.html`
- 当前参数表单：`frontend/control/js/parameter_form.js`
- 颜色来源：Tailwind CSS 默认色板
