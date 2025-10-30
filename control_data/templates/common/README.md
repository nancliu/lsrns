# 控制策略模板 - 公共配置

本目录包含策略模板中复用的全局配置文件。

## 配置文件列表

### 1. `vehicle_types_enum.json` - 车辆类型枚举

定义控制策略中使用的车辆类型，与SUMO `vClass`保持一致。

**使用方式**:
```json
{
  "parameter_name": "allowed_vehicle_types",
  "parameter_type": "enum_array",
  "enum_ref": "@common/vehicle_types_enum",
  "default_value": ["passenger", "bus", "truck", "emergency"]
}
```

**支持的车辆类型**:
- `passenger`: 乘用车 (客车)
- `bus`: 公交车
- `truck`: 货车
- `delivery`: 配送车
- `emergency`: 应急车
- `authority`: 执法车

### 2. `unit_conversions.json` - 单位转换配置

定义时间、速度、距离等单位的转换因子和约束范围。

**使用方式**:
```json
{
  "step_structure": {
    "time_conversion": "@common/unit_conversions#conversions.time",
    "speed_conversion": "@common/unit_conversions#conversions.speed",
    "speed_constraints": "@common/unit_conversions#constraints.speed"
  }
}
```

**转换因子**:
- **时间**: hours → seconds (× 3600)
- **速度**: km/h → m/s (× 0.277778 或 ÷ 3.6)
- **距离**: meters → meters (× 1)

**约束范围**:
- **速度**: 30-130 km/h (高速公路场景)
- **时间**: 0-24 hours (24小时制)
- **流量**: 0-2400 vehicles/hour (单车道)

## 引用语法

### 方式1: 引用整个枚举
```json
"enum_ref": "@common/vehicle_types_enum"
```

### 方式2: 引用特定配置项
```json
"conversion_ref": "@common/unit_conversions#conversions.time"
```

### 方式3: 引用约束
```json
"constraints_ref": "@common/unit_conversions#constraints.speed"
```

## 实现状态

**Phase 2 (当前)**: 配置文件已创建
- ✅ `vehicle_types_enum.json` - 车辆类型枚举
- ✅ `unit_conversions.json` - 单位转换配置

**Phase 2 (待完成)**: 模板引用更新
- ⚠️ 模板文件中仍使用内联定义，需要逐步迁移到引用语法
- ⚠️ 代码层面的引用解析机制待实现

**Phase 3 (计划)**: 模板继承机制
- 📋 实现 `extends` 关键字支持
- 📋 DHS模板重构为继承结构

## 维护指南

### 添加新车辆类型
1. 编辑 `vehicle_types_enum.json`
2. 在 `values` 数组中添加新条目
3. 确保 `sumo_vClass` 与 SUMO配置一致
4. 更新 `version` 和 `updated_at`

### 修改单位转换
1. 编辑 `unit_conversions.json`
2. 修改 `conversions` 或 `constraints` 对应项
3. 更新 `version` 和 `updated_at`
4. 检查是否需要更新代码中的转换逻辑

## 版本历史

- **v1.0** (2025-10-29): 初始版本
  - 创建车辆类型枚举
  - 创建单位转换配置
  - 定义引用语法规范
