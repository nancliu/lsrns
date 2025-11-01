# 车型两层关系设计

**日期**: 2025-11-01
**重要性**: ⭐⭐⭐ 关键设计
**议题**: 策略级别车型与SUMO仿真车型的两层关系

---

## 🎯 问题陈述

当用户在策略中选择 **"客车"** 或 **"货车"** 时，系统应该自动包含该大类下的 **所有详细车型**。

### 例子

```
用户选择: 客车
应实际包含: passenger_small + passenger_large

用户选择: 货车
应实际包含: truck_small + truck_large

用户选择: 特种车
应实际包含: special_small + special_large
```

**问题**: 当前前端和后端没有建立这种对应关系，导致：
- 用户可能误选高级车型，不知道实际包含哪些仿真车型
- 参数验证可能接受"客车"但SUMO中没有定义
- 无法自动转换高级选择为详细车型

---

## 📐 两层架构分析

### 层级关系

```
高级层 (策略配置层)
├─ passenger (客车)
│  ├─ passenger_small (小型客车 k1, k2)
│  └─ passenger_large (大型客车 k3, k4)
├─ truck (货车)
│  ├─ truck_small (小型货车 h1, h2)
│  └─ truck_large (大型货车 h3-h6)
├─ delivery (特种车/配送)
│  ├─ special_small (小型特种 t1, t2)
│  └─ special_large (大型特种 t3-t6)
├─ bus (公交车) - 无详细级
├─ emergency (应急车) - 无详细级
└─ authority (执法车) - 无详细级

详细层 (SUMO仿真层)
├─ passenger_small
├─ passenger_large
├─ truck_small
├─ truck_large
├─ special_small
└─ special_large
```

### 数据关系映射

```json
{
  "vehicle_type_hierarchy": {
    "passenger": {
      "label": "乘用车 (客车)",
      "description": "包含小型和大型乘用车",
      "sumo_vClass": "passenger",
      "includes": ["passenger_small", "passenger_large"],
      "example_ids": ["k1", "k2", "k3", "k4"]
    },
    "truck": {
      "label": "货车",
      "description": "包含小型和大型货车",
      "sumo_vClass": "truck",
      "includes": ["truck_small", "truck_large"],
      "example_ids": ["h1", "h2", "h3", "h4", "h5", "h6"]
    },
    "delivery": {
      "label": "配送车 (特种车)",
      "description": "特种车辆，包括小型和大型配送车",
      "sumo_vClass": "delivery",
      "includes": ["special_small", "special_large"],
      "example_ids": ["t1", "t2", "t3", "t4", "t5", "t6"]
    },
    "bus": {
      "label": "公交车",
      "description": "公共交通客车",
      "sumo_vClass": "bus",
      "includes": [],
      "note": "暂无详细级定义"
    },
    "emergency": {
      "label": "应急车",
      "description": "应急车辆 (救护车、消防车、警车)",
      "sumo_vClass": "emergency",
      "includes": [],
      "note": "暂无详细级定义"
    },
    "authority": {
      "label": "执法车",
      "description": "执法和管理车辆",
      "sumo_vClass": "authority",
      "includes": [],
      "note": "暂无详细级定义"
    }
  }
}
```

---

## 🏗️ 推荐的三层架构

### 层1: 车型定义源 (vehicle_types.json)

```json
{
  "vehicle_types": {
    "passenger_small": {
      "id_prefix": "k",
      "vClass": "passenger",
      "valid_ids": ["k1", "k2"],
      "category": "passenger",  // ← 新增: 指向高级类别
      "label": "小型客车 (k1, k2)"
    },
    "passenger_large": {
      "id_prefix": "k",
      "vClass": "passenger",
      "valid_ids": ["k3", "k4"],
      "category": "passenger",  // ← 新增
      "label": "大型客车 (k3, k4)"
    },
    // ... 其他车型
  }
}
```

### 层2: 车型枚举定义 (vehicle_types_enum.json)

保持为两个枚举值组：

```json
{
  "enums": {
    "vehicle_types_detailed": {
      "id": "vehicle_types_detailed",
      "label": "车型 (详细)",
      "level": "detailed",
      "values": [
        {
          "value": "passenger_small",
          "label": "小型客车 (k1, k2)",
          "category": "passenger",
          "valid_ids": ["k1", "k2"]
        },
        // ... 6 种详细车型
      ]
    },
    "vehicle_types_category": {
      "id": "vehicle_types_category",
      "label": "车型类别",
      "level": "category",
      "values": [
        {
          "value": "passenger",
          "label": "乘用车 (客车)",
          "description": "包含小型和大型乘用车",
          "includes": ["passenger_small", "passenger_large"],
          "example_ids": ["k1", "k2", "k3", "k4"]
        },
        {
          "value": "truck",
          "label": "货车",
          "description": "包含小型和大型货车",
          "includes": ["truck_small", "truck_large"],
          "example_ids": ["h1", "h2", "h3", "h4", "h5", "h6"]
        },
        {
          "value": "delivery",
          "label": "配送车 (特种车)",
          "includes": ["special_small", "special_large"],
          "example_ids": ["t1", "t2", "t3", "t4", "t5", "t6"]
        },
        {
          "value": "bus",
          "label": "公交车",
          "includes": []
        },
        {
          "value": "emergency",
          "label": "应急车",
          "includes": []
        },
        {
          "value": "authority",
          "label": "执法车",
          "includes": []
        }
      ]
    }
  }
}
```

