# Design: Control Strategy Ranking System (Layer 2)

**Change ID**: `add-layer2-control-strategy-ranking`

**Status**: Design

**Date**: 2025-11-04

---

## Overview

This document captures the architectural decisions and design rationale for the Layer 2 control strategy ranking system. The system provides automated multi-criteria evaluation and ranking of traffic control strategies based on batch simulation results.

---

## Design Goals

1. **Decision Support Focus**: Help traffic managers answer "which control plan to deploy first?" not provide exhaustive analysis
2. **Build on Layer 1**: Reuse existing infrastructure and data without additional collection overhead
3. **Objective Ranking**: Replace manual comparison with systematic multi-criteria evaluation
4. **Extensible Design**: Allow future enhancement with EdgeData/TripInfo analysis without redesign
5. **User-Friendly**: Integrate seamlessly into existing batch results workflow

---

## Key Architectural Decisions

### AD-1: Implement Full EdgeData/TripInfo Analysis from MVP

**Decision**: Build ranking engine with complete EdgeData and TripInfo analysis capabilities from the start, using modular analyzers that work with any available output combination.

**Rationale**:

- Traffic control strategy evaluation requires multi-dimensional analysis: vehicle flow (summary.xml), travel experience (tripinfo.xml), and spatial coverage (edgedata.xml)
- EdgeData provides road segment-level insights critical for understanding control strategy effectiveness in spatial distribution
- TripInfo provides OD pair-level metrics essential for evaluating user experience improvements
- Modular architecture allows graceful degradation when specific outputs unavailable, while maximizing insights when all data present
- Better to implement complete analysis once rather than iterative enhancements that risk architectural rework

**Trade-offs**:

- ✅ **Pros**: Complete analysis capability from day 1, no future enhancement needed, better decision support quality
- ✅ **Pros**: Modular design allows testing each analyzer independently, supports all output combinations
- ✅ **Pros**: Encourages users to enable comprehensive outputs for better traffic insights
- ⚠️ **Cons**: Longer initial implementation (2.5 weeks vs 2 weeks), more code to maintain
- ⚠️ **Cons**: Requires implementing tripinfo and edgedata parsers in addition to summary.xml

**Alternatives Considered**:

- Option A: **Implement full EdgeData/TripInfo analysis (selected)** - complete solution from start

---

### AD-1b: Modular Data Source Selection Based on Output Configuration

**Decision**: Ranking system SHALL independently analyze each available output type based on batch output_config, then combine results into unified scores. No hierarchical tier system - each output type analyzed independently.

**Rationale**:

- Different batches may have different output configurations: summary only, summary+tripinfo, summary+edgedata, or all three
- Each output type provides distinct metrics that should be analyzed independently
- Final scoring combines available metrics with appropriate weights
- Simpler mental model: detect available outputs → analyze each → combine scores

**Output Config Detection**:

```python
# From batch simulation_config.json
output_config = {
    "output_tripinfo": bool,    # Enables travel time/delay analysis
    "output_edgedata": bool,    # Enables road segment analysis
    "output_vehroute": bool,    # Not used by ranking
    "output_netstate": bool,    # Not used by ranking
    "output_fcd": bool,         # Not used by ranking
    "output_emission": bool     # Not used by ranking
}

# Possible combinations (4 valid scenarios)
available_outputs = {
    "summary": True,                    # Always available (mandatory)
    "tripinfo": output_config.get("output_tripinfo", False),
    "edgedata": output_config.get("output_edgedata", False)
}
# Valid combinations: summary / summary+tripinfo / summary+edgedata / all
```

**Independent Analysis Approach**:

