# event-scenario-generation Specification

## Purpose
TBD - created by archiving change add-event-scenario-sumo-configuration. Update Purpose after archive.
## Requirements
### Requirement: Event Injection XML Generation

The system SHALL generate SUMO-compatible event injection XML elements from event data records.

**Rationale**: Traffic events (accidents, congestion) must be represented in SUMO simulations to analyze their impact and control strategy effectiveness.

#### Scenario: Generate accident lane closure XML

- **GIVEN** event data with edge_id="-4688", affected_lanes=["应急车道"], start_time="2025-07-14 01:53:49", end_time="2025-07-14 03:22:39"
- **WHEN** event injection XML is generated
- **THEN** output contains `<closedLane id="accident_12547" edge="-4688" lanes="-4688_0" disallow="all" begin="6749" end="12069"/>`
- **AND** time values are converted to simulation seconds from simulation start
- **AND** lane descriptions are mapped to SUMO lane IDs using network file

#### Scenario: Handle invalid event data gracefully

- **GIVEN** event data with missing edge_id field
- **WHEN** event injection XML generation is attempted
- **THEN** system raises `ScenarioValidationError` with descriptive message
- **AND** error is logged with event report_id for debugging

---

### Requirement: Lane ID Resolution

The system SHALL map Chinese lane descriptions to SUMO lane IDs using network file topology.

**Rationale**: Event CSV data contains human-readable lane descriptions (应急车道, 第一车道) that must be converted to SUMO lane IDs (edge_id_lane_index format).

#### Scenario: Map emergency lane to SUMO lane ID

- **GIVEN** edge "-4688" with 4 lanes in network file
- **AND** lane description "应急车道" (emergency lane)
- **WHEN** lane ID resolution is performed
- **THEN** returns "-4688_0" (rightmost lane index 0)

#### Scenario: Map multiple lane descriptions

- **GIVEN** edge "-4688" with lane descriptions ["应急车道", "第一车道"]
- **WHEN** lane ID resolution is performed
- **THEN** returns ["-4688_0", "-4688_1"]
- **AND** lane order matches SUMO lane indexing convention

#### Scenario: Handle unknown lane description

- **GIVEN** edge "-4688" and lane description "未知车道"
- **WHEN** lane ID resolution is attempted
- **THEN** system logs warning and returns empty list
- **AND** raises validation error indicating unmapped lane

---

### Requirement: Combined Scenario XML Generation

The system SHALL combine event injection XML and control strategy XML in a single SUMO `.add.xml` file.

**Rationale**: SUMO simulations require additional files to specify both event conditions and control responses. Combining them in one file simplifies simulation configuration.

#### Scenario: Generate accident + VSS scenario XML

- **GIVEN** accident event at edge "-4688" from 01:53 to 03:22
- **AND** VSS control strategy with speed_limit=60 km/h
- **WHEN** scenario XML is generated
- **THEN** output contains `<additional>` root element
- **AND** contains `<closedLane>` element for accident
- **AND** contains `<variableSpeedSign>` element for VSS control
- **AND** control activation time is 5 minutes before event start
- **AND** XML validates against SUMO additional file schema

#### Scenario: Validate element ID uniqueness

- **GIVEN** scenario with event ID "accident_12547" and control strategy ID "vss_001"
- **WHEN** combined XML is generated
- **THEN** all element IDs are unique within the XML
- **AND** no ID conflicts between event and control elements

---

### Requirement: Scenario File Structure

The system SHALL organize scenario files in a hierarchical directory structure by event type and control strategy.

**Rationale**: 18+ scenarios organized by 6 event types × 3 strategies require clear file organization for maintainability.

#### Scenario: Generate scenario file path

- **GIVEN** event_type="交通事故", strategy="VSS", event_id="12547"
- **WHEN** scenario file path is generated
- **THEN** path is "output/scenarios/01_交通事故/vss/scenario_accident_vss_12547.add.xml"
- **AND** directory structure is created if it doesn't exist

#### Scenario: Generate scenario metadata file

- **GIVEN** generated scenario XML file
- **WHEN** scenario is saved
- **THEN** metadata JSON file is created in same directory
- **AND** metadata contains scenario_id, scenario_name, event_type, control_strategy, file_path, tags
- **AND** metadata includes preview data for UI display

---

### Requirement: Scenario Configuration Bundle Generation

The system SHALL generate three JSON configuration files for each scenario: event description, traffic input config, and control strategy config.

**Rationale**: Complete scenario specification requires event metadata, OD data time range, and control parameters for simulation execution and analysis reproducibility.

#### Scenario: Generate event description JSON

- **GIVEN** event data with location, time, and impact information
- **WHEN** event description JSON is generated
- **THEN** output file "event_description.json" is created in scenario directory
- **AND** JSON contains event_id, event_type, location (road, direction, mileage, edge_id, junction_id)
- **AND** JSON contains time (start_time, end_time, duration_hours)
- **AND** JSON contains impact (affected_lanes, lane_ids)
- **AND** lane descriptions are mapped to SUMO lane IDs

#### Scenario: Generate traffic input config JSON with time buffer

