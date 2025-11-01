/**
 * Parameter Form Generator for Strategy Templates (v2.0)
 *
 * Generates dynamic parameter forms from template schemas.
 *
 * Features:
 * - Automatic form generation from parameter schemas
 * - Real-time validation with error/warning display
 * - Unified timeline update system (4 types: VSS/DHS/Flow/TEC)
 * - Reusable input creation helpers
 * - Centralized validation logic
 * - XML preview generation with syntax highlighting
 * - Support for complex parameter types (arrays, time ranges, etc.)
 *
 * Code Organization:
 * 1. Utility Functions (debounce)
 * 2. Timeline Update System (unified + deprecated legacy)
 * 3. Validation Helpers (validators object + error display)
 * 4. Row Creation Helpers (createTimeInput, createNumberInput, etc.)
 * 5. Form Generation (generateFormFromTemplate)
 * 6. Parameter Control Renderers (renderXxxControl functions)
 * 7. Validation Functions (validateNumberRange, etc.)
 * 8. Form Submission & Preview (extractFormParameters, generateXMLPreview)
 * 9. UI Utilities (showNotification)
 *
 * @module parameter_form
 * @version 2.0
 * @refactored 2025-11-01 - Phase 2 code refactoring (Tasks 2.1-2.4)
 */

// ==================== Timeline Update Helper (时间轴更新辅助函数) ====================

/**
 * 防抖函数：延迟执行，避免频繁更新
 * @param {Function} func - 要防抖的函数
 * @param {number} wait - 延迟毫秒数
 * @returns {Function} 防抖后的函数
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

  // ==================== Unified Timeline Update Functions ====================

  /**
   * Timeline configuration presets for different strategy types.
   * Each config defines how to extract data from table rows and update timeline.
   */
  const TIMELINE_CONFIGS = {
    vss: {
      containerClass: '.step-array-control-enhanced',
      rowSelector: '.step-row',
      timelineType: 'speed',
      extractData: (row) => {
        const timeInput = row.querySelector('.step-time');
        const speedInput = row.querySelector('.step-speed');
        if (timeInput && speedInput) {
          return {
            time_hours: parseFloat(timeInput.value) || 0,
            speed_kmh: parseFloat(speedInput.value) || 0
          };
        }
        return null;
      },
      sortData: (data) => data.sort((a, b) => a.time_hours - b.time_hours)
    },
    dhs: {
      containerClass: '.dhs-interval-control-enhanced',
      rowSelector: '.dhs-interval-row',
      timelineType: 'dhs',
      extractData: (row) => {
        const beginInput = row.querySelector('.dhs-interval-begin');
        const endInput = row.querySelector('.dhs-interval-end');
        const statusSelect = row.querySelector('.dhs-interval-status');
        if (beginInput && endInput && statusSelect) {
          return {
            begin_hours: parseFloat(beginInput.value) || 0,
            end_hours: parseFloat(endInput.value) || 0,
            status: statusSelect.value || 'CLOSED'
          };
        }
        return null;
      }
    },
    flow: {
      containerClass: '.flow-interval-control-enhanced',
      rowSelector: '.interval-row',
      timelineType: 'flow',
      extractData: (row) => {
        const beginInput = row.querySelector('.interval-begin');
        const endInput = row.querySelector('.interval-end');
        const flowInput = row.querySelector('.interval-flow');
        if (beginInput && endInput && flowInput) {
          return {
            begin_hours: parseFloat(beginInput.value) || 0,
            end_hours: parseFloat(endInput.value) || 0,
            flow_vph: parseFloat(flowInput.value) || 0
          };
        }
        return null;
      }
    },
    tec_simple: {
      containerClass: '.tec-interval-control-enhanced',
      rowSelector: '.tec-interval-row',
      timelineType: 'simple_interval',
      extractData: (row) => {
        const beginInput = row.querySelector('.tec-interval-begin');
        const endInput = row.querySelector('.tec-interval-end');
        if (beginInput && endInput) {
          const beginHours = parseFloat(beginInput.value) || 0;
          const endHours = parseFloat(endInput.value) || 0;
          if (endHours > beginHours && beginHours >= 0 && endHours <= 24) {
            return { begin_hours: beginHours, end_hours: endHours };
          }
        }
        return null;
      }
    }
  };

  /**
   * Unified timeline update function - handles all strategy types.
   * Replaces 4 duplicate functions: updateTimelineFromTable, updateDHSTimelineFromTable,
   * updateFlowTimelineFromTable, updateTECTimelineFromTable.
   *
   * @param {HTMLElement} tbody - Table body element containing parameter rows
   * @param {Object} config - Configuration object with extraction logic
   */
  function updateTimeline(tbody, config) {
    if (!window.TimelineVisualizer) {
      console.warn('[updateTimeline] TimelineVisualizer not available');
      return;
    }

    const container = tbody.closest(config.containerClass);
    if (!container) {
      console.warn(`[updateTimeline] Container ${config.containerClass} not found`);
      return;
    }

    const timelineElement = container.querySelector('.parameter-timeline');
    if (!timelineElement) {
      console.warn('[updateTimeline] Timeline element not found');
      return;
    }

    const rows = tbody.querySelectorAll(config.rowSelector);
    const data = [];

    rows.forEach(row => {
      const extracted = config.extractData(row);
      if (extracted !== null) {
        data.push(extracted);
      }
    });

    const finalData = config.sortData ? config.sortData(data) : data;

    try {
      const paramName = tbody.dataset.parameterName;
      if (config.timelineType === 'simple_interval' && paramName) {
        // TEC uses a different signature with paramName
        window.TimelineVisualizer.updateTimeline(timelineElement, paramName, finalData, { type: config.timelineType });
      } else {
        // Standard signature for VSS, DHS, Flow
        window.TimelineVisualizer.updateTimeline(timelineElement, finalData, { type: config.timelineType });
      }
      console.log(`[updateTimeline] Updated timeline (${config.timelineType}) with ${finalData.length} items`);
    } catch (err) {
      console.error(`[updateTimeline] Failed to update timeline:`, err);
    }
  }

  /**
   * Simplified wrapper for updating timeline by strategy type.
   * Uses preset configurations from TIMELINE_CONFIGS.
   *
   * @param {HTMLElement} tbody - Table body element
   * @param {string} type - Strategy type: 'vss', 'dhs', 'flow', or 'tec_simple'
   */
  function updateTimelineByType(tbody, type) {
    const config = TIMELINE_CONFIGS[type];
    if (!config) {
      console.error(`[updateTimelineByType] Unknown type: ${type}`);
      return;
    }
    updateTimeline(tbody, config);
  }

  // Create debounced versions for each type
  const debouncedUpdateTimeline = {
    vss: debounce((tbody) => updateTimelineByType(tbody, 'vss'), 300),
    dhs: debounce((tbody) => updateTimelineByType(tbody, 'dhs'), 300),
    flow: debounce((tbody) => updateTimelineByType(tbody, 'flow'), 300),
    tec_simple: debounce((tbody) => updateTimelineByType(tbody, 'tec_simple'), 300)
  };

// ==================== Legacy Functions (Deprecated) ====================

  // ==================== Legacy Timeline Functions (Deprecated) ====================
// These functions are kept for backward compatibility only.
// All new code should use updateTimelineByType() instead.

/**
 * @deprecated Use updateTimelineByType(tbody, 'vss') instead
   * 从表格中收集步骤数据并更新时间轴
   * @param {HTMLElement} tbody - 表格体元素
   */
function updateTimelineFromTable(tbody) {
  if (!window.TimelineVisualizer) {
    console.warn('[updateTimelineFromTable] TimelineVisualizer not available');
    return;
  }

  const parameterName = tbody.dataset.parameterName;
  if (!parameterName) {
    console.warn('[updateTimelineFromTable] No parameterName found');
    return;
  }

  // 查找对应的容器（步骤数组控件容器）
  const container = tbody.closest('.step-array-control-enhanced');
  if (!container) {
    console.warn('[updateTimelineFromTable] Container not found');
    return;
  }

  const timeline = container.querySelector('.parameter-timeline');
  if (!timeline) {
    console.warn('[updateTimelineFromTable] Timeline element not found');
    return;
  }

  // 收集步骤数据
  const rows = tbody.querySelectorAll('.step-row');
  const steps = [];

  rows.forEach(row => {
    const timeInput = row.querySelector('.step-time');
    const speedInput = row.querySelector('.step-speed');

    if (timeInput && speedInput) {
      const time_hours = parseFloat(timeInput.value) || 0;
      const speed_kmh = parseFloat(speedInput.value) || 0;

      steps.push({ time_hours, speed_kmh });
    }
  });

  // 按时间排序
  steps.sort((a, b) => a.time_hours - b.time_hours);

  console.log('[updateTimelineFromTable] Updating timeline with steps:', steps);

  // 更新时间轴
  try {
    window.TimelineVisualizer.updateTimeline(timeline, steps, { type: 'speed' });
  } catch (err) {
    console.error('[updateTimelineFromTable] Failed to update timeline:', err);
  }
}

// @deprecated Use debouncedUpdateTimeline.vss instead
// 创建防抖版本的更新函数（300ms延迟）
const debouncedUpdateTimelineFromTable = debounce(updateTimelineFromTable, 300);

// ==================== Form Generation ====================

/**
 * Generate form HTML from template schema.
 *
 * @param {string} templateId - Template identifier
 * @param {Object} template - Template object with parameters_schema
 * @returns {string} HTML form string
 */
/**
 * Generate parameter form from template schema.
 * Main entry point for creating dynamic strategy parameter forms.
 *
 * @param {string} templateId - Template identifier
 * @returns {Promise<HTMLFormElement>} Generated form element
 */