| Output Type            | Analysis Module          | Metrics Extracted                                                          | Used For                                                                        |
| ---------------------- | ------------------------ | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **summary.xml**  | `summary_analyzer.py`  | loaded, inserted, ended, running, waiting, teleports, collisions, avgSpeed | Effectiveness (vehicle flow), Coverage (completion rate), Efficiency (baseline) |
| **tripinfo.xml** | `tripinfo_analyzer.py` | depart, arrival, duration, timeLoss, routeLength, vType per vehicle        | Effectiveness (travel time/delay), Coverage (OD pairs)                          |
| **edgedata.xml** | `edgedata_analyzer.py` | edge_speed, edge_occupancy, edge_density per segment                       | Coverage (road segments), Spatial distribution                                  |

**EdgeData Output Range**:
- SUMO EdgeData with `excludeEmpty="true"` outputs only edges with vehicle activity
- Typical coverage: 30-40% of total network edges (~7,390 of 20,124 edges)
- This focuses analysis on actively-used road segments, ignoring unused edges

**Segment Coverage Metrics Definition**:
- `total_segments`: Total number of edges recorded in baseline plan's edgedata.xml
- `improved_segments`: Edges showing performance improvement vs baseline
- `deteriorated_segments`: Edges showing performance degradation vs baseline
- Coverage calculation uses baseline as reference to ensure fair comparison across strategies

**Modular Analysis Workflow**:

```python
def analyze_batch_outputs(batch_id, output_config):
    """Independent analysis of each output type"""
    results = {}

    # Step 1: Always analyze summary.xml (mandatory)
    results['summary'] = analyze_summary_xml(batch_id)

    # Step 2: Analyze tripinfo if available
    if output_config.get('output_tripinfo'):
        results['tripinfo'] = analyze_tripinfo_xml(batch_id)

    # Step 3: Analyze edgedata if available
    if output_config.get('output_edgedata'):
        results['edgedata'] = analyze_edgedata_xml(batch_id)

    return results

def compute_adaptive_scores(results, available_outputs):
    """Combine independent results into unified scores"""
    effectiveness = compute_effectiveness(results, available_outputs)
    coverage = compute_coverage(results, available_outputs)
    efficiency = compute_efficiency(results, available_outputs)
    reliability = compute_reliability(results, available_outputs)

    return {
        'effectiveness': effectiveness,
        'coverage': coverage,
        'efficiency': efficiency,
        'reliability': reliability,
        'metadata': {
            'available_outputs': available_outputs,
            'data_sources': list(results.keys())
        }
    }
```

**Adaptive Scoring Formulas**:

**Effectiveness Score (adapts to available data)**:

```python
def compute_effectiveness(results, available_outputs):
    components = []

    # Base metrics from summary.xml (always present)
    components.append(('ended_improvement', 0.25, results['summary']))
    components.append(('avgSpeed_improvement', 0.25, results['summary']))
    components.append(('waiting_reduction', 0.20, results['summary']))
    components.append(('teleports_reduction', 0.20, results['summary']))
    components.append(('running_reduction', 0.05, results['summary']))
    components.append(('collisions_reduction', 0.05, results['summary']))

    # Add tripinfo metrics if available
    if available_outputs['tripinfo']:
        # Reweight: reduce summary weights, add tripinfo weights
        components = adjust_weights_for_tripinfo(components)
        components.append(('travel_time_reduction', 0.15, results['tripinfo']))
        components.append(('delay_reduction', 0.15, results['tripinfo']))

    # Edgedata doesn't add to effectiveness (spatial validation only)

    return normalize_score(components)
```

**Coverage Score (adapts to available data)**:

```python
def compute_coverage(results, available_outputs):
    components = []

    # Base: vehicle completion rate (from summary.xml)
    components.append(('completion_rate', 0.50, results['summary']))
    components.append(('non_stalled_rate', 0.30, results['summary']))
    components.append(('non_waiting_rate', 0.20, results['summary']))

    # Add OD pair coverage if tripinfo available
    if available_outputs['tripinfo']:
        components = adjust_weights_for_tripinfo(components)
        components.append(('od_pair_coverage', 0.30, results['tripinfo']))

    # Add road segment coverage if edgedata available
    if available_outputs['edgedata']:
        components = adjust_weights_for_edgedata(components)
        components.append(('segment_coverage', 0.35, results['edgedata']))

    return normalize_score(components)
```

