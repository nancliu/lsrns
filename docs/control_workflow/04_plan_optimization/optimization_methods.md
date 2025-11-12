# 管控方案优化方法

本文档说明管控方案的优化方法和策略。

---

## 一、优化概述

### 1.1 优化目标

方案优化的目标：
- ✅ 提高管控效果（速度提升、拥堵减少）
- ✅ 优化资源利用（策略数量、参数设置）
- ✅ 降低实施成本（策略复杂度、维护成本）
- ✅ 提高方案稳定性（减少波动、提高可靠性）

### 1.2 优化类型

1. **参数优化**: 调整策略参数值
2. **组合优化**: 调整策略组合
3. **协同优化**: 优化策略协同机制
4. **效果优化**: 基于仿真结果优化

---

## 二、参数优化

### 2.1 VSS参数优化

#### 限速值优化

**优化目标**: 找到最优限速值，平衡速度提升和交通流稳定性

**优化方法**:
```python
def optimize_vss_speed(congestion_point: dict, target_improvement: float) -> float:
    """优化VSS限速值"""
    
    min_speed = congestion_point['min_speed']
    free_flow_speed = congestion_point.get('free_flow_speed', 100)
    
    # 基于拥堵程度计算目标限速
    if min_speed < 20:
        # 严重拥堵: 限速50 km/h
        optimal_speed = 50
    elif min_speed < 30:
        # 中度拥堵: 限速60-80 km/h
        optimal_speed = free_flow_speed * 0.6
    else:
        # 轻度拥堵: 限速80-100 km/h
        optimal_speed = free_flow_speed * 0.8
    
    return optimal_speed
```

#### 时刻点优化

**优化目标**: 找到最优的时刻点设置

**优化方法**:
- 高峰期前1小时: 预警降速
- 高峰期: 严格限速
- 高峰期后1小时: 恢复

---

### 2.2 DHS参数优化

#### 开放时段优化

**优化目标**: 找到最优的开放时段

**优化方法**:
```python
def optimize_dhs_intervals(congestion_point: dict) -> List[dict]:
    """优化DHS开放时段"""
    
    peak_hours = congestion_point['peak_hours']
    
    # 基于拥堵时段确定开放时段
    intervals = []
    
    # 高峰期前30分钟开始开放
    open_start = min(peak_hours) - 0.5
    # 高峰期后30分钟结束开放
    open_end = max(peak_hours) + 0.5
    
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
    intervals.append({
        'begin_hours': open_end,
        'end_hours': 24,
        'status': 'CLOSED'
    })
    
    return intervals
```

---

### 2.3 TEC参数优化

#### 流量限制优化

**优化目标**: 找到最优的流量限制值

**优化方法**:
```python
def optimize_tec_flow(congestion_point: dict, mainline_capacity: float) -> float:
    """优化TEC流量限制"""
    
    mainline_flow = congestion_point['max_flow']
    
    # 计算允许的入口流量
    available_capacity = mainline_capacity - mainline_flow
    
    # 保留10%安全余量
    optimal_flow = available_capacity * 0.9
    
    return optimal_flow
```

---

## 三、组合优化

### 3.1 策略组合选择

**优化目标**: 选择最优的策略组合

**选择规则**:
- 单策略: 简单拥堵场景
- 双策略: 复杂拥堵场景
- 多策略: 严重拥堵场景

**优化方法**:
```python
def optimize_strategy_combination(congestion_point: dict) -> List[str]:
    """优化策略组合"""
    
    strategies = []
    
    # 规则1: 速度过低 → VSS
    if congestion_point['min_speed'] < 30:
        strategies.append('VSS')
    
    # 规则2: 流量大 + 有应急车道 → DHS
    if congestion_point['max_flow'] > 300 and congestion_point.get('has_hard_shoulder'):
        strategies.append('DHS')
    
    # 规则3: 持续时长长 + 有入口 → TEC
    if congestion_point['severe_duration'] > 6 and congestion_point.get('has_entrance_control'):
        strategies.append('TEC')
    
    return strategies
```

---

### 3.2 策略优先级优化

**优化目标**: 确定策略的执行优先级

**优先级规则**:
- P0: 核心策略（必须执行）
- P1: 重要策略（建议执行）
- P2: 可选策略（按需执行）

---

## 四、协同优化

### 4.1 时序协调优化

**优化目标**: 找到最优的时间偏移

**优化方法**:
```python
def optimize_time_offsets(strategies: List[dict], baseline_data: dict) -> dict:
    """优化时序协调的时间偏移"""
    
    # 基于交通流特征计算最优偏移
    avg_speed = baseline_data['avg_speed_kmh'].mean()
    congestion_propagation_speed = avg_speed * 0.5
    
    # TEC到VSS的偏移 = 距离 / 传播速度
    distance_km = 2.0  # 假设入口到主线距离2km
    optimal_offset = -(distance_km / congestion_propagation_speed) if congestion_propagation_speed > 0 else -1.0
    
    return {
        'TEC_to_VSS': max(-2.0, min(0, optimal_offset)),
        'VSS_to_DHS': 1.0
    }
```

---

### 4.2 空间协调优化

**优化目标**: 优化策略的空间分配

**优化方法**:
- 分析拥堵路段的上下游关系
- 识别最优的控制点位置
- 分配策略到合适的空间范围

---

### 4.3 参数耦合优化

**优化目标**: 优化策略参数间的耦合关系

**优化方法**:
- TEC-VSS耦合: 调整TEC限流值以适应VSS限速
- VSS-DHS耦合: 调整VSS限速以适应DHS开放

---

## 五、效果优化

### 5.1 基于仿真结果优化

**优化流程**:
1. 运行基准仿真（无管控）
2. 运行策略仿真（有管控）
3. 对比效果指标
4. 调整参数
5. 重新仿真验证

**效果指标**:
- 平均速度提升百分比
- 总延误时间减少百分比
- 最大排队长度减少百分比
- 通行能力提升百分比

---

### 5.2 迭代优化

**优化方法**:
```python
def iterative_optimize(plan: dict, case_id: str, max_iterations: int = 5) -> dict:
    """迭代优化方案"""
    
    best_plan = plan
    best_score = 0
    
    for iteration in range(max_iterations):
        # 1. 运行仿真
        simulation_result = run_simulation(plan, case_id)
        
        # 2. 评估效果
        score = evaluate_effectiveness(simulation_result)
        
        # 3. 如果效果更好，更新最佳方案
        if score > best_score:
            best_plan = plan
            best_score = score
        
        # 4. 调整参数
        plan = adjust_parameters(plan, simulation_result)
    
    return best_plan
```

---

## 六、优化工具

### 6.1 参数扫描

**用途**: 测试不同参数值的效果

**方法**:
```python
def parameter_sweep(base_plan: dict, parameter: str, value_range: List[float]) -> List[dict]:
    """参数扫描"""
    
    plans = []
    for value in value_range:
        plan = copy.deepcopy(base_plan)
        plan['parameters'][parameter] = value
        plans.append(plan)
    
    return plans
```

---

### 6.2 因子实验设计（DOE）

**用途**: 系统评估多个参数的交互效果

**方法**:
- 全因子设计: 测试所有参数组合
- 部分因子设计: 测试部分参数组合（减少实验次数）

---

## 七、相关文档

- [参数优化](parameter_optimization.md)
- [效果评估](performance_evaluation.md)
- [方案自动生成算法研究报告](../../control_strategies/方案自动生成算法研究报告.md)

---

**文档版本**: v1.0
**创建日期**: 2025-01-XX






