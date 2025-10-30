# SUMO输出配置建议 - 针对管控策略仿真

**文档版本**: v1.0
**创建日期**: 2025-10-29
**目标**: 为管控策略和批量仿真场景提供优化的SUMO输出配置方案

---

## 📋 执行摘要

本文档针对**管控策略仿真**（VSS/DHS/TEC）和**批量仿真**场景，提供SUMO输出配置的优化建议。核心原则：

1. ✅ **保留核心指标** - 确保策略效果评估的数据完整性
2. ✅ **控制输出规模** - 批量仿真时最小化文件大小和I/O开销
3. ✅ **聚焦管控区域** - 仅监测策略影响的关键路段
4. ✅ **时间粒度优化** - 根据管控时间段调整采样频率

---

## 1. 输出类型分析与建议

### 1.1 Summary Output ⭐⭐⭐⭐⭐ **必需**

**用途**: 全局仿真统计，评估整体性能

**配置**:
```xml
<summary-output value="summary.xml"/>
```

**输出指标**:
- `loaded`, `inserted`, `running`, `ended` - 车辆数量统计
- `meanWaitingTime`, `meanTravelTime` - 全局时间指标
- `running_max`, `waiting_max` - 峰值统计

**文件大小**: ~10-50 KB（与仿真步长成正比）

**建议**:
- ✅ **所有仿真必需**，文件极小，提供宏观效果对比
- ✅ 用于快速评估策略整体影响（如通行能力提升、平均旅行时间缩短）

---

### 1.2 TripInfo Output ⭐⭐⭐⭐ **推荐（有条件）**

**用途**: 每辆车的完整行程统计

**配置**:
```xml
<tripinfo-output value="tripinfo.xml"/>
```

**输出指标**:
- `duration`, `waitingTime`, `timeLoss` - 行程时间分解
- `routeLength`, `departDelay` - 路径和延误统计

**文件大小**: ~100-500 MB（取决于车辆数量，本项目典型28,666辆 × 1小时）

**建议**:
- ✅ **基准方案必需** - 用于对比管控前后的个体车辆行为变化
- ⚠️ **管控方案可选** - 批量仿真时考虑禁用以节省空间
- ✅ **精细分析场景** - 需要车辆级别数据时开启（如评估不同车型的受益程度）

**批量仿真优化**:
```python
# 仅基准方案和重点方案输出tripinfo
simulation_params = {
    'output_tripinfo': plan_id in ['baseline', 'plan_001', 'plan_best']
}
```

---

### 1.3 EdgeData Output ⭐⭐⭐⭐⭐ **强烈推荐**

**用途**: 路段级别聚合统计，管控策略评估的核心数据源

**配置**:
```xml
<edgeData id="ed1"
          freq="300"
          file="edgedata/edgedata.xml"
          excludeEmpty="true"
          withInternal="false"/>
```

**输出指标**:
- `entered`, `left`, `departed`, `arrived` - 车流量统计
- `speed`, `density`, `occupancy` - 交通流参数
- `traveltime`, `timeLoss` - 路段延误

**文件大小**:
- 全路网（~3000 edges）: ~50-200 MB
- **管控路段过滤（~50-100 edges）**: ~2-10 MB ✅ **推荐**

**建议**:
- ✅ **所有管控方案必需** - 精确评估策略影响区域的交通流变化
- ✅ **按管控区域过滤edges** - 显著减小文件大小（见下文配置）
- ✅ **时间聚合频率优化** - 根据管控时间段调整`freq`参数

**管控区域过滤配置示例**:
```xml
<!-- 仅监测VSS/DHS/TEC策略影响的路段 -->
<edgeData id="ed_control_zones"
          freq="300"
          file="edgedata/edgedata.xml"
          edges="edge_800 edge_801 edge_1000 edge_1001 edge_1002 entrance_k12_to_mainline"
          excludeEmpty="true"/>
```

---

### 1.4 E1 Detector Output ⭐⭐⭐ **条件推荐**

**用途**: 龙门架（Gantry）级别精确流量监测

