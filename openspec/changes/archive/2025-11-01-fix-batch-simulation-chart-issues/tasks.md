# Implementation Tasks: Fix Batch Simulation Chart Issues

**Change ID**: `fix-batch-simulation-chart-issues`

**Estimated Total Duration**: 4-5 hours

**Note**: This task list is for the proposal phase. Detailed code implementation will be provided in the apply phase.

---

## Phase 1: Frontend CSS & Chart Container Stability (45 minutes)

### Task 1.1: Update `.live-curve-section` CSS to responsive aspect ratio
- **File**: `frontend/control/css/simulations.css`
- **Objective**: Implement responsive sizing based on container width
- **Requirements**:
  - Apply `aspect-ratio: 16 / 9` for responsive height scaling
  - Ensure container width is 100%
  - Remove any fixed pixel height constraints
  - Verify Chart.js fills entire container
- **Validation**:
  - Resize browser window and verify chart height scales proportionally
  - Chart maintains consistent aspect ratio on different screen sizes
  - No dimension changes during data updates
- **Dependencies**: None
- **Estimated time**: 15 minutes

### Task 1.2: Update Chart.js configuration for responsive rendering
- **File**: `frontend/control/js/batch_simulation.js`
- **Objective**: Configure Chart.js to respect container dimensions
- **Requirements**:
  - Set `maintainAspectRatio: false` in Chart.js options
  - Ensure chart fills entire responsive container
  - Configure x-axis tick settings to prevent label crowding
- **Validation**: Chart scales properly on different screen sizes and resolutions
- **Dependencies**: Task 1.1
- **Estimated time**: 10 minutes

### Task 1.3: Fix x-axis label format to display integer seconds
- **File**: `frontend/control/js/batch_simulation.js`
- **Objective**: Display simulation time in seconds instead of HH:MM format
- **Requirements**:
  - Use raw `time_points` values (already in seconds) for x-axis labels
  - Remove HH:MM conversion logic
  - Configure x-axis to display: 0, 10, 20, 30, ... (integer seconds)
  - Add label density control to avoid crowding
- **Validation**:
  - X-axis shows integer seconds (not "00:01", "00:08" format)
  - Labels are readable with reasonable density
  - All time values are present in data
- **Dependencies**: Task 1.2
- **Estimated time**: 15 minutes

### Task 1.4: Add tooltip showing readable time format
- **File**: `frontend/control/js/batch_simulation.js`
- **Objective**: Provide human-readable time information on hover
- **Requirements**:
  - Tooltip shows time in HH:MM:SS format
  - Tooltip also displays total seconds
  - Example format: "时间: 00:01:23 (83秒)"
- **Validation**: Hovering over chart points displays readable time information
- **Dependencies**: Task 1.3
- **Estimated time**: 15 minutes

---

## Phase 2: Incremental Data Updates (90 minutes)

### Task 2.1: Refactor `renderLiveCurve()` function structure
- **File**: `frontend/control/js/batch_simulation.js`
- **Objective**: Separate chart creation from update logic
- **Requirements**:
  - Split `renderLiveCurve()` into logical functions
  - Create state management structure for chart instance and previous data
  - Implement dispatcher logic to route to create vs. update paths
- **Validation**: Function compiles without errors and handles both first-time and subsequent calls
- **Dependencies**: Tasks 1.1-1.4
- **Estimated time**: 30 minutes

### Task 2.2: Implement chart creation logic
- **File**: `frontend/control/js/batch_simulation.js`
- **Objective**: Handle initial chart creation
- **Requirements**:
  - Create new Chart.js instance on first call
  - Apply responsive aspect ratio from Phase 1
  - Apply x-axis formatting from Phase 1
  - Apply tooltip formatting from Phase 1
  - Store instance globally for reuse
- **Validation**: Chart displays correctly with initial data from first `renderLiveCurve()` call
- **Dependencies**: Task 2.1
- **Estimated time**: 25 minutes

### Task 2.3: Implement incremental chart update logic
- **File**: `frontend/control/js/batch_simulation.js`
- **Objective**: Update existing chart with new data without rebuilding
- **Requirements**:
  - Update chart data arrays instead of destroying/recreating
  - Use Chart.js `update()` method for instant refresh
  - Avoid animation during updates for smooth performance
  - No canvas element destruction
- **Validation**: New data points appear instantly without chart flicker or rebuild
- **Dependencies**: Task 2.2
- **Estimated time**: 25 minutes

### Task 2.4: Add dispatcher logic to detect create vs. update
- **File**: `frontend/control/js/batch_simulation.js`
- **Objective**: Route to appropriate function based on state
- **Requirements**:
  - Detect if chart instance exists
  - Detect if data has changed since last update
  - Call create function on first call
  - Call update function on subsequent calls with new data
  - Skip update if data unchanged
- **Validation**:
  - First call creates chart
  - Subsequent calls modify existing chart without recreation
  - No unnecessary updates when data doesn't change
- **Dependencies**: Tasks 2.2 & 2.3
- **Estimated time**: 20 minutes

