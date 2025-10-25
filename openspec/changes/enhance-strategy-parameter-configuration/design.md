# Design: Enhanced Strategy Parameter Configuration

## Overview

This document details the technical design for enhancing the strategy parameter configuration page (Step 3) to address current usability issues and enable successful strategy instance creation.

## Architecture

### Component Structure

```
frontend/control/
├── templates.html                    # Main page (enhanced Step 3)
├── js/
│   ├── strategy_manager.js          # Core strategy CRUD (enhanced)
│   ├── parameter_form_builder.js    # NEW: Dynamic form generation
│   ├── edge_display_table.js        # NEW: Edge information table
│   ├── name_generator.js            # NEW: Auto-naming logic
│   └── description_generator.js     # NEW: Auto-description logic
└── css/
    └── strategy_config.css           # NEW: Step 3 specific styles
```

### Data Flow

```
User Input (Step 3)
    ↓
Parameter Form Builder
    ↓ (validation)
Parameter Validators
    ↓ (if valid)
Name Generator + Description Generator
    ↓
XML Preview Generator
    ↓ (user confirms)
Strategy Manager (save)
    ↓
POST /api/v1/control/strategy-instances
    ↓
Backend Validation + Storage
```

## Component Design

### 1. Parameter Form Builder (`parameter_form_builder.js`)

**Purpose**: Dynamically generate form inputs based on template parameter schema

**Key Methods**:

