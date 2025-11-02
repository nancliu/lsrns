# TEC策略格式统一方案（严格版 - 无回退）

## 设计原则

**严格统一，无回退策略**：
- ✅ 所有edges**只**存储在`parameters`中
- ✅ 顶层`affected_edges`字段**移除**或仅作为只读派生字段
- ❌ 不检查顶层字段（避免冗余逻辑）
- ❌ 不支持旧格式（强制迁移）

## 目标格式（最终状态）

```json
{
  "strategy_id": "...",
  "strategy_name": "...",
  "template_id": "...",
  "strategy_type": "VSS|DHS|TEC",
  "parameters": {
    // VSS/DHS
    "affected_edges": [...],
    "speed_steps": [...],  // 或其他参数
    // 或 TEC
    "entrance_edges": [...],
    "flow_intervals": [...]
  },
  // 顶层affected_edges字段被移除，或仅作为计算属性（不存储）
  "metadata": {...},
  "template": {...}
}
```

**关键点**：
- `parameters` 是**唯一数据源**
- 不再有顶层的 `affected_edges` 字段（或完全忽略它）

## 需要修改的地方

### 1. API创建策略逻辑 ✅ P0 - 核心修改

**文件**: `api/services/strategy_instance_service.py`

**位置**: `create_strategy()` 方法（约第295行）

**修改前**:
```python
strategy = {
    "parameters": processed_parameters,  # 不包含affected_edges
    "affected_edges": request.affected_edges,  # 顶层
}
```

**修改后**:
```python
# 将所有edges放入parameters（统一处理）
if strategy_type in ["VSS", "DHS"]:
    processed_parameters["affected_edges"] = request.affected_edges
elif strategy_type == "TEC":
    # TEC使用entrance_edges
    processed_parameters["entrance_edges"] = request.affected_edges

# 不再设置顶层affected_edges（或设为空数组作为占位符）
strategy = {
    "parameters": processed_parameters,  # 包含edges
    "affected_edges": [],  # 空数组（占位符，或完全移除）
}
```

**或者更激进**：完全移除顶层字段
```python
strategy = {
    "parameters": processed_parameters,  # 包含edges
    # 不再有affected_edges字段
}
```

### 2. XML生成代码 ✅ P0 - 核心修改

**文件**: `shared/control_tools/additional_generator.py`

#### 2.1 VSS XML生成

**位置**: `generate_vss_xml()` (第82行)

**修改前**:
```python
affected_edges = parameters.get("affected_edges", [])
```

**修改后**:
```python
# 严格从parameters获取，无回退
affected_edges = parameters.get("affected_edges", [])
if not affected_edges:
    raise ValueError(f"VSS strategy requires affected_edges in parameters")
```

#### 2.2 DHS XML生成

**位置**: `generate_dhs_xml()` (第159行)

**修改前**:
```python
affected_edges = parameters.get("affected_edges", [])
```

**修改后**:
```python
# 严格从parameters获取，无回退
affected_edges = parameters.get("affected_edges", [])
if not affected_edges:
    raise ValueError(f"DHS strategy requires affected_edges in parameters")
```

#### 2.3 TEC XML生成

**位置**: `_generate_tec_metering_xml()` (第284行)

**当前状态**: ✅ 已正确（从parameters获取entrance_edges）

**需要移除**: 回退逻辑（第287-291行）

**修改后**:
```python
# 严格从parameters获取，无回退
entrance_edges = parameters.get("entrance_edges", [])
if not entrance_edges:
    raise ValueError("TEC metering requires entrance_edges in parameters")
```

### 3. 方案XML生成 ✅ P0 - 核心修改

**文件**: `shared/control_tools/additional_generator.py`

**位置**: `generate_plan_additional()` (第529-560行)

**修改前**:
```python
template = strategy.get("template", {})
parameters = strategy.get("parameters", {})
# 直接使用parameters（可能缺少edges）
```

**修改后**:
```python
template = strategy.get("template", {})
parameters = strategy.get("parameters", {})

# 验证edges在parameters中（严格检查，不补全）
strategy_type = strategy.get("strategy_type", "")
if strategy_type in ["VSS", "DHS"]:
    if "affected_edges" not in parameters:
        raise ValueError(f"Strategy {strategy.get('strategy_id')} missing affected_edges in parameters")
elif strategy_type == "TEC":
    if "entrance_edges" not in parameters:
        raise ValueError(f"Strategy {strategy.get('strategy_id')} missing entrance_edges in parameters")

# 验证通过后生成XML
strategy_xml = generate_strategy_xml(...)
```

