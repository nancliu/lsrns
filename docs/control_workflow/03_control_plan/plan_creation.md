# 管控方案创建流程

本文档说明如何创建管控方案（Control Plan）。

---

## 一、方案创建概述

### 1.1 创建前提

创建方案前需要：
- ✅ 已创建所需的策略实例
- ✅ 了解策略组合的协同机制
- ✅ 明确方案适用的交通场景

### 1.2 创建方式

1. **手动创建**: 通过前端UI或API手动创建
2. **自动生成**: 基于拥堵模式自动生成（见方案自动生成算法）

---

## 二、手动创建流程

### 2.1 步骤1: 准备策略

#### 查看可用策略

1. 进入策略管理页面
2. 查看策略实例列表
3. 记录需要使用的策略ID

**示例策略列表**:
- `strategy_real_vss_g4202_001` - G4202早高峰VSS
- `strategy_real_dhs_g4202_001` - G4202早高峰DHS
- `strategy_real_tec_g5_001` - G5入口TEC

---

### 2.2 步骤2: 创建方案

#### 填写方案信息

**方案名称**:
- 格式: `plan_{策略类型}_{场景}_{描述}`
- 示例: `plan_vss_morning_peak_simple`

**方案描述**:
- 说明方案用途和预期效果
- 示例: "G4202绕西双流段早高峰可变限速优化方案"

**选择策略**:
- 从策略列表中勾选需要的策略
- 可设置优先级和启用状态

**标签**:
- 添加分类标签
- 建议: 早高峰、VSS、G4202、单策略

**目标场景**:
- 说明方案适用的交通场景
- 示例: "工作日早高峰(7:00-9:00)"

---

### 2.3 步骤3: 配置协同机制（多策略方案）

#### 时序协调

定义策略激活顺序：
- TEC → VSS → DHS
- TEC提前1小时激活
- DHS延后1小时激活

#### 空间协调

定义策略空间分配：
- 上游: TEC入口流量控制
- 中游: VSS可变限速
- 下游: DHS应急车道开放

#### 参数耦合

定义策略参数耦合关系：
- TEC-VSS: TEC限流值应使主线流量保持在VSS限速下的安全容量范围内
- VSS-DHS: DHS开放后，VSS限速提高10-15 km/h

---

### 2.4 步骤4: 保存方案

#### 方案验证

保存前验证：
- ✅ 方案名称唯一
- ✅ 策略ID存在
- ✅ 协同机制合理

#### 保存到文件系统

```python
def save_plan(plan_data: dict):
    """保存方案"""
    plan_id = plan_data["plan_id"]
    
    # 1. 创建方案目录
    plan_dir = f"control_data/plans/{plan_id}"
    os.makedirs(plan_dir, exist_ok=True)
    
    # 2. 保存方案元数据
    metadata_path = f"{plan_dir}/plan_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(plan_data, f, ensure_ascii=False, indent=2)
    
    # 3. 保存策略引用
    strategy_refs_path = f"{plan_dir}/strategy_refs.json"
    with open(strategy_refs_path, 'w', encoding='utf-8') as f:
        json.dump(plan_data["strategy_references"], f, ensure_ascii=False, indent=2)
    
    # 4. 更新方案索引
    update_plans_index(plan_data)
```

---

## 三、自动生成流程

### 3.1 基于拥堵模式生成

**输入**: 拥堵模式类型（如"morning_peak_severe"）

**流程**:
```python
def generate_plan_from_pattern(pattern_type: str) -> dict:
    """基于拥堵模式生成方案"""
    
    # 1. 识别策略类型
    strategy_type = select_strategy_type_for_pattern(pattern_type)
    
    # 2. 选择策略实例
    reference_strategy = find_strategy_by_type(strategies_pool, strategy_type)
    
    # 3. 生成方案元数据
    plan_metadata = {
        "plan_id": f"plan_{strategy_type.lower()}_{pattern_type}",
        "strategy_ids": [reference_strategy["strategy_id"]],
        "applicable_conditions": get_pattern_conditions(pattern_type),
        "expected_effects": calculate_expected_effects(strategy_type)
    }
    
    return plan_metadata
```

