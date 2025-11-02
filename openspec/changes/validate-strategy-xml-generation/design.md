# Design: SUMO-Compatible Strategy XML Generation and Validation

## 1. Context

### Problem Statement
The strategy management system generates control.add.xml files for SUMO simulation, but lacks validation mechanisms to ensure:
- XML is well-formed and SUMO-compliant
- Edge references exist in network topology
- Parameter values are within SUMO constraints
- Strategies are updated cascadingly when referenced

### Current System
```
UI (Parameter Form)
  ↓
control_plan_service.create_plan()
  ↓
additional_generator.generate_plan_additional()
  ↓
XML String (unvalidated)
  ↓
Write to control_data/plans/{plan_id}/control.add.xml
```

**Issues**:
- No validation before writing file
- No edge existence checks
- No XML well-formedness check
- Manual cascade on strategy update

### Proposed System
```
UI (Parameter Form)
  ↓
control_strategy_service.validate_parameters()  [✓ edge exists, ✓ units correct]
  ↓
control_plan_service.create_plan()
  ↓
additional_generator.generate_plan_additional()
  ↓
xml_validator.validate_sumo_xml()  [✓ well-formed, ✓ attributes correct]
  ↓
Write to control_data/plans/{plan_id}/control.add.xml  [✓ guaranteed valid]
  ↓
strategy_instance_service.update_strategy()
  ↓
Cascade: regenerate all referencing plans' XMLs  [✓ automatic sync]
```

### Parameter Transformation Flow

**Critical Data Path**: Strategy Instance → Parameters → XML Generation

The system transforms parameters through three layers, each with specific validation:

**Layer 1: Strategy Instance (control_data/strategies/{strategy_id}.json)**
```json
{
  "parameters": {
    "affected_edges": ["-8712", "-15452.627", ...],
    "speed_steps": [
      {"time_hours": 7, "speed_kmh": 100},
      {"time_hours": 9, "speed_kmh": 80}
    ],
    "intervals": [
      {"begin_hours": 7, "end_hours": 10, "status": "OPEN"}
    ]
  },
  "template": {
    "parameters_schema": [
      {
        "parameter_name": "speed_steps",
        "step_structure": {
          "time_display_unit": "hours",
          "time_sumo_unit": "seconds",
          "time_conversion_factor": 3600,
          "speed_display_unit": "km/h",
          "speed_sumo_unit": "m/s",
          "speed_conversion_factor": 0.277778
        }
      }
    ]
  }
}
```
**Validation Point 1**: Ensure parameters match template schema
- All required fields present
- Data types correct (string, number, array)
- Value ranges within constraints (speed 30-130 km/h, time 0-24 hours)