### 4. 策略加载和显示 ✅ P1 - 必须修改

**文件**: `api/services/strategy_instance_service.py`

**位置**: `get_strategy()` 方法（第360-375行）

**修改前**:
```python
if "affected_edges" in strategy:
    edge_ids = strategy.get("affected_edges", [])
elif "configured_params" in strategy:
    # 从configured_params获取
```

**修改后**:
```python
# 严格从parameters获取edges
parameters = strategy.get("parameters", {})
if strategy_type == "TEC":
    edge_ids = parameters.get("entrance_edges", [])
else:
    # VSS/DHS
    edge_ids = parameters.get("affected_edges", [])
    
# 如果parameters中没有，说明格式错误
if not edge_ids:
    logger.warning(f"Strategy {strategy_id} has no edges in parameters")
```

### 5. 策略索引更新 ✅ P1 - 必须修改

**文件**: `shared/control_tools/strategy_file_manager.py`

**位置**: `_update_index_after_save()` (第484-498行)

**修改前**:
```python
# 复杂的回退逻辑（从顶层、configured_params等多个地方获取）
if "affected_edges" in strategy:
    edges_count = len(strategy["affected_edges"])
elif "configured_params" in strategy:
    ...
```

**修改后**:
```python
# 严格从parameters计算edges_count
parameters = strategy.get("parameters", {})
strategy_type = strategy.get("strategy_type", "")

if strategy_type == "TEC":
    entrance_edges = parameters.get("entrance_edges", [])
    edges_count = len(entrance_edges) if isinstance(entrance_edges, list) else 0
else:
    # VSS/DHS
    affected_edges = parameters.get("affected_edges", [])
    edges_count = len(affected_edges) if isinstance(affected_edges, list) else 0
```

### 6. 策略文件管理器 ✅ P1 - 必须修改

**文件**: `shared/control_tools/strategy_file_manager.py`

**位置**: `regenerate_index()` (第299-310行)

**修改前**:
```python
# 从configured_params计算edges_count
configured_params = strategy.get("configured_params", {})
if strategy_type == "TEC":
    entrance_edge = configured_params.get("entrance_edge", "")
    edges_count = 1 if entrance_edge else 0
else:
    affected_edges = configured_params.get("affected_edges", [])
    edges_count = len(affected_edges) if isinstance(affected_edges, list) else 0
```

**修改后**:
```python
# 严格从parameters计算edges_count
parameters = strategy.get("parameters", {})
if strategy_type == "TEC":
    entrance_edges = parameters.get("entrance_edges", [])
    edges_count = len(entrance_edges) if isinstance(entrance_edges, list) else 0
else:
    affected_edges = parameters.get("affected_edges", [])
    edges_count = len(affected_edges) if isinstance(affected_edges, list) else 0
```

### 7. 修复脚本更新 ✅ P0 - 关键

**文件**: `scripts/fix_strategy_structure.py`

**位置**: `convert_strategy_to_api_format()` (第49行)

**修改**:
1. 确保所有edges都在parameters中
2. **移除顶层affected_edges字段**（或设为空数组）
3. **不保留旧格式的任何痕迹**

**修改后**:
```python
def convert_strategy_to_api_format(strategy: Dict[str, Any]) -> Dict[str, Any]:
    # ... 现有代码 ...
    
    # 4. 构建新的策略结构（严格格式）
    new_strategy = {
        "strategy_id": strategy["strategy_id"],
        "strategy_name": strategy["strategy_name"],
        "template_id": template_id,
        "template_name": ...,
        "strategy_type": strategy_type,
        "parameters": parameters,  # 包含所有edges
        # 不再设置顶层affected_edges（完全移除）
        "metadata": metadata,
    }
    
    # 移除顶层affected_edges字段（如果存在）
    if "affected_edges" in new_strategy:
        del new_strategy["affected_edges"]
    
    return new_strategy
```

### 8. 请求模型更新 ✅ P2 - 可选

**文件**: `api/models/requests/strategy_requests.py`

**考虑**: API请求模型中的`affected_edges`字段如何处理？

**选项A**: 保留（API层仍使用affected_edges，但创建时映射到parameters）
```python
# 请求时仍使用affected_edges（统一接口）
# 创建时根据strategy_type映射到parameters中的对应字段
```

**选项B**: 根据strategy_type使用不同字段名（更严格但API不一致）
```python
# VSS/DHS: affected_edges
# TEC: entrance_edges
```

**推荐**: 选项A（API层保持统一，内部映射）

### 9. 前端代码 ✅ 已正确（无需修改）

**文件**: `frontend/control/templates.html`

