# 架构摘要 - 事件场景系统（中文版）

**版本**: 2.0 (更新于 2025-11-11)
**状态**: 已批准架构

---

## ⚠️ 重要架构变更

### 变更摘要

**问题**: 原设计将仿真配置和结果存储在场景库中，导致：
- 无法有效复用现有实现
- 仿真应该关联案例，而非存储在只读库中
- 需要更清晰的场景定义与仿真执行分离
- 绝对路径导致迁移问题

**解决方案**: 将仿真执行移至cases分支，场景库保持只读定义，**严格遵循现有cases框架结构**。

---

## 快速参考

### 场景库结构（只读）

```
output/scenarios/
├── 01_accident/  ✏️ (英文目录名)
│   ├── scenario_12547_vss/
│   │   ├── scenario_accident_vss_12547.add.xml  ✏️ (仅英文)
│   │   ├── event_description.json
│   │   ├── traffic_input_config.json
│   │   ├── control_strategy_config.json
│   │   └── scenario_metadata.json  ✏️ (per-scenario)
│   ├── scenario_12547_no_control/  ✏️ 新增（仅事件）
│   │   ├── scenario_accident_event_12547.add.xml
│   │   └── scenario_metadata.json
│   └── scenario_12547_dhs/
└── scenario_index.json
```

**❌ 不包含**: `simulation.sumocfg`, `results/`, 中文文件名
**✅ 包含**: 英文名称，per-scenario元数据，`no_control`类型

### Cases结构（包含仿真）

```
cases/case_xxx/
├── metadata.json
├── config/  ✏️ (OD + TAZ，无network.xml)
│   ├── *.od.xml
│   ├── *.rou.xml
│   └── TAZ_*.add.xml
├── analysis/
└── simulations/
    └── scenario_sim_12547/  ✏️ 新增
        ├── sim_baseline/
        │   ├── simulation.sumocfg (相对路径)
        │   ├── TAZ_6.add.xml (已复制)
        │   ├── e1/ (检测器输出)
        │   ├── summary.xml (无results/子目录)
        │   └── tripinfo.xml
        ├── sim_with_event/
        │   ├── simulation.sumocfg
        │   ├── scenario_accident_event_12547.add.xml (已复制)
        │   └── e1/
        ├── sim_with_implemented_control/
        └── sim_with_option_control_vss/
```

**关键特性**:
- ✅ 文件直接存放在`sim_xxx/`（无`results/`子目录）
- ✅ `e1/`目录存放检测器输出
- ✅ `.add.xml`文件复制到仿真目录
- ✅ sumocfg中仅使用相对路径

---

## 文件命名规范

### 事件类型（英文）

| 中文 | 英文 | 目录 |
|------|------|------|
| 交通事故 | accident | 01_accident |
| 交通阻塞 | congestion | 02_congestion |
| 交通管制 | road_control | 03_road_control |
| 地质灾害 | geological | 04_geological |
| 车辆故障 | breakdown | 05_breakdown |
| 恶劣天气 | weather | 06_weather |

### 文件名模板

```
scenario_{event_type}_{strategy}_{event_id}.add.xml

示例:
- scenario_accident_vss_12547.add.xml
- scenario_accident_event_12547.add.xml (no_control)
- scenario_congestion_tec_98765.add.xml
```

---

## SUMO配置路径（仅相对路径）

```xml
<configuration>
    <input>
        <!-- ✅ 网络文件 (4层向上) -->
        <net-file value="../../../../templates/network_files/sichuan202508v7.net.xml"/>

        <!-- ✅ 路由文件 (2层向上到config) -->
        <route-files value="../../config/*.rou.xml"/>

        <!-- ✅ Additional文件 (本地，已复制) -->
        <additional-files value="TAZ_6.add.xml,scenario_accident_vss_12547.add.xml"/>
    </input>
</configuration>
```

**❌ 禁止绝对路径**: `D:/projects/OD_SIM/...`

---

## 元数据模型

### Per-Scenario元数据

**位置**: `output/scenarios/01_accident/scenario_12547_vss/scenario_metadata.json`

```json
{
  "scenario_id": "12547_vss",
  "event_id": "12547",
  "event_type": "accident",
  "event_type_zh": "交通事故",
  "strategy": "VSS",
  "created_date": "2025-11-10T12:00:00Z",
  "scenario_files": {
    "add_xml": "scenario_accident_vss_12547.add.xml",
    "event_description": "event_description.json",
    "traffic_input_config": "traffic_input_config.json",
    "control_strategy_config": "control_strategy_config.json"
  },
  "applied_to_cases": [
    {
      "case_id": "case_morning_peak_20251111",
      "simulation_dir": "scenario_sim_12547",
      "simulation_types": ["sim_baseline", "sim_with_event", "sim_with_option_control_vss"],
      "created_date": "2025-11-11",
      "status": "completed"
    }
  ]
}
```

### 场景索引

**位置**: `output/scenarios/scenario_index.json`

```json
{
  "version": "2.0",
  "generated_date": "2025-11-10",
  "total_scenarios": 40,
  "by_event_type": {
    "accident": 18,
    "congestion": 12,
    "road_control": 6,
    "geological": 4
  },
  "by_strategy": {
    "VSS": 15,
    "TEC": 15,
    "DHS": 4,
    "no_control": 6
  }
}
```

---

## 4种仿真类型

1. **`sim_baseline/`**: 无事件无控制（基准交通）
2. **`sim_with_event/`**: 仅事件（无控制的影响）
3. **`sim_with_implemented_control/`**: 事件+实际使用的控制
4. **`sim_with_option_control_{strategy}/`**: 事件+备选控制

---

## 关键需求检查清单

- [ ] ✅ .add.xml文件名无中文
- [ ] ✅ Per-scenario元数据（非全局）
- [ ] ✅ 包含`no_control`场景
- [ ] ✅ 遵循现有cases结构
- [ ] ✅ 无`results/`子目录
- [ ] ✅ 有`e1/`目录存放检测器输出
- [ ] ✅ .add.xml文件复制到仿真目录
- [ ] ✅ sumocfg中仅使用相对路径

---

## 关键变更说明

### ✅ 1. 无中文文件名
- **之前**: `scenario_交通事故_vss_12547.add.xml`
- **之后**: `scenario_accident_vss_12547.add.xml`
- **原因**: SUMO兼容性问题

### ✅ 2. Per-Scenario元数据
- **之前**: 全局`scenario_metadata.json`
- **之后**: 每个场景目录一个`scenario_metadata.json`
- **原因**: 更好的组织和独立性

### ✅ 3. No_Control场景
- **新增**: `scenario_{id}_no_control/`目录
- **用途**: 仅事件场景，用于基准对比

### ✅ 4. 遵循现有Cases结构
- **config/**: OD文件 + TAZ文件（无network.xml）
- **simulations/sim_xxx/**: 文件直接存放（无results/子目录）
- **e1/**: 检测器输出
- **.add.xml**: 复制到仿真目录

### ✅ 5. 仅相对路径
- **网络文件**: 从sim_xxx/相对到templates/
- **路由文件**: 从sim_xxx/相对到config/
- **Additional**: 本地文件名（已复制）
- **无绝对路径**: 便于迁移

---

**完整详情**: 见`ARCHITECTURE_CHANGES.md`
