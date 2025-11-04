# Proposal: Layer 2 Control Strategy Ranking System

**Change ID**: `add-layer2-control-strategy-ranking`

**Status**: 📋 Proposal (Planning)

**Priority**: P0 (Core Business Value - Control Strategy Optimization)

**Created**: 2025-11-04

---

## Why (Problem Statement)

### Current Gap

**Batch simulation Layer 1 (已实现)**: Comprehensive batch monitoring system with:

- 8 traffic metrics comparison from summary.xml (loaded, inserted, ended, running, waiting, teleports, collisions, avgSpeed)
- Improvement rate calculation (vs baseline)
- Comparison tables and Chart.js visualization
- Complete batch workflow (create, start, monitor, results)

**Missing Layer 2**: Cannot answer the critical business question:
> **"Among multiple control strategies (baseline, VSS, TEC, DHS, combinations), which control plan should we deploy? In what order of priority?"**

### Business Impact

- Traffic managers run batch simulations with 5-10 control strategy plans
- Currently: **Manual comparison** of charts and metrics - time-consuming, subjective, inconsistent
- Need: **Automated strategy ranking** based on objective multi-criteria evaluation
- Value: **Direct decision support** - "Deploy Strategy A first (78% effectiveness), then Strategy C (65% effectiveness)"

---

## What Changes

### Core Capability: Control Strategy Ranking Engine

**Purpose**: Automatically rank control strategies from batch simulation results to guide deployment decisions

**Key Features**:

1. **Multi-Source Data Integration** (D0-Level Analysis)
   - EdgeData analysis: Flow improvement, speed improvement, congestion reduction (road-level view)
   - TripInfo analysis: Travel time reduction, delay reduction, OD pair improvements (user experience view)
   - Combines D-group features from both analysis systems

2. **Multi-Criteria Scoring System**
   - **Effectiveness (40%)**: Improvement rates (flow, speed, travel time, delay)
   - **Coverage (25%)**: Affected road segments, affected OD pairs, benefiting vehicles
   - **Efficiency (20%)**: Improvement per control cost, ROI estimate
   - **Reliability (15%)**: Performance stability across random seeds, adverse scenario resilience

3. **Strategy Ranking Output**
   - Ranked list with scores (0-100)
   - Recommendation categories: "强烈推荐" (>75), "推荐" (60-75), "可选" (45-60), "不推荐" (<45)
   - Supporting evidence: Key metrics comparison table, improvement breakdown
   - Visual comparison: Radar chart, score breakdown bar chart

### Scope: Focused on Decision Support

**In Scope** (必要分析):
- ✅ Multi-strategy comparison table (baseline vs. controlled)
- ✅ Improvement rate calculation (relative to baseline)
- ✅ Multi-criteria scoring and ranking
- ✅ Recommendation report generation (HTML + JSON)
- ✅ D0-level OD pair analysis (TripInfo Group D: G2-D1, G2-D3 - major OD pairs, OD efficiency)
- ✅ Road segment optimization metrics (EdgeData Group D: F2-D1, F2-D2 - segment metrics, network efficiency)

**Out of Scope** (过度分析 - 可选):
- ❌ Deep time-series evolution (can be added later if needed)
- ❌ Detailed spatial propagation animation (useful for research, not decision-making)
- ❌ Advanced predictive modeling (Phase 2 feature)

---

## What Changes (Detailed)

### New Capability: control-strategy-ranking

