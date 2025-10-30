# DHS 模板继承问题修复报告

**修复时间**: 2025-10-30
**问题级别**: P0 - 阻塞性 Bug
**状态**: ✅ 代码修复完成，待用户验证

---

## 问题总结

DHS（应急车道开放）策略创建失败，错误消息：
```
Parameter validation failed: Required parameter 'intervals' not provided
Parameter 'allowed_vehicle_types' must be an array of enum values
```

---

## 根本原因

### 问题分析

1. **模板继承结构**:
   ```
   dhs_peak_hours.json (子模板)
     "extends": "dhs_base"
     参数: ["allowed_vehicle_types"]
       ↓ 应该继承自
   dhs_base.json (父模板)
     参数: ["affected_edges", "intervals", "hard_shoulder_lane_index"]
   ```

2. **代码缺陷**:
   `shared/control_tools/template_loader.py` 的 `load_template_with_schema()` 函数：
   - ❌ **直接返回子模板**，没有解析 `extends` 字段
   - ❌ **未调用** `_resolve_template_inheritance()` 函数
   - ✅ 该函数已存在于同文件（Lines 164-256），但未被使用

3. **影响链路**:
   ```
   Backend: load_template_with_schema()
     → 返回不完整的子模板（缺少 intervals 参数）
       ↓
   Frontend: 接收模板 schema
     → parameters_schema 中没有 "intervals"
     → 参数提取逻辑未执行（因为找不到该参数）
       ↓
   Frontend: 发送策略创建请求
     → 请求体中缺少 "intervals" 字段
       ↓
   Backend: 参数验证
     → ❌ 失败：Required parameter 'intervals' not provided
   ```

---

## 修复方案

### 修改文件

**文件**: `shared/control_tools/template_loader.py`
**函数**: `load_template_with_schema()` (Lines 433-476)
**修改位置**: Lines 458-466

### 修改前代码

```python
if data.get("template_id") == template_id:
    # Validate the template structure
    if not validate_template(data):
        logger.warning(f"Template {template_id} failed validation")
        return None

    return data  # ← 直接返回，未解析继承
```

### 修改后代码

```python
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
        logger.warning(f"Template {template_id} failed validation")
        return None

    return data  # ← 现在返回完整的合并模板
```

### 关键改动

1. **检查继承**: `if "extends" in data`
2. **调用解析函数**: `data = _resolve_template_inheritance(data, templates_dir)`
3. **错误处理**: 捕获继承解析失败，记录日志并返回 None
4. **日志记录**: 添加 `logger.info()` 便于调试

---

## 验证步骤

### 1. 重启服务器

```powershell
# 激活环境
conda activate od_project

# 停止当前服务器（Ctrl+C）

# 重启服务器
.\start_api.ps1
```

### 2. 检查后端日志

服务器启动后，查找以下日志：

```
INFO: Resolving inheritance for template: dhs_peak_hours
```

如果看到此日志，说明模板继承解析已启用。

### 3. 前端验证

#### 步骤 A: 打开浏览器控制台

1. 访问: `http://localhost:8000/control/templates.html`
2. 按 `F12` 打开开发者工具
3. 切换到 Console 标签

#### 步骤 B: 检查模板 Schema

选择 DHS 模板后，在控制台运行：

```javascript
// 检查当前模板的参数
console.log('Template ID:', window.currentTemplate?.template_id);
console.log('Parameters:', window.currentTemplate?.parameters_schema?.map(p => p.parameter_name));
```

**预期输出**:
```
Template ID: dhs_peak_hours
Parameters: ["affected_edges", "intervals", "hard_shoulder_lane_index", "allowed_vehicle_types"]
```

✅ **如果看到 "intervals" 在参数列表中，说明继承解析成功！**

❌ **如果只看到 "allowed_vehicle_types"，说明继承解析失败**

#### 步骤 C: 检查时间轴渲染

1. 选择 DHS 模板："应急车道开放 - 早晚高峰"
2. 选择路段（例如：G4202 逆时针 K38.2-K36.9）
3. 进入步骤3（参数配置）

**预期结果**:
- ✅ 表格上方显示 24 小时时间轴
- ✅ 时间轴有 5 个时间槽（默认值）
- ✅ OPEN 槽为绿色，CLOSED 槽为红色
- ✅ 每个槽显示标签（"开启 07:00-09:00" 等）

#### 步骤 D: 测试策略创建

1. 填写必填参数：
   - **affected_edges**: 选择路段
   - **intervals**: 使用默认值或修改
   - **hard_shoulder_lane_index**: 输入 `-1`（最右侧车道）
   - **allowed_vehicle_types**: 选择 "passenger, bus"

2. 点击 "生成策略实例" 按钮

3. 打开 Network 标签，查看请求 Payload

**预期 Payload**:
```json
{
  "configured_params": {
    "affected_edges": ["-8712", "-15452.627", ...],
    "intervals": [
      {"begin_hours": 0, "end_hours": 7, "status": "CLOSED", "allowed_vehicle_types": ["emergency"]},
      {"begin_hours": 7, "end_hours": 9, "status": "OPEN", "allowed_vehicle_types": ["passenger", "bus"]},
      ...
    ],
    "hard_shoulder_lane_index": -1,
    "allowed_vehicle_types": ["passenger", "bus"]
  }
}
```

