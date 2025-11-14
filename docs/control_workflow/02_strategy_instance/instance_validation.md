# 策略实例验证机制

本文档说明策略实例的验证机制和验证规则。

---

## 一、验证概述

### 1.1 验证目的

确保策略实例：
- ✅ 参数完整（所有必填参数已填写）
- ✅ 参数合法（参数值在允许范围内）
- ✅ 逻辑正确（参数间无冲突）
- ✅ 格式正确（符合SUMO XML生成要求）

### 1.2 验证时机

1. **实时验证**: 用户输入时前端验证
2. **保存前验证**: 保存实例前完整验证
3. **加载时验证**: 加载实例时验证完整性

---

## 二、验证规则

### 2.1 基础字段验证

#### 必填字段

```python
REQUIRED_FIELDS = [
    "strategy_id",
    "strategy_name",
    "template_id",
    "strategy_type",
    "affected_edges",
    "configured_params"
]
```

#### 字段格式验证

- `strategy_id`: 格式 `{type}_{location}_{seq}` 或 `{type}_{seq}`
- `strategy_name`: 非空字符串，最大200字符
- `template_id`: 必须存在于模板索引中
- `strategy_type`: 枚举值 `["VSS", "DHS", "TEC"]`

---

### 2.2 VSS参数验证

#### speed_steps验证

```python
def validate_vss_speed_steps(speed_steps: List[dict]) -> dict:
    """验证VSS速度时刻表"""
    errors = []
    
    # 1. 至少2个时刻点
    if len(speed_steps) < 2:
        errors.append("speed_steps至少需要2个时刻点")
    
    # 2. 验证每个时刻点
    for i, step in enumerate(speed_steps):
        # 2.1 时间范围
        if not (0 <= step["time_hours"] <= 24):
            errors.append(f"时刻点{i+1}时间超出范围(0-24小时)")
        
        # 2.2 速度范围
        if not (30 <= step["speed_kmh"] <= 120):
            errors.append(f"时刻点{i+1}速度超出范围(30-120 km/h)")
    
    # 3. 时刻点排序
    times = [step["time_hours"] for step in speed_steps]
    if times != sorted(times):
        errors.append("时刻点必须按时间顺序排列")
    
    return {"valid": len(errors) == 0, "errors": errors}
```

---

### 2.3 DHS参数验证

#### intervals验证

```python
def validate_dhs_intervals(intervals: List[dict]) -> dict:
    """验证DHS时间段配置"""
    errors = []
    
    # 1. 必须覆盖24小时
    total_coverage = 0
    for interval in intervals:
        begin = interval["begin_hours"]
        end = interval["end_hours"]
        
        if end < begin:  # 跨日
            coverage = (24 - begin) + end
        else:
            coverage = end - begin
        
        total_coverage += coverage
    
    if total_coverage != 24:
        errors.append(f"DHS时间段必须覆盖24小时，当前覆盖{total_coverage}小时")
    
    # 2. 检查时间间隙
    sorted_intervals = sorted(intervals, key=lambda x: x["begin_hours"])
    for i in range(len(sorted_intervals) - 1):
        current_end = sorted_intervals[i]["end_hours"]
        next_begin = sorted_intervals[i + 1]["begin_hours"]
        
        if current_end != next_begin:
            errors.append(f"时间段{i+1}和{i+2}之间存在间隙")
    
    # 3. 状态验证
    for interval in intervals:
        if interval["status"] not in ["OPEN", "CLOSED"]:
            errors.append(f"时间段状态必须是OPEN或CLOSED")
    
    return {"valid": len(errors) == 0, "errors": errors}
```

---

### 2.4 TEC参数验证

#### flow_intervals验证

