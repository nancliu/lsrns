# Design: Event Scenario SUMO Configuration Generation

**Change ID**: `add-event-scenario-sumo-configuration`

**Status**: Design

**Date**: 2025-01-10

---

## Overview

This document captures the architectural decisions and design rationale for the event scenario SUMO configuration generation system. The system extends the existing control strategy XML generation framework to support event-based traffic scenarios, enabling automated simulation of 18+ real-world traffic events with control strategies.

---

## Design Goals

1. **Reuse Proven Patterns**: Leverage existing control strategy XML generation infrastructure
2. **Modular Architecture**: Separate event injection from control strategy logic
3. **Automated Scenario Library**: Generate 18+ scenarios from real event data with minimal manual intervention
4. **SUMO Compatibility**: Produce valid SUMO `.add.xml` files that can be directly simulated
5. **Extensibility**: Support future event types beyond Phase 1 (accidents)

---

## Key Architectural Decisions

### AD-1: Reuse Control Strategy XML Generation

**Decision**: Call existing `additional_generator.generate_strategy_xml()` for VSS/DHS/TEC elements instead of reimplementing strategy generation.

**Rationale**:

**Why Reuse?**

- `additional_generator.py` is proven and validated (used in production control workflows)
- Contains SUMO XML schema knowledge and validation logic
- Implements all three strategy types (VSS, DHS, TEC) with correct parameters
- Already integrated with `xml_validator.py` for schema checking
- Avoids code duplication and maintenance burden

**Integration Pattern**:

```python
# Event scenario generator calls control generator
from shared.control_tools.additional_generator import generate_strategy_xml

def generate_scenario_xml(event_data, control_strategy, control_params):
    # Generate event XML
    event_xml = generate_event_xml(event_data)

    # Generate control XML (reuse existing)
    control_xml = generate_strategy_xml(
        template_id=f"{control_strategy}_template",
        template=get_strategy_template(control_strategy),
        parameters=control_params,
        strategy_type=control_strategy
    )

    # Combine in single .add.xml
    return combine_xml_elements(event_xml, control_xml)
```

**Trade-offs**:

- ✅ **Pros**: Zero duplication, consistent validation, proven reliability
- ✅ **Pros**: Automatically inherits future improvements to control generation
- ✅ **Pros**: Reduces implementation time (1 week saved vs reimplementation)
- ⚠️ **Cons**: Dependency on control tools module (acceptable, stable API)

**Alternatives Considered**:

- Option A: **Reuse existing generator (selected)** - leverages proven infrastructure
- Option B: Implement separate strategy generator for scenarios - rejected, unnecessary duplication
- Option C: Manually create strategy XML strings - rejected, error-prone and unmaintainable

**Priority**: Phase 1 (Foundation) - core architecture decision affecting all scenario generation.

---

### AD-2: Separate Event Injection Generator

**Decision**: Create `event_injector.py` module for event-specific XML generation, separate from `additional_generator.py`.

**Rationale**:

**Why Separate Module?**

- **Event XML differs fundamentally from strategy XML**:
  - Events: `<closedLane>`, `<rerouter>` (simulation state changes)
  - Strategies: `<variableSpeedSign>`, `<calibrator>` (control actions)
- **Different responsibilities**: Event injection simulates incidents, control strategies respond to them
- **Different evolution paths**: Event types will expand (weather, disasters) independent of control strategies

**Event Types and XML Elements**:

| Event Type | SUMO Element | Attributes | Example |
|------------|--------------|-----------|---------|
| 交通事故 (Accident) | `<closedLane>` | edge, lanes, disallow, begin, end | Lane closure for accident duration |
| 交通阻塞 (Congestion) | `<rerouter>` | edges, begin, end | Reroute vehicles (placeholder Phase 1) |
| 交通管制 (Road Control) | `<closedLane>` or `<rerouter>` | TBD Phase 2 | Authority-imposed restrictions |
| 地质灾害 (Geological) | `<closedLane>` | TBD Phase 2 | Extended lane closures |
| 车辆故障 (Breakdown) | `<closedLane>` | TBD Phase 2 | Temporary lane blockage |
| 恶劣天气 (Weather) | TBD | TBD Phase 2 | Visibility/speed effects |

**Module Structure**:

