# Strategy Templates Update - Implementation Tasks

## 1. Template Update and Regeneration

### 1.1 VSS Templates Update

- [ ] 1.1.1 Regenerate `templates/control_strategies/variable_speed_sign/vss_moderate.json`

  - Update `template_version` from 1.0 to 2.0
  - Add `sumo_element` mappings for each parameter
  - Define `speed_steps` parameter as `step_array` type
  - Add conversion factors (hours→seconds: 3600, km/h→m/s: 1/3.6)
  - Keep default speed range 80-100 km/h
- [ ] 1.1.2 Regenerate `vss_strict.json`

  - Similar structure to vss_moderate
  - Adjust speed range to 60-80 km/h (more aggressive)
  - Support more speed steps (up to 5 for incident response)
  - Default intervals same as moderate
- [ ] 1.1.3 Add new template: `vss_weather_based.json` (weather-based progressive limiting)

  - Suitable for fog, rain, snow conditions
  - Support 6+ speed steps for weather progression
  - Example: 120→100→80→60→100→120 km/h (fog clearing pattern)
  - Add weather_condition field (fog, rain, snow, incident)
  - Include preset profiles for each weather type
- [ ] 1.1.4 Add new template: `vss_upstream_warning.json` (upstream preemptive slowdown)

  - Early slowdown 3-15 minutes before downstream event
  - Exactly 3 speed steps (normal→reduced→recovery)
  - Add warning_advance_minutes parameter
  - Add optional bottleneck_location for coordination with DHS
  - Default: Slow from 120→80 km/h at 6:55, restore at 7:00
- [ ] 1.1.5 Add new template: `vss_lane_differentiated.json` (per-lane speed control)

  - Support different speeds for different lanes
  - Add lane_configurations array (lane_index, speed_kmh pairs)
  - Generate separate VSS strategies for each lane group
  - Example: Lane 0 (truck) 80 km/h, Lanes 1-2 (cars) 100 km/h

### 1.2 DHS Template Update

- [ ] 1.2.1 Regenerate `templates/control_strategies/dynamic_hard_shoulder/dhs_peak_hours.json`

  - Update to version 2.0
  - Replace `affected_segments` with `affected_edges` (more precise)
  - Add `hard_shoulder_lane_index` parameter (default 3 for rightmost lane)
  - Replace `intervals` with proper time-based `interval_array`
  - Change `allowed_vehicle_types` to SUMO enum array
  - SUMO enums: passenger, bus, truck, emergency
- [ ] 1.2.2 Validate lane indexing

  - Confirm lane 3 is rightmost for 4-lane highways
  - Document lane indexing convention in template description
- [ ] 1.2.3 Add new template: `dhs_passenger_only.json` (passenger-only hard shoulder)

  - Restrict to passenger + bus, ban trucks and delivery
  - Add allowed_vehicle_types pre-selected to ["passenger", "bus"]
  - Add prohibited_types display showing blocked types
  - Default intervals: Peak hours only (7-9, 17-19)
  - Warning: "Truck ban may create congestion in freight corridors"
- [ ] 1.2.4 Add new template: `dhs_peak_multi_interval.json` (complex multi-interval management)

  - Support 5+ interval definitions for full 24-hour coverage
  - Predefined pattern: Night(closed)→Morning peak(open)→Midday(closed)→Evening peak(open)→Night(closed)
  - Standard time boundaries: 0-7, 7-9, 9-17, 17-19, 19-24 hours
  - Validation: Ensure no gaps in 24-hour coverage
  - Each interval clearly labeled with status and allowed types

### 1.3 TEC Templates Update

- [ ] 1.3.1 Regenerate `tec_entrance_close.json`

  - Update to version 2.0
  - Change `entrance_ids` to `entrance_edge` (single entrance)
  - Replace `time_intervals` with `closure_intervals` (array of [begin, end] seconds)
  - Add `allowed_vehicle_types` for selective closure (empty = all blocked)
  - Control mode: "closure"
- [ ] 1.3.2 Regenerate `tec_truck_ban.json`

  - Change name to `tec_vehicle_restriction.json` (more general)
  - Add vehicle type filtering
  - TEC type: "rerouter" mode (redirect rather than close)