---

### 3.2 基于数据分析生成

**输入**: Case数据分析结果

**流程**:
```python
def generate_plan_from_analysis(analysis_result: dict) -> dict:
    """基于数据分析生成方案"""
    
    # 1. 识别拥堵点
    congestion_points = analysis_result["congestion_points"]
    
    # 2. 选择策略
    recommended_strategies = select_strategies(congestion_points)
    
    # 3. 生成方案
    plan = create_plan_from_strategies(recommended_strategies)
    
    return plan
```

---

## 四、方案创建示例

### 4.1 单策略方案示例

**输入**:
- 策略: `strategy_real_vss_g4202_001`
- 场景: 早高峰拥堵

**输出**:
```json
{
  "plan_id": "plan_vss_morning_peak_simple",
  "plan_name": "早高峰单策略VSS限速方案",
  "description": "针对早高峰时段（6:00-10:00）出现的严重拥堵（平均速度<30 km/h），采用VSS可变限速单策略进行管控",
  "strategy_references": [
    {
      "strategy_id": "strategy_real_vss_g4202_001",
      "is_enabled": true,
      "priority": 1
    }
  ],
  "tags": ["P0", "单策略", "VSS", "早高峰"],
  "target_scenario": "工作日早高峰(6:00-10:00)，城市快速路或高速公路出现严重拥堵",
  "expected_effects": {
    "speed_improvement": "预期速度提升100-200%"
  }
}
```

---

### 4.2 复合策略方案示例

**输入**:
- 策略: `strategy_real_vss_g4202_001`, `strategy_real_dhs_g4202_001`
- 场景: 早高峰严重拥堵

**输出**:
```json
{
  "plan_id": "plan_vss_dhs_morning_composite",
  "plan_name": "早高峰VSS+DHS复合方案",
  "description": "针对早高峰严重拥堵，采用VSS+DHS双策略协同管控",
  "strategy_references": [
    {
      "strategy_id": "strategy_real_vss_g4202_001",
      "is_enabled": true,
      "priority": 1
    },
    {
      "strategy_id": "strategy_real_dhs_g4202_001",
      "is_enabled": true,
      "priority": 2
    }
  ],
  "strategy_coordination": {
    "time_coordination": {
      "activation_order": ["VSS", "DHS"],
      "time_offsets": {"VSS_to_DHS": 1}
    },
    "spatial_coordination": {
      "midstream": "VSS",
      "downstream": "DHS"
    },
    "parameter_coupling": {
      "vss_dhs_coupling": "DHS开放后，VSS限速提高10 km/h"
    }
  },
  "tags": ["P0", "复合策略", "VSS+DHS", "早高峰"],
  "expected_effects": {
    "speed_improvement": "预期速度提升150-250%",
    "capacity_increase": "主线通行能力提升30-35%"
  }
}
```

---

## 五、方案验证

### 5.1 创建时验证

```python
def validate_plan(plan_data: dict) -> dict:
    """验证方案"""
    errors = []
    
    # 1. 验证必填字段
    required_fields = ["plan_id", "plan_name", "strategy_references"]
    for field in required_fields:
        if field not in plan_data:
            errors.append(f"缺少必填字段: {field}")
    
    # 2. 验证策略引用
    for ref in plan_data["strategy_references"]:
        if not strategy_exists(ref["strategy_id"]):
            errors.append(f"策略不存在: {ref['strategy_id']}")
    
    # 3. 验证协同机制（多策略）
    if len(plan_data["strategy_references"]) > 1:
        if "strategy_coordination" not in plan_data:
            errors.append("多策略方案必须配置协同机制")
    
    return {"valid": len(errors) == 0, "errors": errors}
```

---

## 六、相关文档

- [方案架构设计](plan_architecture.md)
- [多策略协同](plan_coordination.md)
- [方案管理用户指南](../../user_guide/plan_management.md)

---

**文档版本**: v1.0
**创建日期**: 2025-01-XX









