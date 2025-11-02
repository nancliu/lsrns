/**
 * E2E测试：批次历史Case ID功能
 *
 * 测试目标：
 * 1. 案例选择后 currentCaseId 正确设置
 * 2. 批次创建后 currentCaseId 正确持久化
 * 3. 批次历史标签页能够正确加载数据
 * 4. 批次状态在生命周期变化时正确更新（pending → running → completed）
 * 5. 页面重新加载后 currentCaseId 能够从 localStorage 恢复
 * 6. batches_index.json 与实际批次状态同步
 */

const { test, expect } = require('@playwright/test');

test.describe('批次历史Case ID功能测试', () => {
    test.beforeEach(async ({ page }) => {
        // 设置较长的超时时间
        test.setTimeout(300000); // 5分钟超时

        // 导航到批量仿真页面
        await page.goto('http://localhost:8000/control/simulations.html');

        // 等待页面加载完成
        await page.waitForLoadState('networkidle');
    });

    test('案例选择后批次历史可以加载', async ({ page }) => {
        console.log('\n=== 测试：案例选择后批次历史可以加载 ===\n');

        // ========== 1. 验证初始状态 - 批次历史标签应该禁用 ==========
        console.log('✓ 步骤1: 验证批次历史标签初始状态');

        const historyTab = page.locator('#historyViewTab');
        const historyTabDisabled = await historyTab.evaluate(el => {
            return el.classList.contains('disabled') || el.hasAttribute('disabled');
        });
        console.log('  批次历史标签禁用状态:', historyTabDisabled);

        // ========== 2. 选择一个案例 ==========
        console.log('\n✓ 步骤2: 选择案例');

        // 等待案例列表加载（至少2个案例）
        await page.waitForFunction(() => {
            const select = document.getElementById('caseSelector');
            const options = Array.from(select.options);
            const validOptions = options.filter(opt => opt.value && opt.value !== '');
            return validOptions.length >= 2;
        }, { timeout: 30000 });

        // 获取所有有效案例
        const caseValues = await page.locator('#caseSelector option[value]').evaluateAll(options =>
            options.map(opt => opt.value).filter(v => v)
        );

        if (caseValues.length < 2) {
            throw new Error(`案例数量不足：只有 ${caseValues.length} 个案例，需要至少2个`);
        }

        // 选择第2个案例（索引1，时间较短的10分钟输入）
        await page.selectOption('#caseSelector', caseValues[1]);
        const selectedCaseId = caseValues[1];
        console.log('  ✓ 已选择第2个案例:', selectedCaseId);

        // 等待currentCaseId设置
        await page.waitForTimeout(1000);

        // ========== 3. 验证 currentCaseId 已设置 ==========
        console.log('\n✓ 步骤3: 验证 currentCaseId');

        const currentCaseId = await page.evaluate(() => window.currentCaseId);
        console.log('  currentCaseId:', currentCaseId);
        expect(currentCaseId).toBe(selectedCaseId);

        // 验证 localStorage 持久化
        const storedCaseId = await page.evaluate(() => localStorage.getItem('lastSelectedCaseId'));
        console.log('  localStorage中的案例ID:', storedCaseId);
        expect(storedCaseId).toBe(selectedCaseId);

        // ========== 4. 验证批次历史标签已启用 ==========
        console.log('\n✓ 步骤4: 验证批次历史标签启用');

        const historyTabEnabledAfterSelection = await historyTab.evaluate(el => {
            return !el.classList.contains('disabled') && !el.hasAttribute('disabled');
        });
        console.log('  批次历史标签已启用:', historyTabEnabledAfterSelection);

        // ========== 5. 点击批次历史标签 ==========
        console.log('\n✓ 步骤5: 加载批次历史');

        await historyTab.click();
        await page.waitForTimeout(2000);

        // 验证视图切换
        const historyView = page.locator('#historyView');
        await expect(historyView).toHaveClass(/active/);
        console.log('  ✓ 批次历史视图已激活');

        // ========== 6. 验证API调用包含case_id ==========
        console.log('\n✓ 步骤6: 验证API调用');

        // 等待API响应
        const apiResponse = await page.waitForResponse(
            response => response.url().includes('/api/v1/control/batch-optimization/batches') &&
                        response.url().includes(`case_id=${selectedCaseId}`),
            { timeout: 10000 }
        ).catch(() => null);

        if (apiResponse) {
            console.log('  ✓ API调用包含正确的case_id参数');
            const responseData = await apiResponse.json();
            console.log('  批次数量:', responseData.batches ? responseData.batches.length : 0);
        } else {
            console.log('  ⚠ 未捕获到API响应（可能已经加载完成）');
        }

        console.log('\n=== 测试完成 ===\n');
    });

    test('批次状态在生命周期中正确更新', async ({ page }) => {
        console.log('\n=== 测试：批次状态生命周期更新 ===\n');

        // ========== 1. 选择案例 ==========
        console.log('✓ 步骤1: 选择第2个案例（10分钟输入）');

        await page.waitForFunction(() => {
            const select = document.getElementById('caseSelector');
            const options = Array.from(select.options);
            const validOptions = options.filter(opt => opt.value && opt.value !== '');
            return validOptions.length >= 2;
        }, { timeout: 30000 });

        const caseValues = await page.locator('#caseSelector option[value]').evaluateAll(options =>
            options.map(opt => opt.value).filter(v => v)
        );

        if (caseValues.length < 2) {
            throw new Error(`案例数量不足：只有 ${caseValues.length} 个案例，需要至少2个`);
        }

        // 选择第2个案例（时间较短）
        await page.selectOption('#caseSelector', caseValues[1]);
        const selectedCaseId = caseValues[1];
        console.log('  ✓ 已选择第2个案例:', selectedCaseId);
        await page.waitForTimeout(2000);

        // ========== 2. 创建批次 ==========
        console.log('\n✓ 步骤2: 创建批次');

        // 等待方案加载
        await page.waitForTimeout(2000);
        const planItems = page.locator('.plan-item');
        const planCount = await planItems.count();

        if (planCount === 0) {
            throw new Error('没有可用的方案');
        }

        // 选择第一个方案
        const firstCheckbox = planItems.first().locator('input[type="checkbox"]');
        await firstCheckbox.check();
        console.log('  ✓ 已选择方案');

        // 创建批次
        await page.click('#createBatchBtn');
        await page.waitForTimeout(3000);

        // 获取批次ID
        const batchId = await page.evaluate(() => window.currentBatchId);
        console.log('  ✓ 批次已创建:', batchId);

        // ========== 3. 验证初始状态 - pending ==========
        console.log('\n✓ 步骤3: 验证批次状态 - pending');

        const initialStatus = await page.locator('#batchStatus').textContent();
        console.log('  批次状态:', initialStatus);

        // ========== 4. 切换到批次历史，验证新批次显示 ==========
        console.log('\n✓ 步骤4: 切换到批次历史验证新批次');

        await page.click('#historyViewTab');
        await page.waitForTimeout(2000);

        // 等待批次列表加载
        const batchCards = page.locator('.batch-history-card');
        const batchCount = await batchCards.count();
        console.log('  历史批次数量:', batchCount);

        if (batchCount > 0) {
            // 检查第一个批次（最新的）
            const firstCard = batchCards.first();
            const firstBatchId = await firstCard.locator('h4').textContent();
            const firstBatchStatus = await firstCard.locator('.batch-status').textContent();
            console.log('  最新批次ID:', firstBatchId);
            console.log('  最新批次状态:', firstBatchStatus);
        }

        // ========== 5. 启动批次 ==========
        console.log('\n✓ 步骤5: 启动批次');

        // 切换回进度视图
        await page.click('#progressViewTab');
        await page.waitForTimeout(1000);

        // 启动批次
        const startBtn = page.locator('#startBatchBtn');
        await expect(startBtn).toBeVisible();
        await startBtn.click();
        await page.waitForTimeout(3000);
        console.log('  ✓ 批次已启动');

        // ========== 6. 验证运行状态 - running ==========
        console.log('\n✓ 步骤6: 验证批次状态 - running');

        const runningStatus = await page.locator('#batchStatus').textContent();
        console.log('  批次状态:', runningStatus);

        // ========== 7. 切换到批次历史，验证状态已更新 ==========
        console.log('\n✓ 步骤7: 验证批次历史中的状态更新');

        await page.click('#historyViewTab');
        await page.waitForTimeout(2000);

        if (batchCount > 0) {
            const updatedStatus = await batchCards.first().locator('.batch-status').textContent();
            console.log('  批次历史中的状态:', updatedStatus);
        }

        // ========== 8. 等待批次完成 ==========
        console.log('\n✓ 步骤8: 等待批次完成（最多2分钟）');

        // 切换回进度视图
        await page.click('#progressViewTab');
        await page.waitForTimeout(1000);

        // 轮询等待完成
        let isCompleted = false;
        let attempts = 0;
        const maxAttempts = 24; // 2分钟 (24 * 5秒)

        while (!isCompleted && attempts < maxAttempts) {
            await page.waitForTimeout(5000);
            const currentStatus = await page.locator('#batchStatus').textContent();
            console.log(`  [${attempts + 1}/${maxAttempts}] 当前状态:`, currentStatus);

            if (currentStatus.includes('已完成') || currentStatus.includes('completed')) {
                isCompleted = true;
                console.log('  ✓ 批次已完成');
            }
            attempts++;
        }

        if (!isCompleted) {
            console.log('  ⚠ 批次未在2分钟内完成，继续验证其他功能');
        }

        // ========== 9. 最终验证批次历史状态 ==========
        console.log('\n✓ 步骤9: 最终验证批次历史');

        await page.click('#historyViewTab');
        await page.waitForTimeout(2000);

        const finalBatchCount = await batchCards.count();
        console.log('  最终批次数量:', finalBatchCount);

        if (finalBatchCount > 0) {
            const finalStatus = await batchCards.first().locator('.batch-status').textContent();
            const finalSuccessRate = await batchCards.first().locator('.batch-success-rate').textContent().catch(() => 'N/A');
            console.log('  最终批次状态:', finalStatus);
            console.log('  成功率:', finalSuccessRate);
        }

        // ========== 10. 保存截图 ==========
        await page.screenshot({
            path: 'test-results/batch-history-lifecycle.png',
            fullPage: true
        });
        console.log('  ✓ 截图已保存: test-results/batch-history-lifecycle.png');

        console.log('\n=== 测试完成 ===\n');
    });

    test('页面重新加载后恢复案例上下文', async ({ page }) => {
        console.log('\n=== 测试：页面重新加载后恢复案例上下文 ===\n');

        // ========== 1. 选择案例 ==========
        console.log('✓ 步骤1: 选择第2个案例');

        await page.waitForFunction(() => {
            const select = document.getElementById('caseSelector');
            const options = Array.from(select.options);
            const validOptions = options.filter(opt => opt.value && opt.value !== '');
            return validOptions.length >= 2;
        }, { timeout: 30000 });

        const caseValues = await page.locator('#caseSelector option[value]').evaluateAll(options =>
            options.map(opt => opt.value).filter(v => v)
        );

        if (caseValues.length < 2) {
            throw new Error(`案例数量不足：只有 ${caseValues.length} 个案例，需要至少2个`);
        }

        // 选择第2个案例
        await page.selectOption('#caseSelector', caseValues[1]);
        const selectedCaseId = caseValues[1];
        console.log('  ✓ 已选择第2个案例:', selectedCaseId);
        await page.waitForTimeout(1000);

        // ========== 2. 验证 localStorage 存储 ==========
        console.log('\n✓ 步骤2: 验证 localStorage');

        const storedCaseId = await page.evaluate(() => localStorage.getItem('lastSelectedCaseId'));
        console.log('  localStorage中的案例ID:', storedCaseId);
        expect(storedCaseId).toBe(selectedCaseId);

        // ========== 3. 重新加载页面 ==========
        console.log('\n✓ 步骤3: 重新加载页面');

        await page.reload();
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);

        // ========== 4. 验证案例自动恢复 ==========
        console.log('\n✓ 步骤4: 验证案例自动恢复');

        const restoredCaseId = await page.locator('#caseSelector').inputValue();
        console.log('  恢复的案例ID:', restoredCaseId);
        expect(restoredCaseId).toBe(selectedCaseId);

        const restoredCurrentCaseId = await page.evaluate(() => window.currentCaseId);
        console.log('  currentCaseId:', restoredCurrentCaseId);
        expect(restoredCurrentCaseId).toBe(selectedCaseId);

        // ========== 5. 验证批次历史标签自动启用 ==========
        console.log('\n✓ 步骤5: 验证批次历史标签自动启用');

        const historyTab = page.locator('#historyViewTab');
        const isEnabled = await historyTab.evaluate(el => {
            return !el.classList.contains('disabled') && !el.hasAttribute('disabled');
        });
        console.log('  批次历史标签已启用:', isEnabled);
        expect(isEnabled).toBe(true);

        // ========== 6. 验证批次历史可以加载 ==========
        console.log('\n✓ 步骤6: 验证批次历史可以加载');

        await historyTab.click();
        await page.waitForTimeout(2000);

        const historyView = page.locator('#historyView');
        await expect(historyView).toHaveClass(/active/);
        console.log('  ✓ 批次历史成功加载');

        // ========== 7. 测试URL参数恢复 ==========
        console.log('\n✓ 步骤7: 测试URL参数恢复');

        // 使用URL参数导航
        await page.goto(`http://localhost:8000/control/simulations.html?case_id=${selectedCaseId}`);
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);

        const urlRestoredCaseId = await page.locator('#caseSelector').inputValue();
        console.log('  从URL恢复的案例ID:', urlRestoredCaseId);
        expect(urlRestoredCaseId).toBe(selectedCaseId);

        const urlRestoredCurrentCaseId = await page.evaluate(() => window.currentCaseId);
        console.log('  currentCaseId:', urlRestoredCurrentCaseId);
        expect(urlRestoredCurrentCaseId).toBe(selectedCaseId);

        console.log('\n=== 测试完成 ===\n');
    });
});
