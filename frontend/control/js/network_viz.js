/**
 * Network Visualization Module (Phase 1B - US4)
 *
 * Provides Canvas-based visualization of road network with:
 * - Junction coordinate rendering
 * - Edge line drawing
 * - Filtered edge highlighting
 * - Pan and zoom controls
 * - Click-to-select functionality
 * - Tooltip on hover
 */

// ==================== Global State ====================

const networkViz = {
    // Canvas and context
    canvas: null,
    ctx: null,

    // Data
    geometry: null,  // {junctions: [], edges: []}
    filteredEdges: [],  // Array of edge_ids from query results
    selectedEdges: new Set(),  // Set of selected edge_ids

    // Coordinate transformation
    transform: {
        offsetX: 0,
        offsetY: 0,
        scale: 1.0,
        minScale: 0.1,
        maxScale: 10.0
    },

    // Bounding box for coordinate transformation
    bounds: {
        minLon: null,
        maxLon: null,
        minLat: null,
        maxLat: null
    },

    // Interaction state
    isDragging: false,
    dragStartX: 0,
    dragStartY: 0,
    hoveredEdge: null,

    // Visual settings
    colors: {
        background: '#f5f7fa',
        normalEdge: '#cbd5e0',
        filteredEdge: '#3498db',
        selectedEdge: '#2ecc71',
        hoveredEdge: '#e74c3c',
        junction: '#95a5a6'
    },

    lineWidths: {
        normalEdge: 1,
        filteredEdge: 2,
        selectedEdge: 3,
        hoveredEdge: 3
    }
};


// ==================== Initialization (T040) ====================

/**
 * Initialize Canvas visualization
 * @param {string} canvasId - ID of canvas element
 */
function initNetworkViz(canvasId = 'network-canvas') {
    networkViz.canvas = document.getElementById(canvasId);
    if (!networkViz.canvas) {
        console.error(`Canvas element with ID '${canvasId}' not found`);
        return false;
    }

    networkViz.ctx = networkViz.canvas.getContext('2d');

    // Set canvas size to container
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Set up event listeners
    setupEventListeners();

    console.log('Network visualization initialized');
    return true;
}


/**
 * Resize canvas to fit container
 */
function resizeCanvas() {
    if (!networkViz.canvas) return;

    const container = networkViz.canvas.parentElement;
    networkViz.canvas.width = container.clientWidth;
    networkViz.canvas.height = container.clientHeight;

    // Redraw after resize
    if (networkViz.geometry) {
        renderNetwork();
    }
}


/**
 * Set up mouse and touch event listeners
 */
function setupEventListeners() {
    const canvas = networkViz.canvas;

    // Mouse events for pan/zoom
    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('mouseleave', handleMouseLeave);
    canvas.addEventListener('wheel', handleWheel);

    // Touch events for mobile (future enhancement)
    // canvas.addEventListener('touchstart', handleTouchStart);
    // canvas.addEventListener('touchmove', handleTouchMove);
    // canvas.addEventListener('touchend', handleTouchEnd);
}


// ==================== Data Loading (T041) ====================

/**
 * Load network geometry from API
 * @param {Array<string>} routeCodes - Optional route codes to filter
 * @returns {Promise<boolean>} Success status
 */
async function loadNetworkGeometry(routeCodes = null) {
    try {
        showLoading('正在加载网络几何数据...');

        // Build API URL
        let url = '/api/v1/control/edges/network_geometry';
        if (routeCodes && routeCodes.length > 0) {
            const params = new URLSearchParams({ route_codes: routeCodes.join(',') });
            url += '?' + params.toString();
        }

        // Fetch geometry
        const response = await fetch(url);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail?.message || 'Failed to load geometry');
        }

        networkViz.geometry = await response.json();

        // Calculate bounding box
        calculateBounds();

        // Initialize transform to fit all geometry
        fitToView();

        // Render network
        renderNetwork();

        hideLoading();

        console.log(
            `Loaded geometry: ${networkViz.geometry.junctions.length} junctions, ` +
            `${networkViz.geometry.edges.length} edges`
        );

        return true;

    } catch (error) {
        console.error('Error loading network geometry:', error);
        hideLoading();
        showError(`加载网络几何数据失败: ${error.message}`);
        return false;
    }
}


/**
 * Calculate bounding box for all junctions
 */
function calculateBounds() {
    if (!networkViz.geometry || !networkViz.geometry.junctions.length) {
        return;
    }

    const junctions = networkViz.geometry.junctions;

    networkViz.bounds.minLon = Math.min(...junctions.map(j => j.longitude));
    networkViz.bounds.maxLon = Math.max(...junctions.map(j => j.longitude));
    networkViz.bounds.minLat = Math.min(...junctions.map(j => j.latitude));
    networkViz.bounds.maxLat = Math.max(...junctions.map(j => j.latitude));

    console.log('Calculated bounds:', networkViz.bounds);
}


