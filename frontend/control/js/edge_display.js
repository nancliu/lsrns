/**
 * Edge Display Table Component (Task 2.1)
 *
 * Displays comprehensive edge information in Step 3 of strategy creation workflow.
 * Features:
 * - Full edge details table with 10 columns
 * - Summary statistics (count, total length, routes, lane range)
 * - DHS-specific validations (continuity, lane count)
 * - No inline removal (simplified UX - users return to Step 2 to modify)
 *
 * @module edge_display
 */

class EdgeDisplayTable {
    /**
     * Constructor
     * @param {HTMLElement} containerEl - Container element for the table
     * @param {string} strategyType - Strategy type (VSS, DHS, TEC)
     */
    constructor(containerEl, strategyType) {
        this.container = containerEl;
        this.strategyType = strategyType;
        this.edges = [];
        this.validationIssues = [];
    }

    /**
     * Load and display edges from IDs
     * Task 2.1: Fetch full edge details and render table
     *
     * @param {Array<string>} edgeIds - Edge IDs to display
     */
    async loadEdges(edgeIds) {
        if (!edgeIds || edgeIds.length === 0) {
            this.renderNoEdgesMessage();
            return;
        }

        try {
            console.log(`[EdgeDisplayTable] Loading ${edgeIds.length} edges...`);

            // Fetch full edge information from backend
            const response = await fetch('/api/v1/control/edges/batch-info', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({edge_ids: edgeIds})
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch edge info: ${response.statusText}`);
            }

            this.edges = await response.json();
            console.log(`[EdgeDisplayTable] Loaded ${this.edges.length} edges`);

            this.render();
            this.checkValidation();

        } catch (error) {
            console.error('[EdgeDisplayTable] Error loading edges:', error);
            this.renderError(error.message);
        }
    }

    /**
     * Main render function
     * Task 2.1: Render complete edge table
     */
    render() {
        this.container.innerHTML = '';

        // Render summary statistics
        const summaryEl = this.renderSummary();
        this.container.appendChild(summaryEl);

        // Render validation warnings/errors if any
        if (this.validationIssues.length > 0) {
            const validationEl = this.renderValidationIssues();
            this.container.appendChild(validationEl);
        }

        // Render table
        const tableEl = this.renderTable();
        this.container.appendChild(tableEl);

        // Add note about modification
        const noteEl = document.createElement('div');
        noteEl.className = 'edge-table-note';
        noteEl.innerHTML = '<em>如需修改路段选择，请返回第2步</em>';
        this.container.appendChild(noteEl);
    }

    /**
     * Render summary statistics
     * Task 2.2: Edge summary statistics
     *
     * @returns {HTMLElement} Summary element
     */
    renderSummary() {
        const summary = document.createElement('div');
        summary.className = 'edge-summary';

        const totalLength = this.edges.reduce((sum, e) => sum + (e.length_m || 0), 0) / 1000;
        const routes = [...new Set(this.edges.map(e => e.route_code))].filter(r => r);
        const laneCounts = this.edges.map(e => e.lane_count || 0).filter(l => l > 0);
        const laneRange = laneCounts.length > 0 ? {
            min: Math.min(...laneCounts),
            max: Math.max(...laneCounts)
        } : {min: 0, max: 0};

        summary.innerHTML = `
            <div class="summary-grid">
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
                    <span class="summary-value">${routes.length > 0 ? routes.join(', ') : 'N/A'}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">车道数范围</span>
                    <span class="summary-value">${laneRange.min}-${laneRange.max} 车道</span>
                </div>
            </div>
        `;

        return summary;
    }

    /**
     * Render validation issues (warnings/errors)
     *
     * @returns {HTMLElement} Validation issues element
     */
    renderValidationIssues() {
        const container = document.createElement('div');
        container.className = 'validation-issues';

        for (const issue of this.validationIssues) {
            const issueEl = document.createElement('div');
            issueEl.className = `validation-${issue.type}`;

            const icon = issue.type === 'error' ? '❌' : '⚠️';
            issueEl.innerHTML = `
                <div class="validation-header">
                    ${icon} ${issue.message}
                </div>
                ${issue.details ? `<div class="validation-details">${issue.details.join('<br>')}</div>` : ''}
                ${issue.note ? `<div class="validation-note"><em>${issue.note}</em></div>` : ''}
            `;

            container.appendChild(issueEl);
        }

        return container;
    }

    /**
     * Render main edge table
     * Task 2.1: Comprehensive edge information table
     *
     * @returns {HTMLElement} Table element
     */
    renderTable() {
        const tableWrapper = document.createElement('div');
        tableWrapper.className = 'edge-table-wrapper';

        const table = document.createElement('table');
        table.className = 'edge-table';

        // Header
        const thead = document.createElement('thead');
        thead.innerHTML = `
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
            </tr>
        `;
        table.appendChild(thead);

        // Body
        const tbody = document.createElement('tbody');

        // Sort by stake order
        const sortedEdges = [...this.edges].sort((a, b) => {
            return (a.start_stake || 0) - (b.start_stake || 0);
        });

        sortedEdges.forEach((edge, index) => {
            const row = this.renderEdgeRow(edge, index + 1);
            tbody.appendChild(row);
        });

        table.appendChild(tbody);
        tableWrapper.appendChild(table);

        // Add pagination if needed (>20 edges)
        if (this.edges.length > 20) {
            const pagination = this.renderPagination();
            tableWrapper.appendChild(pagination);
        }

        return tableWrapper;
    }

    /**
     * Render single edge row
     *
     * @param {Object} edge - Edge data
     * @param {number} index - Row index
     * @returns {HTMLElement} Table row element
     */
    renderEdgeRow(edge, index) {
        const row = document.createElement('tr');
        row.className = 'edge-row';
        row.dataset.edgeId = edge.edge_id;

        // Format stake numbers as K10+200 format
        const formatStake = (stake) => {
            if (!stake) return 'N/A';
            const km = Math.floor(stake / 1000);
            const m = stake % 1000;
            return `K${km}+${m.toString().padStart(3, '0')}`;
        };

        // Translate direction to Chinese
        const translateDirection = (dir) => {
            const translations = {
                'upstream': '上行',
                'downstream': '下行',
                'clockwise': '顺时针',
                'counterclockwise': '逆时针'
            };
            return translations[dir] || dir || 'N/A';
        };

        row.innerHTML = `
            <td>${index}</td>
            <td class="edge-id">${edge.edge_id || 'N/A'}</td>
            <td>${edge.route_code || 'N/A'}</td>
            <td>${edge.section_code || 'N/A'}</td>
            <td>${formatStake(edge.start_stake)}</td>
            <td>${formatStake(edge.end_stake)}</td>
            <td>${edge.length_m ? edge.length_m.toFixed(0) + 'm' : 'N/A'}</td>
            <td>${edge.lane_count || 'N/A'}</td>
            <td>${translateDirection(edge.direction)}</td>
            <td>${edge.node_type || 'N/A'}</td>
        `;

        return row;
    }

    /**
     * Render pagination controls (for >20 edges)
     *
     * @returns {HTMLElement} Pagination element
     */
    renderPagination() {
        const pagination = document.createElement('div');
        pagination.className = 'edge-table-pagination';
        pagination.innerHTML = '<em>显示所有路段（分页功能待实现）</em>';
        return pagination;
    }

    /**
     * Render no edges message
     */
    renderNoEdgesMessage() {
        this.container.innerHTML = `
            <div class="edge-table-empty">
                <p>未选择路段</p>
                <p><em>请返回第2步选择路段</em></p>
            </div>
        `;
    }

    /**
     * Render error message
     *
     * @param {string} message - Error message
     */
    renderError(message) {
        this.container.innerHTML = `
            <div class="edge-table-error">
                <p>❌ 加载路段信息失败</p>
                <p>${message}</p>
            </div>
        `;
    }

    /**
     * Check validation rules
     * Task 2.3 & 2.4: DHS validation
     */
    checkValidation() {
        this.validationIssues = [];

        if (this.strategyType !== 'DHS') {
            return; // Only validate for DHS
        }

        // Task 2.4: Validate lane count ≥ 4 for DHS
        const invalidLaneEdges = this.edges.filter(e => (e.lane_count || 0) < 4);
        if (invalidLaneEdges.length > 0) {
            this.validationIssues.push({
                type: 'error',
                message: 'DHS策略要求车道数≥4，以下路段不符合:',
                details: invalidLaneEdges.map(e => `${e.edge_id} (${e.lane_count}车道)`),
                note: '请返回第2步重新选择符合要求的路段'
            });
        }

        // Task 2.3: Check edge continuity for DHS
        const discontinuities = this.checkEdgeContinuity();
        if (discontinuities.length > 0) {
            this.validationIssues.push({
                type: 'warning',
                message: '警告：所选路段不连续，DHS策略可能效果降低',
                details: discontinuities,
                note: '如需调整路段选择，请返回第2步'
            });
        }
    }

    /**
     * Check edge continuity (for DHS)
     * Task 2.3: DHS edge continuity validation
     *
     * @returns {Array<string>} List of discontinuity descriptions
     */
    checkEdgeContinuity() {
        const gaps = [];
        const sorted = [...this.edges].sort((a, b) =>
            (a.start_stake || 0) - (b.start_stake || 0)
        );

        const tolerance = 50; // 50m tolerance for continuity

        for (let i = 0; i < sorted.length - 1; i++) {
            const current = sorted[i];
            const next = sorted[i + 1];

            const currentEnd = current.end_stake || 0;
            const nextStart = next.start_stake || 0;

            if (currentEnd + tolerance < nextStart) {
                const gapSize = nextStart - currentEnd;
                const formatKm = (m) => `K${(m / 1000).toFixed(1)}`;
                gaps.push(`${formatKm(currentEnd)} 到 ${formatKm(nextStart)} 之间存在 ${gapSize}m 间隙`);
            }
        }

        return gaps;
    }

    /**
     * Get validation status
     *
     * @returns {Object} Validation status {valid: boolean, errors: number, warnings: number}
     */
    getValidationStatus() {
        const errors = this.validationIssues.filter(i => i.type === 'error').length;
        const warnings = this.validationIssues.filter(i => i.type === 'warning').length;

        return {
            valid: errors === 0,
            errors: errors,
            warnings: warnings,
            issues: this.validationIssues
        };
    }

    /**
     * Export edge list to CSV
     * (Feature for future enhancement)
     */
    exportToCSV() {
        const headers = [
            'Edge ID', '路线代码', '路段代码', '起始桩号', '结束桩号',
            '长度', '车道数', '方向', '节点类型'
        ];

        const rows = this.edges.map(e => [
            e.edge_id || '',
            e.route_code || '',
            e.section_code || '',
            e.start_stake || '',
            e.end_stake || '',
            e.length_m || '',
            e.lane_count || '',
            e.direction || '',
            e.node_type || ''
        ]);

        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.join(','))
        ].join('\n');

        const blob = new Blob([csvContent], {type: 'text/csv;charset=utf-8;'});
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `strategy_${Date.now()}_edges.csv`;
        link.click();

        console.log('[EdgeDisplayTable] Exported edge list to CSV');
    }
}

// Export for use in other modules
window.EdgeDisplayTable = EdgeDisplayTable;
