# 管控方案优化子系统开发任务清单

**文档版本**: v2.1
**更新日期**: 2025-10-04
**当前阶段**: Phase 2 基本完成,进入性能验证阶段
**当前版本**: v0.4.0 (Epic 2-5 核心功能已完成)

**关联文档**:
- [下一阶段开发建议_20251003.md](./planning/下一阶段开发建议_20251003.md) - 开发建议与规划
- [控制策略边选择方法论_v2.0.md](./design/控制策略边选择方法论_v2.0.md) - 理论框架
- [边选择方法论融入方案.md](./planning/边选择方法论融入方案.md) - 方法论融入详细方案

---

## 当前状态总览

### ✅ 已完成功能 (截至2025-10-03)

**MVP Phase 1** (2025-10-02完成)

**核心成果**:

- ✅ 批量配置生成（共享配置模式）
- ✅ 并行仿真执行（10实例验证通过，603秒完成）
- ✅ 实例独立目录隔离（每个instance独立的sumocfg + TAZ + e1/ + edgedata/）
- ✅ 前端界面（mvp_parallel_simulation.html）
- ✅ 系统集成（独立路由，不影响主系统）

**技术债务修复** (2025-10-02):

- ✅ anyio 4.11.0 依赖问题修复
- ✅ `list_plans()` 方法缺失修复
- ✅ TraCI连接失败 → 改用subprocess直接运行SUMO
- ✅ 相对路径解析问题 → 使用os.path.relpath()自动计算

**Epic 2.5: 多策略配置支持** (2025-10-03完成)
- ✅ 策略生成器（VSL/DHS/zone_restriction/baseline）
- ✅ 批量配置生成器（独立配置模式）
- ✅ 21/21单元测试 + 3/4集成测试通过
- ✅ 3个API端点上线

**Epic 3.1: EdgeData输出配置** (2025-10-03完成)
- ✅ EdgeData分层模板架构（节点/设施/路网三层）
- ✅ EdgeSelector类实现（K=2拓展算法）
- ✅ 占位符替换机制（`{{EDGES_SPACE_SEPARATED}}`）
- ✅ 5/5测试场景通过

**Epic 3.3: EdgeData解析与指标提取** (2025-10-03完成)
- ✅ EdgeDataParser流式解析(282行)
- ✅ EdgeDataAnalyzer关键指标计算(530行,5大指标)
- ✅ MetricsService数据库存储
- ✅ 70/70测试通过

**Epic 3.4: 基准场景管理** (2025-10-03完成)
- ✅ 基准场景数据模型与数据库表
- ✅ BaselineScenarioService完整CRUD
- ✅ 7个API端点
- ✅ 25/25测试通过

**Epic 4.1: 评分模型实现** (2025-10-03完成)
- ✅ MetricNormalizer标准化(Min-Max)
- ✅ ScoringEngine加权评分
- ✅ DataCleaner数据清洗
- ✅ 39/39测试通过

**Epic 4.2: 排名与Top3推荐** (2025-10-03完成)
- ✅ Ranker批次排名算法(449行)
- ✅ RankingService业务编排(389行)
- ✅ 4个API端点(排名/Top3/对比)
- ✅ 24/24测试通过

**Epic 4.3: 结果导出** (2025-10-03完成)
- ✅ ExportService JSON/CSV导出(586行)
- ✅ 3种导出类型(完整/Top3/对比)
- ✅ 4个API端点
- ✅ 4/4测试通过

**Epic 5.1: 结果页面开发** (2025-10-03完成)
- ✅ Top3推荐卡片(排名徽章/指标/推荐理由)
- ✅ 指标对比图表(柱状图+雷达图,Chart.js)
- ✅ 批次结果表格(分页20条/页,排序,搜索)
- ✅ Top3与基准对比表格
- ✅ 导出功能(JSON/CSV一键导出)
- ✅ 响应式设计(927行单文件实现)

**完成报告汇总**:
- [Epic3_Story3.1_完成报告.md](./reports/Epic3_Story3.1_完成报告.md)
- [Epic3_Story3.3_完成报告.md](./reports/Epic3_Story3.3_完成报告.md)
- [Epic3_Story3.4_完成报告.md](./reports/Epic3_Story3.4_完成报告.md)
- [Epic4_Story4.1_完成报告.md](./reports/Epic4_Story4.1_完成报告.md)
- [Epic4_Story4.2_完成报告.md](./reports/Epic4_Story4.2_完成报告.md)
- [Epic4_Story4.3_完成报告.md](./reports/Epic4_Story4.3_完成报告.md)
- [Epic5_Story5.1_完成报告.md](./reports/Epic5_Story5.1_完成报告.md)

**总测试通过率**: 162/162 (100%) ✅

**待验证** (Phase 2尾期):
- ⏳ 40-60实例大规模并行测试
- ⏳ 100万车辆峰值验证
- ⏳ 实时比≥1.0性能验证

---

## 📊 开发进度总览

| Epic | 完成度 | 状态 | 完成日期 |
|------|-------|------|---------|
| Epic 1: MVP并行仿真基础 | 100% | ✅ 已完成 | 2025-10-02 |
| Epic 2.1: 实例状态管理 | 100% | ✅ 已完成 | 2025-10-02 |
| Epic 2.2: 任务调度优化 | 100% | ✅ 已完成 | 2025-10-02 |
| Epic 2.5: 多策略配置 | 100% | ✅ 已完成 | 2025-10-03 |
| Epic 3.1: EdgeData配置 | 100% | ✅ 已完成 | 2025-10-03 |
| Epic 3.2: 瓶颈识别增强 | 0% | ⏸️ Phase 3 | 待定 |
| Epic 3.3: EdgeData解析 | 100% | ✅ 已完成 | 2025-10-03 |
| Epic 3.4: 基准场景管理 | 100% | ✅ 已完成 | 2025-10-03 |
| Epic 4.1: 评分模型实现 | 100% | ✅ 已完成 | 2025-10-03 |
| Epic 4.2: 排名与Top3推荐 | 100% | ✅ 已完成 | 2025-10-03 |
| Epic 4.3: 结果导出 | 100% | ✅ 已完成 | 2025-10-03 |
| Epic 5.1: 结果页面开发 | 100% | ✅ 已完成 | 2025-10-03 |
| Epic 5.2: 监控页面增强 | 0% | ⏳ 待开始 | 待定 |
| Epic 6: 性能与稳定性验证 | 10% | 🔄 进行中 | 待定 |

---

## 📋 Phase 2 开发任务 (按Epic组织)

### Epic 2.5: 多策略配置支持 ✅ **已完成** (100%)

> **重命名说明**: 原Epic 1.5重命名为Epic 2.5，因为当前正在开发Epic 2，此功能是Epic 2的扩展。

**优先级**: P0 (Epic 3-4的前置依赖)
**完成度**: 100% ✅
**完成日期**: 2025-10-03

**完成内容**:
- ✅ Story 2.5.1: 策略生成器实现 (VSL/DHS/zone_restriction/baseline)
- ✅ Story 2.5.2: 批量配置生成器扩展 (独立配置模式)
- ✅ Story 2.5.3: 测试与验证 (21个单元测试 + 集成测试)
- ✅ Story 2.5.4: API与前端集成 (3个API端点)

