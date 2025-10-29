# 交通管控仿真优化功能域 - 概要设计

**文档版本**: v1.0
**创建日期**: 2025-10-19
**状态**: 设计梗概

---

## 1. 功能域定位

### 1.1 业务背景
在现有OD数据处理与仿真系统的基础上，新增**交通管控仿真优化功能域**，专注于高速公路路网的管控策略设计、仿真测试和优化分析。

### 1.2 核心价值
- **策略设计**：提供可视化、模板化的管控策略配置工具
- **方案对比**：支持多方案并行仿真，快速对比不同管控措施的效果
- **智能优化**：基于多指标评估，自动筛选最优管控方案
- **决策支持**：为交通管理部门提供数据驱动的管控决策依据

### 1.3 应用场景
- 高速公路路网管控策略制定
- 恶劣天气应对措施仿真
- 高峰期拥堵缓解方案优化
- 大型活动交通保障预案评估

---

## 2. 核心概念模型 ✅ 方案-仿真分层架构

### 2.1 核心架构图

基于 `sumo_control_strategies_research.md` 的研究成果，系统采用**策略-方案-仿真三层架构**：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  全局资源层 (Global Resources) - 可跨案例复用
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────┐
│                   策略模板层 (Template)                  │
│  预定义的管控措施配置模板                                │
│  - VSS模板：5个（2基础+3补充）                           │
│  - DHS模板：3个（1基础+2补充）                           │
│  - TEC模板：3个（3层优化设计）                           │
└────────────────────┬────────────────────────────────────┘
                     ↓ 实例化（选择路段 + 配置参数）
┌─────────────────────────────────────────────────────────┐
│                   策略实例层 (Strategy)                  │
│  针对特定路段/入口的单一管控措施                         │
│  - 单一路段区间 OR 单一入口                              │
│  - 一种管控类型（VSS/DHS/TEC）                          │
│  - 可独立运行，可被多个方案引用                          │
└────────────────────┬────────────────────────────────────┘
                     ↓ 组合（选择多个策略）
┌─────────────────────────────────────────────────────────┐
│                   管控方案层 (Plan)                      │
│  多个策略的业务组合，描述通用管控场景                     │
│  - 方案 = 策略1 + 策略2 + 策略3 + ...                   │
│  - 支持基准方案（无管控，用于对比）                      │
│  - 描述适用条件（拥堵模式、时间窗口、严重度阈值）         │
│  - 预期效果范围（如"速度提升100-200%"）                  │
│  - 包含control.add.xml模板                              │
└────────────────────┬────────────────────────────────────┘
                     │
━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  案例级资源层 (Case-Specific Resources) - 绑定具体案例
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                     │
                     ↓ 应用到Case（创建仿真实例）
┌─────────────────────────────────────────────────────────┐
│                   仿真实例层 (Simulation)                │
│  Plan应用到具体Case的运行实例                            │
│  - 绑定到case_id                                        │
│  - 包含具体仿真参数（begin, end, step_length等）        │
│  - 复制/调整Plan的control.add.xml                       │
│  - 包含仿真结果文件（summary.xml, tripinfo.xml等）      │
└────────────────────┬────────────────────────────────────┘
                     ↓ 批量运行（多个方案对比）
┌─────────────────────────────────────────────────────────┐
│              批量仿真管理 (Batch Management)             │
│  在同一Case上并行运行多个Plan的仿真实例                  │
│  - batch_id标识一组对比仿真                             │
│  - 管理多个仿真实例的调度和进度                          │
└────────────────────┬────────────────────────────────────┘
                     ↓ 评估分析
┌─────────────────────────────────────────────────────────┐
│                  优化结果 (Optimization)                  │
│  基于仿真结果的多目标评估和排序                          │
│  - 提取各仿真实例的指标                                  │
│  - 多目标排序，筛选最优方案                              │
│  - 更新Plan的validation_records                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 核心设计原则

#### 2.2.1 方案层（Plan） - 全局可复用

**定位**：通用的管控方案模板，描述"什么样的拥堵场景下使用什么策略组合"

**特征**：
- **通用性**：不绑定具体case，描述拥堵场景模式（如"早高峰拥堵"）
- **可复用性**：同一Plan可应用到多个满足条件的Case
- **适用条件**：明确定义适用的拥堵模式、时间窗口、严重度阈值
- **预期效果**：给出改善范围（如"速度提升100-200%"），而非具体数值
- **验证积累**：通过validation_records记录在不同Case上的验证结果

**包含内容**：
- 方案元数据（plan_metadata.json）
- 策略引用列表（strategy_refs.json）
- SUMO配置模板（control.add.xml）

**示例**：
- `plan_vss_morning_peak_simple`：早高峰单策略VSS限速方案
- `plan_vss_dhs_evening_composite`：晚高峰VSS+DHS复合管控方案
- `plan_vss_dhs_tec_allday_complex`：全天持续拥堵三策略立体管控方案

#### 2.2.2 仿真层（Simulation） - 案例级实例

**定位**：Plan应用到具体Case的运行实例

**特征**：
- **案例绑定**：必须关联到具体的case_id
- **参数具体化**：包含具体的仿真参数（begin, end, step_length等）
- **结果存储**：包含仿真运行的所有输出文件
- **一次性**：仿真结果不可复用，每次运行产生新实例

**包含内容**：
- 仿真配置文件（simulation.sumocfg）
- 管控配置文件（control.add.xml，从Plan复制）
- 仿真结果文件（summary.xml, tripinfo.xml, edgedata.xml等）
- 仿真元数据（simulation_metadata.json，关联plan_id和case_id）

**工作流程**：
```
1. 用户选择Case + Plan
2. 系统创建Simulation实例
   - 复制Plan的control.add.xml到仿真目录
   - 复制Case的网络文件、路由文件
   - 生成simulation.sumocfg
3. 运行SUMO仿真
4. 保存仿真结果
5. 提取指标 → 更新Plan的validation_records
```

### 2.3 核心概念对比

| 维度 | Plan（方案） | Simulation（仿真） |
|------|-------------|-------------------|
| **存储位置** | `control_data/plans/{plan_id}/` | `cases/{case_id}/control_simulations/{batch_id}/{plan_id}_sim/` |
| **生命周期** | 长期存在，可复用 | 一次性，仿真完成后归档 |
| **绑定对象** | 不绑定Case，通用场景模式 | 绑定到具体case_id |
| **可复用性** | ✅ 高（可应用到多个Case） | ❌ 无（一次性运行） |
| **参数特性** | 通用参数（范围、阈值） | 具体参数（begin=0, end=14400） |
| **效果描述** | 范围预期（"速度提升100-200%"） | 具体结果（"速度从15.14→50 km/h"） |
| **验证记录** | validation_records[] | 单次仿真结果 |
| **control.add.xml** | 模板（通用策略组合） | 实例（可能根据Case微调） |

