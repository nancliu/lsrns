# edgeData 聚合指南 (v0.9.0+)

**版本**: 1.0
**日期**: 2025-11-16
**状态**: 稳定版

---

## 概述

edgeData聚合是案例创建过程中的关键步骤，它将事件影响的边缘与所有控制策略的受控边缘合并，生成一个统一的 `edgeData.add.xml` 配置文件供SUMO使用。

---

## 聚合流程

```
案例创建请求
  ↓
提取事件边缘
├── 主边缘 (event_location.edge_id)
└── 扩展范围边缘 (radius_2_hops等)
  ↓
提取所有策略的受控边缘
├── DHS: 从shoulder_segments或affected_lanes提取
├── VSS: 从affected_edges提取（优先）或edge_list/range/pattern
└── TEC: 从affected_edges提取（优先）或entrance_edges
  ↓
合并所有边缘
├── 去重 (使用set)
├── 按来源分类统计 (event, DHS, VSS, TEC)
└── 路网验证 (检查边是否存在)
  ↓
生成 edgeData.add.xml
└── 包含所有有效边缘的SUMO配置
```

---

## 参数识别优先级

### DHS（动态硬路肩）

**优先级** ↓

| 级别 | 参数 | 示例 | 说明 |
|-----|------|------|------|
| 1 | `shoulder_segments` | `["-12680", "-10376"]` | 直接edge ID列表，推荐 ✅ |
| 2 | `affected_lanes` | `["-12680_0", "-10376_0"]` | Lane ID，需要解析 |
| 3 | `shoulder_lanes` | `["edge_id_lane_index"]` | 旧版本格式 |
| 4 | 网络文件 | 从.net.xml读取 | 备用方案 |

### VSS（可变限速）

**优先级** ↓

| 级别 | 参数 | 示例 | 说明 |
|-----|------|------|------|
| 1 | `affected_edges` | `["-3734"]` | 直接edge ID列表，推荐 ✅ |
| 2 | `edge_list` | `["-3734"]` | 旧版本格式 |
| 3 | `edge_range` | `[3000, 3050]` | 范围格式 |
| 4 | `edge_pattern` | `"3000-3050"` | 模式字符串 |

### TEC（收费站管控）

**优先级** ↓

| 级别 | 参数 | 示例 | 说明 |
|-----|------|------|------|
| 1 | `affected_edges` | `["-3734"]` | 所有受影响边缘，推荐 ✅ |
| 2 | `entrance_edges` | `["-3734"]` | 入口点边缘 |
| 3 | `control_edges` | `["-3734"]` | 额外受控边缘 |
| 4 | `entrance_edge` | `"-3734"` | 单个入口（向后兼容） |

---

## 参数格式规范

### 所有策略都应包含

```json
{
  "strategy_type": "DHS|VSS|TEC",
  "parameters": {
    "affected_edges": ["edge1", "edge2", ...],      // ✅ 必需
    "affected_lanes": ["edge1_0", "edge2_0", ...], // ✅ 推荐（用于edgeData）

    // 策略特定参数...
  }
}
```

### affected_edges 格式要求

- **类型**: 字符串列表
- **内容**: SUMO edge ID （例如：`"-3734"`, `"-12680.203"`)
- **必要性**: 🔴 **必需** - edgeData聚合依赖此参数
- **验证**: 所有边缘必须在网络文件中存在

### affected_lanes 格式要求

- **类型**: 字符串列表
- **格式**: `"edge_id_lane_index"` （例如：`"-3734_0"`, `"-12680.203_1"`)
- **必要性**: 🟡 **推荐** - 用于追踪和验证
- **验证**: Lane索引必须有效（< edge的lane总数）

---

## 聚合验证规则

### 有效性检查

