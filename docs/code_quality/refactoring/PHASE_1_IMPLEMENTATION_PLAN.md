# Phase 1 代码重构实施方案

**创建日期**：2025-10-30
**版本**：1.0
**优先级**：🔴 最高 - 立即执行
**预计周期**：5-7 天（2 个工作周）
**覆盖函数**：2 个（updateConfigSummary、createStrategy）

---

## 📋 Executive Summary

Phase 1 重构专注于处理最复杂和最有问题的 2 个函数：

| 函数 | 行数 | 职责数 | 问题严重程度 | 预期周期 |
|------|------|--------|------------|----------|
| `updateConfigSummary()` | 583 | 7+ | 🔴🔴🔴 | 3-4 天 |
| `createStrategy()` | 229 | 8 | 🔴🔴 | 2-3 天 |

**目标**：将这两个大型函数重构为 15+ 个小型、单一职责的函数，每个函数 <50 行代码。

---

## 🎯 任务 1: `updateConfigSummary()` 重构

### 当前状态分析

**文件**：`frontend/control/templates.html`
**位置**：第 1653-2235 行（虽然标记为 583 行，实际可能包含周边逻辑）
**职责数**：7 个独立职责

#### 职责清单

```
updateConfigSummary() 当前包含以下职责：

1. 更新模板信息摘要
   - 读取 selectedTemplate
   - 创建策略类型徽章
   - 更新 DOM: #summary-template

2. 更新路段信息摘要
   - 计数路段
   - 显示警告信息（无路段时）
   - 更新 DOM: #summary-edges

3. 渲染路段列表
   - 格式化路段显示
   - 生成列表 HTML
   - 更新 DOM: #summary-edge-list

4. 显示参数表单
   - 遍历 parameters_schema
   - 根据参数类型创建不同控件
   - 处理特殊参数类型（step_array, dhs_interval, 等）
   - 绑定参数变化监听器

5. 处理参数值提取
   - 字符串、数字、布尔值处理
   - 特殊车型多选处理
   - JSON 数组解析

6. 管理验证反馈
   - 显示参数验证错误
   - 更新错误样式

7. 处理 UI 样式管理
   - 条件渲染
   - 样式应用
```

### 重构方案

#### 拆分结构

```
updateConfigSummary() [协调函数 - 20 行]
├─ updateTemplateSummary(template) [20 行]
├─ updateEdgeSummary(edges) [15 行]
├─ updateEdgeList(edges) [15 行]
├─ renderParametersSection(container, template) [40 行]
│  ├─ renderParameterControl(param, container) [50 行]
│  │  ├─ createStringControl(param)
│  │  ├─ createNumberControl(param)
│  │  ├─ createSelectControl(param)
│  │  ├─ createStepArrayControl(param) [60 行]
│  │  ├─ createDHSIntervalControl(param) [70 行]
│  │  ├─ createFlowIntervalControl(param) [60 行]
│  │  └─ createVehicleTypeControl(param) [40 行]
│  └─ attachParameterListeners(container, template) [35 行]
└─ displayValidationFeedback(validation) [20 行]
```

#### 实现步骤

##### Step 1: 创建基础子函数 (1 小时)

```javascript
/**
 * 更新模板信息摘要
 * @param {Object} template - 选中的策略模板
 */
function updateTemplateSummary(template) {
  if (!template) return;

  const elem = document.getElementById('summary-template');
  if (!elem) {
    console.warn('[updateTemplateSummary] 元素未找到');
    return;
  }

  const strategyNames = {
    'VSS': '可变限速',
    'DHS': '动态硬路肩',
    'TEC': '收费站管控'
  };

  elem.innerHTML = `
    <strong>${template.template_name}</strong>
    <span class="strategy-badge badge-${template.strategy_type}"
          style="margin-left: 10px; padding: 3px 10px; border-radius: 10px; font-size: 0.85rem;">
      ${strategyNames[template.strategy_type]}
    </span>
  `;
}

/**
 * 更新路段数量摘要
 * @param {Array<string>} edges - 已选择的路段列表
 */
function updateEdgeSummary(edges) {
  const elem = document.getElementById('summary-edges');
  if (!elem) return;

  elem.innerHTML = `<strong style="color: #3498db; font-size: 1.2rem;">${edges.length}</strong> 条路段`;
}

/**
 * 更新路段列表显示
 * @param {Array<string>} edges - 已选择的路段列表
 */
function updateEdgeList(edges) {
  const elem = document.getElementById('summary-edge-list');
  if (!elem) return;

  if (edges.length === 0) {
    elem.innerHTML = '<span style="color: #e74c3c;">⚠️ 警告：未选择任何路段！请返回步骤2选择路段。</span>';
  } else {
    elem.innerHTML = edges.map(edge =>
      `<div style="padding: 3px 0; border-bottom: 1px solid #f0f0f0;">${edge}</div>`
    ).join('');
  }
}
```

