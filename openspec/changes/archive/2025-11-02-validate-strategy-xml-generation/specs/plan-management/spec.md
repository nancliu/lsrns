## MODIFIED Requirements

### Requirement: Plan XML Generation with SUMO Validation

The system SHALL automatically generate SUMO-compatible `control.add.xml` files when plans are created or updated, and SHALL validate all parameters and generated XML against SUMO v1.19+ requirements before persisting.

#### Scenario: Create plan with valid strategies

- **WHEN** user creates a plan with valid strategies (all parameters within SUMO constraints)
- **AND** all referenced edges exist in network topology
- **THEN** system validates parameters and generated XML
- **AND** generates well-formed `control.add.xml` file
- **AND** stores it at `control_data/plans/{plan_id}/control.add.xml`
- **AND** returns 201 Created with plan details including xml_validation_status: "valid"
- **AND** plan_metadata.json includes additional_file_path and xml_generated_at timestamp

#### Scenario: Create plan with invalid strategy parameters

- **WHEN** user creates plan with invalid parameters (e.g., speed 150 km/h exceeds maximum 130 km/h)
- **THEN** system validates parameters and detects constraint violation
- **AND** returns 400 Bad Request with validation error details:
  ```json
  {
    "error": "Plan creation failed",
    "reason": "Strategy parameter validation failed",
    "validation_errors": [
      {
        "field": "strategy_001.speed_steps[0].speed_kmh",
        "message": "Speed 150 km/h exceeds maximum 130 km/h",
        "type": "constraint"
      }
    ],
    "affected_strategies": ["strategy_001"]
  }
  ```
- **AND** plan is NOT created
- **AND** detailed error logged to audit trail

#### Scenario: Create plan with non-existent edge reference

- **WHEN** user creates plan with affected_edges referencing non-existent edge IDs
- **THEN** system performs optional network topology validation
- **AND** detects missing edges
- **AND** returns 400 Bad Request with validation error details
- **AND** provides suggestion: "Verify edge IDs in network or use /api/v1/control/edges/search endpoint"
- **AND** plan is NOT created

#### Scenario: XML validation fails (internal error)

- **WHEN** generated XML is malformed or violates SUMO schema
- **THEN** system detects validation failure in xml_validator
- **AND** returns 500 Internal Server Error with debug details
- **AND** logs critical error with full XML content for investigation
- **AND** plan is NOT created
- **NOTE**: This should be extremely rare if parameter validation is correct

#### Scenario: Update plan strategies

- **WHEN** user updates plan's strategy list (add/remove/modify strategies)
- **THEN** system validates all strategies as if creating new plan
- **AND** regenerates `control.add.xml` if validation passes
- **AND** updates plan_metadata.json with new xml_generated_at
- **AND** returns 200 OK with updated plan
- **AND** triggers cascade regeneration if strategy parameters changed (Requirement 3)

---

## ADDED Requirements

### Requirement: Cascade XML Regeneration on Strategy Update

When a strategy is updated, the system SHALL automatically regenerate `control.add.xml` files for all plans that reference that strategy, ensuring consistency across all plans using the modified strategy.

#### Scenario: Update strategy parameters

- **WHEN** user updates a strategy's parameters (e.g., change speed steps)
- **AND** strategy update validation succeeds
- **THEN** system immediately returns 200 OK with update confirmation
- **AND** triggers async background task to find all plans referencing this strategy
- **AND** response includes cascade_status: "in_progress"
- **AND** does NOT block strategy update on cascade regeneration

#### Scenario: Cascade regeneration succeeds for all referencing plans

- **WHEN** background cascade task executes
- **AND** all referencing plans' XMLs are regenerated successfully
- **THEN** system logs success for each plan:
  - Log entry: "Plan {plan_id} XML regenerated (strategy {strategy_id} updated)"
  - Include: regeneration_time_ms, xml_validation_result
- **AND** audit trail records event with timestamp and result
- **AND** plan's plan_metadata.json updated with new xml_generated_at

#### Scenario: Cascade regeneration partially fails

- **WHEN** background cascade task executes
- **AND** some plans' XMLs fail regeneration (e.g., due to network error)
- **THEN** system logs failure for affected plans:
  - Log entry: "Plan {plan_id} XML regeneration failed: {error}"
  - Level: ERROR (not critical, manual regeneration available)
- **AND** successful plans' XMLs updated normally
- **AND** user can manually regenerate failed plans via endpoint
- **AND** strategy update itself is considered successful

