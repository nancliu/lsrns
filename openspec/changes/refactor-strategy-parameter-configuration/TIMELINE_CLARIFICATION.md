# 时间轴更新函数合并策略 - 澄清说明

## 背景

基于用户反馈，需要澄清时间轴更新函数合并时如何处理不同策略类型的语义差异和可能的叠加场景。

## 策略类型本质差异

### 1. VSS (Variable Speed Sign - 可变限速)

**语义**：时刻点的速度值
- **数据结构**：`[{ time_hours: 7, speed_kmh: 60 }]`
- **含义**：从 7:00 开始限速 60 km/h，直到下一个时刻点
- **可视化**：段状着色（每段显示当前速度）
- **计算方式**：`calculateStepSlots()` - 将时刻点转换为时间段

**示例**：
```
0:00 ───[80 km/h]───► 7:00 ───[60 km/h]───► 9:00 ───[80 km/h]───► 24:00
```

### 2. DHS (Dynamic Hard Shoulder - 动态硬路肩)

**语义**：时间段的开关状态
- **数据结构**：`[{ begin_hours: 7, end_hours: 9, status: 'OPEN' }]`
- **含义**：7:00-9:00 硬路肩开放，其他时间关闭
- **可视化**：段状着色（OPEN=绿色，CLOSED=红色）
- **计算方式**：`calculateIntervalSlots()` - 直接使用区间

**示例**：
```
0:00 ───[CLOSED]───► 7:00 ───[OPEN]───► 9:00 ───[CLOSED]───► 24:00
```

### 3. TEC (Toll/Entrance Control - 收费站/入口管控)

**语义**：时间段的开关/流量控制
- **数据结构（开关）**：`[{ begin_hours: 7, end_hours: 9, status: 'OPEN' }]`
- **数据结构（流量）**：`[{ begin_hours: 7, end_hours: 9, flow_vph: 400, target_speed: 60 }]`
- **含义**：
  - 开关：7:00-9:00 入口开放
  - 流量：7:00-9:00 限流 400 车/时，目标速度 60 km/h
- **可视化**：段状着色（流量用颜色表示拥堵程度）
- **计算方式**：`calculateIntervalSlots()` - 直接使用区间

**示例（流量控制）**：
```
0:00 ───[200 vph]───► 7:00 ───[400 vph]───► 9:00 ───[200 vph]───► 24:00
       (绿-低)              (红-高)              (绿-低)
```

## 策略叠加场景

### 场景 1：VSS + DHS 叠加

**现实案例**：G4202 绕城高速 K42.32 段
- **DHS**：7:00-9:00 硬路肩开放（增加通行能力）
- **VSS**：7:00 开始限速 60 km/h（控制车速保证安全）

**可视化需求**：
- 两条独立的时间轴
- 或单条时间轴上下分层显示

### 场景 2：TEC（流量控制）+ VSS 叠加

**现实案例**：入口匝道计量 + 主线限速
- **TEC**：7:00-9:00 入口限流 400 车/时
- **VSS**：7:00-9:00 主线限速 80 km/h

**可视化需求**：
- 两条独立的时间轴（因为作用对象不同：入口 vs 主线）

## 时间轴更新函数合并方案

### 当前问题

**重复代码**：
```javascript
// parameter_form.js 中存在 4 个几乎相同的函数
updateTimelineFromTable(tbody)          // VSS 用
updateDHSTimelineFromTable(tbody)       // DHS 用
updateFlowTimelineFromTable(tbody)      // TEC 流量用
updateTECTimelineFromTable(tbody)       // TEC 开关用
```

### 合并方案

**保持 `TimelineVisualizer.updateTimeline()` 不变**（已经很好地设计了）

**在 `parameter_form.js` 中创建统一的包装函数**：

