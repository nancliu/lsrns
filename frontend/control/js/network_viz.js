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
    // Canvas and context (dual-layer architecture)
    canvas: null,          // Bottom layer: static network rendering
    ctx: null,
    hoverCanvas: null,     // Top layer: hover effects only
    hoverCtx: null,

    // Canvas dimensions (logical pixels for coordinate calculation)
    logicalWidth: 0,
    logicalHeight: 0,

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
        maxScale: 40.0  // Increased from 10.0 to allow more zoom levels
    },

    // Bounding box for coordinate transformation
    bounds: {
        minLon: null,
        maxLon: null,
        minLat: null,
        maxLat: null
    },

    // Progressive rendering state
    rendering: {
        inProgress: false,
        cancelRequested: false,
        chunkSize: 200,  // Render 200 edges per frame
        currentChunk: 0,
        pendingRender: null,  // Debounced render timeout
        pendingHoverRender: null  // Debounced hover layer render
    },

    // Resize state (prevent infinite loop)
    resizing: {
        inProgress: false,
        debounceTimeout: null
    },

    // Interaction state
    isDragging: false,
    mousePressed: false,  // Track if mouse button is pressed
    mouseDownX: 0,        // Mouse position when button was pressed
    mouseDownY: 0,
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
 * Initialize Canvas visualization with dual-layer architecture
 * @param {string} canvasId - ID of main canvas element
 * @param {string} hoverCanvasId - ID of hover layer canvas element
 */
function initNetworkViz(canvasId = 'network-canvas', hoverCanvasId = 'network-canvas-hover') {
    // Initialize bottom layer (static network)
    networkViz.canvas = document.getElementById(canvasId);
    if (!networkViz.canvas) {
        console.error(`Canvas element with ID '${canvasId}' not found`);
        return false;
    }
    networkViz.ctx = networkViz.canvas.getContext('2d');

    // Initialize top layer (hover effects)
    networkViz.hoverCanvas = document.getElementById(hoverCanvasId);
    if (!networkViz.hoverCanvas) {
        console.warn(`Hover canvas with ID '${hoverCanvasId}' not found, falling back to single-layer mode`);
        networkViz.hoverCanvas = null;
        networkViz.hoverCtx = null;
    } else {
        networkViz.hoverCtx = networkViz.hoverCanvas.getContext('2d');
        console.log('✅ Dual-layer Canvas initialized (static + hover)');
    }

    // Set canvas size to container
    resizeCanvas();

    // Remove any existing resize listener before adding new one (prevent duplicates)
    window.removeEventListener('resize', resizeCanvas);
    window.addEventListener('resize', resizeCanvas);

    // Set up event listeners (on main canvas only)
    setupEventListeners();

    console.log('Network visualization initialized');
    return true;
}


/**
 * Resize canvas to fit container (with device pixel ratio support)
 * Resizes both bottom layer and hover layer
 */