### 层3: 策略模板参数配置

根据参数用途，选择合适的枚举级别：

```json
{
  "templates": [
    {
      "template_id": "dhs_strategy",
      "parameters_schema": [
        {
          "parameter_name": "allowed_vehicle_types",
          "parameter_type": "enum_array",
          "description": "允许使用硬路肩的车型",
          "enum_name": "vehicle_types_category",  // ← 使用高级类别
          "level": "category",
          "note": "选择'客车'将自动包含passenger_small和passenger_large"
        }
      ]
    }
  ]
}
```

---

## 🔄 前后端处理流程

### 前端: 参数选择

```javascript
// 用户在UI中看到的选项（高级类别）
enum_values = [
  { value: "passenger", label: "乘用车 (客车)", includes: ["passenger_small", "passenger_large"] },
  { value: "truck", label: "货车", includes: ["truck_small", "truck_large"] },
  // ...
]

// 用户选择
user_selected = ["passenger", "truck"];

// UI显示提示
display_hint("选择'乘用车'将包含: 小型客车(k1,k2) + 大型客车(k3,k4)");
```

### 后端: 参数处理

```python
def create_strategy_instance(strategy_name, template_id, configured_params):
    """创建策略实例时自动转换高级车型为详细车型"""

    for param_name, value in configured_params.items():
        # 检查是否是车型参数
        if param_name in ['allowed_vehicle_types', 'banned_vehicle_types']:
            # 转换高级车型 → 详细车型
            expanded_value = expand_vehicle_types(value)
            configured_params[param_name] = expanded_value

def expand_vehicle_types(vehicle_types_list):
    """
    展开高级车型为详细车型

    输入: ["passenger", "truck"]
    输出: ["passenger_small", "passenger_large", "truck_small", "truck_large"]
    """

    hierarchy = {
        "passenger": ["passenger_small", "passenger_large"],
        "truck": ["truck_small", "truck_large"],
        "delivery": ["special_small", "special_large"],
    }

    expanded = []
    for vtype in vehicle_types_list:
        if vtype in hierarchy:
            expanded.extend(hierarchy[vtype])
        else:
            # 如果是详细级车型，直接保留
            if is_detailed_vehicle_type(vtype):
                expanded.append(vtype)

    return list(set(expanded))  # 去重
```

---

## 📊 方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **纯详细级** | 直接，无转换 | 用户界面复杂 (6个选项) | 需要精细控制 |
| **纯高级类别** | UI简洁 | 无法选择单个详细车型 | 只支持按大类 |
| **两层分离** (推荐) | UI清晰，灵活，易扩展 | 实现复杂度中等 | 大多数场景 |
| **动态级别** | 最灵活 | 实现复杂，难以维护 | 高级需求 |

---

## 🚀 实施建议

### 步骤 1: 数据结构更新

**文件**: `control_data/templates/common/vehicle_types_enum.json`

```json
{
  "enums": {
    "vehicle_types_category": {
      "id": "vehicle_types_category",
      "label": "车型类别",
      "description": "高级车型分类 (自动展开为详细车型)",
      "values": [
        {
          "value": "passenger",
          "label": "乘用车 (客车)",
          "description": "包含: 小型客车(k1,k2) + 大型客车(k3,k4)",
          "includes": ["passenger_small", "passenger_large"],
          "color": "yellow"
        },
        {
          "value": "truck",
          "label": "货车",
          "description": "包含: 小型货车(h1,h2) + 大型货车(h3-h6)",
          "includes": ["truck_small", "truck_large"],
          "color": "blue"
        },
        // ... 完整定义
      ]
    }
  }
}
```

### 步骤 2: 后端转换逻辑

**文件**: `api/services/strategy_instance_service.py` 或新的 `shared/utilities/vehicle_type_utils.py`

```python
# shared/utilities/vehicle_type_utils.py

VEHICLE_TYPE_HIERARCHY = {
    "passenger": ["passenger_small", "passenger_large"],
    "truck": ["truck_small", "truck_large"],
    "delivery": ["special_small", "special_large"],
}

def expand_vehicle_types(vehicle_types_input: List[str]) -> List[str]:
    """
    展开高级车型为详细车型

    参数:
        vehicle_types_input: 用户选择的车型列表 (可能混合高级和详细)

    返回:
        expanded_types: 完整的详细车型列表
    """
    expanded = set()

    for vtype in vehicle_types_input:
        if vtype in VEHICLE_TYPE_HIERARCHY:
            # 高级车型 → 展开为详细车型
            expanded.update(VEHICLE_TYPE_HIERARCHY[vtype])
        else:
            # 假设是详细车型，直接添加
            expanded.add(vtype)

    return sorted(list(expanded))


def get_vehicle_type_display(vehicle_types: List[str]) -> str:
    """返回友好的显示文本"""

    categories = set()
    details = set()

    for vtype in vehicle_types:
        found = False
        for cat, details_list in VEHICLE_TYPE_HIERARCHY.items():
            if vtype in details_list:
                categories.add(cat)
                found = True
                break

        if not found:
            details.add(vtype)

    parts = []
    for cat in sorted(categories):
        parts.append(get_category_label(cat))

    return ", ".join(parts) if parts else "未选择"
```

