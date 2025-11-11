# 多策略协同机制

本文档详细说明多策略方案的协同机制。

---

## 一、协同机制概述

### 1.1 为什么需要协同

多策略组合时，需要确保：
- ✅ 策略激活时间协调一致
- ✅ 策略作用空间合理分配
- ✅ 策略参数相互协调，避免冲突

### 1.2 协同类型

1. **时序协调**: 策略激活时间序列协调
2. **空间协调**: 策略作用空间分配
3. **参数耦合**: 策略参数相互调整

---

## 二、时序协调

### 2.1 协调原则

**激活顺序**: TEC → VSS → DHS

**时间偏移**:
- TEC提前1小时激活（源头控制）
- VSS正常激活（主线控制）
- DHS延后1小时激活（扩容措施）

### 2.2 协调算法

```python
def coordinate_time_sequences(strategies: List[dict]) -> List[dict]:
    """多策略时序协调算法"""
    
    # 1. 提取所有策略的关键时间点
    all_time_points = set()
    for strategy in strategies:
        if strategy['type'] == 'VSS':
            for step in strategy['parameters']['speed_steps']:
                all_time_points.add(step['time_hours'])
        elif strategy['type'] == 'DHS':
            for interval in strategy['parameters']['intervals']:
                all_time_points.add(interval['begin_hours'])
                all_time_points.add(interval['end_hours'])
        elif strategy['type'] == 'TEC':
            for flow in strategy['parameters']['flow_intervals']:
                all_time_points.add(flow['begin_hours'])
                all_time_points.add(flow['end_hours'])
    
    sorted_times = sorted(all_time_points)
    
    # 2. 定义协调规则
    coordination_rules = {
        'activation_order': ['TEC', 'VSS', 'DHS'],
        'time_offsets': {
            'TEC_to_VSS': -1,  # TEC提前1小时
            'VSS_to_DHS': 1     # DHS延后1小时
        }
    }
    
    # 3. 调整各策略的时间参数
    coordinated_strategies = []
    for strategy in strategies:
        if strategy['type'] == 'TEC':
            strategy['activation_time'] = min(sorted_times) + coordination_rules['time_offsets']['TEC_to_VSS']
        elif strategy['type'] == 'VSS':
            strategy['activation_time'] = min(sorted_times)
        elif strategy['type'] == 'DHS':
            strategy['activation_time'] = min(sorted_times) + coordination_rules['time_offsets']['VSS_to_DHS']
        
        coordinated_strategies.append(strategy)
    
    return coordinated_strategies
```

### 2.3 协调示例

**原始策略时间**:
- VSS: 7:00激活
- DHS: 7:00激活
- TEC: 7:00激活

**协调后时间**:
- TEC: 6:00激活（提前1小时）
- VSS: 7:00激活（正常）
- DHS: 8:00激活（延后1小时）

---

## 三、空间协调

### 3.1 协调原则

**空间分配**:
- **上游控制区**: TEC入口流量控制
- **中游控制区**: VSS可变限速
- **下游控制区**: DHS应急车道开放

### 3.2 协调算法

```python
def coordinate_spatial_coverage(strategies: List[dict], road_network: dict) -> dict:
    """多策略空间覆盖协调算法"""
    
    spatial_plan = {
        'upstream': None,
        'midstream': None,
        'downstream': None
    }
    
    # 1. 识别拥堵路段的上下游关系
    congestion_edges = get_congestion_edges(road_network)
    
    # 2. 为每个策略分配空间范围
    for strategy in strategies:
        if strategy['type'] == 'TEC':
            upstream_entrances = find_upstream_entrances(congestion_edges, road_network)
            spatial_plan['upstream'] = {
                'control_type': 'TEC',
                'edges': upstream_entrances
            }
        
        elif strategy['type'] == 'VSS':
            spatial_plan['midstream'] = {
                'control_type': 'VSS',
                'edges': congestion_edges
            }
        
        elif strategy['type'] == 'DHS':
            dhs_eligible_edges = filter_hard_shoulder_edges(congestion_edges, road_network)
            spatial_plan['downstream'] = {
                'control_type': 'DHS',
                'edges': dhs_eligible_edges
            }
    
    # 3. 检查空间冲突
    if spatial_plan['midstream'] and spatial_plan['downstream']:
        if set(spatial_plan['midstream']['edges']) & set(spatial_plan['downstream']['edges']):
            # 有重叠，需要调整VSS限速以适应DHS开放后的通行能力
            adjust_vss_for_dhs(strategies)
    
    return spatial_plan
```

### 3.3 协调示例

**拥堵路段**: G4202 K42.32-K42.35

**空间分配**:
- 上游: TEC控制K42.32上游入口
- 中游: VSS控制K42.32-K42.35主线
- 下游: DHS开放K42.32-K42.35应急车道

---

## 四、参数耦合

### 4.1 TEC-VSS耦合

**耦合原则**: TEC限流值应使主线流量保持在VSS限速下的安全容量范围内

**算法**:
```python
def optimize_tec_vss_coupling(tec_strategy: dict, vss_strategy: dict):
    """TEC-VSS参数耦合优化"""
    
    # 计算VSS限速下的道路容量
    for vss_step in vss_strategy['parameters']['speed_steps']:
        road_capacity = calculate_road_capacity(
            speed_limit=vss_step['speed_kmh'],
            num_lanes=3,
            lane_width=3.75
        )
        
        # 调整TEC限流值，不超过道路容量的80%
        for tec_flow in tec_strategy['parameters']['flow_intervals']:
            if are_overlapping_times(vss_step, tec_flow):
                tec_flow['veh_per_hour'] = min(
                    tec_flow['veh_per_hour'],
                    road_capacity * 0.8
                )
```

---

### 4.2 VSS-DHS耦合

**耦合原则**: DHS开放后，VSS限速应适当提高以充分利用增加的车道

**算法**:
```python
def optimize_vss_dhs_coupling(vss_strategy: dict, dhs_strategy: dict):
    """VSS-DHS参数耦合优化"""
    
    # 找到DHS开放的时间段
    dhs_open_times = [
        (interval['begin_hours'], interval['end_hours'])
        for interval in dhs_strategy['parameters']['intervals']
        if interval['status'] == 'OPEN'
    ]
    
    # 调整VSS在该时间段的速度
    for step in vss_strategy['parameters']['speed_steps']:
        for begin, end in dhs_open_times:
            if begin <= step['time_hours'] < end:
                # DHS开放期间，VSS可以提高10 km/h
                step['speed_kmh'] = min(step['speed_kmh'] + 10, 100)
```

---

## 五、协同配置示例

### 5.1 VSS+DHS协同

```json
{
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
  }
}
```

---

### 5.2 VSS+DHS+TEC协同

```json
{
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

## 六、相关文档

- [方案架构设计](plan_architecture.md)
- [方案创建流程](plan_creation.md)
- [方案自动生成算法研究报告](../../control_strategies/方案自动生成算法研究报告.md)

---

**文档版本**: v1.0
**创建日期**: 2025-01-XX





