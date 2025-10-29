# 设计文档：交通管控方案管理与批量优化

**变更ID**: implement-plan-management-and-batch-optimization
**版本**: 1.0
**日期**: 2025-10-25

## 1. 架构概览

### 1.1 系统架构

本功能遵循项目的两层模块化架构：

```
┌─────────────────────────────────────────────────────────┐
│                   API Layer (api/)                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Routes (HTTP Interface)                          │  │
│  │  - control_plan_routes.py                         │  │
│  │  - batch_optimization_routes.py                   │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   ↓                                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Services (Business Logic)                        │  │
│  │  - control_plan_service.py                        │  │
│  │  - batch_optimization_service.py                  │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   ↓                                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Models (Data Validation)                         │  │
│  │  - entities/plan.py (enhanced)                    │  │
│  │  - requests/plan_request.py                       │  │
│  │  - responses/plan_response.py                     │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│                 Shared Layer (shared/)                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  control_tools/                                   │  │
│  │  - plan_file_manager.py (新增)                    │  │
│  │  - batch_simulation_scheduler.py (新增)           │  │
│  │  - plan_validator.py (新增)                       │  │
│  │  - additional_generator.py (增强)                 │  │
│  │  - strategy_file_manager.py (增强：引用计数)      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 1.2 数据流

```
用户创建方案
    ↓
API: POST /api/v1/control/plans/
    ↓
Service: control_plan_service.create_plan()
    ↓
1. 验证所有strategy_ids存在
2. 加载策略实例
3. 生成方案ID (plan_YYYYMMDD_HHMMSS_xxxxx)
4. 调用additional_generator.generate_plan_additional()
5. 保存方案元数据 (plan_metadata.json)
6. 保存策略引用 (strategy_refs.json)
7. 保存control.add.xml
8. 更新plans_index.json
9. 更新策略引用计数
    ↓
返回方案详情
```

```
批量优化仿真流程
    ↓
API: POST /api/v1/control/optimization/batch
    ↓
Service: batch_optimization_service.create_batch()
    ↓
1. 验证case_id存在
2. 验证所有plan_ids存在
3. 确保包含基准方案
4. 为每个plan创建3次仿真任务
5. 生成batch_id
6. 创建批次目录 cases/{case_id}/simulations/plan_opti/{batch_id}/
    ↓
启动并行仿真调度器
    ↓
For each (plan, seed) in tasks:
    1. 创建仿真目录 {batch_id}/{plan_id}/sim_{seed}/
    2. 复制case配置文件
    3. 复制plan的control.add.xml
    4. 调用simulation_service.prepare_simulation()
    5. 更新sumocfg添加--seed参数
    6. 调用simulation_service.start_simulation()
    7. 更新批次进度
    ↓
所有仿真完成
    ↓
生成批次汇总报告
```

## 2. 核心组件设计

### 2.1 Plan实体模型（增强）

```python
class Plan(BaseModel):
    """控制方案模型"""

    plan_id: str  # 格式: plan_YYYYMMDD_HHMMSS_xxxxx
    plan_name: str  # 用户自定义名称
    description: Optional[str]  # 详细描述
    strategy_ids: List[str]  # 引用的策略ID列表（可为空=基准方案）

    # 新增字段
    tags: List[str] = []  # 标签分类
    target_scenario: Optional[str]  # 目标场景（如"早高峰"）
    expected_effects: Optional[Dict[str, str]]  # 预期效果

    additional_file_path: Optional[str]  # control.add.xml路径

    created_at: datetime
    updated_at: datetime

    # 计算属性
    @property
    def is_baseline(self) -> bool:
        return len(self.strategy_ids) == 0

    @property
    def strategy_count(self) -> int:
        return len(self.strategy_ids)
```

### 2.2 方案文件管理器

**文件**: `shared/control_tools/plan_file_manager.py`

**职责**:
- 管理方案文件的创建、读取、更新、删除
- 维护方案索引 (`plans_index.json`)
- 处理方案目录结构

**目录结构**:
```
control_data/plans/
├── plans_index.json           # 所有方案索引
├── baseline_plan/             # 全局基准方案
│   ├── plan_metadata.json
│   ├── strategy_refs.json     # 空数组[]
│   └── control.add.xml        # 空<additional/>
├── plan_20251025_140530_a1b2c/
│   ├── plan_metadata.json
│   ├── strategy_refs.json     # ["strategy_001", "strategy_002"]
│   └── control.add.xml        # 生成的SUMO配置
└── plan_20251025_141200_d3e4f/
    ├── plan_metadata.json
    ├── strategy_refs.json
    └── control.add.xml
