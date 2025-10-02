# 管控方案优化子系统产品需求文档 (PRD)

## Change Log

| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 2024-12-19 | v1.0 | 初始版本创建 | 项目团队 |
| 2024-12-19 | v1.1 | 审核完善，添加技术细节 | 项目团队 |
| 2025-09-29 | v2.0 | 根据标准PRD模板重构 | John, PM |

## 1. Goals and Background Context

### 1.1 Goals

- 面向MVP：为并行仿真任务配置不同管控策略参数，并行执行仿真
- 汇聚仿真结果，计算核心指标并进行对比与排名
- 输出推荐的Top 3管控策略（基于可配置评分模型）
- 与现有系统无缝集成（最小化改动），提供最小UI用于操作与查看结果

### 1.2 Background Context

现有的OD数据处理与仿真系统已成功建立了强大的交通仿真基础，支持40-65个并行实例。然而，迫切需要扩展该系统以支持先进的交通控制优化功能。管控优化子系统解决了对智能交通管理解决方案日益增长的需求，这些解决方案可以同时评估多种控制策略，支持大规模仿真（100万车辆），并提供可操作的优化建议。

### 1.3 Scope

**包含功能**:

- 策略参数配置（按任务/批量）与校验（最小集）
- 并行仿真提交、状态跟踪与结果汇聚（最小集）
- 指标计算与评分（实时比、通行效率、拥堵代理指标等最小必要集合）
- 策略对比与排名、Top 3推荐
- 最小化UI：启动、状态/进度、结果与Top 3展示

**不包含功能**:

- 完整的方案生命周期管理（复杂模板库、版本治理、全面CRUD）
- 深度分析与高级优化算法（智能搜索、复杂报告生成）
- 复杂权限/多租户/审计体系
- 重型监控栈与分布式架构改造

### 1.4 MVP分阶段策略

本项目采用两阶段开发策略,确保快速交付可用产品并逐步完善功能。

#### Phase 1: MVP核心功能 (Week 1-3, 12-15天)

**目标**: 实现并行仿真集成 + 基础监控 + 峰值曲线 + Top3推荐

**包含功能**:
- ✅ 批量CSV导入策略参数(无复杂UI表单)
- ✅ 批次管理与≤60并行仿真启动
- ✅ 任务状态监控(queued/running/completed/failed)
- ✅ 在网车辆峰值单曲线展示
- ✅ 固定权重评分(delay 50% + capacity 50%)
- ✅ Top3推荐输出(含并列处理)
- ✅ 3个极简页面(启动/监控/结果)

**简化实现**:
- 监控刷新: 30秒定时轮询(无WebSocket)
- 错误处理: 基础日志+超时检测(固定2小时阈值)
- UI交互: 静态时间窗,无动态图表交互

#### Phase 2: 功能扩展 (Week 4+)

**扩展功能**:
- 🔵 策略配置UI表单(替代CSV导入)
- 🔵 可配置评分权重模型
- 🔵 多维度监控曲线(CPU/内存/实时比)
- 🔵 详细分析报告生成
- 🔵 预案模板库CRUD
- 🔵 WebSocket实时推送
- 🔵 完整错误处理机制(重试/断路器/优雅降级)

### 1.5 Success Metrics

#### 核心成功指标

- **功能达成**:
    - 支持为并行任务配置不同策略参数并成功执行
    - 自动汇聚结果并生成策略排名与Top 3推荐
    - 最小UI可用，完成基本启动、状态与结果展示
- **性能与稳定**:
    - 单批并行任务稳定完成率 ≥ 95%
    - 推荐计算耗时 ≤ 5s（单批≤60任务、指标已入库场景）
- **准确性与一致性**:
    - 评分与排名可复现（一致性≥99%同配置重跑）
    - 推荐Top3与业务规则一致性经评审确认

## 2. Requirements

### 2.1 Functional Requirements

1.  **FR1: 策略参数配置（最小集）**
    - **FR1.1**: 支持为每个并行任务提交一组策略参数（支持ATM/DTG常见字段的子集）。
    - **FR1.2**: 提供参数校验与默认值；支持批量导入/一键多任务提交。
    - **FR1.3**: 记录与回显任务的策略参数（便于复跑与对比）。