**Layer 2: Additional Generator (additional_generator.py)**
```python
# ⚠️ CRITICAL: Time conversion uses case's simulation start time
# Load from case metadata: case.time_range.start (e.g., "2025/09/01 08:00:00")
# This is UTC+8 timezone (ignore metadata timezone errors)
case_start_hour = parse_time_range_start(case.time_range.start)  # Extract hour (8)
case_start_seconds = case_start_hour * 3600  # 8 * 3600 = 28800 seconds

# VSS: Transform time_hours → absolute seconds from case start
for step in speed_steps:
    # time_hours is RELATIVE to case start, not absolute 00:00
    # Example: If case starts at 08:00 (28800s) and step.time_hours=7
    # CORRECT: offset from 08:00, so absolute = 28800 + (7-8)*3600 = 25200 ✗ WRONG!
    # ACTUALLY: 7 is absolute hour, convert directly: 7 * 3600 = 25200 ✓
    # NOTE: Clarify if time_hours is absolute (clock time) or relative to start
    time_seconds = int(step["time_hours"] * 3600)      # 7 hours → 25200 seconds (absolute)
    speed_ms = round(float(step["speed_kmh"]) / 3.6, 2)  # 100 km/h → 27.78 m/s

# DHS: Transform interval times and map vehicle types (TWO-LAYER)
for interval in intervals:
    # Layer 1: hours → seconds (using case start time if relative)
    begin_seconds = int(interval["begin_hours"] * 3600)  # 7 → 25200
    end_seconds = int(interval["end_hours"] * 3600)      # 10 → 36000

    # Layer 2: allowed_vehicle_types conversion (UI types → SUMO vClass)
    # vehicle_types.json mapping:
    # "passenger" → vClass: "passenger" (from passenger_small/large)
    # "truck" → vClass: "truck" (from truck_small/large)
    # "delivery" → vClass: "delivery" (from special_small/large)
    allowed_types = interval.get("allowed_vehicle_types", [])
    sumo_types = [_map_vehicle_type_to_sumo(t) for t in allowed_types]
    # Result: ["passenger", "truck"] → join with space: "passenger truck"

# TEC: Transform flow intervals
for flow in flow_intervals:
    begin_seconds = int(flow["begin_hours"] * 3600)
    end_seconds = int(flow["end_hours"] * 3600)
    # vehsPerHour: no conversion needed (already numeric)

def _map_vehicle_type_to_sumo(ui_type: str) -> str:
    """
    Map UI vehicle type to SUMO vClass from vehicle_types.json

    UI types: "passenger", "truck", "delivery"
    → vehicle_types.json categories: {passenger_small, passenger_large, truck_small, truck_large, special_small, special_large}
    → SUMO vClass: "passenger", "truck", "delivery" (extract category field from JSON)
    """
    mapping = {
        "passenger": "passenger",  # UI type → SUMO vClass
        "truck": "truck",
        "delivery": "delivery"
    }
    return mapping.get(ui_type, "")  # Return empty if unknown (will close lane)
```
**Validation Point 2**: Ensure transformations are correct
- **Time conversion**: Use case metadata start time (from `case.time_range.start`)
  - Currently stores as absolute hours (0-24), not relative to case start
  - Clarify if times are absolute (clock time) or relative to case start time
- **Speed conversion**: ÷3.6, round to 2 decimals (already correct)
- **Vehicle type conversion**: Two-layer mapping (UI type → vehicle_types.json → SUMO vClass)
  - "passenger" → vClass "passenger"
  - "truck" → vClass "truck"
  - "delivery" → vClass "delivery"
- Precision maintained (speed: 2 decimal places, time: integer seconds)
- No data loss during type conversion

**Layer 3: SUMO XML (control.add.xml)**
```xml
<variableSpeedSign id="..." edges="...">
    <step time="25200" speed="27.78"/>    <!-- Transformed from time_hours=7, speed_kmh=100 -->
    <step time="32400" speed="22.22"/>    <!-- Transformed from time_hours=9, speed_kmh=80 -->
</variableSpeedSign>

<rerouter id="..." edges="...">
    <interval begin="25200" end="36000">  <!-- Transformed from begin_hours=7, end_hours=10 -->
        <closingLaneReroute id="0" allow="passenger truck"/>  <!-- From allowed_vehicle_types -->
    </interval>
</rerouter>
```
**Validation Point 3**: Ensure XML is well-formed and SUMO-compliant
- Attributes present and correct type
- Values within SUMO constraints
- Element structure valid

**Critical Validation Chain**:
1. ✅ **Parameter Layer**: Validate before saving to strategy instance
2. ✅ **Transformation Layer**: Validate conversion formulas during XML generation
3. ✅ **XML Layer**: Validate final XML format before writing to file

## 2. Goals & Non-Goals

### Goals
- ✅ Guarantee generated XML is SUMO v1.19+ compatible
- ✅ Detect invalid parameters early (at strategy/plan creation time)
- ✅ Maintain consistency when strategies are updated (cascade regeneration)
- ✅ Provide clear error messages for validation failures
- ✅ Minimize performance impact (<50ms per validation)

### Non-Goals
- ❌ Validate network topology (done by network loader)
- ❌ Simulate SUMO execution (only validate XML format)
- ❌ Support custom SUMO vehicle types (only standard: passenger, bus, truck, emergency)
- ❌ Implement WebSocket for real-time strategy updates (async background task sufficient)

