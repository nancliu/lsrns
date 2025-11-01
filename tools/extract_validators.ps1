# PowerShell script to extract validation functions
# Phase 2 Task 2.3 - Extract validation functions

$filePath = "D:\projects\OD_SIM\frontend\control\js\parameter_form.js"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Task 2.3: 提取验证函数" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create backup
$backupPath = "$filePath.backup_task23_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item $filePath $backupPath
Write-Host "✅ 备份已创建: $backupPath" -ForegroundColor Green
Write-Host ""

# Read file content
$content = Get-Content $filePath -Raw

# ==================== Step 1: Insert Validators Object ====================
Write-Host "[Step 1] 插入统一的验证器对象..." -ForegroundColor Yellow

$validatorsCode = @'

// ==================== Validation Helpers ====================

/**
 * Unified validators for form inputs.
 * Provides consistent validation logic across all parameter types.
 */
const validators = {
  /**
   * Validate time order (begin < end).
   * @param {number} beginHours - Start time in hours
   * @param {number} endHours - End time in hours
   * @returns {{valid: boolean, message?: string}}
   */
  timeOrder: (beginHours, endHours) => {
    if (beginHours >= endHours) {
      return {
        valid: false,
        message: `开始时间(${beginHours}h)必须小于结束时间(${endHours}h)`
      };
    }
    return { valid: true };
  },

  /**
   * Validate time range (0-24 hours).
   * @param {number} hours - Time value in hours
   * @returns {{valid: boolean, message?: string}}
   */
  timeRange: (hours) => {
    if (hours < 0 || hours > 24) {
      return {
        valid: false,
        message: `时间必须在 0-24 小时范围内，当前值: ${hours}`
      };
    }
    return { valid: true };
  },

  /**
   * Validate speed range.
   * @param {number} speed - Speed value in km/h
   * @param {number} min - Minimum allowed speed (default: 0)
   * @param {number} max - Maximum allowed speed (default: 120)
   * @returns {{valid: boolean, message?: string}}
   */
  speedRange: (speed, min = 0, max = 120) => {
    if (speed < min || speed > max) {
      return {
        valid: false,
        message: `速度必须在 ${min}-${max} km/h 范围内，当前值: ${speed}`
      };
    }
    return { valid: true };
  },

  /**
   * Validate number range with custom constraints.
   * @param {number} value - Value to validate
   * @param {number} min - Minimum allowed value
   * @param {number} max - Maximum allowed value
   * @param {string} unit - Unit name for error message
   * @returns {{valid: boolean, message?: string}}
   */
  numberRange: (value, min, max, unit = '') => {
    if (value < min || value > max) {
      return {
        valid: false,
        message: `值必须在 ${min}-${max}${unit ? ' ' + unit : ''} 范围内，当前值: ${value}`
      };
    }
    return { valid: true };
  },

  /**
   * Validate required field.
   * @param {string|number} value - Value to validate
   * @returns {{valid: boolean, message?: string}}
   */
  required: (value) => {
    if (value === '' || value === null || value === undefined) {
      return {
        valid: false,
        message: '此字段为必填项'
      };
    }
    return { valid: true };
  },

  /**
   * Validate number format.
   * @param {string} value - String value to check
   * @returns {{valid: boolean, message?: string}}
   */
  isNumber: (value) => {
    if (value !== '' && isNaN(parseFloat(value))) {
      return {
        valid: false,
        message: '请输入有效的数字'
      };
    }
    return { valid: true };
  }
};

/**
 * Show error message on an input element.
 * @param {HTMLInputElement|HTMLSelectElement|HTMLTextAreaElement} input - Input element
 * @param {string} message - Error message to display
 */
function showError(input, message) {
  // Add error class to input
  input.classList.add('input-error');

  // Find or create feedback div
  const formGroup = input.closest('.form-group');
  if (!formGroup) return;

  let feedbackDiv = formGroup.querySelector('.parameter-feedback');
  if (!feedbackDiv) {
    feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'parameter-feedback';
    formGroup.appendChild(feedbackDiv);
  }

  // Set error message
  feedbackDiv.className = 'parameter-feedback error';
  feedbackDiv.textContent = message;
  feedbackDiv.dataset.feedback = 'error';
}

/**
 * Clear error message from an input element.
 * @param {HTMLInputElement|HTMLSelectElement|HTMLTextAreaElement} input - Input element
 */
function clearError(input) {
  // Remove error class from input
  input.classList.remove('input-error');

  // Clear feedback div
  const formGroup = input.closest('.form-group');
  if (!formGroup) return;

  const feedbackDiv = formGroup.querySelector('.parameter-feedback');
  if (feedbackDiv) {
    feedbackDiv.textContent = '';
    feedbackDiv.className = 'parameter-feedback';
    feedbackDiv.dataset.feedback = '';
  }
}

/**
 * Validate input on blur with automatic error display.
 * @param {HTMLInputElement} input - Input element to validate
 * @param {Function} validatorFn - Validator function that returns {valid, message}
 */
