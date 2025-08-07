// API基础URL
// 使用相对路径，这样API请求会发送到提供页面的同一服务器
// const API_BASE_URL = 'http://127.0.0.1:7999';
const API_BASE_URL = '';

// API请求配置
const API_CONFIG = {
    baseUrl: 'http://127.0.0.1:7999',
    timeout: 120000, // 超时时间设置为120秒
    retryCount: 2    // 失败后重试次数
};

// API连接状态检测
let apiConnectionStatus = {
    isConnected: false,
    lastCheck: null,
    errorMessage: null
};

// DOM元素
document.addEventListener('DOMContentLoaded', () => {
    // 显示API连接信息
    const apiInfo = document.createElement('div');
    apiInfo.className = 'api-info';
    apiInfo.innerHTML = `
        <p><strong>API连接信息:</strong></p>
        <p>当前配置的API地址: ${API_CONFIG.baseUrl}</p>
        <p>请求超时时间: ${API_CONFIG.timeout/1000}秒</p>
        <p>请求重试次数: ${API_CONFIG.retryCount}次</p>
        <p>连接状态: <span id="connectionStatus">检测中...</span></p>
        <p>如需修改API配置，请编辑script.js文件中的API_CONFIG变量。</p>
    `;
    document.querySelector('.container').insertBefore(apiInfo, document.querySelector('.card'));
    
    // 检测API连接状态
    checkApiConnection();
    
    // OD数据处理表单
    const odForm = document.getElementById('odForm');
    const processResult = document.getElementById('processResult');
    
    // 仿真运行表单
    const simulationForm = document.getElementById('simulationForm');
    const simulationResult = document.getElementById('simulationResult');
    
    // 精度分析表单
    const accuracyForm = document.getElementById('accuracyForm');
    const accuracyResult = document.getElementById('accuracyResult');
    
    // 状态查询表单
    const statusForm = document.getElementById('statusForm');
    const statusResult = document.getElementById('statusResult');
    
    // 处理OD数据表单提交
    odForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 检查API连接状态
        if (!apiConnectionStatus.isConnected) {
            processResult.className = 'result-box show error';
            processResult.textContent = `❌ API服务器未连接\n\n请确保FastAPI服务器正在运行。\n\n检查步骤：\n1. 运行 start_api_test.bat 启动服务器\n2. 访问 http://127.0.0.1:7999/docs 确认API可用\n3. 检查控制台是否有错误信息`;
            return;
        }
        
        // 显示加载状态
        processResult.textContent = '处理中，请稍候...\n这可能需要几分钟时间，请耐心等待。';
        processResult.className = 'result-box show';
        
        // 获取表单数据
        const data = {
            start_time: document.getElementById('startTime').value,
            end_time: document.getElementById('endTime').value,
            taz_file: document.getElementById('tazFile').value,
            net_file: document.getElementById('netFile').value,
            interval_minutes: parseInt(document.getElementById('intervalMinutes').value),
            enable_mesoscopic: document.getElementById('enableMesoscopic').checked,
            output_summary: document.getElementById('outputSummary').checked,
            output_tripinfo: document.getElementById('outputTripinfo').checked,
            output_vehroute: document.getElementById('outputVehroute').checked,
            output_fcd: document.getElementById('outputFcd').checked,
            output_netstate: document.getElementById('outputNetstate').checked,
            output_emission: document.getElementById('outputEmission').checked
        };
        
        // 验证输入数据
        const validationError = validateOdData(data);
        if (validationError) {
            processResult.className = 'result-box show error';
            processResult.textContent = `❌ 输入验证失败: ${validationError}`;
            return;
        }
        
        // 使用带超时和重试的API调用
        fetchWithTimeout(`${API_CONFIG.baseUrl}/process_od_data/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        }, API_CONFIG.timeout, API_CONFIG.retryCount)
        .then(async response => {
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! Status: ${response.status}, Text: ${errorText}`);
            }
            return response.json();
        })
        .then(result => {
            // 成功响应
            processResult.className = 'result-box show success';
            
            // 格式化显示结果
            const formattedResult = `✅ 处理成功！

运行文件夹: ${result.run_folder}
OD文件: ${result.od_file}
路由文件: ${result.route_file}
配置文件: ${result.sumocfg_file}

您可以使用这些信息填写下方的"运行仿真"表单。`;
            
            processResult.textContent = formattedResult;
            
            // 自动填充仿真表单
            document.getElementById('runFolder').value = result.run_folder;
            
            // 显示自动填充提示
            console.log('已自动填充仿真表单参数');
            showAutoFillNotification('已自动填充仿真表单参数');
        })
        .catch(error => {
            // 网络错误或其他异常
            processResult.className = 'result-box show error';
            
            let errorMessage = `❌ 错误: ${error.message}\n\n`;
            
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                errorMessage += `可能的原因：\n1. FastAPI服务器未运行\n2. 网络连接问题\n3. 防火墙阻止连接\n\n建议操作：\n1. 检查FastAPI服务器是否正在运行\n2. 尝试直接访问: http://127.0.0.1:7999/docs 检查API服务器\n3. 检查网络连接和防火墙设置`;
            } else if (error.message.includes('timeout')) {
                errorMessage += `可能的原因：\n1. 处理大量数据时超时\n2. 数据库查询时间过长\n3. 服务器资源不足\n\n建议操作：\n1. 尝试减小时间范围或增加时间间隔\n2. 检查数据库连接状态\n3. 查看FastAPI服务器控制台输出`;
            } else if (error.message.includes('HTTP error! Status: 500')) {
                errorMessage += `可能的原因：\n1. 服务器内部错误\n2. 数据库连接问题\n3. 文件路径错误\n\n建议操作：\n1. 查看FastAPI服务器控制台输出\n2. 检查数据库连接\n3. 确认文件路径是否正确`;
            } else {
                errorMessage += `可能的原因：\n1. FastAPI服务器未运行\n2. 数据库连接问题\n3. 请求处理超时（处理大量数据时可能需要很长时间）\n\n建议操作：\n1. 检查FastAPI服务器是否正在运行\n2. 尝试直接访问: http://127.0.0.1:7999/docs 检查API服务器\n3. 尝试减小时间范围或增加时间间隔\n4. 查看FastAPI服务器控制台输出是否有错误信息`;
            }
            
            processResult.textContent = errorMessage;
        });
    });
    
    // 运行仿真表单提交
    simulationForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 检查API连接状态
        if (!apiConnectionStatus.isConnected) {
            simulationResult.className = 'result-box show error';
            simulationResult.textContent = `❌ API服务器未连接\n\n请确保FastAPI服务器正在运行。`;
            return;
        }
        
        // 获取运行文件夹
        const runFolder = document.getElementById('runFolder').value;
        const gui = document.getElementById('guiMode').checked;
        
        // 验证输入数据
        if (!runFolder || runFolder.trim() === '') {
            simulationResult.className = 'result-box show error';
            simulationResult.textContent = '❌ 请输入运行文件夹名称';
            return;
        }
        
        // 自动推导文件路径
        const data = {
            run_folder: runFolder,
            od_file: `${runFolder}/dwd_od_weekly_*.od.xml`,
            route_file: `${runFolder}/dwd_od_weekly_*.rou.xml`,
            sumocfg_file: `${runFolder}/simulation.sumocfg`,
            gui: gui
        };
        
        // 显示加载状态
        simulationResult.textContent = '正在启动仿真，请稍候...';
        simulationResult.className = 'result-box show';
        
        // 使用带超时和重试的API调用
        fetchWithTimeout(`${API_CONFIG.baseUrl}/run_simulation/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        }, API_CONFIG.timeout, API_CONFIG.retryCount)
        .then(async response => {
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! Status: ${response.status}, Text: ${errorText}`);
            }
            return response.json();
        })
        .then(result => {
            simulationResult.className = 'result-box show success';
            
            // 根据是否使用GUI模式显示不同的成功消息
            if (result.status === "SUMO GUI launched") {
                simulationResult.textContent = `✅ SUMO GUI已启动！\n\n` +
                    `SUMO GUI正在运行中，请查看是否有新窗口打开。\n\n` +
                    `运行文件夹: ${result.run_folder}\n` +
                    `进程ID: ${result.pid}\n\n` +
                    `如果没有看到SUMO GUI窗口，请检查:\n` +
                    `1. SUMO是否正确安装\n` +
                    `2. 是否有足够的权限运行GUI应用\n` +
                    `3. 查看FastAPI服务器控制台输出是否有错误信息`;
                
                // 自动填充精度分析表单
                document.getElementById('simFolder').value = result.run_folder;
                console.log(`已自动填充精度分析表单: ${result.run_folder}`);
                showAutoFillNotification(`已自动填充精度分析表单: ${result.run_folder}`);
            } else {
                simulationResult.textContent = `✅ 仿真已完成！\n\n${JSON.stringify(result, null, 2)}`;
                
                // 自动填充精度分析表单
                if (result.run_folder) {
                    document.getElementById('simFolder').value = result.run_folder;
                    console.log(`已自动填充精度分析表单: ${result.run_folder}`);
                }
            }
        })
        .catch(error => {
            simulationResult.className = 'result-box show error';
            
            let errorMessage = `❌ 错误: ${error.message}\n\n`;
            
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                errorMessage += `可能的原因：\n1. FastAPI服务器未运行\n2. 网络连接问题\n\n建议操作：\n1. 检查FastAPI服务器是否正在运行\n2. 尝试直接访问: http://127.0.0.1:7999/docs 检查API服务器`;
            } else if (error.message.includes('HTTP error! Status: 500')) {
                errorMessage += `可能的原因：\n1. 仿真文件路径不正确\n2. SUMO未正确安装或配置\n3. 文件权限问题\n\n建议操作：\n1. 确认文件路径是否正确\n2. 检查SUMO是否正确安装\n3. 查看FastAPI服务器控制台输出`;
            } else {
                errorMessage += `可能的原因：\n1. FastAPI服务器未运行\n2. 仿真文件路径不正确\n3. SUMO未正确安装或配置\n\n建议操作：\n1. 检查FastAPI服务器是否正在运行\n2. 确认文件路径是否正确\n3. 查看FastAPI服务器控制台输出是否有错误信息`;
            }
            
            simulationResult.textContent = errorMessage;
        });
    });
    
    // 精度分析表单提交
    accuracyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 检查API连接状态
        if (!apiConnectionStatus.isConnected) {
            accuracyResult.className = 'result-box show error';
            accuracyResult.textContent = `❌ API服务器未连接\n\n请确保FastAPI服务器正在运行。`;
            return;
        }
        
        // 显示加载状态
        accuracyResult.textContent = '正在进行精度分析，请稍候...\n这可能需要几分钟时间，请耐心等待。';
        accuracyResult.className = 'result-box show';
        
        // 获取表单数据
        const data = {
            sim_folder: document.getElementById('simFolder').value
        };
        
        // 验证输入数据
        if (!data.sim_folder || data.sim_folder.trim() === '') {
            accuracyResult.className = 'result-box show error';
            accuracyResult.textContent = '❌ 请输入仿真结果文件夹名称';
            return;
        }
        
        // 使用带超时和重试的API调用
        fetchWithTimeout(`${API_CONFIG.baseUrl}/analyze_accuracy/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        }, API_CONFIG.timeout, API_CONFIG.retryCount)
        .then(async response => {
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! Status: ${response.status}, Text: ${errorText}`);
            }
            return response.json();
        })
        .then(result => {
            if (result.success) {
                accuracyResult.className = 'result-box show success';
                
                const formattedResult = `✅ 精度分析已启动！

结果文件夹: ${result.output_folder}
分析状态: 正在处理中

请等待分析完成，然后使用下方的"精度分析状态查询"功能查看结果。`;
                
                accuracyResult.textContent = formattedResult;
                
                // 自动填充状态查询表单
                document.getElementById('resultFolder').value = result.output_folder;
                showAutoFillNotification(`已自动填充状态查询表单: ${result.output_folder}`);
            } else {
                accuracyResult.className = 'result-box show error';
                accuracyResult.textContent = `❌ 精度分析失败: ${result.error || '未知错误'}`;
            }
        })
        .catch(error => {
            accuracyResult.className = 'result-box show error';
            
            let errorMessage = `❌ 错误: ${error.message}\n\n`;
            
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                errorMessage += `可能的原因：\n1. FastAPI服务器未运行\n2. 网络连接问题\n\n建议操作：\n1. 检查FastAPI服务器是否正在运行\n2. 尝试直接访问: http://127.0.0.1:7999/docs 检查API服务器`;
            } else {
                errorMessage += `可能的原因：\n1. FastAPI服务器未运行\n2. 仿真文件夹不存在或路径错误\n3. 精度分析模块未正确安装\n\n建议操作：\n1. 检查FastAPI服务器是否正在运行\n2. 确认仿真文件夹路径是否正确\n3. 查看FastAPI服务器控制台输出是否有错误信息`;
            }
            
            accuracyResult.textContent = errorMessage;
        });
    });
    
    // 状态查询表单提交
    statusForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 检查API连接状态
        if (!apiConnectionStatus.isConnected) {
            statusResult.className = 'result-box show error';
            statusResult.textContent = `❌ API服务器未连接\n\n请确保FastAPI服务器正在运行。`;
            return;
        }
        
        // 显示加载状态
        statusResult.textContent = '正在查询状态，请稍候...';
        statusResult.className = 'result-box show';
        
        // 获取表单数据
        const resultFolder = document.getElementById('resultFolder').value;
        
        // 验证输入数据
        if (!resultFolder || resultFolder.trim() === '') {
            statusResult.className = 'result-box show error';
            statusResult.textContent = '❌ 请输入结果文件夹名称';
            return;
        }
        
        // 使用带超时和重试的API调用
        fetchWithTimeout(`${API_CONFIG.baseUrl}/accuracy_analysis_status/${resultFolder}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        }, API_CONFIG.timeout, API_CONFIG.retryCount)
        .then(async response => {
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! Status: ${response.status}, Text: ${errorText}`);
            }
            return response.json();
        })
        .then(result => {
            if (result.exists) {
                statusResult.className = 'result-box show success';
                
                // 格式化显示结果
                let formattedResult = `✅ 分析结果已找到！

结果文件夹: ${result.result_folder}
结果路径: ${result.result_path}

文件状态:`;
                
                if (result.files_status.html_report) {
                    formattedResult += '\n✅ HTML报告: 已生成';
                } else {
                    formattedResult += '\n❌ HTML报告: 未生成';
                }
                
                if (result.files_status.charts_folder) {
                    formattedResult += '\n✅ 图表文件夹: 已生成';
                } else {
                    formattedResult += '\n❌ 图表文件夹: 未生成';
                }
                
                formattedResult += '\n\nCSV文件状态:';
                Object.entries(result.files_status.csv_files).forEach(([file, exists]) => {
                    formattedResult += `\n${exists ? '✅' : '❌'} ${file}: ${exists ? '已生成' : '未生成'}`;
                });
                
                statusResult.textContent = formattedResult;
            } else {
                statusResult.className = 'result-box show error';
                statusResult.textContent = `❌ 分析结果不存在: ${result.message || result.error || '未知错误'}`;
            }
        })
        .catch(error => {
            statusResult.className = 'result-box show error';
            
            let errorMessage = `❌ 错误: ${error.message}\n\n`;
            
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                errorMessage += `可能的原因：\n1. FastAPI服务器未运行\n2. 网络连接问题\n\n建议操作：\n1. 检查FastAPI服务器是否正在运行\n2. 尝试直接访问: http://127.0.0.1:7999/docs 检查API服务器`;
            } else {
                errorMessage += `可能的原因：\n1. FastAPI服务器未运行\n2. 结果文件夹路径错误\n\n建议操作：\n1. 检查FastAPI服务器是否正在运行\n2. 确认结果文件夹名称是否正确\n3. 查看FastAPI服务器控制台输出是否有错误信息`;
            }
            
            statusResult.textContent = errorMessage;
        });
    });
    
    // 初始化文件夹列表
    initializeFolderLists();
    
    // 绑定刷新按钮事件
    document.getElementById('refreshRunFolders').addEventListener('click', () => {
        refreshFolderList('runFolderList', 'run_');
    });
    
    document.getElementById('refreshSimFolders').addEventListener('click', () => {
        refreshFolderList('simFolderList', 'run_');
    });
    
    document.getElementById('refreshResultFolders').addEventListener('click', () => {
        refreshFolderList('resultFolderList', 'accuracy_results_');
    });
});

