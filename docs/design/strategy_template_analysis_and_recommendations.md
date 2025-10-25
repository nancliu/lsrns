# 策略模板分析与建议

**文档版本**: v1.0
**创建日期**: 2025-10-24
**目的**: 分析现有策略模板,回答关键设计问题,提供改进建议

---

## 1. 关键问题回答

### 问题1: VSS限速是否可通过edge进行限速?

**答案**: ✅ **可以,且推荐使用edge级别限速**

#### SUMO支持的两种方式

| 方式 | XML语法 | 适用场景 | 推荐度 |
|-----|---------|---------|-------|
| **方式A: 指定lanes** | `lanes="edge_100_0 edge_100_1 edge_100_2"` | 需要分车道差异化限速 | ⭐⭐ |
| **方式B: 指定edges** ⭐ | `edges="edge_100 edge_101"` | 整个edge所有车道同限速 | ⭐⭐⭐⭐⭐ **强烈推荐** |

#### 方式B的XML语法

SUMO从v1.18开始支持`edges`属性:

```xml
<variableSpeedSign id="vss_001" edges="edge_100 edge_101 edge_102">
    <step time="7200" speed="22.22"/>   <!-- 所有车道都限速80km/h -->
</variableSpeedSign>
```

**等价于**:
```xml
<variableSpeedSign id="vss_001"
                   lanes="edge_100_0 edge_100_1 edge_100_2 edge_100_3
                          edge_101_0 edge_101_1 edge_101_2 edge_101_3
                          edge_102_0 edge_102_1 edge_102_2 edge_102_3">
    <step time="7200" speed="22.22"/>
</variableSpeedSign>
```

#### 优势对比

| 特性 | edges方式 | lanes方式 |
|-----|----------|----------|
| **配置简洁** | ✅ 极简 | ❌ 冗长 |
| **易于维护** | ✅ edge数量少 | ❌ lane数量多 |
| **适配路网变化** | ✅ 车道数变化无需修改 | ❌ 车道数变化需更新 |
| **用户友好** | ✅ 用户输入edge ID即可 | ❌ 需要手动生成lane列表 |
| **支持版本** | SUMO ≥ v1.18 | 所有版本 |

#### 建议

**VSS策略推荐使用`edges`属性**:

```json
{
  "strategy_id": "vss_001",
  "strategy_type": "VSS",
  "control_object": {
    "edges": ["edge_100", "edge_101", "edge_102"]
    // 不需要手动指定lanes
  },
  "parameters": {
    "speed_steps": [...]
  }
}
```

**生成的SUMO配置**:
```xml
<variableSpeedSign id="vss_001" edges="edge_100 edge_101 edge_102">
    <step time="0" speed="33.33"/>
    <step time="7200" speed="22.22"/>
</variableSpeedSign>
```

**例外情况** (仍需使用lanes):
- 分车道差异化限速(如货车道限速低于乘用车道)
- 排除应急车道的限速

---

### 问题2: 车型类别应使用项目定义

#### 项目定义的车型 (vehicle_types.json)

| 车型ID | vClass | 说明 | ID前缀 |
|-------|--------|------|-------|
| `passenger_small` | `passenger` | 小型乘用车 | k1, k2 |
| `passenger_large` | `passenger` | 大型乘用车/SUV | k3, k4 |
| `truck_small` | `truck` | 小型货车 | h1, h2 |
| `truck_large` | `truck` | 大型货车 | h3, h4, h5, h6 |
| `special_small` | `delivery` | 小型专用车 | t1, t2 |
| `special_large` | `delivery` | 大型专用车 | t3, t4, t5, t6 |

#### SUMO vClass映射

| 项目车型 | SUMO vClass | 用途 |
|---------|-------------|------|
| `passenger_small`, `passenger_large` | `passenger` | 乘用车管控 |
| `truck_small`, `truck_large` | `truck` | 货车管控 |
| `special_small`, `special_large` | `delivery` | 专用车管控 |

#### 更新建议