### 2.4 职责边界

#### Plan的职责
1. ✅ 定义策略组合
2. ✅ 描述适用场景（通用）
3. ✅ 生成control.add.xml模板
4. ✅ 累积验证记录
5. ❌ 不包含具体仿真参数
6. ❌ 不存储仿真结果

#### Simulation的职责
1. ✅ 关联Plan和Case
2. ✅ 配置具体仿真参数
3. ✅ 运行SUMO仿真
4. ✅ 存储仿真结果
5. ✅ 提供指标给Optimization
6. ❌ 不修改Plan的定义

---

## 3. 数据架构设计

### 3.1 全局资源存储（跨案例复用）

#### 3.1.1 策略模板（复用现有templates目录）

```
templates/
├── control_strategies/              # 新增：策略模板库 - 11个模板
│   ├── variable_speed_sign/        # VSS模板 (5个)
│   │   ├── vss_moderate.json
│   │   ├── vss_strict.json
│   │   ├── vss_weather_based.json
│   │   ├── vss_upstream_warning.json
│   │   └── vss_lane_differentiated.json
│   ├── dynamic_hard_shoulder/      # DHS模板 (3个)
│   │   ├── dhs_peak_hours.json
│   │   ├── dhs_passenger_only.json
│   │   └── dhs_peak_multi_interval.json
│   ├── toll_entrance_control/      # TEC模板 (3个) - 3层设计
│   │   ├── tec_flow_metering.json      # 基础层：流量控制
│   │   ├── tec_vehicle_restriction.json # 限制层：车型限制
│   │   └── tec_emergency_closure.json   # 应急层：紧急关闭
│   └── templates_index.json        # 模板索引
```

#### 3.1.2 策略实例库

```
control_data/strategies/             # 策略实例库（全局）
├── {strategy_id}.json              # 策略定义文件
│   # 示例: strategy_real_vss_g4202_001.json
│   # 内容: template_id, configured_params, description, tags
└── strategies_index.json           # 策略索引
```

**说明**：
- 策略实例是全局的，不绑定case
- 可被多个Plan引用
- 包含具体的路段选择和参数配置

#### 3.1.3 管控方案库（全局，可复用）

```
control_data/plans/                  # 方案库（全局）
├── baseline_plan/                   # 基准方案（无管控）
│   ├── plan_metadata.json          # 方案元数据
│   │   # 字段: plan_id, plan_name, description
│   │   #       strategy_ids: []
│   │   #       applicable_conditions (通用)
│   │   #       expected_effects (范围)
│   │   #       validation_records: [{case_id, metrics}]
│   ├── strategy_refs.json          # [] (空列表)
│   └── control.add.xml             # 空文件或无此文件
│
├── plan_vss_morning_peak_simple/   # 早高峰单策略方案
│   ├── plan_metadata.json
│   │   # applicable_conditions:
│   │   #   - congestion_pattern: "早高峰单向拥堵"
│   │   #   - severity_threshold: "速度<30 km/h, 持续≥2h"
│   │   # expected_effects:
│   │   #   - speed_improvement: "100-200%"
│   │   # validation_records:
│   │   #   - {case_id: "待关联", road_segment: "G4202 K52.4", improvement: 230%}
│   ├── strategy_refs.json          # ["strategy_real_vss_g4202_001"]
│   └── control.add.xml             # VSS策略的SUMO配置模板
│
├── plan_vss_dhs_evening_composite/ # 晚高峰复合方案
│   ├── plan_metadata.json
│   ├── strategy_refs.json          # ["strategy_real_vss_g4202_002", "strategy_real_dhs_g4202_002"]
│   └── control.add.xml             # VSS+DHS策略的SUMO配置模板
│
└── plans_index.json                # 方案索引
    # [{plan_id, plan_name, strategy_count, complexity_level, target_scenario}]
```

**关键字段说明（plan_metadata.json）**：

```json
{
  "plan_id": "plan_vss_morning_peak_simple",
  "plan_name": "早高峰单策略VSS限速方案",
  "description": "针对早高峰时段（6:00-10:00）出现的严重拥堵",
  "strategy_ids": ["strategy_real_vss_g4202_001"],
  "tags": ["P0", "单策略", "VSS", "早高峰"],

  // ✅ 通用适用条件（不绑定具体case）
  "applicable_conditions": {
    "congestion_pattern": "早高峰单向拥堵",
    "time_window": "6:00-10:00",
    "severity_threshold": "平均速度 < 30 km/h，持续时长 ≥ 2小时",
    "road_types": ["城市快速路", "高速公路主线"]
  },

  // ✅ 预期效果范围（不是具体数值）
  "expected_effects": {
    "speed_improvement": "预期速度提升100-200%",
    "congestion_duration_reduction": "预期拥堵时长减少30-50%"
  },

  // ✅ 验证记录（记录在不同case上的实际效果）
  "validation_records": [
    {
      "case_id": "待关联",
      "batch_id": "20251013_20251019",
      "road_segment": "G4202 K52.4",
      "baseline_metrics": {"avg_speed_kmh": 15.14},
      "improvement_metrics": {"speed_improvement_percent": 230},
      "validation_status": "候选方案（待仿真验证）"
    }
  ],

  "additional_file_path": "control_data/plans/plan_vss_morning_peak_simple/control.add.xml",
  "created_at": "2025-10-26T14:00:00",
  "updated_at": "2025-10-26T14:00:00"
}
```

### 3.2 案例级数据存储（绑定具体案例）

#### 3.2.1 仿真实例存储

```
cases/{case_id}/
├── control_simulations/             # 新增：管控仿真结果目录
│   ├── {batch_id}/                 # 批次目录（一组对比仿真）
│   │   │
│   │   ├── baseline_plan_sim/      # 基准方案仿真实例
│   │   │   ├── simulation.sumocfg
│   │   │   ├── summary.xml         # SUMO输出
│   │   │   ├── tripinfo.xml        # SUMO输出
│   │   │   ├── edgedata.xml        # SUMO输出（可选）
│   │   │   ├── control.add.xml     # 空文件（基准方案无管控）
│   │   │   └── simulation_metadata.json
│   │   │       # {
│   │   │       #   "simulation_id": "sim_001",
│   │   │       #   "case_id": "case_20251019_001",
│   │   │       #   "plan_id": "baseline_plan",
│   │   │       #   "batch_id": "batch_001",
│   │   │       #   "simulation_params": {
│   │   │       #     "begin": 0,
│   │   │       #     "end": 14400,
│   │   │       #     "step_length": 1
│   │   │       #   },
│   │   │       #   "status": "COMPLETED",
│   │   │       #   "started_at": "...",
│   │   │       #   "completed_at": "..."
│   │   │       # }
│   │   │
│   │   ├── plan_vss_morning_peak_simple_sim/  # Plan应用到Case的仿真实例
│   │   │   ├── simulation.sumocfg
│   │   │   ├── summary.xml
│   │   │   ├── tripinfo.xml
│   │   │   ├── edgedata.xml
│   │   │   ├── control.add.xml     # 从Plan复制而来
│   │   │   └── simulation_metadata.json
│   │   │       # 同上，但plan_id = "plan_vss_morning_peak_simple"
│   │   │
│   │   ├── plan_vss_dhs_evening_composite_sim/  # 另一个Plan的仿真实例
│   │   │   └── ...
│   │   │
│   │   └── batch_metadata.json     # 批次元数据
│   │       # {
│   │       #   "batch_id": "batch_001",
│   │       #   "case_id": "case_20251019_001",
│   │       #   "plan_ids": ["baseline_plan", "plan_vss_morning_peak_simple", ...],
│   │       #   "status": "COMPLETED",
│   │       #   "progress": {...},
│   │       #   "created_at": "...",
│   │       #   "completed_at": "..."
│   │       # }
│   │
│   └── batches_index.json          # 批次索引
       # [{batch_id, case_id, plan_count, status, created_at}]
```