/**
 * 检测API连接状态
 */
async function checkApiConnection() {
    const statusElement = document.getElementById('connectionStatus');
    
    try {
        const response = await fetch(`${API_CONFIG.baseUrl}/docs`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            apiConnectionStatus.isConnected = true;
            apiConnectionStatus.lastCheck = new Date();
            apiConnectionStatus.errorMessage = null;
            statusElement.textContent = '✅ 已连接';
            statusElement.style.color = '#4CAF50';
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        apiConnectionStatus.isConnected = false;
        apiConnectionStatus.lastCheck = new Date();
        apiConnectionStatus.errorMessage = error.message;
        statusElement.textContent = '❌ 未连接';
        statusElement.style.color = '#f44336';
        
        console.warn('API连接检测失败:', error);
    }
}

/**
 * 验证OD数据输入
 * @param {Object} data - 表单数据
 * @returns {string|null} 错误信息或null
 */
function validateOdData(data) {
    // 验证时间格式
    const timeRegex = /^\d{4}\/\d{2}\/\d{2} \d{2}:\d{2}:\d{2}$/;
    
    if (!timeRegex.test(data.start_time)) {
        return '开始时间格式不正确，请使用 YYYY/MM/DD HH:MM:SS 格式';
    }
    
    if (!timeRegex.test(data.end_time)) {
        return '结束时间格式不正确，请使用 YYYY/MM/DD HH:MM:SS 格式';
    }
    
    // 验证时间逻辑
    const startTime = new Date(data.start_time);
    const endTime = new Date(data.end_time);
    
    if (startTime >= endTime) {
        return '开始时间必须早于结束时间';
    }
    
    // 验证时间间隔
    if (data.interval_minutes < 1 || data.interval_minutes > 60) {
        return '时间间隔必须在1-60分钟之间';
    }
    
    // 验证文件路径
    if (!data.taz_file || data.taz_file.trim() === '') {
        return '请输入TAZ文件路径';
    }
    
    if (!data.net_file || data.net_file.trim() === '') {
        return '请输入网络文件路径';
    }
    
    return null;
}

/**
 * 带超时和重试的fetch函数
 * @param {string} url - 请求URL
 * @param {Object} options - fetch选项
 * @param {number} timeout - 超时时间（毫秒）
 * @param {number} retries - 重试次数
 * @returns {Promise} - fetch Promise
 */
async function fetchWithTimeout(url, options, timeout = 30000, retries = 1) {
    let currentTry = 0;
    
    async function attemptFetch() {
        currentTry++;
        
        // 创建一个可以被中止的控制器
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error(`请求超时（${timeout/1000}秒）。处理大量数据时可能需要更长时间。`);
            }
            
            if (currentTry <= retries) {
                console.log(`请求失败，正在重试(${currentTry}/${retries})...`);
                return attemptFetch();
            }
            
            throw error;
        }
    }
    
    return attemptFetch();
}