**DHS策略的allow/disallow应使用SUMO vClass**:

```xml
<!-- 正确: 使用SUMO vClass -->
<closingLaneReroute id="edge_100_3" allow="passenger truck delivery"/>
<closingLaneReroute id="edge_100_3" disallow="truck"/>

<!-- 错误: 使用项目车型ID -->
<closingLaneReroute id="edge_100_3" allow="passenger_small passenger_large truck_small"/>
```

**原因**: SUMO的allow/disallow只识别vClass,不识别自定义车型ID。

**车型分类管控示例**:

```json
// 策略模板中定义
{
  "allowed_vehicle_classes": {
    "type": "array",
    "description": "允许的SUMO车型类别",
    "enum": ["passenger", "truck", "delivery", "emergency", "authority"],
    "default": ["passenger", "truck", "delivery"]
  }
}
```

**生成规则**:
- 如果用户选择"禁止货车" → `disallow="truck"`
- 如果用户选择"仅允许小客车" → `allow="passenger"`
- 如果用户选择"允许所有车辆" → `allow="passenger truck delivery"`

**建议在策略模板中增加映射说明**:

```json
{
  "vehicle_class_mapping": {
    "小客车": "passenger",
    "货车": "truck",
    "专用车": "delivery",
    "应急车辆": "emergency",
    "权限车辆": "authority",
    "所有车辆": "passenger truck delivery"
  }
}
```

---

### 问题3: 入口Edge识别应使用数据库

**正确方法**: 从数据库`dim.multiscale_node_units`表查询

```sql
-- 查询所有入口edge
SELECT
    sne.edge_id,
    sne.route_code,
    sne.section_code,
    mnu.node_id,
    mnu.node_type,
    mnu.start_stake,
    mnu.node_name
FROM dim.sim_network_edges sne
JOIN dim.multiscale_node_units mnu
    ON sne.from_junction_id = mnu.junction_id
WHERE mnu.node_type = 'entrance'
ORDER BY sne.route_code, mnu.start_stake;
```

**返回示例**:

| edge_id | route_code | node_type | node_name |
|---------|-----------|-----------|-----------|
| entrance_jinjiang_to_sa2 | SA2 | entrance | 锦江收费站入口 |
| entrance_chengya_001 | G4202 | entrance | 成雅高速1号入口 |

**Python实现**:

```python
def get_entrance_edges_from_db() -> list:
    """
    从数据库查询所有入口edge

    Returns:
        入口edge信息列表
    """
    from shared.data_access.connection import get_pooled_connection

    query = """
        SELECT
            sne.edge_id,
            sne.route_code,
            sne.section_code,
            mnu.node_id,
            mnu.node_type,
            mnu.start_stake,
            mnu.node_name
        FROM dim.sim_network_edges sne
        JOIN dim.multiscale_node_units mnu
            ON sne.from_junction_id = mnu.junction_id
        WHERE mnu.node_type = 'entrance'
        ORDER BY sne.route_code, mnu.start_stake;
    """

    with get_pooled_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)

        entrances = []
        for row in cursor.fetchall():
            entrances.append({
                'edge_id': row[0],
                'route_code': row[1],
                'section_code': row[2],
                'node_id': row[3],
                'node_type': row[4],
                'start_stake': row[5],
                'node_name': row[6]
            })

        return entrances
```

**应删除的内容**:

研究报告v2.0的第5.5节"从net.xml识别入口edge"应**删除或标记为过时**,替换为"从数据库查询入口edge"。

---

## 2. 现有策略模板分析

### 2.1 已实现的模板

#### 基础模板 (5个)

| 模板文件 | 模板ID | 策略类型 | 状态 |
|---------|--------|---------|------|
| `vss_moderate.json` | vss_moderate | VSS | ✅ 已实现 |
| `vss_strict.json` | vss_strict | VSS | ✅ 已实现 |
| `dhs_peak_hours.json` | dhs_peak_hours | DHS | ✅ 已实现 |
| `tec_flow_metering.json` | tec_flow_metering | TEC | ✅ 已实现 |
| `tec_vehicle_restriction.json` | tec_vehicle_restriction | TEC | ✅ 已实现 |

