/**
 * E2E测试：批量仿真实时监控 - 前端代码验证
 *
 * 此测试专注于验证前端代码逻辑的正确性，而不依赖真实的批量仿真运行。
 * 通过模拟API响应来测试前端渲染逻辑。
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:8000';
const BATCH_PAGE_URL = `${BASE_URL}/control/simulations.html`;

test.describe('批量仿真实时监控 - 前端代码验证', () => {

    test('验证在网车辆数显示逻辑', async ({ page }) => {
        await page.goto(BATCH_PAGE_URL);
        await page.waitForLoadState('networkidle');

        // 切换到进度视图
        await page.evaluate(() => {
            // 切换到进度视图（liveCurveSection在进度视图中）
            if (typeof switchView === 'function') {
                switchView('progress');
            } else {
                // 手动切换
                document.getElementById('progressView').classList.add('active');
                document.getElementById('configView').classList.remove('active');
            }
        });

        await page.waitForTimeout(500);

        // 模拟API响应数据注入
        await page.evaluate(() => {
            // 模拟进度数据
            const mockProgressData = {
                batch_id: 'test_batch_001',
                status: 'running',
                progress: 0.5,
                total_tasks: 4,
                completed_tasks: 1,
                running_tasks: 2,
                failed_tasks: 0,
                tasks: [
                    {
                        task_id: 'task_001',
                        plan_id: 'plan_001',
                        plan_name: '测试方案1',
                        seed: 100,
                        status: 'running',
                        progress: 45,
                        live_status: {
                            current_step: 6480,
                            total_steps: 14400,
                            progress_percent: 45.0,
                            running_vehicles: 567,
                            ended_vehicles: 1234,
                            loaded_vehicles: 1801,
                            estimated_remaining_seconds: 420
                        }
                    },
                    {
                        task_id: 'task_002',
                        plan_id: 'plan_001',
                        plan_name: '测试方案1',
                        seed: 101,
                        status: 'running',
                        progress: 30,
                        live_status: {
                            current_step: 4320,
                            total_steps: 14400,
                            progress_percent: 30.0,
                            running_vehicles: 423,
                            ended_vehicles: 856,
                            loaded_vehicles: 1279
                        }
                    },
                    {
                        task_id: 'task_003',
                        plan_id: 'plan_002',
                        plan_name: '测试方案2',
                        seed: 100,
                        status: 'completed',
                        progress: 100
                    },
                    {
                        task_id: 'task_004',
                        plan_id: 'plan_002',
                        plan_name: '测试方案2',
                        seed: 101,
                        status: 'pending',
                        progress: 0
                    }
                ],
                live_time_series: {
                    time_points: [0, 100, 200, 300, 400, 500],
                    total_running: [0, 320, 580, 750, 890, 990],
                    task_count: 2,
                    last_update: '2025-10-29T10:30:00'
                },
                estimated_remaining_seconds: 600,
                estimated_completion: '2025-10-29T10:40:00'
            };

            // 调用前端的 renderTaskList 函数
            if (typeof renderTaskList === 'function') {
                renderTaskList(mockProgressData.tasks);
            }

            // 调用前端的 renderLiveCurve 函数
            if (typeof renderLiveCurve === 'function') {
                renderLiveCurve(mockProgressData.live_time_series);
            }

            // 更新任务统计
            document.getElementById('totalTasks').textContent = mockProgressData.total_tasks;
            document.getElementById('completedTasks').textContent = mockProgressData.completed_tasks;
            document.getElementById('runningTasks').textContent = mockProgressData.running_tasks;
            document.getElementById('failedTasks').textContent = mockProgressData.failed_tasks;
            document.getElementById('taskStats').style.display = 'block';
        });

        // 等待渲染完成
        await page.waitForTimeout(1000);

        // 验证1：在网车辆数显示
        const taskItems = await page.$$('.task-item.task-running');
        expect(taskItems.length).toBe(2);
        console.log(`✓ 找到 ${taskItems.length} 个运行中任务`);

        // 检查第一个任务的在网车辆数
        const firstTaskHTML = await taskItems[0].innerHTML();
        expect(firstTaskHTML).toContain('在网: 567辆');
        console.log('✓ 第一个任务显示在网车辆数: 567辆');

        // 检查第二个任务的在网车辆数
        const secondTaskHTML = await taskItems[1].innerHTML();
        expect(secondTaskHTML).toContain('在网: 423辆');
        console.log('✓ 第二个任务显示在网车辆数: 423辆');

        // 验证2：任务进度条显示
        const progressBars = await page.$$('.task-item.task-running .task-progress-bar');
        expect(progressBars.length).toBe(2);
        console.log('✓ 找到 2 个任务进度条');

        // 验证3：任务统计信息
        const totalTasks = await page.textContent('#totalTasks');
        const runningTasks = await page.textContent('#runningTasks');
        expect(totalTasks).toBe('4');
        expect(runningTasks).toBe('2');
        console.log('✓ 任务统计信息正确');

        // 验证4：动态曲线显示
        const liveCurveSection = await page.$('#liveCurveSection');
        const isVisible = await liveCurveSection.isVisible();
        expect(isVisible).toBe(true);
        console.log('✓ 动态曲线区域可见');

        // 验证canvas已渲染
        const canvas = await page.$('#liveCurveChart');
        const canvasBox = await canvas.boundingBox();
        expect(canvasBox.width).toBeGreaterThan(0);
        expect(canvasBox.height).toBeGreaterThan(0);
        console.log(`✓ 曲线图已渲染 (${canvasBox.width}x${canvasBox.height})`);
    });

    test('验证动态曲线在无数据时自动隐藏', async ({ page }) => {
        await page.goto(BATCH_PAGE_URL);
        await page.waitForLoadState('networkidle');

        // 模拟空数据
        await page.evaluate(() => {
            if (typeof renderLiveCurve === 'function') {
                // 情况1：null
                renderLiveCurve(null);
            }
        });

        await page.waitForTimeout(500);

        // 验证曲线区域隐藏
        const liveCurveSection1 = await page.$('#liveCurveSection');
        const isVisible1 = await liveCurveSection1.isVisible();
        expect(isVisible1).toBe(false);
        console.log('✓ 传入null时曲线隐藏');

        // 模拟空time_points
        await page.evaluate(() => {
            if (typeof renderLiveCurve === 'function') {
                renderLiveCurve({
                    time_points: [],
                    total_running: [],
                    task_count: 0
                });
            }
        });

        await page.waitForTimeout(500);

        const liveCurveSection2 = await page.$('#liveCurveSection');
        const isVisible2 = await liveCurveSection2.isVisible();
        expect(isVisible2).toBe(false);
        console.log('✓ 传入空数组时曲线隐藏');
    });

    test('验证任务状态图标和文本', async ({ page }) => {
        await page.goto(BATCH_PAGE_URL);
        await page.waitForLoadState('networkidle');

        // 模拟不同状态的任务
        await page.evaluate(() => {
            const tasks = [
                { task_id: 't1', plan_id: 'p1', plan_name: '方案1', seed: 1, status: 'pending', progress: 0 },
                { task_id: 't2', plan_id: 'p1', plan_name: '方案1', seed: 2, status: 'running', progress: 50, live_status: {} },
                { task_id: 't3', plan_id: 'p1', plan_name: '方案1', seed: 3, status: 'completed', progress: 100 },
                { task_id: 't4', plan_id: 'p1', plan_name: '方案1', seed: 4, status: 'failed', progress: 25 }
            ];

            if (typeof renderTaskList === 'function') {
                renderTaskList(tasks);
            }
        });

        await page.waitForTimeout(500);

        // 验证不同状态的图标
        const pendingTask = await page.$('.task-item.task-pending');
        const pendingHTML = await pendingTask.innerHTML();
        expect(pendingHTML).toContain('⏸');
        expect(pendingHTML).toContain('等待中');
        console.log('✓ pending状态显示正确');

        const runningTask = await page.$('.task-item.task-running');
        const runningHTML = await runningTask.innerHTML();
        expect(runningHTML).toContain('▶');
        expect(runningHTML).toContain('运行中');
        console.log('✓ running状态显示正确');

        const completedTask = await page.$('.task-item.task-completed');
        const completedHTML = await completedTask.innerHTML();
        expect(completedHTML).toContain('✓');
        expect(completedHTML).toContain('完成');
        console.log('✓ completed状态显示正确');

        const failedTask = await page.$('.task-item.task-failed');
        const failedHTML = await failedTask.innerHTML();
        expect(failedHTML).toContain('✗');
        expect(failedHTML).toContain('失败');
        console.log('✓ failed状态显示正确');
    });

    test('验证剩余时间格式化', async ({ page }) => {
        await page.goto(BATCH_PAGE_URL);
        await page.waitForLoadState('networkidle');

        // 测试formatDuration函数
        const testCases = await page.evaluate(() => {
            const results = [];

            if (typeof formatDuration === 'function') {
                results.push({ input: 30, expected: '30秒', actual: formatDuration(30) });
                results.push({ input: 90, expected: '1分30秒', actual: formatDuration(90) });
                results.push({ input: 3665, expected: '1小时1分', actual: formatDuration(3665) });
                results.push({ input: 0, expected: '0秒', actual: formatDuration(0) });
                results.push({ input: null, expected: '--', actual: formatDuration(null) });
            }

            return results;
        });

        testCases.forEach(tc => {
            expect(tc.actual).toBe(tc.expected);
            console.log(`✓ formatDuration(${tc.input}) = "${tc.actual}"`);
        });
    });

    test('验证进度百分比显示', async ({ page }) => {
        await page.goto(BATCH_PAGE_URL);
        await page.waitForLoadState('networkidle');

        // 模拟不同进度的任务
        await page.evaluate(() => {
            const tasks = [
                {
                    task_id: 't1',
                    plan_id: 'p1',
                    plan_name: '方案1',
                    seed: 1,
                    status: 'running',
                    progress: 75,
                    live_status: {
                        progress_percent: 75.5,
                        running_vehicles: 500
                    }
                }
            ];

            if (typeof renderTaskList === 'function') {
                renderTaskList(tasks);
            }
        });

        await page.waitForTimeout(500);

        // 验证进度显示
        const liveStatusDiv = await page.$('.task-live-status');
        const statusHTML = await liveStatusDiv.innerHTML();

        expect(statusHTML).toContain('75.5%');
        console.log('✓ 进度百分比显示正确（使用live_status的值）');
    });
});

/**
 * 运行方法：
 *
 * conda activate od_project
 * npx playwright test tests/e2e/test_batch_monitoring_frontend.spec.js
 *
 * 带浏览器可视化：
 * npx playwright test tests/e2e/test_batch_monitoring_frontend.spec.js --headed
 */