```

**关键方法**:
```python
def create_plan(plan_data: dict) -> str:
    """创建方案，返回plan_id"""

def get_plan(plan_id: str) -> dict:
    """获取方案详情"""

def update_plan(plan_id: str, updates: dict) -> None:
    """更新方案元数据"""

def delete_plan(plan_id: str) -> None:
    """删除方案及其文件"""

def list_plans(filters: dict = None) -> list:
    """列出所有方案（支持过滤）"""

def get_plan_strategies(plan_id: str) -> list:
    """获取方案包含的策略实例列表"""

def regenerate_plan_xml(plan_id: str) -> None:
    """重新生成方案的control.add.xml"""
```

### 2.3 批量仿真调度器

**文件**: `shared/control_tools/batch_simulation_scheduler.py`

**职责**:
- 管理多方案×多随机种子的并行仿真
- 动态控制并发数（基于CPU线程数，默认为线程数×75%，支持40-60个任务并发）
- 跟踪进度和状态

**关键数据结构**:
```python
class BatchSimulationTask:
    task_id: str
    plan_id: str
    plan_name: str
    seed: int
    status: str  # "pending", "running", "completed", "failed"
    simulation_id: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]

class BatchSimulation:
    batch_id: str
    case_id: str
    plan_ids: List[str]
    num_seeds: int = 3  # 每个方案的随机种子数
    base_seed: int = 66  # 起始种子

    tasks: List[BatchSimulationTask]
    status: str  # "pending", "running", "completed", "failed"
    progress: float  # 0.0-1.0

    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
```

**仿真结果目录结构**:
```
cases/{case_id}/simulations/plan_opti/
└── batch_20251025_140530/
    ├── batch_metadata.json        # 批次元数据
    ├── batch_progress.json        # 实时进度
    ├── baseline_plan/
    │   ├── sim_66/
    │   │   ├── simulation.sumocfg
    │   │   ├── control.add.xml    # 复制自方案
    │   │   ├── summary.xml
    │   │   ├── tripinfo.xml
    │   │   └── simulation_metadata.json
    │   ├── sim_67/
    │   └── sim_68/
    ├── plan_20251025_140530_a1b2c/
    │   ├── sim_66/
    │   ├── sim_67/
    │   └── sim_68/
    └── plan_20251025_141200_d3e4f/
        ├── sim_66/
        ├── sim_67/
        └── sim_68/
```

**关键方法**:
```python
async def create_batch(
    case_id: str,
    plan_ids: List[str],
    num_seeds: int = 3,
    base_seed: int = 66
) -> str:
    """创建批量仿真批次"""

async def start_batch(batch_id: str) -> None:
    """启动批量仿真（异步）"""

async def _run_task(task: BatchSimulationTask) -> None:
    """运行单个仿真任务"""

def get_batch_progress(batch_id: str) -> dict:
    """获取批次进度"""

def cancel_batch(batch_id: str) -> None:
    """取消批量仿真"""
```

### 2.4 方案验证器

**文件**: `shared/control_tools/plan_validator.py`

**职责**:
- 验证方案的策略组合合理性
- 检测潜在冲突和问题
- 返回警告信息（非阻塞）

**验证规则**:

1. **空间冲突检测**
   - 检查是否有多个策略控制相同的edge/lane
   - 警告：不同策略类型控制相同对象可能冲突

2. **时间协调检查**
   - 检查VSS和DHS的时间段协调性
   - 警告：DHS开放前应有VSS提前降速

3. **策略类型兼容性**
   - 检查VSS+DHS+TEC组合的合理性
   - 警告：缺少上游限速可能导致急刹车

**方法签名**:
```python
def validate_plan(plan_data: dict, strategies: List[dict]) -> ValidationResult:
    """
    验证方案配置

    Returns:
        ValidationResult(
            is_valid: bool,  # 总是True（警告模式）
            warnings: List[Warning],  # 警告列表
            suggestions: List[str]  # 优化建议
        )
    """