- [ ] 1.3.3 Create new template: `tec_metering.json` (flow control)

  - Control mode: "metering"
  - Uses `<calibrator>` in SUMO
  - Parameters: flow_intervals with vehicles_per_hour and target_speed
  - Default: 480 vehicles/hour normal, 180 peak
- [ ] 1.3.4 Add new template: `tec_metering_advanced.json` (time-varying ramp metering)

  - Support 4+ flow intervals with different rates throughout day
  - Predefined flow profile: 480→180→480→300→480 vehsPerHour
  - Morning peak reduction, evening lighter control
  - Each interval includes entry speed calibration (8-15 m/s)
  - Include visual flow rate graph during configuration
  - Validation: Flow rates in 0-2000 veh/hour range
- [ ] 1.3.5 Add new template: `tec_truck_ban.json` (truck restriction during peak hours)

  - Support 1-3 entrance edges per toll station
  - Disallow types: ["truck", "trailer"] (pre-selected)
  - Typical times: Morning 7-9, Evening 17-19
  - Predefined patterns: Full day ban, or peak-only restriction
  - Note: "Truck bans redirect freight to alternative routes"
- [ ] 1.3.6 Add new template: `tec_closure_complete.json` (full entrance blockage)

  - Support entrance arrays (multiple entries)
  - allowed_types: Empty by default (all vehicles blocked)
  - Add reason field: Enum ["maintenance", "emergency", "congestion_relief"]
  - Warning: "Complete closure redirects ALL vehicles - ensure alternatives exist"
  - Typical duration: 1-4 hours

### 1.4 Create Template Index

- [ ] 1.4.1 Create/update `templates/control_strategies/templates_index.json`
  ```json
  {
    "templates": [
      {"template_id": "vss_moderate", "type": "VSS", "version": "2.0", "name": "可变限速 - 中等控制"},
      {"template_id": "vss_strict", "type": "VSS", "version": "2.0", "name": "可变限速 - 严格控制"},
      {"template_id": "vss_weather_based", "type": "VSS", "version": "2.0", "name": "可变限速 - 天气应急"},
      {"template_id": "vss_upstream_warning", "type": "VSS", "version": "2.0", "name": "可变限速 - 上游预警"},
      {"template_id": "vss_lane_differentiated", "type": "VSS", "version": "2.0", "name": "可变限速 - 分车道控制"},
      {"template_id": "dhs_peak_hours", "type": "DHS", "version": "2.0", "name": "应急车道开放"},
      {"template_id": "dhs_passenger_only", "type": "DHS", "version": "2.0", "name": "应急车道 - 仅客车"},
      {"template_id": "dhs_peak_multi_interval", "type": "DHS", "version": "2.0", "name": "应急车道 - 多时段管理"},
      {"template_id": "tec_metering", "type": "TEC", "version": "2.0", "name": "收费入口 - 限流"},
      {"template_id": "tec_metering_advanced", "type": "TEC", "version": "2.0", "name": "收费入口 - 时变限流"},
      {"template_id": "tec_entrance_close", "type": "TEC", "version": "2.0", "name": "收费入口 - 关闭"},
      {"template_id": "tec_truck_ban", "type": "TEC", "version": "2.0", "name": "收费入口 - 货车限行"},
      {"template_id": "tec_closure_complete", "type": "TEC", "version": "2.0", "name": "收费入口 - 完全关闭"}
    ],
    "total_templates": 13,
    "version": "2.0",
    "last_updated": "2025-10-24",
    "categorization": {
      "VSS": 5,
      "DHS": 3,
      "TEC": 5
    }
  }
  ```

## 2. Backend Parameter Validation

### 2.1 Create Parameter Validator Module

- [ ] 2.1.1 Create `shared/control_tools/parameter_validator.py`

  - Class: `ParameterValidator`
  - Method: `validate_parameter_value(param_schema, value) -> (bool, List[str])`
    - Check type compatibility
    - Check min/max constraints
    - Check enum values (if applicable)
    - Return (is_valid, error_messages)