function resizeCanvas() {
    if (!networkViz.canvas) return;

    // Prevent resize loop: Check if already resizing
    if (networkViz.resizing.inProgress) {
        console.warn('[resizeCanvas] ⚠️ Resize already in progress, skipping');
        return;
    }

    const container = networkViz.canvas.parentElement;
    const dpr = window.devicePixelRatio || 1;

    // Store logical dimensions for coordinate calculations
    const newWidth = container.clientWidth;
    const newHeight = container.clientHeight;

    // Prevent resize loop: Only resize if dimensions actually changed
    if (networkViz.logicalWidth === newWidth && networkViz.logicalHeight === newHeight) {
        // Dimensions unchanged, skip resize
        return;
    }

    // Set resize flag
    networkViz.resizing.inProgress = true;

    networkViz.logicalWidth = newWidth;
    networkViz.logicalHeight = newHeight;

    // Resize bottom layer (static network)
    networkViz.canvas.width = networkViz.logicalWidth * dpr;
    networkViz.canvas.height = networkViz.logicalHeight * dpr;
    networkViz.canvas.style.width = networkViz.logicalWidth + 'px';
    networkViz.canvas.style.height = networkViz.logicalHeight + 'px';

    const ctx = networkViz.canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    // Resize hover layer (if exists)
    if (networkViz.hoverCanvas) {
        networkViz.hoverCanvas.width = networkViz.logicalWidth * dpr;
        networkViz.hoverCanvas.height = networkViz.logicalHeight * dpr;
        networkViz.hoverCanvas.style.width = networkViz.logicalWidth + 'px';
        networkViz.hoverCanvas.style.height = networkViz.logicalHeight + 'px';

        const hoverCtx = networkViz.hoverCanvas.getContext('2d');
        hoverCtx.scale(dpr, dpr);
    }

    console.log(`[resizeCanvas] Canvas resized: ${networkViz.logicalWidth}x${networkViz.logicalHeight} (DPR: ${dpr}, physical: ${networkViz.canvas.width}x${networkViz.canvas.height})`);

    // Redraw after resize
    if (networkViz.geometry) {
        renderNetwork(true);
    }

    // Clear resize flag after a short delay (allow render to complete)
    setTimeout(() => {
        networkViz.resizing.inProgress = false;
    }, 100);
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

        // Ensure canvas is properly sized before rendering
        // Fix: Canvas might be 0x0 if not yet resized
        if (networkViz.logicalWidth === 0 || networkViz.logicalHeight === 0) {
            console.warn('[loadNetworkGeometry] Canvas not yet sized, forcing resize...');
            resizeCanvas();
        }

        // Calculate bounding box
        calculateBounds();

        // Initialize transform to fit all geometry
        fitToView();

        // Render network immediately (initial load with progress indicator)
        renderNetwork(true, true);  // immediate=true, showProgress=true

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
    const transform = networkViz.transform;

    // Normalize to [0, 1]
    const normX = (lon - bounds.minLon) / (bounds.maxLon - bounds.minLon);
    const normY = (lat - bounds.minLat) / (bounds.maxLat - bounds.minLat);

    // Map to canvas coordinates (flip Y axis - canvas Y increases downward)
    // Use logical dimensions, not physical pixels
    const padding = 50;
    const baseX = padding + normX * (networkViz.logicalWidth - 2 * padding);
    const baseY = padding + (1 - normY) * (networkViz.logicalHeight - 2 * padding);

    // Apply transformation (pan and zoom)
    const x = baseX * transform.scale + transform.offsetX;
    const y = baseY * transform.scale + transform.offsetY;

    return { x, y };
}


/**
 * Fit network to view with padding
 */
function fitToView() {
    const bounds = networkViz.bounds;

    if (!networkViz.logicalWidth || !bounds.minLon) return;

    // The coordinate system in lonLatToCanvas() is designed so that:
    // - At scale=1, the full geographic bounds map to [padding, canvas-padding]
    // - So identity transform (scale=1, offset=0) gives the perfect fit
    networkViz.transform.scale = 1.0;
    networkViz.transform.offsetX = 0;
    networkViz.transform.offsetY = 0;

    console.log(`[fitToView] Reset to identity transform (scale=1.0, offset=0, 0)`);
}


// ==================== Rendering (T042) ====================

/**
 * Render entire network on canvas
 * Uses progressive rendering for large datasets to maintain UI responsiveness
 * @param {boolean} immediate - If true, render immediately without debouncing
 * @param {boolean} showProgress - If true, show progress indicator during rendering
 */
function renderNetwork(immediate = false, showProgress = false) {
    if (!networkViz.ctx || !networkViz.geometry) return;

    // For immediate renders (data load, zoom, pan), cancel debounce and render now
    if (immediate) {
        if (networkViz.rendering.pendingRender) {
            clearTimeout(networkViz.rendering.pendingRender);
            networkViz.rendering.pendingRender = null;
        }
        executeRender(showProgress);
        return;
    }

    // For hover events, debounce to avoid excessive rendering
    if (networkViz.rendering.pendingRender) {
        clearTimeout(networkViz.rendering.pendingRender);
    }

    networkViz.rendering.pendingRender = setTimeout(() => {
        networkViz.rendering.pendingRender = null;
        executeRender(showProgress);
    }, 16); // ~60 FPS debounce for hover
}


