# 前端自动化测试行动计划 (Frontend Automation Test Action Plan)

## 优先级 1: 启用网络监听和API验证 (CRITICAL)

### 任务 1.1: 添加浏览器网络日志
**文件**: `tests/e2e/test_frontend_smart.spec.js`
**位置**: `testTemplate()` 函数开头

```javascript
// 添加网络日志监听
page.on('response', async (response) => {
  if (response.url().includes('/api/v1/control/strategy-instances/')) {
    const status = response.status();
    const body = await response.text();
    console.log(`[API_RESPONSE] ${status} - ${response.url()}`);
    if (status >= 400) {
      console.error(`[API_ERROR] ${status}:`, body);
    }
  }
});
```

**预期效果**: 能看到实际的API错误,而非仅看到UI点击成功

### 任务 1.2: 修改步骤9(提交策略)的验证逻辑
**文件**: `tests/e2e/test_frontend_smart.spec.js`
**位置**: 第348-389行

```javascript
// ===== 步骤9: 提交策略并验证API响应 =====
console.log('[步骤9] 提交策略...');

const submitBtn = page.locator('#save-strategy-btn');
const isEnabled = await submitBtn.isEnabled().catch(() => false);

if (!isEnabled) {
  const title = await submitBtn.getAttribute('title');
  console.error(`✗ 提交按钮禁用: ${title}`);
  return false;
}

// 关键改进: 等待API响应
let apiResponse = null;
const responsePromise = page.waitForResponse(
  response => response.url().includes('/api/v1/control/strategy-instances/'),
  { timeout: 15000 }
).then(async (r) => {
  const status = r.status();
  const body = await r.json();
  apiResponse = { status, body };
  return r;
}).catch(err => {
  console.error('[API] 未收到API响应:', err.message);
  return null;
});

// 点击提交按钮
await submitBtn.click();
console.log('  ✓ 提交按钮已点击');

// 等待API响应完成
await responsePromise;
await page.waitForTimeout(2000);

if (!apiResponse) {
  console.error('✗ 未收到API响应');
  return false;
}

if (apiResponse.status !== 201) {
  console.error(`✗ 策略创建失败: ${apiResponse.status}`);
  console.error(`  错误: ${JSON.stringify(apiResponse.body, null, 2)}`);
  return false;
} else {
  const strategyId = apiResponse.body.strategy_id;
  console.log(`✓ 策略创建成功: ${strategyId}`);
}
```

---

## 优先级 2: 修复DHS模板(时间间隔表格) (HIGH)

### 任务 2.1: 识别DHS时间间隔表格位置
**方法**: 在浏览器中手动测试DHS模板,确定:
1. 表格的CSS选择器
2. 添加按钮的位置和文本
3. 表格行的输入字段结构

**检查清单**:
- [ ] 找到时间间隔表格
- [ ] 确认表格是否默认有行(或需要添加)
- [ ] 列出所有需要填充的字段(begin_hours, end_hours, status, allowed_vehicle_types)
- [ ] 确认数据格式和验证规则

### 任务 2.2: 实现DHS表格填充函数
**文件**: `tests/e2e/test_frontend_smart.spec.js`
**新增函数**: 在第285-309行的DHS检查代码中改进

```javascript
async function fillDHSIntervalTable(page, templateType) {
  console.log('  [DHS] 填充时间间隔表格...');

  // 根据DHS子类型填充不同的时间间隔
  let intervals = [];
  if (templateType === 'dhs_peak_hours') {
    intervals = [
      { begin: 7, end: 9, status: 'OPEN', vehicles: ['passenger', 'truck'] },
      { begin: 17, end: 19, status: 'OPEN', vehicles: ['passenger', 'truck'] },
    ];
  } else if (templateType === 'dhs_passenger_only') {
    intervals = [
      { begin: 8, end: 11, status: 'OPEN', vehicles: ['passenger'] },
      { begin: 15, end: 18, status: 'OPEN', vehicles: ['passenger'] },
    ];
  } else if (templateType === 'dhs_peak_multi_interval') {
    intervals = [
      { begin: 6, end: 8, status: 'OPEN', vehicles: ['passenger', 'truck'] },
      { begin: 8, end: 11, status: 'OPEN', vehicles: ['passenger'] },
      { begin: 14, end: 18, status: 'OPEN', vehicles: ['passenger', 'truck'] },
    ];
  }

  // 为每个间隔添加一行
  for (const interval of intervals) {
    const addBtn = page.locator('table button:has-text("添加")').first();
    if (await addBtn.isVisible()) {
      await addBtn.click();
      await page.waitForTimeout(300);
    }

    // 填充这一行的数据
    const lastRow = page.locator('table tbody tr').last();
    const inputs = await lastRow.locator('input[type="number"]').all();

    if (inputs.length >= 2) {
      await inputs[0].fill(interval.begin.toString());
      await inputs[1].fill(interval.end.toString());
      console.log(`    ✓ 添加时间间隔: ${interval.begin:02d}:00 - ${interval.end:02d}:00`);
    }

    await page.waitForTimeout(300);
  }

  console.log('  ✓ DHS时间间隔填充完成');
}
```

### 任务 2.3: 在步骤8中调用该函数
修改第294-319行,在策略名称前调用上述函数