```

### 2.5 Additional生成器增强

**文件**: `shared/control_tools/additional_generator.py`（增强）

**新增功能**:
```python
def generate_plan_additional(
    plan_id: str,
    plan_name: str,
    strategies: List[dict]
) -> str:
    """
    生成方案级别的control.add.xml

    合并多个策略的XML元素，按类型排序：
    1. VSS策略组
    2. DHS策略组
    3. TEC策略组

    Args:
        plan_id: 方案ID
        plan_name: 方案名称
        strategies: 策略实例列表（已加载完整配置）

    Returns:
        格式化的XML字符串
    """
```

**XML输出格式**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<additional>
    <!-- 方案: {plan_name} ({plan_id}) -->
    <!-- 生成时间: {datetime.now()} -->

    <!-- ==================== VSS策略组 ==================== -->
    <!-- 策略: strategy_001 - K10-K15路段限速80km/h -->
    <variableSpeedSign id="strategy_001" lanes="...">
        ...
    </variableSpeedSign>

    <!-- ==================== DHS策略组 ==================== -->
    <!-- 策略: strategy_002 - K15-K20应急车道开放 -->
    <rerouter id="strategy_002" edges="...">
        ...
    </rerouter>

    <!-- ==================== TEC策略组 ==================== -->
    <!-- 策略: strategy_003 - K18入口流量控制 -->
    <calibrator id="strategy_003" edge="...">
        ...
    </calibrator>
</additional>
```

## 3. API端点设计

### 3.1 方案管理端点

#### POST /api/v1/control/plans/
创建新方案

**请求体**:
```json
{
  "plan_name": "早高峰综合管控方案A",
  "description": "缓解K10-K15路段早高峰拥堵",
  "strategy_ids": ["strategy_001", "strategy_002", "strategy_003"],
  "tags": ["早高峰", "综合管控"],
  "target_scenario": "工作日早高峰(7:00-9:00)",
  "expected_effects": {
    "reduce_congestion": "降低瓶颈路段拥堵20%",
    "improve_speed": "提升平均速度15%"
  }
}
```

**响应**:
```json
{
  "plan_id": "plan_20251025_140530_a1b2c",
  "plan_name": "早高峰综合管控方案A",
  "description": "...",
  "strategy_ids": ["strategy_001", "strategy_002", "strategy_003"],
  "strategy_count": 3,
  "additional_file_path": "control_data/plans/plan_20251025_140530_a1b2c/control.add.xml",
  "validation": {
    "is_valid": true,
    "warnings": [
      {
        "type": "timing_coordination",
        "message": "建议VSS策略提前5分钟生效"
      }
    ]
  },
  "created_at": "2025-10-25T14:05:30",
  "updated_at": "2025-10-25T14:05:30"
}
```

#### GET /api/v1/control/plans/
列出所有方案

**查询参数**:
- `tags`: 标签过滤（逗号分隔）
- `target_scenario`: 场景过滤
- `include_baseline`: 是否包含基准方案（默认true）

**响应**:
```json
{
  "plans": [
    {
      "plan_id": "baseline_plan",
      "plan_name": "基准方案（无管控）",
      "is_baseline": true,
      "strategy_count": 0,
      "created_at": "2025-10-25T10:00:00"
    },
    {
      "plan_id": "plan_20251025_140530_a1b2c",
      "plan_name": "早高峰综合管控方案A",
      "is_baseline": false,
      "strategy_count": 3,
      "tags": ["早高峰", "综合管控"],
      "created_at": "2025-10-25T14:05:30"
    }
  ],
  "total": 2
}
```

#### GET /api/v1/control/plans/{plan_id}
获取方案详情

**响应**:
```json
{
  "plan_id": "plan_20251025_140530_a1b2c",
  "plan_name": "早高峰综合管控方案A",
  "description": "...",
  "strategy_ids": ["strategy_001", "strategy_002", "strategy_003"],
  "strategies": [
    {
      "strategy_id": "strategy_001",
      "strategy_name": "K10-K15路段限速80km/h",
      "strategy_type": "VSS",
      "template_id": "vss_moderate"
    },
    ...
  ],
  "tags": ["早高峰", "综合管控"],
  "target_scenario": "工作日早高峰(7:00-9:00)",
  "expected_effects": {...},
  "additional_file_path": "...",
  "created_at": "...",
  "updated_at": "..."
}
```

