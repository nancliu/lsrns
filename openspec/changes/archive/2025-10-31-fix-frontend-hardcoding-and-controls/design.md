# Design Document: Frontend Hardcoding Fix & Unified Control System

## Architecture Overview

### Current Architecture (Problematic)

```
templates.html (contains duplicate control functions + hardcoded values)
├── createFlowIntervalControl() [HARDCODED] ❌
├── createVehicleTypeControl() [HARDCODED] ❌
├── addStepRow() [HARDCODED placeholders] ❌
└── addDHSIntervalRow() [DUPLICATE + HARDCODED] ❌
    │
    └── parameter_form.js (ALSO contains same functions)
        ├── addFlowIntervalRow(6 params) [JS VERSION]
        ├── addDHSIntervalRow(7 params) [JS VERSION]
        ├── createStepArrayControl() [JS VERSION]
        └── renderUnifiedVehicleTypeControl() [INCOMPLETE]

Data Flow Problem:
- template.default_value ──X──> Ignored (hardcoded values used instead)
- HTML placeholder (hardcoded) ──> Displayed to user ❌
```

### Target Architecture (Solution)

```
parameter_form.js (Single Source of Truth) ✅
├── Factory Pattern
│   ├── renderParameterControl(paramSchema)
│   │   └── Routes to appropriate renderer based on type
│   ├── renderIntegerControl(paramName, paramSchema) ✅
│   ├── renderNumberControl(paramName, paramSchema) ✅
│   ├── renderEnumControl(paramName, paramSchema) ✅
│   ├── renderStepArrayControl(paramSchema) ✅
│   │   └── Uses default_value from template schema
│   ├── renderDHSIntervalControl(paramSchema) ✅
│   │   └── Uses default_value from template schema
│   └── renderUnifiedVehicleTypeControl(template) ✅
│       └── Complete vehicle type control with state management
│
├── Helper Functions
│   ├── addFlowIntervalRow(tbody, paramName, ...values) ✅
│   ├── addDHSIntervalRow(tbody, paramName, ...values) ✅
│   └── deleteTableRow(row) ✅
│
└── State Management
    └── Vehicle Type Mode Listener
        ├── Detect restriction_mode change
        ├── Show/hide vehicle type controls
        └── Validate mutual exclusion

templates.html (Minimal - NO logic, NO hardcoding) ✅
├── Semantic HTML only
├── No inline styles (moved to CSS)
├── No hardcoded values
├── No duplicate functions
└── id/class hooks for JavaScript & CSS

Data Flow (Correct):
- template.default_value ──> renderParameterControl()
  ──> Control reads from paramSchema.default_value
  ──> input.value = paramSchema.default_value ✅
  ──> User sees correct template default ✅
```

## Data Flow: From Template to UI

### Current Flow (Broken)
```
API: GET /api/v1/control/templates/{id}
  ↓
Response JSON contains:
{
  "parameters_schema": [
    {
      "parameter_name": "target_speed",
      "default_value": 50,      ← IGNORED!
      "parameter_type": "integer"
    }
  ]
}
  ↓
generateFormFromTemplate() in parameter_form.js
  ↓
renderParameterControl() calls renderNumberControl()
  ↓
[BUG] HTML Hardcoding:
  placeholder="如: 60"  ← Shows this instead of default_value
  ↓
User Input: Shows hardcoded "60" as placeholder, confuses with real default
```

### Corrected Flow
```
API: GET /api/v1/control/templates/{id}
  ↓
Response JSON:
{
  "parameters_schema": [
    {
      "parameter_name": "target_speed",
      "default_value": 50,      ← WILL BE USED
      "parameter_type": "integer"
    }
  ]
}
  ↓
generateFormFromTemplate() in parameter_form.js
  ↓
renderParameterControl(paramSchema) for each parameter
  ↓
renderNumberControl(paramName, paramSchema):
  - Create input element
  - Set input.value = paramSchema.default_value  ← CORRECT!
  - Add comment: "// From template default_value"
  - No placeholder with hardcoded values
  ↓
User Input: Sees actual template default (50), not hardcoded placeholder
```

## Control Factory Pattern

### Factory Method Pattern for Parameter Rendering

