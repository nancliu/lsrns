# 策略实例创建功能验证指南

**目的**: 验证"生成策略实例"按钮是否正确应用了前端界面配置的参数
**适用策略**: VSS (可变限速)、DHS (应急车道开放)、TEC (收费站管控)
**验证时间**: 2025-10-30

---

## 📋 参数提取逻辑检查

### 当前实现概览

`createStrategy()` 函数（`templates.html` 2918-3134行）负责收集所有参数并创建策略实例。

#### 参数提取流程

```javascript
const configuredParams = {};

selectedTemplate.parameters_schema.forEach(param => {
  // 1. affected_edges - 特殊处理（来自步骤2选择的路段）
  if (param.parameter_name === 'affected_edges') {
    configuredParams[param.parameter_name] = selectedEdges;
    return;
  }

  // 2. step_array (VSS) - 从表格提取
  if (param.parameter_type === 'step_array') {
    const tbody = document.querySelector(`[data-parameter-name="${param.parameter_name}"] .steps-tbody`);
    const rows = tbody.querySelectorAll('.step-row');
    const value = Array.from(rows).map(row => ({
      time_hours: parseFloat(row.querySelector('.step-time').value),
      speed_kmh: parseFloat(row.querySelector('.step-speed').value)
    }));
    configuredParams[param.parameter_name] = value;
    return;
  }

  // 3. dhs_interval_array (DHS) - 从表格提取
  if (param.parameter_type === 'dhs_interval_array') {
    const tbody = document.querySelector('.dhs-intervals-tbody[data-parameter-name="' + param.parameter_name + '"]');
    const rows = tbody.querySelectorAll('.dhs-interval-row');
    const value = Array.from(rows).map(row => ({
      begin_hours: parseFloat(row.querySelector('.dhs-interval-begin').value),
      end_hours: parseFloat(row.querySelector('.dhs-interval-end').value),
      status: row.querySelector('.dhs-interval-status').value,
      allowed_vehicle_types: row.querySelector('.dhs-interval-vehicles').value
        .split(',').map(v => v.trim()).filter(v => v)
    }));
    configuredParams[param.parameter_name] = value;
    return;
  }

  // 4. flow_interval_array (TEC) - 从表格提取
  if (param.parameter_type === 'flow_interval_array') {
    const tbody = document.querySelector(`[data-parameter-name="${param.parameter_name}"] .intervals-tbody`);
    const rows = tbody.querySelectorAll('.interval-row');
    const value = Array.from(rows).map(row => ({
      begin_hours: parseFloat(row.querySelector('.interval-begin').value),
      end_hours: parseFloat(row.querySelector('.interval-end').value),
      vehsPerHour: parseFloat(row.querySelector('.interval-flow').value),
      target_speed: parseFloat(row.querySelector('.interval-speed').value)
    }));
    configuredParams[param.parameter_name] = value;
    return;
  }

  // 5. 其他参数类型 - 从 input 元素提取
  const input = document.getElementById(`param-${param.parameter_name}`);
  if (input) {
    // ... 类型转换逻辑
  }
});
```

---

## 🔍 验证步骤

### 验证 1: DHS 参数提取（intervals）

#### 步骤

1. **打开 DHS 策略配置页面**
2. **打开浏览器控制台（F12）**
3. **在"生成策略实例"按钮之前运行此验证脚本**:

