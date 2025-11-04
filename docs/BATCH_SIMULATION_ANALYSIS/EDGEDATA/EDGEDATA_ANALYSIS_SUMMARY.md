# SUMO EdgeData 分析体系汇总

**文档创建日期**: 2025-11-04
**分析范围**: SUMO EdgeData 配置、结果内容、第二层批量分析功能设计
**目标受众**: 项目经理、开发团队、业务分析师

---

## 📋 文档清单

本分析共生成**3份详细文档**，共计**15000+字**：

### 1. **[EDGEDATA_ANALYSIS_COMPREHENSIVE_GUIDE.md](./EDGEDATA_ANALYSIS_COMPREHENSIVE_GUIDE.md)** (主文档)
   - **内容**: EdgeData 配置方法、输出结构、28项功能的完整规格
   - **篇幅**: 约8000字
   - **章节**:
     - 1. EdgeData 配置方法 (参数详解、模板、sumocfg集成)
     - 2. EdgeData 输出结果内容 (XML结构、数据属性、实际示例)
     - 3. 第二层批量分析功能设计 (功能分类、功能单、规格说明)
     - 4. 详细功能规格 (核心优先级功能的详细说明)
     - 5. 数据流架构与技术实现建议
     - 6. 实现时间线与项目计划

### 2. **[BATCH_EDGEDATA_ANALYSIS_FEATURE_SPECIFICATIONS.md](./BATCH_EDGEDATA_ANALYSIS_FEATURE_SPECIFICATIONS.md)** (详细规格)
   - **内容**: 28项功能的具体API和实现规格
   - **篇幅**: 约5000字
   - **结构**:
     - API 端点定义 (REST 接口)
     - 功能分组A-F的Python伪代码和输入输出规格
     - 数据处理管道设计
     - 优先级与依赖关系
     - 详细的开发任务列表 (10个Sprint)

### 3. **[EDGEDATA_ANALYSIS_FEATURE_MATRIX.md](./EDGEDATA_ANALYSIS_FEATURE_MATRIX.md)** (快速查询)
   - **内容**: 28项功能的矩阵表、依赖链、快速查询
   - **篇幅**: 约2000字
   - **用途**:
     - 功能全景图
     - 按优先级分类统计
     - 按场景和格式快速查询
     - 实现路线图
     - 成功标准

---

## 🎯 核心发现

### 1️⃣ EdgeData 配置现状

**配置方法**:
```xml
<edgeData id="ed1"
    freq="300"           <!-- 采集间隔：秒 -->
    file="edgedata.xml"  <!-- 输出文件 -->
    excludeEmpty="true"  <!-- 排除空边 -->
    withInternal="false"/><!-- 排除内部边 -->
```

**关键参数**:
- `freq`: 时间粒度（通常300-600秒）
- `edges`: 可选，指定边列表（空=全部）
- `type`: 可选，输出类型（基础、排放、噪声等）

**当前集成**:
- 模板位置: `templates/edge_add/edgeData.add.xml`
- 在 sumocfg 中通过 `<additional-files>` 引入
- 输出目录: `simulations/{sim_id}/edgedata/edgedata.xml`

---

### 2️⃣ EdgeData 输出内容

**XML 结构**:
```xml
<meandata>
  <interval begin="0" end="300" id="ed1">
    <edge id="-8712"
          entered="48"           <!-- 进入车数 -->
          left="48"              <!-- 离开车数 -->
          speed="8.5"            <!-- 平均速度 m/s -->
          traveltime="45.23"     <!-- 平均通过时间 秒 -->
          density="12.34"        <!-- 车/km -->
          occupancy="0.156"      <!-- 占用率 0-1 -->
          waitingTime="234.5"    <!-- 等待总时长 秒 -->
          sampledSeconds="2145.67"/> <!-- 采样秒数 -->
  </interval>
</meandata>
```