```javascript
class ParameterFormBuilder {
    constructor(templateSchema) {
        this.schema = templateSchema;
        this.formContainer = null;
        this.validators = new Map();
    }

    /**
     * Build complete parameter form
     * @param {HTMLElement} container - Form container element
     * @param {Object} existingValues - Pre-fill values for edit mode
     */
    buildForm(container, existingValues = {}) {
        // Group parameters by category
        const grouped = this.groupParameters(this.schema.parameters_schema);

        // Render each group
        for (const [category, params] of Object.entries(grouped)) {
            this.renderGroup(container, category, params, existingValues);
        }

        // Attach event listeners
        this.attachValidators();
    }

    /**
     * Group parameters by category (Location, Time, Control, Other)
     */
    groupParameters(parameters) {
        const categories = {
            location: [], // affected_edges, entrance_edges, etc.
            time: [],     // time_intervals, intervals, etc.
            control: [],  // speed_steps, allowed_vehicle_types, etc.
            other: []
        };

        parameters.forEach(param => {
            const category = this.categorizeParameter(param.parameter_name);
            categories[category].push(param);
        });

        return categories;
    }

    /**
     * Render parameter group with collapsible section
     */
    renderGroup(container, category, parameters, existingValues) {
        const section = document.createElement('div');
        section.className = 'param-group';
        section.id = `param-group-${category}`;

        // Group header
        const header = this.createGroupHeader(category);
        section.appendChild(header);

        // Group content
        const content = document.createElement('div');
        content.className = 'param-group-content';

        parameters.forEach(param => {
            const field = this.createParameterField(param, existingValues[param.parameter_name]);
            content.appendChild(field);
        });

        section.appendChild(content);
        container.appendChild(section);
    }

    /**
     * Create parameter input field with smart components
     */
    createParameterField(paramSchema, existingValue) {
        const field = document.createElement('div');
        field.className = 'form-field';
        field.dataset.paramName = paramSchema.parameter_name;

        // Label with icon
        const label = this.createLabel(paramSchema);
        field.appendChild(label);

        // Input component (type-specific)
        const input = this.createInputComponent(paramSchema, existingValue);
        field.appendChild(input);

        // Hint text
        const hint = this.createHintText(paramSchema);
        field.appendChild(hint);

        // Error placeholder
        const error = document.createElement('div');
        error.className = 'field-error';
        error.id = `error-${paramSchema.parameter_name}`;
        field.appendChild(error);

        return field;
    }

    /**
     * Create input component based on parameter type
     */
    createInputComponent(paramSchema, existingValue) {
        const type = paramSchema.parameter_type;

        switch(type) {
            case 'array':
                return this.createArrayInput(paramSchema, existingValue);
            case 'time_range_array':
                return this.createTimeIntervalInput(paramSchema, existingValue);
            case 'step_array':
                return this.createStepArrayInput(paramSchema, existingValue);
            case 'integer':
            case 'float':
                return this.createNumberInput(paramSchema, existingValue);
            case 'string':
                return this.createTextInput(paramSchema, existingValue);
            case 'boolean':
                return this.createBooleanInput(paramSchema, existingValue);
            case 'enum':
                return this.createEnumInput(paramSchema, existingValue);
            default:
                return this.createTextInput(paramSchema, existingValue);
        }
    }

    /**
     * Create array input with smart placeholder
     */
    createArrayInput(paramSchema, existingValue) {
        const textarea = document.createElement('textarea');
        textarea.id = `param-${paramSchema.parameter_name}`;
        textarea.name = paramSchema.parameter_name;
        textarea.rows = 6;
        textarea.className = 'array-input';

        // Set placeholder based on parameter name and default value
        textarea.placeholder = this.generateArrayPlaceholder(paramSchema);

        // Pre-fill value
        if (existingValue) {
            if (Array.isArray(existingValue)) {
                if (existingValue.length > 0 && Array.isArray(existingValue[0])) {
                    // Nested array - use JSON
                    textarea.value = JSON.stringify(existingValue, null, 2);
                } else {
                    // Simple array - newline separated
                    textarea.value = existingValue.join('\n');
                }
            }
        } else if (paramSchema.default_value) {
            // Use template default
            const defaultVal = paramSchema.default_value;
            if (Array.isArray(defaultVal) && defaultVal.length > 0 && Array.isArray(defaultVal[0])) {
                textarea.value = JSON.stringify(defaultVal, null, 2);
            } else if (Array.isArray(defaultVal)) {
                textarea.value = defaultVal.join('\n');
            }
        }

        // Attach validator
        textarea.addEventListener('blur', () => this.validateArrayField(paramSchema, textarea));

        return textarea;
    }

    /**
     * Generate smart placeholder for array inputs
     */
    generateArrayPlaceholder(paramSchema) {
        const name = paramSchema.parameter_name.toLowerCase();

        // Time-related parameters
        if (name.includes('time') || name.includes('interval')) {
            if (paramSchema.default_value && Array.isArray(paramSchema.default_value[0])) {
                return `示例格式:\n${JSON.stringify(paramSchema.default_value, null, 2)}\n\n可直接编辑JSON,或每行输入一个时段`;
            }
            return `时段格式示例:\n[\n  [7, 9],\n  [17, 19]\n]\n\n每行一个时间段 [开始小时, 结束小时]`;
        }

        // Speed-related parameters
        if (name.includes('speed')) {
            return `限速值示例(每行一个):\n80\n60\n40\n\n或JSON格式:[80, 60, 40]`;
        }

        // Vehicle type parameters
        if (name.includes('vehicle') || name.includes('type')) {
            return `车型列表示例:\npassenger\ntruck\nbus\n\n或用逗号分隔:passenger, truck, bus`;
        }

        // Edge-related parameters
        if (name.includes('edge') || name.includes('segment')) {
            return `路段ID列表示例:\n-5880\n-5881\n-5882\n\n或用逗号分隔:-5880, -5881, -5882`;
        }

        // Entrance parameters
        if (name.includes('entrance')) {
            return `入口列表示例:\nentrance_1\nentrance_2\n\n或用逗号分隔:entrance_1, entrance_2`;
        }

        // Generic fallback
        return `多个值,每行一个:\nvalue1\nvalue2\nvalue3\n\n或JSON格式:["value1", "value2", "value3"]`;
    }

    /**
     * Validate array field on blur
     */
    validateArrayField(paramSchema, textarea) {
        const value = textarea.value.trim();
        const errorEl = document.getElementById(`error-${paramSchema.parameter_name}`);

        if (!value && paramSchema.required) {
            this.showError(errorEl, '此字段为必填项');
            return false;
        }

        if (!value) {
            this.clearError(errorEl);
            return true;
        }

        try {
            let parsed;

            // Try JSON parse first
            if (value.startsWith('[')) {
                parsed = JSON.parse(value);
                if (!Array.isArray(parsed)) {
                    this.showError(errorEl, 'JSON格式需要是数组');
                    return false;
                }
            } else {
                // Parse as newline/comma separated
                parsed = value.split(/[,\n]/).map(s => s.trim()).filter(s => s);
            }

            // Check min items
            if (paramSchema.min_items && parsed.length < paramSchema.min_items) {
                this.showError(errorEl, `至少需要 ${paramSchema.min_items} 个项目,当前: ${parsed.length}`);
                return false;
            }

            this.clearError(errorEl);
            return true;

        } catch (e) {
            this.showError(errorEl, `JSON格式不正确: ${e.message}`);
            return false;
        }
    }

    /**
     * Show validation error
     */
    showError(errorEl, message) {
        errorEl.textContent = message;
        errorEl.style.display = 'block';
    }

    /**
     * Clear validation error
     */
    clearError(errorEl) {
        errorEl.textContent = '';
        errorEl.style.display = 'none';
    }
}
```