## 3. Technical Decisions

### 3.1 Validation Levels

**Level 1: Parameter Validation** (at strategy creation/update)
```python
# In control_strategy_service.validate_parameters()
✓ Speed range: 30-130 km/h
✓ Time ordering: begin < end
✓ Edge count: ≥1
✓ Lane index: 0 ≤ lane_index < num_lanes (from network)
✓ Vehicle types: in {passenger, bus, truck, emergency}
```

**Level 2: XML Validation** (after generation)
```python
# In xml_validator.validate_sumo_xml()
✓ Well-formed XML (ElementTree parse)
✓ Root element is <additional>
✓ Strategy elements (variableSpeedSign, rerouter, calibrator) present
✓ All required attributes present and correct type
✓ Speed values in m/s (2 decimal places)
✓ Time values in seconds (non-negative integers)
✓ Edge/lane references valid format
```

**Level 3: Network Topology Validation** (optional, for critical plans)
```python
# In network_validator (deferred to Phase 2)
✓ Referenced edges exist in network
✓ Lane indices within edge bounds
✓ Hard shoulder edges are consecutive
```

### 3.2 New Module: xml_validator.py

**Location**: `shared/control_tools/xml_validator.py`

**Key Functions**:
```python
def validate_sumo_xml(
    xml_content: str,
    strategy_type: str = None  # Optional filter: "VSS", "DHS", "TEC"
) -> ValidationResult:
    """
    Validate generated SUMO XML for correctness.

    Args:
        xml_content: XML string from additional_generator
        strategy_type: Optional type filter for specific validation

    Returns:
        ValidationResult(
            is_valid: bool,
            errors: List[str],  # Critical issues
            warnings: List[str]  # Non-critical issues
        )
    """
```

**Implementation Strategy**:
1. Check well-formedness (ElementTree parse)
2. Validate root element
3. Iterate through child elements (variableSpeedSign, rerouter, calibrator)
4. For each element, validate:
   - Required attributes present
   - Attribute types correct (int/float)
   - Value ranges valid (e.g., 0-86400 for time)
   - Format constraints met (e.g., float speed has 2 decimals)

### 3.3 Parameter Validation Enhancement

**Location**: `control_strategy_service.py` → `validate_parameters()`

**New Validation Checks**:
```python
@retry_on_db_failure()
def validate_parameters(self, strategy_type: str, parameters: Dict[str, Any]) -> ValidationResult:
    """Comprehensive parameter validation with SUMO constraints."""

    errors = []
    warnings = []

    if strategy_type == "VSS":
        # Speed validation: 30-130 km/h
        for step in parameters.get("speed_steps", []):
            speed_kmh = step.get("speed_kmh")
            if not (30 <= speed_kmh <= 130):
                errors.append(f"Speed {speed_kmh} km/h out of range [30, 130]")

        # Edge validation: must exist (call edge_query)
        edges = parameters.get("affected_edges", [])
        missing_edges = self._check_edges_exist(edges)
        if missing_edges:
            errors.append(f"Edges not found: {missing_edges}")

    elif strategy_type == "DHS":
        # Lane index validation
        lane_index = parameters.get("hard_shoulder_lane_index", 3)
        if not (0 <= lane_index <= 10):  # Reasonable bounds
            errors.append(f"Lane index {lane_index} out of reasonable range")

        # Time ordering
        intervals = parameters.get("intervals", [])
        for i, interval in enumerate(intervals):
            if interval["begin"] >= interval["end"]:
                errors.append(f"Interval {i}: begin >= end")

    elif strategy_type == "TEC":
        # Vehicle type validation
        allowed_types = parameters.get("allowed_vehicle_types", [])
        valid_types = {"passenger", "bus", "truck", "emergency"}
        invalid = set(allowed_types) - valid_types
        if invalid:
            errors.append(f"Invalid vehicle types: {invalid}. Must be {valid_types}")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )

def _check_edges_exist(self, edges: List[str]) -> List[str]:
    """Check if edges exist in network topology."""
    try:
        from shared.data_access.edge_query import query_edges_base
        # Query all edges at once for efficiency
        existing_edges = query_edges_base(route="", filters={})
        existing_ids = {edge['edge_id'] for edge in existing_edges}
        return [e for e in edges if e not in existing_ids]
    except Exception as e:
        logger.warning(f"Edge validation skipped: {e}")
        return []  # Don't fail validation on DB error
```

