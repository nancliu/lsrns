# 车型分类系统文档

## 概述

本文档描述OD_SIM系统中车型分类系统的架构设计，包括两层分类结构、模板引用方式和使用规范。

**更新日期**: 2025-11-01
**版本**: v0.9.1-dev

---

## 系统架构

### 两层分类设计

OD_SIM车型系统采用**两层映射架构**：

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 1: 用户界面层                         │
│                    (3类业务分类)                               │
├─────────────────────────────────────────────────────────────┤
│  客车 (passenger)                                             │
│  货车 (truck)                                                 │
│  特种车辆 (delivery)                                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ 映射关系
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    Layer 2: SUMO仿真层                        │
│                    (6类详细车型)                               │
├─────────────────────────────────────────────────────────────┤
│  passenger_small  → 小型客车 (长度4m, 最高速120km/h)           │
│  passenger_large  → 大型客车 (长度10m, 最高速100km/h)          │
│  truck_small      → 小型货车 (长度6m, 最高速90km/h)            │
│  truck_large      → 大型货车 (长度12m, 最高速80km/h)           │
│  special_small    → 小型特种车辆 (长度5m, 最高速100km/h)       │
│  special_large    → 大型特种车辆 (长度8m, 最高速90km/h)        │
└─────────────────────────────────────────────────────────────┘
```

### 设计原则

1. **用户友好**: 前端界面使用3类业务分类，符合交通管理直觉
2. **仿真精确**: SUMO仿真使用6类详细车型，包含尺寸、速度等物理参数
3. **自动映射**: 系统自动将用户选择的3类映射到SUMO的6类
4. **统一定义**: 所有车型枚举值存储在单一配置文件中

---

## 车型定义位置

### 主配置文件

**文件**: `templates/config_templates/vehicle_templates/vehicle_types_enum.json`

**用途**:
- 定义前端界面显示的3类车型选项
- 提供标签、描述、图标等UI元素
- 作为所有策略模板的车型枚举引用源

**内容示例**:

```json
{
  "enum_name": "vehicle_types_category",
  "version": "2.0",
  "description": "车型分类枚举定义（三类业务分类）",
  "categories": [
    {
      "value": "passenger",
      "label": "客车",
      "description": "乘用车辆，包含小型和大型客车",
      "icon": "🚗",
      "sumo_mapping": ["passenger_small", "passenger_large"],
      "color": "#4CAF50",
      "typical_scenarios": ["通勤高峰", "节假日出行", "城市日常交通"]
    },
    {
      "value": "truck",
      "label": "货车",
      "description": "货运车辆，包含小型和大型货车",
      "icon": "🚚",
      "sumo_mapping": ["truck_small", "truck_large"],
      "color": "#FF9800",
      "typical_scenarios": ["物流运输", "工业原料", "城市配送"]
    },
    {
      "value": "delivery",
      "label": "特种车辆",
      "description": "特种车辆，包含小型和大型特种车",
      "icon": "🚑",
      "sumo_mapping": ["special_small", "special_large"],
      "color": "#2196F3",
      "typical_scenarios": ["应急救援", "市政作业", "特殊运输"]
    }
  ]
}
```

### SUMO车型参数文件

**文件**: `templates/config_templates/vehicle_templates/vehicle_types.json`

**用途**:
- 定义SUMO仿真所需的6类详细车型参数
- 包含物理属性: 长度、加速度、减速度、最高速度等
- 包含视觉属性: 颜色、车辆类别等

**内容示例**:

```json
{
  "vehicle_types": [
    {
      "id": "passenger_small",
      "vClass": "passenger",
      "accel": 2.6,
      "decel": 4.5,
      "length": 4.0,
      "maxSpeed": 33.33,
      "speedFactor": 1.0,
      "speedDev": 0.1,
      "color": "0,255,0"
    },
    {
      "id": "truck_large",
      "vClass": "truck",
      "accel": 1.0,
      "decel": 3.0,
      "length": 12.0,
      "maxSpeed": 22.22,
      "speedFactor": 0.9,
      "speedDev": 0.05,
      "color": "255,140,0"
    }
    // ... 其他4类
  ]
}
```

---

## 模板引用方式

### 方式1: 直接定义 enum_values

**使用场景**: 大部分DHS模板

**示例**: `dhs_peak_hours.json`

```json
{
  "parameter_name": "allowed_vehicle_types",
  "parameter_type": "enum_array",
  "enum_values": [
    { "value": "passenger", "label": "客车", "description": "..." },
    { "value": "truck", "label": "货车", "description": "..." },
    { "value": "delivery", "label": "特种车辆", "description": "..." }
  ],
  "default_value": ["passenger", "truck", "delivery"]
}
```

**优点**:
- 模板自包含，无需外部依赖
- 可自定义描述文本

**缺点**:
- 车型定义重复，维护成本高
- 修改车型需要同步多个模板

### 方式2: 引用 enum_name

**使用场景**: TEC模板（车型限制）

**示例**: `tec_vehicle_restriction.json`

```json
{
  "parameter_name": "disallow_vehicle_types",
  "parameter_type": "enum_array",
  "enum_name": "vehicle_types_category",
  "enum_values": null,
  "default_value": ["truck"]
}
```

**优点**:
- 统一引用，单一数据源
- 修改 `vehicle_types_enum.json` 即可全局生效
- 模板文件更简洁

**缺点**:
- 需要前端实现 fallback 机制
- 依赖外部文件

---

## 前端实现逻辑

### enum_name 处理机制

**文件位置**: `frontend/control/js/parameter_form.js:2613-2636`

**逻辑流程**:

```javascript
// 1. 尝试获取直接定义的 enum_values
let enumValues = param.enum_values || [];