async function generateFormFromTemplate(templateId) {
  try {
    console.log(`Generating form for template: ${templateId}`);

    // Fetch template with full schema
    const response = await fetch(`/api/v1/control/templates/${templateId}`);
    if (!response.ok) {
      throw new Error(`Failed to load template: ${response.statusText}`);
    }

    const templateDetail = await response.json();
    const template = templateDetail.data || templateDetail; // Handle different response formats

    // Generate form controls for each parameter
    const formHtml = document.createElement("form");
    formHtml.id = `strategy-form-${templateId}`;
    formHtml.className = "strategy-parameter-form";

    // Store template data on form for later use
    formHtml.dataset.templateId = templateId;
    formHtml.dataset.strategyType = template.strategy_type || template.strategyType;

    const parametersSchema = template.parameters_schema || template.parametersSchema || [];

    for (const paramSchema of parametersSchema) {
      const paramControl = renderParameterControl(paramSchema, templateId);
      if (paramControl) {
        formHtml.appendChild(paramControl);
      }

      // [FIX] Inject unified vehicle type control after restriction_mode
      if (paramSchema.parameter_name === 'restriction_mode') {
        const hasVehicleTypeParams = parametersSchema.some(p =>
          p.parameter_name === 'disallow_vehicle_types' || p.parameter_name === 'allowed_vehicle_types'
        );
        if (hasVehicleTypeParams) {
          const unifiedControl = renderUnifiedVehicleTypeControl(template);
          formHtml.appendChild(unifiedControl);
        }
      }
    }

    // Add buttons
    const buttonContainer = document.createElement("div");
    buttonContainer.className = "form-buttons";

    const validateBtn = document.createElement("button");
    validateBtn.type = "button";
    validateBtn.className = "btn btn-validate";
    validateBtn.textContent = "Validate Parameters";
    validateBtn.addEventListener("click", () => validateFormParameters(formHtml));

    const previewBtn = document.createElement("button");
    previewBtn.type = "button";
    previewBtn.className = "btn btn-preview";
    previewBtn.textContent = "Generate XML Preview";
    previewBtn.addEventListener("click", () => generateXMLPreview(formHtml));

    const resetBtn = document.createElement("button");
    resetBtn.type = "reset";
    resetBtn.className = "btn btn-reset";
    resetBtn.textContent = "Reset Form";

    buttonContainer.appendChild(validateBtn);
    buttonContainer.appendChild(previewBtn);
    buttonContainer.appendChild(resetBtn);

    formHtml.appendChild(buttonContainer);

    console.log(`Form generated successfully for template: ${templateId}`);
    return formHtml;

  } catch (error) {
    console.error(`Error generating form for template ${templateId}:`, error);
    const errorDiv = document.createElement("div");
    errorDiv.className = "form-error";
    errorDiv.textContent = `Failed to generate form: ${error.message}`;
    return errorDiv;
  }
}

/**
 * Render parameter control based on parameter type.
 *
 * @param {Object} paramSchema - Parameter schema object
 * @param {string} templateId - Template identifier (for context)
 * @returns {HTMLElement} Form control element
 */
// ==================== Form Generation ====================
// Main form generation and parameter control rendering functions.

function renderParameterControl(paramSchema, templateId) {
  const paramName = paramSchema.parameter_name || paramSchema.parameterName;
  const paramType = paramSchema.parameter_type || paramSchema.parameterType;
  const required = paramSchema.required || false;
  const defaultValue = paramSchema.default_value || paramSchema.defaultValue;

  // [FIX] Hide entrance_edges parameter - redundant with Step 2 edge selector
  // The value will be auto-filled from selectedEdges when creating strategy instance
  if (paramName === 'entrance_edges') {
    console.log('[renderParameterControl] Skipping entrance_edges parameter (auto-filled from edge selector)');
    return null; // Don't render this parameter
  }

  // [FIX] Hide disallow_vehicle_types and allowed_vehicle_types - they will be replaced by a unified control
  // linked to restriction_mode
  if (paramName === 'disallow_vehicle_types' || paramName === 'allowed_vehicle_types') {
    console.log(`[renderParameterControl] Skipping ${paramName} (handled by unified vehicle type control)`);
    return null;
  }

  // Container for the parameter
  const container = document.createElement("div");
  container.className = "form-group";
  container.dataset.parameterName = paramName;
  container.dataset.parameterType = paramType;

  // Label
  const label = document.createElement("label");
  label.htmlFor = `param-${paramName}`;
  label.textContent = paramSchema.display_name || paramSchema.displayName || paramName;
  if (required) {
    const requiredSpan = document.createElement("span");
    requiredSpan.className = "required";
    requiredSpan.textContent = " *";
    label.appendChild(requiredSpan);
  }
  container.appendChild(label);

  // Description
  if (paramSchema.description) {
    const desc = document.createElement("small");
    desc.className = "description";
    desc.textContent = paramSchema.description;
    container.appendChild(desc);
  }

  // Render control based on parameter type
  let control;
  switch (paramType) {
    case "integer":
      control = renderIntegerControl(paramName, paramSchema);
      break;
    case "number":
      control = renderNumberControl(paramName, paramSchema);
      break;
    case "enum":
      control = renderEnumControl(paramName, paramSchema);
      break;
    case "enum_array":
    case "enum_array":
      control = renderEnumArrayControl(paramName, paramSchema);
      break;
    case "step_array":
      control = renderStepArrayControl(paramName, paramSchema);
      break;
    case "dhs_interval_array":
      control = renderDHSIntervalControl(paramName, paramSchema);
      break;
    case "flow_interval_array":
      control = renderFlowIntervalControl(paramName, paramSchema);
      break;
    case "tec_interval_array":
      control = renderTECIntervalControl(paramName, paramSchema);
      break;
    case "edge_array":
      control = renderEdgeArrayControl(paramName, paramSchema);
      break;
    case "string":
      control = renderStringControl(paramName, paramSchema);
      break;
    case "array":
      // Generic array - check for special structure
      if (paramSchema.interval_structure) {
        // [DEPRECATED] interval_structure now handled by explicit parameter types (dhs_interval_array, tec_interval_array, etc.)
        // This fallback is for backward compatibility only
        control = renderGenericArrayControl(paramName, paramSchema);
      } else {
        control = renderGenericArrayControl(paramName, paramSchema);
      }
      break;
    default:
      console.warn(`Unknown parameter type: ${paramType}`);
      control = renderStringControl(paramName, paramSchema);
  }

  if (control) {
    container.appendChild(control);
  }

  // Error/warning display area
  const feedbackDiv = document.createElement("div");
  feedbackDiv.className = "parameter-feedback";
  feedbackDiv.dataset.feedback = "";
  container.appendChild(feedbackDiv);

  return container;
}

// ==================== Parameter Control Renderers ====================

/**
 * Render integer input control with range hints.
 * Task 1.2: Enhanced number input with range validation
 */
// ==================== Parameter Control Renderers ====================
// Functions that render different types of parameter controls (inputs, selects, tables).
// Each function creates DOM elements for a specific parameter type.

function renderIntegerControl(paramName, schema) {
  const container = document.createElement("div");
  container.className = "number-input-wrapper";

  const control = document.createElement("input");
  control.type = "number";
  control.id = `param-${paramName}`;
  control.name = paramName;
  control.className = "form-control";
  control.step = "1";

  if (schema.min_value !== undefined) control.min = schema.min_value;
  if (schema.max_value !== undefined) control.max = schema.max_value;
  if (schema.default_value !== undefined) control.value = schema.default_value;

  container.appendChild(control);

  // Add unit label if available
  if (schema.unit) {
    const unitLabel = document.createElement("span");
    unitLabel.className = "unit-label";
    unitLabel.textContent = schema.unit;
    container.appendChild(unitLabel);
  }

  // Add range hint
  if (schema.min_value !== undefined || schema.max_value !== undefined) {
    const hint = document.createElement("small");
    hint.className = "parameter-hint";
    let hintText = "范围: ";
    if (schema.min_value !== undefined && schema.max_value !== undefined) {
      hintText += `${schema.min_value}-${schema.max_value}`;
    } else if (schema.min_value !== undefined) {
      hintText += `≥${schema.min_value}`;
    } else {
      hintText += `≤${schema.max_value}`;
    }
    if (schema.unit) {
      hintText += ` | 单位: ${schema.unit}`;
    }
    hint.textContent = hintText;
    container.appendChild(hint);
  }

  control.addEventListener("blur", () => validateNumberRange(control, schema));

  return container;
}

/**
 * Render number (float) input control with range hints.
 * Task 1.2: Enhanced number input with range validation
 */
function renderNumberControl(paramName, schema) {
  const container = document.createElement("div");
  container.className = "number-input-wrapper";

  const control = document.createElement("input");
  control.type = "number";
  control.id = `param-${paramName}`;
  control.name = paramName;
  control.className = "form-control";
  control.step = schema.step || "0.01";

  if (schema.min_value !== undefined) control.min = schema.min_value;
  if (schema.max_value !== undefined) control.max = schema.max_value;
  if (schema.default_value !== undefined) control.value = schema.default_value;

  container.appendChild(control);

  // Add unit label if available
  if (schema.unit) {
    const unitLabel = document.createElement("span");
    unitLabel.className = "unit-label";
    unitLabel.textContent = schema.unit;
    container.appendChild(unitLabel);
  }

  // Add range hint
  if (schema.min_value !== undefined || schema.max_value !== undefined) {
    const hint = document.createElement("small");
    hint.className = "parameter-hint";
    let hintText = "范围: ";
    if (schema.min_value !== undefined && schema.max_value !== undefined) {
      hintText += `${schema.min_value}-${schema.max_value}`;
    } else if (schema.min_value !== undefined) {
      hintText += `≥${schema.min_value}`;
    } else {
      hintText += `≤${schema.max_value}`;
    }
    if (schema.unit) {
      hintText += ` | 单位: ${schema.unit}`;
    }
    hint.textContent = hintText;
    container.appendChild(hint);
  }

  control.addEventListener("blur", () => validateNumberRange(control, schema));

  return container;
}