```javascript
/**
 * Render appropriate control based on parameter schema type.
 * Single responsibility: Route to correct renderer.
 *
 * @param {Object} paramSchema - Parameter definition from template
 * @param {string} templateId - Template identifier (for context)
 * @returns {HTMLElement|null} Rendered control or null if skipped
 */
function renderParameterControl(paramSchema, templateId) {
  const paramType = paramSchema.parameter_type;

  // Route to appropriate renderer based on type
  const renderers = {
    'integer': () => renderIntegerControl(paramSchema.parameter_name, paramSchema),
    'number': () => renderNumberControl(paramSchema.parameter_name, paramSchema),
    'string': () => renderStringControl(paramSchema.parameter_name, paramSchema),
    'enum': () => renderEnumControl(paramSchema.parameter_name, paramSchema),
    'boolean': () => renderBooleanControl(paramSchema.parameter_name, paramSchema),
    'step_array': () => renderStepArrayControl(paramSchema),
    'dhs_interval_array': () => renderDHSIntervalControl(paramSchema),
    'vehicle_type_list': () => renderVehicleTypeListControl(paramSchema),
  };

  const renderer = renderers[paramType];
  if (!renderer) {
    console.warn(`[renderParameterControl] Unknown parameter type: ${paramType}`);
    return null;
  }

  try {
    return renderer();
  } catch (error) {
    console.error(`[renderParameterControl] Error rendering ${paramType}:`, error);
    return null;
  }
}
```

### Number Control Example (No Hardcoding)

```javascript
/**
 * Render integer input control with proper default_value loading.
 * Data source: paramSchema.default_value (from template)
 *
 * @param {string} paramName - Parameter name
 * @param {Object} paramSchema - Parameter definition with default_value
 * @returns {HTMLElement} Control element
 */
function renderIntegerControl(paramName, paramSchema) {
  const defaultValue = paramSchema.default_value ?? '';  // From template

  const input = document.createElement('input');
  input.type = 'number';
  input.id = `param-${paramName}`;
  input.name = paramName;

  // ✅ NO HARDCODED PLACEHOLDER
  // If template provides default_value, set it as actual value
  if (defaultValue !== '') {
    input.value = defaultValue;  // ← From template schema
    // Optional: placeholder for format hint only (NO VALUES)
    input.placeholder = `例如: ${paramSchema.example || 'Enter value'}`;
  } else {
    // No default - just format hint
    input.placeholder = 'Enter numeric value';
  }

  // Add constraints from template schema
  if (paramSchema.min !== undefined) input.min = paramSchema.min;
  if (paramSchema.max !== undefined) input.max = paramSchema.max;
  if (paramSchema.step !== undefined) input.step = paramSchema.step;

  return input;
}
```

## Vehicle Type Control State Management

### Restriction Mode State Machine

```
STATE: restriction_mode selector changes
  ↓
┌─────────────────────────────────────────────┐
│  restriction_mode = ? (user selects)       │
└─────────────────────────────────────────────┘
  ↓
  ├─→ "none" (不限制)
  │     └─→ Hide all vehicle type controls ✅
  │         - Hide allowed_vehicle_types ✅
  │         - Hide disallowed_vehicle_types ✅
  │
  ├─→ "allow" (仅允许)
  │     └─→ Show allowed_vehicle_types ONLY ✅
  │         - Show: allowed_vehicle_types (checkboxes)
  │         - Hide: disallowed_vehicle_types ✅
  │         - Uncheck all in disallowed section
  │
  └─→ "disallow" (不允许)
        └─→ Show disallowed_vehicle_types ONLY ✅
            - Show: disallowed_vehicle_types (checkboxes)
            - Hide: allowed_vehicle_types ✅
            - Uncheck all in allowed section
```

### Vehicle Type Control Structure (HTML)

```html
<!-- Unified Vehicle Type Control (SINGLE CONTROL, NOT DUPLICATE) -->
<div class="vehicle-type-control" data-control-type="unified">

  <!-- Section 1: Restriction Mode Selector -->
  <div class="vehicle-type-mode">
    <label for="restriction-mode">车型限制模式</label>
    <select id="restriction-mode" name="restriction_mode">
      <option value="none">不限制</option>
      <option value="allow">仅允许指定车型</option>
      <option value="disallow">不允许指定车型</option>
    </select>
  </div>

  <!-- Section 2: Allowed Vehicle Types (conditional) -->
  <div class="vehicle-type-section allowed-vehicles hidden">
    <h4>允许的车型</h4>
    <div class="checkbox-group">
      <label><input type="checkbox" name="allowed_vehicle_types" value="passenger_small"> 小客车</label>
      <label><input type="checkbox" name="allowed_vehicle_types" value="truck_large"> 大货车</label>
      <!-- ... more vehicle types ... -->
    </div>
  </div>

  <!-- Section 3: Disallowed Vehicle Types (conditional) -->
  <div class="vehicle-type-section disallowed-vehicles hidden">
    <h4>禁止的车型</h4>
    <div class="checkbox-group">
      <label><input type="checkbox" name="disallowed_vehicle_types" value="passenger_small"> 小客车</label>
      <label><input type="checkbox" name="disallowed_vehicle_types" value="truck_large"> 大货车</label>
      <!-- ... more vehicle types ... -->
    </div>
  </div>
</div>
```

### Vehicle Type Control JavaScript (State Management)

