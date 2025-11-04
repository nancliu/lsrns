# SUMO EdgeData 分析综合指南

## 1. EdgeData 配置方法

### 1.1 配置文件结构

EdgeData 是 SUMO 的边级流量数据聚合输出，通过在 Additional 文件中配置来启用。

#### 基础配置模板 (edgeData.add.xml)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<additional>
    <edgeData
        id="ed1"
        freq="300"
        file="edgedata/edgedata.xml"
        excludeEmpty="true"
        withInternal="false"
    />
</additional>
```

### 1.2 关键配置参数

| 参数 | 类型 | 范围 | 说明 | 示例 |
|------|------|------|------|------|
| **id** | 字符串 | - | 唯一标识符 | "ed1" |
| **freq** | 整数 | 1-∞ | 采集间隔（秒） | 300（5分钟） |
| **file** | 路径 | - | 输出文件路径 | "edgedata/edgedata.xml" |
| **edges** | 列表 | - | 指定边（空表示全部） | "-8712 -15452.627" |
| **excludeEmpty** | 布尔值 | true/false | 排除无流量边 | true |
| **withInternal** | 布尔值 | true/false | 包含内部边 | false |
| **period** | 整数 | - | 可选，指定聚合周期 | 600 |
| **type** | 字符串 | - | 可选，输出类型 | 默认为基础流量 |

### 1.3 高级配置选项

#### 选项1：自定义边列表
```xml
<edgeData id="custom_edges"
    freq="300"
    file="edgedata_custom.xml"
    edges="-8712 -15452.627 8750.0 8750.1"
    excludeEmpty="true"/>
```

#### 选项2：仅关键路段
```xml
<edgeData id="highway_only"
    freq="300"
    file="edgedata_highway.xml"
    excludeEmpty="true"/>
```

#### 选项3：排放数据输出
```xml
<edgeData id="emission_data"
    type="emissions"
    freq="300"
    file="edgedata_emissions.xml"
    excludeEmpty="true"/>
```

#### 选项4：噪声数据输出
```xml
<edgeData id="noise_data"
    type="harmonoise"
    freq="300"
    file="edgedata_noise.xml"
    excludeEmpty="true"/>
```

### 1.4 在 sumocfg 中的集成方式

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <input>
        <net-file value="network.net.xml"/>
        <route-files value="routes.rou.xml"/>
        <additional-files value="edgeData.add.xml"/>
    </input>

    <output>
        <!-- 其他输出配置 -->
    </output>

    <time>
        <begin value="0"/>
        <end value="3600"/>
    </time>
</configuration>
```

---

## 2. EdgeData 输出结果内容

### 2.1 XML 输出文件结构

```xml
<?xml version="1.0" encoding="UTF-8"?>
<meandata>
    <interval begin="0" end="300" id="ed1">
        <edge id="-8712"
              sampledSeconds="2145.67"
              traveltime="45.23"
              density="12.34"
              occupancy="0.156"
              waitingTime="234.5"
              speed="8.5"
              departed="0"
              arrived="45"
              entered="48"
              left="48"
              laneChangedFrom="2"
              laneChangedTo="3"
              speedRelative="0.42"/>

        <edge id="-15452.627"
              sampledSeconds="1856.45"
              traveltime="52.1"
              density="9.87"
              occupancy="0.118"
              waitingTime="145.3"
              speed="7.2"
              departed="0"
              arrived="38"
              entered="42"
              left="42"
              laneChangedFrom="1"
              laneChangedTo="1"
              speedRelative="0.36"/>
    </interval>

    <interval begin="300" end="600" id="ed1">
        <!-- 下一个时间间隔的数据 -->
    </interval>
</meandata>
```

### 2.2 核心数据属性详解

#### 流量相关指标
| 属性 | 单位 | 说明 | 计算方式 |
|------|------|------|--------|
| **entered** | 辆 | 进入边的车辆数 | ∑（驶入该边的车） |
| **left** | 辆 | 离开边的车辆数 | ∑（驶出该边的车） |
| **departed** | 辆 | 在边内出发的车辆数 | ∑（从该边起点出发的车） |
| **arrived** | 辆 | 在边内到达的车辆数 | ∑（到达该边终点的车） |

