# parameter-form-layout Specification

## Purpose

Define requirements for the strategy parameter configuration form (Step 3 of strategy creation workflow) to ensure consistent layout, proper data loading from templates, clear time semantics, separated vehicle type configuration, and maintainable code structure.

## ADDED Requirements

### Requirement: Consistent Form Layout

The parameter configuration form SHALL use consistent spacing, alignment, and responsive design across all strategy types (VSS, TEC, DHS).

#### Scenario: Strategy name and description input fields with adequate width

- **GIVEN** user is on Step 3 (Configure Parameters)
- **WHEN** viewing the strategy name and description input fields
- **THEN** input fields SHALL occupy full width minus button space (flex: 1)
- **THEN** buttons SHALL have minimum width of 120px and SHALL NOT be squeezed or wrapped
- **THEN** on mobile (<768px), layout SHALL stack vertically with buttons full-width

#### Scenario: Uniform spacing across all parameter form groups

- **GIVEN** user configures parameters for any strategy type
- **WHEN** viewing the form
- **THEN** all `.form-group` elements SHALL have consistent margin-bottom (16px)
- **THEN** timeline and table spacing SHALL be identical for VSS, TEC, and DHS
- **THEN** spacing SHALL be defined using CSS variables (`--form-spacing-md`)

#### Scenario: Responsive design for narrow screens

- **GIVEN** user accesses form on a narrow screen (<768px)
- **WHEN** viewing parameter controls
- **THEN** form elements SHALL stack vertically
- **THEN** tables SHALL scroll horizontally if needed
- **THEN** buttons SHALL be full-width for touch accessibility

### Requirement: Template Default Value Loading

The parameter form SHALL load default values from template JSON `default_value` fields during form initialization.

#### Scenario: Load default values for basic parameter types

- **GIVEN** template has parameter with `default_value` defined
- **WHEN** form is generated
- **THEN** for number/string/enum types, input value SHALL be set to `default_value`
- **THEN** for boolean types, checkbox SHALL be checked if `default_value` is true
- **THEN** if `default_value` is null, input SHALL remain empty

#### Scenario: Load default values for step_array and interval_array

- **GIVEN** template has `speed_steps` with default_value `[{time_hours: 7, speed_kmh: 60}, ...]`
- **WHEN** form is generated
- **THEN** table SHALL be pre-populated with rows from default_value array
- **THEN** each row SHALL display the time and speed from default_value
- **THEN** timeline SHALL be initialized with the default steps

#### Scenario: Display parameter constraints from schema

- **GIVEN** parameter has `min_value`, `max_value`, or `unit` defined
- **WHEN** form is displayed
- **THEN** constraint hint SHALL show: `{unit} · 范围: {min}-{max}`
- **THEN** required parameters SHALL display red asterisk `*`
- **THEN** constraints SHALL be used for client-side validation

### Requirement: Clear Time Semantics (Point vs Interval)

The parameter form SHALL clearly distinguish between "time point" (时刻) and "time interval" (时段) semantics in UI labels and table columns.

#### Scenario: VSS uses time point semantics

- **GIVEN** user configures VSS strategy
- **WHEN** viewing speed steps table
- **THEN** column labels SHALL be: `时间(小时)` | `限速(km/h)` | `操作`
- **THEN** hint SHALL say: `时刻表示，例如 7 表示 7:00 开始限速`
- **THEN** timeline visualization SHALL use point markers
- **THEN** data structure SHALL use `time_hours` field

#### Scenario: TEC/DHS use time interval semantics

- **GIVEN** user configures TEC or DHS strategy
- **WHEN** viewing interval table
- **THEN** column labels SHALL be: `开始时间(小时)` | `结束时间(小时)` | `[状态/流量]` | `操作`
- **THEN** hint SHALL say: `时段表示，例如 7-9 表示 7:00-9:00`
- **THEN** timeline visualization SHALL use colored segments
- **THEN** data structure SHALL use `begin_hours` and `end_hours` fields

### Requirement: Separated Vehicle Type Configuration

Vehicle type configuration SHALL be a global strategy-level setting, NOT configured per time interval.

#### Scenario: Remove vehicle type from DHS/TEC interval tables

- **GIVEN** user configures DHS or TEC strategy
- **WHEN** viewing interval table
- **THEN** table SHALL NOT contain `allowed_vehicle_types` or `disallow_vehicle_types` columns
- **THEN** interval rows SHALL only contain time and status/flow fields
- **THEN** vehicle types SHALL be configured in a separate global section

#### Scenario: Global vehicle type configuration section

- **GIVEN** template has `allowed_vehicle_types` or `disallow_vehicle_types` parameter
- **WHEN** form is generated
- **THEN** a dedicated vehicle type section SHALL appear after strategy name/description
- **THEN** section SHALL contain checkboxes for all vehicle types
- **THEN** checkboxes SHALL be initialized from template `default_value`