```javascript
// ========== DHS 参数提取验证脚本 ==========
console.log('%c========== DHS 参数提取验证 ==========', 'color: #3b82f6; font-weight: bold;');

// 1. 检查模板信息
console.log('\n1. 检查当前模板...');
if (typeof selectedTemplate !== 'undefined') {
  console.log('✅ selectedTemplate 存在');
  console.log('   - template_id:', selectedTemplate.template_id);
  console.log('   - template_name:', selectedTemplate.template_name);

  // 查找 intervals 参数
  const intervalsParam = selectedTemplate.parameters_schema.find(p => p.parameter_name === 'intervals');
  if (intervalsParam) {
    console.log('✅ intervals 参数存在');
    console.log('   - parameter_type:', intervalsParam.parameter_type);
    console.log('   - required:', intervalsParam.required);
  } else {
    console.error('❌ intervals 参数不存在！');
  }
} else {
  console.error('❌ selectedTemplate 未定义！');
}

// 2. 检查表格数据
console.log('\n2. 检查 DHS 表格...');
const tbody = document.querySelector('.dhs-intervals-tbody[data-parameter-name="intervals"]');

if (tbody) {
  console.log('✅ 找到表格 tbody');
  console.log('   - data-parameter-name:', tbody.dataset.parameterName);

  const rows = tbody.querySelectorAll('.dhs-interval-row');
  console.log('   - 行数:', rows.length);

  if (rows.length > 0) {
    console.log('✅ 表格有数据行');

    // 模拟参数提取逻辑
    const extractedIntervals = Array.from(rows).map((row, index) => {
      const begin = row.querySelector('.dhs-interval-begin');
      const end = row.querySelector('.dhs-interval-end');
      const status = row.querySelector('.dhs-interval-status');
      const vehicles = row.querySelector('.dhs-interval-vehicles');

      console.log(`   行 ${index + 1}:`, {
        begin_hours: begin?.value,
        end_hours: end?.value,
        status: status?.value,
        allowed_vehicle_types: vehicles?.value
      });

      return {
        begin_hours: parseFloat(begin?.value) || 0,
        end_hours: parseFloat(end?.value) || 0,
        status: status?.value || 'CLOSED',
        allowed_vehicle_types: (vehicles?.value || '')
          .split(',')
          .map(v => v.trim())
          .filter(v => v)
      };
    });

    console.log('\n✅ 提取的 intervals 数据:');
    console.log(JSON.stringify(extractedIntervals, null, 2));

    // 3. 验证数据完整性
    console.log('\n3. 验证数据完整性...');
    let isValid = true;

    extractedIntervals.forEach((interval, index) => {
      // 检查时间范围
      if (isNaN(interval.begin_hours) || isNaN(interval.end_hours)) {
        console.error(`❌ 行 ${index + 1}: 时间数据无效`);
        isValid = false;
      } else if (interval.begin_hours >= interval.end_hours) {
        console.warn(`⚠️ 行 ${index + 1}: begin_hours (${interval.begin_hours}) >= end_hours (${interval.end_hours})`);
      }

      // 检查状态
      if (!['OPEN', 'CLOSED'].includes(interval.status)) {
        console.error(`❌ 行 ${index + 1}: 状态无效 (${interval.status})`);
        isValid = false;
      }

      // 检查允许车型
      if (interval.allowed_vehicle_types.length === 0) {
        console.warn(`⚠️ 行 ${index + 1}: 允许车型为空`);
      }
    });

    if (isValid) {
      console.log('\n✅ 所有数据有效');
    } else {
      console.error('\n❌ 发现数据错误');
    }

  } else {
    console.error('❌ 表格没有数据行');
  }
} else {
  console.error('❌ 未找到表格 tbody');
  console.log('   选择器: .dhs-intervals-tbody[data-parameter-name="intervals"]');

  // 尝试查找任何 dhs-intervals-tbody
  const anyDhsTbody = document.querySelector('.dhs-intervals-tbody');
  if (anyDhsTbody) {
    console.log('   找到其他 DHS tbody:');
    console.log('   - data-parameter-name:', anyDhsTbody.dataset.parameterName);
  }
}

// 4. 检查选择的路段
console.log('\n4. 检查选择的路段...');
if (typeof selectedEdges !== 'undefined') {
  console.log('✅ selectedEdges 存在');
  console.log('   - 路段数量:', selectedEdges.length);
  if (selectedEdges.length > 0) {
    console.log('   - 前3个路段:', selectedEdges.slice(0, 3));
  }
} else {
  console.error('❌ selectedEdges 未定义');
}

console.log('\n%c========== 验证完成 ==========', 'color: #22c55e; font-weight: bold;');
console.log('现在可以点击"生成策略实例"按钮');
```

#### 预期输出（成功）