**API Endpoint**:
```
POST /api/v1/analysis/batch/strategy-ranking
Request:
{
  "case_id": "case_20251104_001",
  "batch_id": "batch_20251104_001",
  "baseline_plan_id": "plan_baseline",
  "strategy_plan_ids": ["plan_vss_001", "plan_tec_001", "plan_dhs_001", "plan_vss_tec_combo"],
  "ranking_criteria": {
    "effectiveness_weight": 0.40,
    "coverage_weight": 0.25,
    "efficiency_weight": 0.20,
    "reliability_weight": 0.15
  }
}

Response:
{
  "ranking_id": "ranking_20251104_001",
  "ranked_strategies": [
    {
      "rank": 1,
      "plan_id": "plan_vss_tec_combo",
      "plan_name": "VSS+TEC协同控制",
      "overall_score": 78.5,
      "recommendation": "强烈推荐",
      "scores": {
        "effectiveness": 82.0,
        "coverage": 75.0,
        "efficiency": 78.0,
        "reliability": 76.0
      },
      "key_improvements": {
        "avg_speed_increase": "+18.2%",
        "travel_time_reduction": "-22.5%",
        "delay_reduction": "-35.8%",
        "affected_vehicles": "85% of network"
      }
    },
    {
      "rank": 2,
      "plan_id": "plan_vss_001",
      "overall_score": 65.3,
      "recommendation": "推荐",
      ...
    }
  ],
  "comparison_table": {...},
  "report_file": "frontend/control/optimization.html"
}
```

### New Components

**Backend**:
- `shared/analysis_tools/strategy_ranking_engine.py` - Core ranking algorithm
- `shared/analysis_tools/multi_criteria_scorer.py` - Scoring logic
- `api/services/strategy_ranking_service.py` - Service orchestration
- `api/models/analysis/ranking_requests.py` - Request/response models

**Frontend**:
- `frontend/control/js/strategy_ranking.js` - Ranking result display
- `frontend/control/css/strategy_ranking.css` - Ranking UI styles
- `frontend/control/optimization.html` - Layer 2 ranking results page (displayed after analysis)

### Modified Capabilities

- **batch-optimization**: Add ranking analysis option after batch completion
- **batch-monitoring-unified**: Add "生成优化方案" button in batch results view

---

## Analysis Workflow

### Step 1: Data Aggregation (D0-Level)

**From Layer 1 (summary.xml - 8 metrics)**:
```python
# Layer 1 已提供的基础指标（来自 summary.xml）
{
  # 车辆流量指标 (4个)
  "loaded": 2200,        # 已加载车数 (辆)
  "inserted": 2180,      # 已插入车数 (辆)
  "ended": 2150,         # 已完成车数 (辆) ⬆️ 越高越好
  "running": 30,         # 当前运行车数 (辆) ⬇️ 越低越好

  # 拥堵指标 (3个)
  "waiting": 120,        # 等待车数 (辆) ⬇️ 越低越好
  "teleports": 35,       # 传送次数 (次) ⬇️ 越低越好
  "collisions": 2,       # 碰撞次数 (次) ⬇️ 越低越好

  # 性能指标 (1个)
  "avgSpeed": 48.5,      # 平均速度 (m/s) ⬆️ 越高越好
}
```

**From EdgeData** (F2-D1, F2-D2 - Optional, 增强Layer 1):
```python
# F2-D1: Road segment optimization metrics
{
  "improved_segments": 120,  # Number of segments with flow/speed improvement
  "deteriorated_segments": 15,
  "total_segments": 350,  # Total edges recorded in baseline plan's edgedata.xml
  "net_improvement_rate": "+30.0%",  # (120-15)/350 = net improved / total
  "improved_ratio": "34.3%",  # 120/350 = improved / total
  "deteriorated_ratio": "4.3%",  # 15/350 = deteriorated / total
  "avg_speed_increase": "+12.5%",
  "avg_flow_increase": "+8.3%"
}

# F2-D2: Network efficiency evaluation
{
  "network_efficiency_index": 0.78,  # 0-1 scale
  "congestion_index": 0.35,  # 0-1 scale (lower = better)
  "capacity_utilization": 0.68
}
```

**From TripInfo** (G2-D1, G2-D3 - Optional, 增强Layer 1):
```python
# G2-D1: Major OD pair identification
{
  "top_od_pairs": [
    {"origin": "TAZ_1", "destination": "TAZ_6", "volume": 450, "pct": 5.2%},
    ...
  ],
  "total_od_pairs": 86
}

# G2-D3: OD pair efficiency evaluation
{
  "improved_od_pairs": 58,
  "deteriorated_od_pairs": 12,
  "od_improvement_rate": "+67.4%",
  "avg_travel_time_reduction": "-22.5%",
  "avg_delay_reduction": "-35.8%"
}
```

