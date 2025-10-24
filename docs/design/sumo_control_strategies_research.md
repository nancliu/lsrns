# SUMO管控策略研究报告 - 基于策略-方案两层架构

**文档版本**: v2.0 (重构版)
**创建日期**: 2025-10-24
**研究目标**: 验证SUMO通过.add.xml配置文件实现高速公路管控策略的可行性,并建立策略-方案两层架构

---

## 📋 执行摘要

本研究验证了**SUMO可以完全通过.add.xml配置文件实现三类高速公路管控策略**,无需使用TraCI动态控制接口。

### 核心结论

| 管控类型                       | SUMO实现方式                | 可行性               | 推荐度     |
| ------------------------------ | --------------------------- | -------------------- | ---------- |
| **可变限速 (VSS)**       | `<variableSpeedSign>`     | ✅**完全支持** | ⭐⭐⭐⭐⭐ |
| **应急车道开放 (DHS)**   | `<closingLaneReroute>`    | ✅**完全支持** | ⭐⭐⭐⭐⭐ |
| **收费站入口管控 (TEC)** | `<calibrator>` (流量控制) | ✅**完全支持** | ⭐⭐⭐⭐⭐ |

### 架构特点

- ✅ **两层架构**: 策略层 (可复用单元) + 方案层 (策略组合)
- ✅ **基于时间的静态配置**: 无需TraCI,简化架构
- ✅ **无缝集成OD_SIM**: 符合项目整体设计理念
- ⚠️ **不使用信号灯**: 高速公路场景,已排除 `<tlLogic>`方案

---

## 2. 策略与方案的概念模型

### 2.1 两层架构设计

本系统采用**策略-方案两层架构**,清晰分离可复用单元和业务组合:

```
┌─────────────────────────────────────────────────────────┐
│                   策略模板层 (Template)                  │
│  预定义的管控措施配置模板 (全局,高复用性)                 │
│  - VSS模板: vss_moderate.json, vss_strict.json         │
│  - DHS模板: dhs_peak_hours.json                        │
│  - TEC模板: tec_ramp_metering.json                     │
└────────────────────┬────────────────────────────────────┘
                     ↓ 实例化 (选择路段 + 配置参数)
┌─────────────────────────────────────────────────────────┐
│                   策略实例层 (Strategy)                  │
│  针对特定路段/入口的单一管控措施 (全局,可跨案例复用)        │
│  - 策略1: "K8-K10路段早高峰限速80km/h"                   │
│  - 策略2: "K10-K15路段开放应急车道"                      │
│  - 策略3: "K12入口限流至180辆/小时"                      │
└────────────────────┬────────────────────────────────────┘
                     ↓ 组合 (选择多个策略)
┌─────────────────────────────────────────────────────────┐
│                   管控方案层 (Plan)                      │
│  多个策略的组合,形成完整管控措施集 (全局,可跨案例复用)      │
│  - 方案A: "早高峰综合方案" = 策略1 + 策略2 + 策略3       │
│  - 方案B: "恶劣天气方案" = VSS限速 + 入口关闭            │
│  - 方案Baseline: "无管控基准方案"                        │
└────────────────────┬────────────────────────────────────┘
                     ↓ 生成SUMO配置
┌─────────────────────────────────────────────────────────┐
│                 SUMO配置文件 (control.add.xml)            │
│  包含所有策略的XML元素                                    │
└────────────────────┬────────────────────────────────────┘
                     ↓ 应用到案例
┌─────────────────────────────────────────────────────────┐
│              批量仿真 (Batch Simulation)                 │
│  在特定案例上运行多个方案,对比评估效果                     │
└─────────────────────────────────────────────────────────┘
```

### 2.2 策略定义与分类

#### 2.2.1 什么是策略 (Strategy)

**定义**: 针对**单一路段区间**或**单一入口**的**独立管控措施**。

**核心特征**:

- ✅ **单一控制对象**: 一个路段区间或一个入口
- ✅ **单一管控类型**: VSS、DHS或TEC中的一种
- ✅ **可独立运行**: 可单独生成SUMO配置并仿真
- ✅ **可复用**: 可被多个方案引用

**路段区间说明**:

- **路段区间** = 一组**连续的edge**,形成完整的管控范围
- 示例: "K10-K15路段" = [edge_1000, edge_1001, edge_1002, edge_1003, edge_1004]
- 这些edge应**统一控制**(同时开启/关闭),因此视为一个策略

#### 2.2.2 策略分类

| 策略类型      | 英文名称              | 控制对象           | SUMO元素                                  |
| ------------- | --------------------- | ------------------ | ----------------------------------------- |
| **VSS** | Variable Speed Sign   | 路段区间的车道     | `<variableSpeedSign>`                   |
| **DHS** | Dynamic Hard Shoulder | 路段区间的应急车道 | `<rerouter>` + `<closingLaneReroute>` |
| **TEC** | Toll Entrance Control | 单个入口匝道       | `<calibrator>` 或 `<closingReroute>`  |

#### 2.2.3 策略实例示例

**示例1: VSS策略**

```json
{
  "strategy_id": "vss_001",
  "strategy_name": "K8-K10上游预警限速",
  "strategy_type": "VSS",
  "control_object": {
    "edges": ["edge_800", "edge_801"],
    "lanes": ["edge_800_0", "edge_800_1", "edge_800_2", "edge_801_0", "edge_801_1", "edge_801_2"]
  },
  "parameters": {
    "speed_steps": [
      {"time": 0, "speed": 33.33},
      {"time": 24900, "speed": 22.22},
      {"time": 32400, "speed": 33.33}
    ]
  }
}
```

**示例2: DHS策略**

```json
{
  "strategy_id": "dhs_001",
  "strategy_name": "K10-K15瓶颈路段应急车道开放",
  "strategy_type": "DHS",
  "control_object": {
    "edges": ["edge_1000", "edge_1001", "edge_1002", "edge_1003", "edge_1004"],
    "hard_shoulder_lanes": ["edge_1000_3", "edge_1001_3", "edge_1002_3", "edge_1003_3", "edge_1004_3"]
  },
  "parameters": {
    "intervals": [
      {"begin": 25200, "end": 32400, "allow": "passenger bus truck emergency"}
    ]
  }
}
```

**示例3: TEC策略**

```json
{
  "strategy_id": "tec_001",
  "strategy_name": "K12入口匝道流量控制",
  "strategy_type": "TEC",
  "control_object": {
    "entrance_edge": "entrance_k12_to_mainline"
  },
  "parameters": {
    "flow_intervals": [
      {"begin": 0, "end": 25200, "vehsPerHour": 480, "speed": 15},
      {"begin": 25200, "end": 32400, "vehsPerHour": 180, "speed": 8},
      {"begin": 32400, "end": 86400, "vehsPerHour": 480, "speed": 15}
    ]
  }
}
```

### 2.3 方案定义与组合规则

#### 2.3.1 什么是方案 (Plan)

**定义**: **多个策略的组合**,形成完整的管控措施集,用于解决特定交通问题。

**核心特征**:

- ✅ **多策略组合**: 通常包含≥1个策略
- ✅ **业务导向**: 以解决问题为目标(如"缓解早高峰拥堵")
- ✅ **独立运行**: 生成独立的control.add.xml文件
- ✅ **可对比**: 多个方案可并行仿真,评估效果

**特殊方案**:

- **基准方案 (Baseline)**: 不包含任何管控策略,用于对比分析

#### 2.3.2 方案组合规则

| 规则               | 说明                  | 示例                           |
| ------------------ | --------------------- | ------------------------------ |
| **策略数量** | ≥0 (基准方案为0)     | 早高峰方案包含3个策略          |
| **策略类型** | 可混合VSS/DHS/TEC     | VSS + DHS + TEC                |
| **时空协调** | 策略的时间/空间应协调 | 上游限速应早于下游开放应急车道 |
| **无冲突**   | 不同策略不应相互冲突  | 不能同时"开放"和"关闭"同一车道 |

#### 2.3.3 方案示例

**示例: 早高峰综合方案**

```json
{
  "plan_id": "plan_001",
  "plan_name": "早高峰综合管控方案",
  "description": "缓解K10-K15路段早高峰拥堵",
  "strategy_ids": ["vss_001", "dhs_001", "tec_001"],
  "target_scenario": "早高峰(7:00-9:00)",
  "expected_effects": {
    "reduce_congestion": "降低瓶颈路段拥堵",
    "improve_throughput": "提升整体通行能力",
    "control_flow": "限制上游流入量"
  }
}
```

**对应的control.add.xml** (自动生成):

```xml
<additional>
    <!-- 策略vss_001: K8-K10上游预警限速 -->
    <variableSpeedSign id="vss_001" lanes="edge_800_0 edge_800_1 edge_800_2 edge_801_0 edge_801_1 edge_801_2">
        <step time="0" speed="33.33"/>
        <step time="24900" speed="22.22"/>
        <step time="32400" speed="33.33"/>
    </variableSpeedSign>

    <!-- 策略dhs_001: K10-K15应急车道开放 -->
    <rerouter id="dhs_001" edges="edge_1000 edge_1001 edge_1002 edge_1003 edge_1004">
        <interval begin="25200" end="32400">
            <closingLaneReroute id="edge_1000_3" allow="passenger bus truck emergency"/>
            <closingLaneReroute id="edge_1001_3" allow="passenger bus truck emergency"/>
            <closingLaneReroute id="edge_1002_3" allow="passenger bus truck emergency"/>
            <closingLaneReroute id="edge_1003_3" allow="passenger bus truck emergency"/>
            <closingLaneReroute id="edge_1004_3" allow="passenger bus truck emergency"/>
        </interval>
    </rerouter>

    <!-- 策略tec_001: K12入口限流 -->
    <calibrator id="tec_001" edge="entrance_k12_to_mainline" pos="0">
        <flow begin="0" end="25200" vehsPerHour="480" speed="15"/>
        <flow begin="25200" end="32400" vehsPerHour="180" speed="8"/>
        <flow begin="32400" end="86400" vehsPerHour="480" speed="15"/>
    </calibrator>
</additional>
```

### 2.4 SUMO实现映射

#### 2.4.1 策略→SUMO元素映射

| 策略类型             | SUMO元素                                               | 数量 | 映射规则                 |
| -------------------- | ------------------------------------------------------ | ---- | ------------------------ |
| **1个VSS策略** | 1个 `<variableSpeedSign>`                            | 1:1  | 一个策略生成一个XML元素  |
| **1个DHS策略** | 1个 `<rerouter>` (包含多个 `<closingLaneReroute>`) | 1:N  | 一个rerouter控制多个lane |
| **1个TEC策略** | 1个 `<calibrator>` 或 1个 `<rerouter>`             | 1:1  | 根据TEC类型选择元素      |

#### 2.4.2 方案→control.add.xml映射

```
方案 (Plan)
    ├─ 策略1 (VSS) → <variableSpeedSign id="vss_001">
    ├─ 策略2 (DHS) → <rerouter id="dhs_001">
    └─ 策略3 (TEC) → <calibrator id="tec_001">
            ↓
合并到一个文件
            ↓
    control.add.xml
```

