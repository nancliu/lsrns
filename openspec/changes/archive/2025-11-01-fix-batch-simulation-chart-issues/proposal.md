# OpenSpec Proposal: Fix Batch Simulation Vehicle Count Chart Issues

**ID**: `fix-batch-simulation-chart-issues`

**Status**: Proposed

**Priority**: High

**Created**: 2025-11-02

---

## Executive Summary

The batch simulation vehicle count chart in the progress monitoring view has three critical issues:

1. **Incorrect X-axis format**: Showing time in `HH:MM` format (e.g., "00:01") instead of seconds (integers like 1, 60, 120)
2. **Chart size fluctuating**: Chart dimensions change as data points are added, causing visual instability
3. **Incomplete data accumulation**: Chart is rebuilt from scratch on each progress update instead of incrementally adding new data points

**Data Source Clarification**: Live time series data comes exclusively from `live_curve_cache.json` (per-task) both during runtime and after completion. `progress.json` contains only summary metrics (progress %, task counts), never time series data.

---

## Problem Statement

### Issue 1: X-Axis Shows Time in Wrong Format

**Current behavior**:
- X-axis labels: `00:01`, `00:08`, `00:09`, `00:09`, `00:09`, ...
- Uses `HH:MM` (hours:minutes) format
- Does not show seconds precision

**Expected behavior**:
- X-axis labels: `0`, `60`, `120`, `180`, `240`, ...
- Uses **integer seconds** format
- Matches the `time_points` array in the API response

**Root cause**:
In `batch_simulation.js:616-620`, time points are converted from seconds to `HH:MM` format for display:
```javascript
const timeLabels = liveTimeSeries.time_points.map(t => {
    const hours = Math.floor(t / 3600);
    const minutes = Math.floor((t % 3600) / 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
});
```

This loses seconds and makes the axis unclear for simulation viewers.

---

### Issue 2: Chart Size Fluctuates During Updates

**Current behavior**:
- Chart height changes as new data points are added
- Chart appears to "shrink" or "grow" with each update
- Visual instability disrupts user monitoring

**Expected behavior**:
- Chart maintains consistent aspect ratio throughout simulation
- Responsive scaling: height automatically adjusts based on container width
- Stable visual size that doesn't change during data updates

**Root cause**:
- `.live-curve-chart` has `max-height: 300px` but no fixed aspect ratio
- Chart is destroyed and recreated on each `renderLiveCurve()` call (line 623-625)
- Canvas dimensions change based on data point count instead of maintaining aspect ratio

---

### Issue 3: Chart Data Rebuilt from Scratch on Each Update

**Current behavior**:
- Each progress poll (every 10 seconds) completely rebuilds the chart
- Old data points are lost if chart rendering fails
- No incremental data accumulation

**Expected behavior**:
- Each update adds only new data points to the chart
- Existing data points remain stable
- Full historical data visible once simulation completes

**Data Source Consistency**:
- **During runtime**: Data from `live_curve_cache.json` (per-task cache files)
- **After completion**: Data from same `live_curve_cache.json` cache files (final aggregated state)
- **Unified approach**: Both runtime and completion charts use identical data source (per-task cache files)

---

## Proposed Solution

### Capability 1: Fix X-Axis Label Format to Display Seconds

Replace time-to-HH:MM conversion with direct integer seconds display. Keep tooltip showing time in readable format.

**Changes**:
- Use raw `time_points` values (already in seconds) for x-axis labels
- Add tooltip to show readable time format (`HH:MM:SS`) on hover
- Add x-axis step configuration to avoid label crowding

---

### Capability 2: Stabilize Chart Container Dimensions

Fix the chart container to have explicit, stable dimensions that don't change during data updates.

**Changes**:
- Set fixed height on `.live-curve-chart` (e.g., 300px)
- Add `maintainAspectRatio: false` to Chart.js options
- Ensure `.live-curve-section` has padding that doesn't collapse

---

### Capability 3: Implement Incremental Data Point Addition