**当前状态**:
- 项目已有E1检测器配置（位于`cases/{case_id}/simulations/{sim_id}/e1/`）
- 对应真实龙门架位置（来自数据库`dim.point_gantry`）

**配置** (在additional文件中):
```xml
<e1Detector id="gantry_G420151001000110010_0"
            lane="edge_1000_0"
            pos="50.0"
            freq="300"
            file="e1/gantry_G420151001000110010_0.xml"
            friendlyPos="true"/>
```

**文件大小**:
- 每个检测器: ~3-5 KB（1小时，freq=300）
- 典型龙门架数量: 100-200个 → **总计0.3-1 MB**

**建议**:
- ✅ **基准方案必需** - 用于精度分析（MAPE/GEH计算）
- ⚠️ **管控方案可选** - 如仅关注管控区域，可减少检测器数量
- ✅ **管控区域增强监测** - 在VSS/DHS/TEC策略路段增加检测器密度

**批量仿真优化建议**:
```python
# 策略1: 基准方案全量E1，管控方案仅管控区域E1
if plan_type == 'baseline':
    e1_detectors = load_all_gantry_detectors()  # ~150个
else:
    e1_detectors = load_control_zone_detectors(strategy_edges)  # ~20-30个
```

---

### 1.5 VehRoute Output ⚠️ **不推荐（批量仿真）**

**用途**: 每辆车的详细路径记录

**配置**:
```xml
<vehroute-output value="vehroute.xml"/>
```

**文件大小**: ~500 MB - 2 GB（取决于路径复杂度）

**建议**:
- ❌ **批量仿真禁用** - 文件极大，I/O开销高
- ⚠️ **机理分析场景** - 仅在需要分析路径选择变化时启用（如研究DHS开放后的换道行为）

---

### 1.6 NetState/FCD/Emission Output ❌ **不推荐**

| 输出类型 | 文件大小 | 推荐度 | 说明 |
|---------|---------|--------|------|
| **NetState** | 2-10 GB | ❌ | 每个时间步的全网状态快照，批量仿真禁用 |
| **FCD** | 1-5 GB | ❌ | 浮动车数据，除非需要轨迹可视化 |
| **Emission** | 200-500 MB | ❌ | 排放数据，与管控策略评估无关 |

**建议**:
- ✅ **默认全部禁用**（批量仿真）
- ⚠️ **可视化场景** - 仅演示/调试时启用NetState/FCD

---

## 2. 批量仿真推荐配置

### 2.1 三层配置方案

根据仿真目标和资源限制，提供三种配置级别：

#### **Level 1: 精简模式** ⚡ **批量仿真推荐**

**适用场景**: 批量评估10+个管控方案，快速筛选

**配置**:
```xml
<output>
    <summary-output value="summary.xml"/>
    <!-- EdgeData：仅管控区域 -->
</output>

<additional-files value="control.add.xml,edgeData_control_zones.add.xml"/>
```

**edgeData_control_zones.add.xml**:
```xml
<additional>
    <edgeData id="ed_control"
              freq="300"
              file="edgedata/edgedata.xml"
              edges="<STRATEGY_AFFECTED_EDGES>"
              excludeEmpty="true"/>
</additional>
```

**特点**:
- ✅ 最小化输出（每个方案 < 20 MB）
- ✅ 保留核心评估指标（summary + 管控区域edgeData）
- ✅ 批量仿真效率最高

**Python实现**:
```python
def generate_batch_simulation_config(plan, strategies):
    """生成批量仿真优化配置"""
    # 提取所有策略影响的edges
    affected_edges = set()
    for strategy in strategies:
        affected_edges.update(strategy['configured_params']['affected_edges'])

    # 上下游扩展（监测影响范围）
    extended_edges = expand_edges_upstream_downstream(affected_edges, distance=2000)

    simulation_params = {
        'output_tripinfo': False,  # 禁用
        'output_edgedata': True,
        'edgedata_edges': list(extended_edges),  # 仅管控区域+上下游
        'edgedata_freq': 300  # 5分钟聚合
    }
    return simulation_params
```

---

