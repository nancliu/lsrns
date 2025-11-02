# batch-monitoring-unified Specification

## Purpose
TBD - created by archiving change unify-batch-monitoring-and-history. Update Purpose after archive.
## Requirements
### Requirement: Unified Batch List Displays All Batch States

The system MUST display all batches in a unified list view with status indicators, filtering, and sorting capabilities. The list MUST show running batches with real-time progress updates and completed/failed batches with final status.

**Priority**: P0
**Status**: New

#### Scenario: Display All Batches in Unified List

**Given**:
- System has 15 batches:
  - 2 running (batch_001, batch_002)
  - 10 completed (batch_003 to batch_012)
  - 2 failed (batch_013, batch_014)
  - 1 cancelled (batch_015)

**When**:
- User navigates to "批次监控 (Batch Monitoring)" tab

**Then**:
- List displays all 15 batches as cards in grid layout
- Each card shows:
  - batch_id (abbreviated, e.g., "batch_...001")
  - case_name
  - plan_count (e.g., "3个方案")
  - status badge: "运行中 ⏳" | "已完成 ✓" | "失败 ✗" | "已取消 ❌"
  - created_at (relative time, e.g., "2小时前")
  - For running batches: real-time progress (e.g., "5/9 tasks completed")
  - For completed batches: total duration (e.g., "耗时: 44分钟")

---

#### Scenario: Real-Time Progress Display for Running Batches

**Given**:
- batch_001 is running with 3/9 tasks completed
- User is viewing batch list

**When**:
- API polling returns updated progress (5/9 tasks completed)

**Then**:
- batch_001 card updates to show "5/9 tasks completed"
- Progress bar on card updates to 55% width
- No full page refresh required

---

#### Scenario: Filter Batches by Status

**Given**:
- Batch list displays 15 batches
- Status filter dropdown shows: "全部 | 运行中 | 已完成 | 失败 | 已取消"

**When**:
- User selects "已完成" filter

**Then**:
- List displays only 10 completed batches
- Running, failed, and cancelled batches hidden
- Empty state shown if no completed batches exist

---

#### Scenario: Sort Batches by Creation Time

**Given**:
- Batch list displays all batches

**When**:
- User selects sort option "最近创建"

**Then**:
- Batches sorted by created_at descending (newest first)
- batch_015 (newest) appears at top
- batch_001 (oldest) appears at bottom

---

#### Scenario: Sort Batches by Duration

**Given**:
- Batch list displays completed batches

**When**:
- User selects sort option "耗时最长"

**Then**:
- Batches sorted by duration_seconds descending
- Longest-running batch appears first
- Batches without duration (pending/running) appear last

---

### Requirement: Expandable Batch Cards Show Detailed Execution Information

Users MUST be able to click a batch card to expand it in-place and view detailed execution information. Running batches MUST show real-time task list and live vehicle curves. Completed batches MUST show execution timeline with task durations.

**Priority**: P0
**Status**: New

#### Scenario: Expand Running Batch to Show Live Monitoring

**Given**:
- batch_001 is running with status "running"
- User views batch list

**When**:
- User clicks batch_001 card

**Then**:
- Card expands smoothly (animation <300ms)
- Expanded view shows:
  - Real-time task list with status for each task:
    - Task name (e.g., "baseline_plan_seed66")
    - Status: "pending" | "running" | "completed" | "failed"
    - Start time (if started)
    - Duration (if running/completed)
  - Live progress bar with percentage (e.g., "5/9 tasks - 55%")
  - Estimated completion time (e.g., "预计还需: 12分钟")
  - Live vehicle count curve (updates every 10s)
  - Action buttons: "取消批次" (red), "刷新" (secondary)

---

#### Scenario: Expand Completed Batch to Show Execution History

**Given**:
- batch_003 is completed with all tasks succeeded
- User views batch list

**When**:
- User clicks batch_003 card

**Then**:
- Card expands smoothly
- Expanded view shows:
  - Execution timeline (task timeline visualization):
    - Each task as horizontal bar showing start/end times
    - Task duration in minutes (e.g., "4分30秒")
    - Color-coded by status (green=success, red=failed)
  - Summary metrics:
    - Total duration: "44分18秒"
    - Success rate: "9/9 tasks succeeded (100%)"
    - Average task duration: "4分55秒"
  - Peak vehicle count curve (static snapshot from final results)
  - Action buttons: "查看详细结果 →" (primary), "删除批次" (danger)

