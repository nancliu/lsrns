# Proposal: Unify Batch Monitoring and History

**Change ID**: `unify-batch-monitoring-and-history`

**Status**: ✅ Implemented (Phase 1 & 1.5)

**Priority**: Medium (P1 - UX improvement, not blocking)

**Created**: 2025-11-02
**Implemented**: 2025-11-02 (Phase 1 & 1.5 completed in ~5-6 hours)

---

## Executive Summary

Merge the "进度 (Progress)" and "批次历史 (Batch History)" tabs into a unified "批次监控 (Batch Monitoring)" tab that provides both real-time monitoring of running batches and historical review of completed batches. This improves user workflow by consolidating batch lifecycle management into a single, coherent view.

**Proposed Tab Structure** (4 tabs → 3 tabs):
- **配置 (Config)** - Configure and create batch simulations
- **批次监控 (Batch Monitoring)** - *NEW: Unified view combining Progress + History*
- **结果 (Results)** - Simple batch results (summary.xml-based task analysis, peak curves)

---

## Why

### Current Pain Points

**Tab Fragmentation**:
- Users must switch between "进度" and "批次历史" to track batch lifecycle
- Mental model disconnect: "进度" feels like it should include historical progress, but only shows current batch
- After batch completes, users lose visibility into execution details unless they remember to go to "批次历史"

**Workflow Inefficiency**:
1. User creates batch in "配置" tab
2. User switches to "进度" tab to monitor → sees only current batch
3. User forgets batch_id or wants to review previous run → must switch to "批次历史"
4. User wants to see results → must click batch card, then navigate to "结果" tab

**Logical Inconsistency**:
- "批次历史" should logically include execution progress history, not just final status
- "进度" tab becomes empty/useless once batch completes
- Two tabs serve essentially the same purpose (batch lifecycle visibility) but at different time points

### Desired Experience

**Unified Batch Lifecycle View**:
- **Single source of truth** for all batches (running, completed, failed, cancelled)
- **Progressive disclosure**: List view → detailed execution history → results
- **Consistent mental model**: "批次监控" encompasses both real-time and historical monitoring

**Improved Workflow**:
1. User creates batch in "配置"
2. User switches to "批次监控" → sees batch list with running batches at top
3. User clicks running batch → expands to show real-time progress (task list, live curves)
4. After completion, same batch card shows execution summary with "查看结果" button
5. User clicks "查看结果" → jumps to "结果" tab for summary analysis (summary.xml-based)

---

## Problem Statement

### Current Behavior

**4 Tabs**:
1. **配置 (Config)** - Create batch simulations
2. **进度 (Progress)** - Monitor **only current** running batch (real-time task list, progress bar, live curves)
3. **结果 (Results)** - View batch results (peak curves, comparison tables)
4. **批次历史 (Batch History)** - List **all historical** batches (filter by status, click to view results)

**Issues**:
- "进度" and "批次历史" have overlapping responsibilities
- "进度" lacks batch selection (assumes only one batch runs at a time)
- "批次历史" doesn't show execution details (only final status)
- Users cannot view historical execution logs (which tasks ran when, how long each took)

### Desired Behavior

**3 Tabs**:
1. **配置 (Config)** - Create batch simulations (unchanged)
2. **批次监控 (Batch Monitoring)** - Unified batch list + expandable details:
   - **List View**: All batches (running, completed, failed, cancelled) with status filter
   - **Running Batch Details**: Real-time task list, progress bar, live curves
   - **Completed Batch Details**: Execution history (task timeline, duration, logs)
   - **Action Buttons**: "查看结果" (jump to Results tab), "删除批次"
3. **结果 (Results)** - Simple batch results (summary.xml-based task analysis, peak vehicle curves) (unchanged)

**Note**: Advanced optimization analysis is handled in a separate "方案优化 (Plan Optimization)" page, not in scope for this change.

---

## What Changes

