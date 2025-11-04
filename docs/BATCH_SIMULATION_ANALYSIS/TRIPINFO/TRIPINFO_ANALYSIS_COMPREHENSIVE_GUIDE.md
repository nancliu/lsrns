# SUMO TripInfo 分析综合指南

## 1. TripInfo 配置方法

### 1.1 配置文件结构

TripInfo 是 SUMO 输出的车辆行程信息，记录每辆车从出发到到达的完整旅程统计。

#### 基础配置模板 (sumocfg)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <input>
        <net-file value="network.net.xml"/>
        <route-files value="routes.rou.xml"/>
    </input>

    <output>
        <!-- 启用 TripInfo 输出 -->
        <tripinfo-output value="tripinfo.xml"/>
    </output>

    <time>
        <begin value="0"/>
        <end value="3600"/>
    </time>
</configuration>
```

### 1.2 关键配置参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| **tripinfo-output** | 路径 | TripInfo输出文件路径 | "tripinfo.xml" |
| **device.tripinfo.probability** | 0-1 | 记录概率（默认1.0全记录） | 1.0 |
| **device.tripinfo.explicit** | 列表 | 明确指定记录的车ID | "veh1,veh2" |
| **personinfo-output** | 路径 | 行人信息输出（可选） | "personinfo.xml" |
| **containerinfo-output** | 路径 | 货柜信息输出（可选） | "containerinfo.xml" |

### 1.3 高级配置选项

#### 选项1：仅记录特定车辆
```xml
<!-- 在vehicle或flow定义中 -->
<param key="has.tripinfo.device" value="true"/>
```

#### 选项2：按概率采样（大规模仿真）
```bash
sumo --route-files routes.rou.xml \
     --tripinfo-output tripinfo.xml \
     --device.tripinfo.probability 0.1  # 10%采样率
```

#### 选项3：记录人员和货柜
```xml
<output>
    <tripinfo-output value="tripinfo.xml"/>
    <personinfo-output value="personinfo.xml"/>
    <containerinfo-output value="containerinfo.xml"/>
</output>
```

#### 选项4：记录排放数据
```xml
<vehicle id="veh1" depart="0" type="car" route="route1">
    <param key="has.emissions.device" value="true"/>
</vehicle>
```

#### 选项5：记录电池状态（电动车）
```xml
<vehicle id="ev1" depart="0" type="electric_car" route="route1">
    <param key="has.battery.device" value="true"/>