**问题背景**:

- ❌ 当前所有并行实例使用**完全相同的sumocfg配置**（共享配置模式）
- ❌ 所有实例运行相同的交通场景，无管控策略差异
- ❌ Epic 4的评分系统无法比较不同策略的效果，无法实现Top3优选

**解决方案**: 实现实例级独立配置，支持多种管控策略差异化注入

**技术文档**: [多策略配置技术方案.md](./多策略配置技术方案.md)

#### Story 2.5.1: 策略生成器实现 ✅ **已完成**

**优先级**: P0

- [X] **任务2.5.1.1**: 创建StrategyGenerator类 ✅ (2025-10-02)

  - 文件: `shared/utilities/control_optimization/strategy_generator.py`
  - 功能: 根据策略参数生成SUMO Additional文件（基于rerouter）
  - 支持策略类型:
    - VSL（可变限速）: `<rerouter><setSpeed>` XML生成
    - DHS（动态硬路肩）: `<rerouter><laneAllowed>` XML生成
    - zone_restriction（区域限行）: `<rerouter><vTypeDisallowed>` XML生成
    - baseline（基准场景）: 无附加文件
  - 方法:
    - `generate_control_add_xml()`: 主入口，支持多管控组合
    - `_generate_vsl_rerouter()`: VSL策略XML生成
    - `_generate_dhs_rerouter()`: DHS策略XML生成
    - `_generate_zone_rerouter()`: 区域限行策略XML生成
- [X] **任务2.5.1.2**: 创建EdgeDataAutoGenerator类 ✅ (2025-10-02)

  - 文件: `shared/utilities/control_optimization/edgedata_auto_generator.py`
  - 功能: 根据管控类型自动生成EdgeData配置
  - K=2边选择算法: 基于 `dim.sim_network_connections`表
  - 支持模式:
    - `auto`: 根据策略类型自动选择（VSL用K=2，DHS用主线边）
    - `yirao`: 使用一绕模板（baseline场景）
  - 方法:
    - `generate_from_controls()`: 主入口
    - `_get_k2_edges()`: K=2拓扑扩展（上下游2跳）
    - `_get_zone_boundary_edges()`: 区域边界边选择

#### Story 2.5.2: 批量配置生成器扩展 ✅ **已完成**

**优先级**: P0

- [X] **任务2.5.2.1**: 扩展BatchConfigGenerator支持独立配置模式 ✅ (2025-10-02)

  - 文件: `shared/utilities/control_optimization/batch_config_generator.py`
  - 新增参数:
    - `strategy_configs: List[Dict]` - 策略配置列表
    - `config_mode: str` - "shared" | "independent"
  - 新增方法:
    - `_generate_independent_configs()` - 生成独立配置
    - 按instance_id分组管控
    - 每个实例生成独立sumocfg + control.add.xml + edgedata.add.xml
  - 目录结构:
    ```
    batch_config_{timestamp}/
    ├── instance_0/
    │   ├── simulation.sumocfg
    │   ├── control.add.xml      # 包含所有rerouter
    │   ├── edgedata_auto.add.xml
    │   └── e1/, edgedata/
    ├── instance_1/
    └── ...
    ```
- [X] **任务2.5.2.2**: 扩展sumo_utils支持additional_files参数 ✅ (2025-10-02)

  - 文件: `shared/utilities/sumo_utils.py`
  - 修改函数: `generate_sumocfg_for_simulation()`
  - 新增参数: `simulation_params['additional_files']: List[str]`
  - 功能: 将策略文件路径添加到sumocfg的 `<additional-files>`
  - 路径处理: 自动计算相对路径（相对于simulation_folder）
- [X] **任务2.5.2.3**: 创建CSV解析工具 ✅ (2025-10-02)

  - 文件: `shared/utilities/control_optimization/csv_parser.py`
  - 功能:
    - `parse_control_csv()`: 解析CSV格式策略配置
    - `validate_strategy_configs()`: 验证配置合法性
    - `generate_sample_csv()`: 生成示例CSV文件
  - CSV格式:
    ```csv
    instance_id,control_type,control_id,edges,params
    0,VSL,vsl_1,"edge1,edge2","{""speed"":60,""begin"":25200,""end"":32400}"
    ```

#### Story 2.5.3: 测试与验证 ✅ **已完成** (2025-10-03)

**优先级**: P0

- [X] **任务2.5.3.1**: 单元测试 ✅ (2025-10-03)

  - 测试文件: `tests/unit/test_strategy_generator.py`
  - 测试用例:
    - VSL策略XML格式验证（速度单位转换 km/h → m/s）
    - DHS策略XML格式验证（时间格式转换）
    - zone_restriction策略XML格式验证
    - baseline策略返回None
    - 多管控组合生成验证
  - **测试结果**: 21/21 通过 ✅
- [X] **任务2.5.3.2**: 集成测试 ✅ (2025-10-03)

  - 测试脚本: `test_multi_strategy_config.py` ✅ 已创建
  - 测试场景1: CSV解析验证 ✅
  - 测试场景2: 策略生成器验证（VSL、组合策略）✅
  - 测试场景3: EdgeData自动生成验证 ✅
  - 测试场景4: 批量配置生成验证（需要有效case_id）⏸️ 跳过（需数据库连接）
  - 验证点:
    - CSV解析正确（5个配置） ✅
    - VSL策略XML生成正确 ✅
    - VSL+DHS组合策略生成正确 ✅
    - EdgeData自动生成正确 ✅
- [X] **任务2.5.3.3**: 数据库K=2扩展测试 ⏸️ 可选

  - 验证 `dim.sim_network_connections`表查询正确
  - 验证K=2边集合计算正确
  - 测试一绕EdgeData仿真速度（如太慢改用K=2）
  - **备注**: EdgeData自动生成器已实现K=2逻辑，暂无数据库连接需求

#### Story 2.5.4: API与前端集成 ✅ **已完成** (2025-10-03)

**优先级**: P1

- [X] **任务2.5.4.1**: 新增API端点 ✅ (2025-10-03)

  - 文件: `api/routes/control_optimization_routes.py`
  - 端点1: `POST /api/v1/control_optimization/batches/create_with_strategies` ✅
    - 输入: `strategy_configs: List[Dict]` (JSON格式)
    - 返回: 批次创建结果
    - 行号: 1220-1305
  - 端点2: `POST /api/v1/control_optimization/batches/create_from_csv` ✅ (已存在)
    - 输入: `csv_file: UploadFile`
    - 返回: 批次创建结果
    - 行号: 1308-1312
  - 端点3: `GET /api/v1/control_optimization/download_sample_csv` ✅ (已存在)
    - 返回: 示例CSV文件
  - **测试脚本**: `test_epic2.5_api.py` ✅ (已更新)
- [X] **任务2.5.4.2**: 前端策略配置表单 ⏸️ **Phase 3扩展**

  - 文件: `frontend/control_optimization/strategy_config.html`
  - 功能:
    - 策略类型选择下拉框
    - 动态参数字段显示
    - 策略列表管理（添加/删除）
    - 提交生成配置
  - **备注**: 暂时保留CSV导入方式，前端表单功能留待Phase 3实现

