# 场景库→Case仿真系统 - 最终决策确认

**日期**: 2025-11-11
**状态**: ✅ 确认
**实施目标**: 阶段1 (2-3天)

---

## 📋 五项关键决策确认

### 1️⃣ Case-Scenario关系
**决策**: ✅ **1:1强绑定**

**含义**:
- 一个case对应一个特定的scenario变体
- 一个事件的3个变体(no_control, vss, tec)创建3个独立的case
- case.metadata.source_scenario_id 唯一标识来源

**实现**:
```python
case.metadata = {
    "case_id": "case_20251111_001",
    "source_scenario_id": "scenario_11554_vss",  # 唯一关联
    "source_event_id": "11554",
    "source_variant": "vss",
    ...
}
```

**优势**: 简单清晰，无歧义，便于追踪

---

### 2️⃣ 配置覆盖权限
**决议**: ⚠️ **需要澄清具体指什么**

#### 什么是"配置覆盖权限"?

在从场景创建case时，用户可能想修改的参数有两类：

**A类 - 场景级参数 (不应覆盖)**
```json
{
  "event_id": "11554",              ❌ 不可改 (来源不能变)
  "event_type": "恶劣天气",          ❌ 不可改 (事件类型不能变)
  "location": {                     ❌ 不可改 (位置不能变)
    "road": "G76厦蓉",
    "junction_id": "-5192",
    "edge_id": "-5192"
  },
  "affected_edges": ["-5192"],      ❌ 不可改 (影响范围不能变)
  "control_strategy_type": "vss"    ❌ 不可改 (管控策略类型不能变)
}
```

**B类 - 仿真执行参数 (可以覆盖)**
```json
{
  "simulation_duration_hours": 3,   ⚠️ 可改? (仿真时长)
  "baseline_od_matrix": "default",  ⚠️ 可改? (OD规模)
  "random_seed": 42,                ⚠️ 可改? (随机种子)
  "output_config": {                ⚠️ 可改? (输出格式)
    "generate_tripinfo": true,
    "generate_edgedata": true,
    "generate_vehroute": true
  }
}
```

#### 我的建议

**根据你的需求(edgedata分析)**，我建议：

```
A类 (场景级): 完全锁定，不允许覆盖
  理由: 保持场景完整性，确保可重现性

B类 (仿真级):
  - simulation_duration_hours: ✅ 可覆盖 (用户可能想改仿真窗口)
  - output_config: ✅ 可覆盖 (必须包含edgedata，其他可选)
  - baseline_od_matrix: ❌ 建议不覆盖 (改变会影响对比基准)
  - random_seed: ✅ 可覆盖 (用于重复仿真)
```

#### 实现方案
```python
class CaseConfigFromScenario:
    # 不可覆盖字段 (from scenario)
    IMMUTABLE = [
        'event_id', 'event_type', 'location',
        'affected_edges', 'control_strategy_type'
    ]

    # 可选覆盖字段 (for simulation)
    OVERRIDABLE = {
        'simulation_duration_hours': 3,  # 默认等于事件时长
        'random_seed': None,              # 默认None(随机)
        'output_config': {
            'generate_edgedata': True,    # ⭐ 必须启用
            'generate_tripinfo': True,    # 可选
            'generate_vehroute': False    # 可选
        }
    }
```

---

### 3️⃣ 批量并发数
**决策**: ✅ **可配置(推荐2-8)**

**实现**:
```python
# API参数
POST /api/v1/batch-scenarios/simulate
{
  "parallel_workers": 4,  # 可配置，推荐范围2-8
  "timeout_minutes": 120
}

# 默认配置
DEFAULT_WORKERS = 4
MIN_WORKERS = 2
MAX_WORKERS = 8  # 根据CPU核心数
```

**建议**:
- 2核CPU: parallel_workers = 2
- 4核CPU: parallel_workers = 4 (推荐)
- 8核CPU: parallel_workers = 6-8

---

### 4️⃣ 分析自动化
**决策**: ✅ **仿真后按需手动，复用summary.xml/edgedata.xml/tripinfo结果分析**

**特殊选择**: ⭐ **由于是事件位置改进，建议使用edgedata分析**

#### 分析策略
```
层级1 (必须，自动生成):
  - summary.xml 基础指标
    • 总车辆数、完成率
    • 平均速度、拥堵时间
    • CO2排放等

  ✓ 产出位置: cases/{case_id}/simulations/{scenario_id}/summary.json

层级2 (按需手动调用):
  - Edgedata分析 ⭐ [重点]
    • 路段流量时空分布
    • 事件影响范围评估
    • 管控策略的"治疗范围"

  ✓ API: GET /api/v1/scenario-analysis/edgedata/{case_id}/{simulation_id}

层级3 (后期可选):
  - Tripinfo分析 (轨迹级)
    • 个体车辆迂回率
    • 延误分布

  - 多准则排名
    • 多场景对比评分
```

#### 为什么选择edgedata分析?

