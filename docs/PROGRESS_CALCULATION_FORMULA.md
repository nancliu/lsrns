# Task Progress Calculation Formula Documentation

**Date**: 2025-11-02
**Related**: OpenSpec Change `unify-batch-monitoring-and-history` Phase 1.9
**Status**: ✅ Complete

---

## Overview

This document explains the complete data flow and calculation formulas for task progress display in the batch monitoring system. Progress data originates from the SUMO simulator, flows through the backend API, and is rendered in the frontend with unit conversion and boundary checks.

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ SUMO Simulator Process                                      │
│ (sumo-gui -c simulation.sumocfg)                           │
│ • Simulates traffic for N steps (0 to 14400)              │
│ • Writes progress to progress.json at 1s intervals         │
└─────────────────────┬───────────────────────────────────────┘
                      │ progress.json written every 1 second
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ Backend: batch_optimization_service.py                      │
│ • Reads progress.json                                       │
│ • Calculates progress_percent                              │
│ • Estimates remaining_time                                 │
│ • Returns JSON response to frontend API                    │
└─────────────────────┬───────────────────────────────────────┘
                      │ API Response (1s polling interval)
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ Frontend: batch_simulation.js                               │
│ • Receives progress JSON                                    │
│ • Normalizes/converts units if needed                       │
│ • Renders progress bar & percentage display                │
│ • Updates live vehicle count curve                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend Progress Calculation (Python)

**File**: `api/services/batch_optimization_service.py`
**Lines**: 450-490

### Formula 1: Progress Percentage

```
progress_percent = (current_time / end_time) × 100
```

**Where**:
- `current_time` = Current simulation time in seconds, extracted from summary.xml `<step time="...">`
  - **Source**: From the last `<step>` element in summary.xml
  - **Example**: `<step time="123.00" .../>` means current_time = 123.00 seconds
- `end_time` = Simulation end time from SUMO configuration `<time><end>` value
  - **Source**: From `<sumoConfiguration>` in summary.xml file header comment
  - **Example**: `<end value="600"/>` means simulation runs for 600 seconds
  - **Currently hardcoded as**: 14400 (default, assumes 4-hour simulation) ❌ WRONG
  - **Should be**: Read dynamically from actual config (e.g., 600 seconds = 10 minutes)
- `progress_percent` = Percentage value (0.00 to 100.00), rounded to 2 decimals

**⚠️ Key Clarification**:
- `current_step` in progress.json is **percent value (0-100)**, NOT time in seconds
- The actual numerator should be `current_time` from summary.xml `<step>` element
- This is fundamentally different from a "step count" - it's actual simulation time in seconds

**⚠️ Important Note**: Line 821 in `batch_optimization_service.py` has a TODO comment:
```python
total_steps=14400  # TODO: 从配置或元数据读取
```
The actual simulation duration should be extracted from:
1. **PREFERRED**: `summary.xml` configuration comment (most reliable - contains actual executed config)
   - Located at: `{simulation_dir}/summary.xml`
   - Contains embedded `<sumoConfiguration>` with `<time><end value="..."/>`
   - Example: `<end value="600"/>` means 600-second simulation
2. **Fallback**: `simulation.sumocfg` file if summary.xml not available
   - Located at: `{simulation_dir}/simulation.sumocfg`
   - Contains `<time><end value="..."/>`
3. **Last Resort**: Case metadata `time_range.end - time_range.start` (less accurate)

