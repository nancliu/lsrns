# DHS、VSS、TEC 策略文档索引

**最后更新**: 2025-11-16
**版本**: v0.9.0

---

## 📚 文档导航

### 🚀 快速开始

**新用户？从这里开始**

1. **[Scenario Generator Interface](api/scenario_generator_interface.md)** - 了解基本参数格式
   - ✅ 最新的DHS参数格式（v1.1）
   - ✅ VSS和TEC的affected_edges使用方法
   - ✅ 参数验证规则

2. **[edgeData聚合指南](api/EDGEDATA_AGGREGATION_GUIDE.md)** - 了解如何聚合受控边缘
   - ✅ 参数识别优先级机制
   - ✅ 完整性检查清单
   - ✅ 常见问题排查

3. **[API变更日志 v0.9.0](api_docs/API_CHANGELOG_v0.9.0.md)** - 了解最新改进
   - ✅ 所有三个策略的改进总结
   - ✅ 向后兼容性保证
   - ✅ 迁移指南

---

### 📖 策略详细文档

#### DHS (Dynamic Hard Shoulder / 动态硬路肩)

| 文档 | 内容 | 目标读者 |
|-----|------|---------|
| [**DHS_COMPLETE_FIX_SUMMARY.md**](../DHS_COMPLETE_FIX_SUMMARY.md) | DHS XML生成和edgeData聚合的完整修复说明 | 开发者、技术负责人 |
| Scenario Generator Interface (DHS章节) | DHS参数格式 (shoulder_segments, affected_lanes等) | 参数配置人员 |
| edgeData聚合指南 (DHS部分) | DHS的参数识别优先级和聚合流程 | 系统集成人员 |

**关键参数**:
```python
{
    'shoulder_segments': ["-12680", "-10376", ...],      # 应急车道edges
    'affected_lanes': ["-12680_0", "-10376_0", ...],    # 应急车道lanes
    'hard_shoulder_lane_index': 0,
    'activation_schedule': [{
        'begin': 3300,
        'end': 5400,
        'status': 'OPEN',
        'allowed_vehicle_types': ['passenger']
    }]
}
```

#### VSS (Variable Speed Sign / 可变限速)

| 文档 | 内容 | 目标读者 |
|-----|------|---------|
| [**VSS_TEC_EDGEDATA_AGGREGATION_FIX.md**](../VSS_TEC_EDGEDATA_AGGREGATION_FIX.md) | VSS参数识别修复详情 | 开发者、技术负责人 |
| Scenario Generator Interface (VSS章节) | VSS参数格式 (speed_limit_kmh, affected_edges等) | 参数配置人员 |
| edgeData聚合指南 (VSS部分) | VSS的参数优先级和聚合规则 | 系统集成人员 |

**关键参数**:
```python
{
    'affected_edges': ["-3734"],              # ✅ 推荐
    'speed_limit_kmh': 70,
    'response_delay_seconds': 300,
    'recovery_period_seconds': 600
}
```

#### TEC (Toll Entrance Control / 收费站管控)

| 文档 | 内容 | 目标读者 |
|-----|------|---------|
| [**VSS_TEC_EDGEDATA_AGGREGATION_FIX.md**](../VSS_TEC_EDGEDATA_AGGREGATION_FIX.md) | TEC参数处理改进详情 | 开发者、技术负责人 |
| Scenario Generator Interface (TEC章节) | TEC参数格式 (entrance_edges, affected_edges等) | 参数配置人员 |
| edgeData聚合指南 (TEC部分) | TEC的参数优先级和去重机制 | 系统集成人员 |

**关键参数**:
```python
{
    'affected_edges': ["-3734"],              # ✅ 推荐
    'entrance_edges': ["-3734"],             # 备选
    'flow_reduction': 0.2,
    'response_delay_seconds': 300,
    'recovery_period_seconds': 600
}
```

---

### 🛠️ 开发者文档

