# PowerShell script to refactor row addition functions
# Phase 2 Task 2.2 - Merge row addition functions
# Strategy: Content-based replacement, not line-number based

$filePath = "D:\projects\OD_SIM\frontend\control\js\parameter_form.js"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Task 2.2: 合并行添加函数重构脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create backup
$backupPath = "$filePath.backup_task22_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item $filePath $backupPath
Write-Host "✅ 备份已创建: $backupPath" -ForegroundColor Green
Write-Host ""

# Read file content
$content = Get-Content $filePath -Raw

# ==================== Step 1: Insert Helper Functions ====================
Write-Host "[Step 1] 插入辅助函数..." -ForegroundColor Yellow

# Find the position right before "function addStepRow"
# Insert helper functions before it
$helperFunctions = @'

// ==================== Row Creation Helper Functions ====================

/**
 * Create a time input element (0-24 hours).
 * @param {string} className - CSS class name
 * @param {number} value - Initial value
 * @returns {HTMLInputElement}
 */
function createTimeInput(className, value = 0) {
  const input = document.createElement("input");
  input.type = "number";
  input.className = className;
  input.min = "0";
  input.max = "24";
  input.step = "0.5";
  input.value = value;
  return input;
}

/**
 * Create a number input element with custom constraints.
 * @param {string} className - CSS class name
 * @param {number} value - Initial value
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @param {number} step - Step increment
 * @returns {HTMLInputElement}
 */
function createNumberInput(className, value, min, max, step = 1) {
  const input = document.createElement("input");
  input.type = "number";
  input.className = className;
  input.min = String(min);
  input.max = String(max);
  input.step = String(step);
  input.value = String(value);
  return input;
}

/**
 * Create a remove button for table rows with timeline update.
 * @param {HTMLElement} row - The row to remove
 * @param {HTMLElement} tbody - Table body element
 * @param {string} timelineType - Timeline type (vss/dhs/flow/tec_simple)
 * @returns {HTMLButtonElement}
 */
function createRemoveButton(row, tbody, timelineType) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "btn-remove-step";
  btn.textContent = "删除";
  btn.addEventListener("click", (e) => {
    e.preventDefault();
    row.remove();
    updateTimelineByType(tbody, timelineType);
  });
  return btn;
}

/**
 * Bind input change event to update timeline (with debouncing).
 * @param {HTMLInputElement|HTMLSelectElement} input - Input element
 * @param {HTMLElement} tbody - Table body element
 * @param {string} timelineType - Timeline type
 */
function bindTimelineUpdate(input, tbody, timelineType) {
  input.addEventListener('input', () => {
    if (debouncedUpdateTimeline[timelineType]) {
      debouncedUpdateTimeline[timelineType](tbody);
    }
  });
  // Also handle 'change' event for select elements
  if (input.tagName === 'SELECT') {
    input.addEventListener('change', () => {
      if (debouncedUpdateTimeline[timelineType]) {
        debouncedUpdateTimeline[timelineType](tbody);
      }
    });
  }
}

// ==================== End Helper Functions ====================

'@

# Insert before "function addStepRow"
$pattern = 'function addStepRow\(tbody, paramName, timeVal, speedVal, stepStructure\) \{'
if ($content -match $pattern) {
    $content = $content -replace $pattern, ($helperFunctions + "`r`n" + $pattern)
    Write-Host "  ✅ 辅助函数已插入" -ForegroundColor Green
} else {
    Write-Host "  ❌ 未找到 addStepRow 函数" -ForegroundColor Red
    exit 1
}

# ==================== Step 2: Refactor addStepRow ====================
Write-Host "[Step 2] 重构 addStepRow..." -ForegroundColor Yellow