**关键设计说明**：

1. **Simulation实例命名规则**：`{plan_id}_sim`
   - `baseline_plan_sim`：基准方案仿真
   - `plan_vss_morning_peak_simple_sim`：具体Plan的仿真实例

2. **control.add.xml的来源**：
   - 从Plan的`control_data/plans/{plan_id}/control.add.xml`复制
   - 可能根据Case的具体情况微调（如调整时间参数）

3. **simulation_metadata.json**：
   - 关联到plan_id和case_id
   - 包含具体的仿真参数（begin, end, step_length）
   - 记录仿真状态和时间戳

### 3.3 数据流向

```
创建Plan（全局）
  → 选择策略 → 生成control.add.xml模板 → 保存到 control_data/plans/{plan_id}/

应用Plan到Case（创建Simulation）
  → 选择Case + Plan
  → 创建仿真目录 cases/{case_id}/control_simulations/{batch_id}/{plan_id}_sim/
  → 复制Plan的control.add.xml
  → 复制Case的网络文件、路由文件
  → 生成simulation.sumocfg

运行仿真
  → 运行SUMO → 生成 summary.xml, tripinfo.xml 等

评估结果
  → 提取指标 → 对比分析 → 更新Plan的validation_records[]
```

---

## 4. 管控策略类型设计

### 4.1 策略类型总览 ✅ 技术方案已验证

| 策略类型 | 英文名称 | SUMO实现 | 推荐方案 | 优先级 |
|---------|---------|---------|---------|-------|
| 可变限速 | Variable Speed Sign (VSS) | `<variableSpeedSign>` | 使用 `edges` 属性（v1.18+） | P0 ⭐⭐⭐⭐⭐ |
| 动态硬路肩 | Dynamic Hard Shoulder (DHS) | `<rerouter>` + `<closingLaneReroute>` | 基于时间区间控制 | P0 ⭐⭐⭐⭐⭐ |
| 收费站入口管控 | Toll Entrance Control (TEC) | `<calibrator>` (推荐) | 流量控制，精确到vehsPerHour | P0 ⭐⭐⭐⭐⭐ |
| 收费站入口管控 | Toll Entrance Control (TEC) | `<closingReroute>` (备选) | 完全关闭或车型限制 | P0 ⭐⭐⭐⭐ |

**说明**：
- 基于 `sumo_control_strategies_research.md` 研究成果
- TEC合并了货车限行和入口关闭两种场景，统一为"收费站入口管控"
- Calibrator方案适用于精确流量控制（匝道信号），closingReroute适用于完全关闭或车型限制

### 4.2 策略类型详细定义

#### 4.2.1 可变限速 (VSS)

**业务场景**：恶劣天气、拥堵预防、事故保护

**SUMO实现**：
```xml
<variableSpeedSign id="vss_1" lanes="edge1_0 edge1_1">
    <step time="7200" speed="20.0"/>
    <step time="10800" speed="25.0"/>
</variableSpeedSign>
```

**核心参数**：
- 路段ID列表 (`edges`)
- 车道索引 (`lanes`)
- 时间段 (`time_begin`, `time_end`)
- 限速值序列 (`speed_limits`)
- 触发条件（可选）

---

#### 4.2.2 动态硬路肩 (DHS)

**业务场景**：高峰期拥堵缓解、临时通行能力提升

**SUMO实现方案**：
- 方案A：通过`<closingLaneReroute>`禁用/启用应急车道
- 方案B：动态修改lane的`allow`属性

**核心参数**：
- 路段范围 (`edge_id`, `lane_index`)
- 开放时间段 (`open_time_begin`, `open_time_end`)
- 触发条件 (`congestion_threshold`)
- 允许车型 (`allowed_vClass`)

---

#### 4.2.3 货车限行 (TEC-TB)

**业务场景**：高峰期货车管控、特定时段限行

**SUMO实现**：
```xml
<closingReroute id="tec_tb_1" edge="entrance_1"
                disallow="truck trailer"
                begin="25200" end="32400"/>
```

**核心参数**：
- 入口edge ID (`entrance_edge_id`)
- 限行时间段 (`time_begin`, `time_end`)
- 禁止车型列表 (`disallowed_vClass`)

---

#### 4.2.4 入口关闭 (TEC-EC)

**业务场景**：应急管理、事故封路、临时封闭

**SUMO实现**：
```xml
<closingReroute id="tec_ec_1" edge="entrance_1"
                allow=""
                begin="0" end="3600"/>
```

**核心参数**：
- 入口edge ID (`entrance_edge_id`)
- 关闭时间段 (`time_begin`, `time_end`)
- 改道提示（可选）

---

## 5. 业务流程设计

### 5.1 端到端流程

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  全局资源管理流程（一次创建，多次复用）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────┐
│ 策略管理    │  选模板 → 配置路段和参数 → 保存策略实例
└──────┬──────┘  （全局资源，可跨案例复用）
       ↓
┌─────────────┐
│ 方案管理    │  选策略 → 组合方案 → 生成control.add.xml模板
└──────┬──────┘  （全局资源，描述通用管控场景）
       │
━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  案例级应用流程（每次运行创建新实例）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
       │
       ↓ 应用Plan到Case
┌─────────────┐
│ 批量仿真    │  选Case + 选Plans → 创建仿真实例 → 批量运行 → 监控进度
└──────┬──────┘  （案例级资源，绑定到case_id和batch_id）
       │          每个Plan创建一个Simulation实例
       ↓
┌─────────────┐
│ 方案优化    │  选批次 → 配置指标 → 计算排名 → 对比分析
└──────┬──────┘  （提取仿真结果，更新Plan的validation_records）
       ↓
    [ Plan的验证记录更新 ]