- [ ] 2.1.2 Implement constraint validation

  - Integer constraints: min_value, max_value, step
  - Number constraints: min_value, max_value, precision
  - String constraints: pattern, length
  - Enum constraints: allowed_values only
  - Array constraints: min_items, max_items, unique_keys
- [ ] 2.1.3 Implement unit conversion functions

  - Function: `convert_display_to_sumo(value, param_schema) -> value`
    - Hours → Seconds (multiply by 3600)
    - km/h → m/s (divide by 3.6)
    - Return SUMO-compatible value
  - Inverse: `convert_sumo_to_display(value, param_schema)`
- [ ] 2.1.4 Implement SUMO-specific validation

  - Function: `validate_SUMO_vehicle_types(types: List[str]) -> bool`
    - Only allows: passenger, bus, truck, emergency
  - Function: `validate_time_ordering(steps: List[Dict]) -> bool`
    - Times must be in ascending order
  - Function: `validate_continuous_edges(edges: List[str]) -> bool`
    - Check if edges form connected path (using network graph)
- [ ] 2.1.5 Add validation for speed steps (VSS)

  - At least 1 step, max 10 steps
  - Times in ascending order
  - All times within 0-86400 seconds
  - Speed values 30-130 km/h
- [ ] 2.1.6 Add validation for intervals (DHS, TEC)

  - Begin < End
  - Times within 0-86400 seconds
  - No overlaps (warning, not error)

### 2.2 Enhance Template Parser

- [ ] 2.2.1 Update `shared/control_tools/template_parser.py`

  - Function: `load_template_with_schema(template_id) -> Dict`
    - Load template JSON with full parameter schema
    - Include SUMO mappings (sumo_element, sumo_unit, conversion_factor)
    - Include UI metadata (parameter_type, display_unit)
  - Preserve backward compatibility with v1.0 templates
- [ ] 2.2.2 Add schema validation

  - Function: `validate_template_schema(template: Dict) -> bool`
    - Ensure all required fields present
    - Validate parameter schemas are well-formed
    - Check for missing conversion factors for unit-bearing params

### 2.3 Create API Validation Endpoint

- [ ] 2.3.1 Add validation routes to `api/routes/control_strategy_routes.py`

  - Endpoint: `POST /api/v1/control/strategies/validate-params`
    - Input: {template_id, parameters}
    - Validate all parameters against template schema
    - Return: {valid: bool, errors: List[str], warnings: List[str]}
- [ ] 2.3.2 Add XML preview endpoint

  - Endpoint: `POST /api/v1/control/strategies/generate-xml-preview`
    - Input: {template_id, parameters}
    - Validate parameters first
    - Generate SUMO XML fragment
    - Return: {xml_content: str, valid: bool, validation_message: str}

## 3. XML Generation Enhancement

### 3.1 Update Additional Generator

- [ ] 3.1.1 Enhance `shared/control_tools/additional_generator.py`

  - Update all generation functions to use parameter schemas
  - Apply unit conversions (hours→seconds, km/h→m/s)
  - Generate proper SUMO XML elements
- [ ] 3.1.2 VSS XML generation with speed steps

  - Function: `generate_vss_xml(strategy) -> str`
    - Extract speed_steps array
    - Convert times from hours to seconds
    - Generate `<variableSpeedSign>` with `<step>` elements
    - Example output:
      ```xml
      <variableSpeedSign id="strategy_001" edges="edge_100 edge_101">
        <step time="0" speed="27.78"/>
        <step time="25200" speed="22.22"/>
      </variableSpeedSign>
      ```
- [ ] 3.1.3 DHS XML generation with lane indices

  - Function: `generate_dhs_xml(strategy) -> str`
    - Extract hard_shoulder_lane_index
    - Generate `<rerouter>` with `<interval>` elements
    - Create `<closingLaneReroute>` for each edge + lane combo
    - Include allowed vehicle types in `allow` attribute
- [ ] 3.1.4 TEC XML generation with flow control

  - Function: `generate_tec_xml(strategy) -> str`
    - If mode == "metering": Generate `<calibrator>` with `<flow>` elements
    - If mode == "closure": Generate `<rerouter>` or `<closingReroute>`
    - Convert vehicles/hour to SUMO units if needed