---

### Epic 1.5: 多策略配置支持 ⭐ **前置依赖** (预计2-3天)

> **已重命名为Epic 2.5**，见上方

**优先级**: P0 (Epic 2-4的前置依赖)

**问题背景**:

- ❌ 当前所有并行实例使用**完全相同的sumocfg配置**（共享配置模式）
- ❌ 所有实例运行相同的交通场景，无管控策略差异
- ❌ Epic 4的评分系统无法比较不同策略的效果，无法实现Top3优选

**解决方案**: 实现实例级独立配置，支持多种管控策略差异化注入

**技术文档**: [多策略配置技术方案.md](./多策略配置技术方案.md)

#### Story 1.5.1: 策略生成器实现

**优先级**: P0

- [ ] **任务1.5.1.1**: 创建StrategyGenerator类

  - 文件: `shared/utilities/control_optimization/strategy_generator.py`
  - 功能: 根据策略参数生成SUMO Additional文件
  - 支持策略类型:
    - VSL（可变限速）: `<variableSpeedSign>` XML生成
    - DHS（动态硬路肩）: `<closingRerouter>` XML生成
    - baseline（基准场景）: 无附加文件
  - 方法:
    - `generate_strategy_file()`: 主入口
    - `_generate_vsl_xml()`: VSL策略XML生成
    - `_generate_dhs_xml()`: DHS策略XML生成
- [ ] **任务1.5.1.2**: 单元测试

  - 测试文件: `tests/unit/test_strategy_generator.py`
  - 测试用例:
    - VSL策略XML格式验证（速度单位转换 km/h → m/s）
    - DHS策略XML格式验证（时间格式转换）
    - baseline策略返回None
  - SUMO XML Schema验证（使用 `sumo --check-routes`）

#### Story 1.5.2: 批量配置生成器扩展

**优先级**: P0

- [ ] **任务1.5.2.1**: 扩展BatchConfigGenerator支持独立配置模式

  - 文件: `shared/utilities/control_optimization/batch_config_generator.py`
  - 新增参数:
    - `strategy_configs: List[Dict]` - 策略配置列表
    - `config_mode: str` - "shared" | "independent"
  - 新增方法:
    - `_generate_independent_configs()` - 生成独立配置
    - `_generate_edgedata_config()` - 根据策略类型生成EdgeData配置
  - 目录结构:
    ```
    batch_config_{timestamp}/
    ├── instance_0/
    │   ├── simulation.sumocfg
    │   ├── strategy_vsl.add.xml
    │   ├── edgedata_k2.add.xml
    │   └── e1/, edgedata/
    ├── instance_1/
    └── ...
    ```
- [ ] **任务1.5.2.2**: 扩展sumo_utils支持additional_files参数

  - 文件: `shared/utilities/sumo_utils.py`
  - 修改函数: `generate_sumocfg_for_simulation()`
  - 新增参数: `simulation_params['additional_files']: List[str]`
  - 功能: 将策略文件路径添加到sumocfg的 `<additional-files>`
- [ ] **任务1.5.2.3**: 集成测试

  - 测试场景: 生成3实例批次（VSL_60、VSL_80、baseline）
  - 验证点:
    - 3个instance目录独立创建
    - instance_0有strategy_vsl.add.xml（限速60）
    - instance_1有strategy_vsl.add.xml（限速80）
    - instance_2（baseline）无策略文件
    - 所有sumocfg正确引用策略文件

#### Story 1.5.3: API与前端集成

**优先级**: P1

- [ ] **任务1.5.3.1**: CSV解析逻辑实现

  - 文件: `api/services/strategy_service.py`
  - CSV格式:
    ```csv
    instance_id,strategy_type,edges,speed_limit,time_start,time_end
    0,VSL,"edge_1,edge_2",60,06:00:00,10:00:00
    1,baseline,,,,
    ```
  - 函数: `parse_strategy_csv(csv_file: str) -> List[Dict]`
- [ ] **任务1.5.3.2**: 新增API端点

  - 文件: `api/routes/control_optimization_routes.py`
  - 端点1: `POST /api/v1/control_optimization/batches/create_with_strategies`
    - 输入: `strategy_configs: List[Dict]` (JSON格式)
    - 返回: 批次创建结果
  - 端点2: `POST /api/v1/control_optimization/batches/create_from_csv`
    - 输入: `csv_file: UploadFile`
    - 返回: 批次创建结果
- [ ] **任务1.5.3.3**: 前端策略配置表单（Phase 2扩展）

  - 文件: `frontend/control_optimization/strategy_config.html`
  - 功能:
    - 策略类型选择下拉框
    - 动态参数字段显示
    - 策略列表管理（添加/删除）
    - 提交生成配置
  - **暂时保留CSV导入方式为主**

#### Story 1.5.4: 策略类型扩展（可选）

**优先级**: P2

- [ ] **任务1.5.4.1**: 实现signal_optimization策略生成器

  - XML类型: `<tlLogic>` (交通信号配时)
  - 参数: 周期时长、绿信比、相位偏移
- [ ] **任务1.5.4.2**: 实现area_restriction策略生成器

  - XML类型: `<closingRerouter>` + 车辆类型过滤
  - 参数: 限行区域、限行车型、时间范围

---

### Epic 2: 并行实例管理增强 (预计3-4天)

#### Story 2.1: 实例状态管理与实时监测 ⭐ **核心更新**

**优先级**: P0 (阻塞后续开发)

**设计确认**:

- ✅ 监测间隔：30秒（默认，可配置）
- ✅ 数据存储：元数据文件为主，数据库可选
- ✅ 峰值监测：从summary.xml实时读取

- [X] **任务2.1.1**: Summary实时监测器实现 ✅ (2025-10-02)

  - 类: `SummaryRealTimeMonitor`（文件尾部追踪）
  - 监测间隔: 30秒（可通过环境变量 `MONITORING_INTERVAL`配置）
  - 峰值提取: 读取 `running`属性，自动识别峰值
  - 文件: `shared/utilities/control_optimization/summary_monitor.py`
  - 参考: [SUMO_Summary实时监测技术方案.md](./SUMO_Summary实时监测技术方案.md)
- [X] **任务2.1.2**: Worker进程集成Summary监测 ✅ (2025-10-02)

  - 修改: `shared/utilities/control_optimization/parallel_simulator.py`
  - 集成点: `_run_simulation_worker()` 函数
  - 更新: `instance_status.json`（包含峰值数据）
  - 间隔: 30秒更新一次
  - 测试脚本: `test_summary_monitoring.py`
- [X] **任务2.1.3**: 批次状态文件实时更新 ✅ (2025-10-02)

  - 类: `BatchStatusMonitor`（批次状态监测器）
  - 文件: `shared/utilities/control_optimization/batch_status_monitor.py`
  - 输出: `batch_status.json`（批次级状态文件）
  - 更新频率: 30秒
  - 汇总内容: 进度、车辆统计、交通指标、安全指标、错误列表
  - 集成: `parallel_simulator.py`的 `run()`方法（3处集成点）
  - 测试脚本: `test_batch_status_monitor.py`
  - 参考: [任务2.1.3_实现总结.md](./任务2.1.3_实现总结.md)
