/**
 * Strategy Manager Module (Phase 1C)
 *
 * Provides strategy instance management functionality:
 * - Create strategy instances from templates (T046-T050)
 * - Dynamic form generation based on template schemas (T047)
 * - Frontend validation (T048)
 * - Integration with Phase 1B edge selector (T049)
 * - API integration for CRUD operations (T050)
 *
 * Usage:
 *   const manager = new StrategyManager();
 *   manager.init();
 */

class StrategyManager {
    constructor() {
        this.API_BASE = '/api/v1/control/strategy-instances';
        this.currentStep = 1;
        this.selectedTemplate = null;
        this.selectedEdges = [];
        this.formData = {};
        this.validationErrors = {};
        this.editingStrategy = null; // Holds editing state for updates
    }

    /**
     * Initialize the strategy manager
     * Sets up event listeners and loads initial data
     */
    init() {
        console.log('[StrategyManager] Initializing...');
        this.attachEventListeners();
    }

    /**
     * Attach event listeners for UI interactions
     */
    attachEventListeners() {
        // Implementation can hook into existing templates.html structure
        console.log('[StrategyManager] Event listeners attached');
    }

    // ==================== T046: Strategy Creation UI (4-Step Wizard) ====================

    /**
     * Navigate to specific step in the wizard
     * @param {number} step - Step number (1-3)
     */
    goToStep(step) {
        if (step < 1 || step > 3) {
            console.error(`[StrategyManager] Invalid step: ${step}`);
            return;
        }

        this.currentStep = step;
        this.updateStepIndicators();
        this.showStepContent(step);

        console.log(`[StrategyManager] Navigated to step ${step}`);
    }

    /**
     * Update step indicator visual state
     */
    updateStepIndicators() {
        for (let i = 1; i <= 3; i++) {
            const indicator = document.getElementById(`step-indicator-${i}`);
            if (!indicator) continue;

            indicator.classList.remove('active', 'completed');

            if (i < this.currentStep) {
                indicator.classList.add('completed');
            } else if (i === this.currentStep) {
                indicator.classList.add('active');
            }
        }
    }

    /**
     * Show content for specific step
     * @param {number} step - Step number
     */
    showStepContent(step) {
        // Hide all step content
        for (let i = 1; i <= 3; i++) {
            const content = document.getElementById(`step${i}-content`);
            if (content) {
                content.style.display = i === step ? 'block' : 'none';
            }
        }

        // Special actions when entering specific steps
        if (step === 2 && this.selectedTemplate) {
            this.displayTemplateInfo();
        } else if (step === 3) {
            this.generateParameterForm();
        }
    }

    /**
     * Display selected template information in Step 2
     */
    displayTemplateInfo() {
        const infoCard = document.getElementById('selected-template-info');
        const nameEl = document.getElementById('info-template-name');
        const badgeEl = document.getElementById('info-strategy-badge');

        if (!infoCard || !nameEl || !badgeEl || !this.selectedTemplate) {
            return;
        }

        const strategyNames = {
            'VSS': '可变限速',
            'DHS': '动态硬路肩',
            'TEC': '收费站管控'
        };

        nameEl.textContent = this.selectedTemplate.template_name;
        badgeEl.textContent = strategyNames[this.selectedTemplate.strategy_type];
        badgeEl.className = `strategy-badge badge-${this.selectedTemplate.strategy_type}`;
        infoCard.style.display = 'block';
    }

    // ==================== T047: Dynamic Form Generator ====================

    /**
     * Generate parameter form based on template schema
     * Dynamically creates HTML inputs based on parameter types
     */
    generateParameterForm() {
        if (!this.selectedTemplate) {
            console.error('[StrategyManager] Cannot generate form: No template selected');
            return;
        }

        const form = document.getElementById('params-form');
        if (!form) {
            console.error('[StrategyManager] Form container not found');
            return;
        }

        form.innerHTML = '';

        // Strategy name field (required)
        this.addFormField(form, {
            name: 'strategy_name',
            label: '策略名称',
            type: 'string',
            required: true,
            description: '为该策略实例命名',
            maxLength: 100
        });

        // Generate fields from template parameters_schema
        const schema = this.selectedTemplate.parameters_schema || [];
        schema.forEach(param => {
            // Skip affected_edges - it's handled separately in Step 2
            if (param.parameter_name === 'affected_edges') {
                return;
            }

            this.addFormField(form, {
                name: param.parameter_name,
                label: param.description || param.parameter_name,
                type: param.parameter_type,
                required: param.required,
                min: param.min_value,
                max: param.max_value,
                defaultValue: param.default_value,
                unit: param.unit,
                pattern: param.pattern,
                minItems: param.min_items,
                allowedValues: param.allowed_values
            });
        });

        console.log(`[StrategyManager] Generated form with ${schema.length + 1} fields`);
    }

