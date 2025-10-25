# strategy-templates Specification

## Purpose
TBD - created by archiving change update-strategy-templates-sumo-verified. Update Purpose after archive.
## Requirements
### Requirement: SUMO-Aligned Strategy Templates

The system SHALL provide 13 predefined strategy templates (5 base + 8 supplementary) that accurately reflect SUMO v1.19 XML element requirements and constraints, enabling users to create valid control strategies without manual XML knowledge.

#### Scenario: VSS Moderate template for standard speed control

- **WHEN** user selects "VSS Moderate (可变限速 - 中等控制)" template
- **THEN** system displays template parameters including:
  - `affected_edges`: Array of edge IDs (required)
  - `speed_steps`: Array of {time_seconds, speed_kmh} objects (required, at least 1 step)
  - `time_intervals_hours`: Array of [start_hour, end_hour] for display (required)
  - `applicable_vehicle_types`: Array of SUMO enum values (optional, default all types)
- **THEN** template description explains "Moderate speed control 80-100 km/h for managing traffic flow during peak hours"
- **THEN** default values provided: 2 speed steps (unrestricted + controlled), peak hours [7-9, 17-19]

#### Scenario: VSS Strict template for aggressive speed control

- **WHEN** user selects "VSS Strict (可变限速 - 严格控制)" template
- **THEN** system displays strict parameters:
  - Speed control 60-80 km/h range
  - More aggressive speed steps for incident response
  - Support for 3-5 speed steps in sequence
- **THEN** default guidance: Effective for bottleneck areas during congestion

#### Scenario: DHS Standard template for hard shoulder activation

- **WHEN** user selects "DHS Standard (应急车道开放)" template
- **THEN** system displays parameters:
  - `affected_segments`: Array of edge IDs forming continuous hard shoulder (required)
  - `hard_shoulder_lane_index`: Integer specifying hard shoulder lane (default: 3, rightmost lane)
  - `intervals`: Array of {begin_seconds, end_seconds, allowed_vehicle_types} (required, at least 1)
  - `allowed_vehicle_types`: Array of SUMO vehicle type enums (default: ["passenger", "bus", "truck"])
- **THEN** warning displayed: "Hard shoulder is typically the rightmost lane (lane index 3 for 4-lane highways)"

#### Scenario: TEC Metering template for ramp flow control

- **WHEN** user selects "TEC Metering (收费入口计量控制)" template
- **THEN** system displays parameters:
  - `entrance_edge`: Single entrance edge ID (required)
  - `flow_intervals`: Array of {begin_seconds, end_seconds, vehicles_per_hour, target_speed} (required, at least 1)
  - `control_mode`: Enum ["metering", "closure"] (required)
  - `time_intervals_hours`: Display format for configuration (required)
- **THEN** default values: 180-480 vehicles/hour depending on time period

#### Scenario: TEC Closure template for entrance closure

- **WHEN** user selects "TEC Closure (收费入口关闭)" template
- **THEN** system displays closure-specific parameters:
  - `entrance_edge`: Entrance to close (required)
  - `closure_intervals`: Array of {begin_seconds, end_seconds} (required)
  - `allowed_vehicle_types`: Vehicles allowed through (empty = all blocked, optional)
- **THEN** description: "Temporary closure of entrance, redirects vehicles to alternative routes"

#### Scenario: VSS Weather-Based Progressive Limiting (Supplementary)

- **WHEN** user selects "VSS Weather-Based (可变限速 - 天气应急)" template
- **THEN** system displays progressive speed reduction parameters:
  - `affected_edges`: Array of edge IDs (required)
  - `speed_steps`: Array of {time_seconds, speed_kmh} with 6+ steps (required, supports weather progression)
  - `weather_condition`: Enum ["fog", "rain", "snow", "incident"] (optional, for documentation)
  - Example: 120→100→80→60→100→120 km/h (fog clearing pattern)
- **THEN** default guidance: "Suitable for adverse weather conditions requiring gradual speed reduction throughout the day"
- **THEN** preset weather profiles available: Fog (6 steps), Heavy Rain (4 steps), Snow (5 steps)

#### Scenario: VSS Upstream Warning Speed Control (Supplementary)

- **WHEN** user selects "VSS Upstream Warning (可变限速 - 上游预警)" template
- **THEN** system displays early slowdown parameters:
  - `affected_edges`: Array of edge IDs (required, typically 2-3 km upstream of bottleneck)
  - `speed_steps`: Array of {time_seconds, speed_kmh} with exactly 3 steps (normal→reduced→recovery)
  - `warning_advance_minutes`: Integer 3-15 minutes before downstream event (required)
  - `bottleneck_location`: Reference edge ID for coordination (optional)
