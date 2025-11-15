# Event Scenario Simulation Integration - Enhancement Plan

## Context

Based on the existing implementation review, we have:
- ✅ **case-simulation-center.html** with 3 tabs (Cases, Monitoring, Analysis)
- ✅ **analysis_viewer.html** with 4 analysis tabs (Summary, EdgeData, Comparison, Detail)
- ✅ Backend services for analysis orchestration and results aggregation
- ✅ Real-time simulation monitoring with batch progress tracking

## User Requirements (from `/openspec:apply` command)

> 该change过程中对批量场景生成，sumocfg的正确配置进行了修正；后面继续实现剩下的两个页面: 场景案例管理和影响分析。请结合批量场景创建的逻辑，对这两个页面的设计进行同步修改，目标时最终对事件进行多场景的分析。注意，为保证快速实现，请参考control/optimization.html 批次监控部分的后端和前端组件，以及结果和方案优化分析页的结果分析的后端和前端组件（场景仿真中使用summary.xml edgedata.xml进行分析），但不要破坏原有功能，保持向后兼容。

## Analysis

The user wants:
1. ✅ **Scenario Case Management page** - Already implemented (case-simulation-center.html)
2. ✅ **Impact Analysis page** - Already implemented (analysis_viewer.html)
3. ⏳ **Batch scenario generation integration** - Needs enhancement
4. ⏳ **Multi-scenario analysis** - Needs implementation
5. ⏳ **summary.xml + edgedata.xml visualization** - Partially implemented, needs enhancement
6. ✅ **Reuse control/optimization.html patterns** - Already done
7. ✅ **Backward compatibility** - Maintained

## Enhancement Focus Areas

### 1. Multi-Scenario Analysis Integration

**Problem:** Current implementation analyzes single batches. User wants to analyze multiple scenarios of the same event (e.g., Event 8210655 with NO_CONTROL, VSS, TEC strategies).

**Solution:**
- Enhance AnalysisResultsService to group scenarios by event_id
- Add API endpoint: `/api/v1/analysis/multi-scenario-comparison`
- Integrate into analysis tab with strategy comparison charts

### 2. Batch Scenario-to-Analysis Workflow

**Problem:** Batch scenario generation exists, but workflow from scenarios → cases → simulations → analysis is not seamless.

**Solution:**
- Add "Batch Create Cases from Scenarios" button in case-simulation-center.html Tab 1
- Enhance batch simulation monitoring to support scenario groups
- Auto-trigger analysis when all scenarios' simulations complete

### 3. Summary.xml + EdgeData.xml Visualization Enhancement

**Problem:** Current EdgeData visualization shows top 10 congested roads. Need comprehensive summary.xml metrics and edgedata.xml comparison across strategies.

**Solution:**
- Add SummaryMetrics component (total vehicles, avg speed, throughput)
- Add EdgeData comparison table (baseline vs VSS vs TEC vs DHS)
- Integrate Chart.js for visual comparisons (bar charts, line charts)

## Implementation Tasks

### Backend Enhancements

#### Task B1: Multi-Scenario Comparison API
```python
# api/routes/analysis_routes.py
@router.post("/multi-scenario-comparison")
async def create_multi_scenario_comparison(request: MultiScenarioComparisonRequest):
    """
    Create comparison analysis across multiple scenarios (same event, different strategies)

    Request:
        event_id: str
        scenario_ids: List[str]  # e.g., ["scenario_8210655_no_control", "scenario_8210655_vss", "scenario_8210655_tec"]
        analysis_types: List[str] = ["summary", "edgedata"]

    Response:
        comparison_batch_id: str
        baseline_scenario: str  # NO_CONTROL scenario
        comparison_scenarios: List[str]  # [VSS, TEC, DHS]
    """
```

#### Task B2: Enhance AnalysisResultsService
```python
# api/services/analysis_results_service.py
async def get_multi_scenario_comparison(
    self,
    event_id: str,
    scenario_ids: List[str]
) -> MultiScenarioComparisonResponse:
    """
    Compare multiple scenarios of the same event

    Process:
    1. Group scenarios by strategy type (NO_CONTROL, VSS, TEC, DHS)
    2. Aggregate summary.xml metrics for each strategy
    3. Aggregate edgedata.xml metrics for event-affected edges
    4. Calculate improvement percentages relative to NO_CONTROL baseline
    5. Rank strategies by effectiveness
    """
```