**Implementation** (CORRECTED):
```python
import xml.etree.ElementTree as ET
from pathlib import Path

# Step 1: Extract current_time from summary.xml <step> element
summary_file = Path(simulation_dir) / "summary.xml"
last_step_time = 0  # Default to 0 if no steps found

try:
    # Parse summary.xml to get last step's time attribute
    tree = ET.parse(summary_file)
    root = tree.getroot()

    # Find the LAST <step> element
    steps = root.findall('.//step')
    if steps:
        last_step = steps[-1]
        last_step_time = float(last_step.get('time', 0))
except Exception as e:
    logger.warning(f"Failed to extract time from summary.xml: {e}")
    last_step_time = 0

# Step 2: Extract end_time from SUMO config (in summary.xml header comment)
end_time = 14400  # Default fallback
try:
    with open(summary_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract <sumoConfiguration> from XML comment
    start = content.find('<sumoConfiguration')
    end_tag_pos = content.find('</sumoConfiguration>') + len('</sumoConfiguration>')

    if start >= 0 and end_tag_pos > start:
        config_xml = content[start:end_tag_pos]
        config = ET.fromstring(config_xml)
        end_value = config.find('.//time/end').get('value')

        if end_value:
            end_time = int(float(end_value))
except Exception as e:
    logger.warning(f"Failed to extract end_time from summary.xml config: {e}")

# Step 3: Calculate progress percentage
current_time = last_step_time  # This is the CORRECT numerator

if end_time > 0:
    progress_percent = (current_time / end_time) * 100
    progress_percent = round(progress_percent, 2)
else:
    progress_percent = 0
```

**Example Calculations**:

*Example 1: 600-second simulation (10 minutes, actual case)*
| current_time (from summary.xml) | end_time (from config) | Calculation | progress_percent |
|----------------------------------|------------------------|-------------|------------------|
| 0.00 sec                        | 600 sec                | 0/600 × 100 | 0.00%            |
| 60.00 sec                       | 600 sec                | 60/600 × 100 | 10.00%           |
| 300.00 sec                      | 600 sec                | 300/600 × 100 | 50.00%           |
| 599.00 sec                      | 600 sec                | 599/600 × 100 | 99.83%           |

*Example 2: 14400-second simulation (4 hours, legacy/longer simulation)*
| current_time | end_time | Calculation | progress_percent |
|--------------|----------|-------------|------------------|
| 0.00 sec     | 14400 sec | 0/14400 × 100 | 0.00%            |
| 1440.00 sec  | 14400 sec | 1440/14400 × 100 | 10.00%           |
| 7200.00 sec  | 14400 sec | 7200/14400 × 100 | 50.00%           |
| 14400.00 sec | 14400 sec | 14400/14400 × 100 | 100.00%          |

### Formula 2: Estimated Remaining Time

```
elapsed_seconds = (datetime.now() - started_at).total_seconds()
avg_step_duration = elapsed_seconds / current_step  (if current_step > 0)
remaining_steps = total_steps - current_step
estimated_remaining_seconds = remaining_steps × avg_step_duration
```

**Where**:
- `elapsed_seconds` = Time since simulation started (in seconds)
- `avg_step_duration` = Average time per simulation step
- `remaining_steps` = Steps left to complete
- `estimated_remaining_seconds` = Predicted time until completion

**Implementation**:
```python
from datetime import datetime

started_at = simulation_record['started_at']  # datetime object
elapsed_seconds = (datetime.now() - started_at).total_seconds()

# Calculate average step duration (with safety check)
if current_step > 0:
    avg_step_duration = elapsed_seconds / current_step
else:
    avg_step_duration = 1.0  # Default 1 second per step if no steps elapsed

# Estimate remaining time
remaining_steps = total_steps - current_step
estimated_remaining_seconds = int(remaining_steps * avg_step_duration)
```

**Example Calculation**:
```
Scenario: Simulation running for 10 minutes with 2000 steps completed
├─ elapsed_seconds = 600 seconds
├─ current_step = 2000 steps
├─ avg_step_duration = 600 / 2000 = 0.3 seconds/step
├─ remaining_steps = 14400 - 2000 = 12400 steps
└─ estimated_remaining_seconds = 12400 × 0.3 = 3720 seconds (~62 minutes)
```

### Output JSON Response

```json
{
  "batch_id": "batch_20251102_111342",
  "task_id": "sim_66",
  "status": "running",
  "progress_percent": 13.89,
  "current_step": 2000,
  "total_steps": 14400,
  "elapsed_seconds": 600,
  "estimated_remaining_seconds": 3720,
  "running_vehicles": 45,
  "message": "正在仿真..."
}
```

---

## Frontend Progress Display (JavaScript)

**File**: `frontend/control/js/batch_simulation.js`
**Functions**: `renderTaskList()`, `updateProgress()`

