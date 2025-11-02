# Tasks: Unify Batch Monitoring and History

**Change ID**: `unify-batch-monitoring-and-history`

---

## Prerequisites

- [ ] **BLOCKER**: Complete `fix-batch-history-data-display` change
  - Dependency: `currentCaseId` global variable must exist
  - Dependency: Batch status updates must work correctly
  - Validate: Batch history tab loads correctly in current 4-tab structure

---

## Phase 1: Frontend Structure Refactoring (5-7 hours)

### 1.1 Update Tab Navigation Structure

**File**: `frontend/control/simulations.html`

- [ ] Remove "进度 (Progress)" tab button (line 38)
- [ ] Remove "批次历史 (Batch History)" tab button (line 40)
- [ ] Add new "批次监控 (Batch Monitoring)" tab button:
  ```html
  <button class="view-tab" id="monitoringViewTab" onclick="switchView('monitoring')">批次监控</button>
  ```
- [ ] Reorder tabs: 配置 → 批次监控 → 结果 (3 tabs total)

**Validation**: Tab navigation renders 3 buttons, "批次监控" is second tab

---

### 1.2 Create Unified Monitoring View Container

**File**: `frontend/control/simulations.html`

- [ ] Remove `<div id="progressView">` container (lines 90-150)
- [ ] Remove `<div id="historyView">` container (lines 187-215)
- [ ] Create new `<div id="monitoringView" class="view">` container
- [ ] Add structure:
  ```html
  <div id="monitoringView" class="view">
      <div class="content-header">
          <h2>批次监控</h2>
          <p class="content-subtitle">实时监控和历史回顾批量仿真执行状态</p>
      </div>

      <!-- Filters and Controls -->
      <div class="monitoring-controls">
          <div class="filter-group">
              <label for="statusFilter">状态筛选:</label>
              <select id="statusFilter" onchange="filterBatches()">
                  <option value="">全部状态</option>
                  <option value="running">运行中</option>
                  <option value="completed">已完成</option>
                  <option value="failed">失败</option>
                  <option value="cancelled">已取消</option>
              </select>
          </div>
          <div class="filter-group">
              <label for="sortOrder">排序:</label>
              <select id="sortOrder" onchange="sortBatches()">
                  <option value="created_desc">最近创建</option>
                  <option value="completed_desc">最近完成</option>
                  <option value="duration_desc">耗时最长</option>
              </select>
          </div>
      </div>

      <!-- Batch List -->
      <div id="batchList" class="batch-list">
          <!-- Batch cards dynamically rendered here -->
      </div>

      <!-- Empty State -->
      <div id="batchListEmpty" class="empty-state" style="display: none;">
          <p>暂无批次记录</p>
          <p class="text-muted">请在"配置"标签创建批量仿真</p>
      </div>
  </div>
  ```

**Validation**: New monitoring view container exists, no duplicate IDs

---

### 1.3 Update CSS for Unified Monitoring View

**File**: `frontend/control/css/simulations.css`

- [ ] Rename `.batch-history-list` to `.batch-list`
- [ ] Rename `.batch-history-card` to `.batch-card`
- [ ] Rename `.history-filters` to `.monitoring-controls`
- [ ] Add styles for expandable cards:
  ```css
  .batch-card {
      transition: all 0.25s ease-in-out;
      cursor: pointer;
  }

  .batch-card.expanded {
      cursor: default;
  }

  .batch-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: pointer;
  }

  .batch-card-details {
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.3s ease-in-out;
  }

  .batch-card.expanded .batch-card-details {
      max-height: 1000px; /* Adjust based on content */
  }
  ```
- [ ] Add responsive breakpoints:
  ```css
  @media (min-width: 1200px) {
      .batch-list { grid-template-columns: repeat(4, 1fr); }
  }
  @media (min-width: 768px) and (max-width: 1199px) {
      .batch-list { grid-template-columns: repeat(2, 1fr); }
  }
  @media (max-width: 767px) {
      .batch-list { grid-template-columns: 1fr; }
  }
  ```