#### PUT /api/v1/control/plans/{plan_id}
更新方案

**请求体**: 同创建，所有字段可选

**行为**:
- 如果`strategy_ids`变化，自动重新生成`control.add.xml`
- 更新`updated_at`时间戳

#### DELETE /api/v1/control/plans/{plan_id}
删除方案

**限制**:
- 不能删除`baseline_plan`
- 删除前检查是否被批量仿真引用（警告，但允许删除）

#### POST /api/v1/control/plans/{plan_id}/generate_additional
手动重新生成control.add.xml

**使用场景**:
- 策略更新后手动触发重新生成
- 修复损坏的XML文件

#### POST /api/v1/control/plans/{plan_id}/validate
验证方案

**响应**:
```json
{
  "is_valid": true,
  "warnings": [
    {
      "type": "timing_coordination",
      "severity": "medium",
      "message": "建议VSS策略strategy_001提前5分钟生效",
      "suggestion": "将time_begin从25200改为24900"
    }
  ],
  "suggestions": [
    "考虑添加上游预警限速策略"
  ]
}
```

#### POST /api/v1/control/plans/{plan_id}/preview
预览方案效果

**响应**:
```json
{
  "plan_id": "plan_20251025_140530_a1b2c",
  "summary": {
    "total_strategies": 3,
    "strategy_types": {
      "VSS": 1,
      "DHS": 1,
      "TEC": 1
    },
    "affected_edges": ["edge_800", "edge_801", ...],
    "affected_edge_count": 10,
    "time_range": {
      "earliest": 24900,  # 6:55
      "latest": 32400     # 9:00
    }
  },
  "strategies": [
    {
      "strategy_id": "strategy_001",
      "strategy_name": "...",
      "strategy_type": "VSS",
      "affected_objects": ["edge_800_0", "edge_800_1", ...],
      "active_periods": [[24900, 32400]]
    },
    ...
  ],
  "xml_preview": "<?xml version=\"1.0\"...>"
}
```

### 3.2 批量优化端点

#### POST /api/v1/control/optimization/batch
创建批量仿真批次

**请求体**:
```json
{
  "case_id": "case_20251025_001",
  "plan_ids": [
    "baseline_plan",
    "plan_20251025_140530_a1b2c",
    "plan_20251025_141200_d3e4f"
  ],
  "num_seeds": 3,
  "base_seed": 66,
  "simulation_config": {
    "begin": 0,
    "end": 14400,
    "step_length": 1
  }
}
```

**响应**:
```json
{
  "batch_id": "batch_20251025_143000",
  "case_id": "case_20251025_001",
  "plan_ids": ["baseline_plan", "plan_20251025_140530_a1b2c", "plan_20251025_141200_d3e4f"],
  "total_tasks": 9,  # 3 plans × 3 seeds
  "status": "pending",
  "created_at": "2025-10-25T14:30:00"
}
```

#### POST /api/v1/control/optimization/batch/{batch_id}/start
启动批量仿真

**响应**:
```json
{
  "batch_id": "batch_20251025_143000",
  "status": "running",
  "started_at": "2025-10-25T14:30:05"
}
```

#### GET /api/v1/control/optimization/batch/{batch_id}/progress
获取批次进度

**响应**:
```json
{
  "batch_id": "batch_20251025_143000",
  "status": "running",
  "progress": 0.33,  # 3/9完成
  "tasks": [
    {
      "task_id": "task_001",
      "plan_id": "baseline_plan",
      "plan_name": "基准方案",
      "seed": 66,
      "status": "completed",
      "simulation_id": "sim_001",
      "started_at": "...",
      "completed_at": "..."
    },
    {
      "task_id": "task_002",
      "plan_id": "baseline_plan",
      "seed": 67,
      "status": "running",
      "simulation_id": "sim_002",
      "started_at": "...",
      "progress": 0.45
    },
    {
      "task_id": "task_003",
      "plan_id": "baseline_plan",
      "seed": 68,
      "status": "pending"
    },
    ...
  ],
  "estimated_completion": "2025-10-25T15:30:00"
}
```

#### GET /api/v1/control/optimization/batch/{batch_id}/results
获取批次结果汇总