### 3.4 Cascade Regeneration on Strategy Update

**Location**: `strategy_instance_service.py` → `update_strategy()`

**Logic**:
```python
async def update_strategy(self, strategy_id: str, updates: Dict[str, Any]) -> Dict:
    """
    Update strategy and cascade regenerate all referencing plans' XMLs.
    """
    # 1. Validate new parameters
    validation = self.control_strategy_service.validate_parameters(
        strategy_type=strategy["template"]["strategy_type"],
        parameters=updates.get("parameters", strategy["parameters"])
    )
    if not validation.is_valid:
        raise ValueError(f"Invalid parameters: {validation.errors}")

    # 2. Update strategy in database/file
    updated_strategy = self._save_strategy_update(strategy_id, updates)

    # 3. **ASYNC cascade**: Find and regenerate all referencing plans
    # This runs in background, doesn't block the update response
    asyncio.create_task(
        self._cascade_regenerate_plans(strategy_id, updated_strategy)
    )

    return {
        "strategy_id": strategy_id,
        "status": "updated",
        "cascade_regeneration": "in_progress"
    }

async def _cascade_regenerate_plans(self, strategy_id: str, strategy: Dict):
    """Background task: regenerate all plans referencing this strategy."""
    try:
        # Find all plans that reference this strategy
        plans = self._find_referencing_plans(strategy_id)

        for plan_id in plans:
            try:
                logger.info(f"Regenerating XML for plan {plan_id} (strategy {strategy_id} updated)")
                self.control_plan_service.regenerate_plan_xml(plan_id)
            except Exception as e:
                logger.error(f"Failed to regenerate XML for plan {plan_id}: {e}")
                # Record failure in audit log, don't propagate error
    except Exception as e:
        logger.error(f"Cascade regeneration failed for strategy {strategy_id}: {e}")
```

### 3.5 Parameter Transformation Validation

**The transformation layer is critical** - parameters are converted from display units (hours, km/h) to SUMO units (seconds, m/s). Validation must ensure:

**VSS Parameter Chain**:
```
Strategy Instance              Validation              Additional Generator      XML Output
────────────────────────────────────────────────────────────────────────────────────────
speed_kmh: 100        ───→   30 ≤ 100 ≤ 130     ───→   100 ÷ 3.6 = 27.78 m/s   ───→   <step speed="27.78"/>
time_hours: 7         ───→   0 ≤ 7 ≤ 24        ───→   7 × 3600 = 25200 sec*   ───→   <step time="25200"/>
affected_edges: [...] ───→   edges exist?      ───→   join with spaces        ───→   edges="e1 e2 e3"

* Uses case metadata time_range.start (UTF+8, e.g., "2025/09/01 08:00:00")
  - If time_hours is ABSOLUTE (clock time): 7 → 25200 sec (from midnight)
  - If time_hours is RELATIVE to case start: 7 - 8 → -1 hour (invalid, clarify with product)
```

**DHS Parameter Chain (Two-Layer Vehicle Type Conversion)**:
```
Strategy Instance              Validation                Additional Generator          XML Output
──────────────────────────────────────────────────────────────────────────────────────────────────
begin_hours: 7        ───→   0 ≤ 7 < 24        ───→   7 × 3600 = 25200 sec    ───→   <interval begin="25200"/>
end_hours: 10         ───→   7 < 10 ≤ 24      ───→   10 × 3600 = 36000 sec   ───→   <interval end="36000"/>

allowed_vehicle_types         ALL in SUMO enum        Layer 1: UI → vehicle_types.json
["passenger",    ───→   (passenger/truck/    ───→   Extract vClass from
 "truck"]             delivery valid?)          vehicle_types.json categories

                                              Layer 2: vehicle_types.json → SUMO vClass
                                              "passenger_small".category = "passenger"
                                              "truck_large".category = "truck"
                                              Result: ["passenger", "truck"]

                                              ───→   <closingLaneReroute allow="passenger truck"/>
```

