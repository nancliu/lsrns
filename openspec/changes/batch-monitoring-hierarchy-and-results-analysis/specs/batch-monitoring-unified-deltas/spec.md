## MODIFIED Requirements

### Requirement: Unified Batch List Displays All Batch States

The system SHALL display batches in a hierarchical case-grouped view (Case → Batches) instead of flat list. Case groups SHALL be sortable by latest batch time, collapsible/expandable, and maintain all existing batch status indicators and progress tracking features within each group.

#### Scenario: Display All Batches Grouped by Case

- **WHEN** user navigates to "批次监控 (Batch Monitoring)" tab
- **AND** system has 15 batches across 3 cases
- **THEN** batches organized as case groups (not flat list)
- **AND** each case group shows:
  - Case ID, case name, batch count
  - Latest batch status badge
  - Toggle button [−/+] to expand/collapse
- **AND** case groups sorted by latest batch time (newest first)
- **AND** batch cards appear within respective case groups
- **AND** all status badges and progress bars work as before

---

#### Scenario: 展开和折叠Case分组

- **WHEN** user clicks toggle button [−] next to case group
- **THEN** batch cards in that group collapse (hidden)
- **AND** toggle button changes to [+]
- **AND** other case groups remain visible and unaffected
- **WHEN** user clicks [+], group expands again

---

#### Scenario: Case分组按最新批次排序

- **WHEN** case_001 latest batch is 2025-11-02 10:00
- **AND** case_002 latest batch is 2025-11-01 15:30
- **AND** case_003 latest batch is 2025-11-02 09:00
- **THEN** case groups appear in order: case_001, case_003, case_002 (newest first)

---

### Requirement: Batch Filtering Within Case Scope

The system SHALL apply status filters within the scope of each case group independently. When a filter is applied, only batches within the current context are filtered; other case groups remain unfiltered.

#### Scenario: 在Case内按状态筛选批次

- **WHEN** user selects status filter "已完成" (completed)
- **AND** case_001 contains 5 batches (2 running, 2 completed, 1 failed)
- **THEN** only completed batches within case_001 are shown
- **AND** other case groups remain visible (unfiltered)
- **AND** filtering isolated to current case context

---

### Requirement: Batch Results Comparison (Layer 1)

The system SHALL provide results comparison view triggered by "查看结果" button on batch cards. Results view SHALL display batch summary, comparison table (baseline vs control plans with metrics and improvement rates), and visualizations based on aggregated summary.xml data.

#### Scenario: 点击批次卡片查看结果对比

- **WHEN** user clicks "查看结果" button on completed batch card
- **THEN** results view modal/page opens
- **AND** displays batch summary:
  - Batch ID, case name, plan count, output level, seed info
- **AND** displays comparison table:
  - Columns: plan name, meanTravelTime, improvement rate, ended, improvement rate, meanWaitingTime, improvement rate, maxRunningPersons
  - Baseline row (bold, gray background)
  - Control plan rows (with improvement rates in green/red)
- **AND** displays visualizations (bar charts)
- **AND** close button returns to batch list

---

#### Scenario: 改善率计算和展示

- **WHEN** baseline meanTravelTime = 1201.67s, plan_001 = 1051.67s
- **THEN** system calculates: (1201.67 - 1051.67) / 1201.67 × 100 = +12.5%
- **AND** displays: "+12.5% ↑" in green
- **AND** green indicates improvement (positive direction for time metrics)

---

#### Scenario: 多项指标同时对比

- **WHEN** results view displays comparison table
- **THEN** includes metrics:
  - meanTravelTime (seconds, lower is better)
  - ended (vehicle count, higher is better)
  - meanWaitingTime (seconds, lower is better)
  - maxRunningPersons (vehicle count, higher is better)
- **AND** improvement rates calculated correctly per metric
- **AND** each metric has separate improvement rate column

---

#### Scenario: 缺少结果数据时的处理

- **WHEN** some summary.xml files missing for a plan
- **THEN** system loads partial results (available seeds)
- **AND** displays warning: "Plan {plan_id}: data incomplete (2/3 seeds available)"
- **AND** shows available data in comparison table
- **AND** other plans display normally

---

### Requirement: Results Visualization

The system SHALL provide interactive charts and visualizations for results comparison. Visualizations SHALL include bar charts comparing metrics across plans, color-coded improvement rates, and responsive design for mobile/tablet/desktop.

#### Scenario: 柱状图对比各方案指标

- **WHEN** user views results modal
- **THEN** system displays bar chart showing:
  - X-axis: plans (baseline, plan_001, plan_002, ...)
  - Y-axis: metric values
  - Bars grouped/colored by plan
  - Legend showing plan names
- **AND** chart is responsive and readable on all devices

---

#### Scenario: 改善率可视化

- **WHEN** results loaded
- **THEN** improvement rates color-coded:
  - Green for positive (improvement)
  - Red for negative (degradation)
  - Arrow symbols: ↑ for improvement, ↓ for degradation
- **AND** magnitude clear (e.g., "+12.5%" vs "+0.2%")

---

## NEW Requirements

### Requirement: Results Analysis Layer 1 (Summary Statistics)

The system SHALL aggregate summary.xml files from all simulation runs per plan, calculate mean/std_dev/min/max metrics across seeds, and provide statistical summaries for comparison. Layer 1 focuses on quick-overview metrics from summary.xml; detailed analysis (tripinfo/edgedata) deferred to Layer 2.

#### Scenario: 汇总统计数据计算

- **WHEN** plan_001 has 3 simulation runs (seeds 66, 67, 68)
- **AND** all summary.xml files available
- **THEN** system calculates:
  - meanTravelTime: mean across 3 runs
  - Standard deviation across runs
  - Min/Max values
- **AND** returns aggregated metrics with confidence measures

---

#### Scenario: 结果数据聚合和缺失处理

- **WHEN** plan has 3 runs but seed 68 summary.xml missing
- **THEN** system aggregates 2 available runs
- **AND** calculates mean from 2 samples
- **AND** notes sample_count=2 (not 3) in response
- **AND** logs warning about missing seed 68
- **AND** returns valid partial results for comparison

---

### Requirement: 输出级别展示

The system SHALL display batch output configuration in results view, showing the output level (minimal/standard/full) that was applied to all simulations in the batch. This helps users understand what data was available for analysis.

#### Scenario: 显示批次输出级别

- **WHEN** batch created with output_level="standard"
- **AND** user views batch details/results
- **THEN** system displays: "输出级别: standard (完整输出)"
- **OR** for minimal: "输出级别: minimal (仅汇总数据)"
- **OR** for full: "输出级别: full (完整输出+龙门架数据)"
- **AND** helps user understand available data

---
