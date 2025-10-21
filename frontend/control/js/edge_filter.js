/**
 * Edge Filter JavaScript - Phase 1B Edge Selector
 *
 * Handles API communication, filter parameter management, results display,
 * loading states, and error handling for the edge selector interface.
 */

// Global state
let currentResults = [];
let selectedEdges = new Set();
let isLoading = false;
let availableRoutes = [];
let availableSections = [];

/**
 * Initialize page - load metadata
 */
async function initializePage() {
    try {
        // Load available routes and demonstrations in parallel
        await Promise.all([
            loadAvailableRoutes(),
            loadAvailableDemonstrations()
        ]);

        // Set up route dropdown change listener
        const routeSelect = document.getElementById('route-codes');
        routeSelect.addEventListener('change', onRouteSelectionChange);

    } catch (error) {
        console.error('Error initializing page:', error);
    }
}

/**
 * Load available routes from API
 */
async function loadAvailableRoutes() {
    try {
        const response = await fetch('/api/v1/control/edges/routes');
        if (!response.ok) {
            throw new Error(`Failed to load routes: ${response.status}`);
        }

        availableRoutes = await response.json();

        // Populate route dropdown
        const routeSelect = document.getElementById('route-codes');
        routeSelect.innerHTML = '';

        availableRoutes.forEach(routeInfo => {
            const option = document.createElement('option');
            option.value = routeInfo.route_code;
            option.textContent = `${routeInfo.route_code} (${routeInfo.edge_count} 路段)`;
            routeSelect.appendChild(option);
        });

    } catch (error) {
        console.error('Error loading routes:', error);
        const routeSelect = document.getElementById('route-codes');
        routeSelect.innerHTML = '<option value="">加载失败</option>';
    }
}

/**
 * Handle route selection change - load sections for selected routes
 */
async function onRouteSelectionChange() {
    const routeSelect = document.getElementById('route-codes');
    const sectionSelect = document.getElementById('section-codes');
    const selectedRoutes = Array.from(routeSelect.selectedOptions).map(opt => opt.value);

    if (selectedRoutes.length === 0) {
        sectionSelect.innerHTML = '<option value="">请先选择路线</option>';
        return;
    }

    try {
        sectionSelect.innerHTML = '<option value="">加载中...</option>';

        // Load sections for selected routes
        const allSections = [];
        for (const routeCode of selectedRoutes) {
            const response = await fetch(`/api/v1/control/edges/sections?route_code=${routeCode}`);
            if (!response.ok) {
                throw new Error(`Failed to load sections for ${routeCode}`);
            }
            const sections = await response.json();
            allSections.push(...sections);
        }

        // Populate section dropdown
        sectionSelect.innerHTML = '';
        allSections.forEach(sectionInfo => {
            const option = document.createElement('option');
            option.value = sectionInfo.section_code;
            option.textContent = `${sectionInfo.section_code} (${sectionInfo.stake_range}, ${sectionInfo.edge_count} 路段)`;
            sectionSelect.appendChild(option);
        });

        if (allSections.length === 0) {
            sectionSelect.innerHTML = '<option value="">无可用路段</option>';
        }

    } catch (error) {
        console.error('Error loading sections:', error);
        sectionSelect.innerHTML = '<option value="">加载失败</option>';
    }
}

/**
 * Load available demonstration areas from API
 */
async function loadAvailableDemonstrations() {
    try {
        const response = await fetch('/api/v1/control/edges/demonstrations');
        if (!response.ok) {
            throw new Error(`Failed to load demonstrations: ${response.status}`);
        }

        const demonstrations = await response.json();

        // Populate demonstration dropdown
        const demoSelect = document.getElementById('demonstration-ids');
        demoSelect.innerHTML = '';

        demonstrations.forEach(demoInfo => {
            const option = document.createElement('option');
            option.value = demoInfo.demonstration_id;
            option.textContent = `示范段 ${demoInfo.demonstration_id} (${demoInfo.stake_range}, ${demoInfo.edge_count} 路段)`;
            demoSelect.appendChild(option);
        });

        if (demonstrations.length === 0) {
            demoSelect.innerHTML = '<option value="">无示范段数据</option>';
        }

    } catch (error) {
        console.error('Error loading demonstrations:', error);
        const demoSelect = document.getElementById('demonstration-ids');
        demoSelect.innerHTML = '<option value="">加载失败</option>';
    }
}

// Initialize page when DOM is loaded
document.addEventListener('DOMContentLoaded', initializePage);

/**
 * Query edges with current filter parameters
 */