**Validation**: Styles apply correctly, grid layout responsive

---

### 1.4 Update JavaScript Global State

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Update `currentView` initialization: `let currentView = 'config';`
- [ ] Add `expandedBatchId` state: `let expandedBatchId = null;`
- [ ] Update `switchView()` function:
  ```javascript
  function switchView(view) {
      // Hide all views
      ['config', 'monitoring', 'results'].forEach(v => {
          document.getElementById(`${v}View`).classList.remove('active');
          document.getElementById(`${v}ViewTab`).classList.remove('active');
      });

      // Show selected view
      document.getElementById(`${view}View`).classList.add('active');
      document.getElementById(`${view}ViewTab`).classList.add('active');
      currentView = view;

      // Load data if needed
      if (view === 'monitoring' && currentCaseId) {
          loadBatchList();
      }
  }
  ```

**Validation**: View switching works for 3 tabs, no console errors

---

## Phase 2: Batch Card Component Implementation (8-10 hours)

### 2.1 Create Batch Card Rendering Function

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Rename `loadBatchHistory()` to `loadBatchList()`
- [ ] Update API call to support all batches (not just historical)
- [ ] Create `renderBatchCard(batch)` function:
  ```javascript
  function renderBatchCard(batch) {
      const isExpanded = expandedBatchId === batch.batch_id;
      const statusClass = getStatusClass(batch.status);
      const statusLabel = getStatusLabel(batch.status);

      return `
          <div class="batch-card ${isExpanded ? 'expanded' : ''}"
               data-batch-id="${batch.batch_id}"
               onclick="toggleBatchCard('${batch.batch_id}')">

              <!-- Card Header (always visible) -->
              <div class="batch-card-header">
                  <div>
                      <h4>${batch.batch_id}</h4>
                      <span class="batch-status ${statusClass}">${statusLabel}</span>
                  </div>
                  ${renderBatchProgress(batch)}
              </div>

              <div class="batch-card-body">
                  <p><strong>案例:</strong> ${batch.case_name || batch.case_id}</p>
                  <p><strong>方案:</strong> ${batch.plan_count}个方案</p>
                  <p><strong>创建于:</strong> ${formatRelativeTime(batch.created_at)}</p>
                  ${batch.duration_seconds ? `<p><strong>耗时:</strong> ${formatDuration(batch.duration_seconds)}</p>` : ''}
              </div>

              <!-- Expandable Details (hidden unless expanded) -->
              <div class="batch-card-details">
                  ${isExpanded ? renderBatchDetails(batch) : ''}
              </div>
          </div>
      `;
  }
  ```

**Validation**: Batch cards render correctly with all metadata

---

### 2.2 Implement Batch Card Expand/Collapse Logic

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Create `toggleBatchCard(batchId)` function:
  ```javascript
  async function toggleBatchCard(batchId) {
      if (expandedBatchId === batchId) {
          // Collapse
          expandedBatchId = null;
          stopBatchPolling(); // Stop live updates if running
      } else {
          // Expand
          expandedBatchId = batchId;
          await loadBatchDetails(batchId);

          // Start live polling if batch is running
          const batch = getBatchById(batchId);
          if (batch && batch.status === 'running') {
              startBatchPolling(batchId);
          }
      }

      // Re-render affected card
      updateBatchCardUI(batchId);
  }
  ```
- [ ] Create `updateBatchCardUI(batchId)` function to update single card without full re-render

**Validation**: Click card to expand, click again to collapse, smooth animation

---

