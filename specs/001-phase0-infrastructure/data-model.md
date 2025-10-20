# Data Models: 交通管控仿真系统

**Feature**: Phase 0 基础设施准备
**Date**: 2025-10-19
**Status**: Design Complete

## Overview

Phase 0 定义了4个核心数据模型，用于管控策略优化的完整生命周期：从模板定义→策略创建→方案组建→批量仿真。所有模型使用Pydantic BaseModel实现，提供运行时类型验证和JSON序列化支持。

## Model Hierarchy

```
ControlTemplate (策略模板)
    ↓ 基于模板创建
Strategy (具体策略实例)
    ↓ 多个策略组合
Plan (控制方案)
    ↓ 多个方案并行测试
BatchSimulation (批量仿真任务)
```

---

## 1. ControlTemplate (管控策略模板)

### Purpose

定义某种管控类型（如可变限速VSS、动态硬路肩DHS、入口匝道控制TEC）的参数结构和默认值。模板作为策略创建的"蓝图"，确保参数一致性和可复用性。

### Location

`api/models/control/entities/template.py`

### Model Definition

```python
"""
管控策略模板实体模型
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from ...enums import StrategyType


class ControlTemplate(BaseModel):
    """管控策略模板模型"""

    template_id: str = Field(
        ...,
        description="模板唯一标识符",
        examples=["vss_moderate_001", "dhs_peak_hours_001"]
    )

    template_name: str = Field(
        ...,
        description="模板名称（用户可读）",
        examples=["可变限速-中等强度", "动态硬路肩-高峰时段"]
    )

    strategy_type: StrategyType = Field(
        ...,
        description="管控策略类型（VSS/DHS/TEC）"
    )

    parameters_schema: Dict[str, Any] = Field(
        ...,
        description="参数JSON Schema定义（类型、范围、默认值）",
        examples=[{
            "speed_limit": {
                "type": "integer",
                "minimum": 40,
                "maximum": 120,
                "default": 80,
                "unit": "km/h",
                "description": "限速值"
            },
            "active_hours": {
                "type": "array",
                "items": {"type": "integer", "minimum": 0, "maximum": 23},
                "default": [7, 8, 9, 17, 18, 19],
                "description": "激活时段（小时）"
            }
        }]
    )

    description: Optional[str] = Field(
        None,
        description="模板详细说明（使用场景、注意事项）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "vss_moderate_001",
                "template_name": "可变限速-中等强度",
                "strategy_type": "vss",
                "parameters_schema": {
                    "speed_limit": {
                        "type": "integer",
                        "minimum": 40,
                        "maximum": 120,
                        "default": 80,
                        "unit": "km/h"
                    }
                },
                "description": "适用于高峰时段流量疏导，限速范围40-120km/h"
            }
        }
```

### Fields Specification

| Field | Type | Required | Validation | Purpose |
|-------|------|----------|------------|---------|
| `template_id` | str | Yes | Unique, non-empty | Primary key, file naming |
| `template_name` | str | Yes | Non-empty | Display name for UI |
| `strategy_type` | StrategyType | Yes | Enum (VSS/DHS/TEC) | Strategy category |
| `parameters_schema` | Dict[str, Any] | Yes | Valid JSON Schema | Parameter definition |
| `description` | str | No | - | Documentation text |

### Storage Format

Templates stored as JSON files in `templates/control_strategies/{strategy_type}/{template_id}.json`

Example file: `templates/control_strategies/vss/vss_moderate_001.json`

---

## 2. Strategy (管控策略实例)

### Purpose

基于某个模板创建的具体策略实例，包含用户填写的参数值和目标路段。策略是用户操作的基本单位，可被多个方案复用。

### Location

`api/models/control/entities/strategy.py`

### Model Definition

```python
"""
管控策略实例实体模型
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime


class Strategy(BaseModel):
    """管控策略实例模型"""

    strategy_id: str = Field(
        ...,
        description="策略唯一标识符（UUID或自增ID）",
        examples=["strategy_20251019_001", "strat_uuid_abc123"]
    )

    strategy_name: str = Field(
        ...,
        description="策略名称（用户自定义）",
        examples=["G4202分流点限速80", "高峰时段入口控制方案A"]
    )

    template_id: str = Field(
        ...,
        description="关联的模板ID（外键）",
        examples=["vss_moderate_001"]
    )

    parameters: Dict[str, Any] = Field(
        ...,
        description="参数值字典（键名匹配template的parameters_schema）",
        examples=[{
            "speed_limit": 80,
            "active_hours": [7, 8, 9, 17, 18, 19],
            "warning_threshold": 70
        }]
    )

    target_edges: List[str] = Field(
        ...,
        description="目标路段ID列表（SUMO edge_id）",
        examples=[["edge_e789012", "edge_e789013", "edge_e789015"]]
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间戳"
    )

    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="最后更新时间戳"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "strategy_20251019_001",
                "strategy_name": "G4202分流点限速80",
                "template_id": "vss_moderate_001",
                "parameters": {
                    "speed_limit": 80,
                    "active_hours": [7, 8, 9, 17, 18, 19]
                },
                "target_edges": ["edge_e789012", "edge_e789013"],
                "created_at": "2025-10-19T10:30:00",
                "updated_at": "2025-10-19T10:30:00"
            }
        }
```

