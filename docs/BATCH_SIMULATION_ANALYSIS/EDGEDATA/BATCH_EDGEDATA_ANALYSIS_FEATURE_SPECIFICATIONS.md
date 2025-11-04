# 批量 EdgeData 分析功能规格书

## 目录

1. [核心功能 API](#核心功能-api)
2. [详细功能规格](#详细功能规格)
3. [数据流与实现](#数据流与实现)
4. [优先级与依赖](#优先级与依赖)
5. [开发任务列表](#开发任务列表)

---

## 核心功能 API

### 服务入口

```python
# api/services/batch_edgedata_analysis_service.py

class BatchEdgeDataAnalysisService:
    """批量EdgeData分析服务"""

    async def analyze_batch_comparison(
        self,
        case_id: str,
        scenario_ids: Dict[str, str],  # {baseline_id, scenario_1_id, scenario_2_id, ...}
        analysis_type: str = "all"  # 分析类型
    ) -> Dict[str, Any]:
        """执行批量比较分析"""

    async def evaluate_control_strategy(
        self,
        case_id: str,
        baseline_sim_id: str,
        strategy_sim_id: str,
        strategy_type: str,  # VSS | TEC | DHS
        strategy_config: Dict
    ) -> Dict[str, Any]:
        """评估控制策略效果"""

    async def analyze_spatial_temporal_evolution(
        self,
        case_id: str,
        simulation_id: str,
        metric: str  # speed | flow | density | congestion
    ) -> Dict[str, Any]:
        """分析时空演变过程"""
```

### REST API 端点

```
POST /api/v1/analysis/batch-edgedata/compare
    请求体:
    {
        "case_id": "case_20251028_091831",
        "scenarios": {
            "baseline": "sim_baseline",
            "vss": "sim_vss_001",
            "tec": "sim_tec_001"
        },
        "metrics": ["flow", "speed", "congestion"]
    }
    返回: {analysis_id, comparison_results, charts, report}

POST /api/v1/analysis/batch-edgedata/strategy-evaluation
    请求体:
    {
        "case_id": "case_20251028_091831",
        "baseline_sim_id": "sim_baseline",
        "strategy_sim_id": "sim_vss_001",
        "strategy_type": "VSS",
        "strategy_config": {...}
    }
    返回: {effectiveness_score, kpi_achievement, recommendations}

POST /api/v1/analysis/batch-edgedata/spatial-temporal
    请求体:
    {
        "case_id": "case_20251028_091831",
        "simulation_id": "sim_001",
        "metric": "congestion",
        "output_format": "heatmap_sequence"  # 或 animation
    }
    返回: {frame_list, animation_file}
```

---

## 详细功能规格

### 功能分组

#### 分组 A: 批量对比分析 (Batch Comparison)

##### **F2-A1: 多方案流量对比**

```python
def compare_flow_metrics(
    scenarios: Dict[str, pd.DataFrame],  # scenario_name -> edgedata_df
    baseline_name: str = "baseline"
) -> Dict[str, Any]:
    """
    比较多个方案的流量指标

    Metrics:
    - Overall flow rate (vehicles/hour): ∑entered / duration_hours
    - Flow distribution by edge: edge-level statistics
    - Flow variance: std deviation across time
    - Peak flow: max aggregate flow in any interval
    - Off-peak flow: min aggregate flow
    - Flow uniformity: consistency across edges

    Output:
    {
        "overall_metrics": {
            "baseline": {"avg_flow": 1200, "max_flow": 1500, "std": 100},
            "scenario_1": {...},
        },
        "comparison": {
            "scenario_1_vs_baseline": {
                "relative_change_pct": 15.5,
                "absolute_change": 186
            }
        },
        "edge_level": {
            "-8712": {"baseline": 450, "scenario_1": 490, "diff_pct": 8.9},
            ...
        },
        "top_10_improved": [...],
        "top_10_degraded": [...]
    }
    """
```

**实现步骤**:
1. 加载所有方案的 EdgeData
2. 按边和时间聚合流量数据
3. 计算统计指标
4. 生成对比表格和热力图
5. 输出改善/恶化路段排名

**验证标准**:
- ✓ 流量计算精度 ±0.1%
- ✓ 支持 2-20 个方案对比
- ✓ 生成 3 种以上可视化

---

##### **F2-A2: 多方案速度分析**

```python
def compare_speed_metrics(
    scenarios: Dict[str, pd.DataFrame],
    baseline_name: str = "baseline"
) -> Dict[str, Any]:
    """
    比较多个方案的速度指标

    Metrics:
    - Average speed (m/s)
    - Speed distribution (percentiles: 10th, 25th, 50th, 75th, 90th)
    - Speed reliability (std deviation)
    - Percentage of edges below threshold (e.g., < 5 m/s)
    - Speed-to-limit ratio: actual_speed / speed_limit

    Analysis:
    1. Time-series speed evolution
    2. Edge-level speed statistics
    3. Congestion threshold frequency (e.g., speed < 5 m/s)

    Output:
    {
        "speed_summary": {
            "baseline": {"mean": 8.5, "median": 9.2, "std": 2.1, "min": 0.5, "max": 13.9},
            "scenario_1": {...}
        },
        "percentiles": {
            "baseline": {10: 4.5, 25: 6.8, 50: 9.2, 75: 11.0, 90: 12.5},
            "scenario_1": {...}
        },
        "speed_improvements": {
            "scenario_1_vs_baseline": {
                "mean_increase_pct": 18.8,
                "percentile_improvements": {50: 2.1, 90: 1.5}
            }
        },
        "low_speed_edges": {
            "baseline": 45,  # 低速边的数量
            "scenario_1": 28
        }
    }
    """
```

**实现步骤**:
1. 加载 EdgeData 中的速度字段
2. 计算各分位数
3. 生成速度 CDF 曲线
4. 识别低速（拥堵）区间
5. 生成对比报告

**验证标准**:
- ✓ 分位数计算准确
- ✓ CDF 曲线平滑
- ✓ 生成 PDF 格式报告

---

##### **F2-A3: 多方案拥堵指数对比**

```python
def compare_congestion_index(
    scenarios: Dict[str, pd.DataFrame],
    baseline_name: str = "baseline"
) -> Dict[str, Any]:
    """
    拥堵指数 = waitingTime / interval_duration (0-1, 越高越拥堵)

    Alternative definitions:
    - Speed-based: (1 - speed/speed_limit) * weight
    - Density-based: density / capacity
    - Occupancy-based: occupancy threshold

    Output:
    {
        "congestion_index_stats": {
            "baseline": {
                "mean": 0.15,
                "max": 0.72,
                "std": 0.12,
                "high_congestion_threshold": 0.40,
                "pct_high_congestion_edges": 18.5
            },
            "scenario_1": {...}
        },
        "spatial_distribution": {
            "by_congestion_level": {
                "free_flow": {count: 180, pct: 45.0},
                "light_congestion": {count: 140, pct: 35.0},
                "moderate_congestion": {count: 50, pct: 12.5},
                "severe_congestion": {count: 30, pct: 7.5}
            }
        },
        "time_series": {
            0: {mean: 0.10, max: 0.35},
            300: {mean: 0.18, max: 0.68},
            600: {mean: 0.22, max: 0.78},
            ...
        },
        "improvements": {
            "scenario_1_vs_baseline": {
                "mean_reduction_pct": 35.0,
                "high_congestion_edge_reduction": 12  # 缓解的拥堵路段数
            }
        }
    }
    """
```

---

##### **F2-A4: 路段级效果评估**

```python
def evaluate_edge_level_improvements(
    scenarios: Dict[str, pd.DataFrame],
    baseline_name: str = "baseline",
    top_k: int = 10
) -> Dict[str, Any]:
    """
    按路段评估优化效果

    Output:
    {
        "top_improved_edges": [
            {
                "edge_id": "-8712",
                "baseline_metrics": {speed: 7.2, flow: 450, congestion_idx: 0.35},
                "scenario_1_metrics": {speed: 9.8, flow: 520, congestion_idx: 0.18},
                "improvements": {
                    "speed_increase_pct": 36.1,
                    "flow_increase_pct": 15.6,
                    "congestion_reduction_pct": 48.6
                },
                "improvement_score": 92.3  # 综合评分
            },
            ...
        ],
        "top_degraded_edges": [...],
        "edge_efficiency_matrix": {  # 所有路段的效率矩阵
            "-8712": {"baseline": 0.45, "scenario_1": 0.62, "scenario_2": 0.58},
            "-15452.627": {...},
            ...
        }
    }
    """
```

---

##### **F2-A5: 峰值时段对比**

```python
def analyze_peak_periods(
    scenarios: Dict[str, pd.DataFrame],
    baseline_name: str = "baseline",
    peak_definition: str = "top_20_pct"  # 或 "top_10_pct"
) -> Dict[str, Any]:
    """
    识别和分析峰值时段

    Output:
    {
        "peak_definition": "top 20% flow periods",
        "peak_periods": [
            {
                "time_interval": [1800, 2100],  # 秒数
                "baseline_flow": 1450,
                "scenario_1_flow": 1680,
                "flow_increase_pct": 15.9,
                "baseline_speed": 6.8,
                "scenario_1_speed": 8.2,
                "speed_increase_pct": 20.6
            },
            ...
        ],
        "off_peak_periods": [...],
        "peak_shift_analysis": {
            "description": "是否出现削峰填谷现象",
            "original_peak_time": 2100,
            "new_peak_time": 1950,
            "peak_shift": -150  # 秒
        }
    }
    """
```

---

#### 分组 B: 时空演变分析 (Spatial-Temporal)

##### **F2-B1: 拥堵扩散过程分析**

```python
def analyze_congestion_propagation(
    edgedata_df: pd.DataFrame,
    network_graph: nx.DiGraph,
    metric: str = "congestion_index"
) -> Dict[str, Any]:
    """
    分析拥堵的时空演变

    Output:
    {
        "propagation_timeline": [
            {
                "time": 1800,  # 秒
                "affected_edges": 25,
                "max_congestion": 0.68,
                "propagation_front": [edge_ids...],
                "propagation_speed": 0.5  # km/h
            },
            ...
        ],
        "heatmap_frames": [
            "charts/congestion_heatmap_0.png",
            "charts/congestion_heatmap_1.png",
            ...
        ],
        "xt_diagram": {
            "file": "charts/xt_diagram.png",
            "description": "时间-空间图，显示拥堵波传播"
        },
        "expansion_contraction": {
            "expansion_phase": {
                "start_time": 1800,
                "end_time": 2400,
                "max_affected_edges": 48
            },
            "recovery_phase": {
                "start_time": 2400,
                "end_time": 3600,
                "recovery_rate": 0.08  # 边数/分钟
            }
        },
        "animation": "congestion_evolution.mp4"  # 可选
    }
    """
```

**热力图生成**:
```python
def generate_heatmap_sequence(
    edgedata_df: pd.DataFrame,
    network: nx.DiGraph,
    metric: str,
    freq: int = 300,  # 每5分钟一个帧
    output_dir: Path = None
) -> List[str]:
    """
    生成热力图序列

    对每个时间间隔：
    1. 提取边的 metric 值
    2. 在网络拓扑上着色
    3. 保存为 PNG
    4. 返回文件列表
    """
```

---

##### **F2-B2: 流量波传播分析**

```python
def analyze_flow_wave_propagation(
    edgedata_df: pd.DataFrame,
    route_sequence: List[str]  # 路段序列，如 [edge1, edge2, edge3, ...]
) -> Dict[str, Any]:
    """
    沿路线追踪流量波

    Output:
    {
        "wave_speed": 0.85,  # km/h
        "travel_time_range": {
            "free_flow": 180,  # 秒
            "congested": 420,
            "recovery": 240
        },
        "wave_amplitude": {
            "flow_variation": {min: 200, max: 950},
            "speed_variation": {min: 3.5, max: 12.1}
        },
        "xt_plot_data": {
            "x": [edge_positions...],
            "t": [times...],
            "z": [flow_values...]  # 用于绘制xt图
        }
    }
    """
```

---

##### **F2-B3: 速度梯度分析**

```python
def analyze_speed_gradient(
    edgedata_df: pd.DataFrame,
    network: nx.DiGraph
) -> Dict[str, Any]:
    """
    分析相邻边的速度差异（梯度）

    Output:
    {
        "gradient_statistics": {
            "mean_gradient": 0.45,  # m/s per edge
            "max_gradient": 3.2,
            "steep_gradient_edges": [
                {"from": "edge1", "to": "edge2", "gradient": 3.2},
                ...
            ]
        },
        "gradient_heatmap": "charts/speed_gradient_heatmap.png",
        "critical_points": [
            {
                "edge": "edge_x",
                "description": "容量瓶颈，下游速度低20%",
                "severity": 8.5  # 评分
            }
        ]
    }
    """
```

---

#### 分组 C: 控制策略评估 (Strategy Evaluation)

##### **F2-C1: VSS 策略效果评估**

```python
def evaluate_vss_strategy(
    baseline_edgedata: pd.DataFrame,
    vss_edgedata: pd.DataFrame,
    vss_config: Dict  # {affected_edges: [...], speed_limits: [...]}
) -> Dict[str, Any]:
    """
    评估可变限速(Variable Speed Sign)策略

    评估指标：
    1. 受影响路段的速度改善
    2. 下游路段的连锁效应
    3. 全网的拥堵缓解程度
    4. 安全性指标（速度均匀性）

    Output:
    {
        "strategy_effectiveness": {
            "score": 82.5,  # 0-100
            "level": "effective"  # 优秀/有效/边际/无效
        },
        "kpi_achievement": {
            "speed_improvement": {
                "target": 15,  # %
                "actual": 18.2,
                "status": "exceeded"
            },
            "delay_reduction": {
                "target": 20,
                "actual": 24.5,
                "status": "exceeded"
            },
            "throughput_increase": {
                "target": 10,
                "actual": 12.1,
                "status": "exceeded"
            }
        },
        "affected_areas": {
            "vss_controlled_edges": {
                "count": 12,
                "avg_speed_improvement": 18.2,
                "avg_congestion_reduction": 35.0
            },
            "downstream_edges": {
                "count": 8,
                "avg_speed_improvement": 6.5,  # 连锁效应
                "avg_congestion_reduction": 12.0
            }
        },
        "cost_benefit": {
            "implementation_cost": 150000,  # 元（假设）
            "annual_benefit": 450000,  # 延误减少价值
            "roi_years": 0.33
        },
        "recommendations": [
            "建议在峰值时段启动VSS",
            "可适当提高限速至...以获得更好效果"
        ]
    }
    """
```

---

##### **F2-C2: TEC 策略效果评估**

```python
def evaluate_tec_strategy(
    baseline_edgedata: pd.DataFrame,
    tec_edgedata: pd.DataFrame,
    ramp_config: Dict  # {ramp_edges: [...], metering_rates: [...]}
) -> Dict[str, Any]:
    """
    评估收费站管控(Toll/Entrance Control)策略

    评估指标：
    1. 匝道排队长度变化
    2. 主干线流量改善
    3. 区域内总延误
    4. 公平性（不同出口的流量分配）

    Output:
    {
        "strategy_effectiveness": {
            "score": 75.3,
            "level": "effective"
        },
        "ramp_performance": {
            "ramp_edge_001": {
                "baseline_queue_length": 450,  # 米
                "tec_queue_length": 280,
                "queue_reduction_pct": 37.8,
                "average_wait_time": {
                    "baseline": 120,  # 秒
                    "tec": 75,
                    "reduction_pct": 37.5
                }
            }
        },
        "mainline_benefit": {
            "speed_improvement_pct": 22.0,
            "flow_improvement_pct": 18.5
        },
        "regional_analysis": {
            "total_vehicle_delay": {
                "baseline": 18500,  # 车小时
                "tec": 14200,
                "reduction": 4300
            }
        }
    }
    """
```

---

##### **F2-C3: DHS 策略效果评估**

```python
def evaluate_dhs_strategy(
    baseline_edgedata: pd.DataFrame,
    dhs_edgedata: pd.DataFrame,
    dhs_config: Dict  # {dhs_segments: [...], activation_times: [...]}
) -> Dict[str, Any]:
    """
    评估动态硬路肩(Dynamic Hard Shoulder)策略

    评估指标：
    1. 硬路肩利用率
    2. 容量增加幅度
    3. 安全性影响
    4. 成本效益

    Output:
    {
        "strategy_effectiveness": {
            "score": 88.5,
            "level": "highly_effective"
        },
        "dhs_utilization": {
            "segment_001": {
                "activation_hours": 2.5,
                "average_speed": 9.5,
                "added_throughput": 450,  # 车/小时
                "utilization_rate": 0.85
            }
        },
        "capacity_improvement": {
            "baseline_capacity": 1800,  # 车/小时
            "dhs_capacity": 2250,
            "capacity_increase_pct": 25.0
        },
        "safety_metrics": {
            "speed_uniformity": {
                "baseline_std": 3.2,
                "dhs_std": 4.1,
                "change_pct": 28.1  # 增加（可能更危险）
            },
            "lane_change_frequency": {
                "baseline": 245,
                "dhs": 318,
                "change_pct": 29.8
            }
        },
        "recommendations": [
            "建议在特定时段激活DHS",
            "注意安全风险，加强监测"
        ]
    }
    """
```

---

##### **F2-C4: 协调控制评估**

```python
def evaluate_coordinated_control(
    baseline_edgedata: pd.DataFrame,
    coordinated_edgedata: pd.DataFrame,
    strategy_combination: Dict  # {vss: {...}, tec: {...}, dhs: {...}}
) -> Dict[str, Any]:
    """
    评估多策略协调控制的效果

    Output:
    {
        "overall_effectiveness": {
            "score": 91.2,
            "level": "highly_effective"
        },
        "individual_strategy_contribution": {
            "vss": 35,  # 贡献百分比
            "tec": 40,
            "dhs": 25
        },
        "synergy_effect": {
            "expected_combined_score": 75,
            "actual_combined_score": 91.2,
            "synergy_bonus": 16.2,
            "description": "多策略协调产生显著叠加效应"
        },
        "conflict_analysis": {
            "conflicts": [
                {
                    "strategy_1": "VSS",
                    "strategy_2": "TEC",
                    "description": "在出口处可能产生冲突",
                    "severity": "low",
                    "mitigation": "调整限速与收费时间"
                }
            ],
            "compatibility_score": 0.92
        }
    }
    """
```

---

##### **F2-C5: 关键指标提升量化**

```python
def quantify_kpi_improvements(
    baseline_edgedata: pd.DataFrame,
    scenario_edgedata: pd.DataFrame,
    scenario_name: str
) -> Dict[str, Any]:
    """
    量化关键绩效指标（KPI）的改善

    标准KPI:
    1. 平均速度 (Average Speed)
    2. 总延误 (Total Delay)
    3. 通行能力 (Throughput)
    4. 延误时间成本 (Delay Cost)
    5. 行程时间可靠性 (Journey Time Reliability)

    Output:
    {
        "speed_metrics": {
            "baseline_avg": 8.5,
            "scenario_avg": 10.2,
            "improvement": {
                "absolute": 1.7,
                "percentage": 20.0,
                "confidence_interval": [19.2, 20.8]
            }
        },
        "delay_metrics": {
            "baseline_total_hours": 2450,
            "scenario_total_hours": 1850,
            "reduction": {
                "hours": 600,
                "percentage": 24.5,
                "cost_saving": 1800000  # RMB，按时间价值计
            }
        },
        "throughput_metrics": {
            "baseline": 85200,  # 总通过车数
            "scenario": 98500,
            "increase": {
                "vehicles": 13300,
                "percentage": 15.6
            }
        },
        "reliability_metrics": {
            "baseline_reliability_index": 0.68,
            "scenario_reliability_index": 0.82,
            "improvement_pct": 20.6
        },
        "summary_scorecard": {
            "speed": {value: 20.0, weight: 0.25, contribution: 5.0},
            "delay": {value: 24.5, weight: 0.35, contribution: 8.6},
            "throughput": {value: 15.6, weight: 0.25, contribution: 3.9},
            "reliability": {value: 20.6, weight: 0.15, contribution: 3.1},
            "total_score": 20.6  # 加权平均
        }
    }
    """
```

---

#### 分组 D: 优化效果量化 (Optimization Quantification)

##### **F2-D1: 关键路段优化度量**

```python
def calculate_edge_optimization_metrics(
    scenarios: Dict[str, pd.DataFrame],
    baseline_name: str = "baseline"
) -> Dict[str, Any]:
    """
    计算每条路段的优化效果

    效率指数 = (v / v_max) × (f / f_max) × (1 - CI)
    其中:
    - v: 平均速度
    - v_max: 最高限速
    - f: 流量
    - f_max: 路段容量
    - CI: 拥堵指数

    Output:
    {
        "edge_efficiency_ranking": [
            {
                "edge_id": "-8712",
                "baseline_efficiency": 0.42,
                "scenario_1_efficiency": 0.63,
                "improvement_pct": 50.0,
                "ranking_change": 5  # 从第10上升到第5
            },
            ...
        ],
        "efficiency_matrix": {
            "edge_1": {baseline: 0.42, scenario_1: 0.63, scenario_2: 0.58},
            "edge_2": {...},
            ...
        },
        "efficiency_improvement_distribution": {
            "highly_improved (>30%)": 45,  # 路段数
            "improved (10-30%)": 120,
            "stable (-10 to 10%)": 180,
            "degraded (-30 to -10%)": 35,
            "highly_degraded (<-30%)": 20
        }
    }
    """
```

---

##### **F2-D2: 全网效率评估**

```python
def calculate_network_efficiency(
    scenarios: Dict[str, pd.DataFrame],
    baseline_name: str = "baseline"
) -> Dict[str, Any]:
    """
    评估全网整体效率

    全网效率指数 = Σ(路段效率 × 路段权重) / Σ权重
    权重 = 路段流量 / 总流量

    Output:
    {
        "network_efficiency_index": {
            "baseline": 0.52,
            "scenario_1": 0.68,
            "scenario_2": 0.65
        },
        "commute_index": {
            "baseline": 1.15,  # 延误比 (实际时间 / 自由流时间)
            "scenario_1": 0.95,
            "scenario_2": 0.98
        },
        "congestion_intensity": {
            "baseline": 0.28,  # 0-1
            "scenario_1": 0.18,
            "scenario_2": 0.20
        },
        "spatial_efficiency_variance": {
            "baseline_gini": 0.35,  # 基尼系数，越小越均匀
            "scenario_1_gini": 0.28,
            "scenario_2_gini": 0.31
        }
    }
    """
```

---

##### **F2-D3: 成本-效益分析**

```python
def perform_cost_benefit_analysis(
    scenario_improvements: Dict,
    implementation_cost: float,
    annual_operation_cost: float,
    valuation_params: Dict = None  # 时间价值、事故减少等
) -> Dict[str, Any]:
    """
    执行经济学分析

    Output:
    {
        "costs": {
            "implementation": 500000,
            "annual_operation": 50000,
            "maintenance": 30000,
            "total_annual": 80000
        },
        "benefits": {
            "delay_reduction_value": 1200000,  # 基于VOT
            "accident_reduction": 150000,
            "emission_reduction": 80000,
            "fuel_savings": 100000,
            "total_annual": 1530000
        },
        "economic_metrics": {
            "bcr": 19.1,  # 效益-成本比
            "roi": 1812.5,  # 投资回报率(%)
            "payback_period": 0.33,  # 年
            "npv_10year": 12500000  # 10年净现值
        },
        "sensitivity_analysis": {
            "time_value_sensitivity": [...],
            "implementation_cost_sensitivity": [...]
        }
    }
    """
```

---

#### 分组 E: 高级分析 (Advanced Analytics)

##### **F2-E1: 拥堵识别与分类**

```python
def identify_and_classify_congestion(
    edgedata_df: pd.DataFrame,
    classification_method: str = "speed_based"
) -> Dict[str, Any]:
    """
    识别拥堵并分类其类型

    拥堵类型：
    1. 容量瓶颈 (Capacity Bottleneck): 反复出现的同位置拥堵
    2. 需求峰值 (Demand Peak): 时间集中的拥堵
    3. 突发事件 (Incident-related): 短期尖峰
    4. 事故/工程 (Accident/Construction): 异常模式

    Output:
    {
        "congestion_events": [
            {
                "event_id": 1,
                "time_range": [1800, 2400],
                "affected_edges": [edge_ids...],
                "type": "capacity_bottleneck",
                "severity": 7.5,  # 0-10
                "root_cause": "下游路口容量不足",
                "recommendations": ["增加下游车道", "优化信号"]
            },
            ...
        ],
        "congestion_type_distribution": {
            "capacity_bottleneck": 12,
            "demand_peak": 8,
            "incident_related": 2
        }
    }
    """
```

---

##### **F2-E2: 瓶颈识别**

```python
def identify_bottlenecks(
    edgedata_df: pd.DataFrame,
    network: nx.DiGraph,
    threshold_methods: List[str] = ["speed_based", "flow_based"]
) -> Dict[str, Any]:
    """
    识别和排序网络瓶颈

    Output:
    {
        "bottleneck_ranking": [
            {
                "rank": 1,
                "edge_id": "-8712",
                "bottleneck_score": 8.7,
                "metrics": {
                    "avg_speed": 5.2,
                    "capacity_utilization": 0.92,
                    "queue_length": 450
                },
                "impact": {
                    "affected_downstream_edges": 8,
                    "total_delay_generated": 1200,
                    "network_impact_factor": 0.15
                },
                "mitigation_strategies": [
                    "增加车道数",
                    "实施动态限速",
                    "优化信号控制"
                ]
            },
            ...
        ]
    }
    """
```

---

#### 分组 F: 报告与可视化 (Reporting & Visualization)

##### **F2-F1: 批量分析综合报告**

```python
def generate_comprehensive_report(
    analysis_results: Dict,
    report_format: str = "html"
) -> str:
    """
    生成综合分析报告

    报告结构：
    1. 执行摘要 (Executive Summary)
       - 关键发现
       - 主要改善
       - 建议

    2. 对比分析 (Comparison Analysis)
       - 流量、速度、拥堵对比
       - 图表和表格

    3. 策略评估 (Strategy Evaluation)
       - 各策略的效果评分
       - KPI达成度

    4. 详细分析 (Detailed Analysis)
       - 时空演变
       - 瓶颈识别
       - 改善优先级

    5. 建议和结论 (Recommendations)

    Output:
        report.html (或 .pdf)
    """
```

---

##### **F2-F2: 方案对比仪表板**

```python
def generate_interactive_dashboard(
    scenarios: Dict[str, Dict],
    output_file: Path
) -> str:
    """
    生成交互式仪表板

    功能：
    1. 实时度量显示
    2. 方案切换
    3. 图表交互
    4. 详细信息下钻

    技术：Plotly/Dash

    Output:
        dashboard.html
    """
```

---

##### **F2-F3: 地图可视化**

```python
def generate_network_map_visualization(
    edgedata_df: pd.DataFrame,
    network: nx.DiGraph,
    metric: str = "speed",
    output_file: Path = None
) -> str:
    """
    在网络拓扑上可视化数据

    Output:
        map_visualization.html (交互式地图)
    """
```

---

##### **F2-F4: 动态演动画**

```python
def generate_animation(
    edgedata_df: pd.DataFrame,
    network: nx.DiGraph,
    metric: str = "congestion",
    frame_rate: int = 5,
    output_file: Path = None
) -> str:
    """
    生成时间序列动画

    Output:
        animation.mp4
    """
```

---

##### **F2-F5: 数据导出与API**

```python
def export_analysis_results(
    analysis_results: Dict,
    export_formats: List[str] = ["csv", "json", "xlsx"]
) -> Dict[str, str]:
    """
    导出分析结果到多种格式

    Output:
    {
        "csv_files": [...],
        "json_files": [...],
        "xlsx_files": [...]
    }
    """

async def create_analysis_api_endpoint(
    analysis_id: str
) -> FastAPI.APIRouter:
    """
    为分析结果创建 REST API

    Endpoints:
    GET /analysis/{analysis_id}/summary
    GET /analysis/{analysis_id}/comparison
    GET /analysis/{analysis_id}/edge-details/{edge_id}
    GET /analysis/{analysis_id}/charts
    """
```

---

## 数据流与实现

### 数据处理管道

```
多个 EdgeData XML 文件
    │
    ├─→ 并行加载与解析
    │
    ├─→ 合并到统一 DataFrame
    │
    ├─→ 时间聚合与空间聚合
    │
    ├─→ 计算派生指标
    │   - 拥堵指数
    │   - 效率指数
    │   - 改善率
    │
    ├─→ 分组分析
    │   - 批量对比
    │   - 策略评估
    │   - 时空演变
    │
    ├─→ 数据清洗与验证
    │
    └─→ 报告与可视化生成
```

### 核心数据结构

```python
# EdgeData DataFrame 标准格式
edgedata_df = pd.DataFrame({
    'time_interval': [  # (start_sec, end_sec)
    'edge_id': str,
    'entered': int,      # 进入车数
    'left': int,         # 离开车数
    'speed': float,      # m/s
    'traveltime': float, # 秒
    'density': float,    # 车/km
    'occupancy': float,  # 0-1
    'waitingTime': float # 秒
    'sampledSeconds': float  # 车秒
})

# 分析结果结构
analysis_result = {
    'metadata': {...},
    'comparison_results': {
        'flow': {...},
        'speed': {...},
        'congestion': {...}
    },
    'strategy_evaluation': {
        'vss': {...},
        'tec': {...},
        'dhs': {...}
    },
    'spatial_temporal': {
        'propagation': {...},
        'heatmaps': [...],
        'animations': [...]
    },
    'recommendations': {...}
}
```

---

## 优先级与依赖

### 依赖关系图

```
Phase 1 (Week 1-2): 基础对比分析
├── F2-A1: 多方案流量对比 ✓
├── F2-A2: 多方案速度分析 ✓
├── F2-A3: 多方案拥堵对比 ✓
├── F2-D1: 路段优化度量 ✓
└── F2-D2: 全网效率评估 ✓
    │
    └──→ Phase 2 (Week 2-3): 策略评估
        ├── F2-C1: VSS 评估 (依赖 F2-A1/A2)
        ├── F2-C2: TEC 评估 (依赖 F2-A1/A2)
        ├── F2-C3: DHS 评估 (依赖 F2-A1/A2)
        ├── F2-C5: KPI 量化 (依赖 F2-A1/A2/A3)
        └── F2-C4: 协调评估 (依赖 F2-C1/C2/C3)
            │
            └──→ Phase 3 (Week 3-4): 高级分析
                ├── F2-B1: 拥堵扩散 (依赖 EdgeData 解析)
                ├── F2-B2: 流量波传播
                ├── F2-B3: 速度梯度
                ├── F2-E1: 拥堵分类 (依赖 B1/B2/B3)
                └── F2-E2: 瓶颈识别
                    │
                    └──→ Phase 4 (Week 4-5): 报告与可视化
                        ├── F2-F1: 综合报告 (依赖所有分析)
                        ├── F2-F2: 仪表板
                        ├── F2-F3: 地图可视化
                        ├── F2-F4: 动画生成
                        └── F2-F5: 数据导出
```

### 优先级分类

| 优先级 | 功能 | 完成时间 | 工作量 |
|--------|------|---------|--------|
| **P0** | F2-A1, A2, A3, D1, C1, C2, C5, F1 | 3周 | 16人天 |
| **P1** | F2-A4, A5, B1, C3, C4, E1, E2, F2, F5 | 2周 | 15人天 |
| **P2** | F2-B2, B3, D3, E4, F3, F4 | 2周 | 14人天 |

---

## 开发任务列表

### Sprint 1: 基础分析框架 (3天)

- [ ] 创建 BatchEdgeDataAnalysis 类框架
- [ ] 实现多方案 EdgeData 加载与合并
- [ ] 实现基础统计计算模块
- [ ] 编写单元测试

### Sprint 2: 批量对比分析 (4天)

- [ ] 实现 F2-A1 (流量对比)
- [ ] 实现 F2-A2 (速度对比)
- [ ] 实现 F2-A3 (拥堵对比)
- [ ] 生成对比图表 (Matplotlib/Plotly)
- [ ] 编写测试用例

### Sprint 3: 优化度量 (2天)

- [ ] 实现 F2-D1 (路段优化度量)
- [ ] 实现 F2-D2 (全网效率)
- [ ] 生成排序表格和矩阵

### Sprint 4: 策略评估框架 (3天)

- [ ] 实现策略评估基类
- [ ] 实现 F2-C1 (VSS 评估)
- [ ] 实现 F2-C2 (TEC 评估)
- [ ] 实现 F2-C3 (DHS 评估)

### Sprint 5: KPI 量化 (2天)

- [ ] 实现 F2-C5 (KPI 量化)
- [ ] 集成时间价值计算
- [ ] 生成评分卡

### Sprint 6: 时空分析 (4天)

- [ ] 实现 F2-B1 (拥堵扩散)
- [ ] 实现热力图生成
- [ ] 实现 XT 图绘制
- [ ] 测试性能

### Sprint 7: 高级分析 (3天)

- [ ] 实现 F2-E1 (拥堵识别)
- [ ] 实现 F2-E2 (瓶颈识别)
- [ ] 生成根因分析建议

### Sprint 8: 报告与可视化 (5天)

- [ ] 实现 F2-F1 (综合报告)
- [ ] 实现 F2-F2 (交互仪表板)
- [ ] 实现 F2-F5 (数据导出)
- [ ] 测试报告生成
- [ ] 优化性能

### Sprint 9: API 与集成 (2天)

- [ ] 创建 REST API 端点
- [ ] 编写 API 文档
- [ ] 前端集成测试

### Sprint 10: 优化与文档 (2天)

- [ ] 性能优化
- [ ] 完整性测试
- [ ] 编写用户文档和开发文档

---

**总计**: ~26人天 工作量，约 5-6 周完成所有功能

---

**版本**: 1.0
**最后更新**: 2025-11-04
**状态**: 规格确认中