**关键指标**:
| 指标 | 单位 | 用途 | 范围 |
|------|------|------|------|
| **entered/left** | 辆 | 流量计算 | 0-∞ |
| **speed** | m/s | 通行能力评估 | 0-50 |
| **density** | 车/km | 拥堵程度 | 0-150 |
| **occupancy** | 无 | 路段使用率 | 0-1 |
| **waitingTime** | 秒 | 延误评估 | 0-∞ |

**派生指标**:
- **流量率** = entered / (interval_duration / 3600) [车/小时]
- **拥堵指数** = waitingTime / interval_duration [0-1]
- **效率指数** = (speed/max_speed) × (flow/capacity) × (1-congestion_index)

---

### 3️⃣ 第二层功能体系

**现状**: 仅有第一层单仿真分析（edgedata_analysis.py）
**需求**: 构建28项第二层功能，支持多仿真对比、策略评估、时空分析

**功能分布**:

```
分组A: 批量对比分析 (5项)
├─ F2-A1 流量对比         ✓ P0 (高优先级)
├─ F2-A2 速度对比         ✓ P0
├─ F2-A3 拥堵对比         ✓ P0
├─ F2-A4 路段评估         ✓ P1
└─ F2-A5 峰值对比         ✓ P1

分组B: 时空演变分析 (4项)
├─ F2-B1 拥堵扩散         ✓ P0 (关键)
├─ F2-B2 流量波传播       ✓ P1
├─ F2-B3 速度梯度         ✓ P1
└─ F2-B4 连锁效应         ✓ P2

分组C: 控制策略评估 (5项)
├─ F2-C1 VSS评估          ✓ P0 (战略需求)
├─ F2-C2 TEC评估          ✓ P0
├─ F2-C3 DHS评估          ✓ P0
├─ F2-C4 协调控制         ✓ P1
└─ F2-C5 KPI量化          ✓ P0

分组D: 优化效果量化 (5项)
├─ F2-D1 路段优化度量     ✓ P0
├─ F2-D2 全网效率评估     ✓ P0
├─ F2-D3 成本效益分析     ✓ P1
├─ F2-D4 环保评估         ✓ P2
└─ F2-D5 可靠性评估       ✓ P2

分组E: 高级分析 (4项)
├─ F2-E1 拥堵分类         ✓ P1
├─ F2-E2 瓶颈识别         ✓ P1
├─ F2-E3 措施排序         ✓ P1
└─ F2-E4 时间序列预测     ✓ P2

分组F: 报告与可视化 (5项)
├─ F2-F1 综合报告         ✓ P0
├─ F2-F2 交互仪表板       ✓ P0
├─ F2-F3 地图可视化       ✓ P1
├─ F2-F4 动画生成         ✓ P2
└─ F2-F5 数据导出         ✓ P1

总计: 28项功能
P0优先级: 13项 (基础与战略)
P1优先级: 10项 (重要增强)
P2优先级: 5项 (高级与研究)
```

---

## 📊 优先级分析

### P0 优先级 (必须实现)

**13项功能**，预计工作量: **28.5人天**，周期: **3周**

| 功能 | 目的 | 关键价值 |
|------|------|---------|
| **A1-A3** | 多方案流量/速度/拥堵对比 | 支持决策对标 |
| **C1-C3** | VSS/TEC/DHS 策略评估 | 量化控制效果 |
| **C5** | KPI 量化 | 目标管理 |
| **D1-D2** | 路段与全网效率 | 优化效果评估 |
| **B1** | 拥堵扩散分析 | 理解路网行为 |
| **F1-F2** | 报告与仪表板 | 成果展示 |

**预期收益**:
✓ 支持3+方案并行对比
✓ 自动化策略评估评分
✓ 15分钟内生成完整报告
✓ 支持实时仪表板展示

---

### P1 优先级 (重要补充)

**10项功能**，工作量: **23.5人天**，周期: **2.5周**

重点功能:
- **A4-A5**: 路段评估与峰值分析（详细视角）
- **B2-B3**: 流量波与速度梯度（科学分析）
- **E1-E2**: 拥堵分类与瓶颈识别（根因诊断）
- **C4**: 协调控制评估（复杂场景）
- **D3**: 成本效益分析（经济决策）
- **F3, F5**: 地图与数据导出（扩展应用）

