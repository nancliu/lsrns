/**
 * Plan Management JavaScript
 * Handles plan CRUD operations and UI interactions
 */

const API_BASE = '/api/v1/control';
let allPlans = [];
let allStrategies = [];
let currentPlanId = null;
let selectedStrategyIds = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadPlans();
    setupFilters();
});

/**
 * Load all plans from API
 */
async function loadPlans() {
    try {
        const response = await fetch(`${API_BASE}/plans/`);
        if (!response.ok) throw new Error('Failed to load plans');

        const data = await response.json();
        allPlans = data.plans || [];

        renderPlans(allPlans);
    } catch (error) {
        console.error('Error loading plans:', error);
        showError('加载方案失败: ' + error.message);
    }
}

/**
 * Render plans grid
 */
function renderPlans(plans) {
    const container = document.getElementById('plansContainer');

    if (!plans || plans.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>暂无方案</h3>
                <p>点击"新建方案"开始创建您的第一个管控方案</p>
            </div>
        `;
        return;
    }

    const grid = document.createElement('div');
    grid.className = 'plans-grid';

    plans.forEach(plan => {
        const card = createPlanCard(plan);
        grid.appendChild(card);
    });

    container.innerHTML = '';
    container.appendChild(grid);
}

/**
 * Create plan card element
 */
function createPlanCard(plan) {
    const card = document.createElement('div');
    card.className = 'plan-card' + (plan.is_baseline ? ' baseline' : '');
    card.onclick = () => showPlanDetail(plan.plan_id);

    const tagsHtml = (plan.tags || []).map(tag =>
        `<span class="tag">${tag}</span>`
    ).join('');

    // Determine badge type and color
    let badgeHtml = '';
    if (plan.is_baseline) {
        badgeHtml = '<span class="plan-badge badge-baseline">基准</span>';
    } else if (plan.tags && plan.tags.some(tag => tag.toLowerCase().includes('测试'))) {
        badgeHtml = '<span class="plan-badge badge-test">测试</span>';
    } else if (plan.tags && plan.tags.some(tag => tag.toLowerCase().includes('优化'))) {
        badgeHtml = '<span class="plan-badge badge-optimization">优化</span>';
    }

    card.innerHTML = `
        <div class="plan-header">
            <div>
                <div class="plan-title">${escapeHtml(plan.plan_name)}</div>
                <div class="plan-meta">策略数: ${plan.strategy_count || 0}</div>
            </div>
            ${badgeHtml}
        </div>

        ${plan.description ? `<div class="plan-description">${escapeHtml(plan.description)}</div>` : ''}

        ${tagsHtml ? `<div class="plan-tags">${tagsHtml}</div>` : ''}

        <div class="plan-actions" onclick="event.stopPropagation()">
            <button class="btn btn-success" onclick="viewPlanDetail('${plan.plan_id}')">
                查看
            </button>
            ${!plan.is_baseline ? `
                <button class="btn btn-primary" onclick="editPlan('${plan.plan_id}')">
                    编辑
                </button>
                <button class="btn btn-danger" onclick="deletePlan('${plan.plan_id}')">
                    删除
                </button>
            ` : ''}
        </div>
    `;

    return card;
}

/**
 * Setup filter inputs
 */
function setupFilters() {
    const searchInput = document.getElementById('searchInput');
    const tagFilter = document.getElementById('tagFilter');
    const showBaseline = document.getElementById('showBaseline');

    const applyFilters = () => {
        const searchTerm = searchInput.value.toLowerCase();
        const tagTerm = tagFilter.value.toLowerCase();
        const includeBaseline = showBaseline.checked;

        const filtered = allPlans.filter(plan => {
            // Search filter
            if (searchTerm && !plan.plan_name.toLowerCase().includes(searchTerm)) {
                return false;
            }

            // Tag filter
            if (tagTerm) {
                const planTags = (plan.tags || []).map(t => t.toLowerCase());
                if (!planTags.some(t => t.includes(tagTerm))) {
                    return false;
                }
            }

            // Baseline filter
            if (!includeBaseline && plan.is_baseline) {
                return false;
            }

            return true;
        });

        renderPlans(filtered);
    };

    searchInput.addEventListener('input', applyFilters);
    tagFilter.addEventListener('input', applyFilters);
    showBaseline.addEventListener('change', applyFilters);
}

/**
 * Show create plan modal
 */
async function showCreatePlanModal() {
    currentPlanId = null;
    selectedStrategyIds = [];

    document.getElementById('modalTitle').textContent = '新建方案';
    document.getElementById('planForm').reset();
    document.getElementById('validationWarnings').innerHTML = '';

    // Load strategies
    await loadStrategies();

    document.getElementById('planModal').classList.add('active');
}

/**
 * Close plan modal
 */
function closePlanModal() {
    document.getElementById('planModal').classList.remove('active');
}

/**
 * Load available strategies
 */
async function loadStrategies() {
    try {
        const response = await fetch(`${API_BASE}/strategy-instances/`);
        if (!response.ok) throw new Error('Failed to load strategies');

        const data = await response.json();
        allStrategies = data.strategies || [];

        renderStrategiesSelector();
    } catch (error) {
        console.error('Error loading strategies:', error);
        document.getElementById('strategiesSelector').innerHTML =
            '<div style="color: #e74c3c;">加载策略失败</div>';
    }
}

/**
 * Render strategies selector
 */
function renderStrategiesSelector() {
    const container = document.getElementById('strategiesSelector');

    if (!allStrategies || allStrategies.length === 0) {
        container.innerHTML = '<div style="color: #7f8c8d;">暂无可用策略</div>';
        return;
    }

    container.innerHTML = allStrategies.map(strategy => `
        <div class="strategy-item ${selectedStrategyIds.includes(strategy.strategy_id) ? 'selected' : ''}"
             onclick="toggleStrategy('${strategy.strategy_id}')">
            <input type="checkbox"
                   ${selectedStrategyIds.includes(strategy.strategy_id) ? 'checked' : ''}
                   onclick="event.stopPropagation(); toggleStrategy('${strategy.strategy_id}')">
            <strong>${escapeHtml(strategy.strategy_name)}</strong>
            <span style="color: #7f8c8d; font-size: 0.9em;"> - ${strategy.strategy_type}</span>
        </div>
    `).join('');
}

/**
 * Toggle strategy selection
 */
function toggleStrategy(strategyId) {
    const index = selectedStrategyIds.indexOf(strategyId);
    if (index > -1) {
        selectedStrategyIds.splice(index, 1);
    } else {
        selectedStrategyIds.push(strategyId);
    }

    renderStrategiesSelector();
}

/**
 * Handle plan form submission
 */
async function handlePlanSubmit(event) {
    event.preventDefault();

    const planData = {
        plan_name: document.getElementById('planName').value,
        description: document.getElementById('planDescription').value,
        strategy_ids: selectedStrategyIds,
        tags: document.getElementById('planTags').value
            .split(',')
            .map(t => t.trim())
            .filter(t => t),
        target_scenario: document.getElementById('planScenario').value
    };

    try {
        let response;
        if (currentPlanId) {
            // Update existing plan
            response = await fetch(`${API_BASE}/plans/${currentPlanId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(planData)
            });
        } else {
            // Create new plan
            response = await fetch(`${API_BASE}/plans/`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(planData)
            });
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '操作失败');
        }

        const result = await response.json();

        // Show validation warnings if any
        if (result.validation && result.validation.warnings && result.validation.warnings.length > 0) {
            displayValidationWarnings(result.validation.warnings);
        } else {
            // Success - close modal and reload
            closePlanModal();
            loadPlans();
            showSuccess(currentPlanId ? '方案更新成功' : '方案创建成功');
        }
    } catch (error) {
        console.error('Error saving plan:', error);
        showError('保存失败: ' + error.message);
    }
}