---

#### Scenario: Expand Failed Batch to Show Error Information

**Given**:
- batch_013 failed with 2/9 tasks failed
- User views batch list

**When**:
- User clicks batch_013 card

**Then**:
- Card expands smoothly
- Expanded view shows:
  - Execution timeline highlighting failed tasks:
    - Failed tasks shown in red with error icon
    - Completed tasks shown in green
    - Pending tasks shown in gray (not executed)
  - Error logs for failed tasks:
    - Task name: "plan_001_seed67"
    - Error message: "Simulation timeout after 30 minutes"
    - Timestamp: "2025-11-02 10:35:42"
  - Summary metrics:
    - Total duration: "12分30秒" (partial execution)
    - Success rate: "7/9 tasks succeeded (77.8%)"
  - Action buttons: "重新运行" (primary), "删除批次" (danger)

---

#### Scenario: Collapse Expanded Batch Card

**Given**:
- batch_001 card is expanded

**When**:
- User clicks batch_001 card header again

**Then**:
- Card collapses smoothly (animation <300ms)
- Returns to compact list view
- Other cards remain in their state (expanded/collapsed)

---

### Requirement: Live Monitoring Data Updates in Expanded View

The system MUST automatically update task status, progress bar, and vehicle count curve for running batches in expanded view without manual refresh. Update interval MUST be configurable (default: 10 seconds).

**Priority**: P0
**Status**: New

#### Scenario: Automatic Task Status Update

**Given**:
- batch_001 is expanded and running
- Task "plan_001_seed66" has status "running"
- Update interval is 10 seconds

**When**:
- API polling detects task "plan_001_seed66" status changed to "completed"

**Then**:
- Task status updates to "completed" with green checkmark
- Task duration displayed (e.g., "4分30秒")
- Progress bar updates (6/9 = 67%)
- No full card re-render (smooth update)

---

#### Scenario: Live Vehicle Curve Auto-Update

**Given**:
- batch_001 is expanded and running
- Live vehicle curve displayed with 50 data points
- Last update: 10 seconds ago

**When**:
- Update interval triggers (10 seconds elapsed)
- API returns new vehicle count data (55 data points)

**Then**:
- Chart.js updates incrementally with 5 new points
- X-axis extends to show new time range
- Y-axis adjusts if new data exceeds current max
- Update completes in <70ms (no destroy/recreate)

---

#### Scenario: Stop Auto-Update When Batch Completes

**Given**:
- batch_001 is expanded and running with auto-update polling
- Polling interval: 10 seconds

**When**:
- API returns batch status "completed"

**Then**:
- Polling stops automatically
- Final task status displayed
- Live vehicle curve becomes static (no more updates)
- "取消批次" button hidden
- "查看详细结果" button appears

---

### Requirement: Results Tab Integration from Expanded View

Users MUST be able to navigate to the "结果 (Results)" tab from an expanded completed batch with a single click. The Results tab MUST auto-load the selected batch's summary results (summary.xml-based task analysis and peak curves).

**Priority**: P0
**Status**: New

**Note**: The Results tab provides simple batch summary analysis. Advanced optimization analysis (deep comparisons, recommendations) is handled in a separate "方案优化 (Plan Optimization)" page, not in scope for this change.

#### Scenario: Jump to Results Tab from Completed Batch

**Given**:
- batch_003 is completed and expanded
- "查看结果" button is visible

**When**:
- User clicks "查看结果" button

**Then**:
- Tab switches to "结果 (Results)" tab
- Results tab loads batch_003 summary data:
  - Peak vehicle count curve (aggregated from summary.xml)
  - Task comparison table (task-level metrics)
  - Summary statistics (total duration, success rate)
- Batch monitoring view remains in background (no state loss)
- User can return to "批次监控" tab and see batch_003 still expanded

---

#### Scenario: Navigate to Results Tab from Batch Card Action

**Given**:
- batch_003 is completed (not expanded, just card view)
- Card has "查看结果" button

**When**:
- User clicks "查看结果" button on card

**Then**:
- Tab switches to "结果 (Results)" tab
- Results tab loads batch_003 summary data (summary.xml-based)
- Same behavior as expanded view "查看结果" button

---

### Requirement: Execution Timeline Visualization for Historical Batches