**Note**: Layer 2 ranking implements **complete analysis capabilities** from MVP, including EdgeData and TripInfo analyzers. System automatically adapts to available outputs - works with summary.xml only (minimum) or leverages all three outputs (optimal) based on batch output_config.

### Step 2: Multi-Criteria Scoring

**Effectiveness Score (40%)** - Based on 8 Layer 1 metrics:
- Core formula using summary.xml metrics:
  ```python
  effectiveness = (
      0.25 * normalize(ended_improvement) +        # 已完成车数 ⬆️
      0.25 * normalize(avgSpeed_improvement) +     # 平均速度 ⬆️
      0.20 * normalize(waiting_reduction) +        # 等待车数 ⬇️
      0.20 * normalize(teleports_reduction) +      # 传送次数 ⬇️
      0.05 * normalize(running_reduction) +        # 运行车数 ⬇️
      0.05 * normalize(collisions_reduction)       # 碰撞次数 ⬇️
  )
  # Note: loaded/inserted 通常相同，不计入评分
  ```

**Coverage Score (25%)** - Adaptive based on available outputs:
- **Mode 1 - Summary.xml only**:
  ```python
  # 基于 summary.xml 的车辆覆盖率
  coverage = (
      0.50 * (ended / loaded) +              # 完成率（通行效率）
      0.30 * (1 - running / loaded) +        # 非滞留率
      0.20 * (1 - waiting / loaded)          # 非等待率
  )
  ```
- **Mode 2 - Summary + TripInfo**:
  ```python
  # 增加 OD 对覆盖率
  coverage = (
      0.40 * (ended / loaded) +                          # 车辆完成率
      0.30 * (improved_od_pairs / total_od_pairs) +      # OD对改进覆盖率
      0.30 * (1 - running / loaded)                      # 非滞留率
  )
  ```
- **Mode 3a - Summary + EdgeData (no tripinfo)**:
  ```python
  # 增加路段覆盖率
  coverage = (
      0.40 * (improved_segments / total_segments) +      # 路段改进覆盖率
      0.35 * (ended / loaded) +                           # 车辆完成率
      0.25 * (1 - running / loaded)                       # 非滞留率
  )
  ```
- **Mode 3b - All outputs (Summary + TripInfo + EdgeData)**:
  ```python
  # 多维度覆盖率
  coverage = (
      0.35 * (improved_segments / total_segments) +      # 空间覆盖（路段）
      0.35 * (improved_od_pairs / total_od_pairs) +      # OD对覆盖
      0.30 * (ended / loaded)                             # 车辆覆盖
  )
  ```

**Efficiency Score (20%)**:
- **Simple approach (Layer 1 only)**:
  ```python
  # 综合改进度 / 控制强度
  total_improvement = (
      0.4 * avgSpeed_improvement +
      0.3 * ended_improvement +
      0.3 * teleports_reduction
  )
  control_intensity = len(affected_edges) / total_network_edges
  efficiency = total_improvement / max(control_intensity, 0.1)
  ```
- **Advanced (optional, if cost data available)**:
  ```python
  efficiency = total_improvement / control_cost_estimate
  ```

**Reliability Score (15%)**:
- Performance consistency across random seeds (std deviation of effectiveness)
- Formula: `reliability = 100 - (std_dev_of_effectiveness * 10)`

### Step 3: Ranking and Recommendation

```python
overall_score = (
    effectiveness * 0.40 +
    coverage * 0.25 +
    efficiency * 0.20 +
    reliability * 0.15
)

if overall_score >= 75:
    recommendation = "强烈推荐"
elif overall_score >= 60:
    recommendation = "推荐"
elif overall_score >= 45:
    recommendation = "可选"
else:
    recommendation = "不推荐"
```

---

## Impact

### Affected Specs

- **NEW**: `control-strategy-ranking` (new capability)
- **MODIFIED**: `batch-optimization` (add ranking feature)
- **MODIFIED**: `batch-monitoring-unified` (add ranking UI)

### Affected Files