- [X] **任务2.1.4**: 批次/实例状态查询API ✅ (2025-10-02)

  - API 1: `GET /api/v1/control_optimization/batches/{batch_id}/status` ✅
  - API 2: `GET /api/v1/control_optimization/batches/{batch_id}/instances` ✅
  - API 3: `GET /api/v1/control_optimization/batches/{batch_id}/instances/{instance_id}/status` ✅
  - 返回: 包含峰值车辆数、实时比、交通指标
  - 文件: `api/routes/control_optimization_routes.py`
  - 测试脚本: `test_batch_status_api.py` ✅ 3/3测试通过
- [X] **任务2.1.5**: 失败任务诊断 ✅ (2025-10-02)

  - 错误分类器: `ErrorClassifier` (7种错误类型,自动建议) ✅
  - 诊断报告生成器: `DiagnosticReportGenerator` (JSON/Markdown) ✅
  - API端点:
    - `GET /batches/{batch_id}/diagnostics` (批次诊断) ✅
    - `GET /batches/{batch_id}/instances/{instance_id}/diagnostics` (实例诊断) ✅
    - `POST /batches/{batch_id}/diagnostics/save` (保存报告) ✅
  - 文件:
    - `shared/utilities/control_optimization/error_classifier.py` ✅
    - `shared/utilities/control_optimization/diagnostic_report_generator.py` ✅
    - `api/routes/control_optimization_routes.py` (新增3个端点) ✅
  - 测试: `test_diagnostics_simple.py` ✅

**Story 2.1 完成度**: 5/5任务 (100%) ✅

- ✅ 任务2.1.1-2.1.5: 全部完成
- ✅完成报告: [Epic2_Story2.1_完成报告.md](./Epic2_Story2.1_完成报告.md) (2025-10-02)

#### Story 2.2: 任务调度优化 ✅ **已完成**

**优先级**: P1
**完成日期**: 2025-10-02

- [X] **任务2.2.1**: FIFO任务队列实现 ✅

  - 使用Queue实现FIFO队列
  - 支持动态添加任务 (add_task/add_tasks_batch)
  - 文件: `shared/utilities/control_optimization/task_scheduler.py` ✅
- [X] **任务2.2.2**: 超时检测机制 ✅

  - 可配置超时阈值（默认2小时,7200秒）
  - 后台线程定时检查running任务（默认30秒）
  - 超时自动标记为timeout并终止进程
- [X] **任务2.2.3**: 孤儿任务清理 ✅

  - cleanup_orphan_tasks(): 检测pending/running状态遗留任务
  - cancel_orphan_tasks(): 自动标记为cancelled

**Story 2.2 完成度**: 3/3任务 (100%) ✅

**核心功能**:

- TaskScheduler类（调度器核心）
- FIFO队列管理 + 并发控制
- 超时监控（独立线程）
- 孤儿任务检测和清理
- 状态持久化
- 回调机制

**测试验证**:

- `test_task_scheduler.py` ✅ 5/5测试通过

---

### Epic 3: EdgeData采集与指标计算 (预计4-5天)

#### Story 3.1: EdgeData输出配置 ⭐ **架构优化** ✅ **已完成**

**完成日期**: 2025-10-03
**完成度**: 100%
**优先级**: P0 (评分系统依赖)

**关联文档**: [控制策略边选择方法论_v2.0.md](./design/控制策略边选择方法论_v2.0.md)

**设计原则**:

- ❌ 不采用全网评价（会严重降低仿真速度）
- ✅ 采用分层模板架构（**节点单元 → 设施单元 → 路网单元**）
- ✅ 支持占位符替换机制（动态边集合）
- ✅ 为管控评价提供按层级选择EdgeData范围的能力
- ✅ 手动指定边集合时，使用动态XML拼接

- [X] **任务3.1.1**: 建立EdgeData分层模板目录结构 ✅

  - 创建模板层级目录:
    ```
    templates/edge_add/
    ├── node_level/                      # 节点单元层级（交叉口）
    │   └── edgeData_node_template.add.xml
    ├── facility_level/                  # 设施单元层级（走廊/通道）
    │   ├── edgeData_facility_template.add.xml
    │   └── edgeData_template.add.xml    # 原MVP模板（备用）
    └── network_level/                   # 路网单元层级（区域路网）
        └── edgeData_yirao.add.xml      # 一绕（已实现）
    ```
  - 迁移现有模板:
    - `edgeData_1rao.add.xml` → `network_level/edgeData_yirao.add.xml` ✅
    - `edgeData_template.add.xml` → `facility_level/edgeData_template.add.xml` ✅
  - 文档: `templates/edge_add/README.md` ✅
- [X] **任务3.1.2**: 实现EdgeData占位符替换机制 ✅

  - 功能位置: `shared/utilities/sumo_utils.py:188-201` (已实现)
  - 替换逻辑:
    ```python
    # Epic 3.1: 占位符替换机制
    if '{{EDGES_SPACE_SEPARATED}}' in modified_content:
        edges_list = simulation_params.get('edgedata_edges', [])
        edges_str = ' '.join(edges_list)
        modified_content = modified_content.replace(
            '{{EDGES_SPACE_SEPARATED}}', edges_str
        )
        print(f"EdgeData占位符替换: {len(edges_list)}条边")
    ```
  - 兼容旧逻辑: 保留 `edges` 属性删除逻辑（第200-201行）
- [X] **任务3.1.3**: 扩展simulation_params参数支持 ✅

  - 新增参数:
    - `edgedata_template`: str - 模板路径（相对或绝对路径）✅
    - `edgedata_edges`: list[str] - 动态边集合（用于占位符替换）✅
    - `edgedata_level`: str - 层级标识 ("node"|"facility"|"network") ✅
  - 文档更新: `docs/api_docs/新架构API指南.md` v2.1.0 ✅
- [X] **任务3.1.4**: 边选择器实现（EdgeSelector） ✅

  - 文件: `shared/utilities/control_optimization/edge_selector.py` ✅
  - 实现方法:
    - `generate_k2_edges()`: K=2拓展边（起点 + 1跳 + 2跳）✅
    - `get_regional_edges()`: 路网单元边读取（一绕/二绕/三绕）✅
    - `generate_edgedata_xml()`: 动态XML拼接（手动指定边集合）✅
    - `select_edges_by_strategy()`: 策略类型自动选择边集合 ✅
  - 数据库支持: 基于 `dim.sim_network_connections` 表 ✅
  - **技术参考**: [控制策略边选择方法论_v2.0.md](./design/控制策略边选择方法论_v2.0.md) 第159-441行（各策略边选择方法）
- [X] **任务3.1.5**: 集成到batch_config生成流程 ✅

  - 修改: `shared/utilities/control_optimization/batch_config_generator.py:224-237` ✅
  - 导入EdgeSelector: `from shared.utilities.control_optimization.edge_selector import EdgeSelector` ✅
  - 数据库连接传递给EdgeSelector ✅