---

### P2 优先级 (后续迭代)

**5项高级功能**，工作量: **14.5人天**

用于深度研究和学术发表:
- B4: 路网连锁效应
- D4: 环保评估
- D5: 可靠性评估
- E4: 时间序列预测
- F4: 动画生成

---

## 🛠️ 技术架构

### 模块划分

```
api/services/
├── batch_edgedata_analysis_service.py  [新增]
│   ├── compare_scenarios()             # F2-A系列
│   ├── evaluate_strategy()             # F2-C系列
│   ├── analyze_spatial_temporal()      # F2-B系列
│   └── quantify_optimization()         # F2-D系列

shared/analysis_tools/
├── batch_edgedata_analysis.py          [新增]
│   ├── BatchEdgeDataAnalysis class
│   ├── MultiScenarioComparison
│   ├── StrategyEvaluation
│   ├── SpatialTemporalAnalysis
│   └── ReportGeneration

api/routes/
└── batch_analysis_routes.py            [新增]
    ├── POST /api/v1/analysis/batch-edgedata/compare
    ├── POST /api/v1/analysis/batch-edgedata/strategy-evaluation
    └── POST /api/v1/analysis/batch-edgedata/spatial-temporal
```

### 数据流

```
输入: 2+ EdgeData XML
  ↓
数据加载与验证 (支持并行)
  ↓
DataFrame 合并 (时间对齐)
  ↓
统计计算 (vectorized pandas)
  ↓
┌─────────────────────────────┐
├─ 对比分析 (F2-A)
├─ 策略评估 (F2-C)
├─ 时空分析 (F2-B)
└─ 优化评估 (F2-D)
  ↓
┌─────────────────────────────┐
├─ 高级分析 (F2-E)
├─ 根因诊断
└─ 建议生成
  ↓
报告与可视化 (F2-F)
  ↓
输出: HTML报告 + 图表 + CSV/JSON
```

---

## 📈 实现时间线

### 总体计划: **5.5周** (实际5-6周含测试)

```
Week 1-2 (P0基础):
  ✓ 框架搭建 (1天)
  ✓ F2-A1/A2/A3 (4天)
  ✓ F2-D1/D2 (2天)
  ✓ 测试与调试 (1.5天)
  → 里程碑: 支持多方案对比

Week 2-3 (P0策略):
  ✓ F2-C1/C2/C3 (5天)
  ✓ F2-C5 (2天)
  ✓ F2-A4 (1.5天)
  → 里程碑: 策略评估可用

Week 3 (P0时空+报告):
  ✓ F2-B1 (3天)
  ✓ F2-F1/F2 (5天)
  → 里程碑: 完整报告生成

Week 4 (P1核心):
  ✓ F2-A5/B2/B3 (4.5天)
  ✓ F2-E1/E2 (4天)
  ✓ F2-C4 (2.5天)
  → 里程碑: 高级分析可用

Week 5 (P1/P2补充):
  ✓ F2-D3 (2.5天)
  ✓ F2-F3/F5 (5.5天)
  ✓ P2初步支持 (3天)
  → 里程碑: 完整功能体系
```

**人力配置**:
- Phase 1 (2周): 1人 (基础开发)
- Phase 2 (1周): 1人 (继续开发)
- Phase 3 (2周): 1-2人 (并行开发)
- **总计**: 5人周 (5周 × 1人 或 2.5周 × 2人)

---

## 📝 关键指标

### 功能覆盖度

| 指标 | P0完成 | P0+P1完成 | 全部完成 |
|------|--------|----------|---------|
| 功能数量 | 13/28 | 23/28 | 28/28 |
| 覆盖比例 | 46% | 82% | 100% |
| 工作量 | 28.5天 | 52天 | 66.5天 |
| 时间周期 | 3周 | 5.5周 | 6.5周 |

### 性能指标