#### **Level 2: 标准模式** 🎯 **推荐**

**适用场景**: 详细评估3-5个候选方案

**配置**:
```xml
<output>
    <summary-output value="summary.xml"/>
    <tripinfo-output value="tripinfo.xml"/>  <!-- 新增 -->
</output>

<additional-files value="control.add.xml,edgeData_full.add.xml,e1_control_zones.add.xml"/>
```

**特点**:
- ✅ 包含TripInfo（车辆级别分析）
- ✅ 全路网EdgeData（评估连锁影响）
- ✅ 管控区域E1检测器（精度验证）

**文件大小**: 每个方案 ~150-300 MB

**Python实现**:
```python
def generate_standard_simulation_config(plan, strategies):
    """生成标准仿真配置"""
    simulation_params = {
        'output_tripinfo': True,  # 启用
        'output_edgedata': True,
        'edgedata_edges': None,  # 全路网
        'edgedata_freq': 300,
        'e1_detectors': 'control_zones'  # 仅管控区域
    }
    return simulation_params
```

---

#### **Level 3: 完整模式** 🔬 **研究/演示**

**适用场景**: 最终方案的深度分析、论文研究、演示汇报

**配置**:
```xml
<output>
    <summary-output value="summary.xml"/>
    <tripinfo-output value="tripinfo.xml"/>
    <vehroute-output value="vehroute.xml"/>  <!-- 新增 -->
    <fcd-output value="fcd.xml"/>  <!-- 可选：轨迹可视化 -->
</output>

<additional-files value="control.add.xml,edgeData_full.add.xml,e1_all_gantries.add.xml"/>
```

**特点**:
- ✅ 完整数据集（路径、轨迹、全量E1）
- ✅ 支持机理分析和可视化
- ⚠️ 文件大小: 每个方案 1-3 GB

---

### 2.2 EdgeData配置优化

#### **策略1: 动态边列表生成**

根据管控策略自动生成EdgeData监测范围：

```python
def generate_edgedata_config_for_plan(plan, strategies):
    """
    根据管控方案动态生成EdgeData配置

    策略影响范围:
    - VSS: 策略路段 + 上游2km + 下游1km
    - DHS: 策略路段 + 上游3km + 下游2km（观察车道变换影响）
    - TEC: 入口edge + 主线下游5km（观察流量传播）
    """
    from shared.data_access.edge_query import (
        get_upstream_edges,
        get_downstream_edges
    )

    monitored_edges = set()

    for strategy in strategies:
        strategy_type = strategy['strategy_type']
        affected_edges = strategy['configured_params']['affected_edges']

        if strategy_type == 'VSS':
            # VSS: 上游2km观察速度协调，下游1km观察流量恢复
            for edge in affected_edges:
                monitored_edges.add(edge)
                monitored_edges.update(get_upstream_edges(edge, distance=2000))
                monitored_edges.update(get_downstream_edges(edge, distance=1000))

        elif strategy_type == 'DHS':
            # DHS: 上游3km观察提前换道，下游2km观察容量提升效果
            for edge in affected_edges:
                monitored_edges.add(edge)
                monitored_edges.update(get_upstream_edges(edge, distance=3000))
                monitored_edges.update(get_downstream_edges(edge, distance=2000))

        elif strategy_type == 'TEC':
            # TEC: 入口+下游主线5km观察流量传播和排队消散
            entrance_edge = strategy['configured_params']['entrance_edge']
            monitored_edges.add(entrance_edge)
            monitored_edges.update(get_downstream_edges(entrance_edge, distance=5000))

    return list(monitored_edges)
```

#### **策略2: 时间聚合频率优化**

根据管控时间段动态调整采样频率：