    /**
     * Add a single form field to the form container
     * @param {HTMLElement} form - Form container element
     * @param {Object} field - Field configuration
     */
    addFormField(form, field) {
        const formGroup = document.createElement('div');
        formGroup.className = 'form-group';
        formGroup.id = `form-group-${field.name}`;

        const label = document.createElement('label');
        label.htmlFor = `param-${field.name}`;
        label.textContent = `${field.label} ${field.required ? '*' : ''}`;

        const input = this.createInputElement(field);
        input.id = `param-${field.name}`;
        input.name = field.name;

        // Attach validation listener (T048)
        input.addEventListener('blur', () => this.validateField(field.name));
        input.addEventListener('input', () => this.clearFieldError(field.name));

        const hint = document.createElement('span');
        hint.className = 'form-hint';
        hint.textContent = this.getFieldHint(field);

        const error = document.createElement('span');
        error.className = 'field-error';
        error.id = `error-${field.name}`;
        error.style.display = 'none';
        error.style.color = '#e74c3c';
        error.style.fontSize = '0.85rem';
        error.style.marginTop = '5px';

        formGroup.appendChild(label);
        formGroup.appendChild(input);
        formGroup.appendChild(hint);
        formGroup.appendChild(error);

        form.appendChild(formGroup);
    }

    /**
     * Create appropriate input element based on field type
     * @param {Object} field - Field configuration
     * @returns {HTMLElement} Input element
     */
    createInputElement(field) {
        let input;

        switch (field.type) {
            case 'integer':
            case 'float':
                input = document.createElement('input');
                input.type = 'number';
                input.step = field.type === 'float' ? '0.01' : '1';
                if (field.min !== null && field.min !== undefined) input.min = field.min;
                if (field.max !== null && field.max !== undefined) input.max = field.max;
                if (field.defaultValue !== null) input.value = field.defaultValue;
                break;

            case 'string':
                input = document.createElement('input');
                input.type = 'text';
                if (field.maxLength) input.maxLength = field.maxLength;
                if (field.pattern) input.pattern = field.pattern;
                if (field.defaultValue) input.value = field.defaultValue;
                break;

            case 'boolean':
                input = document.createElement('select');
                input.innerHTML = `
                    <option value="true">是</option>
                    <option value="false" selected>否</option>
                `;
                if (field.defaultValue !== null) {
                    input.value = field.defaultValue.toString();
                }
                break;

            case 'array':
                input = document.createElement('textarea');
                input.rows = 4;
                input.className = 'array-input';

                // Provide better placeholder based on default value format
                if (field.defaultValue && Array.isArray(field.defaultValue) && field.defaultValue.length > 0) {
                    // Check if it's nested array (like time_intervals [[7,9], [17,19]])
                    if (Array.isArray(field.defaultValue[0])) {
                        input.placeholder = '输入嵌套数组，格式如: [[7,9], [17,19]]，每行一个，或输入JSON格式';
                        input.value = JSON.stringify(field.defaultValue, null, 2);
                    } else {
                        input.placeholder = '输入多个值，每行一个，或用逗号分隔';
                        input.value = field.defaultValue.join('\n');
                    }
                } else {
                    input.placeholder = '输入多个值，每行一个，或用逗号分隔';
                }
                break;

            case 'enum':
                input = document.createElement('select');
                if (field.allowedValues) {
                    field.allowedValues.forEach(value => {
                        const option = document.createElement('option');
                        option.value = value;
                        option.textContent = value;
                        input.appendChild(option);
                    });
                }
                if (field.defaultValue) input.value = field.defaultValue;
                break;

            default:
                input = document.createElement('input');
                input.type = 'text';
        }

        if (field.required) {
            input.required = true;
        }

        return input;
    }

    /**
     * Get hint text for a field
     * @param {Object} field - Field configuration
     * @returns {string} Hint text
     */
    getFieldHint(field) {
        const parts = [];

        if (field.type === 'array') {
            if (field.defaultValue && Array.isArray(field.defaultValue[0])) {
                parts.push('支持JSON格式的嵌套数组');
            } else {
                parts.push('每行一个值，或用逗号分隔');
            }
        }

        if (field.unit) parts.push(`单位: ${field.unit}`);
        if (field.min !== null && field.max !== null) {
            parts.push(`范围: ${field.min}-${field.max}`);
        }
        if (field.minItems) {
            parts.push(`至少需要 ${field.minItems} 个项目`);
        }

        return parts.join(' | ');
    }

    // ==================== T048: Frontend Validation ====================

