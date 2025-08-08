/**
 * OD数据处理与仿真系统 - 前端JavaScript逻辑
 */

// API基础URL
const API_BASE_URL = 'http://localhost:8000/api/v1';

// 统一API请求封装
async function apiFetch(url, options = {}) {
    const resp = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        }
    });
    let data;
    try { data = await resp.json(); } catch { data = null; }
    if (!resp.ok) {
        const msg = (data && (data.detail || data.message)) || `HTTP ${resp.status}`;
        throw new Error(msg);
    }
    return data;
}

// 将 <input type="datetime-local"> 的值转为 "YYYY/MM/DD HH:MM:SS"
function toBackendTime(dtLocal) {
    if (!dtLocal) return '';
    const [date, time] = dtLocal.split('T');
    const [y, m, d] = date.split('-');
    const hms = (time || '00:00:00').length === 5 ? `${time}:00` : time;
    return `${y}/${m}/${d} ${hms}`;
}

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
    const odForm = document.getElementById('od-processing-form');
    if (odForm) odForm.addEventListener('submit', processODData);

    const refreshTplBtn = document.getElementById('refresh-templates-btn');
    if (refreshTplBtn) refreshTplBtn.addEventListener('click', loadTemplates);

    const runSimBtn = document.getElementById('run-simulation-btn');
    if (runSimBtn) runSimBtn.addEventListener('click', runSimulation);

    const refreshSimCasesBtn = document.getElementById('refresh-simulation-cases-btn');
    if (refreshSimCasesBtn) refreshSimCasesBtn.addEventListener('click', loadCases);

    const runAnalysisBtn = document.getElementById('run-analysis-btn');
    if (runAnalysisBtn) runAnalysisBtn.addEventListener('click', runAnalysis);

    const refreshAnalysisCasesBtn = document.getElementById('refresh-analysis-cases-btn');
    if (refreshAnalysisCasesBtn) refreshAnalysisCasesBtn.addEventListener('click', loadCases);

    const refreshCasesBtn = document.getElementById('refresh-cases-btn');
    if (refreshCasesBtn) refreshCasesBtn.addEventListener('click', loadCases);

    const caseSearch = document.getElementById('case-search');
    if (caseSearch) caseSearch.addEventListener('input', filterCases);

    const caseStatusFilter = document.getElementById('case-status-filter');
    if (caseStatusFilter) caseStatusFilter.addEventListener('change', filterCases);

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            switchTemplateTab(this.dataset.tab);
        });
    });

    const modal = document.getElementById('modal');
    const closeBtn = document.querySelector('.close');
    if (closeBtn) closeBtn.addEventListener('click', () => { modal.style.display = 'none'; });
    window.addEventListener('click', (e) => { if (e.target === modal) modal.style.display = 'none'; });
}

/**
 * 加载初始数据
 */
async function loadInitialData() {
    try {
        await Promise.all([loadCases(), loadTemplates()]);
        updateTemplateSelects();
    } catch (error) {
        console.error('加载初始数据失败:', error);
        showNotification('加载初始数据失败', 'error');
    }
}