```python
def calculate_optimal_edgedata_freq(plan, strategies):
    """
    计算最优EdgeData聚合频率

    原则:
    - 管控时段内: 高频采样（120-300秒）
    - 非管控时段: 低频采样（600-900秒）
    """
    # 提取所有策略的时间区间
    control_intervals = []
    for strategy in strategies:
        if strategy['strategy_type'] == 'VSS':
            for step in strategy['configured_params']['speed_steps']:
                control_intervals.append(step['time_hours'] * 3600)
        elif strategy['strategy_type'] == 'DHS':
            for interval in strategy['configured_params']['intervals']:
                control_intervals.append(interval['begin_hours'] * 3600)
                control_intervals.append(interval['end_hours'] * 3600)

    # 判断管控密度
    if len(control_intervals) > 10:
        return 300  # 复杂方案: 5分钟聚合
    elif len(control_intervals) > 5:
        return 180  # 中等方案: 3分钟聚合
    else:
        return 300  # 简单方案: 5分钟聚合（默认）
```

---

## 3. 时间粒度建议

### 3.1 EdgeData采样频率

| 频率 | 场景 | 优点 | 缺点 |
|------|------|------|------|
| **60秒** | 实时响应分析 | 捕捉瞬时变化 | 文件大，噪声多 |
| **180秒** | 精细评估 | 平衡精度和效率 | 适中 |
| **300秒** ⭐ | 批量仿真推荐 | 降低30%文件大小 | 可能错过短时变化 |
| **600秒** | 长时间仿真 | 最小化输出 | 精度损失 |

**建议**:
```xml
<!-- 批量仿真默认 -->
<edgeData id="ed1" freq="300" ... />

<!-- 关键时段提高精度 -->
<edgeData id="ed_peak" freq="180" begin="25200" end="32400" ... />
```

### 3.2 E1 Detector采样频率

```xml
<!-- 标准龙门架检测器: 5分钟聚合 -->
<e1Detector id="gantry_001" freq="300" ... />

<!-- 管控区域检测器: 3分钟聚合（提高敏感度）-->
<e1Detector id="control_zone_001" freq="180" ... />
```

---

## 4. 文件大小估算与优化效果

### 4.1 单次仿真文件大小对比

**场景**: 1小时仿真，28,666辆车，3000条边

| 配置方案 | Summary | TripInfo | EdgeData | E1 | VehRoute | **总计** |
|---------|---------|----------|----------|----|---------|----|
| **精简模式** | 20 KB | - | 5 MB | - | - | **~5 MB** ⚡ |
| **标准模式** | 20 KB | 200 MB | 80 MB | 1 MB | - | **~280 MB** 🎯 |
| **完整模式** | 20 KB | 200 MB | 150 MB | 5 MB | 800 MB | **~1.2 GB** 🔬 |
| **当前默认** | 20 KB | 200 MB | 150 MB | 5 MB | - | **~355 MB** |

### 4.2 批量仿真空间节省

**场景**: 批量评估15个管控方案

| 配置方案 | 单方案大小 | 15方案总计 | **节省空间** |
|---------|-----------|-----------|------------|
| **精简模式** | 5 MB | 75 MB | **-95%** ⚡ |
| **标准模式** | 280 MB | 4.2 GB | **-69%** 🎯 |
| **完整模式** | 1.2 GB | 18 GB | - |
| **当前默认** | 355 MB | 5.3 GB | **Baseline** |

---

## 5. 实施指南

### 5.1 修改`sumo_utils.py`

在`generate_sumocfg_for_simulation()`中增加配置级别参数：

```python
def generate_sumocfg_for_simulation(
    case_metadata: dict,
    simulation_type,
    simulation_folder: Path,
    case_root: Path,
    simulation_params: dict | None = None,
    optimization_level: str = 'standard'  # 新增参数
) -> str:
    """
    optimization_level:
    - 'minimal': 精简模式（批量仿真）
    - 'standard': 标准模式（推荐）
    - 'full': 完整模式（研究/演示）
    """
    simulation_params = simulation_params or {}

    # 根据优化级别设置默认参数
    if optimization_level == 'minimal':
        simulation_params.setdefault('output_tripinfo', False)
        simulation_params.setdefault('output_edgedata', True)
        simulation_params.setdefault('edgedata_mode', 'control_zones')
        simulation_params.setdefault('edgedata_freq', 300)
        simulation_params.setdefault('e1_detectors', 'disabled')

    elif optimization_level == 'standard':
        simulation_params.setdefault('output_tripinfo', True)
        simulation_params.setdefault('output_edgedata', True)
        simulation_params.setdefault('edgedata_mode', 'full_network')
        simulation_params.setdefault('edgedata_freq', 300)
        simulation_params.setdefault('e1_detectors', 'control_zones')

    elif optimization_level == 'full':
        simulation_params.setdefault('output_tripinfo', True)
        simulation_params.setdefault('output_vehroute', True)
        simulation_params.setdefault('output_edgedata', True)
        simulation_params.setdefault('edgedata_mode', 'full_network')
        simulation_params.setdefault('edgedata_freq', 180)
        simulation_params.setdefault('e1_detectors', 'all_gantries')

    # ... 继续生成配置逻辑
```

