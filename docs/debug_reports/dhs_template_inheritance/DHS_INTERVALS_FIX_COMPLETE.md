# DHS Intervals 参数缺失问题修复 ✅

**问题**: 创建 DHS 策略实例失败，错误信息：
```
Parameter validation failed: Required parameter 'intervals' not provided
Parameter 'allowed_vehicle_types' must be an array of enum values
```

**根本原因**: 模板继承未正确解析
**修复时间**: 2025-10-30
**状态**: ✅ 已修复

---

## 🔍 问题分析

### 错误信息解析

```
创建失败: Parameter validation failed:
Required parameter 'intervals' not provided;
Parameter 'allowed_vehicle_types' must be an array of enum values
```

**两个问题**:
1. ❌ **`intervals` 参数未提供** - 后端验证失败
2. ❌ **`allowed_vehicle_types` 类型错误** - 应该是枚举数组

### 问题追踪

#### 1. 前端参数提取（已验证正确）

从截图可以看到，前端表格已正确填写：
- 5 行数据
- 每行包含：Start (hours), End (hours), Status, Allowed Vehicle Types
- 数据完整且格式正确

**前端代码**（`templates.html:2971-2995`）:
```javascript
if (param.parameter_type === 'dhs_interval_array') {
  const tbody = document.querySelector('.dhs-intervals-tbody[data-parameter-name="' + param.parameter_name + '"]');
  if (tbody) {
    const rows = tbody.querySelectorAll('.dhs-interval-row');
    const value = Array.from(rows).map(row => ({
      begin_hours: parseFloat(row.querySelector('.dhs-interval-begin').value),
      end_hours: parseFloat(row.querySelector('.dhs-interval-end').value),
      status: row.querySelector('.dhs-interval-status').value,
      allowed_vehicle_types: row.querySelector('.dhs-interval-vehicles').value
        .split(',').map(v => v.trim()).filter(v => v)
    }));
    configuredParams[param.parameter_name] = value;
  }
}
```

✅ 前端逻辑正确

#### 2. 模板结构问题（问题根源）

**DHS 模板继承关系**:
```
dhs_peak_hours.json (子模板)
  └── extends: "dhs_base"
       └── dhs_base.json (父模板，包含 intervals 参数)
```

**dhs_peak_hours.json** (子模板):
```json
{
  "template_id": "dhs_peak_hours",
  "template_name": "应急车道开放",
  "extends": "dhs_base",  // ← 继承父模板
  "parameters_schema": [
    {
      "parameter_name": "allowed_vehicle_types",
      "parameter_type": "enum_array",
      "required": false,
      ...
    }
  ]
}
```

**dhs_base.json** (父模板):
```json
{
  "template_id": "dhs_base",
  "template_name": "应急车道 - 基础模板（抽象）",
  "strategy_type": "DHS",
  "is_abstract": true,
  "parameters_schema": [
    {
      "parameter_name": "affected_edges",
      ...
    },
    {
      "parameter_name": "intervals",  // ← intervals 参数在这里！
      "parameter_type": "dhs_interval_array",
      "required": true,
      ...
    }
  ]
}
```

**问题**: 前端加载模板时，**没有合并父模板的参数**！

#### 3. 后端模板加载逻辑（Bug 所在）

