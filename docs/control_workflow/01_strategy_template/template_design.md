# 策略模板设计原理

本文档说明策略模板的设计原理和架构。

---

## 一、模板设计概述

### 1.1 什么是策略模板

策略模板（Strategy Template）是策略实例的**通用配置模板**，定义了：
- 策略类型（VSS/DHS/TEC）
- 参数结构（参数名称、类型、默认值）
- 参数验证规则
- SUMO XML生成规则

### 1.2 模板的作用

1. **标准化**: 统一策略配置格式，确保一致性
2. **简化**: 用户只需填写必要参数，模板提供默认值
3. **复用**: 一个模板可生成多个策略实例
4. **验证**: 模板定义验证规则，确保参数合法性

---

## 二、模板架构设计

### 2.1 模板文件结构

```json
{
  "template_id": "vss_moderate",
  "template_name": "可变限速 - 中等控制",
  "strategy_type": "VSS",
  "description": "适用于常规拥堵路段的可变限速控制",
  "parameters_schema": [
    {
      "parameter_name": "affected_edges",
      "parameter_type": "edge_array",
      "description": "受限速影响的路段edge ID列表",
      "required": true,
      "default_value": []
    },
    {
      "parameter_name": "speed_steps",
      "parameter_type": "speed_steps_array",
      "description": "速度时刻表，定义不同时间的限速值",
      "required": true,
      "default_value": [
        {"time_hours": 7, "speed_kmh": 80},
        {"time_hours": 9, "speed_kmh": 100}
      ]
    }
  ],
  "validation_rules": {
    "speed_range": [30, 120],
    "time_range": [0, 24]
  },
  "sumo_mapping": {
    "xml_element": "variableSpeedSign",
    "attributes": {
      "edges": "affected_edges"
    }
  }
}
```

### 2.2 模板类型分类

#### VSS模板（5种）

| 模板ID | 模板名称 | 适用场景 | 特点 |
|--------|---------|---------|------|
| `vss_moderate` | 中等控制 | 常规拥堵路段 | 标准限速配置 |
| `vss_strict` | 严格控制 | 严重拥堵路段 | 更严格的限速 |
| `vss_weather_based` | 天气应急 | 恶劣天气条件 | 渐进式限速 |
| `vss_upstream_warning` | 上游预警 | 事故预警 | 早期减速机制 |
| `vss_lane_differentiated` | 分车道控制 | 多车道差异限速 | 分车道独立控制 |

#### DHS模板（3种）

| 模板ID | 模板名称 | 适用场景 | 特点 |
|--------|---------|---------|------|
| `dhs_peak_hours` | 高峰开放 | 高峰时段 | 标准应急车道开放 |
| `dhs_passenger_only` | 仅客车 | 安全优先 | 仅允许客车通行 |
| `dhs_peak_multi_interval` | 多时段管理 | 复杂时段 | 多时段精细管理 |

#### TEC模板（3种）

| 模板ID | 模板名称 | 适用场景 | 特点 |
|--------|---------|---------|------|
| `tec_flow_metering` | 流量控制 | 入口流量限制 | 流量上限控制 |
| `tec_vehicle_restriction` | 车型限制 | 车型管控 | 禁止特定车型 |
| `tec_emergency_closure` | 紧急关闭 | 临时封闭 | 完全关闭入口 |

---

## 三、模板设计原则

### 3.1 单一职责原则

每个模板专注于一种特定的管控场景：
- ✅ `vss_moderate`: 常规拥堵限速
- ✅ `dhs_peak_hours`: 高峰应急车道开放
- ❌ 避免: 一个模板覆盖多种场景

### 3.2 参数化设计

模板使用参数化设计，支持灵活配置：
- 默认值：提供合理的默认参数
- 可选参数：非关键参数可选
- 参数验证：定义参数范围和格式

### 3.3 SUMO兼容性

模板设计考虑SUMO XML生成需求：
- 使用SUMO支持的属性（如`edges`而非`lanes`）
- 使用SUMO识别的车型类别（vClass）
- 时间格式符合SUMO要求（秒级时间戳）

---

## 四、模板创建流程

### 4.1 需求分析

1. **识别场景**: 确定模板适用的交通场景
2. **分析参数**: 识别关键参数和可选参数
3. **研究SUMO**: 了解SUMO XML生成要求

### 4.2 模板设计

1. **定义参数Schema**: 设计参数结构
2. **设置默认值**: 提供合理的默认参数
3. **定义验证规则**: 设置参数范围和格式要求
4. **设计SUMO映射**: 定义如何生成SUMO XML

### 4.3 模板实现

1. **创建JSON文件**: 在`templates/control_strategies/`目录创建模板文件
2. **更新索引**: 在`templates_index.json`中注册模板
3. **编写文档**: 说明模板用途和使用方法
4. **测试验证**: 测试模板生成策略实例和SUMO XML

---

## 五、模板技术规范

### 5.1 参数Schema格式

```json
{
  "parameter_name": "speed_steps",
  "parameter_type": "speed_steps_array",
  "description": "速度时刻表",
  "required": true,
  "default_value": [
    {"time_hours": 7, "speed_kmh": 80},
    {"time_hours": 9, "speed_kmh": 100}
  ],
  "validation": {
    "min_items": 2,
    "time_range": [0, 24],
    "speed_range": [30, 120]
  }
}
```

### 5.2 时间格式规范

**VSS策略**: 使用时刻点（Point in Time）
- 格式: `time_hours` (0-24小时)
- 含义: 从该时刻开始执行限速，直到下一个时刻

**DHS/TEC策略**: 使用时间段（Time Interval）
- 格式: `begin_hours` 和 `end_hours` (0-24小时)
- 含义: 该时间段内执行策略

### 5.3 车型格式规范

使用SUMO vClass，而非项目自定义车型ID：

| SUMO vClass | 说明 | 项目车型映射 |
|-------------|------|-------------|
| `passenger` | 乘用车 | passenger_small, passenger_large |
| `truck` | 货车 | truck_small, truck_large |
| `delivery` | 专用车 | special_small, special_large |
| `emergency` | 应急车辆 | - |
| `authority` | 权限车辆 | - |

---

## 六、模板最佳实践

### 6.1 命名规范

- 模板ID: `{strategy_type}_{scenario}` (小写+下划线)
- 示例: `vss_moderate`, `dhs_peak_hours`, `tec_flow_metering`

### 6.2 参数设计

- **必需参数**: 最少化，只包含关键参数
- **默认值**: 提供合理的默认值，减少用户配置
- **参数分组**: 相关参数组织在一起

### 6.3 文档完善

- 模板描述: 清晰说明适用场景
- 参数说明: 详细说明每个参数的含义和取值范围
- 使用示例: 提供典型使用案例

---

## 七、相关文档

- [模板类型说明](template_types.md)
- [模板创建流程](template_creation.md)
- [策略模板分析与建议](../../design/strategy_template_analysis_and_recommendations.md)

---

**文档版本**: v1.0
**创建日期**: 2025-01-XX






