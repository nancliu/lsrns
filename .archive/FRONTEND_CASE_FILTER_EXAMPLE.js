/**
 * 案例过滤和类型管理 - Frontend Implementation Example
 *
 * 这个文件演示如何在前端实现案例类型过滤，
 * 确保用户在不同的工作流中只看到兼容的案例
 *
 * Date: 2025-11-12
 * Phase: 2 (Case Isolation)
 */

// ============================================================================
// UTILITY FUNCTIONS - 工具函数
// ============================================================================

/**
 * 案例类型枚举
 */
const CASE_SOURCE_TYPE = {
    OD_EXTRACTION: 'od_extraction',
    EVENT_SCENARIO: 'event_scenario'
};

/**
 * 工作流类型枚举
 */
const WORKFLOW_TYPE = {
    BATCH_OPTIMIZATION: 'batch_optimization',        // 管控方案优化
    BATCH_SIMULATION: 'batch_simulation',            // 批量仿真（OD提取）
    EVENT_SCENARIO_ANALYSIS: 'event_scenario_analysis', // 事件场景分析
    CONTROL_PLAN: 'control_plan'                    // 控制方案
};

/**
 * 定义每个工作流支持的案例类型
 */
const WORKFLOW_CASE_COMPATIBILITY = {
    [WORKFLOW_TYPE.BATCH_OPTIMIZATION]: [
        CASE_SOURCE_TYPE.OD_EXTRACTION  // 仅支持OD提取案例
    ],
    [WORKFLOW_TYPE.BATCH_SIMULATION]: [
        CASE_SOURCE_TYPE.OD_EXTRACTION
    ],
    [WORKFLOW_TYPE.EVENT_SCENARIO_ANALYSIS]: [
        CASE_SOURCE_TYPE.EVENT_SCENARIO // 仅支持事件场景案例
    ],
    [WORKFLOW_TYPE.CONTROL_PLAN]: [
        CASE_SOURCE_TYPE.OD_EXTRACTION
    ]
};

/**
 * 获取工作流支持的案例类型
 *
 * @param {string} workflowType - 工作流类型
 * @returns {string[]} - 支持的案例类型列表
 */
function getSupportedCaseTypes(workflowType) {
    return WORKFLOW_CASE_COMPATIBILITY[workflowType] || [];
}

/**
 * 检查案例是否与工作流兼容
 *
 * @param {Object} caseData - 案例数据 {case_id, source_type, ...}
 * @param {string} workflowType - 工作流类型
 * @returns {boolean} - 是否兼容
 */
function isCaseCompatibleWithWorkflow(caseData, workflowType) {
    const caseSourceType = caseData.source_type || CASE_SOURCE_TYPE.OD_EXTRACTION;
    const supportedTypes = getSupportedCaseTypes(workflowType);
    return supportedTypes.includes(caseSourceType);
}

/**
 * 过滤案例列表，仅返回与工作流兼容的案例
 *
 * @param {Object[]} allCases - 所有案例列表
 * @param {string} workflowType - 工作流类型
 * @returns {Object[]} - 过滤后的案例列表
 */
function filterCasesByWorkflow(allCases, workflowType) {
    return allCases.filter(caseData =>
        isCaseCompatibleWithWorkflow(caseData, workflowType)
    );
}

/**
 * 获取案例类型的中文描述
 *
 * @param {string} sourceType - 案例源类型
 * @returns {string} - 中文描述
 */
function getCaseTypeDescription(sourceType) {
    const descriptions = {
        [CASE_SOURCE_TYPE.OD_EXTRACTION]: 'OD提取案例',
        [CASE_SOURCE_TYPE.EVENT_SCENARIO]: '事件场景案例'
    };
    return descriptions[sourceType] || '未知案例类型';
}

/**
 * 获取工作流的中文描述
 *
 * @param {string} workflowType - 工作流类型
 * @returns {string} - 中文描述
 */
function getWorkflowDescription(workflowType) {
    const descriptions = {
        [WORKFLOW_TYPE.BATCH_OPTIMIZATION]: '管控方案优化',
        [WORKFLOW_TYPE.BATCH_SIMULATION]: '批量仿真',
        [WORKFLOW_TYPE.EVENT_SCENARIO_ANALYSIS]: '事件场景分析',
        [WORKFLOW_TYPE.CONTROL_PLAN]: '控制方案'
    };
    return descriptions[workflowType] || '未知工作流';
}