// 2. 如果没找到，检查 enum_name
if (enumValues.length === 0) {
  const enumName = param.enum_name;

  // 3. 如果是标准车型枚举，使用 fallback 3分类
  if (enumName === 'vehicle_types_category') {
    enumValues = [
      { value: 'passenger', label: '客车', description: '乘用车辆，包含小型和大型客车' },
      { value: 'truck', label: '货车', description: '货运车辆，包含小型和大型货车' },
      { value: 'delivery', label: '特种车辆', description: '特种车辆，包含小型和大型特种车' }
    ];
  }
}

// 4. 渲染复选框
enumValues.forEach(enumVal => {
  // 创建 checkbox 控件
});
```

**关键点**:
- 优先使用 `enum_values`（直接定义）
- 如果为空，检查 `enum_name`
- 识别 `vehicle_types_category` 时，使用硬编码的3分类作为 fallback
- 保证两种引用方式的行为一致性

---

## 策略类型使用模式

### DHS (动态硬路肩)

**使用方式**: 主要使用直接定义 `enum_values`

**参数名**:
- `allowed_vehicle_types` - 应急车道开放时允许通行的车型

**常见配置**:

```json
// 全车型开放
"allowed_vehicle_types": ["passenger", "truck", "delivery"]

// 仅客车（高峰期禁货车）
"allowed_vehicle_types": ["passenger"]

// 仅特种车辆（紧急情况）
"allowed_vehicle_types": ["delivery"]
```

**模板示例**:
- `dhs_peak_hours.json` - 全车型开放
- `dhs_passenger_only.json` - 仅客车
- `dhs_emergency_only.json` - 仅特种车辆

### TEC (收费站管控)

**使用方式**: 使用 `enum_name` 引用

**参数名**:
- `restriction_mode` - 限制模式（禁止模式/允许模式）
- `disallow_vehicle_types` - 禁止进入的车型（禁止模式）
- `allowed_vehicle_types` - 允许进入的车型（允许模式）

**统一控件**:
前端使用 `renderUnifiedVehicleTypeControl()` 渲染单一车型选择器，根据 `restriction_mode` 动态切换标签和提示。

**常见配置**:

```json
// 禁止货车（高峰期）
{
  "restriction_mode": "disallow_mode",
  "disallow_vehicle_types": ["truck"]
}

// 仅允许客车（高峰期）
{
  "restriction_mode": "allow_mode",
  "allowed_vehicle_types": ["passenger"]
}
```

**模板示例**:
- `tec_vehicle_restriction.json` - 灵活车型限制

### VSS (可变限速)

**使用方式**: 通常不涉及车型限制

**说明**: VSS策略一般对所有车型生效，无需车型选择参数。如需按车型差异化限速，需扩展模板支持。

---

## 数据流

### 用户配置 → SUMO仿真

```
用户在前端选择车型
    ↓
例如: 选中 [passenger, truck]
    ↓
collectParameterValues() 收集
    ↓
配置数据包含: "allowed_vehicle_types": ["passenger", "truck"]
    ↓
提交到后端 API
    ↓
后端生成 SUMO 配置
    ↓
映射到 SUMO 详细车型
    ↓
sumo_mapping: ["passenger_small", "passenger_large", "truck_small", "truck_large"]
    ↓
写入 .add.xml 文件
    ↓
