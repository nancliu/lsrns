# 从场景库到Case仿真系统实施建议

**文档日期**: 2025-11-11
**状态**: 规划中
**当前进度**: 阶段1完成 (场景库生成)

---

## 📊 当前状态分析

### ✅ 已完成工作
- **场景库生成**: 443个成功场景 + 2个修复场景 = 445个可用场景
- **场景索引**: scenario_index.json 完整记录
- **事件类型正规化**: 支持6种标准事件类型
- **分层仿真控制**: VSS、TEC、DHS三种管控策略
- **现有API**: prepare/start 二步仿真流程已实现

### ⚠️ 缺失功能
- 从场景库创建case的服务层
- 场景到case的配置映射逻辑
- 批量场景场景仿真执行
- 场景仿真结果的分析和对比

---

## 🎯 三阶段实施建议

### 阶段1: 场景-Case映射层 (低风险，高价值)
**预计工作量**: 3-4天
**优先级**: ⭐⭐⭐⭐⭐ 最高

#### 1.1 创建场景数据模型
**文件**: `api/models/entities/scenario.py`
```python
# 新增模型
- ScenarioRef: 场景引用 (event_id, strategy, variant)
- ScenarioMeta: 场景元数据 (事件类型、位置、时间)
- ScenarioConfig: 仿真配置 (时长、OD矩阵、额外文件)
- EventScenarioCase: 从场景创建的Case
```

**关键决策**:
- Case和Scenario的关系：多对多(1个scenario可关联多个case)
- metadata字段：添加 `source_scenario_id` 追溯场景来源
- 配置继承：Case配置 = 场景配置 + 用户自定义

#### 1.2 创建场景Service服务
**文件**: `api/services/scenario_service.py` (新增)
```python
class ScenarioService(BaseService):
    # 核心功能
    - list_scenarios()           # 列出所有可用场景
    - get_scenario_detail()      # 获取场景详情
    - get_scenario_by_event()    # 按事件ID查询场景
    - create_case_from_scenario() # 从场景创建case(关键)
```

**实现细节**:
```python
async def create_case_from_scenario(self, event_id: str, variant: str) -> Dict:
    """
    从场景创建case，包含所有必要的配置

    步骤:
    1. 加载场景定义 (event_description.json)
    2. 加载场景配置 (control_strategy_config.json)
    3. 创建case目录结构
    4. 复制/生成仿真配置
    5. 记录场景来源信息
    """
```

#### 1.3 添加API端点
**文件**: `api/routes/scenario_routes.py` (新增)

```http
GET  /api/v1/scenario/list              # 列出可用场景
GET  /api/v1/scenario/{event_id}        # 获取事件的所有场景
POST /api/v1/scenario/create-case       # 从场景创建case
  {
    "event_id": "11554",
    "variant": "vss",
    "case_name": "可选自定义名称",
    "config_overrides": {...}            # 可选：覆盖配置
  }
```

**Response**:
```json
{
  "case_id": "case_20251111_001",
  "scenario_id": "11554_vss",
  "case_dir": "cases/case_20251111_001",
  "simulation_ready": true,
  "metadata": {...}
}
```

#### 1.4 依赖项检查
- ✅ 已有：DirectoryManager, MetadataManager
- ✅ 已有：case_service.create_case()
- ✅ 已有：ScenarioGenerator (用于生成)
- 需要：scenario_index.json 读取工具

---

### 阶段2: 批量仿真执行 (中等风险，高价值)
**预计工作量**: 2-3天
**优先级**: ⭐⭐⭐⭐ 很高
**依赖**: 阶段1完成

#### 2.1 增强模拟服务
**文件**: `api/services/simulation_service.py` (扩展)

```python
# 新增能力
async def batch_simulate_scenarios(
    event_ids: List[str],
    variants: List[str] = ["no_control", "vss", "tec"],
    parallel_count: int = 4
) -> BatchSimulationResult:
    """
    批量运行多个场景的仿真

    特点:
    - 并行执行 (可配置并发数)
    - 自动监控进度
    - 失败重试机制
    - 结果汇总
    """
```

#### 2.2 创建批量仿真API
**文件**: `api/routes/batch_routes.py` (新增)