**文件组织**:

```
control_data/plans/plan_001/
├── plan_metadata.json          # 方案元数据
├── strategy_refs.json          # 引用的策略ID列表
└── control.add.xml             # 生成的SUMO配置 (包含所有策略)
```

#### 2.4.3 划分判断标准

**如何判断是策略还是方案?**

| 描述                      | 类型             | 理由                                      |
| ------------------------- | ---------------- | ----------------------------------------- |
| "K10-K11路段限速80km/h"   | ✅**策略** | 单一路段区间,单一管控措施                 |
| "K10-K15路段开放应急车道" | ✅**策略** | 多个edge但属于**连续区间**,统一控制 |
| "K12入口限流至180辆/小时" | ✅**策略** | 单一入口,单一管控措施                     |
| "早高峰综合管控"          | ✅**方案** | 包含VSS+DHS+TEC多种措施                   |
| "成都绕城南段管控"        | ✅**方案** | 通常包含多个路段的多种措施                |
| "恶劣天气应急响应"        | ✅**方案** | 包含限速+入口关闭等多种措施               |

**关键判断原则**:

- **空间范围**: 单一区间→策略; 多个区间→方案
- **管控类型**: 单一类型→策略; 多种类型→方案
- **业务语义**: "在X做Y"→策略; "解决Z问题"→方案

---

## 第一部分: 策略层 (Strategy Level)

---

## 3. VSS策略 (可变限速策略)

### 3.1 策略定义

**Variable Speed Sign (VSS) 策略**: 针对**一个路段区间的指定车道**,在**特定时间段**设置**不同的限速值**。

**控制对象**:

- **路段区间**: 一组连续的edge (如K8-K10路段)
- **车道**: edge的指定车道索引 (如所有主线车道,不含应急车道)

**控制参数**:

- **时间步骤** (time steps): 不同时刻的限速值序列
- **限速值** (speed): m/s单位,可设为-1恢复默认限速

**典型应用场景**:

- 恶劣天气降低限速
- 拥堵预防(上游预警限速)
- 事故保护(降低通过速度)
- 高峰期分段限速

### 3.2 SUMO实现: `<variableSpeedSign>`

#### 3.2.1 XML语法

```xml
<additional>
    <variableSpeedSign id="{strategy_id}" edges="{edge_id_list}">
        <step time="{time_seconds}" speed="{speed_ms}"/>
        <step time="{time_seconds}" speed="{speed_ms}"/>
        ...
    </variableSpeedSign>
</additional>
```

#### 3.2.2 属性说明

**`<variableSpeedSign>`元素**:

| 属性      | 类型        | 必填 | 说明                                                                      |
| --------- | ----------- | ---- | ------------------------------------------------------------------------- |
| `id`    | string      | ✅   | 策略唯一标识符(建议使用strategy_id)                                       |
| `edges` | string list | 🟢   | **推荐**: 空格分隔的edge ID列表,自动应用到edge的所有车道 (SUMO v1.18+)   |
| `lanes` | string list | ⚠️   | 备选: 空格分隔的车道ID列表(格式:`edge_id_lane_index`),仅用于差异化控制 |
| `file`  | string      | ❌   | 外部文件引用(可选,用于复杂配置)                                           |

**属性选择建议**:

- **使用`edges`**: 路段所有车道统一限速(高速公路VSS的典型场景)
- **使用`lanes`**: 仅在需要差异化控制时使用(如快慢车道不同限速)

**`<step>`子元素**:

| 属性      | 类型  | 必填 | 说明                           |
| --------- | ----- | ---- | ------------------------------ |
| `time`  | float | ✅   | 时间点(秒),从仿真开始计时      |
| `speed` | float | ✅   | 限速值(m/s),-1表示恢复默认限速 |

#### 3.2.3 Edge控制示例

**使用edges属性** (推荐,简洁高效):

```xml
<variableSpeedSign id="vss_001" edges="edge_800 edge_801 edge_802">
    <step time="0" speed="33.33"/>      <!-- 120km/h -->
    <step time="25200" speed="22.22"/>  <!-- 80km/h -->
</variableSpeedSign>
```

该配置将自动应用到指定edges的**所有车道**(不包括应急车道,SUMO自动排除)。

**使用lanes属性** (仅用于特殊场景):

如需对不同车道实施差异化限速,可使用lanes属性:

```xml
<!-- 示例: 仅限制货车道速度 -->
<variableSpeedSign id="vss_truck_lane" lanes="edge_800_0 edge_801_0">
    <step time="0" speed="25.00"/>  <!-- 货车道限速90km/h -->
</variableSpeedSign>
```

SUMO车道ID格式: `{edge_id}_{lane_index}` (索引0为最右侧车道)

### 3.3 策略参数Schema

```json
{
  "strategy_type": "VSS",
  "parameters_schema": {
    "edges": {
      "type": "array",
      "description": "路段区间的edge ID列表(推荐使用,自动应用到所有车道)",
      "required": true,
      "example": ["edge_800", "edge_801"],
      "comment": "SUMO v1.18+支持,配置简洁,推荐用于统一限速场景"
    },
    "speed_steps": {
      "type": "array",
      "description": "时间-限速值序列",
      "required": true,
      "items": {
        "time": {
          "type": "integer",
          "min": 0,
          "max": 86400,
          "unit": "秒"
        },
        "speed": {
          "type": "float",
          "min": -1,
          "max": 36.11,
          "unit": "m/s",
          "comment": "-1表示恢复默认限速,36.11约等于130km/h"
        }
      }
    }
  }
}
```

### 3.4 策略实例示例

#### 示例1: 恶劣天气渐进式限速

**业务场景**: 雾天K10-K20路段分阶段降低限速

**策略定义**:

```json
{
  "strategy_id": "vss_fog_k10_k20",
  "strategy_name": "K10-K20雾天渐进式限速",
  "strategy_type": "VSS",
  "description": "雾天分4阶段降低限速: 120→100→80→60km/h",
  "control_object": {
    "edges": ["edge_200", "edge_201"]
  },
  "parameters": {
    "speed_steps": [
      {"time": 0, "speed": 33.33, "description": "正常: 120km/h"},
      {"time": 21600, "speed": 27.78, "description": "6:00雾起: 100km/h"},
      {"time": 28800, "speed": 22.22, "description": "8:00雾浓: 80km/h"},
      {"time": 36000, "speed": 16.67, "description": "10:00雾最浓: 60km/h"},
      {"time": 43200, "speed": 27.78, "description": "12:00雾散: 100km/h"},
      {"time": 50400, "speed": 33.33, "description": "14:00恢复: 120km/h"}
    ]
  }
}
```

**生成的SUMO配置**:

```xml
<variableSpeedSign id="vss_fog_k10_k20" edges="edge_200 edge_201">
    <step time="0" speed="33.33"/>      <!-- 120km/h -->
    <step time="21600" speed="27.78"/>  <!-- 100km/h -->
    <step time="28800" speed="22.22"/>  <!-- 80km/h -->
    <step time="36000" speed="16.67"/>  <!-- 60km/h -->
    <step time="43200" speed="27.78"/>  <!-- 100km/h -->
    <step time="50400" speed="33.33"/>  <!-- 120km/h -->
</variableSpeedSign>
```

#### 示例2: 早高峰上游预警限速

**业务场景**: 在下游瓶颈上游5km处提前降速,平滑车流

**策略定义**:

```json
{
  "strategy_id": "vss_upstream_k8_k10",
  "strategy_name": "K8-K10上游预警限速",
  "strategy_type": "VSS",
  "description": "早高峰提前5分钟降速至80km/h,避免急刹车",
  "control_object": {
    "edges": ["edge_800", "edge_801"]
  },
  "parameters": {
    "speed_steps": [
      {"time": 0, "speed": 33.33, "description": "正常: 120km/h"},
      {"time": 24900, "speed": 22.22, "description": "6:55: 80km/h (提前5分钟)"},
      {"time": 32400, "speed": 33.33, "description": "9:00: 恢复120km/h"}
    ]
  }
}
```

**生成的SUMO配置**:

```xml
<variableSpeedSign id="vss_upstream_k8_k10" edges="edge_800 edge_801">
    <step time="0" speed="33.33"/>      <!-- 初始120km/h -->
    <step time="24900" speed="22.22"/>  <!-- 6:55降至80km/h -->
    <step time="32400" speed="33.33"/>  <!-- 9:00恢复 -->
</variableSpeedSign>
```

**设计要点**:

- ⏰ **提前5分钟**: 在应急车道开放前(7:00)提前降速
- 🎯 **目的**: 减少车辆因突然开放应急车道导致的紧急制动

#### 示例3: 分车道差异化限速

**业务场景**: 货车道限速低于乘用车道

**策略定义** (需要拆分为2个策略):

**策略A: 乘用车道限速**

```json
{
  "strategy_id": "vss_passenger_lanes_k10",
  "strategy_name": "K10路段乘用车道限速",
  "strategy_type": "VSS",
  "control_object": {
    "edges": ["edge_100"],
    "lanes": ["edge_100_1", "edge_100_2"]
  },
  "parameters": {
    "speed_steps": [
      {"time": 7200, "speed": 27.78}  <!-- 100km/h -->
    ]
  }
}
```

**策略B: 货车道限速**

```json
{
  "strategy_id": "vss_truck_lane_k10",
  "strategy_name": "K10路段货车道限速",
  "strategy_type": "VSS",
  "control_object": {
    "edges": ["edge_100"],
    "lanes": ["edge_100_0"]
  },
  "parameters": {
    "speed_steps": [
      {"time": 7200, "speed": 22.22}  <!-- 80km/h -->
    ]
  }
}
```

**生成的SUMO配置**:

```xml
<!-- 策略A: 乘用车道 -->
<variableSpeedSign id="vss_passenger_lanes_k10" lanes="edge_100_1 edge_100_2">
    <step time="7200" speed="27.78"/>  <!-- 100km/h -->
</variableSpeedSign>

<!-- 策略B: 货车道 -->
<variableSpeedSign id="vss_truck_lane_k10" lanes="edge_100_0">
    <step time="7200" speed="22.22"/>  <!-- 80km/h -->
</variableSpeedSign>
```

### 3.5 实施要点

#### 速度单位转换

```python
def kmh_to_ms(kmh: float) -> float:
    """公里/小时 → 米/秒"""
    return round(kmh / 3.6, 2)

# 常用限速值
SPEED_130KMH = kmh_to_ms(130)  # 36.11 m/s
SPEED_120KMH = kmh_to_ms(120)  # 33.33 m/s
SPEED_100KMH = kmh_to_ms(100)  # 27.78 m/s
SPEED_80KMH = kmh_to_ms(80)    # 22.22 m/s
SPEED_60KMH = kmh_to_ms(60)    # 16.67 m/s
```

#### 车道列表自动生成

