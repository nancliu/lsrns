# 方案参数优化

本文档详细说明方案参数的优化方法和算法。

---

## 一、参数优化概述

### 1.1 优化目标

参数优化的目标：
- ✅ 最大化管控效果（速度提升、拥堵减少）
- ✅ 最小化负面影响（排队增加、波动增大）
- ✅ 平衡多个目标（速度、流量、稳定性）

### 1.2 优化方法

1. **基于规则**: 使用交通流理论和经验规则
2. **基于数据**: 基于历史数据和仿真结果
3. **基于优化算法**: 使用遗传算法、贝叶斯优化等

---

## 二、VSS参数优化

### 2.1 限速值优化

#### 基于拥堵程度的优化

```python
def optimize_vss_speed_by_congestion(congestion_point: dict) -> float:
    """基于拥堵程度优化VSS限速值"""
    
    min_speed = congestion_point['min_speed']
    free_flow_speed = congestion_point.get('free_flow_speed', 100)
    
    # 根据拥堵严重程度选择限速值
    if min_speed < 15:
        # 极度拥堵: 限速40-50 km/h
        optimal_speed = 50
    elif min_speed < 20:
        # 严重拥堵: 限速50-60 km/h
        optimal_speed = 60
    elif min_speed < 30:
        # 中度拥堵: 限速60-80 km/h
        optimal_speed = free_flow_speed * 0.7
    else:
        # 轻度拥堵: 限速80-100 km/h
        optimal_speed = free_flow_speed * 0.9
    
    return optimal_speed
```

#### 基于自由流速度的优化

```python
def optimize_vss_speed_by_free_flow(congestion_point: dict) -> float:
    """基于自由流速度优化VSS限速值"""
    
    free_flow_speed = congestion_point.get('free_flow_speed', 100)
    
    # 限速值 = 自由流速度 × (0.6~0.8)
    # 根据拥堵持续时间调整系数
    duration_hours = congestion_point.get('severe_duration', 2)
    
    if duration_hours > 4:
        # 持续拥堵时间长: 使用更低的系数
        coefficient = 0.6
    else:
        # 持续拥堵时间短: 使用较高的系数
        coefficient = 0.75
    
    optimal_speed = free_flow_speed * coefficient
    
    return max(40, min(optimal_speed, 100))  # 限制在40-100 km/h
```

---

### 2.2 时刻点优化

#### 基于拥堵时段的优化

```python
def optimize_vss_time_steps(congestion_point: dict, optimal_speed: float) -> List[dict]:
    """优化VSS时刻点设置"""
    
    peak_hours = congestion_point['peak_hours']
    
    speed_steps = []
    
    # 1. 平峰期: 正常速度
    speed_steps.append({'time_hours': 0, 'speed_kmh': 100})
    
    # 2. 高峰期前1小时: 预警降速
    pre_peak_hour = min(peak_hours) - 1
    if pre_peak_hour > 0:
        speed_steps.append({
            'time_hours': pre_peak_hour,
            'speed_kmh': optimal_speed + 20  # 预警速度
        })
    
    # 3. 高峰期: 严格限速
    speed_steps.append({
        'time_hours': min(peak_hours),
        'speed_kmh': optimal_speed
    })
    
    # 4. 高峰期结束: 恢复
    post_peak_hour = max(peak_hours) + 1
    speed_steps.append({
        'time_hours': post_peak_hour,
        'speed_kmh': optimal_speed + 20
    })
    
    # 5. 完全恢复
    speed_steps.append({'time_hours': 23, 'speed_kmh': 100})
    
    return speed_steps
```

---

## 三、DHS参数优化

### 3.1 开放时段优化

#### 基于高峰时段的优化

```python
def optimize_dhs_intervals(congestion_point: dict) -> List[dict]:
    """优化DHS开放时段"""
    
    peak_hours = congestion_point['peak_hours']
    
    intervals = []
    
    # 高峰期前30分钟开始开放
    open_start = max(0, min(peak_hours) - 0.5)
    # 高峰期后30分钟结束开放
    open_end = min(24, max(peak_hours) + 0.5)
    
    # 构建24小时覆盖的时间段
    if open_start > 0:
        intervals.append({
            'begin_hours': 0,
            'end_hours': open_start,
            'status': 'CLOSED'
        })
    
    intervals.append({
        'begin_hours': open_start,
        'end_hours': open_end,
        'status': 'OPEN'
    })
    
    if open_end < 24:
        intervals.append({
            'begin_hours': open_end,
            'end_hours': 24,
            'status': 'CLOSED'
        })
    
    return intervals
```