</vehicle>
```

### 1.4 在项目中的集成

**当前配置位置**: `api/services/simulation_service.py` 中的 sumocfg 生成

**启用方式**: 通过 `output_tripinfo` 参数

```python
# 批量仿真中的配置
{
    "output_config": {
        "output_tripinfo": true,      # 启用
        "output_vehroute": true,
        "output_edgedata": true
    }
}
```

---

## 2. TripInfo 输出结果内容

### 2.1 XML 输出文件结构

```xml
<?xml version="1.0" encoding="UTF-8"?>
<tripinfos>
    <tripinfo
        id="veh_0"                          <!-- 车辆ID -->
        depart="100.00"                     <!-- 出发时间 (秒) -->
        departLane="0"                      <!-- 出发车道 -->
        departPos="0.00"                    <!-- 出发位置 (米) -->
        departSpeed="0.00"                  <!-- 出发速度 (m/s) -->
        departDelay="0.00"                  <!-- 出发延误 (秒) -->
        arrival="1850.50"                   <!-- 到达时间 (秒) -->
        arrivalLane="2"                     <!-- 到达车道 -->
        arrivalPos="500.00"                 <!-- 到达位置 (米) -->
        arrivalSpeed="8.50"                 <!-- 到达速度 (m/s) -->
        duration="1750.50"                  <!-- 总行程时间 (秒) -->
        routeLength="45230.00"              <!-- 路线长度 (米) -->
        waitingTime="180.25"                <!-- 等待时间 (秒) -->
        waitingCount="3"                    <!-- 停止次数 -->
        stopTime="240.00"                   <!-- 停止总时长 (秒) -->
        timeLoss="520.50"                   <!-- 时间损失 (秒) -->
        type="passenger_car"
        vType="car"
        routeValid="1">                     <!-- 路线是否有效 -->

        <!-- 可选: 排放数据 -->
        <emissions
            CO_abs="150.5"                  <!-- CO (mg) -->
            CO2_abs="1240000.0"             <!-- CO2 (mg) -->
            HC_abs="25.3"                   <!-- HC (mg) -->
            PMx_abs="8.5"                   <!-- PMx (mg) -->
            NOx_abs="120.0"                 <!-- NOx (mg) -->
            fuel_abs="420.5"/>              <!-- 燃油 (mg) -->

        <!-- 可选: 电池数据 -->
        <battery
            depleted="0"                    <!-- 电池耗尽次数 -->
            actualBatteryCapacity="85.5"    <!-- 最终电量 (%) -->
            totalEnergyConsumed="12.5"      <!-- 消耗能量 (kWh) -->
            totalEnergyRegenerated="2.3"/>  <!-- 回收能量 (kWh) -->

        <!-- 可选: 出租车数据 -->
        <taxi
            customers="5"                   <!-- 服务客户数 -->
            occupiedDistance="6748.77"      <!-- 载客距离 (米) -->
            occupiedTime="595.00"/>         <!-- 载客时间 (秒) -->

    </tripinfo>

    <tripinfo id="veh_1" depart="150.00" ... />
    <!-- 更多车辆... -->

</tripinfos>
```

### 2.2 核心数据属性详解

#### 时间相关指标
| 属性 | 单位 | 说明 | 范围 |
|------|------|------|------|
| **depart** | 秒 | 车辆出发时间 | 0-∞ |
| **arrival** | 秒 | 车辆到达时间 | 0-∞ |
| **duration** | 秒 | 总行程时间 = arrival - depart | 0-∞ |
| **waitingTime** | 秒 | 被动等待时间（车辆停止） | 0-∞ |
| **stopTime** | 秒 | 计划停止时间总和 | 0-∞ |
| **departDelay** | 秒 | 出发延误（希望出发时间 vs 实际） | -∞-∞ |

#### 距离和速度
| 属性 | 单位 | 说明 | 范围 |
|------|------|------|------|
| **routeLength** | 米 | 行驶的路线总长 | 0-∞ |
| **departSpeed** | m/s | 出发时速度 | 0-50 |
| **arrivalSpeed** | m/s | 到达时速度 | 0-50 |

#### 效率指标
| 属性 | 单位 | 说明 | 范围 |
|------|------|------|------|
| **timeLoss** | 秒 | 因拥堵增加的时间 (实际-自由流时间) | 0-∞ |
| **waitingCount** | 次 | 车辆停止次数 | 0-∞ |

#### 可选指标
| 属性 | 单位 | 说明 | 范围 |
|------|------|------|------|
| **CO_abs** | mg | 一氧化碳排放 | 0-∞ |
| **CO2_abs** | mg | 二氧化碳排放 | 0-∞ |
| **fuel_abs** | mg | 燃油消耗 | 0-∞ |

### 2.3 派生指标计算

**效率评分**:
```
效率评分 = routeLength / (duration × avg_speed)
```

**延误比例**:
```
延误比 = timeLoss / (duration - waitingTime)
```

**平均速度**:
```
平均速度 = routeLength / duration
```

**停止频率**:
```
停止频率 = waitingCount / (routeLength / 1000)  # 每km停止次数
```

### 2.4 行人和货柜信息（可选）

#### 行人信息 (personinfo.xml)
```xml
<personinfo id="person0" depart="0.00">
    <walk
        depart="0.00"
        arrival="47.00"
        arrivalPos="55.00"
        duration="47.00"
        routeLength="40.5"/>

    <ride
        waitingTime="74.00"
        vehicle="train0"
        depart="121.00"
        arrival="140.00"
        arrivalPos="92.00"
        duration="19.00"/>

    <stop
        duration="20.00"
        arrival="160.00"
        arrivalPos="45.00"
        actType="singing"/>