SUMO 仿真使用 6 类详细车型
```

### 映射规则

| 用户选择 | SUMO车型 | 车辆数量分配 |
|---------|---------|------------|
| passenger | passenger_small (70%), passenger_large (30%) | 按真实数据比例分配 |
| truck | truck_small (40%), truck_large (60%) | 按真实数据比例分配 |
| delivery | special_small (80%), special_large (20%) | 按真实数据比例分配 |

**注**: 具体分配比例在 OD数据处理阶段根据真实数据分析确定。

---

## 版本历史

### v2.0 (2025-10-25) - 当前版本

**变更内容**:
- ✅ 统一为3类业务分类: 客车、货车、特种车辆
- ✅ 移除 "公交车" (bus) 和 "应急车" (emergency) 分类
- ✅ 引入两层映射架构（UI 3类 → SUMO 6类）
- ✅ 创建 `vehicle_types_enum.json` 作为单一数据源
- ✅ TEC模板使用 `enum_name` 引用方式
- ✅ 前端实现 enum_name fallback 机制

**影响范围**:
- 所有DHS模板的车型参数描述
- 所有TEC模板的车型限制逻辑
- 前端车型控件渲染逻辑

### v1.0 (2025-10-xx) - 旧版本

**车型分类**:
- 乘用车 (passenger)
- 公交车 (bus) ❌ 已废弃
- 货车 (truck)
- 应急车 (emergency) ❌ 已废弃
- 特种车辆 (delivery)

**废弃原因**:
- "公交车" 和 "应急车" 在SUMO仿真中无明确对应车型
- 业务场景中，公交车可归入客车，应急车可归入特种车辆
- 简化分类提高用户理解和配置效率

---

## 维护指南

### 新增车型步骤

1. **确定业务分类**: 是否需要新的业务分类？还是归入现有3类？
2. **更新 vehicle_types_enum.json**:
   - 如需新业务分类，添加 category
   - 更新 `sumo_mapping` 字段
3. **更新 vehicle_types.json**:
   - 添加新的SUMO详细车型定义
   - 设置物理参数（长度、速度、加速度等）
4. **更新前端 fallback**:
   - 如新增业务分类，修改 `parameter_form.js` 的 fallback 数组
5. **更新所有模板**:
   - 如使用直接定义 `enum_values`，需逐个更新
   - 如使用 `enum_name`，自动生效
6. **测试所有策略模板**:
   - 检查前端渲染是否正确
   - 验证数据收集是否完整
   - 确认SUMO配置生成正确

### 修改车型属性

**场景**: 修改客车的最高速度、长度等物理参数

**步骤**:
1. 修改 `vehicle_types.json` 中对应车型的参数
2. 重新生成测试用例验证
3. 无需修改模板和前端代码

**影响**: 仅影响SUMO仿真行为，不影响UI显示

### 修改车型标签

**场景**: 将"客车"改为"乘用车"

**步骤**:
1. 修改 `vehicle_types_enum.json` 中的 `label` 字段
2. 如模板使用 `enum_name`，自动生效
3. 如模板使用直接定义，需逐个更新 `enum_values`
4. 更新前端 fallback 中的硬编码标签

**影响**: UI显示变化，数据收集逻辑不变

---

## 测试检查清单

### 新增/修改车型时

- [ ] `vehicle_types_enum.json` 定义完整（value, label, description, icon）
- [ ] `vehicle_types.json` 包含对应的SUMO详细车型
- [ ] `sumo_mapping` 字段正确映射
- [ ] 前端 fallback 机制包含新车型
- [ ] 所有策略类型测试通过（DHS, TEC, VSS）
- [ ] 数据收集逻辑正确
- [ ] SUMO配置生成正确
- [ ] 仿真结果验证

### 模板更新时

- [ ] 确定使用 `enum_values` 还是 `enum_name`
- [ ] 如使用 `enum_name`，验证 fallback 生效
- [ ] 如使用 `enum_values`，验证内容与 `vehicle_types_enum.json` 一致
- [ ] `default_value` 设置合理
- [ ] 前端渲染正确（无重复控件、无空白）
- [ ] 数据收集映射正确
- [ ] 用户界面友好（标签、提示清晰）

---

## 相关文档

- [参数表单架构文档](../frontend/parameter_form_architecture.md)
- [控制策略模板规范](../../templates/control_strategies/README.md)
- [SUMO车型配置指南](../sumo/vehicle_configuration.md)
- [前端开发规范](../../CLAUDE.md#frontend-development-standards)

---

## 常见问题

### Q1: 为什么前端只显示3类，SUMO使用6类？

**A**: 这是**用户友好 vs 仿真精确**的权衡设计：
- 前端3类符合交通管理人员的业务直觉（客车、货车、特种）
- SUMO 6类保证仿真精度（区分大小车辆，不同物理参数）
- 系统自动映射，用户无需关心底层细节

### Q2: 如何确定某个策略模板使用哪种引用方式？

**A**: 检查 `parameters_schema` 中车型参数的定义：
- 有 `enum_values` 数组 → 直接定义方式
- 有 `enum_name: "vehicle_types_category"` → 引用方式

### Q3: 修改 vehicle_types_enum.json 会影响哪些模板？

**A**:
- 直接影响: 所有使用 `enum_name` 引用的模板（主要是TEC）
- 间接影响: 使用直接定义的模板不会自动更新，需手动同步

**建议**: 逐步迁移所有模板到 `enum_name` 引用方式，实现单一数据源。

### Q4: 为什么TEC模板不直接定义 enum_values？

**A**:
- TEC模板的车型限制逻辑复杂（两种模式切换）
- 使用引用方式保证数据一致性
- 统一修改车型定义时，无需同步多个TEC模板

### Q5: 前端 fallback 机制何时触发？

**A**: 当满足以下条件时：
- 参数定义中 `enum_values` 为空或不存在
- 参数定义中存在 `enum_name` 字段
- `enum_name` 值为 `"vehicle_types_category"`

---

**维护者**: 开发团队
**反馈**: 如发现文档错误或需要补充，请在项目Issue中提出
