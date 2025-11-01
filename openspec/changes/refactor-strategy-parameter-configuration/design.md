# 设计文档：策略参数配置前端重构

## 架构概览

本重构针对策略创建工作流的第3步（参数配置），涉及前端代码结构、CSS 组织、数据流和交互逻辑。

## 核心设计决策

### 1. 代码模块化策略

**问题**：`parameter_form.js` 2258 行，职责混乱

**决策**：保持单文件，但按职责分区

**理由**：
- 完全拆分为多文件需要重构所有引用，风险高
- 按注释分区可以快速定位功能
- 未来可以逐步抽取为模块

**新结构**：
```javascript
// ==================== 工具函数 ====================
// debounce, validateTimeOrder, validateRange...

// ==================== 模板数据加载 ====================
// initializeDefaultValues, loadParameterDefaults...

// ==================== 时间轴可视化 ====================
// updateTimeline (统一函数，替代4个重复函数)

// ==================== 参数控件渲染 ====================
// renderStepArrayControl, renderIntervalControl (参数化)

// ==================== 行操作 ====================
// addRow (统一函数，替代3个重复函数)
// deleteRow, confirmDelete...

// ==================== 表单生成 ====================
// generateFormFromTemplate, generateVehicleTypeControl...

// ==================== 验证与提交 ====================
// validateForm, extractFormParameters, submitStrategy...
```

### 2. 时间轴更新函数合并

**问题**：4 个几乎相同的函数（`updateTimelineFromTable`, `updateDHSTimelineFromTable` 等）

**决策**：单一参数化函数 + 预设配置

**策略类型差异**（详见 `TIMELINE_CLARIFICATION.md`）：
- **VSS**: 时刻点 (`time_hours`) → 段状可视化
- **DHS**: 时间段 (`begin_hours`, `end_hours`, `status`) → 段状可视化
- **TEC**: 时间段 + 开关状态（本次）或流量（未来扩展）

**新设计**：
```javascript
// 统一更新函数
function updateTimeline(tbody, config = {}) {
    const {
        useInterval = false,     // true: 时段模式, false: 时刻模式
        timeField = 'time_hours',
        beginField = 'begin_hours',
        endField = 'end_hours',
        valueField = 'speed_kmh',
        rowSelector = '.step-row',
        timeSelector = '.step-time',
        beginSelector = '.interval-begin',
        endSelector = '.interval-end',
        valueSelector = '.step-speed',
        visualizationType = 'speed'
    } = config;

    // 提取数据逻辑
    const data = useInterval
        ? extractIntervalData(tbody, {beginField, endField, valueField, ...})
        : extractStepData(tbody, {timeField, valueField, ...});

    // 调用已有的 TimelineVisualizer
    window.TimelineVisualizer.updateTimeline(timeline, data, {
        type: visualizationType
    });
}

// 预设配置
const TIMELINE_CONFIGS = {
    vss: { useInterval: false, visualizationType: 'speed' },
    dhs: { useInterval: true, valueField: 'status', visualizationType: 'dhs' },
    tec_simple: { useInterval: true, visualizationType: 'simple_interval' }
};

// 简化调用
updateTimelineByType(tbody, 'vss');
updateTimelineByType(tbody, 'dhs');
```

**保持不变**：`TimelineVisualizer.updateTimeline()` 已有良好设计，无需修改

**未来扩展**：
- TEC 流量控制（时段 + 流量值）
- VSS + DHS 双层时间轴叠加显示

### 3. 行添加函数合并

**问题**：3 个重复函数（`addDHSIntervalRow`, `addFlowIntervalRow`, `addTECIntervalRow`）

**决策**：单一配置驱动函数

**新设计**：
```javascript
function addRow(tbody, config) {
    const {
        paramName,
        rowType, // 'step' | 'interval-dhs' | 'interval-flow' | 'interval-tec'
        data = {},
        schema = {}
    } = config;

    const row = document.createElement('tr');
    row.className = `${rowType}-row`;

    // 根据 rowType 决定列结构
    const columns = getColumnsForRowType(rowType, schema);
    columns.forEach(col => {
        const cell = createCell(col, data[col.field], schema);
        row.appendChild(cell);
    });

    // 添加操作列
    const actionsCell = createActionsCell(rowType);
    row.appendChild(actionsCell);

    tbody.appendChild(row);
    updateTimeline(tbody, getTimelineConfigForRowType(rowType));
}
```

### 4. CSS 架构

**问题**：样式分散，布局不一致

**决策**：使用 CSS 变量 + 统一组件类