```python
def generate_lane_ids(edges: list, exclude_hard_shoulder: bool = True) -> list:
    """
    从edge列表生成车道ID列表

    Args:
        edges: edge ID列表
        exclude_hard_shoulder: 是否排除应急车道(默认True)

    Returns:
        车道ID列表
    """
    import xml.etree.ElementTree as ET

    net_xml_path = "templates/network_files/sichuan202508v7.net.xml"
    tree = ET.parse(net_xml_path)

    lane_ids = []
    for edge_id in edges:
        edge = tree.find(f".//edge[@id='{edge_id}']")
        if edge is None:
            continue

        lanes = edge.findall('lane')
        max_index = len(lanes) - 1

        for i, lane in enumerate(lanes):
            # 如果排除应急车道,跳过最大索引(通常是应急车道)
            if exclude_hard_shoulder and i == max_index:
                continue

            lane_ids.append(lane.get('id'))

    return lane_ids

# 使用示例
edges = ["edge_800", "edge_801"]
lanes = generate_lane_ids(edges, exclude_hard_shoulder=True)
# 结果: ["edge_800_0", "edge_800_1", "edge_800_2", "edge_801_0", "edge_801_1", "edge_801_2"]
```

---

## 4. DHS策略 (应急车道开放策略)

### 4.1 策略定义

**Dynamic Hard Shoulder (DHS) 策略**: 针对**一个路段区间的应急车道**,在**特定时间段**动态**开放/关闭**,允许或禁止特定车型通行。

**控制对象**:

- **路段区间**: 一组连续的edge (如K10-K15路段)
- **应急车道**: 每个edge的最右侧车道(索引最大)

**控制参数**:

- **时间区间** (intervals): 开放/关闭的时间段
- **允许车型** (allow): 开放时允许的vClass

**典型应用场景**:

- 高峰期增加通行能力
- 拥堵缓解
- 节假日潮汐流管理

### 4.2 SUMO实现: `<closingLaneReroute>`

#### 4.2.1 XML语法

```xml
<additional>
    <rerouter id="{strategy_id}" edges="{edge_id_list}">
        <!-- 时间段1: 关闭应急车道 -->
        <interval begin="{begin_seconds}" end="{end_seconds}">
            <closingLaneReroute id="{lane_id}" allow="emergency authority"/>
        </interval>

        <!-- 时间段2: 开放应急车道 -->
        <interval begin="{begin_seconds}" end="{end_seconds}">
            <closingLaneReroute id="{lane_id}" allow="passenger bus truck emergency"/>
        </interval>
    </rerouter>
</additional>
```

#### 4.2.2 属性说明

**`<rerouter>`元素**:

| 属性      | 类型        | 必填 | 说明                      |
| --------- | ----------- | ---- | ------------------------- |
| `id`    | string      | ✅   | 策略唯一标识符            |
| `edges` | string list | ✅   | 空格分隔的edge ID列表     |
| `pos`   | float       | ❌   | 位置(meters),默认edge起点 |

**`<interval>`元素**:

| 属性      | 类型  | 必填 | 说明         |
| --------- | ----- | ---- | ------------ |
| `begin` | float | ✅   | 开始时间(秒) |
| `end`   | float | ✅   | 结束时间(秒) |

**`<closingLaneReroute>`元素**:

| 属性         | 类型        | 必填 | 说明                                 |
| ------------ | ----------- | ---- | ------------------------------------ |
| `id`       | string      | ✅   | 车道ID (格式:`edge_id_lane_index`) |
| `allow`    | string list | ❌   | 允许的车型(默认:`authority`)       |
| `disallow` | string list | ❌   | 禁止的车型(与allow二选一)            |

**SUMO车型类别(vClass)与项目车型映射**:

| SUMO vClass   | 说明     | 项目车型                                      | 典型用途                    |
| ------------- | -------- | --------------------------------------------- | --------------------------- |
| `passenger` | 乘用车   | passenger_small, passenger_large              | 小型/大型乘用车             |
| `truck`     | 货车     | truck_small, truck_large                      | 小型/大型货车               |
| `delivery`  | 配送车   | special_small, special_large                  | 特种车辆(工程/配送/服务类)  |
| `emergency` | 应急车辆 | emergency                                     | 救护车/消防车               |
| `authority` | 权限车辆 | authority                                     | 警车/公务车                 |
| `bus`       | 公交车   | bus                                           | 公交/大巴                   |

**说明**: 项目定义的6种车型(passenger_small/large, truck_small/large, special_small/large)映射到SUMO的3种vClass(passenger, truck, delivery)。管控策略配置时使用SUMO vClass。

### 4.3 策略参数Schema

```json
{
  "strategy_type": "DHS",
  "parameters_schema": {
    "edges": {
      "type": "array",
      "description": "路段区间的edge ID列表",
      "required": true,
      "example": ["edge_1000", "edge_1001", "edge_1002", "edge_1003", "edge_1004"]
    },
    "hard_shoulder_lanes": {
      "type": "array",
      "description": "应急车道ID列表",
      "required": true,
      "auto_generate": true,
      "comment": "从edges自动生成,取每个edge的最大索引车道"
    },
    "intervals": {
      "type": "array",
      "description": "开放/关闭时间区间",
      "required": true,
      "items": {
        "begin": {"type": "integer", "min": 0, "max": 86400, "unit": "秒"},
        "end": {"type": "integer", "min": 0, "max": 86400, "unit": "秒"},
        "status": {
          "type": "string",
          "enum": ["OPEN", "CLOSED"],
          "description": "OPEN=开放, CLOSED=关闭"
        },
        "allow": {
          "type": "string",
          "description": "允许车型(当status=OPEN时)",
          "default": "passenger bus truck emergency",
          "comment": "CLOSED时固定为'emergency authority'"
        }
      }
    }
  }
}
```

### 4.4 策略实例示例

#### 示例1: 早晚高峰开放应急车道

**业务场景**: K10-K15路段早晚高峰开放应急车道

**策略定义**:

```json
{
  "strategy_id": "dhs_k10_k15_peak",
  "strategy_name": "K10-K15早晚高峰应急车道开放",
  "strategy_type": "DHS",
  "description": "7:00-9:00和17:00-19:00开放应急车道给所有车辆",
  "control_object": {
    "edges": ["edge_1000", "edge_1001", "edge_1002", "edge_1003", "edge_1004"],
    "hard_shoulder_lanes": ["edge_1000_3", "edge_1001_3", "edge_1002_3", "edge_1003_3", "edge_1004_3"]
  },
  "parameters": {
    "intervals": [
      {
        "begin": 0,
        "end": 25200,
        "status": "CLOSED",
        "allow": "emergency authority",
        "description": "00:00-07:00 夜间关闭"
      },
      {
        "begin": 25200,
        "end": 32400,
        "status": "OPEN",
        "allow": "passenger bus truck emergency",
        "description": "07:00-09:00 早高峰开放"
      },
      {
        "begin": 32400,
        "end": 61200,
        "status": "CLOSED",
        "allow": "emergency authority",
        "description": "09:00-17:00 平峰关闭"
      },
      {
        "begin": 61200,
        "end": 68400,
        "status": "OPEN",
        "allow": "passenger bus truck emergency",
        "description": "17:00-19:00 晚高峰开放"
      },
      {
        "begin": 68400,
        "end": 86400,
        "status": "CLOSED",
        "allow": "emergency authority",
        "description": "19:00-24:00 夜间关闭"
      }
    ]
  }
}
```

**生成的SUMO配置**:

```xml
<rerouter id="dhs_k10_k15_peak" edges="edge_1000 edge_1001 edge_1002 edge_1003 edge_1004">
    <!-- 夜间: 关闭 (0:00-7:00) -->
    <interval begin="0" end="25200">
        <closingLaneReroute id="edge_1000_3" allow="emergency authority"/>
        <closingLaneReroute id="edge_1001_3" allow="emergency authority"/>
        <closingLaneReroute id="edge_1002_3" allow="emergency authority"/>
        <closingLaneReroute id="edge_1003_3" allow="emergency authority"/>
        <closingLaneReroute id="edge_1004_3" allow="emergency authority"/>
    </interval>

    <!-- 早高峰: 开放 (7:00-9:00) -->
    <interval begin="25200" end="32400">
        <closingLaneReroute id="edge_1000_3" allow="passenger bus truck emergency"/>
        <closingLaneReroute id="edge_1001_3" allow="passenger bus truck emergency"/>
        <closingLaneReroute id="edge_1002_3" allow="passenger bus truck emergency"/>
        <closingLaneReroute id="edge_1003_3" allow="passenger bus truck emergency"/>
        <closingLaneReroute id="edge_1004_3" allow="passenger bus truck emergency"/>
    </interval>

    <!-- 平峰: 关闭 (9:00-17:00) -->
    <interval begin="32400" end="61200">
        <closingLaneReroute id="edge_1000_3" allow="emergency authority"/>
        <closingLaneReroute id="edge_1001_3" allow="emergency authority"/>
        <closingLaneReroute id="edge_1002_3" allow="emergency authority"/>
        <closingLaneReroute id="edge_1003_3" allow="emergency authority"/>
        <closingLaneReroute id="edge_1004_3" allow="emergency authority"/>
    </interval>

    <!-- 晚高峰: 开放 (17:00-19:00) -->
    <interval begin="61200" end="68400">
        <closingLaneReroute id="edge_1000_3" allow="passenger bus truck emergency"/>
        <closingLaneReroute id="edge_1001_3" allow="passenger bus truck emergency"/>
        <closingLaneReroute id="edge_1002_3" allow="passenger bus truck emergency"/>
        <closingLaneReroute id="edge_1003_3" allow="passenger bus truck emergency"/>
        <closingLaneReroute id="edge_1004_3" allow="passenger bus truck emergency"/>
    </interval>

    <!-- 夜间: 关闭 (19:00-24:00) -->
    <interval begin="68400" end="86400">
        <closingLaneReroute id="edge_1000_3" allow="emergency authority"/>
        <closingLaneReroute id="edge_1001_3" allow="emergency authority"/>
        <closingLaneReroute id="edge_1002_3" allow="emergency authority"/>
        <closingLaneReroute id="edge_1003_3" allow="emergency authority"/>
        <closingLaneReroute id="edge_1004_3" allow="emergency authority"/>
    </interval>
</rerouter>
```

#### 示例2: 仅允许小客车使用应急车道

**业务场景**: 早高峰开放应急车道,但禁止货车

**策略定义**:

```json
{
  "strategy_id": "dhs_passenger_only",
  "strategy_name": "应急车道仅允许小客车",
  "strategy_type": "DHS",
  "description": "早高峰开放应急车道,仅允许小客车和公交车,禁止货车",
  "control_object": {
    "edges": ["edge_1000"],
    "hard_shoulder_lanes": ["edge_1000_3"]
  },
  "parameters": {
    "intervals": [
      {
        "begin": 25200,
        "end": 32400,
        "status": "OPEN",
        "allow": "passenger bus emergency",
        "description": "仅允许小客车和公交车"
      }
    ]
  }
}
```

