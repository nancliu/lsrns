# VSS 和 TEC 策略 edgeData 聚合修复

**修复日期**: 2025-11-16
**状态**: ✅ 已完成和验证
**关键修改**: `shared/utilities/edge_aggregator.py`

---

## 问题描述

VSS（可变限速）和TEC（收费站管控）策略的受控边缘未被正确聚合到 `edgeData.add.xml` 中。

### 根本原因

两个策略的提取函数期望的参数名称与实际使用的参数名称不匹配：

#### VSS 策略

| 实际参数 | 函数期望 | 结果 |
|--------|---------|------|
| `affected_edges` | `edge_list` / `edge_range` / `edge_pattern` | ❌ 完全无法提取 |

函数使用 `elif` 链，导致 `affected_edges` 无法被识别

#### TEC 策略

| 实际参数 | 函数处理 | 结果 |
|--------|--------|------|
| `affected_edges` | ✗ 不检查 | ❌ 被忽视 |
| `entrance_edges` | ✓ 检查 | ✓ 可被提取 |

虽然 `entrance_edges` 能被处理，但 `affected_edges` 被忽视，可能导致边缘遗漏

---

## 解决方案

### 1. 修改 `_extract_vss_edges()` 函数

**文件**: `shared/utilities/edge_aggregator.py`
**行号**: 252-316

**改进内容**:
1. ✅ 优先支持新格式 `affected_edges`
2. ✅ 向后兼容旧格式 `edge_list` / `edge_range` / `edge_pattern`
3. ✅ 详细的参数优先级和日志

**关键改动**:

```python
# 优先使用新格式：affected_edges
if 'affected_edges' in parameters:
    if isinstance(affected_edges, list):
        edges.extend(affected_edges)

# 旧格式: edge_list
elif 'edge_list' in parameters:
    # ...

# 旧格式: edge_range
elif 'edge_range' in parameters:
    # ...

# 旧格式: edge_pattern
elif 'edge_pattern' in parameters:
    # ...
```

### 2. 修改 `_extract_tec_edges()` 函数

**文件**: `shared/utilities/edge_aggregator.py`
**行号**: 318-370

**改进内容**:
1. ✅ 添加对 `affected_edges` 的处理
2. ✅ 使用 `set` 避免重复
3. ✅ 详细的日志记录

**关键改动**:

```python
edges_set = set()

# 优先使用新格式：affected_edges
if 'affected_edges' in parameters:
    edges_set.update(affected_edges)

# 入口边缘
if 'entrance_edges' in parameters:
    edges_set.update(entrance_edges)

# 额外受控边缘
if 'control_edges' in parameters:
    edges_set.update(control_edges)

# 单个入口边缘（向后兼容）
if 'entrance_edge' in parameters:
    edges_set.add(entrance_edge)
```

---

## 验证结果

### ✅ 修复前后对比

**修复前**:

```
[测试1] VSS 策略参数提取
  实际提取到: ❌ 空列表！
  问题：参数名不匹配

[测试3] 完整策略聚合场景
  场景1: 仅VSS策略
    - 来源分解: {'event': 1, 'strategies': {}}  ❌ VSS为空

  场景3: VSS + TEC策略
    - 来源分解: {'event': 1, 'strategies': {'TEC': 1}}  ❌ VSS缺失
```

**修复后**:

```
[测试1] VSS 策略参数提取
  实际提取到: ['-3734']
  ✓ 提取成功

[测试3] 完整策略聚合场景
  场景1: 仅VSS策略
    - 来源分解: {'event': 1, 'strategies': {'VSS': 1}}  ✅ VSS成功

  场景3: VSS + TEC策略
    - 来源分解: {'event': 1, 'strategies': {'VSS': 1, 'TEC': 1}}  ✅ 都成功
```

### 参数提取对比

| 策略 | 修复前 | 修复后 |
|-----|-------|-------|
| **VSS** | ❌ `[]` 空列表 | ✅ `['-3734']` 成功 |
| **TEC** | ⚠️ `['-3734']` (仅通过entrance_edges) | ✅ `['-3734']` (完整处理) |

---

## 参数格式标准化

修复后所有三个策略都统一支持 `affected_edges` 参数：