### 2.3 Implement Running Batch Details Rendering

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Create `renderRunningBatchDetails(batch)` function:
  ```javascript
  function renderRunningBatchDetails(batch) {
      return `
          <div class="batch-details-section">
              <h5>实时任务进度</h5>
              <div class="task-list">
                  ${batch.tasks.map(task => renderTaskItem(task)).join('')}
              </div>

              <div class="progress-summary">
                  <p><strong>进度:</strong> ${batch.completed_tasks}/${batch.total_tasks} tasks (${batch.progress_percent}%)</p>
                  ${batch.estimated_completion ? `<p><strong>预计还需:</strong> ${formatDuration(batch.estimated_remaining_seconds)}</p>` : ''}
              </div>

              <!-- Live Vehicle Curve -->
              <div class="live-curve-container">
                  <h5>实时在网车辆数</h5>
                  <canvas id="liveCurve_${batch.batch_id}" class="live-curve-chart"></canvas>
              </div>

              <div class="batch-actions">
                  <button class="btn btn-danger" onclick="cancelBatch('${batch.batch_id}')">取消批次</button>
                  <button class="btn btn-secondary" onclick="refreshBatchDetails('${batch.batch_id}')">刷新</button>
              </div>
          </div>
      `;
  }
  ```
- [ ] Create `renderTaskItem(task)` function for individual task rendering

**Validation**: Running batch shows task list, progress bar, live curve

---

### 2.4 Implement Completed Batch Details Rendering

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Create `renderCompletedBatchDetails(batch)` function:
  ```javascript
  function renderCompletedBatchDetails(batch) {
      return `
          <div class="batch-details-section">
              <h5>执行摘要</h5>
              <div class="summary-metrics">
                  <p>✓ <strong>总耗时:</strong> ${formatDuration(batch.duration_seconds)}</p>
                  <p>✓ <strong>成功率:</strong> ${batch.completed_tasks}/${batch.total_tasks} tasks (${(batch.success_rate * 100).toFixed(1)}%)</p>
                  <p>✓ <strong>平均耗时:</strong> ${formatDuration(batch.avg_task_duration_seconds)}</p>
              </div>

              <h5>执行时间线</h5>
              <div class="execution-timeline">
                  ${renderExecutionTimeline(batch.tasks)}
              </div>

              <!-- Peak Curve Preview -->
              <h5>峰值在网车辆曲线 (预览)</h5>
              <div class="peak-curve-preview">
                  <canvas id="peakCurve_${batch.batch_id}" class="peak-curve-chart"></canvas>
              </div>

              <div class="batch-actions">
                  <button class="btn btn-primary" onclick="viewBatchResults('${batch.batch_id}')">查看详细结果 →</button>
                  <button class="btn btn-danger" onclick="deleteBatch('${batch.batch_id}')">删除批次</button>
              </div>
          </div>
      `;
  }
  ```
- [ ] Create `renderExecutionTimeline(tasks)` function for Gantt-style timeline

**Validation**: Completed batch shows summary metrics, timeline, peak curve preview

---

### 2.5 Implement Failed Batch Details Rendering

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Create `renderFailedBatchDetails(batch)` function:
  ```javascript
  function renderFailedBatchDetails(batch) {
      const failedTasks = batch.tasks.filter(t => t.status === 'failed');

      return `
          <div class="batch-details-section">
              <h5>执行摘要</h5>
              <div class="summary-metrics error">
                  <p>✗ <strong>失败任务:</strong> ${failedTasks.length}/${batch.total_tasks}</p>
                  <p>✓ <strong>成功任务:</strong> ${batch.completed_tasks}/${batch.total_tasks}</p>
                  <p><strong>耗时:</strong> ${formatDuration(batch.duration_seconds)}</p>
              </div>

              <h5>失败任务详情</h5>
              <div class="failed-tasks-list">
                  ${failedTasks.map(task => renderFailedTaskItem(task)).join('')}
              </div>

              <div class="batch-actions">
                  <button class="btn btn-primary" onclick="retryBatch('${batch.batch_id}')">重新运行</button>
                  <button class="btn btn-danger" onclick="deleteBatch('${batch.batch_id}')">删除批次</button>
              </div>
          </div>
      `;
  }
  ```
- [ ] Create `renderFailedTaskItem(task)` function to show error logs

**Validation**: Failed batch shows failed tasks, error messages, retry button

