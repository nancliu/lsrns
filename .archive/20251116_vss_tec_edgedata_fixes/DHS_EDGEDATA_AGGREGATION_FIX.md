# DHS 应急车道 edgeData 聚合补充修复

**修复日期**: 2025-11-16
**状态**: ✅ 已完成和验证
**关键修改**: `shared/utilities/edge_aggregator.py`

---

## 问题描述

DHS（Dynamic Hard Shoulder / 动态硬路肩）策略的应急车道边缘未被包含在生成的 `edgeData.add.xml` 文件中。

### 原因分析

`edge_aggregator.py` 中的 `_extract_dhs_edges()` 函数期望的参数名称是：
- `shoulder_lanes` - 硬路肩车道列表
- `main_edges` - 主线边缘列表

但实际的DHS控制参数结构（v0.9.0+）使用的是：
- **`shoulder_segments`** - 应急车道edge ID列表
- **`affected_lanes`** - 应急车道车道ID列表（格式：`edge_id_lane_index`）
- `activation_schedule` - 激活时间表

导致函数无法正确提取DHS边缘，edgeData聚合时遗漏了DHS应急车道。

---

## 解决方案

### 修改 `_extract_dhs_edges()` 函数

**文件**: `shared/utilities/edge_aggregator.py`
**行号**: 328-390

**改进内容**：

1. ✅ **新格式支持** - 优先使用 `shoulder_segments`（直接edge ID列表）
2. ✅ **Lane ID解析** - 从 `affected_lanes` 中提取edge ID
3. ✅ **向后兼容** - 保留对旧格式 `shoulder_lanes` 的支持
4. ✅ **详细日志** - 记录提取过程和结果

**关键改动**：

```python
# 优先使用新格式：shoulder_segments
if 'shoulder_segments' in parameters:
    shoulder_segments = parameters['shoulder_segments']
    for edge_id in shoulder_segments:
        edges_set.add(edge_id.strip())

# 新格式: affected_lanes (从lane ID中提取)
if 'affected_lanes' in parameters:
    affected_lanes = parameters['affected_lanes']
    for lane_id in affected_lanes:
        if '_' in lane_id:
            edge_id = lane_id.rsplit('_', 1)[0]
            edges_set.add(edge_id)

# 向后兼容旧格式：shoulder_lanes
if 'shoulder_lanes' in parameters and len(edges_set) == 0:
    # ... 处理旧格式
```

---

## 验证结果

### 测试1：直接提取DHS边缘 ✅

```
输入参数:
  - shoulder_segments: 8 条
  - affected_lanes: 8 条

提取结果:
  ✓ 提取到 8 条边缘: ['-10188', '-6906', '-3324', '-12680', '-1438', '-10376', '-4360', '-10376.203']
  ✓ 验证通过：提取的边缘完全匹配shoulder_segments
```

### 测试2：完整策略聚合场景 ✅

```
聚合结果:
  ✓ 总边缘数: 9
  ✓ 事件边缘: 0
  ✓ 策略边缘总数: 8
    - DHS: 8 条

  ✓ 验证通过：所有DHS应急车道边缘都被聚合
```

### 测试3：生成的 edgeData.add.xml ✅

```
生成结果:
  ✓ 文件: output/scenarios/07_flowsurge/scenario_6120705_dhs/config/edgeData.add.xml
  ✓ 总边缘数: 9
  ✓ DHS边缘包含数: 8/8
  ✓ DHS车道已成功聚合到edgeData.add.xml
```

生成的XML示例：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<additional>
  <!-- EdgeData configuration for event case -->
  <!-- Total edges (validated): 9 -->
  <!-- Event edges: 0 -->
  <!-- Strategy edges: 8 -->
  <!-- Invalid edges excluded: 0 -->
  <edgeData id="ed1"
    freq="300"
    file="edgedata/edgedata.xml"
    edges="-12680 -10376.203 -10376 -6906 -1438 -3324 -4360 -10188 -14078"
    excludeEmpty="true"
    withInternal="false"/>