---

### 3.2 车型限制优化

#### 基于安全性的优化

```python
def optimize_dhs_vehicle_types(safety_priority: bool = True) -> List[str]:
    """优化DHS允许车型"""
    
    if safety_priority:
        # 安全优先: 仅允许客车
        return ['passenger']
    else:
        # 容量优先: 允许所有车型
        return ['passenger', 'truck', 'delivery']
```

---

## 四、TEC参数优化

### 4.1 流量限制优化

#### 基于主线容量的优化

```python
def optimize_tec_flow(
    congestion_point: dict,
    mainline_capacity: float,
    safety_factor: float = 0.9
) -> float:
    """优化TEC流量限制"""
    
    mainline_flow = congestion_point['max_flow']
    
    # 计算允许的入口流量
    available_capacity = mainline_capacity - mainline_flow
    
    # 应用安全系数
    optimal_flow = available_capacity * safety_factor
    
    # 限制在合理范围内
    return max(100, min(optimal_flow, 800))
```

---

### 4.2 目标速度优化

#### 基于限流强度的优化

```python
def optimize_tec_target_speed(flow_reduction_ratio: float) -> float:
    """优化TEC目标速度"""
    
    # 流量削减比例越大，目标速度越低（强制限流）
    if flow_reduction_ratio > 0.6:
        # 严格限流: 目标速度10-15 km/h
        return 10
    elif flow_reduction_ratio > 0.4:
        # 中度限流: 目标速度15-20 km/h
        return 15
    else:
        # 轻度限流: 目标速度20-30 km/h
        return 20
```

---

## 五、多策略参数耦合优化

### 5.1 TEC-VSS耦合优化

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

### 5.2 VSS-DHS耦合优化

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
                # DHS开放期间，VSS可以提高10-15 km/h
                step['speed_kmh'] = min(step['speed_kmh'] + 12, 100)
```

---

## 六、基于仿真反馈的优化

### 6.1 效果评估

```python
def evaluate_plan_effectiveness(simulation_result: dict, baseline_result: dict) -> dict:
    """评估方案效果"""
    
    # 计算改善指标
    speed_improvement = (
        (simulation_result['avg_speed'] - baseline_result['avg_speed']) /
        baseline_result['avg_speed'] * 100
    )
    
    delay_reduction = (
        (baseline_result['total_delay'] - simulation_result['total_delay']) /
        baseline_result['total_delay'] * 100
    )
    
    return {
        'speed_improvement': speed_improvement,
        'delay_reduction': delay_reduction,
        'overall_score': (speed_improvement + delay_reduction) / 2
    }
```

---

### 6.2 参数调整

```python
def adjust_parameters_by_feedback(
    plan: dict,
    simulation_result: dict,
    target_improvement: float = 20.0
) -> dict:
    """基于仿真反馈调整参数"""
    
    current_improvement = simulation_result['speed_improvement']
    
    # 如果改善幅度不足，调整参数
    if current_improvement < target_improvement:
        # VSS: 降低限速值5-10 km/h
        if 'VSS' in plan['strategy_types']:
            for step in plan['vss_params']['speed_steps']:
                if step['speed_kmh'] > 50:
                    step['speed_kmh'] -= 5
        
        # TEC: 增加流量限制10-20%
        if 'TEC' in plan['strategy_types']:
            for flow in plan['tec_params']['flow_intervals']:
                flow['veh_per_hour'] *= 0.9
    
    return plan
```

---

## 七、相关文档

- [优化方法](optimization_methods.md)
- [效果评估](performance_evaluation.md)
- [方案自动生成算法研究报告](../../control_strategies/方案自动生成算法研究报告.md)

---

**文档版本**: v1.0
**创建日期**: 2025-01-XX