#### 速度相关指标
| 属性 | 单位 | 说明 | 范围 |
|------|------|------|------|
| **speed** | m/s | 平均速度 | 0-50 |
| **speedRelative** | 无量纲 | 速度相对于最高限速的比例 | 0-1 |
| **traveltime** | 秒 | 平均通过时间 | 0-∞ |

#### 密度与占用相关
| 属性 | 单位 | 说明 | 范围 |
|------|------|------|------|
| **density** | 车/km | 车辆密度 | 0-150 |
| **occupancy** | 无量纲 | 车道占用率 | 0-1 |
| **sampledSeconds** | 秒 | 采样总秒数（车辆数×存在时间） | 0-∞ |

#### 拥堵相关指标
| 属性 | 单位 | 说明 | 说明 |
|------|------|------|------|
| **waitingTime** | 秒 | 等待总时长 | 停止时间总和 |

#### 车道变更
| 属性 | 单位 | 说明 |
|------|------|------|
| **laneChangedFrom** | 辆 | 从该边变更出去的车 |
| **laneChangedTo** | 辆 | 变更进入该边的车 |

### 2.3 数据行为特性

#### freq 参数的影响
- `freq="300"`: 每5分钟生成一个 interval
- `freq="600"`: 每10分钟生成一个 interval
- 每个 interval 的持续时间等于 freq 值

#### excludeEmpty 的影响
| excludeEmpty | 无流量边 | 数据量 | 分析影响 |
|--------------|---------|--------|---------|
| true | 排除 | 小（仅活跃边） | 更清晰的拥堵识别 |
| false | 包含 | 大（全部边） | 完整的覆盖范围 |

### 2.4 实际输出示例

对于10小时仿真，freq=300（5分钟）：
- 总 interval 数: 120 (10×60÷5)
- 每个 interval 包含: 活跃边数（通常200-500条）
- 总记录数: ~30,000 条

---

## 3. 第二层批量仿真分析功能设计

### 3.1 分析架构

```
┌─────────────────────────────────────┐
│  第一层：单次仿真 EdgeData 输出      │
│  (已有: edgedata_analysis.py)       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  第二层：批量仿真对比分析（新增）     │
│  - 多仿真对比                       │
│  - 时空演变分析                     │
│  - 控制策略评估                     │
│  - 优化效果量化                     │
└──────────────────────────────────────┘
```

### 3.2 功能单 (Feature List)

#### **分析功能分类**

##### A. 批量对比分析 (Batch Comparison Analysis)

| 功能ID | 功能名称 | 优先级 | 输入 | 输出 | 工作量(天) |
|--------|---------|--------|------|------|-----------|
| **F2-A1** | 多方案流量对比 | P0 | 2+个仿真 | 对比图表、差异热力图 | 2 |
| **F2-A2** | 多方案速度分析 | P0 | 2+个仿真 | 速度CDF曲线、区间对比 | 2 |
| **F2-A3** | 多方案拥堵指数对比 | P0 | 2+个仿真 | 拥堵时空分布、改善率 | 1.5 |
| **F2-A4** | 路段级效果评估 | P1 | 2+个仿真 | Top改善/恶化路段表 | 1.5 |
| **F2-A5** | 峰值时段对比 | P1 | 2+个仿真 | 峰值移动分析、容量对标 | 1.5 |

##### B. 时空演变分析 (Spatial-Temporal Analysis)

| 功能ID | 功能名称 | 优先级 | 输入 | 输出 | 工作量(天) |
|--------|---------|--------|------|------|-----------|
| **F2-B1** | 拥堵扩散过程 | P0 | 单/多仿真 | 时间序列热力图、扩散动画 | 3 |
| **F2-B2** | 流量波传播 | P1 | 单/多仿真 | 时空图(xt图)、波速测算 | 2.5 |
| **F2-B3** | 速度梯度分析 | P1 | 单/多仿真 | 速度梯度热力图、临界点 | 2 |
| **F2-B4** | 路网连锁效应 | P2 | 多仿真 | 关键路段流量传递图、影响范围 | 2.5 |