**响应**:
```json
{
  "batch_id": "batch_20251025_143000",
  "status": "completed",
  "plan_results": [
    {
      "plan_id": "baseline_plan",
      "plan_name": "基准方案",
      "simulations": [
        {
          "seed": 66,
          "simulation_id": "sim_001",
          "metrics": {
            "avg_travel_time": 1450.2,
            "total_delay": 58000,
            "avg_speed": 22.5
          }
        },
        {
          "seed": 67,
          "simulation_id": "sim_002",
          "metrics": {...}
        },
        {
          "seed": 68,
          "simulation_id": "sim_003",
          "metrics": {...}
        }
      ],
      "aggregated_metrics": {
        "avg_travel_time": {
          "mean": 1448.5,
          "std": 5.2,
          "min": 1442.0,
          "max": 1455.0
        },
        ...
      }
    },
    ...
  ]
}
```

#### DELETE /api/v1/control/optimization/batch/{batch_id}
取消/删除批次

**行为**:
- 如果正在运行，取消所有未完成任务
- 删除批次目录和元数据

## 4. 前端界面设计

### 4.0 前端访问URL路径

**重要**: 所有管控优化相关页面必须使用 `/control/` 前缀访问

| 功能模块 | 页面文件 | 访问URL | Phase | 状态 |
|---------|---------|---------|-------|------|
| **策略管理** | `templates.html` | `http://localhost:8000/control/templates.html` | Phase 1A | ✅ 已实现 |
| **方案管理** | `plans.html` | `http://localhost:8000/control/plans.html` | Phase 1B | ✅ 已实现 |
| **并行仿真** | `simulations.html` | `http://localhost:8000/control/simulations.html` | Phase 2-3 | ✅ 已实现 |
| **方案优化** | `optimization.html` | `http://localhost:8000/control/optimization.html` | Phase 4 | 🔜 待实现 |

**后端配置** (api/main.py):
```python
from fastapi.staticfiles import StaticFiles

# 挂载整个frontend目录到根路径
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

**路径映射**:
- 物理文件: `frontend/control/plans.html`
- 访问URL: `http://localhost:8000/control/plans.html`
- 浏览器请求 `/control/plans.html` → FastAPI 查找 `frontend/control/plans.html` → 返回文件

**说明**: 由于`frontend`目录挂载到根路径`/`，所有`frontend/control/`下的文件自动映射到`/control/`URL路径

---

### 4.1 方案管理页面（plans.html）

**页面结构**:
```
┌─────────────────────────────────────────────────────────┐
│  交通管控仿真优化系统 - 方案管理     [返回主系统]        │
├──────────┬──────────────────────────────────────────────┤
│          │  [新建方案]                                   │
│  侧边导航 │                                              │
│  策略管理 │  ┌──────────────────────────────────────┐  │
│  方案管理✓│  │  方案列表                             │  │
│  并行仿真 │  │  ┌────────────────────────────────┐  │  │
│  方案优化 │  │  │ 基准方案（无管控）              │  │  │
│          │  │  │ 策略数: 0                       │  │  │
│          │  │  │ [查看] [无法删除]               │  │  │
│          │  │  └────────────────────────────────┘  │  │
│          │  │  ┌────────────────────────────────┐  │  │
│          │  │  │ 早高峰综合管控方案A             │  │  │
│          │  │  │ 策略数: 3  标签: 早高峰 综合    │  │  │
│          │  │  │ [查看] [编辑] [删除]            │  │  │
│          │  │  └────────────────────────────────┘  │  │
│          │  └──────────────────────────────────────┘  │
└──────────┴──────────────────────────────────────────────┘
```

**新建/编辑方案模态框**:
```
┌──────────────────────────────────────────────────┐
│  新建方案                                  [X]    │
├──────────────────────────────────────────────────┤
│  方案名称: [__________________________]          │
│  描述: [______________________________]          │
│        [______________________________]          │
│                                                  │
│  选择策略: [搜索策略...]                         │
│  ┌────────────────────────────────────────────┐ │
│  │ ☑ strategy_001 - K10-K15路段限速80km/h    │ │
│  │ ☑ strategy_002 - K15-K20应急车道开放      │ │
│  │ ☐ strategy_003 - K18入口流量控制          │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  标签: [早高峰] [+添加]                          │
│  目标场景: [工作日早高峰(7:00-9:00)]             │
│                                                  │
│  预期效果:                                        │
│  减少拥堵: [降低瓶颈路段拥堵20%]                 │
│  提升速度: [提升平均速度15%]                     │
│  [+添加效果]                                     │
│                                                  │
│  ⚠️ 验证警告:                                   │
│  - 建议VSS策略提前5分钟生效                      │
│                                                  │
│         [取消]  [预览XML]  [创建方案]            │
└──────────────────────────────────────────────────┘
```