**Report Metadata (tracks data sources)**:

```json
{
  "ranking_id": "ranking_20251104_001",
  "data_sources": {
    "summary": true,
    "tripinfo": true,
    "edgedata": false
  },
  "output_combination": "summary+tripinfo",
  "ranked_strategies": [...],
  "note": "Rankings computed using summary.xml and tripinfo.xml data"
}
```

**Trade-offs**:

- ✅ **Pros**: Simpler mental model (no tier hierarchy), modular and testable
- ✅ **Pros**: Each analyzer can be developed/tested independently
- ✅ **Pros**: Easy to add new output types in future (e.g., emission.xml)
- ✅ **Pros**: Clear metadata about which data sources were used
- ⚠️ **Cons**: Weight adjustment logic needed when combining different output types
- ⚠️ **Cons**: Rankings not directly comparable across different output combinations

**Comparability Mitigation**:

- Report metadata clearly states: `"output_combination": "summary+tripinfo"`
- UI badge shows: "基于仿真结果 + 行程数据" or "基于仿真结果 + 路段数据" or "基于完整数据"
- Documentation recommends: Use same output_config for batches intended to be compared

**Alternatives Considered**:

- Option A (Original): Hierarchical tier system (tier1/2/3) - rejected, too rigid
- Option B: Require all outputs always - rejected, too restrictive
- **Option C: Modular independent analysis (selected)** - flexible and clear

**Priority**: Phase 1 (MVP) - core architecture decision affecting all data extraction and scoring logic.

---

### AD-2: Multi-Criteria Scoring with Four Dimensions

**Decision**: Evaluate strategies using 4 dimensions: Effectiveness (40%), Coverage (25%), Efficiency (20%), Reliability (15%).

**Rationale**:

**Why Four Dimensions?**

- **Effectiveness**: Answers "does it work?" (improvement magnitude)
- **Coverage**: Answers "how widespread?" (affected vehicles/roads)
- **Efficiency**: Answers "is it cost-effective?" (improvement per control cost)
- **Reliability**: Answers "is it stable?" (consistency across seeds)

**Why These Weights?**

- Effectiveness weighted highest (40%) - primary concern is "does it improve traffic?"
- Coverage (25%) - second priority is "how many benefit?"
- Efficiency (20%) - resource constraints matter but not primary
- Reliability (15%) - consistency matters but less than effectiveness

**Trade-offs**:

- ✅ **Pros**: Comprehensive evaluation, addresses multiple stakeholder concerns
- ⚠️ **Cons**: More complex than single-metric ranking, weights may need tuning

**Alternatives Considered**:

- Option A: Single metric ranking (e.g., avgSpeed only) - rejected, too simplistic
- Option B: Equal weights (25%/25%/25%/25%) - rejected, doesn't reflect priorities
- **Option C: Weighted by business priority (selected)** - aligns with traffic management goals

---

### AD-3: Effectiveness Scoring Formula

**Decision**: Use weighted combination of 6 metrics with normalization:

```python
effectiveness = (
    0.25 * normalize(ended_improvement) +        # 已完成车数 ⬆️
    0.25 * normalize(avgSpeed_improvement) +     # 平均速度 ⬆️
    0.20 * normalize(waiting_reduction) +        # 等待车数 ⬇️
    0.20 * normalize(teleports_reduction) +      # 传送次数 ⬇️
    0.05 * normalize(running_reduction) +        # 运行车数 ⬇️
    0.05 * normalize(collisions_reduction)       # 碰撞次数 ⬇️
)
```

**Rationale**:

- **ended** (25%): Throughput - most direct measure of network capacity improvement
- **avgSpeed** (25%): Flow quality - user experience and travel time indicator
- **waiting** (20%): Congestion - stopped vehicles indicate bottlenecks
- **teleports** (20%): Severe congestion - SUMO's indicator of gridlock
- **running** (5%): Minor factor - vehicles still in network at end
- **collisions** (5%): Safety - typically rare, lower weight

