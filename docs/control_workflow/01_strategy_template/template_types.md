# 策略模板类型说明

本文档详细说明所有可用的策略模板类型及其特点。

---

## 一、VSS模板（可变限速）

### 1.1 vss_moderate - 中等控制

**适用场景**: 常规拥堵路段，需要适度的限速控制

**参数特点**:
- 限速范围: 60-100 km/h
- 时刻点: 3-5个
- 限速变化: 渐进式（每次变化≤20 km/h）

**典型配置**:
```json
{
  "speed_steps": [
    {"time_hours": 6, "speed_kmh": 100},
    {"time_hours": 7, "speed_kmh": 80},
    {"time_hours": 9, "speed_kmh": 100}
  ]
}
```

---

### 1.2 vss_strict - 严格控制

**适用场景**: 严重拥堵路段，需要严格的限速控制

**参数特点**:
- 限速范围: 40-80 km/h
- 时刻点: 4-6个
- 限速变化: 更严格的限速值

**典型配置**:
```json
{
  "speed_steps": [
    {"time_hours": 6, "speed_kmh": 80},
    {"time_hours": 7, "speed_kmh": 60},
    {"time_hours": 8, "speed_kmh": 50},
    {"time_hours": 9, "speed_kmh": 60},
    {"time_hours": 10, "speed_kmh": 80}
  ]
}
```

---

### 1.3 vss_weather_based - 天气应急

**适用场景**: 恶劣天气条件（大雾、暴雨、冰雪）

**参数特点**:
- 天气条件参数: `weather_condition` (enum)
- 预设配置: 大雾/暴雨/冰雪三种预设
- 渐进式限速: 6步渐进反映天气过程

**典型配置**:
```json
{
  "weather_condition": "fog",
  "speed_steps": [
    {"time_hours": 0, "speed_kmh": 100},
    {"time_hours": 6, "speed_kmh": 80},
    {"time_hours": 7, "speed_kmh": 60},
    {"time_hours": 8, "speed_kmh": 40},
    {"time_hours": 9, "speed_kmh": 60},
    {"time_hours": 10, "speed_kmh": 100}
  ]
}
```

---

### 1.4 vss_upstream_warning - 上游预警

**适用场景**: 事故预警，需要上游提前减速

**参数特点**:
- 预警提前时间: `warning_advance_minutes`
- 固定3-5步预警模式
- 与下游事件的时间协调

**典型配置**:
```json
{
  "warning_advance_minutes": 30,
  "speed_steps": [
    {"time_hours": 7, "speed_kmh": 100},
    {"time_hours": 7.5, "speed_kmh": 80},
    {"time_hours": 8, "speed_kmh": 60}
  ]
}
```

---

### 1.5 vss_lane_differentiated - 分车道控制

**适用场景**: 多车道差异限速（如货车道限速低于乘用车道）

**参数特点**:
- 车道配置: `lane_configurations`
- 相对速度模式: `speed_offset`
- 为每个车道生成独立VSS元素

**典型配置**:
```json
{
  "lane_configurations": [
    {"lane_index": 0, "speed_offset": 0},
    {"lane_index": 1, "speed_offset": -10},
    {"lane_index": 2, "speed_offset": -20}
  ]
}
```

---

## 二、DHS模板（动态硬路肩）

### 2.1 dhs_peak_hours - 高峰开放

**适用场景**: 高峰时段应急车道开放

**参数特点**:
- 时间段配置: 必须覆盖24小时
- 开放时段: 7-9, 17-19
- 允许车型: 所有车型（默认）

**典型配置**:
```json
{
  "intervals": [
    {"begin_hours": 0, "end_hours": 7, "status": "CLOSED"},
    {"begin_hours": 7, "end_hours": 9, "status": "OPEN"},
    {"begin_hours": 9, "end_hours": 17, "status": "CLOSED"},
    {"begin_hours": 17, "end_hours": 19, "status": "OPEN"},
    {"begin_hours": 19, "end_hours": 24, "status": "CLOSED"}
  ],
  "allowed_vehicle_types": ["passenger", "truck", "delivery"]
}
```

---

### 2.2 dhs_passenger_only - 仅客车

**适用场景**: 安全优先，仅允许客车使用应急车道

