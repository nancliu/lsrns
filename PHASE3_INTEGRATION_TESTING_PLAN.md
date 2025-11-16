# Phase 3: Integration Testing Plan
## Event Scenario Case Management UI Refactor

### Test Scope
Integration testing for the complete event scenario workflow:
- Case-simulation-center.html (Phase 1: Refactored UI)
- analysis_viewer.html (Phase 2: Batch results analysis)
- API endpoints (/simulation/batch-start, /simulation/simulation_progress, /analysis/results)

---

## Test Cases

### Section 1: Case List Loading and Display

#### Test 1.1: Case List Initially Loads
**Precondition**: User navigates to case-simulation-center.html
**Steps**:
1. Open case-simulation-center.html
2. Verify page loads without console errors
3. Check "总案例数" card displays a number > 0

**Expected Result**:
- ✅ Page loads successfully
- ✅ No ReferenceError or 404 errors
- ✅ Case count is displayed and accurate

**Test Data**: Should find event cases from /case/list API

---

#### Test 1.2: Case Table Displays All Columns
**Precondition**: Case list loaded (Test 1.1 passed)
**Steps**:
1. Scroll to the cases table
2. Verify the following columns are visible:
   - Checkbox (select)
   - 案例ID
   - 场景ID
   - 事件类型
   - 管控策略
   - 操作

**Expected Result**:
- ✅ All columns visible and properly aligned
- ✅ Case data populated correctly in each row

**Test Data**: At least 2 event cases with different event types

---

#### Test 1.3: Event Type Localization
**Precondition**: Case list loaded (Test 1.1 passed)
**Steps**:
1. Check "事件类型" column for various cases
2. Verify event types show Chinese labels instead of codes:
   - '01_accident' → '交通事故'
   - '02_congestion' → '交通阻塞'
   - '03_construction' → '交通管制'
   - '04_weather' → '恶劣天气'
   - '05_special_event' → '流量激增工况'
   - '07_flowsurge' → '流量激增工况'

**Expected Result**:
- ✅ All event types display Chinese labels
- ✅ No codes or abbreviations visible

**Test Data**: Cases with different event_type values in metadata.json

---

#### Test 1.4: Control Strategy Display
**Precondition**: Case list loaded (Test 1.1 passed)
**Steps**:
1. Check "管控策略" column
2. Verify it displays control strategies extracted from scenario names
3. Common values: 无管控, VSS, TEC, DHS

**Expected Result**:
- ✅ Strategies correctly parsed from scenario IDs
- ✅ Multiple strategies shown comma-separated when applicable
- ✅ '--' displayed when no strategies found

**Test Data**: Cases with various scenario naming patterns

---

### Section 2: Multi-Select and Bulk Operations

#### Test 2.1: Select Individual Case
**Precondition**: Case list loaded (Test 1.1 passed)
**Steps**:
1. Click checkbox for one case row
2. Verify the row highlights
3. Check "已选 X 个案例" counter updates to 1

**Expected Result**:
- ✅ Checkbox marks as checked
- ✅ Row background highlights
- ✅ Counter shows "已选 1 个案例"

**Test Data**: Any case from the list

---

#### Test 2.2: Select All Cases
**Precondition**: Case list loaded (Test 1.1 passed)
**Steps**:
1. Click "全选" checkbox in table header
2. Verify all case checkboxes become checked
3. Check counter shows total case count

**Expected Result**:
- ✅ All case checkboxes checked
- ✅ Counter shows "已选 N 个案例" where N = total cases
- ✅ All rows highlight

**Test Data**: List with 5+ cases

---

#### Test 2.3: Deselect All Cases
**Precondition**: Test 2.2 completed (all cases selected)
**Steps**:
1. Click the checked "全选" checkbox again
2. Verify all case checkboxes uncheck
3. Check counter resets to 0
4. Verify bulk action buttons hide

**Expected Result**:
- ✅ All checkboxes unchecked
- ✅ No rows highlight
- ✅ Counter shows "已选 0 个案例"
- ✅ "批量启动" and "清除选择" buttons disappear

**Test Data**: Same as Test 2.2

---

#### Test 2.4: Bulk Actions Area Visibility
**Precondition**: Case list loaded (Test 1.1 passed)
**Steps**:
1. Initially verify bulk actions area is hidden
2. Select one case
3. Verify bulk actions area appears with:
   - Selected count display
   - "批量启动" button
   - "清除选择" button