- **THEN** default example: Slow from 120→80 km/h at 6:55, restore at 7:00 when DHS opens
- **THEN** validation: Warning time must occur before referenced DHS opening time

#### Scenario: VSS Lane-Differentiated Speed Control (Supplementary)

- **WHEN** user selects "VSS Lane-Differentiated (可变限速 - 分车道控制)" template
- **THEN** system displays per-lane parameters:
  - `affected_edges`: Array of edge IDs (required)
  - `lane_configurations`: Array of {lane_index, speed_kmh} (required, at least 2 lanes with different speeds)
  - `speed_steps`: Array of {time_seconds, speeds_by_lane} (required)
  - Example: Lane 0 (truck lane) 80 km/h, Lanes 1-2 (car lanes) 100 km/h
- **THEN** system generates separate VSS strategies for each lane group
- **THEN** note displayed: "Lane-differentiated control creates multiple VSS elements in XML for traffic class separation"

#### Scenario: DHS Passenger-Only Hard Shoulder (Supplementary)

- **WHEN** user selects "DHS Passenger-Only (应急车道 - 仅客车)" template
- **THEN** system displays vehicle-restricted parameters:
  - `affected_segments`: Array of edge IDs (required)
  - `allowed_vehicle_types`: Restricted to ["passenger", "bus"] (pre-selected, optional to modify)
  - `intervals`: Array of {begin_seconds, end_seconds, status} (required)
  - `prohibited_types`: Clearly shows "truck", "trailer", "delivery" are blocked
- **THEN** default intervals: Peak hours only (7-9, 17-19)
- **THEN** warning displayed: "Truck ban may create congestion in freight corridors - use with caution"

#### Scenario: DHS Peak-Hour Multi-Interval Management (Supplementary)

- **WHEN** user selects "DHS Peak Multi-Interval (应急车道 - 多时段管理)" template
- **THEN** system displays complex interval parameters:
  - `affected_segments`: Array of edge IDs (required)
  - `intervals`: Array of {begin_seconds, end_seconds, status, allowed_types} with 5+ entries (required)
  - Predefined pattern: Night(closed)→Morning peak(open)→Midday(closed)→Evening peak(open)→Night(closed)
  - Time boundaries: 0-7, 7-9, 9-17, 17-19, 19-24 hours
- **THEN** each interval clearly labeled with time range and status
- **THEN** validation: Ensure no gaps in 24-hour coverage

#### Scenario: TEC Ramp Metering with Time-Varying Flow Rates (Supplementary)

- **WHEN** user selects "TEC Metering Advanced (收费入口 - 时变限流)" template
- **THEN** system displays multi-interval flow control parameters:
  - `entrance_edge`: Single entrance edge ID (required)
  - `flow_intervals`: Array of {begin_seconds, end_seconds, vehsPerHour, speed_ms} (required, 4+ intervals)
  - Predefined flow profile: 480→180→480→300→480 vehsPerHour (morning peak reduction, evening lighter)
  - Each interval includes entry speed calibration (8-15 m/s)
- **THEN** visual flow rate graph shown during configuration
- **THEN** validation: Flow rates must be in 0-2000 veh/hour range

#### Scenario: TEC Truck Ban During Peak Hours (Supplementary)

- **WHEN** user selects "TEC Truck Ban (收费入口 - 货车限行)" template
- **THEN** system displays vehicle-type restriction parameters:
  - `entrance_edges`: Array of entrance edge IDs (required, typically 1-3 entries per toll station)
  - `intervals`: Array of {begin_seconds, end_seconds, disallow_types} (required)
  - Disallow types: ["truck", "trailer"] (pre-selected)
  - Typical times: Morning 7-9, Evening 17-19
- **THEN** predefined patterns: Full day ban, or peak-only restriction options
- **THEN** note: "Truck bans redirect freight to alternative routes - monitor for bottleneck shift"

#### Scenario: TEC Full Entrance Closure (Supplementary)

- **WHEN** user selects "TEC Closure Complete (收费入口 - 完全关闭)" template
- **THEN** system displays complete blockage parameters:
  - `entrance_edges`: Array of entrance edge IDs (required)
  - `closure_intervals`: Array of {begin_seconds, end_seconds} (required)
  - `allowed_types`: Left empty (all vehicles blocked) by default
  - `reason`: Enum ["maintenance", "emergency", "congestion_relief"] (optional for documentation)
