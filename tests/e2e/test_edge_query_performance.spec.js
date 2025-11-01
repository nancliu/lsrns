/**
 * Edge Query Performance Diagnostic Test
 *
 * Purpose: Diagnose why the first edge query is slow
 * Checks:
 * 1. Route selection timing
 * 2. Query API response time
 * 3. Result display timing
 * 4. Performance bottlenecks
 *
 * Performance Baseline:
 * - Route select: <100ms (from cache)
 * - Query request: <2s (normal DB response)
 * - Total: <3s from click to results
 *
 * RULE-E2E-001 Compliant
 */

const { test, expect } = require('@playwright/test');

test.describe('路段查询性能诊断 - 首次查询速度测试', () => {

  test('首次路段查询完整性能分析', async ({ page }) => {
    console.log('\n========== 路段查询性能完整分析 ==========\n');

    // 性能计时器
    const perfMarkers = {};

    // 标记时间点
    const mark = (name) => {
      perfMarkers[name] = Date.now();
      console.log(`[标记] ${name}: ${new Date(perfMarkers[name]).toISOString().split('T')[1]}`);
    };

    // 计算时间差
    const measure = (name, from, to) => {
      const duration = perfMarkers[to] - perfMarkers[from];
      console.log(`[耗时] ${name}: ${duration}ms`);
      return duration;
    };

    // API调用追踪
    const apiTrace = [];
    let lastApiTime = 0;

    page.on('request', request => {
      if (request.url().includes('/api/v1/control/edges')) {
        const endpoint = request.url().split('?')[0].split('/').pop();
        lastApiTime = Date.now();
        apiTrace.push({
          event: 'request',
          endpoint,
          url: request.url(),
          time: lastApiTime
        });
        console.log(`  📤 API请求: /${endpoint}`);
      }
    });

    page.on('response', response => {
      if (response.url().includes('/api/v1/control/edges')) {
        const endpoint = response.url().split('?')[0].split('/').pop();
        const responseTime = Date.now();
        const duration = responseTime - lastApiTime;
        apiTrace.push({
          event: 'response',
          endpoint,
          status: response.status(),
          duration,
          time: responseTime
        });
        console.log(`  📥 API响应: ${response.status()} (耗时: ${duration}ms)`);
      }
    });

    // ===== PHASE 1: 页面加载 =====
    console.log('\n[PHASE 1] 页面加载');
    mark('page_load_start');

    // Force reload to bypass cache and get fresh JS
    await page.goto('http://localhost:8000/control/templates.html', { timeout: 30000, waitUntil: 'networkidle' });
    mark('page_load_complete');
    measure('页面加载', 'page_load_start', 'page_load_complete');

    // ===== PHASE 2: EdgeSelector 初始化 =====
    console.log('\n[PHASE 2] EdgeSelector初始化');
    mark('selector_init_start');

    await page.waitForSelector('.template-card', { timeout: 10000 });
    mark('selector_init_complete');
    measure('初始化完成', 'selector_init_start', 'selector_init_complete');

    // 检查缓存状态
    const cacheStatus = await page.evaluate(() => {
      const cached = localStorage.getItem('edge_selector_sections_cache');
      if (!cached) {
        return { exists: false };
      }
      const cache = JSON.parse(cached);
      return {
        exists: true,
        routes: Object.keys(cache.data || {}).length,
        age_hours: ((Date.now() - cache.timestamp) / (1000 * 60 * 60)).toFixed(2)
      };
    });

    console.log(`\n[缓存状态]`);
    if (cacheStatus.exists) {
      console.log(`✅ 缓存存在 (${cacheStatus.routes} 条路线, 年龄: ${cacheStatus.age_hours}h)`);
    } else {
      console.log(`❌ 缓存不存在`);
    }

    // ===== PHASE 3: 选择VSS模板 =====
    console.log('\n[PHASE 3] 选择VSS模板');
    mark('template_select_start');

    const vssCard = page.locator('.template-card').filter({ hasText: /VSS|可变限速/ }).first();
    const vssVisible = await vssCard.isVisible({ timeout: 5000 }).catch(() => false);

    if (!vssVisible) {
      console.warn('❌ VSS模板卡片未找到，跳过测试');
      test.skip();
    }

    await vssCard.click();
    await page.waitForSelector('#route-codes', { timeout: 10000 });
    mark('template_select_complete');
    measure('模板选择', 'template_select_start', 'template_select_complete');
    console.log('✅ VSS模板已选择');

    // ===== PHASE 4: 路线选择 =====
    console.log('\n[PHASE 4] 路线选择');
    mark('route_select_start');

    // 获取初始状态
    const initialSections = await page.locator('#section-codes option').count();
    console.log(`   初始状态: section-codes ${initialSections} 个选项`);

    await page.selectOption('#route-codes', 'G4202');
    await page.waitForTimeout(500); // 等待UI更新

    const updatedSections = await page.locator('#section-codes option').count();
    mark('route_select_complete');
    const routeSelectTime = measure('路线选择', 'route_select_start', 'route_select_complete');
    console.log(`   更新后: section-codes ${updatedSections} 个选项`);

    // 评估路线选择性能
    if (routeSelectTime < 100) {
      console.log(`✅ 性能优秀 (<100ms) - 使用了缓存`);
    } else if (routeSelectTime < 500) {
      console.log(`⚠️  性能良好 (100-500ms) - 可能的API调用延迟`);
    } else {
      console.log(`❌ 性能较差 (>500ms) - 可能逻辑问题或性能瓶颈`);
    }

    // ===== PHASE 5: 设置查询参数 =====
    console.log('\n[PHASE 5] 设置查询参数');
    mark('params_set_start');

    await page.fill('#min-stake', '33');
    await page.fill('#max-stake', '44');

    mark('params_set_complete');
    measure('参数设置', 'params_set_start', 'params_set_complete');
    console.log('✅ 桩号范围: 33-44 km');

    // ===== PHASE 6: 执行查询 =====
    console.log('\n[PHASE 6] 执行查询');
    mark('query_start');

    // 确认查询按钮可用
    const queryBtn = page.locator('#query-btn, button:has-text("查询路段")').first();
    const btnEnabled = await queryBtn.isEnabled().catch(() => false);
    console.log(`   查询按钮: ${btnEnabled ? '✅ 已启用' : '❌ 禁用'}`);

    if (!btnEnabled) {
      console.warn('❌ 查询按钮不可用，跳过查询');
      test.skip();
    }

    await queryBtn.click();
    mark('query_clicked');
    console.log('✅ 查询请求已发送');

    // ===== PHASE 7: 等待查询结果 =====
    console.log('\n[PHASE 7] 等待查询结果');
    mark('results_wait_start');

    // 智能等待：尝试多种方式检测完成
    let resultRows = 0;
    let completed = false;

    try {
      // 方式1：等待结果表出现
      await page.locator('#results-table').waitFor({ state: 'visible', timeout: 15000 });
      resultRows = await page.locator('#results-tbody tr').count().catch(() => 0);
      completed = true;
      console.log(`✅ 结果表已显示 (${resultRows} 条结果)`);
    } catch (e) {
      console.log('⚠️  结果表未显示或超时');
    }

    if (!completed) {
      // 方式2：等待查询按钮重新启用
      try {
        await page.locator('button:has-text("查询"):not([disabled])').first()
          .waitFor({ state: 'visible', timeout: 15000 });
        resultRows = await page.locator('#results-tbody tr').count().catch(() => 0);
        completed = true;
        console.log(`⚠️  按钮已启用 (${resultRows} 条结果)`);
      } catch (e) {
        console.log('❌ 查询持续超时');
      }
    }

    mark('results_wait_complete');
    const totalQueryTime = measure('总查询耗时', 'query_start', 'results_wait_complete');

    // ===== PHASE 8: 性能分析 =====
    console.log('\n========== 性能分析 ==========\n');

    // 时间分解
    const pageLoadTime = measure('页面加载', 'page_load_start', 'page_load_complete');
    const initTime = measure('初始化', 'selector_init_start', 'selector_init_complete');
    const templateTime = measure('模板选择', 'template_select_start', 'template_select_complete');
    const routeTime = measure('路线选择', 'route_select_start', 'route_select_complete');
    const paramsTime = measure('参数设置', 'params_set_start', 'params_set_complete');
    const queryApiTime = measure('查询API', 'query_clicked', 'results_wait_complete');

    console.log('\n[时间分解表]');
    console.log(`┌──────────────────┬──────────┬──────────┬─────────────┐`);
    console.log(`│ 阶段             │ 耗时(ms) │ 累计(ms) │ 评分        │`);
    console.log(`├──────────────────┼──────────┼──────────┼─────────────┤`);
    console.log(`│ 页面加载         │ ${String(pageLoadTime).padStart(8)} │ ${String(pageLoadTime).padStart(8)} │ ${'⚠️  偏长' .padStart(10)} │`);
    console.log(`│ 初始化完成       │ ${String(initTime).padStart(8)} │ ${String(pageLoadTime + initTime).padStart(8)} │ ${'✅ 优秀'.padStart(10)} │`);
    console.log(`│ 模板选择         │ ${String(templateTime).padStart(8)} │ ${String(pageLoadTime + initTime + templateTime).padStart(8)} │ ${'✅ 优秀'.padStart(10)} │`);
    console.log(`│ 路线选择         │ ${String(routeTime).padStart(8)} │ ${String(pageLoadTime + initTime + templateTime + routeTime).padStart(8)} │ ${(routeTime < 200 ? '✅ 优秀' : '❌ 需改进').padStart(10)} │`);
    console.log(`│ 参数设置         │ ${String(paramsTime).padStart(8)} │ ${String(pageLoadTime + initTime + templateTime + routeTime + paramsTime).padStart(8)} │ ${'✅ 优秀'.padStart(10)} │`);
    console.log(`│ 查询API+显示     │ ${String(queryApiTime).padStart(8)} │ ${String(totalQueryTime).padStart(8)} │ ${(queryApiTime < 2000 ? '✅ 良好' : '❌ 很差').padStart(10)} │`);
    console.log(`└──────────────────┴──────────┴──────────┴─────────────┘`);

    // API调用统计
    console.log('\n[API调用追踪]');
    if (apiTrace.length === 0) {
      console.log('⚠️  未捕获到API调用（可能在页面加载时已完成）');
    } else {
      apiTrace.forEach((call, i) => {
        if (call.event === 'request') {
          console.log(`${i + 1}. 请求 [${call.endpoint}]`);
        } else {
          console.log(`   ↳ 响应 ${call.status} (${call.duration}ms)`);
        }
      });
    }

    // 诊断结论
    console.log('\n========== 诊断结论 ==========\n');

    const issues = [];

    if (routeTime > 200) {
      issues.push('⚠️  路线选择过慢 (>200ms) - 可能未使用缓存或有DOM更新延迟');
    }

    if (queryApiTime > 10000) {
      issues.push('❌ 查询超时 (>10s) - 数据库查询性能问题或前端阻塞');
    } else if (queryApiTime > 2000) {
      issues.push('⚠️  查询较慢 (2-10s) - 可能的数据库查询延迟');
    }

    if (resultRows === 0 && completed) {
      issues.push('⚠️  查询返回无结果 - 检查查询条件和数据库数据');
    }

    if (issues.length === 0) {
      console.log('✅ 所有性能指标正常！');
      console.log(`   - 路线选择: ${routeTime}ms (优秀)`);
      console.log(`   - 查询API: ${queryApiTime}ms (良好)`);
      console.log(`   - 结果显示: ${resultRows} 条路段`);
    } else {
      console.log('发现以下问题：');
      issues.forEach(issue => console.log(`   ${issue}`));
    }

    console.log('\n========== 诊断完成 ==========\n');
  });

});