4. Deselect all
5. Verify bulk actions area hides again

**Expected Result**:
- ✅ Area only visible when cases selected
- ✅ All buttons properly displayed/hidden
- ✅ Count updates correctly

**Test Data**: Any case

---

### Section 3: Batch Startup Workflow

#### Test 3.1: Open Batch Startup Confirmation Modal
**Precondition**: At least one case selected (Test 2.1)
**Steps**:
1. Click "批量启动" button
2. Verify confirmation modal appears with:
   - Title: "确认批量启动"
   - List of selected cases
   - "取消" button
   - "确认启动" button

**Expected Result**:
- ✅ Modal appears centered
- ✅ All selected cases listed
- ✅ Buttons functional

**Test Data**: 2-3 selected cases

---

#### Test 3.2: Confirm Batch Startup
**Precondition**: Batch startup modal open (Test 3.1)
**Steps**:
1. Click "确认启动" button
2. Monitor console for API call: POST /api/v1/simulation/batch-start
3. Verify response includes batch_id
4. Check monitoring panel becomes visible
5. Verify 10-second refresh timer starts

**Expected Result**:
- ✅ API call successful (200 OK)
- ✅ Response contains batch_id
- ✅ Cases tab hidden, monitoring panel shown
- ✅ Console shows no errors

**Test Data**: 2-3 selected cases with simulations

---

#### Test 3.3: Cancel Batch Startup
**Precondition**: Batch startup modal open (Test 3.1)
**Steps**:
1. Click "取消" button
2. Verify modal closes
3. Verify no API call made
4. Cases still selected

**Expected Result**:
- ✅ Modal closes
- ✅ No batch-start API call in console
- ✅ UI returns to normal state
- ✅ Cases still checked

**Test Data**: Any selected case

---

### Section 4: Real-Time Monitoring Panel

#### Test 4.1: Monitoring Panel Layout
**Precondition**: Batch started (Test 3.2)
**Steps**:
1. Verify monitoring panel shows:
   - "批次仿真进度" heading
   - 4 statistic cards: 总计, 已完成, 运行中, 失败
   - Progress bar
   - ETA display
   - Simulation details table
   - "返回案例列表" and "查看分析结果" buttons

**Expected Result**:
- ✅ All elements visible
- ✅ Layout properly responsive
- ✅ Cards display 0 or appropriate numbers initially

**Test Data**: Active batch simulation

---

#### Test 4.2: Progress Updates
**Precondition**: Batch running (Test 3.2 + wait)
**Steps**:
1. Monitor the statistics cards
2. Wait 10 seconds for refresh
3. Verify numbers update:
   - 已完成 count increases
   - 运行中 count changes
   - Progress bar advances
4. Check simulation details table updates with new rows

**Expected Result**:
- ✅ Statistics auto-refresh every 10 seconds
- ✅ Numbers accurately reflect batch status
- ✅ Progress bar reflects completion percentage
- ✅ New simulations appear in table

**Test Data**: Active batch with running simulations

---

#### Test 4.3: Simulation Details Table
**Precondition**: Batch running with 3+ simulations (Test 4.2)
**Steps**:
1. Scroll to simulation details table
2. Verify columns:
   - # (row number)
   - 仿真ID
   - 状态 (with color badges)
   - 进度 (percentage)
   - 耗时 (seconds)
3. Check status badges:
   - Green for completed
   - Red for failed
   - Gray for running/queued

**Expected Result**:
- ✅ All columns visible
- ✅ Status badges color-coded correctly
- ✅ Progress percentages 0-100
- ✅ Times increase over updates

**Test Data**: Running batch with multiple simulations

---

### Section 5: Analysis Results Navigation

#### Test 5.1: View Analysis Results Button
**Precondition**: Batch completed or in progress (Test 4.1)
**Steps**:
1. Verify "查看分析结果" button in monitoring panel
2. Click the button
3. Monitor URL change
4. Verify navigation to: analysis_viewer.html?case_id={caseId}

**Expected Result**:
- ✅ Button visible and clickable
- ✅ URL includes case_id parameter
- ✅ analysis_viewer.html loads without errors

**Test Data**: Case ID from completed batch

---