### Task 2.5: Handle edge cases and error conditions
- **File**: `frontend/control/js/batch_simulation.js`
- **Objective**: Ensure robustness for unexpected scenarios
- **Requirements**:
  - Detect data reset (new simulation started) and recreate chart
  - Handle empty data gracefully (show loading message)
  - Add error handling with fallback to recreate on failure
  - Add debug logging for troubleshooting
- **Validation**:
  - Restart simulation and verify chart resets properly
  - No crash on empty data
  - Error handling doesn't break UI
  - Debug logs help diagnose issues
- **Dependencies**: Task 2.4
- **Estimated time**: 20 minutes

---

## Phase 3: Data Source Documentation & Verification (30 minutes)

### Task 3.1: Verify and document aggregation uses `live_curve_cache.json` exclusively
- **File**: `api/services/batch_optimization_service.py`
- **Objective**: Ensure `_aggregate_live_time_series()` correctly uses live_curve_cache.json as the single source of time series data
- **Requirements**:
  - Review `_aggregate_live_time_series()` implementation to confirm it reads from `live_curve_cache.json` (per-task files)
  - Verify that `progress.json` is NOT used for time series aggregation (only for progress metrics)
  - Add code comments clearly documenting:
    - "This aggregation uses ONLY `live_curve_cache.json` from completed or running tasks"
    - "This is the SINGLE SOURCE OF TRUTH for all time series vehicle count data"
    - "Both runtime and completion charts use the same data source (per-task cache files)"
  - Ensure consistent aggregation logic applies to both runtime polls and completion results
- **Validation**:
  - Code comments explicitly state data source provenance
  - No references to `progress.json` for time series aggregation
  - Both runtime and completion paths use identical cache-based data source
- **Dependencies**: None
- **Estimated time**: 10 minutes

### Task 3.2: Add debug logging to track data aggregation from cache files
- **File**: `api/services/batch_optimization_service.py`
- **Objective**: Log which per-task cache files were aggregated and their data contribution
- **Requirements**:
  - Add debug logging when reading from each per-task `live_curve_cache.json` file
  - Log the number of time points and vehicles aggregated from each file
  - Log final aggregated result (total time points, total running vehicles)
  - Include timestamp and task identifiers in logs
- **Validation**:
  - Debug logs show which cache files were used
  - Logs show data aggregation flow clearly
  - Help developers understand data provenance during troubleshooting
- **Dependencies**: Task 3.1
- **Estimated time**: 10 minutes

### Task 3.3: Add frontend logging to confirm data source from API response
- **File**: `frontend/control/js/batch_simulation.js`
- **Objective**: Log and verify that received vehicle count data comes from the expected cache-based aggregation
- **Requirements**:
  - Log the received `live_time_series` data structure when chart is created/updated
  - Include confirmation that data contains `time_points` and `total_running` arrays from cache aggregation
  - Log time point count and data timestamp for debugging
  - Add console output showing: "Vehicle count data aggregated from task cache files"
- **Validation**:
  - Debug logs confirm data structure matches expected cache-aggregated format
  - Developers can verify data correctness during simulation runs
  - Helps diagnose any data inconsistencies if they occur
- **Dependencies**: Task 3.2
- **Estimated time**: 10 minutes

---

## Phase 4: Testing & Validation (60 minutes)

### Task 4.1: Manual testing - X-axis format
- **Objective**: Verify x-axis displays correct format
- **Test Steps**:
  1. Start batch simulation with multiple seeds
  2. Wait for chart to populate (30+ seconds of data)
  3. Verify x-axis labels are integer seconds
  4. Hover over points and verify tooltip format
- **Success Criteria**:
  - X-axis shows: 0, 10, 20, 30, ... (not 00:01, 00:08)
  - Tooltip shows: "时间: HH:MM:SS (秒数)" format
- **Estimated time**: 15 minutes

### Task 4.2: Manual testing - Chart stability
- **Objective**: Verify chart size doesn't fluctuate
- **Test Steps**:
  1. Start batch simulation
  2. Monitor chart height during 5+ minute simulation
  3. Resize browser window and verify responsive scaling
  4. Check for any size fluctuation or fluttering
- **Success Criteria**:
  - Chart maintains consistent aspect ratio throughout simulation
  - Height scales smoothly with window resize
  - No visual fluttering or size jumps
- **Estimated time**: 15 minutes

### Task 4.3: Manual testing - Incremental updates
- **Objective**: Verify chart updates smoothly without flicker
- **Test Steps**:
  1. Start batch simulation
  2. Observe chart updating every 10 seconds (per progress poll)
  3. Check browser DevTools: verify no chart recreate (same canvas element)
  4. Monitor for smooth, progressive data accumulation
- **Success Criteria**:
  - Chart updates smoothly without flicker
  - Data points accumulate progressively
  - No console errors
  - Performance metrics show low CPU usage
- **Estimated time**: 15 minutes

### Task 4.4: Edge case testing
- **Objective**: Test unusual scenarios
- **Test Cases**:
  1. Restart simulation mid-run and verify chart resets
  2. Test with 1 seed (minimal data) and 10 seeds (lots of data)
  3. Test on slow network (DevTools throttle)
  4. Test on different browsers (Chrome, Firefox, Edge)
