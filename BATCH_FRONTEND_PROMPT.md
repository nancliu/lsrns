# 事件场景批次管理前端实施提示语

## 提示语（复制以下内容使用）

```
/openspec:apply openspec/changes/event-scenario-simulation-integration

继续实现事件场景批次管理的前端部分。

**当前状态**：
✅ 后端完全实现（EventBatchService + 5个API端点）
✅ 对比表格组件已完成（event-scenario-comparison.js/css）
❌ 前端页面重构待完成

**需要实现**：

1. 重构 `frontend/scenarios/case-simulation-center.html` 为 3 视图结构：
   - View 1: 案例管理（已有，保持不变）
   - View 2: 仿真监控（已有，保持不变）
   - View 3: 批次结果（NEW - 需要添加）

2. 创建前端 JavaScript 模块：
   - `frontend/scenarios/js/event-batch-management.js`
   - 功能：连接后端 API `/api/v1/batch/*`，处理批次操作

3. 集成已有组件：
   - ✅ `js/event-scenario-comparison.js`（对比表格组件）
   - ✅ `css/event-scenario-comparison.css`（样式）

**具体修改清单**：

### 修改 `case-simulation-center.html`

1. **添加CSS引用**（第8行附近）：
   ```html
   <link rel="stylesheet" href="css/event-scenario-comparison.css">
   ```

2. **添加第3个Tab按钮**（第437-443行）：
   ```html
   <button class="tab-btn" data-tab="results" onclick="switchTab('results')">
       📊 批次结果
   </button>
   ```

3. **添加第3个Tab内容**（第600行之后，monitor-tab结束后）：
   - 批次选择器（下拉框）
   - 批次信息展示（batch_id, event_id, 场景数量, 完成时间）
   - 策略对比表格容器（调用 renderEventScenarioComparisonTable）
   - 策略排名容器（调用 renderStrategyRanking）
   - 操作按钮（返回监控、导出报告）

4. **添加脚本引用**（第653行之前）：
   ```html
   <script src="js/event-scenario-comparison.js"></script>
   <script src="js/event-batch-management.js"></script>
   ```

5. **更新 switchTab() 函数**（第697-703行）：
   添加 `results` case，调用 `loadBatchResultsTab()`

6. **添加批次结果函数**（第1264行之后）：
   - `loadBatchResultsTab()` - 加载已完成批次列表
   - `loadSelectedBatchResults()` - 加载选中批次的结果
   - `exportBatchReport()` - 导出报告（占位符）

7. **更新 refreshCurrentTab()**（第1266-1272行）：
   添加 `results` case

### 创建 `event-batch-management.js`

创建 EventBatchManager 类，包含方法：
- `getCompletedBatches(limit)` - 获取已完成批次
- `getBatchStatus(batchId)` - 获取批次状态
- `getBatchResults(batchId)` - 获取批次结果
- `createEventBatch()` - 创建事件批次
- `startEventBatch()` - 启动批次仿真
- `startMonitoring()` / `stopMonitoring()` - 实时监控

**后端API端点（已实现）**：
- `GET /api/v1/batch/list-event-batches?status=completed&limit=50`
- `GET /api/v1/batch/event-batch-status/{batch_id}`
- `GET /api/v1/batch/event-batch-results/{batch_id}`
- `POST /api/v1/batch/create-from-event`
- `POST /api/v1/batch/start-event-batch`

**参考文档**：
- `openspec/changes/event-scenario-simulation-integration/SIMPLIFIED_BATCH_WORKFLOW_DESIGN.md`
- `openspec/changes/event-scenario-simulation-integration/BACKEND_IMPLEMENTATION_SUMMARY.md`
- `openspec/changes/event-scenario-simulation-integration/EVENT_SCENARIO_COMPARISON_TABLE_GUIDE.md`
- `FRONTEND_IMPLEMENTATION_GUIDE.md`（刚生成的详细指南）

**参考实现**：
- `frontend/control/optimization.html`（批次工作流参考）
- `frontend/scenarios/js/event-scenario-comparison.js`（对比表格组件）
- `frontend/scenarios/css/event-scenario-comparison.css`（样式）

**重要**：
- 保持现有 Tab 1 和 Tab 2 的功能不变
- 复用已有的对比表格组件（不要重新实现）
- 使用 APIClient 进行API调用
- 遵循项目的代码规范（STANDARD-CODE-001）
- 不要添加内联样式（PITFALL-FE-002）

请实现完整的批次结果视图，确保用户可以：
1. 在 Tab 3 中选择已完成的批次
2. 查看批次信息（event_id, 场景数量等）
3. 查看策略对比表格（NO_CONTROL vs VSS/TEC/DHS）
4. 查看策略效果排名（带奖牌和评价）
```

---

## 使用说明

1. **重置环境后**，将上面的提示语完整复制
2. 在Claude Code中粘贴并执行
3. 系统会自动：
   - 重构 `case-simulation-center.html`
   - 创建 `event-batch-management.js`
   - 集成对比表格组件
   - 完成整个前端实施

## 预期结果

执行后应该得到：
- ✅ 3个Tab页面（案例管理 | 仿真监控 | 批次结果）
- ✅ 批次选择器可以加载已完成的批次
- ✅ 选择批次后显示对比表格和排名
- ✅ 所有现有功能保持正常工作

## 文件清单

**已创建**：
- `frontend/scenarios/js/event-batch-management.js` ✅
- `frontend/scenarios/js/event-scenario-comparison.js` ✅（已存在）
- `frontend/scenarios/css/event-scenario-comparison.css` ✅（已存在）
- `FRONTEND_IMPLEMENTATION_GUIDE.md` ✅（详细指南）
- `add-batch-results-view.patch` ✅（patch文件，可选）

**待修改**：
- `frontend/scenarios/case-simulation-center.html` ⏳

---

**生成时间**: 2025-11-15
**维护者**: 开发团队
