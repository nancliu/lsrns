# Phase 2 OpenSpec Proposal Complete - Implementation Ready

**Date**: 2025-11-12
**Status**: ✅ Ready for Implementation
**Change ID**: `event-scenario-simulation-integration`
**Location**: `openspec/changes/event-scenario-simulation-integration/`

---

## 📋 Executive Summary

完整的第二阶段 OpenSpec 提案已创建，包含了从事件场景到仿真分析的端到端工作流设计。该提案建立在第一阶段（449个事件场景库）的基础之上，实现了**场景→仿真→分析→结果展示**的完整闭环。

### 核心交付物

| 文件 | 大小 | 内容 |
|------|------|------|
| `proposal.md` | 16.5 KB | 总体目标、问题陈述、解决方案、成功标准 |
| `design.md` | 36 KB | 架构设计、组件设计、数据模型、测试策略 |
| `tasks.md` | 29 KB | 按周分解的任务清单、优先级、依赖关系、验收标准 |

---

## 🎯 Phase 2 总体目标

**用户期望的完整流程**：
```
事件场景库 (Phase 1 ✅)
    ↓
创建案例 (已实现)
    ↓
创建仿真 + SUMO配置 (NEW - P0)
    ↓
执行仿真 + 实时监控 (NEW - P1)
    ↓
自动运行分析 (NEW - P0/P2)
    ├─ EdgeData分析 (MANDATORY)
    ├─ TripInfo分析 (OPTIONAL)
    ├─ Accuracy分析 (OPTIONAL)
    └─ Performance分析 (OPTIONAL)
    ↓
查看分析结果 (NEW - P2)
    ├─ 热力图可视化
    ├─ 统计数据对比
    └─ 下载报告
```

---

## 📐 三个新的架构决策 (ADR)

### AD-12: 三层元数据追踪 (Metadata Lineage)

**问题**: 如何确保分析结果能完整回溯到源场景？

**决策**: 建立 Case → Simulation → Analysis 的三层元数据链

```json
Case Metadata (source_scenario_id)
    ↓ 1:1 绑定
Simulation Metadata (source_scenario_id)
    ↓ 1:N 关系
Analysis Metadata (source_scenario_id)
```

**好处**:
- ✅ 完整的追踪链：分析结果 → 源场景 → 源事件
- ✅ 数据隔离：分析永不修改case/simulation元数据
- ✅ 可重现性：可完全重建历史分析

---

### AD-13: SUMO配置相对路径策略 (Portable Configs)

**问题**: 用户在不同机器上运行SUMO，绝对路径会失效

**决策**: 生成sumocfg使用相对路径（从sumocfg位置计算）

```xml
<!-- BEFORE (不可移植)
<net-file value="D:\projects\OD_SIM\templates\network_files\sichuan.net.xml"/>
-->

<!-- AFTER (可移植)
<net-file value="../../templates/network_files/sichuan.net.xml"/>
-->
```

**好处**:
- ✅ Cases可在不同路径上运行
- ✅ Cases可在不同机器上移植
- ✅ Docker容器支持

---

### AD-14: 分析批处理并发管理 (Analysis Concurrency)

**问题**: 需要在N个仿真上运行M种分析（可能很耗时），如何管理资源？

**决策**: 支持2-8个worker的配置化工作池

```python
# 例子：80个仿真 × 4种分析 = 320个任务
# 使用4个worker，可在8小时内完成
paralell_workers = 4
```

**好处**:
- ✅ 可配置性：根据硬件选择worker数
- ✅ 可扩展性：支持449个场景的批处理
- ✅ 可监控性：实时进度跟踪

---

## 🏗️ 核心模块设计

### 模块1: 三层元数据系统 (P0 - 阻塞)

**职责**: 确保数据完整性和可追踪性

**实现位置**:
- `api/services/analysis_orchestration_service.py` - 生成analysis_metadata.json
- `shared/data_processors/simulation_processor.py` - 生成simulation_metadata.json
- `api/services/scenario_service.py` - 确保case_metadata.json有source_scenario_id

**关键设计**:
- 元数据文件JSON格式，不可修改后创建
- 分析服务只读元数据（ISOLATION PRINCIPLE）
- 支持完整回溯：analysis → simulation → case → scenario