/**
 * Execute the actual rendering (called by renderNetwork after debouncing)
 * @param {boolean} showProgress - Whether to show progress indicator (default: false)
 */
function executeRender(showProgress = false) {
    if (!networkViz.ctx || !networkViz.geometry) return;

    // Cancel any in-progress rendering
    if (networkViz.rendering.inProgress) {
        networkViz.rendering.cancelRequested = true;
    }

    // Check if dataset is large enough to benefit from progressive rendering
    const totalEdges = networkViz.geometry.edges?.length || 0;
    const useProgressiveRendering = totalEdges > 500; // Use progressive for > 500 edges

    if (useProgressiveRendering) {
        console.log(`[executeRender] Using progressive rendering for ${totalEdges} edges`);
        renderNetworkProgressive(showProgress);
    } else {
        console.log(`[executeRender] Using synchronous rendering for ${totalEdges} edges`);
        renderNetworkSync();
    }
}


/**
 * Synchronous rendering for small datasets (< 500 edges)
 */
function renderNetworkSync() {
    const ctx = networkViz.ctx;

    // Clear canvas
    ctx.fillStyle = networkViz.colors.background;
    ctx.fillRect(0, 0, networkViz.logicalWidth, networkViz.logicalHeight);

    // Render all content
    renderEdges();
    renderJunctions();
    renderLegend();
}


/**
 * Progressive rendering for large datasets
 * Renders edges in chunks using requestAnimationFrame to avoid UI blocking
 * @param {boolean} showProgress - Whether to show progress indicator (default: false)
 */
async function renderNetworkProgressive(showProgress = false) {
    networkViz.rendering.inProgress = true;
    networkViz.rendering.cancelRequested = false;
    networkViz.rendering.currentChunk = 0;

    const ctx = networkViz.ctx;
    const junctionMap = createJunctionMap();
    const edgesByType = categorizeEdges();

    // Clear canvas
    ctx.fillStyle = networkViz.colors.background;
    ctx.fillRect(0, 0, networkViz.logicalWidth, networkViz.logicalHeight);

    // Show progress (only if requested)
    if (showProgress) {
        updateProgress(0, '正在渲染路网...');
    }

    // Render edges in chunks
    const allEdges = [
        ...edgesByType.normal,
        ...edgesByType.filtered,
        ...edgesByType.selected
    ];

    const totalEdges = allEdges.length;
    const chunkSize = networkViz.rendering.chunkSize;

    for (let i = 0; i < totalEdges; i += chunkSize) {
        // Check for cancellation
        if (networkViz.rendering.cancelRequested) {
            console.log('[renderNetworkProgressive] Rendering cancelled');
            if (showProgress) {
                hideProgress();
            }
            networkViz.rendering.inProgress = false;
            return;
        }

        // Render chunk
        const chunk = allEdges.slice(i, Math.min(i + chunkSize, totalEdges));

        // Set stroke style based on edge type
        chunk.forEach(edge => {
            if (networkViz.selectedEdges.has(edge.edge_id)) {
                ctx.lineWidth = networkViz.lineWidths.selectedEdge;
                ctx.strokeStyle = networkViz.colors.selectedEdge;
            } else if (networkViz.filteredEdges.includes(edge.edge_id)) {
                ctx.lineWidth = networkViz.lineWidths.filteredEdge;
                ctx.strokeStyle = networkViz.colors.filteredEdge;
            } else {
                ctx.lineWidth = networkViz.lineWidths.normalEdge;
                ctx.strokeStyle = networkViz.colors.normalEdge;
            }

            drawEdge(edge, junctionMap);
        });

        // Update progress (only if requested)
        if (showProgress) {
            const progress = Math.min(100, Math.round((i + chunkSize) / totalEdges * 100));
            updateProgress(progress, `正在渲染路网... ${i + chunk.length}/${totalEdges} 条路段`);
        }

        // Yield to browser (allow UI updates, user interactions)
        await new Promise(resolve => requestAnimationFrame(resolve));
    }

    // Note: Hovered edge is now rendered on separate hover layer (not here)

    // Render junctions and legend
    renderJunctions();
    renderLegend();

    // Hide progress and mark complete
    if (showProgress) {
        hideProgress();
    }
    networkViz.rendering.inProgress = false;

    console.log(`[renderNetworkProgressive] Completed rendering ${totalEdges} edges`);
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

    // Note: Hovered edge is now rendered on separate hover layer (not here)
}


