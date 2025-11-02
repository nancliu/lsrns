# TEC策略格式统一分析与修改方案

## 问题背景

当前TEC策略存在格式不一致的问题：
- `entrance_edges` 在 `parameters` 中（XML生成需要）
- `affected_edges` 在顶层（空数组，API格式要求）
- VSS/DHS策略：`affected_edges` 在顶层，但XML生成代码期望在parameters中

这种不一致会在生成sumocfg时造成问题，因为不同框架可能期望不同的数据结构。

## 当前状态分析

### 1. 数据流追踪

#### 前端创建TEC策略
```
EdgeSelector选择edges 
  ↓
collectParameterValues() 将entrance_edges放入parameters
  ↓
buildStrategyPayload() 将edges放入顶层affected_edges
  ↓
API请求: { parameters: {entrance_edges: [...]}, affected_edges: [...] }
```

#### API创建策略
```python
# api/services/strategy_instance_service.py:246
strategy = {
    "parameters": processed_parameters,  # 包含entrance_edges（TEC）
    "affected_edges": request.affected_edges,  # 顶层（TEC为空或忽略）
}
```

#### XML生成
```python
# shared/control_tools/additional_generator.py
# VSS/DHS: 从parameters获取（但实际在顶层）❌ 不一致
affected_edges = parameters.get("affected_edges", [])

# TEC: 从parameters获取entrance_edges ✅ 正确
entrance_edges = parameters.get("entrance_edges", [])
```

#### 方案生成
```python
# shared/control_tools/plan_file_manager.py:332
strategies = get_plan_strategies(plan_id)  # 加载完整策略实例
  ↓
generate_plan_additional(strategies)  # 从策略的parameters中提取数据
  ↓
XML生成：期望edges在parameters中
```

### 2. 问题识别

#### 问题1：VSS/DHS XML生成可能失败
```python
# 当前实现（可能失败）
affected_edges = parameters.get("affected_edges", [])  # 返回空，因为不在parameters中
```

**实际位置**：`strategy["affected_edges"]`（顶层）

#### 问题2：TEC双重存储
- `entrance_edges` 在 `parameters` 中（正确，XML生成需要）
- `affected_edges` 在顶层（冗余，API格式要求）

#### 问题3：sumocfg生成时的风险
当使用不同框架生成sumocfg时：
- **框架A**：期望edges在parameters中 → TEC正常，VSS/DHS失败
- **框架B**：期望edges在顶层 → VSS/DHS正常，TEC失败
- **框架C**：统一接口期望edges在parameters → 需要统一格式

## 统一方案选择

### 方案A：统一为edges在parameters中（推荐）✅

**优点**：
1. XML生成代码已经期望edges在parameters中（TEC已正确）
2. 与模板schema定义一致（模板中定义了edges参数）
3. 统一接口，所有策略类型格式一致
4. 前端逻辑无需大改（已经将edges放入parameters）

**缺点**：
1. 需要修改API创建逻辑（将affected_edges也放入parameters）
2. 需要修改VSS/DHS的XML生成代码（从parameters获取，不是顶层）
3. 顶层的affected_edges字段仍然保留（向后兼容，但可能冗余）

### 方案B：统一为edges在顶层（不推荐）❌

**缺点**：
1. XML生成代码需要大幅修改（TEC需要从顶层获取）
2. 与模板schema不一致（模板定义了edges参数，但不在parameters中）
3. TEC需要特殊处理（entrance_edges需要映射到affected_edges）
4. 不符合"参数化配置"的设计理念

## 推荐方案详细设计（方案A）

### 目标格式

所有策略类型统一为：
```json
{
  "strategy_id": "...",
  "strategy_name": "...",
  "template_id": "...",
  "strategy_type": "VSS|DHS|TEC",
  "parameters": {
    "affected_edges": [...],  // VSS/DHS
    // 或
    "entrance_edges": [...],   // TEC
    // 其他参数...
  },
  "affected_edges": [...],  // 顶层（向后兼容，从parameters派生）
  "metadata": {...},
  "template": {...}
}
```

**关键点**：
- `parameters` 是**唯一数据源**
- 顶层 `affected_edges` 从 `parameters` 派生（向后兼容）

### 需要修改的地方

#### 1. API创建策略逻辑 ✅ 必须修改

**文件**: `api/services/strategy_instance_service.py`

**位置**: `create_strategy()` 方法（约第295行）

**当前代码**:
```python
strategy = {
    "parameters": processed_parameters,  # 不包含affected_edges
    "affected_edges": request.affected_edges,  # 顶层
}
```