- Merge two separate tabs ("进度 (Progress)" and "批次历史 (Batch History)") into single "批次监控 (Batch Monitoring)" tab
- Reduce total tab count from 4 to 3 (配置, 批次监控, 结果)
- Implement expandable batch cards: collapsed view (120px) → expanded view (600-700px)
- Show all batch states in unified list: running, completed, failed, cancelled
- Running batches: real-time task status + live vehicle curve (auto-update every 10s)
- Completed batches: execution timeline + peak vehicle curve preview + "查看结果" button
- Failed batches: error logs + "重新运行" button
- Add status filter (全部|运行中|已完成|失败|已取消) and sort options (创建时间|完成时间|耗时)
- Mobile responsive: 1 card/row on mobile, modal dialog for expanded view (<768px)
- Preserve Results tab as independent summary results view (summary.xml-based analysis)
- Maintain backward compatibility with existing batch data and APIs

**Out of Scope**: Advanced optimization analysis (handled in separate "方案优化" page)

**Impact**:
- Affected spec: `batch-management` (modified batch history view requirements)
- Affected spec: `batch-simulation-charts` (modified live curve integration context)
- New spec: `batch-monitoring-unified` (unified monitoring capability)

---

## Proposed Solution

### Capability: Unified Batch Monitoring UI

**Scope**: Merge "进度" and "批次历史" tabs into a single "批次监控" tab with two-level hierarchy (list + details).

**Key Features**:

#### 1. Batch List View (Default)
- Display all batches as cards in grid layout (similar to current "批次历史")
- Status badge: 运行中 ⏳ | 已完成 ✓ | 失败 ✗ | 已取消 ❌
- Key metrics on card: batch_id, case_name, plan_count, created_at, duration
- Running batches show real-time progress bar (e.g., "5/9 tasks completed")
- Status filter: 全部 | 运行中 | 已完成 | 失败 | 已取消
- Sort options: 最近创建 | 最近完成 | 耗时最长

#### 2. Expandable Batch Details (Click on Card)
Clicking a batch card expands it to show details **in-place** (no tab switch):

**For Running Batches**:
- Real-time task list with status indicators (pending, running, completed, failed)
- Live progress bar with estimated completion time
- Real-time vehicle count curve (live update every 10s)
- Action buttons: "取消批次", "刷新"

**For Completed Batches**:
- Execution timeline: Task start/end times, duration, final status
- Summary metrics: Total duration, success rate (e.g., 9/9 tasks succeeded)
- Peak vehicle curve (static snapshot, not live)
- Action buttons: "查看结果" (jump to Results tab), "删除批次"

**For Failed/Cancelled Batches**:
- Execution timeline showing which tasks failed/were cancelled
- Error logs (if available)
- Action buttons: "重新运行", "删除批次"

#### 3. Results Tab Integration
- Clicking "查看详细结果" button in batch details → switches to "结果" tab
- "结果" tab auto-loads the selected batch's results
- "结果" tab remains independent for deep analysis (comparison tables, optimization insights)

---

## Benefits

### User Experience
- ✅ **Single source of truth**: All batches visible in one place
- ✅ **Reduced cognitive load**: No need to remember which tab shows what
- ✅ **Faster navigation**: 1 click to expand batch details vs. 2 clicks (tab switch + card click)
- ✅ **Historical execution visibility**: See when tasks ran, how long they took (currently unavailable)
- ✅ **Clearer workflow**: Config → Monitor → Results (3 steps instead of 4)

### Technical Benefits
- ✅ **Code reuse**: Merge duplicate batch rendering logic from "进度" and "批次历史"
- ✅ **Simplified state management**: Single `currentBatchId` context instead of separate states
- ✅ **Better data consistency**: Single API call pattern for batch data
- ✅ **Easier maintenance**: Fewer components, clearer responsibilities

### Design Alignment
- ✅ **Follows industry patterns**: GitHub Actions, CI/CD systems use unified job history + expandable details
- ✅ **Progressive disclosure**: Start with overview, expand for details, jump to summary results
- ✅ **Responsive layout**: Card grid adapts to screen size, details expand smoothly

---

## Scope

### In Scope

**Frontend Changes**:
- Merge `progressView` and `historyView` into new `monitoringView`
- Redesign batch card component with expandable details
- Implement two-state rendering: list view vs. expanded details view
- Add execution timeline component for completed batches
- Update tab navigation (remove "进度" and "批次历史", add "批次监控")
- Preserve live curve functionality for running batches
- Add "查看结果" button that switches to Results tab