```javascript
/**
 * 统一的时间轴更新函数（从表格提取数据并更新时间轴）
 * @param {HTMLElement} tbody - 表格体元素
 * @param {Object} config - 配置对象
 */
function updateTimeline(tbody, config = {}) {
    const {
        // 数据提取配置
        useInterval = false,     // true: 时段模式, false: 时刻模式
        timeField = 'time_hours',
        beginField = 'begin_hours',
        endField = 'end_hours',
        valueField = 'speed_kmh',

        // 选择器配置
        rowSelector = '.step-row',
        timeSelector = '.step-time',
        beginSelector = '.interval-begin',
        endSelector = '.interval-end',
        valueSelector = '.step-speed',

        // 可视化配置
        visualizationType = 'speed'  // 'speed' | 'dhs' | 'flow'
    } = config;

    // 查找容器和时间轴元素
    const container = tbody.closest('.step-array-control-enhanced, .interval-control-enhanced');
    if (!container) return;

    const timeline = container.querySelector('.parameter-timeline');
    if (!timeline) return;

    // 提取数据
    const rows = tbody.querySelectorAll(rowSelector);
    const data = [];

    rows.forEach(row => {
        if (useInterval) {
            // 时段模式（DHS, TEC）
            const beginInput = row.querySelector(beginSelector);
            const endInput = row.querySelector(endSelector);
            const valueInput = row.querySelector(valueSelector);

            if (beginInput && endInput) {
                const interval = {
                    [beginField]: parseFloat(beginInput.value) || 0,
                    [endField]: parseFloat(endInput.value) || 0
                };

                // 添加值字段（status, flow_vph 等）
                if (valueInput) {
                    interval[valueField] = valueInput.type === 'select-one'
                        ? valueInput.value
                        : parseFloat(valueInput.value) || 0;
                }

                data.push(interval);
            }
        } else {
            // 时刻模式（VSS）
            const timeInput = row.querySelector(timeSelector);
            const valueInput = row.querySelector(valueSelector);

            if (timeInput && valueInput) {
                data.push({
                    [timeField]: parseFloat(timeInput.value) || 0,
                    [valueField]: parseFloat(valueInput.value) || 0
                });
            }
        }
    });

    // 排序
    if (useInterval) {
        data.sort((a, b) => a[beginField] - b[beginField]);
    } else {
        data.sort((a, b) => a[timeField] - b[timeField]);
    }

    // 调用 TimelineVisualizer
    window.TimelineVisualizer.updateTimeline(timeline, data, {
        type: visualizationType
    });
}

// ==================== 使用示例 ====================

// VSS: 时刻点 + 速度
updateTimeline(tbody, {
    useInterval: false,
    visualizationType: 'speed'
});

// DHS: 时段 + 状态
updateTimeline(tbody, {
    useInterval: true,
    beginField: 'begin_hours',
    endField: 'end_hours',
    valueField: 'status',
    beginSelector: '.interval-begin',
    endSelector: '.interval-end',
    valueSelector: '.interval-status',
    visualizationType: 'dhs'
});

// TEC 流量控制: 时段 + 流量
updateTimeline(tbody, {
    useInterval: true,
    valueField: 'flow_vph',
    valueSelector: '.interval-flow',
    visualizationType: 'flow'
});

// TEC 开关控制: 时段 + 状态（简化版，流量控制作为未来扩展）
updateTimeline(tbody, {
    useInterval: true,
    valueField: 'status',
    valueSelector: '.interval-status',
    visualizationType: 'dhs'  // 复用 DHS 的开关可视化
});
```

### 默认配置预设（简化调用）

```javascript
const TIMELINE_CONFIGS = {
    vss: {
        useInterval: false,
        rowSelector: '.step-row',
        timeSelector: '.step-time',
        valueSelector: '.step-speed',
        visualizationType: 'speed'
    },

    dhs: {
        useInterval: true,
        rowSelector: '.interval-row',
        beginSelector: '.interval-begin',
        endSelector: '.interval-end',
        valueSelector: '.interval-status',
        visualizationType: 'dhs'
    },

    tec_flow: {
        useInterval: true,
        rowSelector: '.interval-row',
        beginSelector: '.interval-begin',
        endSelector: '.interval-end',
        valueSelector: '.interval-flow',
        valueField: 'flow_vph',
        visualizationType: 'flow'
    },

    tec_simple: {
        useInterval: true,
        rowSelector: '.interval-row',
        beginSelector: '.interval-begin',
        endSelector: '.interval-end',
        visualizationType: 'simple_interval'
    }
};

// 简化调用
function updateTimelineByType(tbody, type) {
    updateTimeline(tbody, TIMELINE_CONFIGS[type]);
}

// 使用
updateTimelineByType(tbody, 'vss');
updateTimelineByType(tbody, 'dhs');
updateTimelineByType(tbody, 'tec_flow');
```