/**
 * 初始化文件夹列表
 */
function initializeFolderLists() {
    // 初始化运行文件夹列表
    refreshFolderList('runFolderList', 'run_');
    
    // 初始化仿真文件夹列表
    refreshFolderList('simFolderList', 'run_');
    
    // 初始化结果文件夹列表
    refreshFolderList('resultFolderList', 'accuracy_results_');
}

/**
 * 刷新文件夹列表
 * @param {string} datalistId - datalist元素ID
 * @param {string} prefix - 文件夹前缀
 */
function refreshFolderList(datalistId, prefix) {
    const datalist = document.getElementById(datalistId);
    if (!datalist) return;
    
    // 获取对应的刷新按钮
    const refreshBtn = document.querySelector(`[onclick*="${datalistId}"]`) || 
                      document.querySelector(`[id*="refresh"]`);
    
    // 显示加载状态
    if (refreshBtn) {
        const originalText = refreshBtn.innerHTML;
        refreshBtn.innerHTML = '⏳';
        refreshBtn.disabled = true;
        
        // 获取文件夹列表
        getFolderList(prefix).then(folders => {
            // 清空现有选项
            datalist.innerHTML = '';
            
            folders.forEach(folder => {
                const option = document.createElement('option');
                option.value = folder;
                datalist.appendChild(option);
            });
            
            console.log(`已刷新 ${datalistId}，找到 ${folders.length} 个文件夹`);
            
            // 恢复按钮状态
            refreshBtn.innerHTML = originalText;
            refreshBtn.disabled = false;
            
            // 显示成功通知
            if (folders.length > 0) {
                showAutoFillNotification(`已找到 ${folders.length} 个文件夹`);
            }
        }).catch(error => {
            console.error(`刷新文件夹列表失败: ${error}`);
            
            // 恢复按钮状态
            refreshBtn.innerHTML = originalText;
            refreshBtn.disabled = false;
            
            // 显示错误通知
            showAutoFillNotification('刷新文件夹列表失败');
        });
    }
}

/**
 * 获取文件夹列表
 * @param {string} prefix - 文件夹前缀
 * @returns {Promise<Array<string>>} 文件夹名称数组
 */
async function getFolderList(prefix) {
    try {
        console.log(`正在获取前缀为 '${prefix}' 的文件夹列表...`);
        
        const response = await fetch(`${API_CONFIG.baseUrl}/get_folders/${prefix}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            console.log(`成功获取文件夹列表:`, result);
            return result.folders || [];
        } else {
            console.error(`API返回错误:`, result.error);
            return [];
        }
    } catch (error) {
        console.error(`获取文件夹列表失败: ${error}`);
        return [];
    }
}

/**
 * 显示自动填充通知
 * @param {string} message - 通知消息
 */
function showAutoFillNotification(message) {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = 'auto-fill-notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #4CAF50;
        color: white;
        padding: 10px 15px;
        border-radius: 5px;
        z-index: 1000;
        font-size: 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        animation: slideIn 0.3s ease-out;
    `;
    
    // 添加动画样式
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}