#### 补充模板 (6个)

| 模板文件 | 模板ID | 策略类型 | 状态 | 说明 |
|---------|--------|---------|------|------|
| `vss_weather_based.json` | vss_weather_based | VSS | ✅ 已实现 | 天气应急-渐进式限速 |
| `vss_upstream_warning.json` | vss_upstream_warning | VSS | ✅ 已实现 | 上游预警-早期减速 |
| `vss_lane_differentiated.json` | vss_lane_differentiated | VSS | ✅ 已实现 | 分车道-差异化控制 |
| `dhs_passenger_only.json` | dhs_passenger_only | DHS | ✅ 已实现 | 仅客车-应急车道 |
| `dhs_peak_multi_interval.json` | dhs_peak_multi_interval | DHS | ✅ 已实现 | 多时段-复杂管理 |
| `tec_emergency_closure.json` | tec_emergency_closure | TEC | ✅ 已实现 | 紧急关闭-入口封闭 |

**总结**: 已实现11个模板,覆盖3种策略类型。包括5个基础模板和6个补充模板，其中TEC策略已优化为3层设计架构。

### 2.2 模板与文档要求的对比

#### 对比维度1: 参数Schema

| 维度 | 现有模板 | 文档v2.0要求 | 匹配度 |
|-----|---------|-------------|-------|
| **参数格式** | `parameters_schema` (数组) | `parameters_schema` (对象) | ⚠️ **不匹配** |
| **edge/lane指定** | `affected_edges` | `control_object.edges` | ⚠️ **不匹配** |
| **时间格式** | `time_intervals` [[7,9]] (小时对) | `speed_steps` [{time:7200, speed:22.22}] (秒+速度) | ❌ **不匹配** |
| **车型格式** | `applicable_vehicle_types` (项目车型ID) | `allow` (SUMO vClass) | ⚠️ **需转换** |

#### 对比维度2: VSS模板

**现有模板** (vss_moderate.json):
```json
{
  "parameters_schema": [
    {
      "parameter_name": "affected_edges",
      "parameter_type": "array",
      "default_value": []
    },
    {
      "parameter_name": "speed_limit",
      "parameter_type": "integer",
      "default_value": 80,
      "unit": "km/h"
    },
    {
      "parameter_name": "time_intervals",
      "parameter_type": "array",
      "default_value": [[7, 9], [17, 19]]
    }
  ]
}
```

**文档v2.0要求**:
```json
{
  "parameters_schema": {
    "edges": {
      "type": "array",
      "required": true,
      "example": ["edge_800", "edge_801"]
    },
    "speed_steps": {
      "type": "array",
      "required": true,
      "items": {
        "time": {"type": "integer", "min": 0, "max": 86400, "unit": "秒"},
        "speed": {"type": "float", "min": -1, "max": 36.11, "unit": "m/s"}
      }
    }
  }
}
```

**差异总结**:

| 参数 | 现有模板 | 文档要求 | 差异 |
|-----|---------|---------|------|
| 路段指定 | `affected_edges` | `edges` | 名称不同 |
| 限速方式 | 单一`speed_limit` (km/h) | `speed_steps`序列 (m/s) | **结构完全不同** |
| 时间格式 | `time_intervals` [[7,9]] | `speed_steps[].time` (秒) | **格式不同** |

**结论**: ❌ **现有VSS模板与文档要求不匹配**

#### 对比维度3: DHS模板

**现有模板** (dhs_peak_hours.json):
```json
{
  "parameters_schema": [
    {
      "parameter_name": "affected_segments",
      "description": "可开放硬路肩的路段列表"
    },
    {
      "parameter_name": "opening_hours",
      "default_value": [[7, 9], [17, 19]]
    },
    {
      "parameter_name": "allowed_vehicle_types",
      "default_value": ["passenger_small", "passenger_large", "truck_small", ..."]
    }
  ]
}
```