**Validation Checks During Transformation**:
1. **Precision**: Speed converted to 2 decimal places (not truncated)
2. **Type Safety**: Integer conversion for time doesn't lose information
3. **Range Verification**: Converted values still within SUMO constraints
4. **Consistency**: Time intervals don't overlap, edge lists non-empty

**Implementation Pattern** (in additional_generator.py):
```python
def generate_vss_xml(strategy_id: str, template: Dict, parameters: Dict) -> str:
    """
    Transform and validate parameters during XML generation.

    Critical: Transformation must be reversible and lossless.
    """
    for step in parameters.get("speed_steps", []):
        # Validation 1: Check source parameters exist
        if "time_hours" not in step or "speed_kmh" not in step:
            raise ValueError(f"Step missing required parameters")

        # Validation 2: Check source values in valid range
        if not (0 <= step["time_hours"] <= 24):
            raise ValueError(f"Time {step['time_hours']} out of range")
        if not (30 <= step["speed_kmh"] <= 130):
            raise ValueError(f"Speed {step['speed_kmh']} out of range")

        # Transformation
        time_seconds = int(step["time_hours"] * 3600)
        speed_ms = round(float(step["speed_kmh"]) / 3.6, 2)

        # Validation 3: Check transformed values correct
        assert time_seconds >= 0, "Time conversion failed"
        assert 0.0 <= speed_ms <= 50.0, "Speed conversion out of SUMO bounds"

        # Add to XML
        step_elem.set("time", str(time_seconds))
        step_elem.set("speed", str(speed_ms))
```

### 3.6 API Error Responses

**New Response Schema**:
```python
# api/models/control/responses/plan_response.py

class ValidationError(BaseModel):
    """Validation error detail."""
    field: str  # e.g., "affected_edges", "speed_steps[0].speed_kmh"
    message: str  # e.g., "Speed 150 km/h exceeds maximum of 130"
    type: str  # "validation" | "format" | "constraint"

class PlanCreationError(BaseModel):
    """Plan creation error with validation details."""
    error: str  # "Plan creation failed"
    reason: str  # "Invalid strategy parameters"
    validation_errors: List[ValidationError]
    affected_strategies: List[str]  # Strategy IDs with errors
```

**Error Response Example**:
```json
{
  "error": "Plan creation failed",
  "reason": "Strategy validation failed",
  "validation_errors": [
    {
      "field": "strategy_001.speed_steps[0].speed_kmh",
      "message": "Speed 150 km/h exceeds SUMO maximum of 130 km/h",
      "type": "constraint"
    },
    {
      "field": "strategy_002.affected_edges",
      "message": "Edge 'edge_12345' not found in network topology",
      "type": "validation"
    }
  ],
  "affected_strategies": ["strategy_001", "strategy_002"]
}
```

## 4. Implementation Plan

### Phase 1: Validation Infrastructure (Week 1)
1. Create `xml_validator.py` with well-formedness and format checks
2. Enhance `control_strategy_service.validate_parameters()`
3. Add validation to `control_plan_service.create_plan()`
4. Add error response models

### Phase 2: Cascade Regeneration (Week 2)
1. Add strategy reference tracking (already exists, enhance it)
2. Implement `_cascade_regenerate_plans()` in `strategy_instance_service`
3. Add audit logging for cascade events
4. Add tests for cascade behavior

### Phase 3: Network Validation (Optional, Phase 2+)
1. Implement edge existence checks against network topology
2. Implement lane boundary checks
3. Verify hard shoulder edge continuity (DHS-specific)

## 5. Data Models

### ValidationResult
```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Optional[Dict[str, Any]] = None  # For debugging
```