#### Test 5.2: Analysis Results Page Layout
**Precondition**: Analysis page loaded (Test 5.1)
**Steps**:
1. Verify top bar with:
   - "📈 影响分析" title
   - "🔄 刷新" button
   - "返回案例管理" button
   - "返回" button (history)
2. Verify analysis tabs:
   - 📊 概览
   - 🗺️ 路段分析
   - 📈 对比分析
   - 📋 详细指标
3. Verify "返回案例管理" button is visible

**Expected Result**:
- ✅ All buttons present and functional
- ✅ All tabs clickable
- ✅ "返回案例管理" button visible (new in Phase 2)

**Test Data**: Valid case_id parameter

---

#### Test 5.3: Batch Statistics Display
**Precondition**: Analysis page loaded (Test 5.2)
**Steps**:
1. Verify overview tab shows metrics:
   - 总仿真数 (total simulations)
   - 已完成仿真 (completed count)
   - 失败仿真 (failed count)
   - 完成率 (percentage)

**Expected Result**:
- ✅ All metrics displayed
- ✅ Numbers match batch progress
- ✅ Completion rate calculated correctly

**Test Data**: Batch with 5+ simulations, some completed

---

#### Test 5.4: Simulation List in Details Tab
**Precondition**: Analysis page loaded (Test 5.2)
**Steps**:
1. Click "📋 详细指标" tab
2. Verify table shows "仿真列表" title
3. Table columns:
   - # (row index)
   - 仿真ID
   - 状态
   - 进度 (%)
   - 耗时 (s)
4. Verify all simulations from batch are listed
5. Check status badges color-coded

**Expected Result**:
- ✅ Table title changed to "仿真列表"
- ✅ All simulations displayed
- ✅ Status badges match actual status
- ✅ Progress and time values present

**Test Data**: Batch with 3+ simulations

---

#### Test 5.5: JSON Export from Analysis Page
**Precondition**: Analysis page with batch results (Test 5.3)
**Steps**:
1. Click "📋 导出JSON" button
2. Verify download starts
3. Check filename: `batch_analysis_{case_id}.json`
4. Open file and verify structure:
   - Contains summary object
   - Contains simulations array
   - Valid JSON format

**Expected Result**:
- ✅ File downloads successfully
- ✅ Filename includes batch identifier
- ✅ File contains valid JSON
- ✅ All batch data included

**Test Data**: Completed or running batch

---

### Section 6: Navigation Flow

#### Test 6.1: Circular Navigation
**Precondition**: Batch completed and analysis viewed
**Steps**:
1. Start: case-simulation-center.html
2. Select cases, start batch
3. Click "查看分析结果"
4. Verify: analysis_viewer.html?case_id={caseId}
5. Click "返回案例管理" button
6. Verify: case-simulation-center.html?case_id={caseId}
7. Verify selected case highlighted or visible

**Expected Result**:
- ✅ All navigation links work
- ✅ case_id preserved throughout flow
- ✅ Can navigate back and forth multiple times
- ✅ No data loss

**Test Data**: Complete workflow with one case

---

#### Test 6.2: Direct Access to Analysis Page
**Precondition**: None
**Steps**:
1. Directly visit: analysis_viewer.html?case_id=case_event_123456
2. Verify page loads
3. Check if batch results load (if data available)
4. If no data, verify fallback message

**Expected Result**:
- ✅ Page loads without errors
- ✅ Shows results or appropriate "no data" message
- ✅ "返回案例管理" button available
- ✅ Can navigate back to case management

**Test Data**: Valid existing case_id

---

### Section 7: Error Handling and Edge Cases

#### Test 7.1: No Cases Available
**Precondition**: Empty cases list (if possible)
**Steps**:
1. Verify appropriate message shown
2. Check bulk actions hidden
3. Verify no console errors

**Expected Result**:
- ✅ Graceful empty state message
- ✅ No functionality errors
- ✅ No console errors

**Test Data**: Empty case list

---

#### Test 7.2: Network Error During Batch Start
**Precondition**: Case selected, ready to start batch
**Steps**:
1. Disable network (in DevTools)
2. Click "批量启动" and confirm
3. Verify error handling:
   - Modal closes or error shown
   - No monitoring panel appears
   - Batch not marked as started

**Expected Result**:
- ✅ Error message shown to user
- ✅ UI reverts to normal state
- ✅ No orphaned UI elements
- ✅ Can retry