/**
 * Validate number input range on blur.
 * Task 1.2: Number range validation
 *
 * @param {HTMLInputElement} input - Number input element
 * @param {Object} schema - Parameter schema
 * @returns {boolean} Validation result
 */
// ==================== Validation Functions ====================
// Functions for validating form inputs and displaying errors.
// Uses the unified validators object defined above.

function validateNumberRange(input, schema) {
  const value = parseFloat(input.value);

  // Check if required (using unified validator)
  if (input.value === '' && schema.required) {
    const result = validators.required(input.value);
    if (!result.valid) {
      showError(input, result.message);
      return false;
    }
  }

  if (input.value === '') {
    clearError(input);
    return true; // Empty optional field is valid
  }

  // Check if valid number (using unified validator)
  const numResult = validators.isNumber(input.value);
  if (!numResult.valid) {
    showError(input, numResult.message);
    return false;
  }

  // Check range (using unified validator)
  const minVal = schema.min_value;
  const maxVal = schema.max_value;

  if (minVal !== undefined || maxVal !== undefined) {
    const rangeResult = validators.numberRange(
      value,
      minVal ?? -Infinity,
      maxVal ?? Infinity,
      schema.unit || ''
    );
    if (!rangeResult.valid) {
      showError(input, rangeResult.message);
      return false;
    }
  }

  clearError(input);

  if (maxVal !== undefined && value > maxVal) {
    feedbackDiv.className = 'parameter-feedback error';
    feedbackDiv.textContent = `值不能大于 ${maxVal}`;
    feedbackDiv.dataset.feedback = 'error';
    return false;
  }

  // Success
  feedbackDiv.className = 'parameter-feedback success';
  feedbackDiv.textContent = '✓ 有效';
  feedbackDiv.dataset.feedback = 'success';
  return true;
}

/**
 * Render enum (dropdown) control.
 */
function renderEnumControl(paramName, schema) {
  const control = document.createElement("select");
  control.id = `param-${paramName}`;
  control.name = paramName;
  control.className = "form-control";

  const enumValues = schema.enum_values || schema.enumValues || [];

  // Add empty option if not required
  if (!schema.required) {
    const emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.textContent = "-- Select --";
    control.appendChild(emptyOption);
  }

  // Add enum options
  for (const enumVal of enumValues) {
    const option = document.createElement("option");
    if (typeof enumVal === "string") {
      option.value = enumVal;
      option.textContent = enumVal;
    } else {
      option.value = enumVal.value;
      option.textContent = enumVal.label || enumVal.value;
    }
    control.appendChild(option);
  }

  if (schema.default_value !== undefined) {
    control.value = schema.default_value;
  }

  control.addEventListener("change", () => validateParameterOnChange(control, schema));

  // [FIX] Special handling for restriction_mode - add change listener to update vehicle type control
  if (paramName === 'restriction_mode') {
    control.addEventListener('change', (e) => {
      updateVehicleTypeControlForRestrictionMode(e.target.value);
    });
  }

  return control;
}

/**
 * Render enum_array (checkboxes) control.
 */
function renderEnumArrayControl(paramName, schema) {
  const container = document.createElement("div");
  container.className = "enum-array-control";

  const enumValues = schema.enum_values || schema.enumValues || [];
  const selectedValues = schema.default_value || [];

  for (const enumVal of enumValues) {
    const checkboxDiv = document.createElement("div");
    checkboxDiv.className = "checkbox-item";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.name = paramName;
    checkbox.value = typeof enumVal === "string" ? enumVal : enumVal.value;
    checkbox.className = "enum-checkbox";
    checkbox.dataset.enumValue = checkbox.value;

    // Check if this value should be selected by default
    if (selectedValues && selectedValues.includes(checkbox.value)) {
      checkbox.checked = true;
    }

    checkbox.addEventListener("change", () => validateParameterOnChange(checkbox, schema));

    const label = document.createElement("label");
    label.htmlFor = `${paramName}-${checkbox.value}`;
    checkbox.id = `${paramName}-${checkbox.value}`;
    label.textContent = typeof enumVal === "string" ? enumVal : (enumVal.label || enumVal.value);

    checkboxDiv.appendChild(checkbox);
    checkboxDiv.appendChild(label);
    container.appendChild(checkboxDiv);
  }

  return container;
}

/**
 * Render step_array (speed steps editor) control.
 */
function renderStepArrayControl(paramName, schema) {
  const container = document.createElement("div");
  container.className = "step-array-control-enhanced";
  container.dataset.parameterName = paramName;

  const stepStructure = schema.step_structure || schema.stepStructure || {};
  const defaultSteps = schema.default_value || [];

  // [OPTIMIZED] 添加时间轴可视化（支持空默认值）
  if (window.TimelineVisualizer) {
    try {
      // 添加时间轴说明文字
      const description = document.createElement("div");
      description.className = "timeline-description";
      description.textContent = "时间-限速值序列，支持3-5个步骤实现严格控制和事件响应";
      container.appendChild(description);

      // 使用默认值，或提供示例步骤（如果没有默认值）
      const stepsForDisplay = defaultSteps.length > 0 ? defaultSteps : [
        { time_hours: 7, speed_kmh: 100 },
        { time_hours: 9, speed_kmh: 80 },
        { time_hours: 17, speed_kmh: 100 },
        { time_hours: 22, speed_kmh: 80 }
      ];

      // 渲染时间轴
      const timeline = window.TimelineVisualizer.renderTimeline(
        paramName,
        stepsForDisplay,
        { type: 'speed' }
      );
      container.appendChild(timeline);
    } catch (err) {
      console.warn('Failed to render timeline:', err);
      // 继续渲染表格，不因为时间轴错误而中止
    }
  }

  // Create table for steps
  const table = document.createElement("table");
  table.className = "steps-table";

  // Header
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  const timeHeader = document.createElement("th");
  timeHeader.textContent = `Time (${stepStructure.time_display_unit || 'hours'})`;
  const speedHeader = document.createElement("th");
  speedHeader.textContent = `Speed (${stepStructure.speed_display_unit || 'km/h'})`;
  const actionHeader = document.createElement("th");
  actionHeader.textContent = "Action";

  headerRow.appendChild(timeHeader);
  headerRow.appendChild(speedHeader);
  headerRow.appendChild(actionHeader);
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Body
  const tbody = document.createElement("tbody");
  tbody.className = "steps-tbody";
  tbody.dataset.parameterName = paramName;

  // Add default steps
  defaultSteps.forEach((step, idx) => {
    const timeVal = step.time_hours !== undefined ? step.time_hours : (step.time_seconds / 3600);
    const speedVal = step.speed_kmh !== undefined ? step.speed_kmh : (step.speed_ms * 3.6);
    addStepRow(tbody, paramName, timeVal, speedVal, stepStructure);
  });

  table.appendChild(tbody);
  container.appendChild(table);

  // Add/Remove buttons
  const buttonDiv = document.createElement("div");
  buttonDiv.className = "step-buttons";

  const addBtn = document.createElement("button");
  addBtn.type = "button";
  addBtn.className = "btn btn-add-step";
  addBtn.textContent = "+ Add Step";
  addBtn.addEventListener("click", (e) => {
    e.preventDefault();
    addStepRow(tbody, paramName, 0, 100, stepStructure);
    validateParameterOnChange(tbody, schema);
    // [NEW] 添加新步骤后更新时间轴
    updateTimelineByType(tbody, 'vss');
  });

  buttonDiv.appendChild(addBtn);
  container.appendChild(buttonDiv);

  // [NEW] 添加使用提示
  const hint = document.createElement("div");
  hint.className = "config-hint";
  hint.textContent = "使用表格编辑器配置速度步骤。时间单位：小时，速度单位：km/h";
  container.appendChild(hint);

  return container;
}

/**
 * Add a step row to the steps table.
 */

// ==================== Row Creation Helper Functions ====================

/**
 * Create a time input element (0-24 hours).
 * @param {string} className - CSS class name
 * @param {number} value - Initial value
 * @returns {HTMLInputElement}
 */

// ==================== Validation Helpers ====================

/**
 * Unified validators for form inputs.
 * Provides consistent validation logic across all parameter types.
 */
const validators = {
  /**
   * Validate time order (begin < end).
   * @param {number} beginHours - Start time in hours
   * @param {number} endHours - End time in hours
   * @returns {{valid: boolean, message?: string}}
   */
  timeOrder: (beginHours, endHours) => {
    if (beginHours >= endHours) {
      return {
        valid: false,
        message: `开始时间(${beginHours}h)必须小于结束时间(${endHours}h)`
      };
    }
    return { valid: true };
  },

  /**
   * Validate time range (0-24 hours).
   * @param {number} hours - Time value in hours
   * @returns {{valid: boolean, message?: string}}
   */
  timeRange: (hours) => {
    if (hours < 0 || hours > 24) {
      return {
        valid: false,
        message: `时间必须在 0-24 小时范围内，当前值: ${hours}`
      };
    }
    return { valid: true };
  },

  /**
   * Validate speed range.
   * @param {number} speed - Speed value in km/h
   * @param {number} min - Minimum allowed speed (default: 0)
   * @param {number} max - Maximum allowed speed (default: 120)
   * @returns {{valid: boolean, message?: string}}
   */
  speedRange: (speed, min = 0, max = 120) => {
    if (speed < min || speed > max) {
      return {
        valid: false,
        message: `速度必须在 ${min}-${max} km/h 范围内，当前值: ${speed}`
      };
    }
    return { valid: true };
  },

  /**
   * Validate number range with custom constraints.
   * @param {number} value - Value to validate
   * @param {number} min - Minimum allowed value
   * @param {number} max - Maximum allowed value
   * @param {string} unit - Unit name for error message
   * @returns {{valid: boolean, message?: string}}
   */
  numberRange: (value, min, max, unit = '') => {
    if (value < min || value > max) {
      return {
        valid: false,
        message: `值必须在 ${min}-${max}${unit ? ' ' + unit : ''} 范围内，当前值: ${value}`
      };
    }
    return { valid: true };
  },

  /**
   * Validate required field.
   * @param {string|number} value - Value to validate
   * @returns {{valid: boolean, message?: string}}
   */
  required: (value) => {
    if (value === '' || value === null || value === undefined) {
      return {
        valid: false,
        message: '此字段为必填项'
      };
    }
    return { valid: true };
  },

  /**
   * Validate number format.
   * @param {string} value - String value to check
   * @returns {{valid: boolean, message?: string}}
   */
  isNumber: (value) => {
    if (value !== '' && isNaN(parseFloat(value))) {
      return {
        valid: false,
        message: '请输入有效的数字'
      };
    }
    return { valid: true };
  }
};

