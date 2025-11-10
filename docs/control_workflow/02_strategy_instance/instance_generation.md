# 策略实例生成流程

本文档说明如何从模板生成策略实例。

---

## 一、实例生成概述

### 1.1 什么是策略实例

策略实例（Strategy Instance）是从模板创建的**具体策略配置**，包含：
- 模板ID（引用模板）
- 具体参数值（用户配置）
- 目标路段（edge_id列表）
- 策略元数据（名称、描述、标签等）

### 1.2 生成流程

```
模板选择 → 路段选择 → 参数配置 → 实例生成 → 验证保存
```

---

## 二、详细生成流程

### 2.1 步骤1: 选择模板

#### 模板选择

用户从可用模板中选择：
- 前端显示所有模板卡片
- 用户点击选择模板
- 系统加载模板配置

#### 模板加载

```python
def load_template(template_id: str) -> dict:
    """加载策略模板"""
    template_path = f"templates/control_strategies/{template_id}.json"
    with open(template_path, 'r', encoding='utf-8') as f:
        template = json.load(f)
    return template
```

---

### 2.2 步骤2: 选择路段

#### VSS/DHS路段选择

**查询条件**:
- 路线代码（route_code）
- 路段代码（section_code）
- 桩号范围（start_stake, end_stake）
- 最小车道数（DHS需要≥4）

**数据库查询**:
```sql
SELECT
    edge_id,
    start_stake,
    end_stake,
    length,
    num_lanes,
    route_code,
    route_direction
FROM dim.sim_network_edges
WHERE route_code = 'G4202'
  AND section_code = 'G4202001'
  AND start_stake >= 10.0
  AND end_stake <= 15.0
  AND num_lanes >= 4  -- DHS要求
ORDER BY start_stake;
```

**用户选择**:
- 显示查询结果列表
- 用户勾选目标路段
- 验证路段连续性（可选）

---

### 2.3 步骤3: 配置参数

#### 参数配置界面

根据模板的`parameters_schema`动态生成配置界面：

**VSS参数配置**:
- 速度时刻表配置
- 时间轴可视化
- 限速值输入

**DHS参数配置**:
- 时间段配置
- 开放/关闭状态
- 车型选择

**TEC参数配置**:
- 流量控制时段
- 流量上限设置
- 目标速度设置

#### 参数验证

实时验证用户输入：
- 时间范围: 0-24小时
- 速度范围: 30-120 km/h
- 流量范围: 50-1000 veh/hr
- DHS必须覆盖24小时

---

### 2.4 步骤4: 实例生成

#### 生成策略实例

```python
def create_strategy_instance(
    template_id: str,
    strategy_name: str,
    affected_edges: List[str],
    parameters: Dict[str, Any]
) -> dict:
    """创建策略实例"""
    
    # 1. 加载模板
    template = load_template(template_id)
    
    # 2. 生成策略ID
    strategy_id = generate_strategy_id(template["strategy_type"])
    
    # 3. 构建实例
    instance = {
        "strategy_id": strategy_id,
        "strategy_name": strategy_name,
        "template_id": template_id,
        "strategy_type": template["strategy_type"],
        "affected_edges": affected_edges,
        "configured_params": parameters,
        "created_at": datetime.now().isoformat(),
        "status": "active"
    }
    
    # 4. 验证实例
    validation_result = validate_strategy_instance(instance, template)
    if not validation_result["valid"]:
        raise ValueError(validation_result["errors"])
    
    return instance
```

#### 策略ID生成

```python
def generate_strategy_id(strategy_type: str, location: str = None) -> str:
    """自动生成策略ID"""
    existing_count = count_strategies_by_type(strategy_type)
    seq = existing_count + 1
    
    type_prefix = strategy_type.lower()
    if location:
        return f"{type_prefix}_{location}_{seq:03d}"
    else:
        return f"{type_prefix}_{seq:03d}"
```

---

### 2.5 步骤5: 验证保存

#### 实例验证

验证策略实例的完整性和合法性：