async function queryEdges() {
    if (isLoading) return;

    const queryBtn = document.getElementById('query-btn');
    const resultsContainer = document.getElementById('results-container');
    const resultsTable = document.getElementById('results-table');
    const resultsInfo = document.getElementById('results-info');
    const warningMessage = document.getElementById('warning-message');

    try {
        // Set loading state
        isLoading = true;
        queryBtn.disabled = true;
        queryBtn.textContent = '查询中...';

        resultsContainer.innerHTML = '<div class="loading">加载中</div>';
        resultsTable.style.display = 'none';
        resultsInfo.style.display = 'none';
        warningMessage.style.display = 'none';

        // Build query parameters
        const params = buildQueryParams();
        const queryString = new URLSearchParams(params).toString();
        const url = `/api/v1/control/edges/query${queryString ? '?' + queryString : ''}`;

        // Execute API request
        const response = await fetch(url);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail?.message || errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();

        // Update results
        currentResults = data.edges || [];
        selectedEdges.clear();

        // Display results
        displayResults(data);

    } catch (error) {
        console.error('Error querying edges:', error);
        displayError(error.message);
    } finally {
        // Reset loading state
        isLoading = false;
        queryBtn.disabled = false;
        queryBtn.textContent = '查询路段';
    }
}

/**
 * Build query parameters from filter form
 */
function buildQueryParams() {
    const params = {};

    // Route codes - multi-select dropdown
    const routeSelect = document.getElementById('route-codes');
    const selectedRoutes = Array.from(routeSelect.selectedOptions).map(opt => opt.value);
    if (selectedRoutes.length > 0) {
        params.route_codes = selectedRoutes.join(',');
    }

    // Section codes - multi-select dropdown
    const sectionSelect = document.getElementById('section-codes');
    const selectedSections = Array.from(sectionSelect.selectedOptions).map(opt => opt.value);
    if (selectedSections.length > 0) {
        params.section_codes = selectedSections.join(',');
    }

    // Stake range
    const minStake = document.getElementById('min-stake').value;
    if (minStake) params.min_stake = minStake;

    const maxStake = document.getElementById('max-stake').value;
    if (maxStake) params.max_stake = maxStake;

    // Length range
    const minLength = document.getElementById('min-length').value;
    if (minLength) params.min_length = minLength;

    const maxLength = document.getElementById('max-length').value;
    if (maxLength) params.max_length = maxLength;

    // Minimum lanes
    const minLanes = document.getElementById('min-lanes').value;
    if (minLanes) params.min_lanes = minLanes;

    // Route direction
    const routeDirection = document.getElementById('route-direction').value;
    if (routeDirection) params.route_direction = routeDirection;

    // Node types - multi-select dropdown
    const nodeTypeSelect = document.getElementById('node-types');
    const selectedNodeTypes = Array.from(nodeTypeSelect.selectedOptions).map(opt => opt.value);
    if (selectedNodeTypes.length > 0) {
        params.node_types = selectedNodeTypes.join(',');
    }

    // Demonstration IDs - multi-select dropdown
    const demoSelect = document.getElementById('demonstration-ids');
    const selectedDemos = Array.from(demoSelect.selectedOptions).map(opt => opt.value);
    if (selectedDemos.length > 0) {
        params.demonstration_ids = selectedDemos.join(',');
    }

    // With gantry
    const withGantry = document.getElementById('with-gantry').value;
    if (withGantry === 'true') params.with_gantry = 'true';

    return params;
}

/**
 * Display query results
 */
function displayResults(data) {
    const resultsContainer = document.getElementById('results-container');
    const resultsTable = document.getElementById('results-table');
    const resultsTbody = document.getElementById('results-tbody');
    const resultsInfo = document.getElementById('results-info');
    const warningMessage = document.getElementById('warning-message');
    const resultCount = document.getElementById('result-count');
    const selectedCount = document.getElementById('selected-count');

    // Clear previous results
    resultsTbody.innerHTML = '';

    // Update result count
    resultCount.textContent = data.total_count;
    selectedCount.textContent = '0';

    // Show warning if present
    if (data.warning) {
        warningMessage.textContent = data.warning;
        warningMessage.style.display = 'block';
    } else {
        warningMessage.style.display = 'none';
    }

    // Display results
    if (data.total_count === 0) {
        resultsContainer.innerHTML = '<div class="empty">未找到匹配的路段</div>';
        resultsTable.style.display = 'none';
        resultsInfo.style.display = 'none';
        return;
    }

    // Populate table
    data.edges.forEach(edge => {
        const row = createResultRow(edge);
        resultsTbody.appendChild(row);
    });

    // Show results
    resultsContainer.innerHTML = '';
    resultsTable.style.display = 'table';
    resultsInfo.style.display = 'flex';
}