### 2. Edge Display Table (`edge_display_table.js`)

**Purpose**: Display selected edges with comprehensive information and inline actions

**Key Methods**:

```javascript
class EdgeDisplayTable {
    constructor(containerEl, strategyType) {
        this.container = containerEl;
        this.strategyType = strategyType;
        this.edges = [];
        this.onRemove = null; // Callback when edge removed
    }

    /**
     * Load and display edges
     * @param {Array<string>} edgeIds - Edge IDs to display
     */
    async loadEdges(edgeIds) {
        // Fetch full edge information from API
        const response = await fetch('/api/v1/control/edges/batch-info', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({edge_ids: edgeIds})
        });

        this.edges = await response.json();
        this.render();
        this.checkValidation();
    }

    /**
     * Render edge table
     */
    render() {
        this.container.innerHTML = '';

        // Summary section
        const summary = this.renderSummary();
        this.container.appendChild(summary);

        // Validation warnings (if any)
        const warnings = this.renderWarnings();
        if (warnings) {
            this.container.appendChild(warnings);
        }

        // Table
        const table = this.renderTable();
        this.container.appendChild(table);

        // Export button
        const exportBtn = this.renderExportButton();
        this.container.appendChild(exportBtn);
    }

    /**
     * Render summary section
     */
    renderSummary() {
        const summary = document.createElement('div');
        summary.className = 'edge-summary';

        const totalLength = this.edges.reduce((sum, e) => sum + e.length_m, 0) / 1000;
        const routes = [...new Set(this.edges.map(e => e.route_code))];
        const laneRange = {
            min: Math.min(...this.edges.map(e => e.lane_count)),
            max: Math.max(...this.edges.map(e => e.lane_count))
        };

        summary.innerHTML = `
            <div class="summary-item">
                <span class="summary-label">已选择</span>
                <span class="summary-value">${this.edges.length} 个路段</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">总长度</span>
                <span class="summary-value">${totalLength.toFixed(2)} km</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">覆盖路线</span>
                <span class="summary-value">${routes.join(', ')}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">车道数范围</span>
                <span class="summary-value">${laneRange.min}-${laneRange.max} 车道</span>
            </div>
        `;

        return summary;
    }

    /**
     * Check validation and render warnings
     */
    checkValidation() {
        this.validationIssues = [];

        // DHS-specific validations
        if (this.strategyType === 'DHS') {
            // Check lane count >= 4
            const invalidLanes = this.edges.filter(e => e.lane_count < 4);
            if (invalidLanes.length > 0) {
                this.validationIssues.push({
                    type: 'error',
                    message: 'DHS策略要求车道数≥4,以下路段不符合:',
                    details: invalidLanes.map(e => `${e.edge_id} (${e.lane_count}车道)`)
                });
            }

            // Check edge continuity
            const discontinuities = this.checkEdgeContinuity();
            if (discontinuities.length > 0) {
                this.validationIssues.push({
                    type: 'warning',
                    message: '警告:所选路段不连续,DHS策略可能效果降低',
                    details: discontinuities
                });
            }
        }
    }

    /**
     * Check if edges form continuous path
     * @returns {Array<string>} List of discontinuity descriptions
     */
    checkEdgeContinuity() {
        const gaps = [];
        const sorted = [...this.edges].sort((a, b) => a.start_stake - b.start_stake);

        for (let i = 0; i < sorted.length - 1; i++) {
            const current = sorted[i];
            const next = sorted[i + 1];

            if (current.end_stake < next.start_stake) {
                const gapSize = next.start_stake - current.end_stake;
                gaps.push(`K${(current.end_stake/1000).toFixed(1)} 到 K${(next.start_stake/1000).toFixed(1)} 之间存在 ${gapSize}m 间隙`);
            }
        }

        return gaps;
    }

    /**
     * Render warnings banner
     */
    renderWarnings() {
        if (this.validationIssues.length === 0) {
            return null;
        }

        const warnings = document.createElement('div');
        warnings.className = 'validation-warnings';

        this.validationIssues.forEach(issue => {
            const banner = document.createElement('div');
            banner.className = `validation-banner ${issue.type}`;

            const icon = issue.type === 'error' ? '❌' : '⚠️';
            banner.innerHTML = `
                <div class="banner-icon">${icon}</div>
                <div class="banner-content">
                    <div class="banner-message">${issue.message}</div>
                    ${issue.details ? `<ul class="banner-details">${issue.details.map(d => `<li>${d}</li>`).join('')}</ul>` : ''}
                </div>
            `;

            warnings.appendChild(banner);
        });

        return warnings;
    }

    /**
     * Render edge information table
     */
    renderTable() {
        const table = document.createElement('table');
        table.className = 'edge-table';

        // Table header
        table.innerHTML = `
            <thead>
                <tr>
                    <th>序号</th>
                    <th>Edge ID</th>
                    <th>路线</th>
                    <th>路段</th>
                    <th>起始桩号</th>
                    <th>结束桩号</th>
                    <th>长度</th>
                    <th>车道数</th>
                    <th>方向</th>
                    <th>节点类型</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
                ${this.edges.map((edge, idx) => this.renderTableRow(edge, idx + 1)).join('')}
            </tbody>
        `;

        // Attach remove handlers
        table.querySelectorAll('.remove-edge-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const edgeId = e.target.dataset.edgeId;
                this.removeEdge(edgeId);
            });
        });

        return table;
    }

    /**
     * Render single table row
     */
    renderTableRow(edge, index) {
        return `
            <tr data-edge-id="${edge.edge_id}">
                <td>${index}</td>
                <td class="edge-id">${edge.edge_id}</td>
                <td>${edge.route_code}</td>
                <td>${edge.section_code}</td>
                <td>K${(edge.start_stake / 1000).toFixed(1)}</td>
                <td>K${(edge.end_stake / 1000).toFixed(1)}</td>
                <td>${edge.length_m}m</td>
                <td>${edge.lane_count}</td>
                <td>${this.translateDirection(edge.direction)}</td>
                <td>${this.translateNodeType(edge.node_type)}</td>
                <td>
                    <button class="remove-edge-btn" data-edge-id="${edge.edge_id}">移除</button>
                </td>
            </tr>
        `;
    }

    /**
     * Remove edge from list
     */
    removeEdge(edgeId) {
        this.edges = this.edges.filter(e => e.edge_id !== edgeId);
        this.render();

        // Trigger callback
        if (this.onRemove) {
            this.onRemove(edgeId);
        }
    }

    /**
     * Get current edge IDs
     */
    getEdgeIds() {
        return this.edges.map(e => e.edge_id);
    }
}
```