/**
 * Show error message on an input element.
 * @param {HTMLInputElement|HTMLSelectElement|HTMLTextAreaElement} input - Input element
 * @param {string} message - Error message to display
 */
function showError(input, message) {
  // Add error class to input
  input.classList.add('input-error');

  // Find or create feedback div
  const formGroup = input.closest('.form-group');
  if (!formGroup) return;

  let feedbackDiv = formGroup.querySelector('.parameter-feedback');
  if (!feedbackDiv) {
    feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'parameter-feedback';
    formGroup.appendChild(feedbackDiv);
  }

  // Set error message
  feedbackDiv.className = 'parameter-feedback error';
  feedbackDiv.textContent = message;
  feedbackDiv.dataset.feedback = 'error';
}

/**
 * Clear error message from an input element.
 * @param {HTMLInputElement|HTMLSelectElement|HTMLTextAreaElement} input - Input element
 */
function clearError(input) {
  // Remove error class from input
  input.classList.remove('input-error');

  // Clear feedback div
  const formGroup = input.closest('.form-group');
  if (!formGroup) return;

  const feedbackDiv = formGroup.querySelector('.parameter-feedback');
  if (feedbackDiv) {
    feedbackDiv.textContent = '';
    feedbackDiv.className = 'parameter-feedback';
    feedbackDiv.dataset.feedback = '';
  }
}

/**
 * Validate input on blur with automatic error display.
 * @param {HTMLInputElement} input - Input element to validate
 * @param {Function} validatorFn - Validator function that returns {valid, message}
 */
function validateOnBlur(input, validatorFn) {
  input.addEventListener('blur', () => {
    const result = validatorFn();
    if (!result.valid) {
      showError(input, result.message);
    } else {
      clearError(input);
    }
  });

  // Clear error on input (give user immediate feedback when correcting)
  input.addEventListener('input', () => {
    if (input.classList.contains('input-error')) {
      const result = validatorFn();
      if (result.valid) {
        clearError(input);
      }
    }
  });
}

// ==================== End Validation Helpers ====================

function createTimeInput\(className, value = 0\) \{
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

function addStepRow\(tbody, paramName, timeVal, speedVal, stepStructure\) \{
  const row = document.createElement("tr");
  row.className = "step-row";

  // Time input
  const timeCell = document.createElement("td");
  const timeInput = createTimeInput("step-time", timeVal || 0);
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
    updateTimelineByType(tbody, 'vss');
  });
  actionCell.appendChild(removeBtn);
  row.appendChild(actionCell);

  // [NEW] 为输入框添加变化事件监听器以更新时间轴（使用防抖）
  timeInput.addEventListener('input', () => debouncedUpdateTimeline.vss(tbody));
  speedInput.addEventListener('input', () => debouncedUpdateTimeline.vss(tbody));

  tbody.appendChild(row);
}

/**
 * Render dhs_interval_array control for Dynamic Hard Shoulder strategies.
 * Includes timeline visualization above the table.
 */
function renderDHSIntervalControl(paramName, schema) {
  const container = document.createElement("div");
  container.className = "dhs-interval-control-enhanced";
  container.dataset.parameterName = paramName;

  const defaultIntervals = schema.default_value || [];
  const intervalStructure = schema.interval_structure || {};

  // [OPTIMIZED] 添加时间轴可视化（支持空默认值）
  if (window.TimelineVisualizer) {
    try {
      // 添加时间轴说明文字
      const description = document.createElement("div");
      description.className = "timeline-description";
      description.textContent = schema.description || "应急车道开放/关闭时间区间列表（注意：必须覆盖完整24小时）";
      container.appendChild(description);

      // 使用默认值，或提供示例区间（如果没有默认值）
      const intervalsForDisplay = defaultIntervals.length > 0 ? defaultIntervals : [
        { begin_hours: 0, end_hours: 6, status: 'CLOSED' },
        { begin_hours: 6, end_hours: 10, status: 'OPEN' },
        { begin_hours: 10, end_hours: 15, status: 'CLOSED' },
        { begin_hours: 15, end_hours: 20, status: 'OPEN' },
        { begin_hours: 20, end_hours: 24, status: 'CLOSED' }
      ];

      // 渲染时间轴
      const timeline = window.TimelineVisualizer.renderTimeline(
        paramName,
        intervalsForDisplay,
        { type: 'dhs' }
      );
      container.appendChild(timeline);
    } catch (err) {
      console.warn('[renderDHSIntervalControl] Failed to render timeline:', err);
      // 继续渲染表格，不因为时间轴错误而中止
    }
  }

  // Create table for DHS intervals
  const table = document.createElement("table");
  table.className = "intervals-table";

  // Header
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");

  const beginHeader = document.createElement("th");
  beginHeader.textContent = "开始时间 (小时)";
  const endHeader = document.createElement("th");
  endHeader.textContent = "结束时间 (小时)";
  const statusHeader = document.createElement("th");
  statusHeader.textContent = "状态";
  const vehiclesHeader = document.createElement("th");
  vehiclesHeader.textContent = "允许车型";
  const actionHeader = document.createElement("th");
  actionHeader.textContent = "操作";

  headerRow.appendChild(beginHeader);
  headerRow.appendChild(endHeader);
  headerRow.appendChild(statusHeader);
  headerRow.appendChild(vehiclesHeader);
  headerRow.appendChild(actionHeader);
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Body
  const tbody = document.createElement("tbody");
  tbody.className = "dhs-intervals-tbody";
  tbody.dataset.parameterName = paramName;

  // Add default intervals
  defaultIntervals.forEach((interval) => {
    const beginHours = interval.begin_hours || 0;
    const endHours = interval.end_hours || 1;
    const status = interval.status || "CLOSED";
    const allowedVehicles = interval.allowed_vehicle_types || ["emergency"];

    addDHSIntervalRow(tbody, paramName, beginHours, endHours, status, allowedVehicles, intervalStructure);
  });

  table.appendChild(tbody);
  container.appendChild(table);

  // Add button
  const buttonDiv = document.createElement("div");
  buttonDiv.className = "interval-buttons";

  const addBtn = document.createElement("button");
  addBtn.type = "button";
  addBtn.className = "btn btn-add-interval";
  addBtn.textContent = "+ 添加时间区间";
  addBtn.addEventListener("click", (e) => {
    e.preventDefault();
    addDHSIntervalRow(tbody, paramName, 0, 1, "CLOSED", ["emergency"], intervalStructure);
    // [NEW] Update timeline after adding row
    updateTimelineByType(tbody, 'dhs');
  });

  buttonDiv.appendChild(addBtn);
  container.appendChild(buttonDiv);

  // [NEW] Usage hint
  const hint = document.createElement("div");
  hint.className = "config-hint";
  hint.textContent = "使用表格编辑器配置应急车道开放/关闭区间。时间单位：小时。注意：必须覆盖完整24小时，不能有时间重叠或间隙。";
  container.appendChild(hint);

  return container;
}

/**
 * Add a DHS interval row to the table.
 */
function addDHSIntervalRow(tbody, paramName, beginHours, endHours, status, allowedVehicles, intervalStructure) {
  const row = document.createElement("tr");
  row.className = "dhs-interval-row";

  // Begin time (using helper)
  const beginCell = document.createElement("td");
  const beginInput = createTimeInput("dhs-interval-begin", beginHours || 0);
  beginCell.appendChild(beginInput);
  row.appendChild(beginCell);

  // End time (using helper)
  const endCell = document.createElement("td");
  const endInput = createTimeInput("dhs-interval-end", endHours || 1);
  endCell.appendChild(endInput);
  row.appendChild(endCell);

  // Status (OPEN/CLOSED)
  const statusCell = document.createElement("td");
  const statusSelect = document.createElement("select");
  statusSelect.className = "dhs-interval-status";

  const openOption = document.createElement("option");
  openOption.value = "OPEN";
  openOption.textContent = "开放 (OPEN)";
  const closedOption = document.createElement("option");
  closedOption.value = "CLOSED";
  closedOption.textContent = "关闭 (CLOSED)";

  statusSelect.appendChild(openOption);
  statusSelect.appendChild(closedOption);
  statusSelect.value = status || "CLOSED";

  statusCell.appendChild(statusSelect);
  row.appendChild(statusCell);

  // Allowed vehicle types (multi-select dropdown)
  const vehiclesCell = document.createElement("td");
  const vehiclesSelect = document.createElement("select");
  vehiclesSelect.className = "dhs-interval-vehicles";
  vehiclesSelect.multiple = true;
  vehiclesSelect.size = 4; // Show 4 options at once

  // Standard vehicle type options
  const vehicleOptions = [
    { value: "passenger", label: "乘用车" },
    { value: "bus", label: "公交车" },
    { value: "truck", label: "货车" },
    { value: "emergency", label: "应急车" },
    { value: "authority", label: "执法车" }
  ];

  vehicleOptions.forEach(opt => {
    const option = document.createElement("option");
    option.value = opt.value;
    option.textContent = opt.label;
    // Select if in allowedVehicles array
    if (Array.isArray(allowedVehicles) && allowedVehicles.includes(opt.value)) {
      option.selected = true;
    }
    vehiclesSelect.appendChild(option);
  });

  vehiclesCell.appendChild(vehiclesSelect);
  row.appendChild(vehiclesCell);

  // Remove button (using helper)
  const actionCell = document.createElement("td");
  const removeBtn = createRemoveButton(row, tbody, 'dhs');
  removeBtn.className = "btn-remove-interval"; // Keep original class
  actionCell.appendChild(removeBtn);
  row.appendChild(actionCell);

  // Bind timeline updates (using helper)
  bindTimelineUpdate(beginInput, tbody, 'dhs');
  bindTimelineUpdate(endInput, tbody, 'dhs');
  bindTimelineUpdate(statusSelect, tbody, 'dhs');

  tbody.appendChild(row);
}