// ==================== Coordinate Transformation ====================

/**
 * Convert geographic coordinates (lon, lat) to canvas coordinates (x, y)
 * @param {number} lon - Longitude
 * @param {number} lat - Latitude
 * @returns {{x: number, y: number}} Canvas coordinates
 */
function lonLatToCanvas(lon, lat) {
    const bounds = networkViz.bounds;
    const canvas = networkViz.canvas;
    const transform = networkViz.transform;

    // Normalize to [0, 1]
    const normX = (lon - bounds.minLon) / (bounds.maxLon - bounds.minLon);
    const normY = (lat - bounds.minLat) / (bounds.maxLat - bounds.minLat);

    // Map to canvas coordinates (flip Y axis - canvas Y increases downward)
    const padding = 50;
    const baseX = padding + normX * (canvas.width - 2 * padding);
    const baseY = padding + (1 - normY) * (canvas.height - 2 * padding);

    // Apply transformation (pan and zoom)
    const x = baseX * transform.scale + transform.offsetX;
    const y = baseY * transform.scale + transform.offsetY;

    return { x, y };
}


/**
 * Fit network to view with padding
 */
function fitToView() {
    const canvas = networkViz.canvas;
    const bounds = networkViz.bounds;

    if (!canvas || !bounds.minLon) return;

    // Reset transform
    networkViz.transform.scale = 1.0;
    networkViz.transform.offsetX = 0;
    networkViz.transform.offsetY = 0;

    // Calculate scale to fit both width and height
    const padding = 100;
    const availableWidth = canvas.width - 2 * padding;
    const availableHeight = canvas.height - 2 * padding;

    const lonRange = bounds.maxLon - bounds.minLon;
    const latRange = bounds.maxLat - bounds.minLat;

    // Use smaller scale to ensure everything fits
    const scaleX = availableWidth / lonRange;
    const scaleY = availableHeight / latRange;
    networkViz.transform.scale = Math.min(scaleX, scaleY) * 0.9;  // 90% to add margin

    // Center the network
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    networkViz.transform.offsetX = centerX - (bounds.minLon + lonRange / 2) * networkViz.transform.scale;
    networkViz.transform.offsetY = centerY - (bounds.minLat + latRange / 2) * networkViz.transform.scale;
}


// ==================== Rendering (T042) ====================

/**
 * Render entire network on canvas
 */
function renderNetwork() {
    if (!networkViz.ctx || !networkViz.geometry) return;

    const ctx = networkViz.ctx;
    const canvas = networkViz.canvas;

    // Clear canvas
    ctx.fillStyle = networkViz.colors.background;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Render edges
    renderEdges();

    // Render junctions (small dots)
    renderJunctions();

    // Render legend
    renderLegend();
}


/**
 * Render all edges as lines
 */
function renderEdges() {
    if (!networkViz.geometry || !networkViz.geometry.edges) return;

    const ctx = networkViz.ctx;
    const junctionMap = createJunctionMap();

    // Render in order: normal → filtered → selected → hovered
    const edgesByType = categorizeEdges();

    // Normal edges (background)
    ctx.lineWidth = networkViz.lineWidths.normalEdge;
    ctx.strokeStyle = networkViz.colors.normalEdge;
    edgesByType.normal.forEach(edge => drawEdge(edge, junctionMap));

    // Filtered edges (highlighted)
    ctx.lineWidth = networkViz.lineWidths.filteredEdge;
    ctx.strokeStyle = networkViz.colors.filteredEdge;
    edgesByType.filtered.forEach(edge => drawEdge(edge, junctionMap));

    // Selected edges (green)
    ctx.lineWidth = networkViz.lineWidths.selectedEdge;
    ctx.strokeStyle = networkViz.colors.selectedEdge;
    edgesByType.selected.forEach(edge => drawEdge(edge, junctionMap));

    // Hovered edge (red, on top)
    if (networkViz.hoveredEdge) {
        ctx.lineWidth = networkViz.lineWidths.hoveredEdge;
        ctx.strokeStyle = networkViz.colors.hoveredEdge;
        drawEdge(networkViz.hoveredEdge, junctionMap);
    }
}


/**
 * Draw a single edge as a line
 * @param {Object} edge - Edge data
 * @param {Map} junctionMap - Map of junction_id to junction object
 */
