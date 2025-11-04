# Implementation Tasks: Control Strategy Ranking (Layer 1 Based)

## Overview

**Implementation Approach**: Build complete ranking system with full EdgeData and TripInfo analysis capabilities using modular independent analyzers. System adapts to available outputs based on batch configuration.

**Timeline**: 2.5 weeks (12-14 person-days)

**Key Features**:
- ✅ Modular analyzers for summary.xml, tripinfo.xml, edgedata.xml
- ✅ Adaptive scoring based on available output combinations
- ✅ Graceful degradation if optional outputs missing
- ✅ Complete multi-dimensional analysis: vehicle flow + travel experience + spatial coverage

**Layer 1 Foundation (Already Implemented)**:
- ✅ Batch monitoring system with complete workflow (create, start, monitor, results)
- ✅ API endpoint: `GET /api/v1/batch/{batch_id}/results` returns plan_results with metrics
- ✅ 8 metrics from summary.xml: loaded, inserted, ended, running, waiting, teleports, collisions, avgSpeed
- ✅ Improvement rate calculation (vs baseline plan)
- ✅ Comparison tables with Chart.js visualization
- ✅ Frontend: `frontend/control/js/batch_results.js` handles results display
- ✅ Backend: `api/services/batch_optimization_service.py` contains `get_batch_results()`
- 📁 Implementation reference: `openspec/changes/batch-monitoring-hierarchy-and-results-analysis/`

---

## Phase 1: Data Extraction and Scoring Engine (Week 1, Days 1-4, 4 days)

### 1.0 Output Configuration Detection

- [ ] 1.0.1 Implement output availability detector
  - Read batch simulation_config.json to get output_config
  - Detect available_outputs: `{"summary": true, "tripinfo": bool, "edgedata": bool}`
  - Validate expected output files exist (graceful fallback if missing)
  - Return output_combination string and available file paths dictionary
  - **File**: `shared/analysis_tools/output_detector.py`
  - **Tests**: `tests/unit/analysis_tools/test_output_detector.py`
  - **Estimated**: 0.5 day

### 1.1 Independent Output Analyzers

- [ ] 1.1.1 Create summary.xml analyzer (always required)
  - Call existing `GET /api/v1/batch/{batch_id}/results` endpoint
  - Parse response to extract plan_results with 8 metrics per plan
  - Validate baseline plan presence in results
  - Transform to ranking engine input format
  - **Integration Point**: Uses `api/services/batch_optimization_service.get_batch_results()`
  - **File**: `shared/analysis_tools/summary_analyzer.py`
  - **Tests**: `tests/unit/analysis_tools/test_summary_analyzer.py`
  - **Estimated**: 0.5 day
  - **Note**: Reuses Layer 1 API - no new parsing needed

- [ ] 1.1.2 Create tripinfo.xml analyzer (conditional)
  - Parse tripinfo.xml for each plan's simulation
  - Extract per-vehicle fields: `depart`, `arrival`, `duration`, `timeLoss`, `routeLength`, `vType`
  - Compute aggregates: avg_travel_time (duration), avg_delay (timeLoss), total_delay
  - Identify OD pairs from routeLength/vType
  - Compute improved_od_pairs vs baseline
  - Return independent tripinfo analysis results
  - **File**: `shared/analysis_tools/tripinfo_analyzer.py`
  - **Tests**: `tests/unit/analysis_tools/test_tripinfo_analyzer.py`
  - **Estimated**: 1 day
  - **Note**: Can reuse existing tripinfo parsing patterns from mechanism analysis

- [ ] 1.1.3 Create edgedata.xml analyzer (conditional)
  - Parse edgedata.xml for each plan's simulation
  - Extract per-edge-interval: speed, occupancy, density
  - Compute edge-level improvements vs baseline
  - Identify improved_segments and deteriorated_segments
  - Calculate `total_segments` from baseline plan's edgedata.xml
  - Return independent edgedata analysis results
  - **File**: `shared/analysis_tools/edgedata_analyzer.py`
  - **Tests**: `tests/unit/analysis_tools/test_edgedata_analyzer.py`
  - **Estimated**: 1 day
  - **Note**: Can reuse existing edgedata parsing from edgedata_analysis.py
  - **Note**: `total_segments` = edges recorded in baseline plan's edgedata.xml