</personinfo>
```

#### 货柜信息 (containerinfo.xml)
```xml
<containerinfo id="container0" depart="0.00">
    <tranship
        depart="0.00"
        arrival="54.00"
        arrivalPos="55.00"/>

    <transport
        waitingTime="103.00"
        vehicle="truck0"
        depart="157.00"
        arrival="176.00"
        arrivalPos="92.00"/>
</containerinfo>
```

---

## 3. 第二层批量仿真分析功能设计

### 3.1 分析架构

```
┌─────────────────────────────────────┐
│  第一层：单次仿真 TripInfo 输出     │
│  (简单统计: 平均时间、延误等)       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  第二层：批量仿真对比分析（新增）    │
│  - 多仿真对比                       │
│  - 时间序列演变                     │
│  - 控制策略评估                     │
│  - 出行行为分析                     │
│  - OD对分析                         │
│  - 环保与经济评估                   │
└──────────────────────────────────────┘
```

### 3.2 功能单 (Feature List)

#### **分析功能分类**

##### A. 批量对比分析 (Batch Comparison)

| 功能ID | 功能名称 | 优先级 | 输入 | 输出 | 工作量(天) |
|--------|---------|--------|------|------|-----------|
| **G2-A1** | 多方案出行时间对比 | P0 | 2+仿真 | 时间对比、分布、差异 | 2 |
| **G2-A2** | 多方案延误分析 | P0 | 2+仿真 | 延误改善率、分布 | 1.5 |
| **G2-A3** | 多方案停止频率对比 | P0 | 2+仿真 | 停止次数、等待时间 | 1.5 |
| **G2-A4** | 多方案排放对比 | P1 | 2+仿真 | CO2/NOx/PM等排放量对比 | 2 |
| **G2-A5** | 多方案通行能力评估 | P1 | 2+仿真 | 吞吐量、容量利用率 | 1.5 |

##### B. 时间序列与出行模式 (Temporal & Pattern)

| 功能ID | 功能名称 | 优先级 | 输入 | 输出 | 工作量(天) |
|--------|---------|--------|------|------|-----------|
| **G2-B1** | 出发-到达时间关系分析 | P0 | 单/多仿真 | 出发时间vs到达时间散点图 | 1.5 |
| **G2-B2** | 出行时间分布演变 | P1 | 单仿真 | 时间序列热力图、CDF曲线 | 2 |
| **G2-B3** | 拥堵衍生指标分析 | P1 | 单仿真 | 时间损失、等待时间分布 | 1.5 |
| **G2-B4** | 出行链分析 | P2 | 多仿真 | 车辆出行特征聚类、分类 | 2.5 |

##### C. 控制策略评估 (Strategy Evaluation)

| 功能ID | 功能名称 | 优先级 | 输入 | 输出 | 工作量(天) |
|--------|---------|--------|------|------|-----------|
| **G2-C1** | 出行时间改善评估 | P0 | Baseline+策略 | 改善率、达成度 | 2 |
| **G2-C2** | 延误减少评估 | P0 | Baseline+策略 | 延误改善、人小时减少 | 1.5 |
| **G2-C3** | 排放减少评估 | P1 | Baseline+策略 | CO2/NOx减少量、环保收益 | 2 |
| **G2-C4** | 公平性评估 | P1 | Baseline+策略 | 不同出发时间/路线的收益均衡 | 2 |

##### D. OD对与走廊分析 (OD Corridor)

| 功能ID | 功能名称 | 优先级 | 输入 | 输出 | 工作量(天) |
|--------|---------|--------|------|------|-----------|
| **G2-D1** | 主要OD对识别 | P0 | TripInfo+TAZ | OD流量矩阵、排序 | 1.5 |
| **G2-D2** | OD走廊分析 | P1 | TripInfo+网络 | 走廊拥堵特征、改善机会 | 2.5 |
| **G2-D3** | OD对效率评估 | P1 | 2+仿真 | OD对延误对比、改善优先级 | 2 |
| **G2-D4** | 出行走廊协调分析 | P2 | 多仿真 | 走廊间的相互影响 | 2.5 |

##### E. 高级分析 (Advanced Analytics)

| 功能ID | 功能名称 | 优先级 | 输入 | 输出 | 工作量(天) |
|--------|---------|--------|------|------|-----------|
| **G2-E1** | 出行者行为分析 | P1 | 多仿真 | 路线选择稳定性、反应模式 | 2 |
| **G2-E2** | 拥堵成本评估 | P1 | TripInfo | 时间价值成本、经济损失 | 2 |
| **G2-E3** | 公共交通效率分析 | P2 | TripInfo（公交） | 上车率、准点率、服务质量 | 2.5 |
| **G2-E4** | 走廊容量与瓶颈 | P2 | 多仿真 | 容量分析、瓶颈定位、改善建议 | 2.5 |

##### F. 报告与可视化 (Reporting & Visualization)

| 功能ID | 功能名称 | 优先级 | 输入 | 输出 | 工作量(天) |
|--------|---------|--------|------|------|-----------|
| **G2-F1** | 批量分析综合报告 | P0 | 所有分析结果 | HTML报告、汇总表格 | 2 |
| **G2-F2** | OD走廊地图展示 | P1 | OD数据+网络 | 交互式地图、流量着色 | 2.5 |
| **G2-F3** | 时间序列可视化 | P1 | TripInfo | 出发-到达关系图、CDF曲线 | 2 |
| **G2-F4** | 仪表板与对比工具 | P1 | 多仿真 | 实时交互仪表板 | 3 |

---

## 4. 详细功能规格

### 4.1 核心优先级功能详解

#### **G2-A1: 多方案出行时间对比** (Priority: P0)

**目的**: 对比不同控制方案的出行时间改变

**输入数据**:
- 2个或以上仿真的 TripInfo XML 文件
- 方案标识信息（名称、描述）

**处理逻辑**:
```python
def compare_travel_time_across_scenarios(scenario_tripinfos: Dict[str, pd.DataFrame]) -> Dict:
    """
    比较多个方案的出行时间指标

    关键指标:
    - 平均出行时间 (duration)
    - 出行时间分布 (percentiles: 10%, 50%, 90%)
    - 出行时间改善率 (%)
    - 出行时间可靠性 (std, CV)
    - 迟到率 (delay > threshold)

    输出:
    - overall_stats: 全方案对比
    - distribution_stats: 分布对比
    - reliability_index: 可靠性指数
    - top_improved_routes: 改善最多的路线
    - top_degraded_routes: 恶化的路线
    """