**状态**: ✅ 已经将edges放入parameters（`collectParameterValues()`）

**注意**: `buildStrategyPayload()`也会放入顶层`affected_edges`，这是正确的（API要求），但服务端会将其映射到parameters。

## 修改清单（无回退版本）

| 文件 | 位置 | 修改内容 | 优先级 | 影响范围 |
|------|------|---------|--------|---------|
| `api/services/strategy_instance_service.py` | `create_strategy()` | edges放入parameters，移除顶层 | P0 | 新创建策略 |
| `shared/control_tools/additional_generator.py` | `generate_vss_xml()` | 只从parameters获取，无回退 | P0 | VSS XML生成 |
| `shared/control_tools/additional_generator.py` | `generate_dhs_xml()` | 只从parameters获取，无回退 | P0 | DHS XML生成 |
| `shared/control_tools/additional_generator.py` | `_generate_tec_metering_xml()` | 移除回退逻辑 | P0 | TEC XML生成 |
| `shared/control_tools/additional_generator.py` | `generate_plan_additional()` | 验证edges在parameters中 | P0 | 方案XML生成 |
| `api/services/strategy_instance_service.py` | `get_strategy()` | 只从parameters提取edges | P1 | 策略详情API |
| `shared/control_tools/strategy_file_manager.py` | `_update_index_after_save()` | 只从parameters计算 | P1 | 索引更新 |
| `shared/control_tools/strategy_file_manager.py` | `regenerate_index()` | 只从parameters计算 | P1 | 索引重建 |
| `scripts/fix_strategy_structure.py` | `convert_strategy_to_api_format()` | 移除顶层affected_edges | P0 | 现有策略迁移 |

## 数据迁移步骤

### 步骤1：运行修复脚本（强制统一格式）

```bash
python scripts/fix_strategy_structure.py
```

脚本必须：
1. ✅ 将edges放入parameters
2. ✅ **移除顶层affected_edges字段**
3. ✅ 验证所有策略格式正确

### 步骤2：代码部署（一次性完成）

部署所有修改后的代码，确保：
- 不再读取顶层affected_edges
- 不再有回退逻辑
- 格式错误时直接报错（fail fast）

### 步骤3：验证

1. 创建新策略（VSS/DHS/TEC）→ 验证格式正确
2. 生成XML → 验证从parameters获取edges
3. 生成方案 → 验证所有策略格式统一

## 错误处理策略

**严格模式 - Fail Fast**：
- 如果parameters中缺少edges → **直接抛出异常**
- 不尝试修复或补全
- 明确的错误信息，方便调试

```python
# 示例
if "affected_edges" not in parameters:
    raise ValueError(
        f"Strategy {strategy_id} (type: {strategy_type}) "
        f"missing required 'affected_edges' in parameters. "
        f"Available keys: {list(parameters.keys())}"
    )
```

## 优势

1. ✅ **代码简洁**：无需回退逻辑，代码路径单一
2. ✅ **维护性强**：只有一种格式，维护成本低
3. ✅ **错误明确**：格式错误立即发现，不会静默失败
4. ✅ **性能更好**：无需多次检查多个字段
5. ✅ **格式统一**：所有策略类型格式完全一致

## 风险与应对

### 风险1：现有策略格式错误

**应对**：
- 修复脚本强制转换所有策略
- 部署前运行验证脚本确认格式正确

### 风险2：部分策略迁移失败

**应对**：
- 修复脚本输出详细报告
- 手动检查并修复失败项

### 风险3：前端仍将edges放入顶层

**应对**：
- 检查前端代码（已确认前端将edges放入parameters）
- API层在创建时确保映射正确

## 实施顺序

1. **准备阶段**：
   - 更新修复脚本（移除顶层字段）
   - 更新所有读取edges的代码（移除回退逻辑）

2. **测试阶段**：
   - 在测试环境运行修复脚本
   - 验证所有策略格式正确
   - 测试XML生成功能

3. **部署阶段**：
   - 运行修复脚本（生产环境）
   - 部署新代码
   - 监控错误日志

4. **验证阶段**：
   - 创建新策略验证格式
   - 生成方案验证XML
   - 确认无回退逻辑触发

## 总结

严格统一方案的核心：
- ✅ **单一数据源**：parameters是唯一数据源
- ✅ **无回退逻辑**：格式错误直接报错
- ✅ **完全迁移**：修复脚本移除所有旧格式痕迹
- ✅ **代码简洁**：维护成本低，错误明确

这样虽然迁移时可能有短期风险，但长期维护成本更低，代码更清晰。