- [X] **任务3.1.6**: 验证EdgeData输出文件生成 ✅

  - 测试脚本: `test_epic3.1_edgedata.py` ✅
  - 测试场景1: 节点单元 - 交叉口信号优化（4条边）✅ 通过
  - 测试场景2: 设施单元 - K=2动态边集合（45条边）✅ 通过
  - 测试场景3: 路网单元 - 一绕固定边集合（343条边）✅ 通过
  - 测试场景4: 占位符替换验证 ✅ 通过
  - 测试场景5: 模板目录结构验证 ✅ 通过
  - 总计: **5/5 测试场景通过** ✅

#### Story 3.2: 瓶颈识别与边选择增强 ⭐ **Phase 3扩展** (预计2-3天)

**优先级**: P2 (Phase 3扩展功能)
**完成度**: 0%
**技术参考**: [控制策略边选择方法论_v2.0.md](./design/控制策略边选择方法论_v2.0.md)

**功能说明**: 基于路网结构节点的瓶颈识别与智能边选择,提升策略配置的针对性和效果

- [ ] **任务3.2.1**: 瓶颈识别器实现

  - 文件: `shared/utilities/control_optimization/bottleneck_detector.py`
  - 功能: 基于四类结构节点识别瓶颈
    - 查询 `dim.multiscale_node_units` 表
    - 支持瓶颈类型: diverging/merging/lane_decrease/lane_increase
    - 激活条件筛选: capacity_util≥0.8, delay_prob≥0.6, health_score≤0.7
  - 方法:
    - `detect_bottlenecks()`: 综合瓶颈识别(SQL查询)
    - `get_bottleneck_candidates()`: 候选瓶颈查询
    - `filter_by_activation()`: 激活条件筛选
  - SQL参考: 方法论文档第700-755行
  - 预计时间: 1天
- [ ] **任务3.2.2**: 边选择策略扩展

  - 文件: `shared/utilities/control_optimization/edge_selector.py`(扩展)
  - 新增方法:
    - `select_edges_for_vsl()`: VSL策略边选择(K=2拓展,方法论第161-223行)
    - `select_edges_for_dhs()`: DHS策略边选择(走廊路段边集合,方法论第256-351行)
    - `select_edges_for_ramp_metering()`: 匝道控制边选择(匝道+K=1拓展,方法论第354-441行)
    - `select_edges_for_zone_restriction()`: 区域限行边选择(入口边+1-hop,方法论第505-595行)
  - 边过滤规则: 主线边(highway='motorway')优先
  - 预计时间: 1-2天
- [ ] **任务3.2.3**: 瓶颈-策略-边选择集成

  - 文件: `shared/utilities/control_optimization/strategy_generator.py`(扩展)
  - 集成流程:
    ```
    瓶颈识别 → 策略类型推荐 → 边选择 → EdgeData配置 → SUMO策略文件生成
    ```
  - 新增方法:
    - `generate_strategy_from_bottleneck()`: 基于瓶颈节点生成策略
    - `recommend_strategy_type()`: 根据瓶颈类型推荐策略(合流→VSL,走廊拥堵→DHS)
  - 测试场景: 一绕永宁互通VSL策略生成(方法论第887-929行)
  - 预计时间: 1天

#### Story 3.3: EdgeData解析与指标提取 ⭐ **本周重点** (预计1-2天)

**优先级**: P0 (评分系统依赖)
**完成度**: 0%
**预计完成**: 2025-10-06

- [ ] **任务3.3.1**: EdgeData XML解析器 (0.5天)

  - 文件: `shared/data_processors/edgedata_parser.py`
  - 功能:
    - 解析 `edgedata/output.xml`
    - 提取字段: edge_id, speed, density, occupancy, flow
    - 支持流式解析（避免内存溢出）
  - 输出: 结构化数据（DataFrame或List[Dict]）
  - 预计时间: 0.5天

- [ ] **任务3.3.2**: 关键指标计算 (1天)

  - 文件: `shared/analysis_tools/edgedata_analyzer.py`
  - 指标列表:
    - 平均速度（全网/主线）：`avg_speed_all`, `avg_speed_mainline`
    - 总延误时间：`total_delay = Σ((speed_limit - actual_speed) * length / speed_limit)`
    - 通行能力增幅：`capacity_gain = (baseline_capacity - control_capacity) / baseline_capacity`
    - 拥堵程度：基于速度<40km/h的边占比
  - 方法论支持: 为瓶颈识别提供数据基础
  - 预计时间: 1天

- [ ] **任务3.3.3**: 指标入库 (0.5天)

  - 文件: `api/services/metrics_service.py`
  - 表设计: `control_optimization.task_metrics`
    ```sql
    CREATE TABLE control_optimization.task_metrics (
        id UUID PRIMARY KEY,
        batch_id VARCHAR(64),
        task_id VARCHAR(64),
        avg_speed_all DECIMAL(10,2),
        avg_speed_mainline DECIMAL(10,2),
        total_delay DECIMAL(12,2),
        capacity_gain_ratio DECIMAL(10,4),
        congestion_ratio DECIMAL(10,4),
        created_at TIMESTAMP
    );
    ```
  - 批量插入优化（使用executemany）
  - 预计时间: 0.5天

#### Story 3.4: 基准场景管理

**优先级**: P1

- [ ] **任务3.4.1**: 基准场景定义

  - 无管控策略的仿真作为基准
  - 存储基准指标: baseline_speed, baseline_capacity
  - 表设计: `control_optimization.baseline_scenarios`
- [ ] **任务3.4.2**: 基准场景API

  - `POST /api/v1/control_optimization/baselines` - 创建基准
  - `GET /api/v1/control_optimization/baselines/{case_id}` - 获取基准
  - 文件: `api/routes/control_optimization_routes.py`

---

### Epic 4: 评分与排名系统 (预计3-4天)

#### Story 4.1: 评分模型实现

**优先级**: P0

- [ ] **任务4.1.1**: 指标标准化

  - Min-Max归一化: `(x - min) / (max - min)`
  - 延误取倒数（越低越好）
  - 通行能力增幅正向（越高越好）
  - 文件: `shared/utilities/control_optimization/metric_normalizer.py`
- [ ] **任务4.1.2**: 加权评分计算

  - 默认权重: delay=0.5, capacity_gain=0.5
  - 公式: `score = w1*norm_delay + w2*norm_capacity`
  - 支持自定义权重（Phase 2）
  - 文件: `shared/utilities/control_optimization/scoring_engine.py`
- [ ] **任务4.1.3**: 缺失值处理

  - 策略: 批次均值填充 / 剔除异常任务
  - 记录处理日志
  - 文件: `shared/utilities/control_optimization/data_cleaner.py`

#### Story 4.2: 排名与Top3推荐 ✅ **已完成**

**完成日期**: 2025-10-03
**完成度**: 100%
**优先级**: P0

**完成报告**: [Epic4_Story4.2_完成报告.md](./reports/Epic4_Story4.2_完成报告.md)

**Story 4.2 完成度**: 3/3任务 (100%) ✅

**核心功能**:

- 批次排名算法（按score降序，处理并列，稳定排序）
- Top3提取逻辑（前3个rank，包含所有并列）
- Top3推荐生成（自动推荐理由，emoji标识）
- 排名统计（并列分析、分数范围）
- 基准对比（改善幅度计算）
- 4个REST API端点

**测试验证**:

- `test_ranker.py` ✅ 24/24测试通过

- [X] **任务4.2.1**: 批次排名算法 ✅

  - 按score降序排序 ✅
  - 处理并列情况（分数相同，浮点数精度阈值1e-6）✅
  - 稳定排序（task_id升序）✅
  - 并列标记（is_tied, tied_count）✅
  - 文件: `shared/utilities/control_optimization/ranker.py` (449行)
- [X] **任务4.2.2**: Top3提取逻辑 ✅

  - 前3个不同rank ✅
  - 并列全部纳入（可能>3条）✅
  - 标注并列标识 ✅
  - 推荐理由生成（🥇🥈🥉 + 指标分析）✅
  - 文件: `shared/utilities/control_optimization/ranker.py`
- [X] **任务4.2.3**: 排名结果API ✅

  - `GET /api/v1/control_optimization/batches/{case_id}/ranking` ✅
  - `GET /api/v1/control_optimization/batches/{case_id}/top3` ✅
  - `GET /api/v1/control_optimization/batches/{case_id}/top3/comparison` ✅
  - `POST /api/v1/control_optimization/batches/ranking` ✅
  - 响应格式: rank, task_id, score, metrics, is_tied, recommendation_reason ✅
  - 文件: `api/routes/control_optimization_routes.py` (+325行)
- [X] **任务4.2.4**: RankingService业务服务 ✅

  - rank_batch_by_case_id() ✅
  - rank_batch_by_simulation_ids() ✅
  - get_top3_by_case_id() ✅
  - compare_with_baseline() ✅
  - 文件: `api/services/ranking_service.py` (389行)

#### Story 4.3: 结果导出 ✅ **已完成**

**完成日期**: 2025-10-03
**完成度**: 100%
**优先级**: P1

**完成报告**: [Epic4_Story4.3_完成报告.md](./reports/Epic4_Story4.3_完成报告.md)

**Story 4.3 完成度**: 3/3任务 (100%) ✅

**核心功能**:

- JSON导出（完整结果、Top3、对比，带metadata）
- CSV导出（任务表格、Top3表格、对比表格，Excel兼容）
- 文件名生成（时间戳、类型标识）
- 统一导出接口（支持多种类型和格式组合）
- 4个REST API端点（1个通用 + 3个快捷）

**测试验证**:

- `test_export_service.py` ✅ 4/4测试通过

- [X] **任务4.3.1**: JSON导出 ✅

  - 完整批次结果（所有任务+评分+排名）✅
  - Top3推荐单独导出 ✅
  - Top3与基准对比 ✅
  - Metadata自描述（导出类型、格式、时间戳）✅
  - 文件: `api/services/export_service.py` (586行)
- [X] **任务4.3.2**: CSV导出 ✅

  - 任务级指标表格（动态列生成）✅
  - Top3推荐表格（包含推荐理由）✅
  - Top3对比表格（改善幅度）✅
  - 支持Excel打开（UTF-8编码，数值格式化）✅
  - 关键指标优先排序 ✅
- [X] **任务4.3.3**: 导出API端点 ✅

  - `GET /api/v1/control_optimization/batches/{case_id}/export?format=json|csv` ✅
  - `GET /api/v1/control_optimization/batches/{case_id}/export/full` ✅
  - `GET /api/v1/control_optimization/batches/{case_id}/export/top3` ✅
  - `GET /api/v1/control_optimization/batches/{case_id}/export/comparison` ✅
  - Content-Type设置正确（application/json | text/csv）✅
  - 文件名包含时间戳 ✅
  - 文件: `api/routes/control_optimization_routes.py` (+182行)

---

### Epic 5: 前端界面增强 (预计4-5天)

#### Story 5.1: 结果页面开发 ✅ **已完成**

**完成日期**: 2025-10-03
**完成度**: 100%
**优先级**: P0

**完成报告**: [Epic5_Story5.1_完成报告.md](./reports/Epic5_Story5.1_完成报告.md)

**Story 5.1 完成度**: 3/3任务 (100%) ✅

**核心功能**:

- Top3推荐卡片（排名徽章、评分、指标、推荐理由）
- 指标对比图表（柱状图 + 雷达图，Chart.js）
- 批次结果表格（分页20条/页、排序、搜索）
- Top3与基准对比表格（改善幅度）
- 导出功能（JSON/CSV一键导出）
- 响应式设计（PC + 移动端）
- 3个标签页（概览、对比分析、详细数据）

**页面特性**:

- 单文件实现（927行：HTML + CSS + JavaScript）
- 无外部依赖（除Chart.js CDN）
- 流畅交互动画
- 完整错误处理

- [X] **任务5.1.1**: 批次结果表格 ✅

  - 列: rank, task_id, score, delay, capacity_gain, avg_speed, is_tied ✅
  - 分页支持（20条/页，上一页/下一页）✅
  - 可按指标排序（点击列标题，升序/降序切换）✅
  - 实时搜索（任务ID过滤）✅
  - 文件: `frontend/control_optimization/results.html` (927行)
- [X] **任务5.1.2**: Top3推荐卡片 ✅

  - 突出显示前3名（金/银/铜色系）✅
  - 排名徽章（圆形，右上角）✅
  - 展示关键指标（延误、容量增益、速度）✅
  - 并列标识（橙色徽章）✅
  - 推荐理由（API获取，卡片底部）✅
  - hover效果（上浮+阴影）✅
- [X] **任务5.1.3**: 指标对比图表 ✅

  - 柱状图：Top3评分对比（金银铜配色）✅
  - 雷达图：5维度指标对比（评分、速度、延误、容量、拥堵）✅
  - 使用Chart.js 4.4.0 ✅
  - 响应式图表 ✅
- [X] **任务5.1.4**: API集成 ✅

  - GET /batches/{case_id}/ranking ✅
  - GET /batches/{case_id}/top3/comparison ✅
  - GET /batches/{case_id}/export ✅
- [X] **任务5.1.5**: 导出功能 ✅

  - JSON导出按钮 ✅
  - CSV导出按钮 ✅
  - 文件自动下载 ✅

#### Story 5.2: 监控页面增强

**优先级**: P1

- [ ] **任务5.2.1**: 实时状态刷新

  - 30秒自动刷新（轮询）
  - 显示running/completed/failed数量
  - 进度条展示
  - 文件: `frontend/control_optimization/monitor.html`
- [ ] **任务5.2.2**: 任务详情弹窗

  - 点击任务查看详情
  - 显示策略参数、日志摘要、错误信息
  - 支持手动重试（Phase 2）
- [ ] **任务5.2.3**: 峰值曲线优化

  - 多实例叠加显示
  - 图例交互（显示/隐藏）
  - 时间窗选择（Phase 2）

#### Story 5.3: 启动页面优化

**优先级**: P2

- [ ] **任务5.3.1**: CSV导入增强

  - 文件验证（格式/字段）
  - 预览前5行
  - 错误高亮显示