function drawEdge(edge, junctionMap) {
    const fromJunction = junctionMap.get(edge.from_junction);
    const toJunction = junctionMap.get(edge.to_junction);

    if (!fromJunction || !toJunction) {
        return;  // Skip edges with missing junctions
    }

    const from = lonLatToCanvas(fromJunction.longitude, fromJunction.latitude);
    const to = lonLatToCanvas(toJunction.longitude, toJunction.latitude);

    const ctx = networkViz.ctx;
    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(to.x, to.y);
    ctx.stroke();
}


/**
 * Render junction points
 */
function renderJunctions() {
    if (!networkViz.geometry || !networkViz.geometry.junctions) return;

    const ctx = networkViz.ctx;
    const radius = 2;

    ctx.fillStyle = networkViz.colors.junction;

    networkViz.geometry.junctions.forEach(junction => {
        if (!junction.longitude || !junction.latitude) return;

        const pos = lonLatToCanvas(junction.longitude, junction.latitude);

        ctx.beginPath();
        ctx.arc(pos.x, pos.y, radius, 0, 2 * Math.PI);
        ctx.fill();
    });
}


/**
 * Render legend showing edge colors
 */
function renderLegend() {
    const ctx = networkViz.ctx;
    const canvas = networkViz.canvas;

    const legendX = canvas.width - 200;
    const legendY = 20;
    const lineLength = 30;
    const lineSpacing = 25;

    // Legend background
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.fillRect(legendX - 10, legendY - 10, 190, 120);
    ctx.strokeStyle = '#ddd';
    ctx.lineWidth = 1;
    ctx.strokeRect(legendX - 10, legendY - 10, 190, 120);

    // Legend items
    const items = [
        { color: networkViz.colors.normalEdge, label: '普通路段', width: networkViz.lineWidths.normalEdge },
        { color: networkViz.colors.filteredEdge, label: '筛选结果', width: networkViz.lineWidths.filteredEdge },
        { color: networkViz.colors.selectedEdge, label: '已选择', width: networkViz.lineWidths.selectedEdge },
        { color: networkViz.colors.hoveredEdge, label: '鼠标悬停', width: networkViz.lineWidths.hoveredEdge }
    ];

    ctx.font = '12px -apple-system, sans-serif';
    ctx.fillStyle = '#333';

    items.forEach((item, index) => {
        const y = legendY + index * lineSpacing;

        // Draw line
        ctx.strokeStyle = item.color;
        ctx.lineWidth = item.width;
        ctx.beginPath();
        ctx.moveTo(legendX, y);
        ctx.lineTo(legendX + lineLength, y);
        ctx.stroke();

        // Draw label
        ctx.fillText(item.label, legendX + lineLength + 10, y + 4);
    });
}


/**
 * Create junction map for fast lookup
 * @returns {Map<string, Object>} Map of junction_id to junction object
 */
function createJunctionMap() {
    const map = new Map();
    if (networkViz.geometry && networkViz.geometry.junctions) {
        networkViz.geometry.junctions.forEach(junction => {
            map.set(junction.junction_id, junction);
        });
    }
    return map;
}


/**
 * Categorize edges by rendering type
 * @returns {Object} Edges grouped by type
 */
function categorizeEdges() {
    const normal = [];
    const filtered = [];
    const selected = [];

    networkViz.geometry.edges.forEach(edge => {
        if (networkViz.selectedEdges.has(edge.edge_id)) {
            selected.push(edge);
        } else if (networkViz.filteredEdges.includes(edge.edge_id)) {
            filtered.push(edge);
        } else {
            normal.push(edge);
        }
    });

    return { normal, filtered, selected };
}


// ==================== Highlighting (T043) ====================

/**
 * Highlight filtered edges from query results
 * @param {Array<Object>} queryResults - Array of edge objects from API
 */
function highlightFilteredEdges(queryResults) {
    // Extract edge IDs from query results
    networkViz.filteredEdges = queryResults.map(edge => edge.edge_id);

    console.log(`Highlighting ${networkViz.filteredEdges.length} filtered edges`);

    // Redraw with highlighted edges
    renderNetwork();
}


/**
 * Clear filtered edge highlighting
 */
function clearFilteredEdges() {
    networkViz.filteredEdges = [];
    renderNetwork();
}


// ==================== Pan/Zoom Controls ====================

/**
 * Handle mouse down event (start dragging)
 */
function handleMouseDown(event) {
    networkViz.isDragging = true;
    networkViz.dragStartX = event.clientX - networkViz.transform.offsetX;
    networkViz.dragStartY = event.clientY - networkViz.transform.offsetY;
    networkViz.canvas.style.cursor = 'grabbing';
}


