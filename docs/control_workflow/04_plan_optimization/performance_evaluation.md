# 方案效果评估

本文档说明如何评估管控方案的效果。

---

## 一、评估概述

### 1.1 评估目的

评估方案效果的目的：
- ✅ 验证方案是否达到预期效果
- ✅ 对比不同方案的优劣
- ✅ 识别方案的改进空间
- ✅ 积累方案效果数据

### 1.2 评估方法

1. **仿真对比**: 对比基准方案和策略方案
2. **指标计算**: 计算速度提升、延误减少等指标
3. **统计分析**: 分析效果分布和稳定性

---

## 二、评估指标

### 2.1 速度指标

#### 平均速度提升

```python
def calculate_speed_improvement(baseline: dict, strategy: dict) -> float:
    """计算平均速度提升百分比"""
    
    baseline_speed = baseline['avg_speed_kmh']
    strategy_speed = strategy['avg_speed_kmh']
    
    improvement = (strategy_speed - baseline_speed) / baseline_speed * 100
    
    return improvement
```

#### 速度稳定性

```python
def calculate_speed_stability(strategy: dict) -> float:
    """计算速度稳定性（标准差）"""
    
    speeds = strategy['speed_time_series']
    std_dev = np.std(speeds)
    
    # 稳定性评分: 标准差越小越好
    stability_score = 100 - min(std_dev, 50) * 2
    
    return stability_score
```

---

### 2.2 延误指标

#### 总延误时间减少

```python
def calculate_delay_reduction(baseline: dict, strategy: dict) -> float:
    """计算总延误时间减少百分比"""
    
    baseline_delay = baseline['total_delay_seconds']
    strategy_delay = strategy['total_delay_seconds']
    
    reduction = (baseline_delay - strategy_delay) / baseline_delay * 100
    
    return reduction
```

---

### 2.3 流量指标

#### 通行能力提升

```python
def calculate_capacity_increase(baseline: dict, strategy: dict) -> float:
    """计算通行能力提升百分比"""
    
    baseline_flow = baseline['max_flow_veh_per_hour']
    strategy_flow = strategy['max_flow_veh_per_hour']
    
    increase = (strategy_flow - baseline_flow) / baseline_flow * 100
    
    return increase
```

---

### 2.4 排队指标

#### 最大排队长度减少

```python
def calculate_queue_reduction(baseline: dict, strategy: dict) -> float:
    """计算最大排队长度减少百分比"""
    
    baseline_queue = baseline['max_queue_length_meters']
    strategy_queue = strategy['max_queue_length_meters']
    
    reduction = (baseline_queue - strategy_queue) / baseline_queue * 100
    
    return reduction
```

---

## 三、评估流程

### 3.1 基准仿真

运行无管控的基准仿真：

```python
def run_baseline_simulation(case_id: str) -> dict:
    """运行基准仿真"""
    
    # 创建基准方案（无策略）
    baseline_plan = {
        'plan_id': 'baseline_plan',
        'strategy_references': []
    }
    
    # 运行仿真
    simulation_result = run_simulation(baseline_plan, case_id)
    
    return simulation_result
```

---

### 3.2 策略仿真

运行有管控的策略仿真：

```python
def run_strategy_simulation(plan: dict, case_id: str) -> dict:
    """运行策略仿真"""
    
    # 运行仿真
    simulation_result = run_simulation(plan, case_id)
    
    return simulation_result
```

---

### 3.3 效果对比

对比基准和策略的效果：

```python
def compare_effectiveness(baseline: dict, strategy: dict) -> dict:
    """对比方案效果"""
    
    comparison = {
        'speed_improvement': calculate_speed_improvement(baseline, strategy),
        'delay_reduction': calculate_delay_reduction(baseline, strategy),
        'capacity_increase': calculate_capacity_increase(baseline, strategy),
        'queue_reduction': calculate_queue_reduction(baseline, strategy)
    }
    
    # 计算综合评分
    comparison['overall_score'] = (
        comparison['speed_improvement'] * 0.4 +
        comparison['delay_reduction'] * 0.3 +
        comparison['capacity_increase'] * 0.2 +
        comparison['queue_reduction'] * 0.1
    )
    
    return comparison
```

---

## 四、评估报告

### 4.1 报告结构

```json
{
  "evaluation_report": {
    "plan_id": "plan_vss_morning_peak_simple",
    "case_id": "case_202510",
    "evaluation_date": "2025-10-26",
    "baseline_metrics": {
      "avg_speed_kmh": 15.14,
      "total_delay_seconds": 3600,
      "max_queue_length_meters": 600
    },
    "strategy_metrics": {
      "avg_speed_kmh": 45.32,
      "total_delay_seconds": 2700,
      "max_queue_length_meters": 400
    },
    "improvements": {
      "speed_improvement": 199.2,
      "delay_reduction": 25.0,
      "queue_reduction": 33.3
    },
    "overall_score": 89.5,
    "recommendation": "强烈推荐"
  }
}
```

---

## 五、相关文档

- [优化方法](optimization_methods.md)
- [参数优化](parameter_optimization.md)
- [方案自动生成算法研究报告](../../control_strategies/方案自动生成算法研究报告.md)

---

**文档版本**: v1.0
**创建日期**: 2025-01-XX



