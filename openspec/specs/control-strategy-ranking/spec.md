# control-strategy-ranking Specification

## Purpose
TBD - created by archiving change add-layer2-control-strategy-ranking. Update Purpose after archive.
## Requirements
### Requirement: Modular Data Aggregation Based on Output Configuration

The system SHALL independently analyze each available output type from batch simulations and combine results into unified ranking scores.

#### Scenario: Output configuration detection

- **WHEN** ranking analysis is requested for a batch
- **THEN** the system SHALL read batch simulation_config.json to get output_config parameters
- **AND** the system SHALL detect available_outputs as: `{"summary": true, "tripinfo": bool, "edgedata": bool}`
- **AND** the system SHALL identify output_combination as one of: "summary", "summary+tripinfo", "summary+edgedata", "summary+tripinfo+edgedata"
- **AND** the system SHALL record output_combination in ranking results metadata

#### Scenario: Summary.xml analysis (always required)

- **WHEN** analyzing batch results
- **THEN** the system SHALL extract 8 metrics from each plan's summary.xml including loaded, inserted, ended, running, waiting, teleports, collisions, and avgSpeed
- **AND** the system SHALL validate that baseline plan metrics are available for comparison
- **AND** the system SHALL exclude step metric from comparison (simulation duration is not a performance metric)
- **AND** the system SHALL compute improvement rates relative to baseline for each metric

#### Scenario: Tripinfo.xml analysis (conditional)

- **WHEN** batch output_config has output_tripinfo=true
- **THEN** the system SHALL parse tripinfo.xml for each plan to extract per-vehicle: travel_time, delay, departed_time, arrival_time
- **AND** the system SHALL compute aggregate metrics: avg_travel_time, avg_delay, total_delay
- **AND** the system SHALL identify improved_od_pairs vs baseline based on travel time reduction
- **AND** the system SHALL return tripinfo analysis results as independent dataset

#### Scenario: Edgedata.xml analysis (conditional)

- **WHEN** batch output_config has output_edgedata=true
- **THEN** the system SHALL parse edgedata.xml for each plan to extract per-edge-interval: speed, occupancy, density
- **AND** the system SHALL compute aggregate segment-level metrics: improved_segments, deteriorated_segments, avg_speed_increase
- **AND** the system SHALL return edgedata analysis results as independent dataset

#### Scenario: Metric categorization

- **WHEN** processing extracted metrics from any output type
- **THEN** the system SHALL categorize summary.xml metrics into vehicle flow (loaded, inserted, ended, running), congestion (waiting, teleports, collisions), and performance (avgSpeed)
- **AND** the system SHALL categorize tripinfo metrics as effectiveness metrics (travel_time, delay) and coverage metrics (od_pairs)
- **AND** the system SHALL categorize edgedata metrics as coverage metrics (road segments)
- **AND** the system SHALL identify improvement direction: higher-is-better (ended, avgSpeed) vs lower-is-better (running, waiting, teleports, collisions, travel_time, delay)

#### Scenario: Graceful degradation if configured output missing

- **WHEN** batch output_config indicates tripinfo=true or edgedata=true but corresponding XML files are missing
- **THEN** the system SHALL log warning message with missing file paths and expected locations
- **AND** the system SHALL mark that output type as unavailable in available_outputs
- **AND** the system SHALL continue ranking using only available output types without failure
- **AND** the system SHALL update output_combination metadata to reflect actually used outputs

---

### Requirement: Adaptive Multi-Criteria Scoring Algorithm

The system SHALL score each control strategy using weighted multi-criteria evaluation with four dimensions: effectiveness, coverage, efficiency, and reliability. Scoring formulas SHALL combine available metrics from independent output analyses.

#### Scenario: Effectiveness score with summary.xml only

- **WHEN** computing effectiveness score and only summary.xml is available
- **THEN** the system SHALL use base formula: `0.25*ended_improvement + 0.25*avgSpeed_improvement + 0.20*waiting_reduction + 0.20*teleports_reduction + 0.05*running_reduction + 0.05*collisions_reduction`
- **AND** the effectiveness score SHALL be normalized to 0-100 range
- **AND** improvements SHALL be calculated relative to baseline plan

#### Scenario: Effectiveness score with tripinfo.xml available

