/**
 * E2E Tests for Plan Management
 * Tests complete plan management workflows using Playwright
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:8000';
const PLANS_URL = `${BASE_URL}/control/plans.html`;

test.describe('Plan Management E2E Tests', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to plans page
        await page.goto(PLANS_URL);
        await page.waitForLoadState('networkidle');
    });

    test('should load plans page successfully', async ({ page }) => {
        // Check page title
        await expect(page).toHaveTitle(/方案管理/);

        // Check main elements exist
        await expect(page.locator('button:has-text("新建方案")')).toBeVisible();

        // Check sidebar navigation
        await expect(page.locator('.sidebar-nav a.active')).toContainText('方案管理');
    });

    test('should display baseline plan', async ({ page }) => {
        // Wait for plans to load
        await page.waitForSelector('.plans-grid', { timeout: 5000 });

        // Check if baseline plan exists
        const baselinePlan = page.locator('.plan-card.baseline');
        await expect(baselinePlan).toBeVisible();

        // Check baseline badge
        await expect(baselinePlan.locator('.plan-badge')).toContainText('基准');

        // Check baseline plan name
        await expect(baselinePlan.locator('.plan-title')).toContainText('基准方案');

        // Check strategy count is 0
        await expect(baselinePlan.locator('.plan-meta')).toContainText('策略数: 0');
    });

    test('should filter plans using search', async ({ page }) => {
        await page.waitForSelector('.plans-grid', { timeout: 5000 });

        // Type in search box
        const searchInput = page.locator('#searchInput');
        await searchInput.fill('基准');

        // Wait for filter to apply
        await page.waitForTimeout(500);

        // Should show baseline plan
        const visibleCards = page.locator('.plan-card');
        const count = await visibleCards.count();

        // At least baseline should be visible
        expect(count).toBeGreaterThan(0);

        // Check that visible cards contain search term
        const firstCard = visibleCards.first();
        await expect(firstCard.locator('.plan-title')).toContainText('基准');
    });

    test('should toggle baseline plan visibility', async ({ page }) => {
        await page.waitForSelector('.plans-grid', { timeout: 5000 });

        const showBaselineCheckbox = page.locator('#showBaseline');

        // Uncheck to hide baseline
        await showBaselineCheckbox.uncheck();
        await page.waitForTimeout(300);

        // Baseline should not be visible
        const baselineHidden = page.locator('.plan-card.baseline');
        await expect(baselineHidden).toHaveCount(0);

        // Check to show baseline again
        await showBaselineCheckbox.check();
        await page.waitForTimeout(300);

        // Baseline should be visible
        const baselineVisible = page.locator('.plan-card.baseline');
        await expect(baselineVisible).toBeVisible();
    });

    test('should open create plan modal', async ({ page }) => {
        // Click new plan button
        await page.click('button:has-text("新建方案")');

        // Modal should be visible
        const modal = page.locator('#planModal.active');
        await expect(modal).toBeVisible();

        // Check modal title
        await expect(page.locator('#modalTitle')).toContainText('新建方案');

        // Check form elements exist
        await expect(page.locator('#planName')).toBeVisible();
        await expect(page.locator('#planDescription')).toBeVisible();
        await expect(page.locator('#strategiesSelector')).toBeVisible();
        await expect(page.locator('#planTags')).toBeVisible();
        await expect(page.locator('#planScenario')).toBeVisible();
    });

    test('should close create plan modal', async ({ page }) => {
        // Open modal
        await page.click('button:has-text("新建方案")');
        await expect(page.locator('#planModal.active')).toBeVisible();

        // Close modal
        await page.click('.close-btn');

        // Modal should be hidden
        await expect(page.locator('#planModal.active')).not.toBeVisible();
    });

    test('should create a new plan', async ({ page }) => {
        // Open create modal
        await page.click('button:has-text("新建方案")');

        // Wait for modal to be ready
        await page.waitForSelector('#planModal.active', { timeout: 3000 });

        // Fill in plan details
        await page.fill('#planName', 'E2E测试方案');
        await page.fill('#planDescription', '这是一个自动化测试创建的方案');
        await page.fill('#planTags', '测试, E2E');
        await page.fill('#planScenario', '自动化测试场景');

        // Wait for strategies to load (optional - plan can be created without strategies)
        await page.waitForTimeout(1000);

        // Submit form
        await page.click('button[type="submit"]:has-text("保存方案")');

        // Wait for modal to close (success scenario)
        await page.waitForSelector('#planModal.active', { state: 'hidden', timeout: 5000 });

        // Verify plan appears in list
        await page.waitForTimeout(1000);
        const newPlan = page.locator('.plan-card:has-text("E2E测试方案")');
        await expect(newPlan).toBeVisible();

        // Verify plan details
        await expect(newPlan.locator('.plan-title')).toContainText('E2E测试方案');

        // Check tags are displayed
        await expect(newPlan.locator('.tag:has-text("测试")')).toBeVisible();
        await expect(newPlan.locator('.tag:has-text("E2E")')).toBeVisible();
    });

    test('should view plan details', async ({ page }) => {
        await page.waitForSelector('.plans-grid', { timeout: 5000 });

        // Click on baseline plan to view details
        const baselinePlan = page.locator('.plan-card.baseline').first();
        await baselinePlan.click();

        // Detail modal should open
        const detailModal = page.locator('#detailModal.active');
        await expect(detailModal).toBeVisible();

        // Check detail content
        await expect(page.locator('#detailTitle')).toContainText('基准方案');
        await expect(page.locator('#detailContent')).toContainText('基本信息');
        await expect(page.locator('#detailContent')).toContainText('包含策略');
        await expect(page.locator('#detailContent')).toContainText('XML配置预览');

        // Check XML preview is visible
        await expect(page.locator('.xml-preview')).toBeVisible();
    });

    test('should close plan detail modal', async ({ page }) => {
        await page.waitForSelector('.plans-grid', { timeout: 5000 });

        // Open detail modal
        const baselinePlan = page.locator('.plan-card.baseline').first();
        await baselinePlan.click();
        await expect(page.locator('#detailModal.active')).toBeVisible();

        // Close detail modal
        await page.click('#detailModal .close-btn');

        // Modal should be hidden
        await expect(page.locator('#detailModal.active')).not.toBeVisible();
    });

    test('should not allow deleting baseline plan', async ({ page }) => {
        await page.waitForSelector('.plans-grid', { timeout: 5000 });

        // Baseline plan should not have delete button
        const baselinePlan = page.locator('.plan-card.baseline').first();
        const deleteButton = baselinePlan.locator('button:has-text("删除")');

        // Delete button should not exist for baseline
        await expect(deleteButton).toHaveCount(0);
    });

    test('should edit and update a non-baseline plan', async ({ page }) => {
        // First create a plan to edit
        await page.click('button:has-text("新建方案")');
        await page.waitForSelector('#planModal.active');
        await page.fill('#planName', 'E2E编辑测试方案');
        await page.fill('#planDescription', '初始描述');
        await page.click('button[type="submit"]:has-text("保存方案")');

        // Wait for plan to be created
        await page.waitForSelector('#planModal.active', { state: 'hidden', timeout: 5000 });
        await page.waitForTimeout(1000);

        // Find and click edit button
        const planCard = page.locator('.plan-card:has-text("E2E编辑测试方案")').first();
        await expect(planCard).toBeVisible();

        // Hover over card to make buttons visible
        await planCard.hover();
        await planCard.locator('button.btn.btn-primary:has-text("编辑")').click();

        // Modal should open with existing data
        await expect(page.locator('#planModal.active')).toBeVisible();
        await expect(page.locator('#modalTitle')).toContainText('编辑方案');
        await expect(page.locator('#planName')).toHaveValue('E2E编辑测试方案');
        await expect(page.locator('#planDescription')).toHaveValue('初始描述');

        // Update description
        await page.fill('#planDescription', '更新后的描述');

        // Submit update
        await page.click('button[type="submit"]:has-text("保存方案")');

        // Wait for modal to close
        await page.waitForSelector('#planModal.active', { state: 'hidden', timeout: 5000 });

        // Verify update by viewing details
        await page.waitForTimeout(1000);
        await planCard.click();
        await expect(page.locator('#detailContent')).toContainText('更新后的描述');
    });

    test('should delete a non-baseline plan', async ({ page }) => {
        // Create a plan to delete
        await page.click('button:has-text("新建方案")');
        await page.waitForSelector('#planModal.active');
        await page.fill('#planName', 'E2E删除测试方案');
        await page.click('button[type="submit"]:has-text("保存方案")');
        await page.waitForSelector('#planModal.active', { state: 'hidden', timeout: 5000 });
        await page.waitForTimeout(1000);

        // Find the plan
        const planCard = page.locator('.plan-card:has-text("E2E删除测试方案")').first();
        await expect(planCard).toBeVisible();

        // Handle confirmation dialog
        page.on('dialog', dialog => dialog.accept());

        // Click delete button
        await planCard.locator('button.btn.btn-danger:has-text("删除")').click();

        // Wait for deletion
        await page.waitForTimeout(1500);

        // Plan should no longer be visible
        await expect(planCard).toHaveCount(0);
    });

    test('should handle form validation', async ({ page }) => {
        // Open create modal
        await page.click('button:has-text("新建方案")');
        await expect(page.locator('#planModal.active')).toBeVisible();

        // Try to submit without required field
        await page.click('button[type="submit"]:has-text("保存方案")');

        // Modal should still be visible (validation failed)
        await expect(page.locator('#planModal.active')).toBeVisible();

        // Fill required field
        await page.fill('#planName', '验证测试方案');

        // Now submission should work
        await page.click('button[type="submit"]:has-text("保存方案")');

        // Modal should close
        await page.waitForSelector('#planModal.active', { state: 'hidden', timeout: 5000 });
    });

    test('should handle empty state when no plans exist (after filtering)', async ({ page }) => {
        await page.waitForSelector('.plans-grid', { timeout: 5000 });

        // Search for something that doesn't exist
        await page.fill('#searchInput', 'NONEXISTENT_PLAN_XYZ123');

        await page.waitForTimeout(500);

        // Should show empty state
        const emptyState = page.locator('.empty-state');
        await expect(emptyState).toBeVisible();
        await expect(emptyState).toContainText('暂无方案');
    });

    test('should navigate between sidebar items', async ({ page }) => {
        // Click on different sidebar items
        await page.click('.sidebar-nav a:has-text("策略管理")');
        await page.waitForLoadState('networkidle');

        // Should navigate to templates page
        await expect(page).toHaveURL(/templates\.html/);

        // Go back to plans
        await page.click('.sidebar-nav a:has-text("方案管理")');
        await page.waitForLoadState('networkidle');

        // Should be back on plans page
        await expect(page).toHaveURL(/plans\.html/);
        await expect(page.locator('.sidebar-nav a.active')).toContainText('方案管理');
    });

    test('should return to main system', async ({ page }) => {
        // Click return button
        await page.click('.back-btn:has-text("返回主系统")');
        await page.waitForLoadState('networkidle');

        // Should navigate to main index
        await expect(page).toHaveURL(/\/index\.html|\/$/);
    });
});