// =============== OD 数据处理 ===============
async function processODData(e) {
    e.preventDefault();

    const formData = {
        start_time: toBackendTime(document.getElementById('start-time').value),
        end_time: toBackendTime(document.getElementById('end-time').value),
        taz_file: document.getElementById('taz-file').value,
        net_file: document.getElementById('network-file').value,
        interval_minutes: parseInt(document.getElementById('interval-minutes').value || '5', 10),
        case_name: document.getElementById('case-name').value,
        description: document.getElementById('case-description').value
    };

    if (!formData.start_time || !formData.end_time || !formData.taz_file || !formData.net_file) {
        showNotification('请填写所有必填字段', 'warning');
        return;
    }

    try {
        updateProcessingStatus('processing', '正在处理OD数据...');
        const result = await apiFetch(`${API_BASE_URL}/process_od_data/`, {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        const payload = result && result.data ? result.data : result;
        updateProcessingStatus('completed', 'OD数据处理完成');
        showNotification('OD数据处理成功', 'success');
        displayProcessingResult(payload);
        await loadCases();
    } catch (error) {
        console.error('OD数据处理失败:', error);
        updateProcessingStatus('failed', '处理失败');
        showNotification(`OD数据处理失败: ${error.message}`, 'error');
    }
}

// =============== 仿真运行 ===============
async function runSimulation() {
    const caseId = document.getElementById('simulation-case').value;
    const simulationType = document.getElementById('simulation-type').value;
    const guiMode = document.getElementById('gui-mode').value === 'true';
    if (!caseId) { showNotification('请选择案例', 'warning'); return; }
    try {
        updateSimulationStatus('running', '仿真运行中...');
        showProgressBar();
        const result = await apiFetch(`${API_BASE_URL}/run_simulation/`, {
            method: 'POST',
            body: JSON.stringify({
                run_folder: `cases/${caseId}/simulation`,
                gui: guiMode,
                simulation_type: simulationType
            })
        });
        const payload = result && result.data ? result.data : result;
        updateSimulationStatus('completed', '仿真完成');
        hideProgressBar();
        showNotification('仿真运行成功', 'success');
        displaySimulationResult(payload);
    } catch (error) {
        console.error('仿真运行失败:', error);
        updateSimulationStatus('failed', '仿真失败');
        hideProgressBar();
        showNotification(`仿真运行失败: ${error.message}`, 'error');
    }
}

// =============== 精度分析 ===============
async function runAnalysis() {
    const caseId = document.getElementById('analysis-case').value;
    const analysisType = document.getElementById('analysis-type').value;
    if (!caseId) { showNotification('请选择案例', 'warning'); return; }
    try {
        updateAnalysisStatus('analyzing', '精度分析中...');
        const result = await apiFetch(`${API_BASE_URL}/analyze_accuracy/`, {
            method: 'POST',
            body: JSON.stringify({
                result_folder: `cases/${caseId}/analysis/accuracy`,
                analysis_type: analysisType
            })
        });
        const payload = result && result.data ? result.data : result;
        updateAnalysisStatus('completed', '分析完成');
        showNotification('精度分析启动成功', 'success');
        displayAnalysisResult(payload);
    } catch (error) {
        console.error('精度分析失败:', error);
        updateAnalysisStatus('failed', '分析失败');
        showNotification(`精度分析失败: ${error.message}`, 'error');
    }
}

// =============== 案例列表与筛选 ===============
async function loadCases() {
    try {
        const data = await apiFetch(`${API_BASE_URL}/list_cases/`);
        currentCases = data.cases || [];
        displayCases(currentCases);
        updateCaseSelects();
    } catch (error) {
        console.error('加载案例失败:', error);
        showNotification('加载案例失败', 'error');
    }
}

function displayCases(cases) {
    const caseList = document.querySelector('.case-list');
    if (!caseList) return;
    if (!cases || cases.length === 0) { caseList.innerHTML = '<div class="loading">暂无案例</div>'; return; }
    const casesHTML = cases.map(c => `
        <div class="case-card fade-in">
            <h3>${c.case_name || c.case_id}</h3>
            <div class="case-info">
                <p><strong>ID:</strong> ${c.case_id}</p>
                <p><strong>状态:</strong> ${getStatusText(c.status)}</p>
                <p><strong>创建时间:</strong> ${formatDateTime(c.created_at)}</p>
                <p><strong>描述:</strong> ${c.description || '无描述'}</p>
            </div>
            <div class="case-actions">
                <button class="btn btn-primary" onclick="viewCase('${c.case_id}')">查看</button>
                <button class="btn btn-secondary" onclick="cloneCase('${c.case_id}')">克隆</button>
                <button class="btn btn-danger" onclick="deleteCase('${c.case_id}')">删除</button>
            </div>
        </div>
    `).join('');
    caseList.innerHTML = casesHTML;
}

function updateCaseSelects() {
    ['simulation-case', 'analysis-case'].forEach(selectId => {
        const select = document.getElementById(selectId);
        if (!select) return;
        select.innerHTML = '<option value="">请选择案例</option>';
        currentCases.forEach(item => {
            const option = document.createElement('option');
            option.value = item.case_id;
            option.textContent = item.case_name || item.case_id;
            select.appendChild(option);
        });
    });
}

function filterCases() {
    const searchTerm = (document.getElementById('case-search')?.value || '').toLowerCase();
    const statusFilter = document.getElementById('case-status-filter')?.value || '';
    const filtered = (currentCases || []).filter(c => {
        const matchesSearch = !searchTerm ||
            (c.case_name && c.case_name.toLowerCase().includes(searchTerm)) ||
            (c.case_id && c.case_id.toLowerCase().includes(searchTerm)) ||
            (c.description && c.description.toLowerCase().includes(searchTerm));
        const matchesStatus = !statusFilter || c.status === statusFilter;
        return matchesSearch && matchesStatus;
    });
    displayCases(filtered);
}

// =============== 模板加载与选择器 ===============
async function loadTemplates() {
    try {
        const [tazTemplates, networkTemplates, simulationTemplates] = await Promise.all([
            apiFetch(`${API_BASE_URL}/templates/taz`),
            apiFetch(`${API_BASE_URL}/templates/network`),
            apiFetch(`${API_BASE_URL}/templates/simulation`)
        ]);
        currentTemplates = { taz: tazTemplates, network: networkTemplates, simulation: simulationTemplates };
        displayTemplates();
        updateTemplateSelects();
    } catch (error) {
        console.error('加载模板失败:', error);
        showNotification('加载模板失败', 'error');
    }
}

function updateTemplateSelects() {
    const tazSelect = document.getElementById('taz-file');
    if (tazSelect && currentTemplates.taz) {
        tazSelect.innerHTML = '<option value="">请选择TAZ文件</option>';
        currentTemplates.taz.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.file_path;
            opt.textContent = t.name;
            tazSelect.appendChild(opt);
        });
        // 默认选择 TAZ_5 系列
        const taz5 = Array.from(tazSelect.options).find(o => /TAZ_5/i.test(o.textContent) || /TAZ_5/i.test(o.value));
        if (taz5) tazSelect.value = taz5.value; else if (tazSelect.options[1]) tazSelect.selectedIndex = 1;
    }
    const netSelect = document.getElementById('network-file');
    if (netSelect && currentTemplates.network) {
        netSelect.innerHTML = '<option value="">请选择网络文件</option>';
        currentTemplates.network.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.file_path;
            opt.textContent = t.name;
            netSelect.appendChild(opt);
        });
        // 默认选择 v6 版本
        const v6 = Array.from(netSelect.options).find(o => /v6/i.test(o.textContent) || /v6/i.test(o.value));
        if (v6) netSelect.value = v6.value; else if (netSelect.options[1]) netSelect.selectedIndex = 1;
    }
}