- **WHEN** computing effectiveness score and tripinfo.xml analysis is available
- **THEN** the system SHALL adjust component weights to incorporate tripinfo metrics
- **AND** the system SHALL use formula: `0.20*ended_improvement + 0.20*avgSpeed_improvement + 0.15*travel_time_reduction + 0.15*delay_reduction + 0.15*waiting_reduction + 0.10*teleports_reduction + 0.05*running_reduction`
- **AND** travel_time_reduction and delay_reduction SHALL come from tripinfo analysis results
- **AND** the effectiveness score SHALL be normalized to 0-100 range

#### Scenario: Effectiveness score with edgedata.xml available

- **WHEN** computing effectiveness score and edgedata.xml analysis is available
- **THEN** the system SHALL NOT add edgedata metrics to effectiveness formula (edgedata used for coverage only)
- **AND** the system MAY use edgedata for spatial distribution validation but not scoring

#### Scenario: Coverage score with summary.xml only

- **WHEN** computing coverage score and only summary.xml is available
- **THEN** the system SHALL use vehicle-based formula: `0.50*(ended/loaded) + 0.30*(1 - running/loaded) + 0.20*(1 - waiting/loaded)`
- **AND** coverage represents vehicle completion rate, non-stalled rate, and non-waiting rate
- **AND** the coverage score SHALL be normalized to 0-100 range

#### Scenario: Coverage score with tripinfo.xml available

- **WHEN** computing coverage score and tripinfo.xml analysis is available
- **THEN** the system SHALL adjust component weights to incorporate OD pair coverage
- **AND** the system SHALL use formula: `0.40*(ended/loaded) + 0.30*(improved_od_pairs/total_od_pairs) + 0.30*(1 - running/loaded)`
- **AND** improved_od_pairs SHALL come from tripinfo analysis results
- **AND** the coverage score SHALL be normalized to 0-100 range

#### Scenario: Coverage score with edgedata.xml available

- **WHEN** computing coverage score and edgedata.xml analysis is available
- **THEN** the system SHALL adjust component weights to incorporate road segment coverage
- **AND** if only edgedata available (no tripinfo): use formula `0.40*(improved_segments/total_segments) + 0.35*(ended/loaded) + 0.25*(1 - running/loaded)`
- **AND** if both tripinfo and edgedata available: use formula `0.35*(improved_segments/total_segments) + 0.35*(improved_od_pairs/total_od_pairs) + 0.30*(ended/loaded)`
- **AND** improved_segments SHALL come from edgedata analysis results
- **AND** total_segments SHALL be computed as the number of edges recorded in baseline plan's edgedata.xml
- **AND** the coverage score SHALL be normalized to 0-100 range

#### Scenario: Efficiency score calculation

- **WHEN** computing efficiency score for a strategy
- **THEN** the system SHALL calculate improvement rate per control cost if cost data available
- **OR** the system SHALL calculate improvement rate per control intensity (e.g., number of control devices) if cost data not available
- **AND** the efficiency score SHALL be normalized to 0-100 range

#### Scenario: Reliability score calculation

- **WHEN** computing reliability score for a strategy with multiple random seed simulations
- **THEN** the system SHALL calculate standard deviation of effectiveness scores across seeds
- **AND** reliability score SHALL be `100 - (std_dev_of_effectiveness * 10)` capped at 0-100 range
- **AND** if only one seed available, reliability score SHALL default to 70

#### Scenario: Overall score aggregation

- **WHEN** all four dimension scores are computed
- **THEN** the system SHALL calculate overall score as weighted sum: `effectiveness * 0.40 + coverage * 0.25 + efficiency * 0.20 + reliability * 0.15`
- **AND** overall score SHALL be in 0-100 range

---

### Requirement: Strategy Ranking and Recommendation

The system SHALL rank control strategies by overall score and assign recommendation categories based on score thresholds.

#### Scenario: Strategy ranking by score

- **WHEN** overall scores are computed for all strategies
- **THEN** the system SHALL rank strategies in descending order by overall score
- **AND** each strategy SHALL have rank number (1, 2, 3, ...)
- **AND** ties SHALL be resolved by effectiveness score (higher effectiveness wins)

#### Scenario: Recommendation category assignment

- **WHEN** assigning recommendation category for a strategy
- **THEN** the system SHALL assign "强烈推荐" (Highly Recommended) if overall score >= 75
- **OR** the system SHALL assign "推荐" (Recommended) if overall score >= 60 and < 75
- **OR** the system SHALL assign "可选" (Optional) if overall score >= 45 and < 60
- **OR** the system SHALL assign "不推荐" (Not Recommended) if overall score < 45

#### Scenario: Ranking result structure

