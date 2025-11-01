# 参数表单架构文档

## 概述

本文档描述OD_SIM控制策略前端参数表单的架构设计，包括渲染系统、数据流和已知问题。

**更新日期**: 2025-11-01
**版本**: v0.9.1-dev

---

## 架构概览

### 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                     模板 JSON 文件                            │
│  (templates/control_strategies/{type}/{template_id}.json)   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              参数表单渲染系统（双系统并存）                     │
├─────────────────────────────────────────────────────────────┤
│  系统1: templates.html:820 (主渲染循环)                      │
│  系统2: templates.html:1531 (renderParametersSection)       │
│                                                              │
│  → 调用 parameter_form.js 中的渲染函数                        │
│  → 生成 DOM 元素和控件                                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   用户交互界面                                │
│  (输入框、下拉框、复选框、时间轴等)                             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│               数据收集和验证                                   │
│  collectParameterValues() + validateStrategyParameters()    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                提交到后端 API                                 │
│  POST /api/v1/control/strategies/instances                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 参数类型和渲染函数映射

| 参数类型 | 渲染函数 | 文件位置 | 说明 |
|---------|---------|---------|------|
| `string` | 内联HTML | templates.html:858-869 | 文本输入框或下拉框 |
| `integer`, `float` | 内联HTML | templates.html:846-842 | 数字输入框 |
| `boolean` | 内联HTML | templates.html:871-876 | 是/否下拉框 |
| `enum` | 内联HTML | templates.html:843-857 | 下拉框 |
| `enum_array` | 内联HTML + `renderEnumArrayControl` | templates.html:886-935 | 复选框组 |
| `step_array` | `renderStepArrayControl()` | parameter_form.js:696 | VSS限速步骤表 |
| `dhs_interval_array` | `renderDHSIntervalControl()` | parameter_form.js:1221 | DHS时间区间表 |
| `flow_interval_array` | `renderFlowIntervalControl()` | parameter_form.js:1423 | TEC/Flow流量区间表 |
| `tec_interval_array` | `renderTECIntervalControl()` | parameter_form.js:1616 | TEC时间区间表 |

---

## 特殊处理逻辑

### 1. TEC车型限制统一控件

**问题**: TEC车型限制模板有 `restriction_mode`（禁止/允许模式），但模板定义了两个独立的车型参数：
- `disallow_vehicle_types` - 禁止模式时使用
- `allowed_vehicle_types` - 允许模式时使用

**解决方案**: 统一车型控件 (`renderUnifiedVehicleTypeControl`)

**实现位置**:
- 函数定义: `parameter_form.js:2576`
- 注入点1: `templates.html:971-988` (系统1)
- 注入点2: `templates.html:1546-1563` (系统2)

**工作流程**:
```javascript
1. 检测模板中是否存在 restriction_mode 参数
2. 如果存在，跳过渲染 disallow_vehicle_types 和 allowed_vehicle_types
3. 在 restriction_mode 渲染后，注入统一控件
4. 绑定 change 事件，当模式切换时更新控件标签和提示
5. 数据收集时，根据当前模式读取统一控件值并映射到对应参数
```

**代码示例**:
```javascript
// 检测 restriction_mode
const hasRestrictionMode = template.parameters_schema.some(
  p => p.parameter_name === 'restriction_mode'
);

// 跳过独立车型参数
if (hasRestrictionMode &&
    (param.parameter_name === 'disallow_vehicle_types' ||
     param.parameter_name === 'allowed_vehicle_types')) {
  return; // 不渲染
}

// 注入统一控件
if (hasRestrictionMode && param.parameter_name === 'restriction_mode') {
  const unifiedControl = window.renderUnifiedVehicleTypeControl(template);
  form.appendChild(unifiedControl);
}
```

### 2. enum_name 引用处理

**问题**: 某些模板使用 `enum_name` 引用外部枚举定义，而不是直接定义 `enum_values`。

**示例**:
```json
{
  "parameter_name": "disallow_vehicle_types",
  "parameter_type": "enum_array",
  "enum_name": "vehicle_types_category",  // 引用外部
  "enum_values": null  // 不直接定义
}
```

**解决方案**: Fallback机制

**实现位置**: `parameter_form.js:2613-2636`

```javascript
// 尝试获取 enum_values
let enumValues = disallowParam?.enum_values || allowParam?.enum_values || [];

// 如果没找到，检查 enum_name
if (enumValues.length === 0) {
  const enumName = disallowParam?.enum_name || allowParam?.enum_name;

  // 使用标准3分类系统作为fallback
  if (enumName === 'vehicle_types_category' || enumValues.length === 0) {
    enumValues = [
      { value: 'passenger', label: '客车', description: '...' },
      { value: 'truck', label: '货车', description: '...' },
      { value: 'delivery', label: '特种车辆', description: '...' }
    ];
  }
}
```

### 3. 跳过参数渲染

某些参数由其他步骤处理，不在参数表单中显示：

**跳过列表**:
- `affected_edges` - 由步骤2的边选择器处理
- `affected_segments` - 同上
- `entrance_ids` - 同上
- `disallow_vehicle_types` (当存在 `restriction_mode` 时)
- `allowed_vehicle_types` (当存在 `restriction_mode` 时)

**实现位置**: `templates.html:825-834`