// ============================================================================
// UI UPDATE FUNCTIONS - UI更新函数
// ============================================================================

/**
 * 更新案例选择器的案例列表（主动过滤）
 *
 * 这是推荐的方法：在UI中就过滤掉不兼容的案例，
 * 用户看不到他们无法选择的案例
 *
 * @param {string} workflowType - 当前工作流类型
 * @param {Object[]} allCases - 所有可用案例
 */
async function updateCaseSelectorWithFiltering(workflowType, allCases) {
    const caseSelector = document.getElementById('caseSelect');

    if (!caseSelector) {
        console.warn('Case selector not found');
        return;
    }

    // 过滤案例
    const compatibleCases = filterCasesByWorkflow(allCases, workflowType);

    // 清空现有选项
    caseSelector.innerHTML = '<option value="">-- 选择案例 --</option>';

    if (compatibleCases.length === 0) {
        const option = document.createElement('option');
        option.disabled = true;
        option.textContent = `没有${getWorkflowDescription(workflowType)}的案例`;
        caseSelector.appendChild(option);
        console.warn(`No compatible cases for workflow: ${workflowType}`);
        return;
    }

    // 添加兼容的案例
    compatibleCases.forEach(caseData => {
        const option = document.createElement('option');
        option.value = caseData.case_id;
        option.textContent = `${caseData.case_name || caseData.case_id}`;
        option.dataset.sourceType = caseData.source_type || CASE_SOURCE_TYPE.OD_EXTRACTION;
        caseSelector.appendChild(option);
    });

    console.log(`✓ Case selector updated: ${compatibleCases.length} compatible cases`);
}

/**
 * 显示案例不兼容警告
 *
 * 这个函数在用户选择了不兼容的案例时调用
 *
 * @param {string} caseId - 案例ID
 * @param {string} caseSourceType - 案例源类型
 * @param {string} workflowType - 当前工作流类型
 */
function showCaseIncompatibilityWarning(caseId, caseSourceType, workflowType) {
    const title = '不支持的案例类型';
    const message = `
选中的案例 "${caseId}" 是${getCaseTypeDescription(caseSourceType)}，
不支持当前工作流"${getWorkflowDescription(workflowType)}"。

请选择以下案例类型之一：
${getSupportedCaseTypes(workflowType)
    .map(type => `• ${getCaseTypeDescription(type)}`)
    .join('\n')}
    `;

    // 显示警告（根据前端框架调整）
    if (typeof alert !== 'undefined') {
        alert(`${title}\n\n${message}`);
    } else {
        console.error(title, message);
    }
}

/**
 * 显示案例信息标签
 *
 * 在案例选择器下方显示当前选中案例的信息
 *
 * @param {string} caseId - 案例ID
 * @param {string} caseSourceType - 案例源类型
 * @param {string} workflowType - 当前工作流类型
 */
function showCaseInfoBadge(caseId, caseSourceType, workflowType) {
    const badge = document.getElementById('caseInfoBadge');
    if (!badge) return;

    const isCompatible = isCaseCompatibleWithWorkflow(
        { case_id: caseId, source_type: caseSourceType },
        workflowType
    );

    const caseTypeColor = caseSourceType === CASE_SOURCE_TYPE.OD_EXTRACTION
        ? 'badge-primary'
        : 'badge-info';

    const compatibilityColor = isCompatible ? 'badge-success' : 'badge-danger';

    badge.innerHTML = `
        <span class="badge ${caseTypeColor}">${getCaseTypeDescription(caseSourceType)}</span>
        <span class="badge ${compatibilityColor}">
            ${isCompatible ? '✓ 兼容' : '✗ 不兼容'}
        </span>
    `;
}

// ============================================================================
// EVENT HANDLERS - 事件处理
// ============================================================================

/**
 * 当工作流类型改变时的处理函数
 *
 * 根据新的工作流类型重新过滤案例列表
 */
async function handleWorkflowChanged(newWorkflowType) {
    console.log(`Workflow changed to: ${newWorkflowType}`);

    try {
        // 加载所有案例
        const allCases = await apiClient.listCases();

        // 根据新工作流过滤案例
        await updateCaseSelectorWithFiltering(newWorkflowType, allCases);

        // 重置case选择
        const caseSelector = document.getElementById('caseSelect');
        if (caseSelector) {
            caseSelector.value = '';
        }

    } catch (error) {
        console.error('Failed to update cases:', error);
        showErrorAlert('加载案例失败', error.message);
    }
}