function validateOnBlur(input, validatorFn) {
  input.addEventListener('blur', () => {
    const result = validatorFn();
    if (!result.valid) {
      showError(input, result.message);
    } else {
      clearError(input);
    }
  });

  // Clear error on input (give user immediate feedback when correcting)
  input.addEventListener('input', () => {
    if (input.classList.contains('input-error')) {
      const result = validatorFn();
      if (result.valid) {
        clearError(input);
      }
    }
  });
}

// ==================== End Validation Helpers ====================

'@

# Insert validators before the first helper function (createTimeInput)
$pattern = 'function createTimeInput\(className, value = 0\) \{'
if ($content -match $pattern) {
    $content = $content -replace $pattern, ($validatorsCode + "`r`n" + $pattern)
    Write-Host "  ✅ 验证器对象已插入" -ForegroundColor Green
} else {
    Write-Host "  ❌ 未找到插入位置" -ForegroundColor Red
    exit 1
}

# ==================== Step 2: Update validateNumberRange to use validators ====================
Write-Host "[Step 2] 更新 validateNumberRange 使用统一验证器..." -ForegroundColor Yellow

# Find and update validateNumberRange function to use the new validators
$oldValidateNumberRange = @'
function validateNumberRange(input, schema) {
  const value = parseFloat(input.value);
  const feedbackDiv = input.closest('.form-group')?.querySelector('.parameter-feedback');

  if (!feedbackDiv) return true;

  // Clear previous feedback
  feedbackDiv.textContent = '';
  feedbackDiv.className = 'parameter-feedback';
  feedbackDiv.dataset.feedback = '';

  // Check if required
  if (input.value === '' && schema.required) {
    feedbackDiv.className = 'parameter-feedback error';
    feedbackDiv.textContent = '此字段为必填项';
    feedbackDiv.dataset.feedback = 'error';
    return false;
  }

  if (input.value === '') {
    return true; // Empty optional field is valid
  }

  if (isNaN(value)) {
    feedbackDiv.className = 'parameter-feedback error';
    feedbackDiv.textContent = '请输入有效的数字';
    feedbackDiv.dataset.feedback = 'error';
    return false;
  }

  const minVal = schema.min_value;
  const maxVal = schema.max_value;

  if (minVal !== undefined && value < minVal) {
    feedbackDiv.className = 'parameter-feedback error';
    feedbackDiv.textContent = `值不能小于 ${minVal}`;
    feedbackDiv.dataset.feedback = 'error';
    return false;
  }
'@

$newValidateNumberRange = @'
function validateNumberRange(input, schema) {
  const value = parseFloat(input.value);

  // Check if required (using unified validator)
  if (input.value === '' && schema.required) {
    const result = validators.required(input.value);
    if (!result.valid) {
      showError(input, result.message);
      return false;
    }
  }

  if (input.value === '') {
    clearError(input);
    return true; // Empty optional field is valid
  }

  // Check if valid number (using unified validator)
  const numResult = validators.isNumber(input.value);
  if (!numResult.valid) {
    showError(input, numResult.message);
    return false;
  }

  // Check range (using unified validator)
  const minVal = schema.min_value;
  const maxVal = schema.max_value;

  if (minVal !== undefined || maxVal !== undefined) {
    const rangeResult = validators.numberRange(
      value,
      minVal ?? -Infinity,
      maxVal ?? Infinity,
      schema.unit || ''
    );
    if (!rangeResult.valid) {
      showError(input, rangeResult.message);
      return false;
    }
  }

  clearError(input);
'@

$content = $content -replace [regex]::Escape($oldValidateNumberRange), $newValidateNumberRange

Write-Host "  ✅ validateNumberRange 已更新" -ForegroundColor Green

# ==================== Write back ====================
Write-Host ""
Write-Host "[保存] 写入修改后的文件..." -ForegroundColor Yellow
$content | Set-Content $filePath -NoNewline

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Task 2.3 完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "新增内容：" -ForegroundColor Cyan
Write-Host "  ✅ validators 对象（6个验证器）：" -ForegroundColor White
Write-Host "     - timeOrder" -ForegroundColor Gray
Write-Host "     - timeRange" -ForegroundColor Gray
Write-Host "     - speedRange" -ForegroundColor Gray
Write-Host "     - numberRange" -ForegroundColor Gray
Write-Host "     - required" -ForegroundColor Gray
Write-Host "     - isNumber" -ForegroundColor Gray
Write-Host "  ✅ 辅助函数（3个）：" -ForegroundColor White
Write-Host "     - showError(input, message)" -ForegroundColor Gray
Write-Host "     - clearError(input)" -ForegroundColor Gray
Write-Host "     - validateOnBlur(input, validatorFn)" -ForegroundColor Gray
Write-Host "  ✅ 更新现有函数：validateNumberRange" -ForegroundColor White
Write-Host ""
Write-Host "下一步：Task 2.4 - 添加代码分区注释" -ForegroundColor Magenta
Write-Host ""