| 策略 | affected_edges | 其他参数 | 优先级 |
|-----|---|---|---|
| **DHS** | ✅ shoulder_segments | affected_lanes | shoulder_segments > affected_lanes > 网络文件 |
| **VSS** | ✅ affected_edges | edge_list/range/pattern | affected_edges > 其他 |
| **TEC** | ✅ affected_edges | entrance_edges/control_edges | affected_edges > others |

---

## 影响范围

### 受影响的功能

1. ✅ **案例创建** - VSS/TEC边缘现在被正确聚合到 `edgeData.add.xml`
2. ✅ **EdgeData分析** - 可以分析VSS/TEC受控边缘上的交通数据
3. ✅ **完整数据收集** - edgeData配置包含所有受控策略的边缘

### 受影响的场景

所有包含VSS或TEC策略的案例/场景：
- 事故场景 (01_accident) - 10754, 10762, 10807, 10814等
- 其他自定义场景

### 向后兼容性

✅ **100% 向后兼容**

- VSS: 支持 `edge_list`, `edge_range`, `edge_pattern` 旧格式
- TEC: 支持 `entrance_edges`, `control_edges`, `entrance_edge` 旧格式
- 优先级明确，无冲突

---

## 完整修复流程

```
VSS/TEC参数（control_strategy_config.json）
├─ VSS:
│  ├─ affected_edges: ["-3734"]  ✅ 现在被识别
│  └─ speed_limit_kmh: 70
│
├─ TEC:
│  ├─ affected_edges: ["-3734"]   ✅ 现在被处理
│  ├─ entrance_edges: ["-3734"]   ✅ 继续支持
│  └─ flow_reduction: 0.2
│
↓
edge_aggregator._extract_vss_edges() / _extract_tec_edges()
├─ 优先提取 affected_edges        ✅
├─ 支持旧格式参数                 ✅
└─ 返回完整的边缘列表             ✅
  ↓
aggregate_edgedata_edges()
├─ 合并所有策略边缘               ✅
├─ 按来源分类（VSS/TEC等）       ✅
└─ 路网验证                       ✅
  ↓
generate_edgedata_xml_for_case()
└─ edgeData.add.xml包含所有受控策略的边缘  ✅
```

---

## 测试覆盖范围

### 测试场景

✅ VSS 参数格式识别
✅ TEC 参数格式识别
✅ VSS + TEC 多策略聚合
✅ 向后兼容性验证
✅ 参数去重（set）验证

### 测试文件

- `test_vss_tec_edgedata_aggregation.py` - 完整测试套件

运行命令：
```bash
python test_vss_tec_edgedata_aggregation.py
```

---

## 与DHS修复的一致性

本次修复统一了所有三个策略的参数处理模式：

| 方面 | DHS | VSS | TEC |
|-----|-----|-----|-----|
| 主参数 | `shoulder_segments` | `affected_edges` | `affected_edges` |
| 备用参数1 | `affected_lanes` | `edge_list` | `entrance_edges` |
| 备用参数2 | 网络文件 | `edge_range` | `control_edges` |
| 参数3 | - | `edge_pattern` | `entrance_edge` |
| 日志记录 | ✅ 详细 | ✅ 详细 | ✅ 详细 |

---

## 后续建议

### 短期（立即）
1. ✅ 应用VSS/TEC修复 - **已完成**
2. ✅ 测试验证 - **已通过**
3. 可选：重新生成现有案例的edgeData.add.xml以确保完整性

### 中期（1-2周）
1. 统一所有策略参数的API文档
2. 创建完整的聚合流程文档
3. 为其他可能的策略（如RTLS）检查类似问题

### 长期（1-2月）
1. 创建完整的集成测试覆盖所有策略组合
2. 增强edgeData验证和错误报告
3. 考虑将 `affected_edges` 统一为所有策略的标准参数

---

## 总结

| 方面 | 修复前 | 修复后 |
|-----|-------|-------|
| VSS边缘提取 | ❌ 参数无法识别 | ✅ 正确提取 |
| TEC边缘提取 | ⚠️ 部分支持 | ✅ 完整支持 |
| 向后兼容性 | ✅ 有 | ✅ 增强 |
| 日志详细度 | ⚠️ 不足 | ✅ 详细 |
| 参数一致性 | ❌ 不统一 | ✅ 统一 |

修复确保了VSS和TEC策略在edgeData聚合中得到正确处理，使得SUMO仿真能够完整地收集所有受控策略边缘上的交通数据。