```

### 5.2 Plan管理流程（全局）

```
用户操作                    系统行为                     存储位置
──────────                  ──────────                   ────────────
选择策略实例                加载策略列表                 control_data/strategies/
   ↓
选择多个策略                验证策略兼容性
(可拖拽排序)
   ↓
配置方案元数据              生成plan_id                  control_data/plans/{plan_id}/
- 名称                      (语义化ID)
- 描述
- 标签
- 适用条件(通用)
- 预期效果(范围)
   ↓
预览配置                    根据策略生成                 control_data/plans/{plan_id}/
                           control.add.xml模板           control.add.xml
   ↓
保存方案                    保存元数据和策略引用          plan_metadata.json
                                                        strategy_refs.json
                           更新plans_index.json
```

**关键点**：
- ✅ Plan是全局的，不绑定case
- ✅ 适用条件和预期效果是通用描述
- ✅ control.add.xml是模板，可复用

### 5.3 仿真管理流程（案例级）

```
用户操作                    系统行为                     存储位置
──────────                  ──────────                   ────────────
选择Case                    加载案例信息                 cases/{case_id}/
   ↓
选择多个Plans               加载方案列表                 control_data/plans/
(含基准方案)
   ↓
配置仿真参数                验证参数合法性
- begin                     - 检查时间范围
- end                       - 检查step_length
- step_length
- 其他SUMO参数
   ↓
提交批量仿真                创建batch_id                 cases/{case_id}/control_simulations/
                           生成批次目录                  {batch_id}/
   ↓
系统为每个Plan              创建仿真实例目录              {batch_id}/{plan_id}_sim/
创建Simulation
   ↓
                           复制Plan的                    {plan_id}_sim/control.add.xml
                           control.add.xml
   ↓
                           复制Case的网络/路由文件       {plan_id}_sim/
   ↓
                           生成simulation.sumocfg       {plan_id}_sim/simulation.sumocfg
   ↓
                           生成simulation_metadata      {plan_id}_sim/simulation_metadata.json
                           (关联plan_id和case_id)
   ↓
并行运行仿真                启动SUMO进程
                           更新进度状态
   ↓
仿真完成                    保存仿真结果                 summary.xml, tripinfo.xml等
```

**关键点**：
- ✅ Simulation实例绑定到case_id和batch_id
- ✅ 每个Plan创建一个独立的Simulation实例
- ✅ control.add.xml从Plan复制，可能根据Case微调
- ✅ simulation_metadata.json记录plan_id关联

### 5.4 优化分析流程

```
用户操作                    系统行为                     更新目标
──────────                  ──────────                   ────────────
选择批次                    加载批次中所有仿真实例        cases/{case_id}/control_simulations/
                                                        {batch_id}/
   ↓
配置评估指标                加载指标配置模板
- 权重
- 方向(maximize/minimize)
   ↓
计算指标                    从每个仿真实例提取            summary.xml, tripinfo.xml
                           - 平均行程时间
                           - 总延误
                           - 平均速度
                           - 通行量
   ↓
排序方案                    多目标加权排序
                           生成排名结果
   ↓
查看对比                    生成对比图表
- 雷达图                    - 各方案指标对比
- 柱状图                    - TOP-N排名
   ↓
更新验证记录                将仿真结果添加到              control_data/plans/{plan_id}/
                           Plan的validation_records      plan_metadata.json
                           {
                             case_id,
                             batch_id,
                             road_segment,
                             baseline_metrics,
                             improvement_metrics
                           }
```

**关键点**：
- ✅ 评估基于Simulation实例的结果
- ✅ 排序帮助选择最优Plan
- ✅ 结果反馈到Plan的验证记录，积累效果数据

### 5.5 用户工作流程与页面导航

#### 5.5.1 完整工作流程

```
┌─────────────────┐
│  策略管理页面    │  创建策略实例（全局资源）
│  templates.html  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  方案管理页面    │  组合策略，生成方案（全局资源）
│  plans.html      │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────────────────────┐
│           批量仿真页面 (simulations.html)            │
│                                                      │
│  视图1: 配置                                         │
│  - 选择Case + Plans                                  │
│  - 配置随机种子参数                                   │
│  - [创建批次]                                        │
│                                                      │
│  视图2: 进度                                         │
│  - 实时监控（轮询每2秒）                              │
│  - 显示任务状态（pending/running/completed）          │
│  - [取消批次]                                        │
│                                                      │
│  视图3: 结果（基础版）                                │
│  - 方案对比表                                        │
│  - 在网车辆峰值曲线                                   │
│  - [查看详细优化分析] ──────┐                        │
└─────────────────────────────┼────────────────────────┘
                              │ 跳转（传递batch_id）
                              │
                              ↓