**优势**:
- ✅ **事件空间感知**: 清晰显示事件影响的路段范围
- ✅ **控制效果评估**: 直观看到管控策略的作用范围
- ✅ **可视化友好**: 易生成热力图和时空图
- ✅ **对比明确**: baseline vs 有管控的edgedata对比最直观

**劣势(tripinfo)**:
- ❌ 轨迹级数据量大
- ❌ 对于"位置改进"的需求，精度过高但不必要

#### 实现细节

**API设计**:
```http
GET /api/v1/scenario-analysis/edgedata/{case_id}/{simulation_id}
Response:
{
  "metadata": {
    "event_id": "11554",
    "scenario_variant": "vss",
    "edge_id": "-5192"
  },
  "edgedata_analysis": {
    "impact_area": {
      "primary_edges": ["-5192", "-5193"],  # 直接影响
      "secondary_edges": ["..."],            # 间接影响
      "recovery_distance": 5.2               # 恢复距离(km)
    },
    "control_effectiveness": {
      "flow_improvement": 23.5,              # 流量改善%
      "speed_improvement": 18.2,             # 速度改善%
      "congestion_relief_time": 15           # 缓解时间(min)
    },
    "time_series": [
      {
        "time": "2025-06-29 21:30",
        "lanes": {
          "lane_0": {"occupancy": 0.85, "speed": 42},
          "lane_1": {"occupancy": 0.92, "speed": 35}
        }
      }
    ]
  }
}
```

**存储位置**:
```
cases/{case_id}/
├── simulations/
│   ├── scenario_11554_no_control/
│   │   ├── results/
│   │   │   ├── summary.xml
│   │   │   ├── edgedata.xml
│   │   │   └── tripinfo.xml
│   │   └── analysis/
│   │       └── edgedata_analysis.json  ← 按需生成
│   ├── scenario_11554_vss/
│   └── scenario_11554_tec/
└── analysis/
    └── scenario_edgedata_comparison.json  ← 对比分析
```

---

### 5️⃣ 结果保留期限
**决策**: ✅ **不设置自动清理，手动管理**

**含义**:
- 仿真结果永久保留在case目录中
- 用户自行删除不需要的case
- 不设置定期清理任务

**实现**:
```python
# Case删除API (用户主动调用)
DELETE /api/v1/case/{case_id}
  - 删除整个case目录
  - 记录删除日志
  - 不自动清理

# 不实现的功能
# - 自动清理7天前的结果 ❌
# - 按大小限制保留 ❌
```

**建议的使用策略**:
```
定期检查:
  □ 列出所有case: GET /api/v1/case/list
  □ 按大小排序，查看占用空间
  □ 手动删除不需要的case

监控:
  □ 添加case存储使用统计API
  □ 前端显示当前占用空间
```

---

## 🎯 综合配置总结

```python
# 场景库系统配置 (scenarios/config.py)

SCENARIO_SYSTEM_CONFIG = {
    # 1. Case-Scenario关系
    "relationship_model": "ONE_TO_ONE",  # 1:1强绑定

    # 2. 配置覆盖规则
    "config_override_policy": {
        "immutable_fields": [
            "event_id", "event_type", "location",
            "affected_edges", "control_strategy_type"
        ],
        "overridable_fields": {
            "simulation_duration_hours": "OPTIONAL",
            "random_seed": "OPTIONAL",
            "output_config": "OPTIONAL"
        },
        # edgedata必须启用
        "required_outputs": ["edgedata", "summary"]
    },

    # 3. 批量并发
    "batch_execution": {
        "default_workers": 4,
        "min_workers": 2,
        "max_workers": 8,
        "timeout_minutes": 120
    },

    # 4. 分析策略
    "analysis_strategy": {
        "auto_generate_on_completion": [
            "summary.json"  # 自动
        ],
        "on_demand_analysis": [
            "edgedata_analysis.json",  # 按需 ⭐
            "tripinfo_analysis.json",
            "scenario_comparison.json"
        ],
        "primary_analysis_type": "edgedata"  # 重点分析类型
    },

    # 5. 结果保留
    "retention_policy": {
        "auto_cleanup": False,           # 不自动清理
        "manual_cleanup_only": True,     # 手动管理
        "add_storage_tracking": True     # 添加存储监控
    }
}
```

---

## 📊 决策影响矩阵

| 决策 | 对API的影响 | 对数据库的影响 | 对前端的影响 | 实现复杂度 |
|------|-----------|--------------|-----------|---------|
| 1:1绑定 | 简化(无关联查询) | 简化(直接关系) | 简化(一一映射) | 低 |
| 配置覆盖 | 中等(参数验证) | 无 | 中等(表单) | 低 |
| 可配并发 | 简化(参数化) | 无 | 简化(输入框) | 低 |
| edgedata分析 | 复杂(分析逻辑) | 无 | 中等(图表) | 中 |
| 手动保留 | 简化(无清理) | 简化(无定时任务) | 简化(删除按钮) | 低 |

---

## 🚀 基于这些决策的阶段1实施计划