The system MUST provide a visual execution timeline for completed/failed batches showing task start/end times, durations, and status. Timeline MUST be sortable by task name, start time, or duration.

**Priority**: P1
**Status**: New

#### Scenario: Display Execution Timeline for Completed Batch

**Given**:
- batch_003 has 9 completed tasks with the following data:
  - Task "baseline_plan_seed66": started 10:30:00, ended 10:34:30, duration 270s
  - Task "plan_001_seed66": started 10:30:05, ended 10:35:10, duration 305s
  - ... (7 more tasks)

**When**:
- User expands batch_003

**Then**:
- Execution timeline displays:
  - Gantt-chart-style horizontal bars for each task
  - X-axis: absolute time (10:30 to 11:15)
  - Each bar labeled with task name and duration (e.g., "baseline_plan_seed66 (4分30秒)")
  - Color: green for completed, red for failed
  - Bars aligned by start time (showing parallelism)

---

#### Scenario: Sort Timeline by Task Duration

**Given**:
- Execution timeline displayed for batch_003
- Timeline has sort dropdown: "按开始时间 | 按任务名 | 按耗时"

**When**:
- User selects "按耗时" (descending)

**Then**:
- Tasks reordered with longest-running task at top
- Task "plan_002_seed68" (duration 320s) appears first
- Task "baseline_plan_seed66" (duration 270s) appears lower

---

### Requirement: Responsive Layout for Batch Monitoring View

The system MUST adapt batch card layout to screen size. Desktop MUST show 3-4 cards per row. Tablet MUST show 2 cards per row. Mobile MUST show 1 card per row. Expanded view MUST switch to modal dialog on mobile (<768px width).

**Priority**: P1
**Status**: New

#### Scenario: Desktop Layout (>1200px)

**Given**:
- User views batch monitoring on desktop (1920px width)

**When**:
- Batch list renders

**Then**:
- Grid layout shows 4 cards per row
- Card width: ~450px
- Cards have comfortable spacing (15-20px gap)

---

#### Scenario: Tablet Layout (768px - 1200px)

**Given**:
- User views batch monitoring on tablet (1024px width)

**When**:
- Batch list renders

**Then**:
- Grid layout shows 2 cards per row
- Card width: ~480px
- Cards maintain aspect ratio

---

#### Scenario: Mobile Layout (<768px)

**Given**:
- User views batch monitoring on mobile (375px width)

**When**:
- Batch list renders

**Then**:
- Grid layout shows 1 card per row
- Card width: 100% (minus padding)
- Cards stack vertically

---

#### Scenario: Mobile Expanded View as Modal

**Given**:
- User on mobile device (375px width)
- Batch card clicked to expand

**When**:
- Card expansion triggers

**Then**:
- Instead of inline expansion, modal dialog opens
- Modal covers full screen (90% height)
- Modal has close button (X)
- Modal body scrolls if content overflows
- Background dimmed with overlay

---

### Requirement: Batch Deletion from Monitoring View

Users MUST be able to delete batches (completed, failed, cancelled) directly from the monitoring view. System MUST confirm deletion and update the list without page refresh.

**Priority**: P1
**Status**: New

#### Scenario: Delete Completed Batch

**Given**:
- batch_003 is completed and expanded
- "删除批次" button visible

**When**:
- User clicks "删除批次"
- Confirmation dialog appears: "确认删除该批次吗？此操作不可撤销。"
- User clicks "确认"

**Then**:
- DELETE API call sent: `/api/v1/control/batch-optimization/batches/batch_003`
- API returns 204 No Content
- batch_003 card removed from list with fade-out animation
- Success notification: "批次已删除"
- List updates without page refresh

---

#### Scenario: Cancel Batch Deletion

**Given**:
- User clicks "删除批次" on batch_003
- Confirmation dialog appears

**When**:
- User clicks "取消"

**Then**:
- Dialog closes
- No API call sent
- batch_003 remains in list

---

#### Scenario: Prevent Deletion of Running Batch

**Given**:
- batch_001 is running (status: "running")
- User attempts to delete via API directly (no "删除批次" button shown for running batches)

**When**:
- DELETE request sent to `/api/v1/control/batch-optimization/batches/batch_001`

**Then**:
- API returns 409 Conflict
- Error message: "无法删除运行中的批次，请先取消批次"
- Frontend shows error notification

---