Instead of rebuilding the chart from scratch, add new points incrementally and update chart data.

**Changes**:
- Store previous chart state in global variable
- Detect new data points compared to previous state
- Use Chart.js `update()` method to add points instead of destroy/recreate
- Handle edge cases (data resets, simulation restart)

---

### Capability 4: Clarify Data Source for Chart Updates

Document that all in-network vehicle count data (both during runtime and after completion) comes exclusively from `live_curve_cache.json` per-task files.

**Changes**:
- Document that `live_curve_cache.json` is the ONLY source of time series simulation data
- `progress.json` contains only summary metrics, NO time series data
- Both runtime and completed charts aggregate from same per-task cache files
- Add logging to track data aggregation for debugging

---

## Architecture & Design

### Data Flow

**Both During Runtime AND After Completion** (Same Data Source):
```
summary.xml (per task)
    ↓
live_curve_cache.json (per task) ← _read_or_update_cache()
    ↓                                (incremental updates during run)
    ├─ Runtime: BatchProgressResponse.live_time_series
    │           ↓
    │       renderLiveCurve() [Chart.js update]
    │
    └─ Completion: Same cache files contain final data
                   ↓
                BatchResultsResponse
                   ↓
                renderPeakCurveChart() [Display final results]
```

**Key Point**: `live_curve_cache.json` is the single source of truth for ALL time series data. `progress.json` contains only summary metrics (percentage, task counts), NOT time series data.

### Frontend Chart State Management

Instead of local variable `liveCurveChartInstance`, track:
```javascript
{
    chartInstance: Chart instance,
    lastDataState: {
        time_points: [...],
        total_running: [...],
        last_update: timestamp
    }
}
```

---

## Impact Analysis

### Benefits
- ✅ Chart x-axis clearly shows simulation time in seconds (0, 1, 2, ... 3600)
- ✅ Chart maintains stable visual size throughout simulation
- ✅ Smoother user experience with no rebuild flicker
- ✅ Reduced frontend CPU usage (no full redraws)
- ✅ Better debugging with clear data source tracking

### Risks
- ⚠️ Chart.js `update()` may have edge cases with different data lengths
- ⚠️ Browser memory impact if storing large previous states

### Backward Compatibility
- ✅ No API changes required
- ✅ No backend changes required
- ✅ Pure frontend UI improvement

---

## Success Criteria

- [ ] X-axis labels show integer seconds (0, 60, 120, 180, ...)
- [ ] Tooltip on hover shows readable time (HH:MM:SS)
- [ ] Chart container maintains fixed height (300px)
- [ ] Chart size does not fluctuate during updates
- [ ] Chart data accumulates incrementally (no rebuild)
- [ ] Data source properly documented and logged
- [ ] All existing tests pass
- [ ] E2E tests for batch simulation chart display pass

---

## Timeline

- **Phase 1** (frontend): X-axis format + chart stability (1-2 hours)
- **Phase 2** (frontend): Incremental data point addition (1-2 hours)
- **Phase 3** (docs): Data source documentation (30 minutes)
- **Testing & validation**: (1 hour)

**Total**: 4-5 hours

---

## References

- [batch_simulation.js:549-684](../frontend/control/js/batch_simulation.js#L549-L684) - renderLiveCurve() function
- [batch_simulation.js:616-620](../frontend/control/js/batch_simulation.js#L616-L620) - X-axis label conversion
- [simulations.css:316-319](../frontend/control/css/simulations.css#L316-L319) - Chart CSS
- [batch_optimization_service.py:558-687](../api/services/batch_optimization_service.py#L558-L687) - Live time series aggregation
- [batch_response.py:63-97](../api/models/control/responses/batch_response.py#L63-L97) - LiveTimeSeries model

---

## Next Steps

1. ✅ Review and approve this proposal
2. → Create detailed spec.md files for each capability
3. → Generate tasks.md with specific implementation items
4. → Implement and test fixes
5. → Update related documentation