**Why Not Use loaded/inserted?**

- These are input metrics (constant across strategies), not performance indicators

**Normalization Approach**: Min-max normalization to [0, 100] range

- Ensures all metrics contribute proportionally
- Makes scores interpretable (100 = best in batch, 0 = worst)

---

### AD-4: Adaptive Coverage Scoring Based on Available Data

**Decision**: Coverage score adapts to available outputs, progressively incorporating spatial (EdgeData) and OD pair (TripInfo) coverage as data becomes available.

**Three Scoring Modes**:

**Mode 1 - Summary.xml only** (minimum viable):

```python
coverage = (
    0.50 * (ended / loaded) +              # 完成率（通行效率）
    0.30 * (1 - running / loaded) +        # 非滞留率
    0.20 * (1 - waiting / loaded)          # 非等待率
)
```

**Mode 2 - Summary + TripInfo** (OD pair coverage added):

```python
coverage = (
    0.40 * (ended / loaded) +                          # Vehicle completion
    0.30 * (improved_od_pairs / total_od_pairs) +      # OD pair coverage
    0.30 * (1 - running / loaded)                      # Non-stalled rate
)
```

**Mode 3a - Summary + EdgeData** (road segment coverage, no tripinfo):

```python
coverage = (
    0.40 * (improved_segments / total_segments) +      # Spatial coverage
    0.35 * (ended / loaded) +                           # Vehicle completion
    0.25 * (1 - running / loaded)                       # Non-stalled rate
)
```

**Mode 3b - All outputs** (complete multi-dimensional coverage):

```python
coverage = (
    0.35 * (improved_segments / total_segments) +      # Spatial coverage
    0.35 * (improved_od_pairs / total_od_pairs) +      # OD pair coverage
    0.30 * (ended / loaded)                             # Vehicle coverage
)
```

**Rationale**:

- **Vehicle coverage (summary.xml)**: Basic metric - always available, measures overall throughput
- **OD pair coverage (tripinfo.xml)**: User experience dimension - which origin-destination pairs benefited
- **Spatial coverage (edgedata.xml)**: Network dimension - which road segments improved
- **Adaptive weighting**: As richer data becomes available, coverage becomes more comprehensive and weights adjust to balance all dimensions

**Why Not Fixed Formula?**:

- Traffic control evaluation requires multi-dimensional coverage assessment
- Vehicle-only coverage (summary.xml) doesn't show WHERE improvements occurred
- OD pair coverage adds user experience perspective (trip-level improvements)
- Spatial coverage adds network perspective (which roads benefited)
- System should leverage all available data rather than artificially limiting to one dimension

**Trade-offs**:

- ✅ **Pros**: Comprehensive coverage assessment using all available data, multi-dimensional perspective
- ✅ **Pros**: Graceful degradation - works with minimum data, improves with richer data
- ✅ **Pros**: Encourages users to enable comprehensive outputs for better insights
- ⚠️ **Cons**: Coverage scores not directly comparable across different output combinations (mitigated by metadata)
- ⚠️ **Cons**: More complex weight adjustment logic required

---

### AD-5: Efficiency Scoring - Intensity-Based Approach

**Decision**: Use control intensity (affected edges) as proxy for cost:

```python
total_improvement = (
    0.4 * avgSpeed_improvement +
    0.3 * ended_improvement +
    0.3 * teleports_reduction
)
efficiency = total_improvement / max(control_intensity, 0.1)
```

**Rationale**:

- Control intensity = `len(affected_edges) / total_network_edges`
- Measures "improvement per unit control effort"
- Realistic proxy when actual cost data unavailable

**Why These Improvement Weights?**

- avgSpeed (40%) - most visible user benefit
- ended (30%) - throughput improvement
- teleports (30%) - severe congestion reduction

**Trade-offs**:

- ✅ **Pros**: Computable without cost data, encourages targeted control
- ⚠️ **Cons**: Doesn't reflect actual deployment/maintenance costs