```python
# 1. affected_edges 非空
if not parameters.get('affected_edges'):
    warning(f"策略 {strategy_id}: affected_edges为空，将不被聚合")

# 2. Edge存在于网络文件中
valid_edges = validate_edges_in_network(
    edge_ids=parameters['affected_edges'],
    network_file='sichuan202508v7.net.xml'
)
if not valid_edges:
    warning(f"策略 {strategy_id}: 无有效边缘")

# 3. Lane ID格式正确（如果提供）
for lane_id in parameters.get('affected_lanes', []):
    if '_' not in lane_id:
        warning(f"Lane ID 格式错误: {lane_id}，应为 edge_id_lane_index")
```

### 完整性检查

```python
# DHS: affected_lanes计数应该 == shoulder_segments计数
if len(affected_lanes) != len(shoulder_segments):
    warning(f"DHS {strategy_id}: Lane映射不完整 " +
            f"({len(affected_lanes)} lanes vs {len(shoulder_segments)} segments)")
```

---

## 聚合结果示例

### 输入场景

```python
event = {"edge_id": "-3734"}

strategies = [
    {
        "strategy_type": "DHS",
        "parameters": {
            "shoulder_segments": ["-12680", "-10376"],
            "affected_lanes": ["-12680_0", "-10376_0"],
            "affected_edges": ["-12680", "-10376"]
        }
    },
    {
        "strategy_type": "VSS",
        "parameters": {
            "affected_edges": ["-3734"]
        }
    },
    {
        "strategy_type": "TEC",
        "parameters": {
            "affected_edges": ["-5000"],
            "entrance_edges": ["-5000"]
        }
    }
]
```

### 聚合结果

```python
{
    'merged_edges': ["-3734", "-5000", "-12680", "-10376"],
    'source_breakdown': {
        'event': 1,      # 事件边缘
        'strategies': {
            'DHS': 2,    # DHS受控边缘
            'VSS': 1,    # VSS受控边缘
            'TEC': 1     # TEC受控边缘
        }
    },
    'validation': {
        'valid_edges': ["-3734", "-5000", "-12680", "-10376"],
        'invalid_edges': [],
        'validation_rate': 1.0  # 100%有效
    }
}
```

### 生成的 edgeData.add.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<additional>
  <!-- Total edges: 4 (validated) -->
  <!-- Event edges: 1 -->
  <!-- Strategy edges: 3 (DHS: 2, VSS: 1, TEC: 1) -->
  <edgeData id="ed1"
    freq="300"
    file="edgedata/edgedata.xml"
    edges="-3734 -5000 -12680 -10376"
    excludeEmpty="true"
    withInternal="false"/>
</additional>
```

---

## 常见问题排查

### 问题1：策略边缘不被聚合

**症状**: `edgeData.add.xml` 中不包含策略的受控边缘

**检查清单**:
- [ ] `affected_edges` 参数是否存在且非空？
- [ ] Edge ID 是否在网络文件中？
- [ ] 参数名是否正确（不是 `edges`, `control_edges`, 等）？
- [ ] 对于DHS，`shoulder_segments` 是否存在？

**解决方案**:
```python
# 确保参数结构正确
control_params = {
    "affected_edges": ["edge1", "edge2"],  # ✅ 关键
    "shoulder_segments": ["edge1", "edge2"],  # DHS
    "affected_lanes": ["edge1_0", "edge2_0"]   # 可选但推荐
}
```

### 问题2：Lane ID 格式错误

**症状**: 日志警告 "Lane ID 格式错误"

**原因**: Lane ID 不符合 SUMO 格式 `edge_id_lane_index`

**修正**:
```python
# ❌ 错误
"affected_lanes": ["edge1", "lane_0"]

# ✅ 正确
"affected_lanes": ["-3734_0", "-3734_1"]
```

### 问题3：Edge 在网络文件中不存在

**症状**: 聚合日志显示 "无有效边缘" 或 "无效边缘排除"

**诊断**:
```bash
# 查看生成的edgeData配置
cat cases/case_xxx/config/edgeData.add.xml