    /**
     * Validate a single form field
     * @param {string} fieldName - Field name
     * @returns {boolean} True if valid
     */
    validateField(fieldName) {
        const input = document.getElementById(`param-${fieldName}`);
        if (!input) return true;

        const value = input.value.trim();
        const field = this.getFieldConfig(fieldName);

        // Clear previous error
        this.clearFieldError(fieldName);

        // Required validation
        if (field.required && !value) {
            this.showFieldError(fieldName, '此字段为必填项');
            return false;
        }

        // Type-specific validation
        if (field.type === 'integer' || field.type === 'float') {
            const numValue = parseFloat(value);

            if (isNaN(numValue)) {
                this.showFieldError(fieldName, '请输入有效数字');
                return false;
            }

            if (field.min !== null && numValue < field.min) {
                this.showFieldError(fieldName, `值不能小于 ${field.min}`);
                return false;
            }

            if (field.max !== null && numValue > field.max) {
                this.showFieldError(fieldName, `值不能大于 ${field.max}`);
                return false;
            }
        }

        // String validation
        if (field.type === 'string') {
            if (field.maxLength && value.length > field.maxLength) {
                this.showFieldError(fieldName, `长度不能超过 ${field.maxLength} 个字符`);
                return false;
            }

            if (field.pattern) {
                const regex = new RegExp(field.pattern);
                if (!regex.test(value)) {
                    this.showFieldError(fieldName, '格式不正确');
                    return false;
                }
            }
        }

        // Array validation
        if (field.type === 'array' && value) {
            try {
                let items;
                const trimmed = value.trim();

                // Try JSON parsing first
                if (trimmed.startsWith('[')) {
                    const parsed = JSON.parse(trimmed);
                    if (!Array.isArray(parsed)) {
                        this.showFieldError(fieldName, 'JSON格式不正确，需要是数组');
                        return false;
                    }
                    items = parsed;
                } else {
                    // Simple array parsing
                    items = value.split(/[,\n]/).map(s => s.trim()).filter(s => s);
                }

                if (field.minItems && items.length < field.minItems) {
                    this.showFieldError(fieldName, `至少需要 ${field.minItems} 个项目`);
                    return false;
                }
            } catch (e) {
                this.showFieldError(fieldName, 'JSON格式不正确: ' + e.message);
                return false;
            }
        }

        return true;
    }

    /**
     * Validate all form fields
     * @returns {boolean} True if all fields are valid
     */
    validateAllFields() {
        const form = document.getElementById('params-form');
        if (!form) return false;

        let isValid = true;
        const inputs = form.querySelectorAll('input, select, textarea');

        inputs.forEach(input => {
            const fieldName = input.name;
            if (fieldName && !this.validateField(fieldName)) {
                isValid = false;
            }
        });

        return isValid;
    }

    /**
     * Show validation error for a field
     * @param {string} fieldName - Field name
     * @param {string} message - Error message
     */
    showFieldError(fieldName, message) {
        const errorEl = document.getElementById(`error-${fieldName}`);
        const inputEl = document.getElementById(`param-${fieldName}`);

        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
        }

        if (inputEl) {
            inputEl.style.borderColor = '#e74c3c';
        }

