# Implementation Tasks: Control Strategy Ranking (Layer 1 Based)

## Overview

**Implementation Approach**: Build ranking system on top of existing Layer 1 results (8 metrics from summary.xml). No additional data collection required for minimum viable product.

**Timeline**: 2 weeks (10-12 person-days)

**Key Simplification**: EdgeData/TripInfo D0-level analysis deferred to optional Phase 4

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

## Phase 1: Data Extraction and Scoring Engine (Week 1, Days 1-3, 3 days)

### 1.1 Layer 1 Data Extractor

- [ ] 1.1.1 Create Layer 1 data adapter
  - Call existing `GET /api/v1/batch/{batch_id}/results` endpoint
  - Parse response to extract plan_results with 8 metrics per plan
  - Validate baseline plan presence in results
  - Transform to ranking engine input format
  - **Integration Point**: Uses `api/services/batch_optimization_service.get_batch_results()`
  - **File**: `shared/analysis_tools/layer1_metrics_extractor.py`
  - **Tests**: `tests/unit/analysis_tools/test_layer1_metrics_extractor.py`
  - **Estimated**: 0.5 day
  - **Note**: No new data parsing needed - Layer 1 already provides metrics via API

### 1.2 Multi-Criteria Scoring Implementation

- [ ] 1.2.1 Implement effectiveness scorer (based on 6 Layer 1 metrics)
  - Formula: 0.25*ended + 0.25*avgSpeed + 0.20*waiting + 0.20*teleports + 0.05*running + 0.05*collisions
  - Min-max normalization to 0-100
  - **File**: `shared/analysis_tools/multi_criteria_scorer.py`
  - **Tests**: `tests/unit/analysis_tools/test_multi_criteria_scorer.py`
  - **Estimated**: 0.5 day

- [ ] 1.2.2 Implement coverage scorer (based on Layer 1 metrics)
  - Formula: 0.50*(ended/loaded) + 0.30*(1-running/loaded) + 0.20*(1-waiting/loaded)
  - Represents completion rate, non-stalled rate, non-waiting rate
  - **File**: `shared/analysis_tools/multi_criteria_scorer.py` (extend)
  - **Tests**: `tests/unit/analysis_tools/test_multi_criteria_scorer.py` (extend)
  - **Estimated**: 0.5 day

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
  - RankingRequest: batch_id, baseline_plan_id, strategy_plan_ids, ranking_criteria (optional)
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
  - Input validation (batch exists, plans exist, baseline exists)
  - Error handling
  - **File**: `api/routes/analysis_routes.py` (modify)
  - **Tests**: `tests/integration/test_ranking_api.py`
  - **Estimated**: 0.4 day

---

## Phase 4: Frontend Integration (Week 2, Days 3-4, 2 days)

### 4.1 UI Components

- [ ] 4.1.1 Add ranking trigger button to batch results page
  - "生成策略排序" button next to existing comparison table
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

## Optional Phase 6: Enhanced Analysis (Future Iteration, 1-2 weeks)

**Note**: This phase is deferred for future enhancement. Current implementation works with Layer 1 data only.

### 6.1 EdgeData D0-Level Analysis

- [ ] 6.1.1 Implement F2-D1: Road segment optimization metrics
- [ ] 6.1.2 Implement F2-D2: Network efficiency evaluation

### 6.2 TripInfo D0-Level Analysis

- [ ] 6.2.1 Implement G2-D1: Major OD pair identification
- [ ] 6.2.2 Implement G2-D3: OD pair efficiency evaluation

### 6.3 Enhanced Scoring Integration

- [ ] 6.3.1 Integrate EdgeData metrics into coverage score
- [ ] 6.3.2 Integrate TripInfo metrics into effectiveness score
- [ ] 6.3.3 Update report generation with enhanced insights

---

## Summary

**Total Estimated Time**: 2 weeks (10-12 person-days)

**Phase Breakdown**:
1. Data Extraction & Scoring: 3 days
2. Report Generation: 2 days
3. API & Service: 2 days
4. Frontend Integration: 2 days
5. Testing & Documentation: 1 day

**Critical Path**:
1. Scoring engine (must complete before report generation)
2. Report generation (must complete before API)
3. API (must complete before frontend)
4. Frontend integration (last)

**Deliverables**:
- ✅ Multi-criteria scoring engine (based on 8 Layer 1 metrics)
- ✅ Strategy ranking algorithm
- ✅ HTML report generation with charts
- ✅ REST API endpoint (POST /api/v1/analysis/batch/strategy-ranking)
- ✅ Frontend ranking UI (integrated into Layer 1 batch results page)
- ✅ Integration and E2E tests
- ✅ Documentation (API guide + user guide)

**Integration Points with Layer 1**:
- 📍 Data Source: `GET /api/v1/batch/{batch_id}/results` (Layer 1 API)
- 📍 Frontend Integration: `frontend/control/js/batch_results.js` (extend)
- 📍 UI Placement: Below Layer 1 comparison table in batch results page
- 📍 Design Consistency: Reuse Chart.js, table styling, and UI patterns from Layer 1

**Key Simplifications vs Original Proposal**:
- ❌ Removed EdgeData D0-level analysis (F2-D1, F2-D2) - deferred to Phase 6
- ❌ Removed TripInfo D0-level analysis (G2-D1, G2-D3) - deferred to Phase 6
- ✅ Ranking works with Layer 1 data only (8 metrics from summary.xml)
- ✅ Timeline reduced from 4-5 weeks to 2 weeks
- ✅ No additional data collection infrastructure needed

**Risk Mitigation**:
- Graceful degradation if Layer 1 data incomplete
- Fallback to default weights if custom weights invalid
- Clear error messages for validation failures