┌─────────────────────────────────────────────────────┐
│         方案优化页面 (optimization.html)             │
│                                                      │
│  URL: optimization.html?batch_id=batch_001          │
│                                                      │
│  - 批次信息卡片                                      │
│  - 方案对比表（带改善百分比）                         │
│  - 在网车辆峰值曲线（详细版）                         │
│  - 多指标雷达图（归一化对比）                         │
│  - [返回批量仿真] [导出详细报告]                      │
└─────────────────────────────────────────────────────┘
```

#### 5.5.2 页面导航关系

| 源页面 | 目标页面 | 导航方式 | URL参数 | 触发条件 |
|--------|---------|---------|---------|---------|
| simulations.html（结果视图） | optimization.html | 按钮点击 | `?batch_id={batch_id}` | 批次完成 |
| optimization.html | simulations.html | 按钮点击 | 无 | 用户主动返回 |
| 外部链接/书签 | optimization.html | 直接访问 | `?batch_id={batch_id}` | - |

#### 5.5.3 URL参数传递机制

**批量仿真页面 → 方案优化页面**：

```javascript
// simulations.html 的 batch_simulation.js
function viewOptimizationAnalysis() {
    if (!currentBatchId) {
        showError('未找到批次ID');
        return;
    }

    // 跳转到方案优化页面，传递 batch_id 参数
    window.location.href = `optimization.html?batch_id=${currentBatchId}`;
}
```

**方案优化页面接收参数**：

```javascript
// optimization.html 的 optimization.js
document.addEventListener('DOMContentLoaded', async () => {
    // 从URL参数读取batch_id
    const urlParams = new URLSearchParams(window.location.search);
    const batchId = urlParams.get('batch_id');

    if (batchId) {
        // URL包含batch_id，直接加载该批次结果
        currentBatchId = batchId;
        await loadBatchResults(batchId);
    } else {
        // 显示批次选择界面（或提示返回批量仿真页面）
        showBatchSelector();
    }
});
```

#### 5.5.4 用户操作序列

**典型场景：从策略创建到结果分析**

1. **策略管理阶段**：
   - 访问 `templates.html`
   - 选择模板 → 配置路段 → 配置参数 → 创建策略实例

2. **方案管理阶段**：
   - 访问 `plans.html`
   - 选择多个策略 → 组合方案 → 保存

3. **批量仿真阶段**：
   - 访问 `simulations.html`
   - **配置视图**：选择Case + Plans → 配置种子 → 创建批次
   - **进度视图**：启动仿真 → 监控进度
   - **结果视图**：查看基础对比 → 点击"查看详细优化分析"

4. **方案优化阶段**：
   - 自动跳转到 `optimization.html?batch_id=batch_001`
   - 查看详细的方案对比表（含改善百分比）
   - 分析在网车辆峰值曲线（识别峰值时刻）
   - 查看多指标雷达图（综合评估）
   - 导出详细报告或返回批量仿真

### 5.6 模块交互图

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  全局资源层
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌────────────────┐      ┌────────────────┐
│  策略模板库    │─────→│  策略实例库    │
│  (Templates)   │ 实例化│  (Strategies)  │
└────────────────┘      └────────┬───────┘
                                 │
                                 ↓ 组合
                        ┌────────────────┐
                        │   方案库       │  ← 全局资源
                        │   (Plans)      │    可复用
                        └────────┬───────┘
                                 │
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━
  案例级资源层
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                 │
                                 ↓ 应用到Case（创建Simulation）
                        ┌────────────────┐
         ┌─────────────→│  仿真实例      │  ← 案例级资源
         │              │  (Simulations) │    一次性
         │  提供网络/路由└────────┬───────┘
         │                       │
  案例数据 (Case)                 ↓ 批量管理
         │              ┌────────────────┐
         │              │  批量仿真      │
         │              │  (Batch)       │
         │              └────────┬───────┘
         │                       │
         │                       ↓ 提取指标
         │              ┌────────────────┐
         └─────────────→│  优化分析      │
                        │  (Optimization)│
                        └────────┬───────┘
                                 │
                                 ↓ 更新validation_records
                        ┌────────────────┐
                        │   方案库       │  ← 反馈到全局
                        │   (Plans)      │    验证记录
                        └────────────────┘
```

---

## 6. 后端架构设计

### 6.1 架构分层

遵循现有项目的**两层模块化架构**：

```
┌─────────────────────────────────────┐
│         API Layer (api/)            │
│  ┌───────────┐    ┌──────────────┐ │
│  │  Routes   │───→│  Services    │ │
│  └───────────┘    └──────┬───────┘ │
└────────────────────────────┼────────┘
                             ↓
┌────────────────────────────┼────────┐
│      Shared Layer (shared/)│        │
│  ┌──────────────────────────┴─────┐ │
│  │  control_tools/                │ │
│  │  - template_parser             │ │
│  │  - additional_generator        │ │
│  │  - edge_selector               │ │
│  │  - evaluation_calculator       │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 6.2 API层设计

#### 6.2.1 Routes

```
api/routes/
├── control_strategy_routes.py      # 策略管理路由
│   - GET /api/v1/control/templates/
│   - GET /api/v1/control/strategies/
│   - POST /api/v1/control/strategies/
│   - PUT /api/v1/control/strategies/{id}
│   - DELETE /api/v1/control/strategies/{id}
│
├── control_plan_routes.py          # 方案管理路由
│   - GET /api/v1/control/plans/
│   - POST /api/v1/control/plans/
│   - PUT /api/v1/control/plans/{id}
│   - DELETE /api/v1/control/plans/{id}
│   - POST /api/v1/control/plans/{id}/generate_additional
│
├── control_simulation_routes.py    # 并行仿真路由
│   - POST /api/v1/control/simulations/batch
│   - GET /api/v1/control/simulations/batch/{batch_id}
│   - GET /api/v1/control/simulations/batch/{batch_id}/progress
│   - DELETE /api/v1/control/simulations/batch/{batch_id}
│
└── control_optimization_routes.py  # 优化分析路由
    - POST /api/v1/control/optimizations/
    - GET /api/v1/control/optimizations/{id}
    - GET /api/v1/control/optimizations/{id}/ranking
    - GET /api/v1/control/optimizations/{id}/comparison
```

#### 6.2.2 Services

```
api/services/
├── control_strategy_service.py     # 策略管理服务
│   - list_templates()
│   - create_strategy()
│   - update_strategy()
│   - delete_strategy()
│   - get_strategy_detail()
│
├── control_plan_service.py         # 方案管理服务
│   - create_plan()
│   - update_plan()
│   - delete_plan()
│   - generate_additional_file()
│   - validate_plan()
│
├── control_batch_sim_service.py    # 批量仿真服务
│   - create_batch_simulation()
│   - run_batch_simulation()
│   - get_batch_progress()
│   - cancel_batch()
│
└── control_optimization_service.py # 优化分析服务
    - create_optimization()
    - calculate_metrics()
    - rank_plans()
    - generate_comparison()
```

#### 6.2.3 Models

```
api/models/control/
├── requests/
│   ├── strategy_request.py
│   ├── plan_request.py
│   ├── batch_simulation_request.py
│   └── optimization_request.py
│
├── responses/
│   ├── strategy_response.py
│   ├── plan_response.py
│   ├── batch_simulation_response.py
│   └── optimization_response.py
│
└── entities/
    ├── template.py
    ├── strategy.py
    ├── plan.py
    ├── batch_simulation.py
    └── optimization.py
```

### 6.3 共享层设计

```
shared/control_tools/
├── __init__.py
├── template_parser.py              # 模板解析器
│   - parse_template()
│   - validate_template()
│   - get_parameter_schema()
│
├── additional_generator.py         # Additional文件生成器
│   - generate_control_additional()
│   - generate_vss_xml()
│   - generate_dhs_xml()
│   - generate_tec_xml()
│
└── evaluation_calculator.py        # 评估指标计算器
    - extract_metrics_from_tripinfo()
    - extract_metrics_from_summary()
    - calculate_composite_score()
    - rank_plans()

shared/data_access/
├── edge_query.py                   # 路段选择数据库查询（新增）⭐
│   - query_edges_with_filters()    # 多维度筛选路段
│   - query_nodes_by_type()         # 查询节点信息
│   - query_gantries_on_edge()      # 查询路段上的门架
│   - get_route_codes()             # 获取可用路线编码
│
└── connection.py                   # 数据库连接（现有）
    - open_db_connection()