### Formula 1: Unit Conversion (Simulation time → 0-100%)

**CORRECTION**: Backend should ALWAYS return `progress_percent` as percentage (0-100). The conversion from raw time to percentage happens in the backend, not frontend.

However, if backend accidentally returns raw `current_time` values (0-end_time), frontend should handle it:

```javascript
// Step 1: Extract progress value with explicit null/undefined check
let progressValue = (liveStatus.progress_percent !== null && liveStatus.progress_percent !== undefined)
    ? liveStatus.progress_percent
    : (task.progress !== null && task.progress !== undefined ? task.progress : 0);

// Step 2: Extract end_time from backend for safety
let endTime = liveStatus.end_time || 600;  // Default to common 10-minute simulation

// Step 3: Auto-detect and convert if in different units
let progressPct = progressValue;
if (progressValue > 100) {
    // Input is in simulation seconds (0-end_time), convert to percentage
    // Formula: percentage = (current_time / end_time) × 100 = (current_time / (end_time/100))
    const divisor = endTime / 100;
    progressPct = Math.min((progressValue / divisor), 100);
}

// Step 4: Boundary check to ensure valid range [0, 100]
progressPct = Math.max(0, Math.min(100, progressPct));
```

**Conversion Logic Explanation**:

If numerator is in simulation seconds (0-600 for 10-minute sim):
```
progressPct = (current_time / end_time) × 100
            = (current_time / (600/100))
            = (current_time / 6)
```

**⚠️ Important**: Backend should pass `end_time` in the response so frontend can calculate the correct divisor. Never rely on hardcoded divisor (144 or 6).

**Example Conversions**:

*For 600-second simulation (end_time = 600)*:
| Input Value | Input Type | Calculation | Output % |
|------------|-----------|-------------|----------|
| 50         | Percent (from backend) | No conversion needed | 50.00% |
| 300        | Simulation seconds | 300 / (600/100) = 300/6 = 50 | 50.00% |
| 6          | Simulation seconds | 6 / (600/100) = 6/6 = 1 | 1.00% |
| 600        | Simulation seconds | 600 / (600/100) = 600/6 = 100 | 100.00% |

*For 14400-second simulation (end_time = 14400)*:
| Input Value | Input Type | Calculation | Output % |
|------------|-----------|-------------|----------|
| 50         | Percent (from backend) | No conversion needed | 50.00% |
| 7200       | Simulation seconds | 7200 / (14400/100) = 7200/144 = 50 | 50.00% |
| 144        | Simulation seconds | 144 / (14400/100) = 144/144 = 1 | 1.00% |
| 14400      | Simulation seconds | 14400 / (14400/100) = 14400/144 = 100 | 100.00% |

### Formula 2: Remaining Time Display

```javascript
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}
```

**Example**:
```javascript
// Example: 3720 seconds remaining
formatDuration(3720)
├─ hours = Math.floor(3720 / 3600) = 1
├─ minutes = Math.floor(120 / 60) = 2
├─ secs = Math.floor(0 / 60) = 0
└─ return "1h 2m"
```

### Implementation in renderTaskList()