### 5.2 批量仿真API调用示例

```python
# 批量仿真服务调用
from api.services.batch_optimization_service import BatchOptimizationService

batch_service = BatchOptimizationService()

# 创建批量优化任务
optimization_result = await batch_service.create_batch_optimization(
    case_id='case_20251029_001',
    plan_ids=['plan_baseline', 'plan_001', 'plan_002', 'plan_003'],
    optimization_config={
        'simulation_level': 'minimal',  # 精简模式
        'parallel_jobs': 4,
        'edgedata_mode': 'control_zones'  # 仅管控区域
    }
)
```

---

## 6. 管控策略特定配置

### 6.1 VSS（可变限速）策略

**关键监测指标**:
- 策略路段的`speed`变化
- 上游2km的`speed`协调性
- 下游1km的`flow`恢复情况

**推荐配置**:
```xml
<edgeData id="ed_vss"
          freq="180"
          file="edgedata/edgedata_vss.xml"
          edges="<VSS_EDGES + UPSTREAM_2KM + DOWNSTREAM_1KM>"
          excludeEmpty="true"/>
```

**E1检测器增强**:
```python
# 在VSS策略路段增加检测器密度
for edge in vss_strategy_edges:
    for lane_index in range(num_lanes):
        add_e1_detector(
            edge_id=edge,
            lane_index=lane_index,
            positions=[100, 500, 900],  # 路段首中尾
            freq=180
        )
```

---

### 6.2 DHS（应急车道开放）策略

**关键监测指标**:
- 应急车道的`entered`, `occupancy`（验证开放效果）
- 策略路段的`capacity`提升（通行量增加）
- 上游3km的`density`变化（提前换道行为）

**推荐配置**:
```xml
<!-- 分车道EdgeData -->
<laneData id="ld_dhs"
          freq="300"
          file="edgedata/lanedata_dhs.xml"
          lanes="<DHS_HARD_SHOULDER_LANES>"
          excludeEmpty="true"/>

<!-- 路段级EdgeData -->
<edgeData id="ed_dhs"
          freq="300"
          file="edgedata/edgedata_dhs.xml"
          edges="<DHS_EDGES + UPSTREAM_3KM + DOWNSTREAM_2KM>"
          excludeEmpty="true"/>
```

---

### 6.3 TEC（收费站入口管控）策略

**关键监测指标**:
- 入口edge的`entered`流量（验证限流效果）
- 主线下游5km的`speed`, `density`（流量传播）
- 入口排队长度（需E2检测器或FCD）

**推荐配置**:
```xml
<!-- 入口edge精细监测 -->
<edgeData id="ed_tec_entrance"
          freq="120"
          file="edgedata/edgedata_tec_entrance.xml"
          edges="<TEC_ENTRANCE_EDGES>"
          excludeEmpty="true"/>

<!-- 主线影响范围 -->
<edgeData id="ed_tec_mainline"
          freq="300"
          file="edgedata/edgedata_tec_mainline.xml"
          edges="<TEC_DOWNSTREAM_5KM>"
          excludeEmpty="true"/>
```

---

## 7. 评估指标映射

### 7.1 Summary → 宏观效果