```python
# shared/control_tools/event_injector.py

class EventInjector:
    """Base class for event injection XML generation"""

    def __init__(self, network_file: str):
        self.network = self._load_network(network_file)

    def generate_xml(self, event_data: Dict) -> str:
        """Generate event injection XML (abstract method)"""
        raise NotImplementedError

class AccidentInjector(EventInjector):
    """Generates closedLane XML for traffic accidents"""

    def generate_xml(self, event_data: Dict) -> str:
        edge_id = event_data['edge_id']
        lane_ids = self._resolve_lane_ids(edge_id, event_data['affected_lanes'])
        begin, end = self._convert_event_time(event_data['start_time'], event_data['end_time'])

        return f'<closedLane id="accident_{event_data["report_id"]}" ' \
               f'edge="{edge_id}" lanes="{",".join(lane_ids)}" ' \
               f'disallow="all" begin="{begin}" end="{end}"/>'

class CongestionInjector(EventInjector):
    """Generates rerouter XML for congestion (placeholder)"""

    def generate_xml(self, event_data: Dict) -> str:
        # Phase 1: Basic rerouter structure
        # Phase 2: Add probability, destination, closingReroute
        return f'<rerouter id="congestion_{event_data["report_id"]}" ' \
               f'edges="{event_data["edge_id"]}" begin="0" end="3600"/>'
```

**Trade-offs**:

- ✅ **Pros**: Clean separation of concerns, easier to test event XML independently
- ✅ **Pros**: Event types can evolve without touching control strategy code
- ✅ **Pros**: Modular design allows pluggable event types (extensibility)
- ⚠️ **Cons**: Additional module to maintain (acceptable, well-scoped)

**Alternatives Considered**:

- Option A: **Separate module (selected)** - clean separation of concerns
- Option B: Extend `additional_generator.py` - rejected, mixes event and control concerns
- Option C: Inline event XML generation in scenario script - rejected, not reusable

**Priority**: Phase 1 (Foundation) - enables accident event injection.

---

### AD-3: Combined .add.xml File Per Scenario

**Decision**: Generate single `.add.xml` file containing both event injection and control strategy elements.

**Rationale**:

**Why Single File?**

- **SUMO supports multiple element types in one `.add.xml` file**:
  - Can mix `<closedLane>`, `<variableSpeedSign>`, `<calibrator>`, `<rerouter>` in same file
  - SUMO processes elements by timestamp regardless of declaration order
- **Simplifies simulation configuration**:
  - Only one additional file to reference in `.sumocfg`
  - No need to manage multiple file paths
  - Reduces risk of missing files in simulation setup
- **Logical cohesion**: Event + control response is one "scenario" conceptually

**XML Structure**:

```xml
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">

    <!-- Event Injection Section -->
    <closedLane id="accident_12547"
                edge="-4688"
                lanes="-4688_0"
                disallow="all"
                begin="6749"
                end="12069"/>

    <!-- Control Strategy Section -->
    <variableSpeedSign id="vss_upstream_001"
                       lanes="-4688_0,-4688_1,-4688_2"
                       begin="6449"
                       end="12369">
        <step time="6449" speed="16.67"/>  <!-- 60 km/h = 16.67 m/s -->
    </variableSpeedSign>

    <variableSpeedSign id="vss_downstream_001"
                       lanes="-4689_0,-4689_1,-4689_2"
                       begin="6449"
                       end="12369">
        <step time="6449" speed="22.22"/>  <!-- 80 km/h = 22.22 m/s -->
    </variableSpeedSign>
</additional>
```

**File Naming Convention**:

```
output/scenarios/{event_type}/{strategy}/scenario_{event_type}_{strategy}_{event_id}.add.xml

Examples:
- output/scenarios/01_交通事故/vss/scenario_accident_vss_12547.add.xml
- output/scenarios/01_交通事故/dhs/scenario_accident_dhs_12547.add.xml
- output/scenarios/02_交通阻塞_流量激增/tec/scenario_congestion_tec_98765.add.xml
```

**Trade-offs**:

- ✅ **Pros**: Simpler simulation setup (one file reference)
- ✅ **Pros**: Logical grouping of related elements
- ✅ **Pros**: Matches SUMO best practices (single additional file per scenario)
- ⚠️ **Cons**: Cannot reuse event XML across strategies (acceptable, small file size)

**Alternatives Considered**:

- Option A: **Combined file (selected)** - simplicity and logical cohesion
- Option B: Separate event.add.xml and control.add.xml - rejected, increases complexity
- Option C: Inline XML in .sumocfg - rejected, not reusable

**Priority**: Phase 1 (Foundation) - affects file structure and simulation workflow.

---

### AD-4: Phase 1 Supports Accidents Only

**Decision**: Implement `closedLane` generation for 交通事故 (traffic accidents) in Phase 1. Defer other event types to Phase 2.