```javascript
/**
 * Initialize vehicle type control state management.
 * Listens to restriction_mode change and updates visibility.
 *
 * @param {HTMLElement} controlContainer - Vehicle type control container
 */
function initializeVehicleTypeControl(controlContainer) {
  const modeSelect = controlContainer.querySelector('[name="restriction_mode"]');
  const allowedSection = controlContainer.querySelector('.allowed-vehicles');
  const disallowedSection = controlContainer.querySelector('.disallowed-vehicles');
  const allowedCheckboxes = controlContainer.querySelectorAll('[name="allowed_vehicle_types"]');
  const disallowedCheckboxes = controlContainer.querySelectorAll('[name="disallowed_vehicle_types"]');

  /**
   * Update visibility and state based on restriction mode.
   * Single responsibility: Show/hide appropriate section.
   */
  function updateVehicleTypeVisibility() {
    const mode = modeSelect.value;

    switch (mode) {
      case 'allow':
        allowedSection.classList.remove('hidden');
        disallowedSection.classList.add('hidden');
        // Clear disallowed checkboxes
        disallowedCheckboxes.forEach(cb => cb.checked = false);
        break;

      case 'disallow':
        disallowedSection.classList.remove('hidden');
        allowedSection.classList.add('hidden');
        // Clear allowed checkboxes
        allowedCheckboxes.forEach(cb => cb.checked = false);
        break;

      case 'none':
      default:
        allowedSection.classList.add('hidden');
        disallowedSection.classList.add('hidden');
        // Clear all checkboxes
        [...allowedCheckboxes, ...disallowedCheckboxes].forEach(cb => cb.checked = false);
        break;
    }
  }

  // Listen to mode change
  modeSelect.addEventListener('change', updateVehicleTypeVisibility);

  // Initialize on load
  updateVehicleTypeVisibility();
}
```

## CSS Layout Optimization

### Problem: Current Layout Issues
- Hard-coded widths in HTML (style="") ❌
- Inconsistent spacing between controls
- Tables overflow on mobile
- Labels too long with no wrapping
- No responsive design

### Solution: Unified CSS System

```css
/* templates-forms.css - Centralized form styling */

/* Control Container */
.param-control-wrapper {
  display: grid;
  gap: 8px;  /* Consistent spacing */
  padding: 12px;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 16px;
}

/* Label Styling */
.param-control-wrapper label {
  display: block;
  font-weight: 500;
  margin-bottom: 4px;
  word-break: break-word;  /* Long labels wrap */
}

.param-control-wrapper .required {
  color: #e74c3c;
}

/* Input Controls */
.param-control-wrapper input[type="number"],
.param-control-wrapper input[type="text"],
.param-control-wrapper select,
.param-control-wrapper textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #bdc3c7;
  border-radius: 4px;
  font-family: inherit;
  font-size: 14px;
}

/* Table Controls (Responsive) */
.param-table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  overflow-x: auto;  /* Horizontal scroll on mobile */
}

@media (max-width: 768px) {
  .param-table {
    font-size: 12px;  /* Smaller on mobile */
  }

  .param-table th,
  .param-table td {
    padding: 6px;  /* Tighter spacing */
  }
}

/* Vehicle Type Control */
.vehicle-type-control .vehicle-type-section.hidden {
  display: none;
}

.vehicle-type-control .checkbox-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 8px;
}
```

## Testing Strategy

### Unit Test Coverage
- `addFlowIntervalRow()` - Correct parameter passing
- `addDHSIntervalRow()` - Correct interval structure
- `renderUnifiedVehicleTypeControl()` - Correct show/hide logic
- Default value loading from template schema

### E2E Test Coverage
- Parameter form rendering from template
- Vehicle type control mode switching
- Table row addition/deletion
- Form validation with default values
- Data consistency across control types

## Migration Path

### Step 1: Code Consolidation
1. Identify all duplicate functions in templates.html
2. Move to parameter_form.js with unified signatures
3. Update templates.html to remove function definitions

### Step 2: Remove Hardcoding
1. Find all hardcoded placeholder/value attributes
2. Replace with dynamic loading from paramSchema
3. Add inline comments documenting data source

### Step 3: Vehicle Type Integration
1. Implement renderUnifiedVehicleTypeControl()
2. Add restriction_mode listener
3. Test show/hide and mutual exclusion

### Step 4: CSS Refactoring
1. Move inline styles to templates-forms.css
2. Implement responsive grid layout
3. Test on mobile viewports

## Rollback Strategy

If issues arise:
1. Revert JS changes: `git revert <commit>`
2. CSS stays isolated, safe to keep
3. No database schema changes, data unaffected
4. Frontend-only change, API unaffected

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Zero hardcoded values in HTML | 100% | grep -c 'placeholder="[0-9]' |
| Duplicate function elimination | 100% | No same function in 2 files |
| Vehicle type mode switching | 100% | E2E test pass rate |
| Template default loading | 100% | inspect element: input.value matches template |
| Responsive design | Mobile+Desktop | Manual viewport testing |

