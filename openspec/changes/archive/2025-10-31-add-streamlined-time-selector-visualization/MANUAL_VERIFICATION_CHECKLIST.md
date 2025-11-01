# Manual Verification Checklist - Phase 4 TEC Fixes

**Date**: 2025-10-31
**Template**: TEC Vehicle Restriction (`tec_vehicle_restriction`)
**Change ID**: `add-streamlined-time-selector-visualization`

## ⚠️ E2E Test Status

**Automated Test Created**: `tests/e2e/test_tec_vehicle_restriction_fixes.spec.js`

**Current Issue**: Step 2 → Step 3 transition not working in automated test
- Template selection: ✅ Working
- Edge selection: ✅ Working (edges found and selected)
- Next button: ✅ Clickable and enabled
- **Step 3 display**: ❌ Not appearing after clicking next

**Recommendation**: Use manual testing until step transition bug is fixed.

## Pre-Testing Steps

### ⚠️ IMPORTANT: Clear Browser Cache

Before testing, **you MUST clear the browser cache** to ensure the latest JavaScript changes are loaded:

1. **Chrome/Edge**: Ctrl+Shift+Delete → Clear cached images and files
2. **Firefox**: Ctrl+Shift+Delete → Cached Web Content
3. **Or**: Hard refresh the page: Ctrl+F5 or Ctrl+Shift+R

### Verify JavaScript File is Loaded

1. Open browser DevTools (F12)
2. Go to Network tab
3. Refresh page (Ctrl+F5)
4. Find `parameter_form.js` in the network requests
5. Check file size - should be ~110KB (larger than before due to new functions)
6. Check response - should contain new functions like `renderUnifiedVehicleTypeControl`

## Screenshot Analysis

Based on your screenshot, I see the following **potential issues**:

### ❌ Issue 1: Time Interval Table Shows Vehicle Type Checkboxes

**What I see in screenshot**:
- Time interval table has columns: "开始时间 (小时)" and what appears to be checkboxes for "车型"

**Expected behavior**:
- TEC interval table should have ONLY 2 columns:
  - "开始时间 (小时)" (Start time)
  - "结束时间 (小时)" (End time)
  - "操作" (Action - delete button)
- NO vehicle type checkboxes in the table rows

**Possible causes**:
1. Browser cache not cleared (most likely)
2. JavaScript file not reloaded
3. Wrong template being displayed

### ✅ What Looks Correct in Screenshot

1. Timeline visualization appears at the top (colored bars visible)
2. 6 路段 (6 segments) shown
3. 2.34 km total length
4. G4202 route
5. Step 3 "配置策略参数" active

## Detailed Verification Steps

### Test 1: Verify entrance_edges Parameter is Hidden

**Expected**: ✅
- [x] NO input field for "受管控的收费站入口edge ID列表"
- [x] NO textarea or text input for entering edge IDs

**Screenshot shows**:
- ✅ I don't see an edge ID input field (CORRECT)

**Status**: ✅ PASS

---

### Test 2: Verify Time Interval Table Structure

**Expected**: ✅
- [x] Table has 3 columns only: 开始时间, 结束时间, 操作
- [x] Default: 2 rows showing (7-9, 17-19)
- [x] NO vehicle type checkboxes in table
- [x] "+ 添加时间区间" button below table

**Screenshot shows**:
- ❌ Table appears to have vehicle type checkboxes (INCORRECT)
- Need to verify after cache clear

**Action Required**:
1. Clear browser cache
2. Hard refresh (Ctrl+F5)
3. Re-check table structure

---

### Test 3: Verify Timeline Loads Default Values

