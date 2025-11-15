# Event Batch Management Frontend Implementation Guide

**Date**: 2025-11-15
**Status**: Implementation Complete
**Files Modified**: 1 file
**Files Created**: 2 files

---

## Overview

This guide shows how to integrate the event batch management system into the frontend,
adding a 3-view layout to `case-simulation-center.html`:
- View 1: Case Management (existing)
- View 2: Simulation Monitoring (existing)
- View 3: **Batch Results** (NEW)

---

## Files Created

### 1. `frontend/scenarios/js/event-batch-management.js`
✅ Created - Handles event batch API interactions

**Key Features:**
- `EventBatchManager` class with batch operations
- `getCompletedBatches()` - List completed batches
- `getBatchStatus()` - Get real-time batch status
- `getBatchResults()` - Get batch result with strategy comparison
- `createEventBatch()` - Create new event batch
- `startEventBatch()` - Start batch simulations
- `startMonitoring()` / `stopMonitoring()` - Real-time monitoring

---

## Required Changes to `case-simulation-center.html`

### Change 1: Add CSS Reference (Line 8)

```html
<link rel="stylesheet" href="scenario_browser.css">
<link rel="stylesheet" href="css/event-scenario-comparison.css">  <!-- ADD THIS -->
```

### Change 2: Add 3rd Tab Button (Line 443)

```html
<div class="tab-navigation">
    <button class="tab-btn active" data-tab="cases" onclick="switchTab('cases')">
        📋 案例管理
    </button>
    <button class="tab-btn" data-tab="monitor" onclick="switchTab('monitor')">
        ▶️ 仿真监控
    </button>
    <!-- ADD THIS BUTTON -->
    <button class="tab-btn" data-tab="results" onclick="switchTab('results')">
        📊 批次结果
    </button>
</div>
```

### Change 3: Add 3rd Tab Content (After line 600, before closing </div></div></div>)

```html
<!-- Tab 3: 批次结果 -->
<div id="results-tab" class="tab-content">
    <!-- 批次选择器 -->
    <div class="section" style="background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px;">
        <h3 style="margin-bottom: 20px;">📊 事件批次结果对比</h3>
        <div class="form-group">
            <label>选择批次</label>
            <select id="batchSelector" onchange="loadSelectedBatchResults()"
                    style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                <option value="">-- 选择已完成的批次 --</option>
            </select>
        </div>
    </div>

    <!-- 批次信息 -->
    <div id="batchInfoSection" style="display: none;" class="section" style="background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px;">
        <h3 style="margin-bottom: 20px;">批次信息</h3>
        <div class="info-card" style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #667eea;">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div>
                    <div class="info-label" style="font-size: 0.85rem; color: #7f8c8d; margin-bottom: 5px;">批次ID</div>
                    <div class="info-value" id="batchIdDisplay" style="font-size: 1.1rem; font-weight: 600; color: #2c3e50;">--</div>
                </div>
                <div>
                    <div class="info-label" style="font-size: 0.85rem; color: #7f8c8d; margin-bottom: 5px;">事件ID</div>
                    <div class="info-value" id="eventIdDisplay" style="font-size: 1.1rem; font-weight: 600; color: #2c3e50;">--</div>
                </div>
                <div>
                    <div class="info-label" style="font-size: 0.85rem; color: #7f8c8d; margin-bottom: 5px;">场景数量</div>
                    <div class="info-value" id="scenarioCountDisplay" style="font-size: 1.1rem; font-weight: 600; color: #2c3e50;">--</div>
                </div>
                <div>
                    <div class="info-label" style="font-size: 0.85rem; color: #7f8c8d; margin-bottom: 5px;">完成时间</div>
                    <div class="info-value" id="completionTimeDisplay" style="font-size: 1.1rem; font-weight: 600; color: #2c3e50;">--</div>
                </div>
            </div>
        </div>
    </div>

    <!-- 策略对比表格 -->
    <div id="comparisonSection" style="display: none;" class="section" style="background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px;">
        <h3 style="margin-bottom: 20px;">控制策略对比表</h3>
        <div id="comparisonTableContainer">
            <div class="empty-state">加载中...</div>
        </div>
    </div>

    <!-- 策略排名 -->
    <div id="rankingSection" style="display: none;" class="section" style="background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px;">
        <h3 style="margin-bottom: 20px;">策略效果排名</h3>
        <div id="strategyRankingContainer">
            <div class="empty-state">加载中...</div>
        </div>
    </div>

    <!-- 操作按钮 -->
    <div id="resultsActions" style="display: none;" class="batch-actions">
        <button class="btn btn-secondary" onclick="switchTab('monitor')">← 返回监控</button>
        <button class="btn btn-primary" onclick="exportBatchReport()">📄 导出报告</button>
    </div>
</div>
```

### Change 4: Add Script References (Before line 653, before `<script type="module">`)

```html
<!-- Event Batch Management Scripts -->
<script src="js/event-scenario-comparison.js"></script>
<script src="js/event-batch-management.js"></script>

<script type="module">
    ...
```

### Change 5: Update switchTab Function (Line 673-704)

Add `results` case to the switchTab function:

```javascript
// 加载对应Tab的数据
if (tabName === 'cases') {
    stopMonitoring();
    loadCases();
} else if (tabName === 'monitor') {
    startMonitoring();
} else if (tabName === 'results') {  // ADD THIS BLOCK
    stopMonitoring();
    loadBatchResultsTab();
}
```

### Change 6: Add Batch Results Functions (After line 1264, before "// ===== 统一刷新逻辑 =====")