**验证清单**：
- [ ] 函数长度 <30 行
- [ ] 单一职责
- [ ] 参数 ≤3 个
- [ ] 有完整的 JSDoc 注释

##### Step 2: 创建参数控件工厂 (2 小时)

```javascript
/**
 * 创建字符串输入控件
 * @param {Object} param - 参数定义
 * @returns {HTMLElement} 输入控件
 */
function createStringControl(param) {
  const container = document.createElement('div');
  container.className = 'param-control-group';

  const label = document.createElement('label');
  label.textContent = param.description;
  label.style.cssText = 'display: block; margin-bottom: 5px; font-weight: 500;';

  const input = document.createElement('input');
  input.id = `param-${param.parameter_name}`;
  input.type = 'text';
  input.placeholder = param.example || '';
  input.style.cssText = 'width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;';

  if (param.required) {
    input.required = true;
    label.textContent += ' <span style="color: red;">*</span>';
  }

  container.appendChild(label);
  container.appendChild(input);

  return container;
}

/**
 * 创建数字输入控件
 * @param {Object} param - 参数定义
 * @returns {HTMLElement} 输入控件
 */
function createNumberControl(param) {
  const container = document.createElement('div');
  container.className = 'param-control-group';

  const label = document.createElement('label');
  label.textContent = param.description;
  label.style.cssText = 'display: block; margin-bottom: 5px; font-weight: 500;';

  const input = document.createElement('input');
  input.id = `param-${param.parameter_name}`;
  input.type = 'number';
  if (param.parameter_type === 'float') {
    input.step = '0.01';
  }
  input.placeholder = param.example || '';
  input.style.cssText = 'width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;';

  if (param.required) {
    input.required = true;
    label.textContent += ' <span style="color: red;">*</span>';
  }

  container.appendChild(label);
  container.appendChild(input);

  return container;
}

/**
 * 创建选择控件（下拉列表）
 * @param {Object} param - 参数定义
 * @returns {HTMLElement} 选择控件
 */
function createSelectControl(param) {
  const container = document.createElement('div');
  container.className = 'param-control-group';

  const label = document.createElement('label');
  label.textContent = param.description;
  label.style.cssText = 'display: block; margin-bottom: 5px; font-weight: 500;';

  const select = document.createElement('select');
  select.id = `param-${param.parameter_name}`;
  select.style.cssText = 'width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;';

  if (!param.required) {
    const emptyOption = document.createElement('option');
    emptyOption.value = '';
    emptyOption.textContent = '--- 请选择 ---';
    select.appendChild(emptyOption);
  }

  // 添加选项
  if (param.options && Array.isArray(param.options)) {
    param.options.forEach(option => {
      const opt = document.createElement('option');
      opt.value = option.value;
      opt.textContent = option.label || option.value;
      select.appendChild(opt);
    });
  }

  if (param.required) {
    select.required = true;
    label.textContent += ' <span style="color: red;">*</span>';
  }

  container.appendChild(label);
  container.appendChild(select);

  return container;
}

/**
 * 创建 Step Array 控件（时间-速度表）
 * @param {Object} param - 参数定义
 * @returns {HTMLElement} 表格控件
 */
function createStepArrayControl(param) {
  const container = document.createElement('div');
  container.className = 'param-control-group';
  container.setAttribute('data-parameter-name', param.parameter_name);

  const label = document.createElement('label');
  label.textContent = param.description;
  label.style.cssText = 'display: block; margin-bottom: 10px; font-weight: 500;';

  const table = document.createElement('table');
  table.style.cssText = 'width: 100%; border-collapse: collapse; border: 1px solid #ddd;';

  // 表头
  const thead = document.createElement('thead');
  thead.innerHTML = `
    <tr style="background: #f5f5f5; border-bottom: 1px solid #ddd;">
      <th style="padding: 8px; text-align: left;">时间(小时)</th>
      <th style="padding: 8px; text-align: left;">速度(km/h)</th>
      <th style="padding: 8px; text-align: center; width: 80px;">操作</th>
    </tr>
  `;
  table.appendChild(thead);

  // 表体
  const tbody = document.createElement('tbody');
  tbody.className = 'steps-tbody';
  table.appendChild(tbody);

  // 添加行按钮
  const addBtn = document.createElement('button');
  addBtn.type = 'button';
  addBtn.textContent = '+ 添加时间段';
  addBtn.style.cssText = 'margin-top: 10px; padding: 6px 12px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer;';
  addBtn.onclick = () => addStepRow(tbody);

  container.appendChild(label);
  container.appendChild(table);
  container.appendChild(addBtn);

  return container;
}

/**
 * 为 Step Array 添加新行
 * @param {HTMLTableSectionElement} tbody - 表体元素
 */
function addStepRow(tbody) {
  const row = document.createElement('tr');
  row.className = 'step-row';
  row.style.borderBottom = '1px solid #ddd';

  row.innerHTML = `
    <td style="padding: 8px;">
      <input type="number" class="step-time" min="0" max="24" step="0.5"
             placeholder="如: 7" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 3px;" />
    </td>
    <td style="padding: 8px;">
      <input type="number" class="step-speed" min="0" step="1"
             placeholder="如: 60" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 3px;" />
    </td>
    <td style="padding: 8px; text-align: center;">
      <button type="button" class="delete-row" style="background: #e74c3c; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">删除</button>
    </td>
  `;

  row.querySelector('.delete-row').onclick = () => row.remove();
  tbody.appendChild(row);
}
```

