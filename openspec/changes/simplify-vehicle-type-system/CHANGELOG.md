# CHANGELOG - Parameter Form Bug Fixes

## Version: v0.9.1-dev
## Date: 2025-11-01
## Related Change: simplify-vehicle-type-system

---

## Overview

This changelog documents critical bug fixes for the strategy template parameter form rendering system, specifically addressing issues introduced during the vehicle type system simplification. All fixes maintain backward compatibility and improve user experience.

---

## Bug Fixes

### 1. TEC Duplicate Vehicle Type Controls

**Issue**: TEC (Toll Entrance Control) templates were displaying BOTH `disallow_vehicle_types` and `allowed_vehicle_types` control sections simultaneously, when only one should appear based on the `restriction_mode` selection.

**Root Cause**: Two parallel parameter rendering systems existed in `templates.html`:
- System 1 (line 820): Main rendering loop
- System 2 (line 1531): `renderParametersSection()` function

Only System 1 was initially fixed, leaving System 2 with the old logic.

**Files Changed**:
- `frontend/control/templates.html` (lines 1530-1563)

**Changes**:
```javascript
// Added restriction_mode detection
const hasRestrictionMode = template.parameters_schema.some(
  p => p.parameter_name === 'restriction_mode'
);

// Skip rendering individual vehicle type parameters
if (hasRestrictionMode &&
    (param.parameter_name === 'disallow_vehicle_types' ||
     param.parameter_name === 'allowed_vehicle_types')) {
  return; // Skip rendering
}

// Inject unified control after restriction_mode
if (hasRestrictionMode && param.parameter_name === 'restriction_mode') {
  const unifiedControl = window.renderUnifiedVehicleTypeControl(template);
  form.appendChild(unifiedControl);
}
```

**Impact**:
- ✅ TEC templates now show single unified vehicle type control
- ✅ Control dynamically switches label/hint based on restriction_mode
- ✅ Data collection correctly maps to either disallow or allowed parameter

**Testing**: Verified with screenshots showing correct single control rendering.

---

### 2. TEC Vehicle Type Controls Not Rendering

**Issue**: TEC configuration page showed no vehicle type checkboxes, only hint text.

**Root Cause**: The `renderUnifiedVehicleTypeControl()` function expected `enum_values` to be directly defined in the parameter schema, but TEC templates use `enum_name: "vehicle_types_category"` to reference external enumeration definitions. When `enum_values` was empty, no checkboxes were rendered.

**Files Changed**:
- `frontend/control/js/parameter_form.js` (lines 2613-2636)

**Changes**:
```javascript
// Get enum values - handle both direct and reference
let enumValues = disallowParam?.enum_values || allowParam?.enum_values || [];

// If enum_values not found, check enum_name
if (enumValues.length === 0) {
  const enumName = disallowParam?.enum_name || allowParam?.enum_name;

  // For TEC templates, use standard 3-category fallback
  if (enumName === 'vehicle_types_category' || enumValues.length === 0) {
    enumValues = [
      { value: 'passenger', label: '客车', description: '...' },
      { value: 'truck', label: '货车', description: '...' },
      { value: 'delivery', label: '特种车辆', description: '...' }
    ];
  }
}
```

**Impact**:
- ✅ TEC templates now correctly render vehicle type checkboxes
- ✅ Supports both `enum_values` (direct) and `enum_name` (reference) approaches
- ✅ Fallback to standard 3-category system ensures robustness

**Testing**: Verified with TEC template rendering showing correct checkboxes.

---

### 3. VSS Button Style Inconsistency

**Issue**: VSS (Variable Speed Sign) "Add Step" button displayed English text "Add Step" instead of Chinese "添加限速步骤", inconsistent with other control buttons.

**Files Changed**:
- `frontend/control/js/parameter_form.js` (lines 773-783)

