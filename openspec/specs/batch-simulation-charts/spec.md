# batch-simulation-charts Specification

## Purpose
TBD - created by archiving change fix-batch-simulation-chart-issues. Update Purpose after archive.
## Requirements
### Requirement: X-Axis SHALL Display Integer Seconds

The system SHALL display x-axis labels using raw integer seconds (0, 10, 20, 30, ...) matching the API's `time_points` array, and SHALL include a tooltip showing readable HH:MM:SS format on hover.

**Acceptance Criteria**:
- X-axis labels are integer seconds from `time_points` array
- No time-unit conversion (HH:MM) applied to x-axis
- Tooltip on hover shows HH:MM:SS format plus total seconds
- Label density controlled to avoid crowding

#### Scenario: X-Axis Shows Integer Seconds

**Given** `renderLiveCurve()` receives `liveTimeSeries.time_points = [0, 10, 20, 30, 40, 50, 60, 120, 180, ...]`

**When** Chart.js renders the x-axis

**Then** x-axis displays labels "0", "10", "20", "30", "40", "50", "60", "120", "180" with no conversion or formatting applied

#### Scenario: Tooltip Displays Human-Readable Time Format

**Given** x-axis displays integer seconds

**When** user hovers over any chart point

**Then** tooltip displays:
- Time in HH:MM:SS format (e.g., "00:01:45")
- Total seconds (e.g., "105秒")
- Combined format: "时间: 00:01:45 (105秒)"

---

### Requirement: Chart Container SHALL Maintain Responsive Aspect Ratio

The system SHALL use CSS `aspect-ratio: 16 / 9` to stabilize chart dimensions so height automatically scales with container width, preventing dimension changes during data updates.

**Acceptance Criteria**:
- `.live-curve-section` uses `aspect-ratio: 16 / 9`
- Height = width × 9/16 (automatically calculated by CSS)
- No fixed pixel heights that restrict responsive scaling
- Works on all viewport sizes (desktop, tablet, mobile)
- No visual flicker or size changes during data accumulation

#### Scenario: Chart Scales Responsively Across Screen Sizes

**Given** `.live-curve-section` has `aspect-ratio: 16 / 9` and `width: 100%`

**When** browser viewport changes from 1200px to 800px to 400px width

**Then** chart height automatically adjusts to maintain 16:9 ratio without layout shift or fluttering

#### Scenario: Chart Size Remains Stable During Multiple Updates

**Given** batch simulation is running and new data arrives every 10 seconds

**When** `renderLiveCurve()` is called 5+ times with increasing data points

**Then** chart container maintains exact same dimensions throughout all updates with no visual fluctuation

---

### Requirement: Chart Update Logic SHALL Use Incremental Data Addition

The system SHALL replace the destroy/recreate pattern with incremental Chart.js `update()` calls to add new data points without rebuilding the entire chart instance.

**Acceptance Criteria**:
- First `renderLiveCurve()` call creates Chart instance (stored globally)
- Subsequent calls detect existing instance and use `update()` method
- Canvas element reused (not destroyed and recreated)
- Data points accumulate incrementally without rebuild
- Performance improves from 500ms to ~70ms per update (7x faster)
- CPU usage reduces from ~15% to <5% during updates
- Edge cases handled: data reset, simulation restart, empty data

#### Scenario: Create Chart on First Call

**Given** `renderLiveCurve()` is called for the first time

**When** no chart instance yet exists

**Then** Chart.js instance is created, stored globally, and rendered with initial data

#### Scenario: Update Chart Incrementally on Subsequent Calls

**Given** Chart instance exists and new `liveTimeSeries` data arrives

**When** `renderLiveCurve()` is called with updated data

**Then** function detects existing instance and calls `chart.update('none')` to refresh data without animation or canvas recreation

#### Scenario: Detect and Skip Unchanged Data

**Given** `renderLiveCurve()` is called but data is identical to previous state

**When** comparing `liveTimeSeries` with stored `lastDataState`

**Then** update is skipped and function returns early (no Chart.js operation)

#### Scenario: Handle Simulation Restart with Data Reset

**Given** batch simulation is restarted (data size decreases or simulation ID changes)

**When** `renderLiveCurve()` detects reset condition

**Then** old chart instance is destroyed, new instance created with fresh data, no orphaned objects remain

---

### Requirement: System SHALL Document and Verify Unified Data Source

The system SHALL verify and document that `live_curve_cache.json` (per-task files) is the exclusive, single source of truth for all vehicle count time series data during both runtime and completion. The system SHALL verify that `progress.json` is metrics-only and never used for time series.

**Acceptance Criteria**:
- `_aggregate_live_time_series()` confirmed to use only per-task cache files
- Code comments explicitly document unified data source
- `progress.json` usage verified to be metrics-only
- Debug logging shows per-task cache file aggregation flow
- Frontend receives and logs data structure confirmation
- Both runtime and completion charts confirmed using identical source
- No code references alternating between cache and progress sources

#### Scenario: Backend Aggregation Uses Only Cache Files

**Given** `_aggregate_live_time_series()` is called to aggregate time series data

**When** function processes data from multiple tasks

**Then** function reads only each task's `live_curve_cache.json` file, NOT `progress.json`, and code comments state: "ONLY live_curve_cache.json is the source", "SINGLE SOURCE OF TRUTH", and "Both runtime and completion use the same source"

#### Scenario: Completion Charts Use Identical Cache Source

**Given** batch simulation completes and final results are retrieved

**When** `BatchResultsResponse` populates time series data

**Then** data comes from same per-task `live_curve_cache.json` files via same aggregation logic as runtime charts

#### Scenario: Debug Logging Confirms Data Provenance

**Given** batch simulation runs with debug logging enabled

**When** data aggregation occurs

**Then** logs show:
- "Aggregating from per-task cache files: [task_ids]"
- For each file: "Task [id]: [N] time points, [M] vehicle entries"
- Final: "Aggregation complete: [N] total points, [M] total entries"
- Frontend logs: "Vehicle count data aggregated from task cache files"

---