##### C. 控制策略评估 (Control Strategy Evaluation)

| 功能ID | 功能名称 | 优先级 | 输入 | 输出 | 工作量(天) |
|--------|---------|--------|------|------|-----------|
| **F2-C1** | VSS策略效果评估 | P0 | Baseline+VSS方案 | 改善率报告、目标达成度 | 2 |
| **F2-C2** | TEC策略效果评估 | P0 | Baseline+TEC方案 | 匝道流量、主线流量变化 | 2 |
| **F2-C3** | DHS策略效果评估 | P0 | Baseline+DHS方案 | 硬路肩利用率、容量增加量 | 2 |
| **F2-C4** | 协调控制评估 | P1 | Baseline+多策略 | 协调效果、冲突分析 | 2.5 |
| **F2-C5** | 关键指标提升量化 | P0 | 任意2方案 | 速度提升、延误减少、通行能力 | 2 |

##### D. 优化效果量化 (Optimization Quantification)

| 功能ID | 功能名称 | 优先级 | 输入 | 输出 | 工作量(天) |
|--------|---------|--------|------|------|-----------|
| **F2-D1** | 关键路段优化度量 | P0 | 2+仿真 | 路段效率指数、排名矩阵 | 1.5 |
| **F2-D2** | 全网效率评估 | P0 | 2+仿真 | 网络效率指数、通勤指数 | 2 |
| **F2-D3** | 成本-效益分析 | P1 | 控制方案+成本数据 | ROI分析、成本有效性 | 2.5 |
| **F2-D4** | 环境影响评估 | P2 | 2+仿真(含排放) | 排放量对比、环保收益 | 2.5 |
| **F2-D5** | 可靠性评估 | P2 | 多仿真+扰动数据 | 鲁棒性指标、风险评估 | 3 |

##### E. 高级分析 (Advanced Analytics)

| 功能ID | 功能名称 | 优先级 | 输入 | 输出 | 工作量(天) |
|--------|---------|--------|------|------|-----------|
| **F2-E1** | 拥堵识别与分类 | P1 | EdgeData | 拥堵类型、根因分析 | 2 |
| **F2-E2** | 瓶颈识别 | P1 | EdgeData | 瓶颈排名、容量不足度 | 2 |
| **F2-E3** | 缓解措施有效性排序 | P1 | 多方案 | 措施排序、协同效应 | 2.5 |
| **F2-E4** | 时间序列预测 | P2 | 历史EdgeData | 流量预报、拥堵预警 | 3 |

##### F. 报告与可视化 (Reporting & Visualization)

| 功能ID | 功能名称 | 优先级 | 输入 | 输出 | 工作量(天) |
|--------|---------|--------|------|------|-----------|
| **F2-F1** | 批量分析综合报告 | P0 | 所有分析结果 | HTML报告、总结表格 | 2 |
| **F2-F2** | 方案对比仪表板 | P0 | 多方案数据 | 实时交互仪表板 | 3 |
| **F2-F3** | 地图可视化 | P1 | EdgeData+网络 | 流量热力图、速度着色 | 3 |
| **F2-F4** | 动态演动画 | P2 | EdgeData时间序列 | MP4/GIF动画、时间条 | 3.5 |
| **F2-F5** | 数据导出与API | P1 | 所有分析结果 | CSV/JSON导出、REST API | 2.5 |

---

## 4. 详细功能规格

### 4.1 核心优先级功能详解

#### **F2-A1: 多方案流量对比** (Priority: P0)

**目的**: 对比不同控制方案的流量改变

**输入数据**:
- 2个或以上仿真的 EdgeData XML 文件
- 仿真标识信息（名称、方案描述）

**处理逻辑**:
```python
def compare_flow_across_scenarios(scenario_edgedatas: Dict[str, EdgeData]) -> Dict:
    """
    比较多个方案的流量指标

    输出：
    - overall_flow_stats: 全网流量统计对比
    - edge_flow_diff: 路段级流量差异矩阵
    - top_improved_edges: Top 10 流量改善路段
    - top_degraded_edges: Top 10 流量恶化路段
    - flow_distribution: 流量分布直方图对比
    """
```