/**
 * Create table row for a single edge
 */
function createResultRow(edge) {
    const row = document.createElement('tr');

    // Checkbox
    const checkboxCell = document.createElement('td');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.dataset.edgeId = edge.edge_id;
    checkbox.onchange = () => toggleEdgeSelection(edge.edge_id);
    checkboxCell.appendChild(checkbox);
    row.appendChild(checkboxCell);

    // Edge ID
    const edgeIdCell = document.createElement('td');
    edgeIdCell.textContent = edge.edge_id;
    row.appendChild(edgeIdCell);

    // Route code
    const routeCell = document.createElement('td');
    routeCell.textContent = edge.route_code;
    row.appendChild(routeCell);

    // Section code
    const sectionCell = document.createElement('td');
    sectionCell.textContent = edge.section_code || '-';
    row.appendChild(sectionCell);

    // Stake range
    const stakeCell = document.createElement('td');
    if (edge.start_stake !== null && edge.end_stake !== null) {
        stakeCell.textContent = `K${edge.start_stake.toFixed(2)} - K${edge.end_stake.toFixed(2)}`;
    } else {
        stakeCell.textContent = '-';
    }
    row.appendChild(stakeCell);

    // Length
    const lengthCell = document.createElement('td');
    lengthCell.textContent = edge.length !== null ? edge.length.toFixed(1) : '-';
    row.appendChild(lengthCell);

    // Lanes
    const lanesCell = document.createElement('td');
    lanesCell.textContent = edge.num_lanes !== null ? edge.num_lanes : '-';
    row.appendChild(lanesCell);

    // Direction
    const directionCell = document.createElement('td');
    if (edge.route_direction === 'clockwise') {
        directionCell.textContent = '顺时针';
    } else if (edge.route_direction === 'counterclockwise') {
        directionCell.textContent = '逆时针';
    } else {
        directionCell.textContent = '-';
    }
    row.appendChild(directionCell);

    // Node type
    const nodeTypeCell = document.createElement('td');
    const nodeTypeMap = {
        'diverging': '分流',
        'merging': '汇流',
        'entrance': '入口',
        'exit': '出口'
    };
    nodeTypeCell.textContent = edge.node_type ? (nodeTypeMap[edge.node_type] || edge.node_type) : '-';
    row.appendChild(nodeTypeCell);

    // Gantry count
    const gantryCell = document.createElement('td');
    gantryCell.textContent = edge.gantry_count;
    row.appendChild(gantryCell);

    return row;
}

/**
 * Toggle edge selection
 */
function toggleEdgeSelection(edgeId) {
    if (selectedEdges.has(edgeId)) {
        selectedEdges.delete(edgeId);
    } else {
        selectedEdges.add(edgeId);
    }

    updateSelectedCount();
}

/**
 * Update selected count display
 */
function updateSelectedCount() {
    const selectedCount = document.getElementById('selected-count');
    selectedCount.textContent = selectedEdges.size;

    // Update select-all checkbox state
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    if (selectedEdges.size === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    } else if (selectedEdges.size === currentResults.length) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
    }
}

/**
 * Toggle select all checkboxes
 */
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    const checkboxes = document.querySelectorAll('input[data-edge-id]');

    if (selectAllCheckbox.checked) {
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            selectedEdges.add(checkbox.dataset.edgeId);
        });
    } else {
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
            selectedEdges.delete(checkbox.dataset.edgeId);
        });
    }

    updateSelectedCount();
}

/**
 * Select all edges
 */
function selectAll() {
    const checkboxes = document.querySelectorAll('input[data-edge-id]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
        selectedEdges.add(checkbox.dataset.edgeId);
    });
    updateSelectedCount();
}

/**
 * Deselect all edges
 */
function deselectAll() {
    const checkboxes = document.querySelectorAll('input[data-edge-id]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
        selectedEdges.delete(checkbox.dataset.edgeId);
    });
    updateSelectedCount();
}

/**
 * Display error message
 */
function displayError(message) {
    const resultsContainer = document.getElementById('results-container');
    const resultsTable = document.getElementById('results-table');
    const resultsInfo = document.getElementById('results-info');

    resultsContainer.innerHTML = `<div class="error">查询失败: ${message}</div>`;
    resultsTable.style.display = 'none';
    resultsInfo.style.display = 'none';
}

/**
 * Reset all filters
 */
