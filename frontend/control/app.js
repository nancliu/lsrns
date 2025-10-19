// Control Template Frontend Application

const API_BASE = '/api/v1/control';

// State
let templates = [];

// Initialize app on page load
document.addEventListener('DOMContentLoaded', () => {
    fetchTemplates();
    setupModalHandlers();
});

// Fetch templates from API
async function fetchTemplates() {
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('error');
    const containerEl = document.getElementById('templates-container');

    try {
        loadingEl.style.display = 'block';
        errorEl.style.display = 'none';
        containerEl.innerHTML = '';

        const response = await fetch(`${API_BASE}/templates/`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        templates = data.templates;

        // Update stats
        document.getElementById('total-count').textContent = data.total_count;
        document.getElementById('vss-count').textContent = data.by_type.VSS || 0;
        document.getElementById('dhs-count').textContent = data.by_type.DHS || 0;
        document.getElementById('tec-count').textContent = data.by_type.TEC || 0;

        // Render template cards
        renderTemplateCards(templates);

        loadingEl.style.display = 'none';

    } catch (error) {
        console.error('Error fetching templates:', error);
        loadingEl.style.display = 'none';
        errorEl.textContent = `加载失败: ${error.message}`;
        errorEl.style.display = 'block';
    }
}

// Render template cards
function renderTemplateCards(templates) {
    const container = document.getElementById('templates-container');

    if (templates.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #7f8c8d;">暂无模板</p>';
        return;
    }

    templates.forEach(template => {
        const card = createTemplateCard(template);
        container.appendChild(card);
    });
}

// Create a single template card element
function createTemplateCard(template) {
    const card = document.createElement('div');
    card.className = 'template-card';
    card.onclick = () => showTemplateDetail(template.template_id);

    const strategyType = template.strategy_type;
    const strategyNames = {
        'VSS': '可变限速',
        'DHS': '动态硬路肩',
        'TEC': '收费站管控'
    };

    card.innerHTML = `
        <div class="template-header">
            <div class="template-title">${template.template_name}</div>
            <span class="strategy-badge badge-${strategyType}">${strategyNames[strategyType]}</span>
        </div>
        <div class="template-description">${template.description}</div>
        <div class="template-meta">
            <span>参数: ${template.parameters_schema.length}</span>
            <span>版本: ${template.version}</span>
        </div>
    `;

    return card;
}

// Show template detail in modal
async function showTemplateDetail(templateId) {
    const modal = document.getElementById('template-modal');
    const modalBody = document.getElementById('modal-body');

    try {
        modalBody.innerHTML = '<p>加载中...</p>';
        modal.style.display = 'flex';

        const response = await fetch(`${API_BASE}/templates/${templateId}`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        renderTemplateDetail(data.template);

    } catch (error) {
        console.error('Error fetching template detail:', error);
        modalBody.innerHTML = `<p style="color: #e74c3c;">加载失败: ${error.message}</p>`;
    }
}

// Render template detail in modal
function renderTemplateDetail(template) {
    const modalBody = document.getElementById('modal-body');

    const strategyNames = {
        'VSS': '可变限速',
        'DHS': '动态硬路肩',
        'TEC': '收费站管控'
    };

    let html = `
        <h2 class="modal-title">${template.template_name}</h2>
        <p><strong>策略类型:</strong> ${strategyNames[template.strategy_type]}</p>
        <p><strong>模板ID:</strong> ${template.template_id}</p>
        <p><strong>版本:</strong> ${template.version}</p>
        <p class="modal-description">${template.description}</p>

        <h3 style="margin-top: 30px; color: #2c3e50;">参数配置</h3>
        <table class="parameters-table">
            <thead>
                <tr>
                    <th>参数名称</th>
                    <th>类型</th>
                    <th>说明</th>
                    <th>必填</th>
                    <th>默认值</th>
                    <th>范围/单位</th>
                </tr>
            </thead>
            <tbody>
    `;

    template.parameters_schema.forEach(param => {
        const requiredText = param.required 
            ? '<span class="param-required">是</span>' 
            : '<span class="param-optional">否</span>';

        const defaultValue = param.default_value !== null && param.default_value !== undefined
            ? JSON.stringify(param.default_value)
            : '-';

        let range = '';
        if (param.min_value !== null && param.max_value !== null) {
            range = `${param.min_value}-${param.max_value}`;
        }
        if (param.unit) {
            range += ` ${param.unit}`;
        }
        if (!range) range = '-';

        html += `
            <tr>
                <td><strong>${param.parameter_name}</strong></td>
                <td>${param.parameter_type}</td>
                <td>${param.description}</td>
                <td>${requiredText}</td>
                <td>${defaultValue}</td>
                <td>${range}</td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    modalBody.innerHTML = html;
}

// Setup modal handlers
function setupModalHandlers() {
    const modal = document.getElementById('template-modal');
    const closeBtn = document.querySelector('.close-btn');

    // Close on button click
    closeBtn.onclick = () => {
        modal.style.display = 'none';
    };

    // Close on background click
    modal.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };

    // Close on ESC key
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal.style.display === 'flex') {
            modal.style.display = 'none';
        }
    });
}