**修改为**:
```python
# 将affected_edges放入parameters（VSS/DHS）
if strategy_type in ["VSS", "DHS"]:
    processed_parameters["affected_edges"] = request.affected_edges

# TEC: entrance_edges已经在parameters中（前端已处理）
# 如果前端未处理，需要在这里添加
elif strategy_type == "TEC":
    # 确保entrance_edges在parameters中
    if "entrance_edges" not in processed_parameters:
        # 从顶层affected_edges获取（前端可能放入顶层）
        if request.affected_edges:
            processed_parameters["entrance_edges"] = request.affected_edges

strategy = {
    "parameters": processed_parameters,  # 包含affected_edges或entrance_edges
    "affected_edges": request.affected_edges,  # 顶层（向后兼容）
}
```

#### 2. VSS/DHS XML生成 ✅ 必须修改

**文件**: `shared/control_tools/additional_generator.py`

**位置**: `generate_vss_xml()` (第82行) 和 `generate_dhs_xml()` (第159行)

**当前代码**:
```python
# VSS
affected_edges = parameters.get("affected_edges", [])

# DHS
affected_edges = parameters.get("affected_edges", [])
```

**修改为**:
```python
# VSS - 支持从parameters或顶层获取（向后兼容）
def generate_vss_xml(strategy_id, template, parameters, strategy_dict=None):
    # 优先从parameters获取
    affected_edges = parameters.get("affected_edges", [])
    
    # 向后兼容：如果parameters中没有，尝试从顶层获取
    if not affected_edges and strategy_dict:
        affected_edges = strategy_dict.get("affected_edges", [])
    
    if not affected_edges:
        logger.warning(f"VSS strategy {strategy_id} has no affected_edges")
    
    # ... 后续代码

# DHS - 同样修改
def generate_dhs_xml(strategy_id, template, parameters, strategy_dict=None):
    affected_edges = parameters.get("affected_edges", [])
    if not affected_edges and strategy_dict:
        affected_edges = strategy_dict.get("affected_edges", [])
    # ... 后续代码
```

**但是**：由于`generate_strategy_xml()`只传递了`template`和`parameters`，没有传递完整的`strategy_dict`。

**更好的方案**：修改`generate_plan_additional()`，确保传入完整的strategy对象，然后XML生成函数可以从strategy中提取parameters，同时也有访问顶层字段的能力。

#### 3. 方案XML生成调用链 ✅ 必须修改

**文件**: `shared/control_tools/additional_generator.py`

**位置**: `generate_plan_additional()` (第529-537行，第553-560行)

**当前代码**:
```python
template = strategy.get("template", {})
parameters = strategy.get("parameters", {})
strategy_xml = generate_strategy_xml(
    template_id=strategy.get("template_id", ""),
    template=template,
    parameters=parameters
)
```

**修改为**:
```python
template = strategy.get("template", {})
parameters = strategy.get("parameters", {})

# 确保edges在parameters中（统一处理）
strategy_type = strategy.get("strategy_type", "")
if strategy_type in ["VSS", "DHS"]:
    # 如果parameters中没有affected_edges，从顶层补充
    if "affected_edges" not in parameters:
        top_level_edges = strategy.get("affected_edges", [])
        if top_level_edges:
            parameters["affected_edges"] = top_level_edges
elif strategy_type == "TEC":
    # 确保entrance_edges在parameters中
    if "entrance_edges" not in parameters:
        top_level_edges = strategy.get("affected_edges", [])
        if top_level_edges:
            parameters["entrance_edges"] = top_level_edges

strategy_xml = generate_strategy_xml(
    template_id=strategy.get("template_id", ""),
    template=template,
    parameters=parameters
)
```

#### 4. 前端TEC策略创建 ✅ 需要确认

**文件**: `frontend/control/templates.html`

**位置**: `collectParameterValues()` (第3343行)

**当前代码**:
```javascript
if (['affected_edges', 'entrance_edges', ...].includes(param.parameter_name)) {
    // 将edges放入parameters
    configuredParams[param.parameter_name] = edgeIds;
}
```

**状态**: ✅ **已经正确** - TEC的entrance_edges会被放入parameters

**需要确认**: `buildStrategyPayload()` 也会将edges放入顶层`affected_edges`，这是正确的（向后兼容）。

#### 5. 策略加载和显示 ✅ 需要适配

**文件**: `api/services/strategy_instance_service.py`

**位置**: `get_strategy()` 方法（第360-375行）

**当前代码**:
```python
# 从顶层获取edge_ids
if "affected_edges" in strategy:
    edge_ids = strategy.get("affected_edges", [])
```

**修改为**:
```python
# 统一从parameters中提取edges
parameters = strategy.get("parameters", {})
if strategy_type == "TEC":
    edge_ids = parameters.get("entrance_edges", [])
    # 如果没有，回退到顶层affected_edges（向后兼容）
    if not edge_ids:
        edge_ids = strategy.get("affected_edges", [])
else:
    # VSS/DHS
    edge_ids = parameters.get("affected_edges", [])
    # 如果没有，回退到顶层（向后兼容）
    if not edge_ids:
        edge_ids = strategy.get("affected_edges", [])
```