**验证清单**：
- [ ] 每个函数 <50 行
- [ ] 参数 ≤3 个
- [ ] 返回正确的 HTML 元素
- [ ] 有 JSDoc 注释

##### Step 3: 创建参数容器渲染函数 (1.5 小时)

```javascript
/**
 * 渲染参数表单部分
 * @param {HTMLElement} container - 容器元素
 * @param {Object} template - 策略模板对象
 */
async function renderParametersSection(container, template) {
  if (!template || !template.parameters_schema) {
    console.warn('[renderParametersSection] 模板或参数 schema 缺失');
    return;
  }

  // 清空容器
  container.innerHTML = '';

  // 添加参数标题
  const title = document.createElement('h4');
  title.textContent = '参数配置';
  title.style.cssText = 'margin-bottom: 15px; color: #2c3e50; font-size: 1rem;';
  container.appendChild(title);

  // 创建参数表单
  const form = document.createElement('form');
  form.className = 'parameters-form';
  form.style.cssText = 'display: grid; grid-template-columns: 1fr 1fr; gap: 15px;';

  template.parameters_schema.forEach(param => {
    try {
      const control = renderParameterControl(param);
      form.appendChild(control);
    } catch (error) {
      console.error(`[renderParametersSection] 参数控件创建失败: ${param.parameter_name}`, error);
    }
  });

  container.appendChild(form);

  // 绑定参数变化监听器
  attachParameterListeners(container, template);
}

/**
 * 渲染单个参数控件
 * @param {Object} param - 参数定义
 * @returns {HTMLElement} 参数控件
 */
function renderParameterControl(param) {
  const container = document.createElement('div');
  container.className = 'param-control-wrapper';
  container.setAttribute('data-parameter-name', param.parameter_name);
  container.style.cssText = 'padding: 15px; background: #f8f9fa; border-radius: 6px; border: 1px solid #e9ecef;';

  let control;

  switch (param.parameter_type) {
    case 'string':
      control = createStringControl(param);
      break;
    case 'integer':
    case 'float':
      control = createNumberControl(param);
      break;
    case 'select':
      control = createSelectControl(param);
      break;
    case 'step_array':
      control = createStepArrayControl(param);
      break;
    case 'dhs_interval_array':
      control = createDHSIntervalControl(param);
      break;
    case 'tec_interval_array':
    case 'flow_interval_array':
      control = createFlowIntervalControl(param);
      break;
    case 'array':
      // 特殊处理：车型多选
      if (['applicable_vehicle_types', 'allowed_vehicle_types', 'banned_vehicle_types'].includes(param.parameter_name)) {
        control = createVehicleTypeControl(param);
      } else {
        control = createStringControl(param);
      }
      break;
    default:
      console.warn(`[renderParameterControl] 未知参数类型: ${param.parameter_type}`);
      control = createStringControl(param);
  }

  container.appendChild(control);
  return container;
}

/**
 * 为参数表单绑定变化监听器
 * @param {HTMLElement} container - 参数容器
 * @param {Object} template - 模板对象
 */
function attachParameterListeners(container, template) {
  // 监听参数变化时的验证反馈
  container.addEventListener('change', (event) => {
    const paramWrapper = event.target.closest('[data-parameter-name]');
    if (!paramWrapper) return;

    const paramName = paramWrapper.getAttribute('data-parameter-name');
    const param = template.parameters_schema.find(p => p.parameter_name === paramName);

    if (!param) return;

    try {
      validateParameterValue(event.target, param);
    } catch (error) {
      console.error(`[attachParameterListeners] 验证失败: ${paramName}`, error);
    }
  });
}

/**
 * 验证参数值
 * @param {HTMLElement} input - 输入元素
 * @param {Object} param - 参数定义
 */
function validateParameterValue(input, param) {
  let isValid = true;
  let error = null;

  if (param.required && !input.value) {
    isValid = false;
    error = `${param.description} 是必填项`;
  } else if (param.parameter_type === 'integer') {
    const val = parseInt(input.value);
    if (isNaN(val)) {
      isValid = false;
      error = `${param.description} 必须是整数`;
    }
  } else if (param.parameter_type === 'float') {
    const val = parseFloat(input.value);
    if (isNaN(val)) {
      isValid = false;
      error = `${param.description} 必须是数字`;
    }
  }

  // 更新错误显示
  const wrapper = input.closest('[data-parameter-name]');
  if (wrapper) {
    const errorEl = wrapper.querySelector('.error-message');
    if (errorEl) {
      errorEl.remove();
    }

    if (!isValid) {
      const err = document.createElement('div');
      err.className = 'error-message';
      err.style.cssText = 'color: #e74c3c; font-size: 0.9rem; margin-top: 5px;';
      err.textContent = error;
      wrapper.appendChild(err);
    }
  }

  return isValid;
}
```

