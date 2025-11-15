# Quick Start Guide for Next Phases (4 & 5)

**Document Date**: 2025-11-15
**Current Phase Completed**: Phase 3 (Testing)
**Estimated Remaining Time**: 2-3 weeks

---

## Phase 4: Documentation (7 hours total) - READY TO START

### Task 4.1: Update API Documentation (2 hours)

**What to Do**:
1. Update `docs/api_docs/新架构API指南.md`
2. Document the endpoint: `POST /api/v1/scenario/create_case_with_simulation`
3. Show new response fields in examples

**New Response Fields to Document**:
- `is_new_case` (boolean) - Whether case was newly created or reused
- `case_type` (string) - "event_based" or "time_based"
- `od_generation_status` (string) - "in_progress", "completed", "failed", or "not_needed"
- `case_id` (string) - The case identifier
- `simulation_id` (string) - The simulation identifier

**Example Response (New Case)**:
```json
{
  "is_new_case": true,
  "case_type": "event_based",
  "case_id": "case_event_10814",
  "simulation_id": "event_simulation_scenario_10814_vss",
  "od_generation_status": "in_progress",
  "message": "Creating new event-based case for event 10814, OD generation started"
}
```

**Example Response (Reused Case)**:
```json
{
  "is_new_case": false,
  "case_type": "event_based",
  "case_id": "case_event_10814",
  "simulation_id": "event_simulation_scenario_10814_tec",
  "od_generation_status": "completed",
  "message": "Using existing case for event 10814, simulation created"
}
```

**Files to Update**:
- `docs/api_docs/新架构API指南.md` (main API docs)
- Any OpenAPI/Swagger specification files

**Acceptance Criteria**:
- [ ] New fields documented
- [ ] Examples provided
- [ ] Response schema shows all fields
- [ ] Behavior difference explained (new vs reused case)

---

### Task 4.2: Create Architecture Diagram (2 hours)

**What to Create**:
A visual diagram showing the event-based case architecture

**Diagram Content Required**:
1. **File Structure Comparison**
   - Before: Time-based cases (case_YYYYMMDD_HHMMSS)
   - After: Event-based cases (case_event_{event_id}) with multiple simulations

2. **Case/Simulation Relationship**
   ```
   Event #10814
   └── case_event_10814/
       ├── Scenario A (VSS) → Simulation A
       ├── Scenario B (TEC) → Simulation B
       └── Scenario C (DHS) → Simulation C
   ```

3. **File Distribution Across Levels**
   ```
   Case Level: network, TAZ, OD routes, edgeData template
   Simulation Level: scenario specific files, SUMO config
   Output Level: edgedata results, detector outputs
   ```

4. **Data Flow**
   ```
   Request → Check if case exists →
   If NO: Create case, copy config files, generate OD →
   Create simulation, generate sumocfg →
   Run SUMO simulation
   If YES: Validate config, create simulation, run SUMO
   ```

**Format Options**:
- Mermaid diagram (`.md` with code block)
- Draw.io diagram (export as PNG/SVG)
- ASCII diagram (in markdown)

**Output Location**: `openspec/changes/event-based-case-architecture/architecture-diagram.md`

**Acceptance Criteria**:
- [ ] Diagram created and included in documentation
- [ ] Clear and easy to understand
- [ ] Shows key architecture improvements
- [ ] File structure is clear

---

### Task 4.3: Write User Guide (3 hours)

**What to Write**:
User-facing documentation explaining new event-based case behavior

**Content to Include**:

1. **Overview Section**
   - What is event-based case architecture?
   - Why is it better than time-based?
   - When should you use it?

2. **Case Naming Convention**
   - Format: `case_event_{event_id}`
   - Examples: `case_event_10814`, `case_event_12547`
   - Automatic naming based on event ID

3. **Simulation Naming Convention**
   - Format: `event_simulation_scenario_{scenario_id}`
   - Examples: `event_simulation_scenario_10814_vss`
   - Shows scenario-to-case relationship

4. **Config Reuse Explanation**
   - First scenario creates the case with network, TAZ, OD data
   - Subsequent scenarios reuse these files
   - Why this is more efficient
   - Performance improvements (faster creation)

5. **OD Generation Behavior**
   - Runs once per event (not once per simulation)
   - Status returned in API response
   - How to check if generation is complete

