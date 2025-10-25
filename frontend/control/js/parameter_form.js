/**
 * Parameter Form Generator for Strategy Templates (v2.0)
 *
 * Generates dynamic parameter forms from template schemas.
 * Features:
 * - Automatic form generation from parameter schemas
 * - Real-time validation with error/warning display
 * - Unit conversion (hours ↔ seconds, km/h ↔ m/s)
 * - XML preview generation with syntax highlighting
 * - Support for complex parameter types (arrays, time ranges, etc.)
 *
 * @module parameter_form
 */

// ==================== Form Generation ====================

/**
 * Generate form HTML from template schema.
 *
 * @param {string} templateId - Template identifier
 * @param {Object} template - Template object with parameters_schema
 * @returns {string} HTML form string
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
function renderParameterControl(paramSchema, templateId) {
  const paramName = paramSchema.parameter_name || paramSchema.parameterName;
  const paramType = paramSchema.parameter_type || paramSchema.parameterType;
  const required = paramSchema.required || false;
  const defaultValue = paramSchema.default_value || paramSchema.defaultValue;

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
    case "flow_interval_array":
      control = renderFlowIntervalControl(paramName, paramSchema);
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
        control = renderTimeIntervalArrayControl(paramName, paramSchema);
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
function validateNumberRange(input, schema) {
  const value = parseFloat(input.value);
  const feedbackDiv = input.closest('.form-group')?.querySelector('.parameter-feedback');

  if (!feedbackDiv) return true;

  // Clear previous feedback
  feedbackDiv.textContent = '';
  feedbackDiv.className = 'parameter-feedback';
  feedbackDiv.dataset.feedback = '';

  // Check if required
  if (input.value === '' && schema.required) {
    feedbackDiv.className = 'parameter-feedback error';
    feedbackDiv.textContent = '此字段为必填项';
    feedbackDiv.dataset.feedback = 'error';
    return false;
  }

  if (input.value === '') {
    return true; // Empty optional field is valid
  }

  if (isNaN(value)) {
    feedbackDiv.className = 'parameter-feedback error';
    feedbackDiv.textContent = '请输入有效的数字';
    feedbackDiv.dataset.feedback = 'error';
    return false;
  }

  const minVal = schema.min_value;
  const maxVal = schema.max_value;

  if (minVal !== undefined && value < minVal) {
    feedbackDiv.className = 'parameter-feedback error';
    feedbackDiv.textContent = `值不能小于 ${minVal}`;
    feedbackDiv.dataset.feedback = 'error';
    return false;
  }

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
  container.className = "step-array-control";

  const stepStructure = schema.step_structure || schema.stepStructure || {};
  const defaultSteps = schema.default_value || [];

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
  });

  buttonDiv.appendChild(addBtn);
  container.appendChild(buttonDiv);

  return container;
}

/**
 * Add a step row to the steps table.
 */
function addStepRow(tbody, paramName, timeVal, speedVal, stepStructure) {
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
  });
  actionCell.appendChild(removeBtn);
  row.appendChild(actionCell);

  tbody.appendChild(row);
}

/**
 * Render flow_interval_array control.
 */
