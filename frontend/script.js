/**
 * OD数据处理与仿真系统 - 前端JavaScript逻辑
 */

// API基础URL - 动态获取当前服务器地址，支持远程访问
const API_BASE_URL = `${window.location.protocol}//${window.location.host}/api/v1`;

// =============== 精度分析调试 ===============
function nowTs() {
    try { return new Date().toLocaleTimeString('zh-CN', { hour12: false }); } catch { return new Date().toISOString(); }
}

function appendAnalysisDebug(message, obj) {
    try {
        const el = document.getElementById('analysis-debug');
        if (!el) return;
        const ts = nowTs();
        const lines = [`[${ts}] ${message}`];
        if (obj !== undefined) {
            try { lines.push(typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2)); } catch { lines.push(String(obj)); }
        }
        el.textContent += (el.textContent ? '\n' : '') + lines.join('\n');
        el.scrollTop = el.scrollHeight;
    } catch {}
}

function clearAnalysisDebug() {
    const el = document.getElementById('analysis-debug');
    if (el) el.textContent = '';
}

function toggleAnalysisDebug() {
    const el = document.getElementById('analysis-debug');
    if (!el) return;
    const btn = document.getElementById('toggle-analysis-debug');
    const hidden = el.style.display === 'none';
    el.style.display = hidden ? 'block' : 'none';
    if (btn) btn.textContent = hidden ? '折叠' : '展开';
}