#### Scenario: Dynamic labels for allow vs disallow mode

- **GIVEN** template has `allowed_vehicle_types` parameter
- **WHEN** displaying vehicle type section
- **THEN** label SHALL read: `允许的车型`
- **THEN** hint SHALL read: `仅这些车型可使用此策略`

- **GIVEN** template has `disallow_vehicle_types` parameter
- **WHEN** displaying vehicle type section
- **THEN** label SHALL read: `禁止的车型`
- **THEN** hint SHALL read: `这些车型禁止使用此策略`

### Requirement: Unified Edge Source from Step 2

The parameter form SHALL use edge selection from Step 2 and SHALL NOT display redundant edge input fields.

#### Scenario: Display read-only edge list from Step 2

- **GIVEN** user completed Step 2 (edge selection)
- **WHEN** viewing Step 3 parameter form
- **THEN** a read-only table SHALL display selected edges
- **THEN** table SHALL show: Edge ID, Route Code, Road Code, Milepost Range, Direction
- **THEN** table SHALL use data from `sessionStorage.strategy_selected_edges`

#### Scenario: Hide affected_edges input field

- **GIVEN** template has `affected_edges`, `affected_segments`, or `entrance_ids` parameter
- **WHEN** form is generated
- **THEN** these parameters SHALL be skipped (not rendered as input fields)
- **THEN** form SHALL include a "返回修改路段" button linking to Step 2

### Requirement: Clear Validation and User Prompts

The parameter form SHALL provide clear validation feedback and avoid redundant hints.

#### Scenario: Time order validation for intervals

- **GIVEN** user inputs interval with begin_hours >= end_hours
- **WHEN** end_hours input loses focus
- **THEN** error message SHALL display: `开始时间({begin})必须小于结束时间({end})`
- **THEN** input SHALL have red border
- **THEN** error SHALL clear when corrected

#### Scenario: Value range validation

- **GIVEN** parameter has min_value = 0 and max_value = 120
- **WHEN** user inputs value outside range (e.g., -5 or 150)
- **THEN** error message SHALL display: `{参数名}必须在{min}-{max}范围内，当前值: {value}`
- **THEN** submit button SHALL be disabled until corrected

#### Scenario: Delete row confirmation

- **GIVEN** user clicks delete button on a table row
- **WHEN** delete is triggered
- **THEN** confirm dialog SHALL display: `确定要删除这一行吗？`
- **THEN** row SHALL only be deleted if user confirms

#### Scenario: Non-redundant hint text

- **GIVEN** parameter has both parameter-level constraints and control-level hints
- **WHEN** displaying hints
- **THEN** parameter-level hint SHALL only show: `{unit} · 范围: {min}-{max}`
- **THEN** control-level hint SHALL only show: operational guidance (e.g., `点击「添加步骤」增加新行`)
- **THEN** hints SHALL NOT repeat common phrases like `使用表格编辑器配置...`

### Requirement: Maintainable Code Structure

The `parameter_form.js` file SHALL eliminate code duplication and reduce function complexity.

#### Scenario: Unified timeline update function

- **GIVEN** parameter form contains timeline visualization
- **WHEN** table data changes
- **THEN** a single `updateTimeline(tbody, options)` function SHALL handle all types
- **THEN** function SHALL accept configuration: `{timeField, valueField, visualizationType, useInterval}`
- **THEN** no duplicate functions like `updateDHSTimelineFromTable`, `updateFlowTimelineFromTable` SHALL exist

#### Scenario: Unified row addition function

- **GIVEN** user clicks "Add Row" button
- **WHEN** adding a row to any parameter table
- **THEN** a single `addRow(tbody, config)` function SHALL handle all row types
- **THEN** function SHALL accept configuration: `{rowType, data, schema}`
- **THEN** no duplicate functions like `addDHSIntervalRow`, `addFlowIntervalRow` SHALL exist

#### Scenario: Extracted validation functions

- **GIVEN** parameter form requires input validation
- **WHEN** validation is performed
- **THEN** validation logic SHALL be centralized in `validators` object
- **THEN** validators SHALL include: `timeOrder`, `timeRange`, `speedRange`, `flowRange`
- **THEN** validators SHALL return: `{valid: boolean, message: string}`

#### Scenario: Function length and complexity limits

- **GIVEN** parameter form code
- **WHEN** reviewing functions
- **THEN** all functions SHALL be ≤50 lines (target: ≤30 lines)
- **THEN** functions SHALL have ≤5 parameters (or use config objects)
- **THEN** nesting depth SHALL be ≤3 levels