/**
 * Draw a single edge as a line
 * @param {Object} edge - Edge data
 * @param {Map} junctionMap - Map of junction_id to junction object
 * @param {CanvasRenderingContext2D} ctx - Optional canvas context (defaults to main context)
 */
function drawEdge(edge, junctionMap, ctx = null) {
    const fromJunction = junctionMap.get(edge.from_junction);
    const toJunction = junctionMap.get(edge.to_junction);

    if (!fromJunction || !toJunction) {
        return;  // Skip edges with missing junctions
    }

    const from = lonLatToCanvas(fromJunction.longitude, fromJunction.latitude);
    const to = lonLatToCanvas(toJunction.longitude, toJunction.latitude);

    // Use provided context or default to main context
    const context = ctx || networkViz.ctx;
    context.beginPath();
    context.moveTo(from.x, from.y);
    context.lineTo(to.x, to.y);
    context.stroke();
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

    // Use logical dimensions for legend positioning
    const legendX = networkViz.logicalWidth - 200;
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

    // Redraw with highlighted edges immediately
    renderNetwork(true);
}


/**
 * Clear filtered edge highlighting
 */
function clearFilteredEdges() {
    networkViz.filteredEdges = [];
    renderNetwork(true);  // Immediate render
}


// ==================== Pan/Zoom Controls ====================

/**
 * Handle mouse down event (prepare for potential dragging)
 */
function handleMouseDown(event) {
    // Don't set isDragging immediately - wait for actual mouse movement
    // Store the initial position for drag detection
    networkViz.dragStartX = event.clientX - networkViz.transform.offsetX;
    networkViz.dragStartY = event.clientY - networkViz.transform.offsetY;
    networkViz.mouseDownX = event.clientX;
    networkViz.mouseDownY = event.clientY;
    networkViz.mousePressed = true;
}


/**
 * Handle mouse move event (drag or hover)
 */
function handleMouseMove(event) {
    // Check if we should start dragging (mouse pressed and moved beyond threshold)
    if (networkViz.mousePressed && !networkViz.isDragging) {
        const dragThreshold = 3; // pixels
        const dx = event.clientX - networkViz.mouseDownX;
        const dy = event.clientY - networkViz.mouseDownY;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance > dragThreshold) {
            networkViz.isDragging = true;
            networkViz.canvas.style.cursor = 'grabbing';
            console.log('[handleMouseMove] Started dragging');
        }
    }

    if (networkViz.isDragging) {
        // Pan the network - render immediately for smooth dragging
        networkViz.transform.offsetX = event.clientX - networkViz.dragStartX;
        networkViz.transform.offsetY = event.clientY - networkViz.dragStartY;
        renderNetwork(true);  // Immediate full render for pan
    } else {
        // Check for edge hover
        const hoveredEdge = getEdgeAtPosition(event.offsetX, event.offsetY);

        if (hoveredEdge !== networkViz.hoveredEdge) {
            networkViz.hoveredEdge = hoveredEdge;

            // Render ONLY the hover layer (fast!)
            renderHoverLayer();

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
        // Was dragging, stop dragging
        networkViz.isDragging = false;
        networkViz.mousePressed = false;
        networkViz.canvas.style.cursor = 'default';
        console.log('[handleMouseUp] Stopped dragging');
    } else if (networkViz.mousePressed) {
        // Mouse was pressed but didn't drag - this is a click
        networkViz.mousePressed = false;
        handleEdgeClick(event.offsetX, event.offsetY);
        console.log('[handleMouseUp] Handled as click');
    }
}


