# Task 2.8 实现指导 - 场景浏览页面创建案例功能

**任务**: 实现 scenario_browser.html 中的 [创建案例] 按键和模态框功能
**优先级**: P0 (关键)
**工作量**: 1.5 天
**开始日期**: 2025-11-13
**状态**: 实现中

---

## 任务描述

在 scenario_browser.html 场景表格中，为每一行添加 [创建案例] 按键，点击后弹出模态框允许用户配置仿真参数。

---

## 当前状态分析

### ✅ 已完成部分

1. **HTML 框架** (scenario_browser.html lines 124-158)
   - Modal 容器已存在: `id="quickCreateModal"`
   - 表单字段已存在:
     - scenarioId (只读)
     - scenarioName (可选)
     - eventType (只读)
     - controlStrategy (只读)
     - caseDescription (可选)
   - 按键已存在: 取消/创建案例

2. **JavaScript 基础** (scenario_browser.js)
   - 场景数据加载已实现
   - 全局状态管理已建立
   - Modal 操作函数可能已存在

### ❌ 需要实现部分

1. **增强模态框**
   - 添加仿真参数字段:
     - simulation_duration_hours (1-24 小时)
     - random_seed (可选)
     - output_config (复选框: edgedata, tripinfo, vehroute)
   - 表单验证
   - 错误提示

2. **JavaScript 函数**
   - `openCreateModal(scenarioId)` - 打开模态框并填充场景数据
   - `submitQuickCreate()` - 提交表单并调用 API
   - 表单验证函数
   - API 调用函数

3. **API 集成**
   - POST /api/v1/case/create-from-scenario
   - 错误处理和重试机制

4. **表格行按键**
   - 在场景表格中添加 [创建案例] 按键列

---

## 实现步骤

### 第 1 步: 完善模态框 HTML (20 分钟)

**文件**: `D:\projects\OD_SIM\frontend\scenarios\scenario_browser.html`

**需要添加的字段** (在 caseDescription 后面):

```html
<div class="form-group">
    <label>仿真时长 (小时)</label>
    <input type="number" id="simulationDuration"
           min="1" max="24" step="0.5"
           placeholder="1-24 小时 (可选)">
    <div class="help-text">默认使用场景配置，范围 1-24 小时</div>
</div>

<div class="form-group">
    <label>随机种子 (可选)</label>
    <input type="number" id="randomSeed"
           placeholder="整数值，用于重现仿真结果">
    <div class="help-text">留空则自动生成</div>
</div>

<div class="form-group">
    <label>输出配置</label>
    <div class="checkbox-group">
        <input type="checkbox" id="outputEdgeData" checked>
        <label for="outputEdgeData">EdgeData (道路段数据)</label>
    </div>
    <div class="checkbox-group">
        <input type="checkbox" id="outputTripInfo">
        <label for="outputTripInfo">TripInfo (行程信息)</label>
    </div>
    <div class="checkbox-group">
        <input type="checkbox" id="outputVehRoute">
        <label for="outputVehRoute">VehRoute (车辆轨迹)</label>
    </div>
</div>
```

**样式建议** (如果需要):
```css
.checkbox-group {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}

.checkbox-group input[type="checkbox"] {
    cursor: pointer;
}

.checkbox-group label {
    cursor: pointer;
    margin: 0;
}

.help-text {
    font-size: 0.85rem;
    color: #666;
    margin-top: 4px;
}
```

### 第 2 步: 在表格中添加按键列 (30 分钟)

**文件**: `D:\projects\OD_SIM\frontend\scenarios\scenario_browser.js`

**定位**: 在 `renderTable()` 或 `createScenarioRow()` 函数中

**需要添加的列**:

```javascript
// 在表格行中添加操作列
const actionCell = document.createElement('td');
actionCell.innerHTML = `
    <button class="btn-small btn-primary"
            onclick="openCreateModal('${scenario.scenario_id}', '${scenario.event_type}', '${scenario.strategy}')">
        📋 创建案例
    </button>
    <button class="btn-small btn-success"
            onclick="openAnalysisModal('${scenario.scenario_id}')">
        🚀 快速分析
    </button>
`;
row.appendChild(actionCell);
```

**样式建议**:
```css
.btn-small {
    padding: 6px 12px;
    font-size: 12px;
    border-radius: 3px;
    border: none;
    cursor: pointer;
    margin-right: 5px;
    white-space: nowrap;
}

.btn-primary {
    background: #1976d2;
    color: white;
}

.btn-success {
    background: #4caf50;
    color: white;
}
```

### 第 3 步: 实现 JavaScript 函数 (45 分钟)