**Alternative Approach**: If cost data available, use `efficiency = total_improvement / control_cost_estimate`

---

### AD-6: Reliability Scoring from Random Seeds

**Decision**: Calculate standard deviation of effectiveness across seeds:

```python
reliability = 100 - (std_dev_of_effectiveness * 10)  # Capped at [0, 100]
# If only one seed: reliability = 70 (default)
```

**Rationale**:

- Penalizes strategies with inconsistent performance
- Factor of 10 scales std_dev to [0, 100] range
- Default 70 for single seed = "moderate confidence"

**Example**:

- std_dev = 2.0 → reliability = 80 (good consistency)
- std_dev = 5.0 → reliability = 50 (poor consistency)
- std_dev = 10.0 → reliability = 0 (highly unstable)

**Trade-offs**:

- ✅ **Pros**: Simple, interpretable, uses existing multi-seed data
- ⚠️ **Cons**: Requires ≥2 seeds for meaningful measurement

---

### AD-7: Recommendation Categories

**Decision**: Four recommendation levels based on overall score:

| Score Range | Category           | 中文     | Color  | Interpretation                          |
| ----------- | ------------------ | -------- | ------ | --------------------------------------- |
| ≥75        | Highly Recommended | 强烈推荐 | Green  | Clear winner, high confidence           |
| 60-75       | Recommended        | 推荐     | Blue   | Good choice, deploy if resources allow  |
| 45-60       | Optional           | 可选     | Yellow | Marginal benefit, consider alternatives |
| <45         | Not Recommended    | 不推荐   | Red    | Poor performance, avoid deployment      |

**Rationale**:

- Based on typical educational grading scales (familiar to users)
- Clear separation between action levels
- ≥75 threshold for "strong recommendation" is conservative (top 25%)

---

### AD-8: Frontend Integration Approach

**Decision**: Display ranking results in `frontend/control/optimization.html`, triggered from batch results page.

**Architecture**:

```
Batch Results Page (Layer 1)
    ↓
[生成优化方案] Button
    ↓
POST /api/v1/analysis/batch/strategy-ranking
    ↓
optimization.html (Layer 2 Results)
```

**Rationale**:

- **Separate page** (optimization.html) maintains clear separation between Layer 1 (comparison) and Layer 2 (ranking)
- **Trigger from Layer 1** provides seamless workflow continuation
- **Reuse Chart.js** maintains UI consistency with Layer 1

**Trade-offs**:

- ✅ **Pros**: Clean separation, dedicated space for ranking visualization, consistent with existing optimization workflow
- ⚠️ **Cons**: Requires page navigation (vs. embedded modal)

**Alternatives Considered**:

- Option A: Embed in batch results page modal - rejected, too cramped for radar chart + table
- Option B: Save report in cases/ directory - rejected, inconsistent with frontend routing
- **Option C: Dedicated optimization.html page (selected)** - aligns with existing architecture

---

### AD-9: API Design

**Decision**: Single POST endpoint with baseline + strategy list:

```json
POST /api/v1/analysis/batch/strategy-ranking
{
  "case_id": "case_20251104_001",
  "batch_id": "batch_20251104_001",
  "baseline_plan_id": "plan_baseline",
  "strategy_plan_ids": ["plan_vss_001", "plan_tec_001", ...],
  "ranking_criteria": {
    "effectiveness_weight": 0.40,
    "coverage_weight": 0.25,
    "efficiency_weight": 0.20,
    "reliability_weight": 0.15
  }
}
```

**Rationale**:

- **Single endpoint** simplifies API surface
- **case_id included** enables correct file path resolution for output files and result storage
- **Explicit baseline** ensures comparison reference is clear
- **Optional custom weights** allows advanced users to tune scoring
- **Default weights** make simple use case easy

**Validation Rules**:

- case_id must exist
- batch_id must exist and belong to case_id
- All plan_ids must exist in batch
- All plans must have status = "completed"
- Baseline plan must have type = "baseline"
- Custom weights must sum to 1.0 (±0.01 tolerance)