**验证清单**：
- [ ] `renderParametersSection()` <50 行
- [ ] `renderParameterControl()` <40 行
- [ ] `attachParameterListeners()` <30 行
- [ ] 正确处理各种参数类型

##### Step 4: 创建协调函数 (30 分钟)

```javascript
/**
 * 更新配置摘要（协调函数）
 * 这是主入口，负责调用各个子函数组织工作流
 */
async function updateConfigSummary() {
  console.log('[updateConfigSummary] Called');

  try {
    // 1. 更新摘要信息（各自独立）
    updateTemplateSummary(selectedTemplate);
    updateEdgeSummary(selectedEdges);
    updateEdgeList(selectedEdges);

    // 2. 渲染参数表单
    const paramsContainer = document.getElementById('params-container');
    if (selectedTemplate && paramsContainer) {
      await renderParametersSection(paramsContainer, selectedTemplate);
    }

    console.log('[updateConfigSummary] Completed successfully');
  } catch (error) {
    console.error('[updateConfigSummary] Error:', error);
    throw error;
  }
}
```

**验证清单**：
- [ ] 函数 <30 行
- [ ] 清晰的职责划分
- [ ] 正确的错误处理

---

## 🎯 任务 2: `createStrategy()` 重构

### 当前状态分析

**文件**：`frontend/control/templates.html`
**位置**：第 2918-3147 行（229 行）
**职责数**：8 个独立职责

#### 职责清单

```
createStrategy() 当前包含以下职责：

1. 验证策略名称
   - 检查是否为空
   - 显示警告

2. 验证模板选择
   - 检查 selectedTemplate 是否存在

3. 收集参数值
   - 遍历 parameters_schema
   - 从 DOM 提取各类参数值
   - 处理特殊参数（affected_edges, step_array, 等）

4. 提取参数值的多种类型
   - 字符串、数字、布尔值
   - step_array 表格提取
   - dhs_interval_array 提取
   - tec_interval_array / flow_interval_array 提取
   - 车型多选处理

5. 验证参数完整性
   - 检查必填参数

6. 构建 API Payload
   - 组合 strategy_name, template_id, parameters, affected_edges

7. 调用 API 创建策略
   - fetch POST 请求
   - 错误处理

8. 处理 API 响应和 UI 更新
   - 显示成功/失败提示
   - 刷新策略列表
   - 重置表单
```

### 重构方案

#### 拆分结构