function resetFilters() {
    // Clear multi-select dropdowns
    document.getElementById('route-codes').selectedIndex = -1;
    document.getElementById('section-codes').innerHTML = '<option value="">请先选择路线</option>';

    // Clear other inputs and dropdowns
    document.getElementById('min-stake').value = '';
    document.getElementById('max-stake').value = '';
    document.getElementById('min-length').value = '';
    document.getElementById('max-length').value = '';
    document.getElementById('min-lanes').value = '';
    document.getElementById('route-direction').value = '';
    document.getElementById('node-types').selectedIndex = -1;
    document.getElementById('demonstration-ids').selectedIndex = -1;
    document.getElementById('with-gantry').value = 'false';

    // Clear results
    currentResults = [];
    selectedEdges.clear();

    const resultsContainer = document.getElementById('results-container');
    const resultsTable = document.getElementById('results-table');
    const resultsInfo = document.getElementById('results-info');
    const warningMessage = document.getElementById('warning-message');

    resultsContainer.innerHTML = '<div class="empty">请设置筛选条件并点击"查询路段"</div>';
    resultsTable.style.display = 'none';
    resultsInfo.style.display = 'none';
    warningMessage.style.display = 'none';
}

/**
 * Get currently selected edges
 * @returns {Array} Array of selected edge IDs
 */
function getSelectedEdges() {
    return Array.from(selectedEdges);
}

/**
 * Get currently selected edges with full details
 * @returns {Array} Array of selected edge objects
 */
function getSelectedEdgesDetails() {
    return currentResults.filter(edge => selectedEdges.has(edge.edge_id));
}


// ==================== Visualization Integration (Phase 1B - US4) ====================

/**
 * Load network visualization with current route filter
 */
async function loadVisualization() {
    // Hide empty message
    const emptyDiv = document.querySelector('.viz-empty');
    if (emptyDiv) {
        emptyDiv.style.display = 'none';
    }

    // Get selected routes from filter
    const routeSelect = document.getElementById('route-codes');
    const selectedRoutes = Array.from(routeSelect.selectedOptions).map(opt => opt.value);

    // Initialize visualization if not already done
    if (!networkViz.canvas) {
        const initialized = networkViz.init('network-canvas');
        if (!initialized) {
            alert('无法初始化网络可视化Canvas');
            return;
        }
    }

    // Load geometry
    const success = await networkViz.loadGeometry(selectedRoutes.length > 0 ? selectedRoutes : null);

    if (success) {
        // If we have query results, highlight them
        if (currentResults.length > 0) {
            networkViz.highlightEdges(currentResults);
        }

        // Sync selected edges
        syncVisualizationSelection();
    }
}


/**
 * Callback when visualization selection changes (called from network_viz.js)
 * @param {Array<string>} edgeIds - Selected edge IDs from visualization
 */
function onVisualizationSelectionChanged(edgeIds) {
    // Update table checkboxes to match visualization selection
    const checkboxes = document.querySelectorAll('input[data-edge-id]');

    checkboxes.forEach(checkbox => {
        const edgeId = checkbox.dataset.edgeId;
        const shouldBeChecked = edgeIds.includes(edgeId);

        if (checkbox.checked !== shouldBeChecked) {
            checkbox.checked = shouldBeChecked;

            if (shouldBeChecked) {
                selectedEdges.add(edgeId);
            } else {
                selectedEdges.delete(edgeId);
            }
        }
    });

    updateSelectedCount();
}


/**
 * Sync visualization selection with table selection
 */
function syncVisualizationSelection() {
    if (window.networkViz && window.networkViz.setSelected) {
        const selectedEdgeIds = Array.from(selectedEdges);
        window.networkViz.setSelected(selectedEdgeIds);
    }
}


/**
 * Override toggleEdgeSelection to sync with visualization
 */
const originalToggleEdgeSelection = toggleEdgeSelection;
function toggleEdgeSelection(edgeId) {
    originalToggleEdgeSelection(edgeId);
    syncVisualizationSelection();
}


/**
 * Override selectAll to sync with visualization
 */
const originalSelectAll = selectAll;
function selectAll() {
    originalSelectAll();
    syncVisualizationSelection();
}


/**
 * Override deselectAll to sync with visualization
 */
const originalDeselectAll = deselectAll;
function deselectAll() {
    originalDeselectAll();
    syncVisualizationSelection();
}


/**
 * Override displayResults to update visualization
 */
const originalDisplayResults = displayResults;
function displayResults(data) {
    originalDisplayResults(data);

    // Update visualization if loaded
    if (window.networkViz && window.networkViz.highlightEdges) {
        networkViz.highlightEdges(data.edges || []);
    }
}