---

### 模块2: 分析编排服务 (P0 - 阻塞)

**职责**: 管理多个仿真上的4种分析任务

**新组件**:
- `AnalysisOrchestrationService` - 任务队列和执行管理
- `AnalysisProgressTracker` - 实时进度跟踪
- `analysis_tasks_index.json` - 任务状态持久化

**关键特性**:
- EdgeData MANDATORY（AD-10约束）
- TripInfo/Accuracy/Performance OPTIONAL
- 支持配置化的worker pool (2-8)
- 自动重试（最多3次）
- 10秒更新间隔（不是1秒，降低DB压力）

---

### 模块3: SUMO配置生成器 (P0 - 关键)

**职责**: 生成可移植的SUMO配置文件

**扩展位置**: `shared/utilities/sumo_utils.py`

**关键算法**:
1. 计算相对路径：从sim目录 → templates/data目录
2. 生成sumocfg with 相对路径
3. 验证所有路径可达

**例子**:
```
From: cases/case_id/simulations/sim_id/simulation.sumocfg
To:   templates/network_files/xxx.net.xml
Relative: ../../templates/network_files/xxx.net.xml
```

---

### 模块4: 仿真执行服务扩展 (P1)

**职责**: 批量执行多个仿真

**扩展方法**:
- `batch_start_simulations()` - 批量启动
- `get_batch_execution_status()` - 实时进度
- `validate_simulation_results()` - 输出验证

**关键特性**:
- Worker pool并发（复用BatchOptimizationService模式）
- SUMO日志捕获和压缩
- 结果文件验证（summary.xml, tripinfo.xml, edgedata.xml）
- 完成后自动触发分析

---

### 模块5: 结果聚合和报告 (P2)

**职责**: 汇总多个仿真的分析结果

**新组件**:
- `AnalysisResultsService` - 结果聚合和对比
- `AnalysisResultsResponse` - 可视化友好的数据格式

**关键特性**:
- 聚合EdgeData指标（跨仿真）
- 生成对比报告（基线 vs 事件 vs 事件+控制）
- 支持PDF/JSON下载

---

### 模块6: 前端组件重构 (P1)

**目标**: 从74 KB单文件拆分为可复用组件

**新组件**:
- `shared-utils.js` - 通用工具函数
- `api-client.js` - 集中API调用
- `simulation-monitor.js` - 仿真执行实时监控
- `analysis-results.js` - 分析结果展示

**设计原则**:
- 每个组件单一职责（仿真监控 ≠ 分析结果）
- 可复用性（工具函数不硬编码）
- 实时更新（5-10秒轮询，不是1秒）

---

## 📊 实现规划

### 按优先级分组

**P0 (Week 1 - 阻塞其他任务)**:
- ✅ Analysis Orchestration Service
- ✅ Three-level metadata tracking
- ✅ Analysis progress tracking
- ✅ Data models for analysis
- ✅ API routes for analysis

**P1 (Week 2 - 核心功能)**:
- ✅ Simulation execution (batch)
- ✅ SUMO config generation (relative paths)
- ✅ Batch simulation routes
- ✅ Frontend refactoring
- ✅ Simulation monitor UI

**P2 (Week 3 - 完整体验)**:
- ✅ Analysis results aggregation
- ✅ Results API routes
- ✅ Analysis results dashboard
- ✅ Visualization (heat maps, stats)

**P3 (Week 4 - 生产就绪)**:
- ✅ Error recovery and retries
- ✅ Performance testing
- ✅ Integration & E2E tests
- ✅ Documentation
- ✅ Code review

---

### 任务统计

| Week | 任务数 | 总工作量 | 关键交付物 |
|------|--------|--------|----------|
| 1 | 6 | 5-6 天 | Analysis services + metadata |
| 2 | 6 | 5-6 天 | Batch execution + frontend |
| 3 | 4 | 4-5 天 | Analysis results + dashboard |
| 4 | 6 | 4-5 天 | Testing, docs, polish |
| **总计** | **22** | **18-22 天** | **完整Phase 2** |

---

## 🔍 关键设计决策解读

### 为什么选择三层元数据？