### 3. Name Generator (`name_generator.js`)

**Purpose**: Generate strategy names based on template rules and parameters

**Key Methods**:

```javascript
class StrategyNameGenerator {
    /**
     * Generate strategy name based on type and parameters
     * @param {string} strategyType - VSS, DHS, or TEC
     * @param {Object} parameters - Strategy parameters
     * @param {Array<Object>} edges - Selected edge information
     * @returns {Promise<string>} Generated name
     */
    static async generate(strategyType, parameters, edges) {
        switch(strategyType) {
            case 'VSS':
                return this.generateVSSName(parameters, edges);
            case 'DHS':
                return this.generateDHSName(parameters, edges);
            case 'TEC':
                return this.generateTECName(parameters, edges);
            default:
                return `${strategyType}策略_${Date.now()}`;
        }
    }

    /**
     * Generate VSS strategy name
     * Format: "{Route} {Section} 限速{Speed}km/h ({Time})"
     */
    static generateVSSName(params, edges) {
        const location = this.extractLocation(edges);
        const speed = params.speed_limit || (params.speed_steps && params.speed_steps[1]?.speed) || '变速';
        const time = this.extractTimePeriod(params.time_intervals || [[0, 24]]);

        return `${location.route} ${location.section} 限速${speed}km/h (${time})`;
    }

    /**
     * Generate DHS strategy name
     * Format: "{Route} {Section} 应急车道开放 ({Time})"
     */
    static generateDHSName(params, edges) {
        const location = this.extractLocation(edges);
        const time = this.extractTimePeriod(params.intervals?.map(i => [i.begin/3600, i.end/3600]) || [[0, 24]]);

        return `${location.route} ${location.section} 应急车道开放 (${time})`;
    }

    /**
     * Generate TEC strategy name
     * Format: "{Entrance} {ControlType} ({Time/Details})"
     */
    static async generateTECName(params, edges) {
        const entranceName = await this.extractEntranceName(edges[0]);
        const controlType = this.extractTECControlType(params);
        const detail = this.extractTECDetail(params);

        return `${entranceName} ${controlType} (${detail})`;
    }

    /**
     * Extract location string from edges
     */
    static extractLocation(edges) {
        if (!edges || edges.length === 0) {
            return {route: '未知路线', section: '未知路段'};
        }

        const routes = [...new Set(edges.map(e => e.route_code))];
        const route = routes.length === 1 ? routes[0] : '多路线';

        const sections = [...new Set(edges.map(e => e.section_code))];
        const section = sections.length <= 2 ? sections.join('-') : `${sections[0]}-${sections[sections.length-1]}`;

        return {route, section};
    }

    /**
     * Extract time period description
     */
    static extractTimePeriod(intervals) {
        if (!intervals || intervals.length === 0) {
            return '定时管控';
        }

        // Flatten if nested
        const flattened = intervals[0] instanceof Array ? intervals : [intervals];

        // Check for common patterns
        const isMorningPeak = flattened.some(([start, end]) => start >= 7 && end <= 10);
        const isEveningPeak = flattened.some(([start, end]) => start >= 17 && end <= 20);
        const isFullDay = flattened.some(([start, end]) => start === 0 && end === 24);

        if (isFullDay) return '全天';
        if (isMorningPeak && isEveningPeak) return '早晚高峰';
        if (isMorningPeak) return '早高峰';
        if (isEveningPeak) return '晚高峰';

        return '定时管控';
    }

    /**
     * Extract entrance name from edge data
     */
    static async extractEntranceName(edge) {
        if (!edge) return '未知入口';

        // Try to get junction name from edge metadata
        if (edge.from_junction_name) {
            return edge.from_junction_name.replace('入口', '');
        }

        // Fallback to route + section
        return `${edge.route_code} ${edge.section_code}入口`;
    }

    /**
     * Extract TEC control type
     */
    static extractTECControlType(params) {
        if (params.control_mode === 'closure') {
            if (params.allowed_vehicle_types && params.allowed_vehicle_types.includes('truck')) {
                return '货车限行';
            }
            return '入口关闭';
        }
        return '计量控制';
    }

    /**
     * Extract TEC detail string
     */
    static extractTECDetail(params) {
        if (params.control_mode === 'metering') {
            const flow = params.flow_intervals?.[0]?.vehsPerHour || 300;
            return flow < 300 ? '高峰限流' : '计量管控';
        }

        const time = this.extractTimePeriod(params.intervals?.map(i => [i.begin/3600, i.end/3600]));
        return time;
    }

    /**
     * Ensure name uniqueness
     * @param {string} baseName - Generated base name
     * @returns {Promise<string>} Unique name
     */
    static async ensureUnique(baseName) {
        // Check against existing strategies
        const response = await fetch(`/api/v1/control/strategy-instances?name=${encodeURIComponent(baseName)}`);
        const existing = await response.json();

        if (existing.strategies.length === 0) {
            return baseName;
        }

        // Append counter
        let counter = 2;
        while (true) {
            const candidateName = `${baseName} (${counter})`;
            const checkResponse = await fetch(`/api/v1/control/strategy-instances?name=${encodeURIComponent(candidateName)}`);
            const checkExisting = await checkResponse.json();

            if (checkExisting.strategies.length === 0) {
                return candidateName;
            }
            counter++;
        }
    }
}
```