2.  **FR2: 并行仿真与结果汇聚**
    - **FR2.1**: 并行提交任务（≤60），状态可查询（queued/running/completed/failed）。
    - **FR2.2**: 采用“批次ID（batch_id）”组织一次提交的所有并行任务，评分与排名以批次为单位进行。
    - **FR2.3**: edges定义（监测边集合）为batch级一致：在仿真开始前确定，存放于`cases/<case_id>/control_optimization/<batch_id>/edges.add.xml`；也支持先提供边清单，由系统生成`edges.add.xml`。
    - **FR2.4**: SUMO以additional-file方式加载`edges.add.xml`，仿真过程中按该集合采集边级指标。
    - **FR2.5**: 采集最小必要指标（如平均速度、延误、吞吐、关键路段拥挤代理指标、实时比）。
    - **FR2.6**: 任务完成后自动汇聚指标，支持按批次/任务维度查询（limit分页）。
    - **FR2.7**: 失败任务处理：默认从评分排名中剔除，并在结果页单独列表展示失败原因（可配置为记零分但不参与Top3）。
    - **FR2.8**: 分页/limit：默认每页20条，最大不超过200条；超限请求返回校验错误。
3.  **FR3: 评分与排名**
    - **FR3.1**: 评分模型默认权重固定：延误50% + 主线/断面等效通行能力增幅50%（支持后续可配置，但MVP按此默认权重执行）。
    - **FR3.2**: 指标标准化：延误取更低更优（min-max或倒数标准化）；通行能力增幅取更高更优（min-max标准化）。异常/缺失值按规则剔除或用批次均值填补（不影响Top3公平性）。
    - **FR3.3**: 依据评分对任务进行排名并输出Top 3；若排名分数并列，则并列的策略全部纳入Top 3集合（可能>3条），并在结果中标注“并列”。
    - **FR3.4**: 并列排序稳定性：对并列集合按任务ID升序稳定排序；导出与界面一致。
    - **FR3.3**: 支持导出Top 3结果（JSON/CSV）。
4.  **FR4: 最小UI**
    - **FR4.1**: 启动页：参数输入、批量提交、查看批次ID。
    - **FR4.2**: 进度页：任务列表（状态/实例/进度%），可筛选与定时刷新。
    - **FR4.3**: 结果页：各任务核心指标、评分、Top 3推荐展示。

### 2.2 Non-Functional Requirements

1.  **NFR1: 仿真引擎性能**
    - 实时比 ≥ 1.0
    - 仿真时长范围: 1-8小时
    - 车辆规模: 支持100万车辆仿真
    - 并行实例: 60个并行SUMO实例
2.  **NFR2: 前端性能**
    - 首屏加载: ≤ 3秒
    - 页面切换: ≤ 1秒
    - 图表渲染: ≤ 500ms
    - 数据更新: ≤ 1秒
3.  **NFR3: 后端性能**
    - API响应: ≤ 500ms
    - 数据库查询: ≤ 200ms
    - 并发处理: 支持10个并发用户
    - 文件I/O: ≥ 100MB/s
4.  **NFR4: 系统稳定性**
    - 最长运行时间: ≥ 12小时
    - 内存泄漏: ≤ 1MB/hour
    - CPU使用率: 平均 ≤ 80%
    - 服务可用性: ≥ 99.5%
5.  **NFR5: 兼容性**
    - **系统兼容性**: 与现有API、数据库模式保持向后兼容。
    - **浏览器兼容性**: 支持 Microsoft Edge, Chrome, Firefox。

## 3. User Interface Design Goals

### 3.1 Overall UX Vision

为交通管理者提供一个直观、高效的界面，用于创建、管理和分析复杂的交通管控方案。界面应清晰地展示并行仿真的实时状态，并通过数据可视化提供有力的决策支持。

### 3.2 Key Interaction Paradigms

- **方案配置**: 通过表单和向导式流程引导用户完成策略配置。
- **实时监控**: 使用仪表盘和实时图表展示60个仿真实例的进度和关键指标。
- **对比分析**: 并排视图或覆盖图层，用于直观比较不同方案的仿真结果。

### 3.3 Core Screens and Views

- **管控方案管理页面**: 用于创建、编辑、加载和管理方案及模板。
- **仿真执行与监控页面**: 用于启动仿真任务，并实时监控所有实例的进度、状态和性能指标。
- **分析报告页面**: 用于展示策略对比分析的结果和数据可视化图表。

### 3.4 Accessibility: WCAG AA

### 3.5 Branding

- **设计系统**: Material Design + 自定义CSS变量。
- **图表库**: Chart.js 4.x。

### 3.6 Target Device and Platforms: Web Responsive

## 4. Technical Assumptions

### 4.1 Repository Structure: Monorepo (Implied)

### 4.2 Service Architecture: Monolith (Implied by existing structure)

### 4.3 Testing Requirements: Unit + Integration + E2E + Performance

### 4.4 Additional Technical Assumptions and Requests