**Rationale**:

**Why Accidents First?**

- **Highest volume**: 261 out of 399 events (65%) are traffic accidents
- **Simplest implementation**: `closedLane` is straightforward (no routing logic)
- **Highest business value**: Accidents are most critical events requiring control response
- **Clear validation**: Easy to verify lane closure in SUMO simulation

**Event Type Distribution**:

| Event Type | Count | Phase 1 | Rationale |
|------------|-------|---------|-----------|
| 交通事故 (Accident) | 261 | ✅ Yes | High volume, simple implementation |
| 交通阻塞 (Congestion) | 89 | 🟡 Placeholder | Complex rerouter logic deferred |
| 交通管制 (Road Control) | 28 | ❌ Phase 2 | Lower volume, similar to accidents |
| 地质灾害 (Geological) | 12 | ❌ Phase 2 | Extended closures, rare |
| 车辆故障 (Breakdown) | 6 | ❌ Phase 2 | Short-term closures, rare |
| 恶劣天气 (Weather) | 3 | ❌ Phase 2 | Complex simulation parameters |

**Phase 1 Deliverables**:

- Accident event injection (`closedLane` XML generation)
- Congestion rerouter placeholder (basic structure, no routing logic)
- 18+ scenarios: 6 accident events × 3 control strategies = 18 minimum

**Phase 2 Roadmap** (Future):

- Implement congestion rerouter with probability/destination logic
- Add road control and geological disaster event types
- Implement weather effects (visibility, speed reduction)
- Add event cascading (multi-event scenarios)

**Trade-offs**:

- ✅ **Pros**: Faster delivery (3-4 weeks vs 6-8 weeks for all types)
- ✅ **Pros**: Focused scope reduces risk of scope creep
- ✅ **Pros**: 65% of events covered in Phase 1
- ⚠️ **Cons**: Other event types require Phase 2 (acceptable, prioritized roadmap)

**Alternatives Considered**:

- Option A: **Accidents only Phase 1 (selected)** - fastest path to value
- Option B: All event types Phase 1 - rejected, 6-8 weeks implementation time
- Option C: Accidents + congestion Phase 1 - rejected, complex rerouter logic adds risk

**Priority**: Phase 1 (Scope Definition) - defines MVP deliverables.

---

## Data Flow Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Input: events/all_extracted_events.csv (399 events)            │
│  - event_type, edge_id, junction_id, start_time, end_time      │
│  - affected_lanes, road, direction, duration                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: Scenario Generation Script                            │
│  scripts/generate_scenarios_from_events.py                      │
│                                                                 │
│  [1] Filter Events (duration, spatial matching, quality)       │
│      → Select 18-30 representative events                      │
│                                                                 │
│  [2] Stratify by Event Type (3 per type minimum)               │
│      → Ensure diverse coverage                                 │
│                                                                 │
│  [3] Map to Control Strategies (3 per event: VSS/DHS/TEC)      │
│      → Generate 18+ event-strategy pairs                       │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: Event Scenario Generator                              │
│  shared/control_tools/scenario_generator.py                     │
│                                                                 │
│  For each event-strategy pair:                                 │
│    ┌──────────────────────────────────────────────────────┐   │
│    │ [4] Generate Event XML                               │   │
│    │     → event_injector.generate_xml(event_data)        │   │
│    │     → Returns: <closedLane> or <rerouter> element    │   │
│    └────────────────┬─────────────────────────────────────┘   │
│                     │                                           │
│    ┌────────────────▼─────────────────────────────────────┐   │
│    │ [5] Generate Control XML                             │   │
│    │     → additional_generator.generate_strategy_xml()   │   │
│    │     → Returns: <variableSpeedSign>/<calibrator>/etc  │   │
│    └────────────────┬─────────────────────────────────────┘   │
│                     │                                           │
│    ┌────────────────▼─────────────────────────────────────┐   │
│    │ [6] Combine XML Elements                             │   │
│    │     → Wrap in <additional> root                      │   │
│    │     → Validate combined XML structure                │   │
│    └────────────────┬─────────────────────────────────────┘   │
│                     │                                           │
│    ┌────────────────▼─────────────────────────────────────┐   │
│    │ [7] Validate with SUMO Schema                        │   │
│    │     → xml_validator.validate_sumo_xml()              │   │
│    └────────────────┬─────────────────────────────────────┘   │
│                     │                                           │
│    ┌────────────────▼─────────────────────────────────────┐   │
│    │ [8] Write .add.xml File                              │   │
│    │     → Save to output/scenarios/{type}/{strategy}/    │   │
│    └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Output: Scenario Library                                       │
│                                                                 │
│  output/scenarios/                                              │
│  ├── 01_交通事故/                                               │
│  │   ├── vss/scenario_accident_vss_12547.add.xml              │
│  │   ├── dhs/scenario_accident_dhs_12547.add.xml              │
│  │   └── tec/scenario_accident_tec_12547.add.xml              │
│  ├── 02_交通阻塞_流量激增/                                      │
│  │   └── ... (3 strategies each)                              │
│  └── scenario_index.json (metadata for all scenarios)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Scenario Generation Layer                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  scripts/generate_scenarios_from_events.py                      │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ Main Script Functions:                                │     │
│  │ - filter_representative_events()                      │     │
│  │ - stratify_events_by_type()                           │     │
│  │ - map_event_to_strategies()                           │     │
│  │ - calculate_control_parameters()                      │     │
│  │ - generate_scenario_library() [main loop]            │     │
│  │ - create_scenario_index()                             │     │
│  └───────────────────────────────────────────────────────┘     │
│                                                                 │
└────────────┬────────────────────────────────────────────────────┘
             │ calls
             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Event Scenario Generation Layer                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  shared/control_tools/scenario_generator.py                     │