```
createStrategy() [协调函数 - 30 行]
├─ validateStrategyInput() [20 行]
├─ collectStrategyParameters() [40 行]
│  ├─ collectRegularParameters(template)
│  ├─ collectStepArrayParameter(param)
│  ├─ collectDHSIntervalParameter(param)
│  ├─ collectFlowIntervalParameter(param)
│  └─ collectParameterValue(param)
├─ validateStrategyParameters(params, template) [30 行]
├─ buildStrategyPayload(name, params) [15 行]
├─ submitStrategyAPI(payload) [25 行]
├─ handleStrategyCreated(response) [15 行]
├─ refreshStrategyList() [10 行]
└─ showStrategyError(error) [15 行]
```

#### 实现步骤

##### Step 1: 创建输入验证函数 (1 小时)

```javascript
/**
 * 验证策略创建的输入条件
 * @throws {Error} 如果验证失败
 */
function validateStrategyInput() {
  // 验证模板选择
  if (!selectedTemplate) {
    throw new Error('请先选择策略模板');
  }

  // 验证路段选择
  if (!selectedEdges || selectedEdges.length === 0) {
    throw new Error('请选择至少一条路段');
  }

  // 验证策略名称
  const nameInput = document.getElementById('param-strategy-name');
  if (!nameInput || !nameInput.value) {
    throw new Error('请输入策略名称');
  }

  return nameInput.value;
}

/**
 * 收集策略的所有参数
 * @returns {Object} 参数对象
 */
function collectStrategyParameters() {
  const parameters = {};

  selectedTemplate.parameters_schema.forEach(param => {
    const value = collectParameterValue(param);
    if (value !== undefined) {
      parameters[param.parameter_name] = value;
    }
  });

  console.log('[collectStrategyParameters] Collected:', parameters);
  return parameters;
}

/**
 * 收集单个参数的值
 * @param {Object} param - 参数定义
 * @returns {*} 参数值，如果不需要则返回 undefined
 */
function collectParameterValue(param) {
  // 特殊参数：affected_edges 使用已选路段
  if (param.parameter_name === 'affected_edges' ||
      param.parameter_name === 'affected_segments' ||
      param.parameter_name === 'entrance_ids') {
    return selectedEdges;
  }

  // 特殊参数：step_array
  if (param.parameter_type === 'step_array') {
    return collectStepArrayParameter(param);
  }

  // 特殊参数：dhs_interval_array
  if (param.parameter_type === 'dhs_interval_array') {
    return collectDHSIntervalParameter(param);
  }

  // 特殊参数：tec_interval_array / flow_interval_array
  if (param.parameter_type === 'tec_interval_array' || param.parameter_type === 'flow_interval_array') {
    return collectFlowIntervalParameter(param);
  }

  // 普通参数：从输入元素获取
  const input = document.getElementById(`param-${param.parameter_name}`);
  if (!input) {
    if (param.required) {
      throw new Error(`找不到参数输入框: ${param.description}`);
    }
    return undefined;
  }

  let value = input.value;

  // 如果是可选参数且为空，跳过
  if (!param.required && (value === '' || value === null || value === undefined)) {
    return undefined;
  }

  // 类型转换
  if (param.parameter_type === 'integer') {
    value = parseInt(value);
    if (isNaN(value)) {
      throw new Error(`参数 "${param.description}" 必须是整数`);
    }
  } else if (param.parameter_type === 'float') {
    value = parseFloat(value);
    if (isNaN(value)) {
      throw new Error(`参数 "${param.description}" 必须是数字`);
    }
  } else if (param.parameter_type === 'boolean') {
    value = value === 'true';
  } else if (param.parameter_type === 'array') {
    // 车型多选
    if (['applicable_vehicle_types', 'allowed_vehicle_types', 'banned_vehicle_types'].includes(param.parameter_name)) {
      value = Array.from(input.selectedOptions).map(opt => opt.value);
      if (!param.required && value.length === 0) {
        return undefined;
      }
    } else {
      // JSON 数组解析
      try {
        value = JSON.parse(value);
        if (!Array.isArray(value)) {
          throw new Error('必须是数组格式');
        }
      } catch (error) {
        throw new Error(`参数 "${param.description}" 格式错误：${error.message}`);
      }
    }
  }

  return value;
}

/**
 * 收集 Step Array 参数（如时间-速度对）
 * @param {Object} param - 参数定义
 * @returns {Array} 步骤数组
 */
function collectStepArrayParameter(param) {
  const tbody = document.querySelector(`[data-parameter-name="${param.parameter_name}"] .steps-tbody`);

  if (!tbody) {
    if (param.required) {
      throw new Error(`找不到 ${param.description} 的表格`);
    }
    return undefined;
  }

  const rows = tbody.querySelectorAll('.step-row');

  // 可选参数且无行数据，跳过
  if (!param.required && rows.length === 0) {
    console.log(`[collectStepArrayParameter] 跳过可选参数（无数据）: ${param.parameter_name}`);
    return undefined;
  }

  if (param.required && rows.length === 0) {
    throw new Error(`${param.description} 至少需要一个时间段`);
  }

  return Array.from(rows).map(row => ({
    time_hours: parseFloat(row.querySelector('.step-time').value),
    speed_kmh: parseFloat(row.querySelector('.step-speed').value)
  }));
}

/**
 * 收集 DHS Interval Array 参数
 * @param {Object} param - 参数定义
 * @returns {Array} DHS 间隔数组
 */
function collectDHSIntervalParameter(param) {
  let tbody = document.querySelector(`[data-parameter-name="${param.parameter_name}"] .dhs-intervals-tbody`);
  if (!tbody) {
    tbody = document.querySelector(`.dhs-intervals-tbody[data-parameter-name="${param.parameter_name}"]`);
  }

  if (!tbody) {
    if (param.required) {
      throw new Error(`找不到 ${param.description} 的表格`);
    }
    return undefined;
  }

  const rows = tbody.querySelectorAll('.dhs-interval-row');

  if (!param.required && rows.length === 0) {
    console.log(`[collectDHSIntervalParameter] 跳过可选参数（无数据）: ${param.parameter_name}`);
    return undefined;
  }

  if (param.required && rows.length === 0) {
    throw new Error(`${param.description} 至少需要一个间隔`);
  }

  return Array.from(rows).map(row => {
    const vehiclesSelect = row.querySelector('.dhs-interval-vehicles');
    const selectedOptions = Array.from(vehiclesSelect.selectedOptions).map(opt => opt.value);

    return {
      begin_hours: parseFloat(row.querySelector('.dhs-interval-begin').value),
      end_hours: parseFloat(row.querySelector('.dhs-interval-end').value),
      status: row.querySelector('.dhs-interval-status').value,
      allowed_vehicle_types: selectedOptions
    };
  });
}

/**
 * 收集流量间隔参数（TEC / Flow）
 * @param {Object} param - 参数定义
 * @returns {Array} 流量间隔数组
 */
function collectFlowIntervalParameter(param) {
  const tbody = document.querySelector(`[data-parameter-name="${param.parameter_name}"] .intervals-tbody`);

  if (!tbody) {
    if (param.required) {
      throw new Error(`找不到 ${param.description} 的表格`);
    }
    return undefined;
  }

  const rows = tbody.querySelectorAll('.interval-row');

  if (!param.required && rows.length === 0) {
    console.log(`[collectFlowIntervalParameter] 跳过可选参数（无数据）: ${param.parameter_name}`);
    return undefined;
  }

  if (param.required && rows.length === 0) {
    throw new Error(`${param.description} 至少需要一个间隔`);
  }

  return Array.from(rows).map(row => ({
    begin_hours: parseFloat(row.querySelector('.interval-begin').value),
    end_hours: parseFloat(row.querySelector('.interval-end').value),
    vehsPerHour: parseFloat(row.querySelector('.interval-flow').value),
    target_speed: parseFloat(row.querySelector('.interval-speed').value)
  }));
}
```

