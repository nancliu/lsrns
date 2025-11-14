# Case Creation Status Display Design

**Date**: 2025-11-13
**Question**: 场景案例创建的状态如何显示，在列表中有体现吗，还是在创建按钮的状态上有体现
**Context**: Event scenario case creation with async OD file generation

---

## Question Analysis

The user is asking where case creation status should be displayed:

**Option A**: Show in the scenario list (e.g., add status column showing if case exists)
**Option B**: Show in the create button state (e.g., disable/change button appearance)
**Option C**: Both - show in list AND reflect in button state

---

## Recommended Solution: Option C (Both)

### Architecture

```
Scenario Browser (scenario_browser.html)
├── Scenario List Table
│   └── Status Indicator Column (NEW)
│       ├── ✓ Created: Green badge showing case count
│       ├── ⏳ OD Generating: Orange badge showing progress
│       ├── ⚠️ Failed: Red badge showing error
│       └── — Not Created: Gray/empty
│
└── Action Buttons
    ├── Create Button State (UPDATED)
    │   ├── Enabled: Normal appearance (no case exists)
    │   ├── Disabled: Grayed out (case already exists)
    │   └── Updating: Busy state (OD generating)
    │
    └── Case Details Link (NEW)
        └── Link to case in case management center
```

---

## Implementation Details

### 1. Load Created Cases on Page Load

**Function**: `loadCreatedCases()` (NEW)

```javascript
async function loadCreatedCases() {
    try {
        const response = await fetch('/api/v1/case/list_cases/?page_size=1000');
        const data = response.data || response;
        const allCases = data.cases || data.items || [];

        // Filter for event scenario cases only
        const eventScenarioCases = allCases.filter(c =>
            c.source_type === 'event_scenario' ||
            c.case_type === 'event_scenario_case'
        );

        // Build map: scenario_id -> case info
        window.scenarioCaseMap = {};
        for (const caseItem of eventScenarioCases) {
            const scenario_id = caseItem.scenario_id ||
                               caseItem.source_scenario_id;

            if (!window.scenarioCaseMap[scenario_id]) {
                window.scenarioCaseMap[scenario_id] = [];
            }

            window.scenarioCaseMap[scenario_id].push({
                case_id: caseItem.case_id,
                status: caseItem.status,
                created_at: caseItem.created_at
            });
        }

        console.log('✓ Loaded created cases:', Object.keys(window.scenarioCaseMap).length);
    } catch (error) {
        console.warn('Could not load created cases:', error);
        window.scenarioCaseMap = {};
    }
}

// Call on page load
document.addEventListener('DOMContentLoaded', () => {
    loadCreatedCases();
    loadScenarios();
    setupEventListeners();
});
```

### 2. Update Scenario Table Rendering

**Update**: `renderScenarios()` function

```html
<!-- Add status column to table header -->
<th>创建状态</th>

<!-- Add status cell to each row -->
${getScenarioStatusDisplay(s.scenario_id)}

<!-- Add helper function -->
<script>
function getScenarioStatusDisplay(scenario_id) {
    const cases = window.scenarioCaseMap?.[scenario_id] || [];

    if (cases.length === 0) {
        return '<span class="status-badge status-none">—未创建</span>';
    }

    const case1 = cases[0];
    switch(case1.status) {
        case 'od_generating':
            return '<span class="status-badge status-progress">⏳生成中</span>';
        case 'od_generation_failed':
            return '<span class="status-badge status-error">⚠️生成失败</span>';
        case 'created':
            return '<span class="status-badge status-success">✓已创建</span>';
        case 'simulating':
            return '<span class="status-badge status-running">▶️仿真中</span>';
        case 'completed':
            return '<span class="status-badge status-completed">✅已完成</span>';
        default:
            return '<span class="status-badge status-unknown">◯' + case1.status + '</span>';
    }
}
</script>
```

### 3. Update Create Button Behavior

**Update**: `directCreateCase()` function

```javascript
async function directCreateCase(scenarioId, eventType, strategy) {
    const cases = window.scenarioCaseMap?.[scenarioId] || [];

    // Check if case already exists
    if (cases.length > 0) {
        const case1 = cases[0];

        // If case exists, show options
        const action = confirm(
            `该场景已创建案例:\n\n` +
            `案例ID: ${case1.case_id}\n` +
            `状态: ${case1.status}\n\n` +
            `点击"确定"查看案例详情，点击"取消"创建新案例`
        );

        if (action) {
            // Navigate to case management center
            window.location.href = `case-simulation-center.html?case_id=${case1.case_id}`;
        } else {
            // Continue with creating new case
            // (user explicitly wants another case)
        }
    }

    // ... existing case creation logic ...

    // After successful creation, update scenario case map
    const result = await response.json();
    if (result.data?.case_id) {
        if (!window.scenarioCaseMap[scenarioId]) {
            window.scenarioCaseMap[scenarioId] = [];
        }
        window.scenarioCaseMap[scenarioId].push({
            case_id: result.data.case_id,
            status: result.data.case_status || 'created',
            created_at: result.data.created_at
        });

        // Refresh scenario table to update status
        renderScenarios();
    }
}
```

