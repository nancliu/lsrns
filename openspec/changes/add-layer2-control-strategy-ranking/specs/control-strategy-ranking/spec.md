# Specification: Control Strategy Ranking

## ADDED Requirements

### Requirement: Layer 1 Data Aggregation from summary.xml

The system SHALL aggregate 8 traffic metrics from Layer 1 results (summary.xml) to support strategy evaluation.

#### Scenario: Layer 1 metrics extraction

- **WHEN** ranking analysis is requested for a batch
- **THEN** the system SHALL extract 8 metrics from each plan's summary.xml including loaded, inserted, ended, running, waiting, teleports, collisions, and avgSpeed
- **AND** the system SHALL validate that baseline plan metrics are available for comparison
- **AND** the system SHALL exclude step metric from comparison (simulation duration is not a performance metric)

#### Scenario: Metric categorization

- **WHEN** processing extracted metrics
- **THEN** the system SHALL categorize metrics into vehicle flow (loaded, inserted, ended, running), congestion (waiting, teleports, collisions), and performance (avgSpeed)
- **AND** the system SHALL identify improvement direction for each metric (higher-is-better: ended, avgSpeed; lower-is-better: running, waiting, teleports, collisions)

#### Scenario: Optional enhanced data from EdgeData and TripInfo

- **WHEN** EdgeData or TripInfo analysis results are available
- **THEN** the system MAY optionally integrate road segment metrics (F2-D1, F2-D2) or OD pair metrics (G2-D1, G2-D3) to enhance scoring
- **AND** the system SHALL continue ranking with Layer 1 data only if enhanced data is unavailable

---

### Requirement: Multi-Criteria Scoring Algorithm

The system SHALL score each control strategy using a weighted multi-criteria evaluation with four dimensions: effectiveness, coverage, efficiency, and reliability.

#### Scenario: Effectiveness score calculation

- **WHEN** computing effectiveness score for a strategy
- **THEN** the system SHALL calculate weighted average of speed improvement (30%), travel time reduction (30%), delay reduction (25%), and congestion reduction (15%)
- **AND** the effectiveness score SHALL be normalized to 0-100 range
- **AND** improvements SHALL be calculated relative to baseline plan

#### Scenario: Coverage score calculation

- **WHEN** computing coverage score for a strategy
- **THEN** the system SHALL calculate weighted average of segment coverage (40%), OD pair coverage (30%), and vehicle coverage (30%)
- **AND** segment coverage SHALL be ratio of improved segments to total segments
- **AND** OD pair coverage SHALL be ratio of improved OD pairs to total OD pairs
- **AND** vehicle coverage SHALL be ratio of vehicles with improved trips to total vehicles

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
- **THEN** the system SHALL validate that batch_id exists
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
- **THEN** the UI SHALL display "生成策略排序" (Generate Strategy Ranking) button
- **AND** button SHALL be enabled only if batch status is "completed"
- **AND** button SHALL be enabled only if batch contains at least 2 plans (baseline + 1 strategy)

#### Scenario: Ranking trigger interaction

- **WHEN** user clicks "生成策略排序" button
- **THEN** the UI SHALL send POST request to ranking API endpoint with batch_id and plan_ids
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
