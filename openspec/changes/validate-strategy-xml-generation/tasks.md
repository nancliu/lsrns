# Implementation Tasks: validate-strategy-xml-generation

**Status**: Ready for Implementation
**Priority**: P0 (Critical - blocks simulation reliability)
**Estimated Duration**: 2-3 weeks
**Dependency Order**: Sequential (some items can run in parallel after Phase 1)

---

## Phase 1: Validation Infrastructure (Week 1)

### 1.1 Create xml_validator Module
- [ ] 1.1.1 Create `shared/control_tools/xml_validator.py` file (skeleton with docstrings)
- [ ] 1.1.2 Implement `validate_sumo_xml()` function with:
  - Well-formedness check (ElementTree parse)
  - Root element validation (<additional>)
  - Child element type check (variableSpeedSign, rerouter, calibrator)
- [ ] 1.1.3 Implement `validate_variableSpeedSign()` helper:
  - Check required attributes: id, edges
  - Check each <step>: time (int 0-86400), speed (float, 2 decimals)
  - Return ValidationResult
- [ ] 1.1.4 Implement `validate_rerouter()` helper:
  - Check id, edges attributes
  - Check <interval>: begin/end integers
  - Check <closingLaneReroute>: id (int), allow (empty or space-separated types)
- [ ] 1.1.5 Implement `validate_calibrator()` helper:
  - Check id, edge, pos attributes
  - Check <flow>: begin/end (int), vehsPerHour (int), speed (float)
- [ ] 1.1.6 Add unit tests:
  - Test valid VSS/DHS/TEC XML (happy path)
  - Test malformed XML (invalid tags, missing attributes)
  - Test edge cases (empty intervals, zero values, boundary times)
  - Target coverage: >95%

### 1.2 Create ValidationResult Data Model
- [ ] 1.2.1 Create `api/models/control/responses/validation.py`
- [ ] 1.2.2 Define `ValidationResult` dataclass:
  - is_valid: bool
  - errors: List[str]
  - warnings: List[str]
  - details: Dict (optional)
- [ ] 1.2.3 Define `ValidationError` Pydantic model (for API responses):
  - field: str
  - message: str
  - type: str (validation|format|constraint)
- [ ] 1.2.4 Define `PlanCreationError` response schema
- [ ] 1.2.5 Add to `api/models/__init__.py` for export

### 1.3 Enhance Parameter Validation in control_strategy_service
- [ ] 1.3.1 Add imports and logger to `control_strategy_service.py`
- [ ] 1.3.2 Implement `validate_vss_parameters()`:
  - Speed range: 30-130 km/h
  - Time ordering: begin < end
  - Affected_edges: not empty
  - Return ValidationResult
- [ ] 1.3.3 Implement `validate_dhs_parameters()`:
  - Lane index: 0-10
  - Time ordering per interval
  - Intervals: begin < end
  - Allowed vehicle types: in {passenger, bus, truck, emergency}
- [ ] 1.3.4 Implement `validate_tec_parameters()`:
  - Vehicle types: valid enum
  - Flow rates: 0-3000 vehsPerHour
  - Speed: reasonable range (5-40 m/s)
  - Entrance edges: not empty
- [ ] 1.3.5 Create central `validate_parameters()` dispatcher:
  - Takes strategy_type and parameters dict
  - Calls appropriate validator
  - Returns ValidationResult
- [ ] 1.3.6 Add unit tests for all validators
  - Valid parameters (happy path)
  - Out-of-range values
  - Invalid types/enums
  - Missing required fields
  - Target coverage: >95%