/**
 * Update DHS timeline from table data (reads current table state and updates timeline).
 */
/**
   * @deprecated Use updateTimelineByType(tbody, 'dhs') instead
   */
function updateDHSTimelineFromTable(tbody) {
  const paramName = tbody.dataset.parameterName;
  if (!paramName) return;

  // Find the timeline element (sibling of table)
  const container = tbody.closest('.dhs-interval-control-enhanced');
  if (!container) return;

  const timelineElement = container.querySelector('.parameter-timeline');
  if (!timelineElement) return;

  // Extract intervals from table rows
  const rows = tbody.querySelectorAll('.dhs-interval-row');
  const intervals = [];

  rows.forEach(row => {
    const beginInput = row.querySelector('.dhs-interval-begin');
    const endInput = row.querySelector('.dhs-interval-end');
    const statusSelect = row.querySelector('.dhs-interval-status');

    if (beginInput && endInput && statusSelect) {
      intervals.push({
        begin_hours: parseFloat(beginInput.value) || 0,
        end_hours: parseFloat(endInput.value) || 0,
        status: statusSelect.value || 'CLOSED'
      });
    }
  });

  // Update the timeline
  window.TimelineVisualizer.updateTimeline(timelineElement, intervals, { type: 'dhs' });
}

/**
   * @deprecated Use debouncedUpdateTimeline.dhs instead
   * Debounced version of updateDHSTimelineFromTable (300ms delay).
   */
const debouncedUpdateDHSTimelineFromTable = debounce(updateDHSTimelineFromTable, 300);

/**
 * Render flow_interval_array control.
 */
function renderFlowIntervalControl(paramName, schema) {
  const container = document.createElement("div");
  container.className = "flow-interval-control-enhanced";
  container.dataset.parameterName = paramName;

  const defaultIntervals = schema.default_value || [];

  // [OPTIMIZED] 添加时间轴可视化（支持空默认值）
  if (window.TimelineVisualizer) {
    try {
      // 添加时间轴说明文字
      const description = document.createElement("div");
      description.className = "timeline-description";
      description.textContent = schema.description || "收费站流量控制时间区间列表";
      container.appendChild(description);

      // [FIXED] 统一数据格式：确保所有区间使用 flow_vph 字段
      // 直接使用来自模板的 default_value，不硬编码任何示例数据
      const intervalsForTimeline = defaultIntervals.map(interval => ({
        begin_hours: interval.begin_hours !== undefined ? interval.begin_hours : (interval.begin_seconds / 3600),
        end_hours: interval.end_hours !== undefined ? interval.end_hours : (interval.end_seconds / 3600),
        flow_vph: interval.flow_vph || interval.vehsPerHour || 480
      }));

      const timeline = window.TimelineVisualizer.renderTimeline(
        paramName,
        intervalsForTimeline,
        { type: 'flow' }
      );
      container.appendChild(timeline);
    } catch (err) {
      console.warn('[renderFlowIntervalControl] Failed to render timeline:', err);
      // 继续渲染表格，不因为时间轴错误而中止
    }
  }

  // Create table for flow intervals
  const table = document.createElement("table");
  table.className = "intervals-table";

  // Header
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  const startHeader = document.createElement("th");
  startHeader.textContent = "Start (hours)";
  const endHeader = document.createElement("th");
  endHeader.textContent = "End (hours)";
  const flowHeader = document.createElement("th");
  flowHeader.textContent = "Flow (vehicles/hour)";
  const speedHeader = document.createElement("th");
  speedHeader.textContent = "Speed (km/h)";
  const actionHeader = document.createElement("th");
  actionHeader.textContent = "Action";

  headerRow.appendChild(startHeader);
  headerRow.appendChild(endHeader);
  headerRow.appendChild(flowHeader);
  headerRow.appendChild(speedHeader);
  headerRow.appendChild(actionHeader);
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Body
  const tbody = document.createElement("tbody");
  tbody.className = "intervals-tbody";
  tbody.dataset.parameterName = paramName;

  // [FIXED] 直接使用来自模板的 defaultIntervals（schema.default_value）
  // 时间轴和表格共用同一个数据源，保持数据一致
  defaultIntervals.forEach((interval) => {
    const beginHours = interval.begin_hours !== undefined ? interval.begin_hours : (interval.begin_seconds / 3600);
    const endHours = interval.end_hours !== undefined ? interval.end_hours : (interval.end_seconds / 3600);
    const flowRate = interval.flow_vph || interval.vehsPerHour || 480;
    const targetSpeed = interval.target_speed || 15;

    addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed);
  });

  table.appendChild(tbody);
  container.appendChild(table);

  // Add button
  const buttonDiv = document.createElement("div");
  buttonDiv.className = "interval-buttons";

  const addBtn = document.createElement("button");
  addBtn.type = "button";
  addBtn.className = "btn btn-add-interval";
  addBtn.textContent = "+ 添加流量控制区间";
  addBtn.addEventListener("click", (e) => {
    e.preventDefault();
    addFlowIntervalRow(tbody, paramName, 0, 1, 480, 15);
    // [NEW] 添加区间后更新时间轴
    updateTimelineByType(tbody, 'flow');
  });

  buttonDiv.appendChild(addBtn);
  container.appendChild(buttonDiv);

  // [NEW] 添加使用提示
  const hint = document.createElement("div");
  hint.className = "config-hint";
  hint.textContent = "使用表格编辑器配置流量控制区间。时间单位：小时，流量单位：车辆/小时";
  container.appendChild(hint);

  return container;
}

/**
 * Add a flow interval row.
 */
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

  tbody.appendChild(row);
}

/**
 * Update Flow timeline from table data (reads current table state and updates timeline).
 */
/**
   * @deprecated Use updateTimelineByType(tbody, 'flow') instead
   */
function updateFlowTimelineFromTable(tbody) {
  const paramName = tbody.dataset.parameterName;
  if (!paramName) return;

  // Find the timeline element (sibling of table)
  const container = tbody.closest('.flow-interval-control-enhanced');
  if (!container) return;

  const timelineElement = container.querySelector('.parameter-timeline');
  if (!timelineElement) return;

  // Extract intervals from table rows
  const rows = tbody.querySelectorAll('.interval-row');
  const intervals = [];

  rows.forEach(row => {
    const beginInput = row.querySelector('.interval-begin');
    const endInput = row.querySelector('.interval-end');
    const flowInput = row.querySelector('.interval-flow');

    if (beginInput && endInput && flowInput) {
      intervals.push({
        begin_hours: parseFloat(beginInput.value) || 0,
        end_hours: parseFloat(endInput.value) || 0,
        flow_vph: parseFloat(flowInput.value) || 0
      });
    }
  });

  // Update the timeline
  window.TimelineVisualizer.updateTimeline(timelineElement, intervals, { type: 'flow' });
}

/**
   * @deprecated Use debouncedUpdateTimeline.flow instead
   * Debounced version of updateFlowTimelineFromTable (300ms delay).
   */
const debouncedUpdateFlowTimelineFromTable = debounce(updateFlowTimelineFromTable, 300);

/**
 * Render tec_interval_array control for TEC vehicle restriction strategies.
 * Simplified version - only time intervals (begin_hours, end_hours), no additional parameters.
 * Includes timeline visualization above the table.
 *
 * @param {string} paramName - Parameter name
 * @param {object} schema - Parameter schema
 * @returns {HTMLElement} - Container with timeline and table
 */
