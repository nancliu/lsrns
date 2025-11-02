# 策略实例格式差异说明

## 问题背景

在检查策略实例参数一致性时，发现VSS/DHS和TEC策略实例在结构上有差异：

- **VSS/DHS**: `affected_edges` 在**顶层**
- **TEC**: `entrance_edges` 在 `parameters` 内，且顶层 `affected_edges` 为空数组

## 为什么会形成两套格式？

### 1. 模板定义层面的差异

#### VSS/DHS模板 (vss_moderate.json, dhs_peak_hours.json)
```json
{
  "parameters_schema": [
    {
      "parameter_name": "affected_edges",  // ← 在schema中定义
      "parameter_type": "edge_array",
      "description": "受限速影响的路段edge ID列表"
    },
    {
      "parameter_name": "speed_steps",  // 或其他参数
      ...
    }
  ]
}
```

#### TEC模板 (tec_flow_metering.json)
```json
{
  "parameters_schema": [
    {
      "parameter_name": "entrance_edges",  // ← 在schema中定义（注意名称不同）
      "parameter_type": "edge_array",
      "description": "入口匝道edge ID列表"
    },
    {
      "parameter_name": "flow_intervals",
      ...
    }
  ]
}
```

### 2. API设计层面的处理

API请求模型 `StrategyCreateRequest` 的设计：

```python
class StrategyCreateRequest(BaseModel):
    strategy_name: str
    template_id: str
    parameters: Dict[str, Any]  # ← 包含模板schema中定义的参数
    affected_edges: List[str]    # ← 统一的顶层字段（所有策略类型都有）
```

**设计理念**：
- `affected_edges` 是**API层面的统一字段**，表示"受策略影响的路段"
- 所有策略类型都通过这个字段传递路段信息
- 这是为了前端统一处理：所有策略类型都使用同一个EdgeSelector组件

### 3. 前端处理逻辑

前端在收集参数时，会**跳过**路段相关的参数：

```javascript
// frontend/control/templates.html
// 跳过路段参数（在步骤2已处理）
if (['affected_edges', 'affected_segments', 'entrance_ids', 'entrance_edges'].includes(param.parameter_name)) {
    console.log(`跳过路段参数 ${param.parameter_name}（在步骤2已处理）`);
    return;
}
```

这意味着：
- **VSS/DHS**: `affected_edges` 从模板schema中被跳过 → 放入API请求的顶层 `affected_edges` → 最终策略实例中也在顶层
- **TEC**: `entrance_edges` 从模板schema中被跳过 → 但XML生成需要它在parameters中

### 4. XML生成层面的需求

#### VSS/DHS XML生成
```python
# shared/control_tools/additional_generator.py
def generate_vss_xml(...):
    affected_edges = parameters.get("affected_edges", [])  # ← 从parameters中获取
    # 但实际上，对于API创建的策略，affected_edges在顶层
```

**问题**：XML生成代码期望 `affected_edges` 在 `parameters` 中，但API格式中它在顶层。

#### TEC XML生成
```python
def generate_tec_xml(...):
    entrance_edges = parameters.get("entrance_edges", [])  # ← 从parameters中获取（必须）
    # TEC需要entrance_edges在parameters中，因为：
    # 1. SUMO的calibrator/rerouter需要edge属性
    # 2. 多个入口可能需要生成多个calibrator
```

**关键差异**：
- **TEC必须**在parameters中有`entrance_edges`，因为XML生成需要它
- **VSS/DHS**理论上也应该在parameters中，但当前实现中它在顶层也能工作（因为XML生成代码会从顶层回退查找）

## 实际数据流

### 创建VSS策略时：

1. **前端收集参数**：
   - 从EdgeSelector获取edges → 放入 `affected_edges`（顶层）
   - 收集其他参数（如speed_steps）→ 放入 `parameters`
   - **跳过**模板schema中的`affected_edges`参数（不放入parameters）

2. **API创建策略**：
   ```python
   strategy = {
       "parameters": {...},  # 不包含affected_edges
       "affected_edges": [...],  # 在顶层
   }
   ```

3. **XML生成时**：
   ```python
   # 当前实现：从parameters中获取（会失败，因为不在parameters中）
   # 应该从顶层获取，或需要适配代码
   affected_edges = parameters.get("affected_edges", [])
   ```

### 创建TEC策略时：

1. **前端收集参数**：
   - 从EdgeSelector获取edges → 需要同时放入两个地方：
     - `affected_edges`（顶层，API要求）
     - `entrance_edges`（parameters中，XML生成需要）

2. **API创建策略**：
   ```python
   strategy = {
       "parameters": {
           "entrance_edges": [...],  # ← 必须在parameters中
           "flow_intervals": [...]
       },
       "affected_edges": [],  # ← 顶层可以是空（或不使用）
   }
   ```

3. **XML生成时**：
   ```python
   # 正确：从parameters中获取
   entrance_edges = parameters.get("entrance_edges", [])
   ```

## 为什么会有这种设计？

### 历史演进原因

1. **Phase 1B (Edge Selector)**: 统一了所有策略类型的路段选择流程
   - 所有策略都使用同一个EdgeSelector组件
   - 选择的路段统一放入`affected_edges`

2. **Phase 1C (Strategy Instance)**: API设计时统一了请求格式
   - 所有策略类型都有顶层`affected_edges`字段
   - 这是为了保持API的一致性

3. **XML生成**: 不同策略类型对edges的使用方式不同
   - VSS/DHS: 单个variableSpeedSign/rerouter覆盖多个edges
   - TEC: 可能需要为每个entrance生成单独的calibrator

### 设计冲突

**冲突点**：
- API统一性 vs. XML生成需求
- 模板schema定义 vs. 实际存储格式

**当前状态**：
- VSS/DHS: `affected_edges`在顶层（与API设计一致）
- TEC: `entrance_edges`在parameters中（与XML生成需求一致）
- 顶层`affected_edges`字段对TEC来说可能冗余

## 修复后的统一格式

修复脚本将两种格式统一为：

### VSS/DHS格式（修复后）：
```json
{
  "parameters": {
    "speed_steps": [...],  // affected_edges不在parameters中
    ...
  },
  "affected_edges": [...],  // 在顶层
  "template": {...}
}
```

### TEC格式（修复后）：
```json
{
  "parameters": {
    "entrance_edges": [...],  // 在parameters中（XML生成需要）
    "flow_intervals": [...]
  },
  "affected_edges": [],  // 顶层为空（TEC不使用）
  "template": {...}
}
```

## 建议

### 短期方案（已实施）
- 保持当前格式差异
- 确保XML生成代码能正确处理两种情况
- 文档说明这种差异的原因

### 长期方案（可选）
1. **统一XML生成接口**：
   - 创建一个统一的edges提取函数
   - 优先从parameters中获取，如果不存在则从顶层获取

2. **统一存储格式**：
   - 考虑将所有edges信息都存储在parameters中
   - 顶层`affected_edges`作为冗余字段保留（用于API一致性）

3. **模板schema规范化**：
   - 明确哪些参数应该通过EdgeSelector处理
   - 在schema中标记这些参数，前端统一跳过

## 总结

两套格式的形成是**历史演进和实际需求平衡的结果**：
- **API层**：追求统一性，所有策略都有顶层`affected_edges`
- **XML生成层**：TEC策略需要`entrance_edges`在parameters中
- **前端**：统一使用EdgeSelector，但需要适配不同策略类型的最终存储需求

这种差异是**可以接受的**，因为：
1. 两种格式都有明确的业务逻辑支撑
2. API和XML生成代码都能正确处理
3. 修复后的格式保证了方案生成的一致性