```

**edge_query.py 功能说明**：

边选择器的核心数据访问模块，从dim schema的以下表查询数据：
- `dim.sim_network_edges` - 路段主表（edge_id, route_code, start_stake, end_stake, length, num_lanes）
- `dim.multiscale_node_units` - 节点单元表（node_type: diverging, merging, entrance, exit等）
- `dim.sim_network_junctions` - 节点表（junction坐标）
- `dim.point_gantry` - 门架点表（门架位置和桩号）

支持多维度筛选条件：
- 路线编码（route_code: G4202, G5, SA2等）
- 节点类型（分流点diverging、汇流点merging、入口entrance、出口exit）
- 桩号范围（start_stake, end_stake）
- 路段长度范围（length）
- 方向（route_direction: clockwise/counterclockwise）
- 示范段ID（demonstration_id）
- 车道数（num_lanes）
- 门架筛选（是否仅返回有门架的路段）

**详细设计文档**: [edge_selector_database_design.md](design/edge_selector_database_design.md)

---

## 7. 前端架构设计

### 7.1 页面布局

```
┌────────────────────────────────────────────────────┐
│  顶栏：交通管控仿真优化系统         [返回主系统]   │
├──────────┬─────────────────────────────────────────┤
│          │                                         │
│  左侧导航 │          主内容区                        │
│          │                                         │
│  ━━━━━━  │                                         │
│  策略管理 │                                         │
│  方案管理 │                                         │
│  并行仿真 │                                         │
│  方案优化 │                                         │
│          │                                         │
└──────────┴─────────────────────────────────────────┘
```

### 7.2 前端文件结构

```
frontend/control/
├── index.html                      # 入口页面
├── styles.css                      # 全局样式
├── app.js                          # 主应用逻辑
└── components/
    ├── strategy_manager.js         # 策略管理组件
    ├── plan_manager.js             # 方案管理组件
    ├── batch_simulator.js          # 并行仿真组件
    ├── optimizer.js                # 优化分析组件
    └── edge_selector.js            # 边选择器组件
```

### 7.3 四个核心页面

#### 7.3.1 策略管理页面

**布局设计（三步向导式工作流）**：

**工作流步骤指示器**：
```
┌────────────────────────────────────────────────┐
│  (1) 选择模板  →  (2) 选择路段  →  (3) 配置参数│
└────────────────────────────────────────────────┘
```

**步骤1 - 选择策略模板**：
- 模板卡片网格展示（VSS、DHS、TEC）
- 卡片信息：模板名称、策略类型标签、描述
- 支持卡片选中状态（高亮显示）
- 选中后自动进入步骤2

**步骤2 - 选择管控路段**：
- 边选择器组件区域（占位，Phase 1B实现）
- 提示文字："边选择器功能（Phase 1B）- 支持从数据库查询路段、多维度筛选、路网可视化"
- 已选路段标签列表
- 操作按钮：上一步、下一步

**步骤3 - 配置策略参数**：
- 动态生成参数表单（基于模板的 parameters_schema）
- 表单字段：
  - 策略名称（必填）
  - 策略描述（可选）
  - 各模板参数（根据类型生成input/select控件）
- 参数提示：单位、范围、默认值
- 操作按钮：上一步、重置、生成策略实例

**底部区域 - 已创建策略实例列表**：
- 策略卡片展示
- 每个策略显示：名称、类型标签、元信息
- 操作：查看详情、编辑、删除

**交互流程**：
```
选择模板(步骤1) → 选择路段(步骤2) → 配置参数(步骤3) → 生成策略实例
      ↓                                            ↓
    自动进入步骤2                              显示在底部列表
```

---

#### 7.3.2 方案管理页面

**功能区块**：
1. **左侧**：方案列表（卡片或列表）
2. **右侧**：方案详情编辑
   - 基本信息（名称、描述、标签）
   - 策略选择器（多选）
   - 已选策略列表（可排序、移除）
   - Additional文件预览
   - 保存/删除按钮

**交互流程**：
```
新建方案 → 选择策略 → 预览配置 → 保存方案
```

---

#### 7.3.3 批量仿真页面 (simulations.html)

**功能区块**：

**三个视图（Tabs切换）**：

1. **配置视图**：
   - 案例选择（下拉框）
   - 方案多选（复选框列表，baseline自动选中）
   - 仿真参数配置（随机种子数、起始种子）
   - 预估信息（总任务数）
   - 提交按钮

2. **进度视图**：
   - 批次信息卡片（batch_id、状态）
   - 总进度条
   - 任务列表（按方案分组，显示每个种子的状态）
   - 启动/取消按钮

3. **结果视图**：
   - 方案对比表格（基础版）
   - 在网车辆峰值曲线图
   - **"查看详细优化分析"按钮**（跳转到optimization.html）
   - 导出结果按钮

**交互流程**：
```
配置视图: 选择案例 → 选择方案 → 配置参数 → 创建批次
    ↓
进度视图: 启动仿真 → 实时监控（每2秒轮询）
    ↓
结果视图: 查看基础对比 → 点击"查看详细优化分析" → 跳转到optimization.html?batch_id=xxx
```

**导航目标**：
- 批次完成后 → `optimization.html?batch_id={batch_id}`（传递batch_id参数）

---

#### 7.3.4 方案优化页面 (optimization.html)

**页面定位**：详细的方案对比分析和可视化

**功能区块**：

1. **批次信息区**：
   - 批次ID、案例ID、方案数量、完成时间
   - （如果URL没有batch_id参数，显示批次选择界面）

2. **方案对比表**：
   - 平均行程时间、平均速度、总车辆数
   - **相比基准的改善百分比**（带颜色和箭头指示）
   - 自动计算并高亮最优方案

3. **在网车辆峰值曲线**：
   - 多方案对比折线图（Chart.js）
   - X轴：仿真时间（HH:MM格式）
   - Y轴：在网车辆数
   - 支持交互（悬停查看数值、图例切换）
   - 峰值指标卡片（每个方案的峰值车辆数、峰值时刻、平均车辆数）

4. **多指标雷达图**：
   - 5个维度：平均速度、行程时间、总车辆数、峰值车辆数、系统稳定性
   - 归一化到0-100范围
   - 多方案叠加对比
   - 图例说明（指标含义和方向）

5. **操作按钮**：
   - 返回批量仿真
   - 导出详细报告

**页面加载逻辑**：
```javascript
// URL: optimization.html?batch_id=batch_001

window.onload = () => {
  const urlParams = new URLSearchParams(window.location.search);
  const batchId = urlParams.get('batch_id');

  if (batchId) {
    // URL包含batch_id，直接加载该批次结果
    loadBatchResults(batchId);
  } else {
    // 显示批次选择界面（或提示返回批量仿真页面）
    showBatchSelector();
  }
};
```

**交互流程**：
```
从批量仿真页面跳转（带batch_id） → 加载批次结果 → 展示详细分析
    ↓