### 4. Description Generator (`description_generator.js`)

Similar structure to Name Generator, but creates multi-line formatted descriptions using template metadata and parameter values.

## Database Schema

No schema changes required. Uses existing `dim.sim_network_edges` table for edge information retrieval.

## API Endpoints

### Existing (No Changes)

- `POST /api/v1/control/strategy-instances` - Create strategy
- `PUT /api/v1/control/strategy-instances/{id}` - Update strategy
- `GET /api/v1/control/strategy-instances` - List strategies
- `GET /api/v1/control/templates/{id}` - Get template schema

### New Endpoints (Optional Enhancement)

```python
# API endpoint for batch edge information retrieval
@router.post("/api/v1/control/edges/batch-info")
async def get_batch_edge_info(request: BatchEdgeInfoRequest):
    """
    Get detailed information for multiple edges

    Request:
        {
            "edge_ids": ["-5880", "-5881", "edge_k10_001"]
        }

    Response:
        [
            {
                "edge_id": "-5880",
                "route_code": "G4202",
                "section_code": "K10-K15",
                "start_stake": 10200,
                "end_stake": 10800,
                "length_m": 600,
                "lane_count": 4,
                "direction": "clockwise",
                "node_type": "normal",
                "from_junction_id": "j_123",
                "from_junction_name": "锦江收费站入口",
                "demonstration_segment": "成都示范段"
            },
            ...
        ]
    """
    pass

# API endpoint for edge ID validation
@router.post("/api/v1/control/edges/validate")
async def validate_edge_ids(request: EdgeValidationRequest):
    """
    Validate edge IDs exist in network

    Request:
        {
            "edge_ids": ["-5880", "invalid_edge"]
        }

    Response:
        {
            "valid": ["-5880"],
            "invalid": ["invalid_edge"]
        }
    """
    pass
```