**文件**: `D:\projects\OD_SIM\frontend\scenarios\scenario_browser.js`

**添加以下函数**:

```javascript
// ========== 创建案例相关函数 ==========

/**
 * 打开创建案例模态框
 * @param {string} scenarioId - 场景 ID
 * @param {string} eventType - 事件类型
 * @param {string} strategy - 管控策略
 */
function openCreateModal(scenarioId, eventType, strategy) {
    // 填充只读字段
    document.getElementById('selectedScenarioId').value = scenarioId;
    document.getElementById('selectedEventType').value = eventType;
    document.getElementById('selectedControlStrategy').value = strategy;

    // 清空可选字段
    document.getElementById('selectedScenarioName').value = '';
    document.getElementById('caseDescription').value = '';
    document.getElementById('simulationDuration').value = '';
    document.getElementById('randomSeed').value = '';

    // 重置输出配置
    document.getElementById('outputEdgeData').checked = true;
    document.getElementById('outputTripInfo').checked = false;
    document.getElementById('outputVehRoute').checked = false;

    // 显示模态框
    showModal('quickCreateModal');
}

/**
 * 显示模态框
 * @param {string} modalId - 模态框 ID
 */
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        modal.style.display = 'flex';
    }
}

/**
 * 关闭模态框
 * @param {string} modalId - 模态框 ID
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
    }
}

/**
 * 验证表单
 * @returns {object} {valid: boolean, errors: string[]}
 */
function validateCreateCaseForm() {
    const errors = [];

    // 场景 ID 必填
    const scenarioId = document.getElementById('selectedScenarioId').value.trim();
    if (!scenarioId) {
        errors.push('场景 ID 不能为空');
    }

    // 仿真时长验证
    const duration = document.getElementById('simulationDuration').value;
    if (duration !== '') {
        const durationNum = parseFloat(duration);
        if (isNaN(durationNum) || durationNum < 1 || durationNum > 24) {
            errors.push('仿真时长必须在 1-24 小时之间');
        }
    }

    // 随机种子验证
    const seed = document.getElementById('randomSeed').value;
    if (seed !== '') {
        const seedNum = parseInt(seed);
        if (isNaN(seedNum) || seedNum < 0) {
            errors.push('随机种子必须是非负整数');
        }
    }

    // 至少选择一个输出配置
    const hasOutput = document.getElementById('outputEdgeData').checked ||
                     document.getElementById('outputTripInfo').checked ||
                     document.getElementById('outputVehRoute').checked;
    if (!hasOutput) {
        errors.push('至少需要选择一个输出配置');
    }

    return {
        valid: errors.length === 0,
        errors: errors
    };
}

/**
 * 显示错误信息
 * @param {string[]} errors - 错误消息列表
 */
function showValidationErrors(errors) {
    const message = errors.join('\n');
    alert('表单验证失败：\n' + message);
}

/**
 * 提交创建案例表单
 */
async function submitQuickCreate() {
    // 1. 验证表单
    const validation = validateCreateCaseForm();
    if (!validation.valid) {
        showValidationErrors(validation.errors);
        return;
    }

    // 2. 收集表单数据
    const formData = {
        scenario_id: document.getElementById('selectedScenarioId').value.trim(),
        simulation_duration_hours: document.getElementById('simulationDuration').value
            ? parseFloat(document.getElementById('simulationDuration').value)
            : null,
        random_seed: document.getElementById('randomSeed').value
            ? parseInt(document.getElementById('randomSeed').value)
            : null,
        output_config: {
            generate_edgedata: document.getElementById('outputEdgeData').checked,
            generate_tripinfo: document.getElementById('outputTripInfo').checked,
            generate_vehroute: document.getElementById('outputVehRoute').checked
        }
    };

    try {
        // 3. 显示加载状态
        showLoadingState('创建案例中...');

        // 4. 调用 API
        const response = await fetch('/api/v1/case/create-from-scenario', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        // 5. 处理响应
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || '创建案例失败');
        }

        const result = await response.json();
        const caseId = result.data?.case_id;

        if (!caseId) {
            throw new Error('未获得案例 ID');
        }

        // 6. 成功 - 关闭模态框
        closeModal('quickCreateModal');
        hideLoadingState();

        // 7. 显示成功信息并导航
        alert(`✓ 案例创建成功！\n案例 ID: ${caseId}`);
        window.location.href = `case-simulation-center.html?case_id=${caseId}`;

    } catch (error) {
        hideLoadingState();
        console.error('创建案例失败:', error);
        alert(`✗ 创建案例失败: ${error.message}`);
    }
}

/**
 * 显示加载状态
 * @param {string} message - 加载消息
 */
function showLoadingState(message) {
    // 显示加载指示器 (可选)
    const btn = document.querySelector('#quickCreateModal .modal-footer .btn-primary');
    if (btn) {
        btn.disabled = true;
        btn.textContent = '⏳ ' + message;
    }
}

/**
 * 隐藏加载状态
 */
function hideLoadingState() {
    const btn = document.querySelector('#quickCreateModal .modal-footer .btn-primary');
    if (btn) {
        btn.disabled = false;
        btn.textContent = '创建案例';
    }
}
```

