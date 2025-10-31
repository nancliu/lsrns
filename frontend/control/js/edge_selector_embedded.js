/**
 * Edge Selector Embedded - For use within strategy management workflow
 *
 * This module provides edge selection functionality embedded in templates.html
 * Uses namespacing to avoid conflicts with parent page variables.
 */

// Edge selector namespace to avoid variable conflicts
const EdgeSelector = {
    // Cache configuration
    CACHE_CONFIG: {
        KEY: 'edge_selector_sections_cache',
        VERSION: 'v1.0',
        TTL: 7 * 24 * 60 * 60 * 1000, // 7 days
    },

    // Internal state
    state: {
        edgeSelectionSet: new Set(),
        currentResults: [],
        isLoading: false,
        availableRoutes: [],
        availableSections: [],
        // Cached sections by route (for performance)
        sectionsByRoute: new Map(),
        // Pagination state
        currentPage: 1,
        pageSize: 50,
        totalCount: 0
    },

    /**
     * Load sections from localStorage cache
     */
    loadFromCache() {
        try {
            const cacheStr = localStorage.getItem(this.CACHE_CONFIG.KEY);
            if (!cacheStr) {
                console.log('[EdgeSelector] No cache found');
                return null;
            }

            const cache = JSON.parse(cacheStr);

            // Check version
            if (cache.version !== this.CACHE_CONFIG.VERSION) {
                console.log('[EdgeSelector] Cache version mismatch, ignoring');
                localStorage.removeItem(this.CACHE_CONFIG.KEY);
                return null;
            }

            // Check TTL
            const age = Date.now() - cache.timestamp;
            if (age > this.CACHE_CONFIG.TTL) {
                console.log(`[EdgeSelector] Cache expired (${(age / 86400000).toFixed(1)} days old)`);
                localStorage.removeItem(this.CACHE_CONFIG.KEY);
                return null;
            }

            console.log(`[EdgeSelector] ✅ Cache loaded (age: ${(age / 3600000).toFixed(1)} hours)`);
            return cache.data;
        } catch (error) {
            console.error('[EdgeSelector] Error loading cache:', error);
            localStorage.removeItem(this.CACHE_CONFIG.KEY);
            return null;
        }
    },

    /**
     * Save sections to localStorage cache
     */
    saveToCache(data) {
        try {
            const cache = {
                version: this.CACHE_CONFIG.VERSION,
                timestamp: Date.now(),
                data: data
            };

            localStorage.setItem(this.CACHE_CONFIG.KEY, JSON.stringify(cache));

            const sizeKB = (JSON.stringify(cache).length / 1024).toFixed(1);
            console.log(`[EdgeSelector] ✅ Cache saved (${sizeKB} KB)`);
        } catch (error) {
            console.error('[EdgeSelector] Error saving cache:', error);
            // Quota exceeded or other error - ignore and continue
        }
    },

    /**
     * Clear cache (call this to force refresh)
     */
    clearCache() {
        localStorage.removeItem(this.CACHE_CONFIG.KEY);
        console.log('[EdgeSelector] Cache cleared');
    },

    /**
     * Initialize edge selector
     */
    async init() {
        try {
            // Step 1: Load routes first (sections depend on route list)
            await this.loadRoutes();

            // Step 2: Try to load sections from cache
            const cachedData = this.loadFromCache();
            if (cachedData) {
                // Use cached data
                for (const [routeCode, sections] of Object.entries(cachedData)) {
                    this.state.sectionsByRoute.set(routeCode, sections);
                }
                console.log('[EdgeSelector] Using cached sections');
            } else {
                // Load from API and cache
                await this.loadAllSections();
            }

            // Step 3: Load demonstrations in parallel
            await this.loadDemonstrations();

            // Set up event listeners
            const routeSelect = document.getElementById('route-codes');
            if (routeSelect) {
                routeSelect.addEventListener('change', () => this.onRouteChange());
            }

            console.log('[EdgeSelector] Initialization complete');
        } catch (error) {
            console.error('Error initializing edge selector:', error);
        }
    },

    /**
     * Load available routes
     */
    async loadRoutes() {
        try {
            const response = await fetch('/api/v1/control/edges/routes');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            this.state.availableRoutes = await response.json();
            const routeSelect = document.getElementById('route-codes');
            if (!routeSelect) return;

            routeSelect.innerHTML = '';
            this.state.availableRoutes.forEach(routeInfo => {
                const option = document.createElement('option');
                option.value = routeInfo.route_code;
                option.textContent = `${routeInfo.route_code} (${routeInfo.edge_count} 路段)`;
                routeSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading routes:', error);
            const routeSelect = document.getElementById('route-codes');
            if (routeSelect) {
                routeSelect.innerHTML = '<option value="">加载失败</option>';
            }
        }
    },

    /**
     * Preload all sections for all routes (PERFORMANCE OPTIMIZATION V2)
     *
     * Strategy: Batch API call instead of N individual requests
     * - Single request: /api/v1/control/edges/all-sections
     * - Fallback: Individual requests if batch API unavailable
     */
    async loadAllSections() {
        try {
            console.log('[EdgeSelector] Preloading sections for all routes...');
            const startTime = performance.now();

            // Try batch API first (much faster)
            try {
                const response = await fetch('/api/v1/control/edges/all-sections');
                if (response.ok) {
                    const data = await response.json();
                    // data format: { route_code: [sections], ... }
                    for (const [routeCode, sections] of Object.entries(data)) {
                        this.state.sectionsByRoute.set(routeCode, sections);
                    }

                    const duration = performance.now() - startTime;
                    const totalSections = Object.values(data).reduce((sum, arr) => sum + arr.length, 0);
                    console.log(`[EdgeSelector] ✅ Batch preload completed in ${duration.toFixed(0)}ms (${totalSections} sections)`);

                    // Save to cache
                    this.saveToCache(data);

                    return;
                }
            } catch (error) {
                console.warn('[EdgeSelector] Batch API unavailable, falling back to individual requests');
            }

            // Fallback: Individual requests with detailed timing
            const routeCount = this.state.availableRoutes.length;
            console.log(`[EdgeSelector] Loading ${routeCount} routes individually...`);

            const promises = this.state.availableRoutes.map(async (routeInfo, index) => {
                const routeStartTime = performance.now();
                try {
                    const response = await fetch(`/api/v1/control/edges/sections?route_code=${routeInfo.route_code}`);
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    const sections = await response.json();
                    this.state.sectionsByRoute.set(routeInfo.route_code, sections);

                    const routeDuration = performance.now() - routeStartTime;
                    console.log(`[EdgeSelector] [${index + 1}/${routeCount}] ${routeInfo.route_code}: ${sections.length} sections in ${routeDuration.toFixed(0)}ms`);

                    return { route: routeInfo.route_code, count: sections.length, duration: routeDuration };
                } catch (error) {
                    console.error(`[EdgeSelector] ❌ Failed to load ${routeInfo.route_code}:`, error);
                    this.state.sectionsByRoute.set(routeInfo.route_code, []);
                    return { route: routeInfo.route_code, count: 0, error: true };
                }
            });

            const results = await Promise.all(promises);
            const duration = performance.now() - startTime;

            const totalSections = results.reduce((sum, r) => sum + r.count, 0);
            const avgDuration = results.reduce((sum, r) => sum + (r.duration || 0), 0) / results.length;

            console.log(`[EdgeSelector] ✅ Individual preload completed in ${duration.toFixed(0)}ms (avg: ${avgDuration.toFixed(0)}ms per route, ${totalSections} total sections)`);

            // Save to cache
            const cacheData = {};
            for (const [routeCode, sections] of this.state.sectionsByRoute.entries()) {
                cacheData[routeCode] = sections;
            }
            this.saveToCache(cacheData);

        } catch (error) {
            console.error('[EdgeSelector] ❌ Error preloading sections:', error);
        }
    },

    /**
     * Handle route selection change (OPTIMIZED with cache)
     */
    onRouteChange() {
        const routeSelect = document.getElementById('route-codes');
        const sectionSelect = document.getElementById('section-codes');
        if (!routeSelect || !sectionSelect) return;

        const selectedRoutes = Array.from(routeSelect.selectedOptions).map(opt => opt.value);

        if (selectedRoutes.length === 0) {
            sectionSelect.innerHTML = '<option value="">请先选择路线</option>';
            this.updateDirectionOptions([]);
            return;
        }

        // Use cached data - no API call needed!
        const allSections = [];
        for (const routeCode of selectedRoutes) {
            const cachedSections = this.state.sectionsByRoute.get(routeCode);
            if (cachedSections) {
                allSections.push(...cachedSections);
            }
        }

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

        // Update direction options based on selected routes
        this.updateDirectionOptions(selectedRoutes);
    },

    /**
     * Update route direction dropdown based on selected routes
     *
     * PERFORMANCE OPTIMIZATION (2025-10-22):
     * Removed dynamic database query that was causing 2-4s delay.
     * Now uses static route classification based on network topology:
     * - SA2, G4202: Ring expressways (clockwise/counterclockwise)
     * - Other routes: Linear highways (upstream/downstream)
     *
     * This instant response (0ms) vs slow query (2-4s) trade-off provides
     * better UX while maintaining correct direction options per route type.
     */
    updateDirectionOptions(selectedRoutes) {
        const directionSelect = document.getElementById('route-direction');
        if (!directionSelect) return;

        const currentValue = directionSelect.value;

        if (selectedRoutes.length === 0) {
            // No route selected: show all options
            directionSelect.innerHTML = `
                <option value="">全部</option>
                <option value="upstream">上行</option>
                <option value="downstream">下行</option>
                <option value="clockwise">顺时针</option>
                <option value="counterclockwise">逆时针</option>
            `;
            directionSelect.value = currentValue;
            return;
        }

        // Classify routes: ring expressways vs linear highways
        const ringRoutes = new Set(['SA2', 'G4202']);  // Ring expressways (环形高速)
        const hasRingRoute = selectedRoutes.some(r => ringRoutes.has(r));
        const hasLinearRoute = selectedRoutes.some(r => !ringRoutes.has(r));

        // Determine which direction options to show
        let options = '<option value="">全部</option>';

        if (hasLinearRoute) {
            // Linear highways: upstream/downstream
            options += '<option value="upstream">上行</option>';
            options += '<option value="downstream">下行</option>';
        }

        if (hasRingRoute) {
            // Ring expressways: clockwise/counterclockwise
            options += '<option value="clockwise">顺时针</option>';
            options += '<option value="counterclockwise">逆时针</option>';
        }

        directionSelect.innerHTML = options;

        // Restore previous selection if it's still valid
        if (currentValue) {
            // Check if the current value exists in the new options
            const optionExists = Array.from(directionSelect.options).some(
                opt => opt.value === currentValue
            );
            if (optionExists) {
                directionSelect.value = currentValue;
            }
        }
    },

    /**
     * Load demonstrations
     */
    async loadDemonstrations() {
        try {
            const response = await fetch('/api/v1/control/edges/demonstrations');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const demonstrations = await response.json();
            const demoSelect = document.getElementById('demonstration-ids');
            if (!demoSelect) return;

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
            if (demoSelect) {
                demoSelect.innerHTML = '<option value="">加载失败</option>';
            }
        }
    },

    /**
     * Build query parameters from form
     */
    buildQueryParams() {
        const params = {};

        // Route codes
        const routeSelect = document.getElementById('route-codes');
        if (routeSelect) {
            const selectedRoutes = Array.from(routeSelect.selectedOptions).map(opt => opt.value);
            if (selectedRoutes.length > 0) params.route_codes = selectedRoutes.join(',');
        }

        // Section codes
        const sectionSelect = document.getElementById('section-codes');
        if (sectionSelect) {
            const selectedSections = Array.from(sectionSelect.selectedOptions).map(opt => opt.value);
            if (selectedSections.length > 0) params.section_codes = selectedSections.join(',');
        }

        // Stake range
        const minStake = document.getElementById('min-stake')?.value;
        if (minStake) params.min_stake = minStake;
        const maxStake = document.getElementById('max-stake')?.value;
        if (maxStake) params.max_stake = maxStake;

        // Length range
        const minLength = document.getElementById('min-length')?.value;
        if (minLength) params.min_length = minLength;
        const maxLength = document.getElementById('max-length')?.value;
        if (maxLength) params.max_length = maxLength;

        // Min lanes
        const minLanes = document.getElementById('min-lanes')?.value;
        if (minLanes) params.min_lanes = minLanes;

        // Route direction
        const routeDirection = document.getElementById('route-direction')?.value;
        if (routeDirection) params.route_direction = routeDirection;

        // Node types
        const nodeTypeSelect = document.getElementById('node-types');
        if (nodeTypeSelect) {
            const selectedNodeTypes = Array.from(nodeTypeSelect.selectedOptions).map(opt => opt.value);
            if (selectedNodeTypes.length > 0) params.node_types = selectedNodeTypes.join(',');
        }

        // Demonstrations
        const demoSelect = document.getElementById('demonstration-ids');
        if (demoSelect) {
            const selectedDemos = Array.from(demoSelect.selectedOptions).map(opt => opt.value);
            if (selectedDemos.length > 0) params.demonstration_ids = selectedDemos.join(',');
        }

        // With gantry
        const withGantry = document.getElementById('with-gantry')?.value;
        if (withGantry === 'true') params.with_gantry = 'true';

        return params;
    },

    /**
     * Query edges with filters
     */
    async query() {
        if (this.state.isLoading) return;

        const queryBtn = document.getElementById('query-btn');
        const resultsContainer = document.getElementById('results-container');
        const resultsTable = document.getElementById('results-table');
        const resultsInfo = document.getElementById('results-info');
        const warningMessage = document.getElementById('warning-message');

        try {
            // 验证查询参数（修复：刚加载页面时点击查询的问题）
            const params = this.buildQueryParams();

            // 检查是否有任何有效的查询条件
            const hasValidParams = Object.keys(params).length > 0 &&
                                   Object.values(params).some(value => value && value.trim() !== '');

            if (!hasValidParams) {
                // 没有有效查询条件，显示友好提示
                if (resultsContainer) {
                    resultsContainer.innerHTML = `
                        <div style="text-align: center; padding: 30px; color: #e67e22;">
                            <p style="margin-bottom: 10px;">⚠️ 请先选择查询条件</p>
                            <p style="font-size: 0.9em; color: #7f8c8d;">
                                请至少选择一个路线或设置其他筛选条件
                            </p>
                        </div>
                    `;
                }
                if (resultsTable) resultsTable.style.display = 'none';
                if (resultsInfo) resultsInfo.style.display = 'none';
                return;
            }

            this.state.isLoading = true;
            if (queryBtn) {
                queryBtn.disabled = true;
                queryBtn.textContent = '查询中...';
            }
            if (resultsContainer) {
                resultsContainer.innerHTML = '<div style="text-align: center; padding: 30px;">加载中...</div>';
            }
            if (resultsTable) resultsTable.style.display = 'none';
            if (resultsInfo) resultsInfo.style.display = 'none';
            if (warningMessage) warningMessage.style.display = 'none';

            const queryString = new URLSearchParams(params).toString();
            const url = `/api/v1/control/edges/query${queryString ? '?' + queryString : ''}`;

            console.log('[EdgeSelector] 查询路段:', url);

            const response = await fetch(url);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail?.message || errorData.detail || `HTTP ${response.status}`);
            }

            const data = await response.json();
            this.state.currentResults = data.edges || [];
            this.state.edgeSelectionSet.clear();

            this.displayResults(data);
        } catch (error) {
            console.error('Error querying edges:', error);
            if (resultsContainer) {
                resultsContainer.innerHTML = `<div style="text-align: center; padding: 30px; color: #e74c3c;">查询失败: ${error.message}</div>`;
            }
            if (resultsTable) resultsTable.style.display = 'none';
            if (resultsInfo) resultsInfo.style.display = 'none';
        } finally {
            this.state.isLoading = false;
            if (queryBtn) {
                queryBtn.disabled = false;
                queryBtn.textContent = '查询路段';
            }
        }
    },

    /**
     * Display query results with pagination
     */
    displayResults(data) {
        const resultsContainer = document.getElementById('results-container');
        const resultsTable = document.getElementById('results-table');
        const resultsTbody = document.getElementById('results-tbody');
        const resultsInfo = document.getElementById('results-info');
        const warningMessage = document.getElementById('warning-message');
        const resultCount = document.getElementById('result-count');
        const selectedCount = document.getElementById('selected-count');

        // Store results and pagination info
        this.state.currentResults = data.edges || [];
        this.state.totalCount = data.total_count;
        this.state.currentPage = 1; // Reset to first page

        if (resultsTbody) resultsTbody.innerHTML = '';
        if (resultCount) resultCount.textContent = data.total_count;
        if (selectedCount) selectedCount.textContent = '0';

        if (data.warning && warningMessage) {
            warningMessage.textContent = data.warning;
            warningMessage.style.display = 'block';
        } else if (warningMessage) {
            warningMessage.style.display = 'none';
        }

        if (data.total_count === 0) {
            if (resultsContainer) {
                resultsContainer.innerHTML = '<div style="text-align: center; padding: 30px; color: #7f8c8d;">未找到匹配的路段</div>';
            }
            if (resultsTable) resultsTable.style.display = 'none';
            if (resultsInfo) resultsInfo.style.display = 'none';
            return;
        }

        // Render current page
        this.renderCurrentPage();

        if (resultsContainer) resultsContainer.innerHTML = '';
        if (resultsTable) resultsTable.style.display = 'table';
        if (resultsInfo) resultsInfo.style.display = 'flex';

        // Update visualization if loaded (highlight all results, not just current page)
        if (window.networkViz && window.networkViz.highlightEdges) {
            window.networkViz.highlightEdges(data.edges || []);
        }
    },

    /**
     * Render current page of results
     */
    renderCurrentPage() {
        const resultsTbody = document.getElementById('results-tbody');
        if (!resultsTbody) return;

        // Clear existing rows
        resultsTbody.innerHTML = '';

        // Calculate pagination
        const totalPages = Math.ceil(this.state.totalCount / this.state.pageSize);
        const startIndex = (this.state.currentPage - 1) * this.state.pageSize;
        const endIndex = Math.min(startIndex + this.state.pageSize, this.state.totalCount);

        // Render rows for current page
        const pageEdges = this.state.currentResults.slice(startIndex, endIndex);
        pageEdges.forEach(edge => {
            const row = this.createResultRow(edge);
            resultsTbody.appendChild(row);

            // Restore checkbox state if edge was previously selected
            const checkbox = row.querySelector('input[type="checkbox"]');
            if (checkbox && this.state.edgeSelectionSet.has(edge.edge_id)) {
                checkbox.checked = true;
            }
        });

        // Render pagination controls
        this.renderPaginationControls(totalPages, startIndex, endIndex);
    },

    /**
     * Render pagination controls
     */
    renderPaginationControls(totalPages, startIndex, endIndex) {
        // Remove existing pagination if present
        let paginationDiv = document.getElementById('pagination-controls');
        if (paginationDiv) {
            paginationDiv.remove();
        }

        // Create pagination controls
        paginationDiv = document.createElement('div');
        paginationDiv.id = 'pagination-controls';
        paginationDiv.style.cssText = 'display: flex; justify-content: space-between; align-items: center; padding: 15px; background: #f8f9fa; border-top: 1px solid #dee2e6;';

        // Page info
        const pageInfo = document.createElement('span');
        pageInfo.style.cssText = 'color: #6c757d; font-size: 14px;';
        pageInfo.textContent = `显示 ${startIndex + 1}-${endIndex} / 共 ${this.state.totalCount} 条`;
        paginationDiv.appendChild(pageInfo);

        // Navigation buttons
        const navButtons = document.createElement('div');
        navButtons.style.cssText = 'display: flex; gap: 10px;';

        // Previous button
        const prevBtn = document.createElement('button');
        prevBtn.textContent = '上一页';
        prevBtn.className = 'btn btn-secondary';
        prevBtn.style.cssText = 'padding: 6px 12px; font-size: 14px;';
        prevBtn.disabled = this.state.currentPage === 1;
        prevBtn.onclick = () => this.goToPage(this.state.currentPage - 1);
        navButtons.appendChild(prevBtn);

        // Page number display
        const pageDisplay = document.createElement('span');
        pageDisplay.style.cssText = 'padding: 6px 12px; font-size: 14px; color: #495057;';
        pageDisplay.textContent = `第 ${this.state.currentPage} / ${totalPages} 页`;
        navButtons.appendChild(pageDisplay);

        // Next button
        const nextBtn = document.createElement('button');
        nextBtn.textContent = '下一页';
        nextBtn.className = 'btn btn-secondary';
        nextBtn.style.cssText = 'padding: 6px 12px; font-size: 14px;';
        nextBtn.disabled = this.state.currentPage >= totalPages;
        nextBtn.onclick = () => this.goToPage(this.state.currentPage + 1);
        navButtons.appendChild(nextBtn);

        paginationDiv.appendChild(navButtons);

        // Insert pagination after results table
        const resultsTable = document.getElementById('results-table');
        if (resultsTable && resultsTable.parentNode) {
            resultsTable.parentNode.insertBefore(paginationDiv, resultsTable.nextSibling);
        }
    },

    /**
     * Go to specific page
     */
    goToPage(pageNumber) {
        const totalPages = Math.ceil(this.state.totalCount / this.state.pageSize);
        if (pageNumber < 1 || pageNumber > totalPages) return;

        this.state.currentPage = pageNumber;
        this.renderCurrentPage();
    },

    /**
     * Create table row for edge
     */
    createResultRow(edge) {
        const row = document.createElement('tr');
        row.style.borderBottom = '1px solid #e9ecef';

        const checkboxCell = document.createElement('td');
        checkboxCell.style.padding = '10px';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.dataset.edgeId = edge.edge_id;
        checkbox.onchange = () => this.toggleSelection(edge.edge_id);
        checkboxCell.appendChild(checkbox);
        row.appendChild(checkboxCell);

        const cells = [
            edge.edge_id,
            edge.route_code,
            edge.section_code || '-',
            edge.start_stake !== null && edge.end_stake !== null ?
                `K${edge.start_stake.toFixed(2)} - K${edge.end_stake.toFixed(2)}` : '-',
            edge.length !== null ? edge.length.toFixed(1) : '-',
            edge.num_lanes !== null ? edge.num_lanes : '-',
            edge.route_direction ? {
                'upstream': '上行',
                'downstream': '下行',
                'clockwise': '顺时针',
                'counterclockwise': '逆时针'
            }[edge.route_direction] || edge.route_direction : '-',
            edge.node_type ? {
                'normal': '普通',
                'diverging': '分流',
                'merging': '汇流',
                'lane_increase': '车道增加',
                'lane_decrease': '车道减少',
                'entrance': '入口',
                'exit': '出口'
            }[edge.node_type] || edge.node_type : '-',
            edge.gantry_count
        ];

        cells.forEach(content => {
            const cell = document.createElement('td');
            cell.style.padding = '10px';
            cell.textContent = content;
            row.appendChild(cell);
        });

        return row;
    },

    /**
     * Toggle edge selection
     */
    toggleSelection(edgeId) {
        if (this.state.edgeSelectionSet.has(edgeId)) {
            this.state.edgeSelectionSet.delete(edgeId);
        } else {
            this.state.edgeSelectionSet.add(edgeId);
        }
        this.updateSelectedCount();

        // Sync to parent page's selectedEdges array
        if (typeof selectedEdges !== 'undefined') {
            selectedEdges = Array.from(this.state.edgeSelectionSet);
        }

        // Sync visualization
        this.syncVisualizationSelection();
    },

    /**
     * Update selected count display
     */
    updateSelectedCount() {
        const selectedCount = document.getElementById('selected-count');
        if (selectedCount) {
            selectedCount.textContent = this.state.edgeSelectionSet.size;
        }

        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        if (selectAllCheckbox) {
            if (this.state.edgeSelectionSet.size === 0) {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = false;
            } else if (this.state.edgeSelectionSet.size === this.state.currentResults.length) {
                selectAllCheckbox.checked = true;
                selectAllCheckbox.indeterminate = false;
            } else {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = true;
            }
        }

        // [FIX] Show/hide "进入配置参数" buttons based on edge selection
        const topActionsBtn = document.getElementById('step2-top-actions');
        const bottomActionsBtn = document.getElementById('step2-bottom-actions');
        const hasSelection = this.state.edgeSelectionSet.size > 0;

        if (topActionsBtn) {
            topActionsBtn.style.display = hasSelection ? 'flex' : 'none';
        }
        if (bottomActionsBtn) {
            // Update button visibility (button itself should be visible when there's selection)
            const nextBtn = document.getElementById('step2-next-bottom');
            if (nextBtn) {
                nextBtn.style.display = hasSelection ? 'block' : 'none';
            }
        }

        console.log('[EdgeSelector] updateSelectedCount: selected=' + this.state.edgeSelectionSet.size + ', buttons=' + (hasSelection ? 'shown' : 'hidden'));
    },

    /**
     * Toggle select all
     */
    toggleSelectAll() {
        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        const checkboxes = document.querySelectorAll('input[data-edge-id]');

        if (selectAllCheckbox && selectAllCheckbox.checked) {
            checkboxes.forEach(checkbox => {
                checkbox.checked = true;
                this.state.edgeSelectionSet.add(checkbox.dataset.edgeId);
            });
        } else {
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
                this.state.edgeSelectionSet.delete(checkbox.dataset.edgeId);
            });
        }
        this.updateSelectedCount();

        // Sync to parent
        if (typeof selectedEdges !== 'undefined') {
            selectedEdges = Array.from(this.state.edgeSelectionSet);
        }
    },

    /**
     * Select all edges
     */
    selectAll() {
        const checkboxes = document.querySelectorAll('input[data-edge-id]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            this.state.edgeSelectionSet.add(checkbox.dataset.edgeId);
        });
        this.updateSelectedCount();

        if (typeof selectedEdges !== 'undefined') {
            selectedEdges = Array.from(this.state.edgeSelectionSet);
        }

        // Sync visualization
        this.syncVisualizationSelection();
    },

    /**
     * Deselect all edges
     */
    deselectAll() {
        const checkboxes = document.querySelectorAll('input[data-edge-id]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
            this.state.edgeSelectionSet.delete(checkbox.dataset.edgeId);
        });
        this.updateSelectedCount();

        if (typeof selectedEdges !== 'undefined') {
            selectedEdges = Array.from(this.state.edgeSelectionSet);
        }

        // Sync visualization
        this.syncVisualizationSelection();
    },

    /**
     * Reset all filters
     */
    resetFilters() {
        const routeSelect = document.getElementById('route-codes');
        if (routeSelect) routeSelect.selectedIndex = -1;

        const sectionSelect = document.getElementById('section-codes');
        if (sectionSelect) sectionSelect.innerHTML = '<option value="">请先选择路线</option>';

        const inputs = [
            'min-stake', 'max-stake', 'min-length', 'max-length', 'min-lanes'
        ];
        inputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) input.value = '';
        });

        const routeDirection = document.getElementById('route-direction');
        if (routeDirection) routeDirection.value = '';

        const nodeTypes = document.getElementById('node-types');
        if (nodeTypes) nodeTypes.selectedIndex = -1;

        const demonstrations = document.getElementById('demonstration-ids');
        if (demonstrations) demonstrations.selectedIndex = -1;

        const withGantry = document.getElementById('with-gantry');
        if (withGantry) withGantry.value = 'false';

        this.state.currentResults = [];
        this.state.edgeSelectionSet.clear();

        const resultsContainer = document.getElementById('results-container');
        if (resultsContainer) {
            resultsContainer.innerHTML = '<div style="text-align: center; padding: 30px; color: #7f8c8d;">请设置筛选条件并点击"查询路段"</div>';
        }

        const resultsTable = document.getElementById('results-table');
        if (resultsTable) resultsTable.style.display = 'none';

        const resultsInfo = document.getElementById('results-info');
        if (resultsInfo) resultsInfo.style.display = 'none';

        const warningMessage = document.getElementById('warning-message');
        if (warningMessage) warningMessage.style.display = 'none';
    },

    // ==================== Visualization Integration (Phase 1B - US4) ====================

    /**
     * Load network visualization with current route filter
     */
    async loadVisualization() {
        // Hide empty message
        const emptyDiv = document.querySelector('.viz-empty');
        if (emptyDiv) {
            emptyDiv.style.display = 'none';
        }

        // Get selected routes from filter
        const routeSelect = document.getElementById('route-codes');
        const selectedRoutes = routeSelect ? Array.from(routeSelect.selectedOptions).map(opt => opt.value) : [];

        // Initialize visualization if not already done
        if (!window.networkViz || typeof window.networkViz.init !== 'function') {
            console.error('Network visualization module not loaded');
            console.error('window.networkViz:', window.networkViz);
            alert('网络可视化模块未加载，请确认 network_viz.js 已正确引入');
            return;
        }

        const initialized = window.networkViz.init('network-canvas');
        if (!initialized) {
            alert('无法初始化网络可视化Canvas');
            return;
        }

        // Load geometry
        const success = await window.networkViz.loadGeometry(selectedRoutes.length > 0 ? selectedRoutes : null);

        if (success) {
            // If we have query results, highlight them
            if (this.state.currentResults.length > 0) {
                window.networkViz.highlightEdges(this.state.currentResults);
            }

            // Sync selected edges
            this.syncVisualizationSelection();
        }
    },

    /**
     * Reset visualization view
     */
    resetView() {
        if (window.networkViz && window.networkViz.resetView) {
            window.networkViz.resetView();
        }
    },

    /**
     * Clear visualization selection
     */
    clearVizSelection() {
        if (window.networkViz && window.networkViz.clearSelected) {
            window.networkViz.clearSelected();
        }
    },

    /**
     * Sync visualization selection with table selection
     */
    syncVisualizationSelection() {
        if (window.networkViz && window.networkViz.setSelected) {
            const selectedEdgeIds = Array.from(this.state.edgeSelectionSet);
            window.networkViz.setSelected(selectedEdgeIds);
        }

        // Update viz selected count
        const vizCountEl = document.getElementById('viz-selected-count');
        if (vizCountEl) {
            vizCountEl.textContent = this.state.edgeSelectionSet.size;
        }
    }
};

