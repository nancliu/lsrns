# 管控方案架构设计

本文档说明管控方案（Control Plan）的架构设计原理。

---

## 一、方案架构概述

### 1.1 Plan架构定位

**核心理念**: Plan（控制方案）是**通用的、可复用的交通管控模板**，而不是针对单个Case的一次性配置。

### 1.2 Plan vs Case 关系

```
┌─────────────────────────────────────────────────────────────┐
│  Plan（控制方案）- 通用模板                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ • 描述拥堵场景模式（如"早高峰拥堵"）                    │  │
│  │ • 定义策略组合（如VSS+DHS）                            │  │
│  │ • 配置协同机制（时序、空间、参数耦合）                  │  │
│  │ • 预期效果类型（速度提升100-200%）                    │  │
│  │ • 适用条件（速度<30 km/h，持续2h+）                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│                     可应用于 ↓                                │
│                                                               │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │ Case A      │   │ Case B      │   │ Case C      │       │
│  │ (10月数据)  │   │ (11月数据)  │   │ (12月数据)  │       │
│  └─────────────┘   └─────────────┘   └─────────────┘       │
│                                                               │
│  同一个Plan在不同Case上验证，accumulate validation_records   │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、Plan核心属性

### 2.1 标识信息

| 属性 | 描述 | 是否绑定Case |
|------|------|-------------|
| `plan_id` | 语义化ID，如`plan_vss_morning_peak_simple` | ❌ 不绑定 |
| `plan_name` | 描述性名称 | ❌ 不绑定 |

### 2.2 策略配置

| 属性 | 描述 | 是否绑定Case |
|------|------|-------------|
| `strategy_ids` | 引用的策略ID列表 | ❌ 不绑定 |
| `strategy_coordination` | 策略协同机制（时序、空间、参数） | ❌ 不绑定 |

### 2.3 适用条件

| 属性 | 描述 | 是否绑定Case |
|------|------|-------------|
| `applicable_conditions` | 拥堵模式、时间窗口、严重度阈值 | ❌ 不绑定（通用） |
| `target_scenario` | 目标场景描述（通用表述） | ❌ 不绑定 |

### 2.4 预期效果

| 属性 | 描述 | 是否绑定Case |
|------|------|-------------|
| `expected_effects` | 改善类型和范围（如"提升100-200%"） | ❌ 不绑定（范围） |

### 2.5 验证记录

| 属性 | 描述 | 是否绑定Case |
|------|------|-------------|
| `validation_records` | 在哪些Case上验证过，效果如何 | ✅ 记录Case关联 |

---

## 三、Plan设计原则

### 3.1 通用性优先

Plan描述"拥堵场景模式"而非"具体路段拥堵事件"：

**✅ 正确**:
```json
{
  "plan_id": "plan_vss_morning_peak_simple",
  "target_scenario": "工作日早高峰(6:00-10:00)，城市快速路或高速公路出现严重拥堵（平均速度<30 km/h，持续2小时以上）"
}
```

**❌ 错误**:
```json
{
  "plan_id": "plan_vss_g4202_k52_4",
  "target_scenario": "G4202 K52.4路段早高峰拥堵"  // 绑定具体路段
}
```

### 3.2 可复用性

同一Plan可应用到多个满足条件的Case：

```python
# Plan可应用到多个Case
apply_plan_to_case("plan_vss_morning_peak_simple", "case_202510")
apply_plan_to_case("plan_vss_morning_peak_simple", "case_202511")
apply_plan_to_case("plan_vss_morning_peak_simple", "case_202512")
```

### 3.3 参数化

具体参数（如限速值）可根据Case数据微调：

```python
# Plan定义通用参数范围
plan = {
    "parameter_ranges": {
        "VSS": {
            "speed_range": (50, 100)  # 通用范围
        }
    }
}