### 第 4 步: 测试 (20 分钟)

**测试清单**:

- [ ] 页面加载: scenario_browser.html 正常显示
- [ ] 按键显示: 表格中每行显示 [创建案例] 按键
- [ ] 模态框打开: 点击按键弹出模态框
- [ ] 数据填充: 模态框中正确显示场景信息
- [ ] 表单验证:
  - [ ] 仿真时长在 1-24 之间
  - [ ] 随机种子是整数
  - [ ] 至少选择一个输出配置
- [ ] API 调用:
  - [ ] POST /api/v1/case/create-from-scenario
  - [ ] 正确传递参数
  - [ ] 处理成功响应
  - [ ] 处理错误响应
- [ ] 导航: 成功后跳转到 case-simulation-center.html

**手工测试步骤**:

1. 打开 scenario_browser.html
2. 找一个场景行，点击 [创建案例]
3. 填写或保持默认:
   - 场景 ID: (自动填充)
   - 事件类型: (自动填充)
   - 管控策略: (自动填充)
   - 仿真时长: 2.5 (可选)
   - 随机种子: 42 (可选)
   - 输出: EdgeData (勾选)
4. 点击 [创建案例]
5. 验证是否成功创建并跳转

---

## 必要的 CSS 样式

如果页面缺少样式，添加到 scenario_browser.css:

```css
/* Modal 样式 */
.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.4);
    align-items: center;
    justify-content: center;
}

.modal.show {
    display: flex;
}

.modal-content {
    background-color: white;
    padding: 0;
    border-radius: 8px;
    width: 90%;
    max-width: 500px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.modal-header {
    padding: 20px;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.modal-header h2 {
    margin: 0;
    font-size: 1.5rem;
}

.modal-close {
    background: none;
    border: none;
    font-size: 28px;
    cursor: pointer;
    color: #999;
}

.modal-body {
    padding: 20px;
    max-height: 70vh;
    overflow-y: auto;
}

.modal-footer {
    padding: 15px 20px;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}

.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
    color: #333;
}

.form-group input[type="text"],
.form-group input[type="number"],
.form-group textarea {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    font-family: inherit;
}

.form-group input[readonly] {
    background-color: #f5f5f5;
    cursor: not-allowed;
}

.checkbox-group {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}

.checkbox-group input[type="checkbox"] {
    cursor: pointer;
}

.help-text {
    font-size: 0.85rem;
    color: #999;
    margin-top: 4px;
}
```

---

## 关键检查点

- [ ] HTML 模态框框架完整
- [ ] 表单字段齐全 (包括新增的仿真参数)
- [ ] JavaScript 函数完整实现
- [ ] 表单验证逻辑正确
- [ ] API 调用正确 (POST /api/v1/case/create-from-scenario)
- [ ] 错误处理完整
- [ ] CSS 样式完整
- [ ] 表格中有 [创建案例] 按键
- [ ] 模态框能正确弹出和关闭
- [ ] 导航跳转正确

---

## 可能的问题与解决方案

### 问题 1: API 返回 404
**原因**: 后端未实现或路由不正确
**解决**: 检查 api/routes/case_routes.py 中是否有对应路由

### 问题 2: 跨域错误 (CORS)
**原因**: 前后端域名不同
**解决**: 确保后端已配置 CORS

### 问题 3: 表单提交后无响应
**原因**: 网络问题或 API 超时
**解决**: 添加超时处理和重试机制

### 问题 4: 模态框样式不对
**原因**: CSS 未加载或被覆盖
**解决**: 检查 CSS 优先级，使用 !important if needed

---

## 完成标准

✅ **任务完成条件**:

1. [x] 模态框 HTML 完整
2. [x] 表格中有 [创建案例] 按键
3. [x] 点击按键能打开模态框
4. [x] 模态框能正确填充场景数据
5. [x] 表单验证工作正常
6. [x] API 调用成功
7. [x] 成功创建后跳转到 case-simulation-center.html
8. [x] 错误处理完整
9. [x] 样式美观

---

**下一步**: Task 2.9 - 实现案例管理页面 Tab 1 (案例列表)