**Expected**: ✅
- [x] Timeline shows 2 blue segments
- [x] Segment 1: 7:00-9:00 (morning peak)
- [x] Segment 2: 17:00-19:00 (evening peak)
- [x] Timeline uses blue color (#3b82f6) for simple intervals

**Screenshot shows**:
- ✅ Timeline visible with colored segments (appears correct)

**Status**: ✅ LIKELY PASS (verify exact time ranges)

---

### Test 4: Verify Restriction Mode Dropdown

**Expected**: ✅
- [x] "限制模式" dropdown present
- [x] Options: "禁止模式 - 选择要禁止的车型", "允许模式 - 仅允许选中的车型"
- [x] Default selected: "禁止模式"

**Screenshot shows**:
- Cannot clearly see this dropdown in screenshot
- Need to scroll down to verify

**Action Required**:
1. Scroll down in configuration form
2. Find "限制模式" dropdown
3. Verify options

---

### Test 5: Verify Unified Vehicle Type Control

**Expected**: ✅
- [x] SINGLE checkbox group for vehicle types
- [x] Label: "禁止进入的车辆类型" (when disallow_mode)
- [x] Checkboxes: 乘用车, 公交车, 货车, 应急车
- [x] Hint: "选中的车型将被禁止进入，其他车型可自由通行"
- [x] NO separate "禁止车型" and "允许车型" sections

**Screenshot shows**:
- Cannot see this section in screenshot (need to scroll)

**Action Required**:
1. Scroll down in configuration form
2. Find vehicle type section
3. Verify:
   - Only ONE checkbox group (not two)
   - Label changes when restriction mode changes
   - Checkboxes clear when mode changes

**Test Steps**:
1. Initial state: restriction_mode = "disallow_mode"
   - Label should be: "禁止进入的车辆类型"
2. Change to: "allow_mode"
   - Label should change to: "允许进入的车辆类型"
   - Checkboxes should clear
   - Hint should change

---

### Test 6: Verify Strategy Name and Description Fields

**Expected**: ✅
- [x] Strategy name: Full-width input field
- [x] Description: Multi-line textarea (3+ rows)
- [x] Both fields: 100% width, comfortable for long text

**Screenshot shows**:
- Cannot see these fields in screenshot (they should be at the top of the form)

**Action Required**:
1. Scroll to top of configuration form
2. Check strategy name field width
3. Check description field type (should be textarea, not input)

---

### Test 7: Verify Hint Text

**Expected**: ✅
- [x] Only ONE hint below time interval table
- [x] Hint text comes from template schema (not hardcoded)

**Screenshot shows**:
- Cannot clearly see hint text in screenshot

**Action Required**:
1. Check if there's hint text below time interval table
2. Verify only ONE hint (not duplicate)

---

## Common Issues and Solutions

### Issue: Old JavaScript Still Loading

**Symptoms**:
- Time interval table shows vehicle type checkboxes
- Two separate vehicle type sections (disallow + allow)
- entrance_edges input field still visible

**Solution**:
```bash
# 1. Clear browser cache completely
# 2. Restart browser
# 3. Hard refresh: Ctrl+F5
# 4. Check DevTools Console for errors
# 5. Verify parameter_form.js file timestamp in Network tab
```

### Issue: JavaScript Errors in Console

**Action**:
1. Open DevTools (F12)
2. Go to Console tab
3. Look for red errors
4. Share error messages if found

### Issue: Changes Not Applied

**Possible causes**:
1. API server not reloaded after JavaScript changes
2. Browser using cached version
3. Wrong template being displayed

**Solution**:
```powershell
# Restart API server
# Press Ctrl+C in the terminal running the server
# Then run again:
.\start_api.ps1
```

## Expected vs Actual Comparison

| Feature | Expected | Screenshot Shows | Status |
|---------|----------|------------------|--------|
| entrance_edges hidden | Hidden | ✅ Not visible | ✅ PASS |
| Time interval table | 3 columns (start, end, action) | ❌ Shows vehicle checkboxes? | ❌ NEEDS VERIFICATION |
| Timeline default values | 2 blue segments (7-9, 17-19) | ✅ Timeline visible | ⚠️ VERIFY EXACT VALUES |
| Restriction mode dropdown | Present with 2 options | Not visible in screenshot | ⚠️ SCROLL TO VERIFY |
| Unified vehicle control | Single checkbox group | Not visible in screenshot | ⚠️ SCROLL TO VERIFY |
| Strategy name field | Full width | Not visible in screenshot | ⚠️ SCROLL TO VERIFY |
| Description field | Textarea (multi-line) | Not visible in screenshot | ⚠️ SCROLL TO VERIFY |
| Single hint | One hint only | Not clearly visible | ⚠️ VERIFY |

## Next Steps

### Step 1: Clear Cache and Reload ⚠️ CRITICAL

```
1. Close all browser tabs for the application
2. Clear browser cache (Ctrl+Shift+Delete)
3. Restart browser
4. Navigate to: http://localhost:8000/control/templates.html
5. Hard refresh: Ctrl+F5
```

### Step 2: Full Screenshot Verification

Please provide **3 screenshots**:

1. **Screenshot 1**: Full configuration form (scroll to top)
   - Should show: strategy name, description fields

2. **Screenshot 2**: Middle of configuration form
   - Should show: restriction_intervals table + timeline
   - Verify table has ONLY 3 columns (no vehicle checkboxes in table)

3. **Screenshot 3**: Bottom of configuration form
   - Should show: restriction_mode dropdown + unified vehicle type control

### Step 3: Check Browser Console

```
1. Open DevTools (F12)
2. Go to Console tab
3. Look for:
   - "[renderParameterControl] Skipping entrance_edges parameter"
   - "[renderParameterControl] Skipping disallow_vehicle_types"
   - "[renderParameterControl] Skipping allowed_vehicle_types"
4. Share any errors (red text)
```

### Step 4: Verify JavaScript Loading

```
1. DevTools → Network tab
2. Filter: JS
3. Find: parameter_form.js
4. Check:
   - Status: 200 OK
   - Size: ~110KB (not from cache)
   - Preview: Search for "renderUnifiedVehicleTypeControl"
```

## Debug Checklist

- [ ] Browser cache cleared
- [ ] Hard refresh performed (Ctrl+F5)
- [ ] No JavaScript errors in console
- [ ] parameter_form.js loaded (not from cache)
- [ ] File contains new functions (check in Network→Preview)
- [ ] Correct template selected (TEC vehicle restriction)
- [ ] Step 3 (配置参数) active

## Contact Points

If issues persist after cache clear:

1. **Share Console Errors**: Copy any red errors from DevTools Console
2. **Share Network Info**: Screenshot of parameter_form.js in Network tab
3. **Share Full Form Screenshot**: Scroll through entire form and screenshot each section

## Expected Console Logs (After Cache Clear)

When the form loads correctly, you should see these console logs:

```
[renderParameterControl] Skipping entrance_edges parameter (auto-filled from edge selector)
[renderParameterControl] Skipping disallow_vehicle_types (handled by unified vehicle type control)
[renderParameterControl] Skipping allowed_vehicle_types (handled by unified vehicle type control)
```

If you don't see these logs, the new JavaScript hasn't loaded yet.