### 核心API设计

```http
# 1. 列出可用场景
GET /api/v1/scenario/list
Response: [
  {
    "event_id": "11554",
    "event_type": "恶劣天气",
    "variants": ["no_control", "vss", "tec"],
    "location": {...},
    "available": true
  }
]

# 2. 从场景创建case
POST /api/v1/scenario/create-case
{
  "source_scenario_id": "scenario_11554_vss",

  # 可选覆盖配置
  "config_overrides": {
    "simulation_duration_hours": 4,  # 可改
    "random_seed": 123               # 可改
  },

  # 不可改(会被忽略)
  "event_id": "11554"  # ❌ 会被忽略
}

Response:
{
  "case_id": "case_20251111_001",
  "source_scenario_id": "scenario_11554_vss",
  "status": "ready_for_simulation"
}

# 3. 批量创建case并仿真
POST /api/v1/batch-scenarios/create-and-simulate
{
  "event_ids": ["11554", "12522"],
  "variants": ["no_control", "vss", "tec"],
  "execution": {
    "parallel_workers": 4,          # 可配
    "auto_run_simulation": true
  }
}

# 4. 按需进行edgedata分析
GET /api/v1/scenario-analysis/edgedata/{case_id}/{simulation_id}
Response: {
  "impact_area": {...},
  "control_effectiveness": {...},
  "time_series": [...]
}
```

### 数据模型

```python
# api/models/entities/scenario.py

class ScenarioVariant(str, Enum):
    NO_CONTROL = "no_control"
    VSS = "vss"
    TEC = "tec"
    DHS = "dhs"

class Scenario(BaseModel):
    event_id: str
    event_type: str
    variant: ScenarioVariant
    location: Dict[str, Any]
    duration_hours: float
    affected_edges: List[str]

    # 关键: 追踪来源
    class Config:
        schema_extra = {
            "example": {
                "event_id": "11554",
                "variant": "vss",
                "location": {"edge_id": "-5192"},
                "source_scenario_library_path": "output/scenarios/06_weather/scenario_11554_vss"
            }
        }

class EventScenarioCaseCreationRequest(BaseModel):
    source_scenario_id: str  # 格式: "scenario_{event_id}_{variant}"

    # 可选覆盖
    config_overrides: Optional[Dict[str, Any]] = None
    case_name: Optional[str] = None  # 用户自定义名称
```

### Service实现要点

```python
# api/services/scenario_service.py

class ScenarioService(BaseService):

    async def create_case_from_scenario(
        self,
        scenario_id: str,
        config_overrides: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        关键函数：从场景创建case

        步骤:
        1. 解析scenario_id → event_id, variant
        2. 从scenario_index.json加载场景定义
        3. 验证场景文件存在
        4. 创建case目录结构
        5. 继承场景配置到case.metadata
        6. 应用config_overrides(仅允许的字段)
        7. 记录source_scenario_id
        """

        # 验证scenario_id格式: scenario_11554_vss
        event_id, variant = self._parse_scenario_id(scenario_id)

        # 加载场景定义
        scenario_def = self._load_scenario_definition(event_id, variant)

        # 创建case
        case_id = self.generate_unique_id("case")
        case_dir = DirectoryManager.create_case_structure(case_id)

        # 构建case metadata
        case_metadata = {
            "case_id": case_id,
            "source_scenario_id": scenario_id,      # ⭐ 关键字段
            "source_event_id": event_id,
            "source_variant": variant,
            "event_type": scenario_def["event_type"],
            "location": scenario_def["location"],
            "affected_edges": scenario_def["affected_edges"],
            "control_strategy_type": scenario_def["strategy_type"],

            # 继承场景配置
            "simulation_config": {
                "duration_hours": scenario_def.get("duration_hours", 3),
                "output_config": {
                    "generate_edgedata": True,    # ⭐ 强制启用
                    "generate_summary": True,
                    "generate_tripinfo": scenario_def.get("include_tripinfo", False)
                }
            },

            # 应用用户覆盖(仅OVERRIDABLE字段)
            **self._apply_safe_overrides(config_overrides)
        }

        # 保存
        MetadataManager.save_case_metadata(case_dir, case_metadata)

        return {
            "case_id": case_id,
            "source_scenario_id": scenario_id,
            "ready_for_simulation": True
        }
```

---

## ✅ 检查清单 (实施前)

- [ ] 确认这5项决策与项目目标一致
- [ ] 确认edgedata分析是首选分析方式
- [ ] 确认不需要tripinfo轨迹级分析
- [ ] 确认UI/前端可以接受1:1绑定模型
- [ ] 确认团队熟悉edgedata XML格式

---

## 📚 相关文件

| 文件 | 用途 |
|------|------|
| `docs/IMPLEMENTATION_ROADMAP.md` | 详细技术方案 |
| `docs/NEXT_STEPS_SUMMARY.md` | 快速参考 |
| `docs/IMPLEMENTATION_DECISIONS.md` | 本文件 |

