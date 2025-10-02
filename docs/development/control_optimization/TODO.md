# 管控方案优化子系统开发任务清单

**文档版本**: v1.0
**更新日期**: 2025-10-02
**当前阶段**: MVP Phase 1 → Phase 2 过渡期

---

## 当前状态总览

### ✅ MVP Phase 1 已完成 (2025-10-02)

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

**待验证**:
- ⏳ 40-60实例大规模并行测试
- ⏳ 100万车辆峰值验证
- ⏳ 实时比≥1.0性能验证

---

## 📋 Phase 2 开发任务 (按Epic组织)

### Epic 2: 并行实例管理增强 (预计3-4天)

#### Story 2.1: 实例状态管理与实时监测 ⭐ **核心更新**
**优先级**: P0 (阻塞后续开发)

**设计确认**:
- ✅ 监测间隔：30秒（默认，可配置）
- ✅ 数据存储：元数据文件为主，数据库可选
- ✅ 峰值监测：从summary.xml实时读取

- [ ] **任务2.1.1**: Summary实时监测器实现
  - 类: `SummaryRealTimeMonitor`（文件尾部追踪）
  - 监测间隔: 30秒（可通过环境变量`MONITORING_INTERVAL`配置）
  - 峰值提取: 读取`running`属性，自动识别峰值
  - 文件: `shared/utilities/control_optimization/summary_monitor.py`
  - 参考: [SUMO_Summary实时监测技术方案.md](./SUMO_Summary实时监测技术方案.md)

- [ ] **任务2.1.2**: Worker进程集成Summary监测
  - 修改: `shared/utilities/control_optimization/parallel_simulator.py`
  - 集成点: `_run_simulation_worker()` 函数
  - 更新: `instance_status.json`（包含峰值数据）
  - 间隔: 30秒更新一次

- [ ] **任务2.1.3**: 批次状态文件实时更新
  - 文件: `batch_status.json`
  - 更新频率: 30秒
  - 汇总内容: 所有实例的状态分布、总峰值
  - 实现: 主进程定时读取各实例状态并汇总

- [ ] **任务2.1.4**: 批次/实例状态查询API
  - API 1: `GET /api/v1/control_optimization/batches/{batch_id}/status`
  - API 2: `GET /api/v1/control_optimization/batches/{batch_id}/instances`
  - API 3: `GET /api/v1/control_optimization/batches/{batch_id}/instances/{instance_id}/status`
  - 返回: 包含峰值车辆数、实时比、交通指标
  - 文件: `api/routes/control_optimization_routes.py`

- [ ] **任务2.1.5**: 失败任务诊断
  - 错误分类: timeout, sumo_error, config_error, system_error
  - 错误信息存储与查询
  - 文件: `shared/utilities/control_optimization/error_classifier.py`

#### Story 2.2: 任务调度优化
**优先级**: P1

- [ ] **任务2.2.1**: FIFO任务队列实现
  - 使用multiprocessing.Queue或数据库队列
  - 支持动态添加任务
  - 文件: `shared/utilities/control_optimization/task_scheduler.py`

- [ ] **任务2.2.2**: 超时检测机制
  - 可配置超时阈值（默认2小时）
  - 定时检查running任务是否超时
  - 超时自动标记为failed

- [ ] **任务2.2.3**: 孤儿任务清理
  - 启动时检查pending状态的遗留任务
  - 自动标记为cancelled或重新调度

---

### Epic 3: EdgeData采集与指标计算 (预计4-5天)

#### Story 3.1: EdgeData输出配置
**优先级**: P0 (评分系统依赖)

- [ ] **任务3.1.1**: 生成edges.add.xml
  - 监测边集合定义（主线+关键路段）
  - 放置在 `batch_config_xxx/edges.add.xml`
  - 文件: `shared/utilities/control_optimization/edge_selector.py`

- [ ] **任务3.1.2**: 集成EdgeData到sumocfg
  - 修改 `generate_sumocfg_for_simulation()` 添加EdgeData支持
  - 输出配置: `<edgeData file="edgedata/output.xml" ...>`
  - 文件: `shared/utilities/sumo_utils.py`

- [ ] **任务3.1.3**: 为每个实例创建edgedata输出
  - 实例配置中修改EdgeData路径
  - 确保edgedata目录存在
  - 文件: `parallel_simulator.py` (已有edgedata目录创建)

#### Story 3.2: EdgeData解析与指标提取
**优先级**: P0

- [ ] **任务3.2.1**: EdgeData XML解析器
  - 解析 `edgedata/output.xml`
  - 提取字段: edge_id, speed, density, occupancy, flow
  - 文件: `shared/data_processors/edgedata_parser.py`

- [ ] **任务3.2.2**: 关键指标计算
  - 平均速度（全网/主线）
  - 总延误时间（理论速度-实际速度）
  - 通行能力增幅（vs基准场景）
  - 文件: `shared/analysis_tools/edgedata_analyzer.py`

- [ ] **任务3.2.3**: 指标入库
  - 表设计: `control_optimization.task_metrics` (task_id, avg_speed, delay, capacity_gain, ...)
  - 批量插入优化
  - 文件: `api/services/metrics_service.py`

#### Story 3.3: 基准场景管理
**优先级**: P1

- [ ] **任务3.3.1**: 基准场景定义
  - 无管控策略的仿真作为基准
  - 存储基准指标: baseline_speed, baseline_capacity
  - 表设计: `control_optimization.baseline_scenarios`

- [ ] **任务3.3.2**: 基准场景API
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

