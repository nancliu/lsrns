# 策略参数配置说明

本文档详细说明策略实例的参数配置方法。

---

## 一、参数配置概述

### 1.1 参数来源

策略实例的参数来自两个来源：
1. **模板默认值**: 模板定义的默认参数
2. **用户配置**: 用户在创建实例时配置的参数

### 1.2 参数类型

| 参数类型 | 说明 | 示例 |
|---------|------|------|
| `edge_array` | 路段ID数组 | `["-9292", "-8014"]` |
| `speed_steps_array` | 速度时刻表 | `[{"time_hours": 7, "speed_kmh": 80}]` |
| `time_intervals_array` | 时间段数组 | `[{"begin_hours": 7, "end_hours": 9}]` |
| `flow_intervals_array` | 流量控制时段 | `[{"begin_hours": 7, "end_hours": 9, "vehsPerHour": 400}]` |
| `vehicle_types_array` | 车型数组 | `["passenger", "truck"]` |

---

## 二、VSS参数配置

### 2.1 speed_steps配置

**参数结构**:
```json
{
  "speed_steps": [
    {"time_hours": 7, "speed_kmh": 80},
    {"time_hours": 9, "speed_kmh": 100}
  ]
}
```

**配置说明**:
- `time_hours`: 时刻点（0-24小时）
- `speed_kmh`: 限速值（30-120 km/h）
- 每个时刻点是起始点，限速持续到下一个时刻点

**配置示例**:
```json
{
  "speed_steps": [
    {"time_hours": 6, "speed_kmh": 120},   // 6:00-7:00: 120 km/h
    {"time_hours": 7, "speed_kmh": 100},   // 7:00-8:00: 100 km/h
    {"time_hours": 8, "speed_kmh": 80},    // 8:00-9:00: 80 km/h
    {"time_hours": 9, "speed_kmh": 100},   // 9:00-次日6:00: 100 km/h
  ]
}
```

**验证规则**:
- ✅ 至少2个时刻点
- ✅ 时间范围: 0-24小时
- ✅ 速度范围: 30-120 km/h
- ✅ 时刻点按时间顺序排列

---

## 三、DHS参数配置

### 3.1 intervals配置

**参数结构**:
```json
{
  "intervals": [
    {
      "begin_hours": 0,
      "end_hours": 7,
      "status": "CLOSED",
      "allowed_vehicle_types": ["emergency"]
    },
    {
      "begin_hours": 7,
      "end_hours": 9,
      "status": "OPEN",
      "allowed_vehicle_types": ["passenger", "truck"]
    }
  ]
}
```

**配置说明**:
- `begin_hours`: 开始时间（0-24小时）
- `end_hours`: 结束时间（0-24小时，可跨日）
- `status`: 状态（"OPEN"或"CLOSED"）
- `allowed_vehicle_types`: 允许的车型（SUMO vClass）

**重要要求**:
- ⚠️ **必须覆盖完整24小时**
- ⚠️ 时间段不能有间隙
- ⚠️ 跨日时段: `{"begin_hours": 19, "end_hours": 7}` 表示19:00-次日7:00

**配置示例**:
```json
{
  "intervals": [
    {"begin_hours": 0, "end_hours": 7, "status": "CLOSED"},
    {"begin_hours": 7, "end_hours": 9, "status": "OPEN"},
    {"begin_hours": 9, "end_hours": 17, "status": "CLOSED"},
    {"begin_hours": 17, "end_hours": 19, "status": "OPEN"},
    {"begin_hours": 19, "end_hours": 24, "status": "CLOSED"}
  ]
}
```

**验证规则**:
- ✅ 必须覆盖24小时
- ✅ 时间段无间隙
- ✅ 状态为"OPEN"或"CLOSED"

---

## 四、TEC参数配置

### 4.1 flow_intervals配置

**参数结构**:
```json
{
  "entrance_edge": "-10592",
  "flow_intervals": [
    {
      "begin_hours": 7,
      "end_hours": 9,
      "vehsPerHour": 400,
      "target_speed": 60
    }
  ]
}
```

**配置说明**:
- `entrance_edge`: 入口匝道edge ID
- `begin_hours`: 开始时间
- `end_hours`: 结束时间
- `vehsPerHour`: 流量上限（车辆/小时）
- `target_speed`: 目标速度（km/h）

**配置示例**:
```json
{
  "entrance_edge": "-10592",
  "flow_intervals": [
    {
      "begin_hours": 0,
      "end_hours": 7,
      "vehsPerHour": 600,
      "target_speed": 20
    },
    {
      "begin_hours": 7,
      "end_hours": 9,
      "vehsPerHour": 240,
      "target_speed": 10
    },
    {
      "begin_hours": 9,
      "end_hours": 24,
      "vehsPerHour": 600,
      "target_speed": 20
    }
  ]
}
```

**验证规则**:
- ✅ 流量范围: 50-1000 veh/hr
- ✅ 速度范围: 30-120 km/h
- ✅ 时间段不要求覆盖24小时（非控制时段无限制）

---

### 4.2 banned_vehicle_types配置

**参数结构**:
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

**配置说明**:
- `banned_vehicle_types`: 禁止的车型（SUMO vClass）
- 时间段内禁止指定车型进入

---

## 五、车型配置

### 5.1 车型类别

使用SUMO vClass，而非项目自定义ID：

| SUMO vClass | 说明 | 使用场景 |
|-------------|------|---------|
| `passenger` | 乘用车 | DHS允许、TEC禁止 |
| `truck` | 货车 | DHS允许、TEC禁止 |
| `delivery` | 专用车 | DHS允许 |
| `emergency` | 应急车辆 | DHS始终允许 |
| `authority` | 权限车辆 | 特殊管控 |

### 5.2 配置方式

**允许模式** (DHS):
```json
{
  "allowed_vehicle_types": ["passenger", "truck"]
}
```

**禁止模式** (TEC):
```json
{
  "banned_vehicle_types": ["truck"]
}
```

---

## 六、参数验证

### 6.1 实时验证

前端在用户输入时实时验证：
- 时间范围检查
- 数值范围检查
- 格式检查
- 依赖关系检查

### 6.2 保存前验证

保存策略实例前进行完整验证：
- 必填参数检查
- 参数值合法性检查
- 参数间依赖检查
- DHS 24小时覆盖检查

---

## 七、参数优化建议

### 7.1 VSS参数优化

**限速值选择**:
- 基于自由流速度: `限速 = 自由流速度 × (0.6~0.8)`
- 基于拥堵程度: 速度<20 km/h → 限速50 km/h

**时刻点设置**:
- 高峰期前1小时: 预警降速
- 高峰期: 严格限速
- 高峰期后1小时: 恢复

### 7.2 DHS参数优化

**开放时段**:
- 只在高峰时段开放（7-9, 17-19）
- 避免全天开放（失去动态意义）

**车型限制**:
- 安全优先: 仅允许客车
- 容量优先: 允许所有车型

### 7.3 TEC参数优化

**流量限制**:
- 计算公式: `(主线容量 - 主线流量) × 0.9`
- 保留10%安全余量

**目标速度**:
- 10-20 km/h: 强制限流
- 20-30 km/h: 适度限流

---

## 八、相关文档

- [实例生成流程](instance_generation.md)
- [实例验证机制](instance_validation.md)
- [策略创建用户指南](../../user_guides/strategy_creation_guide.md)

---

**文档版本**: v1.0
**创建日期**: 2025-01-XX





