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

## 2. 核心概念模型 ✅ 两层架构

### 2.1 策略-方案两层架构

基于 `sumo_control_strategies_research.md` 的研究成果，系统采用**策略-方案两层架构**：

```
┌─────────────────────────────────────────────────────────┐
│                   策略模板层 (Template)                  │
│  预定义的管控措施配置模板（全局，高复用性）               │
│  - VSS模板、DHS模板、TEC模板                            │
└────────────────────┬────────────────────────────────────┘
                     ↓ 实例化（选择路段 + 配置参数）
┌─────────────────────────────────────────────────────────┐
│                   策略实例层 (Strategy)                  │
│  针对特定路段/入口的单一管控措施（全局，可跨案例复用）    │
│  - 单一路段区间或单一入口的独立管控措施                  │
│  - 可独立运行，可被多个方案引用                          │
└────────────────────┬────────────────────────────────────┘
                     ↓ 组合（选择多个策略）
┌─────────────────────────────────────────────────────────┐
│                   管控方案层 (Plan)                      │
│  多个策略的组合，形成完整管控措施集（全局，可跨案例复用）  │
│  - 方案 = 策略1 + 策略2 + 策略3 + ...                   │
│  - 支持基准方案（无管控，用于对比）                      │
└────────────────────┬────────────────────────────────────┘
                     ↓ 生成SUMO配置
┌─────────────────────────────────────────────────────────┐
│                 SUMO配置文件 (control.add.xml)            │
│  包含所有策略的XML元素，按类型排序（VSS→DHS→TEC）        │
└────────────────────┬────────────────────────────────────┘
                     ↓ 应用到案例
┌─────────────────────────────────────────────────────────┐
│              批量仿真 (Batch Simulation)                 │
│  在特定案例上运行多个方案，对比评估效果                   │
└────────────────────┬────────────────────────────────────┘
                     ↓ 评估分析
┌─────────────────────────────────────────────────────────┐
│                  优化结果 (Optimization)                  │
│  多目标排序，筛选最优方案                                │
└─────────────────────────────────────────────────────────┘
```

**核心设计原则**：

- **策略（Strategy）**：单一控制对象的独立管控措施
  - 一个路段区间 OR 一个入口
  - 一种管控类型（VSS/DHS/TEC）
  - 可独立运行、可复用

- **方案（Plan）**：多个策略的业务组合
  - ≥0个策略（基准方案为0）
  - 以解决问题为目标（如"早高峰综合管控"）
  - 生成独立的control.add.xml

### 2.2 核心概念定义

| 概念 | 定义 | 全局/案例级 | 可复用性 |
|------|------|------------|---------|
| **策略模板** | 预定义的管控措施配置模板 | 全局 | 高 |
| **策略实例** | 基于模板创建的具体策略 | 全局 | 高（跨案例） |
| **管控方案** | 多个策略的组合（策略集） | 全局 | 高（跨案例） |
| **批量仿真** | 在特定案例上运行多个方案 | 案例级 | 无 |
| **优化分析** | 基于仿真结果的评估排序 | 全局（关联批次） | 可参考 |

---

## 3. 数据架构设计

### 3.1 全局资源存储

#### 3.1.1 策略模板（复用现有templates目录）

```
templates/
├── control_strategies/              # 新增：策略模板库
│   ├── variable_speed_sign/        # 可变限速
│   │   ├── vss_moderate.json
│   │   ├── vss_strict.json
│   │   └── README.md
│   ├── dynamic_hard_shoulder/      # 动态硬路肩
│   │   ├── dhs_peak_hours.json
│   │   ├── dhs_congestion_triggered.json
│   │   └── README.md
│   ├── toll_entrance_control/      # 收费入口控制
│   │   ├── tec_truck_ban_daytime.json
│   │   ├── tec_entrance_close_emergency.json
│   │   └── README.md
│   └── templates_index.json        # 模板索引文件
```

#### 3.1.2 全局管控数据

```
control_data/                        # 新增：全局管控数据目录
├── strategies/                      # 策略实例库
│   ├── {strategy_id}.json          # 策略定义文件
│   └── strategies_index.json       # 策略索引
├── plans/                           # 方案库
│   ├── {plan_id}/
│   │   ├── plan_metadata.json      # 方案元数据
│   │   ├── strategy_refs.json      # 引用的策略ID列表
│   │   └── control.add.xml         # 生成的SUMO additional文件
│   └── plans_index.json            # 方案索引
└── optimizations/                   # 优化分析记录（全局存储）
    ├── {optimization_id}/
    │   ├── metadata.json            # 关联case_id, batch_id
    │   ├── evaluation.json          # 评估指标
    │   └── ranking.json             # 排名结果
    └── optimizations_index.json
```

### 3.2 案例级数据存储

```
cases/{case_id}/
├── control_simulations/             # 新增：管控仿真结果
│   ├── {batch_id}/                 # 批次目录
│   │   ├── {plan_id}_sim/          # 单个方案的仿真结果
│   │   │   ├── simulation.sumocfg
│   │   │   ├── summary.xml
│   │   │   ├── tripinfo.xml
│   │   │   └── simulation_metadata.json
│   │   └── batch_metadata.json     # 批次元数据
│   └── batches_index.json          # 批次索引
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
┌─────────────┐
│ 策略管理    │  选模板 → 配置参数 → 保存策略
└──────┬──────┘
       ↓
┌─────────────┐
│ 方案管理    │  选策略 → 组合方案 → 生成additional文件
└──────┬──────┘
       ↓
┌─────────────┐
│ 并行仿真    │  选案例 + 选方案集 → 批量运行 → 监控进度
└──────┬──────┘
       ↓
┌─────────────┐
│ 方案优化    │  选批次 → 配置指标 → 计算排名 → 对比分析
└─────────────┘
```

### 5.2 模块交互图

```
┌────────────────┐      ┌────────────────┐
│  策略模板库    │─────→│  策略实例库    │
│  (Templates)   │ 实例化│  (Strategies)  │
└────────────────┘      └────────┬───────┘
                                 │
                                 ↓ 组合
                        ┌────────────────┐
                        │   方案库       │
                        │   (Plans)      │
                        └────────┬───────┘
                                 │
                                 ↓ 应用到案例
                        ┌────────────────┐
         ┌─────────────→│  批量仿真      │
         │              │  (Batch Sim)   │
         │              └────────┬───────┘
         │                       │
  案例数据 (Case)                 ↓ 结果分析
         │              ┌────────────────┐
         └─────────────→│  优化分析      │
                        │  (Optimization)│
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

#### 7.3.3 并行仿真页面

**功能区块**：
1. **顶部**：任务配置区
   - 案例选择（下拉框）
   - 方案多选（复选框列表）
   - 仿真参数配置
   - 提交按钮
2. **中部**：进度监控面板
   - 各方案进度条
   - 状态指示（待运行/运行中/已完成/失败）
   - 日志输出
3. **底部**：历史批次列表

**交互流程**：
```
选择案例 → 选择方案 → 配置参数 → 提交仿真 → 监控进度
```

---

#### 7.3.4 方案优化页面

**功能区块**：
1. **顶部**：批次选择 + 指标配置
   - 仿真批次选择（下拉框）
   - 指标权重设置（滑块）
   - 计算按钮
2. **中部**：评估结果展示
   - Top-N排名表格
   - 雷达图对比
   - 柱状图对比
3. **底部**：详细报告下载

**交互流程**：
```
选择批次 → 配置指标 → 计算排名 → 查看对比 → 导出报告
```

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