```javascript
function renderTaskList(tasks) {
    let tasksByGroup = {};

    // Group tasks by simulation_id
    Object.values(tasks).forEach(task => {
        let group_key = task.simulation_id || 'unknown';
        if (!tasksByGroup[group_key]) {
            tasksByGroup[group_key] = [];
        }
        tasksByGroup[group_key].push(task);
    });

    let content = '';

    Object.keys(tasksByGroup).sort().forEach(sim_id => {
        let group = tasksByGroup[sim_id];
        let sim_name = group[0].simulation_name || sim_id;

        content += `<div class="task-group-header">${sim_name}</div>`;

        group.forEach(task => {
            if (task.status === 'running') {
                const liveStatus = task.live_status || {};

                // ===== CRITICAL SECTION: Progress Normalization =====
                // Step 1: Extract with explicit null/undefined check
                let progressValue = (liveStatus.progress_percent !== null &&
                                    liveStatus.progress_percent !== undefined)
                    ? liveStatus.progress_percent
                    : (task.progress !== null && task.progress !== undefined
                        ? task.progress
                        : 0);

                // Step 2: Auto-detect and convert if in different units
                let progressPct = progressValue;
                if (progressValue > 100) {
                    // Convert from simulation steps (0-14400) to percentage
                    progressPct = Math.min((progressValue / 144), 100);
                }

                // Step 3: Boundary check to ensure valid range
                progressPct = Math.max(0, Math.min(100, progressPct));
                // ===== END CRITICAL SECTION =====

                const runningVeh = liveStatus.running_vehicles;
                const remainingSec = liveStatus.estimated_remaining_seconds;

                // Render progress bar with normalized percentage
                content += `
                    <div class="task-item">
                        <div class="task-header">
                            <span class="task-name">${task.task_id}</span>
                            <span class="task-status-badge running">运行中</span>
                        </div>

                        <!-- Progress Bar -->
                        <div class="task-progress-bar" style="
                            width: 100%;
                            height: 24px;
                            background: #e8e8e8;
                            border-radius: 4px;
                            overflow: hidden;
                            margin: 8px 0;
                        ">
                            <div style="
                                width: ${progressPct}%;
                                height: 100%;
                                background: linear-gradient(90deg, #4CAF50, #45a049);
                                transition: width 0.3s ease;
                            "></div>
                        </div>

                        <!-- Progress Text and Live Info -->
                        <div class="task-live-status" style="
                            display: flex;
                            justify-content: space-between;
                            font-size: 12px;
                            color: #666;
                        ">
                            <span>${progressPct.toFixed(1)}%</span>
                            ${runningVeh !== undefined ? `<span>在网: ${runningVeh}辆</span>` : ''}
                            ${remainingSec !== undefined ? `<span>剩余: ${formatDuration(remainingSec)}</span>` : ''}
                        </div>
                    </div>
                `;
            }
        });
    });

    // Render to DOM
    const taskListElement = document.getElementById('monitorTaskList');
    if (taskListElement) {
        taskListElement.innerHTML = content;
    }
}
```

---

## Complete Calculation Example

### Scenario: Real Batch Simulation

**Setup** (from actual data):
- Case ID: `case_20251028_091831`
- Batch ID: `batch_20251102_111342`
- Plan ID: `baseline_plan`
- Seed: `66`
- Simulation config: `<time><end value="600"/>`
- **Total simulation duration**: 600 seconds (10 minutes) - NOT hardcoded 14400!
- Current simulation time: 300.00 seconds (extracted from summary.xml `<step time="300.00" .../>`)

### Backend Calculation

**At simulation time 300.00 seconds (halfway through 600-second simulation)**:

```
Numerator: current_time = 300.00 seconds (from summary.xml <step time="300.00">)
Denominator: end_time = 600 seconds (from <sumoConfiguration><time><end value="600"/></sumoConfiguration>)

1️⃣ Progress Percentage (CORRECTED):
   progress_percent = (300.00 / 600) × 100
                    = 0.5 × 100
                    = 50.00%

2️⃣ Average Step Duration:
   elapsed_seconds = 300.00 seconds (wall clock time)
   steps_completed = 300.00 (simulation time in seconds, not "step count")
   avg_second_per_second = elapsed_seconds / steps_completed

3️⃣ Remaining Time:
   remaining_time = 600 - 300.00 = 300.00 seconds
   estimated_remaining_seconds = 300.00 seconds
                                = 5 minutes
```

**Key Point**: The numerator is `current_time` (simulation time from `<step>` element), NOT a "step count". This is seconds elapsed in simulation, divided by seconds configured for the simulation.

**Backend Response**:
```json
{
  "batch_id": "batch_20251102_111342",
  "task_id": "sim_66",
  "status": "running",
  "progress_percent": 50.00,
  "current_time": 300.00,
  "end_time": 600,
  "estimated_remaining_seconds": 300,
  "running_vehicles": 45,
  "message": "正在仿真...",
  "live_status": {
    "progress_percent": 50.00,
    "current_time": 300.00,
    "end_time": 600,
    "running_vehicles": 45,
    "estimated_remaining_seconds": 300
  }
}
```

**Note**: `current_time` is in seconds (from summary.xml `<step time="..."/>`), not a "step count".

### Frontend Rendering

**JavaScript Processing**:

```javascript
const task = {
    task_id: 'sim_66',
    status: 'running',
    progress: 50.00,
    live_status: {
        progress_percent: 50.00,
        running_vehicles: 45,
        estimated_remaining_seconds: 300
    }
};

// Extract progress value
let progressValue = (task.live_status.progress_percent !== null &&
                     task.live_status.progress_percent !== undefined)
    ? task.live_status.progress_percent
    : (task.progress !== null && task.progress !== undefined
        ? task.progress
        : 0);

// progressValue = 50.00

// Check if conversion needed (only if > 100)
let progressPct = 50.00;
if (50.00 > 100) {  // FALSE - no conversion needed
    progressPct = Math.min((50.00 / 144), 100);
}

// Boundary check
progressPct = Math.max(0, Math.min(100, 50.00));  // Still 50.00

// Final output: 50.00%

// Format remaining time
formatDuration(300):
├─ hours = Math.floor(300 / 3600) = 0
├─ minutes = Math.floor(300 / 60) = 5
├─ secs = Math.floor(0 / 60) = 0
└─ return "5m 0s"
```

**HTML Output**:
```html
<div class="task-item">
    <div class="task-header">
        <span class="task-name">sim_66</span>
        <span class="task-status-badge running">运行中</span>
    </div>

    <div class="task-progress-bar" style="...">
        <div style="width: 50.00%; ..."></div>
    </div>

    <div class="task-live-status">
        <span>50.0%</span>
        <span>在网: 45辆</span>
        <span>剩余: 5m 0s</span>
    </div>
</div>
```

**Visual Result**:
```
sim_66                                    [运行中]

[██████████████████████░░░░░░░░░░░░░░░░░░]

50.0%   在网: 45辆   剩余: 5m 0s
```

---

## Key Parameters Table

| Parameter | Source | Type | Range | Purpose | Current Status |
|-----------|--------|------|-------|---------|-----------------|
| `current_step` | progress.json | Integer | 0-N | Position in simulation (seconds) | ✅ Correct |
| `total_steps` | Should be from SUMO config `<time><end>` | Integer | Variable | Total simulation duration in seconds | ❌ Hardcoded as 14400 (TODO) |
| `progress_percent` | Backend calc | Float | 0.00-100.00 | Percentage complete | ✅ Correct (if total_steps is correct) |
| `elapsed_seconds` | Backend calc | Integer | 0-∞ | Time since start (wall clock) | ✅ Correct |
| `avg_step_duration` | Backend calc | Float | 0.01-∞ | Seconds per simulation step | ✅ Correct |
| `estimated_remaining_seconds` | Backend calc | Integer | 0-∞ | Predicted time to completion | ✅ Correct (if total_steps is correct) |
| `running_vehicles` | SUMO simulation | Integer | 0-∞ | Active vehicles in network | ✅ Correct |
| `progressValue` | Frontend extract | Float | 0-∞ | Raw value from backend | ✅ Correct |
| `progressPct` | Frontend normalize | Float | 0.00-100.00 | Display percentage (normalized) | ✅ Correct (with caveats) |

---

## Phase 1.9 Bugfix Details

### Issue 1: Falsy Value Handling

**Problem**: Using OR operator with 0 as falsy value
```javascript
// ❌ WRONG - Treats 0 as falsy
const progressPct = liveStatus.progress_percent || task.progress || 0;
// When progress_percent = 0: evaluates to (false || task.progress || 0)
// Falls back to task.progress instead of using 0
```

**Solution**: Explicit null/undefined checks
```javascript
// ✅ CORRECT - Treats 0 as valid value
let progressValue = (liveStatus.progress_percent !== null &&
                     liveStatus.progress_percent !== undefined)
    ? liveStatus.progress_percent
    : (task.progress !== null && task.progress !== undefined
        ? task.progress
        : 0);
```

### Issue 2: Unit Mismatch (Steps vs Percentage)

**Problem**: Backend sometimes returns progress in different units
- Scenario 1: Backend returns `progress_percent = 13.89` (percentage)
- Scenario 2: Backend returns `progress = 2000` (simulation steps)
- Frontend must handle both cases transparently

**Solution**: Auto-detection and conversion
```javascript
let progressPct = progressValue;
if (progressValue > 100) {
    // If value > 100, must be in steps (0-14400)
    // Convert: steps / 144 = percentage
    progressPct = Math.min((progressValue / 144), 100);
}
// If value ≤ 100, assume already a percentage
```

**Validation Logic**:
| progressValue | Interpretation | progressPct | Confidence |
|--------------|----------------|------------|------------|
| 0            | Percentage or steps | 0.00% | High (same value) |
| 13.89        | Percentage | 13.89% | High (< 100) |
| 100          | Percentage or steps (1% of 14400) | 100% | Medium (ambiguous) |
| 2000         | Simulation steps | 13.89% | High (> 100) |
| 14400        | Simulation steps | 100% | High (> 100) |
| 150          | Steps | 104.17% → Clamped to 100% | High (> 100) |

---

## Data Quality Notes

### Reliability

1. **Backend Calculation**: ⚠️ Partially Reliable
   - Direct division: `current_step / total_steps` ✅
   - Math is simple and deterministic ✅
   - **BUT**: `total_steps` is hardcoded as 14400 ❌
   - Currently hardcoded value doesn't match actual simulation durations (e.g., 600 seconds)
   - **Impact**: Progress percentages are wrong when simulation duration ≠ 14400 seconds

2. **Frontend Display**: ✅ Reliable (after Phase 1.9 fix)
   - Explicit null checks prevent falsy value issues
   - Unit conversion handles both percentage and step inputs (with assumptions)
   - Boundary checks ensure valid [0, 100] range
   - Updated to task.md as of 2025-11-02
   - **BUT**: Auto-converts assuming default 14400-second duration (see Frontend Limitation above)

### Critical Issues to Fix

1. **Hardcoded total_steps = 14400** 🚨 **MUST FIX**
   - Location: `api/services/batch_optimization_service.py` line 821
   - Issue: Doesn't match actual simulation durations (e.g., 600 seconds)
   - Solution: Read from SUMO config `<time><end value="..."/>` in `simulation.sumocfg`
   - Impact: Wrong progress percentage when simulation duration ≠ 14400

2. **Missing total_steps in API Response** 🚨 **SHOULD FIX**
   - Frontend unit conversion assumes 14400 seconds (divisor = 144)
   - If total_steps varies, conversion will be inaccurate
   - Solution: Include `total_steps` in backend JSON response so frontend can calculate correct divisor

### Potential Issues

1. **Zero Step Duration** (Rare)
   - Backend handles: `if current_step > 0` → `avg_step_duration = 1.0` fallback
   - Result: Remaining time estimate will be conservative

2. **Simulation Restart** (Edge Case)
   - If `total_steps` changes mid-simulation, percentages will jump
   - Mitigation: Simulation duration is set at config creation time, doesn't change

3. **Time Drift** (Negligible)
   - Backend uses `datetime.now()` for elapsed time
   - If server time changes, estimates may be inaccurate for one update
   - Mitigation: Frontend doesn't use wall-clock time, uses backend calculations

---

## Implementation Files Reference

### Backend Files

| File | Function | Lines | Purpose |
|------|----------|-------|---------|
| `api/services/batch_optimization_service.py` | `_calculate_task_progress()` | 450-490 | Backend progress calculation |
| `api/services/batch_optimization_service.py` | `get_batch_tasks_status()` | 200-250 | API endpoint returning progress data |

### Frontend Files

| File | Function | Purpose |
|------|----------|---------|
| `frontend/control/js/batch_simulation.js` | `renderTaskList()` | Task list rendering with progress display |
| `frontend/control/js/batch_simulation.js` | `updateProgress()` | Real-time progress updates |
| `frontend/control/js/batch_simulation.js` | `formatDuration()` | Remaining time formatting |
| `frontend/control/simulations.html` | HTML structure | Progress bar and percentage display |
| `frontend/control/css/simulations.css` | `.task-progress-bar` | Progress bar styling |

### Related Documentation

| Document | Purpose |
|----------|---------|
| `openspec/changes/unify-batch-monitoring-and-history/IMPLEMENTATION_SUMMARY.md` | Phase 1.9 implementation details |
| `openspec/changes/unify-batch-monitoring-and-history/tasks.md` | Task list with Phase 1.9 completion |

---

## Known Limitations & TODO Items

### Summary: Two Critical Issues Identified

| Issue | Severity | Root Cause | Impact | Status |
|-------|----------|-----------|--------|--------|
| **Issue 1**: Hardcoded total_steps in backend | 🚨 CRITICAL | Line 821: `total_steps=14400` hardcoded | Progress percentage completely wrong for non-14400s simulations | ❌ NOT FIXED |
| **Issue 2**: Frontend missing total_steps | 🚨 SHOULD FIX | Frontend assumes divisor=144 | Unit conversion inaccurate if backend values in steps | ⚠️ PARTLY MITIGATED |

### Fix Priority & Order

**Priority 1 (MUST FIX FIRST)**: Issue 1 - Extract total_steps from summary.xml
- Reason: This is the root cause of incorrect progress calculations
- Impact: Once fixed, progress_percent will be correct
- Effort: Medium (need to parse XML comment from summary.xml)
- Code location: `batch_optimization_service.py` lines 817-822

**Priority 2 (SHOULD FIX AFTER Priority 1)**: Issue 2 - Include total_steps in API response
- Reason: Defensive programming - ensures frontend can do correct conversions even if Issue 1 is broken
- Impact: Frontend becomes more robust
- Effort: Low (just add field to response dictionary)
- Code location: `batch_optimization_service.py` lines 481-493, `batch_simulation.js` unit conversion

---

### Issue 1: Hardcoded total_steps in Backend ❌ CRITICAL

**Current State**:
```python
# Line 821 in batch_optimization_service.py
live_status = self._get_simulation_live_status(
    case_id=case_id,
    batch_id=batch_id,
    task=task_dict,
    total_steps=14400  # TODO: 从配置或元数据读取
)
```

**Problem**: Always assumes 14400 seconds (4 hours), regardless of actual simulation configuration
- Example: Simulation configured for 600 seconds (10 minutes) shows 0.67% progress at 4 minutes elapsed
- Correct should be: ~66.7% progress at 4 minutes elapsed (in a 600-second simulation)

**Solution**: Extract `total_steps` from `summary.xml` configuration comment

**Recommended Implementation** (extract from summary.xml - most reliable):
```python
import xml.etree.ElementTree as ET
from pathlib import Path

def get_simulation_total_steps(simulation_dir: Path) -> int:
    """Extract simulation end time from summary.xml configuration comment"""
    summary_file = simulation_dir / "summary.xml"

    if not summary_file.exists():
        return 14400  # Fallback to default

    try:
        with open(summary_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the sumoConfiguration embedded in XML comment
        start = content.find('<sumoConfiguration')
        end = content.find('</sumoConfiguration>') + len('</sumoConfiguration>')

        if start >= 0 and end > start:
            config_xml = content[start:end]
            config = ET.fromstring(config_xml)
            end_value = config.find('.//time/end').get('value')

            if end_value:
                return int(float(end_value))
    except Exception as e:
        logger.warning(f"Failed to parse total_steps from summary.xml: {e}")

    # Fallback to simulation.sumocfg
    return get_total_steps_from_config(simulation_dir / "simulation.sumocfg")

def get_total_steps_from_config(config_file: Path) -> int:
    """Fallback: Extract from simulation.sumocfg"""
    try:
        config = ET.parse(config_file)
        end_time = config.find('.//time/end').get('value', '14400')
        return int(float(end_time))
    except Exception:
        return 14400
```

**Then update the call at line 817-822**:
```python
# Calculate actual total_steps from simulation configuration
total_steps = get_simulation_total_steps(simulation_dir)

live_status = self._get_simulation_live_status(
    case_id=case_id,
    batch_id=batch_id,
    task=task_dict,
    total_steps=total_steps  # ← Now dynamic, not hardcoded
)
```

**Files to Modify**:
- `api/services/batch_optimization_service.py` lines 817-822 (use dynamic total_steps)
- Consider adding helper function `get_simulation_total_steps()` to this service class

---

### Issue 2: Frontend Missing total_steps ❌ SHOULD FIX

**Current State**: Frontend assumes divisor of 144 for unit conversion (hardcoded for 14400 seconds)
```javascript
if (progressValue > 100) {
    progressPct = Math.min((progressValue / 144), 100);  // Hardcoded divisor
}
```

**Problem**: If simulation duration ≠ 14400 seconds, unit conversion is inaccurate
- Example: 600-second simulation, showing 300 steps (in progress.json)
- Current calculation: 300 / 144 = 2.08% (WRONG - shows as barely started)
- Correct calculation: 300 / (600/100) = 300 / 6 = 50.00% (halfway through)

**Why this matters**: After Issue 1 is fixed, backend will return correct `progress_percent` ONLY when backend is fixed. Until then, frontend may need to do fallback unit conversion using actual total_steps.

**Solution**: Include `total_steps` in backend API response

**Backend change** (in response JSON):
```python
# In batch_optimization_service.py, ensure live_status includes total_steps:
live_status = {
    'current_step': current_step,
    'total_steps': total_steps,           # ← Add this field
    'progress_percent': progress_percent,  # ← Already correct if Issue 1 is fixed
    'running_vehicles': running_vehicles,
    'estimated_remaining_seconds': estimated_remaining_seconds
}
```

**Frontend change** (improved unit conversion):
```javascript
// Receive from backend:
let progressValue = liveStatus.progress_percent;
let totalSteps = liveStatus.total_steps || 14400;  // Use backend value if available

// Smart conversion:
let progressPct = progressValue;
if (progressValue > 100) {
    // Value is in steps, convert to percentage using actual total_steps
    const divisor = totalSteps / 100;
    progressPct = Math.min((progressValue / divisor), 100);
}

// Boundary check
progressPct = Math.max(0, Math.min(100, progressPct));
```

**Files to Modify**:
- `api/services/batch_optimization_service.py` (lines 481-493)
  - Ensure `total_steps` is included in live_status dictionary
- `frontend/control/js/batch_simulation.js`
  - Update unit conversion to use `total_steps` from backend if available
  - Calculate dynamic divisor: `divisor = total_steps / 100`

---

## Critical Finding: The Numerator is Simulation Time, NOT Step Count

**IMPORTANT CLARIFICATION**: The numerator in the progress formula is **simulation time in seconds** (from `<step time="..."/>`), NOT a count of simulation steps.

```
progress_percent = (simulation_seconds / configured_end_seconds) × 100

Examples:
- At 300 seconds in a 600-second simulation: (300 / 600) × 100 = 50%
- At 7200 seconds in a 14400-second simulation: (7200 / 14400) × 100 = 50%
- At 599 seconds in a 600-second simulation: (599 / 600) × 100 = 99.83%
```

This is fundamentally different from counting discrete steps. The numerator directly comes from the `time` attribute of the last `<step>` element in summary.xml.

---

## Conclusion

The task progress calculation system follows a clear three-layer architecture:

1. **Backend (Python)**:
   - Reads current simulation time from summary.xml `<step time="...">`
   - Reads end time from SUMO config `<time><end value="..."/>`
   - Calculates: `progress_percent = (current_time / end_time) × 100`

2. **API (JSON)**:
   - Returns `progress_percent` as percentage (0-100)
   - Also returns `current_time` and `end_time` for frontend safety

3. **Frontend (JavaScript)**:
   - Displays percentage directly
   - If backend returns raw time values, converts using `end_time` from response

**Current Status**:
- ✅ Formula is conceptually correct (time/time = percentage)
- ❌ **CRITICAL BUG**: Backend hardcodes denominator to 14400 instead of reading from config
- ❌ **SHOULD FIX**: Backend should include `end_time` in API response

See "Known Limitations & TODO Items" section for detailed fix instructions.