#### Task B3: Batch History API
```python
# api/routes/simulation_routes.py
@router.get("/batch-history")
async def get_batch_history(
    status: Optional[str] = None,  # completed, running, failed
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50
) -> BatchHistoryResponse:
    """
    Get batch simulation history with analysis results

    Returns:
        batches: List[BatchHistoryItem]
            - batch_id
            - created_at
            - total_simulations
            - completed_simulations
            - analysis_batch_id (if analysis ran)
            - event_ids (list of events in this batch)
    """
```

### Frontend Enhancements

#### Task F1: Add Batch Case Creation Modal (case-simulation-center.html Tab 1)
```html
<!-- New button in Tab 1 -->
<button class="btn btn-primary" onclick="openBatchCaseCreationModal()">
    📋 批量创建案例
</button>

<!-- Modal for batch case creation -->
<div id="batchCaseCreationModal" class="modal">
    <div class="modal-content">
        <h3>批量创建案例</h3>

        <!-- Step 1: Select event or scenarios -->
        <div class="form-group">
            <label>选择事件或场景</label>
            <select id="eventSelector" onchange="loadScenariosByEvent()">
                <option value="">-- 选择事件 --</option>
                <!-- Populated from scenario_index.json, grouped by event_id -->
            </select>
        </div>

        <!-- Step 2: Select strategies -->
        <div class="form-group">
            <label>选择策略</label>
            <div class="checkbox-group">
                <label><input type="checkbox" value="no_control" checked disabled> NO_CONTROL (基线)</label>
                <label><input type="checkbox" value="vss"> VSS</label>
                <label><input type="checkbox" value="tec"> TEC</label>
                <label><input type="checkbox" value="dhs"> DHS</label>
            </div>
        </div>

        <!-- Step 3: Preview scenarios -->
        <div class="scenario-preview">
            <h4>将创建的案例:</h4>
            <ul id="scenarioPreviewList">
                <!-- e.g., scenario_8210655_no_control, scenario_8210655_vss, scenario_8210655_tec -->
            </ul>
        </div>

        <!-- Actions -->
        <div class="modal-actions">
            <button class="btn btn-primary" onclick="confirmBatchCaseCreation()">确认创建</button>
            <button class="btn btn-secondary" onclick="closeBatchCaseCreationModal()">取消</button>
        </div>
    </div>
</div>
```

#### Task F2: Enhance Analysis Tab (case-simulation-center.html Tab 3)
```javascript
// Integrate AnalysisResultsViewer component
import { AnalysisResultsViewer } from '../components/analysis-results.js';

let analysisViewer = null;

async function loadAnalysisResults(batchId, caseId) {
    if (!analysisViewer) {
        analysisViewer = new AnalysisResultsViewer('analysisResultsContainer', {
            apiClient: api
        });
    }

    await analysisViewer.loadAnalysisResults(batchId, caseId);
}

// Auto-load when switching to analysis tab
async function switchTab(tabName) {
    // ... existing code ...

    if (tabName === 'analysis') {
        // Check if simulation batch is complete
        if (currentBatchId && batchStatus === 'completed') {
            // Auto-start analysis if not already running
            const analysisStatus = await checkAnalysisStatus(currentBatchId);

            if (!analysisStatus.batch_id) {
                await startBatchAnalysis(currentBatchId);
            }

            // Load results
            await loadAnalysisResults(analysisStatus.batch_id, currentCaseId);
        }
    }
}
```

#### Task F3: Add Batch History Section (case-simulation-center.html Tab 2)
```html
<!-- Add to Tab 2 after batch progress section -->
<div class="batch-history">
    <h3>批次历史</h3>

    <table class="simulations-table">
        <thead>
            <tr>
                <th>批次ID</th>
                <th>创建时间</th>
                <th>仿真数</th>
                <th>事件数</th>
                <th>状态</th>
                <th>分析结果</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody id="batchHistoryBody">
            <!-- Populated from /api/v1/simulation/batch-history -->
        </tbody>
    </table>
</div>
```