</additional>
```

---

## DHS参数到edgeData聚合的完整流程

```
DHS策略参数 (control_strategy_config.json)
├── shoulder_segments: ["-12680", "-10376.203", ...]
├── affected_lanes: ["-12680_0", "-10376.203_0", ...]
└── activation_schedule: [{"begin": 3300, "end": 5400, ...}]
    ↓
edge_aggregator._extract_dhs_edges()
├── 从 shoulder_segments 提取所有edge ID
├── 从 affected_lanes 解析并提取edge ID
└── 返回deduplicated边缘列表
    ↓
aggregate_edgedata_edges()
├── 合并事件边缘 + 策略边缘
├── 按来源分类（event, VSS, TEC, DHS等）
├── 对合并的边进行路网验证
└── 返回验证通过的边缘列表
    ↓
generate_edgedata_xml_for_case()
├── 生成edgeData.add.xml内容
├── 包含所有有效的DHS应急车道边缘
└── 保存到 case/config/edgeData.add.xml
    ↓
最终XML中的edges属性包含DHS应急车道: ✅
```

---

## 影响范围

### 修改的文件

- **`shared/utilities/edge_aggregator.py`** (lines 328-390)
  - 改进 `_extract_dhs_edges()` 函数
  - 支持新格式DHS参数
  - 保留向后兼容性

### 受影响的功能

1. ✅ **案例创建** - 生成的 `edgeData.add.xml` 现在包含DHS车道
2. ✅ **EdgeData分析** - 可以分析DHS应急车道上的交通数据
3. ✅ **SUMO仿真配置** - edgeData配置更完整

### 后向兼容性

✅ **完全兼容**
- 支持旧格式参数（`shoulder_lanes`）
- 优先级：`shoulder_segments` > `affected_lanes` > `shoulder_lanes`
- 如果都不存在，返回空列表并记录警告

---

## 测试覆盖范围

### 已测试的场景

1. ✅ 单个DHS策略的边缘提取
2. ✅ DHS+事件的完整聚合
3. ✅ edgeData.add.xml生成和验证
4. ✅ 路网验证（边缘存在性检查）
5. ✅ 来源分解统计

### 测试文件

- `test_dhs_edgedata_aggregation.py` - 完整测试套件

运行命令：
```bash
python test_dhs_edgedata_aggregation.py
```

---

## 配置建议

### 确保DHS参数完整性

在 `api/services/scenario_service.py` 的 `_prepare_control_params()` 中：

```python
return {
    "shoulder_segments": affected_edges,      # ✅ edgeData需要
    "affected_lanes": affected_lanes,         # ✅ edgeData需要
    "hard_shoulder_lane_index": lane_index,
    "activation_schedule": [...],
    ...
}
```

两个参数都应该包含：
- `shoulder_segments` - edgeData聚合的主要来源
- `affected_lanes` - 备用提取方式

---

## 后续建议

### 短期（当前）
1. ✅ 修改 `_extract_dhs_edges()` 函数 - **已完成**
2. ✅ 验证修复效果 - **已通过**
3. 将修复应用到现有案例的 `edgeData.add.xml` 文件

### 中期
1. 为VSS和TEC策略检查edgeData聚合逻辑
2. 添加更详细的聚合过程日志
3. 创建edgeData聚合的集成测试

### 长期
1. 统一所有策略的参数格式
2. 在API文档中明确说明edgeData包含的内容
3. 添加edgeData验证的可视化工具

---

## 总结

| 方面 | 修复前 | 修复后 |
|-----|-------|-------|
| DHS边缘提取 | ❌ 参数名不匹配 | ✅ 支持新旧格式 |
| edgeData聚合中的DHS | ❌ 遗漏应急车道 | ✅ 包含所有8条应急车道 |
| 向后兼容性 | N/A | ✅ 完全兼容旧参数 |
| 日志详细度 | ⚠️ 不够详细 | ✅ 详细记录提取过程 |
| 测试覆盖 | ❌ 缺失 | ✅ 完整的测试套件 |

修复确保了DHS应急车道在edgeData聚合中得到正确处理，使得SUMO仿真能够完整地收集所有受控车道上的交通数据。