#### Scenario: Manual XML regeneration

- **WHEN** user calls POST `/api/v1/control/plans/{plan_id}/regenerate-xml`
- **THEN** system regenerates plan's `control.add.xml`
- **AND** validates new XML
- **AND** returns 200 OK with:
  ```json
  {
    "plan_id": "plan_001",
    "status": "regenerated",
    "generated_at": "2025-11-02T10:30:00",
    "validation_result": {
      "is_valid": true,
      "errors": [],
      "warnings": []
    }
  }
  ```
- **OR** returns 400 Bad Request if validation fails with error details

#### Scenario: Strategy referenced by multiple plans

- **WHEN** strategy is updated
- **AND** 5+ plans reference this strategy
- **THEN** system finds all 5 plans (reference tracking)
- **AND** regenerates XML for each concurrently (async, up to 10 parallel)
- **AND** logs success/failure for each independently
- **AND** average regeneration time < 200ms per plan
- **AND** strategy update response returned within 500ms (doesn't wait for all cascade)

---

## REMOVED Requirements

None. All existing requirements remain.

---

---

## ADDED Requirements (Part 2)

### Requirement: Parameter Transformation Validation

The system SHALL validate parameter transformations from strategy instance display units to SUMO XML units, ensuring data integrity and correctness throughout the conversion pipeline.

#### Scenario: VSS parameter transformation

- **WHEN** strategy parameters contain speed_steps with time_hours and speed_kmh
- **THEN** system validates source parameters are in correct range
- **AND** transforms time_hours to seconds (×3600)
- **AND** transforms speed_kmh to m/s (÷3.6, rounded to 2 decimals)
- **AND** verifies transformed values are within SUMO constraints (seconds [0-86400], m/s [0-50])
- **AND** places transformed values in XML as `<step time="25200" speed="27.78"/>`
- **Example**: time_hours=7, speed_kmh=100 → time="25200", speed="27.78" (✓ correct)
- **Counter-example**: time_hours=7, speed_kmh=150 → rejected (150 > 130 max)

#### Scenario: DHS parameter transformation with vehicle types (TWO-LAYER)

- **WHEN** strategy parameters contain intervals with begin_hours, end_hours, allowed_vehicle_types
- **THEN** system validates:
  - time values in range [0, 24] hours
  - intervals don't overlap and cover complete 24 hours
  - vehicle types are valid SUMO enum (passenger, truck, delivery - from vehicle_types.json categories)
- **AND** transforms hours to seconds (×3600)
- **AND** performs TWO-LAYER vehicle type conversion:
  - **Layer 1**: Validate UI types exist in vehicle_types.json (`allowed_vehicle_types` in strategy instance)
  - **Layer 2**: Map to SUMO vClass by extracting category field from vehicle_types.json
    - "passenger" (UI) → extract "passenger_small".category → "passenger" (SUMO vClass)
    - "truck" (UI) → extract "truck_large".category → "truck" (SUMO vClass)
    - "delivery" (UI) → extract "special_small".category → "delivery" (SUMO vClass)
- **AND** maps converted vehicle types to XML `allow` attribute (space-separated)
- **AND** places in XML as `<interval begin="25200" end="36000"><closingLaneReroute id="0" allow="passenger truck"/></interval>`
- **AND** handles empty allowed_vehicle_types as fully closed (allow="")
- **Example**: allowed_vehicle_types=["passenger", "truck"] → vehicle_types.json lookup → ["passenger", "truck"] → XML allow="passenger truck"

#### Scenario: Transformation precision and data loss prevention

- **WHEN** parameters are transformed from display units to SUMO units
- **THEN** system ensures:
  - Speed precision: 100 km/h → 27.78 m/s (NOT 27.7 or 28, must be 2 decimals)
  - No truncation of time values: 7 hours → exactly 25200 seconds (not 25199 or 25201)
  - Type conversion safe: integer result has no data loss
  - Transformed value within SUMO bounds (m/s: [0-50], seconds: [0-86400])
- **AND** logs transformation details for debugging (source value, conversion formula, result)
- **Example**: speed_kmh=50 → speed_ms=13.89 (NOT 13.8 or 13.9)

#### Scenario: Transformation validation fails

- **WHEN** transformation produces out-of-bounds value
- **EXAMPLE**: speed_kmh parameter itself is valid (within 30-130), but after ÷3.6 would be >50 m/s (theoretical edge case)
- **THEN** system returns 500 Internal Server Error (indicates logic bug)
- **AND** logs critical error with transformation details
- **AND** includes source value, formula applied, result value in error message
- **NOTE**: This should be extremely rare if parameter validation is correct; indicates bug in conversion logic

#### Scenario: Time conversion uses case metadata simulation start time

- **WHEN** converting strategy time_hours to SUMO seconds for a plan's case
- **THEN** system retrieves case metadata: `case.time_range.start` (UTC+8 timestamp, e.g., "2025/09/01 08:00:00")
- **AND** determines if strategy time_hours is:
  - **Absolute** (clock time, 0-24): Use directly → time_hours × 3600 = seconds (from midnight)
  - **Relative** (offset from case start): Adjust by case_start_hour before conversion
- **AND** validates time after conversion is within SUMO bounds [0-86400] seconds
- **ASSUMPTION**: Current system stores time_hours as ABSOLUTE (0-24 clock time, not relative to case start)
- **IMPLEMENTATION NOTE**: Confirm with product team if times should ever be relative to case start time
- **Example**: Case starts at "2025/09/01 08:00:00" (start_hour=8)
  - Strategy with time_hours=7 (absolute) → 7 × 3600 = 25200 sec ✓
  - NOT: 28800 + (7-8)*3600 = 25200 (this only works if converting from absolute to relative-adjusted)

#### Scenario: Strategy template defines transformation rules

- **WHEN** strategy template provides conversion factors and units in parameters_schema
- **THEN** system uses template-defined transformation rules (not hardcoded)
- **EXAMPLE**:
  ```json
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
  ```
- **AND** applies conversion_factor: value_km/h × 0.277778 = value_m/s
- **AND** validates transformation rules are consistent across all parameter types

---

## CLARIFICATIONS (Non-Normative)

### SUMO XML Format Requirements

**VSS (Variable Speed Sign) Element**:
```xml
<variableSpeedSign id="strategy_id" edges="edge1 edge2 ...">
    <step time="0" speed="27.78"/>
    <step time="25200" speed="22.22"/>
</variableSpeedSign>
```
- Time: Integer seconds [0, 86400]
- Speed: Float m/s, 2 decimal places [0.0, 50.0]
- Edges: Space-separated edge IDs that must exist in network

**DHS (Dynamic Hard Shoulder) Element**:
```xml
<rerouter id="strategy_id" edges="edge1 edge2 ...">
    <interval begin="0" end="25200">
        <closingLaneReroute id="3" allow="passenger bus truck emergency"/>
    </interval>
</rerouter>
```
- Lane ID: Integer index (0=rightmost, typically 3=hard shoulder on 4-lane)
- Allow: Space-separated vehicle types or empty string (fully closed)
- Valid types: passenger, bus, truck, emergency (SUMO standard enum)

**TEC (Toll Entrance Control) Element**:
```xml
<calibrator id="strategy_id" edge="entrance_edge" pos="0">
    <flow begin="0" end="25200" vehsPerHour="480" speed="15.0"/>
</calibrator>
```
- vehsPerHour: Integer [0, 3000]
- Speed: Float m/s [0.0, 50.0]

### Parameter Constraint Reference

| Parameter | Type | Range | SUMO Unit | UI Unit | Note |
|-----------|------|-------|-----------|---------|------|
| time_hours | float | [0, 24] | seconds (×3600) | hours | Beginning time of interval |
| speed_kmh | float | [30, 130] | m/s (÷3.6) | km/h | Speed limit for VSS |
| vehsPerHour | int | [0, 3000] | - | vehicles/hour | Flow rate for TEC |
| lane_index | int | [0, 10] | - | - | Hard shoulder lane (typically 3 for 4-lane) |
| affected_edges | List[str] | ≥1 item | - | - | Must exist in network |

### Best Practices

1. **Always validate parameters before creating/updating plans**
   - Use POST `/api/v1/control/strategies/validate-params` endpoint
   - Check response for errors before proceeding

2. **Check XML preview before saving**
   - Use GET `/api/v1/control/plans/{plan_id}/preview` to review generated XML
   - Verify elements are well-formed and attributes correct

3. **Monitor cascade regeneration**
   - Check audit logs for cascade events: `/logs/cascade_audit.log`
   - Verify all referencing plans regenerated after strategy update

4. **Handle validation errors gracefully**
   - Read validation_errors array for specific issues
   - Use error.type field to categorize (constraint|format|validation)
   - Adjust parameters and retry

---

**Specification Version**: 2.0
**Last Updated**: 2025-11-02
**Status**: Active