/**
 * 当选择案例时的处理函数
 *
 * 检查案例是否与当前工作流兼容
 */
async function handleCaseSelected(caseId, allCases, currentWorkflowType) {
    if (!caseId) return;

    console.log(`Case selected: ${caseId}`);

    try {
        // 找到选中的案例
        const selectedCase = allCases.find(c => c.case_id === caseId);
        if (!selectedCase) {
            console.error(`Case not found: ${caseId}`);
            return;
        }

        const caseSourceType = selectedCase.source_type || CASE_SOURCE_TYPE.OD_EXTRACTION;

        // 检查兼容性
        const isCompatible = isCaseCompatibleWithWorkflow(selectedCase, currentWorkflowType);

        // 显示案例信息
        showCaseInfoBadge(caseId, caseSourceType, currentWorkflowType);

        if (!isCompatible) {
            // 显示警告
            showCaseIncompatibilityWarning(caseId, caseSourceType, currentWorkflowType);

            // 重置选择
            const caseSelector = document.getElementById('caseSelect');
            if (caseSelector) {
                caseSelector.value = '';
            }
            return;
        }

        // 案例兼容，继续加载时长等信息
        if (currentWorkflowType === WORKFLOW_TYPE.BATCH_OPTIMIZATION) {
            await loadCaseDuration(caseId);
        }

    } catch (error) {
        console.error('Failed to process case selection:', error);
        showErrorAlert('案例选择失败', error.message);
    }
}

/**
 * 加载案例仿真时长（带错误处理）
 *
 * @param {string} caseId - 案例ID
 */
async function loadCaseDuration(caseId) {
    try {
        const duration = await apiClient.getCaseDuration(caseId);
        updateDurationDisplay(duration);
        console.log(`✓ Case duration loaded: ${duration.display_text}`);

    } catch (error) {
        if (error.response?.status === 400) {
            const detail = error.response.data.detail;

            // 检查是否是案例不兼容错误
            if (detail.error === 'INCOMPATIBLE_CASE_TYPE') {
                showCaseIncompatibilityWarning(
                    caseId,
                    detail.case_type,
                    WORKFLOW_TYPE.BATCH_OPTIMIZATION
                );

                // 重置case选择
                const caseSelector = document.getElementById('caseSelect');
                if (caseSelector) {
                    caseSelector.value = '';
                }
                return;
            }
        }

        console.error('Failed to load case duration:', error);
        showErrorAlert('加载案例时长失败', error.message);
    }
}

/**
 * 更新仿真时长显示
 */
function updateDurationDisplay(duration) {
    const durationDisplay = document.getElementById('durationDisplay');
    if (durationDisplay) {
        durationDisplay.textContent = duration.display_text ||
            `${duration.duration_hours}小时${duration.duration_minutes}分钟`;
    }
}

// ============================================================================
// INITIALIZATION - 初始化
// ============================================================================

/**
 * 初始化案例选择器和工作流管理
 *
 * 调用这个函数来启动案例隔离功能
 */
async function initializeCaseManagement() {
    console.log('Initializing case management...');

    try {
        // 加载所有案例
        const allCases = await apiClient.listCases();
        console.log(`✓ Loaded ${allCases.length} cases`);

        // 获取当前工作流类型
        const workflowSelector = document.getElementById('workflowType');
        const currentWorkflow = workflowSelector?.value || WORKFLOW_TYPE.BATCH_OPTIMIZATION;

        // 初始化案例选择器
        await updateCaseSelectorWithFiltering(currentWorkflow, allCases);

        // 绑定工作流改变事件
        if (workflowSelector) {
            workflowSelector.addEventListener('change', (e) => {
                handleWorkflowChanged(e.target.value);
            });
        }

        // 绑定案例选择事件
        const caseSelector = document.getElementById('caseSelect');
        if (caseSelector) {
            caseSelector.addEventListener('change', (e) => {
                handleCaseSelected(e.target.value, allCases, currentWorkflow);
            });
        }

        console.log('✓ Case management initialized');

    } catch (error) {
        console.error('Failed to initialize case management:', error);
        showErrorAlert('初始化失败', error.message);
    }
}

// ============================================================================
// EXPORTS (如果使用模块系统)
// ============================================================================

// export {
//     CASE_SOURCE_TYPE,
//     WORKFLOW_TYPE,
//     filterCasesByWorkflow,
//     isCaseCompatibleWithWorkflow,
//     getCaseTypeDescription,
//     initializeCaseManagement
// };
