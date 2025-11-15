# 流量激增场景架构重构方案

## 当前问题分析

### 代码重复问题

**当前架构**：
```
generate_flowsurge_scenarios.py
├── generate_control_params_vss()     # 重复！VSS参数生成逻辑
├── generate_control_params_tec()     # 重复！TEC参数生成逻辑
├── generate_control_params_dhs()     # 流量激增特有
└── 调用 scenario_generator.generate_scenario()
```

**其他事件类型**：
```
generate_scenarios_from_events.py
└── 直接调用 scenario_generator.generate_scenario()
    └── scenario_generator内部处理VSS/TEC参数
```

### 不一致风险

1. **参数生成逻辑重复**：
   - VSS的`speed_steps`计算逻辑在两个地方
   - TEC的`flow_intervals`计算逻辑在两个地方
   - 修改一处可能忘记修改另一处

2. **维护成本高**：
   - 时间计算逻辑需要在多处同步
   - 参数结构变化需要多处修改

3. **测试复杂度高**：
   - 需要验证两套实现的一致性

## 推荐方案：方案A - 最小改动重构

### 核心思想

**职责分离**：
- `scenario_generator.py`：负责**所有**事件类型的VSS/TEC/NO_CONTROL场景生成
- `generate_flowsurge_scenarios.py`：仅负责**流量激增特有的处理**
  - 事件数据读取和筛选
  - DHS场景生成（流量激增特有的固定时段策略）
  - 编排和统计

### 重构步骤

#### Step 1: 删除重复的VSS/TEC参数生成

**删除**：
- `generate_control_params_vss()` (第209-271行)
- `generate_control_params_tec()` (第357-427行)

**原因**：这些逻辑已经在`scenario_generator.py`中实现

#### Step 2: 简化VSS/TEC场景生成调用

**修改前**（generate_flowsurge_scenarios.py）：
```python
# 生成VSS参数
if strategy == 'VSS':
    control_params = generate_control_params_vss(row)  # ❌ 重复实现

# 调用generator
files = generator.generate_scenario(
    event_data=event_data,
    strategy_type='VSS',
    control_params=control_params
)
```

**修改后**：
```python
# 直接调用，无需预先生成参数
if strategy == 'VSS':
    files = generator.generate_scenario(
        event_data=event_data,
        strategy_type='VSS',
        control_params={
            'affected_edges': [str(row['edge_id'])],
            'speed_limit_kmh': 80,  # 简化参数
            'response_delay_seconds': 300,
            'recovery_period_seconds': 600
        }
    )
```

**说明**：
- `scenario_generator`内部会自动处理时间计算
- 无需在外部计算`begin/end`

#### Step 3: 保留DHS参数生成（流量激增特有）

**保留**：
- `generate_control_params_dhs()` (第274-354行)

**原因**：
- DHS是流量激增特有的控制策略
- 使用固定时段（7:30-9:30）而非响应式管控
- 需要特定的路段配置（G4202南段）

### 重构后的架构

```
generate_flowsurge_scenarios.py (简化版)
├── load_and_filter_flowsurge_events()    # 流量激增特有的事件筛选
├── enhance_with_control_strategy()       # 添加DHS策略标记
├── generate_control_params_dhs()         # DHS参数生成（保留）
└── generate_flowsurge_scenarios()
    ├── VSS: 直接调用 scenario_generator.generate_scenario()
    ├── TEC: 直接调用 scenario_generator.generate_scenario()
    └── DHS: 使用 generate_control_params_dhs() → 调用 scenario_generator

scenario_generator.py (统一处理)
├── _generate_control_strategy_config()
│   ├── VSS: 自动计算 speed_steps 的 begin/end
│   ├── TEC: 自动计算 flow_intervals 的 begin/end
│   └── DHS: 使用提供的 intervals 参数
└── generate_scenario()
```

## 方案B：完全合并（不推荐）

### 描述
将流量激增处理逻辑完全合并到`scenario_generator.py`中

### 缺点
1. `scenario_generator.py`变得过于复杂
2. 违反单一职责原则
3. 流量激增特有的业务逻辑（DHS固定时段、路段筛选）混入通用生成器

### 结论
**不推荐**

## 实施方案A的详细代码

### 修改1：简化VSS调用

**文件**：`scripts/generate_flowsurge_scenarios.py`

**删除**：第209-271行的`generate_control_params_vss()`函数

**修改**：第518-519行
```python
# 修改前
if strategy == 'VSS':
    control_params = generate_control_params_vss(row)

# 修改后
if strategy == 'VSS':
    control_params = {
        'affected_edges': [str(row['edge_id'])],
        'speed_limit_kmh': 80,
        'response_delay_seconds': 300,
        'recovery_period_seconds': 600
    }
```

### 修改2：简化TEC调用