function renderTECIntervalControl(paramName, schema) {
  const container = document.createElement("div");
  container.className = "tec-interval-control-enhanced";
  container.dataset.parameterName = paramName;

  const defaultIntervals = schema.default_value || [];
  const intervalStructure = schema.interval_structure || {};

  // Add timeline visualization
  if (window.TimelineVisualizer) {
    try {
      // Add timeline description
      const description = document.createElement("div");
      description.className = "timeline-description";
      description.textContent = schema.description || "车型限制时间区间列表";
      container.appendChild(description);

      // Use default values, or provide example intervals if none
      const intervalsForDisplay = defaultIntervals.length > 0 ? defaultIntervals : [
        { begin_hours: 7, end_hours: 9 },
        { begin_hours: 17, end_hours: 19 }
      ];

      // Render timeline with simple_interval type
      const timeline = window.TimelineVisualizer.renderTimeline(
        paramName,
        intervalsForDisplay,
        { type: 'simple_interval' }
      );
      container.appendChild(timeline);
    } catch (err) {
      console.warn('[renderTECIntervalControl] Failed to render timeline:', err);
      // Continue rendering table even if timeline fails
    }
  }

  // Create table for TEC intervals
  const table = document.createElement("table");
  table.className = "intervals-table";

  // Header
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");

  const beginHeader = document.createElement("th");
  beginHeader.textContent = "开始时间 (小时)";
  const endHeader = document.createElement("th");
  endHeader.textContent = "结束时间 (小时)";
  const actionHeader = document.createElement("th");
  actionHeader.textContent = "操作";

  headerRow.appendChild(beginHeader);
  headerRow.appendChild(endHeader);
  headerRow.appendChild(actionHeader);
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Body
  const tbody = document.createElement("tbody");
  tbody.className = "tec-intervals-tbody";
  tbody.dataset.parameterName = paramName;

  // Add default intervals
  defaultIntervals.forEach((interval) => {
    const beginHours = interval.begin_hours !== undefined ? interval.begin_hours : 0;
    const endHours = interval.end_hours !== undefined ? interval.end_hours : 1;
    addTECIntervalRow(tbody, paramName, beginHours, endHours);
  });

  // If no default intervals, add one empty row
  if (defaultIntervals.length === 0) {
    addTECIntervalRow(tbody, paramName, 7, 9);
  }

  table.appendChild(tbody);
  container.appendChild(table);

  // Add button
  const buttonDiv = document.createElement("div");
  buttonDiv.className = "interval-buttons";

  const addBtn = document.createElement("button");
  addBtn.type = "button";
  addBtn.className = "btn btn-add-interval";
  addBtn.textContent = "+ 添加时间区间";
  addBtn.addEventListener("click", (e) => {
    e.preventDefault();
    addTECIntervalRow(tbody, paramName, 0, 1);
    // Update timeline after adding row
    updateTimelineByType(tbody, 'tec_simple');
  });

  buttonDiv.appendChild(addBtn);
  container.appendChild(buttonDiv);

  // [FIX] Use hint from schema if available, instead of hardcoded hint
  // This avoids duplicate hints and uses the more comprehensive template-defined hint
  if (schema.hint || schema.config_hint) {
    const hint = document.createElement("div");
    hint.className = "config-hint";
    hint.textContent = schema.hint || schema.config_hint;
    container.appendChild(hint);
  }

  return container;
}

/**
 * Add a TEC interval row to the table.
 *
 * @param {HTMLElement} tbody - Table body element
 * @param {string} paramName - Parameter name
 * @param {number} beginHours - Start time in hours
 * @param {number} endHours - End time in hours
 */
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

/**
 * Update TEC timeline visualization from table data.
 *
 * @param {HTMLElement} tbody - Table body element
 */
/**
   * @deprecated Use updateTimelineByType(tbody, 'tec_simple') instead
   */
function updateTECTimelineFromTable(tbody) {
  // Find timeline element in parent container
  const container = tbody.closest('.tec-interval-control-enhanced');
  if (!container) return;

  const timelineElement = container.querySelector('.parameter-timeline');
  if (!timelineElement || !window.TimelineVisualizer) return;

  // Collect intervals from table
  const intervals = [];
  const rows = tbody.querySelectorAll('.tec-interval-row');

  rows.forEach(row => {
    const beginInput = row.querySelector('.tec-interval-begin');
    const endInput = row.querySelector('.tec-interval-end');

    if (beginInput && endInput) {
      const beginHours = parseFloat(beginInput.value) || 0;
      const endHours = parseFloat(endInput.value) || 0;

      // Only add valid intervals
      if (endHours > beginHours && beginHours >= 0 && endHours <= 24) {
        intervals.push({
          begin_hours: beginHours,
          end_hours: endHours
        });
      }
    }
  });

  // Update timeline
  try {
    const paramName = tbody.dataset.parameterName;
    window.TimelineVisualizer.updateTimeline(
      timelineElement,
      paramName,
      intervals,
      { type: 'simple_interval' }
    );
  } catch (err) {
    console.warn('[updateTECTimelineFromTable] Failed to update timeline:', err);
  }
}

/**
 * Render edge_array control.
 */
function renderEdgeArrayControl(paramName, schema) {
  const container = document.createElement("div");
  container.className = "edge-array-control";

  const defaultEdges = schema.default_value || [];

  // Create list of edge inputs
  const edgesList = document.createElement("div");
  edgesList.className = "edges-list";
  edgesList.dataset.parameterName = paramName;

  defaultEdges.forEach((edgeId) => {
    addEdgeInputRow(edgesList, paramName, edgeId);
  });

  container.appendChild(edgesList);

  // Add button
  const addBtn = document.createElement("button");
  addBtn.type = "button";
  addBtn.className = "btn btn-add-edge";
  addBtn.textContent = "+ Add Edge";
  addBtn.addEventListener("click", (e) => {
    e.preventDefault();
    addEdgeInputRow(edgesList, paramName, "");
  });

  container.appendChild(addBtn);

  return container;
}

/**
 * Add an edge input row.
 */
function addEdgeInputRow(edgesList, paramName, edgeId) {
  const row = document.createElement("div");
  row.className = "edge-input-row";

  const input = document.createElement("input");
  input.type = "text";
  input.className = "form-control edge-id-input";
  input.name = `${paramName}-edge`;
  input.placeholder = "Enter edge ID";
  input.value = edgeId;

  const removeBtn = document.createElement("button");
  removeBtn.type = "button";
  removeBtn.className = "btn-remove-edge";
  removeBtn.textContent = "✕";
  removeBtn.addEventListener("click", (e) => {
    e.preventDefault();
    row.remove();
  });

  row.appendChild(input);
  row.appendChild(removeBtn);
  edgesList.appendChild(row);
}

/**
 * Render string control.
 */
function renderStringControl(paramName, schema) {
  // [FIX] Use textarea for description fields to provide more space
  const isDescriptionField = paramName.includes('description') || paramName.includes('desc');

  let control;
  if (isDescriptionField) {
    control = document.createElement("textarea");
    control.id = `param-${paramName}`;
    control.name = paramName;
    control.className = "form-control description-field";
    control.rows = 3; // Default 3 rows for descriptions
    control.placeholder = "请输入策略描述...";

    if (schema.default_value !== undefined) {
      control.value = schema.default_value;
    }
  } else {
    control = document.createElement("input");
    control.type = "text";
    control.id = `param-${paramName}`;
    control.name = paramName;
    control.className = "form-control";

    // [FIX] Add special class for strategy_name to expand width
    if (paramName === 'strategy_name') {
      control.className += " strategy-name-field";
    }

    if (schema.default_value !== undefined) {
      control.value = schema.default_value;
    }
  }

  control.addEventListener("change", () => validateParameterOnChange(control, schema));

  return control;
}

/**
 * Render generic array control with smart placeholders.
 */
function renderGenericArrayControl(paramName, schema) {
  const control = document.createElement("textarea");
  control.id = `param-${paramName}`;
  control.name = paramName;
  control.className = "form-control array-input";
  control.rows = 6;

  // Generate smart placeholder based on parameter name and type
  control.placeholder = generateSmartPlaceholder(paramName, schema);

  if (schema.default_value !== undefined) {
    // Decide format based on value structure
    if (Array.isArray(schema.default_value) && schema.default_value.length > 0) {
      if (Array.isArray(schema.default_value[0])) {
        // Nested array - use JSON format
        control.value = JSON.stringify(schema.default_value, null, 2);
      } else {
        // Simple array - use newline-separated format
        control.value = schema.default_value.join('\n');
      }
    } else {
      control.value = JSON.stringify(schema.default_value, null, 2);
    }
  }

  // Add blur validation
  control.addEventListener('blur', () => validateArrayField(control, schema));

  return control;
}

/**
 * Generate smart placeholder for array parameters based on naming patterns.
 * Task 1.1: Smart placeholder generation
 *
 * @param {string} paramName - Parameter name
 * @param {Object} schema - Parameter schema
 * @returns {string} Placeholder text with examples
 */
function generateSmartPlaceholder(paramName, schema) {
  const name = paramName.toLowerCase();

  // Extract default value as example if available
  const defaultExample = schema.default_value ?
    JSON.stringify(schema.default_value, null, 2) : null;

  // Time/interval parameters
  if (name.includes('time') || name.includes('interval')) {
    return `时段格式示例:
[
  [7, 9],
  [17, 19]
]

每行一个时间段 [开始小时, 结束小时]
或换行分隔: 7,9 然后 17,19`;
  }

  // Speed parameters
  if (name.includes('speed')) {
    return `限速值示例(每行一个):
80
60
40

或JSON格式: [80, 60, 40]`;
  }

  // Vehicle type parameters
  if (name.includes('vehicle') || name.includes('type')) {
    return `车型列表示例:
passenger
truck
bus

或用逗号分隔: passenger, truck, bus`;
  }

  // Edge/segment parameters
  if (name.includes('edge') || name.includes('segment')) {
    return `路段ID列表示例:
-5880
-5881
-5882

或用逗号分隔: -5880, -5881, -5882`;
  }

  // Entrance parameters
  if (name.includes('entrance')) {
    return `入口列表示例:
entrance_1
entrance_2

或用逗号分隔: entrance_1, entrance_2`;
  }

  // Generic fallback with default value hint
  if (defaultExample) {
    return `示例格式:\n${defaultExample}\n\n或每行一个值`;
  }

  return `多个值, 每行一个:
value1
value2
value3

或JSON格式: ["value1", "value2", "value3"]`;
}

/**
 * Validate array field on blur.
 * Task 1.3: Array parameter format validation
 *
 * @param {HTMLTextAreaElement} textarea - Textarea element
 * @param {Object} schema - Parameter schema
 * @returns {boolean} Validation result
 */