```
========== DHS 参数提取验证 ==========

1. 检查当前模板...
✅ selectedTemplate 存在
   - template_id: dhs_peak_hours
   - template_name: 应急车道开放
✅ intervals 参数存在
   - parameter_type: dhs_interval_array
   - required: true

2. 检查 DHS 表格...
✅ 找到表格 tbody
   - data-parameter-name: intervals
   - 行数: 5
✅ 表格有数据行
   行 1: {begin_hours: "0", end_hours: "7", status: "CLOSED", allowed_vehicle_types: "emergency,authority"}
   行 2: {begin_hours: "7", end_hours: "9", status: "OPEN", allowed_vehicle_types: "passenger,bus,truck,emergency"}
   ...

✅ 提取的 intervals 数据:
[
  {
    "begin_hours": 0,
    "end_hours": 7,
    "status": "CLOSED",
    "allowed_vehicle_types": ["emergency", "authority"]
  },
  {
    "begin_hours": 7,
    "end_hours": 9,
    "status": "OPEN",
    "allowed_vehicle_types": ["passenger", "bus", "truck", "emergency"]
  },
  ...
]

3. 验证数据完整性...
✅ 所有数据有效

4. 检查选择的路段...
✅ selectedEdges 存在
   - 路段数量: 4
   - 前3个路段: ["-8712", "-15452.627", "-15452.1254"]

========== 验证完成 ==========
现在可以点击"生成策略实例"按钮
```

---

### 验证 2: 监控实际 API 请求

#### 步骤

1. **打开 Network 标签**（F12 → Network）
2. **点击"生成策略实例"按钮**
3. **查找 POST 请求** `/api/v1/control/strategy-instances/`
4. **查看 Request Payload**

#### 预期 Payload（DHS 示例）

```json
{
  "strategy_name": "测试DHS_G4202_1",
  "template_id": "dhs_peak_hours",
  "parameters": {
    "affected_edges": [
      "-8712",
      "-15452.627",
      "-15452.1254",
      "-15452.2508"
    ],
    "intervals": [
      {
        "begin_hours": 0,
        "end_hours": 7,
        "status": "CLOSED",
        "allowed_vehicle_types": ["emergency", "authority"]
      },
      {
        "begin_hours": 7,
        "end_hours": 9,
        "status": "OPEN",
        "allowed_vehicle_types": ["passenger", "bus", "truck", "emergency"]
      },
      {
        "begin_hours": 9,
        "end_hours": 17,
        "status": "CLOSED",
        "allowed_vehicle_types": ["emergency", "authority"]
      },
      {
        "begin_hours": 17,
        "end_hours": 19,
        "status": "OPEN",
        "allowed_vehicle_types": ["passenger", "bus", "truck", "emergency"]
      },
      {
        "begin_hours": 19,
        "end_hours": 24,
        "status": "CLOSED",
        "allowed_vehicle_types": ["emergency", "authority"]
      }
    ]
  },
  "affected_edges": [
    "-8712",
    "-15452.627",
    "-15452.1254",
    "-15452.2508"
  ]
}
```

#### 检查点

- ✅ `intervals` 参数存在
- ✅ `intervals` 是数组
- ✅ 每个区间包含 `begin_hours`, `end_hours`, `status`, `allowed_vehicle_types`
- ✅ 时间值是数字（不是字符串）
- ✅ `allowed_vehicle_types` 是数组（不是逗号分隔的字符串）
- ✅ `affected_edges` 存在且不为空

---

### 验证 3: 检查控制台日志

#### 步骤

1. **打开控制台（F12 → Console）**
2. **点击"生成策略实例"按钮**
3. **查看控制台输出**

#### 预期日志

```
[createStrategy] Extracting step_array for: speed_steps (如果是 VSS)
[createStrategy] Found tbody: <tbody class="steps-tbody" data-parameter-name="speed_steps">
[createStrategy] Found rows: 4
[createStrategy] Extracted value: [{time_hours: 7, speed_kmh: 100}, ...]
[createStrategy] Setting parameter: speed_steps = [...]

[createStrategy] Final configuredParams: {
  affected_edges: [...],
  intervals: [...]  // 或 speed_steps: [...]
}

Creating strategy via API: {
  strategy_name: "测试DHS_G4202_1",
  template_id: "dhs_peak_hours",
  parameters: {...},
  affected_edges: [...]
}

Strategy created successfully: {
  strategy_id: "...",
  ...
}
```

#### 检查点

- ✅ 看到 `[createStrategy] Final configuredParams:` 日志
- ✅ `configuredParams` 包含正确的参数
- ✅ DHS: `intervals` 数组存在
- ✅ VSS: `speed_steps` 数组存在
- ✅ TEC: 相应的流量控制参数存在
- ✅ 看到 `Creating strategy via API:` 日志
- ✅ 看到 `Strategy created successfully:` 日志（如果成功）
- ❌ 如果看到 `Error creating strategy:`，查看错误详情

---

## 🐛 常见问题排查

### 问题 1: "缺少 intervals 参数"

**症状**:
- API 返回错误：`intervals parameter is required`
- 或：`Field required` for `intervals`