#### Story 4.2: 排名与Top3推荐
**优先级**: P0

- [ ] **任务4.2.1**: 批次排名算法
  - 按score降序排序
  - 处理并列情况（分数相同）
  - 稳定排序（task_id升序）
  - 文件: `shared/utilities/control_optimization/ranking_engine.py`

- [ ] **任务4.2.2**: Top3提取逻辑
  - 前3名策略
  - 并列全部纳入（可能>3条）
  - 标注并列标识
  - 文件: `shared/utilities/control_optimization/recommendation_engine.py`

- [ ] **任务4.2.3**: 排名结果API
  - `GET /api/v1/control_optimization/batches/{batch_id}/ranking`
  - `GET /api/v1/control_optimization/batches/{batch_id}/top3`
  - 响应格式: rank, task_id, score, metrics, is_tied
  - 文件: `api/routes/control_optimization_routes.py`

#### Story 4.3: 结果导出
**优先级**: P1

- [ ] **任务4.3.1**: JSON导出
  - 完整批次结果（所有任务+评分+排名）
  - Top3推荐单独导出
  - 文件: `api/services/export_service.py`

- [ ] **任务4.3.2**: CSV导出
  - 任务级指标表格
  - Top3推荐表格
  - 支持Excel打开

- [ ] **任务4.3.3**: 导出API端点
  - `GET /api/v1/control_optimization/batches/{batch_id}/export?format=json|csv`
  - Content-Type设置正确
  - 文件名包含时间戳

---

### Epic 5: 前端界面增强 (预计4-5天)

#### Story 5.1: 结果页面开发
**优先级**: P0

- [ ] **任务5.1.1**: 批次结果表格
  - 列: rank, task_id, strategy_params, score, avg_speed, delay, capacity_gain
  - 分页支持（20条/页）
  - 可按指标排序
  - 文件: `frontend/control_optimization/results.html`

- [ ] **任务5.1.2**: Top3推荐卡片
  - 突出显示前3名
  - 展示关键指标和策略参数
  - 并列标识
  - 导出按钮

- [ ] **任务5.1.3**: 指标对比图表
  - 柱状图：Top3评分对比
  - 雷达图：多维度指标对比（速度/延误/通行能力）
  - 使用Chart.js

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

## 🚧 当前优先级任务（本周）

### 高优先级 (P0) - 必须完成

1. **验证实例独立目录功能** (0.5天)
   - [ ] 重新测试10实例并行
   - [ ] 检查每个instance目录的输出文件
   - [ ] 验证summary.xml、tripinfo.xml、e1/输出都正确

2. **EdgeData采集配置** (1-2天)
   - [ ] 实现edges.add.xml生成（Story 3.1.1）
   - [ ] 集成到batch_config生成流程（Story 3.1.2）
   - [ ] 验证EdgeData输出文件生成

3. **EdgeData解析与指标计算** (1-2天)
   - [ ] 实现EdgeData解析器（Story 3.2.1）
   - [ ] 计算关键指标（Story 3.2.2）
   - [ ] 指标入库（Story 3.2.3）

### 中优先级 (P1) - 本周完成

4. **评分模型实现** (1-2天)
   - [ ] 指标标准化（Story 4.1.1）
   - [ ] 加权评分计算（Story 4.1.2）
   - [ ] 缺失值处理（Story 4.1.3）

5. **Top3推荐算法** (1天)
   - [ ] 排名算法（Story 4.2.1）
   - [ ] Top3提取（Story 4.2.2）
   - [ ] API端点（Story 4.2.3）

### 低优先级 (P2) - 下周完成

6. **结果页面开发** (2-3天)
   - [ ] 批次结果表格（Story 5.1.1）
   - [ ] Top3推荐卡片（Story 5.1.2）
   - [ ] 指标对比图表（Story 5.1.3）

7. **监控页面增强** (1-2天)
   - [ ] 实时状态刷新（Story 5.2.1）
   - [ ] 任务详情弹窗（Story 5.2.2）

---

## 🔮 Phase 2 后续功能 (Week 4+)

### 扩展功能列表

1. **策略配置UI表单** (2-3天)
   - 替代CSV导入
   - 动态表单字段
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

## 🎯 本周工作计划 (2025-10-02 ~ 2025-10-08)

### Day 1-2: EdgeData采集
- [ ] 生成edges.add.xml（主线边集合）
- [ ] 集成到批量配置生成流程
- [ ] 验证EdgeData输出文件

### Day 3-4: 指标计算
- [ ] 解析EdgeData XML
- [ ] 计算平均速度、延误、通行能力
- [ ] 指标入库

### Day 5: 评分系统
- [ ] 指标标准化
- [ ] 加权评分计算
- [ ] Top3推荐算法

### Day 6-7: 前端开发
- [ ] 结果页面（表格+Top3卡片）
- [ ] 指标对比图表
- [ ] 集成测试

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

- **PRD文档**: [管控方案优化子系统PRD文档.md](./管控方案优化子系统PRD文档.md)
- **MVP功能清单**: [MVP功能清单.md](./MVP功能清单.md)
- **MVP测试指南**: [MVP测试指南.md](./MVP测试指南.md)
- **架构设计**: [架构设计方案.md](./架构设计方案.md)
- **API文档**: [../../api_docs/新架构API指南.md](../../api_docs/新架构API指南.md)
- **主项目指南**: [../../../CLAUDE.md](../../../CLAUDE.md)

---

**维护者**: 开发团队
**最后更新**: 2025-10-02