---

## Phase 3: Live Monitoring Integration (6-8 hours)

### 3.1 Preserve Live Curve Polling Logic

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Extract live curve rendering from old `progressView` context
- [ ] Create `initializeLiveCurve(batchId, canvasId)` function
- [ ] Create `updateLiveCurve(batchId, newData)` function
- [ ] Ensure Chart.js instance stored per batch: `liveCurveCharts[batchId]`

**Validation**: Live curve renders in expanded running batch card

---

### 3.2 Implement Batch Details Polling

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Create `startBatchPolling(batchId)` function:
  ```javascript
  function startBatchPolling(batchId) {
      stopBatchPolling(); // Clear any existing interval

      batchPollInterval = setInterval(async () => {
          const batch = await fetchBatchDetails(batchId);

          if (batch.status !== 'running') {
              stopBatchPolling(); // Batch completed/failed
          }

          updateBatchCardUI(batchId, batch); // Update UI
          updateLiveCurve(batchId, batch.live_time_series); // Update curve
      }, 10000); // 10 seconds
  }
  ```
- [ ] Create `stopBatchPolling()` function to clear interval
- [ ] Ensure polling stops when card collapses or tab switches

**Validation**: Running batch updates every 10s, polling stops when completed

---

### 3.3 Implement Task Status Real-Time Updates

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Create `updateTaskListUI(batchId, tasks)` function
- [ ] Update individual task status without full card re-render:
  ```javascript
  function updateTaskStatus(batchId, taskId, newStatus) {
      const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
      if (taskElement) {
          taskElement.className = `task-item ${newStatus}`;
          taskElement.querySelector('.task-status').textContent = getStatusLabel(newStatus);

          if (newStatus === 'completed') {
              const duration = calculateTaskDuration(taskId);
              taskElement.querySelector('.task-duration').textContent = formatDuration(duration);
          }
      }
  }
  ```

**Validation**: Task status updates smoothly without flicker, progress bar updates

---

### 3.4 Handle Batch Completion in Expanded View

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Detect batch completion in polling callback
- [ ] Transform expanded running batch view to completed batch view:
  ```javascript
  async function onBatchCompleted(batchId) {
      stopBatchPolling();

      // Fetch final batch data with results
      const batch = await fetchBatchDetails(batchId);

      // Replace live curve with peak curve
      destroyLiveCurve(batchId);
      renderPeakCurve(batchId, batch.peak_curve_data);

      // Update actions (remove "取消批次", add "查看详细结果")
      updateBatchActions(batchId, 'completed');

      showNotification('批次仿真已完成', 'success');
  }
  ```

**Validation**: Running batch smoothly transitions to completed state when done

---

## Phase 4: Results Tab Integration (4-5 hours)

### 4.1 Implement "查看结果" Button Logic

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Create `viewBatchResults(batchId)` function:
  ```javascript
  async function viewBatchResults(batchId) {
      // Store selected batch ID for Results tab
      currentBatchId = batchId;

      // Switch to Results tab
      switchView('results');

      // Load simple summary results (summary.xml-based)
      await loadBatchResults(batchId);
  }
  ```
- [ ] Ensure `loadBatchResults()` function loads peak curve and task comparison table (summary.xml data)
- [ ] Preserve monitoring view state (keep card expanded in background)

**Note**: Results tab shows simple batch summary. Advanced optimization analysis is in separate "方案优化" page (out of scope).

**Validation**: Click "查看结果" → switches to Results tab, summary data loads correctly

---

### 4.2 Add "查看结果" Quick Action on Collapsed Cards

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Add "查看结果" button to completed batch cards (collapsed state):
  ```html
  <button class="btn btn-small btn-primary" onclick="viewBatchResults('${batch.batch_id}')">查看结果</button>
  ```
- [ ] Ensure button appears only for completed batches

**Validation**: Completed batch cards show "查看结果" button, clicking jumps to Results tab

---