**生成的SUMO配置**:

```xml
<rerouter id="dhs_passenger_only" edges="edge_1000">
    <interval begin="25200" end="32400">
        <!-- 使用allow方式: 明确列出允许的车型 -->
        <closingLaneReroute id="edge_1000_3" allow="passenger bus emergency"/>
    </interval>
</rerouter>
```

**或使用disallow方式**:

```xml
<rerouter id="dhs_passenger_only" edges="edge_1000">
    <interval begin="25200" end="32400">
        <!-- 使用disallow方式: 明确禁止货车 -->
        <closingLaneReroute id="edge_1000_3" disallow="truck trailer"/>
    </interval>
</rerouter>
```

### 4.5 实施要点

#### 应急车道识别

```python
def get_hard_shoulder_lane(net_xml_path: str, edge_id: str) -> str:
    """
    获取edge的应急车道ID

    Args:
        net_xml_path: 路网文件路径
        edge_id: edge ID

    Returns:
        应急车道ID (通常是索引最大的车道)
    """
    import xml.etree.ElementTree as ET

    tree = ET.parse(net_xml_path)
    edge = tree.find(f".//edge[@id='{edge_id}']")

    if edge is None:
        raise ValueError(f"Edge {edge_id} not found")

    lanes = edge.findall('lane')
    max_index = len(lanes) - 1

    return f"{edge_id}_{max_index}"

# 批量生成
def generate_hard_shoulder_lanes(edges: list) -> list:
    """从edge列表生成应急车道列表"""
    net_xml_path = "templates/network_files/sichuan202508v7.net.xml"
    return [get_hard_shoulder_lane(net_xml_path, edge_id) for edge_id in edges]

# 使用示例
edges = ["edge_1000", "edge_1001", "edge_1002"]
hard_shoulder_lanes = generate_hard_shoulder_lanes(edges)
# 结果: ["edge_1000_3", "edge_1001_3", "edge_1002_3"]
```

#### 与VSS联动(避免紧急制动)

根据SUMO文档警告:"修改车道权限可能导致紧急制动"

**解决方案**: 在开放应急车道前,提前在上游设置VSS降速

**联动示例** (在方案层组合):

```python
# 策略1: 上游提前降速 (提前5分钟)
vss_strategy = {
    "strategy_id": "vss_prepare_dhs",
    "speed_steps": [
        {"time": 24900, "speed": 22.22}  # 6:55降至80km/h
    ]
}

# 策略2: 7:00开放应急车道
dhs_strategy = {
    "strategy_id": "dhs_k10_k15",
    "intervals": [
        {"begin": 25200, "end": 32400}  # 7:00-9:00开放
    ]
}

# 方案层组合这两个策略
plan = {
    "plan_id": "plan_dhs_with_vss",
    "strategy_ids": ["vss_prepare_dhs", "dhs_k10_k15"]
}
```

#### 处理路径错误

**问题**: 车辆路径规划时可能未考虑应急车道,开放后会产生路径错误

**解决方案**: 在sumocfg中添加 `--ignore-route-errors`选项

```xml
<configuration>
    <processing>
        <ignore-route-errors>true</ignore-route-errors>
    </processing>
</configuration>
```

或在启动命令中添加:

```bash
sumo --ignore-route-errors -c simulation.sumocfg
```

---

## 5. TEC策略 (收费站入口管控策略)

### 5.1 策略定义

**Toll Entrance Control (TEC) 策略**: 针对**单个收费站入口匝道**,控制车辆**进入主线的流量**或**禁止特定车型**进入。

**控制对象**:

- **入口匝道**: 单个entrance edge (连接收费站到主线的匝道)

**控制参数**:

- **流量控制**: 每小时允许进入的车辆数(vehsPerHour)
- **车型限制**: 禁止或允许的vClass

**典型应用场景**:

- 高峰期匝道信号控制(Ramp Metering)
- 货车限行
- 应急入口关闭
- 流量调节

### 5.2 SUMO实现方案对比

| 方案                      | SUMO元素                      | 适用场景              | 优先级                       |
| ------------------------- | ----------------------------- | --------------------- | ---------------------------- |
| **方案A: 流量控制** | `<calibrator>` + `<flow>` | 精确流量控制/匝道信号 | ⭐⭐⭐⭐⭐**强烈推荐** |
| **方案B: 路段关闭** | `<closingReroute>`          | 完全关闭/车型限制     | ⭐⭐⭐⭐ 推荐                |

**选择建议**:

- **需要精确流量控制** → 使用方案A (Calibrator)
- **需要完全关闭入口** → 使用方案B (closingReroute)
- **需要禁止特定车型** → 使用方案B (closingReroute)

### 5.3 方案A: Calibrator流量控制 ⭐ 推荐

#### 5.3.1 XML语法

```xml
<additional>
    <calibrator id="{strategy_id}" edge="{entrance_edge}" pos="0">
        <flow begin="{begin_seconds}" end="{end_seconds}"
              vehsPerHour="{vehicles_per_hour}"
              speed="{speed_ms}"
              type="{vehicle_type}"
              route="{route_id}"/>
    </calibrator>
</additional>
```

#### 5.3.2 属性说明

**`<calibrator>`元素**:

| 属性       | 类型   | 必填 | 说明                                     |
| ---------- | ------ | ---- | ---------------------------------------- |
| `id`     | string | ✅   | 策略唯一标识符                           |
| `edge`   | string | ✅   | 受控的entrance edge ID                   |
| `pos`    | float  | ✅   | 位置(meters),**入口匝道通常设为0** |
| `period` | float  | ❌   | 检查周期(秒),默认60                      |
| `output` | string | ❌   | 输出文件路径                             |

**`<flow>`子元素**:

| 属性            | 类型   | 必填 | 说明                |
| --------------- | ------ | ---- | ------------------- |
| `begin`       | float  | ✅   | 开始时间(秒)        |
| `end`         | float  | ✅   | 结束时间(秒)        |
| `vehsPerHour` | float  | ✅   | 每小时流量(辆/小时) |
| `speed`       | float  | ❌   | 插入速度(m/s)       |
| `type`        | string | ❌   | 车辆类型            |
| `route`       | string | ❌   | 路径ID              |

#### 5.3.3 流量对照表

| vehsPerHour | 等效间隔 | 说明       |
| ----------- | -------- | ---------- |
| 600         | 6秒/辆   | 正常通行   |
| 480         | 7.5秒/辆 | 轻度限流   |
| 360         | 10秒/辆  | 中度限流   |
| 240         | 15秒/辆  | 严格限流   |
| 180         | 20秒/辆  | 极严格限流 |
| 120         | 30秒/辆  | 最严格限流 |

**计算公式**:

```
间隔(秒/辆) = 3600 / vehsPerHour
```

#### 5.3.4 策略参数Schema

```json
{
  "strategy_type": "TEC_CALIBRATOR",
  "parameters_schema": {
    "entrance_edge": {
      "type": "string",
      "description": "入口匝道edge ID",
      "required": true,
      "example": "entrance_k12_to_mainline"
    },
    "position": {
      "type": "float",
      "description": "Calibrator位置(meters)",
      "default": 0,
      "required": false
    },
    "flow_intervals": {
      "type": "array",
      "description": "流量控制时间段",
      "required": true,
      "items": {
        "begin": {"type": "integer", "min": 0, "max": 86400},
        "end": {"type": "integer", "min": 0, "max": 86400},
        "vehsPerHour": {
          "type": "float",
          "min": 0,
          "max": 2000,
          "description": "每小时流量(辆/小时)"
        },
        "speed": {
          "type": "float",
          "min": 5,
          "max": 20,
          "unit": "m/s",
          "description": "插入速度"
        },
        "type": {
          "type": "string",
          "optional": true,
          "description": "车辆类型"
        }
      }
    }
  }
}
```

#### 5.3.5 策略实例示例

**示例: K12入口早高峰严格限流**

**策略定义**:

```json
{
  "strategy_id": "tec_ramp_meter_k12",
  "strategy_name": "K12入口匝道流量控制",
  "strategy_type": "TEC_CALIBRATOR",
  "description": "早高峰限流至180辆/小时(20秒/辆),模拟匝道信号效果",
  "control_object": {
    "entrance_edge": "entrance_k12_to_mainline"
  },
  "parameters": {
    "position": 0,
    "flow_intervals": [
      {
        "begin": 0,
        "end": 25200,
        "vehsPerHour": 480,
        "speed": 15,
        "description": "夜间/平峰: 正常流量(7.5秒/辆)"
      },
      {
        "begin": 25200,
        "end": 32400,
        "vehsPerHour": 180,
        "speed": 8,
        "description": "早高峰: 严格限流(20秒/辆)"
      },
      {
        "begin": 32400,
        "end": 61200,
        "vehsPerHour": 480,
        "speed": 15,
        "description": "平峰: 恢复正常"
      },
      {
        "begin": 61200,
        "end": 68400,
        "vehsPerHour": 300,
        "speed": 10,
        "description": "晚高峰: 中度限流(12秒/辆)"
      },
      {
        "begin": 68400,
        "end": 86400,
        "vehsPerHour": 480,
        "speed": 15,
        "description": "夜间: 正常流量"
      }
    ]
  }
}
```

**生成的SUMO配置**:

```xml
<calibrator id="tec_ramp_meter_k12" edge="entrance_k12_to_mainline" pos="0">
    <!-- 夜间/平峰: 480辆/小时 -->
    <flow begin="0" end="25200" vehsPerHour="480" speed="15"/>

    <!-- 早高峰: 180辆/小时 (严格限流) -->
    <flow begin="25200" end="32400" vehsPerHour="180" speed="8"/>

    <!-- 平峰: 480辆/小时 -->
    <flow begin="32400" end="61200" vehsPerHour="480" speed="15"/>

    <!-- 晚高峰: 300辆/小时 (中度限流) -->
    <flow begin="61200" end="68400" vehsPerHour="300" speed="10"/>

    <!-- 夜间: 480辆/小时 -->
    <flow begin="68400" end="86400" vehsPerHour="480" speed="15"/>
</calibrator>
```

### 5.4 方案B: Rerouter路段关闭

#### 5.4.1 XML语法

```xml
<additional>
    <rerouter id="{strategy_id}" edges="{entrance_edge}">
        <interval begin="{begin_seconds}" end="{end_seconds}">
            <closingReroute id="{entrance_edge}" disallow="{vehicle_classes}"/>
        </interval>
    </rerouter>
</additional>
```

#### 5.4.2 属性说明

**`<closingReroute>`元素**:

| 属性         | 类型        | 必填 | 说明                         |
| ------------ | ----------- | ---- | ---------------------------- |
| `id`       | string      | ✅   | 要关闭的edge ID              |
| `allow`    | string list | ❌   | 允许的车型(默认:无,完全关闭) |
| `disallow` | string list | ❌   | 禁止的车型(与allow二选一)    |

#### 5.4.3 策略参数Schema

