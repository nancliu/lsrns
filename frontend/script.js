/**
 * OD数据处理与仿真系统 - 前端JavaScript逻辑
 */

// API基础URL
const API_BASE_URL = 'http://localhost:8000/api/v1';

// 全局变量
let currentCases = [];
let currentTemplates = {};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeEventListeners();
    loadInitialData();
});

/**
 * 初始化导航
 */
function initializeNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 移除所有活动状态
            navLinks.forEach(l => l.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            
            // 添加活动状态
            this.classList.add('active');
            const targetId = this.getAttribute('href').substring(1);
            document.getElementById(targetId).classList.add('active');
        });
    });
}

/**
 * 初始化事件监听器
 */
function initializeEventListeners() {
    // 案例管理事件
    document.getElementById('create-case-btn').addEventListener('click', showCreateCaseModal);
    document.getElementById('refresh-cases-btn').addEventListener('click', loadCases);
    
    // 仿真控制事件
    document.getElementById('run-simulation-btn').addEventListener('click', runSimulation);
    
    // 分析控制事件
    document.getElementById('run-analysis-btn').addEventListener('click', runAnalysis);
    
    // 模板管理事件
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            switchTemplateTab(this.dataset.tab);
        });
    });
    
    // 工具事件
    document.getElementById('fix-taz-btn').addEventListener('click', showFixTazModal);
    document.getElementById('compare-taz-btn').addEventListener('click', showCompareTazModal);
    
    // 模态框事件
    const modal = document.getElementById('modal');
    const closeBtn = document.querySelector('.close');
    
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

/**
 * 加载初始数据
 */
async function loadInitialData() {
    try {
        await Promise.all([
            loadCases(),
            loadTemplates()
        ]);
    } catch (error) {
        console.error('加载初始数据失败:', error);
        showNotification('加载初始数据失败', 'error');
    }
}

/**
 * 加载案例列表
 */
async function loadCases() {
    try {
        const response = await fetch(`${API_BASE_URL}/list_cases/`);
        const data = await response.json();
        
        if (response.ok) {
            currentCases = data.cases;
            displayCases(data.cases);
            updateCaseSelects();
        } else {
            throw new Error(data.detail || '加载案例失败');
        }
    } catch (error) {
        console.error('加载案例失败:', error);
        showNotification('加载案例失败', 'error');
    }
}

/**
 * 显示案例列表
 */
function displayCases(cases) {
    const caseList = document.querySelector('.case-list');
    
    if (cases.length === 0) {
        caseList.innerHTML = '<div class="loading">暂无案例</div>';
        return;
    }
    
    const casesHTML = cases.map(case => `
        <div class="case-card fade-in">
            <h3>${case.case_name || case.case_id}</h3>
            <div class="case-info">
                <p><strong>ID:</strong> ${case.case_id}</p>
                <p><strong>状态:</strong> ${getStatusText(case.status)}</p>
                <p><strong>创建时间:</strong> ${formatDateTime(case.created_at)}</p>
                <p><strong>描述:</strong> ${case.description || '无描述'}</p>
            </div>
            <div class="case-actions">
                <button class="btn btn-primary" onclick="viewCase('${case.case_id}')">查看</button>
                <button class="btn btn-secondary" onclick="cloneCase('${case.case_id}')">克隆</button>
                <button class="btn btn-danger" onclick="deleteCase('${case.case_id}')">删除</button>
            </div>
        </div>
    `).join('');
    
    caseList.innerHTML = casesHTML;
}

/**
 * 更新案例选择器
 */
function updateCaseSelects() {
    const selects = ['case-select', 'analysis-case-select'];
    
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.innerHTML = '<option value="">请选择案例</option>';
            currentCases.forEach(caseItem => {
                const option = document.createElement('option');
                option.value = caseItem.case_id;
                option.textContent = caseItem.case_name || caseItem.case_id;
                select.appendChild(option);
            });
        }
    });
}

/**
 * 加载模板数据
 */