│  ┌───────────────────────────────────────────────────────┐     │
│  │ ScenarioGenerator:                                    │     │
│  │ + generate_scenario(event_data, strategy, params)    │     │
│  │ + combine_event_and_control_xml(event, control)      │     │
│  │ + generate_scenario_path(type, strategy, id)         │     │
│  │ + generate_scenario_metadata(event, control)         │     │
│  │ + validate_scenario_consistency(event, control)      │     │
│  └───────────────────────────────────────────────────────┘     │
│                                                                 │
└──────────┬──────────────────────────────────┬───────────────────┘
           │                                  │
           │ calls                            │ calls
           ▼                                  ▼
┌──────────────────────────┐     ┌───────────────────────────────┐
│ Event Injection Layer    │     │ Control Strategy Layer        │
├──────────────────────────┤     ├───────────────────────────────┤
│                          │     │                               │
│ event_injector.py        │     │ additional_generator.py       │
│ ┌──────────────────────┐ │     │ ┌───────────────────────────┐ │
│ │ EventInjector (base) │ │     │ │ generate_strategy_xml()   │ │
│ │ + generate_xml()     │ │     │ │   (existing, reused)      │ │
│ └──────────────────────┘ │     │ └───────────────────────────┘ │
│                          │     │                               │
│ ┌──────────────────────┐ │     │ Generates:                    │
│ │ AccidentInjector     │ │     │ - VSS: variableSpeedSign      │
│ │ + generate_xml()     │ │     │ - DHS: rerouter (lane open)   │
│ │ + _resolve_lane_ids()│ │     │ - TEC: calibrator             │
│ └──────────────────────┘ │     └───────────────────────────────┘
│                          │
│ ┌──────────────────────┐ │
│ │ CongestionInjector   │ │
│ │ + generate_xml()     │ │
│ │   (placeholder)      │ │
│ └──────────────────────┘ │
└──────────────────────────┘
           │
           │ calls
           ▼
┌──────────────────────────────────────────────────────────────┐
│                    Validation Layer                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  shared/control_tools/xml_validator.py (existing, reused)   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ validate_sumo_xml(xml_content, schema_type)            │ │
│  │   - Validates against SUMO XSD schemas                 │ │
│  │   - Checks element-specific constraints                │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Key Design Patterns

### 1. Strategy Pattern (Event Injectors)

```python
# Base class defines interface
class EventInjector(ABC):
    @abstractmethod
    def generate_xml(self, event_data: Dict) -> str:
        pass

# Concrete implementations for each event type
class AccidentInjector(EventInjector):
    def generate_xml(self, event_data: Dict) -> str:
        return self._generate_closed_lane_xml(event_data)

class CongestionInjector(EventInjector):
    def generate_xml(self, event_data: Dict) -> str:
        return self._generate_rerouter_xml(event_data)

# Factory selects appropriate injector
def create_event_injector(event_type: str) -> EventInjector:
    injectors = {
        '交通事故': AccidentInjector,
        '交通阻塞': CongestionInjector,
        # Add more types in Phase 2
    }
    return injectors[event_type]()
```

### 2. Template Method Pattern (Scenario Generation)

