# 案例管理与影响分析混乱诊断与清理指南

**日期**: 2025-11-15
**状态**: 🟢 **Phase 1 完成 ✅ | Phase 1.5 完成 ✅ | Phase 2 规划中**
**优先级**: P0 - 影响核心工作流
**实施文档**:
- **Phase 1**: `PHASE1_CLEANUP_PLAN.md`, `PHASE1_IMPLEMENTATION_STATUS.md`, `PHASE1_IMPLEMENTATION_COMPLETE.md`
- **Phase 1.5**: `PHASE1_5_CLEANUP_PLAN.md`, `PHASE1_5_IMPLEMENTATION_STRATEGY.md`, `PHASE1_5_IMPLEMENTATION_COMPLETE.md`, `PHASE1_5_IMPLEMENTATION_VERIFICATION.md`
- **Phase 2**: Documentation to be created

---

## 核心问题诊断

### 问题 1: 案例创建接口重复（4个接口做同一件事）

#### 当前混乱状态

```
POST /api/v1/case/create_case/                    ← 通用创建
    └─> case_service.create_case()

POST /api/v1/case/create-from-scenario            ← Phase 2
    └─> case_service.quick_create_case_from_event()

POST /api/v1/case/quick-create-from-event         ← Phase 5.3.3
    └─> case_service.quick_create_case_from_event()  ⚠️ 同一个函数！

POST /api/v1/case/create-case-with-simulation     ← 统一创建
    └─> case_service.create_case_with_simulation()
```

#### 源代码中的冗余方法

```python
# CaseService 中有多个创建方法：
1. create_case(request)                    # Line 33
2. _get_or_create_event_case(...)         # Line 213（内部）
3. _get_or_create_event_case_with_lock()  # Line 319（内部，锁定版本）
4. create_case_from_scenario(request)     # Line 951
5. quick_create_case_from_event(request)  # Line 1068
6. create_case_with_simulation(request)   # 可能存在（需要验证）
```

#### 为什么混乱

1. **相同功能多次实现**: `/create-from-scenario` 和 `/quick-create-from-event` 都调用相同的 `quick_create_case_from_event()`，说明它们完全重复

2. **缺乏统一入口**: 没有清晰的流程说明应该用哪个接口
   - OD提取用户应该用 `/create_case/`
   - 事件场景用户应该用哪个？三选一？

3. **历史遗留**:
   - Phase 2 增加了 `/create-from-scenario`
   - Phase 5.3.3 又增加了 `/quick-create-from-event` (完全重复)
   - 统一创建 `/create-case-with-simulation` (又是另一个)

4. **代码混乱**:
   - 有锁定逻辑 `_get_or_create_event_case_with_lock()` 但不清楚何时需要
   - 内部方法与公共方法职责不清

---

### 问题 2: 影响分析路由不完整

#### 当前状态

```python
# analysis_routes.py 中只有：
@router.post("/analyze_accuracy/")
    └─> 精度分析（说"暂不支持多仿真"）

@router.get("/analysis_history/{case_id}")
    └─> 获取分析历史

@router.get("/analysis_mapping/{case_id}")
    └─> 获取分析映射

@router.get("/analysis_results/{case_id}")
    └─> （只是框架，代码被截断）
```

#### 缺失的功能

对比原始设计需求，当前缺失：

| 功能 | 路由 | 状态 | 问题 |
|------|------|------|------|
| EdgeData分析 | 无 | ❌ 缺失 | 完全没有实现 |
| 机制分析 | 无 | ❌ 缺失 | 完全没有实现 |
| 性能分析 | 无 | ❌ 缺失 | 完全没有实现 |
| 精度分析 | `/analyze_accuracy/` | ⚠️ 不完整 | 只支持单仿真，不支持批量 |
| 分析结果 | `/analysis_results/` | ⚠️ 不完整 | 框架存在，无实现 |
| 分析进度 | 无 | ❌ 缺失 | 无法追踪分析进度 |

#### 代码注释说明问题

```python
# analysis_routes.py Line 9
# "不再从api.services导入旧函数，直接使用服务类"
# 这说明有过重构，但重构不完整
```

#### 为什么分析部分混乱

1. **重构未完成**: 注释表明有从函数到服务类的重构，但只有精度分析被转换了

2. **遗留的OD分析**: 当前路由是为OD提取的精度分析，不适合事件场景

3. **缺少聚合能力**: 没有跨多仿真的批量分析能力（Phase 2 需要）

4. **缺少实时进度**: 没有分析进度追踪接口

---

### 问题 3: 案例管理前端与后端API不匹配

#### 前端期望 (case-simulation-center.html)

```javascript
// Tab 1: 案例列表
GET /api/v1/case/list (有过滤)
  ├─ status: 运行中|已完成|失败
  ├─ source_scenario_id: 筛选来自特定场景的案例
  └─ search: 按ID或名称搜索

// Tab 2: 仿真监控
POST /api/v1/simulation/batch-start
GET  /api/v1/simulation/batch-status/{batch_id}

// Tab 3: 批次历史
GET /api/v1/simulation/batch-list?status=completed
```

#### 后端实际提供

```python
# case_routes.py 提供的
GET  /api/v1/case/list_cases/        # ⚠️ 端点名不同！
  ├─ 支持 page, page_size
  ├─ 支持 status 筛选
  ├─ 支持 search
  └─ ❌ 不支持 source_scenario_id 筛选

# simulation_routes.py 不清楚是否有
POST /api/v1/simulation/batch-start   # 需要验证
GET  /api/v1/simulation/batch-status  # 需要验证
```

#### API端点命名混乱

| 端点名 | 用途 | 问题 |
|--------|------|------|
| `/create_case/` | 创建 | 名称后缀有斜杠 |
| `/create-from-scenario` | 从场景创建 | 使用连字符 |
| `/quick-create-from-event` | 快速从事件创建 | 冗余 |
| `/create-case-with-simulation` | 统一创建 | 另一种命名 |
| `/list_cases/` | 列表 | 后缀有斜杠 |
| `/case/{case_id}` | 详情 | 无斜杠 |