```json
{
  "strategy_type": "TEC_REROUTER",
  "parameters_schema": {
    "entrance_edges": {
      "type": "array",
      "description": "入口edge ID列表",
      "required": true
    },
    "intervals": {
      "type": "array",
      "description": "关闭时间段",
      "required": true,
      "items": {
        "begin": {"type": "integer"},
        "end": {"type": "integer"},
        "closure_type": {
          "type": "string",
          "enum": ["FULL_CLOSE", "TRUCK_BAN", "PARTIAL"],
          "default": "FULL_CLOSE"
        },
        "disallow": {
          "type": "string",
          "description": "禁止车型(仅当closure_type=TRUCK_BAN或PARTIAL时)",
          "optional": true,
          "examples": ["truck trailer", "truck", "delivery"]
        }
      }
    }
  }
}
```

#### 5.4.4 策略实例示例

**示例1: 早高峰完全关闭入口**

**策略定义**:

```json
{
  "strategy_id": "tec_close_jinjiang",
  "strategy_name": "锦江收费站入口早高峰关闭",
  "strategy_type": "TEC_REROUTER",
  "description": "7:00-9:00完全关闭入口",
  "control_object": {
    "entrance_edges": ["entrance_jinjiang_to_sa2"]
  },
  "parameters": {
    "intervals": [
      {
        "begin": 25200,
        "end": 32400,
        "closure_type": "FULL_CLOSE"
      }
    ]
  }
}
```

**生成的SUMO配置**:

```xml
<rerouter id="tec_close_jinjiang" edges="entrance_jinjiang_to_sa2">
    <!-- 7:00-9:00 完全关闭 -->
    <interval begin="25200" end="32400">
        <closingReroute id="entrance_jinjiang_to_sa2"/>
    </interval>
</rerouter>
```

**示例2: 货车限行**

**策略定义**:

```json
{
  "strategy_id": "tec_truck_ban_chengya",
  "strategy_name": "成雅高速入口货车限行",
  "strategy_type": "TEC_REROUTER",
  "description": "早晚高峰禁止货车进入",
  "control_object": {
    "entrance_edges": ["entrance_chengya_001", "entrance_chengya_002"]
  },
  "parameters": {
    "intervals": [
      {
        "begin": 25200,
        "end": 32400,
        "closure_type": "TRUCK_BAN",
        "disallow": "truck trailer",
        "description": "早高峰禁止货车"
      },
      {
        "begin": 61200,
        "end": 68400,
        "closure_type": "TRUCK_BAN",
        "disallow": "truck trailer",
        "description": "晚高峰禁止货车"
      }
    ]
  }
}
```

**生成的SUMO配置**:

```xml
<rerouter id="tec_truck_ban_chengya" edges="entrance_chengya_001 entrance_chengya_002">
    <!-- 早高峰禁止货车 -->
    <interval begin="25200" end="32400">
        <closingReroute id="entrance_chengya_001" disallow="truck trailer"/>
        <closingReroute id="entrance_chengya_002" disallow="truck trailer"/>
    </interval>

    <!-- 晚高峰禁止货车 -->
    <interval begin="61200" end="68400">
        <closingReroute id="entrance_chengya_001" disallow="truck trailer"/>
        <closingReroute id="entrance_chengya_002" disallow="truck trailer"/>
    </interval>
</rerouter>
```

### 5.5 入口Edge识别方法

#### 方法A: 从数据库查询入口edge (推荐 ⭐)

本项目已在数据库中标注了所有收费站入口节点,使用以下SQL查询即可获取入口edge列表:

```sql
SELECT
    sne.edge_id,
    sne.route_code,
    mnu.node_name,
    mnu.node_type,
    mnu.start_stake
FROM dim.sim_network_edges sne
JOIN dim.multiscale_node_units mnu
    ON sne.from_junction_id = mnu.junction_id
WHERE mnu.node_type = 'entrance'
ORDER BY sne.route_code, mnu.start_stake;
```

**数据表说明**:

- `dim.sim_network_edges`: 仿真路网edge表,包含edge_id, route_code, from_junction_id等
- `dim.multiscale_node_units`: 多尺度节点单元表,包含node_type字段标注入口/出口/枢纽等
- `node_type = 'entrance'`: 收费站入口节点

**优势**:

- ✅ 数据库已标注,无需解析net.xml
- ✅ 包含业务信息(路线代码、里程桩号、节点名称)
- ✅ 方便按路线或里程筛选入口

**Python查询示例**:

```python
from shared.data_access.connection import get_pooled_connection

def get_entrance_edges(route_code: str = None) -> list:
    """
    从数据库查询入口edge列表

    Args:
        route_code: 路线代码(可选),如'SA2', 'G4202'

    Returns:
        list of dict: [{"edge_id": "...", "route_code": "...", "node_name": "..."}]
    """
    query = """
        SELECT
            sne.edge_id,
            sne.route_code,
            mnu.node_name,
            mnu.start_stake
        FROM dim.sim_network_edges sne
        JOIN dim.multiscale_node_units mnu
            ON sne.from_junction_id = mnu.junction_id
        WHERE mnu.node_type = 'entrance'
    """

    if route_code:
        query += f" AND sne.route_code = '{route_code}'"

    query += " ORDER BY sne.route_code, mnu.start_stake"

    conn = get_pooled_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        conn.close()
```

#### 方法B: 从net.xml解析识别 (备选)

如果没有数据库访问权限,可通过解析net.xml文件识别入口edge:

```python
def find_entrance_edges_from_netxml(net_xml_path: str) -> list:
    """
    从net.xml识别入口匝道edge

    入口edge特征:
    1. function属性包含"onRamp"
    2. from节点是边界节点(通常以gneJ开头)
    """
    import xml.etree.ElementTree as ET

    tree = ET.parse(net_xml_path)
    entrance_edges = []

    for edge in tree.findall('.//edge'):
        edge_id = edge.get('id')
        edge_function = edge.get('function', '')

        # 检查function属性
        if 'onRamp' in edge_function:
            entrance_edges.append(edge_id)

    return entrance_edges
```

**注意**: 此方法仅用于没有数据库访问权限的场景,识别结果不包含业务信息。

---

## 第二部分: 方案层 (Plan Level)

---

## 6. 管控方案设计

### 6.1 方案定义与组成

#### 6.1.1 什么是方案 (Plan)

**定义**: **多个策略的有机组合**,形成完整的管控措施集,用于解决特定的交通管理问题。

**核心要素**:

- **方案ID** (plan_id): 全局唯一标识符
- **方案名称** (plan_name): 业务友好的名称
- **策略列表** (strategy_ids): 包含的策略ID数组
- **目标场景** (target_scenario): 适用的交通场景
- **预期效果** (expected_effects): 管控目标

**特殊方案**:

- **基准方案 (Baseline Plan)**: 不包含任何管控策略(strategy_ids=[]),用于对比评估

#### 6.1.2 方案组成规则

| 维度               | 要求         | 说明                       |
| ------------------ | ------------ | -------------------------- |
| **策略数量** | ≥0          | 基准方案为0,典型方案3-5个  |
| **策略类型** | 可混合       | 可包含VSS+DHS+TEC          |
| **空间覆盖** | 无重叠冲突   | 不同策略的控制对象不应冲突 |
| **时间协调** | 合理衔接     | 上下游策略时间应协调       |
| **业务逻辑** | 符合管控目标 | 策略组合应有明确的管控意图 |

### 6.2 方案生成流程

```
┌─────────────────────────────────────┐
│  1. 选择策略                         │
│  - 从策略库选择多个策略实例           │
│  - 策略可跨类型(VSS/DHS/TEC)         │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  2. 验证组合                         │
│  - 检查时空冲突                      │
│  - 验证业务逻辑                      │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  3. 生成方案元数据                   │
│  - plan_metadata.json               │
│  - strategy_refs.json               │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  4. 生成SUMO配置                     │
│  - 合并所有策略的XML元素             │
│  - 生成control.add.xml              │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│  5. 验证XML格式                      │
│  - xmllint验证                      │
│  - SUMO配置检查                     │
└─────────────────────────────────────┘
```

### 6.3 control.add.xml生成规则

#### 6.3.1 生成算法

```python
def generate_control_additional(plan: dict, strategies: list) -> str:
    """
    根据方案和策略列表生成control.add.xml

    Args:
        plan: 方案元数据
        strategies: 策略实例列表(按strategy_ids顺序)

    Returns:
        格式化的XML字符串
    """
    import xml.etree.ElementTree as ET
    from xml.dom import minidom

    # 创建根元素
    root = ET.Element('additional')

    # 添加注释: 方案信息
    comment = ET.Comment(f' 方案: {plan["plan_name"]} ({plan["plan_id"]}) ')
    root.append(comment)

    # 按策略类型分组添加
    for strategy in strategies:
        # 添加策略注释
        strategy_comment = ET.Comment(
            f' 策略{strategy["strategy_id"]}: {strategy["strategy_name"]} ({strategy["strategy_type"]}) '
        )
        root.append(strategy_comment)

        # 根据策略类型生成对应XML元素
        if strategy['strategy_type'] == 'VSS':
            elem = generate_vss_xml(strategy)
        elif strategy['strategy_type'] == 'DHS':
            elem = generate_dhs_xml(strategy)
        elif strategy['strategy_type'] in ['TEC_CALIBRATOR', 'TEC_REROUTER']:
            elem = generate_tec_xml(strategy)

        root.append(elem)

    # 格式化输出
    xml_str = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent='    ')
```

#### 6.3.2 元素排序规则

**推荐顺序**: VSS策略 → DHS策略 → TEC策略

**理由**:

- VSS通常在上游,应先生效
- DHS在瓶颈路段,次之
- TEC控制入口流量,最后

**示例**:

```xml
<additional>
    <!-- VSS策略组 -->
    <variableSpeedSign id="vss_001">...</variableSpeedSign>
    <variableSpeedSign id="vss_002">...</variableSpeedSign>

    <!-- DHS策略组 -->
    <rerouter id="dhs_001">...</rerouter>

    <!-- TEC策略组 -->
    <calibrator id="tec_001">...</calibrator>
    <rerouter id="tec_002">...</rerouter>
</additional>
```

---

## 7. 典型方案示例

### 7.1 早高峰综合方案

**方案目标**: 缓解K10-K15路段早高峰拥堵,提升整体通行能力

**管控策略**:

1. 上游预警限速(K8-K10)
2. 瓶颈开放应急车道(K10-K15)
3. 入口流量控制(K12)

#### 7.1.1 方案元数据

```json
{
  "plan_id": "plan_peak_morning_001",
  "plan_name": "早高峰综合管控方案A",
  "plan_type": "CONTROL",
  "description": "缓解K10-K15路段早高峰拥堵",
  "target_scenario": "工作日早高峰(7:00-9:00)",
  "strategy_ids": [
    "vss_upstream_k8_k10",
    "dhs_k10_k15_peak",
    "tec_ramp_meter_k12"
  ],
  "expected_effects": {
    "reduce_congestion": "降低瓶颈路段拥堵20%",
    "improve_speed": "提升平均速度15%",
    "increase_throughput": "增加通行能力10%"
  },
  "created_at": "2025-10-24T10:00:00",
  "tags": ["早高峰", "综合管控", "拥堵缓解"]
}
```