查看对比表、峰值曲线、雷达图 → 分析方案优劣 → 导出报告/返回
```

**导航来源**：
- 来自 `simulations.html` 的"查看详细优化分析"按钮
- URL格式：`optimization.html?batch_id={batch_id}`

---

## 8. 核心数据模型

### 8.1 策略模板 (ControlTemplate)

```json
{
  "template_id": "vss_moderate_001",
  "template_name": "中度可变限速",
  "strategy_type": "VARIABLE_SPEED_SIGN",
  "description": "适用于恶劣天气或中度拥堵",
  "parameters_schema": {
    "edges": {
      "type": "array",
      "description": "路段ID列表",
      "required": true
    },
    "time_begin": {
      "type": "integer",
      "description": "开始时间(秒)",
      "required": true
    },
    "time_end": {
      "type": "integer",
      "description": "结束时间(秒)",
      "required": true
    },
    "speed_limit": {
      "type": "float",
      "description": "限速值(m/s)",
      "required": true
    }
  },
  "default_values": {
    "speed_limit": 22.22
  },
  "sumo_element_type": "variableSpeedSign"
}
```

### 8.2 策略实例 (Strategy)

```json
{
  "strategy_id": "strategy_001",
  "strategy_name": "成雅高速可变限速A",
  "template_id": "vss_moderate_001",
  "configured_params": {
    "edges": ["edge_100", "edge_101", "edge_102"],
    "time_begin": 7200,
    "time_end": 10800,
    "speed_limit": 19.44
  },
  "created_at": "2025-10-19T10:00:00",
  "updated_at": "2025-10-19T10:00:00",
  "description": "早高峰可变限速，限速70km/h",
  "tags": ["早高峰", "可变限速"]
}
```

### 8.3 管控方案 (Plan)

```json
{
  "plan_id": "plan_001",
  "plan_name": "综合管控方案A",
  "plan_type": "CONTROL",
  "strategy_ids": ["strategy_001", "strategy_005", "strategy_012"],
  "description": "组合VSS+DHS+TEC，适用于早高峰",
  "created_at": "2025-10-19T11:00:00",
  "updated_at": "2025-10-19T11:00:00",
  "tags": ["高峰期", "综合管控"],
  "additional_file_path": "control_data/plans/plan_001/control.add.xml"
}
```

### 8.4 批量仿真 (BatchSimulation)

```json
{
  "batch_id": "batch_001",
  "case_id": "case_20251019_001",
  "plan_ids": ["plan_baseline", "plan_001", "plan_002", "plan_003"],
  "simulation_config": {
    "gui": false,
    "begin": 0,
    "end": 14400,
    "step_length": 1
  },
  "status": "RUNNING",
  "progress": {
    "plan_baseline": {
      "status": "COMPLETED",
      "progress": 100,
      "sim_id": "sim_001"
    },
    "plan_001": {
      "status": "RUNNING",
      "progress": 45,
      "sim_id": "sim_002"
    },
    "plan_002": {
      "status": "PENDING",
      "progress": 0,
      "sim_id": null
    },
    "plan_003": {
      "status": "PENDING",
      "progress": 0,
      "sim_id": null
    }
  },
  "created_at": "2025-10-19T12:00:00",
  "started_at": "2025-10-19T12:01:00",
  "completed_at": null
}
```

### 8.5 优化分析 (Optimization)

```json
{
  "optimization_id": "opt_001",
  "batch_id": "batch_001",
  "case_id": "case_20251019_001",
  "metrics_config": {
    "avg_travel_time": {"weight": 0.4, "direction": "minimize"},
    "total_delay": {"weight": 0.3, "direction": "minimize"},
    "avg_speed": {"weight": 0.2, "direction": "maximize"},
    "throughput": {"weight": 0.1, "direction": "maximize"}
  },
  "ranking": [
    {
      "rank": 1,
      "plan_id": "plan_002",
      "plan_name": "方案B",
      "composite_score": 0.85,
      "metrics": {
        "avg_travel_time": 1200.5,
        "total_delay": 45000,
        "avg_speed": 25.3,
        "throughput": 4500
      }
    },
    {
      "rank": 2,
      "plan_id": "plan_001",
      "plan_name": "方案A",
      "composite_score": 0.78,
      "metrics": {
        "avg_travel_time": 1350.2,
        "total_delay": 52000,
        "avg_speed": 23.1,
        "throughput": 4300
      }
    }
  ],
  "created_at": "2025-10-19T14:00:00"
}
```

---

## 9. 关键技术实现要点

### 9.1 边选择器 (Edge Selector)

**技术方案**：
1. 解析net.xml，提取edge信息（ID、位置、长度）
2. 使用Canvas/SVG绘制路网简图
3. 支持交互：点击选择、框选、搜索过滤
4. 高亮显示已选路段

**数据流**：
```
net.xml → edge_selector.parse_network() → edge_info_list
         ↓
前端Canvas绘图 → 用户点击 → selected_edge_ids
         ↓
提交到策略配置
```

---

### 9.2 Additional文件生成

**生成流程**：
```python
def generate_control_additional(plan: Plan, strategies: List[Strategy]) -> str:
    """根据方案和策略列表生成SUMO additional文件"""
    additional_xml = ['<additional>']

    for strategy in strategies:
        if strategy.template.strategy_type == "VSS":
            additional_xml.append(generate_vss_xml(strategy))
        elif strategy.template.strategy_type == "DHS":
            additional_xml.append(generate_dhs_xml(strategy))
        elif strategy.template.strategy_type == "TEC":
            additional_xml.append(generate_tec_xml(strategy))

    additional_xml.append('</additional>')

    # 验证XML格式
    validate_xml(''.join(additional_xml))

    return ''.join(additional_xml)
```

---

### 9.3 并行仿真调度

**调度策略**：
```python
async def run_batch_simulation(batch: BatchSimulation):
    """并行运行多个方案的仿真"""
    for plan_id in batch.plan_ids:
        # 1. 创建仿真目录
        sim_dir = create_simulation_directory(batch.case_id, batch.batch_id, plan_id)

        # 2. 复制案例配置文件
        copy_case_config_files(batch.case_id, sim_dir)

        # 3. 添加control.add.xml到sumocfg
        plan = load_plan(plan_id)
        add_control_additional_to_sumocfg(sim_dir, plan.additional_file_path)

        # 4. 启动仿真进程（并发控制）
        await start_simulation_async(sim_dir, batch.simulation_config)

        # 5. 更新进度
        update_batch_progress(batch.batch_id, plan_id, status="RUNNING")
```

**并发控制**：使用信号量限制同时运行的仿真数量（如最多4个）

---

### 9.4 评估指标计算

**指标提取**：
```python
def calculate_metrics(simulation_result_path: str) -> dict:
    """从仿真结果提取评估指标"""
    tripinfo_file = os.path.join(simulation_result_path, "tripinfo.xml")
    summary_file = os.path.join(simulation_result_path, "summary.xml")

    metrics = {}

    # 从tripinfo.xml提取
    metrics['avg_travel_time'] = extract_avg_travel_time(tripinfo_file)
    metrics['total_delay'] = extract_total_delay(tripinfo_file)

    # 从summary.xml提取
    metrics['avg_speed'] = extract_avg_speed(summary_file)
    metrics['throughput'] = extract_throughput(summary_file)

    return metrics