**Test Data**: Any selected case

---

#### Test 7.3: Network Error During Progress Refresh
**Precondition**: Batch started and monitoring running
**Steps**:
1. Wait for monitoring to start refreshing
2. Disable network
3. Observe monitoring panel behavior
4. Re-enable network
5. Verify refresh recovers

**Expected Result**:
- ✅ Shows error or "last known" state
- ✅ Retries on next interval
- ✅ Recovers when network restored
- ✅ No continuous error messages

**Test Data**: Running batch

---

#### Test 7.4: Invalid case_id in URL
**Precondition**: None
**Steps**:
1. Visit: analysis_viewer.html?case_id=invalid_case_12345
2. Monitor console
3. Verify error handling:
   - Page loads (doesn't crash)
   - Error message or fallback shown
   - Can navigate back

**Expected Result**:
- ✅ Page doesn't crash
- ✅ Clear error message
- ✅ Can still navigate away
- ✅ No console errors (just warnings)

**Test Data**: Non-existent case_id

---

### Section 8: Browser Compatibility

#### Test 8.1: Chrome/Edge Latest
**Steps**:
1. Run all tests in Chrome latest version
2. Verify no console errors
3. Check responsive design

**Expected Result**: ✅ All tests pass

#### Test 8.2: Firefox Latest
**Steps**: Same as 8.1

**Expected Result**: ✅ All tests pass

#### Test 8.3: Mobile Viewport (375px width)
**Steps**:
1. Enable mobile viewport in DevTools (375px)
2. Navigate to case-simulation-center.html
3. Verify:
   - Table columns stack or scroll properly
   - Buttons remain clickable
   - Modal displays correctly
4. Test same for analysis_viewer.html

**Expected Result**: ✅ Mobile responsive design works

---

## Test Execution Summary Template

```
Test Suite: Phase 3 Integration Testing
Date: _______________
Tester: _______________
Environment: _______________
Browser: _______________

Test Results:
- Section 1 (Case Loading): _____ / 4 passed
- Section 2 (Multi-Select): _____ / 4 passed
- Section 3 (Batch Startup): _____ / 3 passed
- Section 4 (Monitoring): _____ / 3 passed
- Section 5 (Analysis): _____ / 5 passed
- Section 6 (Navigation): _____ / 2 passed
- Section 7 (Error Handling): _____ / 4 passed
- Section 8 (Compatibility): _____ / 3 passed

Total: _____ / 28 tests passed

Failed Tests:
- [Test ID]: [Description] - [Failure Reason]
- [Test ID]: [Description] - [Failure Reason]

Issues Found:
1. [Issue] - Severity: [High/Medium/Low]
2. [Issue] - Severity: [High/Medium/Low]

Recommendations:
- [Recommendation 1]
- [Recommendation 2]

Sign-off: _______________
```

---

## Performance Checklist

- [ ] Initial page load < 2 seconds
- [ ] Case list load < 3 seconds (100 cases)
- [ ] Multi-select operations responsive (< 100ms)
- [ ] Monitoring refresh smooth (no flicker)
- [ ] Analysis page loads < 2 seconds
- [ ] No memory leaks (DevTools heap snapshot)
- [ ] Network requests optimized (no duplicate calls)

---

## Cleanup Items for Phase 3

- [ ] Review and remove unnecessary console.log statements (keep important ones)
- [ ] Consolidate duplicated utility functions
- [ ] Add JSDoc comments to public functions
- [ ] Update CSS class naming for consistency
- [ ] Remove any commented-out code
- [ ] Verify no hardcoded values in frontend code
- [ ] Update API endpoint references in documentation

---

## Documentation Updates Needed

- [ ] Update README.md with new workflow
- [ ] Document case_id parameter usage
- [ ] Add screenshots of new UI
- [ ] Update API documentation
- [ ] Create user guide for batch operations
- [ ] Document fallback mechanism
- [ ] Add troubleshooting guide

---

## Sign-Off Criteria

Phase 3 is complete when:
- ✅ All 28 integration tests pass
- ✅ No critical or high-priority issues remain
- ✅ Code cleanup completed
- ✅ Documentation updated
- ✅ Performance acceptable
- ✅ Cross-browser testing passed
- ✅ Mobile responsiveness verified
- ✅ Ready for production deployment