**Files Modified**:
- `frontend/control/simulations.html` - Tab structure and view containers
- `frontend/control/js/batch_simulation.js` - Merge progress/history logic, add expandable card logic
- `frontend/control/css/simulations.css` - New styles for unified monitoring view

### Out of Scope

- Backend API changes (existing APIs support all required data)
- Results tab modifications (remains independent, summary.xml-based)
- Config tab modifications (unchanged)
- New data sources or analysis features
- **Advanced optimization analysis** (handled in separate "方案优化 (Plan Optimization)" page, not part of batch simulation page)

---

## Design Decisions

### Why Keep Results Tab Separate?

**Reasoning**:
- Results tab serves a different purpose: **simple summary analysis** (summary.xml) vs. **real-time monitoring**
- Results require dedicated space for peak curves and task comparison tables
- Results tab shows consolidated view across all tasks in a batch
- Clear separation between monitoring (live data) and results (post-execution analysis)

**Note**: Advanced optimization analysis (deep comparisons, optimization recommendations) is handled in the separate "方案优化 (Plan Optimization)" page, not in the batch simulation Results tab.

**Alternative Considered**: Embed results directly in expanded batch details
- **Rejected**: Would make batch cards too large, reduce list view usability

### Why Expandable Cards Instead of Modal/Sidebar?

**Reasoning**:
- **Contextual**: Details appear inline, preserving list context
- **Faster**: No modal loading delay, no overlay to close
- **Familiar**: Common pattern in modern UIs (GitHub issues, Jira tickets)

**Alternative Considered**: Modal dialog for batch details
- **Rejected**: Modals hide the list, make comparison harder, require extra clicks to close

### Why Show Historical Execution Timeline?

**Reasoning**:
- **User request**: Users want to see "执行进度和完成情况" (execution progress and completion status)
- **Debugging**: Identify which tasks are slow, which failed
- **Audit trail**: Understand batch execution history for reporting

**Data Source**: Already available in `batch_metadata.json` and `batch_progress.json`

---

## Success Criteria

### Functional Acceptance

**AC1: Unified Batch List Displays All Batches**
- [ ] Navigate to "批次监控" tab
- [ ] **Expected**: See all batches (running, completed, failed, cancelled)
- [ ] **Expected**: Running batches show real-time progress (e.g., "5/9 tasks")
- [ ] **Expected**: Status filter works (filter by running/completed/failed/cancelled)

**AC2: Running Batch Details Show Live Monitoring**
- [ ] Click on a running batch card
- [ ] **Expected**: Card expands to show task list with real-time status
- [ ] **Expected**: Live progress bar updates automatically
- [ ] **Expected**: Live vehicle curve displays and updates every 10s
- [ ] **Expected**: "取消批次" button visible and functional

**AC3: Completed Batch Details Show Execution History**
- [ ] Click on a completed batch card
- [ ] **Expected**: Card expands to show execution timeline (task start/end times, durations)
- [ ] **Expected**: Summary metrics displayed (total duration, success rate)
- [ ] **Expected**: Peak vehicle curve displayed (static snapshot)
- [ ] **Expected**: "查看结果" button visible

**AC4: Results Tab Integration Works**
- [ ] Click "查看结果" button in expanded completed batch
- [ ] **Expected**: Tab switches to "结果" tab
- [ ] **Expected**: Results tab loads the selected batch's data
- [ ] **Expected**: Peak curve and comparison table display correctly

**AC5: Failed Batch Details Show Error Information**
- [ ] Click on a failed batch card (if exists)
- [ ] **Expected**: Card expands to show which tasks failed
- [ ] **Expected**: Error logs displayed (if available)
- [ ] **Expected**: "重新运行" and "删除批次" buttons visible

### UX Acceptance

**UX1: Navigation is Intuitive**
- [ ] User can find batch monitoring without confusion
- [ ] User understands how to expand/collapse batch cards
- [ ] User can easily jump from monitoring to results

**UX2: Performance is Acceptable**
- [ ] Batch list loads within 1 second for 50 batches
- [ ] Card expansion animates smoothly (<300ms)
- [ ] Live curve updates do not cause UI lag

### Technical Acceptance

**TA1: Code Deduplication**
- [ ] No duplicate batch rendering logic between old "进度" and "批次历史"
- [ ] Shared components for batch cards, task lists, progress bars