## UI/UX Specifications

### Step 3 Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Step 3: 配置参数                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  已选路段 (15个)  总长度: 8.5km  [导出列表]          │  │
│  │                                                       │  │
│  │  ⚠️ 警告: 所选路段不连续... [查看详情]                │  │
│  │                                                       │  │
│  │  [Edge Table - 10 columns, scrollable]               │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  📍 管控位置                           [收起 ▲]      │  │
│  │  ────────────────────────────────────────────        │  │
│  │  (Location parameters shown here)                    │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  ⏰ 时间配置                           [收起 ▲]      │  │
│  │  ────────────────────────────────────────────        │  │
│  │  (Time parameters shown here)                        │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  🚗 管控参数                           [收起 ▲]      │  │
│  │  ────────────────────────────────────────────        │  │
│  │  (Control parameters shown here)                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  策略名称 *              [建议名称 🔄]               │  │
│  │  [G4202 K10-K15 限速80km/h (早晚高峰)            ]  │  │
│  │                                                       │  │
│  │  策略描述 *              [重新生成 🔄]               │  │
│  │  [                                                 ]  │  │
│  │  [ Auto-generated description...                  ]  │  │
│  │  [                                                 ]  │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  SUMO XML 预览                         [复制XML ▼]   │  │
│  │  ────────────────────────────────────────────        │  │
│  │  <variableSpeedSign id="..." edges="...">            │  │
│  │    <step time="25200" speed="22.22"/>               │  │
│  │  </variableSpeedSign>                                │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│                        [上一步]  [保存策略]                │
└─────────────────────────────────────────────────────────────┘
```

### Color Scheme

- **Validation Error**: `#e74c3c` (Red)
- **Validation Warning**: `#f39c12` (Orange)
- **Success/Valid**: `#27ae60` (Green)
- **Info/Hint**: `#3498db` (Blue)
- **Group Headers**: `#2c3e50` (Dark Gray)

