/**
 * Event Scenario Browser - JavaScript functionality
 * Handles loading scenarios, filtering, and quick case creation
 */

let allScenarios = [];
let filteredScenarios = [];
let selectedScenario = null;

/**
 * Initialize the page
 */
async function initializePage() {
    setupEventListeners();
    await loadScenarios();
    renderTable();
}

/**
 * Setup event listeners for filters and buttons
 */
function setupEventListeners() {
    const filterEvent = document.getElementById('filter-event');
    const filterStrategy = document.getElementById('filter-strategy');
    const filterSearch = document.getElementById('filter-search');
    const createBtn = document.getElementById('create-case-btn');
    const modalClose = document.getElementById('modal-close');
    const modalCancel = document.getElementById('modal-cancel');
    const createCaseForm = document.getElementById('create-case-form');

    filterEvent.addEventListener('change', applyFilters);
    filterStrategy.addEventListener('change', applyFilters);
    filterSearch.addEventListener('input', applyFilters);

    // Modal controls
    if (createBtn) {
        createBtn.addEventListener('click', () => {
            if (!selectedScenario) {
                alert('请先选择一个事件场景');
                return;
            }
            openCreateCaseModal();
        });
    }

    modalClose.addEventListener('click', closeCreateCaseModal);
    modalCancel.addEventListener('click', closeCreateCaseModal);

    createCaseForm.addEventListener('submit', handleCreateCase);

    // Close modal when clicking outside
    const modal = document.getElementById('create-case-modal');
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeCreateCaseModal();
        }
    });
}

/**
 * Load scenarios from scenario_index.json
 */
async function loadScenarios() {
    const loading = document.getElementById('loading');
    const emptyState = document.getElementById('empty-state');

    try {
        loading.classList.add('active');

        const response = await fetch('/output/scenarios/scenario_index.json');
        if (!response.ok) {
            throw new Error('Failed to load scenarios');
        }

        const data = await response.json();
        allScenarios = data.scenarios || [];

        loading.classList.remove('active');

        if (allScenarios.length === 0) {
            emptyState.classList.add('active');
        }
    } catch (error) {
        console.error('Error loading scenarios:', error);
        loading.classList.remove('active');

        const emptyState = document.getElementById('empty-state');
        emptyState.querySelector('p').textContent = '加载场景失败，请刷新重试';
        emptyState.classList.add('active');
    }
}

/**
 * Apply filters to scenarios
 */
function applyFilters() {
    const eventType = document.getElementById('filter-event').value;
    const strategy = document.getElementById('filter-strategy').value;
    const search = document.getElementById('filter-search').value.toLowerCase();

    filteredScenarios = allScenarios.filter((scenario) => {
        const matchesEvent = !eventType || scenario.event_type === eventType;
        const matchesStrategy =
            !strategy ||
            scenario.strategy.toLowerCase() === strategy.toLowerCase();
        const matchesSearch =
            !search ||
            scenario.event_id.toLowerCase().includes(search) ||
            scenario.strategy.toLowerCase().includes(search);

        return matchesEvent && matchesStrategy && matchesSearch;
    });

    renderTable();
}

/**
 * Render scenarios table
 */
function renderTable() {
    const tbody = document.getElementById('scenarios-tbody');
    const table = document.getElementById('scenarios-table');
    const emptyState = document.getElementById('empty-state');

    if (filteredScenarios.length === 0) {
        table.style.display = 'none';
        emptyState.classList.add('active');
        return;
    }

    table.style.display = 'table';
    emptyState.classList.remove('active');

    tbody.innerHTML = '';

    filteredScenarios.forEach((scenario) => {
        const row = createTableRow(scenario);
        tbody.appendChild(row);
    });
}

/**
 * Create a table row for a scenario
 */