- [ ] 3.1.5 Add XML validation after generation

  - Function: `validate_generated_xml(xml_content: str) -> (bool, str)`
    - Use ElementTree to parse and validate
    - Check for well-formed XML
    - Return validation result

## 4. Frontend Parameter Form

### 4.1 Dynamic Form Generator

- [ ] 4.1.1 Create `frontend/control/js/parameter_form.js`

  - Function: `generateFormFromTemplate(templateId)`
    - Fetch template with schema via GET `/api/v1/control/templates/{templateId}`
    - Parse parameter types
    - Generate appropriate HTML controls for each parameter
- [ ] 4.1.2 Implement parameter control rendering

  - Function: `renderParameterControl(parameter_schema, parameter_name)`
    - Integer: `<input type="number">` with min/max
    - Number: `<input type="number" step="0.01">`
    - Enum: `<select>` with options from enum_values
    - Enum_array: `<div>` with checkboxes for each option
    - Edge_array: Custom input with edge ID suggestions
    - Return HTML string for control
- [ ] 4.1.3 Add time interval picker component

  - Function: `renderTimeRangePicker(parameter_schema)`
    - Two number inputs: start_hour (0-24), end_hour (0-24)
    - Display format: "HH:00" (e.g., "07:00")
    - Visual timeline bar showing covered hours
    - Auto-convert to seconds for SUMO before submission
- [ ] 4.1.4 Add speed steps editor (VSS)

  - Function: `renderStepArrayEditor(parameter_schema, initial_values)`
    - Table with Time (hours) and Speed (km/h) columns
    - Add/Remove row buttons
    - Drag-to-reorder rows
    - Validate time ordering
- [ ] 4.1.5 Add flow interval editor (TEC)

  - Function: `renderFlowIntervalEditor(parameter_schema)`
    - Table: Begin time, End time, Vehicles/hour, Target speed (km/h)
    - Add/Remove interval buttons
    - Time picker for range selection
    - Vehicle count spinner

### 4.2 Form Validation

- [ ] 4.2.1 Implement real-time validation

  - On blur/change event: Call `validateParameter(paramSchema, value)`
  - Check local validation rules immediately
  - Show error/warning message below input
  - Color code: Error (red), Warning (yellow), Valid (green)
- [ ] 4.2.2 Add constraint violation messages

  - Speed < 30: "Speed below highway minimum"
  - Speed > 130: "Speed exceeds highway maximum"
  - Overlapping times: "Warning: 7:00-10:00 and 9:00-11:00 overlap"
  - Out-of-order steps: "Error: Time steps must be in ascending order"
- [ ] 4.2.3 Implement form submission validation

  - Before submitting: POST to `/api/v1/control/strategies/validate-params`
  - Show loading spinner during validation
  - Display server-side errors prominently
  - Prevent form submission if validation fails

### 4.3 XML Preview Component

- [ ] 4.3.1 Create XML preview panel

  - Create `frontend/control/components/xml_viewer.html`
  - Div for syntax-highlighted XML display
  - Buttons: Copy to Clipboard, Download XML
  - Collapse/expand toggle
- [ ] 4.3.2 Implement XML preview generation

  - Function: `generateXMLPreview(templateId, parameters)`
    - Debounce calls (200ms delay after last change)
    - Only generate if form passes local validation
    - POST to `/api/v1/control/strategies/generate-xml-preview`
    - Display returned XML with syntax highlighting
- [ ] 4.3.3 Add syntax highlighting

  - Use highlight.js library for XML highlighting
  - Function: `highlightXML(xmlContent)`
    - Color tags (blue), attributes (red), text (black)
    - Add line numbers
- [ ] 4.3.4 Add copy and download functionality

  - Button: "Copy XML" → copies to clipboard
  - Button: "Download XML" → downloads as `.add.xml` file

### 4.4 UI Components and Helpers

- [ ] 4.4.1 Create vehicle type multi-select component

  - Checkboxes for: passenger, bus, truck, emergency
  - Each with label and description (Chinese)
  - Default selection: passenger, bus, truck