#### 核心实现

| 文件 | 功能 | 关键改动 |
|-----|------|---------|
| `shared/utilities/edge_aggregator.py` | edgeData聚合和参数识别 | +98行，支持新格式参数 |
| `shared/control_tools/additional_generator.py` | SUMO XML生成 (DHS, VSS, TEC) | +51行，优先使用affected_lanes |
| `shared/control_tools/scenario_generator.py` | 场景生成主逻辑 | 时间间隔优先级处理 |
| `api/services/scenario_service.py` | 参数生成和验证 | +72行，完整的DHS参数结构 |

#### 参数识别流程

```python
# 聚合流程
event.edge_id → edge_aggregator.aggregate_edgedata_edges()
strategies[].parameters → _extract_dhs_edges / _extract_vss_edges / _extract_tec_edges
└→ merged_edges → validate_in_network() → generate_edgedata_xml_for_case()
```

#### 参数优先级

```
DHS:  shoulder_segments > affected_lanes > shoulder_lanes > 网络文件
VSS:  affected_edges > edge_list > edge_range > edge_pattern
TEC:  affected_edges > entrance_edges > control_edges > entrance_edge
```

---

### ✅ 测试和验证

#### 测试覆盖

| 测试文件 | 覆盖内容 | 执行命令 |
|---------|---------|---------|
| `test_dhs_edgedata_aggregation.py` | DHS参数提取和聚合 | `python test_dhs_edgedata_aggregation.py` |
| `test_vss_tec_edgedata_aggregation.py` | VSS/TEC参数提取和聚合 | `python test_vss_tec_edgedata_aggregation.py` |

#### 验证检查清单

```
□ affected_edges 参数不为空
□ Edge ID 存在于网络文件中
□ Lane ID 格式正确 (edge_id_lane_index)
□ 参数优先级识别正确
□ edgeData.add.xml 包含所有受控边缘
□ SUMO 仿真能加载 XML 配置
```

---

### 📋 常见场景导航

#### 场景1: 创建新DHS策略

**文档路径**:
1. Scenario Generator Interface → DHS章节
2. DHS_COMPLETE_FIX_SUMMARY.md → 参数结构
3. edgeData聚合指南 → 验证规则

**参数检查清单**:
- [ ] `shoulder_segments` 包含所有应急车道edge ID
- [ ] `affected_lanes` 包含所有对应的lane ID
- [ ] `activation_schedule` 有正确的begin/end时间
- [ ] `hard_shoulder_lane_index` 设置正确

#### 场景2: 创建新VSS策略

**文档路径**:
1. Scenario Generator Interface → VSS章节
2. VSS_TEC_EDGEDATA_AGGREGATION_FIX.md
3. edgeData聚合指南 → VSS部分

**参数检查清单**:
- [ ] `affected_edges` 不为空
- [ ] `speed_limit_kmh` 在有效范围内 (30-130 km/h)
- [ ] Edge ID 在网络文件中存在

#### 场景3: 创建新TEC策略

**文档路径**:
1. Scenario Generator Interface → TEC章节
2. VSS_TEC_EDGEDATA_AGGREGATION_FIX.md
3. edgeData聚合指南 → TEC部分

**参数检查清单**:
- [ ] `affected_edges` 不为空
- [ ] `entrance_edges` 或 `affected_edges` 至少一个存在
- [ ] `flow_reduction` 在有效范围内 (0.1-1.0)

#### 场景4: 调试edgeData聚合问题

**文档路径**:
1. edgeData聚合指南 → 常见问题排查
2. 相应策略的修复文档 (DHS/VSS/TEC)
3. 查看聚合日志中的参数识别结果

**诊断命令**:
```bash
# 查看生成的edgeData配置
cat cases/case_xxx/config/edgeData.add.xml

# 验证策略参数
cat cases/case_xxx/simulations/sim_xxx/control_strategy_config.json

# 检查聚合日志
grep "聚合了" cases/case_xxx/generation.log
```