### Fields Specification

| Field | Type | Required | Validation | Purpose |
|-------|------|----------|------------|---------|
| `strategy_id` | str | Yes | Unique, non-empty | Primary key |
| `strategy_name` | str | Yes | Non-empty, max 100 chars | User-facing name |
| `template_id` | str | Yes | Must reference existing template | Foreign key |
| `parameters` | Dict[str, Any] | Yes | Must match template schema | Actual parameter values |
| `target_edges` | List[str] | Yes | Non-empty, valid edge_ids | SUMO road segments |
| `created_at` | datetime | Auto | ISO 8601 format | Audit trail |
| `updated_at` | datetime | Auto | ISO 8601 format | Audit trail |

### Storage Format

Strategies stored as JSON files in `control_data/strategies/{strategy_id}.json`

Index file: `control_data/strategies/strategies_index.json`

---

## 3. Plan (控制方案)

### Purpose

包含多个策略的组合，用于生成SUMO Additional文件。方案定义了一组协同工作的管控措施，是仿真测试的基本单位。

### Location

`api/models/control/entities/plan.py`

### Model Definition

```python
"""
控制方案实体模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Plan(BaseModel):
    """控制方案模型"""

    plan_id: str = Field(
        ...,
        description="方案唯一标识符",
        examples=["plan_20251019_001", "plan_baseline"]
    )

    plan_name: str = Field(
        ...,
        description="方案名称（用户自定义）",
        examples=["高峰时段综合管控方案A", "基线方案（无管控）"]
    )

    description: Optional[str] = Field(
        None,
        description="方案详细描述（目标、适用场景）",
        examples=["针对早高峰7-9点，结合限速和入口控制"]
    )

    strategy_ids: List[str] = Field(
        default_factory=list,
        description="包含的策略ID列表（外键，允许空表示基线方案）",
        examples=[["strategy_001", "strategy_002", "strategy_003"]]
    )

    additional_file_path: Optional[str] = Field(
        None,
        description="生成的SUMO Additional文件路径（相对路径）",
        examples=["control_data/plans/plan_20251019_001/control.add.xml"]
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间戳"
    )

    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="最后更新时间戳"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "plan_20251019_001",
                "plan_name": "高峰时段综合管控方案A",
                "description": "结合G4202分流点限速和入口控制",
                "strategy_ids": ["strategy_001", "strategy_002"],
                "additional_file_path": "control_data/plans/plan_20251019_001/control.add.xml",
                "created_at": "2025-10-19T11:00:00",
                "updated_at": "2025-10-19T11:00:00"
            }
        }
```

### Fields Specification

| Field | Type | Required | Validation | Purpose |
|-------|------|----------|------------|---------|
| `plan_id` | str | Yes | Unique, non-empty | Primary key |
| `plan_name` | str | Yes | Non-empty, max 100 chars | User-facing name |
| `description` | str | No | Max 500 chars | Documentation |
| `strategy_ids` | List[str] | No | Each must reference existing strategy | Strategy composition |
| `additional_file_path` | str | No | Valid relative path | Generated XML location |
| `created_at` | datetime | Auto | ISO 8601 format | Audit trail |
| `updated_at` | datetime | Auto | ISO 8601 format | Audit trail |

### Storage Format

Plans stored as JSON files in `control_data/plans/{plan_id}/plan_metadata.json`

Additional files in same directory: `control_data/plans/{plan_id}/control.add.xml`

---

## 4. BatchSimulation (批量仿真任务)

### Purpose

针对某个案例（Case）和多个方案（Plans）执行并行仿真。批量仿真管理仿真调度、进度跟踪、结果收集，是优化分析的基础。

### Location

`api/models/control/entities/batch_simulation.py`

### Model Definition

```python
"""
批量仿真任务实体模型
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from ...enums import BatchSimulationStatus


class BatchSimulation(BaseModel):
    """批量仿真任务模型"""

    batch_id: str = Field(
        ...,
        description="批次唯一标识符",
        examples=["batch_20251019_001"]
    )

    batch_name: str = Field(
        ...,
        description="批次名称（用户自定义）",
        examples=["高峰时段方案对比测试"]
    )

    case_id: str = Field(
        ...,
        description="关联的案例ID（外键，引用已有Case）",
        examples=["case_20251015_baseline"]
    )

    plan_ids: List[str] = Field(
        ...,
        description="待测试的方案ID列表（外键）",
        min_length=1,
        examples=[["plan_baseline", "plan_001", "plan_002", "plan_003"]]
    )

    status: BatchSimulationStatus = Field(
        default=BatchSimulationStatus.PENDING,
        description="批次状态（PENDING/RUNNING/COMPLETED/FAILED）"
    )

    progress: Dict[str, int] = Field(
        default_factory=lambda: {"total": 0, "completed": 0, "failed": 0},
        description="进度统计",
        examples=[{"total": 4, "completed": 2, "failed": 0}]
    )

    simulation_ids: List[str] = Field(
        default_factory=list,
        description="生成的仿真ID列表（外键，引用Simulation）",
        examples=[["sim_001_plan_baseline", "sim_002_plan_001"]]
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间戳"
    )

    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="最后更新时间戳"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_20251019_001",
                "batch_name": "高峰时段方案对比测试",
                "case_id": "case_20251015_baseline",
                "plan_ids": ["plan_baseline", "plan_001", "plan_002"],
                "status": "running",
                "progress": {"total": 3, "completed": 1, "failed": 0},
                "simulation_ids": ["sim_001_plan_baseline"],
                "created_at": "2025-10-19T14:00:00",
                "updated_at": "2025-10-19T14:15:00"
            }
        }
```