#### 7.1.2 完整control.add.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<additional>
    <!-- 方案: 早高峰综合管控方案A (plan_peak_morning_001) -->

    <!-- ==================== VSS策略组 ==================== -->

    <!-- 策略vss_upstream_k8_k10: K8-K10上游预警限速 (VSS) -->
    <variableSpeedSign id="vss_upstream_k8_k10"
                       lanes="edge_800_0 edge_800_1 edge_800_2 edge_801_0 edge_801_1 edge_801_2">
        <step time="0" speed="33.33"/>      <!-- 正常: 120km/h -->
        <step time="24900" speed="22.22"/>  <!-- 6:55: 80km/h (提前5分钟) -->
        <step time="32400" speed="33.33"/>  <!-- 9:00: 恢复120km/h -->
    </variableSpeedSign>

    <!-- ==================== DHS策略组 ==================== -->

    <!-- 策略dhs_k10_k15_peak: K10-K15早晚高峰应急车道开放 (DHS) -->
    <rerouter id="dhs_k10_k15_peak" edges="edge_1000 edge_1001 edge_1002 edge_1003 edge_1004">
        <!-- 夜间: 关闭 (0:00-7:00) -->
        <interval begin="0" end="25200">
            <closingLaneReroute id="edge_1000_3" allow="emergency authority"/>
            <closingLaneReroute id="edge_1001_3" allow="emergency authority"/>
            <closingLaneReroute id="edge_1002_3" allow="emergency authority"/>
            <closingLaneReroute id="edge_1003_3" allow="emergency authority"/>
            <closingLaneReroute id="edge_1004_3" allow="emergency authority"/>
        </interval>

        <!-- 早高峰: 开放 (7:00-9:00) -->
        <interval begin="25200" end="32400">
            <closingLaneReroute id="edge_1000_3" allow="passenger bus truck emergency"/>
            <closingLaneReroute id="edge_1001_3" allow="passenger bus truck emergency"/>
            <closingLaneReroute id="edge_1002_3" allow="passenger bus truck emergency"/>
            <closingLaneReroute id="edge_1003_3" allow="passenger bus truck emergency"/>
            <closingLaneReroute id="edge_1004_3" allow="passenger bus truck emergency"/>
        </interval>

        <!-- 平峰: 关闭 (9:00-17:00) -->
        <interval begin="32400" end="61200">
            <closingLaneReroute id="edge_1000_3" allow="emergency authority"/>
            <closingLaneReroute id="edge_1001_3" allow="emergency authority"/>
            <closingLaneReroute id="edge_1002_3" allow="emergency authority"/>
            <closingLaneReroute id="edge_1003_3" allow="emergency authority"/>
            <closingLaneReroute id="edge_1004_3" allow="emergency authority"/>
        </interval>

        <!-- 晚高峰: 开放 (17:00-19:00) -->
        <interval begin="61200" end="68400">
            <closingLaneReroute id="edge_1000_3" allow="passenger bus truck emergency"/>
            <closingLaneReroute id="edge_1001_3" allow="passenger bus truck emergency"/>
            <closingLaneReroute id="edge_1002_3" allow="passenger bus truck emergency"/>
            <closingLaneReroute id="edge_1003_3" allow="passenger bus truck emergency"/>
            <closingLaneReroute id="edge_1004_3" allow="passenger bus truck emergency"/>
        </interval>

        <!-- 夜间: 关闭 (19:00-24:00) -->
        <interval begin="68400" end="86400">
            <closingLaneReroute id="edge_1000_3" allow="emergency authority"/>
            <closingLaneReroute id="edge_1001_3" allow="emergency authority"/>
            <closingLaneReroute id="edge_1002_3" allow="emergency authority"/>
            <closingLaneReroute id="edge_1003_3" allow="emergency authority"/>
            <closingLaneReroute id="edge_1004_3" allow="emergency authority"/>
        </interval>
    </rerouter>

    <!-- ==================== TEC策略组 ==================== -->

    <!-- 策略tec_ramp_meter_k12: K12入口匝道流量控制 (TEC_CALIBRATOR) -->
    <calibrator id="tec_ramp_meter_k12" edge="entrance_k12_to_mainline" pos="0">
        <!-- 夜间/平峰: 480辆/小时 -->
        <flow begin="0" end="25200" vehsPerHour="480" speed="15"/>

        <!-- 早高峰: 180辆/小时 (严格限流) -->
        <flow begin="25200" end="32400" vehsPerHour="180" speed="8"/>

        <!-- 平峰: 480辆/小时 -->
        <flow begin="32400" end="61200" vehsPerHour="480" speed="15"/>

        <!-- 晚高峰: 300辆/小时 (中度限流) -->
        <flow begin="61200" end="68400" vehsPerHour="300" speed="10"/>

        <!-- 夜间: 480辆/小时 -->
        <flow begin="68400" end="86400" vehsPerHour="480" speed="15"/>
    </calibrator>

</additional>
```

### 7.2 恶劣天气应急方案

**方案目标**: 雾天降低事故风险,保障行车安全

**管控策略**:

1. 全路段渐进式降速
2. 关闭部分入口

#### 7.2.1 方案元数据

```json
{
  "plan_id": "plan_weather_fog_001",
  "plan_name": "恶劣天气(雾天)应急方案",
  "plan_type": "CONTROL",
  "description": "雾天分阶段降低限速,关闭高风险入口",
  "target_scenario": "大雾天气(能见度<200m)",
  "strategy_ids": [
    "vss_fog_k10_k20",
    "tec_close_jinjiang"
  ],
  "expected_effects": {
    "reduce_accidents": "降低事故率30%",
    "improve_safety": "提升行车安全性",
    "smooth_flow": "平滑车流,避免急刹车"
  },
  "created_at": "2025-10-24T11:00:00",
  "tags": ["恶劣天气", "安全保障", "应急响应"]
}
```

#### 7.2.2 完整control.add.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<additional>
    <!-- 方案: 恶劣天气(雾天)应急方案 (plan_weather_fog_001) -->

    <!-- 策略vss_fog_k10_k20: K10-K20雾天渐进式限速 (VSS) -->
    <variableSpeedSign id="vss_fog_k10_k20"
                       lanes="edge_200_0 edge_200_1 edge_200_2 edge_201_0 edge_201_1 edge_201_2">
        <step time="0" speed="33.33"/>      <!-- 正常: 120km/h -->
        <step time="21600" speed="27.78"/>  <!-- 6:00雾起: 100km/h -->
        <step time="28800" speed="22.22"/>  <!-- 8:00雾浓: 80km/h -->
        <step time="36000" speed="16.67"/>  <!-- 10:00雾最浓: 60km/h -->
        <step time="43200" speed="27.78"/>  <!-- 12:00雾散: 100km/h -->
        <step time="50400" speed="33.33"/>  <!-- 14:00恢复: 120km/h -->
    </variableSpeedSign>

    <!-- 策略tec_close_jinjiang: 锦江收费站入口早高峰关闭 (TEC_REROUTER) -->
    <rerouter id="tec_close_jinjiang" edges="entrance_jinjiang_to_sa2">
        <!-- 雾天期间完全关闭 (6:00-14:00) -->
        <interval begin="21600" end="50400">
            <closingReroute id="entrance_jinjiang_to_sa2"/>
        </interval>
    </rerouter>

</additional>
```

### 7.3 分阶段拥堵响应方案

**方案目标**: 根据拥堵程度渐进式实施管控措施

**管控策略**:

- 阶段1(轻度拥堵): 仅上游限速
- 阶段2(中度拥堵): 限速 + 开放应急车道
- 阶段3(严重拥堵): 限速 + 应急车道 + 入口限流

#### 7.3.1 方案元数据

```json
{
  "plan_id": "plan_staged_response_001",
  "plan_name": "分阶段拥堵响应方案",
  "plan_type": "CONTROL",
  "description": "根据拥堵加剧程度,分3阶段实施管控",
  "target_scenario": "动态拥堵场景",
  "strategy_ids": [
    "vss_stage1_light",
    "vss_stage2_moderate",
    "dhs_stage2",
    "vss_stage3_severe",
    "dhs_stage3",
    "tec_stage3"
  ],
  "expected_effects": {
    "adaptive_control": "自适应管控强度",
    "gradual_intervention": "渐进式干预,避免突变"
  },
  "created_at": "2025-10-24T12:00:00",
  "tags": ["分阶段", "自适应", "拥堵响应"]
}
```

#### 7.3.2 完整control.add.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<additional>
    <!-- 方案: 分阶段拥堵响应方案 (plan_staged_response_001) -->

    <!-- ==================== 阶段1 (7:00-7:30): 轻度管控 ==================== -->

    <!-- 策略vss_stage1_light: 轻度限速100km/h (VSS) -->
    <variableSpeedSign id="vss_stage1_light"
                       lanes="edge_800_0 edge_800_1 edge_800_2">
        <step time="25200" speed="27.78"/>  <!-- 7:00: 100km/h -->
        <step time="27000" speed="33.33"/>  <!-- 7:30: 恢复(如无需升级) -->
    </variableSpeedSign>

    <!-- ==================== 阶段2 (7:30-8:00): 中度管控 ==================== -->

    <!-- 策略vss_stage2_moderate: 中度限速80km/h (VSS) -->
    <variableSpeedSign id="vss_stage2_moderate"
                       lanes="edge_800_0 edge_800_1 edge_800_2">
        <step time="27000" speed="22.22"/>  <!-- 7:30: 80km/h -->
        <step time="28800" speed="33.33"/>  <!-- 8:00: 恢复(如无需升级) -->
    </variableSpeedSign>

    <!-- 策略dhs_stage2: 部分路段开放应急车道 (DHS) -->
    <rerouter id="dhs_stage2" edges="edge_1000 edge_1001">
        <interval begin="27000" end="28800">
            <closingLaneReroute id="edge_1000_3" allow="passenger bus"/>
            <closingLaneReroute id="edge_1001_3" allow="passenger bus"/>
        </interval>
    </rerouter>

    <!-- ==================== 阶段3 (8:00-9:00): 严格管控 ==================== -->

    <!-- 策略vss_stage3_severe: 严格限速60km/h (VSS) -->
    <variableSpeedSign id="vss_stage3_severe"
                       lanes="edge_800_0 edge_800_1 edge_800_2">
        <step time="28800" speed="16.67"/>  <!-- 8:00: 60km/h -->
        <step time="32400" speed="33.33"/>  <!-- 9:00: 恢复 -->
    </variableSpeedSign>

    <!-- 策略dhs_stage3: 全路段开放应急车道 (DHS) -->
    <rerouter id="dhs_stage3" edges="edge_1000 edge_1001 edge_1002">
        <interval begin="28800" end="32400">
            <closingLaneReroute id="edge_1000_3" allow="passenger bus truck"/>
            <closingLaneReroute id="edge_1001_3" allow="passenger bus truck"/>
            <closingLaneReroute id="edge_1002_3" allow="passenger bus truck"/>
        </interval>
    </rerouter>

    <!-- 策略tec_stage3: 入口严格限流 (TEC_CALIBRATOR) -->
    <calibrator id="tec_stage3" edge="entrance_k12" pos="0">
        <flow begin="28800" end="32400" vehsPerHour="120" speed="8"/>  <!-- 30秒/辆 -->
    </calibrator>