---

### AD-10: Report Generation Control Plan

**Decision**: Generate static HTML report with embedded PNG charts.

**Structure**:

1. Executive summary (top recommendation)
2. Radar chart (4 dimensions, all strategies)
3. Ranking table (scores + recommendation badges)
4. Detailed breakdown per plan

**Technology Choices**:

- **matplotlib or plotly** for radar chart generation
- **Chart.js** alternative (browser-side rendering)
- **PNG embedding** for static HTML portability

**Trade-offs**:

- ✅ **Pros**: Self-contained, printable, shareable
- ⚠️ **Cons**: Static (not interactive), regeneration needed for updates

---

## System Integration

### Layer 1 Integration Points

```
Layer 1 (Batch Monitoring)          Layer 2 (Ranking)
─────────────────────────           ─────────────────
GET /batch/{id}/results       →     Data Source (8 metrics)
batch_results.js              →     Trigger UI (button)
Chart.js visualization        →     Design consistency
frontend/control/simulations.html → Entry point
```

### Shared Layer Components

```
shared/analysis_tools/
├── layer1_metrics_extractor.py    # Adapts Layer 1 API response
├── multi_criteria_scorer.py       # Implements 4 scoring dimensions
├── strategy_ranking_engine.py     # Ranking algorithm + tie-breaking
├── ranking_chart_generator.py     # Radar chart + bar chart
└── ranking_report_generator.py    # HTML report assembly
```

---

## Performance Considerations

### Expected Load

- Typical batch: 5-10 plans
- Scoring computation: O(n) per plan
- Ranking: O(n log n) sort
- **Total latency**: < 1 second for typical batch

### Optimization Control plans

- Cache Layer 1 results (already fetched by batch monitoring)
- Parallel chart generation (radar + bar charts)
- Lazy report generation (only when requested)

---

## Post-MVP Enhancements

**Note**: EdgeData and TripInfo integration are now included in Phase 1 MVP implementation (see AD-1, AD-1b, AD-4).

### Advanced UI Features

- **Customizable weight UI**: Interactive slider controls for adjusting effectiveness/coverage/efficiency/reliability weights
- **Historical ranking comparison**: Compare ranking results across different time periods or batch runs
- **Sensitivity analysis**: Visualize how weight adjustments affect final ranking order
- **Enhanced export options**: Export ranking reports to Excel/PDF formats with custom templates

### Performance Optimization (If Needed)

- **Caching layer**: Cache analyzer results for frequently-accessed batches
- **Parallel processing**: Run tripinfo/edgedata analyzers in parallel for large batches
- **Incremental updates**: Re-rank only changed plans instead of full batch re-analysis

---

## Risk Mitigation

| Risk                                     | Mitigation                                 |
| ---------------------------------------- | ------------------------------------------ |
| Layer 1 data incomplete                  | Graceful degradation, clear error messages |
| Invalid custom weights                   | Validation, fall back to defaults          |
| Single seed (no reliability data)        | Default reliability = 70, warn user        |
| Scoring formula disputes                 | Document rationale, allow future tuning    |
| Performance on large batches (20+ plans) | Add pagination, lazy loading if needed     |

---

## Success Metrics

### Technical

- API response time < 2s for 10-plan batch
- All unit tests passing (>95% coverage)
- Integration tests validate end-to-end workflow

### Business

- Traffic managers use ranking for deployment decisions
- Reduces manual comparison time from 30min → 2min
- Ranking reproducibility = 100% (same input → same result)

---

## References

- **Layer 1 Implementation**: `/batch-monitoring-hierarchy-and-results-analysis`
- **SUMO Documentation**: summary.xml vehicleSummary attributes
- **Related Research**: Multi-criteria decision analysis (MCDA) methods

---

**Document Status**: ✅ Ready for implementation

**Next Steps**: Begin Phase 1 - Data Extraction and Scoring Engine