- **THEN** warning displayed: "Complete closure redirects ALL vehicles - ensure alternative routes exist"
- **THEN** typical duration: 1-4 hours

### Requirement: Parameter Schema with SUMO Constraints

The system SHALL define parameter schemas that include SUMO-specific metadata to enable validation and proper UI rendering.

#### Scenario: Time parameter with hour-to-second conversion

- **WHEN** parameter is time-based
- **THEN** schema includes:

  ```json
  {
    "parameter_name": "time_intervals",
    "parameter_type": "time_range_array",
    "display_unit": "hours",  // User sees 7:00-9:00
    "sumo_unit": "seconds",   // SUMO receives 25200-32400
    "conversion_factor": 3600,
    "description": "Time periods when control is active"
  }
  ```
- **THEN** system automatically converts display values to SUMO second
- 
- **THEN** schema includes:

  ```json
  {
    "parameter_name": "speed_value",
    "parameter_type": "number",
    "unit": "km/h",
    "min_value": 30,          // SUMO minimum realistic speed
    "max_value": 130,         // Highway maximum
    "default_value": 80,
    "step": 5,                // UI increment in km/h
    "description": "Speed limit to enforce"
  }
  ```
- **THEN** UI prevents values outside valid range with error message

#### Scenario: Vehicle type parameter with SUMO enums

- **WHEN** parameter involves vehicle type filtering
- **THEN** schema includes SUMO standard vehicle type enums:
  ```json
  {
    "parameter_name": "allowed_vehicle_types",
    "parameter_type": "enum_array",
    "enum_values": [
      { "value": "passenger", "label": "Passenger Cars (客车)" },
      { "value": "bus", "label": "Buses (公交车)" },
      { "value": "truck", "label": "Trucks (货车)" },
      { "value": "emergency", "label": "Emergency Vehicles (应急车)" }
    ],
    "default_selection": ["passenger", "bus", "truck"],
    "description": "Vehicle types allowed through hard shoulder"
  }
  ```
- **THEN** UI displays as multi-select checkboxes with descriptions

#### Scenario: Speed steps array for VSS

- **WHEN** parameter is speed_steps (VSS time-varying speed)
- **THEN** schema supports array of steps:
  ```json
  {
    "parameter_name": "speed_steps",
    "parameter_type": "step_array",
    "step_structure": {
      "time_display_unit": "hours",
      "time_sumo_unit": "seconds",
      "speed_unit": "km/h"
    },
    "min_steps": 1,
    "max_steps": 10,
    "description": "Speed limit changes over time (e.g., free flow → controlled → free flow)"
  }
  ```
- **THEN** each step is {time: X hours, speed: Y km/h} in display, converted to seconds in SUMO

#### Scenario: Lane index parameter for DHS

- **WHEN** parameter specifies which lane is hard shoulder
- **THEN** schema includes:
  ```json
  {
    "parameter_name": "hard_shoulder_lane_index",
    "parameter_type": "integer",
    "description": "0=leftmost, N=rightmost; typically rightmost is hard shoulder",
    "default_value": 3,
    "note": "For 4-lane highway: lanes 0-2 are traffic, lane 3 is hard shoulder"
  }
  ```

#### Scenario: Flow interval parameter for TEC

- **WHEN** parameter defines time-varying flow control
- **THEN** schema includes:
  ```json
  {
    "parameter_name": "flow_intervals",
    "parameter_type": "flow_interval_array",
    "interval_structure": {
      "begin": "seconds (0-86400)",
      "end": "seconds (0-86400)",
      "vehicles_per_hour": "integer (0-3000)",
      "target_speed": "km/h (0-130, 0=no speed control)"
    },
    "description": "Metering rate (vehicles/hour) during each time period"
  }
  ```

### Requirement: Dynamic Parameter Form Generation

The system SHALL generate HTML forms dynamically based on template parameter schemas, with appropriate input controls for each parameter type.

#### Scenario: Generate form for VSS Moderate template

- **WHEN** user starts creating VSS strategy from template
- **THEN** system generates form with:
  - Text input with "edge_*" placeholder for `affected_edges` (with add/remove buttons for array)
  - Speed step editor UI (table with time, speed columns; add/remove row buttons)
  - Time range picker for `time_intervals` (show as 7:00-9:00, not 25200-32400)
  - Multi-select checkboxes for vehicle types
  - All required fields marked with asterisk
- **THEN** form displays template description and each parameter help text

#### Scenario: Generate form for DHS template