**验证清单**：
- [ ] 每个函数 <50 行
- [ ] 完整的错误信息
- [ ] 正确的参数收集逻辑

##### Step 2: 创建验证和 API 函数 (1 小时)

```javascript
/**
 * 验证策略参数的完整性和有效性
 * @param {Object} parameters - 收集的参数
 * @param {Object} template - 策略模板
 * @throws {Error} 如果验证失败
 */
function validateStrategyParameters(parameters, template) {
  const errors = [];

  template.parameters_schema.forEach(param => {
    // 检查必填参数
    if (param.required) {
      const value = parameters[param.parameter_name];
      if (value === undefined || value === null || value === '') {
        errors.push(`${param.description} 是必填项`);
      }
    }
  });

  if (errors.length > 0) {
    throw new Error(errors.join('\n'));
  }
}

/**
 * 构建策略 API Payload
 * @param {string} strategyName - 策略名称
 * @param {Object} parameters - 策略参数
 * @returns {Object} API payload
 */
function buildStrategyPayload(strategyName, parameters) {
  return {
    strategy_name: strategyName,
    template_id: selectedTemplate.template_id,
    parameters: parameters,
    affected_edges: selectedEdges
  };
}

/**
 * 提交策略创建请求到后端 API
 * @param {Object} payload - API payload
 * @returns {Promise<Object>} API 响应
 * @throws {Error} 如果 API 调用失败
 */
async function submitStrategyAPI(payload) {
  console.log('[submitStrategyAPI] 提交 payload:', payload);

  const response = await fetch('/api/v1/control/strategy-instances/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return await response.json();
}

/**
 * 处理策略创建成功
 * @param {Object} response - API 响应
 */
function handleStrategyCreated(response) {
  console.log('[handleStrategyCreated] 策略创建成功:', response);

  // 显示成功消息
  alert(`策略创建成功！\n策略ID: ${response.strategy_id}`);
}

/**
 * 刷新策略实例列表
 * @returns {Promise<void>}
 */
async function refreshStrategyList() {
  try {
    await fetchStrategyInstances();
  } catch (error) {
    console.error('[refreshStrategyList] 刷新列表失败:', error);
  }
}

/**
 * 显示策略创建错误
 * @param {Error} error - 错误对象
 */
function showStrategyError(error) {
  console.error('[showStrategyError] 错误:', error);
  alert(`创建策略失败: ${error.message}`);
}
```