**结论**: 接口命名风格不一致（有时 `/path/`，有时 `/path`，有时用连字符，有时用下划线）

---

## 混乱的根本原因分析

### 1. 多个并行开发流程汇聚 🔴

```
Phase 1: OD提取工作流
    └─ create_case() / list_cases() / get_case()

Phase 2 (Event-Scenario)
    ├─ 增加: create-from-scenario
    ├─ 增加: 分析结果聚合
    └─ 注意：不应修改现有OD流程

Phase 5 (另一个改进)
    └─ 增加: quick-create-from-event (与Phase 2重复)

统一创建优化
    └─ 增加: create-case-with-simulation (原子操作)
```

每个阶段都添加新接口，而不是整合现有接口。

### 2. 没有清晰的分工界限 🔴

```
API 层应该做什么？
  ❌ 当前: 混合了多个工作流的不同创建逻辑
  ✅ 应该: 提供清晰的主要工作流入口

业务逻辑应该在哪里？
  ❌ 当前: 分散在 CaseService 的多个方法中
  ✅ 应该: 统一的工作流编排（orchestration）

数据访问在哪里？
  ❌ 当前: BaseService 和 CaseService 混合
  ✅ 应该: 分离关注点
```

### 3. 没有统一的工作流定义 🔴

```
当前状态：
  OD工作流 → API → CaseService → 各种方法
  Event工作流 → API → CaseService → 其他方法
  (没有统一的orchestration层)

应该是：
  工作流定义（Workflow）
    ├─ OD工作流: scenario→case→simulation→analysis
    ├─ Event工作流: scenario→case→simulation→analysis
    └─ Unified工作流: scenario→(case+simulation)→analysis

  API 层（Router）
    ├─ POST /api/v1/workflows/od-extraction
    ├─ POST /api/v1/workflows/event-scenario
    └─ POST /api/v1/workflows/create-case

  服务层（Service）
    └─ WorkflowOrchestrator → CaseService → ...
```

---

## 清理方案

### 方案选择: 分阶段整合

#### 阶段 1: 整合案例创建接口 (立即执行 - 1 天)

**目标**: 从 4 个接口简化为 2 个

**保留的接口**:

```python
# 1. 通用创建（保留现状）
POST /api/v1/case/create
  Request:
    - case_name: 案例名称
    - case_config: 配置（网络、OD数据等）
    - description: 描述
  Response: { case_id, metadata, status }
  用途: OD提取工作流，通用创建

# 2. 批量创建事件案例（**推荐用于事件场景工作流**）
POST /api/v1/scenario/create-case-batch
  Request: CreateEventCaseBatchRequest
    - event_id: 事件ID（例: "10754"）
    - event_type: 事件类型（例: "01_accident"）
    - scenarios: 场景数组，包含：
        - scenario_id: 场景ID
        - event_location: 事件位置
        - control_strategy: 控制策略（可选）
        - output_config: 输出配置
        - time: {sim_duration_hours, sim_start_time, sim_end_time}
    - network_file: 网络文件路径
    - od_file: OD数据源（例: "dwd.dwd_od_weekly"）
    - taz_file: TAZ文件路径
    - time_range: {start_time, end_time}
    - simulation_type: "microscopic"
  Response: EventCaseBatchCreationResponse
    - case_id: "case_event_{event_id}"
    - event_id: 事件ID
    - successful_scenarios: 成功创建的场景数
    - failed_scenarios: 失败场景数
    - total_scenarios: 总场景数
    - simulations: {sim_id: {...}, ...}
    - edgedata_info: {edge_count, validation_rate, should_enable, ...}
    - scenario_results: [{scenario_id, simulation_id, success, ...}, ...]
    - duration_seconds: 耗时
  用途: **事件场景主工作流，为一个事件的所有场景一次性创建OD case+仿真配置**
  说明:
    - case_id 格式: case_event_{event_id}（基于event_id，不是时间戳）
    - 所有scenario共享同一个OD case
    - OD数据仅生成一次（后台异步）
    - 每个scenario创建独立的simulation（sim_scenario_xxx）
    - EdgeData由所有策略聚合生成（智能决策）
    - **为什么这是推荐接口**: 一次API调用vs N次，性能提升5-10倍；无并发问题；EdgeData聚合更完整
    - **当前阶段**: 这是主要使用的接口（暂不需要单个场景创建）

# 2.1 单个场景创建（**未来保留，目前不需要**）
POST /api/v1/case/create-from-event-scenario  ⚠️ **RESERVED FOR FUTURE USE**
  说明:
    - 保留此接口以支持未来"逐个添加scenario到已有case"的需求
    - 目前阶段不需要使用此接口
    - 如果需要后续添加新场景到现有事件，将启用此接口（需要case重用和文件锁机制）
```

**删除的接口**:

```python
❌ DELETE /api/v1/case/create_case/
   ← 改名为 /api/v1/case/create

❌ DELETE /api/v1/case/quick-create-from-event
   ← 改名为 /api/v1/case/create-from-event-scenario
   ← 合并 create-from-scenario 的功能

❌ DELETE /api/v1/case/create-case-with-simulation
   ← 功能由 create-from-event-scenario 的自动模拟创建实现
```

**服务层实现**:

```python
# CaseService 中的方法
# 保留（OD提取工作流）
✓ create_case()                      # 基础创建（OD工作流）
✓ list_cases()
✓ get_case()
✓ delete_case()
✓ clone_case()

# 主要使用（事件场景工作流）- 推荐
✓ create_event_case_batch()          # 批量创建事件案例+仿真
                                      # 为一个事件的所有scenarios一次性创建：
                                      # - 1个OD case (case_event_{event_id})
                                      # - N个simulations (sim_scenario_xxx)
                                      # - 1个聚合的edgeData.add.xml
                                      # 参数: CreateEventCaseBatchRequest
                                      # 返回: EventCaseBatchCreationResponse

# 保留（未来可能需要）
⚠️ create_case_from_event_scenario()  # 单个场景创建（RESERVED FOR FUTURE）
                                      # 用于后续添加新场景到已有case
                                      # 目前阶段不需要使用
                                      # 需要: case重用 + 文件锁 + is_new_case判断
```