**TA2: State Management**
- [ ] Single `currentBatchId` tracks selected batch
- [ ] Single API call pattern for batch data (no redundant calls)

---

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Users confused by 3-tab structure (expect 4) | Low | Low | Add tooltip: "批次监控整合了进度和历史功能" |
| Expandable cards don't fit mobile screens | Medium | Medium | Use responsive breakpoints, collapse to modal on <768px |
| Live curve update breaks after tab merge | Low | High | Thorough testing, preserve existing polling logic |
| Users miss the Results tab (expect results in monitoring) | Medium | Low | Prominent "查看结果" button, clear visual separation |

---

## Implementation Phases

### Phase 1: Frontend Structure Refactoring (4-6 hours)

**Tasks**:
1. Create new `monitoringView` container in `simulations.html`
2. Remove `progressView` and `historyView` containers
3. Update tab navigation (3 tabs instead of 4)
4. Merge batch list rendering logic into unified component
5. Add expandable card component (list state + expanded state)

**Validation**: Tab structure renders correctly, no console errors

### Phase 2: Batch Details Implementation (6-8 hours)

**Tasks**:
1. Implement expandable card logic (click to expand/collapse)
2. Render running batch details (task list, progress bar, live curve)
3. Render completed batch details (execution timeline, peak curve)
4. Render failed batch details (error logs)
5. Add "查看结果" button and tab switch logic

**Validation**: All batch states render correctly, expansion/collapse smooth

### Phase 3: Live Monitoring Integration (4-6 hours)

**Tasks**:
1. Preserve live curve polling logic from old "进度" tab
2. Ensure live updates work in expanded card context
3. Add auto-refresh for task list in running batches
4. Test concurrent batch monitoring (if applicable)

**Validation**: Live curves update correctly, task status refreshes in real-time

### Phase 4: Styling and Polish (3-4 hours)

**Tasks**:
1. Refine CSS for unified monitoring view
2. Add smooth expand/collapse animations
3. Ensure responsive layout (desktop, tablet, mobile)
4. Polish status badges, icons, button styles

**Validation**: UI looks polished, animations smooth, mobile responsive

### Phase 5: Testing and Bug Fixes (4-6 hours)

**Tasks**:
1. Test all batch states (pending, running, completed, failed, cancelled)
2. Test status filters and sorting
3. Test Results tab integration
4. Cross-browser testing (Chrome, Edge, Firefox)
5. Fix any bugs found

**Validation**: All acceptance criteria met, no critical bugs

---

## Time Estimate

| Phase | Development | Testing | Total |
|-------|------------|---------|-------|
| Phase 1: Structure Refactoring | 4-6h | 1h | 5-7h |
| Phase 2: Batch Details | 6-8h | 2h | 8-10h |
| Phase 3: Live Monitoring | 4-6h | 2h | 6-8h |
| Phase 4: Styling | 3-4h | 1h | 4-5h |
| Phase 5: Testing & Fixes | 2h | 4-6h | 6-8h |
| **Total** | **19-26h** | **10-12h** | **29-38h** |

**Estimated Duration**: 4-5 working days

---

## Dependencies

### Prerequisites
- ✅ `fix-batch-history-data-display` change must be completed first (fixes `currentCaseId` bug)
- ✅ All batch-optimization APIs already implemented
- ✅ Live curve functionality already working

### Blocking Issues
- ⚠️ `fix-batch-history-data-display` proposal must be approved and implemented first

### Related Changes
- Builds on archived changes:
  - `implement-plan-management-and-batch-optimization`
  - `enhance-batch-simulation-monitoring`
  - `fix-batch-simulation-chart-issues`
- Depends on active change:
  - `fix-batch-history-data-display` (must complete first)

---

## Alternatives Considered

### Alternative 1: Keep 4 Tabs, Only Improve UX

**Description**: Keep separate "进度" and "批次历史" tabs, but improve navigation between them.

**Pros**: Lower risk, less code change
**Cons**: Doesn't address root issue (tab fragmentation), users still confused

**Decision**: Rejected - doesn't solve the fundamental UX problem

### Alternative 2: Merge All 3 Tabs into One "Batch Management"