- [ ] 1.1.4 Create modular data orchestrator
  - Orchestrates output detection + calls appropriate analyzers
  - Collects independent analysis results into results dictionary
  - Handles missing data gracefully (continues with available outputs)
  - Returns combined results with metadata: output_combination, available_outputs
  - **File**: `shared/analysis_tools/analysis_orchestrator.py`
  - **Tests**: `tests/unit/analysis_tools/test_analysis_orchestrator.py`
  - **Estimated**: 0.5 day

### 1.2 Adaptive Multi-Criteria Scoring Implementation

- [ ] 1.2.1 Implement adaptive effectiveness scorer
  - **Base (summary only)**: `0.25*ended + 0.25*avgSpeed + 0.20*waiting + 0.20*teleports + 0.05*running + 0.05*collisions`
  - **With tripinfo**: Reweight and add `0.15*travel_time_reduction + 0.15*delay_reduction`
  - **With edgedata**: No change (edgedata doesn't affect effectiveness)
  - Implement weight adjustment logic based on available_outputs
  - Min-max normalization to 0-100
  - **File**: `shared/analysis_tools/multi_criteria_scorer.py`
  - **Tests**: `tests/unit/analysis_tools/test_multi_criteria_scorer.py`
  - **Estimated**: 0.8 day

- [ ] 1.2.2 Implement adaptive coverage scorer
  - **Mode 1 - Summary only**: `0.50*(ended/loaded) + 0.30*(1-running/loaded) + 0.20*(1-waiting/loaded)`
  - **Mode 2 - Summary + TripInfo**: `0.40*(ended/loaded) + 0.30*(improved_od_pairs/total_od_pairs) + 0.30*(1-running/loaded)`
  - **Mode 3a - Summary + EdgeData (no tripinfo)**: `0.40*(improved_segments/total_segments) + 0.35*(ended/loaded) + 0.25*(1-running/loaded)`
  - **Mode 3b - All outputs (summary + tripinfo + edgedata)**: `0.35*(improved_segments/total_segments) + 0.35*(improved_od_pairs/total_od_pairs) + 0.30*(ended/loaded)`
  - Implement weight adjustment logic based on available_outputs
  - Min-max normalization to 0-100
  - **File**: `shared/analysis_tools/multi_criteria_scorer.py` (extend)
  - **Tests**: `tests/unit/analysis_tools/test_multi_criteria_scorer.py` (extend)
  - **Estimated**: 0.8 day

- [ ] 1.2.3 Implement efficiency scorer (simple approach)
  - Total improvement: 0.4*avgSpeed + 0.3*ended + 0.3*teleports
  - Control intensity from plan metadata
  - Efficiency = total_improvement / max(control_intensity, 0.1)
  - **File**: `shared/analysis_tools/multi_criteria_scorer.py` (extend)
  - **Tests**: `tests/unit/analysis_tools/test_multi_criteria_scorer.py` (extend)
  - **Estimated**: 0.5 day

- [ ] 1.2.4 Implement reliability scorer
  - Calculate std deviation of effectiveness across random seeds
  - Formula: 100 - (std_dev * 10), default 70 if single seed
  - **File**: `shared/analysis_tools/multi_criteria_scorer.py` (extend)
  - **Tests**: `tests/unit/analysis_tools/test_multi_criteria_scorer.py` (extend)
  - **Estimated**: 0.3 day

### 1.3 Ranking Algorithm

- [ ] 1.3.1 Implement overall score aggregation
  - Weighted sum: 0.40*effectiveness + 0.25*coverage + 0.20*efficiency + 0.15*reliability
  - Support custom weights (validate sum to 1.0)
  - **File**: `shared/analysis_tools/strategy_ranking_engine.py`
  - **Tests**: `tests/unit/analysis_tools/test_strategy_ranking_engine.py`
  - **Estimated**: 0.3 day

- [ ] 1.3.2 Implement ranking logic
  - Sort by overall score descending
  - Assign rank numbers
  - Tie-breaking by effectiveness score
  - **File**: `shared/analysis_tools/strategy_ranking_engine.py` (extend)
  - **Tests**: `tests/unit/analysis_tools/test_strategy_ranking_engine.py` (extend)
  - **Estimated**: 0.2 day

- [ ] 1.3.3 Implement recommendation category assignment
  - >=75: "强烈推荐"
  - 60-75: "推荐"
  - 45-60: "可选"
  - <45: "不推荐"
  - **File**: `shared/analysis_tools/strategy_ranking_engine.py` (extend)
  - **Tests**: `tests/unit/analysis_tools/test_strategy_ranking_engine.py` (extend)
  - **Estimated**: 0.2 day

---

## Phase 2: Report Generation (Week 1, Days 4-5, 2 days)

### 2.1 HTML Report Template

- [ ] 2.1.1 Create HTML report template
  - Executive summary section
  - Ranking table with color-coded recommendations
  - Radar chart placeholder
  - Score breakdown section
  - **File**: `shared/templates/ranking_report_template.html`
  - **Estimated**: 0.5 day

### 2.2 Chart Generation

- [ ] 2.2.1 Implement radar chart generation
  - 4 axes: effectiveness, coverage, efficiency, reliability
  - Multiple strategies on same chart
  - Save as PNG
  - **File**: `shared/analysis_tools/ranking_chart_generator.py`
  - **Dependencies**: matplotlib or plotly
  - **Tests**: `tests/unit/analysis_tools/test_ranking_chart_generator.py`
  - **Estimated**: 0.8 day

- [ ] 2.2.2 Implement score breakdown bar chart
  - Dimension scores for top 3 strategies
  - Save as PNG
  - **File**: `shared/analysis_tools/ranking_chart_generator.py` (extend)
  - **Tests**: `tests/unit/analysis_tools/test_ranking_chart_generator.py` (extend)
  - **Estimated**: 0.5 day

### 2.3 Report Assembly

- [ ] 2.3.1 Implement report generator
  - Populate HTML template with ranking data
  - Embed chart images
  - Save to `frontend/control/optimization.html`
  - **File**: `shared/analysis_tools/ranking_report_generator.py`
  - **Tests**: `tests/unit/analysis_tools/test_ranking_report_generator.py`
  - **Estimated**: 0.7 day

---

## Phase 3: API and Service Layer (Week 2, Days 1-2, 2 days)

### 3.1 Backend API

- [ ] 3.1.1 Create request/response models
  - RankingRequest: case_id, batch_id, baseline_plan_id, strategy_plan_ids, ranking_criteria (optional)
  - RankingResponse: ranking_id, ranked_strategies, comparison_table, report_file
  - **File**: `api/models/analysis/ranking_requests.py`
  - **Estimated**: 0.3 day

- [ ] 3.1.2 Implement ranking service
  - Orchestrate data extraction from Layer 1 results
  - Call ranking engine
  - Generate report
  - Save results to JSON
  - **File**: `api/services/strategy_ranking_service.py`
  - **Tests**: `tests/unit/services/test_strategy_ranking_service.py`
  - **Estimated**: 0.8 day

- [ ] 3.1.3 Add API endpoint
  - POST `/api/v1/analysis/batch/strategy-ranking`
  - Input validation (case exists, batch exists and belongs to case, plans exist, baseline exists)
  - Error handling
  - **File**: `api/routes/analysis_routes.py` (modify)
  - **Tests**: `tests/integration/test_ranking_api.py`
  - **Estimated**: 0.4 day

---

## Phase 4: Frontend Integration (Week 2, Days 3-4, 2 days)

### 4.1 UI Components

- [ ] 4.1.1 Add ranking trigger button to batch results page
  - "生成优化方案" button next to existing comparison table
  - Enable only if batch completed and has >=2 plans
  - **Integration Point**: Add to existing batch results UI (Layer 1)
  - **File**: `frontend/control/simulations.html` (modify)
  - **Estimated**: 0.3 day

- [ ] 4.1.2 Implement ranking request logic
  - Click handler in batch_results.js
  - Loading indicator (reuse existing UI patterns)
  - API call to ranking endpoint (POST /api/v1/analysis/batch/strategy-ranking)
  - Error handling with toast notifications
  - **Integration Point**: Extend `frontend/control/js/batch_results.js` (Layer 1 module)
  - **File**: `frontend/control/js/batch_results.js` (modify)
  - **Estimated**: 0.4 day

- [ ] 4.1.3 Create ranking results display module
  - Ranked list table with score breakdown
  - Color-coded recommendation badges (green/blue/yellow/red)
  - Radar chart display (using Chart.js like Layer 1)
  - Download report button
  - **Design Pattern**: Follow Layer 1's comparison table styling
  - **File**: `frontend/control/js/strategy_ranking.js` (new)
  - **File**: `frontend/control/css/strategy_ranking.css` (new)
  - **Estimated**: 1 day

- [ ] 4.1.4 Integrate ranking results into batch results page
  - Modal or collapsible section below Layer 1 comparison table
  - Link to HTML report (saved in frontend/control/)
  - **Integration Point**: Render below existing batch results display
  - **File**: `frontend/control/js/batch_results.js` (modify)
  - **Estimated**: 0.3 day

---

## Phase 5: Testing and Documentation (Week 2, Day 5, 1 day)

### 5.1 Integration Testing

- [ ] 5.1.1 Create E2E test for ranking workflow
  - Create batch with baseline + 2 strategies
  - Verify ranking results structure
  - Verify report generation
  - **File**: `tests/e2e/test_strategy_ranking_workflow.spec.js`
  - **Estimated**: 0.5 day

- [ ] 5.1.2 Test edge cases
  - Batch with only baseline (should fail validation)
  - Batch with incomplete simulations (should fail)
  - Custom weights validation
  - **File**: `tests/integration/test_ranking_edge_cases.py`
  - **Estimated**: 0.3 day

### 5.2 Documentation

- [ ] 5.2.1 Update API documentation
  - Add ranking endpoint to API guide
  - Request/response examples
  - **File**: `docs/api_docs/新架构API指南.md` (modify)
  - **Estimated**: 0.1 day

- [ ] 5.2.2 Create user guide
  - How to trigger ranking analysis from batch results page
  - How to interpret ranking scores and recommendation categories
  - Scoring criteria explanation (effectiveness, coverage, efficiency, reliability)
  - Comparison with Layer 1 metrics display
  - **Reference**: Follow format of Layer 1 documentation (`docs/features/batch-monitoring-hierarchy.md`)
  - **File**: `docs/features/策略排序用户指南.md` (new)
  - **Estimated**: 0.1 day

---

---

## Summary

**Total Estimated Time**: 2.5 weeks (12-14 person-days)

**Phase Breakdown**:
1. Data Extraction & Scoring: 4 days (includes adaptive tier handling)
2. Report Generation: 2 days
3. API & Service: 2 days
4. Frontend Integration: 2 days
5. Testing & Documentation: 1 day

**Critical Path**:
1. Output config detection (must complete first)
2. Tier-specific data extractors (parallel development possible)
3. Adaptive scoring engine (must complete before report generation)
4. Report generation (must complete before API)
5. API (must complete before frontend)
6. Frontend integration (last)

**Deliverables**:
- ✅ Output availability detection based on batch output_config
- ✅ Independent modular analyzers (summary.xml, tripinfo.xml, edgedata.xml)
- ✅ Adaptive multi-criteria scoring engine (combines available metrics)
- ✅ Strategy ranking algorithm
- ✅ HTML report generation with charts
- ✅ REST API endpoint (POST /api/v1/analysis/batch/strategy-ranking)
- ✅ Frontend ranking UI (integrated into Layer 1 batch results page)
- ✅ Integration and E2E tests
- ✅ Documentation (API guide + user guide)

**Integration Points with Layer 1**:
- 📍 Data Source: `GET /api/v1/batch/{batch_id}/results` (Layer 1 API) + batch simulation_config.json
- 📍 Output Config: Reads batch output_config to determine available outputs
- 📍 Frontend Integration: `frontend/control/js/batch_results.js` (extend)
- 📍 UI Placement: Below Layer 1 comparison table in batch results page
- 📍 Design Consistency: Reuse Chart.js, table styling, and UI patterns from Layer 1

**Modular Data Strategy**:
- ✅ **summary.xml**: Always analyzed (mandatory) - provides vehicle flow, congestion, performance metrics
- ✅ **tripinfo.xml**: Analyzed if output_tripinfo=true - adds travel time/delay metrics, OD pair coverage
- ✅ **edgedata.xml**: Analyzed if output_edgedata=true - adds road segment coverage, spatial distribution
- ✅ **Valid combinations**: summary / summary+tripinfo / summary+edgedata / summary+tripinfo+edgedata
- ✅ Graceful degradation: Automatically uses available outputs if configured files missing
- ✅ No batch configuration changes required: Works with existing output_config settings
- ✅ Metadata tracking: Report includes output_combination field documenting data sources used

**Risk Mitigation**:
- Graceful degradation if configured output files missing
- Fallback to base scoring if optional analysis fails
- Fallback to default weights if custom weights invalid
- Clear error messages for validation failures
- Comprehensive logging of output detection and analyzer execution
- Metadata in report tracks exactly which data sources were used
