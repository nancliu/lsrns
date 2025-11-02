# Supplement: Critical Time and Vehicle Type Transformation Details

**Date**: 2025-11-02 (After Initial Enhancement)
**Status**: ✅ Validated
**Focus**: Time conversion with case metadata + Two-layer vehicle type mapping

---

## Critical Issue 1: Time Conversion Must Use Case Metadata

### The Problem

Previously, the proposal simplified time conversion as:
```
time_hours × 3600 = seconds (WRONG - oversimplified!)
```

**Reality**: Time conversion depends on case metadata simulation start time!

### The Solution

**Source Data**: `case.metadata.time_range.start` (UTC+8 timestamp)
```json
{
  "case_id": "case_20251016_113040",
  "time_range": {
    "start": "2025/09/01 08:00:00",  ← Extract hour: 8
    "end": "2025/09/01 09:00:00"
  }
}
```

**Time Transformation Logic**:
```python
# Step 1: Load case metadata
case_start_timestamp = "2025/09/01 08:00:00"  # UTC+8 (ignore timezone errors in metadata)
case_start_hour = extract_hour(case_start_timestamp)  # 8

# Step 2: Determine if time_hours is ABSOLUTE or RELATIVE
# ASSUMPTION (needs confirmation): time_hours is ABSOLUTE (0-24 clock time)
#
# ABSOLUTE (Clock Time):
#   time_hours = 7 → 7 × 3600 = 25200 sec from midnight
#   (Independent of case start time, applies to any case)
#
# RELATIVE (Offset from Case Start):
#   time_hours = 7, case_start_hour = 8
#   → (7 - 8) × 3600 = -3600 sec (INVALID - negative!)
#   This would only work if case starts at hour ≥ 7

# Step 3: Validate transformed time
assert 0 <= time_seconds <= 86400, "Time out of SUMO bounds"
```

### Current Implementation Status

**Strategy instances store**: `time_hours` as ABSOLUTE clock hours (0-24)
- Example: `strategy_real_vss_g4202_001.json` has `time_hours: 7` (7:00 AM, absolute)
- NOT relative to case start (which could be 08:00)

**Implementation Note**: **CLARIFY WITH PRODUCT TEAM** whether times should ever be:
- Relative to case start time (would need case_start_hour adjustment)
- Always absolute (current assumption, simpler)

---

## Critical Issue 2: Vehicle Type Conversion is TWO-LAYER

### The Problem

Previously, the proposal treated vehicle type as simple 1-step conversion:
```
allowed_vehicle_types → SUMO allow attribute (INCOMPLETE!)
```

**Reality**: Vehicle type mapping is TWO-LAYER with `vehicle_types.json` as intermediary!

### The Solution

**Layer 1: UI Types → vehicle_types.json**
```
Strategy Instance (control_data/strategies/strategy_*.json):
{
  "parameters": {
    "intervals": [
      {
        "allowed_vehicle_types": ["passenger", "truck", "delivery"]  ← UI types
      }
    ]
  }
}
```

**Layer 2: vehicle_types.json → SUMO vClass**
```json
{
  "vehicle_types": {
    "passenger_small": {
      "category": "passenger",  ← SUMO vClass
      "vClass": "passenger",
      ...
    },
    "passenger_large": {
      "category": "passenger",  ← Same category
      ...
    },
    "truck_small": {
      "category": "truck",  ← SUMO vClass
      "vClass": "truck",
      ...
    },
    "truck_large": {
      "category": "truck",  ← Same category
      ...
    },
    "special_small": {
      "category": "delivery",  ← SUMO vClass
      "vClass": "delivery",
      ...
    },
    "special_large": {
      "category": "delivery",  ← Same category
      ...
    }
  }
}
```

### Transformation Flow

```
Strategy Instance                  vehicle_types.json              SUMO XML
──────────────────────────────────────────────────────────────────────────

allowed_vehicle_types:             Load vehicle_types.json
["passenger", "truck"]    ────→   Extract unique categories:
                                  "passenger_small".category = "passenger"
                                  "passenger_large".category = "passenger"
                                  "truck_small".category = "truck"
                                  "truck_large".category = "truck"
                                  Result: {"passenger", "truck"}
                          ────→   Join with spaces: "passenger truck"

                          ────→   <closingLaneReroute allow="passenger truck"/>
```

### Implementation Code Pattern