**可选方案对比**:

| 方案 | 优点 | 缺点 | 我们的选择 |
|------|------|------|----------|
| **单层** (只有Case) | 简单 | 无法回溯，数据易混淆 | ❌ |
| **两层** (Case + Sim) | 较好 | 仍无法从分析追踪到场景 | ❌ |
| **三层** (Case + Sim + Analysis) | 完整追踪 | 稍复杂 | ✅ |

**决策**: 选择三层，因为可完整回溯是处理449个场景时的关键。

---

### 为什么强制EdgeData而不强制其他分析？

**AD-10约束** (来自Phase 1):
```
EdgeData = 必需（道路段级分析，对场景影响评估关键）
TripInfo = 可选（行程级分析，额外信息）
Accuracy = 可选（需要真实数据，有时无法进行）
Performance = 可选（系统性能，不总是相关）
```

**原因**: EdgeData提供最直接的事件影响评估，不需要外部数据。

---

### 为什么采用相对路径而不采用其他方案？

**可选方案对比**:

| 方案 | 优点 | 缺点 | 我们的选择 |
|------|------|------|----------|
| **绝对路径** | 简单 | 不可移植 | ❌ |
| **环境变量** (SUMO_HOME) | 灵活 | 需要用户配置 | ❌ |
| **相对路径** | 可移植，无需配置 | 需要计算 | ✅ |
| **符号链接** | 灵活 | Windows不支持 | ❌ |

**决策**: 相对路径，因为自动化且可移植。

---

## 📈 成功标准

### 功能完成度
- [ ] 用户可点击"创建仿真" → 自动生成SUMO配置
- [ ] 用户可批量启动仿真 + 实时监控进度
- [ ] 仿真完成 → 自动运行4种分析
- [ ] 分析进度可视化（不是等待最后的大惊喜）
- [ ] 结果展示：热力图、统计数据、对比报告

### 规模验证
- [ ] 支持449个场景的完整流程
- [ ] 单个案例最多100个仿真的批处理
- [ ] 80个仿真 × 4种分析 = 320任务，可在8-10小时内完成

### 质量标准
- [ ] 元数据链完整（可从分析回溯到源场景）
- [ ] SUMO配置可移植（相对路径）
- [ ] 单元测试覆盖 > 80%
- [ ] 集成测试覆盖完整工作流
- [ ] E2E测试验证用户体验

### 文档完整度
- [ ] 用户指南（含截图和步骤）
- [ ] API文档（所有新端点）
- [ ] 开发指南（扩展方法）
- [ ] AD-12/13/14记录在CLAUDE.md

---

## 🚀 立即可执行的行动

### 1. Review & Approve Proposal
```bash
# 检查proposal是否合理
# 文件位置: openspec/changes/event-scenario-simulation-integration/proposal.md
```

### 2. Setup Development Environment
```bash
# 确保环境准备好
conda activate od_project
python -m pytest --version  # 验证pytest
node --version              # 验证Node.js
```

### 3. Create Implementation Tracking
```bash
# 根据tasks.md创建项目管理工具中的任务
# 或使用todo list跟踪
```

### 4. Start Week 1 Tasks
```bash
# Task 1.1: AnalysisOrchestrationService
# Task 1.2: Analysis routes
# Task 1.3: Data models
# Task 1.4: Metadata structure
# Task 1.5: Progress tracking
# Task 1.6: Unit tests
```

---

## 💡 关键洞察

### 1. 复用已有的BatchOptimizationService模式
- 不需要重新发明轮子
- BatchOptimizationService在生产中证明有效
- Analysis orchestration可直接复用worker pool模式

### 2. 元数据隔离是关键
- 分析服务只读元数据
- 不修改case或simulation的metadata.json
- 确保数据安全和可追踪

### 3. 进度可视化很重要
- 长时间运行的操作需要进度反馈
- 10秒更新间隔是平衡（不是太快太慢）
- 前端实时监控改善用户体验

### 4. 前端重构带来长期收益
- 74 KB单文件难以维护
- 组件化设计支持未来扩展
- scenario_browser.js是良好范例

---

## 📚 参考文献