**新 CSS 结构**：
```css
/* variables.css - 已存在 */
:root {
    --form-spacing-sm: 8px;
    --form-spacing-md: 16px;
    --form-spacing-lg: 24px;
    --input-width-full: 100%;
    --input-width-medium: 300px;
    --button-width-auto: auto;
    --button-min-width: 120px;
}

/* templates-forms.css - 扩展 */
.form-group {
    margin-bottom: var(--form-spacing-md);
}

.form-group .flex-start {
    display: flex;
    gap: var(--form-spacing-sm);
    align-items: flex-start;
}

.form-group .flex-start input.flex-1,
.form-group .flex-start textarea.flex-1 {
    flex: 1;
    min-width: 0; /* 防止flex溢出 */
}

.form-group .flex-start button {
    flex-shrink: 0;
    min-width: var(--button-min-width);
}

/* 响应式设计 */
@media (max-width: 768px) {
    .form-group .flex-start {
        flex-direction: column;
    }

    .form-group .flex-start button {
        width: 100%;
    }
}
```

### 5. 模板默认值加载流程

**问题**：表单打开时是空的，未加载模板默认值

**决策**：在表单生成时同步加载默认值

**新流程**：
```javascript
function generateFormFromTemplate(template) {
    // 1. 创建基础表单结构
    // 2. 遍历 parameters_schema
    template.parameters_schema.forEach(param => {
        const group = createParameterGroup(param);

        // 3. 从 schema.default_value 初始化值
        if (param.default_value !== null && param.default_value !== undefined) {
            initializeParameterValue(group, param.default_value, param.parameter_type);
        }

        form.appendChild(group);
    });
}

function initializeParameterValue(group, defaultValue, paramType) {
    switch(paramType) {
        case 'number':
        case 'string':
        case 'enum':
            // 直接设置 input.value
            const input = group.querySelector('input, select, textarea');
            input.value = defaultValue;
            break;

        case 'step_array':
            // 填充表格
            const tbody = group.querySelector('tbody');
            defaultValue.forEach(step => {
                addRow(tbody, {
                    rowType: 'step',
                    data: step
                });
            });
            break;

        case 'interval_array':
            // 类似处理
            break;
    }
}
```

### 6. 时间语义明确化

**问题**：VSS 用时刻，TEC/DHS 用时段，UI 无区分

**决策**：在 UI 标签和数据结构中明确区分

**实现**：
```javascript
// VSS: 时刻表示
const vssConfig = {
    columnLabels: ['时间(小时)', '限速(km/h)'],
    fields: ['time_hours', 'speed_kmh'],
    rowType: 'step',
    timelineType: 'point'  // 点状标记
};

// TEC/DHS: 时段表示
const dhsConfig = {
    columnLabels: ['开始时间(小时)', '结束时间(小时)', '状态'],
    fields: ['begin_hours', 'end_hours', 'status'],
    rowType: 'interval-dhs',
    timelineType: 'segment'  // 段状着色
};

function renderParameterControl(param, config) {
    // 根据 config 动态生成表头和列
    const thead = createTableHeader(config.columnLabels);
    // ...
}
```

### 7. 车型配置分离

**问题**：车型混在 DHS/TEC 间隔表中

**决策**：全局车型配置区域 + 移除表格中的车型列

**新 UI 结构**：
```html
<!-- Step 3: 配置参数 -->
<div id="params-form">
    <!-- 策略名称/描述 -->
    <div class="form-group">...</div>

    <!-- 时间-速度步骤 (无车型) -->
    <div class="form-group" data-parameter-name="speed_steps">
        <table>
            <thead>
                <tr>
                    <th>时间(小时)</th>
                    <th>限速(km/h)</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>...</tbody>
        </table>
    </div>

    <!-- [单独区域] 车型配置 -->
    <div class="form-group vehicle-type-config">
        <label id="vehicle-type-label">允许的车型</label>
        <div class="vehicle-checkboxes">
            <label><input type="checkbox" name="vehicle_types" value="passenger"> 小客车</label>
            <label><input type="checkbox" name="vehicle_types" value="truck"> 货车</label>
            <!-- ... -->
        </div>
        <span class="form-hint" id="vehicle-type-hint">仅这些车型可使用此策略</span>
    </div>
</div>
```

**逻辑**：
```javascript
// 动态生成车型配置区域
function generateVehicleTypeControl(template) {
    const allowParam = template.parameters_schema.find(
        p => p.parameter_name === 'allowed_vehicle_types'
    );
    const disallowParam = template.parameters_schema.find(
        p => p.parameter_name === 'disallow_vehicle_types'
    );

    if (!allowParam && !disallowParam) return null;

    const isAllowMode = !!allowParam;
    const param = isAllowMode ? allowParam : disallowParam;

    // 动态标签和提示
    const labelText = isAllowMode ? '允许的车型' : '禁止的车型';
    const hintText = isAllowMode
        ? '仅这些车型可使用此策略'
        : '这些车型禁止使用此策略';

    // 生成复选框组
    const vehicleTypes = param.enum_values || [
        { value: 'passenger', label: '小客车' },
        { value: 'truck', label: '货车' },
        // ...
    ];

    // 返回 DOM 元素
    return createVehicleCheckboxGroup(labelText, hintText, vehicleTypes, param.default_value);
}
```