- **前端技术栈**: HTML5, CSS3, JavaScript ES6+, Material Design, Chart.js 4.x。
- **后端技术栈**: FastAPI, PostgreSQL。
- **集成架构**: 通过API集成和静态文件挂载与现有系统集成。
- **数据库**: 使用独立的`control_optimization` schema来隔离数据。
- **缓存**: 使用Redis进行缓存以提高性能。
- **日志**: 使用`RotatingFileHandler`进行日志记录。
- **错误处理**: 建立统一的全局异常处理机制。

## 5. Epic List

- **Epic 1: 核心仿真引擎验证 (3-4周)**: 验证100万车辆规模与实时比≥1.0的技术可行性。
- **Epic 2: 并行实例管理核心 (2-3周)**: 验证与稳定化60个并行实例的创建、调度与状态管理。
- **Epic 3: 性能监控与验证 (2-3周)**: 建立性能指标采集、实时监控、报告与告警，验证性能达标。
- **Epic 4: 最小化UI实现 (1-2周)**: 提供启动仿真、查看状态与基本性能可视化的最小界面。
- **Epic 5: 集成测试与验证 (1-2周)**: 端到端流程、稳定性与性能验证，产出MVP验证报告。

## 6. Epic 1: 核心仿真引擎验证 ✅ (已完成预研)

**Goal**: 面向MVP验证100万车辆规模仿真的技术可行性，达成实时比≥1.0，并形成可复用的基线与调优手册。

**状态**: ✅ Epic 1完成 - ParallelSimulator已证明峰值>100万车辆能力
**MVP工作**: 无新增开发,仅集成调用现有并行仿真框架
**Phase 1预算**: 0天 (技术债务已清偿)

**遗留工作(不计入MVP开发量)**:
- 📝 文档化: 输出《核心仿真引擎调优手册》
- ✅ 集成: 已封装为ParallelSimulator模块（Epic 1完成）

### Story 1.1: 基线容量与实时比验证 ✅ (已完成)
**状态**: ✅ Epic 1完成并验证通过
**MVP无需执行**: 直接复用验证结果

### Story 1.2: SUMO集成与运行配置 ✅ (已完成)
**状态**: 现有系统已实现
**MVP无需执行**: 复用现有SimulationService

### Story 1.3: 性能指标埋点与数据采集 🔵 (Phase 2扩展)
**MVP简化实现**: 仅采集在网车辆数(每10步),存储为CSV文件
**Phase 2扩展**: 采集CPU/内存/IO等完整指标,入库并提供查询API

### Story 1.4: 基准测试与优化闭环 🔵 (Phase 2扩展)
**MVP简化实现**: 单次端到端测试验证实时比≥1.0
**Phase 2扩展**: 建立3组可复现基准工况,输出调优手册

## 6.2 Epic 2: 并行实例管理核心 🔵 (Phase 1核心)

**Goal**: 建立稳定可控的60实例并行管理能力，覆盖实例池、任务调度、状态追踪。
**Phase 1预算**: 3-4天
**Phase 2扩展**: 故障自愈、健康探测、动态资源配额

### Story 2.1: 实例池与任务调度 ✅ (MVP必需)
**Phase 1 Acceptance Criteria**:
1. 支持固定实例数配置(上限60),简单FIFO调度
2. 任务入队与分派,基础超时检测(固定2小时)
3. 关键事件日志(任务ID/实例ID/时间戳)

**Phase 2扩展**:
- 动态实例池(可用/不可用标记)
- 智能调度(考虑负载均衡)
- 重试机制(指数退避)

### Story 2.2: 任务生命周期与状态机 ✅ (MVP必需)
**Phase 1 Acceptance Criteria**:
1. 基础状态机: queued → running → completed/failed
2. 状态落库(batch_id/task_id/status/timestamps)
3. 失败状态记录错误信息

**Phase 2扩展**:
- 状态历史查询(最近N条)
- 幂等重试支持
- cancelled状态与非法跃迁检测

### Story 2.3: 健康检查与容错 🔵 (Phase 2)
**Phase 1简化实现**:
- 仅超时检测(固定阈值),超时标记failed
- 孤儿任务回收(启动时清理pending遗留)
- 无自动健康探测

**Phase 2扩展**:
- 实例心跳探测(≤30秒)
- 自动下线与任务迁移
- 输出运维手册

### Story 2.4: 资源配额与限流 🔵 (Phase 2)
**Phase 1简化实现**:
- 固定并发上限(60)
- 无运行时监控CPU/内存

**Phase 2扩展**:
- 动态资源监控
- 背压与降级机制
- 可观测限流事件

