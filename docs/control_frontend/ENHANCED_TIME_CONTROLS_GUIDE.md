# 增强型时间选择器集成指南

## 概述

基于`docs/control_frontend/universal-time-strategy-config.html`的设计，为策略参数配置添加可视化时间轴组件。

---

## 设计特性

### 1. **可视化时间轴**
- 24小时时间条
- 时段颜色编码
- 拖拽调整边界
- 跨午夜支持

### 2. **三种控件类型**

#### VSS速度步骤 (step_array)
```
时间轴: [==100km/h==][==80km/h==][==60km/h==]
表格:   时间 | 速度
        7:00 | 100
        9:00 | 80
       17:00 | 60
```

#### DHS时间区间 (dhs_interval_array)
```
时间轴: [CLOSED][OPEN: 应急车辆][OPEN: 所有车型][CLOSED]
表格:   开始 | 结束 | 状态  | 车型
        0:00 | 7:00 | CLOSED| emergency
        7:00 | 9:00 | OPEN  | all
```

#### TEC流量控制 (flow_interval_array)
```
时间轴: [正常120vph][高峰480vph][正常120vph]
表格:   开始 | 结束 | 流量   | 速度
        6:00 | 10:00| 480    | 15
       10:00 | 17:00| 120    | 30
```

---

## 实现方案

### 方案A: 独立时间轴组件（推荐）

**优势**:
- 模块化，易维护
- 可复用
- 独立样式

**实现**:
```javascript
// 在 parameter_form.js 中添加

function renderTimeline(parameterName, intervals, options) {
    const timeline = document.createElement('div');
    timeline.className = 'parameter-timeline';
    timeline.dataset.parameterName = parameterName;

    // 时间轴标尺
    const hours = document.createElement('div');
    hours.className = 'timeline-hours';
    for (let i = 0; i < 24; i++) {
        const hour = document.createElement('div');
        hour.className = 'timeline-hour';
        hour.textContent = i.toString().padStart(2, '0');
        hours.appendChild(hour);
    }
    timeline.appendChild(hours);

    // 时间段可视化
    const slots = document.createElement('div');
    slots.className = 'timeline-slots';
    intervals.forEach(interval => {
        const slot = createTimelineSlot(interval, options);
        slots.appendChild(slot);
    });
    timeline.appendChild(slots);

    return timeline;
}

function createTimelineSlot(interval, options) {
    const start = timeToPercentage(interval.begin_hours || interval.time_hours);
    const end = timeToPercentage(interval.end_hours || 24);
    const width = end - start;

    const slot = document.createElement('div');
    slot.className = 'timeline-slot';
    slot.style.left = `${start}%`;
    slot.style.width = `${width}%`;
    slot.style.backgroundColor = getColorForValue(interval, options);

    // 标签
    const label = document.createElement('div');
    label.className = 'timeline-slot-label';
    label.textContent = getLabel(interval, options);
    slot.appendChild(label);

    return slot;
}
```

### 方案B: 集成到现有表格（当前实现）

**优势**:
- 与现有代码一致
- 学习曲线低

**实现**: 在表格上方添加时间轴预览

---

## CSS样式（从参考文件提取）

```css
/* 时间轴容器 */
.parameter-timeline {
    position: relative;
    height: 100px;
    background: #f3f4f6;
    border-radius: 8px;
    margin-bottom: 15px;
    overflow: hidden;
}

/* 时间标尺 */
.timeline-hours {
    display: flex;
    height: 25px;
    border-bottom: 1px solid #d1d5db;
}

.timeline-hour {
    flex: 1;
    text-align: center;
    font-size: 10px;
    color: #6b7280;
    padding-top: 5px;
    border-right: 1px solid #e5e7eb;
}

/* 时间槽位 */
.timeline-slots {
    position: relative;
    height: 75px;
    padding: 5px;
}

.timeline-slot {
    position: absolute;
    height: 65px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    padding: 0 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.timeline-slot:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.timeline-slot-label {
    font-size: 11px;
    color: white;
    font-weight: 600;
    text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
```

---

## 颜色方案

### VSS速度步骤
```javascript
function getSpeedColor(speed_kmh) {
    if (speed_kmh >= 100) return '#10b981'; // 绿色-高速
    if (speed_kmh >= 80) return '#3b82f6';  // 蓝色-中速
    if (speed_kmh >= 60) return '#f59e0b';  // 橙色-低速
    return '#ef4444';                        // 红色-很慢
}
```

### DHS状态
```javascript
function getDHSColor(status) {
    return status === 'OPEN' ? '#10b981' : '#ef4444';
}
```

### TEC流量
```javascript
function getFlowColor(vehsPerHour) {
    if (vehsPerHour >= 400) return '#ef4444'; // 红色-高流量
    if (vehsPerHour >= 200) return '#f59e0b'; // 橙色-中流量
    return '#10b981';                          // 绿色-低流量
}
```