## Testing Strategy

### Unit Tests

- ParameterFormBuilder: Test each input type generation
- EdgeDisplayTable: Test continuity checking, validation logic
- NameGenerator: Test name generation for each strategy type
- DescriptionGenerator: Test description templates

### Integration Tests

- Full Step 3 workflow with real template schemas
- Edge removal and table updates
- Name/description auto-generation and override
- XML preview updates on parameter changes

### E2E Tests (Playwright)

```javascript
test('Create VSS strategy with auto-generated name and description', async ({ page }) => {
    await page.goto('/control/templates.html');

    // Select VSS template
    await page.click('text=VSS Moderate');

    // Select edges (Step 2)
    await page.click('text=G4202');
    await page.click('text=K10-K15');
    await page.click('.apply-filter-btn');
    await page.click('.select-all-edges');

    // Proceed to Step 3
    await page.click('#step2-next');

    // Verify edge table displayed
    await expect(page.locator('.edge-table')).toBeVisible();
    await expect(page.locator('.edge-table tbody tr')).toHaveCount(15);

    // Fill parameters
    await page.fill('#param-speed_limit', '80');
    await page.fill('#param-time_intervals', '[[7, 9], [17, 19]]');

    // Verify auto-generated name
    await expect(page.locator('#param-strategy_name')).toHaveValue(/G4202.*限速80km\/h/);

    // Verify auto-generated description
    await expect(page.locator('#param-strategy_description')).toContainText('可变限速策略');
    await expect(page.locator('#param-strategy_description')).toContainText('G4202');
    await expect(page.locator('#param-strategy_description')).toContainText('80 km/h');

    // Save strategy
    await page.click('.save-strategy-btn');

    // Verify success
    await expect(page.locator('.success-message')).toContainText('策略创建成功');
});
```

## Migration Path

1. **Phase 1**: Deploy enhanced parameter form builder (backward compatible)
2. **Phase 2**: Add edge display table
3. **Phase 3**: Implement auto-generation features (name, description)
4. **Phase 4**: Remove personnel fields (if present)
5. **Phase 5**: Add XML preview enhancements

## Performance Considerations

- **Edge Table Rendering**: Use virtual scrolling for >50 edges
- **XML Preview Updates**: Debounce parameter changes (500ms delay)
- **Name Generation**: Cache generated names to avoid duplicate API calls
- **Edge Information Loading**: Batch API request instead of individual queries

## Security Considerations

- **XSS Prevention**: Sanitize all user inputs before rendering in HTML
- **CSRF Protection**: Use CSRF tokens for all form submissions
- **Input Validation**: Server-side validation in addition to client-side
- **Rate Limiting**: Limit name uniqueness check API calls to prevent abuse