**输出格式**:
- 表格: 全网平均流量、最大流量、标准差对比
- 热力图: 路段级流量改变（相对改变率%）
- 柱状图: Top改善/恶化路段排名

**成功标准**:
- ✓ 支持2-10个方案同时对比
- ✓ 准确计算流量改变率
- ✓ 生成可视化对比图表

---

#### **F2-C1: VSS策略效果评估** (Priority: P0)

**目的**: 量化可变限速（VSS）策略的有效性

**输入数据**:
- Baseline 方案 EdgeData
- VSS 方案 EdgeData
- VSS 配置信息（限速值、应用路段）

**处理逻辑**:
```python
def evaluate_vss_strategy(baseline: EdgeData, vss: EdgeData,
                         vss_config: Dict) -> Dict:
    """
    评估VSS策略效果

    关键指标：
    1. 速度改善: (vss.speed - baseline.speed) / baseline.speed
    2. 拥堵缓解: (baseline.waitingTime - vss.waitingTime) / baseline.waitingTime
    3. 通行能力: (vss.entered - baseline.entered) / baseline.entered
    4. 安全性: 速度均匀性指标

    输出：
    - effectiveness_score: 0-100分
    - target_achievement: 是否达到KPI目标
    - cost_benefit: 成本效益比
    """
```

**输出格式**:
- 评分卡: 目标达成度（速度、延误、通行能力）
- 对比图: 时间序列对比、分布对比
- 报告: 定性效果分析

**成功标准**:
- ✓ 通过F2-A1和F2-A2获得数据基础
- ✓ 计算与目标的距离
- ✓ 给出效果评价和建议

---

#### **F2-D1: 关键路段优化度量** (Priority: P0)

**目的**: 识别和量化关键路段的优化效果

**输入数据**:
- 多方案 EdgeData
- 路段重要性指标（通过量）

**关键算法**:
```python
def calculate_route_segment_efficiency(edgedatas: Dict[str, EdgeData]) -> Dict:
    """
    计算路段效率指数

    效率指数 = (速度 / 最高限速) × (通行能力 / 容量) × (1 - 拥堵指数)

    输出路段排序、效率矩阵、改善优先级
    """
```

**输出**:
- 路段效率排序表（按优化幅度）
- 效率矩阵（方案×路段）
- Top改善路段的详细分析

---

#### **F2-B1: 拥堵扩散过程分析** (Priority: P0)

**目的**: 可视化拥堵在路网中的时空演变过程

**处理方式**:
```
时间轴 → 生成热力图序列
  │
  ├─ T=0min:    初始状态
  ├─ T=30min:   扩散过程1
  ├─ T=60min:   扩散过程2
  ├─ T=90min:   峰值状态
  └─ T=120min:  缓解过程
```

**输出**:
- 时间序列热力图（PNG序列）
- XT图（时间-空间图）
- 拥堵传播速度分析

---

### 4.2 依赖关系与实现顺序

```
┌─────────────────────────────────────┐
│ 基础工具层 (Week 1)                 │
├─ F2-A1: 多方案流量对比              │
├─ F2-A2: 多方案速度分析              │
├─ F2-D1: 关键路段优化度量            │
└─────────────────────────────────────┘
           │ (依赖)
┌──────────▼─────────────────────────┐
│ 控制评估层 (Week 2)                 │
├─ F2-C1: VSS策略评估 (基于F2-A1/A2) │
├─ F2-C2: TEC策略评估 (基于F2-A1/A2) │
├─ F2-C3: DHS策略评估 (基于F2-A1/A2) │
└─────────────────────────────────────┘
           │ (依赖)
┌──────────▼─────────────────────────┐
│ 高级分析层 (Week 3)                 │
├─ F2-B1: 拥堵扩散过程 (基于EdgeData) │
├─ F2-E1: 拥堵识别与分类              │
├─ F2-E2: 瓶颈识别                    │
└─────────────────────────────────────┘
```