function displayTemplates() {
    const tazSection = document.getElementById('taz-templates');
    if (tazSection) {
        tazSection.innerHTML = currentTemplates.taz && currentTemplates.taz.length ? `
            <div class="template-grid">
                ${currentTemplates.taz.map(t => `
                    <div class="template-card">
                        <h3>${t.name}</h3>
                        <p>${t.description}</p>
                        <p><strong>版本:</strong> ${t.version}</p>
                        <p><strong>状态:</strong> ${t.status}</p>
                    </div>
                `).join('')}
            </div>
        ` : '<div class="loading">暂无TAZ模板</div>';
    }
    const networkSection = document.getElementById('network-templates');
    if (networkSection) {
        networkSection.innerHTML = currentTemplates.network && currentTemplates.network.length ? `
            <div class="template-grid">
                ${currentTemplates.network.map(t => `
                    <div class="template-card">
                        <h3>${t.name}</h3>
                        <p>${t.description}</p>
                        <p><strong>版本:</strong> ${t.version}</p>
                        <p><strong>状态:</strong> ${t.status}</p>
                    </div>
                `).join('')}
            </div>
        ` : '<div class="loading">暂无网络模板</div>';
    }
    const simulationSection = document.getElementById('simulation-templates');
    if (simulationSection) {
        simulationSection.innerHTML = currentTemplates.simulation && currentTemplates.simulation.length ? `
            <div class="template-grid">
                ${currentTemplates.simulation.map(t => `
                    <div class="template-card">
                        <h3>${t.name}</h3>
                        <p>${t.description}</p>
                        <p><strong>版本:</strong> ${t.version}</p>
                        <p><strong>状态:</strong> ${t.status}</p>
                    </div>
                `).join('')}
            </div>
        ` : '<div class="loading">暂无仿真模板</div>';
    }
}

function switchTemplateTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    const btn = document.querySelector(`[data-tab="${tabName}"]`);
    if (btn) btn.classList.add('active');
    document.querySelectorAll('.template-section').forEach(s => s.classList.remove('active'));
    const section = document.getElementById(`${tabName}-templates`);
    if (section) section.classList.add('active');
}

// =============== 状态与结果展示 ===============
function updateProcessingStatus(status, message) {
    const area = document.getElementById('od-processing-result');
    if (!area) return;
    area.innerHTML = `
        <div class="status-indicator">
            <span class="status-dot ${status}"></span>
            <span class="status-text">${message}</span>
        </div>
    `;
}

function updateSimulationStatus(status, message) {
    const statusText = document.querySelector('.simulation-status .status-text');
    const statusDot = document.querySelector('.simulation-status .status-dot');
    if (statusText) statusText.textContent = message;
    if (statusDot) statusDot.className = `status-dot ${status}`;
}

function updateAnalysisStatus(status, message) {
    const area = document.getElementById('analysis-result');
    if (!area) return;
    area.innerHTML = `
        <div class="status-indicator">
            <span class="status-dot ${status}"></span>
            <span class="status-text">${message}</span>
        </div>
    `;
}

function showProgressBar() {
    const bar = document.getElementById('simulation-progress');
    if (bar) bar.style.display = 'block';
}

function hideProgressBar() {
    const bar = document.getElementById('simulation-progress');
    if (bar) bar.style.display = 'none';
}

function displayProcessingResult(result) {
    const area = document.getElementById('od-processing-result');
    if (!area) return;
    area.innerHTML = `
        <div class="case-card fade-in">
            <h3>OD数据处理结果</h3>
            <div class="case-info">
                <p><strong>运行文件夹:</strong> ${result.run_folder || 'N/A'}</p>
                <p><strong>OD文件:</strong> ${result.od_file || 'N/A'}</p>
                <p><strong>路由文件:</strong> ${result.route_file || 'N/A'}</p>
                <p><strong>配置文件:</strong> ${result.sumocfg_file || 'N/A'}</p>
                <p><strong>总记录数:</strong> ${result.total_records || 'N/A'}</p>
                <p><strong>OD对数:</strong> ${result.od_pairs || 'N/A'}</p>
            </div>
        </div>
    `;
}

function displaySimulationResult(result) {
    const area = document.getElementById('simulation-result');
    if (!area) return;
    area.innerHTML = `
        <div class="case-card fade-in">
            <h3>仿真运行结果</h3>
            <div class="case-info">
                <p><strong>运行文件夹:</strong> ${result.run_folder || 'N/A'}</p>
                <p><strong>仿真类型:</strong> ${result.simulation_type || 'N/A'}</p>
                <p><strong>GUI模式:</strong> ${result.gui ? '是' : '否'}</p>
                <p><strong>开始时间:</strong> ${result.started_at || 'N/A'}</p>
                <p><strong>状态:</strong> ${result.status || 'N/A'}</p>
            </div>
        </div>
    `;
}

function displayAnalysisResult(result) {
    const area = document.getElementById('analysis-result');
    if (!area) return;
    area.innerHTML = `
        <div class="case-card fade-in">
            <h3>精度分析结果</h3>
            <div class="case-info">
                <p><strong>结果文件夹:</strong> ${result.result_folder || 'N/A'}</p>
                <p><strong>分析类型:</strong> ${result.analysis_type || 'N/A'}</p>
                <p><strong>开始时间:</strong> ${result.started_at || 'N/A'}</p>
                <p><strong>状态:</strong> ${result.status || 'N/A'}</p>
                ${result.metrics ? `<p><strong>指标:</strong> ${JSON.stringify(result.metrics)}</p>` : ''}
            </div>
        </div>
    `;
}