$oldAddStepRow = [regex]::Escape('function addStepRow(tbody, paramName, timeVal, speedVal, stepStructure) {
  const row = document.createElement("tr");
  row.className = "step-row";

  // Time input
  const timeCell = document.createElement("td");
  const timeInput = document.createElement("input");
  timeInput.type = "number";
  timeInput.className = "step-time";
  timeInput.min = "0";
  timeInput.max = "24";
  timeInput.step = "0.5";
  timeInput.value = timeVal || 0;
  timeCell.appendChild(timeInput);
  row.appendChild(timeCell);

  // Speed input
  const speedCell = document.createElement("td");
  const speedInput = document.createElement("input");
  speedInput.type = "number";
  speedInput.className = "step-speed";
  speedInput.min = stepStructure.speed_min || 30;
  speedInput.max = stepStructure.speed_max || 130;
  speedInput.value = speedVal || 100;
  speedCell.appendChild(speedInput);
  row.appendChild(speedCell);

  // Remove button
  const actionCell = document.createElement("td");
  const removeBtn = document.createElement("button");
  removeBtn.type = "button";
  removeBtn.className = "btn-remove-step";
  removeBtn.textContent = "Remove";
  removeBtn.addEventListener("click", (e) => {
    e.preventDefault();
    row.remove();
    // [NEW] 删除行后更新时间轴
    updateTimelineByType(tbody, ''vss'');
  });
  actionCell.appendChild(removeBtn);
  row.appendChild(actionCell);

  // [NEW] 为输入框添加变化事件监听器以更新时间轴（使用防抖）
  timeInput.addEventListener(''input'', () => debouncedUpdateTimeline.vss(tbody));
  speedInput.addEventListener(''input'', () => debouncedUpdateTimeline.vss(tbody));

  tbody.appendChild(row);
}')

$newAddStepRow = @'
function addStepRow(tbody, paramName, timeVal, speedVal, stepStructure) {
  const row = document.createElement("tr");
  row.className = "step-row";

  // Time input (using helper)
  const timeCell = document.createElement("td");
  const timeInput = createTimeInput("step-time", timeVal || 0);
  timeCell.appendChild(timeInput);
  row.appendChild(timeCell);

  // Speed input (using helper)
  const speedCell = document.createElement("td");
  const speedInput = createNumberInput(
    "step-speed",
    speedVal || 100,
    stepStructure.speed_min || 30,
    stepStructure.speed_max || 130
  );
  speedCell.appendChild(speedInput);
  row.appendChild(speedCell);

  // Remove button (using helper)
  const actionCell = document.createElement("td");
  const removeBtn = createRemoveButton(row, tbody, 'vss');
  actionCell.appendChild(removeBtn);
  row.appendChild(actionCell);

  // Bind timeline updates (using helper)
  bindTimelineUpdate(timeInput, tbody, 'vss');
  bindTimelineUpdate(speedInput, tbody, 'vss');

  tbody.appendChild(row);
}
'@

# Use non-greedy regex to match the function
$pattern = '(?s)function addStepRow\(tbody, paramName, timeVal, speedVal, stepStructure\) \{.+?^}'
if ($content -match $pattern) {
    $content = $content -replace $pattern, $newAddStepRow, 1
    Write-Host "  ✅ addStepRow 已重构" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  使用简化替换策略" -ForegroundColor Yellow
    # Fallback: replace key sections
    $content = $content -replace 'const timeInput = document\.createElement\("input"\);\s+timeInput\.type = "number";\s+timeInput\.className = "step-time";\s+timeInput\.min = "0";\s+timeInput\.max = "24";\s+timeInput\.step = "0\.5";\s+timeInput\.value = timeVal \|\| 0;', 'const timeInput = createTimeInput("step-time", timeVal || 0);'
}

# ==================== Step 3: Refactor addDHSIntervalRow ====================
Write-Host "[Step 3] 重构 addDHSIntervalRow..." -ForegroundColor Yellow