```python
class ScenarioGenerator:
    def generate_scenario(self, event_data, strategy, params):
        """Template method defining scenario generation workflow"""

        # Step 1: Generate event XML (varies by event type)
        event_xml = self._generate_event_xml(event_data)

        # Step 2: Generate control XML (varies by strategy)
        control_xml = self._generate_control_xml(strategy, params)

        # Step 3: Combine XML (common logic)
        combined_xml = self._combine_xml(event_xml, control_xml)

        # Step 4: Validate (common logic)
        self._validate_xml(combined_xml)

        # Step 5: Write file (common logic)
        file_path = self._generate_file_path(event_data, strategy)
        self._write_scenario_file(file_path, combined_xml)

        return file_path
```

### 3. Facade Pattern (Scenario Generator)

```python
# Simple interface hides complex subsystem interactions
class ScenarioGenerator:
    def __init__(self):
        self.event_injector = EventInjector()
        self.control_generator = AdditionalGenerator()
        self.xml_validator = XMLValidator()

    def generate_scenario(self, event_data, strategy, params):
        """Single method hides complexity of XML generation"""
        # Orchestrates multiple subsystems
        event_xml = self.event_injector.generate_xml(event_data)
        control_xml = self.control_generator.generate_strategy_xml(strategy, params)
        combined = self._combine_xml(event_xml, control_xml)
        self.xml_validator.validate_sumo_xml(combined)
        return self._write_file(combined)
```

---

## Data Models

### Event Data Model

```python
@dataclass
class EventData:
    """Event data from CSV with spatial matching"""
    report_id: str              # Unique event ID (e.g., "12547")
    event_type: str             # Event type (交通事故, 交通阻塞, etc.)
    event_description: str      # Chinese description
    road: str                   # G5京昆高速（绵广段）
    direction: str              # 上行/下行
    location: str               # K1576+000
    start_time: str             # YYYY-MM-DD HH:MM:SS
    end_time: str               # YYYY-MM-DD HH:MM:SS
    duration_hours: float       # Computed from start/end
    affected_lanes: List[str]   # [应急车道, 第一车道]

    # Spatial matching (from network analysis)
    junction_id: str            # SUMO junction ID (e.g., "-35882")
    edge_id: str                # SUMO edge ID (e.g., "-4688")

    # Metadata
    data_source: str            # CSV file path
    extraction_date: str        # When extracted from source
```

### Control Strategy Parameters

```python
@dataclass
class ControlStrategyParams:
    """Parameters for control strategy generation"""
    strategy_type: str          # VSS, DHS, or TEC

    # VSS specific
    speed_limit: Optional[int]  # km/h (e.g., 60)
    affected_lanes: Optional[List[str]]  # Lane IDs for speed limit

    # DHS specific
    open_shoulder: Optional[bool]  # Open emergency lane
    shoulder_edge_id: Optional[str]  # Edge with shoulder

    # TEC specific
    flow_reduction: Optional[float]  # 0.0-1.0 (e.g., 0.3 = 30% reduction)
    toll_entrance_edge: Optional[str]  # Entrance edge ID

    # Timing
    activation_offset: int      # Seconds before event (e.g., 300 = 5 min)
    deactivation_offset: int    # Seconds after event (e.g., 300)
```

### Scenario Metadata

```python
@dataclass
class ScenarioMetadata:
    """Metadata for generated scenario"""
    scenario_id: str            # SC_EVT_001
    scenario_name: str          # 京昆高速K1576交通事故+VSS限速
    event_type: str             # 交通事故
    control_strategy: str       # VSS
    source_event_id: str        # 12547

    # Location
    road: str                   # G5京昆高速（绵广段）
    location: str               # K1576+000
    direction: str              # 上行/下行

    # Timing
    duration_hours: float       # 1.48
    created_date: str           # YYYY-MM-DD

    # Files
    file_path: str              # Relative path to .add.xml
    simulation_files: Dict[str, str]  # {"additional_file": "..."}

    # Classification
    tags: List[str]             # ["货车追尾", "应急车道", "夜间"]

    # Analysis results (populated after simulation)
    effectiveness_score: Optional[int]  # 0-100
    simulation_count: int       # Number of times simulated

    # Preview data
    preview: Dict[str, Any]     # Event details for UI display
```

### Event Description JSON Model