function createTableRow(scenario) {
    const row = document.createElement('tr');

    const timeRange = `${scenario.time.start_time} ~ ${scenario.time.end_time}`;
    const strategyBadge = getStrategyBadge(scenario.strategy);

    row.innerHTML = `
        <td>${scenario.event_type}</td>
        <td>${scenario.event_id}</td>
        <td>${strategyBadge}</td>
        <td>${timeRange}</td>
        <td>
            <div class="action-buttons">
                <button class="btn-primary" onclick="selectScenarioAndCreateCase('${
                    scenario.event_id
                }', '${scenario.event_type}', '${scenario.strategy}')">
                    创建案例
                </button>
            </div>
        </td>
    `;

    return row;
}

/**
 * Get HTML for strategy badge
 */
function getStrategyBadge(strategy) {
    const badgeClass = `badge badge-${strategy.toLowerCase()}`;
    const displayName =
        strategy === 'VSS'
            ? 'VSS (可变限速)'
            : strategy === 'TEC'
              ? 'TEC (收费站控制)'
              : 'DHS (动态硬路肩)';

    return `<span class="${badgeClass}">${displayName}</span>`;
}

/**
 * Select scenario and open create case modal
 */
function selectScenarioAndCreateCase(eventId, eventType, strategy) {
    selectedScenario = {
        event_id: eventId,
        event_type: eventType,
        strategy: strategy,
        scenario_id: `scenario_${eventId}_${strategy.toLowerCase()}`,
    };

    openCreateCaseModal();
}

/**
 * Open create case modal
 */
function openCreateCaseModal() {
    const modal = document.getElementById('create-case-modal');
    const form = document.getElementById('create-case-form');

    if (selectedScenario) {
        // Reset form
        form.reset();

        // Set default case name
        const caseName = document.getElementById('case-name');
        caseName.value = `事件${selectedScenario.event_id}_${selectedScenario.strategy}`;
    }

    modal.classList.add('active');
}

/**
 * Close create case modal
 */
function closeCreateCaseModal() {
    const modal = document.getElementById('create-case-modal');
    modal.classList.remove('active');
    selectedScenario = null;
}

/**
 * Handle create case form submission
 */
async function handleCreateCase(event) {
    event.preventDefault();

    if (!selectedScenario) {
        alert('未选择事件场景');
        return;
    }

    const caseName = document.getElementById('case-name').value.trim();
    const networkFile = document.getElementById('network-file').value;
    const odFile = document.getElementById('od-file').value.trim();
    const tazFile = document.getElementById('taz-file').value.trim();
    const description = document.getElementById('case-description').value.trim();

    // Validation
    if (!caseName) {
        alert('请输入案例名称');
        return;
    }
    if (!networkFile) {
        alert('请选择网络文件');
        return;
    }
    if (!odFile) {
        alert('请输入OD文件路径');
        return;
    }

    await createCase({
        case_name: caseName,
        event_type: selectedScenario.event_type,
        strategy: selectedScenario.strategy,
        scenario_id: selectedScenario.scenario_id,
        network_file: networkFile,
        od_file: odFile,
        taz_file: tazFile || null,
        description:
            description ||
            `从事件场景 ${selectedScenario.scenario_id} 创建`,
    });
}

/**
 * Create case via API
 */
async function createCase(requestData) {
    const submitBtn = document.querySelector('#create-case-form button[type="submit"]');
    const originalText = submitBtn.textContent;

    try {
        submitBtn.disabled = true;
        submitBtn.textContent = '创建中...';

        const response = await fetch('/api/v1/quick-create-from-event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || '创建案例失败');
        }

        // Success
        alert(`案例创建成功！案例ID: ${data.data.case_id}`);
        closeCreateCaseModal();

        // Navigate to case or refresh list
        // Optional: navigate to case detail page
        // window.location.href = `/control/case_detail.html?case_id=${data.data.case_id}`;
    } catch (error) {
        console.error('Error creating case:', error);
        alert(`创建案例失败: ${error.message}`);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

// Initialize page when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePage);
} else {
    initializePage();
}