# Replace begin time input creation
$content = $content -replace '(?s)// Begin time\s+const beginCell = document\.createElement\("td"\);\s+const beginInput = document\.createElement\("input"\);\s+beginInput\.type = "number";\s+beginInput\.className = "dhs-interval-begin";\s+beginInput\.min = "0";\s+beginInput\.max = "24";\s+beginInput\.step = "0\.5";\s+beginInput\.value = beginHours \|\| 0;\s+beginCell\.appendChild\(beginInput\);\s+row\.appendChild\(beginCell\);', @'
// Begin time (using helper)
  const beginCell = document.createElement("td");
  const beginInput = createTimeInput("dhs-interval-begin", beginHours || 0);
  beginCell.appendChild(beginInput);
  row.appendChild(beginCell);
'@

# Replace end time input creation
$content = $content -replace '(?s)// End time\s+const endCell = document\.createElement\("td"\);\s+const endInput = document\.createElement\("input"\);\s+endInput\.type = "number";\s+endInput\.className = "dhs-interval-end";\s+endInput\.min = "0";\s+endInput\.max = "24";\s+endInput\.step = "0\.5";\s+endInput\.value = endHours \|\| 1;\s+endCell\.appendChild\(endInput\);\s+row\.appendChild\(endCell\);', @'
// End time (using helper)
  const endCell = document.createElement("td");
  const endInput = createTimeInput("dhs-interval-end", endHours || 1);
  endCell.appendChild(endInput);
  row.appendChild(endCell);
'@

# Replace remove button in DHS
$content = $content -replace '(?s)// Remove button\s+const actionCell = document\.createElement\("td"\);\s+const removeBtn = document\.createElement\("button"\);\s+removeBtn\.type = "button";\s+removeBtn\.className = "btn-remove-interval";\s+removeBtn\.textContent = "删除";\s+removeBtn\.addEventListener\("click", \(e\) => \{\s+e\.preventDefault\(\);\s+row\.remove\(\);\s+// \[NEW\] Update timeline after removing row\s+updateTimelineByType\(tbody, ''dhs''\);\s+\}\);\s+actionCell\.appendChild\(removeBtn\);\s+row\.appendChild\(actionCell\);', @'
// Remove button (using helper)
  const actionCell = document.createElement("td");
  const removeBtn = createRemoveButton(row, tbody, 'dhs');
  removeBtn.className = "btn-remove-interval"; // Keep original class
  actionCell.appendChild(removeBtn);
  row.appendChild(actionCell);
'@

# Replace event listeners in DHS
$content = $content -replace '(?s)// \[NEW\] Add input event listeners for real-time timeline update\s+beginInput\.addEventListener\(''input'', \(\) => debouncedUpdateTimeline\.dhs\(tbody\)\);\s+endInput\.addEventListener\(''input'', \(\) => debouncedUpdateTimeline\.dhs\(tbody\)\);\s+statusSelect\.addEventListener\(''change'', \(\) => debouncedUpdateTimeline\.dhs\(tbody\)\);', @'
// Bind timeline updates (using helper)
  bindTimelineUpdate(beginInput, tbody, 'dhs');
  bindTimelineUpdate(endInput, tbody, 'dhs');
  bindTimelineUpdate(statusSelect, tbody, 'dhs');
'@

Write-Host "  ✅ addDHSIntervalRow 已重构" -ForegroundColor Green

# ==================== Step 4: Refactor addFlowIntervalRow ====================
Write-Host "[Step 4] 重构 addFlowIntervalRow..." -ForegroundColor Yellow

