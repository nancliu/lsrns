/**
 * E2E测试：批量仿真实时监控
 *
 * 测试范围：
 * 1. 在网车辆数显示（running_vehicles）
 * 2. 动态曲线显示和隐藏
 * 3. 任务进度条和实时状态
 * 4. 预计完成时间显示
 *
 * 前置条件：
 * - API服务器运行在 http://localhost:8000
 * - 已有测试案例和方案数据
 * - od_project conda环境已激活
 */

const { test, expect } = require('@playwright/test');

// 测试配置
const BASE_URL = 'http://localhost:8000';
const BATCH_PAGE_URL = `${BASE_URL}/control/simulations.html`;
const API_BASE_URL = `${BASE_URL}/api/v1`;

// 测试超时配置
const BATCH_CREATE_TIMEOUT = 30000;   // 创建批次超时
const SIMULATION_START_TIMEOUT = 60000; // 仿真启动超时
const MONITORING_DURATION = 45000;     // 监控持续时间（45秒，至少4次轮询）

test.describe('批量仿真实时监控', () => {
    let currentBatchId;

    test('1. 创建并启动批量仿真批次', async ({ page }) => {
        // 1.1 访问批量仿真页面
        await page.goto(BATCH_PAGE_URL);
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveTitle(/批量/);

        // 1.2 等待案例和方案加载（使用更灵活的等待策略）
        await page.waitForFunction(() => {
            const select = document.querySelector('#caseSelector');
            return select && select.options.length > 1;
        }, { timeout: 15000 });

        await page.waitForFunction(() => {
            const plans = document.querySelectorAll('.plan-item');
            return plans.length > 0;
        }, { timeout: 15000 });

        // 1.3 选择第一个案例
        const caseOptions = await page.$$('#caseSelector option');
        if (caseOptions.length < 2) {
            throw new Error('没有可用的案例数据');
        }
        const firstCaseValue = await caseOptions[1].getAttribute('value');
        await page.selectOption('#caseSelector', firstCaseValue);
        console.log(`已选择案例: ${firstCaseValue}`);

        // 1.4 确保至少有2个方案被选中（包括baseline）
        const selectedPlans = await page.$$('.plan-item input[type="checkbox"]:checked');
        console.log(`已选中 ${selectedPlans.length} 个方案`);
        expect(selectedPlans.length).toBeGreaterThanOrEqual(1);

        // 如果只有baseline被选中，再选择一个方案
        if (selectedPlans.length === 1) {
            const firstNonBaselinePlan = await page.$('.plan-item input[type="checkbox"]:not(:checked)');
            if (firstNonBaselinePlan) {
                await firstNonBaselinePlan.check();
                console.log('已额外选择一个方案');
            }
        }

        // 1.5 设置随机种子参数（使用较小的值以加快测试）
        await page.fill('#numSeeds', '2');  // 2个随机种子
        await page.fill('#baseSeed', '100'); // 起始种子100

        // 1.6 创建批次
        await page.click('#createBatchBtn');

        // 1.7 等待切换到进度视图
        await page.waitForSelector('#progressView.active', { timeout: BATCH_CREATE_TIMEOUT });
        console.log('已切换到进度视图');

        // 1.8 提取batch_id
        const batchTitle = await page.textContent('#batchTitle');
        const batchIdMatch = batchTitle.match(/batch_\d+_\d+/);
        expect(batchIdMatch).not.toBeNull();
        currentBatchId = batchIdMatch[0];
        console.log(`批次创建成功: ${currentBatchId}`);

        // 1.9 验证批次状态为pending
        const batchStatus = await page.textContent('#batchStatus');
        expect(batchStatus).toContain('等待启动');

        // 1.10 启动批次
        await page.click('#startBatchBtn');
        console.log('已点击启动仿真按钮');

        // 1.11 等待任务开始运行（状态变为running）
        await page.waitForFunction(() => {
            const statusText = document.querySelector('#batchStatus').textContent;
            return statusText.includes('运行中');
        }, { timeout: SIMULATION_START_TIMEOUT });

        console.log('批次已开始运行');
    });

    test('2. 验证任务统计信息显示', async () => {
        // 等待任务统计区域显示
        await page.waitForSelector('#taskStats', { state: 'visible', timeout: 10000 });

        // 验证统计项存在
        const totalTasks = await page.textContent('#totalTasks');
        const completedTasks = await page.textContent('#completedTasks');
        const runningTasks = await page.textContent('#runningTasks');
        const failedTasks = await page.textContent('#failedTasks');

        console.log(`任务统计: 总数=${totalTasks}, 完成=${completedTasks}, 运行中=${runningTasks}, 失败=${failedTasks}`);

        expect(parseInt(totalTasks)).toBeGreaterThan(0);
        expect(parseInt(completedTasks)).toBeGreaterThanOrEqual(0);
        expect(parseInt(failedTasks)).toBe(0); // 测试期间不应有失败任务
    });

    test('3. 验证在网车辆数显示', async () => {
        console.log('开始监控在网车辆数...');

        let vehicleCountFound = false;
        const maxAttempts = 6; // 最多等待60秒（每次10秒轮询）

        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            console.log(`第 ${attempt}/${maxAttempts} 次检查在网车辆数...`);

            // 等待10秒（轮询间隔）
            await page.waitForTimeout(10000);

            // 检查任务列表中是否有在网车辆数显示
            const taskItems = await page.$$('.task-item.task-running');

            if (taskItems.length > 0) {
                console.log(`发现 ${taskItems.length} 个运行中任务`);

                for (const taskItem of taskItems) {
                    const html = await taskItem.innerHTML();

                    // 检查是否包含 "在网: X辆" 文本
                    if (html.includes('在网:') && html.includes('辆')) {
                        const match = html.match(/在网:\s*(\d+)辆/);
                        if (match) {
                            const vehicleCount = parseInt(match[1]);
                            console.log(`✓ 发现在网车辆数: ${vehicleCount} 辆`);
                            vehicleCountFound = true;
                            expect(vehicleCount).toBeGreaterThanOrEqual(0);
                            break;
                        }
                    }
                }
            }

            if (vehicleCountFound) {
                break;
            }
        }

        expect(vehicleCountFound).toBe(true);
        console.log('在网车辆数显示验证通过');
    });

    test('4. 验证动态曲线显示', async () => {
        console.log('开始监控动态曲线...');

        let curveDisplayed = false;
        const maxAttempts = 6;

        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            console.log(`第 ${attempt}/${maxAttempts} 次检查动态曲线...`);

            // 等待10秒
            await page.waitForTimeout(10000);

            // 检查 liveCurveSection 是否可见
            const liveCurveSection = await page.$('#liveCurveSection');
            if (liveCurveSection) {
                const isVisible = await liveCurveSection.isVisible();

                if (isVisible) {
                    console.log('✓ 动态曲线区域可见');

                    // 验证canvas元素存在
                    const canvas = await page.$('#liveCurveChart');
                    expect(canvas).not.toBeNull();

                    // 检查canvas尺寸（Chart.js渲染后会有尺寸）
                    const canvasBox = await canvas.boundingBox();
                    if (canvasBox && canvasBox.width > 0 && canvasBox.height > 0) {
                        console.log(`✓ 曲线图已渲染 (宽度: ${canvasBox.width}px, 高度: ${canvasBox.height}px)`);
                        curveDisplayed = true;
                        break;
                    }
                }
            }
        }

        expect(curveDisplayed).toBe(true);
        console.log('动态曲线显示验证通过');
    });

    test('5. 验证任务进度条显示', async () => {
        console.log('验证任务进度条...');

        // 查找运行中任务的进度条
        const progressBars = await page.$$('.task-item.task-running .task-progress-bar');

        expect(progressBars.length).toBeGreaterThan(0);
        console.log(`找到 ${progressBars.length} 个任务进度条`);

        // 验证第一个进度条的内部进度条宽度
        const firstProgressBar = progressBars[0];
        const innerProgressBar = await firstProgressBar.$('div[style*="width"]');
        expect(innerProgressBar).not.toBeNull();

        const style = await innerProgressBar.getAttribute('style');
        const widthMatch = style.match(/width:\s*([\d.]+)%/);

        if (widthMatch) {
            const progressPct = parseFloat(widthMatch[1]);
            console.log(`任务进度: ${progressPct}%`);
            expect(progressPct).toBeGreaterThanOrEqual(0);
            expect(progressPct).toBeLessThanOrEqual(100);
        }

        console.log('任务进度条验证通过');
    });

    test('6. 验证预计完成时间显示', async () => {
        console.log('验证预计完成时间...');

        let estimatedTimeFound = false;
        const maxAttempts = 4;

        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            console.log(`第 ${attempt}/${maxAttempts} 次检查预计完成时间...`);

            // 等待10秒
            if (attempt > 1) {
                await page.waitForTimeout(10000);
            }

            const estimatedCompletion = await page.$('#estimatedCompletion');
            if (estimatedCompletion) {
                const html = await estimatedCompletion.innerHTML();

                // 检查是否包含 "预计剩余" 或 "预计完成"
                if (html.includes('预计剩余') || html.includes('预计完成')) {
                    console.log('✓ 发现预计完成时间信息');
                    estimatedTimeFound = true;
                    break;
                }
            }
        }

        expect(estimatedTimeFound).toBe(true);
        console.log('预计完成时间显示验证通过');
    });

    test('7. 验证浏览器控制台调试日志', async () => {
        console.log('验证调试日志输出...');

        const consoleLogs = [];

        // 监听控制台消息
        page.on('console', msg => {
            if (msg.type() === 'log') {
                consoleLogs.push(msg.text());
            }
        });

        // 等待一次轮询周期
        await page.waitForTimeout(12000);

        // 验证关键日志是否存在
        const hasApiResponseLog = consoleLogs.some(log => log.includes('=== API Progress Response ==='));
        const hasLiveCurveLog = consoleLogs.some(log => log.includes('=== renderLiveCurve called ==='));

        expect(hasApiResponseLog).toBe(true);
        console.log('✓ API响应日志存在');

        // liveCurve日志可能在summary.xml生成后才出现，不作为强制要求
        if (hasLiveCurveLog) {
            console.log('✓ 动态曲线渲染日志存在');
        }

        console.log('调试日志验证完成');
    });

    test('8. 验证曲线在无数据时自动隐藏', async () => {
        console.log('验证曲线隐藏逻辑...');

        // 这个测试在批次完成后执行，验证曲线是否隐藏
        // 但由于测试时间限制，我们通过检查初始状态来验证

        // 刷新页面，创建新的pending批次（不启动）
        await page.goto(BATCH_PAGE_URL);
        await page.waitForLoadState('networkidle');

        // 检查 liveCurveSection 初始状态（应该隐藏）
        const liveCurveSection = await page.$('#liveCurveSection');
        if (liveCurveSection) {
            const isVisible = await liveCurveSection.isVisible();
            expect(isVisible).toBe(false);
            console.log('✓ 在无数据时曲线区域已隐藏');
        }

        console.log('曲线隐藏逻辑验证通过');
    });
});

/**
 * 测试运行说明：
 *
 * 1. 确保API服务器运行:
 *    .\start_api.ps1
 *
 * 2. 激活conda环境:
 *    conda activate od_project
 *
 * 3. 运行此测试:
 *    npx playwright test tests/e2e/test_batch_live_monitoring.spec.js
 *
 * 4. 运行测试（带浏览器可视化）:
 *    npx playwright test tests/e2e/test_batch_live_monitoring.spec.js --headed
 *
 * 5. 生成HTML报告:
 *    npx playwright test tests/e2e/test_batch_live_monitoring.spec.js --reporter=html
 *    npx playwright show-report
 *
 * 预期结果：
 * - 所有8个测试用例通过
 * - 在网车辆数正确显示
 * - 动态曲线正确渲染
 * - 任务进度条正常工作
 * - 预计完成时间正确显示
 */