- [ ] 4.4.2 Create edge selector component

  - Input field with autocomplete
  - Suggestions from network database
  - Add/Remove buttons for array input
  - Display edge properties (length, lanes, route)
- [ ] 4.4.3 Create loading and error states

  - Show spinner during form generation
  - Show skeleton loaders for template loading
  - Display error messages with retry option

## 5. Integration and Testing

### 5.1 Backend Unit Tests

- [ ] 5.1.1 Create `tests/unit/test_parameter_validator.py`

  - Test speed validation: `test_validate_speed_in_range`, `test_validate_speed_out_of_range`
  - Test time validation: `test_validate_time_ordering`, `test_validate_time_range`
  - Test enum validation: `test_validate_vehicle_types`, `test_validate_invalid_vehicle_type`
  - Test array validation: `test_validate_edge_array`, `test_validate_step_array`
  - Test unit conversion: `test_convert_hours_to_seconds`, `test_convert_kmh_to_ms`
- [ ] 5.1.2 Create `tests/unit/test_template_parser.py`

  - Test loading v2.0 template: `test_load_vss_moderate_v2`
  - Test schema parsing: `test_parse_parameter_schema`
  - Test backward compatibility: `test_load_v1_template_still_works`
  - Test missing schema handling: `test_missing_parameter_in_schema`
- [ ] 5.1.3 Create `tests/unit/test_additional_generator_v2.py`

  - Test VSS generation: `test_generate_vss_xml_with_steps`
  - Test DHS generation: `test_generate_dhs_xml_with_intervals`
  - Test TEC metering generation: `test_generate_tec_calibrator_xml`
  - Test unit conversion in XML: `test_vss_speed_converted_to_ms`
  - Test XML validation: `test_generated_xml_is_well_formed`
- [ ] 5.1.4 Create `tests/unit/test_api_validation_endpoints.py`

  - Test POST /validate-params: `test_validate_params_valid_input`
  - Test validation errors: `test_validate_params_with_errors`
  - Test XML preview: `test_generate_xml_preview_endpoint`
  - Test invalid template: `test_validate_params_unknown_template`

### 5.2 Frontend Unit Tests

- [ ] 5.2.1 Create `tests/unit/frontend/test_parameter_form.js` (if using Jest)
  - Test form generation: `test_generate_form_from_vss_template`
  - Test control rendering: `test_render_integer_control`, `test_render_enum_control`
  - Test validation: `test_validate_speed_on_change`
  - Test unit conversion: `test_convert_hours_to_seconds_in_form`

### 5.3 Integration Tests

- [ ] 5.3.1 Create `tests/integration/test_strategy_template_workflow.py`

  - Test full workflow: Load template → Fill form → Validate → Generate XML
  - Test: Create VSS strategy from template
  - Test: Create DHS strategy from template
  - Test: Create TEC metering strategy from template
  - Test: Backward compatibility with v1.0 strategies
- [ ] 5.3.2 Test parameter validation chain

  - Local validation → Backend validation → XML generation
  - Test error propagation at each stage

### 5.4 E2E Tests

- [ ] 5.4.1 Create `tests/e2e/test_strategy_parameter_configuration.spec.js`

  - Test: User selects VSS template and fills form
    - Scenario: Select vss_moderate, enter 2 speed steps, see XML preview
  - Test: User creates DHS strategy
    - Scenario: Select dhs_peak_hours, select edges, set vehicle types, confirm
  - Test: User creates TEC metering strategy
    - Scenario: Select tec_metering, add flow intervals, see calibrator XML
  - Test: Real-time validation errors
    - Scenario: Enter invalid speed (200 km/h), see error message, fix and revalidate
- [ ] 5.4.2 Test form interactivity

  - Test time range picker: Select start/end times, see graphical representation
  - Test step array editor: Add/remove/reorder speed steps
  - Test vehicle type multi-select: Select/deselect types
  - Test XML preview: Updates in real-time as user edits
- [ ] 5.4.3 Test error scenarios

  - Test: Overlapping time intervals → show warning
  - Test: Out-of-order time steps → show error
  - Test: Invalid edge ID → show error with suggestion

### 5.5 Performance Testing