**Description**: Merge "配置", "进度", and "批次历史" into a single mega-tab.

**Pros**: Maximum simplification
**Cons**: Too crowded, mixes creation and monitoring concerns

**Decision**: Rejected - violates separation of concerns (creation vs. monitoring)

### Alternative 3: Use Modal Dialogs for Batch Details

**Description**: Keep list view in main tab, show details in modal dialog.

**Pros**: Familiar pattern, saves screen space
**Cons**: Modals hide list context, require extra clicks to close, feel clunky

**Decision**: Rejected - expandable cards provide better UX (inline, contextual)

---

## References

- **User Requirements**: Clarifying questions answered 2025-11-02
- **Current Implementation**:
  - `frontend/control/simulations.html` - 4-tab structure
  - `frontend/control/js/batch_simulation.js` - Progress and history logic
- **Related Specs**:
  - `openspec/specs/batch-management/spec.md` - Batch history requirements
  - `openspec/specs/batch-simulation-charts/spec.md` - Live curve requirements
- **Design Inspiration**:
  - GitHub Actions workflow runs (list + expandable details)
  - GitLab CI/CD pipeline history
  - JIRA issue list with inline expansion

---

## Approval

**Stakeholders**: Development Team, Product Owner, UX Designer

**Approval Required**: Yes (impacts core user workflow)

**Approval Status**: Pending Review

---

## Open Questions

1. Should we add bulk actions (e.g., "delete all completed batches")?
   - **Decision Deferred**: Not in initial scope, can add in future iteration

2. Should we show multiple running batches simultaneously?
   - **Answer**: Yes, if multiple batches exist, show all in list with expand capability

3. Should we persist expanded/collapsed state in localStorage?
   - **Decision Deferred**: Not in initial scope, collapse all on page reload for now

4. Should we add batch comparison mode (select 2+ batches, compare results)?
   - **Decision Deferred**: Results tab already supports multi-batch comparison, not needed in monitoring view

---

## 📊 Implementation Status (2025-11-02)

### ✅ Completed

**Phase 1: Frontend Structure Refactoring** (~3-4 hours)
- 3-tab navigation structure (配置 → 批次监控 → 结果)
- Two-panel monitoring view HTML structure (上栏监控 + 下栏列表)
- CSS updates for two-panel layout
- JavaScript state management for 3 tabs
- Null-safety fixes for removed elements

**Phase 1.5: Batch Control & Progress Monitoring** (~2 hours)
- Batch card control buttons (启动/取消/监控进度/查看结果/删除)
- `startBatchById()`, `cancelBatchById()`, `closeCurrentMonitor()` functions
- Upper panel progress monitoring integration
- Real-time polling with live vehicle count curve
- Updated `updateProgress()` and `renderLiveCurve()` for monitor elements

**Key Achievement**:
- Fully restored original "进度" tab functionality within the unified monitoring view
- Two-panel layout addresses user feedback: "批次监控和正在监看的运行的批次可以分上下两栏"
- Users can now start/monitor/cancel batches directly from batch cards
- Real-time progress monitoring works in upper panel while browsing batch list below

### ⏸️ Deferred (Future Enhancements)

**Phase 2-8**: Expandable cards, advanced filtering, responsive design, testing
- Not critical for MVP functionality
- Can be implemented incrementally based on user feedback
- Current implementation uses simple two-panel layout instead of expandable cards
  - Upper panel: Shows detailed monitoring when "监控进度" clicked
  - Lower panel: Always shows batch list
  - Simpler implementation, same functionality

### 📝 Actual Design Changes

**Original Proposal**: Expandable batch cards (click card → expands inline to show details)

**Actual Implementation**: Two-panel layout (上下两栏)
- Upper panel (`currentBatchMonitor`): Hidden by default, shows when "监控进度" clicked
- Lower panel (`batch-list-section`): Always visible, shows all batches
- **Rationale**: User feedback indicated preference for traditional upper/lower separation vs. inline expansion
- **Benefit**: Matches original UI paradigm, easier to understand

**Files Modified**:
- `frontend/control/simulations.html` - Two-panel HTML structure
- `frontend/control/css/simulations.css` - Panel styles, button styles
- `frontend/control/js/batch_simulation.js` - View switching, batch controls, progress monitoring
