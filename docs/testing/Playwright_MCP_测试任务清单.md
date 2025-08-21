# Playwright MCP 自动化测试任务清单

## 📋 测试概述

本文档定义了OD数据处理与仿真系统的Playwright MCP自动化测试任务，涵盖系统的主要功能模块和用户交互流程。

**测试目标：** 验证系统各功能模块的正常工作，确保用户界面响应正确，数据处理流程完整。

**测试环境：** 
- 本地开发环境 (http://localhost:8000)
- Playwright MCP工具
- 预设的测试数据

**测试优势：**
- ✅ 稳定可靠，兼容性好
- ✅ 错误信息清晰，便于调试
- ✅ 支持多种浏览器引擎
- ✅ 元素定位精确，交互稳定

---

## 🧪 测试任务清单

### 1. 基础功能测试

#### 1.1 页面加载和导航 ✅
- **测试步骤：**
  1. 访问 http://localhost:8000
  2. 验证页面标题显示正确
  3. 检查导航菜单项完整性
  
- **预期结果：**
  - 页面成功加载
  - 标题：`OD数据处理与仿真系统`
  - 导航菜单包含：OD数据处理、仿真运行、结果分析、案例管理、模板查看
  
- **Playwright MCP验证方法：**
  ```javascript
  // 检查页面标题
  await expect(page).toHaveTitle("OD数据处理与仿真系统");
  
  // 检查导航菜单项数量
  const navLinks = page.locator(".nav-link");
  await expect(navLinks).toHaveCount(5);
  
  // 验证导航菜单项可见性
  await expect(page.locator("text=OD数据处理")).toBeVisible();
  await expect(page.locator("text=仿真运行")).toBeVisible();
  await expect(page.locator("text=结果分析")).toBeVisible();
  await expect(page.locator("text=案例管理")).toBeVisible();
  await expect(page.locator("text=模板查看")).toBeVisible();
  ```

#### 1.2 模板文件加载 ✅
- **测试步骤：**
  1. 检查TAZ文件下拉选项
  2. 检查网络文件下拉选项
  
- **预期结果：**
  - TAZ文件选项：TAZ_5_validated.add.xml, TAZ_4.add.xml
  - 网络文件选项：sichuan202508v7.net.xml, sichuan202503v6.net.xml, sichuan202503v5.net.xml
  
- **Playwright MCP验证方法：**
  ```javascript
  // 检查TAZ文件选择器
  const tazSelect = page.locator("#taz-file");
  await expect(tazSelect).toBeVisible();
  
  // 检查TAZ文件选项数量
  const tazOptions = tazSelect.locator("option");
  await expect(tazOptions).toHaveCountGreaterThan(2);
  
  // 检查特定TAZ文件选项
  await expect(page.locator("option[value*='TAZ_5_validated']")).toBeVisible();
  await expect(page.locator("option[value*='TAZ_4']")).toBeVisible();
  
  // 检查网络文件选择器
  const networkSelect = page.locator("#network-file");
  await expect(networkSelect).toBeVisible();
  
  // 检查网络文件选项数量
  const networkOptions = networkSelect.locator("option");
  await expect(networkOptions).toHaveCountGreaterThan(3);
  
  // 检查特定网络文件选项
  await expect(page.locator("option[value*='sichuan202503v6']")).toBeVisible();
  ```

---

### 2. OD数据处理测试

#### 2.1 时间选择器功能
- **测试步骤：**
  1. 修改开始时间为：2025/08/04 08:00:00
  2. 修改结束时间为：2025/08/04 08:15:00
  3. 修改时间间隔为：1分钟
  
- **预期结果：**
  - 开始时间：2025-08-04T08:00
  - 结束时间：2025-08-04T08:15
  - 时间间隔：1
  
- **Playwright MCP验证方法：**
  ```javascript
  // 设置时间值
  await page.locator("#start-time").fill("2025-08-04T08:00");
  await page.locator("#end-time").fill("2025-08-04T08:15");
  await page.locator("#interval-minutes").fill("1");
  
  // 验证时间值
  await expect(page.locator("#start-time")).toHaveValue("2025-08-04T08:00");
  await expect(page.locator("#end-time")).toHaveValue("2025-08-04T08:15");
  await expect(page.locator("#interval-minutes")).toHaveValue("1");
  ```

#### 2.2 文件选择功能
- **测试步骤：**
  1. 选择TAZ文件：TAZ_5_validated.add.xml
  2. 选择网络文件：sichuan202503v6.net.xml
  
- **预期结果：**
  - TAZ文件已选择：TAZ_5_validated.add.xml
  - 网络文件已选择：sichuan202503v6.net.xml
  
- **Playwright MCP验证方法：**
  ```javascript
  // 选择文件
  await page.locator("#taz-file").selectOption("templates/taz_files/TAZ_5_validated.add.xml");
  await page.locator("#network-file").selectOption("templates/network_files/sichuan202503v6.net.xml");
  
  // 验证文件选择
  await expect(page.locator("#taz-file")).toHaveValue("templates/taz_files/TAZ_5_validated.add.xml");
  await expect(page.locator("#network-file")).toHaveValue("templates/network_files/sichuan202503v6.net.xml");
  ```

#### 2.3 案例信息填写
- **测试步骤：**
  1. 填写案例名称：Playwright MCP 自动化测试案例
  2. 填写案例描述：这是一个使用Playwright MCP进行自动化测试的案例，测试OD数据处理表单的完整功能
  
- **预期结果：**
  - 案例名称已填写
  - 案例描述已填写
  
- **Playwright MCP验证方法：**
  ```javascript
  // 填写案例信息
  await page.locator("#case-name").fill("Playwright MCP 自动化测试案例");
  await page.locator("#case-description").fill("这是一个使用Playwright MCP进行自动化测试的案例，测试OD数据处理表单的完整功能");
  
  // 验证案例信息
  await expect(page.locator("#case-name")).toHaveValue("Playwright MCP 自动化测试案例");
  await expect(page.locator("#case-description")).toContainText("Playwright MCP");
  ```

#### 2.4 表单提交测试
- **测试步骤：**
  1. 点击"处理OD数据"按钮
  2. 等待处理完成
  3. 检查处理结果
  
- **预期结果：**
  - 表单成功提交
  - 显示处理进度
  - 最终显示成功消息和案例ID
  
- **Playwright MCP验证方法：**
  ```javascript
  // 提交表单
  const submitButton = page.locator("#process-od-btn");
  await expect(submitButton).toBeVisible();
  await submitButton.click();
  
  // 等待处理开始
  await page.waitForTimeout(3000);
  
  // 检查结果区域
  const resultArea = page.locator("#od-processing-result");
  await expect(resultArea).toBeVisible();
  
  // 验证处理结果包含关键信息
  await expect(page.locator("text=运行文件夹")).toBeVisible();
  await expect(page.locator("text=OD文件")).toBeVisible();
  await expect(page.locator("text=路由文件")).toBeVisible();
  ```

---

### 3. 仿真运行测试

#### 3.1 案例选择
- **测试步骤：**
  1. 切换到"仿真运行"标签页
  2. 选择刚创建的案例
  3. 点击"刷新案例列表"按钮
  
- **预期结果：**
  - 案例下拉列表包含刚创建的案例
  - 案例信息正确显示
  
- **Playwright MCP验证方法：**
  ```javascript
  // 切换到仿真运行标签页
  await page.locator("a[href='#simulation']").click();
  
  // 检查案例选择下拉框
  const caseSelect = page.locator("#simulation-case");
  await expect(caseSelect).toBeVisible();
  
  // 点击刷新案例列表按钮
  const refreshButton = page.locator("#refresh-simulation-cases-btn");
  await refreshButton.click();
  
  // 等待案例加载
  await page.waitForTimeout(2000);
  
  // 检查案例选项
  const caseOptions = caseSelect.locator("option");
  await expect(caseOptions).toHaveCountGreaterThan(0);
  ```

#### 3.2 仿真参数配置
- **测试步骤：**
  1. 填写仿真名称：Playwright MCP 仿真测试
  2. 填写仿真描述：自动化测试仿真运行功能
  3. 选择仿真类型：微观仿真
  4. 选择运行模式：后台运行
  5. 配置输出选项：summary, tripinfo
  
- **预期结果：**
  - 所有参数正确设置
  - 输出选项正确勾选
  
- **Playwright MCP验证方法：**
  ```javascript
  // 填写仿真参数
  await page.locator("#simulation-name").fill("Playwright MCP 仿真测试");
  await page.locator("#simulation-description").fill("自动化测试仿真运行功能");
  
  // 选择仿真类型
  await page.locator("#simulation-type").selectOption("microscopic");
  
  // 选择运行模式
  await page.locator("#gui-mode").selectOption("false");
  
  // 配置输出选项
  const summaryCheckbox = page.locator("#sim-out-summary");
  const tripinfoCheckbox = page.locator("#sim-out-tripinfo");
  
  // 确保必要的输出选项被选中
  if (!(await summaryCheckbox.isChecked())) {
    await summaryCheckbox.check();
  }
  if (!(await tripinfoCheckbox.isChecked())) {
    await tripinfoCheckbox.check();
  }
  
  // 验证参数设置
  await expect(page.locator("#simulation-name")).toHaveValue("Playwright MCP 仿真测试");
  await expect(page.locator("#simulation-type")).toHaveValue("microscopic");
  await expect(page.locator("#gui-mode")).toHaveValue("false");
  await expect(summaryCheckbox).toBeChecked();
  await expect(tripinfoCheckbox).toBeChecked();
  ```

#### 3.3 仿真启动和监控
- **测试步骤：**
  1. 点击"启动仿真"按钮
  2. 观察仿真状态变化
  3. 监控进度条更新
  4. 等待仿真完成
  5. 检测仿真成功结果
  6. 验证仿真输出文件
  
- **预期结果：**
  - 仿真成功启动
  - 状态显示"仿真运行中"
  - 进度条正常更新
  - 仿真状态最终显示"仿真完成"或"仿真成功"
  - 仿真结果区域显示完整的仿真信息
  - 仿真输出文件正确生成
  
- **Playwright MCP验证方法：**
  ```javascript
  // 启动仿真
  const runButton = page.locator("#run-simulation-btn");
  await expect(runButton).toBeVisible();
  await runButton.click();
  
  // 检查仿真状态 - 启动阶段
  await expect(page.locator("text=仿真运行中")).toBeVisible();
  
  // 监控仿真进度（等待仿真完成，最多等待60秒）
  let simulationCompleted = false;
  let waitTime = 0;
  const maxWaitTime = 60000; // 60秒
  
  while (!simulationCompleted && waitTime < maxWaitTime) {
    await page.waitForTimeout(2000); // 每2秒检查一次
    waitTime += 2000;
    
    // 检查仿真状态
    const statusText = page.locator(".status-text, .simulation-status");
    if (await statusText.count() > 0) {
      const currentStatus = await statusText.first().textContent();
      
      if (currentStatus.includes("仿真完成") || currentStatus.includes("仿真成功")) {
        simulationCompleted = true;
        console.log("✅ 仿真成功完成");
        break;
      } else if (currentStatus.includes("仿真失败") || currentStatus.includes("失败")) {
        console.log("❌ 仿真执行失败");
        throw new Error("仿真执行失败");
      }
    }
  }
  
  if (!simulationCompleted) {
    console.log("⚠️ 仿真超时，检查当前状态");
  }
  
  // 检查仿真结果区域
  await expect(page.locator("text=仿真运行结果")).toBeVisible();
  
  // 验证仿真信息完整性
  await expect(page.locator("text=运行文件夹")).toBeVisible();
  await expect(page.locator("text=仿真类型")).toBeVisible();
  await expect(page.locator("text=状态")).toBeVisible();
  
  // 检测仿真成功结果 - 详细验证
  // 1. 检查仿真状态为成功
  const finalStatus = page.locator(".status-text, .simulation-status");
  if (await finalStatus.count() > 0) {
    const statusText = await finalStatus.first().textContent();
    if (statusText.includes("仿真完成") || statusText.includes("仿真成功")) {
      console.log("✅ 仿真状态验证成功");
    } else {
      console.log("⚠️ 仿真状态异常:", statusText);
    }
  }
  
  // 2. 检查仿真输出文件信息
  await expect(page.locator("text=输出文件")).toBeVisible();
  await expect(page.locator("text=summary.xml")).toBeVisible();
  await expect(page.locator("text=tripinfo.xml")).toBeVisible();
  
  // 3. 检查仿真配置信息
  await expect(page.locator("text=仿真配置")).toBeVisible();
  await expect(page.locator("text=仿真名称")).toBeVisible();
  await expect(page.locator("text=仿真类型")).toBeVisible();
  
  // 4. 检查仿真时间信息
  await expect(page.locator("text=开始时间")).toBeVisible();
  await expect(page.locator("text=结束时间")).toBeVisible();
  await expect(page.locator("text=运行时长")).toBeVisible();
  
  // 5. 验证仿真结果数据
  const resultData = page.locator(".simulation-result-data, .result-info");
  if (await resultData.count() > 0) {
    console.log("✅ 仿真结果数据区域可见");
    
    // 检查是否有错误信息
    const errorMessages = page.locator("text=错误, text=失败, text=Error");
    if (await errorMessages.count() > 0) {
      console.log("⚠️ 发现仿真错误信息");
      const errorText = await errorMessages.first().textContent();
      console.log("错误详情:", errorText);
    }
  }
  
  // 6. 检查仿真日志（如果可见）
  const simulationLog = page.locator(".simulation-log, .log-output");
  if (await simulationLog.count() > 0) {
    console.log("✅ 仿真日志区域可见");
    
    // 检查日志中是否包含成功信息
    const successIndicators = page.locator("text=成功, text=完成, text=SUCCESS");
    if (await successIndicators.count() > 0) {
      console.log("✅ 仿真日志显示成功状态");
    }
  }
  
  console.log("🎉 仿真启动和监控测试完成");
  ```

---

### 4. 结果分析测试

#### 4.1 分析案例选择
- **测试步骤：**
  1. 切换到"结果分析"标签页
  2. 选择已完成的仿真案例
  
- **预期结果：**
  - 案例列表包含已完成的案例
  - 案例选择成功
  
- **Playwright MCP验证方法：**
  ```javascript
  // 切换到结果分析标签页
  await page.locator("a[href='#accuracy-analysis']").click();
  
  // 检查案例选择下拉框
  const analysisCaseSelect = page.locator("#analysis-case");
  await expect(analysisCaseSelect).toBeVisible();
  
  // 选择案例（如果有可用案例）
  const caseOptions = analysisCaseSelect.locator("option");
  if (await caseOptions.count() > 1) {
    await analysisCaseSelect.selectOption({ index: 1 });
  }
  ```

#### 4.2 分析执行
- **测试步骤：**
  1. 点击"开始分析"按钮
  2. 等待分析完成
  
- **预期结果：**
  - 分析成功执行
  - 显示分析结果或错误信息
  
- **Playwright MCP验证方法：**
  ```javascript
  // 检查执行分析按钮
  const runAnalysisButton = page.locator("#run-analysis-btn");
  await expect(runAnalysisButton).toBeVisible();
  
  // 点击开始分析按钮
  await runAnalysisButton.click();
  
  // 等待分析响应
  await page.waitForTimeout(3000);
  
  // 检查分析状态（可能成功或失败）
  const analysisResult = page.locator("#analysis-result, .error-message");
  await expect(analysisResult).toBeVisible();
  ```

#### 4.3 精度分析详细测试

##### 4.3.1 精度分析基础功能
- **测试步骤：**
  1. 选择"精度"分析类型
  2. 确保案例和仿真结果已选择
  3. 点击"开始分析"按钮
  4. 监控分析进度
  
- **预期结果：**
  - 精度分析类型正确选择
  - 分析进度条正常显示
  - 分析状态实时更新
  
- **Playwright MCP验证方法：**
  ```javascript
  // 选择精度分析类型
  const accuracyTypeSelect = page.locator("#analysis-type");
  await accuracyTypeSelect.selectOption("精度");
  
  // 验证精度分析类型已选择
  await expect(accuracyTypeSelect).toHaveValue("accuracy");
  
  // 点击开始分析按钮
  const startAnalysisButton = page.locator("#start-analysis-btn");
  await expect(startAnalysisButton).toBeVisible();
  await startAnalysisButton.click();
  
  // 等待分析开始
  await page.waitForTimeout(2000);
  
  // 检查分析进度显示
  const progressBar = page.locator(".analysis-progress, .progress-bar");
  if (await progressBar.count() > 0) {
    await expect(progressBar).toBeVisible();
    console.log("✅ 精度分析进度条显示正常");
  }
  
  // 检查分析状态
  const analysisStatus = page.locator(".analysis-status, .status-text");
  if (await analysisStatus.count() > 0) {
    await expect(analysisStatus).toBeVisible();
    const statusText = await analysisStatus.first().textContent();
    console.log("当前分析状态:", statusText);
  }
  ```

##### 4.3.2 精度分析结果验证
- **测试步骤：**
  1. 等待精度分析完成
  2. 检查分析结果页面
  3. 验证精度指标显示
  4. 检查图表和可视化
  
- **预期结果：**
  - 分析成功完成
  - 显示完整的精度评估结果
  - 包含关键精度指标
  - 图表正确渲染
  
- **Playwright MCP验证方法：**
  ```javascript
  // 等待分析完成（最多等待5分钟）
  let analysisCompleted = false;
  let waitTime = 0;
  const maxWaitTime = 300000; // 5分钟
  
  while (!analysisCompleted && waitTime < maxWaitTime) {
    await page.waitForTimeout(5000); // 每5秒检查一次
    waitTime += 5000;
    
    // 检查分析状态
    const statusElements = page.locator(".analysis-status, .status-text, .result-status");
    if (await statusElements.count() > 0) {
      const currentStatus = await statusElements.first().textContent();
      
      if (currentStatus.includes("分析完成") || currentStatus.includes("分析成功") || currentStatus.includes("completed")) {
        analysisCompleted = true;
        console.log("✅ 精度分析成功完成");
        break;
      } else if (currentStatus.includes("分析失败") || currentStatus.includes("失败") || currentStatus.includes("error")) {
        console.log("❌ 精度分析执行失败");
        throw new Error("精度分析执行失败");
      }
    }
  }
  
  if (!analysisCompleted) {
    console.log("⚠️ 精度分析超时，检查当前状态");
  }
  
  // 检查精度分析结果区域
  const accuracyResults = page.locator("#accuracy-results, .accuracy-analysis-results");
  await expect(accuracyResults).toBeVisible();
  
  // 验证关键精度指标
  await expect(page.locator("text=精度评估")).toBeVisible();
  await expect(page.locator("text=总体精度")).toBeVisible();
  await expect(page.locator("text=门架匹配率")).toBeVisible();
  await expect(page.locator("text=时间精度")).toBeVisible();
  await expect(page.locator("text=路径精度")).toBeVisible();
  
  // 检查数值指标显示
  const accuracyMetrics = page.locator(".accuracy-metric, .metric-value");
  if (await accuracyMetrics.count() > 0) {
    console.log("✅ 精度指标数值显示正常");
    
    // 验证精度值范围（应该在0-100%之间）
    for (let i = 0; i < Math.min(await accuracyMetrics.count(), 5); i++) {
      const metricText = await accuracyMetrics.nth(i).textContent();
      if (metricText.includes("%")) {
        const percentage = parseFloat(metricText.replace("%", ""));
        if (percentage >= 0 && percentage <= 100) {
          console.log(`✅ 精度指标 ${metricText} 数值范围正常`);
        } else {
          console.log(`⚠️ 精度指标 ${metricText} 数值范围异常`);
        }
      }
    }
  }
  
  // 检查图表显示
  const charts = page.locator(".accuracy-chart, .chart-container, canvas");
  if (await charts.count() > 0) {
    console.log("✅ 精度分析图表显示正常");
    
    // 验证图表类型
    await expect(page.locator("text=精度分布图")).toBeVisible();
    await expect(page.locator("text=时间精度对比")).toBeVisible();
    await expect(page.locator("text=路径精度热力图")).toBeVisible();
  }
  
  // 检查详细分析报告
  const detailedReport = page.locator(".detailed-report, .analysis-report");
  if (await detailedReport.count() > 0) {
    console.log("✅ 详细分析报告显示正常");
    
    // 验证报告内容
    await expect(page.locator("text=分析摘要")).toBeVisible();
    await expect(page.locator("text=数据质量评估")).toBeVisible();
    await expect(page.locator("text=精度影响因素")).toBeVisible();
    await expect(page.locator("text=改进建议")).toBeVisible();
  }
  ```

##### 4.3.3 精度分析数据验证
- **测试步骤：**
  1. 检查精度分析的数据来源
  2. 验证门架数据匹配
  3. 检查时间精度计算
  4. 验证路径精度评估
  
- **预期结果：**
  - 数据来源正确
  - 门架匹配逻辑正确
  - 时间精度计算准确
  - 路径精度评估合理
  
- **Playwright MCP验证方法：**
  ```javascript
  // 检查数据来源信息
  const dataSourceInfo = page.locator(".data-source, .source-info");
  if (await dataSourceInfo.count() > 0) {
    await expect(page.locator("text=门架数据")).toBeVisible();
    await expect(page.locator("text=仿真结果")).toBeVisible();
    await expect(page.locator("text=数据时间范围")).toBeVisible();
    console.log("✅ 数据来源信息显示完整");
  }
  
  // 验证门架匹配详情
  const gantryMatching = page.locator(".gantry-matching, .matching-details");
  if (await gantryMatching.count() > 0) {
    await expect(page.locator("text=门架匹配率")).toBeVisible();
    await expect(page.locator("text=匹配门架数")).toBeVisible();
    await expect(page.locator("text=未匹配门架")).toBeVisible();
    
    // 检查匹配率数值
    const matchingRate = page.locator(".matching-rate, .rate-value");
    if (await matchingRate.count() > 0) {
      const rateText = await matchingRate.first().textContent();
      console.log(`门架匹配率: ${rateText}`);
    }
  }
  
  // 检查时间精度分析
  const timeAccuracy = page.locator(".time-accuracy, .time-precision");
  if (await timeAccuracy.count() > 0) {
    await expect(page.locator("text=时间精度")).toBeVisible();
    await expect(page.locator("text=平均时间误差")).toBeVisible();
    await expect(page.locator("text=标准差")).toBeVisible();
    
    // 验证时间误差范围
    const timeError = page.locator(".time-error, .error-value");
    if (await timeError.count() > 0) {
      const errorText = await timeError.first().textContent();
      console.log(`时间误差: ${errorText}`);
    }
  }
  
  // 检查路径精度分析
  const pathAccuracy = page.locator(".path-accuracy, .route-precision");
  if (await pathAccuracy.count() > 0) {
    await expect(page.locator("text=路径精度")).toBeVisible();
    await expect(page.locator("text=路径匹配度")).toBeVisible();
    await expect(page.locator("text=路径偏差")).toBeVisible();
    
    // 验证路径精度指标
    const pathMetrics = page.locator(".path-metric, .route-metric");
    if (await pathMetrics.count() > 0) {
      for (let i = 0; i < Math.min(await pathMetrics.count(), 3); i++) {
        const metricText = await pathMetrics.nth(i).textContent();
        console.log(`路径精度指标 ${i+1}: ${metricText}`);
      }
    }
  }
  ```

##### 4.3.4 精度分析导出功能
- **测试步骤：**
  1. 检查导出按钮可用性
  2. 测试PDF报告导出
  3. 测试Excel数据导出
  4. 验证导出文件完整性
  
- **预期结果：**
  - 导出功能正常
  - 导出文件格式正确
  - 导出内容完整
  
- **Playwright MCP验证方法：**
  ```javascript
  // 检查导出功能区域
  const exportSection = page.locator(".export-section, .export-options");
  if (await exportSection.count() > 0) {
    await expect(page.locator("text=导出分析结果")).toBeVisible();
    
    // 检查PDF导出按钮
    const pdfExportButton = page.locator("button:has-text('PDF报告'), .pdf-export");
    if (await pdfExportButton.count() > 0) {
      await expect(pdfExportButton).toBeVisible();
      console.log("✅ PDF导出功能可用");
    }
    
    // 检查Excel导出按钮
    const excelExportButton = page.locator("button:has-text('Excel数据'), .excel-export");
    if (await excelExportButton.count() > 0) {
      await expect(excelExportButton).toBeVisible();
      console.log("✅ Excel导出功能可用");
    }
    
    // 检查CSV导出按钮
    const csvExportButton = page.locator("button:has-text('CSV数据'), .csv-export");
    if (await csvExportButton.count() > 0) {
      await expect(csvExportButton).toBeVisible();
      console.log("✅ CSV导出功能可用");
    }
  }
  
  // 测试PDF导出功能
  const pdfExportBtn = page.locator("button:has-text('PDF报告')");
  if (await pdfExportBtn.count() > 0) {
    await pdfExportBtn.click();
    
    // 等待导出处理
    await page.waitForTimeout(3000);
    
    // 检查导出状态
    const exportStatus = page.locator(".export-status, .download-status");
    if (await exportStatus.count() > 0) {
      const statusText = await exportStatus.first().textContent();
      if (statusText.includes("导出成功") || statusText.includes("下载完成")) {
        console.log("✅ PDF报告导出成功");
      } else {
        console.log("⚠️ PDF导出状态:", statusText);
      }
    }
  }
  
  // 测试Excel导出功能
  const excelExportBtn = page.locator("button:has-text('Excel数据')");
  if (await excelExportBtn.count() > 0) {
    await excelExportBtn.click();
    
    // 等待导出处理
    await page.waitForTimeout(3000);
    
    // 检查导出状态
    const excelStatus = page.locator(".excel-export-status, .download-status");
    if (await excelStatus.count() > 0) {
      const statusText = await excelStatus.first().textContent();
      if (statusText.includes("导出成功") || statusText.includes("下载完成")) {
        console.log("✅ Excel数据导出成功");
      } else {
        console.log("⚠️ Excel导出状态:", statusText);
      }
    }
  }
  ```

##### 4.3.5 精度分析历史记录
- **测试步骤：**
  1. 点击"查看历史结果"按钮
  2. 检查历史分析记录
  3. 验证历史结果完整性
  4. 测试历史结果对比
  
- **预期结果：**
  - 历史记录正确显示
  - 历史结果完整保存
  - 对比功能正常工作
  
- **Playwright MCP验证方法：**
  ```javascript
  // 点击查看历史结果按钮
  const historyButton = page.locator("button:has-text('查看历史结果'), #view-history-btn");
  if (await historyButton.count() > 0) {
    await expect(historyButton).toBeVisible();
    await historyButton.click();
    
    // 等待历史记录加载
    await page.waitForTimeout(2000);
    
    // 检查历史记录区域
    const historySection = page.locator(".history-section, .historical-results");
    if (await historySection.count() > 0) {
      await expect(historySection).toBeVisible();
      console.log("✅ 历史记录区域显示正常");
      
      // 检查历史记录列表
      const historyList = page.locator(".history-list, .historical-list");
      if (await historyList.count() > 0) {
        const historyItems = historyList.locator(".history-item, .historical-item");
        const itemCount = await historyItems.count();
        console.log(`历史记录数量: ${itemCount}`);
        
        if (itemCount > 0) {
          // 检查最新的历史记录
          const latestItem = historyItems.first();
          await expect(latestItem).toBeVisible();
          
          // 验证历史记录信息
          await expect(latestItem.locator("text=分析时间")).toBeVisible();
          await expect(latestItem.locator("text=分析类型")).toBeVisible();
          await expect(latestItem.locator("text=精度结果")).toBeVisible();
          
          // 点击查看详情
          const viewDetailsBtn = latestItem.locator("button:has-text('查看详情')");
          if (await viewDetailsBtn.count() > 0) {
            await viewDetailsBtn.click();
            await page.waitForTimeout(1000);
            
            // 验证历史详情
            await expect(page.locator("text=历史分析详情")).toBeVisible();
            await expect(page.locator("text=分析参数")).toBeVisible();
            await expect(page.locator("text=分析结果")).toBeVisible();
          }
        }
      }
    }
  }
  
  // 测试历史结果对比功能
  const compareButton = page.locator("button:has-text('对比分析'), .compare-results");
  if (await compareButton.count() > 0) {
    await expect(compareButton).toBeVisible();
    await compareButton.click();
    
    // 等待对比界面加载
    await page.waitForTimeout(2000);
    
    // 检查对比功能
    const compareSection = page.locator(".compare-section, .comparison-view");
    if (await compareSection.count() > 0) {
      await expect(compareSection).toBeVisible();
      console.log("✅ 历史结果对比功能正常");
      
      // 验证对比内容
      await expect(page.locator("text=精度对比")).toBeVisible();
      await expect(page.locator("text=趋势分析")).toBeVisible();
      await expect(page.locator("text=改进效果")).toBeVisible();
    }
  }
  ```

---

### 5. 案例管理测试

#### 5.1 案例列表查看
- **测试步骤：**
  1. 切换到"案例管理"标签页
  2. 查看案例列表
  
- **预期结果：**
  - 显示所有已创建的案例
  - 案例信息完整
  
- **Playwright MCP验证方法：**
  ```javascript
  // 切换到案例管理标签页
  await page.locator("a[href='#case-management']").click();
  
  // 等待页面加载
  await page.waitForTimeout(2000);
  
  // 检查案例列表区域
  const caseListArea = page.locator("#case-list");
  if (await caseListArea.count() > 0) {
    await expect(caseListArea).toBeVisible();
  }
  
  // 检查搜索和筛选功能
  await expect(page.locator("text=搜索案例")).toBeVisible();
  await expect(page.locator("text=全部状态")).toBeVisible();
  ```

#### 5.2 案例详情查看
- **测试步骤：**
  1. 点击案例的"查看详情"按钮
  2. 查看案例详细信息
  
- **预期结果：**
  - 显示案例完整信息
  - 包含文件路径、状态等
  
- **Playwright MCP验证方法：**
  ```javascript
  // 查找可用的查看按钮
  const viewButtons = page.locator("button:has-text('查看')");
  
  if (await viewButtons.count() > 0) {
    // 点击第一个查看按钮
    await viewButtons.first().click();
    
    // 等待详情加载
    await page.waitForTimeout(1000);
    
    // 验证详情信息
    await expect(page.locator("text=ID:")).toBeVisible();
    await expect(page.locator("text=状态:")).toBeVisible();
    await expect(page.locator("text=创建时间:")).toBeVisible();
  }
  ```

---

### 6. 模板查看测试

#### 6.1 模板文件列表
- **测试步骤：**
  1. 切换到"模板查看"标签页
  2. 查看TAZ和网络文件模板
  
- **预期结果：**
  - 显示所有可用模板
  - 模板信息完整
  
- **Playwright MCP验证方法：**
  ```javascript
  // 切换到模板查看标签页
  await page.locator("a[href='#templates']").click();
  
  // 等待页面加载
  await page.waitForTimeout(2000);
  
  // 检查模板区域
  const templateArea = page.locator("#templates");
  await expect(templateArea).toBeVisible();
  
  // 检查模板分类按钮
  await expect(page.locator("button:has-text('TAZ模板')")).toBeVisible();
  await expect(page.locator("button:has-text('网络模板')")).toBeVisible();
  await expect(page.locator("button:has-text('仿真模板')")).toBeVisible();
  
  // 验证模板详情
  await expect(page.locator("text=TAZ_5_validated.add.xml")).toBeVisible();
  await expect(page.locator("text=版本:")).toBeVisible();
  await expect(page.locator("text=状态:")).toBeVisible();
  ```

---

## 🔍 测试验证要点

### 数据一致性验证
- [ ] 案例元数据中的文件路径正确
- [ ] 生成的sumocfg包含TAZ文件配置
- [ ] 仿真输出文件路径正确

### 错误处理验证
- [ ] 必填字段验证
- [ ] 文件不存在时的错误提示
- [ ] 网络错误时的用户友好提示

### 性能验证
- [ ] 页面加载时间 < 3秒
- [ ] 表单提交响应时间 < 2秒
- [ ] 仿真启动响应时间 < 5秒

---

## 📝 测试执行记录

### 测试日期：_________
### 测试人员：_________
### 测试环境：_________

| 测试项目 | 状态 | 备注 |
|---------|------|------|
| 基础功能测试 | ⬜ | |
| OD数据处理测试 | ⬜ | |
| 仿真运行测试 | ⬜ | |
| 结果分析测试 | ⬜ | |
| 结果分析-精度分析详细测试 | ⬜ | 新增详细测试任务 |
| 案例管理测试 | ⬜ | |
| 模板查看测试 | ⬜ | |

### 发现的问题：
1. _________________________________
2. _________________________________
3. _________________________________

### 测试结论：
_________________________________

---

## 🚀 Playwright MCP 测试指南

### 环境准备
```bash
# 确保Playwright已安装
playwright --version

# 安装浏览器（如果未安装）
playwright install

# 启动API服务
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 测试执行流程
1. **启动系统服务**：确保API和前端服务正常运行
2. **准备测试数据**：检查模板文件和数据库连接
3. **执行测试任务**：按照清单逐步执行测试步骤
4. **记录测试结果**：记录成功/失败状态和发现的问题
5. **生成测试报告**：整理测试结果和问题清单

### 测试技巧
- **等待策略**：使用`page.waitForTimeout()`等待页面加载
- **元素定位**：优先使用ID选择器，其次使用文本内容
- **错误处理**：捕获并记录详细的错误信息
- **状态验证**：验证每个操作后的页面状态变化

---

## 📚 相关文档

- [API文档](../api_docs/README.md)
- [部署指南](../DEPLOYMENT_GUIDE.md)
- [开发指南](../development/新架构开发指南.md)
- [架构重构报告](../development/架构重构完成报告.md)

---

## 🎯 精度分析专项测试执行指南

### 测试前置条件
1. **案例准备**：确保有已完成的OD数据处理案例
2. **仿真完成**：确保仿真已成功运行并完成
3. **数据同步**：等待仿真结果与分析模块同步（建议等待5-10分钟）

### 测试执行顺序
1. **基础功能验证**：案例选择、分析类型选择
2. **分析执行测试**：启动精度分析、监控进度
3. **结果验证测试**：检查精度指标、图表显示
4. **数据验证测试**：验证数据来源、计算逻辑
5. **导出功能测试**：测试各种导出格式
6. **历史记录测试**：验证历史数据管理

### 关键验证点
- **精度指标范围**：所有百分比值应在0-100%之间
- **数据一致性**：门架匹配率应与实际数据一致
- **时间精度**：时间误差应在合理范围内
- **图表渲染**：所有图表应正确显示，无渲染错误
- **导出完整性**：导出文件应包含完整的分析结果

### 常见问题处理
- **分析超时**：检查数据量和系统性能，适当延长等待时间
- **图表不显示**：检查浏览器兼容性和JavaScript错误
- **导出失败**：检查文件权限和磁盘空间
- **数据不匹配**：验证案例选择和仿真结果关联

---

*最后更新：2025-08-20*
*版本：v2.1 - 增加精度分析详细测试*
