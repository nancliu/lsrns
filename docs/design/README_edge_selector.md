# 边选择器文档导航

**版本**: v1.1
**最后更新**: 2025-10-19

---

## 📖 快速导航

### 🚀 我想快速开始

**问题**: 我需要立即实现收费入口管控（TEC）或动态硬路肩管控（DHS）

**答案**: 👉 [edge_selector_scenarios_answer.md](edge_selector_scenarios_answer.md)
- ✅ TEC收费入口管控 - 立即可用，无需开发
- △ DHS动态硬路肩管控 - 基本可用，建议扩展

---

### 📚 我想全面了解边选择器

**推荐阅读顺序**：

1️⃣ **数据库设计** → [edge_selector_database_design.md](edge_selector_database_design.md)
   - 了解数据表结构
   - 理解筛选维度
   - 查看查询策略

2️⃣ **测试报告** → [edge_selector_test_report.md](edge_selector_test_report.md)
   - 查看功能验证结果
   - 了解9种筛选维度的效果
   - 参考推荐筛选策略

3️⃣ **特殊场景方案** → [edge_selector_special_scenarios.md](edge_selector_special_scenarios.md)
   - TEC/DHS详细实现方案
   - API设计示例
   - 数据库扩展建议

---

### 🛠️ 我想开发新功能

**场景1**: 添加新的筛选维度
- 参考：[edge_selector_database_design.md](edge_selector_database_design.md) 第3节
- 代码：[shared/data_access/edge_query.py](../../shared/data_access/edge_query.py)

**场景2**: 支持新的控制策略场景
- 参考：[edge_selector_special_scenarios.md](edge_selector_special_scenarios.md)
- 测试：[tests/test_special_scenarios.py](../../tests/test_special_scenarios.py)

**场景3**: 性能优化
- 参考：[edge_selector_test_report.md](edge_selector_test_report.md) 第4.2节（索引建议）

---

## 📋 文档清单

### 核心设计文档（必读）

| 文档 | 版本 | 用途 | 重要性 |
|------|------|------|--------|
| [edge_selector_database_design.md](edge_selector_database_design.md) | v1.1 | 数据库设计总览 | ⭐⭐⭐⭐⭐ |
| [edge_selector_test_report.md](edge_selector_test_report.md) | v1.1 | 功能验证报告 | ⭐⭐⭐⭐⭐ |

### 特殊场景文档（推荐）

| 文档 | 版本 | 用途 | 重要性 |
|------|------|------|--------|
| [edge_selector_scenarios_answer.md](edge_selector_scenarios_answer.md) | v1.0 | TEC/DHS快速方案 | ⭐⭐⭐⭐⭐ |
| [edge_selector_special_scenarios.md](edge_selector_special_scenarios.md) | v1.0 | TEC/DHS详细方案 | ⭐⭐⭐⭐ |

### 测试脚本

| 脚本 | 用途 | 状态 |
|------|------|------|
| [tests/test_edge_selector_simple.py](../../tests/test_edge_selector_simple.py) | 基础筛选测试 | ✅ 已验证 |
| [tests/test_section_filter.py](../../tests/test_section_filter.py) | 路段筛选测试 | ✅ 已验证 |
| [tests/test_special_scenarios.py](../../tests/test_special_scenarios.py) | 特殊场景数据分析 | ✅ 已验证 |
| [tests/test_detailed_scenarios.py](../../tests/test_detailed_scenarios.py) | 深入场景验证 | ✅ 已验证 |

---

## 🎯 核心功能一览

### 已支持的筛选维度（9种）

| # | 维度 | 参数 | 状态 | 典型场景 |
|---|------|------|------|---------|
| 1 | 路线编码 | route_codes | ✅ | 所有场景 |
| 2 | **路段编码** | **section_codes** | ✅ | 所有场景 |
| 3 | 方向 | route_direction | ✅ | 环线/双向道路 |
| 4 | 桩号范围 | min/max_stake | ✅ | 区域控制 |
| 5 | 路段长度 | min/max_length | ✅ | 策略适配 |
| 6 | 车道数 | min_lanes | ✅ | 容量控制 |
| 7 | 节点类型 | node_types | ✅ | **TEC入口管控** ⭐ |
| 8 | 门架筛选 | with_gantry | ✅ | 观测数据验证 |
| 9 | 示范段 | demonstration_ids | ✅ | 预定义区域 |

### 待扩展的筛选维度（3种）