### 4.3 Support Return to Monitoring View from Results

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Ensure switching back to "批次监控" tab preserves expanded card state
- [ ] No need to reload batch list (already in memory)

**Validation**: Results → Monitoring tab switch preserves UI state

---

## Phase 5: Filtering, Sorting, and Utilities (4-5 hours)

### 5.1 Implement Status Filter

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Create `filterBatches()` function:
  ```javascript
  function filterBatches() {
      const status = document.getElementById('statusFilter').value;
      const cards = document.querySelectorAll('.batch-card');

      let visibleCount = 0;
      cards.forEach(card => {
          const cardStatus = card.dataset.status;
          const visible = !status || cardStatus === status;
          card.style.display = visible ? 'block' : 'none';
          if (visible) visibleCount++;
      });

      // Show empty state if no batches match filter
      document.getElementById('batchListEmpty').style.display = visibleCount === 0 ? 'block' : 'none';
  }
  ```

**Validation**: Filter dropdown works, shows only matching batches

---

### 5.2 Implement Sort Order

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Create `sortBatches()` function:
  ```javascript
  function sortBatches() {
      const sortOrder = document.getElementById('sortOrder').value;
      const batchList = document.getElementById('batchList');
      const cards = Array.from(batchList.querySelectorAll('.batch-card'));

      cards.sort((a, b) => {
          const batchA = getBatchDataFromCard(a);
          const batchB = getBatchDataFromCard(b);

          switch (sortOrder) {
              case 'created_desc':
                  return new Date(batchB.created_at) - new Date(batchA.created_at);
              case 'completed_desc':
                  return new Date(batchB.completed_at || 0) - new Date(batchA.completed_at || 0);
              case 'duration_desc':
                  return (batchB.duration_seconds || 0) - (batchA.duration_seconds || 0);
              default:
                  return 0;
          }
      });

      // Re-append cards in sorted order
      cards.forEach(card => batchList.appendChild(card));
  }
  ```

**Validation**: Sort dropdown works, batches reorder correctly

---

### 5.3 Implement Execution Timeline Visualization

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Create `renderExecutionTimeline(tasks)` function using HTML/CSS (no chart library):
  ```javascript
  function renderExecutionTimeline(tasks) {
      const sortedTasks = tasks.sort((a, b) => new Date(a.started_at) - new Date(b.started_at));
      const minTime = new Date(sortedTasks[0].started_at).getTime();
      const maxTime = Math.max(...tasks.map(t => new Date(t.completed_at || Date.now()).getTime()));
      const totalDuration = maxTime - minTime;

      return sortedTasks.map(task => {
          const start = new Date(task.started_at).getTime();
          const end = new Date(task.completed_at || Date.now()).getTime();
          const offset = ((start - minTime) / totalDuration * 100).toFixed(2);
          const width = ((end - start) / totalDuration * 100).toFixed(2);
          const statusClass = task.status === 'completed' ? 'success' : 'failed';

          return `
              <div class="timeline-row">
                  <span class="timeline-label">${task.task_id}</span>
                  <div class="timeline-bar-container">
                      <div class="timeline-bar ${statusClass}"
                           style="margin-left: ${offset}%; width: ${width}%;">
                          ${formatDuration((end - start) / 1000)}
                      </div>
                  </div>
              </div>
          `;
      }).join('');
  }
  ```
- [ ] Add CSS for timeline bars:
  ```css
  .timeline-row {
      display: flex;
      align-items: center;
      margin-bottom: 8px;
  }

  .timeline-bar-container {
      flex: 1;
      height: 24px;
      background: #f0f0f0;
      border-radius: 4px;
      position: relative;
  }

  .timeline-bar {
      height: 100%;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 12px;
  }

  .timeline-bar.success { background: #43A047; }
  .timeline-bar.failed { background: #E53935; }
  ```

**Validation**: Execution timeline displays Gantt-style bars with durations

---