---

### 📊 修复汇总

#### v0.9.0 修复清单

| 问题 | 影响 | 修复状态 | 验证 |
|-----|------|---------|------|
| DHS XML格式错误 | ❌ SUMO加载失败 | ✅ 已修复 | ✅ SUMO验证通过 |
| DHS参数识别失败 | ❌ edgeData缺失 | ✅ 已修复 | ✅ 测试通过 |
| VSS参数无法识别 | ❌ edgeData缺失 | ✅ 已修复 | ✅ 测试通过 |
| TEC参数被忽视 | ⚠️ edgeData不完整 | ✅ 已修复 | ✅ 测试通过 |

#### 代码修改统计

```
文件总数: 4
├─ shared/utilities/edge_aggregator.py      +98行, -22行
├─ shared/control_tools/additional_generator.py +51行
├─ shared/control_tools/scenario_generator.py   (参数优先级)
└─ api/services/scenario_service.py         +72行, -5行

总计: +221行新增代码，100%向后兼容
```

---

### 🔗 快速链接

#### API和集成

- **Scenario Generator Interface**: `docs/api/scenario_generator_interface.md` - v1.1
- **edgeData Aggregation Guide**: `docs/api/EDGEDATA_AGGREGATION_GUIDE.md` - v1.0
- **API Changelog v0.9.0**: `docs/api_docs/API_CHANGELOG_v0.9.0.md`
- **Control Plan API**: `docs/api_docs/control_plan_api.md`

#### 修复文档

- **DHS Complete Fix Summary**: `DHS_COMPLETE_FIX_SUMMARY.md`
- **VSS/TEC Aggregation Fix**: `VSS_TEC_EDGEDATA_AGGREGATION_FIX.md`
- **All Strategies Aggregation Fix**: `ALL_STRATEGIES_EDGEDATA_AGGREGATION_FIX.md`

#### 实现文件

- **Edge Aggregator**: `shared/utilities/edge_aggregator.py` (参数识别)
- **Additional Generator**: `shared/control_tools/additional_generator.py` (XML生成)
- **Scenario Generator**: `shared/control_tools/scenario_generator.py` (主逻辑)

#### 测试

- **DHS Test**: `test_dhs_edgedata_aggregation.py`
- **VSS/TEC Test**: `test_vss_tec_edgedata_aggregation.py`

---

### ❓ 帮助和支持

#### 遇到问题？

1. **查看edgeData聚合指南**: 中文详细说明，包括故障排除
2. **检查API变更日志**: 了解最新变更和向后兼容性
3. **查看相应的修复文档**: 深入理解技术细节
4. **运行测试**: 验证参数识别是否正常

#### 想了解更多？

1. **参数识别的工作原理**: 查看 `shared/utilities/edge_aggregator.py` 源代码
2. **DHS XML生成的细节**: 查看 `shared/control_tools/additional_generator.py`
3. **场景生成的完整流程**: 查看 `shared/control_tools/scenario_generator.py`

---

## 📝 文档维护

| 文档 | 最后更新 | 维护者 | 状态 |
|-----|---------|--------|------|
| scenario_generator_interface.md | 2025-11-16 | Tech Team | ✅ 最新 |
| EDGEDATA_AGGREGATION_GUIDE.md | 2025-11-16 | Tech Team | ✅ 最新 |
| API_CHANGELOG_v0.9.0.md | 2025-11-16 | Tech Team | ✅ 最新 |
| DHS_COMPLETE_FIX_SUMMARY.md | 2025-11-16 | Tech Team | ✅ 最新 |
| VSS_TEC_EDGEDATA_AGGREGATION_FIX.md | 2025-11-16 | Tech Team | ✅ 最新 |

---

## 📧 反馈

如有问题或建议，请联系开发团队。

**维护者**: OD_SIM Development Team
**更新日期**: 2025-11-16