```python
@dataclass
class EventDescriptionJSON:
    """Event description JSON file structure"""
    event_id: str
    event_type: str
    event_description: str
    location: EventLocation
    time: EventTime
    impact: EventImpact

@dataclass
class EventLocation:
    """Event location details"""
    road: str                   # G5京昆高速（绵广段）
    direction: str              # 上行/下行
    mileage: str                # K1576+000
    junction_id: str            # SUMO junction ID
    edge_id: str                # SUMO edge ID

@dataclass
class EventTime:
    """Event time information"""
    start_time: str             # YYYY-MM-DD HH:MM:SS
    end_time: str               # YYYY-MM-DD HH:MM:SS
    duration_hours: float       # Computed duration

@dataclass
class EventImpact:
    """Event impact information"""
    affected_lanes: List[str]   # ["应急车道"]
    lane_ids: List[str]         # ["-4688_0"]
```

**JSON File Example**:
```json
{
  "event_id": "12547",
  "event_type": "交通事故",
  "event_description": "货车追尾事故",
  "location": {
    "road": "G5京昆高速（绵广段）",
    "direction": "下行",
    "mileage": "K1576+000",
    "junction_id": "-35882",
    "edge_id": "-4688"
  },
  "time": {
    "start_time": "2025-07-14 01:53:49",
    "end_time": "2025-07-14 03:22:39",
    "duration_hours": 1.48
  },
  "impact": {
    "affected_lanes": ["应急车道"],
    "lane_ids": ["-4688_0"]
  }
}
```

### Traffic Input Config JSON Model

```python
@dataclass
class TrafficInputConfigJSON:
    """Traffic input configuration JSON file structure"""
    od_time_range: ODTimeRange
    od_table: str               # Database table name
    simulation_duration_hours: float
    vehicle_types: List[str]    # ["passenger", "truck", "bus"]

@dataclass
class ODTimeRange:
    """OD data time range with buffer"""
    start: str                  # event_start - buffer (YYYY-MM-DD HH:MM:SS)
    end: str                    # event_end + buffer (YYYY-MM-DD HH:MM:SS)
    event_start: str            # Original event start time
    event_end: str              # Original event end time
    buffer_minutes: int         # Buffer duration (default: 30)
```

**JSON File Example**:
```json
{
  "od_time_range": {
    "start": "2025-07-14 01:23:49",
    "end": "2025-07-14 03:52:39",
    "event_start": "2025-07-14 01:53:49",
    "event_end": "2025-07-14 03:22:39",
    "buffer_minutes": 30
  },
  "od_table": "baseline.od_data_sichuan_202507",
  "simulation_duration_hours": 2.5,
  "vehicle_types": ["passenger", "truck", "bus"]
}
```

**Buffer Time Rationale**:
- **30 minutes before event**: Capture baseline traffic conditions
- **30 minutes after event**: Observe traffic recovery period
- **Configurable**: Can be adjusted based on event characteristics

**OD Table Selection Logic**:
```python
def determine_od_table(event_date: datetime) -> str:
    """Select appropriate OD data table based on event date"""
    year_month = event_date.strftime("%Y%m")
    return f"baseline.od_data_sichuan_{year_month}"

# Example: "2025-07-14" → "baseline.od_data_sichuan_202507"
```

### Control Strategy Config JSON Model

```python
@dataclass
class ControlStrategyConfigJSON:
    """Control strategy configuration JSON file structure"""
    strategy_type: str          # VSS, DHS, TEC
    strategy_name: str          # Chinese display name
    parameters: StrategyParameters
    timing: StrategyTiming

@dataclass
class StrategyParameters:
    """Strategy-specific parameters"""
    # VSS parameters
    speed_limit_kmh: Optional[int]

    # DHS parameters
    open_shoulder: Optional[bool]
    shoulder_lane_ids: Optional[List[str]]

    # TEC parameters
    flow_reduction: Optional[float]
    toll_entrance_edge: Optional[str]

    # Common parameters
    affected_edges: List[str]
    affected_lanes: List[str]
    response_delay_seconds: int     # Time AFTER event detection (realistic: 300s = 5min)
    recovery_period_seconds: int    # Time AFTER event ends (allow stabilization: 600s = 10min)

@dataclass
class StrategyTiming:
    """Control strategy activation timing"""
    activation_time: str        # YYYY-MM-DD HH:MM:SS (event_start + response_delay)
    deactivation_time: str      # YYYY-MM-DD HH:MM:SS (event_end + recovery_period)
```

**JSON File Example**:
```json
{
  "strategy_type": "VSS",
  "strategy_name": "可变限速标志",
  "parameters": {
    "speed_limit_kmh": 60,
    "affected_edges": ["-4688", "-4689"],
    "affected_lanes": ["-4688_0", "-4688_1", "-4688_2"],
    "response_delay_seconds": 300,      // 5 min after event detection
    "recovery_period_seconds": 600      // 10 min after event ends
  },
  "timing": {
    "activation_time": "2025-07-14 01:58:49",   // event_start + 5min
    "deactivation_time": "2025-07-14 03:32:39"  // event_end + 10min
  }
}
```