### 5.4 Implement Utility Functions

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Create `formatRelativeTime(timestamp)` function:
  ```javascript
  function formatRelativeTime(timestamp) {
      const now = Date.now();
      const diff = now - new Date(timestamp).getTime();
      const minutes = Math.floor(diff / 60000);
      const hours = Math.floor(minutes / 60);
      const days = Math.floor(hours / 24);

      if (days > 0) return `${days}天前`;
      if (hours > 0) return `${hours}小时前`;
      if (minutes > 0) return `${minutes}分钟前`;
      return '刚刚';
  }
  ```
- [ ] Create `formatDuration(seconds)` function:
  ```javascript
  function formatDuration(seconds) {
      const h = Math.floor(seconds / 3600);
      const m = Math.floor((seconds % 3600) / 60);
      const s = Math.floor(seconds % 60);

      if (h > 0) return `${h}小时${m}分${s}秒`;
      if (m > 0) return `${m}分${s}秒`;
      return `${s}秒`;
  }
  ```

**Validation**: Timestamps and durations display correctly in human-readable format

---

## Phase 6: Responsive Design and Mobile Support (4-5 hours)

### 6.1 Implement Mobile Modal for Expanded View

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Detect screen width in `toggleBatchCard()`:
  ```javascript
  async function toggleBatchCard(batchId) {
      const isMobile = window.innerWidth < 768;

      if (isMobile && expandedBatchId !== batchId) {
          // Open modal instead of inline expansion
          openBatchDetailsModal(batchId);
      } else {
          // Normal inline expand/collapse
          // ... (existing logic)
      }
  }
  ```
- [ ] Create `openBatchDetailsModal(batchId)` function:
  ```javascript
  function openBatchDetailsModal(batchId) {
      const batch = getBatchById(batchId);
      const modalHTML = `
          <div class="modal-overlay" onclick="closeBatchDetailsModal()">
              <div class="modal-dialog" onclick="event.stopPropagation()">
                  <div class="modal-header">
                      <h4>${batch.batch_id}</h4>
                      <button class="modal-close" onclick="closeBatchDetailsModal()">×</button>
                  </div>
                  <div class="modal-body">
                      ${renderBatchDetails(batch)}
                  </div>
              </div>
          </div>
      `;
      document.body.insertAdjacentHTML('beforeend', modalHTML);
  }
  ```

**Validation**: On mobile (<768px), clicking card opens modal dialog

---

### 6.2 Add CSS for Mobile Modal

**File**: `frontend/control/css/simulations.css`

- [ ] Add modal styles:
  ```css
  .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.5);
      z-index: 1000;
      display: flex;
      align-items: center;
      justify-content: center;
  }

  .modal-dialog {
      background: white;
      border-radius: 8px;
      max-width: 90%;
      max-height: 90%;
      overflow-y: auto;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  }

  .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 15px;
      border-bottom: 1px solid #e0e0e0;
  }

  .modal-close {
      background: none;
      border: none;
      font-size: 28px;
      cursor: pointer;
      color: #757575;
  }

  .modal-body {
      padding: 20px;
  }

  @media (min-width: 768px) {
      .modal-overlay { display: none !important; } /* Modals only on mobile */
  }
  ```

**Validation**: Modal displays correctly on mobile, scrollable, close button works

---

### 6.3 Test Responsive Breakpoints

- [ ] Test on desktop (1920px): 4 cards per row
- [ ] Test on laptop (1366px): 3 cards per row
- [ ] Test on tablet (1024px): 2 cards per row
- [ ] Test on mobile (375px): 1 card per row, modal expansion
- [ ] Ensure charts resize correctly in all viewports

**Validation**: Layout adapts smoothly across all screen sizes

---

## Phase 7: Testing and Bug Fixes (6-8 hours)

### 7.1 Functional Testing