/**
 * Handle mouse move event (drag or hover)
 */
function handleMouseMove(event) {
    if (networkViz.isDragging) {
        // Pan the network
        networkViz.transform.offsetX = event.clientX - networkViz.dragStartX;
        networkViz.transform.offsetY = event.clientY - networkViz.dragStartY;
        renderNetwork();
    } else {
        // Check for edge hover
        const hoveredEdge = getEdgeAtPosition(event.offsetX, event.offsetY);

        if (hoveredEdge !== networkViz.hoveredEdge) {
            networkViz.hoveredEdge = hoveredEdge;
            renderNetwork();

            if (hoveredEdge) {
                showTooltip(event.clientX, event.clientY, hoveredEdge);
                networkViz.canvas.style.cursor = 'pointer';
            } else {
                hideTooltip();
                networkViz.canvas.style.cursor = 'default';
            }
        }
    }
}


/**
 * Handle mouse up event (stop dragging or click)
 */
function handleMouseUp(event) {
    if (networkViz.isDragging) {
        networkViz.isDragging = false;
        networkViz.canvas.style.cursor = 'default';
    } else {
        // Handle click to toggle selection (T045)
        handleEdgeClick(event.offsetX, event.offsetY);
    }
}


/**
 * Handle mouse leave event
 */
function handleMouseLeave() {
    networkViz.isDragging = false;
    networkViz.hoveredEdge = null;
    networkViz.canvas.style.cursor = 'default';
    hideTooltip();
    renderNetwork();
}


/**
 * Handle mouse wheel event (zoom)
 */
function handleWheel(event) {
    event.preventDefault();

    const zoomIntensity = 0.1;
    const delta = event.deltaY < 0 ? 1 : -1;
    const newScale = networkViz.transform.scale * (1 + delta * zoomIntensity);

    // Clamp scale to min/max
    if (newScale < networkViz.transform.minScale || newScale > networkViz.transform.maxScale) {
        return;
    }

    // Zoom toward mouse position
    const rect = networkViz.canvas.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;

    // Calculate new offsets to zoom toward mouse
    const scaleFactor = newScale / networkViz.transform.scale;
    networkViz.transform.offsetX = mouseX - (mouseX - networkViz.transform.offsetX) * scaleFactor;
    networkViz.transform.offsetY = mouseY - (mouseY - networkViz.transform.offsetY) * scaleFactor;
    networkViz.transform.scale = newScale;

    renderNetwork();
}


/**
 * Reset view to fit all geometry
 */
function resetView() {
    fitToView();
    renderNetwork();
}


// ==================== Edge Selection (T045) ====================

/**
 * Get edge at given canvas position
 * @param {number} x - Canvas X coordinate
 * @param {number} y - Canvas Y coordinate
 * @returns {Object|null} Edge object or null
 */
function getEdgeAtPosition(x, y) {
    if (!networkViz.geometry) return null;

    const junctionMap = createJunctionMap();
    const threshold = 5;  // Click tolerance in pixels

    // Check edges in reverse order (hovered/selected edges on top)
    const edgesByType = categorizeEdges();
    const allEdges = [
        ...edgesByType.selected,
        ...edgesByType.filtered,
        ...edgesByType.normal
    ];

    for (let edge of allEdges) {
        const fromJunction = junctionMap.get(edge.from_junction);
        const toJunction = junctionMap.get(edge.to_junction);

        if (!fromJunction || !toJunction) continue;

        const from = lonLatToCanvas(fromJunction.longitude, fromJunction.latitude);
        const to = lonLatToCanvas(toJunction.longitude, toJunction.latitude);

        // Calculate distance from point to line segment
        const dist = distanceToSegment(x, y, from.x, from.y, to.x, to.y);

        if (dist < threshold) {
            return edge;
        }
    }

    return null;
}


/**
 * Calculate distance from point to line segment
 */
function distanceToSegment(px, py, x1, y1, x2, y2) {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const lengthSquared = dx * dx + dy * dy;

    if (lengthSquared === 0) {
        // Degenerate segment (point)
        return Math.sqrt((px - x1) * (px - x1) + (py - y1) * (py - y1));
    }

    // Project point onto line segment
    let t = ((px - x1) * dx + (py - y1) * dy) / lengthSquared;
    t = Math.max(0, Math.min(1, t));

    const projX = x1 + t * dx;
    const projY = y1 + t * dy;

    return Math.sqrt((px - projX) * (px - projX) + (py - projY) * (py - projY));
}


/**
 * Handle edge click to toggle selection
 * @param {number} x - Canvas X coordinate
 * @param {number} y - Canvas Y coordinate
 */
