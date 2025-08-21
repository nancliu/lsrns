# 评估指标定义

## 1. 核心评估指标

### 1.1 流量匹配度指标

#### 1.1.1 流量误差（Flow Error）
- **定义**: 仿真流量与观测流量的相对误差
- **计算公式**: 
  ```python
  flow_error = abs(simulated_flow - observed_flow) / observed_flow
  ```
- **单位**: 百分比（%）
- **目标值**: < 15%
- **权重**: 0.30
- **数据来源**: 
  - 仿真数据: SUMO输出文件中的车辆计数
  - 观测数据: 真实交通检测器数据

#### 1.1.2 流量分布误差（Flow Distribution Error）
- **定义**: 不同时间段流量分布的匹配程度
- **计算公式**: 
  ```python
  # 按时间段（如15分钟）计算
  distribution_error = sqrt(sum((sim_flow_t - obs_flow_t)^2) / n_periods)
  ```
- **单位**: 车辆/小时
- **目标值**: < 20%
- **权重**: 0.20

### 1.2 延误准确性指标

#### 1.2.1 平均延误误差（Average Delay Error）
- **定义**: 仿真平均延误与观测平均延误的相对误差
- **计算公式**: 
  ```python
  delay_error = abs(sim_avg_delay - obs_avg_delay) / obs_avg_delay
  ```
- **单位**: 百分比（%）
- **目标值**: < 20%
- **权重**: 0.30
- **数据来源**: 
  - 仿真数据: SUMO行程时间统计
  - 观测数据: 真实交通延误数据

#### 1.2.2 延误分布误差（Delay Distribution Error）
- **定义**: 延误分布函数的匹配程度
- **计算公式**: 
  ```python
  # 使用Kolmogorov-Smirnov检验
  ks_statistic = max(abs(sim_cdf - obs_cdf))
  ```
- **单位**: 无单位（统计量）
- **目标值**: < 0.1
- **权重**: 0.15

### 1.3 车辆插入指标

#### 1.3.1 插入成功率（Insertion Success Rate）
- **定义**: 成功插入路网的车辆数量与计划车辆总数的比例
- **计算公式**: 
  ```python
  insertion_rate = successful_insertions / total_planned_vehicles
  ```
- **单位**: 百分比（%）
- **目标值**: > 95%
- **权重**: 0.25
- **数据来源**: SUMO仿真日志和统计文件

#### 1.3.2 插入延迟（Insertion Delay）
- **定义**: 车辆计划插入时间与实际插入时间的差异
- **计算公式**: 
  ```python
  insertion_delay = actual_insertion_time - planned_insertion_time
  ```
- **单位**: 秒
- **目标值**: < 60秒
- **权重**: 0.10

### 1.4 路网性能指标

#### 1.4.1 路网利用率（Network Utilization）
- **定义**: 实际运行的车辆数量与路网理论容量的比例
- **计算公式**: 
  ```python
  network_utilization = actual_vehicles / theoretical_capacity
  ```
- **单位**: 百分比（%）
- **目标值**: > 80%
- **权重**: 0.15
- **数据来源**: SUMO路网统计和容量分析

#### 1.4.2 交通流稳定性（Traffic Flow Stability）
- **定义**: 交通流速度变化的稳定性
- **计算公式**: 
  ```python
  # 使用变异系数
  stability = std_deviation(speed) / mean(speed)
  ```
- **单位**: 无单位
- **目标值**: < 0.3
- **权重**: 0.10

## 2. 综合评估函数

### 2.1 加权适应度函数