**方案详情页面**:
```
┌─────────────────────────────────────────────────────────┐
│  方案: 早高峰综合管控方案A                    [编辑]     │
├─────────────────────────────────────────────────────────┤
│  描述: 缓解K10-K15路段早高峰拥堵                         │
│  标签: [早高峰] [综合管控]                              │
│  创建时间: 2025-10-25 14:05:30                          │
│                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  包含策略 (3个)                                          │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 1. VSS - K10-K15路段限速80km/h (strategy_001)     │ │
│  │    影响路段: edge_800, edge_801, ...              │ │
│  │    生效时间: 6:55-9:00                             │ │
│  ├───────────────────────────────────────────────────┤ │
│  │ 2. DHS - K15-K20应急车道开放 (strategy_002)       │ │
│  │    影响路段: edge_1000-edge_1004                  │ │
│  │    生效时间: 7:00-9:00                             │ │
│  ├───────────────────────────────────────────────────┤ │
│  │ 3. TEC - K18入口流量控制 (strategy_003)           │ │
│  │    控制入口: entrance_k18                         │ │
│  │    限流: 180辆/小时 (7:00-9:00)                   │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  XML配置预览                                  [下载]    │
│  ┌───────────────────────────────────────────────────┐ │
│  │ <?xml version="1.0" encoding="UTF-8"?>            │ │
│  │ <additional>                                      │ │
│  │   <!-- 方案: 早高峰综合管控方案A -->                │ │
│  │   <variableSpeedSign id="strategy_001" ...>       │ │
│  │   ...                                             │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│         [删除方案]  [重新生成XML]  [应用到仿真]          │
└─────────────────────────────────────────────────────────┘
```

**说明**：
- "应用到仿真"按钮点击后跳转到并行仿真页面（simulations.html）
- 自动预选当前方案，用户可继续选择case和其他方案进行批量仿真

### 4.2 并行仿真页面（simulations.html）

**说明**：
- 本页面处理批量仿真的配置、执行、进度监控和基础结果对比
- Phase 4 将新增独立的"方案优化"页面（optimization.html），提供高级评估、多目标排序等功能

**批量仿真配置**:
```
┌─────────────────────────────────────────────────────────┐
│  批量优化仿真                                            │
├─────────────────────────────────────────────────────────┤
│  选择案例: [case_20251025_001 ▼]                        │
│                                                         │
│  选择方案:                                               │
│  ┌───────────────────────────────────────────────────┐ │
│  │ ☑ 基准方案（无管控） - 必选                        │ │
│  │ ☑ 早高峰综合管控方案A                              │ │
│  │ ☑ 早高峰综合管控方案B                              │ │
│  │ ☐ 恶劣天气应急方案                                 │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  仿真配置:                                               │
│  随机种子数: [3] (每个方案)                              │
│  起始种子: [66]                                          │
│  仿真时长: [14400] 秒                                   │
│                                                         │
│  预估: 3个方案 × 3次随机 = 9次仿真                       │
│  预计耗时: 约45分钟                                      │
│                                                         │
│                    [取消]  [开始批量仿真]                │
└─────────────────────────────────────────────────────────┘
```