6. **Simulation Independence**
   - Each simulation has its own scenario-specific files
   - Can be run independently or together
   - Output directories are separate

7. **Step-by-Step Examples**
   - Creating first scenario for an event
   - Creating second scenario for same event
   - Checking OD generation status
   - Running multiple simulations in parallel

8. **Troubleshooting**
   - What if OD generation fails?
   - What if config validation fails?
   - How to check if case was created correctly?

**Example Scenario to Document**:
```
Event 10814 Analysis with Multiple Control Strategies:

Step 1: Create VSS strategy simulation
  - Request: event_id=10814, scenario=scenario_10814_vss
  - Result: case_event_10814 created, OD generation started
  - Time: ~2 minutes (includes OD generation)

Step 2: Create TEC strategy simulation
  - Request: event_id=10814, scenario=scenario_10814_tec
  - Result: case_event_10814 reused, no OD regeneration
  - Time: ~30 seconds (much faster!)

Step 3: Create DHS strategy simulation
  - Request: event_id=10814, scenario=scenario_10814_dhs
  - Result: case_event_10814 reused again
  - Time: ~30 seconds

Result: 3 simulations with shared infrastructure, saved ~90 seconds
```

**Output Location**: User documentation directory (TBD - check project structure)

**Acceptance Criteria**:
- [ ] Clear explanation of event-based architecture
- [ ] Examples provided
- [ ] Screenshots/diagrams included (if applicable)
- [ ] Troubleshooting guide included

---

## Phase 5: Deployment & Monitoring (9 hours total) - PLAN AHEAD

### Task 5.1: Create Migration/Validation Script (4 hours)

**What to Create**:
A Python script that validates existing cases work with new code

**Script Functionality**:
1. Scan all existing cases in `cases/` directory
2. Detect case type (event-based vs time-based)
3. Validate config files present
4. Test metadata loading
5. Generate compatibility report

**Output**:
- Report showing which cases are compatible
- Any validation failures noted
- Summary: X cases checked, Y passed, Z failed

**Location**: `scripts/validate_case_compatibility.py`

**Acceptance Criteria**:
- [ ] Script runs without errors
- [ ] All existing cases validated
- [ ] No errors for time-based cases
- [ ] Report generated and readable

---

### Task 5.2: Add Performance Monitoring (3 hours)

**What to Implement**:
Metrics tracking for performance improvements

**Metrics to Track**:
1. **OD Generation Frequency**
   - Count: How many OD generations per event
   - Expected: 1 per event (not per simulation)

2. **Config Reuse Rate**
   - Count: How many times configs were reused vs created
   - Expected: Growing reuse rate as more simulations use same event

3. **Case Creation Time**
   - New case: ~2+ minutes (includes OD generation)
   - Reused case: ~30 seconds (much faster)
   - Track both averages

4. **Disk Usage**
   - Per event: Shared config files
   - Per simulation: Scenario-specific files
   - Shows space savings

**Implementation Location**: `api/services/case_service.py`

**Metrics Class Example**:
```python
class CaseServiceMetrics:
    def __init__(self):
        self.new_cases = 0
        self.reused_cases = 0
        self.od_generations = 0
        self.creation_times = []

    def record_case_creation(self, is_new: bool, duration: float):
        if is_new:
            self.new_cases += 1
            self.od_generations += 1
        else:
            self.reused_cases += 1
        self.creation_times.append(duration)

    def get_reuse_rate(self) -> float:
        total = self.new_cases + self.reused_cases
        if total == 0:
            return 0
        return (self.reused_cases / total) * 100
```

**Exposure**:
- Optional: Metrics API endpoint (e.g., `GET /api/v1/metrics/case-service`)
- Optional: Dashboard widget showing metrics

**Acceptance Criteria**:
- [ ] Metrics collected during operation
- [ ] Accessible via API endpoint or logs
- [ ] Shows expected improvements (reuse rate > 50%)

---

### Task 5.3: Create Rollback Plan (2 hours)

**What to Document**:
Detailed rollback procedure if issues arise

**Rollback Procedure**:
1. **Identify Issue**
   - Monitor for bugs, performance problems, data issues
   - Threshold: Blocking bug or >10% performance regression

