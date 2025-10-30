# DHS 模板继承修复 - 快速验证指南

## 问题确认

✅ **修改位置正确**: `shared/control_tools/template_loader.py` Lines 459-466
✅ **模板结构正确**:
   - **dhs_peak_hours.json** (子模板) - 模板名称: **"应急车道开放"**
   - **extends**: "dhs_base"
   - **继承参数**: affected_edges, intervals, hard_shoulder_lane_index (来自 dhs_base)
   - **自有参数**: allowed_vehicle_types

## 当前状态

⚠️ **服务器未运行**: 因为在 conda base 环境下启动脚本拒绝启动
⚠️ **测试脚本失败**: 因为 base 环境缺少 pydantic 等依赖

## 解决方案

### 方法 1: 正确启动服务器（推荐）

#### 步骤 1: 打开新的 PowerShell 窗口

不要在当前窗口，新开一个 PowerShell。

#### 步骤 2: 激活 od_project 环境

```powershell
conda activate od_project
```

确认命令提示符变成：
```
(od_project) PS C:\...>
```

#### 步骤 3: 启动服务器

```powershell
cd D:\projects\OD_SIM
.\start_api.ps1
```

等待启动完成（看到 "Application startup complete"）。

#### 步骤 4: 验证修复

1. **打开浏览器**: `http://localhost:8000/control/templates.html`

2. **选择策略类型**: 应急车道开放（DHS）

3. **选择模板**: **"应急车道开放"** （这是 dhs_peak_hours 的显示名称）

4. **选择路段**: 任意选择一个路段（例如 G4202 逆时针段）

5. **进入参数配置**: 点击"下一步"

6. **检查时间轴**: 表格上方应该显示 24 小时时间轴

7. **验证参数**: 打开控制台（F12），运行：
   ```javascript
   console.log(window.currentTemplate.parameters_schema.map(p => p.parameter_name))
   ```

   **预期输出**:
   ```javascript
   ["affected_edges", "intervals", "hard_shoulder_lane_index", "allowed_vehicle_types"]
   ```

   ✅ 如果看到 **4 个参数**（包括 "intervals"），说明继承解析成功！
   ❌ 如果只看到 **1 个参数**（只有 "allowed_vehicle_types"），说明继承解析失败。

8. **测试策略创建**:
   - 填写必填参数（表格已有默认值）
   - hard_shoulder_lane_index 输入 `-1` 或 `0`
   - 点击"生成策略实例"
   - 应该成功创建（200 响应），无 "intervals not provided" 错误

---

### 方法 2: 直接测试 API 端点（如果服务器已在其他地方运行）

如果你在其他地方已经启动了服务器（在 od_project 环境下），可以直接测试 API：

#### 在浏览器访问:

```
http://localhost:8000/api/v1/control/templates/dhs_peak_hours
```

#### 预期响应（JSON）:

查找 `parameters_schema` 数组，应该包含 4 个参数对象：

```json
{
  "template_id": "dhs_peak_hours",
  "template_name": "应急车道开放",
  "parameters_schema": [
    {
      "parameter_name": "affected_edges",
      ...
    },
    {
      "parameter_name": "intervals",  // ← 这个参数来自父模板 dhs_base
      "parameter_type": "dhs_interval_array",
      "required": true,
      "default_value": [
        {"begin_hours": 0, "end_hours": 7, "status": "CLOSED", ...},
        {"begin_hours": 7, "end_hours": 9, "status": "OPEN", ...},
        ...
      ],
      ...
    },
    {
      "parameter_name": "hard_shoulder_lane_index",
      ...
    },
    {
      "parameter_name": "allowed_vehicle_types",  // ← 这个参数来自子模板自己
      ...
    }
  ]
}
```

✅ **如果响应包含 "intervals" 参数，说明继承解析成功！**

---

### 方法 3: 使用 curl 测试（命令行）

如果服务器已运行，可以用 curl 测试：

```powershell
# PowerShell
curl http://localhost:8000/api/v1/control/templates/dhs_peak_hours | ConvertFrom-Json | Select-Object -ExpandProperty parameters_schema | Select-Object parameter_name

# Git Bash
curl http://localhost:8000/api/v1/control/templates/dhs_peak_hours | jq '.parameters_schema[].parameter_name'
```

**预期输出**:
```
affected_edges
intervals
hard_shoulder_lane_index
allowed_vehicle_types
```

---

## 关键验证点

| 检查项 | 预期结果 | 说明 |
|--------|----------|------|
| 参数数量 | 4 个 | 3 个来自父模板 + 1 个来自子模板 |
| intervals 参数 | ✅ 存在 | 来自父模板 dhs_base，证明继承解析成功 |
| 时间轴渲染 | ✅ 显示 | 表格上方显示 24 小时时间轴，5 个时间槽 |
| 策略创建 | ✅ 成功 | 无 "intervals not provided" 错误 |
| 服务器日志 | ✅ 显示 | `INFO: Resolving inheritance for template: dhs_peak_hours` |

---

## 常见问题

### Q: 为什么我找不到"应急车道开放 - 早晚高峰"模板？

**A**: 模板显示名称是 **"应急车道开放"**（来自 template_name 字段），不是"应急车道开放 - 早晚高峰"。

模板文件 `dhs_peak_hours.json` 的 `template_name` 字段值为：
```json
"template_name": "应急车道开放"
```

### Q: 我该选择哪个模板测试？

**A**: DHS 类型下有 3 个模板：
1. **应急车道开放** (dhs_peak_hours) - 高峰期开放
2. **应急车道开放 - 仅允许客车** (dhs_passenger_only) - 限制车型
3. **应急车道开放 - 多时段控制** (dhs_peak_multi_interval) - 多个时间段

任何一个都可以测试，它们都继承自 `dhs_base`，都应该包含 `intervals` 参数。

### Q: 如果 API 返回的参数列表中没有 intervals 怎么办？

**A**: 说明以下可能：
1. **uvicorn 自动重载失败**: 手动重启服务器
2. **代码修改未保存**: 检查 `template_loader.py` Lines 459-466
3. **缓存问题**: 清除浏览器缓存（Ctrl+F5）

### Q: 修改的代码是否正确？

**A**: ✅ 已确认正确。

查看 `shared/control_tools/template_loader.py` Lines 459-466：
```python
if data.get("template_id") == template_id:
    # Resolve template inheritance if needed
    try:
        if "extends" in data:
            logger.info(f"Resolving inheritance for template: {template_id}")
            data = _resolve_template_inheritance(data, templates_dir)
    except Exception as e:
        logger.error(f"Failed to resolve template inheritance for {template_id}: {e}")
        return None
```

这段代码会在加载包含 `extends` 字段的模板时调用 `_resolve_template_inheritance()` 函数，合并父模板参数。

---

## 下一步行动

1. **在新的 PowerShell 窗口激活 od_project 环境**
2. **启动服务器** (`.\start_api.ps1`)
3. **访问前端或 API 端点验证**
4. **确认参数列表包含 "intervals"**
5. **测试策略创建功能**

如果所有步骤通过，说明修复完全成功！

---

**文档创建时间**: 2025-10-30
**修复位置**: `shared/control_tools/template_loader.py:459-466`
**模板名称**: "应急车道开放" (dhs_peak_hours)