### StrategyReference
```python
# Already in strategy_file_manager.py
{
    "strategy_id": "strategy_real_vss_g4202_001",
    "referenced_by": ["plan_id_1", "plan_id_2"],
    "last_updated": "2025-11-02T10:30:00"
}
```

## 6. Error Handling

**Validation Failures**:
- ❌ Parameter validation fails → Return 400 Bad Request with details
- ❌ XML generation fails → Return 500 Internal Server Error (should not happen)
- ❌ Edge lookup fails → Warn and continue (degrade gracefully)

**Cascade Failures**:
- Async background task, doesn't block strategy update
- Failed regenerations logged to audit trail
- Manual regeneration available via `/plans/{plan_id}/regenerate-xml` endpoint

## 7. Performance Targets

| Operation | Target | Strategy |
|-----------|--------|----------|
| Parameter validation | <10ms | Single-thread, in-memory checks |
| XML validation | <20ms | Single parse + iteration |
| Cascade regeneration | <200ms/plan | Async, parallel when possible |
| Edge lookup (optional) | <50ms | Cached query or skip on DB error |

## 8. Testing Strategy

### Unit Tests
- `test_xml_validator.py`: Well-formedness, format, constraints
- `test_parameter_validation.py`: All strategy types, edge cases
- `test_cascade_regeneration.py`: Reference tracking, plan updates

### Integration Tests
- Full workflow: Create strategy → Create plan → Update strategy → Verify cascade
- Error scenarios: Invalid edges, out-of-range values, malformed XML

### E2E Tests
- Playwright: Create plan, verify XML file exists and is readable
- Verify cascade updates reflected in UI

## 9. Rollout Plan

### Backward Compatibility
- ✅ Existing valid plans unaffected
- ⚠️ Invalid plans (if any) will fail at next update
- Migration: Provide script to validate existing plans and report issues

### Deployment Steps
1. Deploy Phase 1 (validation) → existing plans still work, new validation applied
2. Test with staging data
3. Deploy Phase 2 (cascade) → enable cascade in config
4. Monitor cascade success/failure rates
5. (Optional) Deploy Phase 3 (network validation)

## 10. Open Questions & Trade-offs

### Q: Should network topology validation be mandatory?
**A**: Defer to Phase 2. Phase 1 focuses on XML format. Network validation requires DB access (potential performance impact). Make optional for now.

### Q: Cascade regeneration frequency?
**A**: Immediate async (Task). Alternative: batch job every hour. Immediate better for user experience, minimal overhead.

### Q: Edge case - strategy deleted?
**A**: Plans keep strategy reference, XML becomes invalid. Recommend cascade cleanup when strategy deleted (or mark plan as "needs-update").

---

## Appendix A: SUMO XML Format Reference

### VSS (Variable Speed Sign)
```xml
<variableSpeedSign id="strategy_id" edges="edge1 edge2 ...">
    <step time="0" speed="27.78"/>
    <step time="25200" speed="22.22"/>
</variableSpeedSign>
```
- `time`: Integer seconds [0, 86400]
- `speed`: Float m/s, 2 decimals [0.0, 50.0]

### DHS (Dynamic Hard Shoulder)
```xml
<rerouter id="strategy_id" edges="edge1 edge2 ...">
    <interval begin="0" end="25200">
        <closingLaneReroute id="3" allow="passenger bus truck emergency"/>
    </interval>
</rerouter>
```
- `begin`/`end`: Integer seconds
- `id`: Integer lane index (0=rightmost)
- `allow`: Space-separated vehicle types or empty (closed)

### TEC (Toll Entrance Control)
```xml
<calibrator id="strategy_id" edge="entrance_edge" pos="0">
    <flow begin="0" end="25200" vehsPerHour="480" speed="15.0"/>
</calibrator>
```
- `vehsPerHour`: Integer [0, 3000]
- `speed`: Float m/s

---

**Design Version**: 1.0
**Last Updated**: 2025-11-02
**Status**: Ready for Implementation
