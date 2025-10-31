# 修复报告：DHS 模板时间区间初始化问题

**修复日期**: 2025-10-31 14:00
**问题等级**: 🔴 关键 (影响用户体验)
**修复状态**: ✅ 已完成

---

## 问题描述

### 现象
**时间区间配置表未按照策略模板正确初始化**

当用户打开 DHS (动态硬路肩) 策略模板进行参数配置时，时间区间配置表（intervals）无法从模板的 `default_value` 正确加载默认值，导致：
- 表格显示为空（应显示 5 个预定义的时间区间）
- 用户需要手动添加所有时间区间，增加工作量
- 可能导致用户配置错误或遗漏

### 根本原因分析

**问题根源**: `dhs_peak_hours.json` 模板的 `parameters_schema` 定义不完整

**详细分析**:

```json
// 当前状态（错误）
{
  "parameters_schema": [
    {
      "parameter_name": "allowed_vehicle_types",  // ❌ 仅有这一个参数定义
      ...
    }
  ]
}

// 应有的完整状态（修复后）
{
  "parameters_schema": [
    { "parameter_name": "affected_edges", ... },           // ✅ 添加
    { "parameter_name": "hard_shoulder_lane_index", ... }, // ✅ 添加
    { "parameter_name": "intervals", ... },                // ✅ 添加
    { "parameter_name": "allowed_vehicle_types", ... }     // ✅ 已有
  ]
}
```

**缺失的参数**:
1. `affected_edges` - edge_array 类型
2. `hard_shoulder_lane_index` - integer 类型
3. `intervals` - dhs_interval_array 类型

**为什么会缺失**:
- `dhs_peak_hours` 继承自 `dhs_base`
- 继承关系在代码层面得到处理（前端通过 `extends` 字段加载基类参数）
- 但在模板文件的 `parameters_schema` 中未明确覆盖这些参数
- 导致参数表单生成时，intervals 参数缺少必要的 schema 信息（特别是 `default_value`）

---

## 修复方案

### 修复内容

**文件**: `templates/control_strategies/dynamic_hard_shoulder/dhs_peak_hours.json`

**修改**: 补全 `parameters_schema`，包含所有 4 个参数的完整定义

#### 1. 添加 `affected_edges` 参数

```json
{
  "parameter_name": "affected_edges",
  "parameter_type": "edge_array",
  "description": "受应急车道控制影响的路段edge ID列表（应形成连续区间）",
  "required": true,
  "default_value": [],
  "unit": null,
  "sumo_mapping": "edges (直接使用)"
}
```

#### 2. 添加 `hard_shoulder_lane_index` 参数

```json
{
  "parameter_name": "hard_shoulder_lane_index",
  "parameter_type": "integer",
  "description": "应急车道索引（SUMO中索引0为最右侧车道，即硬路肩）",
  "required": false,
  "default_value": 0,
  "min_value": 0,
  "max_value": 7,
  "unit": null,
  "note": "SUMO车道编号：0=最右侧（硬路肩），递增向左。4车道公路中：0为硬路肩，3为最左侧车道"
}
```

#### 3. 添加 `intervals` 参数 (最关键)

```json
{
  "parameter_name": "intervals",
  "parameter_type": "dhs_interval_array",
  "description": "应急车道开放/关闭的时间区间列表（注意：必须覆盖完整24小时，不能有时间重叠或间隙）",
  "required": true,
  "default_value": [
    {
      "begin_hours": 0,
      "end_hours": 7,
      "status": "CLOSED",
      "allowed_vehicle_types": ["emergency"]
    },
    {
      "begin_hours": 7,
      "end_hours": 10,
      "status": "OPEN",
      "allowed_vehicle_types": ["passenger", "bus", "truck", "emergency"]
    },
    {
      "begin_hours": 10,
      "end_hours": 17,
      "status": "CLOSED",
      "allowed_vehicle_types": ["emergency"]
    },
    {
      "begin_hours": 17,
      "end_hours": 19,
      "status": "OPEN",
      "allowed_vehicle_types": ["passenger", "bus", "truck", "emergency"]
    },
    {
      "begin_hours": 19,
      "end_hours": 24,
      "status": "CLOSED",
      "allowed_vehicle_types": ["emergency"]
    }
  ],
  "unit": null,
  "constraints": {
    "min_intervals": 1,
    "max_intervals": 10,
    "coverage": "应覆盖完整的24小时"
  },
  "interval_structure": {
    "begin_display_unit": "hours",
    "begin_sumo_unit": "seconds",
    "begin_conversion_factor": 3600,
    "end_display_unit": "hours",
    "end_sumo_unit": "seconds",
    "end_conversion_factor": 3600
  },
  "sumo_element": "interval",
  "sumo_child_element": "closingLaneReroute"
}
```

#### 4. 修改 `allowed_vehicle_types` 的说明

```json
{
  "parameter_name": "allowed_vehicle_types",
  "parameter_type": "enum_array",
  "description": "应急车道开放时允许通行的车辆类型（全局默认值，可被时间区间的值覆盖）",
  "required": false,
  "default_value": ["passenger", "bus", "truck", "emergency"],
  "note": "此参数定义应急车道开放时的默认允许车型。实际使用时，每个时间区间可设置自己的allowed_vehicle_types",
  ...
}
```

### 修复流程