**原因**:
- `configuredParams` 中没有 `intervals` 键
- 表格未找到或数据提取失败

**排查**:
1. 运行验证脚本（见上方）
2. 检查是否看到 `❌ 未找到表格 tbody`
3. 检查 `tbody` 的 `data-parameter-name` 是否为 `intervals`

**解决方案**:
```javascript
// 在控制台手动设置 data-parameter-name
const tbody = document.querySelector('.dhs-intervals-tbody');
if (tbody && !tbody.dataset.parameterName) {
  tbody.dataset.parameterName = 'intervals';
  console.log('✅ 已手动设置 data-parameter-name');
}
```

---

### 问题 2: "allowed_vehicle_types 是字符串而非数组"

**症状**:
- API 返回错误：`allowed_vehicle_types should be array`

**原因**:
- 字符串分割逻辑未正确执行

**检查**:
```javascript
// 测试字符串分割
const testString = "passenger,bus,truck,emergency";
const result = testString.split(',').map(v => v.trim()).filter(v => v);
console.log('Split result:', result);
// 应该输出: ["passenger", "bus", "truck", "emergency"]
```

---

### 问题 3: "时间值是字符串而非数字"

**症状**:
- API 返回错误：`begin_hours should be number`

**原因**:
- `parseFloat()` 未正确调用或返回 NaN

**检查**:
```javascript
// 测试数值转换
const beginInput = document.querySelector('.dhs-interval-begin');
console.log('Raw value:', beginInput.value);
console.log('Parsed value:', parseFloat(beginInput.value));
console.log('Type:', typeof parseFloat(beginInput.value));
// 应该输出数字类型
```

---

## ✅ 完整验证清单

使用此清单验证所有策略类型：

### VSS (可变限速)

- [ ] 参数名称：`speed_steps`
- [ ] 表格选择器：`[data-parameter-name="speed_steps"] .steps-tbody`
- [ ] 行选择器：`.step-row`
- [ ] 提取字段：`time_hours`, `speed_kmh`
- [ ] 时间值类型：数字
- [ ] 速度值类型：数字
- [ ] API Payload 包含 `speed_steps`
- [ ] 策略创建成功

### DHS (应急车道开放)

- [ ] 参数名称：`intervals`
- [ ] 表格选择器：`.dhs-intervals-tbody[data-parameter-name="intervals"]`
- [ ] 行选择器：`.dhs-interval-row`
- [ ] 提取字段：`begin_hours`, `end_hours`, `status`, `allowed_vehicle_types`
- [ ] 时间值类型：数字
- [ ] 状态值：'OPEN' 或 'CLOSED'
- [ ] 车型列表类型：数组
- [ ] API Payload 包含 `intervals`
- [ ] 策略创建成功

### TEC (收费站管控)

- [ ] 参数名称：通常是 `flow_intervals` 或类似
- [ ] 表格选择器：`[data-parameter-name="..."] .intervals-tbody`
- [ ] 行选择器：`.interval-row`
- [ ] 提取字段：`begin_hours`, `end_hours`, `vehsPerHour`, `target_speed`
- [ ] 时间值类型：数字
- [ ] 流量值类型：数字
- [ ] 速度值类型：数字
- [ ] API Payload 包含流量控制参数
- [ ] 策略创建成功

---

## 📝 验证报告模板

完成验证后，请填写此报告：

```markdown
# 策略实例创建验证报告

**测试日期**: YYYY-MM-DD
**测试人员**: [姓名]
**浏览器**: [Chrome/Firefox/Edge + 版本]

## 测试结果

### VSS 测试
- [ ] 通过 / [ ] 失败
- 问题描述：[如果失败，描述问题]
- 截图：[如果有]

### DHS 测试
- [ ] 通过 / [ ] 失败
- 问题描述：[如果失败，描述问题]
- 截图：[如果有]

### TEC 测试
- [ ] 通过 / [ ] 失败
- 问题描述：[如果失败，描述问题]
- 截图：[如果有]

## 控制台日志
```
[粘贴控制台输出]
```

## Network Payload
```json
[粘贴 API 请求 Payload]
```

## 结论
- [ ] 所有测试通过
- [ ] 部分测试失败（见上述描述）
```

---

**文档创建时间**: 2025-10-30
**用于验证**: 策略实例创建功能的参数提取逻辑
**关键文件**: `templates.html` (createStrategy 函数, lines 2918-3134)
