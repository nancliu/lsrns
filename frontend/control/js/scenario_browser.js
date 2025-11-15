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

    filterEvent.addEventListener('change', applyFilters);
    filterStrategy.addEventListener('change', applyFilters);
    filterSearch.addEventListener('input', applyFilters);
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

// Initialize page when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePage);
} else {
    initializePage();
}