async function loadTemplates() {
    try {
        const [tazTemplates, networkTemplates, simulationTemplates] = await Promise.all([
            fetch(`${API_BASE_URL}/templates/taz`).then(r => r.json()),
            fetch(`${API_BASE_URL}/templates/network`).then(r => r.json()),
            fetch(`${API_BASE_URL}/templates/simulation`).then(r => r.json())
        ]);
        
        currentTemplates = {
            taz: tazTemplates,
            network: networkTemplates,
            simulation: simulationTemplates
        };
        
        displayTemplates();
    } catch (error) {
        console.error('加载模板失败:', error);
        showNotification('加载模板失败', 'error');
    }
}

/**
 * 显示模板
 */
function displayTemplates() {
    // 显示TAZ模板
    const tazSection = document.getElementById('taz-templates');
    if (currentTemplates.taz && currentTemplates.taz.length > 0) {
        tazSection.innerHTML = `
            <div class="template-grid">
                ${currentTemplates.taz.map(template => `
                    <div class="template-card">
                        <h3>${template.name}</h3>
                        <p>${template.description}</p>
                        <p><strong>版本:</strong> ${template.version}</p>
                        <p><strong>状态:</strong> ${template.status}</p>
                    </div>
                `).join('')}
            </div>
        `;
    } else {
        tazSection.innerHTML = '<div class="loading">暂无TAZ模板</div>';
    }
    
    // 显示网络模板
    const networkSection = document.getElementById('network-templates');
    if (currentTemplates.network && currentTemplates.network.length > 0) {
        networkSection.innerHTML = `
            <div class="template-grid">
                ${currentTemplates.network.map(template => `
                    <div class="template-card">
                        <h3>${template.name}</h3>
                        <p>${template.description}</p>
                        <p><strong>版本:</strong> ${template.version}</p>
                        <p><strong>状态:</strong> ${template.status}</p>
                    </div>
                `).join('')}
            </div>
        `;
    } else {
        networkSection.innerHTML = '<div class="loading">暂无网络模板</div>';
    }
    
    // 显示仿真模板
    const simulationSection = document.getElementById('simulation-templates');
    if (currentTemplates.simulation && currentTemplates.simulation.length > 0) {
        simulationSection.innerHTML = `
            <div class="template-grid">
                ${currentTemplates.simulation.map(template => `
                    <div class="template-card">
                        <h3>${template.name}</h3>
                        <p>${template.description}</p>
                        <p><strong>版本:</strong> ${template.version}</p>
                        <p><strong>状态:</strong> ${template.status}</p>
                    </div>
                `).join('')}
            </div>
        `;
    } else {
        simulationSection.innerHTML = '<div class="loading">暂无仿真模板</div>';
    }
}

/**
 * 切换模板标签页
 */
function switchTemplateTab(tabName) {
    // 更新标签按钮状态
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // 更新内容区域
    document.querySelectorAll('.template-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(`${tabName}-templates`).classList.add('active');
}

/**
 * 显示创建案例模态框
 */
function showCreateCaseModal() {
    const modal = document.getElementById('modal');
    const modalBody = document.getElementById('modal-body');
    
    modalBody.innerHTML = `
        <h2>创建新案例</h2>
        <form id="create-case-form">
            <div class="form-group">
                <label for="case-name">案例名称:</label>
                <input type="text" id="case-name" class="form-control" placeholder="输入案例名称">
            </div>
            <div class="form-group">
                <label for="start-time">开始时间:</label>
                <input type="datetime-local" id="start-time" class="form-control">
            </div>
            <div class="form-group">
                <label for="end-time">结束时间:</label>
                <input type="datetime-local" id="end-time" class="form-control">
            </div>
            <div class="form-group">
                <label for="case-description">描述:</label>
                <textarea id="case-description" class="form-control" rows="3" placeholder="输入案例描述"></textarea>
            </div>
            <div class="form-group">
                <button type="submit" class="btn btn-primary">创建案例</button>
                <button type="button" class="btn btn-secondary" onclick="closeModal()">取消</button>
            </div>
        </form>
    `;
    
    modal.style.display = 'block';
    
    // 添加表单提交事件
    document.getElementById('create-case-form').addEventListener('submit', createCase);
}

/**
 * 创建案例
 */
async function createCase(e) {
    e.preventDefault();
    
    const formData = {
        case_name: document.getElementById('case-name').value,
        start_time: document.getElementById('start-time').value,
        end_time: document.getElementById('end-time').value,
        description: document.getElementById('case-description').value
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/create_case/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                time_range: {
                    start: formData.start_time,
                    end: formData.end_time
                },
                config: {},
                case_name: formData.case_name,
                description: formData.description
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('案例创建成功', 'success');
            closeModal();
            loadCases();
        } else {
            throw new Error(data.detail || '创建案例失败');
        }
    } catch (error) {
        console.error('创建案例失败:', error);
        showNotification('创建案例失败', 'error');
    }
}