**删除**：第357-427行的`generate_control_params_tec()`函数

**修改**：第522-523行
```python
# 修改前
elif strategy == 'TEC':
    control_params = generate_control_params_tec(row)

# 修改后
elif strategy == 'TEC':
    control_params = {
        'entrance_edges': [str(row['edge_id'])],
        'flow_coefficient': 0.9,
        'response_delay_seconds': 300,
        'recovery_period_seconds': 600
    }
```

### 修改3：保留DHS参数生成

**保留**：`generate_control_params_dhs()`函数（不修改）

**原因**：DHS是流量激增特有的策略，需要特殊处理

### 修改4：确保scenario_generator正确处理

**检查**：`scenario_generator.py`的`_generate_control_strategy_config()`

**应该已包含**：
```python
# VSS自动计算begin/end
if strategy_type.upper() == 'VSS' and 'speed_steps' in parameters:
    for step in parameters['speed_steps']:
        step['begin'] = begin_seconds
        step['end'] = end_seconds

# TEC自动计算begin/end
elif strategy_type.upper() == 'TEC' and 'flow_intervals' in parameters:
    for interval in parameters['flow_intervals']:
        interval['begin'] = begin_seconds
        interval['end'] = end_seconds
```

**注意**：我们之前已经在修复事件加载时间时添加了这部分逻辑！

## 验证清单

### 功能验证

- [ ] VSS场景生成正确（begin/end自动计算）
- [ ] TEC场景生成正确（begin/end自动计算）
- [ ] DHS场景生成正确（使用固定时段）
- [ ] 流量激增事件筛选正常
- [ ] 场景文件结构一致

### 一致性验证

- [ ] 流量激增的VSS场景与其他事件类型的VSS场景结构相同
- [ ] 流量激增的TEC场景与其他事件类型的TEC场景结构相同
- [ ] `control_strategy_config.json`格式统一
- [ ] `.add.xml`文件格式统一

### 回归测试

- [ ] 运行`python scripts/generate_flowsurge_scenarios.py`
- [ ] 检查生成的场景数量正确
- [ ] 验证至少一个VSS场景的时间参数
- [ ] 验证至少一个TEC场景的时间参数
- [ ] 验证至少一个DHS场景的时间参数

## 优势总结

### 架构优势

1. **单一数据源（Single Source of Truth）**：
   - VSS/TEC参数生成逻辑只在`scenario_generator.py`中
   - 避免代码重复和不一致

2. **职责清晰**：
   - `scenario_generator.py`：通用场景生成
   - `generate_flowsurge_scenarios.py`：流量激增特定处理

3. **易于维护**：
   - 修改VSS/TEC逻辑只需改一处
   - 流量激增特有逻辑（DHS）独立管理

### 实现优势

1. **代码精简**：
   - 删除~160行重复代码
   - 脚本更简洁易读

2. **自动一致性**：
   - 所有场景使用相同的时间计算逻辑
   - 参数结构自动统一

3. **未来扩展性**：
   - 新增事件类型：直接使用`scenario_generator`
   - 新增控制策略：在`scenario_generator`中实现一次，所有事件类型自动可用

## 风险与缓解

### 风险1：参数传递不完整

**风险**：简化参数可能缺少必要信息

**缓解**：
- `scenario_generator`使用默认值填充
- 明确文档化所需参数

### 风险2：DHS场景兼容性

**风险**：DHS参数结构可能与`scenario_generator`不兼容

**缓解**：
- 保持DHS参数生成不变
- 确保`scenario_generator`正确处理DHS的`intervals`参数

### 风险3：回归问题

**风险**：修改后可能影响现有场景

**缓解**：
- 完整的回归测试
- 对比修改前后的场景文件
- 保留修改前的代码版本

## 实施时间线

1. **准备阶段**（10分钟）：
   - 创建备份：`cp generate_flowsurge_scenarios.py generate_flowsurge_scenarios.py.backup`
   - 阅读当前代码确认理解

2. **重构阶段**（20分钟）：
   - 删除VSS/TEC参数生成函数
   - 简化调用代码
   - 更新文档字符串

3. **测试阶段**（15分钟）：
   - 运行场景生成
   - 验证生成的场景文件
   - 对比修改前后的差异

4. **文档阶段**（5分钟）：
   - 更新README
   - 添加架构说明

**总计**：约50分钟

## 推荐行动

**立即执行方案A**：
1. 删除重复的VSS/TEC参数生成函数
2. 简化调用代码
3. 运行测试验证
4. 更新文档

**理由**：
- 代码重复是技术债务，越早解决越好
- 架构统一后，后续维护成本大幅降低
- 修改风险低，影响范围明确

---

**创建时间**：2025-11-14
**状态**：待实施
**优先级**：🟡 中（建议在下次修改前完成）