**Changes**:
```javascript
const addBtn = document.createElement("button");
addBtn.type = "button";
addBtn.className = "btn btn-add-interval";  // Changed from btn-add-step
addBtn.textContent = "+ 添加限速步骤";  // Changed from English "Add Step"
addBtn.addEventListener("click", (e) => {
  e.preventDefault();
  addStepRow(tbody, paramName, 0, 100, stepStructure);
  validateParameterOnChange(tbody, schema);
  updateTimelineByType(tbody, 'vss');
});
```

**Impact**:
- ✅ Consistent Chinese UI across all control buttons
- ✅ CSS class alignment with other interval controls
- ✅ Improved user experience for Chinese-speaking users

---

### 4. Deprecated Function Call

**Issue**: `templates.html` line 1481 called deprecated `createVehicleTypeControl()` function that no longer existed.

**Files Changed**:
- `frontend/control/templates.html` (line 1481)
- `frontend/control/js/parameter_form.js` (line 2807)

**Changes**:
```javascript
// templates.html - Use exported function with fallback
control = window.renderEnumArrayControl ?
  window.renderEnumArrayControl(param.parameter_name, param) :
  createStringControl(param);

// parameter_form.js - Export the function
window.renderEnumArrayControl = renderEnumArrayControl;
```

**Impact**:
- ✅ Removed dependency on deprecated function
- ✅ Proper fallback mechanism for edge cases
- ✅ Cleaner function exports

---

### 5. Data Collection for Unified Vehicle Type Control

**Issue**: Unified vehicle type control used `name="vehicle_types"` but data collection logic didn't map it correctly to `disallow_vehicle_types` or `allowed_vehicle_types` based on the current restriction mode.

**Files Changed**:
- `frontend/control/templates.html` (lines 3126-3142)

**Changes**:
```javascript
if (param.parameter_type === 'enum_array') {
  // Special handling for TEC restriction mode vehicle types
  if ((param.parameter_name === 'disallow_vehicle_types' ||
       param.parameter_name === 'allowed_vehicle_types') &&
      configuredParams.restriction_mode) {

    // Check if unified control exists
    const unifiedCheckboxes = document.querySelectorAll(
      `input[name="vehicle_types"][type="checkbox"]:checked`
    );

    if (unifiedCheckboxes.length > 0) {
      const value = Array.from(unifiedCheckboxes).map(cb => cb.value);
      const currentMode = configuredParams.restriction_mode;

      // Only collect the parameter matching current mode
      if ((currentMode === 'disallow_mode' &&
           param.parameter_name === 'disallow_vehicle_types') ||
          (currentMode === 'allow_mode' &&
           param.parameter_name === 'allowed_vehicle_types')) {
        configuredParams[param.parameter_name] = value;
      }
      return;
    }
  }

  // Normal checkbox collection for other controls
  // ...
}
```

**Impact**:
- ✅ Correct data mapping based on restriction mode
- ✅ API receives only the active parameter (not both)
- ✅ Clean payload structure

---

## Template Content Updates

### 6. DHS Passenger-Only Template - Remove "公交车" References

**Issue**: `dhs_passenger_only.json` template still contained references to deprecated "公交车" (bus) category in descriptions.

**Files Changed**:
- `templates/control_strategies/dynamic_hard_shoulder/dhs_passenger_only.json`

**Changes**:
- **Line 4**: Template description
  - Before: "应急车道仅允许乘用车和公交车通行..."
  - After: "应急车道仅允许客车通行，禁止货车。特种车辆可在关闭时段通行。"

- **Line 31**: `intervals` parameter description
  - Before: "...（预设为仅允许客车和公交，禁止货车）"
  - After: "...（预设为仅允许客车，禁止货车）"

- **Line 81**: `allowed_vehicle_types` description
  - Before: "...（全局默认值，预设为仅客车和公交）"
  - After: "...（全局默认值，预设为仅客车）"

**Impact**:
- ✅ Consistent with new 3-category vehicle type system
- ✅ Removes all references to deprecated "公交车" category
- ✅ Accurate descriptions matching actual implementation

---

### 7. TEC Emergency Closure - Remove Contact Fields