- [ ] **Test AC1**: Unified batch list displays all batches with correct status
- [ ] **Test AC2**: Running batch details show live task list and curve
- [ ] **Test AC3**: Completed batch details show execution timeline and peak curve
- [ ] **Test AC4**: "查看详细结果" button navigates to Results tab and loads data
- [ ] **Test AC5**: Failed batch details show error information and retry button
- [ ] **Test**: Status filter works (filter by running/completed/failed/cancelled)
- [ ] **Test**: Sort order works (created_desc, completed_desc, duration_desc)
- [ ] **Test**: Batch deletion with confirmation dialog
- [ ] **Test**: Live polling updates task status and curve automatically
- [ ] **Test**: Polling stops when batch completes or card collapses

**Validation**: All functional requirements met, no critical bugs

---

### 7.2 Cross-Browser Testing

- [ ] Test on Chrome (latest)
- [ ] Test on Edge (latest)
- [ ] Test on Firefox (latest)
- [ ] Test on Safari (macOS, if available)

**Validation**: Works consistently across all browsers

---

### 7.3 Performance Testing

- [ ] Load batch list with 50 batches → measure load time (should be <1s)
- [ ] Expand/collapse animation → measure duration (should be <300ms)
- [ ] Live curve update → measure CPU usage (should be <5%)
- [ ] Filter/sort operations → measure response time (should be instant)

**Validation**: Performance meets acceptance criteria

---

### 7.4 Bug Fixes and Polish

- [ ] Fix any visual glitches found during testing
- [ ] Ensure smooth animations (no jank)
- [ ] Polish status badges, icons, button styles
- [ ] Add loading indicators where appropriate
- [ ] Handle edge cases (empty data, network errors, etc.)

**Validation**: UI polished, no visual bugs, graceful error handling

---

## Phase 8: Documentation and Cleanup (2-3 hours)

### 8.1 Update Code Comments

**File**: `frontend/control/js/batch_simulation.js`

- [ ] Add JSDoc comments for all new functions
- [ ] Document state management (expandedBatchId, batchPollInterval)
- [ ] Add inline comments for complex logic (timeline calculation, polling)

---

### 8.2 Remove Legacy Code

- [ ] Delete old `progressView` rendering logic
- [ ] Delete old `historyView` rendering logic
- [ ] Remove unused CSS classes
- [ ] Remove unused global variables

**Validation**: No dead code, clean codebase

---

### 8.3 Update User Documentation (if applicable)

- [ ] Update user guide (if exists) to reflect 3-tab structure
- [ ] Add screenshots of new unified monitoring view
- [ ] Document expandable card interaction

---

## Final Validation Checklist

- [ ] All 3 tabs render correctly (配置, 批次监控, 结果)
- [ ] Batch list displays all batches with status badges
- [ ] Status filter and sort work correctly
- [ ] Batch cards expand/collapse smoothly (<300ms)
- [ ] Running batch shows live task list and vehicle curve with auto-update
- [ ] Completed batch shows execution timeline and peak curve
- [ ] Failed batch shows error logs and retry button
- [ ] "查看详细结果" button navigates to Results tab
- [ ] Results tab loads selected batch data correctly
- [ ] Mobile responsive (grid adapts, modal expansion on <768px)
- [ ] No console errors
- [ ] No visual bugs or glitches
- [ ] Performance acceptable (list loads <1s for 50 batches)
- [ ] Cross-browser compatible (Chrome, Edge, Firefox)

---

## Dependencies

- **BLOCKER**: `fix-batch-history-data-display` must be completed first
- **Required**: All batch-optimization APIs functional
- **Required**: Live curve functionality working

---

## Estimated Total Time

| Phase | Hours |
|-------|-------|
| Phase 1: Structure Refactoring | 5-7 |
| Phase 2: Batch Card Component | 8-10 |
| Phase 3: Live Monitoring | 6-8 |
| Phase 4: Results Integration | 4-5 |
| Phase 5: Filtering & Utilities | 4-5 |
| Phase 6: Responsive Design | 4-5 |
| Phase 7: Testing & Bugs | 6-8 |
| Phase 8: Documentation | 2-3 |
| **Total** | **39-51 hours** |

**Estimated Duration**: 5-7 working days