```

**排序算法**：
```python
def rank_plans(plans_metrics: dict, weights: dict) -> list:
    """多目标加权排序"""
    # 1. 归一化各指标（Min-Max归一化）
    normalized = normalize_metrics(plans_metrics)

    # 2. 加权求和
    for plan_id, metrics in normalized.items():
        score = 0
        for metric_name, metric_value in metrics.items():
            weight = weights[metric_name]['weight']
            direction = weights[metric_name]['direction']

            # minimize指标：分数 = 1 - normalized_value
            # maximize指标：分数 = normalized_value
            if direction == 'minimize':
                score += weight * (1 - metric_value)
            else:
                score += weight * metric_value

        plans_metrics[plan_id]['composite_score'] = score

    # 3. 排序
    sorted_plans = sorted(plans_metrics.items(),
                         key=lambda x: x[1]['composite_score'],
                         reverse=True)

    return sorted_plans
```

---

## 10. 与现有系统的关系

### 10.1 复用现有功能

| 现有模块 | 复用方式 | 复用内容 |
|---------|---------|---------|
| `simulation_service` | 调用 | 仿真调度、进度监控 |
| `sumo_utils` | 调用 | sumocfg生成、SUMO进程管理 |
| `file_utils` | 调用 | 文件操作、路径处理 |
| Case数据 | 引用 | 作为仿真的基础数据 |

### 10.2 扩展新功能

| 新增模块 | 位置 | 功能 |
|---------|------|------|
| `control_strategy_routes` | `api/routes/` | 策略管理API |
| `control_plan_routes` | `api/routes/` | 方案管理API |
| `control_simulation_routes` | `api/routes/` | 并行仿真API |
| `control_optimization_routes` | `api/routes/` | 优化分析API |
| `control_tools/` | `shared/` | 管控工具集 |

### 10.3 独立部分

- **前端页面**：独立的HTML/CSS/JS，不影响现有前端
- **数据存储**：独立的`control_data/`目录，不影响现有案例数据

### 10.4 集成点

```
现有系统 (OD仿真) ←→ 管控功能域
         │
         ├─ 共享 Case数据
         ├─ 共享 Network文件
         ├─ 复用 Simulation引擎
         └─ 独立 前端页面/数据存储
```

---

## 11. 开发路线图

### Phase 1: 策略管理模块 (2-3周)

**目标**：实现策略模板管理和策略实例创建

**任务**：
- [ ] 设计策略模板JSON Schema
- [ ] 创建模板示例文件（VSS, DHS, TEC）
- [ ] 实现模板解析器 (`template_parser.py`)
- [ ] 开发策略CRUD API (`control_strategy_routes.py`, `control_strategy_service.py`)
- [ ] 开发前端策略管理页面
- [ ] 实现边选择器原型（基于静态路网图）
- [ ] 单元测试

---

### Phase 2: 方案管理模块 (2-3周)

**目标**：实现方案组建和Additional文件生成

**任务**：
- [ ] 设计方案数据模型
- [ ] 实现Additional文件生成器 (`additional_generator.py`)
  - [ ] VSS生成逻辑
  - [ ] DHS生成逻辑
  - [ ] TEC生成逻辑
- [ ] 开发方案CRUD API (`control_plan_routes.py`, `control_plan_service.py`)
- [ ] 开发前端方案管理页面
- [ ] 实现方案预览功能
- [ ] XML格式验证
- [ ] 集成测试

---

### Phase 3: 并行仿真模块 (3-4周)

**目标**：实现批量仿真调度和进度监控

**任务**：
- [ ] 设计批量仿真调度器
- [ ] 实现并发控制机制（信号量）
- [ ] 开发批量仿真API (`control_simulation_routes.py`, `control_batch_sim_service.py`)
- [ ] 扩展现有`simulation_service`以支持管控仿真
- [ ] 实现进度跟踪和状态更新
- [ ] 开发前端并行仿真页面
- [ ] 实现实时进度监控（轮询或WebSocket）
- [ ] 错误处理和重试机制
- [ ] 性能测试（大规模并行）

---

### Phase 4: 方案优化模块 (2-3周)

**目标**：实现评估指标计算和方案排序

**任务**：
- [ ] 设计评估指标体系
- [ ] 实现指标提取器 (`evaluation_calculator.py`)
  - [ ] tripinfo.xml解析
  - [ ] summary.xml解析
  - [ ] edgedata.xml解析（可选）
- [ ] 实现多目标排序算法
- [ ] 开发优化分析API (`control_optimization_routes.py`, `control_optimization_service.py`)
- [ ] 开发前端优化页面
- [ ] 实现可视化对比图表（雷达图、柱状图）
- [ ] 报告生成和导出功能
- [ ] 端到端测试

---

### Phase 5: 完善与优化 (1-2周)

**目标**：系统优化、文档完善、用户验证

**任务**：
- [ ] 完善边选择器（支持动态路网加载、缩放、搜索）
- [ ] 性能优化（大规模方案并行、数据库索引）
- [ ] UI/UX优化（加载提示、错误提示、操作引导）
- [ ] 代码重构和清理
- [ ] 完善API文档（OpenAPI规范）
- [ ] 编写用户手册
- [ ] 用户验收测试（UAT）
- [ ] Bug修复和优化

---

## 12. 后续细化方向

本文档提供设计梗概，后续将使用**spec-kit**工具逐步细化以下内容：

1. **详细的API规范**：使用`/speckit.specify`生成各API的详细规范
2. **实施计划**：使用`/speckit.plan`生成每个模块的实施计划
3. **任务分解**：使用`/speckit.tasks`生成具体的开发任务清单
4. **质量检查**：使用`/speckit.checklist`生成测试检查清单
5. **一致性分析**：使用`/speckit.analyze`进行跨模块一致性检查

---

## 附录

### A. 缩写说明

| 缩写 | 全称 | 说明 |
|------|------|------|
| VSS | Variable Speed Sign | 可变限速 |
| DHS | Dynamic Hard Shoulder | 动态硬路肩 |
| TEC | Toll Entrance Control | 收费入口控制 |
| TB | Truck Ban | 货车限行 |
| EC | Entrance Closure | 入口关闭 |

### B. 参考资料

- [SUMO Documentation - Additional Files](https://sumo.dlr.de/docs/Simulation/Rerouter.html)
- [SUMO Variable Speed Signs](https://sumo.dlr.de/docs/Simulation/Variable_Speed_Signs.html)
- 现有项目文档：`docs/development/新架构开发指南.md`
- 现有项目文档：`docs/api_docs/新架构API指南.md`

---

**文档结束**