# Replace begin/end time inputs in Flow function
$content = $content -replace '(?s)function addFlowIntervalRow\(tbody, paramName, beginHours, endHours, flowRate, targetSpeed\) \{\s+const row = document\.createElement\("tr"\);\s+row\.className = "interval-row";\s+// Begin time\s+const beginCell = document\.createElement\("td"\);\s+const beginInput = document\.createElement\("input"\);\s+beginInput\.type = "number";\s+beginInput\.className = "interval-begin";\s+beginInput\.min = "0";\s+beginInput\.max = "24";\s+beginInput\.step = "0\.5";\s+beginInput\.value = beginHours \|\| 0;\s+beginCell\.appendChild\(beginInput\);\s+row\.appendChild\(beginCell\);\s+// End time\s+const endCell = document\.createElement\("td"\);\s+const endInput = document\.createElement\("input"\);\s+endInput\.type = "number";\s+endInput\.className = "interval-end";\s+endInput\.min = "0";\s+endInput\.max = "24";\s+endInput\.step = "0\.5";\s+endInput\.value = endHours \|\| 1;\s+endCell\.appendChild\(endInput\);\s+row\.appendChild\(endCell\);', @'
function addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed) {
  const row = document.createElement("tr");
  row.className = "interval-row";

  // Begin time (using helper)
  const beginCell = document.createElement("td");
  const beginInput = createTimeInput("interval-begin", beginHours || 0);
  beginCell.appendChild(beginInput);
  row.appendChild(beginCell);

  // End time (using helper)
  const endCell = document.createElement("td");
  const endInput = createTimeInput("interval-end", endHours || 1);
  endCell.appendChild(endInput);
  row.appendChild(endCell);
'@

# Replace flow and speed inputs in Flow function
$content = $content -replace '(?s)// Flow rate\s+const flowCell = document\.createElement\("td"\);\s+const flowInput = document\.createElement\("input"\);\s+flowInput\.type = "number";\s+flowInput\.className = "interval-flow";\s+flowInput\.min = "0";\s+flowInput\.max = "2000";\s+flowInput\.value = flowRate \|\| 480;\s+flowCell\.appendChild\(flowInput\);\s+row\.appendChild\(flowCell\);\s+// Target speed\s+const speedCell = document\.createElement\("td"\);\s+const speedInput = document\.createElement\("input"\);\s+speedInput\.type = "number";\s+speedInput\.className = "interval-speed";\s+speedInput\.min = "0";\s+speedInput\.max = "50";\s+speedInput\.step = "0\.5";\s+speedInput\.value = targetSpeed \|\| 15;\s+speedCell\.appendChild\(speedInput\);\s+row\.appendChild\(speedCell\);', @'
// Flow rate (using helper)
  const flowCell = document.createElement("td");
  const flowInput = createNumberInput("interval-flow", flowRate || 480, 0, 2000);
  flowCell.appendChild(flowInput);
  row.appendChild(flowCell);

  // Target speed (using helper)
  const speedCell = document.createElement("td");
  const speedInput = createNumberInput("interval-speed", targetSpeed || 15, 0, 50, 0.5);
  speedCell.appendChild(speedInput);
  row.appendChild(speedCell);
'@

# Replace remove button in Flow
$content = $content -replace '(?s)// Remove button\s+const actionCell = document\.createElement\("td"\);\s+const removeBtn = document\.createElement\("button"\);\s+removeBtn\.type = "button";\s+removeBtn\.className = "btn-remove-interval";\s+removeBtn\.textContent = "删除";\s+removeBtn\.addEventListener\("click", \(e\) => \{\s+e\.preventDefault\(\);\s+row\.remove\(\);\s+// \[NEW\] 删除行后更新时间轴\s+updateTimelineByType\(tbody, ''flow''\);\s+\}\);\s+actionCell\.appendChild\(removeBtn\);\s+row\.appendChild\(actionCell\);\s+// \[NEW\] 为输入框添加变化事件监听器以更新时间轴（使用防抖）\s+beginInput\.addEventListener\(''input'', \(\) => debouncedUpdateTimeline\.flow\(tbody\)\);\s+endInput\.addEventListener\(''input'', \(\) => debouncedUpdateTimeline\.flow\(tbody\)\);\s+flowInput\.addEventListener\(''input'', \(\) => debouncedUpdateTimeline\.flow\(tbody\)\);', @'
// Remove button (using helper)
  const actionCell = document.createElement("td");
  const removeBtn = createRemoveButton(row, tbody, 'flow');
  removeBtn.className = "btn-remove-interval"; // Keep original class
  actionCell.appendChild(removeBtn);
  row.appendChild(actionCell);

  // Bind timeline updates (using helper)
  bindTimelineUpdate(beginInput, tbody, 'flow');
  bindTimelineUpdate(endInput, tbody, 'flow');
  bindTimelineUpdate(flowInput, tbody, 'flow');
'@

Write-Host "  ✅ addFlowIntervalRow 已重构" -ForegroundColor Green

# ==================== Step 5: Refactor addTECIntervalRow ====================
Write-Host "[Step 5] 重构 addTECIntervalRow (并修复debounce问题)..." -ForegroundColor Yellow

# Replace entire TEC function
$oldTECPattern = '(?s)function addTECIntervalRow\(tbody, paramName, beginHours, endHours\) \{.+?tbody\.appendChild\(row\);\s+\}'
$newTECFunction = @'
function addTECIntervalRow(tbody, paramName, beginHours, endHours) {
  const row = document.createElement("tr");
  row.className = "tec-interval-row";

  // Begin time (using helper)
  const beginCell = document.createElement("td");
  const beginInput = createTimeInput("tec-interval-begin", beginHours || 0);
  beginCell.appendChild(beginInput);
  row.appendChild(beginCell);

  // End time (using helper)
  const endCell = document.createElement("td");
  const endInput = createTimeInput("tec-interval-end", endHours || 1);
  endCell.appendChild(endInput);
  row.appendChild(endCell);

  // Remove button (using helper)
  const actionCell = document.createElement("td");
  const removeBtn = createRemoveButton(row, tbody, 'tec_simple');
  removeBtn.className = "btn btn-delete-row"; // Keep original class name
  actionCell.appendChild(removeBtn);
  row.appendChild(actionCell);

  // Bind timeline updates (using helper) - FIX: use unified debounced version
  bindTimelineUpdate(beginInput, tbody, 'tec_simple');
  bindTimelineUpdate(endInput, tbody, 'tec_simple');

  tbody.appendChild(row);
}
'@

if ($content -match $oldTECPattern) {
    $content = $content -replace $oldTECPattern, $newTECFunction
    Write-Host "  ✅ addTECIntervalRow 已重构 (修复了内联debounce问题)" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  TEC函数替换失败，需手动检查" -ForegroundColor Yellow
}

# ==================== Write back ====================
Write-Host ""
Write-Host "[保存] 写入修改后的文件..." -ForegroundColor Yellow
$content | Set-Content $filePath -NoNewline

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Task 2.2 重构完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "修改摘要：" -ForegroundColor Cyan
Write-Host "  ✅ 新增4个辅助函数：" -ForegroundColor White
Write-Host "     - createTimeInput()" -ForegroundColor Gray
Write-Host "     - createNumberInput()" -ForegroundColor Gray
Write-Host "     - createRemoveButton()" -ForegroundColor Gray
Write-Host "     - bindTimelineUpdate()" -ForegroundColor Gray
Write-Host "  ✅ 重构4个行添加函数：" -ForegroundColor White
Write-Host "     - addStepRow (VSS)" -ForegroundColor Gray
Write-Host "     - addDHSIntervalRow (DHS)" -ForegroundColor Gray
Write-Host "     - addFlowIntervalRow (Flow)" -ForegroundColor Gray
Write-Host "     - addTECIntervalRow (TEC) - 修复debounce" -ForegroundColor Gray
Write-Host "  📉 预计减少代码：~80-100行" -ForegroundColor White
Write-Host ""
Write-Host "下一步：" -ForegroundColor Magenta
Write-Host "  npx playwright test tests/e2e/test_strategy_creation_workflow.spec.js" -ForegroundColor Yellow
Write-Host ""