function renderFlowIntervalControl(paramName, schema) {
  const container = document.createElement("div");
  container.className = "flow-interval-control";

  const defaultIntervals = schema.default_value || [];

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

  defaultIntervals.forEach((interval) => {
    const beginHours = interval.begin_hours !== undefined ? interval.begin_hours : (interval.begin_seconds / 3600);
    const endHours = interval.end_hours !== undefined ? interval.end_hours : (interval.end_seconds / 3600);
    const flowRate = interval.vehsPerHour || 480;
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
  addBtn.textContent = "+ Add Interval";
  addBtn.addEventListener("click", (e) => {
    e.preventDefault();
    addFlowIntervalRow(tbody, paramName, 0, 1, 480, 15);
  });

  buttonDiv.appendChild(addBtn);
  container.appendChild(buttonDiv);

  return container;
}

/**
 * Add a flow interval row.
 */
function addFlowIntervalRow(tbody, paramName, beginHours, endHours, flowRate, targetSpeed) {
  const row = document.createElement("tr");
  row.className = "interval-row";

  // Begin time
  const beginCell = document.createElement("td");
  const beginInput = document.createElement("input");
  beginInput.type = "number";
  beginInput.className = "interval-begin";
  beginInput.min = "0";
  beginInput.max = "24";
  beginInput.step = "0.5";
  beginInput.value = beginHours || 0;
  beginCell.appendChild(beginInput);
  row.appendChild(beginCell);

  // End time
  const endCell = document.createElement("td");
  const endInput = document.createElement("input");
  endInput.type = "number";
  endInput.className = "interval-end";
  endInput.min = "0";
  endInput.max = "24";
  endInput.step = "0.5";
  endInput.value = endHours || 1;
  endCell.appendChild(endInput);
  row.appendChild(endCell);

  // Flow rate
  const flowCell = document.createElement("td");
  const flowInput = document.createElement("input");
  flowInput.type = "number";
  flowInput.className = "interval-flow";
  flowInput.min = "0";
  flowInput.max = "2000";
  flowInput.value = flowRate || 480;
  flowCell.appendChild(flowInput);
  row.appendChild(flowCell);

  // Target speed
  const speedCell = document.createElement("td");
  const speedInput = document.createElement("input");
  speedInput.type = "number";
  speedInput.className = "interval-speed";
  speedInput.min = "0";
  speedInput.max = "50";
  speedInput.step = "0.5";
  speedInput.value = targetSpeed || 15;
  speedCell.appendChild(speedInput);
  row.appendChild(speedCell);

  // Remove button
  const actionCell = document.createElement("td");
  const removeBtn = document.createElement("button");
  removeBtn.type = "button";
  removeBtn.className = "btn-remove-interval";
  removeBtn.textContent = "Remove";
  removeBtn.addEventListener("click", (e) => {
    e.preventDefault();
    row.remove();
  });
  actionCell.appendChild(removeBtn);
  row.appendChild(actionCell);

  tbody.appendChild(row);
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
  const control = document.createElement("input");
  control.type = "text";
  control.id = `param-${paramName}`;
  control.name = paramName;
  control.className = "form-control";

  if (schema.default_value !== undefined) {
    control.value = schema.default_value;
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

/**
 * Render time interval array control (for DHS intervals with status).
 */
function renderTimeIntervalArrayControl(paramName, schema) {
  const container = document.createElement("div");
  container.className = "time-interval-array-control";

  const defaultIntervals = schema.default_value || [];

  // Create table for intervals
  const table = document.createElement("table");
  table.className = "time-intervals-table";

  // Header
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  const startHeader = document.createElement("th");
  startHeader.textContent = "Start (hours)";
  const endHeader = document.createElement("th");
  endHeader.textContent = "End (hours)";
  const statusHeader = document.createElement("th");
  statusHeader.textContent = "Status";
  const vehiclesHeader = document.createElement("th");
  vehiclesHeader.textContent = "Allowed Vehicle Types";

  headerRow.appendChild(startHeader);
  headerRow.appendChild(endHeader);
  headerRow.appendChild(statusHeader);
  headerRow.appendChild(vehiclesHeader);
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Body
  const tbody = document.createElement("tbody");
  tbody.className = "time-intervals-tbody";
  tbody.dataset.parameterName = paramName;

  defaultIntervals.forEach((interval) => {
    const beginHours = interval.begin_hours || 0;
    const endHours = interval.end_hours || 24;
    const status = interval.status || "CLOSED";
    const allowedTypes = interval.allowed_vehicle_types || [];

    addTimeIntervalRow(tbody, paramName, beginHours, endHours, status, allowedTypes);
  });

  table.appendChild(tbody);
  container.appendChild(table);

  return container;
}

/**
 * Add a time interval row.
 */
function addTimeIntervalRow(tbody, paramName, beginHours, endHours, status, allowedTypes) {
  const row = document.createElement("tr");
  row.className = "time-interval-row";

  // Begin time
  const beginCell = document.createElement("td");
  const beginInput = document.createElement("input");
  beginInput.type = "number";
  beginInput.className = "interval-begin";
  beginInput.min = "0";
  beginInput.max = "24";
  beginInput.step = "0.5";
  beginInput.value = beginHours || 0;
  beginCell.appendChild(beginInput);
  row.appendChild(beginCell);

  // End time
  const endCell = document.createElement("td");
  const endInput = document.createElement("input");
  endInput.type = "number";
  endInput.className = "interval-end";
  endInput.min = "0";
  endInput.max = "24";
  endInput.step = "0.5";
  endInput.value = endHours || 24;
  endCell.appendChild(endInput);
  row.appendChild(endCell);

  // Status
  const statusCell = document.createElement("td");
  const statusSelect = document.createElement("select");
  statusSelect.className = "interval-status";
  const openOption = document.createElement("option");
  openOption.value = "OPEN";
  openOption.textContent = "OPEN";
  const closedOption = document.createElement("option");
  closedOption.value = "CLOSED";
  closedOption.textContent = "CLOSED";
  statusSelect.appendChild(openOption);
  statusSelect.appendChild(closedOption);
  statusSelect.value = status || "CLOSED";
  statusCell.appendChild(statusSelect);
  row.appendChild(statusCell);

  // Vehicle types (simplified - just show as text)
  const vehiclesCell = document.createElement("td");
  const vehiclesInput = document.createElement("input");
  vehiclesInput.type = "text";
  vehiclesInput.className = "interval-vehicles";
  vehiclesInput.placeholder = "e.g., passenger,bus,truck";
  vehiclesInput.value = allowedTypes.join(", ");
  vehiclesCell.appendChild(vehiclesInput);
  row.appendChild(vehiclesCell);

  tbody.appendChild(row);
}

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
function extractFormParameters(form) {
  const parameters = {};
  const formGroups = form.querySelectorAll(".form-group");

  for (const group of formGroups) {
    const paramName = group.dataset.parameterName;
    const paramType = group.dataset.parameterType;

    if (!paramName || !paramType) continue;

    let value;

    if (paramType === "enum_array") {
      // Collect selected checkboxes
      const checkboxes = group.querySelectorAll(`.enum-checkbox:checked`);
      value = Array.from(checkboxes).map((cb) => cb.value);
    } else if (paramType === "step_array") {
      // Collect step rows
      const tbody = group.querySelector(".steps-tbody");
      if (tbody) {
        value = Array.from(tbody.querySelectorAll(".step-row")).map((row) => ({
          time_hours: parseFloat(row.querySelector(".step-time").value),
          speed_kmh: parseFloat(row.querySelector(".step-speed").value)
        }));
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

// Export functions for use in other modules
window.generateFormFromTemplate = generateFormFromTemplate;
window.validateFormParameters = validateFormParameters;
window.generateXMLPreview = generateXMLPreview;
window.extractFormParameters = extractFormParameters;
