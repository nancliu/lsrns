/**
 * 方案XML验证核心模块
 *
 * 职责：
 * - 调用后端API进行XML验证
 * - 处理验证结果
 * - 协调UI更新和用户反馈
 *
 * 单一职责：业务逻辑，不直接操作DOM
 * 依赖：plan-validation-ui.js, ui-utils.js
 */

/**
 * 验证方案XML（后端API调用）
 * @param {string} planId - 方案ID
 * @returns {Promise<Object>} 验证结果
 */
async function validatePlanXMLAPI(planId) {
    const url = `/api/v1/control/plans/${planId}/generate_additional`;

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    return await response.json();
}

/**
 * 处理验证结果
 * @param {string} planId - 方案ID
 * @param {Object} result - API返回结果
 */
function handleValidationResult(planId, result) {
    const validation = result.validation;

    if (!validation) {
        throw new Error('API返回缺少validation字段');
    }

    if (validation.is_valid) {
        handleValidationSuccess(planId, validation.warnings);
    } else {
        handleValidationFailure(planId, validation.errors);
    }
}

/**
 * 处理验证成功
 * @param {string} planId - 方案ID
 * @param {Array} warnings - 警告列表
 */
function handleValidationSuccess(planId, warnings) {
    if (warnings && warnings.length > 0) {
        updateValidationStatus(planId, 'warning');
        showWarningModal(planId, warnings);
        showToast('warning', `验证通过，但有${warnings.length}个警告`);
    } else {
        updateValidationStatus(planId, 'success');
        showToast('success', 'XML验证通过');
    }
}

/**
 * 处理验证失败
 * @param {string} planId - 方案ID
 * @param {Array} errors - 错误列表
 */
function handleValidationFailure(planId, errors) {
    updateValidationStatus(planId, 'error');

    const errorMessage = errors && errors.length > 0
        ? errors.join('; ')
        : '验证失败';

    showToast('error', `验证失败: ${errorMessage}`);
}

/**
 * 主验证流程（协调器）
 * @param {string} planId - 方案ID
 */
async function validatePlan(planId) {
    try {
        setValidationLoading(planId, true);
        disableValidationButton(planId, true);

        const result = await validatePlanXMLAPI(planId);
        handleValidationResult(planId, result);

    } catch (error) {
        console.error('验证错误:', error);
        updateValidationStatus(planId, 'error');
        showToast('error', `验证失败: ${error.message}`);

    } finally {
        setValidationLoading(planId, false);
        disableValidationButton(planId, false);
    }
}