---

## 优先级 3: 修复TEC节点类型过滤 (HIGH)

### 任务 3.1: 确认TEC节点类型选择器的准确位置
**方法**: 使用浏览器开发者工具检查
1. 元素是`<select>`还是自定义组件?
2. 确切的CSS类或aria-label是什么?
3. 选项文本是"entrance"还是其他?

**示例代码**:
```bash
# 在Chrome DevTools Console中运行:
document.querySelectorAll('[name*="node"], [aria-label*="节点"]').forEach(el => {
  console.log('选择器:', el);
  console.log('可见:', el.offsetHeight > 0);
  console.log('选项:', Array.from(el.options || el.querySelectorAll('[role="option"]')).map(o => o.textContent));
});
```

### 任务 3.2: 改进TEC节点类型选择逻辑
**文件**: `tests/e2e/test_frontend_smart.spec.js`
**位置**: 第180-197行

```javascript
if (template.type === 'TEC') {
  console.log('  ℹ 检测到TEC模板，选择节点类型=entrance...');

  // 方法1: 尝试使用select标签
  const select = page.locator('select[name*="node_type"], select[aria-label*="节点"]').first();
  if (await select.isVisible({ timeout: 5000 }).catch(() => false)) {
    await select.selectOption('entrance');
    console.log(`  ✓ 已通过select标签选择: entrance`);
    await page.waitForTimeout(800);
  }

  // 方法2: 如果是自定义下拉框
  else {
    const dropdown = page.locator('[class*="dropdown"], [class*="select"]').filter({
      has: page.locator('text=节点')
    }).first();

    if (await dropdown.isVisible({ timeout: 5000 }).catch(() => false)) {
      await dropdown.click();
      await page.waitForTimeout(300);

      const option = page.locator('[role="option"]:has-text("entrance"), div:has-text("entrance")').first();
      if (await option.isVisible({ timeout: 3000 }).catch(() => false)) {
        await option.click();
        console.log(`  ✓ 已通过自定义下拉框选择: entrance`);
        await page.waitForTimeout(800);
      }
    }
  }

  // 验证选择结果
  const selectedValue = await page.locator('[class*="selected"], [aria-selected="true"]').textContent();
  if (selectedValue && selectedValue.includes('entrance')) {
    console.log(`  ✓ 确认选择成功: ${selectedValue}`);
  } else {
    console.warn(`  ⚠ 未确认选择成功,继续执行`);
  }
}
```

### 任务 3.3: 增加TEC的边数预期
由于节点类型限制,"entrance"类型的边可能很少,需要:
1. 调查G5路线有多少entrance节点
2. 如果<2个,考虑使用其他路线或增加最小边数要求

```javascript
// 在TEMPLATES配置中修改TEC部分
{
  templateId: 'tec_flow_metering',
  templateName: '收费入口 - 流量控制',
  strategyName: 'TEC流量控制-UI测试',
  type: 'TEC',
  route: 'G5',
  edgeCount: 1  // 改为1,因为G5entrance节点可能很少
},
```

---

## 优先级 4: 增强测试可靠性 (MEDIUM)

### 任务 4.1: 添加步骤级别的错误恢复
某个步骤失败时,记录充分信息便于调试

### 任务 4.2: 添加测试报告生成
自动生成HTML报告,包含:
- 成功/失败统计
- 每个步骤的时间
- 失败原因分析
- 截图和视频

### 任务 4.3: 集成到CI/CD
在GitHub Actions中运行,定期执行

---

## 执行时间表 (Timeline)

| 优先级 | 任务 | 预期时间 | 负责人 |
|--------|------|---------|--------|
| P1 | 1.1 - 网络日志 | 30分钟 | - |
| P1 | 1.2 - API验证 | 60分钟 | - |
| P2 | 2.1 - 识别DHS表格 | 45分钟 | - |
| P2 | 2.2 - 实现DHS填充 | 90分钟 | - |
| P2 | 2.3 - 集成DHS函数 | 30分钟 | - |
| P3 | 3.1 - 确认TEC选择器 | 45分钟 | - |
| P3 | 3.2 - 改进选择逻辑 | 60分钟 | - |
| P3 | 3.3 - 调整期望 | 30分钟 | - |
| P4 | 4.1-4.3 - 增强 | 120分钟 | - |

**总预计时间**: ~520分钟 (~8.7小时)

---

## 验收标准 (Acceptance Criteria)

- [ ] 所有11个测试报告"通过"
- [ ] 数据库中存在所有11个创建的策略实例
- [ ] 策略名称与测试脚本中定义的相匹配
- [ ] 测试执行日志清晰,无模糊错误
- [ ] API请求全部返回201状态码

---

## 风险和依赖 (Risks & Dependencies)

### 依赖
- ✓ API服务器运行中 (http://localhost:8000)
- ✓ PostgreSQL数据库可访问
- ✓ Playwright已安装配置

### 风险
- DHS/TEC UI结构可能比预期复杂
- 浏览器自动化可能遇到React/Vue等框架的动态更新
- 时间间隔验证规则可能未在测试脚本中完全实现

---

**文档更新**: 2025-11-01
**版本**: 1.0