**验证清单**：
- [ ] 每个函数 <30 行
- [ ] 正确的错误处理
- [ ] 清晰的职责划分

##### Step 3: 创建协调函数 (30 分钟)

```javascript
/**
 * 创建策略（协调函数）
 * 这是主入口，负责协调整个策略创建流程
 */
async function createStrategy() {
  try {
    // 1. 验证输入
    const strategyName = validateStrategyInput();

    // 2. 收集参数
    const parameters = collectStrategyParameters();

    // 3. 验证参数
    validateStrategyParameters(parameters, selectedTemplate);

    // 4. 构建 payload
    const payload = buildStrategyPayload(strategyName, parameters);

    // 5. 提交 API
    const response = await submitStrategyAPI(payload);

    // 6. 处理响应
    handleStrategyCreated(response);

    // 7. 刷新列表
    await refreshStrategyList();

    // 8. 重置表单
    resetForm();

  } catch (error) {
    showStrategyError(error);
  }
}
```

**验证清单**：
- [ ] 函数 <30 行
- [ ] 清晰的流程
- [ ] 完整的错误处理

---

## 📊 Implementation Timeline

### Week 1

**Monday (3-4 小时)**：
- [ ] 分析 updateConfigSummary() 所有职责
- [ ] 设计拆分方案
- [ ] 创建 4 个基础子函数
- [ ] 编写初始单元测试

**Tuesday (3-4 小时)**：
- [ ] 实现参数控件工厂
- [ ] 测试各个控件创建
- [ ] 集成到 renderParametersSection()

**Wednesday (3 小时)**：
- [ ] 完成 updateConfigSummary() 协调函数
- [ ] 集成测试
- [ ] 代码审查

**Thursday-Friday (5-6 小时)**：
- [ ] 分析 createStrategy() 职责
- [ ] 实现 9 个新函数
- [ ] 编写单元测试
- [ ] 集成测试和代码审查

### Week 2

**继续进行**：
- [ ] 修复测试失败
- [ ] 代码优化
- [ ] 文档完善
- [ ] 最终验证

---

## 🧪 Testing Strategy

### 单元测试

每个函数都应有对应的单元测试。使用 Mocha + Chai 或类似框架。

**示例测试套件**：