- [ ] 5.5.1 Test parameter validation performance

  - Validate 100 parameters: Target <200ms
  - Generate XML preview: Target <150ms
- [ ] 5.5.2 Test form generation performance

  - Generate form with 10 parameters: Target <100ms
  - Render 5 speed steps in table: Target <50ms

## 6. Documentation

### 6.1 Template Documentation

- [ ] 6.1.1 Update template documentation

  - Document each template: vss_moderate, vss_strict, dhs_peak_hours, tec_entrance_close, tec_metering
  - For each: Description, parameters, SUMO XML output example, typical use cases
- [ ] 6.1.2 Document parameter types and constraints

  - Document each parameter type (integer, enum, step_array, etc.)
  - Show examples of valid values
  - Show error cases and error messages
- [ ] 6.1.3 Create parameter schema reference

  - Document all schema fields: parameter_type, sumo_unit, display_unit, conversion_factor
  - Show template structure with example

### 6.2 API Documentation

- [ ] 6.2.1 Update API docs with new endpoints

  - POST /api/v1/control/strategies/validate-params
  - POST /api/v1/control/strategies/generate-xml-preview
  - Include request/response examples
- [ ] 6.2.2 Document SUMO unit conversions

  - Time: hours (display) → seconds (SUMO)
  - Speed: km/h (display) → m/s (SUMO)
  - Flow: vehicles/hour (both display and SUMO)

### 6.3 Developer Guide

- [ ] 6.3.1 Update development guide with template updates

  - Explain v1.0 vs v2.0 templates
  - Document backward compatibility approach
  - Show how to add new templates
- [ ] 6.3.2 Document parameter validator usage

  - Show how to validate parameters
  - Show how to generate XML
  - Show unit conversion usage

## 7. Code Quality and Review

### 7.1 Code Standards

- [ ] 7.1.1 Run code formatter

  - `black api/ shared/ frontend/`
- [ ] 7.1.2 Run linter

  - `flake8 api/ shared/` - fix warnings
- [ ] 7.1.3 Type checking

  - Verify all functions have type hints
  - Run mypy if configured

### 7.2 Testing Coverage

- [ ] 7.2.1 Run all tests

  - `pytest tests/unit/` --cov=shared/control_tools/parameter_validator.py --cov=api/services/control_strategy_service.py`
  - Target >90% coverage for parameter_validator module
- [ ] 7.2.2 Run E2E tests

  - `npx playwright test tests/e2e/test_strategy_parameter_configuration.spec.js`

### 7.3 Review and Sign-off

- [ ] 7.3.1 Code review

  - Have peer review parameter validator logic
  - Review XML generation changes
  - Review frontend form generation
- [ ] 7.3.2 Manual testing

  - Create VSS strategy with various speed steps
  - Create DHS strategy with multiple intervals
  - Create TEC metering strategy with flow control
  - Verify generated XML matches SUMO requirements

## Timeline Estimate

- **Template Regeneration**: 1 day

  - All 5 templates with v2.0 schema
- **Backend Implementation**: 2 days

  - Parameter validator, XML generation enhancement, API endpoints
- **Frontend Implementation**: 2 days

  - Form generation, validation UI, XML preview
- **Testing**: 1-2 days

  - Unit tests, integration tests, E2E tests
- **Documentation & Review**: 1 day

  - API docs, developer guide, code review
- **Total**: 7-9 days (1-2 weeks)

## Acceptance Criteria

- [ ] All 5 templates regenerated with v2.0 schema including SUMO mappings
- [ ] Parameter validator handles all parameter types correctly
- [ ] Unit conversion (hours→seconds, km/h→m/s) works correctly
- [ ] Form generation creates proper controls for each parameter type
- [ ] Real-time validation shows errors/warnings while typing
- [ ] XML preview displays during strategy configuration
- [ ] All unit tests pass (>90% coverage for validator module)
- [ ] All E2E tests pass (template → form → XML workflow)
- [ ] Backward compatibility: v1.0 strategies still loadable
- [ ] Performance: Form generation <100ms, validation <200ms, XML generation <150ms
- [ ] API documentation updated with new endpoints
- [ ] No type errors or linting warnings