// 统一API请求封装
async function apiFetch(url, options = {}) {
    const resp = await fetch(url, {
        cache: 'no-store',
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        }
    });
    let data;
    try { data = await resp.json(); } catch { data = null; }
    if (!resp.ok) {
        let msg = `HTTP ${resp.status}`;
        if (data) {
            if (data.detail) {
                // FastAPI validation errors
                if (Array.isArray(data.detail)) {
                    msg = data.detail.map(err => `${err.loc?.join('.')}: ${err.msg}`).join(', ');
                } else {
                    msg = data.detail;
                }
            } else if (data.message) {
                msg = data.message;
            }
        }
        console.error('API Error:', resp.status, data);
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
let currentSim = { caseId: null, startedAt: null };

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeEventListeners();
    loadInitialData();
    
    // 修复时间输入框格式问题
    fixTimeInputFormats();
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
    
    const simulationCaseSelect = document.getElementById('simulation-case');
    if (simulationCaseSelect) simulationCaseSelect.addEventListener('change', function() {
        loadCaseSimulations(this.value);
    });

    const runAnalysisBtn = document.getElementById('run-analysis-btn');
    if (runAnalysisBtn) runAnalysisBtn.addEventListener('click', runAnalysis);

    const refreshAnalysisCasesBtn = document.getElementById('refresh-analysis-cases-btn');
    if (refreshAnalysisCasesBtn) refreshAnalysisCasesBtn.addEventListener('click', loadCases);
    
    const analysisCaseSelect = document.getElementById('analysis-case');
    if (analysisCaseSelect) analysisCaseSelect.addEventListener('change', function() {
        loadAnalysisSimulations(this.value);
    });

  const viewHistoryBtn = document.getElementById('view-analysis-history-btn');
  if (viewHistoryBtn) viewHistoryBtn.addEventListener('click', viewAnalysisHistory);

    const clearDebugBtn = document.getElementById('clear-analysis-debug');
    if (clearDebugBtn) clearDebugBtn.addEventListener('click', clearAnalysisDebug);
    const toggleDebugBtn = document.getElementById('toggle-analysis-debug');
    if (toggleDebugBtn) toggleDebugBtn.addEventListener('click', toggleAnalysisDebug);

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
        description: document.getElementById('case-description').value,
        // 仿真输出配置已移至仿真运行阶段
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

// =============== 仿真管理 ===============
async function loadCaseSimulations(caseId) {
    if (!caseId) {
        document.getElementById('existing-simulations').innerHTML = '<div class="loading">请先选择案例</div>';
        return;
    }
    
    try {
        document.getElementById('existing-simulations').innerHTML = '<div class="loading">加载中...</div>';
        const response = await apiFetch(`${API_BASE_URL}/simulations/${caseId}`);
        const simulations = response.data?.simulations || [];
        
        if (simulations.length === 0) {
            document.getElementById('existing-simulations').innerHTML = '<div class="no-data">该案例暂无仿真结果</div>';
            return;
        }
        
        const simulationsHtml = simulations.map(sim => `
            <div class="simulation-card ${sim.status}">
                <div class="simulation-card-header">
                    <div class="simulation-card-title">${sim.simulation_name || sim.simulation_id}</div>
                    <div class="simulation-card-status ${sim.status}">${getStatusText(sim.status)}</div>
                </div>
                <div class="simulation-card-info">
                    <div><strong>类型:</strong> ${sim.simulation_type === 'microscopic' ? '微观' : '中观'}</div>
                    <div><strong>创建时间:</strong> ${formatDateTime(sim.created_at)}</div>
                    ${sim.started_at ? `<div><strong>开始时间:</strong> ${formatDateTime(sim.started_at)}</div>` : ''}
                    ${sim.description ? `<div><strong>描述:</strong> ${sim.description}</div>` : ''}
                    ${sim.duration ? `<div><strong>耗时:</strong> ${sim.duration}秒</div>` : ''}
                </div>
                <div class="simulation-card-actions">
                    <button class="btn btn-secondary" onclick="viewSimulationDetail('${sim.simulation_id}')">查看详情</button>
                    ${sim.status === 'completed' ? `<button class="btn btn-primary" onclick="analyzeSimulation('${sim.simulation_id}')">分析结果</button>` : ''}
                    <button class="btn btn-danger" onclick="deleteSimulation('${sim.simulation_id}')">删除</button>
                </div>
            </div>
        `).join('');
        
        document.getElementById('existing-simulations').innerHTML = simulationsHtml;
    } catch (error) {
        console.error('加载仿真列表失败:', error);
        document.getElementById('existing-simulations').innerHTML = '<div class="error">加载失败</div>';
    }
}

function getStatusText(status) {
    const statusMap = {
        'running': '运行中',
        'completed': '已完成',
        'failed': '失败',
        'pending': '等待中'
    };
    return statusMap[status] || status;
}

function formatDateTime(dateString) {
    try {
        return new Date(dateString).toLocaleString('zh-CN');
    } catch {
        return dateString;
    }
}

async function viewSimulationDetail(simulationId) {
    try {
        const response = await apiFetch(`${API_BASE_URL}/simulation/${simulationId}`);
        const simulation = response.data;
        
        const modalBody = document.getElementById('modal-body');
        // 组装输入文件显示
        const inf = simulation.input_files || {};
        const netFile = inf.network_file || '—';
        const routesFiles = (inf.routes_files && inf.routes_files.length) ? inf.routes_files : [];
        const tazFiles = (inf.taz_files && inf.taz_files.length) ? inf.taz_files : [];
        const routesHtml = routesFiles.length ? routesFiles.map(u=>`<code title="${u}">${u.split('/').pop()}</code>`).join(' | ') : '—';
        const tazHtml = tazFiles.length ? tazFiles.map(u=>`<code title="${u}">${u.split('/').pop()}</code>`).join(' | ') : '—';
        modalBody.innerHTML = `
            <h3>仿真详情</h3>
            <div class="detail-info">
                <p><strong>仿真ID:</strong> ${simulation.simulation_id}</p>
                <p><strong>名称:</strong> ${simulation.simulation_name || '无'}</p>
                <p><strong>类型:</strong> ${simulation.simulation_type === 'microscopic' ? '微观仿真' : '中观仿真'}</p>
                <p><strong>状态:</strong> ${getStatusText(simulation.status)}</p>
                <p><strong>创建时间:</strong> ${formatDateTime(simulation.created_at)}</p>
                ${simulation.started_at ? `<p><strong>开始时间:</strong> ${formatDateTime(simulation.started_at)}</p>` : ''}
                ${simulation.completed_at ? `<p><strong>完成时间:</strong> ${formatDateTime(simulation.completed_at)}</p>` : ''}
                ${simulation.duration ? `<p><strong>耗时:</strong> ${simulation.duration}秒</p>` : ''}
                ${simulation.description ? `<p><strong>描述:</strong> ${simulation.description}</p>` : ''}
                <p><strong>结果路径:</strong> ${simulation.result_folder}</p>
                <h4>输入文件</h4>
                <p><strong>路网文件:</strong> <code title="${netFile}">${(netFile||'').split('/').pop() || '—'}</code></p>
                <p><strong>路由文件:</strong> ${routesHtml}</p>
                <p><strong>TAZ文件:</strong> ${tazHtml}</p>
            </div>
        `;
        showModal();
    } catch (error) {
        console.error('获取仿真详情失败:', error);
        showNotification('获取仿真详情失败', 'error');
    }
}

async function deleteSimulation(simulationId) {
    if (!confirm('确定要删除这个仿真结果吗？')) return;
    
    try {
        await apiFetch(`${API_BASE_URL}/simulation/${simulationId}`, {
            method: 'DELETE'
        });
        showNotification('删除成功', 'success');
        // 重新加载当前案例的仿真列表
        const caseId = document.getElementById('simulation-case').value;
        if (caseId) {
            await loadCaseSimulations(caseId);
        }
    } catch (error) {
        console.error('删除仿真失败:', error);
        showNotification('删除仿真失败', 'error');
    }
}

async function loadAnalysisSimulations(caseId) {
    const container = document.getElementById('analysis-simulations');
    if (!caseId) {
        container.innerHTML = '<div class="loading">请先选择案例</div>';
        return;
    }
    
    try {
        container.innerHTML = '<div class="loading">加载中...</div>';
        const response = await apiFetch(`${API_BASE_URL}/simulations/${caseId}`);
        const simulations = response.data?.simulations || [];
        
        const completedSimulations = simulations.filter(sim => sim.status === 'completed');
        
        if (completedSimulations.length === 0) {
            container.innerHTML = '<div class="no-data">该案例暂无已完成的仿真结果</div>';
            return;
        }
        
        const checkboxesHtml = completedSimulations.map(sim => `
            <div class="checkbox-item">
                <input type="checkbox" id="sim_${sim.simulation_id}" name="simulation" value="${sim.simulation_id}">
                <label for="sim_${sim.simulation_id}" class="checkbox-item-label">
                    ${sim.simulation_name || sim.simulation_id}
                    <span class="checkbox-item-info">
                        ${sim.simulation_type === 'microscopic' ? '微观' : '中观'} | ${formatDateTime(sim.created_at)}
                    </span>
                </label>
            </div>
        `).join('');
        
        container.innerHTML = checkboxesHtml;
    } catch (error) {
        console.error('加载仿真列表失败:', error);
        container.innerHTML = '<div class="error">加载失败</div>';
    }
}

// =============== 仿真运行 ===============
async function runSimulation() {
    const caseId = document.getElementById('simulation-case').value;
    const simulationType = document.getElementById('simulation-type').value;
    const guiMode = document.getElementById('gui-mode').value === 'true';
    const simulationName = document.getElementById('simulation-name').value.trim();
    const simulationDescription = document.getElementById('simulation-description').value.trim();
    
    // 收集仿真输出配置
    const simulationParams = {
        output_summary: document.getElementById('sim-out-summary').checked,
        output_tripinfo: document.getElementById('sim-out-tripinfo').checked,
        output_vehroute: document.getElementById('sim-out-vehroute').checked,
        output_netstate: document.getElementById('sim-out-netstate').checked,
        output_fcd: document.getElementById('sim-out-fcd').checked,
        output_emission: document.getElementById('sim-out-emission').checked
    };
    
    if (!caseId) { showNotification('请选择案例', 'warning'); return; }
    try {
        updateSimulationStatus('running', '仿真运行中...');
        showProgressBar();

        const progressBar = document.getElementById('simulation-progress');
        const fill = progressBar ? progressBar.querySelector('.progress-fill') : null;
        let pollTimer = null;
        // 调试函数已移除
        const startPolling = () => {
            const pollOnce = async () => {
                try {
                    const ts = Date.now();
                    const p = await apiFetch(`${API_BASE_URL}/simulation_progress/${caseId}?_=${ts}`);
                    const data = p && p.data ? p.data : p;
                    const pct = (data && typeof data.percent === 'number') ? Math.max(0, Math.min(100, data.percent)) : 0;
                    const msg = data && data.message ? data.message : '';
                    if (fill) fill.style.width = `${pct}%`;
                    updateSimulationStatus('running', `仿真中 ${pct}%${msg ? `（${msg}）` : ''}`);
                    if (data && (data.status === 'completed' || data.status === 'failed')) {
                        clearInterval(pollTimer);
                        pollTimer = null;
                        if (data.status === 'completed') {
                            updateSimulationStatus('completed', `仿真完成 100%`);
                            if (fill) fill.style.width = '100%';
                            const endTs = (data && data.updated_at) ? data.updated_at : new Date().toISOString();
                            displaySimulationResult({ run_folder: `cases/${caseId}/simulation`, simulation_type: simulationType, gui: guiMode, started_at: currentSim.startedAt, ended_at: endTs, status: 'completed' });
                        } else {
                            updateSimulationStatus('failed', `仿真失败 ${pct}%${msg ? `（${msg}）` : ''}`);
                            displaySimulationResult({ run_folder: `cases/${caseId}/simulation`, simulation_type: simulationType, gui: guiMode, started_at: currentSim.startedAt, status: 'failed' });
                        }
                        hideProgressBar();
                    }
                } catch (e) { /* ignore */ }
            };
            pollTimer = setInterval(pollOnce, 10000);
            pollOnce();
        };

        // 准备请求数据
        const requestData = {
            case_id: caseId,
            gui: guiMode,
            simulation_type: simulationType,
            simulation_name: simulationName || null,
            simulation_description: simulationDescription || null,
            simulation_params: simulationParams
        };
        
        console.log('发送仿真请求:', requestData);
        
        // 先启动仿真，再开始轮询，避免第一轮读到上一次的progress.json
        const result = await apiFetch(`${API_BASE_URL}/run_simulation/`, {
            method: 'POST',
            body: JSON.stringify(requestData)
        });
        // 启动成功后，先显示“已启动”，结果面板状态以轮询完成为准
        const payload = result && result.data ? result.data : result;
        showNotification('仿真已启动', 'success');
        currentSim.caseId = caseId;
        currentSim.startedAt = payload.started_at || new Date().toISOString();
        displaySimulationResult({ run_folder: `cases/${caseId}/simulation`, simulation_type: simulationType, gui: guiMode, started_at: currentSim.startedAt, status: 'started' });
        
        // 等待后端写入初始progress.json后再开始轮询
        setTimeout(startPolling, 1200);

        // 轮询将自行在completed/failed时停止
    } catch (error) {
        console.error('仿真运行失败:', error);
        let errorMsg = '未知错误';
        
        if (error && error.message) {
            errorMsg = error.message;
        } else if (typeof error === 'string') {
            errorMsg = error;
        } else if (error && typeof error === 'object') {
            try {
                errorMsg = JSON.stringify(error);
            } catch {
                errorMsg = error.toString();
            }
        } else if (error && error.toString) {
            errorMsg = error.toString();
        }
        
        console.log('处理后的错误消息:', errorMsg);
        updateSimulationStatus('failed', '仿真失败');
        showNotification(`仿真运行失败: ${errorMsg}`, 'error');
        hideProgressBar();
    }
}

// =============== 精度分析 ===============
async function runAnalysis() {
    const caseId = document.getElementById('analysis-case').value;
    let analysisType = document.getElementById('analysis-type').value;
            // 分析类型映射已更新，不再需要转换
    if (!caseId) { showNotification('请选择案例', 'warning'); return; }
    
    // 获取选中的仿真结果
    const selectedSimulations = [];
    document.querySelectorAll('#analysis-simulations input[type="checkbox"]:checked').forEach(checkbox => {
        selectedSimulations.push(checkbox.value);
    });
    
    if (selectedSimulations.length === 0) {
        showNotification('请至少选择一个仿真结果进行分析', 'warning');
        return;
    }
    
    try {
        clearAnalysisDebug();
        appendAnalysisDebug('开始分析');
        // 分析类型已经是英文值，直接使用
        let englishAnalysisType = analysisType;
        
        const reqBody = {
            case_id: caseId,
            simulation_ids: selectedSimulations,
            analysis_type: englishAnalysisType
        };
        
        // 根据分析类型选择API端点
        let apiEndpoint;
        if (englishAnalysisType === 'accuracy') {
            apiEndpoint = `${API_BASE_URL}/analyze_accuracy/`;
        } else if (englishAnalysisType === 'mechanism') {
            apiEndpoint = `${API_BASE_URL}/analyze_mechanism/`;
        } else if (englishAnalysisType === 'performance') {
            apiEndpoint = `${API_BASE_URL}/analyze_performance/`;
        } else {
            apiEndpoint = `${API_BASE_URL}/analyze_accuracy/`;
        }
        
        appendAnalysisDebug('请求', { url: apiEndpoint, body: reqBody });
        updateAnalysisStatus('analyzing', '分析中...');
        const result = await apiFetch(apiEndpoint, {
            method: 'POST',
            body: JSON.stringify(reqBody)
        });
        const payload = result && result.data ? result.data : result;
        appendAnalysisDebug('响应', payload);
        updateAnalysisStatus('completed', '分析完成');
        showNotification(`分析启动成功，已选择${selectedSimulations.length}个仿真结果`, 'success');
        
        // 检查返回的数据结构，适配新的API格式
        let displayData = payload;
        if (payload && payload.data) {
            // 新API格式：{success: true, message: "...", data: {...}}
            displayData = payload.data;
        }
        
        // 添加分析类型信息
        if (!displayData.analysis_type) {
            displayData.analysis_type = englishAnalysisType;
        }
        
        displayAnalysisResult(displayData);
    } catch (error) {
        appendAnalysisDebug('错误', { message: error?.message, stack: error?.stack });
        console.error(`${analysisType}分析失败:`, error);
        updateAnalysisStatus('failed', '分析失败');
        showNotification(`${analysisType}分析失败: ${error.message}`, 'error');
    }
}

// 辅助函数：将英文分析类型转换为中文显示名称
function getAnalysisTypeDisplayName(analysisType) {
    switch(analysisType) {
        case 'mechanism': return '机理';
        case 'performance': return '性能';
        case 'accuracy':
        default: return '精度';
    }
}

// =============== 精度历史结果 ===============
async function viewAnalysisHistory() {
  const caseId = document.getElementById('analysis-case').value;
  if (!caseId) { showNotification('请选择案例', 'warning'); return; }
  // 读取下拉的当前分析类型
  let at = document.getElementById('analysis-type').value;
  // 分析类型已经是英文值，直接使用
  let historyType = at;
  try {
    const data = await apiFetch(`${API_BASE_URL}/analysis_results/${caseId}?analysis_type=${encodeURIComponent(historyType)}`);
    const payload = data && data.data ? data.data : data;
    renderAnalysisHistory(payload);
  } catch (e) {
    console.error(e);
    // 向后兼容：老接口（仅精度）
    try {
      const data2 = await apiFetch(`${API_BASE_URL}/accuracy_results/${caseId}`);
      const payload2 = data2 && data2.data ? data2.data : data2;
      renderAnalysisHistory({ case_id: payload2.case_id, analysis_type: 'accuracy', results: payload2.results || [] });
    } catch (e2) {
      showNotification('获取历史结果失败', 'error');
    }
  }
}

function renderAnalysisHistory(payload) {
  const area = document.getElementById('analysis-history');
  if (!area) return;
  const results = (payload && payload.results) || [];
  if (!results.length) { area.innerHTML = '<div class="loading">暂无历史结果</div>'; return; }
  const html = `
    <div class="case-card fade-in">
      <h3>历史${getAnalysisTypeDisplayName(payload.analysis_type||'accuracy')}结果（${payload.case_id}）</h3>
      <div class="case-info">
        ${results.map(r => `
          <details style="margin-bottom:8px;">
            <summary><strong>${r.folder}</strong> <span style="opacity:.7;">（${formatDateTime(r.created_at)}）</span></summary>
            ${r.report_html ? `<p><a class="btn btn-primary" href="${r.report_html}" target="_blank">查看报告</a></p>` : ''}
            ${r.csv_files && r.csv_files.length ? `<p><strong>CSV:</strong> ${r.csv_files.map(u => `<a href="${u}" target="_blank">${u.split('/').pop()}</a>`).join(' | ')}</p>` : ''}
            ${r.chart_files && r.chart_files.length ? `<p><strong>图表:</strong> ${r.chart_files.slice(0,6).map(u => `<a href="${u}" target="_blank">${u.split('/').pop()}</a>`).join(' | ')}${r.chart_files.length>6?' …':''}</p>` : ''}
          </details>
        `).join('')}
      </div>
    </div>`;
  area.innerHTML = html;
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
                ${renderAnalysisSummary(c.analysis)}
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

function renderAnalysisSummary(analysis) {
  try {
    if (!analysis) return '';
    const acc = analysis.accuracy || {};
    const mech = analysis.mechanism || {};
    const perf = analysis.performance || {};
    const accUrl = acc.latest_report_url ? `<a href="${acc.latest_report_url}" target="_blank">精度</a>` : '精度: —';
    const mechUrl = mech.latest_report_url ? `<a href="${mech.latest_report_url}" target="_blank">机理</a>` : '机理: —';
    const perfUrl = perf.latest_report_url ? `<a href="${perf.latest_report_url}" target="_blank">性能</a>` : '性能: —';
    const accTime = acc.updated_at ? `（${formatDateTime(acc.updated_at)}）` : '';
    const mechTime = mech.updated_at ? `（${formatDateTime(mech.updated_at)}）` : '';
    const perfTime = perf.updated_at ? `（${formatDateTime(perf.updated_at)}）` : '';
    return `
      <div style="margin-top:6px; font-size: 13px;">
        <p><strong>最新报告:</strong> ${accUrl}${accTime} | ${mechUrl}${mechTime} | ${perfUrl}${perfTime}</p>
      </div>
    `;
  } catch { return ''; }
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
    // 显示结果区域容器
    const area = document.getElementById('simulation-result');
    if (area && area.style.display === 'none') area.style.display = 'block';
}

function updateAnalysisStatus(status, message) {
    const area = document.getElementById('analysis-result');
    if (!area) return;
    if (area.style.display === 'none') area.style.display = 'block';
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
                <p><strong>总记录数:</strong> ${result.total_records || 'N/A'}</p>
                <p><strong>OD对数:</strong> ${result.od_pairs || 'N/A'}</p>
            </div>
        </div>
    `;
}

function displaySimulationResult(result) {
    const area = document.getElementById('simulation-result');
    if (!area) return;
    if (area.style.display === 'none') area.style.display = 'block';
    const endTimeText = result.status === 'completed' && result.ended_at ? `<p><strong>结束时间:</strong> ${result.ended_at}</p>` : '';
    area.innerHTML = `
        <div class="case-card fade-in">
            <h3>仿真运行结果</h3>
            <div class="case-info">
                <p><strong>运行文件夹:</strong> ${result.run_folder || 'N/A'}</p>
                <p><strong>仿真类型:</strong> ${result.simulation_type || 'N/A'}</p>
                <p><strong>GUI模式:</strong> ${result.gui ? '是' : '否'}</p>
                <p><strong>开始时间:</strong> ${result.started_at || 'N/A'}</p>
                ${endTimeText}
                <p><strong>状态:</strong> ${result.status || 'N/A'}</p>
            </div>
        </div>
    `;
}

function displayAnalysisResult(result) {
    const area = document.getElementById('analysis-result');
    if (!area) return;
    if (area.style.display === 'none') area.style.display = 'block';
    const at = (result.analysis_type || '').toLowerCase();
            const typeLabel = at === 'mechanism' ? '机理' : at === 'performance' ? '性能' : '精度';

    // 通用部分
    const reportLink = result.report_file ? `<p><a class="btn btn-primary" href="${result.report_file}" target="_blank">查看报告</a></p>` : '';
    const chartsLinks = (result.chart_files && result.chart_files.length) ? `<p><strong>图表:</strong> ${result.chart_files.map(u=>`<a href=\"${u}\" target=\"_blank\">${u.split('/').pop()}</a>`).join(' | ')}</p>` : '';
    const csvList = result.csv_files ? Object.values(result.csv_files) : [];

            if (at === 'mechanism') {
        // 机理分析渲染：突出两个CSV对比产物
        const odObservedVsInput = csvList.find(u => /od_observed_vs_input\.csv$/i.test(u));
        const odInputVsOutput = csvList.find(u => /od_input_vs_simoutput\.csv$/i.test(u));
        const csvSection = `
          <div class="case-info">
            <p><strong>对比产物:</strong></p>
            <ul style="margin-left:16px;">
              <li>观测OD vs 仿真输入flow：${odObservedVsInput ? `<a href="${odObservedVsInput}" target="_blank">od_observed_vs_input.csv</a>` : '未生成'}</li>
              <li>仿真输入flow vs 仿真输出车流：${odInputVsOutput ? `<a href="${odInputVsOutput}" target="_blank">od_input_vs_simoutput.csv</a>` : '未生成'}</li>
            </ul>
          </div>`;
        const reportLink = result.report_file ? `<p><a class="btn btn-primary" href="${result.report_file}" target="_blank">查看报告</a></p>` : '';
        area.innerHTML = `
          <div class="case-card fade-in">
            <h3>机理分析结果</h3>
            <div class="case-info">
              <p><strong>结果文件夹:</strong> ${result.result_folder || 'N/A'}</p>
              <p><strong>分析类型:</strong> ${typeLabel}</p>
              <p><strong>状态:</strong> ${result.status || 'N/A'}</p>
              ${reportLink}
              ${chartsLinks}
            </div>
            ${csvSection}
            <div style="font-size:12px;color:#666;margin-top:8px;">提示：若缺少“仿真输入 vs 仿真输出”对比，请在仿真配置中开启 tripinfo（或 vehroute）。</div>
          </div>`;
        return;
    }

            if (at === 'performance') {
            // 性能分析渲染：强调运行耗时与summary统计
            const eff = result.efficiency || {};
            const chartsLinksPerf = (result.chart_files && result.chart_files.length) ? `<p><strong>图表:</strong> ${result.chart_files.map(u=>`<a href=\"${u}\" target=\"_blank\">${u.split('/').pop()}</a>`).join(' | ')}</p>` : '';
            const csvListPerf = result.csv_files ? Object.values(result.csv_files) : [];
            const csvLinksPerf = (csvListPerf.length) ? `<p><strong>CSV:</strong> ${csvListPerf.map(u=>`<a href=\"${u}\" target=\"_blank\">${u.split('/').pop()}</a>`).join(' | ')}</p>` : '';
            const reportLinkPerf = result.report_file ? `<p><a class="btn btn-primary" href="${result.report_file}" target="_blank">查看报告</a></p>` : '';
            const summaryStats = result.analysis_summary || {};
            const summaryHTML = Object.keys(summaryStats).length ? `
              <div class="case-info">
                <p><strong>仿真摘要:</strong> steps=${summaryStats.total_steps ?? '—'}, loaded_total=${summaryStats.total_loaded ?? '—'}, inserted_total=${summaryStats.total_inserted ?? '—'}, running_max=${summaryStats.max_running ?? '—'}, waiting_max=${summaryStats.max_waiting ?? '—'}, ended_total=${summaryStats.total_ended ?? '—'}</p>
              </div>` : '';
            const perfHTML = `
              <div class="case-info">
                <p><strong>分析耗时:</strong> ${eff.total_time ?? '—'}</p>
                <p><strong>图表产出:</strong> ${eff.chart_count ?? '—'} 个</p>
                <p><strong>报告大小:</strong> ${eff.report_size ?? '—'}</p>
              </div>`;

        area.innerHTML = `
          <div class="case-card fade-in">
            <h3>性能分析结果</h3>
            <div class="case-info">
              <p><strong>结果文件夹:</strong> ${result.result_folder || 'N/A'}</p>
              <p><strong>分析类型:</strong> ${typeLabel}</p>
              <p><strong>状态:</strong> ${result.status || 'N/A'}</p>
              ${reportLinkPerf}
              ${chartsLinksPerf}
              ${csvLinksPerf}
            </div>
            <h4>效率</h4>
            ${perfHTML}
            ${summaryHTML}
          </div>`;
        return;
    }

    // 精度/性能默认渲染（沿用原模板，精度有指标，性能可拓展）
    const m = result.metrics || {};
    const flowMape = firstNonNull(m.flow_mape, m.mape);
    const gehMean = firstNonNull(m.flow_geh_mean, m.geh_mean);
    const gehPass = firstNonNull(m.flow_geh_pass_rate, m.geh_pass_rate);
    const sampleSize = firstNonNull(m.flow_sample_size, m.sample_size);
    const src = result.source_stats || {};
    const ali = result.alignment || {};

    const mapeColor = (v)=> (isFiniteNumber(v) ? (v <= 15 ? '#27ae60' : v <= 30 ? '#f39c12' : '#e74c3c') : '#7f8c8d');
    const gehPassColor = (v)=> (isFiniteNumber(v) ? (v >= 75 ? '#27ae60' : v >= 60 ? '#f39c12' : '#e74c3c') : '#7f8c8d');
    const failColor = (v)=> (v > 0 ? '#e74c3c' : '#27ae60');

    const overviewHTML = `
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:10px 0;">
        <div style="background:#f6f8fa;border-radius:8px;padding:12px;text-align:center;">
          <div style="opacity:.8;font-size:12px;">MAPE</div>
          <div style="font-size:22px;font-weight:600;color:${mapeColor(flowMape)};">${fmtPercent(flowMape)}</div>
          <div style="opacity:.7;font-size:12px;">目标≤15%</div>
        </div>
        <div style="background:#f6f8fa;border-radius:8px;padding:12px;text-align:center;">
          <div style="opacity:.8;font-size:12px;">GEH均值</div>
          <div style="font-size:22px;font-weight:600;">${fmtNumber(gehMean,2)}</div>
          <div style="opacity:.7;font-size:12px;">目标≤5</div>
        </div>
        <div style="background:#f6f8fa;border-radius:8px;padding:12px;text-align:center;">
          <div style="opacity:.8;font-size:12px;">GEH合格率</div>
          <div style="font-size:22px;font-weight:600;color:${gehPassColor(gehPass)};">${fmtPercent(gehPass)}</div>
          <div style="opacity:.7;font-size:12px;">参考≥75%</div>
        </div>
        <div style="background:#f6f8fa;border-radius:8px;padding:12px;text-align:center;">
          <div style="opacity:.8;font-size:12px;">样本量</div>
          <div style="font-size:22px;font-weight:600;">${isFiniteNumber(sampleSize)?Math.round(sampleSize):'—'}</div>
          <div style="opacity:.7;font-size:12px;">有效记录</div>
        </div>
      </div>`;

    const sourceHTML = `
      <div class="case-info">
        <p><strong>数据源:</strong> ${src.data_source_used || '—'}</p>
        <p><strong>E1文件:</strong> 共 ${src.e1_total_files ?? '—'}，有效 ${src.e1_valid_tables ?? '—'}，解析失败 <span style="color:${failColor(src.e1_parse_failures||0)};">${src.e1_parse_failures ?? 0}</span></p>
      </div>`;

    const alignHTML = `
      <div class="case-info">
        <p><strong>公共列:</strong> ${(ali.common_columns && ali.common_columns.length) ? ali.common_columns.join(', ') : '—'}</p>
        <p><strong>MAPE零分母策略:</strong> ${ali.mape_zero_policy || 'filter'}${ali.mape_zero_policy==='epsilon' ? `（epsilon=${ali.mape_epsilon}）` : ''}</p>
      </div>`;

    const csvLinks = (csvList && csvList.length) ? `<p><strong>CSV:</strong> ${csvList.map(u=>`<a href=\"${u}\" target=\"_blank\">${u.split('/').pop()}</a>`).join(' | ')}</p>` : '';

    area.innerHTML = `
      <div class="case-card fade-in">
        <h3>${typeLabel}分析结果</h3>
        <div class="case-info">
          <p><strong>结果文件夹:</strong> ${result.result_folder || 'N/A'}</p>
          <p><strong>分析类型:</strong> ${typeLabel}</p>
          <p><strong>开始时间:</strong> ${result.started_at || 'N/A'}</p>
          <p><strong>状态:</strong> ${result.status || 'N/A'}</p>
          ${reportLink}
          ${chartsLinks}
          ${csvLinks}
        </div>
        <h4>概览</h4>
        ${overviewHTML}
        <h4>数据源</h4>
        ${sourceHTML}
        <h4>对齐策略</h4>
        ${alignHTML}
      </div>`;
}

// =============== 辅助格式化 ===============
function isFiniteNumber(v) { return typeof v === 'number' && isFinite(v); }
function firstNonNull(...vals) { for (const v of vals) { if (v !== undefined && v !== null) return v; } return undefined; }
function fmtNumber(v, digits=2) { return isFiniteNumber(v) ? v.toFixed(digits) : '—'; }
function fmtPercent(v, digits=1) { return isFiniteNumber(v) ? `${v.toFixed(digits)}%` : '—'; }
function fmtBytes(b) {
  const n = Number(b);
  if (!isFinite(n) || n <= 0) return '—';
  const units = ['B','KB','MB','GB','TB'];
  const i = Math.floor(Math.log(n)/Math.log(1024));
  return `${(n/Math.pow(1024,i)).toFixed(1)} ${units[i]}`;
}
function fmtDuration(sec) {
  const n = Number(sec);
  if (!isFinite(n) || n < 0) return '—';
  if (n < 60) return `${n.toFixed(1)} s`;
  const m = Math.floor(n/60); const s = Math.round(n%60);
  return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
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

/**
 * 修复时间输入框格式问题
 */
function fixTimeInputFormats() {
    const startTimeInput = document.getElementById('start-time');
    const endTimeInput = document.getElementById('end-time');
    
    if (startTimeInput && endTimeInput) {
        // 设置默认时间值
        const now = new Date();
        const startTime = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 8, 0, 0);
        const endTime = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 8, 15, 0);
        
        // 格式化为 YYYY-MM-DDTHH:MM 格式
        startTimeInput.value = startTime.toISOString().slice(0, 16);
        endTimeInput.value = endTime.toISOString().slice(0, 16);
        
        // 添加输入验证
        startTimeInput.addEventListener('change', function() {
            const value = this.value;
            if (value && !isValidTimeFormat(value)) {
                console.warn('开始时间格式无效:', value);
                // 尝试修复格式
                const fixedValue = fixTimeFormat(value);
                if (fixedValue) {
                    this.value = fixedValue;
                }
            }
        });
        
        endTimeInput.addEventListener('change', function() {
            const value = this.value;
            if (value && !isValidTimeFormat(value)) {
                console.warn('结束时间格式无效:', value);
                // 尝试修复格式
                const fixedValue = fixTimeFormat(value);
                if (fixedValue) {
                    this.value = fixedValue;
                }
            }
        });
    }
}

/**
 * 验证时间格式是否正确
 */
function isValidTimeFormat(timeStr) {
    const timeRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/;
    return timeRegex.test(timeStr);
}

/**
 * 修复时间格式
 */
function fixTimeFormat(timeStr) {
    try {
        // 尝试解析时间字符串
        const date = new Date(timeStr);
        if (isNaN(date.getTime())) {
            return null;
        }
        // 返回正确的格式
        return date.toISOString().slice(0, 16);
    } catch (e) {
        console.error('时间格式修复失败:', e);
        return null;
    }
}

// 初始化时设置默认时间
document.addEventListener('DOMContentLoaded', () => {
    // try { setDefaultLastWeekMonday0800To0900(); } catch {}
}); 