### 4. Add CSS Styling for Status Badges

```css
.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    white-space: nowrap;
}

.status-none {
    background-color: #f0f0f0;
    color: #666;
}

.status-progress {
    background-color: #fff3cd;
    color: #856404;
    animation: pulse 1.5s infinite;
}

.status-error {
    background-color: #f8d7da;
    color: #721c24;
}

.status-success {
    background-color: #d4edda;
    color: #155724;
}

.status-running {
    background-color: #cfe2ff;
    color: #084298;
    animation: pulse 1s infinite;
}

.status-completed {
    background-color: #d1ecf1;
    color: #0c5460;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}
```

---

## User Experience Flow

### Scenario A: Scenario Has No Case Yet
```
User views scenario in list
  ↓
Status column shows: "— 未创建"
Create button shows: Normal, clickable
  ↓
User clicks Create
  ↓
Case creation starts
Status updates to: "⏳ 生成中" (if OD generation)
  ↓
Case created successfully
Status updates to: "✓ 已创建"
```

### Scenario B: Scenario Has Case with OD Generating
```
User views scenario in list
  ↓
Status column shows: "⏳ 生成中"
Create button shows: Disabled (case exists)
  ↓
User can click case link to monitor OD generation
  ↓
OD generation completes
Status updates to: "✓ 已创建"
```

### Scenario C: Scenario Has Case with OD Failed
```
User views scenario in list
  ↓
Status column shows: "⚠️ 生成失败"
Create button shows: Enabled (allow retry or create new)
  ↓
User can click "创建" to retry or create new case
```

---

## Data Flow Diagram

```
Page Load
  ↓
loadCreatedCases()
  ├─ Fetch /api/v1/case/list_cases/
  ├─ Filter: source_type === 'event_scenario'
  └─ Store in window.scenarioCaseMap
       └─ Key: scenario_id
       └─ Value: [{case_id, status, created_at}, ...]

renderScenarios()
  ├─ For each scenario:
  │   ├─ Check window.scenarioCaseMap[scenario_id]
  │   ├─ Get status from first case (if exists)
  │   └─ Render status badge in table
  │
  └─ Render Create button
      ├─ If case exists: Show different appearance
      └─ If case exists: Show case details link option

directCreateCase()
  ├─ Check if case exists
  ├─ If exists: Show confirm dialog
  │   └─ Option to navigate to case or create new
  ├─ If not exists: Create case
  └─ Update window.scenarioCaseMap
      └─ Call renderScenarios() to refresh
```

---

## Benefits of This Approach

### For Users
- ✅ **Clear Status**: See at a glance which scenarios have cases
- ✅ **Prevents Duplicates**: Know if case already exists before creating
- ✅ **Progress Visibility**: See OD generation status
- ✅ **Quick Navigation**: Direct link to case details
- ✅ **Error Recovery**: Know if generation failed and can retry

### For Development
- ✅ **Stateless**: No database queries needed, only load on page load
- ✅ **Efficient**: Client-side filtering using scenario_id
- ✅ **Flexible**: Can handle multiple cases per scenario
- ✅ **Extensible**: Easy to add more statuses later
- ✅ **Non-blocking**: Doesn't delay scenario list rendering

---

## Alternative Approaches Not Recommended

### ❌ Option A Only (List Column)
- Pro: Shows full information
- Con: Doesn't guide user action on create button
- Con: User doesn't know button should be disabled

### ❌ Option B Only (Button State)
- Pro: Guides user action
- Con: No visibility into what case exists
- Con: User can't see error status (OD generation failed)
- Con: No way to navigate to existing case

---

## Implementation Priority

1. **Phase 1** (Now): Add status column and load created cases
   - ~50 lines of code
   - No API changes needed
   - Improves visibility immediately

2. **Phase 2** (Optional): Update create button behavior
   - ~30 lines of code
   - Prevents accidental duplicates
   - Guides user to existing case

3. **Phase 3** (Enhancement): Real-time status updates
   - WebSocket or polling
   - Show OD generation progress in real-time
   - Not critical for MVP

---

## Summary

**Recommended: Display status in BOTH places**

1. **In the scenario list table** - Show status column with badge
2. **In the create button** - Disable if case exists, show options

This provides the best user experience: users can see what cases exist (list) and the button guides them to the right action (create or view).

---

**Status**: Design document complete, ready for implementation if approved