✅ **如果 Payload 包含 "intervals" 数组，说明参数提取成功！**

4. 检查响应

**预期响应** (200 OK):
```json
{
  "strategy_id": "strategy_...",
  "message": "Strategy instance created successfully"
}
```

✅ **如果收到 200 响应，说明策略创建成功！**

---

## 测试清单

### 后端验证
- [ ] 服务器重启成功
- [ ] 日志显示 "Resolving inheritance for template: dhs_peak_hours"
- [ ] 无错误日志

### 前端验证
- [ ] 模板加载后 `currentTemplate.parameters_schema` 包含 "intervals"
- [ ] 参数配置页面显示时间轴（表格上方）
- [ ] 时间轴有 5 个默认时间槽
- [ ] 时间槽颜色正确（绿色=OPEN，红色=CLOSED）
- [ ] 修改表格值，时间轴自动更新

### 策略创建验证
- [ ] 点击 "生成策略实例" 按钮
- [ ] Network 请求 Payload 包含 "intervals" 字段
- [ ] 响应状态码为 200
- [ ] 策略实例创建成功
- [ ] 策略列表中显示新创建的策略

---

## 影响范围

### 直接修复的模板

1. **dhs_peak_hours** (早晚高峰) - extends dhs_base
2. **dhs_passenger_only** (仅允许客车) - extends dhs_base
3. **dhs_peak_multi_interval** (多时段控制) - extends dhs_base

### 间接受益

所有使用 `extends` 关键字的模板现在都会正确解析继承关系。

### 不受影响的模板

- **vss_strict**, **vss_moderate** 等 VSS 模板（不使用继承）
- **tec_flow_metering** 等 TEC 模板（不使用继承）

---

## 相关文档

- **Frontend Timeline 修复**: `DHS_TEC_TIMELINE_COMPLETE.md`
- **快速诊断指南**: `DHS_QUICK_FIX.md`
- **诊断脚本**: `fix_dhs_timeline.js`
- **参数提取验证**: `STRATEGY_CREATE_VERIFICATION.md`

---

## 技术细节

### _resolve_template_inheritance() 函数功能

该函数位于 `shared/control_tools/template_loader.py:164-256`，功能包括：

1. **递归解析**: 支持多级继承（A extends B, B extends C）
2. **循环检测**: 防止 A extends B, B extends A
3. **参数合并**:
   - 子模板参数覆盖同名父模板参数
   - 保留父模板参数顺序
   - 追加子模板新增参数
4. **字段覆盖**: 子模板的非参数字段覆盖父模板字段
5. **extends 移除**: 最终输出不包含 "extends" 字段

### 合并示例

**父模板** (dhs_base.json):
```json
{
  "template_id": "dhs_base",
  "parameters_schema": [
    {"parameter_name": "affected_edges", ...},
    {"parameter_name": "intervals", ...},
    {"parameter_name": "hard_shoulder_lane_index", ...}
  ]
}
```

**子模板** (dhs_peak_hours.json):
```json
{
  "template_id": "dhs_peak_hours",
  "extends": "dhs_base",
  "parameters_schema": [
    {"parameter_name": "allowed_vehicle_types", ...}
  ]
}
```

**合并结果** (返回给前端):
```json
{
  "template_id": "dhs_peak_hours",
  "parameters_schema": [
    {"parameter_name": "affected_edges", ...},      // 从父模板
    {"parameter_name": "intervals", ...},           // 从父模板
    {"parameter_name": "hard_shoulder_lane_index", ...},  // 从父模板
    {"parameter_name": "allowed_vehicle_types", ...}      // 从子模板
  ]
}
```

---

## 后续优化建议

### 1. 单元测试

为 `_resolve_template_inheritance()` 添加单元测试：

```python
# tests/unit/test_template_inheritance.py
def test_resolve_single_level_inheritance():
    """测试单级继承解析"""
    pass

def test_resolve_multi_level_inheritance():
    """测试多级继承解析"""
    pass

def test_detect_circular_inheritance():
    """测试循环继承检测"""
    pass

def test_parameter_override():
    """测试参数覆盖逻辑"""
    pass
```

### 2. 模板验证

添加模板加载时的继承验证：
- 检查 `extends` 引用的父模板是否存在
- 检查是否存在循环继承
- 输出继承关系树（用于调试）

### 3. 前端缓存

优化模板加载性能：
- 缓存已解析的模板（避免重复解析）
- 添加模板版本管理（invalidate cache on update）

---

## 总结

✅ **根本原因**: `load_template_with_schema()` 未调用 `_resolve_template_inheritance()`
✅ **修复方法**: 添加继承解析逻辑（8 行代码）
✅ **验证方法**: 检查日志、前端 schema、时间轴渲染、策略创建
✅ **影响范围**: 所有使用 `extends` 的 DHS 模板

**下一步**: 用户重启服务器并按照验证步骤测试。

---

**文档创建时间**: 2025-10-30
**预计修复时间**: 已完成（代码修改 < 5 分钟）
**预计验证时间**: 5-10 分钟