/**
 * Handle mouse leave event
 */
function handleMouseLeave() {
    networkViz.isDragging = false;
    networkViz.mousePressed = false;
    networkViz.hoveredEdge = null;
    networkViz.canvas.style.cursor = 'default';
    hideTooltip();

    // Clear hover layer
    clearHoverLayer();
}


/**
 * Render only the hover layer (super fast, no network redraw)
 * This is called on every mouse move to show/hide the hovered edge
 */
function renderHoverLayer() {
    // Fallback: if no hover canvas, use full render
    if (!networkViz.hoverCanvas || !networkViz.hoverCtx) {
        renderNetwork();  // Fall back to full render (debounced)
        return;
    }

    // Clear hover layer
    clearHoverLayer();

    // If there's a hovered edge, draw it on hover layer
    if (networkViz.hoveredEdge) {
        const junctionMap = createJunctionMap();
        const ctx = networkViz.hoverCtx;

        // Draw hovered edge in red
        ctx.lineWidth = networkViz.lineWidths.hoveredEdge;
        ctx.strokeStyle = networkViz.colors.hoveredEdge;
        drawEdge(networkViz.hoveredEdge, junctionMap, ctx);
    }
}


/**
 * Clear the hover layer canvas
 */
function clearHoverLayer() {
    if (!networkViz.hoverCanvas || !networkViz.hoverCtx) return;

    networkViz.hoverCtx.clearRect(0, 0, networkViz.logicalWidth, networkViz.logicalHeight);
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

    renderNetwork(true);  // Immediate render for zoom
}


/**
 * Reset view to fit all geometry
 */
function resetView() {
    fitToView();
    renderNetwork(true);  // Immediate render for reset view
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

    console.log('[handleEdgeClick] Clicked position:', x, y);
    console.log('[handleEdgeClick] Found edge:', clickedEdge);

    if (!clickedEdge) {
        console.log('[handleEdgeClick] No edge found at click position');
        return;
    }

    // Toggle selection
    const wasSelected = networkViz.selectedEdges.has(clickedEdge.edge_id);
    if (wasSelected) {
        networkViz.selectedEdges.delete(clickedEdge.edge_id);
        console.log(`[handleEdgeClick] ❌ Deselected edge: ${clickedEdge.edge_id}`);
    } else {
        networkViz.selectedEdges.add(clickedEdge.edge_id);
        console.log(`[handleEdgeClick] ✅ Selected edge: ${clickedEdge.edge_id}`);
    }

    console.log('[handleEdgeClick] Total selected edges:', networkViz.selectedEdges.size);

    // Update selected edges list in main UI
    updateSelectedEdgesList();

    // Redraw immediately (user interaction)
    renderNetwork(true);
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
    renderNetwork(true);  // Immediate render
}


/**
 * Set selected edges from external source (e.g., table checkboxes)
 * @param {Array<string>} edgeIds - Array of edge IDs to select
 */
function setSelectedEdges(edgeIds) {
    networkViz.selectedEdges = new Set(edgeIds);
    updateSelectedEdgesList();  // Update count display
    renderNetwork(true);  // Immediate render
}


// ==================== Tooltip ====================

/**
 * Show tooltip with edge information
 * @param {number} x - Screen X coordinate
 * @param {number} y - Screen Y coordinate
 * @param {Object} edge - Edge object
 */