function validateArrayField(textarea, schema) {
  const value = textarea.value.trim();
  const feedbackDiv = textarea.closest('.form-group')?.querySelector('.parameter-feedback');

  if (!feedbackDiv) return true;

  // Clear previous feedback
  feedbackDiv.textContent = '';
  feedbackDiv.className = 'parameter-feedback';
  feedbackDiv.dataset.feedback = '';

  // Check if required
  if (!value && schema.required) {
    feedbackDiv.className = 'parameter-feedback error';
    feedbackDiv.textContent = '此字段为必填项';
    feedbackDiv.dataset.feedback = 'error';
    return false;
  }

  if (!value) {
    return true; // Empty optional field is valid
  }

  try {
    let parsed;

    // Try JSON parsing first
    if (value.startsWith('[')) {
      parsed = JSON.parse(value);
      if (!Array.isArray(parsed)) {
        feedbackDiv.className = 'parameter-feedback error';
        feedbackDiv.textContent = 'JSON格式需要是数组';
        feedbackDiv.dataset.feedback = 'error';
        return false;
      }
    } else {
      // Parse as newline or comma-separated
      parsed = value.split(/[,\n]/).map(s => s.trim()).filter(s => s);
    }

    // Validate array constraints
    const minItems = schema.min_items || schema.minItems;
    const maxItems = schema.max_items || schema.maxItems;

    if (minItems !== undefined && parsed.length < minItems) {
      feedbackDiv.className = 'parameter-feedback error';
      feedbackDiv.textContent = `至少需要 ${minItems} 个项目, 当前: ${parsed.length}`;
      feedbackDiv.dataset.feedback = 'error';
      return false;
    }

    if (maxItems !== undefined && parsed.length > maxItems) {
      feedbackDiv.className = 'parameter-feedback error';
      feedbackDiv.textContent = `最多允许 ${maxItems} 个项目, 当前: ${parsed.length}`;
      feedbackDiv.dataset.feedback = 'error';
      return false;
    }

    // Validate nested arrays (time intervals)
    if (Array.isArray(parsed[0])) {
      for (let i = 0; i < parsed.length; i++) {
        const interval = parsed[i];
        if (!Array.isArray(interval) || interval.length !== 2) {
          feedbackDiv.className = 'parameter-feedback error';
          feedbackDiv.textContent = `时段${i + 1}格式错误: 需要恰好2个值 [开始, 结束]`;
          feedbackDiv.dataset.feedback = 'error';
          return false;
        }

        const [start, end] = interval;

        // Validate hour range (0-24)
        if (start < 0 || start > 24) {
          feedbackDiv.className = 'parameter-feedback error';
          feedbackDiv.textContent = `时段${i + 1}无效: 开始小时${start}超出范围(0-24)`;
          feedbackDiv.dataset.feedback = 'error';
          return false;
        }

        if (end < 0 || end > 24) {
          feedbackDiv.className = 'parameter-feedback error';
          feedbackDiv.textContent = `时段${i + 1}无效: 结束小时${end}超出范围(0-24)`;
          feedbackDiv.dataset.feedback = 'error';
          return false;
        }

        // Validate start < end (unless cross-midnight)
        if (start >= end) {
          feedbackDiv.className = 'parameter-feedback warning';
          feedbackDiv.textContent = `时段${i + 1}警告: 开始时间≥结束时间 (跨午夜时段?)`;
          feedbackDiv.dataset.feedback = 'warning';
        }
      }
    }

    // Success
    feedbackDiv.className = 'parameter-feedback success';
    feedbackDiv.textContent = `✓ 已识别 ${parsed.length} 个项目`;
    feedbackDiv.dataset.feedback = 'success';
    return true;

  } catch (e) {
    feedbackDiv.className = 'parameter-feedback error';
    feedbackDiv.textContent = `JSON格式不正确: ${e.message}`;
    feedbackDiv.dataset.feedback = 'error';
    return false;
  }
}
// [REMOVED] Old renderTimeIntervalArrayControl and addTimeIntervalRow functions
// These have been superseded by renderDHSIntervalControl and addDHSIntervalRow
// DHS interval control now handles time intervals with status and vehicle types

// ==================== Validation ====================

/**
 * Validate form parameters against template schema.
 */
async function validateFormParameters(form) {
  try {
    const templateId = form.dataset.templateId;
    const parameters = extractFormParameters(form);

    console.log(`Validating parameters for ${templateId}:`, parameters);

    // Call backend validation endpoint
    const response = await fetch("/api/v1/control/strategies/validate-params", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        template_id: templateId,
        parameters: parameters
      })
    });

    const result = await response.json();

    // Display validation results
    displayValidationResults(form, result);

    if (result.valid) {
      showNotification("Validation passed!", "success");
    } else {
      showNotification("Validation failed. See errors below.", "error");
    }

  } catch (error) {
    console.error("Validation error:", error);
    showNotification(`Validation error: ${error.message}`, "error");
  }
}

/**
 * Validate parameter on change (real-time validation).
 */
function validateParameterOnChange(element, schema) {
  // Local validation only for now
  // More comprehensive validation can be added later

  const feedbackDiv = element.closest(".form-group")?.querySelector(".parameter-feedback");
  if (!feedbackDiv) return;

  // Clear previous feedback
  feedbackDiv.textContent = "";
  feedbackDiv.className = "parameter-feedback";
  feedbackDiv.dataset.feedback = "";

  // Basic validation based on type
  const paramType = schema.parameter_type || schema.parameterType;

  if (paramType === "integer" || paramType === "number") {
    const value = parseFloat(element.value);
    const minVal = schema.min_value;
    const maxVal = schema.max_value;

    if (minVal !== undefined && value < minVal) {
      feedbackDiv.className = "parameter-feedback error";
      feedbackDiv.textContent = `Value must be at least ${minVal}`;
      feedbackDiv.dataset.feedback = "error";
    } else if (maxVal !== undefined && value > maxVal) {
      feedbackDiv.className = "parameter-feedback error";
      feedbackDiv.textContent = `Value must not exceed ${maxVal}`;
      feedbackDiv.dataset.feedback = "error";
    }
  }
}

/**
 * Display validation results on form.
 */
function displayValidationResults(form, result) {
  // Clear previous results
  form.querySelectorAll(".parameter-feedback").forEach((div) => {
    div.textContent = "";
    div.className = "parameter-feedback";
    div.dataset.feedback = "";
  });

  // Display errors
  for (const error of result.errors || []) {
    const paramGroup = form.querySelector(`[data-parameter-name="${error.parameter}"]`);
    if (paramGroup) {
      const feedbackDiv = paramGroup.querySelector(".parameter-feedback");
      if (feedbackDiv) {
        feedbackDiv.className = "parameter-feedback error";
        feedbackDiv.textContent = error.message;
        feedbackDiv.dataset.feedback = "error";
      }
    }
  }

  // Display warnings
  for (const warning of result.warnings || []) {
    const paramGroup = form.querySelector(`[data-parameter-name="${warning.parameter}"]`);
    if (paramGroup) {
      const feedbackDiv = paramGroup.querySelector(".parameter-feedback");
      if (feedbackDiv) {
        feedbackDiv.className = "parameter-feedback warning";
        feedbackDiv.textContent = warning.message;
        feedbackDiv.dataset.feedback = "warning";
      }
    }
  }
}

// ==================== XML Preview ====================

/**
 * Generate XML preview from form parameters.
 */
async function generateXMLPreview(form) {
  try {
    const templateId = form.dataset.templateId;
    const parameters = extractFormParameters(form);

    console.log(`Generating XML preview for ${templateId}:`, parameters);

    // Call backend XML generation endpoint
    const response = await fetch("/api/v1/control/strategies/generate-xml-preview", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        template_id: templateId,
        parameters: parameters
      })
    });

    const result = await response.json();

    // Display XML preview
    displayXMLPreview(result);

    if (result.valid) {
      showNotification("XML preview generated successfully", "success");
    } else {
      showNotification(`XML generation failed: ${result.validation_message}`, "error");
    }

  } catch (error) {
    console.error("XML preview error:", error);
    showNotification(`Error generating XML: ${error.message}`, "error");
  }
}

/**
 * Display XML preview in modal or sidebar.
 */
function displayXMLPreview(result) {
  // Create or get preview modal
  let modal = document.getElementById("xml-preview-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "xml-preview-modal";
    modal.className = "modal";
    document.body.appendChild(modal);
  }

  const content = modal.querySelector(".modal-content") || document.createElement("div");
  content.className = "modal-content";
  content.innerHTML = "";

  // Header
  const header = document.createElement("div");
  header.className = "modal-header";
  const title = document.createElement("h2");
  title.textContent = "XML Preview";
  const closeBtn = document.createElement("button");
  closeBtn.className = "close-btn";
  closeBtn.textContent = "✕";
  closeBtn.addEventListener("click", () => modal.style.display = "none");
  header.appendChild(title);
  header.appendChild(closeBtn);
  content.appendChild(header);

  // Body
  const body = document.createElement("div");
  body.className = "modal-body";

  if (result.valid && result.xml_content) {
    // XML viewer
    const codeDiv = document.createElement("pre");
    codeDiv.className = "xml-code";
    codeDiv.textContent = result.xml_content;
    body.appendChild(codeDiv);

    // Copy button
    const copyBtn = document.createElement("button");
    copyBtn.className = "btn btn-copy";
    copyBtn.textContent = "Copy XML";
    copyBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(result.xml_content);
      showNotification("XML copied to clipboard", "success");
    });
    body.appendChild(copyBtn);
  } else {
    // Show errors
    const errorDiv = document.createElement("div");
    errorDiv.className = "error-message";
    errorDiv.textContent = result.validation_message || "Failed to generate XML";
    body.appendChild(errorDiv);

    if (result.errors && result.errors.length > 0) {
      const errorList = document.createElement("ul");
      for (const error of result.errors) {
        const li = document.createElement("li");
        li.textContent = error.message;
        errorList.appendChild(li);
      }
      body.appendChild(errorList);
    }
  }

  content.appendChild(body);
  if (!modal.querySelector(".modal-content")) {
    modal.appendChild(content);
  }

  modal.style.display = "flex";
}

// ==================== Utility Functions ====================

/**
 * Extract parameters from form controls.
 */