        this.validationErrors[fieldName] = message;
    }

    /**
     * Clear validation error for a field
     * @param {string} fieldName - Field name
     */
    clearFieldError(fieldName) {
        const errorEl = document.getElementById(`error-${fieldName}`);
        const inputEl = document.getElementById(`param-${fieldName}`);

        if (errorEl) {
            errorEl.style.display = 'none';
        }

        if (inputEl) {
            inputEl.style.borderColor = '#ddd';
        }

        delete this.validationErrors[fieldName];
    }

    /**
     * Get field configuration
     * @param {string} fieldName - Field name
     * @returns {Object} Field configuration
     */
    getFieldConfig(fieldName) {
        if (fieldName === 'strategy_name') {
            return {
                name: 'strategy_name',
                type: 'string',
                required: true,
                maxLength: 100
            };
        }

        if (!this.selectedTemplate || !this.selectedTemplate.parameters_schema) {
            return {};
        }

        const param = this.selectedTemplate.parameters_schema.find(
            p => p.parameter_name === fieldName
        );

        if (!param) {
            return {};
        }

        // Convert to field config format
        return {
            name: param.parameter_name,
            type: param.parameter_type,
            label: param.description || param.parameter_name,
            required: param.required,
            min: param.min_value,
            max: param.max_value,
            defaultValue: param.default_value,
            unit: param.unit,
            pattern: param.pattern,
            minItems: param.min_items,
            allowedValues: param.allowed_values
        };
    }

    // ==================== T049: Integration with Phase 1B Edge Selector ====================

    /**
     * Handle edge selection from Phase 1B edge selector
     * This integrates with the existing edge selector embedded in templates.html
     *
     * @param {Array<string>} edgeIds - Selected edge IDs
     */
    onEdgesSelected(edgeIds) {
        this.selectedEdges = edgeIds;
        console.log(`[StrategyManager] ${edgeIds.length} edges selected:`, edgeIds);

        // Update UI to reflect selection
        this.updateEdgeSelectionDisplay();
    }

    /**
     * Update the display showing selected edges count
     */
    updateEdgeSelectionDisplay() {
        const countEl = document.getElementById('selected-count');
        if (countEl) {
            countEl.textContent = this.selectedEdges.length;
        }

        // Enable/disable next button based on edge selection
        const nextBtn = document.getElementById('step2-next');
        if (nextBtn) {
            nextBtn.disabled = this.selectedEdges.length === 0;
        }
    }

    /**
     * Get selected edges from global state (integration point)
     * This hooks into the global selectedEdges variable from edge_selector_embedded.js
     * @returns {Array<string>} Array of edge IDs
     */
    getSelectedEdgesFromSelector() {
        // Integration with Phase 1B edge selector
        if (typeof window.selectedEdges !== 'undefined') {
            return window.selectedEdges;
        }
        return this.selectedEdges;
    }

    // ==================== T050: Save Strategy API Call ====================

    /**
     * Save strategy instance via API
     * POST /api/v1/control/strategy-instances
     *
     * @returns {Promise<Object>} API response with strategy_id
     */
    async saveStrategy() {
        console.log('[StrategyManager] Starting strategy save...');

        // Step 1: Validate all fields
        if (!this.validateAllFields()) {
            this.showMessage('请修正表单中的错误', 'error');
            return null;
        }

        // Step 2: Collect form data
        const formData = this.collectFormData();

        // Step 3: Validate template selection
        if (!this.selectedTemplate) {
            this.showMessage('请先选择策略模板', 'error');
            return null;
        }

        // Step 4: Validate edge selection (at least 1 edge required)
        const edges = this.getSelectedEdgesFromSelector();
        if (!edges || edges.length === 0) {
            this.showMessage('请至少选择一个管控路段', 'error');
            return null;
        }

        // Step 5: Build API request payload
        const payload = {
            strategy_name: formData.strategy_name,
            template_id: this.selectedTemplate.template_id,
            parameters: formData.parameters,
            affected_edges: edges
        };

        console.log('[StrategyManager] Request payload:', payload);

        try {
            // Step 6: Call API
            const response = await fetch(this.API_BASE + '/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            // Step 7: Handle response
            if (!response.ok) {
                const errorData = await response.json();
                console.error('[StrategyManager] API error:', errorData);

                if (response.status === 400) {
                    this.showMessage(`验证失败: ${errorData.detail || '参数不符合要求'}`, 'error');
                } else if (response.status === 404) {
                    this.showMessage('模板未找到，请重新选择', 'error');
                } else {
                    this.showMessage(`创建失败 (${response.status})`, 'error');
                }

                return null;
            }

            const result = await response.json();
            console.log('[StrategyManager] Strategy created:', result);

            // Step 8: Show success message
            this.showMessage(`策略创建成功！ID: ${result.strategy_id}`, 'success');

            // Step 9: Reset form
            this.resetForm();

            return result;

        } catch (error) {
            console.error('[StrategyManager] Network error:', error);
            this.showMessage('网络错误，请检查连接后重试', 'error');
            return null;
        }
    }

    /**
     * Collect all form data
     * @returns {Object} Collected form data
     */
    collectFormData() {
        const form = document.getElementById('params-form');
        if (!form) return {};

        const data = {
            strategy_name: '',
            parameters: {}
        };

        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            const fieldName = input.name;
            const value = input.value.trim();

            if (fieldName === 'strategy_name') {
                data.strategy_name = value;
            } else if (fieldName) {
                // Handle type conversion
                const field = this.getFieldConfig(fieldName);

                if (field.type === 'integer') {
                    data.parameters[fieldName] = parseInt(value);
                } else if (field.type === 'float') {
                    data.parameters[fieldName] = parseFloat(value);
                } else if (field.type === 'boolean') {
                    data.parameters[fieldName] = value === 'true';
                } else if (field.type === 'array') {
                    // Try to parse as JSON first (for nested arrays)
                    try {
                        const trimmed = value.trim();
                        if (trimmed.startsWith('[')) {
                            // Looks like JSON array
                            data.parameters[fieldName] = JSON.parse(trimmed);
                        } else {
                            // Parse as simple array (newline or comma separated)
                            data.parameters[fieldName] = value
                                .split(/[,\n]/)
                                .map(s => s.trim())
                                .filter(s => s);
                        }
                    } catch (e) {
                        // Fallback to simple array parsing
                        data.parameters[fieldName] = value
                            .split(/[,\n]/)
                            .map(s => s.trim())
                            .filter(s => s);
                    }
                } else {
                    data.parameters[fieldName] = value;
                }
            }
        });

        return data;
    }

    /**
     * Show user message (success/error notification)
     * @param {string} message - Message to display
     * @param {string} type - Message type ('success' or 'error')
     */
    showMessage(message, type = 'info') {
        // Create message element if it doesn't exist
        let messageEl = document.getElementById('strategy-message');

        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'strategy-message';
            messageEl.style.position = 'fixed';
            messageEl.style.top = '20px';
            messageEl.style.right = '20px';
            messageEl.style.padding = '15px 25px';
            messageEl.style.borderRadius = '4px';
            messageEl.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
            messageEl.style.zIndex = '9999';
            messageEl.style.maxWidth = '400px';
            messageEl.style.transition = 'opacity 0.3s';
            document.body.appendChild(messageEl);
        }

        // Set message and style based on type
        messageEl.textContent = message;

        if (type === 'success') {
            messageEl.style.background = '#2ecc71';
            messageEl.style.color = 'white';
        } else if (type === 'error') {
            messageEl.style.background = '#e74c3c';
            messageEl.style.color = 'white';
        } else {
            messageEl.style.background = '#3498db';
            messageEl.style.color = 'white';
        }

        messageEl.style.display = 'block';
        messageEl.style.opacity = '1';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            messageEl.style.opacity = '0';
            setTimeout(() => {
                messageEl.style.display = 'none';
            }, 300);
        }, 5000);
    }

    /**
     * Reset the form to initial state
     */
    resetForm() {
        this.currentStep = 1;
        this.selectedTemplate = null;
        this.selectedEdges = [];
        this.formData = {};
        this.validationErrors = {};
        this.editingStrategy = null;

        this.goToStep(1);

        // Clear template selection
        document.querySelectorAll('.template-card').forEach(card => {
            card.classList.remove('selected');
        });

        // Clear form
        const form = document.getElementById('params-form');
        if (form) {
            form.innerHTML = '';
        }

        console.log('[StrategyManager] Form reset');
    }

    // ==================== T085: Edit Strategy ====================

    /**
     * Load strategy for editing
     * GET /api/v1/control/strategy-instances/{strategy_id}
     *
     * @param {string} strategyId - Strategy ID to edit
     * @returns {Promise<boolean>} True if loaded successfully
     */
    async editStrategy(strategyId) {
        console.log(`[StrategyManager] Loading strategy for editing: ${strategyId}`);

        try {
            // Step 1: Fetch strategy details from API
            const response = await fetch(`${this.API_BASE}/${strategyId}`);

            if (!response.ok) {
                if (response.status === 404) {
                    this.showMessage('策略未找到', 'error');
                } else {
                    this.showMessage(`加载策略失败 (${response.status})`, 'error');
                }
                return false;
            }

            const strategy = await response.json();
            console.log('[StrategyManager] Strategy loaded:', strategy);

            // Step 2: Store editing state
            this.editingStrategy = {
                strategy_id: strategy.strategy_id,
                original_updated_at: strategy.metadata.updated_at,
                original_data: strategy
            };

            // Step 3: Load template for schema
            await this.loadTemplateById(strategy.template_id);

            if (!this.selectedTemplate) {
                this.showMessage('无法加载策略模板', 'error');
                return false;
            }

            // Step 4: Extract edges from affected_edges array
            this.selectedEdges = strategy.affected_edges.map(edge => edge.edge_id);

            // Step 5: Show edit modal/form
            this.showEditModal(strategy);

            // Step 6: Populate form with existing values
            this.populateEditForm(strategy);

            return true;

        } catch (error) {
            console.error('[StrategyManager] Error loading strategy:', error);
            this.showMessage('网络错误，请检查连接后重试', 'error');
            return false;
        }
    }

    /**
     * Load template by ID
     * @param {string} templateId - Template ID
     * @returns {Promise<boolean>} True if loaded successfully
     */
    async loadTemplateById(templateId) {
        try {
            const response = await fetch(`/api/v1/control/templates/${templateId}`);

            if (!response.ok) {
                console.error(`[StrategyManager] Template not found: ${templateId}`);
                return false;
            }

            this.selectedTemplate = await response.json();
            console.log('[StrategyManager] Template loaded for editing');
            return true;

        } catch (error) {
            console.error('[StrategyManager] Error loading template:', error);
            return false;
        }
    }

    /**
     * Show edit modal with strategy data
     * @param {Object} strategy - Strategy data
     */
    showEditModal(strategy) {
        // Create or show edit modal
        let modal = document.getElementById('edit-strategy-modal');

        if (!modal) {
            modal = this.createEditModal();
            document.body.appendChild(modal);
        }

        // Set modal title
        const titleEl = modal.querySelector('#edit-modal-title');
        if (titleEl) {
            titleEl.textContent = `编辑策略: ${strategy.strategy_name}`;
        }

        // Generate form
        this.generateEditForm();

        // Show modal
        modal.style.display = 'block';
    }

    /**
     * Create edit modal HTML structure
     * @returns {HTMLElement} Modal element
     */
    createEditModal() {
        const modal = document.createElement('div');
        modal.id = 'edit-strategy-modal';
        modal.className = 'modal';
        modal.style.display = 'none';
        modal.style.position = 'fixed';
        modal.style.zIndex = '10000';
        modal.style.left = '0';
        modal.style.top = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.overflow = 'auto';
        modal.style.backgroundColor = 'rgba(0,0,0,0.4)';

        modal.innerHTML = `
            <div class="modal-content" style="background-color: #fefefe; margin: 5% auto; padding: 30px; border: 1px solid #888; width: 80%; max-width: 800px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee;">
                    <h2 id="edit-modal-title" style="margin: 0; color: #2c3e50;">编辑策略</h2>
                    <span class="close" id="edit-modal-close" style="color: #aaa; font-size: 28px; font-weight: bold; cursor: pointer;">&times;</span>
                </div>
                <div class="modal-body">
                    <form id="edit-params-form"></form>
                </div>
                <div class="modal-footer" style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 25px; padding-top: 15px; border-top: 1px solid #eee;">
                    <button type="button" id="edit-cancel-btn" class="btn btn-secondary" style="padding: 10px 20px; border: 1px solid #ccc; background: #f8f9fa; color: #333; border-radius: 4px; cursor: pointer;">取消</button>
                    <button type="button" id="edit-save-btn" class="btn btn-primary" style="padding: 10px 20px; border: none; background: #3498db; color: white; border-radius: 4px; cursor: pointer;">保存更改</button>
                </div>
            </div>
        `;

        // Attach event listeners
        const closeBtn = modal.querySelector('#edit-modal-close');
        const cancelBtn = modal.querySelector('#edit-cancel-btn');
        const saveBtn = modal.querySelector('#edit-save-btn');

        closeBtn.onclick = () => this.closeEditModal();
        cancelBtn.onclick = () => this.cancelEdit();
        saveBtn.onclick = () => this.saveStrategyUpdate();

        // Close when clicking outside modal
        modal.onclick = (event) => {
            if (event.target === modal) {
                this.closeEditModal();
            }
        };

        return modal;
    }

    /**
     * Generate edit form with current strategy values
     */
    generateEditForm() {
        if (!this.selectedTemplate || !this.editingStrategy) {
            console.error('[StrategyManager] Cannot generate edit form: Missing template or strategy');
            return;
        }

        const form = document.getElementById('edit-params-form');
        if (!form) {
            console.error('[StrategyManager] Edit form container not found');
            return;
        }

        form.innerHTML = '';

        // Strategy name field (required)
        this.addFormField(form, {
            name: 'strategy_name',
            label: '策略名称',
            type: 'string',
            required: true,
            description: '策略实例名称',
            maxLength: 100
        });

        // Generate fields from template parameters_schema
        const schema = this.selectedTemplate.parameters_schema || [];
        schema.forEach(param => {
            if (param.parameter_name === 'affected_edges') {
                return;
            }

            this.addFormField(form, {
                name: param.parameter_name,
                label: param.description || param.parameter_name,
                type: param.parameter_type,
                required: param.required,
                min: param.min_value,
                max: param.max_value,
                defaultValue: param.default_value,
                unit: param.unit,
                pattern: param.pattern,
                minItems: param.min_items,
                allowedValues: param.allowed_values
            });
        });

        // Add edges display (read-only for now)
        const edgesGroup = document.createElement('div');
        edgesGroup.className = 'form-group';
        edgesGroup.innerHTML = `
            <label>受影响路段</label>
            <div style="padding: 10px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; margin-top: 5px;">
                <p style="margin: 0; color: #6c757d;">已选择 <strong>${this.selectedEdges.length}</strong> 个路段</p>
                <p style="margin: 5px 0 0 0; font-size: 0.85rem; color: #6c757d;">注意：当前版本不支持修改路段选择</p>
            </div>
        `;
        form.appendChild(edgesGroup);

        console.log(`[StrategyManager] Generated edit form`);
    }

    /**
     * Populate edit form with existing strategy values
     * @param {Object} strategy - Strategy data
     */
    populateEditForm(strategy) {
        // Populate strategy name
        const nameInput = document.getElementById('param-strategy_name');
        if (nameInput) {
            nameInput.value = strategy.strategy_name;
        }

        // Populate parameters
        const parameters = strategy.parameters || {};
        Object.keys(parameters).forEach(paramName => {
            const input = document.getElementById(`param-${paramName}`);
            if (!input) return;

            const value = parameters[paramName];
            const field = this.getFieldConfig(paramName);

            // Set value based on type
            if (field.type === 'boolean') {
                input.value = value.toString();
            } else if (field.type === 'array') {
                if (Array.isArray(value)) {
                    if (value.length > 0 && Array.isArray(value[0])) {
                        // Nested array - use JSON format
                        input.value = JSON.stringify(value, null, 2);
                    } else {
                        // Simple array - newline separated
                        input.value = value.join('\n');
                    }
                }
            } else {
                input.value = value;
            }
        });

        console.log('[StrategyManager] Form populated with existing values');
    }

    // ==================== T086: Save Strategy Update ====================

    /**
     * Save strategy updates via API
     * PUT /api/v1/control/strategy-instances/{strategy_id}
     *
     * @returns {Promise<Object>} API response
     */
    async saveStrategyUpdate() {
        console.log('[StrategyManager] Saving strategy updates...');

        if (!this.editingStrategy) {
            this.showMessage('编辑状态错误', 'error');
            return null;
        }

        // Step 1: Validate all fields
        const form = document.getElementById('edit-params-form');
        if (!form) {
            this.showMessage('表单未找到', 'error');
            return null;
        }

        // Validate using existing validation logic
        let isValid = true;
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.name && !this.validateField(input.name)) {
                isValid = false;
            }
        });

        if (!isValid) {
            this.showMessage('请修正表单中的错误', 'error');
            return null;
        }

        // Step 2: Collect form data
        const formData = this.collectFormData();

        // Step 3: Build API request payload
        const payload = {
            strategy_name: formData.strategy_name,
            parameters: formData.parameters,
            affected_edges: this.selectedEdges,
            original_updated_at: this.editingStrategy.original_updated_at
        };

        console.log('[StrategyManager] Update payload:', payload);

        try {
            // Step 4: Call PUT API
            const response = await fetch(
                `${this.API_BASE}/${this.editingStrategy.strategy_id}`,
                {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                }
            );

            // Step 5: Handle response
            if (!response.ok) {
                const errorData = await response.json();
                console.error('[StrategyManager] Update error:', errorData);

                if (response.status === 409) {
                    // Concurrency conflict (T087)
                    this.handleConcurrencyConflict(errorData);
                    return null;
                } else if (response.status === 400) {
                    this.showMessage(`验证失败: ${errorData.detail}`, 'error');
                } else if (response.status === 404) {
                    this.showMessage('策略未找到', 'error');
                } else {
                    this.showMessage(`更新失败 (${response.status})`, 'error');
                }

                return null;
            }

            const result = await response.json();
            console.log('[StrategyManager] Strategy updated:', result);

            // Step 6: Show success message
            this.showMessage('策略更新成功！', 'success');

            // Step 7: Close modal and refresh list
            this.closeEditModal();

            // Step 8: Optionally refresh strategy list if visible
            // (This would require list management to be implemented)

            return result;

        } catch (error) {
            console.error('[StrategyManager] Network error:', error);
            this.showMessage('网络错误，请检查连接后重试', 'error');
            return null;
        }
    }

    // ==================== T087: Concurrency Conflict Handling ====================

    /**
     * Handle concurrency conflict (409 response)
     * @param {Object} errorData - Error response data
     */
    handleConcurrencyConflict(errorData) {
        console.warn('[StrategyManager] Concurrency conflict detected');

        // Show conflict warning modal
        const message = `
            策略已被其他用户修改。

            ${errorData.detail || '请刷新后重试。'}

            建议：关闭编辑窗口，刷新策略列表，重新编辑。
        `;

        // Create conflict modal
        const modal = document.createElement('div');
        modal.className = 'conflict-modal';
        modal.style.position = 'fixed';
        modal.style.zIndex = '10001';
        modal.style.left = '0';
        modal.style.top = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.backgroundColor = 'rgba(0,0,0,0.5)';

        modal.innerHTML = `
            <div style="background: white; margin: 10% auto; padding: 30px; width: 80%; max-width: 500px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <span style="font-size: 48px; color: #f39c12; margin-right: 15px;">⚠️</span>
                    <h2 style="margin: 0; color: #2c3e50;">并发冲突</h2>
                </div>
                <div style="white-space: pre-line; margin-bottom: 25px; color: #555; line-height: 1.6;">
                    ${message}
                </div>
                <div style="display: flex; justify-content: flex-end; gap: 10px;">
                    <button id="conflict-close-btn" style="padding: 10px 20px; border: none; background: #3498db; color: white; border-radius: 4px; cursor: pointer; font-size: 14px;">
                        确定
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close button handler
        const closeBtn = modal.querySelector('#conflict-close-btn');
        closeBtn.onclick = () => {
            document.body.removeChild(modal);
            this.closeEditModal();
        };

        // Click outside to close
        modal.onclick = (event) => {
            if (event.target === modal) {
                document.body.removeChild(modal);
                this.closeEditModal();
            }
        };
    }

    // ==================== T088: Cancel Edit ====================

    /**
     * Cancel edit operation and discard changes
     */
    cancelEdit() {
        console.log('[StrategyManager] Edit cancelled by user');

        // Ask for confirmation if form has changes
        const confirmed = confirm('确定要取消编辑吗？未保存的更改将丢失。');

        if (confirmed) {
            this.closeEditModal();
            this.showMessage('已取消编辑', 'info');
        }
    }

    /**
     * Close edit modal
     */
    closeEditModal() {
        const modal = document.getElementById('edit-strategy-modal');
        if (modal) {
            modal.style.display = 'none';
        }

        // Clear editing state
        this.editingStrategy = null;

        console.log('[StrategyManager] Edit modal closed');
    }

    // ==================== T097: Delete Strategy ====================

    /**
     * Delete a strategy with confirmation
     * DELETE /api/v1/control/strategy-instances/{strategy_id}
     *
     * @param {string} strategyId - Strategy ID to delete
     * @param {string} strategyName - Strategy name for confirmation message
     * @returns {Promise<boolean>} True if deleted successfully
     */
    async deleteStrategy(strategyId, strategyName) {
        console.log(`[StrategyManager] Delete requested for strategy: ${strategyId}`);

        // Step 1: Show confirmation dialog (T098)
        const confirmed = await this.showDeleteConfirmation(strategyId, strategyName);

        if (!confirmed) {
            console.log('[StrategyManager] Delete cancelled by user');
            return false;
        }

        try {
            // Step 2: Call DELETE API
            console.log(`[StrategyManager] Calling DELETE for ${strategyId}...`);
            const response = await fetch(
                `${this.API_BASE}/${strategyId}`,
                {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }
            );

            // Step 3: Handle response
            if (!response.ok) {
                const errorData = await response.json();
                console.error('[StrategyManager] Delete error:', errorData);

                if (response.status === 404) {
                    this.showMessage('策略未找到', 'error');
                } else if (response.status === 409) {
                    // Strategy is used in plans (Phase 2)
                    this.showMessage(
                        `无法删除：${errorData.detail || '该策略正在被使用'}`,
                        'error'
                    );
                } else {
                    this.showMessage(
                        `删除失败 (${response.status}): ${errorData.detail || '请检查后重试'}`,
                        'error'
                    );
                }

                return false;
            }

            // Step 4: Handle success
            const result = await response.json();
            console.log('[StrategyManager] Strategy deleted:', result);

            // Step 5: Show success message
            this.showMessage(`策略 "${strategyName}" 已删除`, 'success');

            // Step 6: Refresh strategy list if visible
            // (This would require list management to be implemented)
            // For now, we can dispatch a custom event for list refresh
            window.dispatchEvent(new Event('strategyDeleted'));

            return true;

        } catch (error) {
            console.error('[StrategyManager] Network error:', error);
            this.showMessage('网络错误，请检查连接后重试', 'error');
            return false;
        }
    }

    // ==================== T098: Delete Confirmation Dialog ====================

    /**
     * Show delete confirmation dialog
     * @param {string} strategyId - Strategy ID
     * @param {string} strategyName - Strategy name
     * @returns {Promise<boolean>} True if user confirmed deletion
     */
    async showDeleteConfirmation(strategyId, strategyName) {
        return new Promise((resolve) => {
            // Create confirmation modal (T099 - styled)
            const modal = document.createElement('div');
            modal.id = 'delete-confirmation-modal';
            modal.className = 'delete-confirmation-modal';
            modal.style.position = 'fixed';
            modal.style.zIndex = '10000';
            modal.style.left = '0';
            modal.style.top = '0';
            modal.style.width = '100%';
            modal.style.height = '100%';
            modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
            modal.style.display = 'flex';
            modal.style.alignItems = 'center';
            modal.style.justifyContent = 'center';

            const content = document.createElement('div');
            content.className = 'delete-confirmation-content';
            content.style.backgroundColor = 'white';
            content.style.padding = '30px';
            content.style.borderRadius = '8px';
            content.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
            content.style.width = '90%';
            content.style.maxWidth = '400px';
            content.style.textAlign = 'center';

            // Icon and title
            const header = document.createElement('div');
            header.style.marginBottom = '20px';

            const icon = document.createElement('div');
            icon.style.fontSize = '48px';
            icon.style.marginBottom = '10px';
            icon.textContent = '⚠️';

            const title = document.createElement('h2');
            title.style.margin = '0';
            title.style.color = '#e74c3c';
            title.style.fontSize = '20px';
            title.textContent = '确认删除策略';

            header.appendChild(icon);
            header.appendChild(title);

            // Message
            const message = document.createElement('div');
            message.style.marginBottom = '25px';
            message.style.color = '#555';
            message.style.lineHeight = '1.6';

            const messageText = document.createElement('p');
            messageText.style.margin = '0 0 10px 0';
            messageText.textContent = `确定要删除策略 "${strategyName}" 吗？`;

            const warningText = document.createElement('p');
            warningText.style.margin = '10px 0';
            warningText.style.fontSize = '13px';
            warningText.style.color = '#e74c3c';
            warningText.textContent = '此操作无法撤销。';

            message.appendChild(messageText);
            message.appendChild(warningText);

            // Buttons
            const buttonContainer = document.createElement('div');
            buttonContainer.style.display = 'flex';
            buttonContainer.style.justifyContent = 'center';
            buttonContainer.style.gap = '10px';

            const cancelBtn = document.createElement('button');
            cancelBtn.id = 'delete-cancel-btn';
            cancelBtn.className = 'btn btn-secondary';
            cancelBtn.textContent = '取消';
            cancelBtn.style.padding = '10px 25px';
            cancelBtn.style.border = '1px solid #ccc';
            cancelBtn.style.background = '#f8f9fa';
            cancelBtn.style.color = '#333';
            cancelBtn.style.borderRadius = '4px';
            cancelBtn.style.cursor = 'pointer';
            cancelBtn.style.fontSize = '14px';
            cancelBtn.style.fontWeight = '500';
            cancelBtn.style.transition = 'all 0.2s';

            const deleteBtn = document.createElement('button');
            deleteBtn.id = 'delete-confirm-btn';
            deleteBtn.className = 'btn btn-danger';
            deleteBtn.textContent = '删除';
            deleteBtn.style.padding = '10px 25px';
            deleteBtn.style.border = 'none';
            deleteBtn.style.background = '#e74c3c';
            deleteBtn.style.color = 'white';
            deleteBtn.style.borderRadius = '4px';
            deleteBtn.style.cursor = 'pointer';
            deleteBtn.style.fontSize = '14px';
            deleteBtn.style.fontWeight = '500';
            deleteBtn.style.transition = 'all 0.2s';

            // Hover effects
            cancelBtn.addEventListener('mouseover', () => {
                cancelBtn.style.background = '#e8e9ea';
            });
            cancelBtn.addEventListener('mouseout', () => {
                cancelBtn.style.background = '#f8f9fa';
            });

            deleteBtn.addEventListener('mouseover', () => {
                deleteBtn.style.background = '#c0392b';
            });
            deleteBtn.addEventListener('mouseout', () => {
                deleteBtn.style.background = '#e74c3c';
            });

            buttonContainer.appendChild(cancelBtn);
            buttonContainer.appendChild(deleteBtn);

            // Assemble modal
            content.appendChild(header);
            content.appendChild(message);
            content.appendChild(buttonContainer);
            modal.appendChild(content);
            document.body.appendChild(modal);

            // Event handlers
            const cleanup = () => {
                document.body.removeChild(modal);
            };

            cancelBtn.onclick = () => {
                cleanup();
                resolve(false);
            };

            deleteBtn.onclick = () => {
                cleanup();
                resolve(true);
            };

            // Close on background click
            modal.onclick = (event) => {
                if (event.target === modal) {
                    cleanup();
                    resolve(false);
                }
            };

            // Close on Escape key
            const escapeHandler = (event) => {
                if (event.key === 'Escape') {
                    document.removeEventListener('keydown', escapeHandler);
                    cleanup();
                    resolve(false);
                }
            };
            document.addEventListener('keydown', escapeHandler);
        });
    }
}

// Export for global usage
window.StrategyManager = StrategyManager;

// Create global instance (optional, for convenience)
window.strategyManager = new StrategyManager();

console.log('[StrategyManager] Module loaded successfully');