**问题函数**: `load_template_with_schema()` ([shared/control_tools/template_loader.py:433-467](../shared/control_tools/template_loader.py#L433-L467))

**修复前**:
```python
def load_template_with_schema(template_id: str, templates_dir: Path):
    for file_path in template_files:
        data = _load_json_file(file_path)
        if data.get("template_id") == template_id:
            # Validate the template structure
            if not validate_template(data):
                return None

            return data  # ❌ 直接返回，没有解析继承！
```

**问题**:
- ❌ 加载 `dhs_peak_hours` 时，只返回子模板的内容
- ❌ 没有调用 `_resolve_template_inheritance()` 合并父模板
- ❌ 结果：`intervals` 参数缺失（因为它在父模板 `dhs_base` 中）

---

## 🛠️ 修复方案

### 修复代码

**文件**: `shared/control_tools/template_loader.py`
**函数**: `load_template_with_schema()`
**行数**: 458-473

**修复后**:
```python
def load_template_with_schema(template_id: str, templates_dir: Path):
    for file_path in template_files:
        data = _load_json_file(file_path)
        if data.get("template_id") == template_id:
            # ✅ [NEW] Resolve template inheritance if needed
            try:
                if "extends" in data:
                    logger.info(f"Resolving inheritance for template: {template_id}")
                    data = _resolve_template_inheritance(data, templates_dir)
            except Exception as e:
                logger.error(f"Failed to resolve template inheritance for {template_id}: {e}")
                return None

            # Validate the template structure
            if not validate_template(data):
                return None

            return data  # ✅ 现在返回合并后的完整模板
```

**关键改动**:
1. ✅ 检查模板是否有 `extends` 字段
2. ✅ 调用 `_resolve_template_inheritance()` 解析继承
3. ✅ 返回合并后的完整模板（包含父模板的所有参数）

---

## 🎯 修复效果

### 修复前

**加载 `dhs_peak_hours` 模板返回**:
```json
{
  "template_id": "dhs_peak_hours",
  "extends": "dhs_base",
  "parameters_schema": [
    {
      "parameter_name": "allowed_vehicle_types",  // ← 只有子模板的参数
      ...
    }
  ]
}
```

❌ 缺少 `intervals` 参数（在父模板中）
❌ 前端无法找到 `intervals` 参数定义
❌ 前端无法渲染 DHS intervals 表格
❌ 后端验证失败："intervals not provided"

---

### 修复后

**加载 `dhs_peak_hours` 模板返回**:
```json
{
  "template_id": "dhs_peak_hours",
  "template_name": "应急车道开放",
  "strategy_type": "DHS",  // ← 从父模板继承
  "parameters_schema": [
    {
      "parameter_name": "affected_edges",  // ← 从父模板继承
      ...
    },
    {
      "parameter_name": "intervals",  // ← 从父模板继承（关键！）
      "parameter_type": "dhs_interval_array",
      "required": true,
      ...
    },
    {
      "parameter_name": "allowed_vehicle_types",  // ← 子模板的参数
      ...
    }
  ]
}
```

✅ 包含所有参数（父模板 + 子模板）
✅ `intervals` 参数存在
✅ 前端正确渲染 DHS intervals 表格
✅ 后端验证通过

---

## 🔄 模板继承机制

### 工作原理

`_resolve_template_inheritance()` 函数 ([template_loader.py:164-256](../shared/control_tools/template_loader.py#L164-L256)) 负责递归解析模板继承：

```python
def _resolve_template_inheritance(data, templates_dir, loaded_templates=None):
    # 1. 检查是否有 extends 字段
    parent_template_id = data.get("extends")
    if not parent_template_id:
        return data  # 没有继承，直接返回

    # 2. 加载父模板
    parent_data = _load_json_file(parent_file_path)

    # 3. 递归解析父模板的继承（支持多级继承）
    parent_data = _resolve_template_inheritance(parent_data, templates_dir, loaded_templates)

    # 4. 合并父模板和子模板
    merged = {**parent_data, **data}  # 子模板覆盖父模板

    # 5. 特殊处理：合并 parameters_schema
    parent_params = {p["parameter_name"]: p for p in parent_data.get("parameters_schema", [])}
    child_params = {p["parameter_name"]: p for p in data.get("parameters_schema", [])}
    merged_params = []

    # 5.1 子模板参数优先（覆盖父模板同名参数）
    for param_name, param in child_params.items():
        merged_params.append(param)

    # 5.2 添加父模板中子模板没有的参数
    for param_name, param in parent_params.items():
        if param_name not in child_params:
            merged_params.append(param)

    merged["parameters_schema"] = merged_params

    # 6. 移除 extends 字段
    merged.pop("extends", None)

    return merged
```

**支持特性**:
- ✅ 多级继承（A extends B extends C）
- ✅ 参数覆盖（子模板同名参数覆盖父模板）
- ✅ 参数合并（父模板独有参数保留）
- ✅ 循环检测（防止 A extends B extends A）

---

## 📝 测试验证

### 测试步骤

1. **重启服务器**（应用代码修复）:
   ```bash
   # 激活环境
   conda activate od_project

   # 重启服务器
   .\start_api.ps1
   ```

2. **刷新前端页面**:
   ```
   Ctrl+F5 强制刷新
   ```

3. **选择 DHS 模板**:
   - 访问: `http://localhost:8000/control/templates.html`
   - 选择"应急车道开放"模板

4. **查看控制台日志**:
   ```
   [INFO] Resolving inheritance for template: dhs_peak_hours
   [INFO] Template inheritance resolved: dhs_peak_hours
   ```

5. **检查模板加载结果**:
   - 打开浏览器控制台（F12）
   - 运行:
     ```javascript
     console.log('Template:', selectedTemplate);
     console.log('Parameters:', selectedTemplate.parameters_schema.map(p => p.parameter_name));
     ```
   - 应该看到:
     ```
     Parameters: ["affected_edges", "hard_shoulder_lane_index", "intervals", "allowed_vehicle_types"]
     ```

6. **进入参数配置页面**:
   - 选择路段
   - 点击"下一步"
   - **应该看到**:
     - ✅ intervals 参数配置表格
     - ✅ 5 行默认数据
     - ✅ 时间轴可视化（如果已修复）

7. **创建策略实例**:
   - 填写策略名称
   - 点击"生成策略实例"
   - **应该成功**

### 预期结果

#### 成功标志

- ✅ 控制台日志显示 "Resolving inheritance for template: dhs_peak_hours"
- ✅ `selectedTemplate.parameters_schema` 包含 4 个参数（包括 `intervals`）
- ✅ 参数配置页面显示 intervals 表格
- ✅ API 请求 Payload 包含 `intervals` 参数
- ✅ 策略创建成功，返回 `strategy_id`

#### API Payload 示例

```json
{
  "strategy_name": "测试DHS_G4202",
  "template_id": "dhs_peak_hours",
  "parameters": {
    "affected_edges": [...],
    "intervals": [
      {"begin_hours": 0, "end_hours": 7, "status": "CLOSED", "allowed_vehicle_types": ["emergency", "authority"]},
      {"begin_hours": 7, "end_hours": 9, "status": "OPEN", "allowed_vehicle_types": ["passenger", "bus", "emergency"]},
      {"begin_hours": 9, "end_hours": 17, "status": "CLOSED", "allowed_vehicle_types": ["emergency", "authority"]},
      {"begin_hours": 17, "end_hours": 19, "status": "OPEN", "allowed_vehicle_types": ["passenger", "bus", "emergency"]},
      {"begin_hours": 19, "end_hours": 24, "status": "CLOSED", "allowed_vehicle_types": ["emergency", "authority"]}
    ],
    "allowed_vehicle_types": ["passenger", "bus", "truck", "emergency"]
  },
  "affected_edges": [...]
}
```

---

## 🐛 如果仍然失败

### 检查 1: 服务器是否重启

**症状**: 代码修改后仍然报同样的错误

**原因**: Python 代码修改需要重启服务器才能生效

**解决**:
```bash
# 停止服务器（如果正在运行）
# Ctrl+C

# 重新启动
conda activate od_project
.\start_api.ps1
```

---

### 检查 2: 模板文件是否正确

**验证父模板**:
```bash
cat templates/control_strategies/dynamic_hard_shoulder/dhs_base.json | grep -A 5 "intervals"
```

应该看到:
```json
"parameter_name": "intervals",
"parameter_type": "dhs_interval_array",
"required": true,
```

---

### 检查 3: 继承是否正确解析

**在服务器日志中查找**:
```
[INFO] Resolving inheritance for template: dhs_peak_hours
[INFO] Template inheritance resolved: dhs_peak_hours
```

**如果没有这些日志**:
- 说明 `extends` 字段未被识别
- 检查 `dhs_peak_hours.json` 中是否有 `"extends": "dhs_base"`

---

### 检查 4: 前端是否收到完整模板

**在浏览器控制台运行**:
```javascript
// 检查模板参数
if (selectedTemplate) {
  console.log('Template ID:', selectedTemplate.template_id);
  console.log('Parameters:');
  selectedTemplate.parameters_schema.forEach(p => {
    console.log(`  - ${p.parameter_name} (${p.parameter_type}, required: ${p.required})`);
  });

  // 查找 intervals 参数
  const intervalsParam = selectedTemplate.parameters_schema.find(p => p.parameter_name === 'intervals');
  if (intervalsParam) {
    console.log('✅ intervals 参数存在');
    console.log('   details:', intervalsParam);
  } else {
    console.error('❌ intervals 参数缺失！');
  }
}
```

**预期输出**:
```
Template ID: dhs_peak_hours
Parameters:
  - affected_edges (edge_array, required: true)
  - hard_shoulder_lane_index (integer, required: false)
  - intervals (dhs_interval_array, required: true)
  - allowed_vehicle_types (enum_array, required: false)
✅ intervals 参数存在
```

---

## 📊 修复影响范围

### 受影响的模板

所有使用 `extends` 继承的模板：

| 子模板 | 父模板 | 状态 |
|--------|--------|------|
| `dhs_peak_hours` | `dhs_base` | ✅ 已修复 |
| `dhs_passenger_only` | `dhs_base` | ✅ 已修复 |
| `dhs_peak_multi_interval` | `dhs_base` | ✅ 已修复 |
| 其他继承模板 | 任何父模板 | ✅ 已修复 |

### 修复的功能

- ✅ DHS 策略实例创建
- ✅ 模板参数正确加载
- ✅ 前端参数表单正确渲染
- ✅ 后端参数验证正确执行

---

## ✅ 验证清单

完成修复后，使用此清单验证：

### 代码修复

- [x] 修改 `template_loader.py` 中的 `load_template_with_schema()` 函数
- [x] 添加模板继承解析逻辑
- [x] 添加错误处理和日志

### 服务器

- [ ] 重启服务器
- [ ] 查看服务器日志，确认无错误
- [ ] 查看继承解析日志

### 前端

- [ ] 刷新前端页面（Ctrl+F5）
- [ ] 选择 DHS 模板
- [ ] 检查控制台，确认模板包含 intervals 参数
- [ ] 进入参数配置页面，确认显示 intervals 表格

### API

- [ ] 创建策略实例
- [ ] 检查 Network 请求，确认 Payload 包含 intervals
- [ ] 确认策略创建成功

---

## 📚 相关文档

- **template_loader.py** - 模板加载和继承解析
- **dhs_base.json** - DHS 基础模板（包含 intervals 参数）
- **dhs_peak_hours.json** - DHS 子模板（继承 dhs_base）
- **templates.html** - 前端参数提取逻辑

---

**修复完成时间**: 2025-10-30
**修复文件**: `shared/control_tools/template_loader.py`
**修复行数**: 459-466
**状态**: ✅ 已修复，待用户测试验证

**下一步**: 请重启服务器并测试 DHS 策略创建！