### 8. 路段数据来源统一

**问题**：Step 2 和 Step 3 都有路段输入

**决策**：Step 3 显示 Step 2 的只读列表，移除旧输入框

**数据流**：
```javascript
// Step 2 完成时
const selectedEdges = window.EdgeSelector.getSelectedEdges();
sessionStorage.setItem('strategy_selected_edges', JSON.stringify(selectedEdges));

// Step 3 加载时
const selectedEdges = JSON.parse(sessionStorage.getItem('strategy_selected_edges') || '[]');

// 显示只读表格
function renderSelectedEdgesSummary(edges) {
    const table = createTable(['Edge ID', '路线', '路段代码', '桩号', '方向']);
    edges.forEach(edge => {
        const row = createRow([
            edge.edge_id,
            edge.route_code,
            edge.road_code,
            `K${edge.start_km} - K${edge.end_km}`,
            edge.direction
        ]);
        table.appendChild(row);
    });
    return table;
}

// 移除旧的 affected_edges 输入框
// 在 generateFormFromTemplate 中跳过
if (param.parameter_name === 'affected_edges' ||
    param.parameter_name === 'affected_segments') {
    return; // 不生成输入框
}
```

### 9. 验证策略

**问题**：验证逻辑分散，提示不清

**决策**：统一验证器 + 清晰错误提示

**新设计**：
```javascript
const validators = {
    timeOrder: (beginHours, endHours) => {
        if (beginHours >= endHours) {
            return {
                valid: false,
                message: `开始时间(${beginHours}h)必须小于结束时间(${endHours}h)`
            };
        }
        return { valid: true };
    },

    timeRange: (hours) => {
        if (hours < 0 || hours > 24) {
            return {
                valid: false,
                message: `时间必须在 0-24 小时范围内，当前值: ${hours}`
            };
        }
        return { valid: true };
    },

    speedRange: (speed, min = 0, max = 120) => {
        if (speed < min || speed > max) {
            return {
                valid: false,
                message: `速度必须在 ${min}-${max} km/h 范围内，当前值: ${speed}`
            };
        }
        return { valid: true };
    }
};

// 使用
function addRow(tbody, config) {
    // ...

    // 绑定验证
    const beginInput = row.querySelector('.interval-begin');
    const endInput = row.querySelector('.interval-end');

    endInput.addEventListener('blur', () => {
        const result = validators.timeOrder(
            parseFloat(beginInput.value),
            parseFloat(endInput.value)
        );

        if (!result.valid) {
            showError(endInput, result.message);
        } else {
            clearError(endInput);
        }
    });
}
```

### 10. Hint 文本管理

**问题**：参数级和控制级 Hint 重复

**决策**：分层 Hint，避免重复

**新策略**：
```javascript
// 参数级 Hint（从 schema 生成，紧凑）
function generateParameterHint(param) {
    const parts = [];

    if (param.unit) parts.push(param.unit);
    if (param.min_value !== null && param.max_value !== null) {
        parts.push(`范围: ${param.min_value}-${param.max_value}`);
    }
    if (param.required) parts.push('必填');

    return parts.join(' · ');  // 例："km/h · 范围: 0-120 · 必填"
}

// 控制级 Hint（仅操作说明，简洁）
const controlHints = {
    stepArray: "点击「添加步骤」增加新行，时间轴自动更新",
    intervalArray: "点击「添加区间」增加新行，必须覆盖完整24小时"
};

// 避免双重显示
// 如果参数有 schema.description，优先使用它
// 如果没有，使用 controlHints
```

## 性能考虑

1. **防抖时间轴更新**：已实现 300ms 防抖
2. **虚拟滚动**：暂不实现（路段表格预计 <100 行）
3. **懒加载图表**：时间轴仅在可见时绘制
4. **缓存 DOM 查询**：在事件处理中缓存常用元素

## 测试策略

1. **单元测试**：验证器函数、数据转换函数
2. **集成测试**：表单生成、默认值加载
3. **E2E 测试**：
   - 创建 VSS 策略（时刻表示）
   - 创建 DHS 策略（时段表示）
   - 创建 TEC 策略（时段表示）
   - 验证车型配置逻辑
   - 验证路段显示

## 向后兼容

- 旧策略实例数据结构不变
- 新 UI 能正确解析旧数据
- 时间语义变化仅影响新建策略
- 代码重构不改变外部 API

## 未来扩展

1. **拖拽重排**：DHS 路段顺序调整
2. **图形化编辑器**：可视化时间轴拖拽
3. **参数预设**：常用参数组合保存
4. **导入导出**：JSON 格式参数导入