**Control Timing Calculation** (Corrected - Realistic Response):
```python
def calculate_control_timing(event_start: datetime, event_end: datetime,
                             response_delay: int, recovery_period: int) -> dict:
    """
    Calculate control strategy activation/deactivation times.

    IMPORTANT: Control activates AFTER event occurs (realistic scenario).
    Event must happen before control can respond - cannot predict future.

    Args:
        event_start: Event start time
        event_end: Event end time
        response_delay: Seconds AFTER event detection to activate (default: 300 = 5min)
        recovery_period: Seconds AFTER event ends to deactivate (default: 600 = 10min)

    Returns:
        Dict with activation_time and deactivation_time
    """
    # Control activates AFTER event starts (response delay)
    activation = event_start + timedelta(seconds=response_delay)

    # Control deactivates AFTER event ends (recovery period)
    deactivation = event_end + timedelta(seconds=recovery_period)

    return {
        "activation_time": activation.strftime("%Y-%m-%d %H:%M:%S"),
        "deactivation_time": deactivation.strftime("%Y-%m-%d %H:%M:%S")
    }

# Example: Event 01:53:49 - 03:22:39
#          Response delay: 300s (5 min), Recovery: 600s (10 min)
# → Control active 01:58:49 - 03:32:39
#   (5 min after event starts, 10 min after event ends)
```

**Rationale for Response Delay**:
- Event detection time (monitoring systems identify the incident)
- Decision-making time (operators analyze and decide on control strategy)
- Activation time (system deployment and activation)
- Total realistic delay: 3-10 minutes (default: 5 minutes)

---

## XML Schema Validation

### SUMO Additional File Schema

All generated `.add.xml` files must validate against SUMO's additional file schema:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="additional">
    <xs:complexType>
      <xs:choice maxOccurs="unbounded">
        <xs:element name="closedLane" type="closedLaneType"/>
        <xs:element name="rerouter" type="rerouterType"/>
        <xs:element name="variableSpeedSign" type="vssType"/>
        <xs:element name="calibrator" type="calibratorType"/>
        <!-- ... other elements ... -->
      </xs:choice>
    </xs:complexType>
  </xs:element>
</xs:schema>
```

### Validation Strategy

1. **Syntax Validation**: Check XML is well-formed
2. **Schema Validation**: Validate against SUMO XSD using `xml_validator.py`
3. **Semantic Validation**: Check scenario-specific consistency rules

```python
def validate_scenario_consistency(event_data, control_params):
    """Scenario-specific validation rules"""
    errors = []

    # Rule 1: Control activation must start before or at event time
    if control_params.activation_time > event_data.start_time:
        errors.append("Control activation after event start")

    # Rule 2: Event location and control location must be compatible
    if not is_location_compatible(event_data.edge_id, control_params.affected_edges):
        errors.append("Control location incompatible with event location")

    # Rule 3: Lane closures and control lanes must not conflict
    if has_lane_conflict(event_data.affected_lanes, control_params.affected_lanes):
        errors.append("Lane closure conflicts with control lanes")

    return errors
```

---

## Error Handling Strategy

### Validation Errors

```python
class ScenarioValidationError(Exception):
    """Raised when scenario validation fails"""
    pass

def generate_scenario_with_validation(event_data, strategy, params):
    try:
        # Generate XMLs
        event_xml = generate_event_xml(event_data)
        control_xml = generate_control_xml(strategy, params)

        # Validate
        validate_xml_syntax(event_xml)
        validate_xml_syntax(control_xml)

        combined = combine_xml(event_xml, control_xml)
        validate_sumo_schema(combined)
        validate_scenario_consistency(event_data, params)

        return combined

    except XMLSyntaxError as e:
        logger.error(f"XML syntax error in scenario {event_data.report_id}: {e}")
        raise ScenarioValidationError(f"Invalid XML: {e}")

    except SchemaValidationError as e:
        logger.error(f"SUMO schema violation in scenario {event_data.report_id}: {e}")
        raise ScenarioValidationError(f"Schema violation: {e}")

    except ConsistencyError as e:
        logger.error(f"Scenario consistency error in {event_data.report_id}: {e}")
        raise ScenarioValidationError(f"Consistency check failed: {e}")