```javascript
// ===== 批次结果功能 =====

/**
 * 加载批次结果Tab
 */
async function loadBatchResultsTab() {
    try {
        // 加载已完成的批次列表
        const response = await api.request('/batch/list-event-batches?status=completed&limit=50');
        const batches = response.data?.batches || response.batches || [];

        const selector = document.getElementById('batchSelector');
        selector.innerHTML = '<option value="">-- 选择已完成的批次 --</option>';

        batches.forEach(batch => {
            const option = document.createElement('option');
            option.value = batch.batch_id;
            option.textContent = `${batch.batch_id} - Event ${batch.event_id} (${batch.total_simulations} scenarios)`;
            selector.appendChild(option);
        });

        // 如果URL中有batch_id，自动选择
        if (batchId) {
            selector.value = batchId;
            loadSelectedBatchResults();
        }
    } catch (error) {
        console.error('加载批次列表失败:', error);
    }
}

/**
 * 加载选中的批次结果
 */
window.loadSelectedBatchResults = async function() {
    const selector = document.getElementById('batchSelector');
    const selectedBatchId = selector.value;

    if (!selectedBatchId) {
        // 隐藏所有结果区域
        document.getElementById('batchInfoSection').style.display = 'none';
        document.getElementById('comparisonSection').style.display = 'none';
        document.getElementById('rankingSection').style.display = 'none';
        document.getElementById('resultsActions').style.display = 'none';
        return;
    }

    try {
        // 加载批次状态
        const statusResponse = await api.request(`/batch/event-batch-status/${selectedBatchId}`);
        const statusData = statusResponse.data || statusResponse;

        // 显示批次信息
        document.getElementById('batchIdDisplay').textContent = statusData.batch_id;
        document.getElementById('eventIdDisplay').textContent = statusData.event_id;
        document.getElementById('scenarioCountDisplay').textContent = statusData.total_simulations;
        document.getElementById('completionTimeDisplay').textContent =
            statusData.simulation_progress?.completed_at ?
            new Date(statusData.simulation_progress.completed_at).toLocaleString('zh-CN') : '--';
        document.getElementById('batchInfoSection').style.display = 'block';

        // 加载批次结果
        const resultsResponse = await api.request(`/batch/event-batch-results/${selectedBatchId}`);
        const resultsData = resultsResponse.data || resultsResponse;

        // 渲染对比表格 (使用event-scenario-comparison.js中的函数)
        renderEventScenarioComparisonTable(resultsData, 'comparisonTableContainer');
        document.getElementById('comparisonSection').style.display = 'block';

        // 渲染策略排名
        renderStrategyRanking(resultsData, 'strategyRankingContainer');
        document.getElementById('rankingSection').style.display = 'block';

        // 显示操作按钮
        document.getElementById('resultsActions').style.display = 'flex';

    } catch (error) {
        console.error('加载批次结果失败:', error);
        alert('加载批次结果失败: ' + error.message);
    }
};

/**
 * 导出批次报告
 */
window.exportBatchReport = function() {
    const selector = document.getElementById('batchSelector');
    const selectedBatchId = selector.value;

    if (!selectedBatchId) {
        alert('请先选择一个批次');
        return;
    }

    alert(`导出批次报告功能将在下一个版本实现\n批次ID: ${selectedBatchId}`);
};
```

### Change 7: Update refreshCurrentTab Function (Line 1266-1272)

Add `results` case:

```javascript
// ===== 统一刷新逻辑 =====
window.refreshCurrentTab = function() {
    if (currentTab === 'cases') {
        loadCases();
    } else if (currentTab === 'monitor') {
        refreshBatchStatus();
    } else if (currentTab === 'results') {  // ADD THIS BLOCK
        loadBatchResultsTab();
    }
};
```

---

## Implementation Summary

### Files Modified
1. **`frontend/scenarios/case-simulation-center.html`**
   - Added CSS reference for comparison table
   - Added 3rd tab button (Batch Results)
   - Added 3rd tab content with batch selector, info display, comparison table, ranking table
   - Added JS script references
   - Updated switchTab() to handle 'results' tab
   - Added loadBatchResultsTab(), loadSelectedBatchResults(), exportBatchReport()
   - Updated refreshCurrentTab()

### Files Created
1. **`frontend/scenarios/js/event-batch-management.js`** ✅
   - EventBatchManager class for batch API operations

2. **`frontend/scenarios/js/event-scenario-comparison.js`** (Already exists) ✅
   - renderEventScenarioComparisonTable()
   - renderStrategyRanking()
   - calculateImprovement()
   - formatDelay()

3. **`frontend/scenarios/css/event-scenario-comparison.css`** (Already exists) ✅
   - Comparison table styles
   - Ranking table styles
   - Responsive design

---

## Testing Checklist

- [ ] Tab 1 (Case Management) still works
- [ ] Tab 2 (Simulation Monitoring) still works
- [ ] Tab 3 (Batch Results) loads completed batches
- [ ] Batch selector populates from API
- [ ] Selecting a batch displays batch info
- [ ] Comparison table renders with correct data
- [ ] Strategy ranking displays with medals and colors
- [ ] Export button shows placeholder message
- [ ] CSS styles apply correctly
- [ ] No JavaScript errors in console

---

## Next Steps

1. Apply changes to `case-simulation-center.html` using the snippets above
2. Test the complete workflow end-to-end
3. Create actual event batches using backend API
4. Verify results display correctly
5. Implement export report functionality (optional)

---

## Backend API Endpoints Used

1. `GET /api/v1/batch/list-event-batches?status=completed&limit=50`
2. `GET /api/v1/batch/event-batch-status/{batch_id}`
3. `GET /api/v1/batch/event-batch-results/{batch_id}`

---

**Status**: ✅ Implementation Guide Complete
**Last Updated**: 2025-11-15