// Callback for visualization selection changes (called from network_viz.js)
function onVisualizationSelectionChanged(edgeIds) {
    // Update Edge Selector state and table checkboxes
    EdgeSelector.state.edgeSelectionSet = new Set(edgeIds);

    const checkboxes = document.querySelectorAll('input[data-edge-id]');
    checkboxes.forEach(checkbox => {
        const edgeId = checkbox.dataset.edgeId;
        checkbox.checked = edgeIds.includes(edgeId);
    });

    EdgeSelector.updateSelectedCount();
    // Don't call syncVisualizationSelection() here to avoid infinite loop!
    // This callback is already triggered FROM the visualization layer.

    // Update viz selected count manually
    const vizCountEl = document.getElementById('viz-selected-count');
    if (vizCountEl) {
        vizCountEl.textContent = edgeIds.length;
    }

    // Sync to parent page's selectedEdges array
    if (typeof selectedEdges !== 'undefined') {
        selectedEdges = edgeIds;
    }
}

// Global functions for HTML onclick handlers
function queryEdges() {
    EdgeSelector.query();
}

function resetFilters() {
    EdgeSelector.resetFilters();
}

function refreshSectionCache() {
    if (confirm('确定要刷新路段缓存吗？将重新加载所有路段数据。')) {
        EdgeSelector.clearCache();
        alert('缓存已清除，页面将刷新以重新加载数据...');
        location.reload();
    }
}

function selectAll() {
    EdgeSelector.selectAll();
}

function deselectAll() {
    EdgeSelector.deselectAll();
}

function toggleSelectAll() {
    EdgeSelector.toggleSelectAll();
}

// Visualization global wrappers (for templates.html onclick handlers)
function loadVisualization() {
    EdgeSelector.loadVisualization();
}

function resetView() {
    EdgeSelector.resetView();
}

function clearVizSelection() {
    EdgeSelector.clearVizSelection();
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => EdgeSelector.init());
} else {
    EdgeSelector.init();
}