- [ ] **任务5.3.2**: 参数表单UI（替代CSV）

  - 策略类型选择（VSL/DHS/DTG）
  - 动态字段显示
  - 批量复制功能
  - **Phase 2扩展**

---

### Epic 6: 性能与稳定性验证 (预计2-3天)

#### Story 6.1: 大规模并行测试

**优先级**: P0

- [ ] **任务6.1.1**: 40实例并行测试

  - 验证稳定完成率≥95%
  - 记录总耗时、峰值车辆数
  - 监控CPU/内存使用
- [ ] **任务6.1.2**: 60实例并行测试

  - 验证系统极限
  - 识别性能瓶颈
  - 产出优化建议
- [ ] **任务6.1.3**: 100万车辆规模测试

  - 验证峰值车辆数>100万
  - 验证实时比≥1.0
  - 记录性能指标

#### Story 6.2: 长稳运行测试

**优先级**: P1

- [ ] **任务6.2.1**: 2小时连续运行

  - 多批次连续提交
  - 验证无内存泄漏
  - 验证无进程残留
- [ ] **任务6.2.2**: 12小时长稳测试（Phase 2）

  - 自动资源监控
  - 内存增长≤1MB/hour
  - 产出详细报告

---

## 🚧 当前优先级任务（本周 2025-10-03 ~ 2025-10-10）

### 📍 当前进度

- ✅ **Epic 2.5**: 多策略配置支持 - 已完成
- ✅ **Epic 3.1**: EdgeData输出配置 - 已完成
- ✅ **Epic 3.3**: EdgeData解析与指标提取 - 已完成 (2025-10-03)
- ✅ **Epic 3.4**: 基准场景管理 - 已完成 (2025-10-03)
- ✅ **Epic 4.1**: 评分模型实现 - 已完成 (2025-10-03)
- ✅ **Epic 4.2**: 排名与Top3推荐 - 已完成 (2025-10-03)
- ✅ **Epic 4.3**: 结果导出 - 已完成 (2025-10-03)
- ✅ **Epic 5.1**: 结果页面开发 - 已完成 (2025-10-03)

### 高优先级 (P0/P1) - 建议后续任务

1. **Epic 5.2: 监控页面增强** (1-2天) ⭐ **建议下一任务**

   - [ ] 任务5.2.1: 实时状态刷新
   - [ ] 任务5.2.2: 任务详情弹窗
   - [ ] 任务5.2.3: 峰值曲线优化
   - **目标**: 2025-10-05完成

2. **Epic 5.1: 结果页面开发** (2-3天)

   - [ ] 任务5.1.1: 批次结果表格
   - [ ] 任务5.1.2: Top3推荐卡片
   - [ ] 任务5.1.3: 指标对比图表
   - **目标**: 2025-10-06完成

### 已完成Epic总结 (2025-10-03)

**Epic 3.3**: EdgeData解析与指标提取
- EdgeDataParser: 流式解析，时间/边过滤
- EdgeDataAnalyzer: 5大指标计算
- MetricsService: 指标入库
- 测试: 70/70通过 ✅

**Epic 3.4**: 基准场景管理
- 数据库表: baseline_scenarios
- BaselineScenarioService: 完整CRUD
- 7个API端点
- 测试: 25/25通过 ✅

**Epic 4.1**: 评分模型实现
- MetricNormalizer: Min-Max标准化
- ScoringEngine: 加权评分
- DataCleaner: 数据清洗
- 测试: 39/39通过 ✅

**Epic 4.2**: 排名与Top3推荐
- Ranker: 批次排名算法
- RankingService: 业务编排
- 4个API端点（排名、Top3、对比）
- 测试: 24/24通过 ✅

**Epic 4.3**: 结果导出
- ExportService: JSON/CSV导出
- 3种导出类型（完整、Top3、对比）
- 4个API端点（1个通用 + 3个快捷）
- Excel兼容CSV（UTF-8，数值格式化）
- 测试: 4/4通过 ✅

**总计**: 162个测试全部通过，5个Epic完整交付
   - [ ] 任务3.4.2: 基准场景API实现
   - **目标**: 2025-10-07完成

### 中优先级 (P1) - 本周尽量完成

3. **Epic 4.1: 评分模型实现** (1-2天) - **依赖Epic 3.3完成**

   - [ ] 任务4.1.1: 指标标准化（Min-Max归一化）
   - [ ] 任务4.1.2: 加权评分计算（默认权重0.5/0.5）
   - [ ] 任务4.1.3: 缺失值处理
   - **目标**: 2025-10-09完成

4. **Epic 4.2: Top3推荐** (1天)

   - [ ] 任务4.2.1: 排名算法
   - [ ] 任务4.2.2: Top3提取逻辑
   - [ ] 任务4.2.3: 排名结果API
   - **目标**: 2025-10-10完成

### 低优先级 (P2) - 下周完成

5. **Epic 4.3: 结果导出** (1天)

   - [ ] JSON导出
   - [ ] CSV导出
   - [ ] 导出API端点

6. **Epic 5: 前端界面增强** (2-3天)

   - [ ] 结果页面开发（Story 5.1）
   - [ ] 监控页面增强（Story 5.2）

---

## 🔮 Phase 3 扩展功能 (Week 3-4, 2025-10-17+)

### Story 3.2: 瓶颈识别与边选择增强 (2-3天)

**优先级**: P2 (Phase 3扩展功能)
**技术参考**: [控制策略边选择方法论_v2.0.md](./design/控制策略边选择方法论_v2.0.md)

基于路网结构节点的瓶颈识别与智能边选择，提升策略配置的针对性和效果。

- [ ] **任务3.2.1**: 瓶颈识别器实现 (1天)

  - 文件: `shared/utilities/control_optimization/bottleneck_detector.py`
  - 功能: 基于四类结构节点识别瓶颈
    - 查询 `dim.multiscale_node_units` 表
    - 支持瓶颈类型: diverging/merging/lane_decrease/lane_increase
    - 激活条件筛选: capacity_util≥0.8, delay_prob≥0.6, health_score≤0.7
  - SQL参考: 方法论文档第700-755行

- [ ] **任务3.2.2**: 边选择策略扩展 (1-2天)

  - 文件: `shared/utilities/control_optimization/edge_selector.py` (扩展)
  - 新增方法:
    - `select_edges_for_vsl()`: VSL策略边选择（K=2拓展，方法论第161-223行）
    - `select_edges_for_dhs()`: DHS策略边选择（走廊路段边集合，方法论第256-351行）
    - `select_edges_for_ramp_metering()`: 匝道控制边选择（匝道+K=1拓展，方法论第354-441行）
    - `select_edges_for_zone_restriction()`: 区域限行边选择（入口边+1-hop，方法论第505-595行）

- [ ] **任务3.2.3**: 瓶颈-策略-边选择集成 (1天)

  - 文件: `shared/utilities/control_optimization/strategy_generator.py` (扩展)
  - 集成流程: 瓶颈识别 → 策略类型推荐 → 边选择 → EdgeData配置 → SUMO策略文件生成
  - 测试场景: 一绕永宁互通VSL策略生成（方法论第887-929行）

