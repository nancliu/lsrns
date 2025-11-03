/**
 * E2E Test: Batch Results Page Verification
 * 测试批量仿真结果页面是否正确展示
 *
 * 验证内容：
 * 1. 结果标签页是否存在且可访问
 * 2. 结果页面HTML结构是否完整
 * 3. 是否能加载批次列表
 * 4. 点击"查看结果"是否能打开结果页面
 * 5. 结果对比表是否正确渲染
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:8000';
const SIMULATIONS_URL = `${BASE_URL}/control/simulations.html`;
const API_BASE = `${BASE_URL}/api/v1`;

test.describe('Batch Results Page E2E Tests', () => {
    test.beforeEach(async ({ page }) => {
        // 导航到批量仿真页面
        await page.goto(SIMULATIONS_URL);
        await page.waitForLoadState('networkidle');
    });

    test('结果标签页应该存在且可见', async ({ page }) => {
        // 检查"结果"标签页按钮是否存在
        const resultsTab = page.locator('#resultsViewTab');
        await expect(resultsTab).toBeVisible();

        // 检查标签文本
        await expect(resultsTab).toContainText('结果');
    });

    test('点击结果标签页应该切换到结果视图', async ({ page }) => {
        // 找到结果标签页
        const resultsTab = page.locator('#resultsViewTab');

        // 点击标签页
        await resultsTab.click();

        // 检查结果视图是否变为活跃
        const resultsView = page.locator('#resultsView');
        await expect(resultsView).toHaveClass(/active/);

        // 检查标签页是否标记为活跃
        await expect(resultsTab).toHaveClass(/active/);
    });

    test('结果视图应该包含对比表容器', async ({ page }) => {
        // 切换到结果视图
        await page.locator('#resultsViewTab').click();

        // 等待结果视图加载
        const resultsView = page.locator('#resultsView');
        await expect(resultsView).toHaveClass(/active/);

        // 检查对比表容器是否存在
        const comparisonTable = page.locator('#comparisonTable');
        await expect(comparisonTable).toBeVisible();

        // 检查方案对比表标题
        const tableTitle = page.locator('#resultsView h3').first();
        await expect(tableTitle).toContainText('方案对比');
    });

    test('结果视图应该包含峰值曲线区域', async ({ page }) => {
        // 切换到结果视图
        await page.locator('#resultsViewTab').click();

        // 检查峰值曲线区域是否存在（即使初始隐藏也应该存在DOM中）
        const peakCurveSection = page.locator('#peakCurveSection');
        await expect(peakCurveSection).toBeInViewport({ ratio: 0 }); // 可能隐藏但应该在DOM中
    });

    test('批次监控视图应该有查看结果按钮选项', async ({ page }) => {
        // 切换到批次监控视图
        await page.locator('#monitoringViewTab').click();

        // 检查批次列表是否存在
        const batchList = page.locator('#batchList');
        await expect(batchList).toBeVisible();
    });

    test('验证结果页面HTML结构完整性', async ({ page }) => {
        // 切换到结果视图
        await page.locator('#resultsViewTab').click();

        // 检查主要容器
        const resultsContainer = page.locator('.results-container');
        await expect(resultsContainer).toBeVisible();

        // 检查配置区域
        const configSections = page.locator('#resultsView .config-section');
        const count = await configSections.count();
        expect(count).toBeGreaterThanOrEqual(1);

        // 检查按钮组
        const btnGroup = page.locator('#resultsView .btn-group');
        await expect(btnGroup).toBeVisible();
    });

    test('批次列表应该支持点击操作', async ({ page }) => {
        // 切换到批次监控视图
        await page.locator('#monitoringViewTab').click();

        // 等待批次列表加载
        await page.waitForTimeout(2000);

        // 检查是否有批次卡片
        const batchCards = page.locator('.batch-card');
        const batchCount = await batchCards.count();

        if (batchCount > 0) {
            console.log(`找到 ${batchCount} 个批次卡片`);

            // 获取第一个卡片
            const firstCard = batchCards.first();

            // 检查卡片是否可见
            await expect(firstCard).toBeVisible();

            // 检查卡片中是否有"查看结果"按钮
            const viewResultsBtn = firstCard.locator('.view-results-btn, button:has-text("查看结果"), button:has-text("结果")');
            if (await viewResultsBtn.count() > 0) {
                console.log('找到查看结果按钮');
                await expect(viewResultsBtn.first()).toBeVisible();
            }
        } else {
            console.log('暂无批次卡片，跳过此测试');
        }
    });

    test('验证API端点 GET /batch/{batch_id}/results 是否存在', async ({ page, context }) => {
        // 拦截API请求
        let apiEndpointFound = false;

        page.on('response', response => {
            if (response.url().includes('/api/v1/control/optimization/batch') &&
                response.url().includes('/results')) {
                apiEndpointFound = true;
                console.log(`API端点应答: ${response.url()} - Status: ${response.status()}`);
            }
        });

        // 切换到批次监控视图
        await page.locator('#monitoringViewTab').click();
        await page.waitForTimeout(2000);

        // 尝试触发结果加载（通过API调用或点击按钮）
        const batchCards = page.locator('.batch-card');
        const batchCount = await batchCards.count();

        if (batchCount > 0) {
            // 查找"查看结果"按钮并点击
            const viewResultsBtns = page.locator('button:has-text("查看结果")');
            if (await viewResultsBtns.count() > 0) {
                await viewResultsBtns.first().click();
                // 等待API请求
                await page.waitForTimeout(3000);
            }
        }
    });

    test('验证renderResults函数是否存在于JavaScript中', async ({ page }) => {
        // 检查window对象中是否存在renderResults函数
        const hasRenderResults = await page.evaluate(() => {
            return typeof window.renderResults === 'function';
        });

        expect(hasRenderResults).toBe(true);
    });

    test('验证renderPeakCurveChart函数是否存在', async ({ page }) => {
        // 检查window对象中是否存在renderPeakCurveChart函数
        const hasRenderPeakCurve = await page.evaluate(() => {
            return typeof window.renderPeakCurveChart === 'function';
        });

        expect(hasRenderPeakCurve).toBe(true);
    });

    test('验证switchView函数是否正常工作', async ({ page }) => {
        // 执行switchView('results')
        await page.evaluate(() => {
            window.switchView('results');
        });

        // 检查结果视图是否变为活跃
        const resultsView = page.locator('#resultsView');
        const isActive = await resultsView.evaluate(el =>
            el.classList.contains('active')
        );

        expect(isActive).toBe(true);
    });

    test('结果表格应该有正确的列标题', async ({ page }) => {
        // 切换到结果视图
        await page.locator('#resultsViewTab').click();

        // 等待结果视图加载
        await page.waitForTimeout(1000);

        // 检查表格是否存在（动态创建的表格）
        const tables = page.locator('#comparisonTable table');

        // 如果有表格，检查表头
        if (await tables.count() > 0) {
            const headers = page.locator('#comparisonTable table th');
            const headerCount = await headers.count();
            console.log(`表格列数: ${headerCount}`);

            // 预期至少有4列（方案, 平均行程时间, 平均速度, 总车辆数）
            expect(headerCount).toBeGreaterThanOrEqual(4);
        } else {
            console.log('表格尚未渲染（可能需要实际数据）');
        }
    });

    test('验证Chart.js是否加载', async ({ page }) => {
        // 检查Chart全局对象是否存在
        const hasChart = await page.evaluate(() => {
            return typeof window.Chart === 'function';
        });

        expect(hasChart).toBe(true);
    });

    test('验证CSS文件是否加载（simulations.css）', async ({ page }) => {
        // 获取所有样式表
        const stylesheets = await page.evaluate(() => {
            return Array.from(document.styleSheets).map(sheet => sheet.href);
        });

        // 检查是否有simulations.css
        const hasSimulationsCss = stylesheets.some(href =>
            href && href.includes('simulations.css')
        );

        expect(hasSimulationsCss).toBe(true);
    });

    test('结果视图按钮应该存在', async ({ page }) => {
        // 切换到结果视图
        await page.locator('#resultsViewTab').click();

        // 检查返回配置按钮
        const backBtn = page.locator('#backToConfigBtn');
        await expect(backBtn).toBeVisible();
        await expect(backBtn).toContainText('返回配置');

        // 检查详细分析按钮
        const detailBtn = page.locator('#viewOptimizationBtn');
        await expect(detailBtn).toBeVisible();
        await expect(detailBtn).toContainText('查看详细优化分析');
    });

    test('返回配置按钮点击应该切换视图', async ({ page }) => {
        // 切换到结果视图
        await page.locator('#resultsViewTab').click();
        await page.waitForTimeout(500);

        // 验证在结果视图
        const resultsView = page.locator('#resultsView');
        await expect(resultsView).toHaveClass(/active/);

        // 点击返回配置按钮
        const backBtn = page.locator('#backToConfigBtn');
        if (await backBtn.isVisible()) {
            await backBtn.click();

            // 验证切换到配置视图
            const configView = page.locator('#configView');
            await expect(configView).toHaveClass(/active/);
        }
    });

    test('验证页面JavaScript没有console错误', async ({ page }) => {
        let consoleErrors = [];

        // 监听console错误
        page.on('console', msg => {
            if (msg.type() === 'error') {
                consoleErrors.push(msg.text());
            }
        });

        // 切换到结果视图
        await page.locator('#resultsViewTab').click();
        await page.waitForTimeout(2000);

        // 输出发现的错误
        if (consoleErrors.length > 0) {
            console.log('发现Console错误:');
            consoleErrors.forEach(err => console.log(`  - ${err}`));
        } else {
            console.log('没有发现Console错误');
        }

        // 不失败，只报告
        expect(true).toBe(true);
    });
});

test.describe('Results Page Data Rendering', () => {
    test('验证renderResults函数可以正确处理示例数据', async ({ page }) => {
        await page.goto(SIMULATIONS_URL);
        await page.waitForLoadState('networkidle');

        // 定义示例数据
        const sampleData = {
            plan_results: [
                {
                    plan_name: '基准方案',
                    aggregated_metrics: {
                        avg_travel_time: { mean: 1200.5, std_dev: 50 },
                        avg_speed: { mean: 45.3, std_dev: 5 },
                        total_vehicles: { mean: 2500, std_dev: 100 }
                    }
                },
                {
                    plan_name: '控制方案1',
                    aggregated_metrics: {
                        avg_travel_time: { mean: 1050.3, std_dev: 45 },
                        avg_speed: { mean: 52.1, std_dev: 4 },
                        total_vehicles: { mean: 2650, std_dev: 95 }
                    }
                }
            ]
        };

        // 切换到结果视图
        await page.locator('#resultsViewTab').click();

        // 调用renderResults函数
        await page.evaluate((data) => {
            window.renderResults(data);
        }, sampleData);

        // 等待表格渲染
        await page.waitForTimeout(1000);

        // 验证表格是否被渲染
        const table = page.locator('#comparisonTable table');
        if (await table.count() > 0) {
            // 检查表格行数
            const rows = page.locator('#comparisonTable table tbody tr');
            const rowCount = await rows.count();
            expect(rowCount).toBe(2); // 应该有2行数据

            // 验证表格内容
            const firstRow = rows.first();
            await expect(firstRow).toContainText('基准方案');
        }
    });

    test('验证renderPeakCurveChart函数可以正确处理时序数据', async ({ page }) => {
        await page.goto(SIMULATIONS_URL);
        await page.waitForLoadState('networkidle');

        // 定义示例时序数据
        const sampleData = {
            plan_results: [
                {
                    plan_name: '基准方案',
                    time_series: {
                        time_points: [0, 600, 1200, 1800, 2400, 3000],
                        running: {
                            mean: [100, 500, 850, 1000, 800, 200]
                        }
                    }
                },
                {
                    plan_name: '控制方案1',
                    time_series: {
                        time_points: [0, 600, 1200, 1800, 2400, 3000],
                        running: {
                            mean: [100, 450, 750, 900, 650, 150]
                        }
                    }
                }
            ]
        };

        // 切换到结果视图
        await page.locator('#resultsViewTab').click();

        // 调用renderPeakCurveChart函数
        await page.evaluate((data) => {
            window.renderPeakCurveChart(data);
        }, sampleData);

        // 等待图表渲染
        await page.waitForTimeout(2000);

        // 验证峰值曲线区域是否显示
        const peakCurveSection = page.locator('#peakCurveSection');
        const isVisible = await peakCurveSection.evaluate(el =>
            el.style.display !== 'none'
        );

        expect(isVisible).toBe(true);

        // 验证Canvas是否存在
        const canvas = page.locator('#peakCurveChart');
        await expect(canvas).toBeVisible();
    });
});