function showTooltip(x, y, edge) {
    // Debug: Log edge data to see what fields are available
    console.log('[showTooltip] Edge data:', edge);

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

    // Build tooltip content with enhanced information
    const parts = [];

    // Route code and section (primary identification)
    if (edge.route_code) {
        let routeInfo = `<strong>路线:</strong> ${edge.route_code}`;
        if (edge.section_code) {
            routeInfo += ` (${edge.section_code})`;
        }
        parts.push(routeInfo);
    }

    // Edge ID
    parts.push(`<strong>路段ID:</strong> ${edge.edge_id}`);

    // Number of lanes
    if (edge.num_lanes !== null && edge.num_lanes !== undefined) {
        parts.push(`<strong>车道数:</strong> ${edge.num_lanes} 车道`);
    }

    // Stake range (start and end)
    if (edge.start_stake !== null && edge.start_stake !== undefined &&
        edge.end_stake !== null && edge.end_stake !== undefined) {
        parts.push(`<strong>起点桩号:</strong> K${edge.start_stake.toFixed(3)}`);
        parts.push(`<strong>终点桩号:</strong> K${edge.end_stake.toFixed(3)}`);
    }

    // Length
    if (edge.length !== null && edge.length !== undefined) {
        parts.push(`<strong>长度:</strong> ${edge.length.toFixed(1)}m`);
    }

    tooltip.innerHTML = parts.join('<br>');

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
 * Show/update rendering progress bar
 * @param {number} percentage - Progress percentage (0-100)
 * @param {string} message - Progress message
 */
function updateProgress(percentage, message) {
    let progressBar = document.getElementById('viz-progress-bar');

    if (!progressBar) {
        // Create progress bar element if it doesn't exist
        const container = document.getElementById('network-viz-container');
        if (!container) return;

        progressBar = document.createElement('div');
        progressBar.id = 'viz-progress-bar';
        progressBar.style.position = 'absolute';
        progressBar.style.top = '50%';
        progressBar.style.left = '50%';
        progressBar.style.transform = 'translate(-50%, -50%)';
        progressBar.style.width = '80%';
        progressBar.style.maxWidth = '400px';
        progressBar.style.background = 'rgba(255, 255, 255, 0.95)';
        progressBar.style.padding = '20px';
        progressBar.style.borderRadius = '8px';
        progressBar.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
        progressBar.style.zIndex = '1000';
        progressBar.style.textAlign = 'center';

        progressBar.innerHTML = `
            <div style="margin-bottom: 10px; font-size: 14px; color: #333;" id="viz-progress-text"></div>
            <div style="width: 100%; height: 6px; background: #e0e0e0; border-radius: 3px; overflow: hidden;">
                <div id="viz-progress-fill" style="width: 0%; height: 100%; background: linear-gradient(90deg, #3498db, #2ecc71); transition: width 0.3s ease;"></div>
            </div>
            <div style="margin-top: 8px; font-size: 12px; color: #666;" id="viz-progress-percent">0%</div>
        `;

        container.appendChild(progressBar);
    }

    // Update progress
    const textEl = document.getElementById('viz-progress-text');
    const fillEl = document.getElementById('viz-progress-fill');
    const percentEl = document.getElementById('viz-progress-percent');

    if (textEl) textEl.textContent = message;
    if (fillEl) fillEl.style.width = percentage + '%';
    if (percentEl) percentEl.textContent = percentage + '%';

    progressBar.style.display = 'block';
}


/**
 * Hide rendering progress bar
 */
function hideProgress() {
    const progressBar = document.getElementById('viz-progress-bar');
    if (progressBar) {
        progressBar.style.display = 'none';
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

// Export functions and state for external use
window.networkViz = {
    // Public API methods
    init: initNetworkViz,
    loadGeometry: loadNetworkGeometry,
    highlightEdges: highlightFilteredEdges,
    clearFiltered: clearFilteredEdges,
    getSelected: getSelectedEdges,
    setSelected: setSelectedEdges,
    clearSelected: clearSelectedEdges,
    resetView: resetView,
    render: renderNetwork,

    // Expose internal state for external use
    get transform() {
        return networkViz.transform;
    },
    get bounds() {
        return networkViz.bounds;
    },
    get canvas() {
        return networkViz.canvas;
    },
    get geometry() {
        return networkViz.geometry;
    }
};