```

### Batch Generation Resilience

```python
def generate_scenario_library(events, output_dir):
    """Generate scenarios with error tolerance"""
    results = {
        'success': [],
        'failed': [],
        'total': len(events)
    }

    for event in events:
        for strategy in ['VSS', 'DHS', 'TEC']:
            try:
                scenario_path = generate_scenario(event, strategy, params)
                results['success'].append({
                    'event_id': event.report_id,
                    'strategy': strategy,
                    'path': scenario_path
                })
                logger.info(f"✓ Generated scenario {event.report_id}_{strategy}")

            except ScenarioValidationError as e:
                results['failed'].append({
                    'event_id': event.report_id,
                    'strategy': strategy,
                    'error': str(e)
                })
                logger.warning(f"✗ Failed scenario {event.report_id}_{strategy}: {e}")
                continue  # Continue with next scenario

    # Log summary
    logger.info(f"Scenario generation complete: "
                f"{len(results['success'])}/{results['total']} succeeded, "
                f"{len(results['failed'])} failed")

    return results
```

---

## Testing Strategy

### Unit Tests

```python
# Test event XML generation
def test_accident_xml_generation():
    event = EventData(report_id="12547", event_type="交通事故", ...)
    injector = AccidentInjector()
    xml = injector.generate_xml(event)

    assert '<closedLane id="accident_12547"' in xml
    assert 'edge="-4688"' in xml
    assert 'disallow="all"' in xml

# Test lane ID resolution
def test_lane_id_resolution():
    injector = AccidentInjector(network_file="test_network.net.xml")
    lane_ids = injector._resolve_lane_ids("-4688", ["应急车道", "第一车道"])

    assert lane_ids == ["-4688_0", "-4688_1"]

# Test time conversion
def test_event_time_conversion():
    start = "2025-07-14 01:53:49"
    end = "2025-07-14 03:22:39"
    sim_start = "2025-07-14 00:00:00"

    begin, duration = convert_event_time(start, end, sim_start)
    assert begin == 6829  # seconds from sim start
    assert duration == 5330  # seconds duration
```

### Integration Tests

```python
# Test end-to-end scenario generation
def test_scenario_generation_e2e():
    event = load_test_event("test_event_12547.json")
    generator = ScenarioGenerator()

    scenario_path = generator.generate_scenario(
        event_data=event,
        strategy='VSS',
        params={'speed_limit': 60}
    )

    assert scenario_path.exists()
    assert scenario_path.suffix == '.xml'

    # Validate XML content
    xml_content = scenario_path.read_text()
    assert '<closedLane' in xml_content
    assert '<variableSpeedSign' in xml_content

    # Validate against SUMO schema
    validation_result = validate_sumo_xml(xml_content)
    assert validation_result.is_valid

# Test SUMO simulation execution
def test_scenario_simulation():
    scenario_path = "output/scenarios/test/scenario_test.add.xml"
    sumocfg = create_test_sumocfg(additional_file=scenario_path)

    result = run_sumo_simulation(sumocfg)

    assert result.exit_code == 0
    assert result.summary_xml.exists()

    # Verify event injection active
    summary = parse_summary_xml(result.summary_xml)
    assert summary['teleports'] < 10  # Control mitigates event impact
```

---

## Performance Considerations

### Batch Generation Performance

**Target**: Generate 18-30 scenarios in < 5 minutes

**Bottlenecks**:
- Network file parsing (load once, reuse)
- XML validation (use cached schemas)
- File I/O (batch writes)

**Optimizations**:

```python
class ScenarioGenerator:
    def __init__(self, network_file: str):
        # Load network once, reuse for all scenarios
        self.network = sumolib.net.readNet(network_file, withInternal=False)

        # Cache SUMO schemas
        self.xml_validator = XMLValidator(cache_schemas=True)

    def generate_scenario_library(self, events, strategies):
        """Optimized batch generation"""

        # Pre-compute event-strategy pairs
        pairs = [(e, s) for e in events for s in strategies]

        # Generate in parallel (optional Phase 2)
        # results = parallel_map(self._generate_single, pairs, workers=4)

        # Sequential generation (Phase 1)
        results = [self._generate_single(event, strategy)
                   for event, strategy in pairs]

        return results
```

---

## Summary

This design provides a modular, extensible foundation for event scenario generation:

- **Reuses** proven control strategy generation infrastructure
- **Separates** event injection concerns from control strategy logic
- **Validates** all generated XML against SUMO schemas
- **Handles** errors gracefully during batch generation
- **Supports** future expansion to additional event types

The implementation follows established patterns from the control workflow domain while adapting to the unique requirements of event-based simulation scenarios.

**Next Steps**: Proceed with implementation according to `tasks.md` phased breakdown.