**仿真进度监控**:
```
┌─────────────────────────────────────────────────────────┐
│  批量仿真进度 - batch_20251025_143000                    │
│  总进度: ████████░░░░░░░░ 33% (3/9)                     │
├─────────────────────────────────────────────────────────┤
│  基准方案（无管控）                                      │
│  ├─ Seed 66: ✓ 完成 (耗时: 4m 32s)                      │
│  ├─ Seed 67: ▶ 运行中... 45% (预计剩余: 2m)              │
│  └─ Seed 68: ⏸ 等待中...                                │
│                                                         │
│  早高峰综合管控方案A                                     │
│  ├─ Seed 66: ⏸ 等待中...                                │
│  ├─ Seed 67: ⏸ 等待中...                                │
│  └─ Seed 68: ⏸ 等待中...                                │
│                                                         │
│  早高峰综合管控方案B                                     │
│  ├─ Seed 66: ⏸ 等待中...                                │
│  ├─ Seed 67: ⏸ 等待中...                                │
│  └─ Seed 68: ⏸ 等待中...                                │
│                                                         │
│                          [取消批量仿真]                  │
└─────────────────────────────────────────────────────────┘
```

**结果对比（Phase 4实现详细对比）**:
```
┌─────────────────────────────────────────────────────────┐
│  批量仿真结果 - batch_20251025_143000                    │
│  状态: ✓ 全部完成 (9/9)                                 │
├─────────────────────────────────────────────────────────┤
│  方案对比摘要:                                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 方案         │ 平均行程时间 │ 平均速度 │ 吞吐量    │ │
│  ├───────────────────────────────────────────────────┤ │
│  │ 基准方案     │ 1448.5s     │ 22.5km/h │ 4200辆   │ │
│  │ 方案A        │ 1250.3s ↓   │ 26.8km/h│ 4450辆 ↑│ │
│  │ 方案B        │ 1180.8s ↓   │ 28.2km/h│ 4580辆 ↑│ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  详细结果文件: cases/.../plan_opti/batch_20251025_143000│
│                                                         │
│         [下载完整报告]  [查看详细对比]  [导出数据]       │
└─────────────────────────────────────────────────────────┘
```

## 5. 策略引用保护机制

### 5.1 引用计数

在策略元数据中增加引用计数字段：

```python
# shared/control_tools/strategy_file_manager.py 增强

def increment_strategy_reference(strategy_id: str, plan_id: str) -> None:
    """增加策略引用计数"""
    metadata = load_strategy_metadata(strategy_id)

    if 'referenced_by' not in metadata:
        metadata['referenced_by'] = []

    if plan_id not in metadata['referenced_by']:
        metadata['referenced_by'].append(plan_id)

    save_strategy_metadata(strategy_id, metadata)

def decrement_strategy_reference(strategy_id: str, plan_id: str) -> None:
    """减少策略引用计数"""
    metadata = load_strategy_metadata(strategy_id)

    if 'referenced_by' in metadata and plan_id in metadata['referenced_by']:
        metadata['referenced_by'].remove(plan_id)

    save_strategy_metadata(strategy_id, metadata)

def can_delete_strategy(strategy_id: str) -> Tuple[bool, List[str]]:
    """检查策略是否可以删除"""
    metadata = load_strategy_metadata(strategy_id)
    referenced_by = metadata.get('referenced_by', [])

    return (len(referenced_by) == 0, referenced_by)
```

### 5.2 删除保护

在策略删除API中增加检查：

```python
# api/services/control_strategy_service.py

def delete_strategy(strategy_id: str) -> dict:
    """删除策略（带引用保护）"""

    can_delete, referenced_by = can_delete_strategy(strategy_id)

    if not can_delete:
        raise ValueError(
            f"无法删除策略 {strategy_id}，因为它被以下方案引用: "
            f"{', '.join(referenced_by)}"
        )

    # 执行删除
    strategy_file_manager.delete_strategy(strategy_id)

    return {"deleted": True}
```

### 5.3 策略更新传播

当策略更新时，自动重新生成所有引用方案的XML：

```python
# api/services/control_strategy_service.py

def update_strategy(strategy_id: str, updates: dict) -> dict:
    """更新策略并传播到方案"""

    # 1. 更新策略
    strategy_file_manager.update_strategy(strategy_id, updates)

    # 2. 获取所有引用该策略的方案
    metadata = strategy_file_manager.load_strategy_metadata(strategy_id)
    referenced_by = metadata.get('referenced_by', [])

    # 3. 异步重新生成所有方案的XML
    for plan_id in referenced_by:
        try:
            plan_file_manager.regenerate_plan_xml(plan_id)
            logger.info(f"重新生成方案 {plan_id} 的XML")
        except Exception as e:
            logger.error(f"重新生成方案 {plan_id} 失败: {e}")

    return {
        "updated": True,
        "propagated_to_plans": referenced_by,
        "propagation_count": len(referenced_by)
    }
```