// ==================== Form Submission & Preview ====================
// Functions for extracting form data, validation, and XML preview generation.

/**
 * Extract all parameter values from the form.
 * Handles different parameter types (step_array, interval_array, enum_array, etc.).
 *
 * @param {HTMLFormElement} form - Form element containing parameters
 * @returns {Object} Parameter values keyed by parameter name
 */
function extractFormParameters(form) {
  const parameters = {};
  const formGroups = form.querySelectorAll(".form-group");

  console.log('[extractFormParameters] Found form groups:', formGroups.length);

  for (const group of formGroups) {
    const paramName = group.dataset.parameterName;
    const paramType = group.dataset.parameterType;

    console.log('[extractFormParameters] Processing:', { paramName, paramType });

    if (!paramName || !paramType) continue;

    let value;

    if (paramType === "enum_array") {
      // Collect selected checkboxes
      const checkboxes = group.querySelectorAll(`.enum-checkbox:checked`);
      value = Array.from(checkboxes).map((cb) => cb.value);
    } else if (paramType === "step_array") {
      // Collect step rows
      const tbody = group.querySelector(".steps-tbody");
      console.log('[extractFormParameters] step_array - found tbody:', tbody);
      if (tbody) {
        const rows = tbody.querySelectorAll(".step-row");
        console.log('[extractFormParameters] step_array - found rows:', rows.length);
        value = Array.from(rows).map((row) => ({
          time_hours: parseFloat(row.querySelector(".step-time").value),
          speed_kmh: parseFloat(row.querySelector(".step-speed").value)
        }));
        console.log('[extractFormParameters] step_array - extracted value:', value);
      } else {
        console.warn('[extractFormParameters] step_array - tbody not found!');
      }
    } else if (paramType === "flow_interval_array") {
      // Collect flow interval rows
      const tbody = group.querySelector(".intervals-tbody");
      if (tbody) {
        value = Array.from(tbody.querySelectorAll(".interval-row")).map((row) => ({
          begin_hours: parseFloat(row.querySelector(".interval-begin").value),
          end_hours: parseFloat(row.querySelector(".interval-end").value),
          vehsPerHour: parseFloat(row.querySelector(".interval-flow").value),
          target_speed: parseFloat(row.querySelector(".interval-speed").value)
        }));
      }
    } else if (paramType === "edge_array") {
      // Collect edge inputs
      const edgesList = group.querySelector(".edges-list");
      if (edgesList) {
        value = Array.from(edgesList.querySelectorAll(".edge-id-input"))
          .map((input) => input.value)
          .filter((v) => v.trim());
      }
    } else if (paramType === "array") {
      // Check for special array types
      const tbody = group.querySelector(".time-intervals-tbody");
      if (tbody) {
        // Time interval array
        value = Array.from(tbody.querySelectorAll(".time-interval-row")).map((row) => ({
          begin_hours: parseFloat(row.querySelector(".interval-begin").value),
          end_hours: parseFloat(row.querySelector(".interval-end").value),
          status: row.querySelector(".interval-status").value,
          allowed_vehicle_types: row.querySelector(".interval-vehicles").value
            .split(",")
            .map((v) => v.trim())
            .filter((v) => v)
        }));
      } else {
        // Generic array from textarea
        const control = group.querySelector(".form-control");
        if (control && control.tagName === "TEXTAREA") {
          try {
            value = JSON.parse(control.value);
          } catch (e) {
            value = [];
          }
        }
      }
    } else {
      // Simple input
      const control = group.querySelector(".form-control, input, select, textarea");
      if (control) {
        value = control.value;

        // Type conversion
        if (paramType === "integer") {
          value = parseInt(value);
        } else if (paramType === "number") {
          value = parseFloat(value);
        }
      }
    }

    if (value !== undefined) {
      parameters[paramName] = value;
    }
  }

  return parameters;
}

/**
 * Show notification message.
 */
// ==================== UI Utilities ====================
// Helper functions for user interface notifications and feedback.

function showNotification(message, type) {
  const notification = document.createElement("div");
  notification.className = `notification notification-${type}`;
  notification.textContent = message;

  document.body.appendChild(notification);

  // Auto-dismiss after 3 seconds
  setTimeout(() => {
    notification.remove();
  }, 3000);
}

/**
 * [FIX] Render unified vehicle type control for TEC vehicle restriction
 * This control changes its meaning based on restriction_mode:
 * - disallow_mode: Shows "禁止进入的车辆类型"
 * - allow_mode: Shows "允许进入的车辆类型"
 *
 * @param {Object} templateData - Template data containing disallow/allowed schemas
 * @returns {HTMLElement} Container with unified vehicle type control
 */
function renderUnifiedVehicleTypeControl(templateData) {
  const container = document.createElement("div");
  container.className = "form-group unified-vehicle-type-control";
  container.id = "unified-vehicle-type-container";

  // Find the restriction_mode default value
  const restrictionModeParam = templateData.parameters_schema.find(p => p.parameter_name === 'restriction_mode');
  const initialMode = restrictionModeParam?.default_value || 'disallow_mode';

  // Find the vehicle type schemas
  const disallowParam = templateData.parameters_schema.find(p => p.parameter_name === 'disallow_vehicle_types');
  const allowParam = templateData.parameters_schema.find(p => p.parameter_name === 'allowed_vehicle_types');

  // Label (will be updated dynamically)
  const label = document.createElement("label");
  label.id = "vehicle-type-label";
  label.htmlFor = "param-vehicle_types";
  label.textContent = initialMode === 'disallow_mode' ? '禁止进入的车辆类型' : '允许进入的车辆类型';
  container.appendChild(label);

  // Description (will be updated dynamically)
  const description = document.createElement("small");
  description.className = "description";
  description.id = "vehicle-type-description";
  const currentParam = initialMode === 'disallow_mode' ? disallowParam : allowParam;
  description.textContent = currentParam?.description || '';
  container.appendChild(description);

  // Checkbox group for vehicle types
  const checkboxContainer = document.createElement("div");
  checkboxContainer.className = "enum-array-control";
  checkboxContainer.id = "vehicle-type-checkboxes";

  const enumValues = disallowParam?.enum_values || allowParam?.enum_values || [];
  const defaultValues = initialMode === 'disallow_mode'
    ? (disallowParam?.default_value || [])
    : (allowParam?.default_value || []);

  enumValues.forEach(enumVal => {
    const checkboxDiv = document.createElement("div");
    checkboxDiv.className = "checkbox-item";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.name = "vehicle_types"; // Unified name, will be converted on submit
    checkbox.value = typeof enumVal === "string" ? enumVal : enumVal.value;
    checkbox.className = "enum-checkbox";
    checkbox.id = `vehicle-type-${checkbox.value}`;

    // Check default values
    if (defaultValues.includes(checkbox.value)) {
      checkbox.checked = true;
    }

    const checkboxLabel = document.createElement("label");
    checkboxLabel.htmlFor = checkbox.id;
    checkboxLabel.textContent = typeof enumVal === "string" ? enumVal : (enumVal.label || enumVal.value);

    checkboxDiv.appendChild(checkbox);
    checkboxDiv.appendChild(checkboxLabel);
    checkboxContainer.appendChild(checkboxDiv);
  });

  container.appendChild(checkboxContainer);

  // Hint (will be updated dynamically)
  const hint = document.createElement("span");
  hint.className = "config-hint";
  hint.id = "vehicle-type-hint";
  hint.textContent = initialMode === 'disallow_mode'
    ? '选中的车型将被禁止进入，其他车型可自由通行'
    : '仅选中的车型允许进入，其他车型被禁止';
  container.appendChild(hint);

  return container;
}

/**
 * [FIX] Update vehicle type control when restriction mode changes
 * @param {string} mode - 'disallow_mode' or 'allow_mode'
 */
function updateVehicleTypeControlForRestrictionMode(mode) {
  const label = document.getElementById('vehicle-type-label');
  const description = document.getElementById('vehicle-type-description');
  const hint = document.getElementById('vehicle-type-hint');
  const checkboxes = document.querySelectorAll('input[name="vehicle_types"]');

  if (!label || !hint) return; // Control not found

  if (mode === 'disallow_mode') {
    label.textContent = '禁止进入的车辆类型';
    hint.textContent = '选中的车型将被禁止进入，其他车型可自由通行';
    if (description) {
      description.textContent = '禁止进入的车辆类型（仅在禁止模式下使用）';
    }
    // Optionally clear selections when mode changes
    checkboxes.forEach(cb => cb.checked = false);
  } else if (mode === 'allow_mode') {
    label.textContent = '允许进入的车辆类型';
    hint.textContent = '仅选中的车型允许进入，其他车型被禁止';
    if (description) {
      description.textContent = '允许进入的车辆类型（仅在允许模式下使用）';
    }
    // Optionally clear selections when mode changes
    checkboxes.forEach(cb => cb.checked = false);
  }

  console.log(`[updateVehicleTypeControlForRestrictionMode] Updated for mode: ${mode}`);
}

// Export functions for use in other modules
window.generateFormFromTemplate = generateFormFromTemplate;
window.validateFormParameters = validateFormParameters;
window.generateXMLPreview = generateXMLPreview;
window.extractFormParameters = extractFormParameters;
window.renderUnifiedVehicleTypeControl = renderUnifiedVehicleTypeControl;
window.updateVehicleTypeControlForRestrictionMode = updateVehicleTypeControlForRestrictionMode;

// Export individual render functions for use in templates.html
window.renderStepArrayControl = renderStepArrayControl;
window.renderDHSIntervalControl = renderDHSIntervalControl;
window.renderFlowIntervalControl = renderFlowIntervalControl;
window.renderTECIntervalControl = renderTECIntervalControl;

// Export row addition functions for use in strategy_manager.js
window.addStepRow = addStepRow;
window.addFlowIntervalRow = addFlowIntervalRow;