**Phase 1 完成文档**:
- `FINAL_STATUS_REPORT.md` - Phase 1总结
- `docs/PHASE_1_SCENARIO_BACKEND_IMPLEMENTATION.md` - Phase 1详细设计
- `IMPLEMENTATION_COMPLETE.md` - Phase 1前端完成

**项目规范**:
- `CLAUDE.md` - 项目开发指南
- `openspec/project.md` - 项目上下文

**相关ADR**:
- `AD-7`: 1:1 Case-Scenario Binding (Phase 1)
- `AD-8`: Configuration Override Policy (Phase 1)
- `AD-9`: Batch Concurrency Support (Phase 1)
- `AD-10`: EdgeData Analysis Mandatory (Phase 1)
- `AD-11`: Manual Result Retention (Phase 1)
- `AD-12`: Three-Level Metadata Tracking (Phase 2 NEW)
- `AD-13`: SUMO Configuration Relative Paths (Phase 2 NEW)
- `AD-14`: Analysis Orchestration Concurrency (Phase 2 NEW)

---

## 🎬 后续步骤

### 立即执行
1. ✅ Review this summary document
2. ✅ Discuss proposal with team
3. ✅ Approve or request revisions
4. ✅ Create project tracking

### Week 1开始
1. ✅ Assign Task 1.1-1.6 to team members
2. ✅ Setup code review process
3. ✅ Daily standup to track progress

### 每周结束
1. ✅ Sprint review (demo working features)
2. ✅ Sprint retro (lessons learned)
3. ✅ Plan next week

---

## 📞 Questions & Support

**如果有疑问**:
1. 检查 `openspec/changes/event-scenario-simulation-integration/` 中的详细设计文档
2. 查阅 CLAUDE.md 中的相关原则
3. 参考 Phase 1 的实现（许多模式可以复用）

**如果需要澄清**:
1. AD-12/13/14 的决策逻辑
2. 任务优先级和依赖关系
3. 特定组件的实现细节

---

**OpenSpec Proposal Complete ✅**

**Status**: Ready for team review and implementation approval

**Document Generated**: 2025-11-12
**Change ID**: `event-scenario-simulation-integration`
**Location**: `openspec/changes/event-scenario-simulation-integration/`

---

# 额外资源：Week 1快速启动清单

## 开发前的准备

### 环境检查
```bash
# 激活环境
conda activate od_project

# 验证依赖
pip show pytest pydantic fastapi

# 检查代码质量工具
black --version
flake8 --version
```

### 代码结构熟悉
```bash
# 查看Phase 1的实现作为参考
cat api/services/scenario_service.py  # 350 LOC, 学习模式
cat api/routes/scenario_routes.py     # 270 LOC, 学习API设计
cat frontend/scenarios/scenario_browser.js  # 学习前端组件化
```

### 创建开发分支
```bash
git checkout -b phase2/analysis-orchestration
git config user.name "Your Name"
git config user.email "your.email@company.com"
```

## Task 1.1 开发指南

### 文件结构
```
api/services/analysis_orchestration_service.py
├─ class AnalysisOrchestrationService
│  ├─ async def create_analysis_batch(...)
│  ├─ async def get_analysis_progress(...)
│  ├─ async def cancel_analysis_batch(...)
│  └─ async def _execute_task_queue(...)
└─ def _queue_analysis_tasks(...)
```

### 测试优先开发（TDD）
```python
# tests/unit/services/test_analysis_orchestration_service.py
# 1. 先写测试
async def test_create_analysis_batch_with_valid_inputs():
    service = AnalysisOrchestrationService()
    response = await service.create_analysis_batch(
        simulation_ids=["sim_1", "sim_2"],
        baseline_scenario_id="scenario_none"
    )
    assert response.batch_id is not None
    assert response.total_tasks == 8  # 2 sims × 4 analysis types

# 2. 再实现功能
```

### 关键检查清单
- [ ] 函数有docstring（Google风格）
- [ ] 所有参数有type hints
- [ ] 异常处理（不要broad except）
- [ ] 日志记录关键操作（不要print()）
- [ ] 单元测试覆盖主路径
- [ ] 没有代码重复（复用helper函数）

---

**祝你好运！Phase 2即将开始 🚀**