**文档v2.0要求**:
```json
{
  "parameters_schema": {
    "edges": {
      "type": "array",
      "required": true
    },
    "hard_shoulder_lanes": {
      "type": "array",
      "auto_generate": true
    },
    "intervals": {
      "type": "array",
      "items": {
        "begin": {"type": "integer", "unit": "秒"},
        "end": {"type": "integer", "unit": "秒"},
        "status": {"enum": ["OPEN", "CLOSED"]},
        "allow": {"type": "string"}  // SUMO vClass
      }
    }
  }
}
```

**差异总结**:

| 参数 | 现有模板 | 文档要求 | 差异 |
|-----|---------|---------|------|
| 路段指定 | `affected_segments` | `edges` | 名称不同 |
| 时间格式 | `opening_hours` [[7,9]] | `intervals` [{begin:25200, end:32400}] | **格式不同** |
| 车型格式 | `allowed_vehicle_types` (项目车型ID) | `allow` (SUMO vClass) | **类型不同** |

**结论**: ⚠️ **现有DHS模板与文档要求部分匹配,需调整**

#### 对比维度4: TEC模板

**现有模板** (tec_truck_ban.json):
```json
{
  "parameters_schema": [
    {
      "parameter_name": "entrance_ids",
      "description": "受管控的收费站入口列表"
    },
    {
      "parameter_name": "control_mode",
      "default_value": "restrict"
    },
    {
      "parameter_name": "banned_vehicle_types",
      "default_value": ["truck_small", "truck_large"]
    },
    {
      "parameter_name": "time_intervals",
      "default_value": [[6, 10], [16, 20]]
    }
  ]
}
```

**文档v2.0要求** (TEC_REROUTER):
```json
{
  "parameters_schema": {
    "entrance_edges": {
      "type": "array",
      "required": true
    },
    "intervals": {
      "type": "array",
      "items": {
        "begin": {"type": "integer"},
        "end": {"type": "integer"},
        "closure_type": {"enum": ["FULL_CLOSE", "TRUCK_BAN", "PARTIAL"]},
        "disallow": {"type": "string"}  // SUMO vClass
      }
    }
  }
}
```

**差异总结**:

| 参数 | 现有模板 | 文档要求 | 差异 |
|-----|---------|---------|------|
| 入口指定 | `entrance_ids` | `entrance_edges` | 名称不同 |
| 管控模式 | `control_mode` ("restrict") | `closure_type` ("TRUCK_BAN") | 枚举值不同 |
| 车型格式 | `banned_vehicle_types` (项目ID) | `disallow` (SUMO vClass) | **类型不同** |
| 时间格式 | `time_intervals` [[6,10]] | `intervals` [{begin, end}] | **格式不同** |

**结论**: ⚠️ **现有TEC模板与文档要求部分匹配,需调整**

### 2.3 总体评估

| 评估维度 | 评分 | 说明 |
|---------|-----|------|
| **参数Schema一致性** | ❌ 2/10 | 格式完全不同(数组 vs 对象) |
| **时间格式一致性** | ❌ 1/10 | 小时对 vs 秒级时间戳 |
| **车型格式一致性** | ⚠️ 4/10 | 项目车型ID vs SUMO vClass |
| **参数命名一致性** | ⚠️ 5/10 | affected_edges vs edges |
| **SUMO映射正确性** | ⚠️ 6/10 | 缺少speed_steps等关键参数 |

**总体结论**: ❌ **现有模板与文档v2.0要求不匹配,需要重构**

---

## 3. 建议方案

### 方案A: 重新生成策略模板 ⭐ 推荐

**优势**:
- ✅ 完全符合文档v2.0规范
- ✅ 支持直接生成SUMO XML
- ✅ 与additional_generator.py代码匹配
- ✅ 面向未来,易于扩展

**劣势**:
- ⚠️ 需要重新创建5个模板文件
- ⚠️ 如果已有基于旧模板的策略实例,需迁移

**实施步骤**:

1. **备份现有模板**:
   ```bash
   mv templates/control_strategies templates/control_strategies_old
   ```

2. **创建新模板** (按文档v2.0附录A):
   - `vss_moderate_v2.json`
   - `vss_strict_v2.json`
   - `dhs_peak_hours_v2.json`
   - `tec_ramp_metering_v2.json` (新增Calibrator方案)
   - `tec_entrance_close_v2.json`

3. **更新模板索引**:
   - `templates_index.json`

4. **迁移工具** (可选):
   - 编写脚本将旧策略实例转换为新格式

### 方案B: 修改并补充策略模板

**优势**:
- ✅ 保留现有工作成果
- ✅ 渐进式迁移,风险低

**劣势**:
- ❌ 需要维护两套格式(新旧兼容)
- ❌ 增加代码复杂度
- ❌ 不利于长期维护

**实施步骤**:

1. **修改现有模板**:
   - 调整参数Schema格式
   - 统一时间格式为秒
   - 车型格式增加映射

2. **补充新模板**:
   - 新增`tec_ramp_metering.json` (Calibrator方案)

3. **兼容层**:
   - 在additional_generator.py中增加旧格式转换逻辑

### 推荐方案: **方案A**

**理由**:
- 项目处于早期阶段,现在重构成本最低
- 文档v2.0架构清晰,符合SUMO最佳实践
- 避免技术债务

---

## 4. 多方案快速生成策略

### 4.1 方案差异来源

您的观察完全正确！

**方案差异主要来自两个维度**:

| 维度 | 说明 | 示例 |
|-----|------|------|
| **1. 参数差异** | 同一策略类型,不同参数值 | VSS限速80km/h vs 60km/h |
| **2. 组合差异** | 不同策略的组合 | 方案A=VSS+DHS, 方案B=VSS+TEC |

### 4.2 快速生成工作流设计

#### 工作流1: 参数扫描生成

**场景**: 测试不同限速值的效果

```python
# 自动生成5个VSS策略,限速值递减
base_strategy = {
    "template_id": "vss_moderate",
    "control_object": {"edges": ["edge_100", "edge_101"]},
    "parameters": {
        "speed_steps": [
            {"time": 0, "speed": 33.33},
            {"time": 7200, "speed": None},  # 待填充
            {"time": 32400, "speed": 33.33}
        ]
    }
}

# 参数扫描: 限速值从100km/h到60km/h
speed_limits_kmh = [100, 90, 80, 70, 60]

strategies = []
for i, speed_kmh in enumerate(speed_limits_kmh):
    strategy = copy.deepcopy(base_strategy)
    strategy['strategy_id'] = f"vss_speed{speed_kmh}"
    strategy['strategy_name'] = f"限速{speed_kmh}km/h策略"
    strategy['parameters']['speed_steps'][1]['speed'] = speed_kmh / 3.6  # km/h -> m/s
    strategies.append(strategy)

# 结果: 生成5个策略
# vss_speed100, vss_speed90, vss_speed80, vss_speed70, vss_speed60
```

#### 工作流2: 组合生成方案

**场景**: 测试不同策略组合的效果

```python
# 策略池
strategy_pool = {
    'vss_upstream': 'vss_001',
    'vss_bottleneck': 'vss_002',
    'dhs_k10_k15': 'dhs_001',
    'tec_k12': 'tec_001'
}

# 组合矩阵
combinations = [
    {
        'plan_id': 'plan_baseline',
        'plan_name': '基准方案(无管控)',
        'strategies': []
    },
    {
        'plan_id': 'plan_vss_only',
        'plan_name': '仅VSS管控',
        'strategies': ['vss_upstream']
    },
    {
        'plan_id': 'plan_vss_dhs',
        'plan_name': 'VSS+DHS组合',
        'strategies': ['vss_upstream', 'dhs_k10_k15']
    },
    {
        'plan_id': 'plan_full',
        'plan_name': '全策略组合',
        'strategies': ['vss_upstream', 'vss_bottleneck', 'dhs_k10_k15', 'tec_k12']
    }
]

# 自动生成方案
plans = []
for combo in combinations:
    plan = {
        'plan_id': combo['plan_id'],
        'plan_name': combo['plan_name'],
        'strategy_ids': [strategy_pool[s] for s in combo['strategies']]
    }
    plans.append(plan)
```

