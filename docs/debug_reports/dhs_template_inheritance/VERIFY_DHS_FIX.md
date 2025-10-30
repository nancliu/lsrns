# DHS 模板继承修复验证指南

**修复状态**: ✅ 代码已修改（`template_loader.py`）
**服务器状态**: ✅ 已启动（uvicorn --reload 自动重载）
**下一步**: 前端验证修复是否生效

---

## 快速验证（5 分钟）

### 步骤 1: 打开 DHS 策略配置页面

1. 访问: `http://localhost:8000/control/templates.html`
2. 在策略类型下拉框选择: **"应急车道开放（DHS）"**
3. 选择任一模板（例如："应急车道开放 - 早晚高峰"）
4. 选择路段（例如：G4202 逆时针 K38.2-K36.9）
5. 点击 "下一步" 进入参数配置页面

---

### 步骤 2: 检查时间轴是否显示

**预期结果** ✅:
- 表格上方显示 **24 小时时间轴**
- 时间轴有 **5 个时间槽**（默认配置）
- **绿色槽** = OPEN（开启）
- **红色槽** = CLOSED（关闭）
- 每个槽显示时间范围标签（例如："开启 07:00-09:00"）

**如果看到时间轴** = ✅ **前端渲染修复成功**

**如果没看到时间轴** = ❌ 前端渲染仍有问题（按照 `DHS_QUICK_FIX.md` 诊断）

---

### 步骤 3: 验证模板参数完整性（关键）

打开浏览器控制台（按 `F12`），运行：

```javascript
// 检查当前模板的参数列表
const params = window.currentTemplate?.parameters_schema?.map(p => p.parameter_name);
console.log('Template ID:', window.currentTemplate?.template_id);
console.log('Parameters:', params);
```

**预期输出** ✅:
```javascript
Template ID: "dhs_peak_hours"
Parameters: ["affected_edges", "intervals", "hard_shoulder_lane_index", "allowed_vehicle_types"]
```

**关键检查点**:
- ✅ 参数列表中包含 **"intervals"**（从父模板 dhs_base 继承）
- ✅ 参数列表中包含 **"allowed_vehicle_types"**（子模板自有）
- ✅ 总共 **4 个参数**（3 个来自父模板 + 1 个来自子模板）

**如果缺少 "intervals"** = ❌ **模板继承仍未解析**

---

### 步骤 4: 测试策略创建（最终验证）

#### 4.1 填写必填参数

根据表单填写：

| 参数名 | 值 | 说明 |
|-------|-----|------|
| **affected_edges** | （已自动填充） | 选择的路段边列表 |
| **intervals** | （使用默认值或修改表格） | 时间区间列表 |
| **hard_shoulder_lane_index** | `-1` | 最右侧车道（应急车道） |
| **allowed_vehicle_types** | `passenger, bus` | 允许的车辆类型 |

#### 4.2 点击 "生成策略实例" 按钮

#### 4.3 检查 Network 请求

打开开发者工具的 **Network** 标签，查看请求：

**预期请求 URL**:
```
POST http://localhost:8000/api/v1/control/strategies/instances
```

**预期 Request Payload** ✅:
```json
{
  "template_id": "dhs_peak_hours",
  "strategy_name": "测试策略",
  "configured_params": {
    "affected_edges": ["-8712", "-15452.627", ...],
    "intervals": [
      {
        "begin_hours": 0,
        "end_hours": 7,
        "status": "CLOSED",
        "allowed_vehicle_types": ["emergency"]
      },
      {
        "begin_hours": 7,
        "end_hours": 9,
        "status": "OPEN",
        "allowed_vehicle_types": ["passenger", "bus"]
      },
      // ... more intervals
    ],
    "hard_shoulder_lane_index": -1,
    "allowed_vehicle_types": ["passenger", "bus"]
  }
}
```

**关键检查点**:
- ✅ `configured_params` 中包含 **"intervals"** 字段
- ✅ `intervals` 是一个数组，包含 5 个对象
- ✅ 每个对象包含 `begin_hours`, `end_hours`, `status`, `allowed_vehicle_types`

**如果 Payload 缺少 "intervals"** = ❌ **参数提取逻辑有问题**

#### 4.4 检查响应

**预期响应** ✅ (Status 200):
```json
{
  "strategy_id": "strategy_dhs_peak_hours_20251030_021234",
  "message": "Strategy instance created successfully",
  "file_path": "control_data/strategies/strategy_dhs_peak_hours_20251030_021234.json"
}
```