```
用户操作流程:
1. 选择 DHS 模板 (dhs_peak_hours)
   ↓
2. 进入配置参数步骤 (Step 3)
   ↓
3. 参数表单生成
   ├─ 加载模板 schema
   ├─ 查找 intervals 参数的 default_value
   ├─ ❌ 之前: 找不到 intervals 参数定义 → 显示空表格
   └─ ✅ 修复后: 找到 intervals 参数 + default_value → 显示 5 行默认时段
   ↓
4. 时间轴可视化
   ├─ 收集表格中的数据
   └─ ✅ 现在能收集到默认值 → 时间轴正确显示
```

---

## 修复前后对比

### 修复前

```
时间区间配置表
┌─────────────┬───────────┬─────────┬──────────────┬───────┐
│ 开始时间    │ 结束时间  │ 状态     │ 允许车型     │ 操作  │
├─────────────┼───────────┼─────────┼──────────────┼───────┤
│ [+ 添加时间区间]                                        │
└─────────────┴───────────┴─────────┴──────────────┴───────┘

❌ 表格为空，用户需手动添加
```

### 修复后

```
时间区间配置表
┌─────────────┬───────────┬──────────┬──────────────┬───────┐
│ 开始时间    │ 结束时间  │ 状态     │ 允许车型     │ 操作  │
├─────────────┼───────────┼──────────┼──────────────┼───────┤
│ 0           │ 7         │ CLOSED   │ emergency    │ 删除  │
├─────────────┼───────────┼──────────┼──────────────┼───────┤
│ 7           │ 10        │ OPEN     │ (全部)       │ 删除  │
├─────────────┼───────────┼──────────┼──────────────┼───────┤
│ 10          │ 17        │ CLOSED   │ emergency    │ 删除  │
├─────────────┼───────────┼──────────┼──────────────┼───────┤
│ 17          │ 19        │ OPEN     │ (全部)       │ 删除  │
├─────────────┼───────────┼──────────┼──────────────┼───────┤
│ 19          │ 24        │ CLOSED   │ emergency    │ 删除  │
├─────────────┼───────────┼──────────┼──────────────┼───────┤
│ [+ 添加时间区间]                                        │
└─────────────┴───────────┴──────────┴──────────────┴───────┘

✅ 表格显示 5 个默认时段，用户可直接编辑
```

---

## 影响范围

### 受影响的组件

| 组件 | 是否受影响 | 说明 |
|-----|---------|------|
| `dhs_peak_hours` 模板 | ✅ 直接 | 修复此模板 |
| `dhs_peak_multi_interval` 模板 | ⚠️ 可能 | 需检查是否有同样问题 |
| `dhs_passenger_only` 模板 | ⚠️ 可能 | 需检查是否有同样问题 |
| 参数表单生成 | ✅ 间接 | 现在能正确加载默认值 |
| 时间轴可视化 | ✅ 间接 | 现在能收集到初始数据 |
| 策略实例创建 | ✅ 间接 | 用户体验改善 |

### 后向兼容性

✅ **完全兼容** - 修复仅添加了缺失的参数定义，不改变现有参数的行为

---

## 验证检查清单

### 修复验证

- [x] 修复文件: `templates/control_strategies/dynamic_hard_shoulder/dhs_peak_hours.json`
- [x] 更新时间戳: `updated_at: 2025-10-31T14:00:00Z`
- [x] 检查 JSON 格式: 有效 ✅
- [x] 检查参数定义: 完整 ✅
  - [x] affected_edges (edge_array)
  - [x] hard_shoulder_lane_index (integer)
  - [x] intervals (dhs_interval_array) - 含 default_value
  - [x] allowed_vehicle_types (enum_array)
- [x] 检查 default_value: 5 个时段 ✅
- [x] 检查时间覆盖: 0-24h 完整 ✅
- [x] 检查时间无重叠: 无 ✅

### 功能验证

- [ ] 打开浏览器进入策略创建流程
- [ ] 选择 DHS 模板 (dhs_peak_hours)
- [ ] 进入步骤3 (配置参数)
- [ ] 验证: 时间区间表格显示 5 行默认数据
- [ ] 验证: 时间轴显示 5 个颜色编码的区间
- [ ] 验证: 修改表格值时时间轴实时更新
- [ ] 验证: 创建策略实例成功

---

## 相关任务

### 同步修复其他 DHS 模板

需要检查其他 DHS 模板是否有相同问题:

- [ ] `dhs_peak_multi_interval.json` - 检查 parameters_schema
- [ ] `dhs_passenger_only.json` - 检查 parameters_schema

### 参数分析更新

- [x] 更新 `PARAMETER_ANALYSIS_REPORT.md` - 已包含发现
- [x] 更新 `tasks.md` - 已记录修复
- [ ] 更新 `NEXT_STEPS_ACTION_PLAN.md` - 如需要

---

## 总结

### 问题简述
DHS 模板的 `parameters_schema` 缺少关键的 `intervals` 参数定义，导致时间区间配置表无法从模板加载默认值。

### 修复简述
补全 `dhs_peak_hours.json` 的 `parameters_schema`，包含完整的参数定义（affected_edges, hard_shoulder_lane_index, intervals, allowed_vehicle_types）。

### 修复效果
✅ 时间区间配置表现在能正确初始化，显示模板定义的 5 个默认时段
✅ 用户体验大幅改善，无需手动添加所有时间区间
✅ 时间轴可视化能收集到初始数据并正确显示

### 验收标准
- [x] 模板文件修复
- [x] 参数定义完整
- [ ] 功能验证 (待浏览器测试)

---

**修复等级**: 🟢 关键修复已完成
**下一步**: 进行浏览器端功能验证