---

## 5. 数据流架构

```
多仿真结果 (Baseline + 方案1 + 方案2 + ...)
    │
    ├─→ EdgeData XML 解析 ─────────────┐
    │                                  │
    ├─→ 基础统计计算 ─────────────────┤
    │   (流量、速度、密度、拥堵)       │
    │                                  │
    ├─→ 对比分析 (F2-A系列)           │
    │   - 时间序列对比                 │
    │   - 分布对比                     │
    │   - 路段差异                     │
    │                                  │
    ├─→ 策略评估 (F2-C系列)           │
    │   - 效果量化                     │
    │   - KPI评估                      │
    │   - 改善率计算                   │
    │                                  │
    ├─→ 时空分析 (F2-B系列)           │
    │   - 热力图生成                   │
    │   - 扩散过程                     │
    │   - 动画渲染                     │
    │                                  │
    └─→ 报告生成 (F2-F系列)
        - HTML报告 + 图表
        - 导出数据 (CSV/JSON)
        - 仪表板展示
```

---

## 6. 技术实现建议

### 6.1 核心模块设计

```python
# shared/analysis_tools/batch_edgedata_analysis.py

class BatchEdgeDataAnalysis:
    """批量EdgeData分析器"""

    def __init__(self):
        self.scenarios = {}  # scenario_name -> EdgeData
        self.baseline = None
        self.results = {}

    # 对比分析
    def compare_flow(self) -> Dict:
        """F2-A1: 流量对比"""

    def compare_speed(self) -> Dict:
        """F2-A2: 速度对比"""

    def compare_congestion(self) -> Dict:
        """F2-A3: 拥堵对比"""

    # 策略评估
    def evaluate_vss_strategy(self, vss_edges: List[str]) -> Dict:
        """F2-C1: VSS效果评估"""

    def evaluate_tec_strategy(self, ramp_edges: List[str]) -> Dict:
        """F2-C2: TEC效果评估"""

    # 时空分析
    def analyze_congestion_propagation(self) -> Dict:
        """F2-B1: 拥堵扩散"""

    def generate_heatmap_sequence(self, metric: str) -> List[str]:
        """生成热力图序列"""

    # 报告生成
    def generate_comparison_report(self) -> str:
        """F2-F1: 综合报告"""
```

### 6.2 数据库和缓存策略

```python
# 使用内存缓存加速多次查询
cache = {
    'edgedata_df': pd.DataFrame,      # 原始数据缓存
    'temporal_agg': Dict[time, stats], # 时间聚合缓存
    'spatial_agg': Dict[edge, stats],  # 空间聚合缓存
}
```

### 6.3 性能考虑

- **大数据处理**: 使用 Dask 处理超过内存的数据
- **并行计算**: 多方案对比并行化
- **渐进式渲染**: 报告分块生成，避免超时

---

## 7. 实现时间线

| 阶段 | 功能 | 时间 | 人力 |
|------|------|------|------|
| **Phase 1** | F2-A1/A2/D1 (基础对比) | 1周 | 1人 |
| **Phase 2** | F2-C1/C2/C3 (策略评估) | 1.5周 | 1人 |
| **Phase 3** | F2-B1 (时空分析) | 1周 | 1人 |
| **Phase 4** | F2-E1/E2 (高级分析) | 1.5周 | 1人 |
| **Phase 5** | F2-F1/F2/F3 (报告可视化) | 1周 | 1人 |
| **总计** | 完整第二层分析 | **5.5周** | **5人周** |

---

## 8. 参考资源

- SUMO EdgeData 官方文档: https://github.com/eclipse-sumo/sumo
- 本项目 EdgeData 实现: [shared/analysis_tools/edgedata_analysis.py](../../shared/analysis_tools/edgedata_analysis.py)
- API 服务: [api/services/edgedata_service.py](../../api/services/edgedata_service.py)

---

**文档版本**: v1.0
**最后更新**: 2025-11-04
**作者**: AI Assistant
**状态**: Draft