```python
def _map_vehicle_types_to_sumo(allowed_types: List[str], vehicle_types_json: Dict) -> str:
    """
    Two-layer vehicle type conversion.

    Args:
        allowed_types: UI types from strategy instance (e.g., ["passenger", "truck"])
        vehicle_types_json: Loaded from templates/config_templates/vehicle_templates/vehicle_types.json

    Returns:
        SUMO vClass string (space-separated, e.g., "passenger truck")
    """
    sumo_types = set()

    # Layer 1: Validate UI types exist in vehicle_types.json
    valid_categories = set()
    for vehicle_key, vehicle_config in vehicle_types_json.get("vehicle_types", {}).items():
        category = vehicle_config.get("category")
        if category:
            valid_categories.add(category)

    # Layer 2: Map UI types to SUMO vClass (extract category field)
    for ui_type in allowed_types:
        if ui_type not in valid_categories:
            raise ValueError(f"Vehicle type '{ui_type}' not found in vehicle_types.json categories")
        # Category IS the SUMO vClass
        sumo_types.add(ui_type)  # "passenger" maps to "passenger", etc.

    # Result: space-separated SUMO types for XML
    return " ".join(sorted(sumo_types)) if sumo_types else ""
```

### Validation Checkpoint

**During Parameter Validation** (control_strategy_service.py):
```python
def validate_dhs_parameters(parameters: Dict) -> ValidationResult:
    errors = []

    # Load vehicle_types.json for validation
    vehicle_types_json = load_json("templates/config_templates/vehicle_templates/vehicle_types.json")
    valid_categories = {v["category"] for v in vehicle_types_json["vehicle_types"].values()}

    # Validate each interval's vehicle types
    for interval in parameters.get("intervals", []):
        for vehicle_type in interval.get("allowed_vehicle_types", []):
            if vehicle_type not in valid_categories:
                errors.append(f"Vehicle type '{vehicle_type}' not in vehicle_types.json: {valid_categories}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

**During XML Generation** (additional_generator.py):
```python
def generate_dhs_xml(strategy_id: str, template: Dict, parameters: Dict) -> str:
    # Load vehicle_types.json for type mapping
    vehicle_types_json = load_json("templates/config_templates/vehicle_templates/vehicle_types.json")

    for interval in parameters.get("intervals", []):
        # Two-layer conversion
        sumo_allow = _map_vehicle_types_to_sumo(
            interval.get("allowed_vehicle_types", []),
            vehicle_types_json
        )

        # Add to XML
        closing_elem = SubElement(interval_elem, "closingLaneReroute")
        closing_elem.set("allow", sumo_allow)  # e.g., "passenger truck"
```

---

## Summary of Updates

### Files Modified

| File | Change | Lines |
|------|--------|-------|
| design.md | Added case metadata time handling + two-layer vehicle type mapping | +100 |
| tasks.md | Added critical tasks for time and vehicle type handling | +50 |
| spec.md | Added scenario for case metadata time + clarified vehicle type mapping | +30 |

### Key Clarifications

**Time Conversion**:
- ✅ Case metadata provides simulation start time: `case.time_range.start`
- ✅ Assumption: `time_hours` is ABSOLUTE (0-24), not relative to case start
- ⚠️ **Action Item**: Confirm with product team before implementation

**Vehicle Type Conversion**:
- ✅ **Layer 1**: Validate UI types exist in `vehicle_types.json` categories
- ✅ **Layer 2**: Map to SUMO vClass by extracting `.category` field
- ✅ All three types map cleanly:
  - "passenger" → vClass "passenger"
  - "truck" → vClass "truck"
  - "delivery" → vClass "delivery"

### Implementation Requirements

1. **Load case metadata**: `case.metadata.time_range.start` (extract hour)
2. **Load vehicle_types.json**: From `templates/config_templates/vehicle_templates/vehicle_types.json`
3. **Implement mapping function**: `_map_vehicle_types_to_sumo(allowed_types, vehicle_types_json)`
4. **Add validation**: Check vehicle types exist in vehicle_types.json at strategy creation time
5. **Add transformation**: Use mapping during XML generation
6. **Log decisions**: Document which assumption was chosen (absolute vs. relative time)

---

## Next Steps

1. **Clarify with product**: Is `time_hours` absolute or relative to case start?
2. **Update additional_generator.py**:
   - Load case metadata for time context
   - Load vehicle_types.json for type mapping
   - Implement two-layer vehicle type conversion
3. **Update parameter validation**:
   - Validate vehicle types against vehicle_types.json categories
   - Optionally validate time relative to case duration
4. **Add comprehensive tests**:
   - Test with real strategy instances
   - Test vehicle type mapping with different case start times
   - Test edge cases (empty vehicle types, invalid types, etc.)

---

**Validation Status**: ✅ Proposal still valid with these clarifications
**Next Action**: Schedule product team meeting to clarify time handling assumption