/**
 * 运行仿真
 */
async function runSimulation() {
    const caseId = document.getElementById('case-select').value;
    const simulationType = document.getElementById('simulation-type').value;
    
    if (!caseId) {
        showNotification('请选择案例', 'warning');
        return;
    }
    
    try {
        updateSimulationStatus('running');
        
        const response = await fetch(`${API_BASE_URL}/run_simulation/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                run_folder: `cases/${caseId}/simulation`,
                gui: false,
                simulation_type: simulationType
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('仿真启动成功', 'success');
            updateSimulationStatus('completed');
        } else {
            throw new Error(data.detail || '仿真运行失败');
        }
    } catch (error) {
        console.error('仿真运行失败:', error);
        showNotification('仿真运行失败', 'error');
        updateSimulationStatus('failed');
    }
}

/**
 * 运行分析
 */
async function runAnalysis() {
    const caseId = document.getElementById('analysis-case-select').value;
    const analysisType = document.getElementById('analysis-type').value;
    
    if (!caseId) {
        showNotification('请选择案例', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/analyze_accuracy/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                result_folder: `cases/${caseId}/analysis/accuracy`,
                analysis_type: analysisType
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('分析启动成功', 'success');
        } else {
            throw new Error(data.detail || '分析运行失败');
        }
    } catch (error) {
        console.error('分析运行失败:', error);
        showNotification('分析运行失败', 'error');
    }
}

/**
 * 更新仿真状态
 */
function updateSimulationStatus(status) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    statusDot.className = `status-dot ${status}`;
    
    const statusMessages = {
        'running': '运行中...',
        'completed': '已完成',
        'failed': '失败',
        'idle': '未开始'
    };
    
    statusText.textContent = statusMessages[status] || '未知状态';
}

/**
 * 查看案例详情
 */
async function viewCase(caseId) {
    try {
        const response = await fetch(`${API_BASE_URL}/case/${caseId}`);
        const caseData = await response.json();
        
        if (response.ok) {
            showCaseDetails(caseData);
        } else {
            throw new Error(caseData.detail || '获取案例详情失败');
        }
    } catch (error) {
        console.error('获取案例详情失败:', error);
        showNotification('获取案例详情失败', 'error');
    }
}

/**
 * 显示案例详情
 */
function showCaseDetails(caseData) {
    const modal = document.getElementById('modal');
    const modalBody = document.getElementById('modal-body');
    
    modalBody.innerHTML = `
        <h2>案例详情</h2>
        <div class="case-details">
            <p><strong>案例ID:</strong> ${caseData.case_id}</p>
            <p><strong>案例名称:</strong> ${caseData.case_name || '未命名'}</p>
            <p><strong>状态:</strong> ${getStatusText(caseData.status)}</p>
            <p><strong>创建时间:</strong> ${formatDateTime(caseData.created_at)}</p>
            <p><strong>更新时间:</strong> ${formatDateTime(caseData.updated_at)}</p>
            <p><strong>描述:</strong> ${caseData.description || '无描述'}</p>
            <p><strong>时间范围:</strong> ${caseData.time_range.start} - ${caseData.time_range.end}</p>
        </div>
        <div class="form-group">
            <button type="button" class="btn btn-secondary" onclick="closeModal()">关闭</button>
        </div>
    `;
    
    modal.style.display = 'block';
}

/**
 * 克隆案例
 */
async function cloneCase(caseId) {
    try {
        const response = await fetch(`${API_BASE_URL}/case/${caseId}/clone`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('案例克隆成功', 'success');
            loadCases();
        } else {
            throw new Error(data.detail || '案例克隆失败');
        }
    } catch (error) {
        console.error('案例克隆失败:', error);
        showNotification('案例克隆失败', 'error');
    }
}

/**
 * 删除案例
 */
async function deleteCase(caseId) {
    if (!confirm('确定要删除这个案例吗？此操作不可恢复。')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/case/${caseId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('案例删除成功', 'success');
            loadCases();
        } else {
            const data = await response.json();
            throw new Error(data.detail || '案例删除失败');
        }
    } catch (error) {
        console.error('案例删除失败:', error);
        showNotification('案例删除失败', 'error');
    }
}

/**
 * 显示修复TAZ模态框
 */
function showFixTazModal() {
    const modal = document.getElementById('modal');
    const modalBody = document.getElementById('modal-body');
    
    modalBody.innerHTML = `
        <h2>修复TAZ文件</h2>
        <div class="form-group">
            <label for="taz-file-path">TAZ文件路径:</label>
            <input type="text" id="taz-file-path" class="form-control" placeholder="输入TAZ文件路径">
        </div>
        <div class="form-group">
            <button type="button" class="btn btn-primary" onclick="fixTazFile()">修复文件</button>
            <button type="button" class="btn btn-secondary" onclick="closeModal()">取消</button>
        </div>
    `;
    
    modal.style.display = 'block';
}

/**
 * 修复TAZ文件
 */
async function fixTazFile() {
    const filePath = document.getElementById('taz-file-path').value;
    
    if (!filePath) {
        showNotification('请输入文件路径', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/tools/taz/fix?file_path=${encodeURIComponent(filePath)}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('TAZ文件修复成功', 'success');
            closeModal();
        } else {
            throw new Error(data.detail || 'TAZ文件修复失败');
        }
    } catch (error) {
        console.error('TAZ文件修复失败:', error);
        showNotification('TAZ文件修复失败', 'error');
    }
}

/**
 * 显示比较TAZ模态框
 */
function showCompareTazModal() {
    const modal = document.getElementById('modal');
    const modalBody = document.getElementById('modal-body');
    
    modalBody.innerHTML = `
        <h2>比较TAZ文件</h2>
        <div class="form-group">
            <label for="taz-file1">第一个TAZ文件:</label>
            <input type="text" id="taz-file1" class="form-control" placeholder="输入第一个TAZ文件路径">
        </div>
        <div class="form-group">
            <label for="taz-file2">第二个TAZ文件:</label>
            <input type="text" id="taz-file2" class="form-control" placeholder="输入第二个TAZ文件路径">
        </div>
        <div class="form-group">
            <button type="button" class="btn btn-primary" onclick="compareTazFiles()">比较文件</button>
            <button type="button" class="btn btn-secondary" onclick="closeModal()">取消</button>
        </div>
    `;
    
    modal.style.display = 'block';
}

/**
 * 比较TAZ文件
 */
async function compareTazFiles() {
    const file1 = document.getElementById('taz-file1').value;
    const file2 = document.getElementById('taz-file2').value;
    
    if (!file1 || !file2) {
        showNotification('请输入两个文件路径', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/tools/taz/compare`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file1: file1,
                file2: file2
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('TAZ文件比较完成', 'success');
            closeModal();
        } else {
            throw new Error(data.detail || 'TAZ文件比较失败');
        }
    } catch (error) {
        console.error('TAZ文件比较失败:', error);
        showNotification('TAZ文件比较失败', 'error');
    }
}

/**
 * 关闭模态框
 */
function closeModal() {
    document.getElementById('modal').style.display = 'none';
}

/**
 * 显示通知
 */
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // 添加样式
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-weight: 500;
        z-index: 1001;
        animation: slideIn 0.3s ease;
    `;
    
    // 根据类型设置背景色
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8'
    };
    
    notification.style.backgroundColor = colors[type] || colors.info;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

/**
 * 工具函数
 */
function getStatusText(status) {
    const statusMap = {
        'created': '已创建',
        'processing': '处理中',
        'simulating': '仿真中',
        'analyzing': '分析中',
        'completed': '已完成',
        'failed': '失败'
    };
    return statusMap[status] || status;
}

function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return '未知';
    const date = new Date(dateTimeStr);
    return date.toLocaleString('zh-CN');
}

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style); 