```python
def calculate_fitness(metrics_dict):
    """
    计算综合适应度得分
    
    Args:
        metrics_dict: 包含各项指标的字典
        
    Returns:
        float: 综合适应度得分 (0-1，越高越好)
    """
    # 权重配置
    weights = {
        'flow_error': 0.30,
        'flow_distribution_error': 0.20,
        'delay_error': 0.30,
        'delay_distribution_error': 0.15,
        'insertion_rate': 0.25,
        'insertion_delay': 0.10,
        'network_utilization': 0.15,
        'traffic_stability': 0.10
    }
    
    # 归一化处理
    normalized_metrics = {}
    
    # 流量误差归一化 (越小越好 -> 越大越好)
    normalized_metrics['flow_error'] = max(0, 1 - metrics_dict['flow_error'])
    normalized_metrics['flow_distribution_error'] = max(0, 1 - metrics_dict['flow_distribution_error'])
    
    # 延误误差归一化 (越小越好 -> 越大越好)
    normalized_metrics['delay_error'] = max(0, 1 - metrics_dict['delay_error'])
    normalized_metrics['delay_distribution_error'] = max(0, 1 - metrics_dict['delay_distribution_error'])
    
    # 插入成功率 (越大越好)
    normalized_metrics['insertion_rate'] = metrics_dict['insertion_rate']
    
    # 插入延迟归一化 (越小越好 -> 越大越好)
    max_delay = 300  # 最大允许延迟5分钟
    normalized_metrics['insertion_delay'] = max(0, 1 - metrics_dict['insertion_delay'] / max_delay)
    
    # 路网利用率 (越大越好)
    normalized_metrics['network_utilization'] = metrics_dict['network_utilization']
    
    # 交通流稳定性归一化 (越小越好 -> 越大越好)
    max_stability = 0.5  # 最大允许稳定性值
    normalized_metrics['traffic_stability'] = max(0, 1 - metrics_dict['traffic_stability'] / max_stability)
    
    # 计算加权得分
    total_weight = sum(weights.values())
    fitness = sum(weights[key] * normalized_metrics[key] for key in weights.keys()) / total_weight
    
    return fitness
```

### 2.2 多目标优化函数

```python
def calculate_multi_objective_fitness(metrics_dict):
    """
    计算多目标适应度（用于Pareto优化）
    
    Returns:
        dict: 各目标的适应度值
    """
    objectives = {
        'flow_accuracy': 1 - metrics_dict['flow_error'],
        'delay_accuracy': 1 - metrics_dict['delay_error'],
        'insertion_efficiency': metrics_dict['insertion_rate'],
        'network_efficiency': metrics_dict['network_utilization']
    }
    
    return objectives
```

## 3. 指标计算方法

### 3.1 流量计算

```python
def calculate_flow_metrics(sim_data, obs_data, time_interval=900):
    """
    计算流量相关指标
    
    Args:
        sim_data: 仿真流量数据
        obs_data: 观测流量数据
        time_interval: 时间间隔（秒）
        
    Returns:
        dict: 流量指标字典
    """
    # 按时间段聚合流量
    sim_flow_by_time = aggregate_flow_by_time(sim_data, time_interval)
    obs_flow_by_time = aggregate_flow_by_time(obs_data, time_interval)
    
    # 计算总流量误差
    total_sim_flow = sum(sim_flow_by_time.values())
    total_obs_flow = sum(obs_flow_by_time.values())
    flow_error = abs(total_sim_flow - total_obs_flow) / total_obs_flow
    
    # 计算分布误差
    distribution_error = calculate_distribution_error(sim_flow_by_time, obs_flow_by_time)
    
    return {
        'flow_error': flow_error,
        'flow_distribution_error': distribution_error,
        'total_sim_flow': total_sim_flow,
        'total_obs_flow': total_obs_flow
    }
```

### 3.2 延误计算

```python
def calculate_delay_metrics(sim_trip_data, obs_delay_data):
    """
    计算延误相关指标
    
    Args:
        sim_trip_data: 仿真行程时间数据
        obs_delay_data: 观测延误数据
        
    Returns:
        dict: 延误指标字典
    """
    # 计算仿真延误
    sim_delays = calculate_delays_from_trips(sim_trip_data)
    
    # 计算平均延误误差
    sim_avg_delay = np.mean(sim_delays)
    obs_avg_delay = np.mean(obs_delay_data)
    delay_error = abs(sim_avg_delay - obs_avg_delay) / obs_avg_delay
    
    # 计算延误分布误差
    delay_distribution_error = calculate_ks_statistic(sim_delays, obs_delay_data)
    
    return {
        'delay_error': delay_error,
        'delay_distribution_error': delay_distribution_error,
        'sim_avg_delay': sim_avg_delay,
        'obs_avg_delay': obs_avg_delay
    }
```

### 3.3 插入成功率计算