**参数特点**:
- 允许车型: 仅`passenger`
- 禁止货车: 提高安全性

**典型配置**:
```json
{
  "intervals": [
    {"begin_hours": 7, "end_hours": 9, "status": "OPEN"},
    {"begin_hours": 9, "end_hours": 17, "status": "CLOSED"},
    {"begin_hours": 17, "end_hours": 19, "status": "OPEN"},
    {"begin_hours": 19, "end_hours": 7, "status": "CLOSED"}
  ],
  "allowed_vehicle_types": ["passenger"]
}
```

---

### 2.3 dhs_peak_multi_interval - 多时段管理

**适用场景**: 复杂时段管理，需要精细控制

**参数特点**:
- 多个开放时段
- 不同时段允许不同车型
- 更精细的时间控制

**典型配置**:
```json
{
  "intervals": [
    {"begin_hours": 6, "end_hours": 7, "status": "OPEN", "allowed_vehicle_types": ["passenger"]},
    {"begin_hours": 7, "end_hours": 9, "status": "OPEN", "allowed_vehicle_types": ["passenger", "truck"]},
    {"begin_hours": 9, "end_hours": 17, "status": "CLOSED"},
    {"begin_hours": 17, "end_hours": 20, "status": "OPEN", "allowed_vehicle_types": ["passenger", "truck"]},
    {"begin_hours": 20, "end_hours": 6, "status": "CLOSED"}
  ]
}
```

---

## 三、TEC模板（入口管控）

### 3.1 tec_flow_metering - 流量控制

**适用场景**: 入口流量限制，控制进入主线的车辆数量

**参数特点**:
- 流量上限: `vehsPerHour` (车辆/小时)
- 目标速度: `target_speed` (km/h)
- 时间段配置: 仅配置需要控制的时段

**典型配置**:
```json
{
  "entrance_edge": "-10592",
  "flow_intervals": [
    {
      "begin_hours": 7,
      "end_hours": 9,
      "vehsPerHour": 400,
      "target_speed": 60
    },
    {
      "begin_hours": 17,
      "end_hours": 19,
      "vehsPerHour": 350,
      "target_speed": 50
    }
  ]
}
```

---

### 3.2 tec_vehicle_restriction - 车型限制

**适用场景**: 禁止特定车型进入（如货车限行）

**参数特点**:
- 禁止车型: `banned_vehicle_types` (SUMO vClass)
- 时间段配置: 限制时段

**典型配置**:
```json
{
  "entrance_edge": "-10592",
  "intervals": [
    {
      "begin_hours": 7,
      "end_hours": 9,
      "banned_vehicle_types": ["truck"]
    }
  ]
}
```

---

### 3.3 tec_emergency_closure - 紧急关闭

**适用场景**: 临时封闭入口（事故、施工等）

**参数特点**:
- 关闭时段: `closure_time`
- 完全禁止: 所有车型禁止进入

**典型配置**:
```json
{
  "entrance_edge": "-10592",
  "closure_time": {
    "begin_hours": 8,
    "end_hours": 12
  }
}
```

---

## 四、模板选择指南

### 4.1 选择原则

| 场景特征 | 推荐模板 |
|---------|---------|
| 常规拥堵 | `vss_moderate` |
| 严重拥堵 | `vss_strict` |
| 恶劣天气 | `vss_weather_based` |
| 事故预警 | `vss_upstream_warning` |
| 分车道限速 | `vss_lane_differentiated` |
| 高峰应急车道 | `dhs_peak_hours` |
| 安全优先 | `dhs_passenger_only` |
| 复杂时段 | `dhs_peak_multi_interval` |
| 流量限制 | `tec_flow_metering` |
| 车型限制 | `tec_vehicle_restriction` |
| 临时封闭 | `tec_emergency_closure` |

### 4.2 组合使用

多个模板可以组合使用：
- VSS + DHS: 限速 + 应急车道开放
- VSS + TEC: 限速 + 入口限流
- DHS + TEC: 应急车道 + 入口管控
- VSS + DHS + TEC: 全策略组合

---

## 五、相关文档

- [模板设计原理](template_design.md)
- [模板创建流程](template_creation.md)
- [策略创建用户指南](../../user_guides/strategy_creation_guide.md)

---

**文档版本**: v1.0
**创建日期**: 2025-01-XX