/**
 * Display validation warnings
 */
function displayValidationWarnings(warnings) {
    const container = document.getElementById('validationWarnings');

    const html = `
        <div class="validation-warnings">
            <strong>⚠ 验证警告</strong>
            ${warnings.map(w => `
                <div class="warning-item">
                    <strong>${w.message}</strong>
                    ${w.suggestion ? `<div style="color: #666; font-size: 0.9em;">${w.suggestion}</div>` : ''}
                </div>
            `).join('')}
            <div style="margin-top: 10px;">
                <button type="button" class="btn btn-secondary" onclick="closePlanModal()">取消</button>
                <button type="button" class="btn btn-primary" onclick="saveIgnoreWarnings()">忽略警告并保存</button>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

/**
 * Save plan ignoring warnings
 */
async function saveIgnoreWarnings() {
    // Just close warnings and reload
    document.getElementById('validationWarnings').innerHTML = '';
    closePlanModal();
    loadPlans();
    showSuccess(currentPlanId ? '方案更新成功' : '方案创建成功');
}

/**
 * Edit plan
 */
async function editPlan(planId) {
    try {
        const response = await fetch(`${API_BASE}/plans/${planId}?include_strategies=true`);
        if (!response.ok) throw new Error('Failed to load plan');

        const plan = await response.json();

        currentPlanId = planId;
        selectedStrategyIds = plan.strategy_ids || [];

        document.getElementById('modalTitle').textContent = '编辑方案';
        document.getElementById('planName').value = plan.plan_name;
        document.getElementById('planDescription').value = plan.description || '';
        document.getElementById('planTags').value = (plan.tags || []).join(', ');
        document.getElementById('planScenario').value = plan.target_scenario || '';

        await loadStrategies();

        document.getElementById('planModal').classList.add('active');
    } catch (error) {
        console.error('Error loading plan for edit:', error);
        showError('加载方案失败: ' + error.message);
    }
}

/**
 * Delete plan
 */
async function deletePlan(planId) {
    if (!confirm('确定要删除此方案吗？此操作不可撤销。')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/plans/${planId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '删除失败');
        }

        loadPlans();
        showSuccess('方案删除成功');
    } catch (error) {
        console.error('Error deleting plan:', error);
        showError('删除失败: ' + error.message);
    }
}

/**
 * Show plan detail
 */
async function showPlanDetail(planId) {
    try {
        const [planResponse, previewResponse] = await Promise.all([
            fetch(`${API_BASE}/plans/${planId}?include_strategies=true`),
            fetch(`${API_BASE}/plans/${planId}/preview`, {method: 'POST'})
        ]);

        if (!planResponse.ok || !previewResponse.ok) {
            throw new Error('Failed to load plan details');
        }

        const plan = await planResponse.json();
        const preview = await previewResponse.json();

        renderPlanDetail(plan, preview);

        document.getElementById('detailModal').classList.add('active');
    } catch (error) {
        console.error('Error loading plan detail:', error);
        showError('加载详情失败: ' + error.message);
    }
}

/**
 * Render plan detail content
 */
function renderPlanDetail(plan, preview) {
    document.getElementById('detailTitle').textContent = plan.plan_name;

    // Format strategies with enhanced card layout
    const strategiesHtml = (plan.strategies || []).map(s => `
        <div class="strategy-card">
            <div class="strategy-header">
                <span class="strategy-name">${escapeHtml(s.strategy_name)}</span>
                <span class="strategy-type-badge">${s.strategy_type}</span>
            </div>
        </div>
    `).join('');

    const tagsHtml = (plan.tags || []).map(tag =>
        `<span class="tag">${tag}</span>`
    ).join('');

    // Format time range display
    const timeRangeHtml = preview.summary.time_range ? `
        <span class="time-display">
            ${Math.floor(preview.summary.time_range.earliest / 3600)}:${Math.floor((preview.summary.time_range.earliest % 3600) / 60).toString().padStart(2, '0')}
            →
            ${Math.floor(preview.summary.time_range.latest / 3600)}:${Math.floor((preview.summary.time_range.latest % 3600) / 60).toString().padStart(2, '0')}
        </span>
    ` : '<span style="color: #7f8c8d;">无时间限制</span>';

    const content = `
        <!-- Basic Information Section -->
        <div class="detail-section">
            <h3>📋 基本信息</h3>
            <div class="detail-grid">
                <div class="info-item">
                    <span class="info-label">方案描述</span>
                    <span class="info-value">${escapeHtml(plan.description || '无描述')}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">目标场景</span>
                    <span class="info-value">${escapeHtml(plan.target_scenario || '无')}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">创建时间</span>
                    <span class="info-value">${new Date(plan.created_at).toLocaleString('zh-CN')}</span>
                </div>
                ${tagsHtml ? `
                <div class="info-item">
                    <span class="info-label">标签</span>
                    <div class="info-value">${tagsHtml}</div>
                </div>
                ` : ''}
            </div>
        </div>

        <!-- Strategy List Section -->
        <div class="detail-section">
            <h3>🎯 包含策略 (${preview.summary.total_strategies}个)</h3>
            ${strategiesHtml || '<p style="color: #7f8c8d;">无策略（基准方案）</p>'}
        </div>

        <!-- Impact Statistics Section -->
        <div class="detail-section">
            <h3>📊 影响范围统计</h3>
            <div class="stat-row">
                <div class="stat-item">
                    <span class="stat-label">影响边数</span>
                    <span class="stat-value">${preview.summary.affected_edge_count}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">策略数量</span>
                    <span class="stat-value">${preview.summary.total_strategies}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">时间范围</span>
                    <div class="stat-value" style="font-size: 1rem;">${timeRangeHtml}</div>
                </div>
            </div>
        </div>

        <!-- Validation Status Section -->
        <div class="detail-section">
            <h3>✅ XML验证状态</h3>
            <span id="validation-status-${plan.plan_id}" class="validation-status pending">
                <i class="status-icon">⏳</i> 未验证
            </span>
        </div>

        <!-- XML Preview Section -->
        <div class="detail-section">
            <h3>📄 XML配置预览</h3>
            <div class="xml-preview">${escapeHtml(preview.xml_preview)}</div>
        </div>

        <!-- Action Buttons -->
        <div class="detail-actions">
            <button class="btn btn-primary btn-validate" onclick="validatePlan('${plan.plan_id}')">
                验证XML
            </button>
            ${!plan.is_baseline ? `
                <button class="btn btn-primary" onclick="closeDetailModal(); editPlan('${plan.plan_id}')">编辑方案</button>
                <button class="btn btn-danger" onclick="closeDetailModal(); deletePlan('${plan.plan_id}')">删除方案</button>
            ` : ''}
            <button class="btn btn-secondary" onclick="closeDetailModal()">关闭</button>
        </div>
    `;

    document.getElementById('detailContent').innerHTML = content;
}

/**
 * Close detail modal
 */
function closeDetailModal() {
    document.getElementById('detailModal').classList.remove('active');
}

/**
 * View plan detail (wrapper)
 */
function viewPlanDetail(planId) {
    showPlanDetail(planId);
}

/**
 * showSuccess 和 showError 由 notification.js 提供（居中显示的提示框）
 */

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