#### 工作流3: 因子实验设计 (DOE)

**场景**: 系统评估VSS限速值和DHS开放时长的交互效果

```python
# 因子1: VSS限速值
vss_speeds = [100, 80, 60]  # km/h

# 因子2: DHS开放时长
dhs_durations = [1, 2, 3]  # 小时

# 全因子设计: 3x3 = 9个方案
plans = []
for vss_speed in vss_speeds:
    for dhs_duration in dhs_durations:
        # 创建VSS策略
        vss_strategy = create_vss_strategy(
            strategy_id=f"vss_{vss_speed}",
            speed_kmh=vss_speed
        )

        # 创建DHS策略
        dhs_strategy = create_dhs_strategy(
            strategy_id=f"dhs_{dhs_duration}h",
            duration_hours=dhs_duration
        )

        # 创建方案
        plan = {
            'plan_id': f"plan_vss{vss_speed}_dhs{dhs_duration}h",
            'plan_name': f"VSS{vss_speed}+DHS{dhs_duration}小时",
            'strategy_ids': [vss_strategy['strategy_id'], dhs_strategy['strategy_id']]
        }
        plans.append(plan)

# 结果: 生成9个方案用于实验
```

### 4.3 前端快速生成界面设计

#### 界面1: 参数扫描工具

```
┌─────────────────────────────────────────────┐
│  快速生成策略 - 参数扫描                     │
├─────────────────────────────────────────────┤
│  基准策略: [vss_moderate ▼]                 │
│  扫描参数: [限速值 ▼]                        │
│                                             │
│  起始值: [60] km/h                          │
│  结束值: [100] km/h                         │
│  步长:   [10] km/h                          │
│                                             │
│  [预览] 将生成5个策略:                       │
│    ✓ vss_speed60  (60km/h)                 │
│    ✓ vss_speed70  (70km/h)                 │
│    ✓ vss_speed80  (80km/h)                 │
│    ✓ vss_speed90  (90km/h)                 │
│    ✓ vss_speed100 (100km/h)                │
│                                             │
│  [ 取消 ]  [ 生成策略 ]                      │
└─────────────────────────────────────────────┘
```

#### 界面2: 方案组合生成器

```
┌─────────────────────────────────────────────┐
│  快速生成方案 - 组合生成器                   │
├─────────────────────────────────────────────┤
│  可用策略:                                   │
│  ☐ vss_001 - K8-K10限速                    │
│  ☐ vss_002 - K10-K15限速                   │
│  ☐ dhs_001 - K10-K15应急车道开放            │
│  ☐ tec_001 - K12入口限流                   │
│                                             │
│  生成模式:                                   │
│  ⦿ 增量组合 (1个→2个→3个→全部)              │
│  ○ 全组合 (所有可能组合)                    │
│  ○ 自定义                                   │
│                                             │
│  [预览] 将生成5个方案:                       │
│    方案1: 基准(无策略)                       │
│    方案2: vss_001                           │
│    方案3: vss_001 + dhs_001                │
│    方案4: vss_001 + dhs_001 + tec_001      │
│    方案5: 全部策略                           │
│                                             │
│  [ 取消 ]  [ 生成方案 ]                      │
└─────────────────────────────────────────────┘
```

### 4.4 API设计

```python
# POST /api/v1/control/strategies/batch_generate
{
  "generation_mode": "parameter_sweep",
  "base_template_id": "vss_moderate",
  "sweep_config": {
    "parameter": "speed_limit",
    "start": 60,
    "end": 100,
    "step": 10,
    "unit": "km/h"
  },
  "naming_pattern": "vss_speed{value}"
}

# Response
{
  "generated_strategies": [
    {"strategy_id": "vss_speed60", "strategy_name": "限速60km/h策略"},
    {"strategy_id": "vss_speed70", "strategy_name": "限速70km/h策略"},
    ...
  ],
  "count": 5
}
```