#### 6. 策略索引更新 ✅ 需要适配

**文件**: `shared/control_tools/strategy_file_manager.py`

**位置**: `_update_index_after_save()` (第484-498行)

**当前代码**:
```python
# 计算edges_count
if "affected_edges" in strategy:
    edges_count = len(strategy["affected_edges"])
elif "configured_params" in strategy:
    if strategy_type == "TEC":
        entrance_edge = configured_params.get("entrance_edge", "")
        edges_count = 1 if entrance_edge else 0
    else:
        affected_edges = configured_params.get("affected_edges", [])
        edges_count = len(affected_edges) if isinstance(affected_edges, list) else 0
```

**修改为**:
```python
# 统一从parameters中计算edges_count
parameters = strategy.get("parameters", {})
if strategy_type == "TEC":
    entrance_edges = parameters.get("entrance_edges", [])
    edges_count = len(entrance_edges) if isinstance(entrance_edges, list) else 0
    # 向后兼容
    if edges_count == 0:
        edges_count = len(strategy.get("affected_edges", []))
else:
    # VSS/DHS
    affected_edges = parameters.get("affected_edges", [])
    edges_count = len(affected_edges) if isinstance(affected_edges, list) else 0
    # 向后兼容
    if edges_count == 0:
        edges_count = len(strategy.get("affected_edges", []))
```

### 修改清单

| 文件 | 位置 | 修改类型 | 优先级 | 说明 |
|------|------|---------|--------|------|
| `api/services/strategy_instance_service.py` | `create_strategy()` | 核心修改 | P0 | 将affected_edges放入parameters |
| `shared/control_tools/additional_generator.py` | `generate_plan_additional()` | 适配修改 | P0 | 确保edges在parameters中 |
| `api/services/strategy_instance_service.py` | `get_strategy()` | 适配修改 | P1 | 从parameters提取edges |
| `shared/control_tools/strategy_file_manager.py` | `_update_index_after_save()` | 适配修改 | P1 | 从parameters计算edges_count |
| `scripts/fix_strategy_structure.py` | `convert_strategy_to_api_format()` | 修复脚本 | P1 | 确保修复后的策略格式正确 |
| `shared/control_tools/additional_generator.py` | `generate_vss_xml()` | 向后兼容 | P2 | 支持从顶层回退（如果parameters中没有） |
| `shared/control_tools/additional_generator.py` | `generate_dhs_xml()` | 向后兼容 | P2 | 支持从顶层回退 |

### 向后兼容策略

1. **顶层`affected_edges`字段保留**：确保旧代码和旧数据仍能工作
2. **优先级规则**：优先使用`parameters`中的edges，如果不存在则回退到顶层
3. **数据迁移**：运行修复脚本确保现有策略格式正确

### 测试要点

1. **创建新策略**：
   - [ ] VSS策略：affected_edges在parameters中
   - [ ] DHS策略：affected_edges在parameters中
   - [ ] TEC策略：entrance_edges在parameters中

2. **XML生成**：
   - [ ] VSS XML正确生成（从parameters获取edges）
   - [ ] DHS XML正确生成（从parameters获取edges）
   - [ ] TEC XML正确生成（从parameters获取entrance_edges）

3. **方案生成**：
   - [ ] 混合策略方案（VSS+DHS+TEC）XML生成正确
   - [ ] sumocfg引用control.add.xml正确

4. **向后兼容**：
   - [ ] 旧格式策略（edges在顶层）仍能正常加载和生成XML
   - [ ] 修复脚本正确转换旧格式

### 风险点

1. **高风险**：如果修改不完整，可能导致XML生成失败，进而影响sumocfg生成
2. **中风险**：向后兼容代码如果实现不当，可能在某些边界情况下失败
3. **低风险**：前端逻辑基本不需要修改（已经正确）

### 实施建议

1. **分阶段实施**：
   - 阶段1：修改API创建逻辑（确保新创建的策略格式正确）
   - 阶段2：修改XML生成适配（确保新旧格式都能处理）
   - 阶段3：运行修复脚本（统一现有策略格式）
   - 阶段4：测试验证（确保所有场景正常工作）

2. **验证顺序**：
   - 先修改API创建逻辑，创建测试策略验证格式
   - 再修改XML生成，验证新旧格式都能生成正确XML
   - 最后修复现有策略，确保一致性

3. **回滚方案**：
   - 保留修改前的代码版本
   - 如果出现问题，可以快速回滚到兼容两种格式的版本

## 总结

统一TEC策略格式的关键是**将所有edges参数统一存储在`parameters`中**，这样：
1. ✅ 与模板schema定义一致
2. ✅ XML生成代码统一（都从parameters获取）
3. ✅ sumocfg生成时格式一致，避免跨框架问题
4. ✅ 符合"参数化配置"的设计理念

顶层`affected_edges`字段作为**向后兼容字段**保留，但不再是主要数据源。