```python
def validate_strategy_instance(instance: dict, template: dict) -> dict:
    """验证策略实例"""
    errors = []
    
    # 1. 验证必填字段
    required_fields = ["strategy_id", "strategy_name", "template_id", "affected_edges"]
    for field in required_fields:
        if field not in instance:
            errors.append(f"缺少必填字段: {field}")
    
    # 2. 验证参数
    for param_schema in template["parameters_schema"]:
        param_name = param_schema["parameter_name"]
        if param_schema.get("required", False):
            if param_name not in instance["configured_params"]:
                errors.append(f"缺少必需参数: {param_name}")
    
    # 3. 验证参数值
    validation_rules = template.get("validation_rules", {})
    # 验证速度范围、时间范围等
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
```

#### 保存实例

```python
def save_strategy_instance(instance: dict):
    """保存策略实例"""
    # 1. 保存JSON文件
    instance_path = f"control_data/strategies/{instance['strategy_id']}.json"
    with open(instance_path, 'w', encoding='utf-8') as f:
        json.dump(instance, f, ensure_ascii=False, indent=2)
    
    # 2. 更新索引
    update_strategies_index(instance)
```

---

## 三、实例生成示例

### 3.1 VSS实例生成

**输入**:
- 模板: `vss_moderate`
- 路段: `["-9292", "-8014", "-10702"]`
- 参数: `{"speed_steps": [{"time_hours": 7, "speed_kmh": 80}, {"time_hours": 9, "speed_kmh": 100}]}`

**输出**:
```json
{
  "strategy_id": "strategy_real_vss_g4202_001",
  "strategy_name": "G4202北段K12-K17早高峰可变限速",
  "template_id": "vss_moderate",
  "strategy_type": "VSS",
  "affected_edges": ["-9292", "-8014", "-10702"],
  "configured_params": {
    "speed_steps": [
      {"time_hours": 7, "speed_kmh": 80},
      {"time_hours": 9, "speed_kmh": 100}
    ]
  },
  "created_at": "2025-10-26T00:00:00Z",
  "status": "active"
}
```

---

### 3.2 DHS实例生成

**输入**:
- 模板: `dhs_peak_hours`
- 路段: `["-13154", "-5004", "-9292"]`
- 参数: `{"intervals": [{"begin_hours": 7, "end_hours": 9, "status": "OPEN"}, ...]}`

**输出**:
```json
{
  "strategy_id": "strategy_real_dhs_g4202_001",
  "strategy_name": "G4202南段K20-K28早高峰应急车道开放",
  "template_id": "dhs_peak_hours",
  "strategy_type": "DHS",
  "affected_edges": ["-13154", "-5004", "-9292"],
  "configured_params": {
    "intervals": [
      {"begin_hours": 0, "end_hours": 7, "status": "CLOSED"},
      {"begin_hours": 7, "end_hours": 9, "status": "OPEN"},
      {"begin_hours": 9, "end_hours": 24, "status": "CLOSED"}
    ],
    "allowed_vehicle_types": ["passenger", "truck"]
  },
  "created_at": "2025-10-26T00:00:00Z",
  "status": "active"
}
```

---

## 四、批量生成

### 4.1 参数扫描生成

**场景**: 测试不同限速值的效果

```python
def batch_generate_vss_strategies(
    base_template: str,
    edges: List[str],
    speed_range: List[int]
) -> List[dict]:
    """批量生成VSS策略"""
    strategies = []
    
    for speed_kmh in speed_range:
        strategy = create_strategy_instance(
            template_id=base_template,
            strategy_name=f"限速{speed_kmh}km/h策略",
            affected_edges=edges,
            parameters={
                "speed_steps": [
                    {"time_hours": 7, "speed_kmh": speed_kmh},
                    {"time_hours": 9, "speed_kmh": 100}
                ]
            }
        )
        strategies.append(strategy)
    
    return strategies
```

---

## 五、相关文档

- [参数配置说明](parameter_configuration.md)
- [实例验证机制](instance_validation.md)
- [策略创建用户指南](../../user_guides/strategy_creation_guide.md)

---

**文档版本**: v1.0
**创建日期**: 2025-01-XX