```python
# POST /api/v1/control/plans/batch_generate
{
  "generation_mode": "incremental_combination",
  "strategy_ids": ["vss_001", "dhs_001", "tec_001"],
  "include_baseline": true
}

# Response
{
  "generated_plans": [
    {"plan_id": "plan_baseline", "strategy_count": 0},
    {"plan_id": "plan_combo_1", "strategy_count": 1},
    {"plan_id": "plan_combo_2", "strategy_count": 2},
    {"plan_id": "plan_combo_3", "strategy_count": 3}
  ],
  "count": 4
}
```

---

## 5. 命名自动化策略

### 5.1 命名策略设计

| 对象 | 命名方式 | 推荐度 |
|-----|---------|-------|
| **策略ID** | 自动生成 | ⭐⭐⭐⭐⭐ 强烈推荐 |
| **策略名称** | 自动建议 + 用户可修改 | ⭐⭐⭐⭐ 推荐 |
| **方案ID** | 自动生成 | ⭐⭐⭐⭐⭐ 强烈推荐 |
| **方案名称** | 自动建议 + 用户可修改 | ⭐⭐⭐⭐ 推荐 |

### 5.2 策略ID自动生成规则

#### 规则: `{type}_{seq}` 或 `{type}_{location}_{seq}`

**示例**:
```
vss_001
vss_k8_k10_001
dhs_001
dhs_k10_k15_001
tec_001
tec_k12_001
```

**Python实现**:
```python
def generate_strategy_id(strategy_type: str, location: str = None) -> str:
    """
    自动生成策略ID

    Args:
        strategy_type: VSS/DHS/TEC
        location: 可选,路段标识(如k8_k10)

    Returns:
        策略ID
    """
    # 查询已有策略数量
    existing_count = count_strategies_by_type(strategy_type)
    seq = existing_count + 1

    type_prefix = strategy_type.lower()

    if location:
        return f"{type_prefix}_{location}_{seq:03d}"
    else:
        return f"{type_prefix}_{seq:03d}"

# 使用示例
strategy_id = generate_strategy_id("VSS", "k8_k10")  # vss_k8_k10_001
```

### 5.3 策略名称自动建议规则

#### 规则: `{路段/入口} + {管控类型} + {关键参数}`

**VSS策略命名**:
```python
def suggest_vss_name(edges: list, speed_limit_kmh: int) -> str:
    """
    自动建议VSS策略名称

    示例:
    - edges=["edge_800", "edge_801"], speed=80
      → "K8-K10路段限速80km/h"
    """
    # 从edge ID提取桩号(假设edge_800表示K8)
    start_km = extract_km_from_edge(edges[0])
    end_km = extract_km_from_edge(edges[-1])

    return f"K{start_km}-K{end_km}路段限速{speed_limit_kmh}km/h"

# 结果: "K8-K10路段限速80km/h"
```

**DHS策略命名**:
```python
def suggest_dhs_name(edges: list, time_period: str) -> str:
    """
    自动建议DHS策略名称

    示例:
    - edges=["edge_1000",...], time_period="早高峰"
      → "K10-K15路段早高峰应急车道开放"
    """
    start_km = extract_km_from_edge(edges[0])
    end_km = extract_km_from_edge(edges[-1])

    return f"K{start_km}-K{end_km}路段{time_period}应急车道开放"

# 结果: "K10-K15路段早高峰应急车道开放"
```

**TEC策略命名**:
```python
def suggest_tec_name(entrance_name: str, control_type: str) -> str:
    """
    自动建议TEC策略名称

    示例:
    - entrance="锦江收费站", control_type="货车禁行"
      → "锦江收费站入口货车禁行"
    """
    return f"{entrance_name}入口{control_type}"

# 结果: "锦江收费站入口货车禁行"
```