```

**输出格式**:
- 表格: 平均时间、分位数、改善率对比
- 箱线图: 多方案出行时间分布
- 柱状图: 改善率排序

**成功标准**:
- ✓ 支持2-10个方案同时对比
- ✓ 时间计算准确度 ≥99%
- ✓ 生成完整的统计对比

---

#### **G2-A2: 多方案延误分析** (Priority: P0)

**目的**: 量化拥堵引起的时间延误改善

**处理逻辑**:
```python
def compare_delay_metrics(scenarios: Dict[str, pd.DataFrame]) -> Dict:
    """
    比较多方案的延误指标

    延误 = timeLoss (因拥堵增加的时间)
    或 = departDelay (出发延误)

    输出:
    {
        "overall_delay_stats": {
            "baseline": {avg: 180.5, median: 150, std: 120, max: 2100},
            "scenario_1": {...}
        },
        "delay_reduction": {
            "scenario_1": {absolute: 85.5, percentage: 47.4}
        },
        "distribution": {
            "no_delay": 45,      # %
            "light_delay": 35,
            "moderate_delay": 15,
            "severe_delay": 5
        }
    }
    """
```

**关键指标**:
- 平均延误 (秒)
- 延误减少幅度 (%)
- 人小时延误总和 (车×小时)
- 延误率分布

---

#### **G2-D1: 主要OD对识别** (Priority: P0)

**目的**: 识别网络中的主要出行走廊

**处理逻辑**:
```python
def identify_major_od_pairs(tripinfo_df: pd.DataFrame, taz_file: str) -> Dict:
    """
    识别和排序主要OD对

    从 TAZ (Traffic Analysis Zone) 出发和到达位置计算OD对

    输出:
    {
        "od_matrix": {
            shape: (zones, zones),
            values: flow counts
        },
        "top_od_pairs": [
            {origin: "TAZ_1", destination: "TAZ_2", volume: 450, pct: 5.2},
            ...
        ],
        "od_characteristics": {
            "avg_travel_time": {...},
            "avg_delay": {...},
            "congestion_level": {...}
        }
    }
    """