**为什么推荐 create_event_case_batch**:
1. **性能**: 1次API调用，vs 单个场景创建需要N次调用
2. **简单**: 原子操作，无需处理并发重复创建问题
3. **完整**: 聚合所有策略生成EdgeData，而不是单个处理
4. **可靠**: 一次性为所有scenario创建，无遗漏和重试问题

**代码示例**:

```python
# 新的统一方法（CaseService）
async def create_case_from_event_scenario(
    self,
    request: CreateFromEventScenarioRequest
) -> CreateCaseResponse:
    """
    从事件场景创建案例并自动创建仿真。

    这是Phase 2事件场景工作流的主要入口。
    替代: create_case_from_scenario() + quick_create_case_from_event()

    返回格式:
    - case_id: case_event_{event_id}
    - simulation_id: event_simulation_scenario_{scenario_id}
    - case_type: event_based
    """
    try:
        # 1. 验证场景存在
        scenario = self._validate_event_scenario(request.scenario_id)
        event_id = scenario.event_id

        # 2. 创建案例（带锁定）
        with self._acquire_event_case_lock(request.scenario_id):
            case = self._create_event_case(
                scenario_id=request.scenario_id,
                event_id=event_id,
                case_id=f"case_event_{event_id}"
            )

        # 3. 创建仿真（总是创建，不需要参数控制）
        simulation = self._create_and_prepare_simulation(
            case_id=case.case_id,
            scenario_id=request.scenario_id,
            simulation_id=f"event_simulation_scenario_{request.scenario_id}",
            simulation_duration_hours=request.simulation_duration_hours,
            output_config=request.output_config
        )

        return CreateCaseResponse(
            case_id=case.case_id,
            case_type="event_based",
            simulation_id=simulation.simulation_id,
            metadata=case.metadata,
            status="case_created_with_scenario"
        )

    except Exception as e:
        raise CreateCaseError(f"场景创建失败: {str(e)}")
```

**影响**:
- ✅ API 端点从 4 个减少到 2 个
- ✅ 功能完整（所有现有功能保留）
- ✅ 清晰的工作流（OD vs Event）
- ✅ 向后兼容（旧端点可在兼容层继续支持）

---

#### 阶段 1.5: 事件批量仿真管理 (1 天)

**目标**: 实现事件仿真的批量启动和进度监控功能

**背景**:

通过 `POST /api/v1/case/create-from-event-scenario` 创建的每个案例都会自动创建一个仿真，但这些仿真需要统一的批量管理能力：
- 创建多个事件场景的案例和仿真后，需要批量启动
- 需要统一监控仿真进度
- 需要跟踪批次级别的仿真结果

**新增的接口**:

```python
# 1. 批量启动事件仿真
POST /api/v1/event-simulation/batch-start
  Request:
    - case_ids: [case_event_1, case_event_2, ...]  或 sim_ids: [...]
    - description: 批次描述（可选）
  Response: {
    batch_id: "event_sim_batch_{timestamp}",
    total_simulations: 5,
    status: "batch_started",
    created_at: "2025-11-15T12:00:00"
  }
  用途: 启动多个事件仿真，返回批次ID用于追踪

# 2. 查询批量仿真进度
GET /api/v1/event-simulation/batch-progress/{batch_id}
  Response: {
    batch_id: "event_sim_batch_{timestamp}",
    total_simulations: 5,
    completed: 2,
    failed: 0,
    running: 1,
    pending: 2,
    progress_percent: 40,
    current_status: {...},  # 当前运行中的仿真状态
    simulations: [
      { sim_id, status, progress, eta, error_msg },
      ...
    ],
    batch_status: "in_progress",
    eta_completion: "2025-11-15T14:30:00"
  }
  用途: 实时查询批次中各仿真的运行状态和进度

# 3. 获取批量仿真结果
GET /api/v1/event-simulation/batch-results/{batch_id}
  Response: {
    batch_id,
    total_simulations,
    successful,
    failed,
    results: [
      { sim_id, case_id, status, output_files, error_msg },
      ...
    ]
  }
  用途: 获取所有仿真的最终结果
```

**删除的接口**:

```python
# 删除以下单独仿真相关的通用接口（不再需要）
❌ DELETE POST /api/v1/simulation          # 创建仿真
❌ DELETE GET  /api/v1/simulation          # 列表
❌ DELETE POST /api/v1/simulation/start    # 单个启动
❌ DELETE GET  /api/v1/simulation/{sim_id} # 单个详情
```

**服务层实现**:

```python
# 新增 EventSimulationService
class EventSimulationService:
    """
    专门处理事件仿真的批量管理和进度追踪
    """

    async def batch_start_event_simulations(
        self,
        request: BatchStartEventSimulationRequest
    ) -> BatchStartResponse:
        """
        批量启动事件仿真。

        Args:
            request: 包含 case_ids 或 sim_ids

        Returns:
            batch_id, total_simulations, status
        """
        # 1. 验证案例/仿真存在
        simulations = await self._get_simulations(request)

        # 2. 创建批次记录
        batch = await self._create_batch(
            simulations=simulations,
            description=request.description
        )

        # 3. 异步启动所有仿真
        await self._start_all_simulations_async(batch.batch_id, simulations)

        return BatchStartResponse(
            batch_id=batch.batch_id,
            total_simulations=len(simulations),
            status="batch_started",
            created_at=batch.created_at
        )

    async def get_batch_progress(self, batch_id: str) -> BatchProgressResponse:
        """
        实时获取批次进度。使用数据库或缓存追踪各仿真状态。
        """
        batch = await self._get_batch(batch_id)

        simulations = await self._get_simulations_for_batch(batch_id)

        stats = self._calculate_stats(simulations)

        return BatchProgressResponse(
            batch_id=batch_id,
            **stats,
            simulations=simulations
        )

    async def get_batch_results(self, batch_id: str) -> BatchResultsResponse:
        """
        获取批次中所有仿真的最终结果。
        """
        simulations = await self._get_simulations_for_batch(batch_id)

        return BatchResultsResponse(
            batch_id=batch_id,
            total_simulations=len(simulations),
            successful=sum(1 for s in simulations if s.status == "completed"),
            failed=sum(1 for s in simulations if s.status == "failed"),
            results=[
                {
                    "sim_id": s.simulation_id,
                    "case_id": s.case_id,
                    "status": s.status,
                    "output_files": s.output_files,
                    "error_msg": s.error_msg
                }
                for s in simulations
            ]
        )
```