```http
POST /api/v1/batch-scenarios/simulate
  {
    "scenario_selection": {
      "event_ids": ["11554", "12522"],
      "variants": ["no_control", "vss"],
      "event_types": ["weather", "breakdown"]  # 或按类型选择
    },
    "execution": {
      "parallel_workers": 4,
      "timeout_minutes": 120
    }
  }

GET /api/v1/batch-scenarios/status/{batch_id}
GET /api/v1/batch-scenarios/results/{batch_id}
```

#### 2.3 进度追踪
- 使用现有的 `SimulationTracker`
- 扩展支持批量任务
- 记录每个scenario的执行状态

---

### 阶段3: 结果分析与对比 (低风险，中价值)
**预计工作量**: 3-5天
**优先级**: ⭐⭐⭐ 中等
**依赖**: 阶段1、2完成

#### 3.1 场景对比分析
**文件**: `api/services/scenario_analysis_service.py` (新增)

```python
class ScenarioAnalysisService:
    # 核心分析
    - compare_baseline_vs_control()     # 场景无管控 vs 有管控对比
    - rank_strategies_for_event()       # 为单个事件排名管控策略
    - event_impact_summary()            # 事件影响评估
    - strategy_effectiveness_metric()   # 管控策略有效性评分
```

#### 3.2 分析维度
```
层级1 (基础):
  - 流量对比 (车辆数、平均速度)
  - 时间对比 (拥堵缓解时间)

层级2 (深度):
  - 机理分析 (OD流量变化、速度时序)
  - EdgeData分析 (路段时空演变)

层级3 (决策):
  - 多准则排名 (effectiveness, coverage, efficiency)
  - 最优策略推荐
```

#### 3.3 分析API
```http
GET /api/v1/scenario-analysis/compare/{event_id}
  # 返回该事件所有场景的对比结果

GET /api/v1/scenario-analysis/strategy-ranking/{event_id}
  # 为单个事件的管控策略排名

POST /api/v1/scenario-analysis/batch-report
  # 生成一批场景的汇总报告
```

---

## 📋 实施优先级清单

### 🔴 第一优先(必做)
```
□ 场景Service基础版本 (create_case_from_scenario)
□ 场景列表API (GET /api/v1/scenario/list)
□ 从场景创建case的API (POST /api/v1/scenario/create-case)
□ 场景索引加载工具
□ 前端: 场景浏览→快速创建Case功能
```
**预计时间**: 2-3天

### 🟡 第二优先(推荐)
```
□ 批量仿真执行 (batch_simulate_scenarios)
□ 批量仿真监控API
□ 仿真结果汇总存储
□ 前端: 批量操作UI
```
**预计时间**: 2天

### 🟢 第三优先(后续)
```
□ 场景对比分析 (compare_baseline_vs_control)
□ 策略效果评分
□ 多准则排名
□ 分析报告生成
□ 前端: 分析可视化页面
```
**预计时间**: 3-5天

---

## 🏗️ 技术架构建议

### 目录结构调整
```
api/
├── services/
│   ├── case_service.py           (现有，保留)
│   ├── simulation_service.py      (现有，扩展)
│   ├── scenario_service.py        (新增) ⭐
│   ├── scenario_analysis_service.py (新增，后期)
│   └── batch_service.py           (新增，后期)
│
├── routes/
│   ├── case_routes.py             (现有)
│   ├── simulation_routes.py        (现有，扩展)
│   ├── scenario_routes.py          (新增) ⭐
│   └── batch_routes.py            (新增，后期)
│
└── models/
    ├── entities/
    │   ├── case.py               (现有)
    │   └── scenario.py           (新增) ⭐
    └── requests/
        └── scenario_requests.py   (新增) ⭐
```

### 数据流架构
```
output/scenarios/                  (只读 - 场景库)
    ├── 06_weather/
    │   ├── scenario_11554_no_control/
    │   ├── scenario_11554_vss/
    │   └── scenario_11554_tec/
    └── scenario_index.json

    ↓ ScenarioService.create_case_from_scenario()

cases/                             (可写 - 执行库)
├── case_{id}_1/
│   ├── metadata.json              (追溯源场景)
│   ├── simulations/
│   │   ├── scenario_11554_no_control/
│   │   │   ├── simulation.sumocfg
│   │   │   ├── results/
│   │   │   └── analysis/
│   │   ├── scenario_11554_vss/
│   │   └── scenario_11554_tec/
│   └── analysis/
│       ├── scenario_comparison.json
│       └── ranking_report.json
```

