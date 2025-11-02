## MODIFIED Requirements

### Requirement: 用户可以创建批量仿真批次 (User can create batch optimization)

The system SHALL allow users to create batch optimization jobs with unified output configuration, automatic baseline plan inclusion, and configurable random simulation counts. All plans in a batch MUST use identical output settings (summary/tripinfo/edgedata) and seed sequences to ensure fair comparison.

#### Scenario: 创建批次时自动包含基准方案并统一输出配置

- **WHEN** user creates batch with plan_ids=["plan_001", "plan_002"], output_level="standard", num_seeds=3
- **AND** baseline_plan is NOT in the list
- **THEN** system auto-includes baseline_plan at beginning of plan list
- **AND** generates simulation_config.json with unified output settings:
  - summary_xml: true
  - tripinfo_xml: true
  - edgedata_xml: true
  - seed_sequence: [66, 67, 68]
- **AND** creates 9 tasks (3 plans × 3 seeds)
- **AND** all tasks read same simulation_config.json
- **AND** returns 201 with batch_id, plan_count=3, total_tasks=9

---

#### Scenario: 用户选择不同的输出级别

- **WHEN** user creates batch with output_level="minimal"
- **THEN** system creates simulation_config.json with:
  - summary_xml: true (always)
  - tripinfo_xml: false
  - edgedata_xml: false
  - e1_detectors: false
- **AND** configuration applied to ALL plans (no per-plan overrides)
- **AND** batch created successfully

---

#### Scenario: 随机仿真次数超出范围

- **WHEN** user creates batch with num_seeds=15 (out of range [1-10])
- **THEN** system validates num_seeds range
- **AND** returns 400 Bad Request: "num_seeds must be between 1 and 10"
- **AND** batch NOT created

---

### Requirement: 输出配置一致性验证

The system SHALL ensure all plans in a batch use identical output configuration, enforced at creation time. Configuration saved as `simulation_config.json` in batch directory, readable by all tasks, preventing per-plan override.

#### Scenario: 验证批次内所有方案输出配置一致

- **WHEN** batch creation reaches finalization step
- **THEN** system validates simulation_config.json exists and is valid JSON
- **AND** verifies seed_sequence length matches num_seeds
- **AND** returns batch with validation_status="valid"
- **AND** logs: "Batch output configuration validation passed"

---

#### Scenario: 配置不一致则批次创建失败

- **WHEN** batch creation attempts to save but simulation_config.json write fails
- **THEN** system detects configuration creation failure
- **AND** returns error: "Failed to create unified output configuration"
- **AND** rolls back batch creation (no files saved)

---

## NEW Requirements

### Requirement: 结果分析 API 端点

The system SHALL provide `GET /api/v1/control/optimization/batch/{batch_id}/results` endpoint that aggregates all summary.xml files from a completed batch and returns comparison metrics, improvement rates, and statistical summaries for all plans.

#### Scenario: 获取批次聚合结果

- **WHEN** user requests GET /api/v1/control/optimization/batch/batch_001/results
- **AND** batch_001 is completed with 3 plans × 3 seeds
- **AND** all summary.xml files exist
- **THEN** system parses all summary.xml files
- **AND** aggregates per-plan metrics (mean, std_dev, min, max) across seeds
- **AND** identifies baseline_plan and calculates improvement_rates for control plans
- **AND** returns 200 OK with JSON containing:
  - baseline_metrics (aggregated)
  - plans[] with metrics and improvement_rates
  - sample_count per plan

---

#### Scenario: 缺少结果数据

- **WHEN** batch is completed but some summary.xml files missing
- **THEN** system aggregates available results
- **AND** skips missing files with warning log
- **AND** returns partial results
- **AND** returns 200 OK with sample_count < num_seeds

---

#### Scenario: 批次不存在

- **WHEN** user requests results for non-existent batch
- **THEN** system returns 404 Not Found: "Batch not found"

---