2. **Stop New Event Cases**
   - Disable event-based case creation if needed
   - Switch back to time-based (existing endpoint)

3. **Revert Code**
   - Git revert to previous version
   - Or disable feature flag (if implemented)

4. **Verify Rollback**
   - Existing event-based cases still readable
   - Time-based cases unaffected
   - System stable

5. **Post-Mortem**
   - Analyze what went wrong
   - Plan fix
   - Test thoroughly

**Recovery Time Estimate**: 15-30 minutes

**Location**: `openspec/changes/event-based-case-architecture/ROLLBACK.md`

**Acceptance Criteria**:
- [ ] Rollback plan documented
- [ ] Steps are clear and actionable
- [ ] Recovery time minimized
- [ ] Team trained on procedure

---

## Quick Command Reference

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run only Phase 3 tests
pytest tests/unit/ tests/integration/ tests/e2e/ -v

# Run with coverage
pytest tests/ --cov=api --cov=shared --cov-report=html

# Run E2E tests
npx playwright test tests/e2e/
```

### Code Quality
```bash
# Check syntax
python -m py_compile api/services/case_service.py

# Format code
black api/ shared/ frontend/

# Lint code
flake8 api/ shared/
```

### Deployment Check
```bash
# Verify no circular dependencies
pydeps api/ --show-cycles

# Check reverse imports (should be empty)
grep -r "from api" shared/
```

---

## Key Files to Update for Phase 4

1. **API Docs**: `docs/api_docs/新架构API指南.md`
2. **Architecture**: New file `openspec/changes/event-based-case-architecture/architecture-diagram.md`
3. **User Guide**: Location TBD (check docs structure)
4. **Tasks MD**: Update `openspec/changes/event-based-case-architecture/tasks.md` to mark Phase 4 complete

---

## Key Files to Create for Phase 5

1. **Migration Script**: `scripts/validate_case_compatibility.py`
2. **Rollback Plan**: `openspec/changes/event-based-case-architecture/ROLLBACK.md`
3. **Metrics Code**: Update `api/services/case_service.py` to add metrics

---

## Estimated Timeline

### Phase 4 (Documentation) - READY NOW
- Task 4.1 (API Docs): 2 hours - **Can start immediately**
- Task 4.2 (Diagram): 2 hours - **Can start immediately**
- Task 4.3 (User Guide): 3 hours - **Can start immediately**
- **Total**: 7 hours (~1 day)

### Phase 5 (Deployment) - AFTER PHASE 4
- Task 5.1 (Migration): 4 hours - **Depends on Phase 4 completion**
- Task 5.2 (Monitoring): 3 hours - **Depends on Phase 4 completion**
- Task 5.3 (Rollback): 2 hours - **Can start anytime**
- **Total**: 9 hours (~1.5 days)

### Complete Project Timeline
- Phase 1-3 (Done): 2 weeks
- Phase 4 (Ready): 1 day
- Phase 5 (Ready): 1.5 days
- **Total Project**: ~2.5 weeks from start

---

## Success Criteria for Completion

### Phase 4 Success
- [ ] All API endpoints documented
- [ ] Architecture diagram created and clear
- [ ] User guide explains event-based approach
- [ ] No documentation TODOs remaining

### Phase 5 Success
- [ ] Migration script runs and generates report
- [ ] Metrics collected and accessible
- [ ] Rollback plan documented and team-ready
- [ ] System ready for production deployment

### Overall Success
- [ ] All 25 tasks (1-5) completed
- [ ] All documentation in place
- [ ] All monitoring and rollback systems ready
- [ ] Code passes all quality checks
- [ ] Team trained and ready for operation

---

## Current Completed Work Summary

✅ **Phase 1**: 8/8 tasks (100%)
✅ **Phase 2**: 6/6 tasks (100%)
✅ **Phase 3**: 5/5 tasks (100%) + 2 bug fixes
⏳ **Phase 4**: 0/3 tasks (0%) - READY TO START
⏳ **Phase 5**: 0/3 tasks (0%) - PLAN AHEAD

**Total Progress**: 19/25 tasks (76%)
**Remaining Effort**: ~7 hours documentation + 9 hours deployment = 16 hours

---

**Last Updated**: 2025-11-15
**Ready for Phase 4**: YES ✅
**Next Action**: Begin Phase 4 documentation tasks