### 关键类设计
```python
# scenario.py
class ScenarioReference:
    event_id: str
    event_type: str
    variant: str  # "no_control", "vss", "tec"

class ScenarioMetadata:
    road: str
    direction: str
    mileage: str
    duration_hours: float

class ScenarioFromLibrary:
    # 从场景库加载的完整场景对象
    @staticmethod
    async def from_event_id(event_id: str, variant: str) -> 'ScenarioFromLibrary'

    def to_case_config(self) -> Dict:
        # 转换为case配置格式
```

---

## ⚙️ 配置管理建议

### 场景配置继承链
```
1. 场景定义 (output/scenarios/*/event_description.json)
   ↓
2. 场景配置 (output/scenarios/*/control_strategy_config.json)
   ↓
3. Case配置 (cases/{case_id}/metadata.json) ← 用户可修改
   ↓
4. 仿真配置 (cases/{case_id}/simulations/{scenario_id}/simulation.sumocfg)
```

### 推荐的配置覆盖策略
```python
# 不允许覆盖的字段(场景级)
IMMUTABLE_FIELDS = [
    'event_id', 'event_type', 'location', 'time',
    'affected_edges', 'control_strategy_type'
]

# 可选覆盖的字段(case级)
OVERRIDABLE_FIELDS = [
    'simulation_duration',      # 仿真时长
    'num_vehicles',             # 车辆数量
    'output_config',            # 输出格式
    'seed',                      # 随机种子
    'batch_size'                # 批量大小
]
```

---

## 🧪 测试策略

### 单元测试优先级
```
高优先:
□ ScenarioService.create_case_from_scenario()
□ 场景索引加载和查询
□ Case metadata正确生成

中优先:
□ 批量仿真执行逻辑
□ 进度追踪
□ 结果汇总

低优先:
□ 分析算法细节
```

### 集成测试
```
场景1: 快速路径
  □ 加载场景 → 创建case → 仿真 → 获取结果 (10分钟)

场景2: 批量路径
  □ 批量选择场景 → 批量创建case → 并行仿真 (30分钟)

场景3: 对比路径
  □ 同一事件多策略 → 对比分析 → 排名报告 (20分钟)
```

---

## 📈 风险评估与缓解

| 风险 | 等级 | 缓解方案 |
|------|------|--------|
| SUMO配置差异 | 中 | 使用现有的scenario_sumocfg_generator |
| 并发冲突 | 低 | 使用case_id隔离，文件级锁定 |
| 性能瓶颈 | 中 | 可调配worker数，缓存场景索引 |
| 数据一致性 | 低 | 完整的metadata追踪，版本控制 |

---

## 💡 实施建议摘要

### 快速启动(周1)
**只做必做工作**：
1. 创建ScenarioService + 基础API
2. 实现create_case_from_scenario()
3. 添加前端快速创建按钮
4. **目标**: 能从UI点击"创建仿真"自动转换场景→case

### 迭代改进(周2)
1. 添加批量操作
2. 优化进度追踪
3. 完善错误处理

### 知识沉淀(周3-4)
1. 分析和对比功能
2. 排名和报告生成
3. 文档完善

### 关键成功指标
- ✅ 从任何场景可一键创建可仿真的case
- ✅ 批量仿真支持4+并发执行
- ✅ 提供场景间对比分析
- ✅ 自动生成决策报告

---

## 📞 决策点需求

在开始实施前，建议确认：

1. **Case定价**:
   - 是否保留case的所有历史仿真？
   - 还是case和scenario强绑定(1:1)?

2. **配置灵活性**:
   - 用户能否修改场景的管控策略参数？
   - 如果能修改，如何追踪变更？

3. **分析深度**:
   - 仅需基础对比(流量、速度)？
   - 还是需要机理分析(OD变化)？

4. **前端优先级**:
   - 优先完善场景浏览器？
   - 还是优先实现批量操作？

5. **数据存储**:
   - 是否保留所有批量仿真的临时case？
   - 还是仅保留最终分析报告？