```javascript
describe('updateTemplateSummary', () => {
  beforeEach(() => {
    // 创建测试 DOM 环境
    document.body.innerHTML = '<div id="summary-template"></div>';
  });

  it('应该更新模板信息', () => {
    const template = {
      template_name: 'Test Template',
      strategy_type: 'VSS'
    };

    updateTemplateSummary(template);

    const elem = document.getElementById('summary-template');
    expect(elem.textContent).to.include('Test Template');
    expect(elem.textContent).to.include('可变限速');
  });

  it('应该处理缺失元素', () => {
    document.body.innerHTML = '';
    expect(() => updateTemplateSummary({template_name: 'Test'})).not.to.throw();
  });
});

describe('collectStrategyParameters', () => {
  it('应该从 DOM 收集参数', () => {
    // 模拟 DOM
    document.body.innerHTML = `
      <input id="param-strategy-name" value="Test Strategy" />
      <input id="param-speed_limit" value="60" />
    `;

    selectedTemplate = {
      parameters_schema: [
        { parameter_name: 'strategy_name', parameter_type: 'string', required: true },
        { parameter_name: 'speed_limit', parameter_type: 'integer', required: false }
      ]
    };

    const params = collectStrategyParameters();

    expect(params.strategy_name).to.equal('Test Strategy');
    expect(params.speed_limit).to.equal(60);
  });
});
```

### 集成测试

测试重构后的函数是否能保持原有功能。

**示例集成测试**：

```javascript
describe('updateConfigSummary 集成', () => {
  it('应该正确更新所有摘要信息', async () => {
    // 设置全局状态
    selectedTemplate = { /* template data */ };
    selectedEdges = ['edge1', 'edge2'];

    // 创建 DOM
    document.body.innerHTML = `
      <div id="summary-template"></div>
      <div id="summary-edges"></div>
      <div id="summary-edge-list"></div>
      <div id="params-container"></div>
    `;

    // 调用
    await updateConfigSummary();

    // 验证
    expect(document.getElementById('summary-edges').textContent).to.include('2');
    expect(document.getElementById('summary-edge-list').children.length).to.equal(2);
  });
});
```

---

## ✅ Validation Checklist

### 函数质量检查

- [ ] **代码行数**：<50 行（协调函数 <100 行）
- [ ] **参数个数**：≤5 个
- [ ] **圈复杂度**：<8
- [ ] **职责数**：1 个（单一职责原则）
- [ ] **嵌套深度**：<3 层
- [ ] **JSDoc 注释**：完整

### 测试覆盖检查

- [ ] **单元测试**：每个函数覆盖
- [ ] **边界测试**：空值、异常情况
- [ ] **集成测试**：验证整体功能
- [ ] **覆盖率**：>90%

### 功能验证检查

- [ ] **原有功能不变**：所有功能正常工作
- [ ] **错误处理**：正确捕获和处理错误
- [ ] **用户体验**：UI/UX 没有退化
- [ ] **性能**：没有性能下降

### 代码审查检查

- [ ] **代码风格**：遵循项目规范
- [ ] **命名规范**：清晰的函数/变量名
- [ ] **文档完善**：有足够的注释
- [ ] **可维护性**：易于理解和修改

---

## 📝 Deliverables

### 代码改动

1. **修改文件**：`frontend/control/templates.html`
2. **新增函数**：18 个（2 个协调函数 + 16 个子函数）
3. **代码行数变化**：
   - 删除：约 800 行（原始两个函数）
   - 新增：约 600 行（重构后的函数）
   - 净减少：约 200 行（包括注释和空行优化）

### 测试代码

1. **单元测试**：18 个测试套件，≥50 个测试用例
2. **集成测试**：2 个完整流程测试
3. **测试覆盖率**：>90%

### 文档

1. **实施说明**：本文档
2. **代码注释**：JSDoc 风格的完整注释
3. **变更日志**：记录所有改动

---

## 🚀 Success Criteria

✅ **Phase 1 成功的标志**：

- [ ] 所有 18 个新函数代码行数 <50 行
- [ ] 所有函数都有完整的 JSDoc 注释
- [ ] 单元测试覆盖率 ≥90%
- [ ] 所有测试通过（Unit + Integration）
- [ ] 代码审查批准无异议
- [ ] 原有功能 100% 保持
- [ ] 性能无下降

---

## 📞 Support & Escalation

### 遇到问题？

1. **查看分析文档**：`FUNCTION_REFACTORING_ANALYSIS.md`
2. **参考示例代码**：`REFACTORING_EXAMPLES.md`
3. **快速指南**：`REFACTORING_QUICK_GUIDE.md`

### 需要帮助？

- 代码审查讨论最佳实践
- 测试策略讨论
- 集成问题排查

---

**版本**：1.0
**创建日期**：2025-10-30
**预计完成日期**：2025-11-07（5-7 个工作日）

---

**准备好开始吗？** 💪 让我们从 `updateConfigSummary()` 开始！