| SUMO指标 | 管控评估指标 | 计算方法 |
|---------|------------|---------|
| `meanTravelTime` | 平均旅行时间改善率 | `(Baseline - Control) / Baseline × 100%` |
| `ended` | 通行能力提升 | `Control / Baseline × 100% - 100%` |
| `meanWaitingTime` | 等待时间缩短率 | 同上 |

### 7.2 EdgeData → 策略效果

| SUMO指标 | VSS评估 | DHS评估 | TEC评估 |
|---------|---------|---------|---------|
| `speed` | ✅ 速度协调性 | ✅ 容量提升验证 | ✅ 拥堵传播 |
| `entered` | ⚠️ 流量变化 | ✅ 通行量增加 | ✅ 限流效果 |
| `density` | ✅ 密度调控 | ✅ 车道利用率 | ⚠️ 排队扩散 |
| `timeLoss` | ✅ 延误降低 | ✅ 时间节省 | ⚠️ 上游延误 |

### 7.3 TripInfo → 个体受益

```python
def calculate_vehicle_benefit(baseline_tripinfo, control_tripinfo):
    """
    计算个体车辆受益程度

    指标:
    - 旅行时间节省: duration_baseline - duration_control
    - 延误降低: timeLoss_baseline - timeLoss_control
    - 受益车辆比例: (improved_vehicles / total_vehicles) × 100%
    """
    benefits = []
    for veh_id in baseline_tripinfo.keys():
        if veh_id in control_tripinfo:
            benefit = {
                'vehicle_id': veh_id,
                'time_saved': baseline_tripinfo[veh_id]['duration'] -
                              control_tripinfo[veh_id]['duration'],
                'delay_reduced': baseline_tripinfo[veh_id]['timeLoss'] -
                                 control_tripinfo[veh_id]['timeLoss']
            }
            benefits.append(benefit)
    return benefits
```

---

## 8. 最终推荐配置

### 8.1 批量仿真（10+方案）

```python
batch_simulation_config = {
    'optimization_level': 'minimal',
    'output': {
        'summary': True,          # 必需
        'tripinfo': False,        # 禁用
        'edgedata': True,         # 启用
        'e1': False,              # 禁用
        'vehroute': False         # 禁用
    },
    'edgedata': {
        'mode': 'control_zones',  # 仅管控区域
        'freq': 300,              # 5分钟聚合
        'expand_range': {
            'VSS': {'upstream': 2000, 'downstream': 1000},
            'DHS': {'upstream': 3000, 'downstream': 2000},
            'TEC': {'downstream': 5000}
        }
    }
}
```

**预期效果**:
- 单方案输出: ~5 MB
- 15方案总计: ~75 MB
- 仿真速度提升: ~30%（减少I/O等待）

---

### 8.2 详细评估（3-5方案）

```python
detailed_simulation_config = {
    'optimization_level': 'standard',
    'output': {
        'summary': True,
        'tripinfo': True,         # 启用
        'edgedata': True,
        'e1': 'control_zones',    # 管控区域E1
        'vehroute': False
    },
    'edgedata': {
        'mode': 'full_network',   # 全路网
        'freq': 300
    },
    'e1': {
        'locations': 'control_zones',
        'freq': 300
    }
}
```

**预期效果**:
- 单方案输出: ~280 MB
- 5方案总计: ~1.4 GB
- 支持完整评估分析

---

### 8.3 最终方案（1-2方案）

```python
final_simulation_config = {
    'optimization_level': 'full',
    'output': {
        'summary': True,
        'tripinfo': True,
        'edgedata': True,
        'e1': 'all_gantries',     # 全量龙门架
        'vehroute': True,         # 启用路径分析
        'fcd': True               # 可选：轨迹可视化
    },
    'edgedata': {
        'mode': 'full_network',
        'freq': 180               # 3分钟聚合（提高精度）
    },
    'e1': {
        'locations': 'all_gantries',
        'freq': 180
    }
}
```

**预期效果**:
- 单方案输出: ~1.2 GB
- 支持深度分析、论文、演示

---

## 9. 实施优先级