```python
def validate_tec_flow_intervals(flow_intervals: List[dict]) -> dict:
    """验证TEC流量控制时段"""
    errors = []
    
    for i, interval in enumerate(flow_intervals):
        # 1. 时间范围
        if not (0 <= interval["begin_hours"] < interval["end_hours"] <= 24):
            errors.append(f"时段{i+1}时间范围无效")
        
        # 2. 流量范围
        if not (50 <= interval["vehsPerHour"] <= 1000):
            errors.append(f"时段{i+1}流量超出范围(50-1000 veh/hr)")
        
        # 3. 速度范围
        if not (30 <= interval["target_speed"] <= 120):
            errors.append(f"时段{i+1}速度超出范围(30-120 km/h)")
    
    return {"valid": len(errors) == 0, "errors": errors}
```

---

## 三、路段验证

### 3.1 路段存在性验证

```python
def validate_edges_exist(edge_ids: List[str]) -> dict:
    """验证路段是否存在"""
    from shared.data_access.connection import get_pooled_connection
    
    with get_pooled_connection() as conn:
        cursor = conn.cursor()
        placeholders = ','.join(['%s'] * len(edge_ids))
        query = f"""
            SELECT edge_id FROM dim.sim_network_edges
            WHERE edge_id IN ({placeholders})
        """
        cursor.execute(query, edge_ids)
        existing_edges = [row[0] for row in cursor.fetchall()]
    
    missing_edges = set(edge_ids) - set(existing_edges)
    
    if missing_edges:
        return {
            "valid": False,
            "errors": [f"路段不存在: {', '.join(missing_edges)}"]
        }
    
    return {"valid": True, "errors": []}
```

### 3.2 路段连续性验证（可选）

```python
def validate_edges_continuity(edge_ids: List[str]) -> dict:
    """验证路段连续性"""
    from shared.data_access.connection import get_pooled_connection
    
    with get_pooled_connection() as conn:
        cursor = conn.cursor()
        # 查询路段连接关系
        # 验证前一段的to_junction = 后一段的from_junction
    
    # 返回验证结果
    pass
```

---

## 四、模板一致性验证

### 4.1 参数Schema一致性

```python
def validate_against_template(instance: dict, template: dict) -> dict:
    """验证实例与模板的一致性"""
    errors = []
    
    # 1. 检查必填参数
    for param_schema in template["parameters_schema"]:
        param_name = param_schema["parameter_name"]
        if param_schema.get("required", False):
            if param_name not in instance["configured_params"]:
                errors.append(f"缺少必需参数: {param_name}")
    
    # 2. 检查参数类型
    for param_name, param_value in instance["configured_params"].items():
        param_schema = find_param_schema(template, param_name)
        if param_schema:
            if not validate_parameter_type(param_value, param_schema["parameter_type"]):
                errors.append(f"参数{param_name}类型不匹配")
    
    return {"valid": len(errors) == 0, "errors": errors}
```

---

## 五、SUMO XML生成验证

### 5.1 XML生成前验证

```python
def validate_for_xml_generation(instance: dict) -> dict:
    """验证实例是否可以生成SUMO XML"""
    errors = []
    
    # 1. 检查是否有affected_edges
    if not instance.get("affected_edges"):
        errors.append("缺少affected_edges，无法生成XML")
    
    # 2. 检查参数完整性
    template = load_template(instance["template_id"])
    for param_schema in template["parameters_schema"]:
        if param_schema.get("required", False):
            param_name = param_schema["parameter_name"]
            if param_name not in instance["configured_params"]:
                errors.append(f"缺少必需参数{param_name}，无法生成XML")
    
    return {"valid": len(errors) == 0, "errors": errors}
```

---

## 六、验证结果处理

### 6.1 验证结果格式

```python
{
    "valid": True/False,
    "errors": [
        "错误信息1",
        "错误信息2"
    ],
    "warnings": [
        "警告信息1"
    ]
}
```

### 6.2 错误处理

- **实时验证**: 前端显示错误提示，阻止继续操作
- **保存前验证**: 显示错误列表，阻止保存
- **加载时验证**: 记录错误日志，标记实例为无效

---

## 七、相关文档

- [实例生成流程](instance_generation.md)
- [参数配置说明](parameter_configuration.md)
- [策略创建用户指南](../../user_guides/strategy_creation_guide.md)

---

**文档版本**: v1.0
**创建日期**: 2025-01-XX