```

---

#### **G2-C1: 出行时间改善评估** (Priority: P0)

**目的**: 量化策略对出行时间的改善效果

**处理逻辑**:
```python
def evaluate_travel_time_improvement(baseline: pd.DataFrame,
                                    strategy: pd.DataFrame) -> Dict:
    """
    评估策略的出行时间改善

    关键指标:
    1. 平均出行时间改善: (baseline_avg - strategy_avg) / baseline_avg × 100%
    2. 可靠性改善: (baseline_std - strategy_std) / baseline_std × 100%
    3. 迟到率改善: (baseline_late_pct - strategy_late_pct)
    4. 人小时改善: Σ改善 / 总人数

    输出:
    {
        "effectiveness": {
            "score": 0-100,
            "rating": "优秀/有效/边际"
        },
        "improvements": {
            "avg_time_reduction": 180.5,  # 秒
            "reduction_percentage": 22.5,  # %
            "reliability_improvement": 35.0,
            "people_hours_saved": 450
        },
        "distribution_shift": {
            "faster_routes_pct": 65,
            "stable_routes_pct": 25,
            "slower_routes_pct": 10
        }
    }
    """
```

---

### 4.2 依赖关系与实现顺序

```
基础工具层 (Week 1-2):
├─ G2-A1: 多方案出行时间对比
├─ G2-A2: 多方案延误分析
├─ G2-D1: 主要OD对识别
└─ G2-B1: 出发-到达时间关系
     ↓ (依赖)
对比评估层 (Week 2-3):
├─ G2-C1: 出行时间改善评估
├─ G2-C2: 延误减少评估
├─ G2-A3: 停止频率对比
└─ G2-A5: 通行能力评估
     ↓ (依赖)
高级分析层 (Week 3-4):
├─ G2-D2: OD走廊分析
├─ G2-D3: OD对效率评估
├─ G2-B2: 出行时间分布演变
└─ G2-E1: 出行者行为分析
     ↓ (依赖)
报告与展示 (Week 4+):
├─ G2-F1: 综合报告
├─ G2-F2: OD走廊地图
├─ G2-F3: 时间序列可视化
└─ G2-F4: 交互仪表板
```

---

## 5. 数据流架构

```
多仿真 TripInfo XML + TAZ 文件
    │
    ├─→ 数据加载与验证
    │   - 解析XML
    │   - 关联TAZ
    │   - 数据清洗
    │
    ├─→ 基础统计计算
    │   - 时间指标
    │   - 距离指标
    │   - 排放指标
    │
    ├─→ 对比分析 (G2-A系列)
    │   - 时间对比
    │   - 延误对比
    │   - 停止对比
    │
    ├─→ OD分析 (G2-D系列)
    │   - OD矩阵
    │   - 走廊特征
    │   - 效率评估
    │
    ├─→ 策略评估 (G2-C系列)
    │   - 时间改善
    │   - 延误减少
    │   - 公平性评估
    │
    ├─→ 高级分析 (G2-E系列)
    │   - 行为分析
    │   - 成本评估
    │   - 容量分析
    │
    └─→ 报告生成 (G2-F系列)
        - HTML报告
        - 地图展示
        - 交互仪表板