- **WHEN** generating ranking results
- **THEN** the system SHALL return JSON structure containing ranked_strategies array with rank, plan_id, plan_name, overall_score, recommendation, dimension scores, and key_improvements
- **AND** the system SHALL include comparison_table with all strategies' metrics side-by-side
- **AND** the system SHALL generate report_file path for HTML report

---

### Requirement: Ranking Report Generation

The system SHALL generate human-readable ranking reports in HTML format with visual comparisons.

#### Scenario: HTML report generation

- **WHEN** ranking analysis completes
- **THEN** the system SHALL generate HTML report saved in `frontend/control/optimization.html`
- **AND** the report SHALL include executive summary with top recommendation
- **AND** the report SHALL include radar chart comparing all strategies across four dimensions
- **AND** the report SHALL include comparison table with all metrics
- **AND** the report SHALL include detailed breakdown for each strategy

#### Scenario: Visual comparison charts

- **WHEN** generating charts for report
- **THEN** the system SHALL create radar chart with four axes (effectiveness, coverage, efficiency, reliability)
- **AND** each strategy SHALL be represented as a different colored line on radar chart
- **AND** the system SHALL create score breakdown bar chart showing dimension scores for top 3 strategies
- **AND** charts SHALL be embedded as PNG images in HTML report

---

### Requirement: Ranking API Endpoint

The system SHALL provide REST API endpoint for requesting strategy ranking analysis.

#### Scenario: Ranking request validation

- **WHEN** POST request to `/api/v1/analysis/batch/strategy-ranking` is received
- **THEN** the system SHALL validate that case_id exists
- **AND** the system SHALL validate that batch_id exists and belongs to case_id
- **AND** the system SHALL validate that baseline_plan_id exists in batch
- **AND** the system SHALL validate that all strategy_plan_ids exist in batch
- **AND** the system SHALL validate that all plans have completed simulation status
- **AND** the system SHALL return 400 Bad Request if validation fails with error details

#### Scenario: Ranking request with custom weights

- **WHEN** request includes ranking_criteria with custom weights
- **THEN** the system SHALL validate that weights sum to 1.0 (tolerance ±0.01)
- **AND** the system SHALL use custom weights for overall score calculation
- **OR** if ranking_criteria not provided, SHALL use default weights (0.40, 0.25, 0.20, 0.15)

#### Scenario: Successful ranking response

- **WHEN** ranking analysis completes successfully
- **THEN** the system SHALL return 200 OK with ranking_id, ranked_strategies array, comparison_table, and report_file path
- **AND** the system SHALL save ranking results to `cases/{case_id}/analysis/ranking/{ranking_id}/ranking_results.json`

---

### Requirement: UI Integration for Ranking Trigger

The system SHALL provide user interface for triggering strategy ranking from batch results view.

#### Scenario: Ranking button display

- **WHEN** user views batch results page for a completed batch
- **THEN** the UI SHALL display "生成优化方案" (Generate Optimization Plan) button
- **AND** button SHALL be enabled only if batch status is "completed"
- **AND** button SHALL be enabled only if batch contains at least 2 plans (baseline + 1 strategy)

#### Scenario: Ranking trigger interaction

- **WHEN** user clicks "生成优化方案" button
- **THEN** the UI SHALL send POST request to ranking API endpoint with case_id, batch_id and plan_ids
- **AND** the UI SHALL show loading indicator during analysis
- **AND** upon success, SHALL display ranking results in modal or embedded section
- **AND** upon error, SHALL show error message with details

#### Scenario: Ranking results display

- **WHEN** ranking results are returned from API
- **THEN** the UI SHALL display ranked list of strategies with rank, name, overall score, and recommendation category
- **AND** the UI SHALL color-code recommendations (green for 强烈推荐, blue for 推荐, yellow for 可选, red for 不推荐)
- **AND** the UI SHALL provide link to download HTML report
- **AND** the UI SHALL display radar chart comparing strategies

---

### Requirement: Baseline Plan Enforcement for Ranking

The system SHALL enforce that baseline plan exists in batch before allowing ranking analysis.

#### Scenario: Baseline plan presence check

- **WHEN** ranking request is received
- **THEN** the system SHALL verify that baseline_plan_id corresponds to a plan with type "baseline"
- **AND** if baseline plan not found, SHALL return 400 Bad Request with error "Baseline plan required for ranking analysis"

#### Scenario: Auto-baseline inclusion during batch creation

- **WHEN** batch is created without baseline_plan in plan_ids
- **THEN** the system SHALL automatically include baseline_plan as first plan in batch
- **AND** the system SHALL log warning "Baseline plan auto-added to batch for comparison purposes"