| 阶段 | 任务 | 优先级 | 预估工时 |
|------|------|-------|---------|
| **Phase 1** | 修改`sumo_utils.py`支持`optimization_level`参数 | P0 | 4h |
| **Phase 2** | 实现EdgeData动态边列表生成（基于策略） | P0 | 6h |
| **Phase 3** | 批量仿真API集成优化配置 | P1 | 4h |
| **Phase 4** | 前端增加"仿真精度级别"选择 | P2 | 3h |
| **Phase 5** | 文档化评估指标计算方法 | P2 | 2h |

---

## 10. 参考资料

### SUMO官方文档
- [EdgeData Output](https://sumo.dlr.de/docs/Simulation/Output/Lane-_or_Edge-based_Traffic_Measures.html)
- [TripInfo Output](https://sumo.dlr.de/docs/Simulation/Output/TripInfo.html)
- [Summary Output](https://sumo.dlr.de/docs/Simulation/Output/Summary.html)
- [E1 Detectors](https://sumo.dlr.de/docs/Simulation/Output/Induction_Loops_Detectors_(E1).html)

### 项目文档
- `docs/design/sumo_control_strategies_research.md` - 管控策略SUMO实现研究
- `docs/真实数据分析与策略建议_G4202_G5综合.md` - 真实数据分析
- `shared/utilities/sumo_utils.py` - SUMO配置生成工具

---

## 附录A: EdgeData配置生成工具

```python
# shared/control_tools/edgedata_generator.py

from pathlib import Path
from typing import List, Dict, Set
from shared.data_access.edge_query import (
    get_upstream_edges,
    get_downstream_edges
)


def generate_edgedata_config_for_strategies(
    strategies: List[Dict],
    output_path: Path,
    mode: str = 'control_zones',
    freq: int = 300
) -> Path:
    """
    根据管控策略生成EdgeData配置文件

    Args:
        strategies: 策略列表
        output_path: 输出路径
        mode: 'control_zones'（管控区域）或 'full_network'（全路网）
        freq: 聚合频率（秒）

    Returns:
        生成的配置文件路径
    """
    if mode == 'full_network':
        # 全路网模式：不指定edges
        edges_attr = ''
    else:
        # 管控区域模式：动态生成边列表
        monitored_edges = _collect_monitored_edges(strategies)
        edges_list = ' '.join(sorted(monitored_edges))
        edges_attr = f' edges="{edges_list}"'

    # 生成XML内容
    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<additional>
    <edgeData id="ed_control_strategy"
              freq="{freq}"
              file="edgedata/edgedata.xml"{edges_attr}
              excludeEmpty="true"
              withInternal="false"/>
</additional>
'''

    # 写入文件
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    return output_path


def _collect_monitored_edges(strategies: List[Dict]) -> Set[str]:
    """
    收集所有需要监测的edges

    扩展规则:
    - VSS: 策略路段 + 上游2km + 下游1km
    - DHS: 策略路段 + 上游3km + 下游2km
    - TEC: 入口edge + 下游5km
    """
    monitored = set()

    for strategy in strategies:
        strategy_type = strategy['strategy_type']
        params = strategy['configured_params']

        if strategy_type == 'VSS':
            edges = params.get('affected_edges', [])
            for edge in edges:
                monitored.add(edge)
                monitored.update(get_upstream_edges(edge, 2000))
                monitored.update(get_downstream_edges(edge, 1000))

        elif strategy_type == 'DHS':
            edges = params.get('affected_edges', [])
            for edge in edges:
                monitored.add(edge)
                monitored.update(get_upstream_edges(edge, 3000))
                monitored.update(get_downstream_edges(edge, 2000))

        elif strategy_type in ['TEC', 'TEC_CALIBRATOR', 'TEC_REROUTER']:
            entrance = params.get('entrance_edge') or params.get('entrance_edges', [])
            if isinstance(entrance, str):
                entrance = [entrance]
            for edge in entrance:
                monitored.add(edge)
                monitored.update(get_downstream_edges(edge, 5000))

    return monitored
```

---

**文档状态**: ✅ 已完成
**最后更新**: 2025-10-29
**维护者**: OD_SIM开发团队