#### Task F4: Enhance analysis_viewer.html with Multi-Scenario Comparison
```javascript
// Add new tab: Strategy Comparison
async function loadMultiScenarioComparison(eventId) {
    const response = await api.request(`/analysis/multi-scenario-comparison`, {
        method: 'POST',
        body: JSON.stringify({
            event_id: eventId,
            analysis_types: ['summary', 'edgedata']
        })
    });

    const comparisonData = response.data;

    // Render comparison charts
    renderStrategyComparisonChart(comparisonData.summary_metrics);
    renderEdgeDataComparisonTable(comparisonData.edgedata_metrics);
    renderStrategyRanking(comparisonData.strategy_effectiveness);
}

function renderStrategyComparisonChart(metrics) {
    // Use Chart.js to create bar chart
    const ctx = document.getElementById('comparisonChart').getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['平均速度', '平均行程时间', '总车辆数', '完成率'],
            datasets: [
                {
                    label: 'NO_CONTROL',
                    data: [metrics.no_control.avg_speed, metrics.no_control.avg_trip_time, ...],
                    backgroundColor: 'rgba(128, 128, 128, 0.5)'
                },
                {
                    label: 'VSS',
                    data: [metrics.vss.avg_speed, metrics.vss.avg_trip_time, ...],
                    backgroundColor: 'rgba(33, 150, 243, 0.5)'
                },
                {
                    label: 'TEC',
                    data: [metrics.tec.avg_speed, metrics.tec.avg_trip_time, ...],
                    backgroundColor: 'rgba(255, 152, 0, 0.5)'
                },
                {
                    label: 'DHS',
                    data: [metrics.dhs.avg_speed, metrics.dhs.avg_trip_time, ...],
                    backgroundColor: 'rgba(76, 175, 80, 0.5)'
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '多策略对比分析 (基于summary.xml)'
                }
            }
        }
    });
}
```

## Testing Plan

### Test Case 1: Batch Scenario Generation to Analysis
1. Generate batch scenarios: `python scripts/generate_flowsurge_scenarios.py`
2. Open scenario_browser.html
3. Select event (e.g., Event 8210655)
4. View scenarios: NO_CONTROL, VSS, TEC (3 scenarios)
5. Click "批量创建案例" → Create 3 cases
6. Navigate to case-simulation-center.html
7. Tab 1: Verify 3 cases created
8. Tab 2: Click "开始批量仿真" → Select all 3 simulations → Start
9. Tab 2: Monitor real-time progress (3 simulations)
10. Tab 3: Auto-load analysis when simulations complete
11. Tab 3: View multi-scenario comparison (VSS vs TEC vs NO_CONTROL)

### Test Case 2: Multi-Scenario Analysis
1. In analysis_viewer.html
2. Load multi-scenario comparison for Event 8210655
3. Verify Summary metrics (avg_speed, avg_trip_time, total_vehicles)
4. Verify EdgeData comparison (affected edges only)
5. Verify Strategy ranking (best to worst based on improvement)
6. Export comparison report (PDF/JSON)

### Test Case 3: Batch History
1. In case-simulation-center.html Tab 2
2. View batch history table
3. Filter by date range
4. Click "查看分析" on a completed batch
5. Navigate to analysis tab with pre-loaded results

## Backward Compatibility Checklist

- ✅ Existing OD extraction workflow unchanged
- ✅ Existing control plan optimization workflow unchanged
- ✅ New endpoints use separate routes (`/multi-scenario-comparison`)
- ✅ Metadata version detection (v1.0 vs v2.0)
- ✅ No database schema changes
- ✅ All enhancements additive (no breaking changes)

## Implementation Timeline

| Phase | Tasks | Duration | Priority |
|-------|-------|----------|----------|
| **Phase 1.5** | Backend API enhancements (B1, B2, B3) | 2 days | P0 |
| **Phase 1.6** | Frontend enhancements (F1, F2, F3, F4) | 2-3 days | P0 |
| **Phase 1.7** | Integration testing | 1 day | P0 |
| **Phase 1.8** | Documentation and UAT | 1 day | P1 |

**Total Estimated Effort:** 6-7 days

## Success Criteria

1. ✅ User can select an event and create cases for all strategies (NO_CONTROL, VSS, TEC, DHS) in one click
2. ✅ User can launch batch simulations for all scenarios of an event
3. ✅ User can monitor real-time progress of batch simulations
4. ✅ Analysis auto-starts when all simulations complete
5. ✅ User can view multi-scenario comparison with strategy ranking
6. ✅ User can export comparison reports
7. ✅ Backward compatibility maintained (existing workflows work)

## Next Steps

1. **Implement Backend APIs** (B1, B2, B3)
2. **Enhance Frontend Pages** (F1, F2, F3, F4)
3. **Integration Testing** (Test Cases 1-3)
4. **User Acceptance Testing**
5. **Documentation Updates**

---

**Document Status:** Ready for implementation
**Last Updated:** 2025-11-15
**Approved by:** System Design Review