### 5.4 方案命名自动建议

#### 规则: `{场景} + {管控类型组合}`

```python
def suggest_plan_name(strategy_ids: list, scenario: str = None) -> str:
    """
    自动建议方案名称

    Args:
        strategy_ids: 策略ID列表
        scenario: 可选,场景描述(如"早高峰")

    Returns:
        方案名称建议
    """
    # 统计策略类型
    strategy_types = [get_strategy_type(sid) for sid in strategy_ids]
    type_counts = {
        'VSS': strategy_types.count('VSS'),
        'DHS': strategy_types.count('DHS'),
        'TEC': strategy_types.count('TEC')
    }

    # 构建名称
    parts = []
    if type_counts['VSS'] > 0:
        parts.append('可变限速')
    if type_counts['DHS'] > 0:
        parts.append('应急车道开放')
    if type_counts['TEC'] > 0:
        parts.append('入口管控')

    strategy_desc = '+'.join(parts)

    if scenario:
        return f"{scenario}{strategy_desc}方案"
    else:
        return f"{strategy_desc}组合方案"

# 示例
suggest_plan_name(['vss_001', 'dhs_001', 'tec_001'], '早高峰')
# 结果: "早高峰可变限速+应急车道开放+入口管控方案"
```

### 5.5 前端交互设计

```
┌─────────────────────────────────────────────┐
│  创建策略 - VSS                              │
├─────────────────────────────────────────────┤
│  策略ID: [vss_k8_k10_001]  (自动生成) 🔒    │
│                                             │
│  策略名称: [K8-K10路段限速80km/h]            │
│            ↑ 自动建议,可修改                 │
│                                             │
│  路段选择: [edge_800, edge_801]             │
│  限速值:   [80] km/h                        │
│  时间段:   [07:00 - 09:00]                  │
│                                             │
│  [自动建议名称] [保存策略]                   │
└─────────────────────────────────────────────┘

说明:
- 策略ID: 🔒 自动生成,不可修改
- 策略名称: 自动建议,用户可修改
- [自动建议名称] 按钮: 根据当前参数重新生成建议名称
```

### 5.6 命名冲突处理

```python
def ensure_unique_name(base_name: str, object_type: str) -> str:
    """
    确保名称唯一,如有冲突自动追加序号

    Args:
        base_name: 基础名称
        object_type: 'strategy' 或 'plan'

    Returns:
        唯一名称
    """
    if not name_exists(base_name, object_type):
        return base_name

    # 追加序号
    counter = 2
    while True:
        new_name = f"{base_name} ({counter})"
        if not name_exists(new_name, object_type):
            return new_name
        counter += 1

# 示例
ensure_unique_name("K8-K10路段限速80km/h", "strategy")
# 如果已存在,返回: "K8-K10路段限速80km/h (2)"
```

---

## 6. 实施建议

### 阶段1: 策略模板重构 (优先级: P0)

- [ ] 按文档v2.0附录A重新创建5个策略模板
- [ ] 更新模板格式:
  - [ ] 参数Schema改为对象格式
  - [ ] 时间格式统一为秒
  - [ ] 车型使用SUMO vClass
  - [ ] VSS支持edges属性
- [ ] 删除从net.xml识别入口的代码
- [ ] 新增从数据库查询入口的功能

### 阶段2: 快速生成功能 (优先级: P1)

- [ ] 实现参数扫描生成API
- [ ] 实现方案组合生成API
- [ ] 开发前端快速生成界面

### 阶段3: 命名自动化 (优先级: P1)

- [ ] 实现策略ID自动生成
- [ ] 实现策略名称自动建议
- [ ] 实现方案名称自动建议
- [ ] 前端集成命名建议功能

### 阶段4: 文档更新 (优先级: P0)

- [ ] 更新research_v2.0第3-5节:
  - [ ] VSS改为使用edges属性
  - [ ] 车型改为SUMO vClass
  - [ ] 删除5.5节net.xml识别方法
  - [ ] 新增数据库查询方法

---

**文档结束**