- **WHEN** user starts creating DHS strategy
- **THEN** system generates:
  - Edge array input for `affected_segments` (edges should form continuous hard shoulder)
  - Integer spinner for `hard_shoulder_lane_index` (default 3, range 0-7)
  - Interval array editor (time range picker + vehicle type multi-select per interval)
  - Helpful note: "Hard shoulder is typically lane 3 (rightmost)"

#### Scenario: Generate form for TEC Metering template

- **WHEN** user starts creating TEC metering strategy
- **THEN** system generates:
  - Single edge input for `entrance_edge` (validation ensures it's entrance type)
  - Flow interval editor:
    - Each row: time range + vehicles per hour spinner + speed input
    - Add/remove interval buttons
  - Mode selector: "Metering" vs "Closure"

#### Scenario: Render time interval picker

- **WHEN** form includes time intervals (hours display format)
- **THEN** UI renders:
  - Two time inputs (start hour: 0-24, end hour: 0-24)
  - Graphical timeline bar showing covered hours
  - Visual indication if time period spans midnight (e.g., 22:00-4:00)
  - Help text: "Displayed in simulation hours; 7:00-9:00 = 25200-32400 seconds in SUMO"

### Requirement: Real-Time Parameter Validation

The system SHALL validate parameters as user inputs them, showing errors before form submission, with SUMO-specific guidance.

#### Scenario: Validate speed value within range

- **WHEN** user enters speed in VSS form
- **THEN** system validates:
  - Must be between 30-130 km/h (realistic highway speeds)
  - If outside range, show error: "Speed must be 30-130 km/h (current: 150)"
- **THEN** validation happens on blur/change (not just submit)

#### Scenario: Detect overlapping time intervals

- **WHEN** user adds multiple time intervals with potential overlap
- **THEN** system warns: "Warning: Time periods 7:00-10:00 and 9:00-11:00 overlap"
- **THEN** allows overlap (intentional in some cases) but alerts user

#### Scenario: Validate edges exist in network

- **WHEN** user enters edge IDs in parameter
- **THEN** system validates against known network edges
- **THEN** if edge not found, show error: "Edge 'edge_invalid' not found in network"
- **THEN** provide quick link to edge browser for discovery

#### Scenario: Check for continuous hard shoulder edges in DHS

- **WHEN** user selects multiple edges for hard shoulder
- **THEN** system checks if edges form continuous path
- **THEN** if discontinuous, warn: "Edges {e1, e2, e5} are not continuous; DHS effectiveness may be reduced"
- **THEN** allow user to proceed (may be intentional for multiple segments)

#### Scenario: Validate vehicle type enum values

- **WHEN** user selects vehicle types
- **THEN** system ensures only SUMO standard types selected: passenger, bus, truck, emergency
- **THEN** prevent custom values; only show predefined options

#### Scenario: Validate time interval does not exceed 24 hours

- **WHEN** user sets time intervals
- **THEN** system validates total simulation time span (should cover 0-24 hour day)
- **THEN** warn if gaps: "Coverage gap: 12:00-14:00 (2 hours) has no control settings"

### Requirement: XML Preview During Configuration

The system SHALL show real-time preview of generated SUMO XML while user configures parameters, enabling feedback before saving.

#### Scenario: Preview VSS XML as user edits speed steps

- **WHEN** user is in VSS parameter form
- **THEN** system displays XML preview panel showing:
  ```xml
  <variableSpeedSign id="strategy_001" edges="edge_100 edge_101 edge_102">
    <step time="25200" speed="33.33"/>
    <step time="32400" speed="22.22"/>
  </variableSpeedSign>
  ```
- **THEN** preview updates in real-time as user modifies speeds/times
- **THEN** XML syntax is highlighted (color-coded tags)

#### Scenario: Preview DHS XML with interval and vehicle restrictions

- **WHEN** user configures DHS intervals
- **THEN** preview shows:
  ```xml
  <rerouter id="strategy_002" edges="edge_1000 edge_1001">
    <interval begin="25200" end="32400">
      <closingLaneReroute id="edge_1000_3" allow="passenger bus truck"/>
      <closingLaneReroute id="edge_1001_3" allow="passenger bus truck"/>
    </interval>
  </rerouter>
  ```
- **THEN** preview reflects selected vehicle types and time periods

#### Scenario: Preview TEC XML with flow calibration

- **WHEN** user enters flow intervals for TEC metering
- **THEN** preview shows:
  ```xml
  <calibrator id="strategy_003" edge="entrance_k12" pos="0">
    <flow begin="0" end="25200" vehsPerHour="480" speed="15"/>
    <flow begin="25200" end="32400" vehsPerHour="180" speed="8"/>
  </calibrator>
  ```
- **THEN** updates as user changes flow rates and speeds

#### Scenario: Copy XML to clipboard

- **WHEN** user views XML preview
- **THEN** system provides "Copy XML" button
- **THEN** click button copies generated XML to clipboard for manual inspection

### Requirement: Parameter Validation API

The system SHALL provide backend validation endpoint for parameter combinations before strategy instance creation, preventing invalid SUMO XML generation.

#### Scenario: Validate parameter set before strategy creation

- **WHEN** user submits strategy form
- **THEN** frontend POSTs to `POST /api/v1/control/strategies/validate-params`
  ```json
  {
    "template_id": "vss_moderate",
    "parameters": {
      "affected_edges": ["edge_100", "edge_101"],
      "speed_steps": [
        {"time_seconds": 0, "speed_kmh": 100},
        {"time_seconds": 25200, "speed_kmh": 80}
      ],
      "time_intervals_hours": [[7, 9]],
      "applicable_vehicle_types": []
    }
  }
  ```
- **THEN** backend validates:
  - All edges exist in network
  - Time steps are in ascending order
  - Speed values in valid range
  - Vehicle types are SUMO enums or empty
- **THEN** returns validation result:
  ```json
  {
    "valid": true,
    "errors": [],
    "warnings": ["Speed 80 km/h is below highway average; confirm intentional"]
  }
  ```

#### Scenario: Report validation errors before strategy save

- **WHEN** validation endpoint returns errors
- **THEN** frontend shows error message to user before allowing save
- **THEN** error message references specific parameter: "Parameter 'speed_steps' is invalid: time step 2 (32400s) must be > time step 1 (32400s)"

#### Scenario: Generate SUMO XML on backend for preview

- **WHEN** user requests XML preview
- **THEN** frontend POSTs to `POST /api/v1/control/strategies/generate-xml-preview`
  ```json
  {
    "template_id": "vss_moderate",
    "parameters": { /* same as validate */ }
  }
  ```
- **THEN** backend returns generated XML:
  ```json
  {
    "xml_content": "<variableSpeedSign ...>...</variableSpeedSign>",
    "valid": true,
    "validation_message": "XML is well-formed and ready for SUMO"
  }
  ```

### Requirement: Template Index with Metadata

The system SHALL provide indexed access to all strategy templates with filtering and search capabilities.

#### Scenario: List all templates with metadata

- **WHEN** user GETs `/api/v1/control/templates/`
- **THEN** system returns:
  ```json
  {
    "templates": [
      {
        "template_id": "vss_moderate",
        "template_name": "可变限速 - 中等控制",
        "strategy_type": "VSS",
        "description": "Medium intensity speed control...",
        "parameters_count": 5,
        "version": "2.0",
        "last_updated": "2025-10-24T12:00:00Z"
      }
    ],
    "total_count": 5
  }
  ```

#### Scenario: Filter templates by strategy type

- **WHEN** user GETs `/api/v1/control/templates/?strategy_type=VSS`
- **THEN** system returns only VSS templates (vss_moderate, vss_strict)

#### Scenario: Get template details with full parameter schema

- **WHEN** user GETs `/api/v1/control/templates/vss_moderate`
- **THEN** system returns template with complete parameter schema including SUMO constraints:
  ```json
  {
    "template_id": "vss_moderate",
    "parameters_schema": [
      {
        "parameter_name": "speed_steps",
        "parameter_type": "step_array",
        "sumo_unit": "seconds",
        "display_unit": "hours",
        "min_steps": 1,
        "max_steps": 10,
        "step_schema": {
          "time": {"type": "integer", "min": 0, "max": 86400},
          "speed": {"type": "number", "min": 30, "max": 130, "unit": "km/h"}
        }
      }
    ]
  }
  ```

### Requirement: Backward Compatibility with Existing Strategies

The system SHALL preserve all existing strategy instances while upgrading templates to SUMO-verified versions.

#### Scenario: Load existing VSS strategy with old template

- **WHEN** system loads strategy created with template v1.0
- **THEN** existing strategy parameters remain valid
- **THEN** system allows editing but shows notice: "This strategy uses template v1.0; some v2.0 features unavailable"
- **THEN** user can choose to "Upgrade to v2.0" template (creates new strategy, preserves old)

#### Scenario: New strategies use v2.0 templates only

- **WHEN** user creates new strategy
- **THEN** only v2.0 templates available in template selector
- **THEN** new strategies automatically use upgraded schema with SUMO validation