---

## 集成步骤

### Step 1: 修改 renderStepArrayControl()

```javascript
function renderStepArrayControl(parameterName, paramConfig) {
    const container = document.createElement('div');
    container.className = 'step-array-control-enhanced';
    container.dataset.parameterName = parameterName;

    // 1. 添加时间轴可视化
    const timeline = renderTimeline(parameterName,
        paramConfig.default_value || [],
        { type: 'speed' }
    );
    container.appendChild(timeline);

    // 2. 原有的表格编辑器
    const table = createStepTable(parameterName, paramConfig);
    container.appendChild(table);

    return container;
}
```

### Step 2: 实时更新时间轴

```javascript
function onStepChange(tbody, parameterName) {
    // 收集当前数据
    const steps = collectStepsFromTable(tbody);

    // 更新时间轴
    const timeline = tbody.closest('[data-parameter-name]')
        .querySelector('.parameter-timeline');
    if (timeline) {
        updateTimeline(timeline, steps, { type: 'speed' });
    }
}
```

---

## 用户体验增强

### 1. 交互反馈
- ✅ 鼠标悬停显示详细信息
- ✅ 点击时段定位到对应表格行
- ✅ 拖拽边界调整时间

### 2. 验证提示
- ⚠️ 时间重叠警告（红色边框）
- ⚠️ 时间间隙提示（虚线填充）
- ✅ 24小时覆盖完整性检查

### 3. 快捷操作
- 📋 从时间轴复制时段
- ➕ 双击时间轴添加新时段
- 🗑️ 右键菜单删除时段

---

## 配置选项

```javascript
const timelineOptions = {
    // 基础配置
    height: 100,              // 时间轴高度(px)
    showLabels: true,         // 显示时段标签
    allowOverlap: false,      // 允许时间重叠

    // VSS特定
    speedColors: {
        high: '#10b981',      // >= 100 km/h
        medium: '#3b82f6',    // 80-100 km/h
        low: '#f59e0b',       // 60-80 km/h
        verySlow: '#ef4444'   // < 60 km/h
    },

    // DHS特定
    statusColors: {
        OPEN: '#10b981',
        CLOSED: '#ef4444'
    },

    // TEC特定
    flowColors: {
        high: '#ef4444',      // >= 400 vph
        medium: '#f59e0b',    // 200-400 vph
        low: '#10b981'        // < 200 vph
    }
};
```

---

## 测试用例

### VSS速度步骤
```json
[
  {"time_hours": 0, "speed_kmh": 100},
  {"time_hours": 7, "speed_kmh": 80},
  {"time_hours": 9, "speed_kmh": 100},
  {"time_hours": 17, "speed_kmh": 60},
  {"time_hours": 19, "speed_kmh": 100}
]
```

### DHS时间区间
```json
[
  {"begin_hours": 0, "end_hours": 7, "status": "CLOSED", "allowed_vehicle_types": ["emergency"]},
  {"begin_hours": 7, "end_hours": 9, "status": "OPEN", "allowed_vehicle_types": ["passenger", "truck"]},
  {"begin_hours": 9, "end_hours": 17, "status": "CLOSED", "allowed_vehicle_types": ["emergency"]},
  {"begin_hours": 17, "end_hours": 19, "status": "OPEN", "allowed_vehicle_types": ["passenger", "truck"]},
  {"begin_hours": 19, "end_hours": 24, "status": "CLOSED", "allowed_vehicle_types": ["emergency"]}
]
```

---

## 实现优先级

### P0 (立即实现)
- [x] 静态时间轴渲染
- [x] 颜色编码显示
- [ ] 表格数据变化 → 时间轴更新

### P1 (后续迭代)
- [ ] 点击时段 → 高亮表格行
- [ ] 拖拽调整时间边界
- [ ] 时间冲突检测和提示

### P2 (可选)
- [ ] 导出时间轴为图片
- [ ] 预设模板快速填充
- [ ] 对比模式（多个策略）

---

## 参考资源

- 参考设计: `docs/control_frontend/universal-time-strategy-config.html`
- 当前实现: `frontend/control/js/parameter_form.js`
- 使用位置: `frontend/control/templates.html` (步骤3)

---

## 后续建议

考虑到代码复杂度，建议：

1. **分阶段实施**:
   - 第一阶段：静态时间轴展示 ✅
   - 第二阶段：交互功能
   - 第三阶段：高级特性

2. **保持向后兼容**:
   - 时间轴作为可选增强
   - 表格编辑器保留为主要输入方式

3. **用户反馈**:
   - 先在一个策略类型上试点
   - 收集用户反馈后推广

---

**更新日期**: 2025-10-29
**文档版本**: v1.0