```python
def calculate_insertion_metrics(sumo_output_files):
    """
    计算车辆插入相关指标
    
    Args:
        sumo_output_files: SUMO输出文件路径列表
        
    Returns:
        dict: 插入指标字典
    """
    # 解析SUMO输出文件
    planned_vehicles = parse_planned_vehicles(sumo_output_files)
    successful_insertions = parse_successful_insertions(sumo_output_files)
    insertion_times = parse_insertion_times(sumo_output_files)
    
    # 计算插入成功率
    insertion_rate = len(successful_insertions) / len(planned_vehicles)
    
    # 计算平均插入延迟
    insertion_delay = np.mean(insertion_times)
    
    return {
        'insertion_rate': insertion_rate,
        'insertion_delay': insertion_delay,
        'planned_vehicles': len(planned_vehicles),
        'successful_insertions': len(successful_insertions)
    }
```

## 4. 指标验证与校准

### 4.1 数据质量检查

```python
def validate_metrics_data(sim_data, obs_data):
    """
    验证指标数据的质量
    
    Returns:
        bool: 数据是否有效
    """
    # 检查数据完整性
    if not sim_data or not obs_data:
        return False
    
    # 检查数据一致性
    if len(sim_data) < 10 or len(obs_data) < 10:
        return False
    
    # 检查异常值
    if has_extreme_outliers(sim_data) or has_extreme_outliers(obs_data):
        return False
    
    return True
```

### 4.2 指标校准

```python
def calibrate_metrics(metrics_dict, calibration_factors):
    """
    根据校准因子调整指标值
    
    Args:
        metrics_dict: 原始指标字典
        calibration_factors: 校准因子字典
        
    Returns:
        dict: 校准后的指标字典
    """
    calibrated_metrics = {}
    
    for metric_name, value in metrics_dict.items():
        if metric_name in calibration_factors:
            factor = calibration_factors[metric_name]
            calibrated_metrics[metric_name] = value * factor
        else:
            calibrated_metrics[metric_name] = value
    
    return calibrated_metrics
```

## 5. 指标报告生成

### 5.1 综合报告

```python
def generate_metrics_report(metrics_dict, fitness_score, generation=None):
    """
    生成指标评估报告
    
    Args:
        metrics_dict: 各项指标值
        fitness_score: 综合适应度得分
        generation: 当前代数
        
    Returns:
        str: 格式化的报告文本
    """
    report = f"""
# SUMO参数标定评估报告
{'='*50}

## 基本信息
- 评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 当前代数: {generation if generation else 'N/A'}
- 综合适应度: {fitness_score:.4f}

## 详细指标
{'='*50}

### 流量指标
- 流量误差: {metrics_dict.get('flow_error', 0):.2%}
- 流量分布误差: {metrics_dict.get('flow_distribution_error', 0):.2%}

### 延误指标  
- 平均延误误差: {metrics_dict.get('delay_error', 0):.2%}
- 延误分布误差: {metrics_dict.get('delay_distribution_error', 0):.4f}

### 插入指标
- 插入成功率: {metrics_dict.get('insertion_rate', 0):.2%}
- 平均插入延迟: {metrics_dict.get('insertion_delay', 0):.1f}秒

### 路网性能
- 路网利用率: {metrics_dict.get('network_utilization', 0):.2%}
- 交通流稳定性: {metrics_dict.get('traffic_stability', 0):.4f}

## 评估结论
{'='*50}
"""
    
    # 添加评估结论
    if fitness_score >= 0.8:
        report += "- 标定效果优秀，参数组合接近最优\n"
    elif fitness_score >= 0.6:
        report += "- 标定效果良好，参数组合合理\n"
    elif fitness_score >= 0.4:
        report += "- 标定效果一般，需要进一步优化\n"
    else:
        report += "- 标定效果较差，建议重新设计参数范围\n"
    
    return report
```

### 5.2 趋势分析

```python
def analyze_metrics_trend(history_data):
    """
    分析指标变化趋势
    
    Args:
        history_data: 历史指标数据列表
        
    Returns:
        dict: 趋势分析结果
    """
    if len(history_data) < 2:
        return {}
    
    trends = {}
    
    for metric_name in history_data[0].keys():
        values = [data[metric_name] for data in history_data]
        
        # 计算趋势斜率
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        # 判断趋势
        if slope > 0.01:
            trend = "上升"
        elif slope < -0.01:
            trend = "下降"
        else:
            trend = "稳定"
        
        trends[metric_name] = {
            'trend': trend,
            'slope': slope,
            'improvement': (values[-1] - values[0]) / values[0] if values[0] != 0 else 0
        }
    
    return trends
```

