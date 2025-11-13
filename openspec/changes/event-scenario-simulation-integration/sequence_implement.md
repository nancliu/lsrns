 建议的开发实施步骤

  📋 总体规划

  总工时: 3-4周 (2人团队)开发顺序: 基础设施 → 执行层 → 结果展示 → 优化完善

  ---
  第一周: 基础设施 (P0 - 阻塞所有其他任务)

  1️⃣ 元数据版本支持 (1天)

  为什么优先: 所有其他任务都依赖于此

  - 实现 detect_metadata_version() 函数
  - 支持 v1.0 (现有OD案例) 和 v2.0 (事件场景案例) 双模式
  - 确保向后兼容,不破坏现有工作流

  2️⃣ SimulationOrchestrator 服务 (2天)

  核心编排层 - 检测仿真来源并委派给合适的服务

  - 创建 api/services/simulation_orchestrator.py
  - 实现源检测逻辑 (事件场景/OD提取/控制方案)
  - 委派给现有服务 (复用 BatchSimulationScheduler)

  3️⃣ AnalysisOrchestrationService 适配层 (2天)

  关键架构决策: 不修改现有分析服务,创建适配层

  - 创建 api/services/analysis_orchestration_service.py
  - 复用 SummaryAnalyzer 和 EdgeDataAnalyzer (共享层,不修改)
  - 不使用 OD分析服务 (accuracy/mechanism等)

  4️⃣ 三级元数据结构 (1.5天)

  实现完整的可追溯链: 场景 → 案例 → 仿真 → 分析

  - Case metadata: 包含 source_scenario_id
  - Simulation metadata: 复制场景配置快照
  - Analysis metadata: 回溯到源场景

  5️⃣ 进度跟踪基础设施 (1天)

  - 实现 AnalysisProgressTracker 类
  - 支持实时进度更新 (每10秒)
  - 计算ETA (预计完成时间)

  6️⃣ 单元测试 (1.5天)

  - 20+ 测试用例覆盖核心功能
  - 代码覆盖率 > 80%

  ---
  第二周: 执行层 & 前端重构 (P1)

  1️⃣ SUMO相对路径生成 (1天)

  AD-13架构决策 - 可移植配置

  - 实现 generate_sumocfg_with_relative_paths()
  - 元数据存储相对于项目根的路径
  - sumocfg使用相对于自身位置的路径

  2️⃣ 批量仿真执行API (1天)

  - 路由: POST /api/v1/simulation/batch-start
  - 路由: GET /api/v1/simulation/batch-status/{batch_id}

  3️⃣ 前端组件重构 - 工具库 (1.5天)

  渐进式重构 - 不修改现有代码

  - 创建 frontend/components/shared-utils.js
  - 创建 frontend/components/api-client.js

  4️⃣ 实时仿真监控UI (2天)

  - 创建 frontend/components/simulation-monitor.js
  - 5-10秒轮询更新
  - 进度条、状态徽章、日志查看器

  5️⃣ 数据模型 (1天)

  - Pydantic模型: 请求/响应验证
  - BatchSimulationStartRequest
  - BatchExecutionStatusResponse

  ---
  第三周: 结果分析 & 可视化 (P2)

  1️⃣ 分析结果聚合 (1.5天)

  - 创建 AnalysisResultsService
  - 聚合多个仿真的EdgeData/TripInfo指标
  - 生成对比报告 (基线 vs 事件 vs 控制策略)

  2️⃣ 分析结果API (1天)

  - 路由: GET /api/v1/analysis/results/{batch_id}
  - 路由: GET /api/v1/analysis/comparison/{batch_id}

  3️⃣ 分析结果可视化仪表板 (2天)

  - 创建 frontend/components/analysis-results.js
  - EdgeData热力图
  - 统计指标展示
  - 对比图表 (绿色=改善, 红色=恶化)

  4️⃣ 响应模型 (1天)

  - EdgeDataMetrics, TripInfoMetrics
  - ComparisonMetrics

  ---
  第四周: 完善 & 生产就绪 (P2/P3)

  1️⃣ 错误恢复和重试 (1天)

  - 实现 @retry 装饰器
  - 指数退避: 1s → 2s → 4s
  - 最多3次重试

  2️⃣ 集成测试 (1.5天)

  - E2E工作流测试
  - 场景 → 案例 → 仿真 → 分析
  - 批量执行 (10个场景)

  3️⃣ Playwright E2E测试 (1.5天)

  - 用户工作流测试
  - UI实时更新验证

  4️⃣ 性能测试 (1天)

  - 50个并发仿真
  - 100个分析任务

  5️⃣ 文档编写 (1.5天)

  - 用户指南 (PHASE_2_USER_GUIDE.md)
  - API参考 (PHASE_2_API_REFERENCE.md)
  - 开发者指南
  - 更新 CLAUDE.md

  6️⃣ 代码审查和质量检查 (1天)

  - 覆盖率 > 80%
  - 无循环依赖
  - 元数据隔离验证

  ---
  🔀 并行化策略 (2人团队)

  Person A (后端):
  - Week 1: 1.1, 1.2, 1.3, 1.4
  - Week 2: 2.1, 2.2, 2.3
  - Week 3: 3.1, 3.2
  - Week 4: 4.1, 4.2, 4.5

  Person B (前端+测试):
  - Week 1: 1.6 (测试)
  - Week 2: 2.4, 2.5, 2.6
  - Week 3: 3.3, 3.4
  - Week 4: 4.3, 4.4, 4.5

  ---
  ✅ 成功标准

  - 用户可以点击"从场景创建案例" → 自动创建仿真
  - 批量启动10+仿真并实时监控进度
  - 仿真完成后自动运行4种分析
  - 分析进度可见 (不只是最终结果)
  - 可视化结果 (热力图、统计数据、对比)
  - 完整元数据链: 场景 → 案例 → 仿真 → 分析
  - 449个场景全部可仿真和分析
  - SUMO配置可移植 (不同机器/路径可用)
  - 无数据损坏 (元数据隔离)
  - 前端响应流畅

  ---
  🚨 关键非破坏性原则

  1. 新服务不修改现有服务接口
  2. 新元数据字段可选 (向后兼容)
  3. 新API使用独立端点 (不覆盖现有)
  4. 现有工作流继续正常工作:
    - ✅ OD提取仿真
    - ✅ 控制方案优化
    - ✅ 前端页面 (index.html, control/, scenarios/)

  这个实施计划遵循OpenSpec的设计决策 (Q1-Q14) 和架构原则,确保在不破坏现有功能的前提下完成Phase 2集成。