</additional>
```

### 7.4 基准方案 (Baseline)

**方案目标**: 无管控状态,用于对比分析

#### 7.4.1 方案元数据

```json
{
  "plan_id": "plan_baseline",
  "plan_name": "基准方案(无管控)",
  "plan_type": "BASELINE",
  "description": "无任何管控措施,用于对比评估",
  "target_scenario": "所有场景",
  "strategy_ids": [],
  "expected_effects": {
    "baseline": "提供基准数据用于对比"
  },
  "created_at": "2025-10-24T09:00:00",
  "tags": ["基准", "无管控", "对比"]
}
```

#### 7.4.2 完整control.add.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<additional>
    <!-- 方案: 基准方案(无管控) (plan_baseline) -->
    <!-- 本文件为空,不包含任何管控策略 -->
</additional>
```

**说明**: 基准方案的control.add.xml为空文件(仅包含 `<additional>`根元素),或者在仿真时不加载任何additional文件。

---

## 第三部分: 实施指南

---

## 8. 与OD_SIM系统的集成

### 8.1 架构集成点

根据项目的[traffic_control_optimization_overview.md](traffic_control_optimization_overview.md),管控功能域需与现有OD_SIM架构无缝集成:

```
现有OD仿真系统
    ├─ Case数据 (cases/{case_id}/)
    ├─ Network文件 (templates/network_files/)
    └─ Simulation服务 (api/services/simulation_service.py)
        ↓
【新增】管控策略功能域
    ├─ 策略模板库 (templates/control_strategies/)
    ├─ 策略实例库 (control_data/strategies/)
    ├─ 管控方案库 (control_data/plans/)
    └─ control.add.xml生成器 (shared/control_tools/additional_generator.py)
        ↓
批量仿真 (复用simulation_service)
    ├─ 方案A仿真 (cases/{case_id}/control_simulations/{batch_id}/plan_001_sim/)
    ├─ 方案B仿真 (cases/{case_id}/control_simulations/{batch_id}/plan_002_sim/)
    └─ 基准仿真 (cases/{case_id}/control_simulations/{batch_id}/plan_baseline_sim/)
        ↓
评估分析 (新增evaluation_calculator)
    └─ 方案排名 (control_data/optimizations/{optimization_id}/)
```

### 8.2 文件存储结构

```
D:\projects\OD_SIM\
├── templates/
│   └── control_strategies/          # 策略模板库(全局)
│       ├── vss_moderate.json
│       ├── vss_strict.json
│       ├── dhs_peak_hours.json
│       ├── tec_ramp_metering.json
│       └── templates_index.json
│
├── control_data/                    # 全局管控数据
│   ├── strategies/                  # 策略实例库
│   │   ├── vss_001.json
│   │   ├── dhs_001.json
│   │   ├── tec_001.json
│   │   └── strategies_index.json
│   │
│   ├── plans/                       # 方案库
│   │   ├── plan_001/
│   │   │   ├── plan_metadata.json
│   │   │   ├── strategy_refs.json  # ["vss_001", "dhs_001", "tec_001"]
│   │   │   └── control.add.xml     # 生成的SUMO配置
│   │   ├── plan_baseline/
│   │   │   ├── plan_metadata.json
│   │   │   ├── strategy_refs.json  # []
│   │   │   └── control.add.xml     # 空文件
│   │   └── plans_index.json
│   │
│   └── optimizations/               # 优化分析记录
│       ├── opt_001/
│       │   ├── metadata.json        # 关联case_id, batch_id
│       │   ├── evaluation.json
│       │   └── ranking.json
│       └── optimizations_index.json
│
└── cases/
    └── case_20251024_001/
        └── control_simulations/     # 管控仿真结果(案例级)
            └── batch_001/
                ├── plan_baseline_sim/
                │   ├── simulation.sumocfg
                │   ├── summary.xml
                │   └── tripinfo.xml
                ├── plan_001_sim/
                │   ├── simulation.sumocfg
                │   ├── control.add.xml  # 从plans/plan_001/复制
                │   ├── summary.xml
                │   └── tripinfo.xml
                └── batch_metadata.json
```

### 8.3 Python实现: additional_generator.py

**位置**: `shared/control_tools/additional_generator.py`

```python
"""
SUMO管控策略Additional文件生成器
基于策略-方案两层架构
"""
from typing import List, Dict
import xml.etree.ElementTree as ET
from xml.dom import minidom


def generate_vss_xml(strategy: Dict) -> ET.Element:
    """
    生成VSS策略的XML元素

    Args:
        strategy: VSS策略实例

    Returns:
        <variableSpeedSign>元素
    """
    vss = ET.Element('variableSpeedSign', {
        'id': strategy['strategy_id'],
        'lanes': ' '.join(strategy['control_object']['lanes'])
    })

    for step in strategy['parameters']['speed_steps']:
        ET.SubElement(vss, 'step', {
            'time': str(step['time']),
            'speed': str(step['speed'])
        })

    return vss


def generate_dhs_xml(strategy: Dict) -> ET.Element:
    """
    生成DHS策略的XML元素

    Args:
        strategy: DHS策略实例

    Returns:
        <rerouter>元素(包含<closingLaneReroute>)
    """
    rerouter = ET.Element('rerouter', {
        'id': strategy['strategy_id'],
        'edges': ' '.join(strategy['control_object']['edges'])
    })

    for interval in strategy['parameters']['intervals']:
        interval_elem = ET.SubElement(rerouter, 'interval', {
            'begin': str(interval['begin']),
            'end': str(interval['end'])
        })

        # 为每个应急车道添加closingLaneReroute
        for lane_id in strategy['control_object']['hard_shoulder_lanes']:
            ET.SubElement(interval_elem, 'closingLaneReroute', {
                'id': lane_id,
                'allow': interval.get('allow', 'emergency authority')
            })

    return rerouter


def generate_tec_calibrator_xml(strategy: Dict) -> ET.Element:
    """
    生成TEC策略的XML元素(Calibrator方案)

    Args:
        strategy: TEC策略实例(类型=TEC_CALIBRATOR)

    Returns:
        <calibrator>元素
    """
    calibrator = ET.Element('calibrator', {
        'id': strategy['strategy_id'],
        'edge': strategy['control_object']['entrance_edge'],
        'pos': str(strategy['parameters'].get('position', 0))
    })

    for flow_interval in strategy['parameters']['flow_intervals']:
        attrs = {
            'begin': str(flow_interval['begin']),
            'end': str(flow_interval['end']),
            'vehsPerHour': str(flow_interval['vehsPerHour']),
            'speed': str(flow_interval['speed'])
        }

        # 可选属性
        if 'type' in flow_interval:
            attrs['type'] = flow_interval['type']
        if 'route' in flow_interval:
            attrs['route'] = flow_interval['route']

        ET.SubElement(calibrator, 'flow', attrs)

    return calibrator


def generate_tec_rerouter_xml(strategy: Dict) -> ET.Element:
    """
    生成TEC策略的XML元素(Rerouter方案)

    Args:
        strategy: TEC策略实例(类型=TEC_REROUTER)

    Returns:
        <rerouter>元素
    """
    rerouter = ET.Element('rerouter', {
        'id': strategy['strategy_id'],
        'edges': ' '.join(strategy['control_object']['entrance_edges'])
    })

    for interval in strategy['parameters']['intervals']:
        interval_elem = ET.SubElement(rerouter, 'interval', {
            'begin': str(interval['begin']),
            'end': str(interval['end'])
        })

        for edge_id in strategy['control_object']['entrance_edges']:
            attrs = {'id': edge_id}

            # 根据closure_type设置属性
            if interval.get('closure_type') == 'FULL_CLOSE':
                # 完全关闭,不设置allow/disallow(默认禁止所有)
                pass
            elif interval.get('closure_type') == 'TRUCK_BAN' or interval.get('disallow'):
                attrs['disallow'] = interval.get('disallow', 'truck trailer')
            elif interval.get('allow'):
                attrs['allow'] = interval['allow']

            ET.SubElement(interval_elem, 'closingReroute', attrs)

    return rerouter


def generate_control_additional(plan: Dict, strategies: List[Dict]) -> str:
    """
    根据管控方案生成完整的control.add.xml文件

    Args:
        plan: 方案元数据
        strategies: 策略实例列表(按strategy_ids顺序)

    Returns:
        格式化的XML字符串
    """
    root = ET.Element('additional')

    # 添加方案注释
    plan_comment = ET.Comment(f' 方案: {plan["plan_name"]} ({plan["plan_id"]}) ')
    root.append(plan_comment)

    # 分类添加策略
    vss_strategies = []
    dhs_strategies = []
    tec_strategies = []

    for strategy in strategies:
        if strategy['strategy_type'] == 'VSS':
            vss_strategies.append(strategy)
        elif strategy['strategy_type'] == 'DHS':
            dhs_strategies.append(strategy)
        elif strategy['strategy_type'] in ['TEC_CALIBRATOR', 'TEC_REROUTER']:
            tec_strategies.append(strategy)

    # 按类型分组添加
    if vss_strategies:
        vss_comment = ET.Comment(' ==================== VSS策略组 ==================== ')
        root.append(vss_comment)
        for strategy in vss_strategies:
            strategy_comment = ET.Comment(
                f' 策略{strategy["strategy_id"]}: {strategy["strategy_name"]} ({strategy["strategy_type"]}) '
            )
            root.append(strategy_comment)
            root.append(generate_vss_xml(strategy))

    if dhs_strategies:
        dhs_comment = ET.Comment(' ==================== DHS策略组 ==================== ')
        root.append(dhs_comment)
        for strategy in dhs_strategies:
            strategy_comment = ET.Comment(
                f' 策略{strategy["strategy_id"]}: {strategy["strategy_name"]} ({strategy["strategy_type"]}) '
            )
            root.append(strategy_comment)
            root.append(generate_dhs_xml(strategy))

    if tec_strategies:
        tec_comment = ET.Comment(' ==================== TEC策略组 ==================== ')
        root.append(tec_comment)
        for strategy in tec_strategies:
            strategy_comment = ET.Comment(
                f' 策略{strategy["strategy_id"]}: {strategy["strategy_name"]} ({strategy["strategy_type"]}) '
            )
            root.append(strategy_comment)

            if strategy['strategy_type'] == 'TEC_CALIBRATOR':
                root.append(generate_tec_calibrator_xml(strategy))
            else:  # TEC_REROUTER
                root.append(generate_tec_rerouter_xml(strategy))

    # 格式化输出
    xml_str = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent='    ')


def validate_additional_xml(xml_str: str) -> bool:
    """验证生成的XML格式正确性"""
    try:
        ET.fromstring(xml_str)
        return True
    except ET.ParseError as e:
        print(f"XML验证失败: {e}")
        return False
```