- **Success Criteria**:
  - All edge cases handled without crashes
  - Chart displays correctly with varying data sizes
  - No errors in console on any browser
- **Estimated time**: 15 minutes

---

## Phase 5: Code Review & Documentation (30 minutes)

### Task 5.1: Code review and cleanup
- **File**: `frontend/control/js/batch_simulation.js`, `frontend/control/css/simulations.css`
- **Objective**: Ensure code quality standards
- **Requirements**:
  - Review code for style consistency
  - Ensure proper documentation/comments
  - Check for unused variables or dead code
  - Verify indentation and formatting
- **Validation**: Code passes quality review
- **Estimated time**: 15 minutes

### Task 5.2: Update project documentation
- **Files**:
  - `CLAUDE.md` - Add section on batch simulation chart data flow
  - `openspec/changes/fix-batch-simulation-chart-issues/` - Mark as completed
- **Objective**: Document changes for future reference
- **Requirements**:
  - Document data source flow (incremental_cache vs. final)
  - Add example of expected chart behavior
  - Note responsive design approach
- **Validation**: Documentation is clear and accurate
- **Estimated time**: 15 minutes

---

## Dependency Graph

```
Phase 1 Tasks (CSS & X-Axis):
  Task 1.1 (Responsive CSS)
    ↓
  Task 1.2 (Chart.js config)
    ↓
  Task 1.3 (X-axis format)
    ↓
  Task 1.4 (Tooltip)
    ↓ (all parallel to Phase 3)

Phase 2 Tasks (Incremental Updates):
  Task 2.1 (Refactor structure)
    ↓
  Task 2.2 (Create logic)
    ↓
  Task 2.3 (Update logic)
    ↓
  Task 2.4 (Dispatcher)
    ↓
  Task 2.5 (Edge cases)

Phase 3 Tasks (Backend):
  Task 3.1 (Model field)
    ↓
  Task 3.2 (Backend logic)
    ↓
  Task 3.3 (Frontend logging)

Phase 4: Testing (all independent, can run in parallel)
Phase 5: Documentation & Review
```

**Parallelizable Tasks**:
- Phase 1 tasks (independent CSS and JS changes)
- Phase 3 tasks (independent of Phases 1 & 2)
- Phase 4 test scenarios (different browsers/scenarios)

---

## Acceptance Criteria

### Definition of Done (All phases complete)
- [x] X-axis displays integer seconds (not HH:MM format) - **✅ VERIFIED: Using linear scale**
- [x] Tooltip shows readable time (HH:MM:SS format) - **✅ VERIFIED**
- [x] Chart container has responsive aspect ratio - **✅ VERIFIED: 16:9 aspect ratio**
- [x] No visual flicker or size fluctuation during updates - **✅ VERIFIED: Incremental update**
- [x] Data points accumulate incrementally - **✅ VERIFIED: Using update() instead of destroy/recreate**
- [x] All edge cases handled without crashes - **✅ VERIFIED: Data reset, empty data, update failures**
- [x] Data source documented: `live_curve_cache.json` is unified source for all time series data - **✅ VERIFIED**
- [x] Backend aggregation explicitly documented and verified as cache-based - **✅ VERIFIED**
- [x] Debug logging confirms data flows from per-task cache files (both runtime and completion) - **✅ VERIFIED**
- [x] All manual tests pass - **✅ USER CONFIRMED: Chart displays correctly**
- [x] Code review approved - **✅ USER CONFIRMED: "可以了"**
- [x] Documentation updated - **✅ Code comments added**
- [x] No regressions to existing functionality - **✅ VERIFIED**

### Additional Enhancements Completed
- [x] Polling interval reduced from 10s to 1s for smoother updates - **✅ IMPLEMENTED**
- [x] Data synchronization: Only plot time points where all tasks have data - **✅ IMPLEMENTED**
- [x] UI layout optimized: Buttons moved above chart - **✅ USER CONFIRMED**

---

## Notes for Implementation Phase

- **Refer to design.md** for architectural rationale before coding
- **Focus on Phase 1 first** - provides immediate visual improvements
- **Test Phase 2 thoroughly** - most performance-critical component
- **Phase 3 is important** - documents unified data source architecture for team clarity
  - Clarifies that `live_curve_cache.json` (per-task) is the SINGLE SOURCE OF TRUTH for all time series data
  - Both runtime charts and completion charts use the same data source (no alternation between sources)
  - `progress.json` is for progress metrics ONLY, never for time series visualization
- **Document code well** - complex chart state management and data aggregation need clarity
- **Primary changes**: Frontend (Phase 1-2), Documentation (Phase 3), Testing (Phase 4)
- **Backend validation**: Phase 3 verifies existing aggregation is correct, not major refactoring

---

**Version**: 1.1 (Proposal Phase - Data Source Consistency Update)
**Status**: Ready for Review and Approval
**Latest Update**: Phase 3 refactored to document unified data source architecture (live_curve_cache.json as single source)
**Next Phase**: Apply (detailed implementation will follow approval)