- **GIVEN** event with start_time="2025-07-14 01:53:49", end_time="2025-07-14 03:22:39"
- **AND** default buffer of 30 minutes
- **WHEN** traffic input config JSON is generated
- **THEN** output file "traffic_input_config.json" is created
- **AND** od_time_range.start = "2025-07-14 01:23:49" (event_start - 30min)
- **AND** od_time_range.end = "2025-07-14 03:52:39" (event_end + 30min)
- **AND** od_time_range contains original event_start and event_end
- **AND** od_table is determined from event date (e.g., "baseline.od_data_sichuan_202507")
- **AND** simulation_duration_hours is calculated including buffer

#### Scenario: Generate control strategy config JSON with realistic timing

- **GIVEN** VSS strategy with speed_limit=60 kmh, response_delay=300s, recovery_period=600s
- **AND** event at edge "-4688" from 01:53:49 to 03:22:39
- **WHEN** control strategy config JSON is generated
- **THEN** output file "control_strategy_config.json" is created
- **AND** JSON contains strategy_type="VSS", strategy_name="可变限速标志"
- **AND** parameters.speed_limit_kmh = 60
- **AND** parameters.response_delay_seconds = 300 (control activates AFTER event detection)
- **AND** parameters.recovery_period_seconds = 600 (control continues after event ends)
- **AND** parameters.affected_edges and affected_lanes are mapped
- **AND** timing.activation_time = "2025-07-14 01:58:49" (event_start + 5min, realistic response)
- **AND** timing.deactivation_time = "2025-07-14 03:32:39" (event_end + 10min, allow recovery)

#### Scenario: All configuration files co-located with scenario XML

- **GIVEN** scenario generation for event 12547 with VSS strategy
- **WHEN** scenario bundle is generated
- **THEN** four files are created in same directory:
  - scenario_accident_vss_12547.add.xml
  - event_description.json
  - traffic_input_config.json
  - control_strategy_config.json
- **AND** all files reference same event_id and scenario_id

---

### Requirement: Batch Scenario Generation

The system SHALL generate multiple scenarios from filtered event CSV data in batch mode.

**Rationale**: 399 events in CSV require automated filtering and batch generation to create representative scenario library efficiently.

#### Scenario: Filter representative events by quality

- **GIVEN** events CSV with 399 events
- **AND** target count of 18 scenarios
- **WHEN** event filtering is performed
- **THEN** selects 3 events per event type (6 types)
- **AND** filters by duration between 0.5-3 hours
- **AND** filters by data completeness (has edge_id, junction_id, start_time, end_time)
- **AND** prioritizes diverse locations and time periods

#### Scenario: Generate scenario library with 18 scenarios

- **GIVEN** 6 filtered events (one per event type)
- **AND** 3 control strategies (VSS, DHS, TEC)
- **WHEN** batch scenario generation is executed
- **THEN** generates 18 scenario XML files (6 events × 3 strategies)
- **AND** creates scenario_index.json with all scenario metadata
- **AND** completes generation in less than 5 minutes
- **AND** logs summary with success/failure counts

#### Scenario: Handle generation errors gracefully

- **GIVEN** batch generation with 10 event-strategy pairs
- **AND** 2 pairs have invalid data causing validation errors
- **WHEN** batch generation is executed
- **THEN** continues processing remaining 8 pairs
- **AND** logs errors for failed pairs with event_id and reason
- **AND** final summary shows 8 succeeded, 2 failed
- **AND** returns results dictionary with success/failed lists

---

### Requirement: Event-Strategy Parameter Mapping

The system SHALL calculate appropriate control strategy parameters based on event characteristics.

**Rationale**: Different events require different control responses (accident severity affects speed limit, blockage extent affects flow reduction).

#### Scenario: Calculate VSS speed limit from accident severity

- **GIVEN** accident event with affected_lanes=["应急车道"] (1 lane blocked)
- **WHEN** VSS parameters are calculated
- **THEN** speed_limit is set to 60 km/h
- **AND** activation_offset is 300 seconds (5 minutes before event)
- **AND** deactivation_offset is 300 seconds (5 minutes after event)

#### Scenario: Calculate DHS parameters from event location

- **GIVEN** accident event at edge "-4688"
- **WHEN** DHS parameters are calculated
- **THEN** open_shoulder is set to true
- **AND** shoulder_edge_id is determined from network topology
- **AND** activation zone includes upstream edges

#### Scenario: Use default parameters when event data insufficient

- **GIVEN** event with minimal data (only edge_id and time range)
- **WHEN** control parameters are calculated
- **THEN** uses default parameters from event_strategy_mapping.json
- **AND** logs warning about using defaults

---

### Requirement: SUMO XML Schema Validation

The system SHALL validate all generated scenario XML against SUMO's additional file schema before saving.

**Rationale**: Invalid XML will cause SUMO simulation failures. Early validation prevents wasted simulation attempts.

#### Scenario: Validate scenario XML against schema

- **GIVEN** generated scenario XML with closedLane and variableSpeedSign elements
- **WHEN** XML validation is performed
- **THEN** validates syntax (well-formed XML)
- **AND** validates against SUMO additional_file.xsd schema
- **AND** checks element-specific constraints (time ranges, IDs)
- **AND** returns validation result with error details if invalid

#### Scenario: Detect inconsistent time ranges

- **GIVEN** scenario with event begin=1000, end=2000
- **AND** control strategy begin=2500 (after event end)
- **WHEN** scenario consistency validation is performed
- **THEN** validation fails with error "Control activation after event end"
- **AND** suggests corrected activation time

---