## 叠加显示方案（未来扩展）

### 方案 A：双层时间轴（推荐）

**适用场景**：VSS + DHS 叠加

**UI 结构**：
```html
<div class="timeline-group">
    <div class="timeline-label">DHS 状态</div>
    <div class="parameter-timeline" data-type="dhs">
        <!-- DHS 时间轴 -->
    </div>

    <div class="timeline-label">VSS 限速</div>
    <div class="parameter-timeline" data-type="speed">
        <!-- VSS 时间轴 -->
    </div>
</div>
```

**优点**：
- 清晰展示两种策略
- 容易理解时间关系
- 实现简单

**缺点**：
- 占用更多垂直空间

### 方案 B：分层叠加时间轴（复杂，暂不实现）

**适用场景**：需要在同一时间轴上显示多个参数

**实现**：
```html
<div class="parameter-timeline multilayer">
    <div class="timeline-layer" data-layer="dhs">
        <!-- DHS 槽，透明度 50% -->
    </div>
    <div class="timeline-layer" data-layer="speed">
        <!-- VSS 槽，透明度 50% -->
    </div>
</div>
```

**优点**：
- 节省空间
- 直观展示叠加关系

**缺点**：
- 视觉混乱
- 实现复杂
- 颜色区分困难

## TEC 流量控制的简化处理

### 当前阶段（本次重构）

**仅支持 TEC 开关模式**：
- 时间段 + 开放/关闭状态
- 使用 DHS 的可视化逻辑（复用代码）

**不支持（未来扩展）**：
- 时间段 + 流量值（400 vph）
- 时间段 + 目标速度（60 km/h）

### 未来扩展（Phase 2）

**完整 TEC 流量控制**：
- 增加表格列：`流量(车/时)` | `目标速度(km/h)`
- 时间轴双层显示：
  - 上层：流量值（颜色表示拥堵）
  - 下层：目标速度（类似 VSS）

## 修改总结

### parameter_form.js 修改

1. **删除**：4 个重复函数
   - `updateTimelineFromTable()`
   - `updateDHSTimelineFromTable()`
   - `updateFlowTimelineFromTable()`
   - `updateTECTimelineFromTable()`

2. **新增**：统一函数
   - `updateTimeline(tbody, config)` - 通用更新函数
   - `TIMELINE_CONFIGS` - 预设配置
   - `updateTimelineByType(tbody, type)` - 简化调用

3. **调用点修改**：
   - 所有调用旧函数的地方改为 `updateTimelineByType(tbody, 'vss'|'dhs'|'tec_simple')`

### TimelineVisualizer.js 修改

**无需修改**！现有的 `updateTimeline()` API 已经足够通用。

### 数据流

```
表格输入
   ↓
updateTimelineByType(tbody, type) [新]
   ↓
updateTimeline(tbody, TIMELINE_CONFIGS[type]) [新]
   ↓
提取数据 → 转换格式
   ↓
TimelineVisualizer.updateTimeline(timeline, data, options) [已存在]
   ↓
渲染时间轴
```

## 验证计划

1. **VSS 策略**：创建速度步骤，验证时间轴显示正确
2. **DHS 策略**：创建开放/关闭区间，验证时间轴显示正确
3. **TEC 简单策略**：创建开放/关闭区间，验证复用 DHS 可视化
4. **数据一致性**：修改表格后，时间轴立即更新
5. **边界条件**：空表格、单行、24小时覆盖

## 与其他文档的关系

- **design.md 第2节**：更新时间轴合并方案
- **tasks.md Task 2.1**：实施时间轴函数合并
- **spec.md Requirement 7**：代码结构要求

## 决策记录

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 合并方式 | 参数化配置对象 | 保持灵活性，易于扩展 |
| VSS 语义 | 时刻点（但可视化为段） | 符合用户理解，与 SUMO 一致 |
| DHS/TEC 语义 | 时间段 | 明确表达开关区间 |
| TEC 流量控制 | 暂不实现 | 降低复杂度，Phase 2 扩展 |
| 叠加显示 | 双层时间轴（未来） | 清晰易懂，本次重构不实现 |
| 代码重用 | 复用 TimelineVisualizer | 已有良好设计，无需修改 |