## 6.3 Epic 3: 性能监控与验证 🔵 (Phase 1核心)

**Goal**: 建立最小化性能监控,支持在网车辆峰值可视化与基础验收。
**Phase 1预算**: 2-3天
**Phase 2扩展**: 多维度监控、自动告警、详细性能报告

### Story 3.1: 指标模型与采集 ✅ (MVP必需)
**Phase 1 Acceptance Criteria**:
1. 仅采集在网车辆数(每10仿真步)
2. 数据存储为CSV文件(`<task_id>/vehicles.csv`)
3. 任务级汇总入库(peak_count/duration)

**Phase 2扩展**:
- 完整指标模型(实时比/CPU/内存/IO)
- 可配置采集频率(1-5秒)
- 聚合查询API(时间窗/limit分页)

### Story 3.2: 实时监控与告警 🔵 (Phase 1最小集)
**Phase 1 Acceptance Criteria**:
1. 单曲线图:在网车辆数 vs 仿真步数
2. 30秒定时刷新(无WebSocket)
3. 无自动告警,异常通过日志记录

**Phase 2扩展**:
- 多维度看板(实时比/CPU/内存/实例活跃数)
- 阈值告警与事件推送
- 告警全链路追踪

### Story 3.3: 性能报告与验收门禁 ✅ (MVP必需)
**Phase 1 Acceptance Criteria**:
1. 单次端到端测试,手动验证实时比≥1.0
2. 记录关键指标(峰值车辆数/持续时长/稳定率)
3. 简单验收清单(通过/失败)

**Phase 2扩展**:
- 自动生成性能报告(JSON/Markdown)
- 定义达标门槛与自动判定
- 报告可追溯(版本/构建号)

## 6.4 Epic 4: 最小化UI实现 🔵 (Phase 1核心)

**Goal**: 提供3个极简页面,支持批量提交、状态监控、Top3展示。
**Phase 1预算**: 4-5天
**Phase 2扩展**: 完整表单配置、动态图表交互、详细分析页面

### Story 4.1: 仿真启动面板 ✅ (MVP必需)
**Phase 1 Acceptance Criteria**:
1. 批量CSV导入组件(解析+基础校验)
2. 简化提交表单(batch_id/case_id/instance_count)
3. 启动按钮+成功显示batch_id

**Phase 2扩展**:
- 策略参数UI表单配置
- 实时表单验证与默认值
- 失败重试建议

### Story 4.2: 状态与进度总览 ✅ (MVP必需)
**Phase 1 Acceptance Criteria**:
1. 任务列表表格:task_id/status/progress/timestamps
2. 支持状态筛选(queued/running/completed/failed)
3. 30秒定时刷新(无实时推送)

**Phase 2扩展**:
- 任务详情弹窗(状态历史/日志摘要)
- 可配置刷新频率
- 分页+limit查询

### Story 4.3: 性能可视化（最小集） ✅ (MVP必需)
**Phase 1 Acceptance Criteria**:
1. 单曲线图:在网车辆数 vs 仿真步数(Chart.js)
2. 图表渲染≤2s(降低原500ms要求)
3. 静态时间窗(默认全时段)

**Phase 2扩展**:
- 多维度曲线(实时比/CPU/内存)
- 动态时间窗选择
- 图表交互(缩放/导出)

## 6.5 Epic 5: 集成测试与验证 ✅ (Phase 1必需)

**Goal**: 验证MVP核心流程可用,确认实时比≥1.0与60实例稳定性。
**Phase 1预算**: 2-3天
**Phase 2扩展**: 完整自动化测试套件、CI集成、性能回归监控

### Story 5.1: 端到端流程测试 ✅ (MVP必需)
**Phase 1 Acceptance Criteria**:
1. 手动测试完整流程:CSV导入→提交→监控→查看Top3
2. 验证关键场景(正常完成/任务失败/参数错误)
3. 记录测试截图与日志

**Phase 2扩展**:
- Playwright自动化测试
- 失败路径详细断言
- CI集成与门禁

### Story 5.2: 稳定性与长稳运行测试 🔵 (Phase 2)
**Phase 1简化实现**:
- 单次2小时测试,验证任务成功率≥95%
- 人工检查无明显内存泄漏

**Phase 2扩展**:
- 连续12小时长稳测试
- 自动资源监控(内存≤1MB/hour)
- 产出详细测试报告

### Story 5.3: 性能压测与回归 ✅ (MVP必需)
**Phase 1 Acceptance Criteria**:
1. 40-60实例并行测试,验证实时比≥1.0
2. 峰值车辆数>100万验证
3. 记录关键指标(稳定率/峰值时长)