---

## 数据流

### 1. 表单生成流程

```
用户选择策略模板
    ↓
loadTemplate() 加载模板JSON
    ↓
template.parameters_schema.forEach()
    ↓
根据 parameter_type 选择渲染方式
    ↓
├─ 简单类型 → 内联HTML
├─ 复杂数组 → 调用专用渲染函数
└─ 特殊逻辑 → 统一控件/跳过
    ↓
生成DOM元素并添加到表单
    ↓
绑定事件监听器（change, blur, input）
```

### 2. 数据收集流程

```
用户填写完表单后点击"生成策略实例"
    ↓
collectParameterValues(template)
    ↓
遍历 template.parameters_schema
    ↓
根据 parameter_type 收集数据
    ↓
├─ 简单类型 → getElementById(param-{name}).value
├─ enum_array → querySelectorAll('input[name="{name}"]:checked')
├─ 数组类型 → extractTableParameters(name, type)
└─ 特殊处理 → 统一车型控件值映射
    ↓
类型转换（string → int/float/boolean）
    ↓
验证参数（validateStrategyParameters）
    ↓
构建请求payload
    ↓
POST /api/v1/control/strategies/instances
```

### 3. TEC统一控件数据映射

```
用户选择车型（name="vehicle_types"）
    ↓
collectParameterValues() 检测到 restriction_mode
    ↓
获取 restriction_mode 的值
    ↓
根据模式决定映射目标
    ↓
├─ disallow_mode → 收集到 disallow_vehicle_types
└─ allow_mode → 收集到 allowed_vehicle_types
    ↓
最终payload只包含一个车型参数
```

**代码实现**: `templates.html:3126-3142`

---

## 已知问题和技术债

### 1. 双渲染系统并存 ⚠️

**问题描述**:
存在两套参数渲染系统并行运行：
- **系统1**: `templates.html:820` - 主渲染循环
- **系统2**: `templates.html:1531` - `renderParametersSection()` 函数

**影响**:
- 代码重复
- 修复需要同步到两个系统
- 增加维护成本

**历史原因**:
- 系统2是旧实现，使用内联样式
- 系统1是重构后的实现，使用CSS类
- 未完全移除旧系统导致并存

**建议修复**:
```javascript
// 替换 renderParametersSection 内容为:
function renderParametersSection(container, template) {
  // 直接调用系统1的渲染逻辑
  const form = generateFormFromTemplate(template);
  container.appendChild(form);
}
```

**预期收益**:
- 消除代码重复
- 单一渲染路径
- 更易维护

### 2. 废弃函数调用 ⚠️

**问题**: `templates.html:1481` 仍调用 `createVehicleTypeControl()`

**状态**: 已通过fallback修复

```javascript
// 当前实现（临时修复）
control = window.renderEnumArrayControl ?
  window.renderEnumArrayControl(param.parameter_name, param) :
  createStringControl(param);
```

**建议**: 移除旧系统后此问题自动解决

### 3. 缺少集中的参数类型注册表

**问题**: 参数类型和渲染函数的映射分散在多个if-else和switch语句中

**建议**: 创建参数类型注册表

```javascript
// 建议的实现
const PARAMETER_TYPE_REGISTRY = {
  'string': { render: renderStringControl, validate: validateString },
  'integer': { render: renderNumberControl, validate: validateInteger },
  'enum_array': { render: renderEnumArrayControl, validate: validateEnumArray },
  'step_array': { render: renderStepArrayControl, validate: validateStepArray },
  // ...
};

function renderParameter(param) {
  const handler = PARAMETER_TYPE_REGISTRY[param.parameter_type];
  if (!handler) {
    console.warn('Unknown parameter type:', param.parameter_type);
    return renderStringControl(param); // fallback
  }
  return handler.render(param);
}
```

---

## 测试检查清单

### 新增模板参数时

- [ ] 确定参数类型 (`parameter_type`)
- [ ] 在两个渲染系统中都能正确显示
- [ ] 数据收集函数能正确获取值
- [ ] 类型转换正确（string/int/float/boolean/array）
- [ ] 验证规则正确（必填/范围/格式）
- [ ] 提交到后端成功

### 修改车型相关参数时

- [ ] 检查是否需要更新 `vehicle_types_enum.json`
- [ ] 检查所有策略模板的 `enum_values`
- [ ] 测试TEC统一控件的模式切换
- [ ] 验证数据映射逻辑正确

### 修改时间区间相关参数时

- [ ] 检查时间轴可视化是否正确
- [ ] 检查单位转换（hours ↔ seconds）
- [ ] 验证24小时覆盖验证
- [ ] 测试添加/删除行功能

---

## 相关文档

- [车型分类系统文档](../templates/vehicle_type_system.md)
- [OpenSpec参数表单布局规范](../../openspec/specs/parameter-form-layout/spec.md)
- [前端代码规范](../../CLAUDE.md#frontend-development-standards)

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|-----|------|---------|
| v0.9.1 | 2025-11-01 | 修复TEC双重渲染、enum_name处理、VSS按钮样式 |
| v0.9.0 | 2025-10-xx | 引入统一车型控件、时间轴可视化 |

---

**维护者**: 开发团队
**反馈**: 如发现文档错误或需要补充，请在项目Issue中提出