| # | 维度 | 参数 | 优先级 | 典型场景 | 工作量 |
|---|------|------|--------|---------|--------|
| 10 | 边类型 | edge_types | P0 | TEC, DHS | 0.5天 |
| 11 | TAZ筛选 | taz_ids | P2 | TEC增强 | 1天 |
| 12 | 应急车道 | has_emergency_lane | P1 | DHS | 1-2天 |

---

## 🔍 快速查找

### 按场景查找

**收费入口管控（TEC - Toll Entrance Control）**
- 快速方案：[edge_selector_scenarios_answer.md](edge_selector_scenarios_answer.md) - 问题1
- 详细方案：[edge_selector_special_scenarios.md](edge_selector_special_scenarios.md) - 第3.1节
- 数据验证：[tests/test_special_scenarios.py](../../tests/test_special_scenarios.py)

**动态硬路肩管控（DHS - Dynamic Hard Shoulder）**
- 快速方案：[edge_selector_scenarios_answer.md](edge_selector_scenarios_answer.md) - 问题2
- 详细方案：[edge_selector_special_scenarios.md](edge_selector_special_scenarios.md) - 第3.2节
- 数据验证：[tests/test_detailed_scenarios.py](../../tests/test_detailed_scenarios.py)

**可变限速标志（VSS - Variable Speed Sign）**
- 基础筛选：使用现有9种维度即可
- 推荐策略：[edge_selector_test_report.md](edge_selector_test_report.md) - 第8.2节

---

### 按开发阶段查找

**Phase 1A - 已完成** ✅
- 9种基础筛选维度
- TEC收费入口管控支持
- 完整的测试验证
- 参考：[edge_selector_test_report.md](edge_selector_test_report.md)

**Phase 1B - 规划中** 📋
- edge_types参数（P0）
- query_edges_with_emergency_lanes()（P1）
- query_edges_by_taz()（P2）
- 参考：[edge_selector_special_scenarios.md](edge_selector_special_scenarios.md) - 第4节

**Phase 2 - 未来** 🔮
- 数据库预处理优化
- 缓存机制
- 智能推荐
- 参考：[edge_selector_database_design.md](edge_selector_database_design.md) - 第8节

---

## 💡 常见问题（FAQ）

### Q1: 边选择器支持TAZ筛选吗？

**A**: 部分支持
- ✅ 通过`demonstration_ids`间接筛选（TAZ关联示范段）
- 📋 直接TAZ筛选需要扩展（P2优先级，工作量1天）
- 详见：[edge_selector_scenarios_answer.md](edge_selector_scenarios_answer.md)

### Q2: 如何识别应急车道？

**A**: 两种方案
- 短期：基于车道数推断（`min_lanes≥5`）✅ 立即可用
- 长期：关联sim_network_lanes表精确识别 📋 需扩展
- 详见：[edge_selector_special_scenarios.md](edge_selector_special_scenarios.md) - 第3.2节

### Q3: 边、路段、路线的层级关系是什么？

**A**: 三级层级
```
路线 (Route) - route_code (如G4202)
  └── 路段 (Section) - section_code (如G4202001)
        └── 边 (Edge) - edge_id (如-6638.218)
```
- 详见：[edge_selector_test_report.md](edge_selector_test_report.md) - 测试用例1A

### Q4: 如何添加新的筛选维度？

**A**: 三步流程
1. 更新`query_edges_with_filters()`函数添加参数
2. SQL查询中添加WHERE条件
3. 编写测试验证
- 参考代码：[shared/data_access/edge_query.py](../../shared/data_access/edge_query.py)

---

## 📊 数据统计

**测试数据规模**（截至2025-10-19）：
- 边（Edge）: 8000+条
- 路线（Route）: 8条
- 路段（Section）: 26个
- 示范段（Demonstration）: 9个
- TAZ映射: 461条
- 车道配置: 覆盖大部分主路

**筛选效果**：
- 路线筛选：1198个边 → 需进一步筛选
- 路段筛选：621个边 → 减少48%
- 综合筛选：可精确到4-15个边 ✅

---

## 🔗 外部链接

- **SUMO文档**: https://sumo.dlr.de/docs/
- **TAZ配置**: https://sumo.dlr.de/docs/Definition_of_Vehicles,_Vehicle_Types,_and_Routes.html#traffic_assignement_zones_taz
- **车道配置**: https://sumo.dlr.de/docs/Networks/SUMO_Road_Networks.html#lane-specific_definitions

---

**文档维护者**: OD_SIM开发团队
**最后更新**: 2025-10-19
**反馈方式**: 项目issue或技术讨论会