**Phase 2扩展**:
- 性能回归自动检测(>5%告警)
- 基线数据管理
- 对比报告自动生成

## 7. Risks & Mitigation

- **R1: 100万车辆仿真性能不达标 (高风险)**
    - **Mitigation**: 采用均匀分配和负载均衡算法；在高峰时段调整仿真参数（如降低车辆密度）。
- **R2: 并行实例管理失败 (高风险)**
    - **Mitigation**: 明确硬件要求（≥ 64核 CPU, ≥ 256GB 内存）；采用固定实例数量和统一配置。
- **R3: 实时监控性能问题 (高风险)**
    - **Mitigation**: 降低监控数据更新频率（状态每30秒，进度每60秒）；简化监控工具，不使用复杂的监控栈。
- **R4: 与现有系统集成失败 (中风险)**
    - **Mitigation**: 使用独立的数据库schema和带前缀的API路由，避免冲突。

## 8. QA & Testing

- **单元测试**: 代码覆盖率 ≥ 80%。
- **集成测试**: API集成、数据库集成。
- **功能测试**: 前端功能、用户交互 (使用Playwright MCP)。
- **性能测试**: 100万车辆仿真、60个实例稳定性测试。
- **用户验收测试**: 功能完整性、用户体验。

## 9. Appendix

### 9.1 Terminology

- **OD**: Origin-Destination，起讫点数据
- **VSL**: Variable Speed Limit，可变限速
- **DHS**: Dynamic Hard Shoulder，动态硬路肩
- **ATM**: Active Traffic Management，主动交通管控
- **DTG**: Dynamic Traffic Guidance，动态交通诱导
- **SUMO**: Simulation of Urban Mobility，城市交通仿真
- **MVP**: Minimum Viable Product，最小可行产品

### 9.2 References

- 现有系统架构文档
- Material Design设计规范
- Chart.js官方文档
- FastAPI官方文档
- PostgreSQL官方文档
- Playwright MCP测试文档

### 9.3 指标定义与评分公式（MVP）

**延误（Delay）**
- 定义：相对于基准旅行时间（无策略或默认策略）的旅行时间增量。
- 观测窗口：按仿真时间滚动聚合（建议5分钟或15分钟），任务级取窗口均值或加权均值。
- 公式（任务级）：Delay = Avg(TravelTime_strategy) − Avg(TravelTime_baseline)
- 方向：更低更优。

**主线/断面等效通行能力增幅（CapacityGain）**
- 定义：选定主线或关键断面集合的单位时间通过流量较基线的增幅比例。
- 参考集合：由业务配置提供主线/断面ID集合；若缺失则使用默认主线集合。
- 公式（任务级）：CapacityGain = (Flow_strategy − Flow_baseline) / max(Flow_baseline, ε)
- 单位：相对增幅（可表示为%）。方向：更高更优。

**标准化（按批次）**
- 延误标准化：Delay_norm = 1 − MinMax(Delay) 或使用倒数标准化以保证“更低更优”。
- 通行能力增幅标准化：CapacityGain_norm = MinMax(CapacityGain)。
- 缺失/异常：剔除或用批次均值填补，不参与Top3时采用剔除策略。

**评分（默认权重）**
- Score = 0.5 × Delay_norm + 0.5 × CapacityGain_norm
- 并列处理：同分任务全部纳入Top3集合，并标注“并列”；集合内部按任务ID升序稳定排序。

### 9.4 edges定义与采集流程（SUMO additional-file）

**edges定义（batch级一致）**
- 生成时机：仿真开始前，依据“管控位置→节点/设施→主线方向±K个单元（K=2）拓展→去重”的规则确定边集合。
- 存放路径：`cases/<case_id>/control_optimization/<batch_id>/edges.add.xml`。
- 生成方式：
  - 直接提供XML（`edges.add.xml`）
  - 或提供edge_id清单（CSV/JSON），由系统拼接生成`edges.add.xml`。

**SUMO加载与采集**
- 使用`--additional cases/<case_id>/control_optimization/<batch_id>/edges.add.xml`加载。
- 仿真期间按edges集合采集边级指标（travel_time, flow, speed等），明细落地文件（建议Parquet/CSV），任务级汇总入库用于评分与排名。

**混合存储策略**
- 明细：文件为主，按`<case_id>/<batch_id>/<task_id>/edges.parquet|csv`落地，并写`metrics.meta.json|xml`。
- 汇总：数据库为辅，入库字段含`batch_id/task_id/case_id/score/各指标`与`files_root/path`，便于查询与追溯。