### 8.4 SUMOCFG集成

```python
def add_control_additional_to_sumocfg(sumocfg_path: str, control_add_xml_path: str):
    """
    将管控配置添加到simulation.sumocfg

    Args:
        sumocfg_path: simulation.sumocfg文件路径
        control_add_xml_path: control.add.xml文件路径
    """
    import xml.etree.ElementTree as ET

    tree = ET.parse(sumocfg_path)
    root = tree.getroot()

    # 查找<input>节点
    input_node = root.find('input')
    if input_node is None:
        input_node = ET.SubElement(root, 'input')

    # 添加additional-files
    existing_additional = input_node.find('additional-files')
    if existing_additional is not None:
        # 追加到现有additional-files
        existing_value = existing_additional.get('value', '')
        files = [f.strip() for f in existing_value.split(',') if f.strip()]
        if control_add_xml_path not in files:
            files.append(control_add_xml_path)
        existing_additional.set('value', ','.join(files))
    else:
        # 创建新的additional-files节点
        ET.SubElement(input_node, 'additional-files', {
            'value': control_add_xml_path
        })

    # 保存修改
    tree.write(sumocfg_path, encoding='utf-8', xml_declaration=True)
```

### 8.5 API端点设计

根据架构设计,新增以下API路由:

#### 策略管理API

```
POST   /api/v1/control/strategies/           # 创建策略实例
GET    /api/v1/control/strategies/           # 列出所有策略
GET    /api/v1/control/strategies/{id}       # 获取策略详情
PUT    /api/v1/control/strategies/{id}       # 更新策略
DELETE /api/v1/control/strategies/{id}       # 删除策略
```

#### 方案管理API

```
POST   /api/v1/control/plans/                # 创建管控方案
GET    /api/v1/control/plans/                # 列出所有方案
GET    /api/v1/control/plans/{id}            # 获取方案详情
POST   /api/v1/control/plans/{id}/generate   # 生成control.add.xml
DELETE /api/v1/control/plans/{id}            # 删除方案
```

#### 批量仿真API

```
POST   /api/v1/control/simulations/batch                    # 提交批量仿真任务
GET    /api/v1/control/simulations/batch/{batch_id}         # 获取批次状态
GET    /api/v1/control/simulations/batch/{batch_id}/progress # 查询进度
```

---

## 9. 技术限制与解决方案

### 9.1 .add.xml配置方式的限制

| 限制项                             | 影响                           | 解决方案                        |
| ---------------------------------- | ------------------------------ | ------------------------------- |
| **无法基于实时流量动态调整** | 无法实现"当流量>X时触发"的逻辑 | 使用典型场景历史数据设计时间表  |
| **无法响应突发事件**         | 事故/异常需重新配置            | Phase 2可引入TraCI扩展          |
| **时间段必须预定义**         | 需提前规划所有时段             | 创建多个场景配置,批量仿真对比   |
| **无法实现反馈控制**         | 无法根据仿真结果自动调整       | 通过多方案对比+优化分析迭代改进 |

### 9.2 推荐的实施策略

#### Phase 1: 基于时间的静态管控(当前)

**特点**:

- ✅ 完全使用.add.xml配置
- ✅ 架构简单,易于实施
- ✅ 满足典型场景仿真需求
- ✅ 支持批量方案对比

**适用场景**:

- 高峰期管控方案设计
- 节假日管控预案评估
- 恶劣天气管控方案
- 历史场景复现分析

#### Phase 2: 混合模式(可选扩展)

**特点**:

- 基准配置使用.add.xml
- 动态调整使用TraCI
- 支持实时流量触发

**适用场景**:

- 需要实时响应的管控研究
- 自适应管控算法测试
- 智能交通系统(ITS)仿真

---

## 10. 测试验证计划

### 10.1 单元测试

**测试内容**:

- VSS/DHS/TEC策略XML生成
- 方案组合验证
- control.add.xml生成
- XML格式验证

**测试框架**: pytest

### 10.2 集成测试

**测试内容**:

- 完整的策略→方案→仿真流程
- 批量仿真调度
- 结果评估分析

### 10.3 真实场景验证

**验证场景1**: 成都绕城早高峰管控

- VSS: K50-K55路段限速80km/h
- DHS: K50-K55开放应急车道
- TEC: K52入口限流

**验证场景2**: 成雅高速雾天管控

- VSS: K10-K20分阶段降速
- TEC: 关闭两个入口

---

## 附录A: 策略模板JSON Schema完整定义

### A.1 VSS策略模板

```json
{
  "template_id": "vss_moderate_001",
  "template_name": "中度可变限速",
  "strategy_type": "VSS",
  "description": "适用于恶劣天气或中度拥堵场景的可变限速策略",
  "parameters_schema": {
    "edges": {
      "type": "array",
      "description": "路段区间的edge ID列表",
      "required": true,
      "validation": {
        "min_length": 1
      },
      "example": ["edge_800", "edge_801"]
    },
    "lanes": {
      "type": "array",
      "description": "车道ID列表(格式: edge_id_lane_index)",
      "required": true,
      "auto_generate": true,
      "generation_rule": "从edges自动生成所有主线车道(排除应急车道)",
      "validation": {
        "min_length": 1,
        "item_pattern": "^[a-zA-Z0-9_]+_\\d+$"
      }
    },
    "speed_steps": {
      "type": "array",
      "description": "时间-限速值序列",
      "required": true,
      "items": {
        "time": {
          "type": "integer",
          "min": 0,
          "max": 86400,
          "unit": "秒",
          "description": "时间点(从仿真开始计时)"
        },
        "speed": {
          "type": "float",
          "min": -1,
          "max": 36.11,
          "unit": "m/s",
          "description": "限速值,-1表示恢复默认限速"
        }
      }
    }
  },
  "default_values": {
    "speed_steps": [
      {"time": 0, "speed": 33.33},
      {"time": 25200, "speed": 22.22},
      {"time": 32400, "speed": 33.33}
    ]
  },
  "sumo_element_type": "variableSpeedSign"
}
```

### A.2 DHS策略模板

```json
{
  "template_id": "dhs_peak_hours_001",
  "template_name": "高峰期应急车道开放",
  "strategy_type": "DHS",
  "description": "早晚高峰期间开放应急车道,增加通行能力",
  "parameters_schema": {
    "edges": {
      "type": "array",
      "description": "路段区间的edge ID列表",
      "required": true,
      "example": ["edge_1000", "edge_1001", "edge_1002"]
    },
    "hard_shoulder_lanes": {
      "type": "array",
      "description": "应急车道ID列表",
      "required": true,
      "auto_generate": true,
      "generation_rule": "从edges自动生成,取每个edge的最大索引车道"
    },
    "intervals": {
      "type": "array",
      "description": "开放/关闭时间区间",
      "required": true,
      "items": {
        "begin": {"type": "integer", "min": 0, "max": 86400, "unit": "秒"},
        "end": {"type": "integer", "min": 0, "max": 86400, "unit": "秒"},
        "status": {
          "type": "string",
          "enum": ["OPEN", "CLOSED"],
          "description": "OPEN=开放, CLOSED=关闭"
        },
        "allow": {
          "type": "string",
          "description": "允许车型(当status=OPEN时)",
          "default": "passenger bus truck emergency",
          "comment": "CLOSED时固定为'emergency authority'"
        }
      }
    }
  },
  "default_values": {
    "intervals": [
      {"begin": 25200, "end": 32400, "status": "OPEN", "allow": "passenger bus truck emergency"},
      {"begin": 61200, "end": 68400, "status": "OPEN", "allow": "passenger bus truck emergency"}
    ]
  },
  "sumo_element_type": "rerouter"
}
```

### A.3 TEC策略模板 (Calibrator)

```json
{
  "template_id": "tec_ramp_metering_001",
  "template_name": "匝道流量控制",
  "strategy_type": "TEC_CALIBRATOR",
  "description": "通过Calibrator精确控制入口匝道流量,模拟匝道信号效果",
  "parameters_schema": {
    "entrance_edge": {
      "type": "string",
      "description": "入口匝道edge ID",
      "required": true,
      "example": "entrance_k12_to_mainline"
    },
    "position": {
      "type": "float",
      "description": "Calibrator位置(meters),通常设为0",
      "default": 0,
      "required": false
    },
    "flow_intervals": {
      "type": "array",
      "description": "流量控制时间段",
      "required": true,
      "items": {
        "begin": {"type": "integer", "min": 0, "max": 86400},
        "end": {"type": "integer", "min": 0, "max": 86400},
        "vehsPerHour": {
          "type": "float",
          "min": 0,
          "max": 2000,
          "description": "每小时流量(辆/小时)"
        },
        "speed": {
          "type": "float",
          "min": 5,
          "max": 20,
          "unit": "m/s",
          "description": "插入速度"
        },
        "type": {
          "type": "string",
          "optional": true,
          "description": "车辆类型"
        }
      }
    }
  },
  "default_values": {
    "position": 0,
    "flow_intervals": [
      {"begin": 0, "end": 25200, "vehsPerHour": 600, "speed": 15},
      {"begin": 25200, "end": 32400, "vehsPerHour": 240, "speed": 10},
      {"begin": 32400, "end": 86400, "vehsPerHour": 600, "speed": 15}
    ]
  },
  "sumo_element_type": "calibrator"
}
```

### A.4 TEC策略模板 (Rerouter)

```json
{
  "template_id": "tec_entrance_close_001",
  "template_name": "收费站入口关闭",
  "strategy_type": "TEC_REROUTER",
  "description": "特定时段关闭收费站入口或限制特定车型",
  "parameters_schema": {
    "entrance_edges": {
      "type": "array",
      "description": "入口edge ID列表",
      "required": true
    },
    "intervals": {
      "type": "array",
      "description": "关闭时间段",
      "required": true,
      "items": {
        "begin": {"type": "integer"},
        "end": {"type": "integer"},
        "closure_type": {
          "type": "string",
          "enum": ["FULL_CLOSE", "TRUCK_BAN", "PARTIAL"],
          "default": "FULL_CLOSE"
        },
        "disallow": {
          "type": "string",
          "description": "禁止车型(仅当closure_type=TRUCK_BAN或PARTIAL时)",
          "optional": true,
          "examples": ["truck trailer", "truck", "delivery"]
        }
      }
    }
  },
  "default_values": {
    "intervals": [
      {"begin": 25200, "end": 32400, "closure_type": "FULL_CLOSE"}
    ]
  },
  "sumo_element_type": "rerouter"
}
```

---

**文档结束**

**版本历史**:

- v1.0: 初始版本(技术实现导向)
- v2.0: 重构版本(策略-方案两层架构) - 2025-10-24