function handleEdgeClick(x, y) {
    const clickedEdge = getEdgeAtPosition(x, y);

    if (!clickedEdge) return;

    // Toggle selection
    if (networkViz.selectedEdges.has(clickedEdge.edge_id)) {
        networkViz.selectedEdges.delete(clickedEdge.edge_id);
        console.log(`Deselected edge: ${clickedEdge.edge_id}`);
    } else {
        networkViz.selectedEdges.add(clickedEdge.edge_id);
        console.log(`Selected edge: ${clickedEdge.edge_id}`);
    }

    // Update selected edges list in main UI
    updateSelectedEdgesList();

    // Redraw
    renderNetwork();
}


/**
 * Get array of selected edge IDs
 * @returns {Array<string>} Array of selected edge_ids
 */
function getSelectedEdges() {
    return Array.from(networkViz.selectedEdges);
}


/**
 * Clear all edge selections
 */
function clearSelectedEdges() {
    networkViz.selectedEdges.clear();
    updateSelectedEdgesList();
    renderNetwork();
}


/**
 * Set selected edges from external source (e.g., table checkboxes)
 * @param {Array<string>} edgeIds - Array of edge IDs to select
 */
function setSelectedEdges(edgeIds) {
    networkViz.selectedEdges = new Set(edgeIds);
    renderNetwork();
}


// ==================== Tooltip ====================

/**
 * Show tooltip with edge information
 * @param {number} x - Screen X coordinate
 * @param {number} y - Screen Y coordinate
 * @param {Object} edge - Edge object
 */
function showTooltip(x, y, edge) {
    let tooltip = document.getElementById('network-tooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.id = 'network-tooltip';
        tooltip.style.position = 'fixed';
        tooltip.style.background = 'rgba(0, 0, 0, 0.8)';
        tooltip.style.color = 'white';
        tooltip.style.padding = '8px 12px';
        tooltip.style.borderRadius = '4px';
        tooltip.style.fontSize = '12px';
        tooltip.style.pointerEvents = 'none';
        tooltip.style.zIndex = '10000';
        tooltip.style.whiteSpace = 'nowrap';
        document.body.appendChild(tooltip);
    }

    // Build tooltip content
    tooltip.innerHTML = `
        <strong>路段ID:</strong> ${edge.edge_id}<br>
        <strong>路线:</strong> ${edge.route_code || 'N/A'}<br>
        <strong>起点:</strong> ${edge.from_junction}<br>
        <strong>终点:</strong> ${edge.to_junction}
    `;

    // Position tooltip
    tooltip.style.left = (x + 15) + 'px';
    tooltip.style.top = (y + 15) + 'px';
    tooltip.style.display = 'block';
}


/**
 * Hide tooltip
 */
function hideTooltip() {
    const tooltip = document.getElementById('network-tooltip');
    if (tooltip) {
        tooltip.style.display = 'none';
    }
}


// ==================== UI Integration ====================

/**
 * Show loading message
 */
function showLoading(message) {
    const container = document.getElementById('network-viz-container');
    if (container) {
        const loading = container.querySelector('.viz-loading');
        if (loading) {
            loading.textContent = message;
            loading.style.display = 'block';
        }
    }
}


/**
 * Hide loading message
 */
function hideLoading() {
    const container = document.getElementById('network-viz-container');
    if (container) {
        const loading = container.querySelector('.viz-loading');
        if (loading) {
            loading.style.display = 'none';
        }
    }
}


/**
 * Show error message
 */
function showError(message) {
    const container = document.getElementById('network-viz-container');
    if (container) {
        const error = container.querySelector('.viz-error');
        if (error) {
            error.textContent = message;
            error.style.display = 'block';
        }
    }
}


/**
 * Update selected edges list in main UI (to be implemented by integrator)
 */
function updateSelectedEdgesList() {
    const selectedEdgeIds = getSelectedEdges();

    // Call external function if available
    if (typeof onVisualizationSelectionChanged === 'function') {
        onVisualizationSelectionChanged(selectedEdgeIds);
    }

    // Update count display
    const countElement = document.getElementById('viz-selected-count');
    if (countElement) {
        countElement.textContent = selectedEdgeIds.length;
    }
}


// ==================== Export API ====================

// Export functions for external use
window.networkViz = {
    init: initNetworkViz,
    loadGeometry: loadNetworkGeometry,
    highlightEdges: highlightFilteredEdges,
    clearFiltered: clearFilteredEdges,
    getSelected: getSelectedEdges,
    setSelected: setSelectedEdges,
    clearSelected: clearSelectedEdges,
    resetView: resetView,
    render: renderNetwork
};