| 指标 | 目标 | 方法 |
|------|------|------|
| **单仿真处理时间** | <30秒 | 向量化计算 + 缓存 |
| **10仿真对比** | <5分钟 | 并行处理 |
| **报告生成** | <2分钟 | 模板渲染 |
| **内存占用** | <2GB | Chunking + 清理 |
| **准确度** | ±1% | 单元测试验证 |

---

## 🚀 快速启动指南

### 立即开始 (Week 1)

1. **阅读完整规格**
   - 仔细阅读 `EDGEDATA_ANALYSIS_COMPREHENSIVE_GUIDE.md`
   - 理解 28 项功能的目的和输入输出

2. **设计数据结构**
   - 定义标准 EdgeData DataFrame 格式
   - 设计分析结果的 JSON 结构

3. **实现基础框架**
   ```python
   # shared/analysis_tools/batch_edgedata_analysis.py
   class BatchEdgeDataAnalysis:
       def load_scenarios(scenarios: Dict[str, str]) -> Dict[str, pd.DataFrame]
       def compute_comparison(scenarios) -> Dict
       def generate_report() -> str
   ```

4. **先实现 P0 功能**
   按顺序: A1 → A2 → A3 → D1 → D2 → C1/C2/C3 → B1 → F1/F2

### 验收标准

- [ ] 支持 2-10 个方案并行对比
- [ ] 流量/速度/拥堵对比准确度 ≥99%
- [ ] 策略评估评分一致性 ≥95%
- [ ] 报告自动生成无缺陷
- [ ] API 响应时间 <5 秒/方案
- [ ] 单元测试覆盖率 ≥90%

---

## 📚 相关资源

### 项目内部文档
- `[CLAUDE.md](./CLAUDE.md)` - 项目规范和架构
- `[openspec/project.md](../openspec/project.md)` - 项目管理规范
- `[api/services/edgedata_service.py](../api/services/edgedata_service.py)` - 当前第一层实现
- `[shared/analysis_tools/edgedata_analysis.py](../shared/analysis_tools/edgedata_analysis.py)` - 单仿真分析

### SUMO 官方资源
- [Eclipse SUMO EdgeData Documentation](https://github.com/eclipse-sumo/sumo)
- [Lane-/Edge-based Traffic Measures](https://github.com/eclipse-sumo/sumo/docs/web/docs/Simulation/Output/Lane-_or_Edge-based_Traffic_Measures.md)

### 相关工具
- **Pandas**: 数据处理
- **Matplotlib/Seaborn**: 静态图表
- **Plotly/Dash**: 交互式仪表板
- **Folium**: 地图可视化
- **NetworkX**: 网络分析

---

## ❓ FAQ

**Q: 为什么需要第二层批量分析？**
A: 第一层分析（单仿真）无法对比方案效果、评估策略影响，无法支持决策。第二层支持多方案对标，定量评估控制策略效果。

**Q: P0 功能能否在 3 周完成？**
A: 是的，P0 功能相对独立，预计 28.5 人天，1 人可在 3-4 周完成（考虑测试和迭代）。

**Q: 支持的最大方案数量？**
A: 理论上无限制，但实际考虑内存和性能，建议 ≤20 个方案。超过时可分批处理。

**Q: EdgeData 采集频率对结果的影响？**
A: freq=300（5分钟）适合宏观分析；freq=60（1分钟）适合微观拥堵分析。建议使用 300-600 秒。

**Q: 与 Accuracy Analysis 有什么区别？**
A: Accuracy Analysis 比较仿真 vs 实际观测数据；Batch EdgeData Analysis 比较不同仿真方案之间的差异。

**Q: 能否与控制策略 API 集成？**
A: 是的，F2-C1/C2/C3 正是为此设计的，可直接评估策略效果。

---

## 📞 联系与反馈

**文档维护**: AI Assistant (Claude Code)
**最后更新**: 2025-11-04
**版本**: v1.0
**状态**: 功能规格确认，待开发实现

如有疑问或建议，请更新本文档或在项目讨论中提出。

---

**END OF SUMMARY**