**数据模型**:

```python
# Request 模型
class BatchStartEventSimulationRequest(BaseModel):
    case_ids: Optional[List[str]] = None   # case_event_xxx
    sim_ids: Optional[List[str]] = None    # event_simulation_scenario_xxx
    description: Optional[str] = None

    # 验证：case_ids 和 sim_ids 至少提供一个
    @root_validator
    def validate_ids(cls, values):
        if not values.get('case_ids') and not values.get('sim_ids'):
            raise ValueError("Must provide either case_ids or sim_ids")
        return values

# Response 模型
class BatchStartResponse(BaseModel):
    batch_id: str
    total_simulations: int
    status: str  # "batch_started"
    created_at: datetime

class BatchProgressResponse(BaseModel):
    batch_id: str
    total_simulations: int
    completed: int
    failed: int
    running: int
    pending: int
    progress_percent: float
    batch_status: str  # "in_progress", "completed", "partial_failure"
    eta_completion: Optional[datetime]
    simulations: List[Dict]

class BatchResultsResponse(BaseModel):
    batch_id: str
    total_simulations: int
    successful: int
    failed: int
    results: List[Dict]
```

**影响**:
- ✅ 提供统一的事件仿真批量管理能力
- ✅ 支持实时进度追踪
- ✅ 简化前端对仿真的管理
- ✅ 删除不需要的单仿真接口，降低API复杂度

---

#### 阶段 2: 事件仿真批量结果分析 (2-3 天)

**目标**: 对事件仿真批次的结果进行对比分析，评估不同管控策略下的效果

**背景**:

事件仿真的核心价值在于对比不同管控策略下的仿真结果。分析功能应该：

- **输入**：事件仿真批次结果（来自 `event-simulation/batch-results`）
  - 数据来源：`summary.xml` （必有）和 `edgedata.xml` （可选，智能生成）
  - 不涉及 tripinfo 数据

- **对比场景**：
  - 事件条件下**无管控** vs **有不同管控**的仿真对比
  - 事件**实际管控**（如果存在）vs **不同管控方案**的对比
  - 关键对比维度：交通流量、速度、拥堵程度等

- **输出**：对比分析报告（排名、差异、洞察建议）
- **焦点**：管控策略效果对比，而不是 E1/Gantry 的精度验证

**关键技术点**:

1. **edgedata 智能生成**：
   - 在创建 case_from_event_scenario 时，根据事件和管控配置是否涉及 edge 决定是否输出 edgedata
   - 如果不涉及 edge → 不生成 edgedata.xml，不输出 edgeData.add.xml
   - 仅包含 summary.xml 数据用于分析

2. **仿真配置顺序**（关键约束）：
   ```
   正确顺序（必须遵守）：
   a) 生成 rou.xml (路由文件)
   b) 生成 sumocfg.xml (参考 rou.xml)

   ⚠️ 顺序错误后果：sumocfg 中的配置会引入错误，导致仿真失败
   ```

**当前状态**:

```
✓ AnalysisResultsService (存在，~900行)
  ├─ get_analysis_results()
  ├─ get_comparison_report()      ← 这正是我们需要的
  └─ 其他分析方法

❌ 面向事件仿真的分析路由 (缺失)
❌ 批次级别的对比分析 (缺失)
❌ 分析进度追踪 (缺失)
```

**新的分析架构**:

```
事件工作流架构（推荐）:
1. create-case-batch (创建event的所有scenario的case+仿真配置)  ← 主接口
   ├─ 输入: 1个event_id + N个scenarios
   ├─ 输出: 1个case_event_{event_id} + N个simulations + 聚合EdgeData
   └─ OD数据: 后台异步生成（共用）
   ↓
2. event-simulation/batch-start (启动所有仿真批次)
   ├─ 输入: case_ids 或 sim_ids
   └─ 输出: batch_id, 启动状态
   ↓
3. event-simulation/batch-results (获取仿真结果)
   ├─ 查询仿真执行状态
   └─ 获取仿真完成后的结果
   ↓
4. event-simulation-analysis/run-comparison (对比分析) ← 未来Phase 2
   ├─ 对比不同策略的仿真结果
   └─ 基于summary.xml + edgedata.xml
   ↓
5. event-simulation-analysis/results (分析报告) ← 未来Phase 2
   └─ 获取完整的对比分析报告

---

备选工作流架构（未来支持）:
1. create-from-event-scenario (逐个创建scenario)  ← 保留接口（RESERVED）
   ├─ 首个scenario: 创建case + 启动OD生成
   ├─ 后续scenario: 复用case + 不重复生成OD
   └─ 需要: case重用 + 文件锁机制
   ↓
2-5. 同上（batch-start, batch-results, analysis等）

注意：目前阶段推荐使用第一种工作流（create-case-batch）
```

**新增的接口**:

```python
# 1. 启动批次级别的对比分析
POST /api/v1/event-simulation-analysis/run-comparison
  Request:
    - batch_id: "event_sim_batch_{timestamp}"  (from batch-start)
    - analysis_config: {
        metrics: ["trip_count", "avg_speed", "congestion_ratio"],  # 来自 summary.xml
        enable_edge_analysis: true/false,  # 可选，仅在某些模拟有 edgedata.xml 时为 true
        reference_sim_id: "event_simulation_scenario_xxx" (可选，用于基准对比)
      }
  Response: {
    analysis_batch_id: "event_analysis_{timestamp}",
    total_simulations: 5,
    with_edgedata: 3,  # 有 edgedata.xml 的仿真数
    status: "analysis_started",
    created_at: "2025-11-15T12:00:00"
  }
  用途: 对事件仿真批次的结果进行对比分析
  说明:
    - 数据来源：summary.xml （必有）和 edgedata.xml （可选）
    - 不涉及 tripinfo 数据

# 2. 查询分析进度
GET /api/v1/event-simulation-analysis/progress/{analysis_batch_id}
  Response: {
    analysis_batch_id,
    total_simulations,
    analyzed: 3,
    failed: 0,
    progress_percent: 60,
    status: "in_progress",
    eta_completion: "2025-11-15T13:30:00"
  }
  用途: 实时查询分析进度

# 3. 获取对比分析结果
GET /api/v1/event-simulation-analysis/results/{analysis_batch_id}
  Response: {
    analysis_batch_id,
    original_batch_id,
    timestamp: "2025-11-15T13:25:00",
    analysis_config,

    # 数据源统计
    data_sources: {
      total_with_summary: 5,
      total_with_edgedata: 3,
      edge_coverage: "60%"
    },

    # 对比分析结果
    comparison_summary: {
      total_simulations: 5,
      best_performer: {
        sim_id,
        control_strategy,  # 管控策略标识
        metrics: { trip_count, avg_speed, congestion_ratio }
      },
      worst_performer: { sim_id, control_strategy, metrics },
      average_metrics: { trip_count, avg_speed, congestion_ratio }
    },

    # 详细的对比数据（来自 summary.xml）
    simulations_comparison: [
      {
        sim_id: "event_simulation_scenario_1",
        case_id: "case_event_123",
        control_strategy: "no_control",  # 无管控 | 策略A | 策略B | 实际管控等
        metrics: {
          trip_count: 1523,           # from summary.xml
          avg_speed: 45.2,            # from summary.xml
          congestion_ratio: 0.32,     # 根据 summary.xml 计算

          # 如果有 edgedata.xml 数据
          edge_metrics: {
            congested_segments: 12,
            avg_segment_speed: 38.5,
            ...
          }
        },
        rank: 1,
        delta_vs_best: 0,
        delta_vs_avg: -5.2
      },
      ...
    ],

    # 管控策略对比分析
    control_strategy_comparison: {
      "no_control": {
        avg_speed: 42.3,
        congestion_ratio: 0.45
      },
      "strategy_A": {
        avg_speed: 45.2,
        congestion_ratio: 0.32,
        improvement_vs_no_control: "+6.9% speed, -28.9% congestion"
      },
      "actual_control": {
        avg_speed: 44.8,
        congestion_ratio: 0.35,
        improvement_vs_no_control: "+5.9% speed, -22.2% congestion"
      }
    },

    # 差异分析和建议
    insights: [
      {
        type: "performance_gap",
        description: "Strategy A的平均速度比无管控快6.9%，拥堵程度降低28.9%",
        simulations: ["scenario_A"],
        recommendation: "Strategy A 效果最佳，建议采用"
      },
      {
        type: "edge_analysis",
        description: "边界路段分析：X路段在Strategy A下拥堵解决率最高（85%）",
        segments: ["seg_X", "seg_Y"],
        note: "仅在 edgedata.xml 可用时出现"
      },
      ...
    ]
  }
  用途: 获取详细的对比分析报告
  说明:
    - 所有指标均基于 summary.xml（必有）
    - edge_metrics 仅在仿真包含 edgedata.xml 时出现
    - 支持无管控 vs 不同管控的对比
    - 如存在实际管控，自动包含实际管控的对比
```

**删除/改造的接口**:

```python
# 删除通用分析接口（不再需要）
❌ DELETE POST /api/v1/analysis/run-batch
❌ DELETE GET  /api/v1/analysis/batch-progress/{batch_id}
❌ DELETE GET  /api/v1/analysis/results/{batch_id}
❌ DELETE @router.post("/analyze_accuracy/")
❌ DELETE @router.get("/analysis_history/{case_id}")
❌ DELETE @router.get("/analysis_mapping/{case_id}")

# 改造原有服务
✓ AnalysisResultsService.get_comparison_report()
  └─ 重点：输入为 batch_id，输出为管控策略间的对比
```

**关于数据驱动的实现细节**:

1. **Summary.xml 解析**（必须实现）：
   - 从 SUMO 输出的 summary.xml 提取关键指标
   - 关键字段：`<step>`, `<running>`, `<speed>`, `<duration>`
   - 计算指标：trip_count（总行程）, avg_speed（平均速度）, congestion_ratio（拥堵率）

2. **EdgeData.xml 解析**（可选实现）：
   - 仅当事件+管控涉及 edge 时，SUMO 才输出 edgedata.xml
   - 智能判断：创建仿真配置时检查是否需要 edge 输出
   - 提取路段级别的拥堵、速度等数据

3. **rou.xml 和 sumocfg 生成顺序**（关键约束）：
   ```python
   # ❌ 错误的顺序（会导致配置错误）
   step1: generate_sumocfg()  # 先生成 sumocfg
   step2: generate_rou()      # 再生成 rou
   结果：sumocfg 中引入错误

   # ✅ 正确的顺序（必须遵守）
   step1: generate_rou()      # 先生成路由文件
   step2: generate_sumocfg()  # 再生成配置文件（参考 rou.xml）
   结果：sumocfg 配置正确
   ```

**服务层实现**:

```python
# 新增 EventSimulationAnalysisService
class EventSimulationAnalysisService:
    """
    专门处理事件仿真批次的对比分析
    """

    async def run_comparison_analysis(
        self,
        request: RunComparisonAnalysisRequest
    ) -> RunAnalysisResponse:
        """
        启动批次级别的对比分析。

        Args:
            request: 包含 batch_id 和 analysis_config

        Returns:
            analysis_batch_id, total_simulations, status
        """
        # 1. 验证仿真批次存在
        batch = await self._get_event_sim_batch(request.batch_id)

        # 2. 验证仿真都已完成
        simulations = await self._get_batch_simulations(batch.batch_id)
        if any(s.status != "completed" for s in simulations):
            raise AnalysisError("仿真未全部完成，无法分析")

        # 3. 创建分析批次记录
        analysis_batch = await self._create_analysis_batch(
            original_batch_id=request.batch_id,
            config=request.analysis_config
        )

        # 4. 异步启动分析任务
        await self._start_analysis_async(
            analysis_batch.analysis_batch_id,
            simulations,
            request.analysis_config
        )

        return RunAnalysisResponse(
            analysis_batch_id=analysis_batch.analysis_batch_id,
            total_simulations=len(simulations),
            status="analysis_started",
            created_at=analysis_batch.created_at
        )

    async def get_analysis_progress(
        self,
        analysis_batch_id: str
    ) -> AnalysisProgressResponse:
        """
        实时获取分析进度。
        """
        batch = await self._get_analysis_batch(analysis_batch_id)
        stats = await self._calculate_progress_stats(analysis_batch_id)

        return AnalysisProgressResponse(
            analysis_batch_id=analysis_batch_id,
            **stats
        )

    async def get_comparison_results(
        self,
        analysis_batch_id: str
    ) -> ComparisonAnalysisResponse:
        """
        获取对比分析结果。重点是管控策略间的对比。

        数据来源：
        - summary.xml （必须）: 提取 trip_count, avg_speed, congestion_ratio
        - edgedata.xml （可选）: 提取路段级别数据
        """
        batch = await self._get_analysis_batch(analysis_batch_id)
        simulations = await self._get_analyzed_simulations(analysis_batch_id)

        # 1. 从 summary.xml 解析基础指标
        for sim in simulations:
            sim.metrics = await self._extract_summary_metrics(
                sim.simulation_id
            )  # trip_count, avg_speed, congestion_ratio

        # 2. 从 edgedata.xml 解析补充数据（仅当存在时）
        sims_with_edgedata = [s for s in simulations if s.has_edgedata]
        data_sources = {
            "total_with_summary": len(simulations),
            "total_with_edgedata": len(sims_with_edgedata),
            "edge_coverage": f"{len(sims_with_edgedata)/len(simulations)*100:.1f}%"
        }

        for sim in sims_with_edgedata:
            sim.edge_metrics = await self._extract_edgedata_metrics(
                sim.simulation_id
            )

        # 3. 按管控策略分组对比
        control_strategy_comparison = self._group_by_control_strategy(
            simulations
        )

        # 4. 计算统计数据
        comparison_summary = self._calculate_comparison_summary(simulations)
        simulations_comparison = self._rank_simulations(simulations)

        # 5. 生成智能洞察（包括管控策略效果、边界分析等）
        insights = self._generate_insights(
            simulations_comparison,
            control_strategy_comparison
        )

        return ComparisonAnalysisResponse(
            analysis_batch_id=analysis_batch_id,
            original_batch_id=batch.original_batch_id,
            timestamp=batch.created_at,
            analysis_config=batch.config,
            data_sources=data_sources,
            comparison_summary=comparison_summary,
            simulations_comparison=simulations_comparison,
            control_strategy_comparison=control_strategy_comparison,
            insights=insights
        )
```

**数据模型**:

```python
# Request 模型
class RunComparisonAnalysisRequest(BaseModel):
    batch_id: str  # event_sim_batch_xxx
    analysis_config: Dict = {
        "metrics": ["trip_count", "avg_speed", "congestion_ratio"],
        "reference_sim_id": Optional[str]
    }

class SummaryMetrics(BaseModel):
    """来自 summary.xml 的基础指标"""
    trip_count: int         # 总行程数
    avg_speed: float        # 平均速度 (km/h)
    congestion_ratio: float # 拥堵率 (0-1)

class EdgeMetrics(BaseModel):
    """来自 edgedata.xml 的边界路段指标（可选）"""
    congested_segments: int     # 拥堵路段数
    avg_segment_speed: float    # 平均路段速度 (km/h)
    max_segment_wait: float     # 最大路段等待时间 (s)
    # ... 其他路段指标

class AnalysisMetrics(BaseModel):
    """组合指标"""
    summary: SummaryMetrics
    edge_metrics: Optional[EdgeMetrics] = None  # 仅当有 edgedata.xml 时

class SimulationComparison(BaseModel):
    sim_id: str
    case_id: str
    control_strategy: str  # "no_control" | "strategy_A" | "actual_control" 等
    metrics: AnalysisMetrics
    rank: int
    delta_vs_best: float  # 与最佳的差异百分比
    delta_vs_avg: float   # 与平均值的差异百分比

class ControlStrategyMetrics(BaseModel):
    """按管控策略聚合的指标"""
    avg_speed: float
    congestion_ratio: float
    improvement_vs_no_control: Optional[str]  # "+6.9% speed, -28.9% congestion"

class ComparisonSummary(BaseModel):
    total_simulations: int
    best_performer: SimulationComparison
    worst_performer: SimulationComparison
    average_metrics: AnalysisMetrics

class AnalysisInsight(BaseModel):
    type: str  # "performance_gap", "strategy_recommendation", "edge_analysis"
    description: str
    simulations: List[str]
    recommendation: Optional[str]
    segments: Optional[List[str]] = None  # 仅在 edge_analysis 时出现
    note: Optional[str] = None

class DataSources(BaseModel):
    total_with_summary: int  # 有 summary.xml 的仿真数
    total_with_edgedata: int # 有 edgedata.xml 的仿真数
    edge_coverage: str       # "60%"

# Response 模型
class RunAnalysisResponse(BaseModel):
    analysis_batch_id: str
    total_simulations: int
    with_edgedata: int       # 有 edgedata.xml 的仿真数
    status: str              # "analysis_started"
    created_at: datetime

class AnalysisProgressResponse(BaseModel):
    analysis_batch_id: str
    total_simulations: int
    analyzed: int
    failed: int
    progress_percent: float
    status: str  # "in_progress", "completed"
    eta_completion: Optional[datetime]

class ComparisonAnalysisResponse(BaseModel):
    analysis_batch_id: str
    original_batch_id: str
    timestamp: datetime
    analysis_config: Dict
    data_sources: DataSources
    comparison_summary: ComparisonSummary
    simulations_comparison: List[SimulationComparison]
    control_strategy_comparison: Dict[str, ControlStrategyMetrics]
    insights: List[AnalysisInsight]
```