**Issue**: `tec_emergency_closure.json` template contained unnecessary "负责人员或部门" (contact_person) and "应急联系电话或方式" (emergency_contact) parameters that were not used in implementation.

**Files Changed**:
- `templates/control_strategies/toll_entrance_control/tec_emergency_closure.json`

**Changes**: Removed two parameters (lines 81-96):
```json
// REMOVED:
{
  "parameter_name": "contact_person",
  "parameter_type": "string",
  "description": "负责人员或部门（用于文档和应急沟通）",
  "required": false,
  "default_value": "",
  "unit": null
},
{
  "parameter_name": "emergency_contact",
  "parameter_type": "string",
  "description": "应急联系电话或方式",
  "required": false,
  "default_value": "",
  "unit": null
}
```

**Impact**:
- ✅ Cleaner template definition
- ✅ Removed unused parameters from UI
- ✅ Simplified parameter configuration process

---

## Documentation Created

### 8. Parameter Form Architecture Documentation

**File**: `docs/frontend/parameter_form_architecture.md`

**Content**:
- Complete architecture overview with ASCII diagrams
- Parameter type to rendering function mappings
- Detailed explanation of dual rendering system problem
- TEC unified vehicle type control implementation
- enum_name reference handling mechanism
- Data flow diagrams
- Known issues and technical debt
- Testing checklists
- Version history

**Purpose**: Provide comprehensive technical documentation to prevent future bugs and aid maintenance.

---

### 9. Vehicle Type System Documentation

**File**: `docs/templates/vehicle_type_system.md`

**Content**:
- Two-layer vehicle type architecture (UI 3-category → SUMO 6-detailed)
- Configuration file locations and structures
- Template reference methods (enum_values vs enum_name)
- Frontend enum_name fallback mechanism
- Usage patterns across strategy types (DHS, TEC, VSS)
- Data flow from user selection to SUMO simulation
- Maintenance guide and testing checklist
- Migration history from old 5-category system

**Purpose**: Centralize vehicle type system knowledge and guide future development.

---

## Technical Debt Identified

### 1. Dual Rendering System ⚠️

**Problem**: Two parallel parameter rendering systems coexist in `templates.html`:
- System 1 (line 820): Main rendering loop
- System 2 (line 1531): `renderParametersSection()` function

**Impact**:
- Code duplication
- Bug fixes must be applied twice
- Increased maintenance cost

**Recommended Fix**:
```javascript
function renderParametersSection(container, template) {
  // Delegate to System 1 instead of duplicating logic
  const form = generateFormFromTemplate(template);
  container.appendChild(form);
}
```

**Benefits**:
- Single rendering path
- No code duplication
- Easier to maintain

---

### 2. Hardcoded Fallback Values

**Problem**: `renderUnifiedVehicleTypeControl()` has hardcoded 3-category fallback when `enum_name` is detected.

**Impact**:
- If `vehicle_types_enum.json` changes, fallback becomes outdated
- Maintenance burden to keep in sync

**Recommended Fix**:
- Fetch `vehicle_types_enum.json` dynamically
- Cache it for performance
- Remove hardcoded fallback

---

### 3. Missing Parameter Type Registry

**Problem**: Parameter type to rendering function mappings are scattered across multiple if-else and switch statements.

**Recommended Fix**:
```javascript
const PARAMETER_TYPE_REGISTRY = {
  'string': { render: renderStringControl, validate: validateString },
  'enum_array': { render: renderEnumArrayControl, validate: validateEnumArray },
  'step_array': { render: renderStepArrayControl, validate: validateStepArray },
  // ...
};

function renderParameter(param) {
  const handler = PARAMETER_TYPE_REGISTRY[param.parameter_type];
  if (!handler) {
    console.warn('Unknown parameter type:', param.parameter_type);
    return renderStringControl(param); // fallback
  }
  return handler.render(param);
}
```

**Benefits**:
- Centralized type handling
- Easy to extend
- Better error handling

---

## Testing Summary

### Manual Testing Performed