// =============== 工具通知与通用 ===============
function showNotification(message, type = 'info') {
    const n = document.createElement('div');
    n.className = `notification ${type}`;
    n.textContent = message;
    n.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 1000;
        padding: 10px 15px; border-radius: 5px; color: #fff;
        background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : type === 'warning' ? '#ff9800' : '#2196F3'};
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    `;
    document.body.appendChild(n);
    setTimeout(() => { if (n.parentNode) n.parentNode.removeChild(n); }, 3000);
}

function getStatusText(status) {
    const m = { created: '已创建', processing: '处理中', simulating: '仿真中', analyzing: '分析中', completed: '已完成', failed: '失败' };
    return m[status] || status || '未知';
}

function formatDateTime(s) {
    if (!s) return 'N/A';
    try { return new Date(s).toLocaleString('zh-CN'); } catch { return s; }
}

// 案例操作
async function viewCase(caseId) {
    try { const d = await apiFetch(`${API_BASE_URL}/case/${caseId}`); showCaseDetails(d); }
    catch (e) { console.error(e); showNotification('获取案例详情失败', 'error'); }
}

async function cloneCase(caseId) {
    try { await apiFetch(`${API_BASE_URL}/case/${caseId}/clone`, { method: 'POST', body: JSON.stringify({}) }); showNotification('案例克隆成功', 'success'); loadCases(); }
    catch (e) { console.error(e); showNotification('案例克隆失败', 'error'); }
}

async function deleteCase(caseId) {
    if (!confirm('确定要删除这个案例吗？此操作不可恢复。')) return;
    try { await apiFetch(`${API_BASE_URL}/case/${caseId}`, { method: 'DELETE' }); showNotification('案例删除成功', 'success'); loadCases(); }
    catch (e) { console.error(e); showNotification('案例删除失败', 'error'); }
}

function showCaseDetails(c) {
    const modal = document.getElementById('modal');
    const body = document.getElementById('modal-body');
    body.innerHTML = `
        <h2>案例详情</h2>
        <div class="case-details">
            <p><strong>案例ID:</strong> ${c.case_id}</p>
            <p><strong>案例名称:</strong> ${c.case_name || '未命名'}</p>
            <p><strong>状态:</strong> ${getStatusText(c.status)}</p>
            <p><strong>创建时间:</strong> ${formatDateTime(c.created_at)}</p>
            <p><strong>更新时间:</strong> ${formatDateTime(c.updated_at)}</p>
            <p><strong>描述:</strong> ${c.description || '无描述'}</p>
            <p><strong>时间范围:</strong> ${(c.time_range && c.time_range.start) || 'N/A'} - ${(c.time_range && c.time_range.end) || 'N/A'}</p>
        </div>
        <div class="form-group">
            <button type="button" class="btn btn-secondary" onclick="closeModal()">关闭</button>
        </div>
    `;
    modal.style.display = 'block';
}

function closeModal() { const modal = document.getElementById('modal'); if (modal) modal.style.display = 'none'; }

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

// 默认时间快捷设置：上一周周一 08:00-09:00（整分钟）
function setDefaultLastWeekMonday0800To0900() {
    const now = new Date();
    const day = now.getDay(); // 0=周日,1=周一
    const daysSinceMonday = (day + 6) % 7; // 周一->0, 周日->6
    const thisMonday = new Date(now);
    thisMonday.setDate(now.getDate() - daysSinceMonday);
    thisMonday.setHours(0,0,0,0);
    const lastMonday = new Date(thisMonday);
    lastMonday.setDate(thisMonday.getDate() - 7);
    const start = new Date(lastMonday);
    start.setHours(8,0,0,0);
    const end = new Date(lastMonday);
    end.setHours(9,0,0,0);
    const toLocalInput = (d)=>{
        const pad=n=>String(n).padStart(2,'0');
        return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
    };
    const startInput = document.getElementById('start-time');
    const endInput = document.getElementById('end-time');
    if (startInput) startInput.value = toLocalInput(start);
    if (endInput) endInput.value = toLocalInput(end);
}

// 初始化时设置默认时间
document.addEventListener('DOMContentLoaded', () => {
    try { setDefaultLastWeekMonday0800To0900(); } catch {}
}); 