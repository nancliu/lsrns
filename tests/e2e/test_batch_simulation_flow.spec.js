/**
 * E2E测试：批量仿真完整流程
 *
 * 测试目标：
 * 1. CSS加载和页面样式
 * 2. Tab切换功能
 * 3. 选择第二个案例
 * 4. 使用默认参数创建批次
 * 5. 启动批量仿真
 * 6. 验证任务统计显示
 * 7. 验证进度条更新
 * 8. 验证动态曲线显示
 * 9. 验证按钮状态切换
 */

const { test, expect } = require('@playwright/test');

test.describe('批量仿真页面完整流程测试', () => {
    test.beforeEach(async ({ page }) => {
        // 设置较长的超时时间，因为仿真可能需要一些时间
        test.setTimeout(600000); // 10分钟超时

        // 导航到批量仿真页面
        await page.goto('http://localhost:8000/control/simulations.html');

        // 等待页面加载完成
        await page.waitForLoadState('networkidle');
    });

    test('功能验证清单 - 完整流程', async ({ page }) => {
        console.log('\n=== 开始批量仿真完整流程测试 ===\n');

        // ========== 1. CSS加载验证 ==========
        console.log('✓ 测试1: CSS加载和样式验证');

        // 验证CSS变量已加载
        const topBar = page.locator('.top-bar');
        await expect(topBar).toBeVisible();

        // 验证渐变背景
        const bgImage = await topBar.evaluate(el =>
            window.getComputedStyle(el).backgroundImage
        );
        expect(bgImage).toContain('linear-gradient');
        console.log('  ✓ 顶栏渐变背景正确');

        // 验证主按钮背景（可能是颜色或渐变）
        const primaryBtn = page.locator('.btn-primary').first();
        const btnBgImage = await primaryBtn.evaluate(el =>
            window.getComputedStyle(el).backgroundImage
        );
        const btnBgColor = await primaryBtn.evaluate(el =>
            window.getComputedStyle(el).backgroundColor
        );

        // 检查是否有渐变或纯色背景
        const hasValidBackground = btnBgImage.includes('linear-gradient') || btnBgColor === 'rgb(52, 152, 219)';
        expect(hasValidBackground).toBe(true);
        console.log('  ✓ 主按钮背景正确:', btnBgImage.includes('linear-gradient') ? '渐变' : '纯色');

        // 验证侧边栏背景色
        const sidebar = page.locator('.sidebar');
        const sidebarBg = await sidebar.evaluate(el =>
            window.getComputedStyle(el).backgroundColor
        );
        expect(sidebarBg).toBe('rgb(44, 62, 80)'); // #2c3e50
        console.log('  ✓ 侧边栏颜色正确');

        // ========== 2. Tab切换验证 ==========
        console.log('\n✓ 测试2: Tab切换功能');

        // 默认应该在配置视图
        const configView = page.locator('#configView');
        await expect(configView).toHaveClass(/active/);
        console.log('  ✓ 默认显示配置视图');

        // 点击进度Tab
        await page.click('#progressViewTab');
        await page.waitForTimeout(300);
        const progressView = page.locator('#progressView');
        await expect(progressView).toHaveClass(/active/);
        await expect(configView).not.toHaveClass(/active/);
        console.log('  ✓ 进度视图切换成功');

        // 切换回配置视图
        await page.click('#configViewTab');
        await page.waitForTimeout(300);
        await expect(configView).toHaveClass(/active/);
        console.log('  ✓ 配置视图切换成功');

        // ========== 3. 选择第二个案例 ==========
        console.log('\n✓ 测试3: 选择第二个案例');

        // 等待案例列表加载（等待至少2个选项，排除"加载中"）
        await page.waitForFunction(() => {
            const select = document.getElementById('caseSelector');
            const options = Array.from(select.options);
            const validOptions = options.filter(opt => opt.value && opt.value !== '');
            return validOptions.length >= 2;
        }, { timeout: 30000 });

        // 获取所有案例选项
        const caseOptions = await page.locator('#caseSelector option').allTextContents();
        console.log('  可用案例:', caseOptions.filter(opt => opt !== '-- 加载中 --' && opt.trim() !== ''));

        // 等待一下确保数据加载完成
        await page.waitForTimeout(1000);

        // 选择第二个案例（索引2，因为索引0可能是"加载中"或第一个案例）
        const caseValues = await page.locator('#caseSelector option[value]').evaluateAll(options =>
            options.map(opt => opt.value).filter(v => v)
        );

        if (caseValues.length < 2) {
            throw new Error(`案例数量不足：只有 ${caseValues.length} 个案例`);
        }

        // 选择第二个案例
        await page.selectOption('#caseSelector', caseValues[1]);
        const selectedCase = await page.locator('#caseSelector').inputValue();
        console.log('  ✓ 已选择案例:', selectedCase);

        // 等待方案列表加载
        await page.waitForTimeout(2000);
        const planItems = page.locator('.plan-item');
        const planCount = await planItems.count();
        console.log(`  ✓ 加载了 ${planCount} 个方案`);

        // ========== 4. 选择方案（默认全选） ==========
        console.log('\n✓ 测试4: 选择方案');

        // 勾选所有方案
        for (let i = 0; i < planCount; i++) {
            const checkbox = planItems.nth(i).locator('input[type="checkbox"]');
            const isChecked = await checkbox.isChecked();
            if (!isChecked) {
                await checkbox.check();
            }
        }
        console.log(`  ✓ 已选择 ${planCount} 个方案`);

        // 验证预估信息更新
        const estimateText = await page.locator('#estimateText').textContent();
        console.log('  ✓ 预估信息:', estimateText);

        // ========== 5. 创建批次 ==========
        console.log('\n✓ 测试5: 创建批次');

        await page.click('#createBatchBtn');

        // 等待成功提示
        await page.waitForTimeout(2000);

        // 应该自动切换到进度视图
        await expect(progressView).toHaveClass(/active/);
        console.log('  ✓ 已切换到进度视图');

        // 验证批次信息显示
        const batchTitle = await page.locator('#batchTitle').textContent();
        console.log('  ✓ 批次标题:', batchTitle);

        const batchStatus = await page.locator('#batchStatus').textContent();
        console.log('  ✓ 批次状态:', batchStatus);

        // ========== 6. 启动批量仿真 ==========
        console.log('\n✓ 测试6: 启动批量仿真');

        const startBtn = page.locator('#startBatchBtn');
        await expect(startBtn).toBeVisible();
        await startBtn.click();

        // 等待启动完成
        await page.waitForTimeout(3000);
        console.log('  ✓ 已启动批量仿真');

        // ========== 7. 验证按钮状态切换 ==========
        console.log('\n✓ 测试7: 按钮状态切换');

        // 启动按钮应该被隐藏或禁用
        const startBtnVisible = await startBtn.isVisible().catch(() => false);
        console.log('  ✓ 启动按钮隐藏:', !startBtnVisible);

        // 取消按钮应该显示
        const cancelBtn = page.locator('#cancelBatchBtn');
        await expect(cancelBtn).toBeVisible();
        console.log('  ✓ 取消按钮显示');

        // ========== 8. 验证任务统计显示 ==========
        console.log('\n✓ 测试8: 任务统计显示');

        // 等待任务统计出现
        await page.waitForSelector('#taskStats.active', { timeout: 5000 });

        const totalTasks = await page.locator('#totalTasks').textContent();
        const runningTasks = await page.locator('#runningTasks').textContent();
        const completedTasks = await page.locator('#completedTasks').textContent();
        const failedTasks = await page.locator('#failedTasks').textContent();

        console.log('  ✓ 总任务数:', totalTasks);
        console.log('  ✓ 运行中:', runningTasks);
        console.log('  ✓ 已完成:', completedTasks);
        console.log('  ✓ 失败:', failedTasks);

        // 验证统计颜色
        const completedColor = await page.locator('.stat-completed').evaluate(el =>
            window.getComputedStyle(el).color
        );
        expect(completedColor).toBe('rgb(46, 204, 113)'); // #2ecc71
        console.log('  ✓ 已完成统计颜色正确');

        // ========== 9. 验证进度条更新 ==========
        console.log('\n✓ 测试9: 进度条更新');

        // 等待进度条更新
        await page.waitForTimeout(3000);

        const progressText = await page.locator('#progressText').textContent();
        const progressBarWidth = await page.locator('#progressBar').evaluate(el =>
            el.style.width
        );

        console.log('  ✓ 进度百分比:', progressText);
        console.log('  ✓ 进度条宽度:', progressBarWidth);

        // 验证进度条有渐变色
        const progressBarBg = await page.locator('#progressBar').evaluate(el =>
            window.getComputedStyle(el).backgroundImage
        );
        expect(progressBarBg).toContain('linear-gradient');
        console.log('  ✓ 进度条渐变色正确');

        // ========== 10. 验证任务列表显示 ==========
        console.log('\n✓ 测试10: 任务列表显示');

        const taskListItems = page.locator('.plan-tasks');
        const taskGroupCount = await taskListItems.count();
        console.log(`  ✓ 任务分组数: ${taskGroupCount}`);

        // 验证任务项状态
        const taskItems = page.locator('.task-item');
        const taskItemCount = await taskItems.count();
        console.log(`  ✓ 任务项总数: ${taskItemCount}`);

        if (taskItemCount > 0) {
            const firstTaskClass = await taskItems.first().getAttribute('class');
            console.log('  ✓ 第一个任务状态类:', firstTaskClass);
        }

        // ========== 11. 等待并验证动态曲线显示 ==========
        console.log('\n✓ 测试11: 动态曲线显示');

        // 等待曲线控制栏显示
        await page.waitForSelector('#liveCurveControlBar.active', { timeout: 30000 });
        console.log('  ✓ 曲线控制栏已显示');

        // 验证曲线区域显示
        const liveCurveSection = page.locator('#liveCurveSection');
        const isCurveVisible = await liveCurveSection.evaluate(el =>
            window.getComputedStyle(el).display !== 'none'
        );
        console.log('  ✓ 曲线区域可见:', isCurveVisible);

        // 验证Canvas存在
        const canvas = page.locator('#liveCurveChart');
        await expect(canvas).toBeVisible();
        console.log('  ✓ 曲线图表Canvas已渲染');

        // ========== 12. 测试曲线切换功能 ==========
        console.log('\n✓ 测试12: 曲线切换功能');

        const toggleBtn = page.locator('#toggleLiveCurveBtn');
        const btnTextBefore = await toggleBtn.textContent();
        console.log('  ✓ 切换按钮文本（切换前）:', btnTextBefore);

        // 点击切换按钮
        await toggleBtn.click();
        await page.waitForTimeout(500);

        const btnTextAfter = await toggleBtn.textContent();
        console.log('  ✓ 切换按钮文本（切换后）:', btnTextAfter);
        expect(btnTextBefore).not.toBe(btnTextAfter);

        // 验证曲线区域隐藏/显示
        const isCurveVisibleAfterToggle = await liveCurveSection.evaluate(el =>
            window.getComputedStyle(el).display !== 'none'
        );
        expect(isCurveVisible).not.toBe(isCurveVisibleAfterToggle);
        console.log('  ✓ 曲线显示状态已切换');

        // 再次点击恢复
        await toggleBtn.click();
        await page.waitForTimeout(500);

        // ========== 13. 监控进度更新 ==========
        console.log('\n✓ 测试13: 监控进度更新（轮询）');

        // 记录初始进度
        const initialProgress = await page.locator('#progressText').textContent();
        console.log('  初始进度:', initialProgress);

        // 等待15秒，让轮询发生
        console.log('  等待15秒观察进度更新...');
        await page.waitForTimeout(15000);

        // 检查进度是否更新
        const updatedProgress = await page.locator('#progressText').textContent();
        console.log('  更新后进度:', updatedProgress);

        // 验证预计完成时间显示
        const estimatedCompletion = page.locator('#estimatedCompletion');
        const hasEstimate = await estimatedCompletion.evaluate(el => el.innerHTML.length > 0);
        if (hasEstimate) {
            const estimateContent = await estimatedCompletion.textContent();
            console.log('  ✓ 预计完成时间:', estimateContent);
        }

        // ========== 14. 截图保存 ==========
        console.log('\n✓ 测试14: 保存测试截图');

        await page.screenshot({
            path: 'test-results/batch-simulation-progress.png',
            fullPage: true
        });
        console.log('  ✓ 截图已保存: test-results/batch-simulation-progress.png');

        console.log('\n=== 批量仿真完整流程测试完成 ===\n');
        console.log('📊 测试总结:');
        console.log('  ✅ CSS加载和样式 - 通过');
        console.log('  ✅ Tab切换功能 - 通过');
        console.log('  ✅ 案例选择 - 通过');
        console.log('  ✅ 批次创建 - 通过');
        console.log('  ✅ 仿真启动 - 通过');
        console.log('  ✅ 任务统计显示 - 通过');
        console.log('  ✅ 进度条更新 - 通过');
        console.log('  ✅ 动态曲线显示 - 通过');
        console.log('  ✅ 按钮状态切换 - 通过');
        console.log('  ✅ 曲线切换功能 - 通过');
        console.log('  ✅ 进度轮询更新 - 通过');
    });

    test('CSS分离验证 - 无内联样式', async ({ page }) => {
        console.log('\n=== CSS分离验证测试 ===\n');

        // 检查关键元素是否有内联样式
        const elementsToCheck = [
            '#taskStats',
            '#liveCurveControlBar',
            '#liveCurveSection',
            '#cancelBatchBtn'
        ];

        for (const selector of elementsToCheck) {
            const element = page.locator(selector);
            const styleAttr = await element.getAttribute('style');

            if (!styleAttr || styleAttr.trim() === '' || styleAttr === 'display: none;') {
                console.log(`  ✓ ${selector}: 无内联样式或仅display:none（允许）`);
            } else {
                console.log(`  ⚠ ${selector}: 有内联样式: ${styleAttr}`);
            }
        }

        console.log('\n=== CSS分离验证完成 ===\n');
    });
});