**如果收到 400 错误** ❌:
```json
{
  "detail": "Parameter validation failed: Required parameter 'intervals' not provided"
}
```

说明模板继承仍未解析，后端验证失败。

---

## 故障排查

### 问题 A: 时间轴不显示

**原因**: 前端渲染逻辑问题

**解决方案**:
1. 强制刷新页面（`Ctrl+F5`）
2. 清除浏览器缓存
3. 查看控制台是否有 JavaScript 错误
4. 运行诊断脚本：`fix_dhs_timeline.js`（见 `DHS_QUICK_FIX.md`）

---

### 问题 B: 参数列表缺少 "intervals"

**原因**: 后端模板继承未解析

**检查步骤**:

#### 1. 检查服务器日志

在服务器终端窗口查找：
```
INFO: Resolving inheritance for template: dhs_peak_hours
```

**如果没有此日志**:
- 说明 `_resolve_template_inheritance()` 未被调用
- 可能是 uvicorn 自动重载失败

**解决方案**:
```powershell
# 停止服务器（Ctrl+C）
# 重新启动
.\start_api.ps1
```

#### 2. 手动测试 API

在浏览器访问（或用 curl/Postman）：
```
GET http://localhost:8000/api/v1/control/templates/dhs_peak_hours
```

**预期响应** ✅:
```json
{
  "template_id": "dhs_peak_hours",
  "parameters_schema": [
    {
      "parameter_name": "affected_edges",
      ...
    },
    {
      "parameter_name": "intervals",  // ← 应该存在
      "parameter_type": "dhs_interval_array",
      ...
    },
    {
      "parameter_name": "hard_shoulder_lane_index",
      ...
    },
    {
      "parameter_name": "allowed_vehicle_types",
      ...
    }
  ]
}
```

**如果响应中缺少 "intervals" 参数**:
- 说明后端代码未生效
- 需要手动重启服务器

#### 3. 检查代码修改

确认 `shared/control_tools/template_loader.py` 的修改已保存：

```python
# Line 458-466 应该包含：
if data.get("template_id") == template_id:
    # ✅ [NEW] Resolve template inheritance if needed
    try:
        if "extends" in data:
            logger.info(f"Resolving inheritance for template: {template_id}")
            data = _resolve_template_inheritance(data, templates_dir)
    except Exception as e:
        logger.error(f"Failed to resolve template inheritance for {template_id}: {e}")
        return None
```

如果代码缺失或被还原，需要重新应用修改。

---

### 问题 C: 策略创建失败（400 错误）

**错误消息**:
```
Parameter validation failed: Required parameter 'intervals' not provided
```

**原因**: 前端参数提取成功，但后端验证失败

**可能原因**:
1. 模板继承未解析（同问题 B）
2. 参数提取逻辑选择器错误（不太可能，已验证）

**解决方案**:
- 优先排查问题 B（模板继承）
- 检查 Network 请求 Payload 是否包含 "intervals"
- 如果 Payload 正确但后端仍报错，查看后端日志详细错误

---

## 验证成功标志

✅ **全部通过，修复成功**：
- [ ] 时间轴正常显示（表格上方）
- [ ] 时间轴有 5 个时间槽，颜色正确
- [ ] 控制台输出参数列表包含 "intervals"
- [ ] Network 请求 Payload 包含 "intervals" 数组
- [ ] 策略创建成功（200 响应）
- [ ] 服务器日志显示 "Resolving inheritance for template: dhs_peak_hours"

✅ **如果所有步骤都通过，说明 DHS 模板继承问题已完全修复！**

---

## 测试其他 DHS 模板（可选）

为确保修复适用于所有 DHS 模板，可以测试：

1. **dhs_passenger_only** (仅允许客车使用应急车道)
2. **dhs_peak_multi_interval** (多时段应急车道控制)

每个模板都应：
- ✅ 显示时间轴
- ✅ 包含 "intervals" 参数
- ✅ 策略创建成功

---

## 需要帮助？

如果验证过程中遇到问题，请提供：

1. **浏览器控制台截图**（包含参数列表输出）
2. **Network 请求截图**（Payload 和 Response）
3. **服务器日志**（特别是 "Resolving inheritance" 相关日志）
4. **时间轴状态**（是否显示，如何显示）

这样可以快速定位问题。

---

**验证预计时间**: 5 分钟
**文档创建时间**: 2025-10-30