```

---

## 6. 技术实现建议

### 6.1 核心模块设计

```python
# shared/analysis_tools/batch_tripinfo_analysis.py

class BatchTripInfoAnalysis:
    """批量TripInfo分析器"""

    def __init__(self):
        self.scenarios = {}      # scenario_name -> TripInfo DataFrame
        self.taz_mapping = {}    # 车辆ID -> TAZ映射
        self.results = {}

    # 对比分析
    def compare_travel_time(self) -> Dict:
        """G2-A1: 出行时间对比"""

    def compare_delays(self) -> Dict:
        """G2-A2: 延误对比"""

    def compare_stops(self) -> Dict:
        """G2-A3: 停止频率对比"""

    # OD分析
    def identify_od_pairs(self, taz_file: str) -> Dict:
        """G2-D1: OD对识别"""

    def analyze_od_corridors(self) -> Dict:
        """G2-D2: OD走廊分析"""

    # 策略评估
    def evaluate_travel_time_improvement(self, baseline: str, strategy: str) -> Dict:
        """G2-C1: 出行时间改善评估"""

    # 报告生成
    def generate_comparison_report(self) -> str:
        """G2-F1: 综合报告"""

    def generate_od_map_visualization(self) -> str:
        """G2-F2: OD地图"""
```

### 6.2 数据结构

```python
# TripInfo DataFrame 标准格式
tripinfo_df = pd.DataFrame({
    'id': str,              # 车辆ID
    'depart': float,        # 出发时间
    'arrival': float,       # 到达时间
    'duration': float,      # 出行时间
    'routeLength': float,   # 路线长度
    'waitingTime': float,   # 等待时间
    'waitingCount': int,    # 停止次数
    'timeLoss': float,      # 时间损失
    'departDelay': float,   # 出发延误
    'vType': str,           # 车型
    'origin_taz': str,      # 出发TAZ
    'destination_taz': str  # 到达TAZ
})

# OD矩阵格式
od_matrix = {
    'data': np.ndarray,     # (n_zones, n_zones)
    'zones': list,          # 区域ID列表
    'top_pairs': list       # 前K个OD对
}
```

### 6.3 性能考虑

- **大数据处理**: 使用 Dask/Pandas 处理大规模车辆数据
- **并行计算**: 多方案对比并行化
- **缓存策略**: 缓存OD矩阵计算结果
- **增量处理**: 支持流式处理大文件

---

## 7. 实现时间线

| 阶段 | 功能 | 时间 | 人力 |
|------|------|------|------|
| **Phase 1** | G2-A1/A2/D1/B1 (基础) | 1周 | 1人 |
| **Phase 2** | G2-C1/C2/A3/A5 (对比评估) | 1.5周 | 1人 |
| **Phase 3** | G2-D2/D3/B2/E1 (高级) | 1.5周 | 1人 |
| **Phase 4** | G2-F1/F2/F3/F4 (展示) | 1周 | 1人 |
| **总计** | 完整第二层分析 | **5周** | **5人周** |

---

## 8. 参考资源

- SUMO TripInfo 官方文档: https://github.com/eclipse-sumo/sumo
- 本项目批量仿真: `api/services/batch_optimization_service.py`
- TAZ配置: `templates/taz_files/`

---

**文档版本**: v1.0
**最后更新**: 2025-11-04
**作者**: AI Assistant
**状态**: Draft