# 验证edge是否在网络文件中
grep 'id="-3734"' templates/network_files/sichuan202508v7.net.xml
```

**解决方案**:
- 确认 edge ID 拼写正确
- 检查 edge ID 是否在选定的网络文件中
- 对于VSS，使用 `edge_list` 而不是 `edge_range`

---

## 最佳实践

### DO ✅

1. **总是包含 `affected_edges`**
   ```python
   {
       "strategy_type": "VSS",
       "parameters": {
           "affected_edges": ["-3734"],  # 必须
           "speed_limit_kmh": 70
       }
   }
   ```

2. **为所有策略提供 `affected_lanes`**
   ```python
   {
       "affected_edges": ["-3734"],
       "affected_lanes": ["-3734_0", "-3734_1"]  # 推荐
   }
   ```

3. **验证边缘存在于网络文件中**
   ```bash
   grep -E '(id="-3734"|id="-12680")' templates/network_files/*.net.xml
   ```

4. **检查聚合日志以确认边缘被识别**
   ```bash
   # 从案例日志检查聚合结果
   grep "聚合了.*条.*边缘" case_xxx/generation.log
   ```

### DON'T ❌

1. **不要使用不同的参数名**
   ```python
   # ❌ 错误
   {"edges": ["-3734"]}          # 应该是 affected_edges
   {"control_edges": ["-3734"]}  # 对VSS无效
   ```

2. **不要省略 Lane ID 的 edge_id 部分**
   ```python
   # ❌ 错误
   {"affected_lanes": ["_0", "_1"]}

   # ✅ 正确
   {"affected_lanes": ["-3734_0", "-3734_1"]}
   ```

3. **不要混合使用多个参数格式**
   ```python
   # ❌ 混乱
   {
       "affected_edges": ["-3734"],
       "edge_list": ["-3735"],
       "edge_range": [3700, 3750]
   }

   # ✅ 清晰
   {"affected_edges": ["-3734", "-3735"]}
   ```

---

## 版本变更历史

### v0.9.0 (2025-11-16)

**新增**:
- ✅ 统一的edgeData聚合参数识别
- ✅ VSS和TEC的 `affected_edges` 支持
- ✅ DHS的 `shoulder_segments` 和 `affected_lanes` 支持
- ✅ 完整的验证和错误处理

**改进**:
- 🔄 所有策略现在都支持 `affected_edges`
- 🔄 参数优先级更清晰
- 🔄 日志更详细

**兼容性**:
- ✅ 100% 向后兼容旧参数格式
- ✅ 自动参数转换
- ✅ 无需修改现有配置

---

## 相关代码

### 主要实现

- **聚合函数**: `shared/utilities/edge_aggregator.py`
  - `aggregate_edgedata_edges()` - 主聚合函数
  - `_extract_dhs_edges()` - DHS边缘提取
  - `_extract_vss_edges()` - VSS边缘提取
  - `_extract_tec_edges()` - TEC边缘提取

- **XML生成**: `shared/utilities/sumo_utils.py`
  - `generate_edgedata_xml_for_case()` - edgeData XML生成

### 参考文档

- `docs/api/scenario_generator_interface.md` - 场景生成接口
- `ALL_STRATEGIES_EDGEDATA_AGGREGATION_FIX.md` - 完整修复说明
- `VSS_TEC_EDGEDATA_AGGREGATION_FIX.md` - VSS/TEC修复详情
- `DHS_COMPLETE_FIX_SUMMARY.md` - DHS修复详情

---

## 支持和反馈

如遇到问题：
1. 查看[常见问题排查](#常见问题排查)
2. 检查相关代码中的日志输出
3. 参考聚合函数的文档注释
4. 查看测试用例了解预期行为

**测试文件**:
- `test_dhs_edgedata_aggregation.py`
- `test_vss_tec_edgedata_aggregation.py`

---

**维护者**: OD_SIM Development Team
**最后更新**: 2025-11-16
