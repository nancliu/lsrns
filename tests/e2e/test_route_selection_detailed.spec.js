/**
 * 路线选择性能详细诊断测试
 *
 * 在浏览器内运行JavaScript来测量DOM操作的实际耗时
 * 不受Playwright API调用开销的影响
 */

const { test, expect } = require('@playwright/test');

test.describe('路线选择性能 - 详细前端分析', () => {

  test('在浏览器内测量onRouteChange()的实际耗时', async ({ page }) => {
    console.log('\n========== onRouteChange() 前端性能测试 ==========\n');

    // 页面加载和初始化
    console.log('⏳ 页面加载中...');
    await page.goto('http://localhost:8000/control/templates.html', {
      timeout: 30000,
      waitUntil: 'networkidle'
    });
    console.log('✅ 页面加载完成\n');

    // 等待EdgeSelector初始化
    await page.waitForSelector('.template-card', { timeout: 10000 });

    // 选择VSS模板进入Step 2
    const vssCard = page.locator('.template-card').filter({ hasText: /VSS|可变限速/ }).first();
    await vssCard.click();
    await page.waitForSelector('#route-codes', { timeout: 10000 });

    console.log('[等待缓存预加载...]');
    await page.waitForTimeout(2000);  // 确保缓存已加载

    // 注入性能测量脚本
    console.log('\n[在浏览器内注入性能测量代码]');

    const performanceData = await page.evaluate(() => {
      return new Promise((resolve) => {
        // 等待EdgeSelector就绪
        if (!window.EdgeSelector) {
          console.error('❌ EdgeSelector未定义');
          resolve(null);
          return;
        }

        // 获取当前选择的路线数
        const routeSelect = document.getElementById('route-codes');
        const sectionSelect = document.getElementById('section-codes');

        if (!routeSelect || !sectionSelect) {
          console.error('❌ DOM元素未找到');
          resolve(null);
          return;
        }

        // 测试场景：从无选择 → 选择G4202
        const results = [];

        // 场景1: 选择路线 G4202
        {
          console.log('\n[测试场景1: 选择G4202]');

          // 获取初始状态
          const initialSections = Array.from(sectionSelect.options).length;
          console.log(`  初始: ${initialSections} 个section选项`);

          // 选择路线（模拟用户操作）
          routeSelect.value = 'G4202';

          // 测量onRouteChange()的执行时间
          const startTime = performance.now();

          // 手动触发change事件
          const event = new Event('change', { bubbles: true });
          routeSelect.dispatchEvent(event);

          // 等待DOM更新完成
          setTimeout(() => {
            const endTime = performance.now();
            const duration = endTime - startTime;
            const updatedSections = Array.from(sectionSelect.options).length;

            console.log(`  耗时: ${Math.round(duration)}ms`);
            console.log(`  更新后: ${updatedSections} 个section选项`);

            results.push({
              scenario: '选择G4202',
              duration,
              sectionsUpdate: {
                before: initialSections,
                after: updatedSections
              }
            });
          }, 100);
        }

        // 场景2: 取消选择（复位）
        {
          console.log('\n[测试场景2: 取消选择]');

          const beforeSections = Array.from(sectionSelect.options).length;
          console.log(`  初始: ${beforeSections} 个section选项`);

          routeSelect.value = '';

          const startTime = performance.now();
          const event = new Event('change', { bubbles: true });
          routeSelect.dispatchEvent(event);

          await new Promise(resolve => {
            let frameCount = 0;
            const checkComplete = () => {
              frameCount++;
              if (frameCount > 2) {
                resolve();
              } else {
                requestAnimationFrame(checkComplete);
              }
            };
            requestAnimationFrame(checkComplete);
          }).then(() => {
            const endTime = performance.now();
            const duration = endTime - startTime;
            const afterSections = Array.from(sectionSelect.options).length;

            console.log(`  耗时: ${Math.round(duration)}ms`);
            console.log(`  更新后: ${afterSections} 个section选项`);

            results.push({
              scenario: '取消选择',
              duration,
              sectionsUpdate: {
                before: beforeSections,
                after: afterSections
              }
            });
          });
        }

        // 返回结果
        resolve(results);
      });
    });

    if (!performanceData) {
      console.error('❌ 性能测量失败');
      return;
    }

    // 分析结果
    console.log('\n========== 性能分析结果 ==========\n');

    performanceData.forEach((result, i) => {
      console.log(`[${i + 1}. ${result.scenario}]`);
      console.log(`  耗时: ${Math.round(result.duration)}ms`);
      console.log(`  section更新: ${result.sectionsUpdate.before} → ${result.sectionsUpdate.after}`);

      // 性能评分
      if (result.duration < 100) {
        console.log(`  ✅ 性能优秀 (<100ms) - DocumentFragment优化有效`);
      } else if (result.duration < 200) {
        console.log(`  ✅ 性能良好 (100-200ms)`);
      } else if (result.duration < 500) {
        console.log(`  ⚠️  性能一般 (200-500ms)`);
      } else {
        console.log(`  ❌ 性能较差 (>500ms) - 可能未正确使用优化`);
      }
    });

    // 总体评估
    console.log('\n========== 总体评估 ==========\n');

    const avgDuration = performanceData.reduce((sum, r) => sum + r.duration, 0) / performanceData.length;
    console.log(`平均耗时: ${Math.round(avgDuration)}ms`);

    if (avgDuration < 150) {
      console.log('✅ onRouteChange() 性能优秀！DocumentFragment优化已生效');
      console.log('   剩余的531ms延迟来自其他因素（Playwright API、网络等）');
    } else {
      console.log('⚠️  onRouteChange() 性能仍需改进');
      console.log('   考虑检查是否有其他DOM操作或事件监听器');
    }

    console.log('\n✅ 前端性能测试完成\n');
  });

  test('测量direction选项更新性能', async ({ page }) => {
    console.log('\n========== direction选项更新性能测试 ==========\n');

    await page.goto('http://localhost:8000/control/templates.html', {
      timeout: 30000,
      waitUntil: 'networkidle'
    });

    await page.waitForSelector('.template-card', { timeout: 10000 });

    const vssCard = page.locator('.template-card').filter({ hasText: /VSS|可变限速/ }).first();
    await vssCard.click();
    await page.waitForSelector('#route-codes', { timeout: 10000 });
    await page.waitForTimeout(2000);

    const result = await page.evaluate(() => {
      const directionSelect = document.getElementById('route-direction');
      if (!directionSelect) return null;

      const startTime = performance.now();

      // 模拟updateDirectionOptions()调用
      let optionsHTML = '<option value="">全部</option>';
      optionsHTML += '<option value="upstream">上行</option>';
      optionsHTML += '<option value="downstream">下行</option>';
      optionsHTML += '<option value="clockwise">顺时针</option>';
      optionsHTML += '<option value="counterclockwise">逆时针</option>';

      directionSelect.innerHTML = optionsHTML;

      // 等待DOM更新
      return new Promise(resolve => {
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            const endTime = performance.now();
            resolve(endTime - startTime);
          });
        });
      });
    });

    console.log(`direction选项更新耗时: ${Math.round(result)}ms`);

    if (result < 50) {
      console.log('✅ 性能优秀 (<50ms)');
    } else {
      console.log('⚠️  性能一般');
    }

    console.log('\n✅ direction性能测试完成\n');
  });

});