**新增API端点**:
- `GET /api/v1/control_optimization/bottlenecks/detect` - 瓶颈识别
- `POST /api/v1/control_optimization/strategies/generate_from_bottleneck` - 基于瓶颈生成策略
- `POST /api/v1/control_optimization/batches/create_from_bottlenecks` - 基于瓶颈列表创建批次

**详细方案**: [边选择方法论融入方案.md](./planning/边选择方法论融入方案.md)

---

## 🔮 Phase 2 后续功能 (Week 4+)

### 扩展功能列表

1. **策略配置UI表单** (2-3天)

   - 替代CSV导入
   - 动态表单字段（基于Epic 1.5的CSV导入功能扩展）
   - 实时验证与默认值
2. **可配置评分权重** (1-2天)

   - 权重配置界面
   - 自定义评分模型
   - 权重验证（总和=1.0）
3. **多维度监控曲线** (2-3天)

   - CPU/内存使用曲线
   - 实时比曲线
   - 多实例叠加显示
4. **详细分析报告** (2-3天)

   - PDF/Markdown报告生成
   - 包含图表和统计数据
   - 可下载分享
5. **预案模板库** (3-4天)

   - 模板CRUD API
   - 模板分类与标签
   - 快速应用模板
6. **WebSocket实时推送** (2-3天)

   - 任务状态实时推送
   - 进度实时更新
   - 前端自动刷新
7. **完整错误处理** (2-3天)

   - 自动重试机制（指数退避）
   - 断路器模式
   - 优雅降级

---

## 📊 技术架构演进

### 当前架构 (MVP Phase 1)

```
前端 (mvp_parallel_simulation.html)
  ↓
API Routes (control_optimization_routes.py)
  ├─→ BatchConfigGenerator (批量配置生成)
  └─→ ParallelSimulator (并行仿真 - subprocess直接运行)
       ├─→ 10个独立instance目录
       ├─→ 独立sumocfg + TAZ + e1/ + edgedata/
       └─→ SimulationTimer (时长统计)
```

### 目标架构 (Phase 2)

```
前端 (3个页面: 启动/监控/结果)
  ↓
API Layer
  ├─→ TaskManager (任务状态管理)
  ├─→ BatchManager (批次管理)
  ├─→ MetricsService (指标计算)
  ├─→ ScoringEngine (评分排名)
  └─→ ExportService (结果导出)
       ↓
Shared Layer
  ├─→ EdgeDataAnalyzer (EdgeData解析)
  ├─→ RankingEngine (排名算法)
  ├─→ RecommendationEngine (Top3推荐)
  └─→ ParallelSimulator (仿真执行)
       ↓
Database
  ├─→ task_status (任务状态)
  ├─→ task_metrics (任务指标)
  ├─→ baseline_scenarios (基准场景)
  └─→ batch_summary (批次汇总)
```

---

## 🎯 本周工作计划 (2025-10-03 ~ 2025-10-10)

### ~~Day 1-2 (周四-周五 10-03/10-04)~~: Epic 2.5 + Epic 3.1 ✅ **已完成**

- [X] Epic 2.5测试完成（21/21单元测试通过）
- [X] Epic 3.1完整实现（EdgeSelector + 三层模板）
- [X] 5/5测试场景验证通过

### Day 3-4 (周六-周日 10-05/10-06): Epic 3.3 EdgeData解析与指标计算

- [ ] **Day 3上午**: EdgeData XML解析器实现
- [ ] **Day 3下午**: 解析器单元测试
- [ ] **Day 4上午**: 关键指标计算逻辑
- [ ] **Day 4下午**: 指标计算测试 + 入库实现

### Day 5 (周一 10-07): Epic 3.4 基准场景管理

- [ ] **上午**: 基准场景表设计 + 数据模型
- [ ] **下午**: 基准场景API实现

### Day 6-7 (周二-周三 10-08/10-09): Epic 4.1 评分模型

- [ ] **Day 6**: 指标标准化 + 加权评分计算
- [ ] **Day 7**: Top3推荐算法 + API端点

---

## 🎯 ~~原计划~~ 本周工作计划 (2025-10-02 ~ 2025-10-08)

### ~~原计划工作内容~~ (已完成调整)

**已完成**:
- ✅ Day 1-2: Epic 2.5多策略配置支持（21/21测试通过）
- ✅ Day 1-2: Epic 3.1 EdgeData输出配置（5/5测试通过）

**调整后重点**:
- 🔄 Day 3-4: Epic 3.3 EdgeData解析与指标计算（当前进行中）
- ⏳ Day 5: Epic 3.4 基准场景管理
- ⏳ Day 6-7: Epic 4.1 评分模型实现

---

## 📝 开发规范

### 代码组织

- **API层**: `api/services/` - 业务逻辑服务
- **共享层**: `shared/analysis_tools/` - 分析引擎
- **数据访问**: `shared/data_access/` - 数据库操作
- **工具函数**: `shared/utilities/control_optimization/` - 通用工具

### 文档要求

- 每个Story完成后更新对应文档
- API变更更新 `docs/api_docs/新架构API指南.md`
- 重要决策记录在 `docs/development/control_optimization/`

### 测试要求

- 单元测试: `pytest tests/unit/`
- 集成测试: `pytest tests/integration/`
- 手动测试: 记录在测试报告中

---

## 🔗 相关文档

### 规划与设计文档

- **下一阶段开发建议**: [下一阶段开发建议_20251003.md](./planning/下一阶段开发建议_20251003.md) v2.0
- **边选择方法论**: [控制策略边选择方法论_v2.0.md](./design/控制策略边选择方法论_v2.0.md)
- **方法论融入方案**: [边选择方法论融入方案.md](./planning/边选择方法论融入方案.md)
- **架构设计**: [管控方案优化子系统架构设计方案.md](./planning/管控方案优化子系统架构设计方案.md)
- **PRD文档**: [管控方案优化子系统PRD文档.md](./planning/管控方案优化子系统PRD文档.md)

### 技术方案文档

- **多策略配置**: [多策略配置技术方案.md](./design/多策略配置技术方案.md)
- **EdgeData分层配置**: [EdgeData分层配置技术方案.md](./design/EdgeData分层配置技术方案.md)

### 完成报告

- **Epic 3.1完成报告**: [Epic3_Story3.1_完成报告.md](./reports/Epic3_Story3.1_完成报告.md)
- **Epic 2 Story 2.1完成报告**: [Epic2_Story2.1_完成报告.md](./reports/Epic2_Story2.1_完成报告.md)

### 测试文档

- **管控方案优化测试报告**: [管控方案优化子模块测试报告.md](../../testing/管控方案优化子模块测试报告.md)
- **管控方案优化测试总结**: [管控方案优化测试总结-2025-10-01.md](../../testing/管控方案优化测试总结-2025-10-01.md)

### 系统文档

- **API文档**: [新架构API指南.md](../../api_docs/新架构API指南.md) v2.1.0
- **主项目指南**: [CLAUDE.md](../../../CLAUDE.md)

---

**文档维护者**: AI Assistant
**审核状态**: 待审核
**文档版本**: v2.0 (整合最新开发进展)
**最后更新**: 2025-10-03