### Fields Specification

| Field | Type | Required | Validation | Purpose |
|-------|------|----------|------------|---------|
| `batch_id` | str | Yes | Unique, non-empty | Primary key |
| `batch_name` | str | Yes | Non-empty, max 100 chars | User-facing name |
| `case_id` | str | Yes | Must reference existing Case | Base case for simulation |
| `plan_ids` | List[str] | Yes | Non-empty, each must reference existing Plan | Plans to test |
| `status` | BatchSimulationStatus | Auto | Enum (PENDING/RUNNING/COMPLETED/FAILED) | Task state |
| `progress` | Dict[str, int] | Auto | total >= completed + failed | Progress tracking |
| `simulation_ids` | List[str] | Auto | Each must reference existing Simulation | Result tracking |
| `created_at` | datetime | Auto | ISO 8601 format | Audit trail |
| `updated_at` | datetime | Auto | ISO 8601 format | Audit trail |

### Storage Format

Batch simulations stored as JSON files in `control_data/optimizations/{batch_id}/batch_metadata.json`

---

## Enums (api/models/enums.py)

### StrategyType

```python
class StrategyType(str, Enum):
    """管控策略类型枚举"""
    VSS = "vss"  # Variable Speed Sign (可变限速)
    DHS = "dhs"  # Dynamic Hard Shoulder (动态硬路肩)
    TEC = "tec"  # Toll Entrance Control (入口匝道控制)
```

### BatchSimulationStatus

```python
class BatchSimulationStatus(str, Enum):
    """批量仿真状态枚举"""
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
```

---

## Relationships

```
┌─────────────────┐
│ ControlTemplate │ (1)
└────────┬────────┘
         │ 1:N
         ↓
    ┌──────────┐
    │ Strategy │ (N)
    └────┬─────┘
         │ N:M (via Plan.strategy_ids)
         ↓
      ┌──────┐
      │ Plan │ (M)
      └──┬───┘
         │ N:1 (via BatchSimulation.plan_ids)
         ↓
┌──────────────────┐
│ BatchSimulation  │ (1 batch → N plans)
└──────────────────┘
         ↓ 1:N (generates)
┌──────────────────┐
│   Simulation     │ (existing entity)
│  (Phase 3 creates)
└──────────────────┘
```

---

## Validation Rules

### Cross-Model Consistency

1. **Strategy.template_id** → Must reference existing ControlTemplate
2. **Strategy.parameters** → Keys must match ControlTemplate.parameters_schema
3. **Plan.strategy_ids** → Each ID must reference existing Strategy
4. **BatchSimulation.case_id** → Must reference existing Case (from existing system)
5. **BatchSimulation.plan_ids** → Each ID must reference existing Plan
6. **BatchSimulation.progress.total** = len(BatchSimulation.plan_ids)

### Business Rules

1. **Baseline Plan**: A plan with empty `strategy_ids` represents no control (baseline scenario)
2. **Unique Naming**: `strategy_name` and `plan_name` should be unique within user workspace (not enforced at model level, UI validation)
3. **Immutable After Simulation**: Once a Plan is used in a completed BatchSimulation, it should not be modified (audit trail)
4. **Status Transitions**: BatchSimulationStatus follows lifecycle: PENDING → RUNNING → COMPLETED/FAILED

---

## Implementation Notes

### Phase 0 Scope

- Define all 4 models in their respective files
- Add enums to `api/models/enums.py`
- Create `__init__.py` files for proper imports
- **No validation logic** (deferred to Phase 1C)
- **No storage implementation** (deferred to Phase 1C)
- **No relationship enforcement** (deferred to Phase 1C)

### Future Phases

- **Phase 1A**: Add template validation against JSON Schema
- **Phase 1C**: Implement CRUD operations with relationship checks
- **Phase 2**: Add Additional file generation logic (use Plan.strategy_ids)
- **Phase 3**: Implement BatchSimulation orchestration
- **Phase 4**: Add optimization metrics to BatchSimulation results

---

## File Structure Summary

```
api/models/control/
├── __init__.py              # Export all models
└── entities/
    ├── __init__.py          # Export entity models
    ├── template.py          # ControlTemplate
    ├── strategy.py          # Strategy
    ├── plan.py              # Plan
    └── batch_simulation.py  # BatchSimulation

api/models/enums.py          # Add StrategyType, BatchSimulationStatus
```

**Status**: ✅ Data model design complete - ready for implementation