### 1.4 Integrate XML Validation in Plan Creation
- [ ] 1.4.1 Update `control_plan_service.create_plan()`:
  - Call `validate_parameters()` for each strategy BEFORE XML generation
  - If validation fails, return error with details (don't create plan)
  - Log validation failures
- [ ] 1.4.2 Update `additional_generator.generate_plan_additional()`:
  - After XML generation, call `xml_validator.validate_sumo_xml()`
  - If invalid, raise ValueError with specific error
- [ ] 1.4.3 Update error handling in `control_plan_routes.py`:
  - Catch ValidationErrors and PlanCreationErrors
  - Return 400 Bad Request with ValidationError response
  - Include affected strategies in response
- [ ] 1.4.4 Add integration test:
  - Create plan with valid strategies → success
  - Create plan with invalid speed → 400 error with details
  - Create plan with malformed edge reference → 400 error
  - Target: 3+ test cases

### 1.5 Validate Parameter Transformation Layer
- [ ] 1.5.1 Create `tests/unit/test_parameter_transformation.py` to verify:
  - **VSS transformation**: time_hours×3600 → seconds, speed_kmh÷3.6 → m/s
  - **DHS transformation**: begin_hours×3600 → begin_seconds, end_hours×3600 → end_seconds
  - **TEC transformation**: flow intervals converted correctly
  - Precision maintained: speed rounded to 2 decimals
  - Type safety: no data loss during int conversion
  - Edge cases: boundary values (0, 24, 30, 130), precision edge cases
- [ ] 1.5.2 **CRITICAL: Case metadata time handling**
  - Load case metadata: `case.time_range.start` (e.g., "2025/09/01 08:00:00", UTC+8)
  - **Clarify assumption**: Is time_hours ABSOLUTE (0-24 clock time) or RELATIVE to case start?
  - Test both scenarios:
    - Absolute: time_hours=7 → 7×3600=25200 sec
    - Relative: time_hours=7, case_start_hour=8 → (7-8)×3600=-3600 sec (would be invalid)
  - **Action item**: Confirm with product team which interpretation is correct
  - Document in implementation code which assumption was chosen
- [ ] 1.5.3 **CRITICAL: Vehicle type TWO-LAYER conversion**
  - Load `vehicle_types.json` mapping:
    ```json
    {
      "passenger_small": {"category": "passenger", ...},
      "truck_large": {"category": "truck", ...},
      "special_small": {"category": "delivery", ...}
    }
    ```
  - Implement mapping function: `ui_type → vehicle_types.json → SUMO vClass`
    - "passenger" (UI) → lookup vehicle_types.json → extract .category → "passenger" (SUMO)
    - "truck" (UI) → lookup vehicle_types.json → extract .category → "truck" (SUMO)
    - "delivery" (UI) → lookup vehicle_types.json → extract .category → "delivery" (SUMO)
  - Test DHS transformation with vehicle types:
    - allowed_vehicle_types=["passenger", "truck"] → ["passenger", "truck"] (after lookup) → XML allow="passenger truck"
  - Test TEC validation: Only allow standard SUMO types from vehicle_types.json
- [ ] 1.5.4 Test each transformation with real strategy instances:
  - strategy_real_vss_g4202_001.json: Verify actual parameters transform correctly
  - strategy_real_dhs_g4202_001.json: Verify interval transformation + vehicle type mapping
  - strategy_real_tec_g5_001.json: Verify flow transformation
- [ ] 1.5.5 Verify transformation chain:
  - Source parameter (e.g., speed_kmh=100, allowed_vehicle_types=["passenger"])
  - → Validated (30≤100≤130, type in vehicle_types.json)
  - → Transformed (100÷3.6=27.78, lookup vehicle type in JSON)
  - → Placed in XML (<step speed="27.78"/>, <closingLaneReroute allow="passenger"/>)
  - Verify no intermediate step is skipped or incorrect
- [ ] 1.5.6 Add transformation validation to additional_generator.py:
  - Add case metadata loading: `case.time_range.start`
  - Add vehicle_types.json loading for type mapping
  - Add assertions after transformation (e.g., assert 0≤speed_ms≤50)
  - Add assertions for vehicle type mapping (assert all types resolved)
  - Log transformation results for debugging
  - Return detailed error if transformation yields out-of-bounds value
  - Log which vehicle_types.json entries were used for mapping

### 1.6 Create Test Suite for Phase 1
- [ ] 1.6.1 Create `tests/unit/test_xml_validator.py`
- [ ] 1.6.2 Create `tests/unit/test_parameter_validation.py`
- [ ] 1.6.3 Create `tests/unit/test_parameter_transformation.py` (from 1.5)
- [ ] 1.6.4 Create `tests/integration/test_plan_creation_validation.py`
- [ ] 1.6.5 Run all tests: `pytest tests/unit/test_*.py`
- [ ] 1.6.6 Check coverage: `pytest --cov=shared/control_tools/xml_validator`
- [ ] 1.6.7 Check coverage: `pytest --cov=shared/control_tools/additional_generator`
- [ ] 1.6.8 All tests passing with >95% coverage (including transformation tests)

---

## Phase 2: Cascade Regeneration (Week 2)

### 2.1 Enhance Strategy Reference Tracking
- [ ] 2.1.1 Review existing `strategy_file_manager.py` reference tracking
- [ ] 2.1.2 Ensure `strategy_refs.json` format:
  ```json
  {
    "strategy_id": "strategy_001",
    "referenced_by": ["plan_id_1", "plan_id_2"],
    "last_updated": "2025-11-02T10:30:00"
  }
  ```
- [ ] 2.1.3 Update `strategy_file_manager.update_strategy()`:
  - Maintain `referenced_by` list when strategies are updated
- [ ] 2.1.4 Create `_find_referencing_plans()` helper:
  - Query `strategy_refs.json` to find all plans using a strategy
  - Return List[str] of plan IDs

### 2.2 Implement Cascade Regeneration Logic
- [ ] 2.2.1 Add `_cascade_regenerate_plans()` method to `strategy_instance_service.py`:
  - Takes strategy_id as input
  - Finds all referencing plans (async)
  - For each plan: call `regenerate_plan_xml(plan_id)`
  - Log success/failure per plan
- [ ] 2.2.2 Update `update_strategy()` in `strategy_instance_service.py`:
  - After strategy update succeeds
  - Call `asyncio.create_task(self._cascade_regenerate_plans(strategy_id))`
  - Return immediately (don't wait for cascade)
  - Indicate cascade is "in_progress"
- [ ] 2.2.3 Create `regenerate_plan_xml()` in `control_plan_service.py`:
  - Load plan metadata and strategies
  - Call `generate_plan_additional()` again
  - Validate new XML
  - Write to file
  - Log result
- [ ] 2.2.4 Add error handling:
  - Cascade failures don't block strategy update
  - Log errors to audit trail
  - Provide manual regeneration endpoint

### 2.3 Add Manual Regeneration Endpoint
- [ ] 2.3.1 Add route to `control_plan_routes.py`:
  - POST `/api/v1/control/plans/{plan_id}/regenerate-xml`
  - Calls `control_plan_service.regenerate_plan_xml(plan_id)`
  - Returns 200 with regeneration result or 400 if validation fails
- [ ] 2.3.2 Add response model to `plan_response.py`:
  - plan_id, status, generated_at, validation_result
- [ ] 2.3.3 Document endpoint in code comments

### 2.4 Add Audit Logging for Cascade Events
- [ ] 2.4.1 Create audit log entry structure:
  - event_type: "strategy_updated" | "cascade_regeneration_started" | "plan_regenerated"
  - timestamp, strategy_id, plan_id, result, error_message
- [ ] 2.4.2 Log to file: `logs/cascade_audit.log`
- [ ] 2.4.3 Add audit entries in:
  - `update_strategy()` - log strategy update
  - `_cascade_regenerate_plans()` - log start/end
  - `regenerate_plan_xml()` - log each plan regeneration

### 2.5 Create Tests for Phase 2
- [ ] 2.5.1 Create `tests/integration/test_cascade_regeneration.py`
- [ ] 2.5.2 Test: Update strategy → all referencing plans regenerated
- [ ] 2.5.3 Test: Cascade failure → doesn't block update, logged
- [ ] 2.5.4 Test: Manual regeneration endpoint
- [ ] 2.5.5 Test: Multiple strategies in one plan (all regenerated)
- [ ] 2.5.6 All tests passing

---

## Phase 3: Documentation & Deployment (Week 2 End)

### 3.1 Update Specifications
- [ ] 3.1.1 Update `openspec/specs/plan-management/spec.md`:
  - Modify Requirement 2: Add SUMO validation requirements
  - Add new Requirement 3: Cascade regeneration on strategy update
  - Add scenarios for validation failures
- [ ] 3.1.2 Update `openspec/specs/strategy-templates/spec.md`:
  - Clarify XML attribute format constraints
  - Add unit conversion requirements (hours→seconds, km/h→m/s)
- [ ] 3.1.3 Create CHANGELOG entry: `docs/CHANGELOG.md`
  - Feature: SUMO XML validation
  - Feature: Cascade regeneration on strategy update
  - Bug fix: Prevent invalid XML generation

### 3.2 Update Documentation
- [ ] 3.2.1 Update CLAUDE.md:
  - Add SUMO XML validation best practices
  - Add parameter constraint reference
  - Add troubleshooting guide
- [ ] 3.2.2 Create `docs/design/sumo_xml_validation.md`:
  - Overview of validation layers
  - Parameter constraint reference table
  - XML format examples (VSS, DHS, TEC)
  - Troubleshooting guide

### 3.3 Create Migration Guide
- [ ] 3.3.1 Create `docs/migration/validate-strategy-xml-generation.md`:
  - Summary of changes
  - Backward compatibility notes
  - Action required for existing invalid strategies
- [ ] 3.3.2 Create validation script: `scripts/validate_existing_plans.py`
  - Scans all existing plans
  - Validates their XML
  - Reports issues
  - (Optional) Auto-fix if possible

### 3.4 Deployment Checklist
- [ ] 3.4.1 All unit tests passing: `pytest tests/unit/test_*validation*.py`
- [ ] 3.4.2 All integration tests passing: `pytest tests/integration/test_*validation*.py`
- [ ] 3.4.3 Code review: PR approved
- [ ] 3.4.4 Manual QA: Test creating/updating plans and strategies
- [ ] 3.4.5 Verify no existing plans are broken: Run validation script
- [ ] 3.4.6 API documentation updated: `/docs` endpoint reflects new responses

---

## Phase 4: Optional - Network Topology Validation (Future)

### 4.1 Edge Existence Check
- [ ] 4.1.1 Implement `_check_edges_exist()` in `control_strategy_service.py`
- [ ] 4.1.2 Query edge database: `from shared.data_access.edge_query import query_edges_base`
- [ ] 4.1.3 Add to parameter validation (optional flag)
- [ ] 4.1.4 Tests: Valid/invalid edge IDs

### 4.2 Lane Boundary Check
- [ ] 4.2.1 Get edge lane count from network
- [ ] 4.2.2 Validate lane index: 0 ≤ index < num_lanes
- [ ] 4.2.3 Tests: Valid/out-of-bounds lane indices

### 4.3 Hard Shoulder Continuity Check (DHS-specific)
- [ ] 4.3.1 Verify all edges in affected_edges are consecutive
- [ ] 4.3.2 Check hard shoulder lane exists on all edges
- [ ] 4.3.3 Tests: Continuous/discontinuous edge sequences

**Note**: Phase 4 can start after Phase 2 is stable. It requires network topology data and adds DB dependency to validation.

---

## Success Criteria

### Phase 1 Complete When:
- ✅ `xml_validator.py` created with all validators implemented
- ✅ All unit tests passing (>95% coverage)
- ✅ Parameter validation integrated into plan creation
- ✅ Invalid plans return 400 with clear error messages
- ✅ Existing valid plans unaffected

### Phase 2 Complete When:
- ✅ Cascade regeneration working for strategy updates
- ✅ All integration tests passing
- ✅ Manual regeneration endpoint working
- ✅ Audit logs tracking all events
- ✅ Performance acceptable (<200ms/plan)

### Phase 3 Complete When:
- ✅ Specs updated with validation requirements
- ✅ Documentation comprehensive and clear
- ✅ Migration guide provided
- ✅ Validation script provided
- ✅ Deployment checklist completed

---

## Risk Mitigation

**Risk**: Existing invalid plans break on update
**Mitigation**: Provide validation script to identify issues before deployment. Make validation non-blocking for reads.

**Risk**: Cascade regeneration causes performance spike
**Mitigation**: Use async tasks, batch updates, log slow operations.

**Risk**: Network validation adds DB dependency to validation
**Mitigation**: Make network validation optional (Phase 4), graceful degradation if DB unavailable.

**Risk**: Edge case - strategy deleted but plans reference it
**Mitigation**: Add cleanup logic in strategy deletion, or mark plan as "needs-update" status.

---

## Deliverables

- ✅ `shared/control_tools/xml_validator.py` (~200 lines)
- ✅ Enhanced `control_strategy_service.py` (~100 lines)
- ✅ Enhanced `control_plan_service.py` (~50 lines)
- ✅ Enhanced `strategy_instance_service.py` (~80 lines)
- ✅ API response models (`validation.py`)
- ✅ Unit tests (~400 lines)
- ✅ Integration tests (~300 lines)
- ✅ Documentation and migration guide
- ✅ Updated specs in openspec/

**Total Lines of Code**: ~1,500 (including tests)
**Test Coverage**: >95%