**影响**:
- ✅ 分析功能完全围绕事件仿真批次展开
- ✅ 清晰的对比分析逻辑（排名、差异、洞察）
- ✅ 支持实时进度追踪
- ✅ 删除不必要的通用分析接口
- ✅ 输出的分析报告直接支持决策（最佳/最差、改进建议）

---

#### 阶段 3: API 命名规范化 (半天)

**当前混乱**:

```
❌ /case/create_case/          ← 后缀斜杠
❌ /case/list_cases/           ← 后缀斜杠
✓ /case/{case_id}             ← 无斜杠
❌ /case/create-from-scenario  ← 连字符
❌ /case/quick-create-from-event
```

**统一规范**:

```python
# 统一规则: RESTful 风格，无后缀斜杠，使用连字符

# 案例管理
POST   /api/v1/case              # 创建案例
GET    /api/v1/case              # 列表
GET    /api/v1/case/{case_id}    # 获取详情
DELETE /api/v1/case/{case_id}    # 删除
POST   /api/v1/case/{case_id}/clone  # 克隆

# 事件场景创建（新）
POST   /api/v1/case/from-event-scenario  # 从场景创建

# 事件仿真管理
POST   /api/v1/event-simulation/batch-start          # 批量启动事件仿真
GET    /api/v1/event-simulation/batch-progress/{id}  # 批量进度监控
GET    /api/v1/event-simulation/batch-results/{id}   # 批量结果

# 事件仿真对比分析
POST   /api/v1/event-simulation-analysis/run-comparison   # 启动对比分析
GET    /api/v1/event-simulation-analysis/progress/{id}    # 分析进度
GET    /api/v1/event-simulation-analysis/results/{id}     # 分析结果
```

---

## 详细的删除清单

### 应该删除的代码

#### 1. 重复的 API 端点

```python
# api/routes/case_routes.py

❌ @router.post("/create-from-scenario")
   理由: 与 /quick-create-from-event 重复
   替代: 合并到 /from-event-scenario

❌ @router.post("/quick-create-from-event")
   理由: 与 /create-from-scenario 调用同一函数
   替代: 合并到 /from-event-scenario

❌ @router.post("/create-case-with-simulation")
   理由: 功能可由 /from-event-scenario 的参数实现
   替代: auto_start_simulation 参数
```

#### 2. 内部重复方法

```python
# api/services/case_service.py

❌ _get_or_create_event_case()
   理由: 与 create_case_from_event_scenario() 重复逻辑
   替代: 内联到 create_case_from_event_scenario()

❌ _get_or_create_event_case_with_lock()
   理由: 变体太多，单一职责原则违反
   替代: 锁定逻辑内含在 create_case_from_event_scenario()

❌ create_case_from_scenario()
   理由: 与 quick_create_case_from_event() 功能相同
   替代: 只保留 create_case_from_event_scenario()

❌ quick_create_case_from_event()
   理由: 与 create_case_from_scenario() 重复，名称不清
   替代: 合并到 create_case_from_event_scenario()
```

#### 3. 过时的通用分析接口

```python
# api/routes/analysis_routes.py

❌ @router.post("/analyze_accuracy/")
   理由: 面向OD-Gantry精度分析，与事件仿真对比分析无关
   替代: /api/v1/event-simulation-analysis/run-comparison

❌ @router.get("/analysis_history/{case_id}")
   理由: 与事件工作流不匹配，改为批次级别的分析进度
   替代: /api/v1/event-simulation-analysis/progress/{analysis_batch_id}

❌ @router.get("/analysis_mapping/{case_id}")
   理由: 信息可包含在对比分析结果中
   替代: /api/v1/event-simulation-analysis/results/{analysis_batch_id}

❌ @router.get("/analysis_results/{case_id}")
   理由: 改为批次级别的对比分析结果
   替代: /api/v1/event-simulation-analysis/results/{analysis_batch_id}
```

#### 4. 过时的单仿真接口

```python
# api/routes/simulation_routes.py

❌ @router.post("/")
   理由: 创建仿真现在由 /case/create-from-event-scenario 自动处理
   替代: 无需显式创建接口

❌ @router.get("/")
   理由: 单仿真列表功能不再需要，改为事件批量管理
   替代: /api/v1/event-simulation/batch-progress

❌ @router.get("/{sim_id}")
   理由: 单仿真详情查询改为批量查询
   替代: /api/v1/event-simulation/batch-progress/{batch_id}

❌ @router.post("/{sim_id}/start")
   理由: 单仿真启动改为批量启动
   替代: /api/v1/event-simulation/batch-start
```

---

## 应该保留的代码

### 核心工作流入口

```python
✅ POST /api/v1/case                 # 基础创建（OD工作流）
✅ POST /api/v1/case/from-event-scenario  # 场景创建（Event工作流，自动创建仿真）
✅ GET  /api/v1/case                 # 列表（with filtering）
✅ GET  /api/v1/case/{case_id}       # 详情
✅ DELETE /api/v1/case/{case_id}     # 删除
✅ POST /api/v1/case/{case_id}/clone # 克隆

✅ POST /api/v1/event-simulation/batch-start      # 批量启动事件仿真
✅ GET  /api/v1/event-simulation/batch-progress/{batch_id}    # 批量进度监控
✅ GET  /api/v1/event-simulation/batch-results/{batch_id}     # 批量结果

✅ POST /api/v1/event-simulation-analysis/run-comparison      # 启动对比分析
✅ GET  /api/v1/event-simulation-analysis/progress/{batch_id} # 分析进度
✅ GET  /api/v1/event-simulation-analysis/results/{batch_id}  # 分析结果
```

### 核心服务方法