# 应用时根据Case数据微调
case_data = load_case_data("case_202510")
adjusted_speed = optimize_speed_for_case(plan, case_data)  # 具体值
```

### 3.4 验证积累

每次在新Case上验证后，更新validation_records：

```json
{
  "validation_records": [
    {
      "case_id": "case_202510",
      "road_segment": "G4202 K52.4",
      "baseline_speed": 15.14,
      "improvement_percent": 230,
      "validation_status": "已验证"
    },
    {
      "case_id": "case_202511",
      "road_segment": "G5 K1820.15",
      "baseline_speed": 17.97,
      "improvement_percent": 180,
      "validation_status": "已验证"
    }
  ]
}
```

---

## 四、方案分层架构

### 4.1 简单方案（单策略）

**适用场景**:
- 拥堵程度: 低速 (<30 km/h)，短时拥堵 (2-4小时)
- 优先级: P0 (紧急部署)
- 目标: 快速验证策略有效性

**结构**:
```json
{
  "plan_id": "plan_vss_morning_peak_simple",
  "strategy_ids": ["strategy_real_vss_g4202_001"],
  "strategy_coordination": null  // 单策略无需协同
}
```

---

### 4.2 复合方案（双策略）

**适用场景**:
- 拥堵程度: 低速 (<20 km/h) + 高流量 (>300 veh/hr)
- 持续时长: 3-6小时
- 目标: 速度控制 + 通行能力提升

**结构**:
```json
{
  "plan_id": "plan_vss_dhs_morning_composite",
  "strategy_ids": [
    "strategy_real_vss_g4202_001",
    "strategy_real_dhs_g4202_001"
  ],
  "strategy_coordination": {
    "time_coordination": {
      "activation_order": ["VSS", "DHS"],
      "time_offsets": {"VSS_to_DHS": 1}
    },
    "spatial_coordination": {
      "upstream": null,
      "midstream": "VSS",
      "downstream": "DHS"
    },
    "parameter_coupling": {
      "vss_dhs_coupling": "DHS开放后，VSS限速提高10 km/h"
    }
  }
}
```

---

### 4.3 复杂方案（多策略）

**适用场景**:
- 拥堵程度: 全天持续拥堵
- 持续时长: >6小时
- 目标: 全方位管控

**结构**:
```json
{
  "plan_id": "plan_vss_dhs_tec_allday_complex",
  "strategy_ids": [
    "strategy_real_vss_g4202_001",
    "strategy_real_dhs_g4202_001",
    "strategy_real_tec_g5_001"
  ],
  "strategy_coordination": {
    "time_coordination": {
      "activation_order": ["TEC", "VSS", "DHS"],
      "time_offsets": {
        "TEC_to_VSS": -1,
        "VSS_to_DHS": 1
      }
    },
    "spatial_coordination": {
      "upstream": "TEC",
      "midstream": "VSS",
      "downstream": "DHS"
    },
    "parameter_coupling": {
      "tec_vss_coupling": "TEC限流值应使主线流量保持在VSS限速下的安全容量范围内",
      "vss_dhs_coupling": "DHS开放后，VSS限速提高10-15 km/h"
    }
  }
}
```

---

## 五、策略引用系统

### 5.1 引用机制

Plan通过策略ID引用策略实例：

```json
{
  "plan_id": "plan_vss_morning_peak_simple",
  "strategy_references": [
    {
      "strategy_id": "strategy_real_vss_g4202_001",
      "is_enabled": true,
      "priority": 1
    }
  ]
}
```

### 5.2 引用优势

1. **策略复用**: 一个策略可在多个Plan中使用
2. **自动更新**: 修改策略配置自动影响所有引用它的Plan
3. **版本管理**: 方便策略版本管理和对比

### 5.3 引用验证

创建Plan时验证：
- ✅ 策略ID存在
- ✅ 策略类型匹配
- ✅ 策略状态为active

---

## 六、方案元数据

### 6.1 标签系统

```json
{
  "tags": ["早高峰", "VSS", "G4202", "单策略"]
}
```

**标签分类**:
- 时段标签: 早高峰、晚高峰、全天
- 策略类型: VSS、TEC、DHS
- 路段标签: G4202、G5
- 复杂度: 单策略、多策略、复合方案

### 6.2 目标场景

```json
{
  "target_scenario": "工作日早高峰(6:00-10:00)，城市快速路或高速公路出现严重拥堵（平均速度<30 km/h，持续2小时以上）"
}
```

### 6.3 预期效果

```json
{
  "expected_effects": {
    "speed_improvement": "预期速度提升100-200%",
    "implementation_difficulty": "简单（单策略，快速部署）"
  }
}
```

---

## 七、相关文档

- [方案创建流程](plan_creation.md)
- [多策略协同](plan_coordination.md)
- [方案管理用户指南](../../user_guide/plan_management.md)

---

**文档版本**: v1.0
**创建日期**: 2025-01-XX