## 6. 基准方案自动创建

### 6.1 全局基准方案初始化

在系统首次启动或安装时创建全局基准方案：

```python
# shared/control_tools/plan_file_manager.py

BASELINE_PLAN_ID = "baseline_plan"

def ensure_baseline_plan_exists() -> None:
    """确保全局基准方案存在"""

    baseline_path = Path("control_data/plans/baseline_plan")

    if baseline_path.exists():
        return

    # 创建基准方案
    baseline_plan = {
        "plan_id": BASELINE_PLAN_ID,
        "plan_name": "基准方案（无管控）",
        "description": "无任何管控措施的基准方案，用于对比评估管控效果",
        "strategy_ids": [],
        "tags": ["基准", "无管控"],
        "target_scenario": "所有场景",
        "expected_effects": {
            "baseline": "提供基准数据用于对比"
        },
        "additional_file_path": "control_data/plans/baseline_plan/control.add.xml",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    # 创建目录
    baseline_path.mkdir(parents=True, exist_ok=True)

    # 保存元数据
    with open(baseline_path / "plan_metadata.json", "w", encoding="utf-8") as f:
        json.dump(baseline_plan, f, ensure_ascii=False, indent=2)

    # 保存空策略引用
    with open(baseline_path / "strategy_refs.json", "w", encoding="utf-8") as f:
        json.dump([], f)

    # 生成空XML
    empty_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<additional>\n    <!-- 基准方案：无管控 -->\n</additional>'
    with open(baseline_path / "control.add.xml", "w", encoding="utf-8") as f:
        f.write(empty_xml)

    logger.info("全局基准方案创建成功")
```

### 6.2 启动时检查

在FastAPI应用启动时调用：

```python
# api/main.py

from shared.control_tools.plan_file_manager import ensure_baseline_plan_exists

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""

    # 确保基准方案存在
    ensure_baseline_plan_exists()

    logger.info("应用启动完成")
```

## 7. 技术决策

### 7.1 为什么选择eager生成XML？

**决策**: 在方案创建时立即生成control.add.xml

**理由**:
1. **即时验证**: 创建时立即验证XML格式正确性
2. **简化仿真**: 仿真时直接复制文件，无需重新生成
3. **性能**: 避免仿真启动时的生成延迟
4. **一致性**: 确保所有仿真使用相同的配置

**权衡**: 策略更新后需要重新生成，但通过异步处理可接受

### 7.2 为什么选择动态并发控制？

**决策**: 批量仿真并发数基于CPU线程数动态计算

**理由**:
1. **系统资源**: 根据实际硬件能力自动调整（默认CPU线程数×75%）
2. **可扩展性**: 支持40-60个任务并发（高性能服务器）
3. **可配置**: 可通过环境变量或配置文件覆盖默认值
4. **灵活性**: 开发环境、生产环境自动适配

**实现方式**:
```python
import os
import multiprocessing

def get_max_concurrent_simulations() -> int:
    """
    计算最大并发仿真数
    - 优先读取环境变量 MAX_CONCURRENT_SIMULATIONS
    - 否则使用 CPU线程数 * 0.75
    - 最小值4，最大值80
    """
    if env_value := os.getenv("MAX_CONCURRENT_SIMULATIONS"):
        return max(4, min(80, int(env_value)))
    cpu_count = multiprocessing.cpu_count()
    return max(4, min(80, int(cpu_count * 0.75)))
```

### 7.3 为什么选择警告模式验证？

**决策**: 方案验证返回警告而非阻塞

**理由**:
1. **灵活性**: 允许专家用户创建特殊方案
2. **探索性**: 支持实验性配置
3. **用户体验**: 提示而非强制，减少挫折感

**权衡**: 可能创建不合理方案，但通过清晰警告信息缓解

## 8. 未来扩展

### Phase 4（不在本提案范围）
- 方案评估指标计算（MAPE、GEH、吞吐量等）
- 多目标排序算法
- 雷达图、柱状图对比可视化
- 详细评估报告生成

### 可能的增强
- 方案版本历史
- 方案模板库（预定义常见组合）
- 智能方案推荐（基于case特征）
- A/B测试框架
- 实时管控集成（TraCI）