- ✅ TEC templates: Vehicle type control renders correctly (single unified control)
- ✅ TEC restriction mode switching: Labels and hints update dynamically
- ✅ TEC data collection: Correct parameter mapping (disallow vs allowed)
- ✅ DHS templates: All vehicle type references use new 3-category system
- ✅ VSS templates: "添加限速步骤" button displays correctly in Chinese
- ✅ All strategy types: No hardcoded example data in forms
- ✅ All strategy types: Parameter values load from template default_value

### User-Reported Issues

All reported issues have been resolved:
1. ✅ TEC duplicate controls → Fixed (unified control)
2. ✅ TEC controls not rendering → Fixed (enum_name fallback)
3. ✅ VSS button English text → Fixed (Chinese text)
4. ✅ DHS "公交车" references → Fixed (removed)
5. ✅ TEC contact fields → Fixed (removed from template)

### Known Limitations

- Dual rendering system still exists (scheduled for future refactoring)
- Hardcoded fallback values require manual sync with enum definition
- No automated E2E tests for parameter form rendering (Playwright tests pending)

---

## Migration Guide

### For Template Developers

**If using direct enum_values definition**:
- ✅ Continue to work without changes
- ⚠️ Consider migrating to `enum_name` reference for easier maintenance

**If migrating to enum_name reference**:
1. Remove `enum_values` array from parameter definition
2. Add `"enum_name": "vehicle_types_category"`
3. Set `"enum_values": null`
4. Verify frontend renders correctly (fallback mechanism active)

**Example**:
```json
// Before (direct definition)
{
  "parameter_name": "allowed_vehicle_types",
  "parameter_type": "enum_array",
  "enum_values": [
    { "value": "passenger", "label": "客车", "description": "..." },
    { "value": "truck", "label": "货车", "description": "..." },
    { "value": "delivery", "label": "特种车辆", "description": "..." }
  ],
  "default_value": ["passenger"]
}

// After (enum_name reference)
{
  "parameter_name": "allowed_vehicle_types",
  "parameter_type": "enum_array",
  "enum_name": "vehicle_types_category",
  "enum_values": null,
  "default_value": ["passenger"]
}
```

### For Frontend Developers

**When adding new parameter types**:
1. Add rendering function in `parameter_form.js`
2. Export function to `window` object if needed by templates.html
3. Update BOTH rendering systems (lines 820 and 1531) in `templates.html`
4. Add data collection logic in `collectParameterValues()`
5. Update documentation in `parameter_form_architecture.md`

**When fixing rendering bugs**:
1. ⚠️ Remember the dual rendering system
2. Apply fixes to BOTH System 1 (line 820) and System 2 (line 1531)
3. Test with multiple strategy types (DHS, TEC, VSS)
4. Verify data collection works correctly

---

## Related Changes

This changelog is part of the **simplify-vehicle-type-system** OpenSpec change:
- See [openspec/changes/simplify-vehicle-type-system/proposal.md](./proposal.md) for original proposal
- See [openspec/changes/simplify-vehicle-type-system/design.md](./design.md) for design details
- See [openspec/changes/simplify-vehicle-type-system/tasks.md](./tasks.md) for implementation tasks

---

## Contributors

- **Implementation**: Claude Code Agent
- **Testing & Verification**: Development Team
- **User Feedback**: Project Stakeholder

---

## Next Steps

### Immediate (Priority: High)

- [ ] Add Playwright E2E tests for parameter form rendering
- [ ] Test all 15+ strategy templates for correct rendering
- [ ] Verify data collection for edge cases

### Short-term (Priority: Medium)

- [ ] Refactor to eliminate dual rendering system
- [ ] Create parameter type registry
- [ ] Migrate all templates to enum_name reference

### Long-term (Priority: Low)

- [ ] Dynamic loading of vehicle_types_enum.json
- [ ] Automated sync checking between templates and enum definitions
- [ ] Performance optimization for large parameter schemas

---

**Last Updated**: 2025-11-01
**Version**: v0.9.1-dev
**Status**: Fixes Deployed, Documentation Complete