### 步骤 3: 前端参数提示

**文件**: `frontend/control/templates.html` 或 `frontend/control/js/parameter_form.js`

```javascript
// 当显示高级车型枚举时，添加扩展说明

function renderVehicleTypeCheckboxes(param, vehicleTypes) {
    const checkboxesHtml = vehicleTypes.map(vt => {
        let tooltipText = vt.label;

        // 如果有 includes 字段，添加详细说明
        if (vt.includes && vt.includes.length > 0) {
            const detailLabels = vt.includes.map(v =>
                getDetailedVehicleTypeLabel(v)
            ).join(' + ');
            tooltipText += ` (包含: ${detailLabels})`;
        }

        return `<div class="checkbox-wrapper" title="${tooltipText}">
                  <input type="checkbox" name="${param.parameter_name}" value="${vt.value}">
                  <label>${vt.label}</label>
                  <span class="vehicle-type-hint">${detailLabels}</span>
                </div>`;
    }).join('');

    return checkboxesHtml;
}
```

---

## 🔄 转换示例

### 例子 1: DHS 策略 - 允许的车型

```
用户选择:
  ☑ 乘用车 (客车)
  ☑ 货车
  ☐ 配送车

后端处理:
  input: ["passenger", "truck"]
  expand_vehicle_types() → ["passenger_small", "passenger_large", "truck_small", "truck_large"]

存储到数据库:
  allowed_vehicle_types: ["passenger_small", "passenger_large", "truck_small", "truck_large"]

SUMO验证:
  ✅ 所有车型都在 vehicle_types.json 中定义
```

### 例子 2: TEC 策略 - 禁止的车型

```
用户选择:
  ☑ 公交车 (bus)
  ☑ 应急车 (emergency)

后端处理:
  input: ["bus", "emergency"]
  expand_vehicle_types() → ["bus", "emergency"] (无详细级)

存储到数据库:
  banned_vehicle_types: ["bus", "emergency"]

注意: 这些车型可能在 vehicle_types.json 中无定义
      但在 vehicle_types_enum.json 中定义
```

---

## 📋 实施检查清单

### 数据层
- [ ] vehicle_types_enum.json 包含完整的类别定义和 includes 映射
- [ ] vehicle_types.json 的每个类型包含 category 字段指向高级类别
- [ ] 验证所有 includes 中的车型都存在

### 后端层
- [ ] 实现 expand_vehicle_types() 函数
- [ ] 参数验证时调用此函数
- [ ] 存储时保存展开后的车型列表
- [ ] 单元测试覆盖各种组合
- [ ] API 返回时明确说明转换逻辑

### 前端层
- [ ] 参数定义中明确 enum_name 指向高级类别
- [ ] 显示 includes 列表给用户
- [ ] 提示文本说明"选择X将包含Y"
- [ ] E2E 测试验证选择和提交

### 文档层
- [ ] 更新 API 文档说明转换逻辑
- [ ] 添加参数配置指南
- [ ] 记录车型层级关系

---

## 🎯 关键设计决策

### Q1: 应该在前端还是后端转换?

**A**: 在后端转换，原因：
- 验证数据的完整性在后端
- 前端无需知道复杂的映射关系
- 单一真实源原则

### Q2: 用户选择的记录应该保存高级还是详细车型?

**A**: 都保存（推荐）：
```json
{
  "user_selection": ["passenger", "truck"],  // 用户选择
  "expanded_types": ["passenger_small", "passenger_large", "truck_small", "truck_large"]  // 实际值
}
```

### Q3: 如果新增详细车型，是否需要修改高级定义?

**A**: 是的。需要：
1. 在 vehicle_types.json 中定义新的详细车型
2. 在 vehicle_types_enum.json 的 includes 中添加
3. 更新转换函数的映射

---

## 总结

✅ **两层关系设计的核心**:
- 高级层: 用户友好的分类 (客车、货车、特种车)
- 详细层: SUMO仿真中实际使用的车型 (passenger_small, passenger_large, ...)
- 自动转换: 后端负责将用户的高级选择展开为详细车型

✅ **数据一致性保证**:
- vehicle_types.json: SUMO唯一真实源
- vehicle_types_enum.json: 转换映射和类别定义
- 后端: 自动展开和验证

✅ **用户体验**:
- 前端显示清晰易懂的分类
- 自动包含提示 ("选择客车将包含...")
- 后端自动处理转换细节