**Backend**:
- `shared/analysis_tools/strategy_ranking_engine.py` (new)
- `shared/analysis_tools/multi_criteria_scorer.py` (new)
- `api/services/strategy_ranking_service.py` (new)
- `api/routes/analysis_routes.py` (modify - add ranking endpoint)
- `api/models/analysis/ranking_requests.py` (new)

**Frontend**:
- `frontend/control/js/strategy_ranking.js` (new)
- `frontend/control/css/strategy_ranking.css` (new)
- `frontend/control/js/batch_results.js` (modify - add ranking trigger)

### Breaking Changes

⚠️ **None** - Fully additive feature

---

## Success Criteria

### Functional Acceptance

- [ ] **AC1: D0-Level Data Integration**
  - EdgeData F2-D1, F2-D2 analysis works correctly
  - TripInfo G2-D1, G2-D3 analysis works correctly
  - Data aggregation combines both sources

- [ ] **AC2: Multi-Criteria Scoring**
  - Effectiveness score calculated correctly (0-100)
  - Coverage score calculated correctly (0-100)
  - Efficiency score calculated correctly (0-100)
  - Reliability score calculated correctly (0-100)
  - Overall score is weighted average

- [ ] **AC3: Strategy Ranking**
  - Strategies ranked by overall score (descending)
  - Recommendation categories assigned correctly
  - Ranking report generated (HTML + JSON)

- [ ] **AC4: UI Integration**
  - Batch results page has "生成策略排序" button
  - Ranking results display with radar chart and table
  - User can export ranking report

### Business Acceptance

- [ ] **BA1: Decision Support Quality**
  - Traffic manager can identify top strategy within 2 minutes
  - Ranking results are reproducible (same input → same ranking)
  - Recommendation rationale is clear and understandable

---

## Dependencies

### Prerequisites

- ✅ **Batch optimization system implemented**
- ✅ **Layer 1 results analysis implemented** (8 metrics from summary.xml)
  - loaded, inserted, ended, running (车辆流量 4个)
  - waiting, teleports, collisions (拥堵指标 3个)
  - avgSpeed (性能指标 1个)
- ✅ **EdgeData/TripInfo analysis to be implemented** (Phase 1):
  - EdgeData: Road segment metrics (improved_segments, avg_speed_increase)
  - TripInfo: OD pair metrics (improved_od_pairs, avg_travel_time, avg_delay)

**Note**: Layer 2 ranking implements **complete analysis** from MVP. System works with summary.xml only (graceful degradation) but provides full capabilities when all outputs available.

### Implementation Sequence

**Phase 1: Complete Analysis & Scoring Engine** (Week 1-1.5, Days 1-8)
- Implement output availability detector (reads batch output_config)
- Implement modular analyzers: summary.xml, tripinfo.xml, edgedata.xml
- Implement adaptive multi-criteria scoring (effectiveness, coverage, efficiency, reliability)
- Implement ranking algorithm
- Unit tests for all analyzers and scorers

**Phase 2: API and Service** (Week 2, Days 1-3)
- Backend API endpoint (`POST /api/v1/analysis/batch/strategy-ranking`)
- Service orchestration with modular analyzer calls
- Integration tests

**Phase 3: UI and Reporting** (Week 2-2.5, Days 4-7)
- Frontend ranking display with data source badges
- HTML report generation with charts
- Output combination metadata display
- User acceptance testing

---

## Open Questions

1. **Cost Data Availability**: Do we have control strategy cost estimates? If not, use intensity-based efficiency metric
2. **Weight Customization**: Should users adjust scoring weights? Or use fixed weights?
3. **Baseline Requirement**: Should system enforce that batch includes baseline plan? (Recommendation: Yes, auto-add if missing)

---

## References

- EdgeData analysis spec: `docs/BATCH_SIMULATION_ANALYSIS/EDGEDATA/`
- TripInfo analysis spec: `docs/BATCH_SIMULATION_ANALYSIS/TRIPINFO/`
- Current batch monitoring: `openspec/changes/batch-monitoring-hierarchy-and-results-analysis/`
- Batch optimization: `openspec/specs/batch-optimization/spec.md`