```python
# CaseService - 保留
✅ create_case(request)
✅ list_cases(page, page_size, status, search)
✅ get_case(case_id)
✅ delete_case(case_id)
✅ clone_case(case_id, request)

# CaseService - 保留但重构
✅ create_case_from_event_scenario(request)  # 替代5个旧方法
                                              # 总是创建案例和仿真
                                              # 返回: case_id, simulation_id, case_type

# EventSimulationService - 新增
✅ batch_start_event_simulations()           # 批量启动事件仿真
✅ get_batch_progress()                      # 获取批次进度
✅ get_batch_results()                       # 获取批次结果

# EventSimulationAnalysisService - 新增
✅ run_comparison_analysis()                 # 启动批次对比分析
✅ get_analysis_progress()                   # 获取分析进度
✅ get_comparison_results()                  # 获取对比分析结果

# AnalysisResultsService - 重构
✅ get_comparison_report()                   # 重点用于事件仿真间的对比
                                              # （移除OD-Gantry精度分析逻辑）
```

---

## 迁移计划

### 兼容层（可选，用于过渡）

如果需要保持向后兼容（可选），可创建兼容层：

```python
# api/routes/case_routes_legacy.py (可选兼容层)

@router.post("/create-from-scenario")  # 已弃用
async def create_from_scenario_legacy(request):
    """已弃用，请使用 POST /case/from-event-scenario"""
    import warnings
    warnings.warn("This endpoint is deprecated", DeprecationWarning)
    return await create_case(request, from_event_scenario=True)

@router.post("/quick-create-from-event")  # 已弃用
async def quick_create_legacy(request):
    """已弃用，请使用 POST /case/from-event-scenario"""
    return await create_case(request, from_event_scenario=True)
```

**优点**: 不会破坏现有客户端
**缺点**: 增加维护负担

**建议**: 如果前端已更新，直接删除（不需要兼容层）

---

## 清理前的检查清单

在执行清理前，验证：

- [ ] 所有前端调用已更新为新的统一接口
- [ ] 所有测试已更新为新的接口
- [ ] 所有文档已更新为新的接口
- [ ] 已备份旧的API定义（存档）
- [ ] 已通知所有使用该API的人

---

## 预期改进

### 清理前 ❌

```
案例创建接口数:         4个
仿真接口:              混杂（单独创建、启动、查询）
分析接口:              不完整（3个框架）
命名风格一致性:        低
代码重复度:            高（5个方法做同一件事）
事件仿真管理能力:      无（没有批量启动和进度追踪）
新开发者理解难度:      高（4个接口都做什么？）
维护成本:              高（改一个特性要改多个地方）
```

### 清理后 ✅

```
案例创建接口数:         2个（清晰分工）
仿真接口:              专注事件（批量启动 + 进度监控）
分析接口:              完整（3个，数据驱动的对比分析）
  ├─ 启动对比分析（数据来源：summary.xml + edgedata.xml）
  ├─ 分析进度监控
  └─ 对比分析结果（排名、策略对比、洞察建议）

命名风格一致性:        高（RESTful统一）
代码重复度:            低（单一职责）

事件仿真管理能力:      完整（批量启动、实时进度、结果查询）
事件仿真分析能力:      ⭐ 完整且数据驱动
  ├─ 数据来源清晰：summary.xml（必有）+ edgedata.xml（智能判断）
  ├─ 对比场景完整：无管控 vs 不同管控 vs 实际管控
  ├─ 指标体系完整：交通流量、速度、拥堵程度等
  └─ 输出质量高：排名、策略对比、边界分析、改进建议

仿真配置约束:         ⭐ 明确的顺序要求
  ├─ 必须先生成 rou.xml
  └─ 再生成 sumocfg.xml（参考 rou.xml）

新开发者理解难度:      低（清晰的事件工作流）
维护成本:              低（单一真实来源）
```

---

## 时间预估

| 任务 | 工作量 | 影响范围 |
|------|--------|---------|
| 阶段1: 案例接口整合 | 1天 | 后端路由 + 服务 + 前端 |
| 阶段1.5: 事件批量仿真管理 | 1天 | 新增服务 + 路由 + 前端 |
| 阶段2: 分析功能完成 | 2-3天 | 后端服务 + 路由 |
| 阶段3: API命名规范化 | 半天 | 后端路由 + 文档 |
| **总计** | **3.5-4.5天** | **所有层** |

---

## 结论

**核心问题**: 多个开发阶段的 API 设计叠加，导致接口重复、命名混乱、职责不清

**根本原因**: 缺乏统一的工作流 orchestration 层，导致每个阶段都试图在 CaseService 中添加新方法

**清理效果**:
- 案例创建接口 -50% (4→2)
- 仿真接口优化 (删除单仿真，保留批量事件仿真)
- 分析接口专焦化 (从通用→事件仿真对比分析)
- 代码重复度 -70%
- 命名规范化 100%
- 新开发者上手时间 -60%

**新增功能**:
- 事件仿真批量管理（批量启动、实时进度、结果查询）
- 事件仿真对比分析（数据驱动、管控策略对比、性能排名、洞察建议）

**数据驱动的改进**:
- ✅ 数据来源明确：summary.xml（必有）+ edgedata.xml（智能判断）
- ✅ 对比场景完整：
  - 事件无管控 vs 有不同管控
  - 事件实际管控 vs 不同管控方案
- ✅ 指标体系完整：trip_count、avg_speed、congestion_ratio、edge级数据等
- ✅ 不涉及tripinfo（简化数据处理）

**技术约束明确**:
- ✅ rou.xml → sumocfg.xml 的顺序要求（防止配置错误）
- ✅ edgedata 智能判断（根据事件+管控是否涉及edge）

**架构改进**:
```
清理前 (混乱):
  创建接口: create_case / quick_create_case / create_case_from_scenario / create_case_with_simulation
  仿真接口: POST /api/v1/simulation (单仿真)
  分析接口: /analyze_accuracy / /analysis_history / /analysis_mapping (通用、数据不驱动)

清理后 (清晰 + 数据驱动):
  创建: case + scenario (自动创建仿真，智能判断edgedata)
       ↓
  仿真: event-simulation/batch-* (批量管理)
       ↓
  分析: event-simulation-analysis/* (数据驱动对比分析)
       ├─ 数据来源：summary.xml + edgedata.xml
       ├─ 对比对象：管控策略
       └─ 输出：排名、策略对比、改进建议
```

**建议优先级**: P0 - 这个清理会显著提高代码质量，应该立即执行

