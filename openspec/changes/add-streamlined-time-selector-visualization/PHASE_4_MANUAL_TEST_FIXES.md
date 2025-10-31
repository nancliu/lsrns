# Phase 4: 手动测试发现问题修复报告

**日期**: 2025-10-31
**状态**: 进行中
**OpenSpec变更ID**: `add-streamlined-time-selector-visualization`

## 概述

本文档记录了Phase 4阶段基于手动测试反馈的问题修复工作。手动测试由用户在真实环境中进行，发现了3个关键问题需要修复。

## 问题来源

**测试场景**: 应急车道开放（DHS）定时管控模板配置流程

**测试步骤**:
1. 选择模板 → 应急车道开放 定时管控
2. 选择路段 → 14个路段，3.69 km，G4202 K35+101 - K34+890
3. 配置参数 → 时间配置表 + 时间轴可视化

**测试截图**: 用户提供的截图显示了配置参数步骤（步骤3）的界面

## 发现的问题

### 问题1: DHS时间轴与配置表未正确联动 ⏳

**严重程度**: P0 (高)
**状态**: 待修复

**问题描述**:
- 在配置参数步骤中，可视化时间轴与时间配置表未正确联动
- 用户修改时间配置表中的值时，时间轴没有实时更新
- 这导致用户无法直观看到配置变化

**根本原因分析**:
通过代码审查发现，DHS时间轴更新逻辑已经实现：
- `updateDHSTimelineFromTable()` 函数存在 (parameter_form.js:905-936)
- 事件监听器已绑定 (parameter_form.js:895-897)
- 防抖机制已实现 (300ms)

**可能的原因**:
1. TimelineVisualizer未正确加载（JavaScript加载顺序问题）
2. DHS模板的default_value格式与期望不符
3. 时间轴初始化时机问题（在表格渲染前调用）
4. 控制台可能有JavaScript错误阻止更新

**修复计划**:
- [ ] 需要API服务器运行才能进行E2E测试验证
- [ ] 创建的E2E测试: `tests/e2e/test_dhs_timeline_sync.spec.js` (8个测试用例)
- [ ] 手动测试验证：选择DHS模板 → 修改时间配置 → 观察时间轴变化
- [ ] 检查浏览器控制台是否有JavaScript错误

**相关文件**:
- `frontend/control/js/parameter_form.js` (renderDHSIntervalControl, updateDHSTimelineFromTable)
- `frontend/control/js/timeline_visualizer.js` (updateTimeline)
- `tests/e2e/test_dhs_timeline_sync.spec.js` (新创建的测试文件)

---

### 问题2: 车型配置表样式允许多行，影响效果 ⏳

**严重程度**: P1 (中)
**状态**: 待实现

**问题描述**:
- 在DHS时间配置表中，"允许车型"列使用多选下拉框（`<select multiple>`）
- 当选中多个车型时，表格单元格可能显示为多行文本
- 这导致表格行高不一致，视觉效果混乱

**当前实现**:
```html
<select class="dhs-interval-vehicles" multiple size="4">
  <option value="passenger">乘用车</option>
  <option value="bus">公交车</option>
  <option value="truck">货车</option>
  <option value="emergency">应急车</option>
  <option value="authority">执法车</option>
</select>
```

**期望效果**:
- 紧凑、单行显示
- 使用徽章/标签样式显示车型（类似芯片组件）
- 如果车型超过3个，显示 "+N more" 提示
- 悬停时显示完整车型列表

**解决方案设计**:

**方案A: CSS限制 + 省略号**
```css
.dhs-interval-vehicles {
  max-height: 2em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```
- 优点：简单快速
- 缺点：用户看不到完整车型列表

**方案B: 徽章样式显示 (推荐)**
```html
<div class="vehicle-badges">
  <span class="badge badge-passenger">乘用车</span>
  <span class="badge badge-truck">货车</span>
  <span class="badge-more">+2 more</span>
</div>
```
```css
.badge {
  display: inline-block;
  padding: 2px 8px;
  margin: 2px;
  border-radius: 12px;
  font-size: 12px;
  background-color: #3b82f6;
  color: white;
}
.badge-more {
  color: #6b7280;
  font-style: italic;
}
```
- 优点：视觉美观，信息清晰
- 缺点：需要修改JavaScript渲染逻辑

**方案C: 显示数量 + 悬停提示**
```html
<span class="vehicle-count" title="乘用车, 公交车, 货车, 应急车">4 种车型</span>
```
- 优点：极简，不占空间
- 缺点：信息隐藏，需要悬停才能看到

**推荐实施**: 方案B（徽章） + 方案C（悬停提示）组合
- 显示前3个车型为徽章
- 超过3个显示 "+N more"
- 悬停显示完整列表的tooltip

**修复计划**:
- [ ] 创建CSS文件：`frontend/control/css/vehicle-type-badges.css`
- [ ] 修改JavaScript渲染逻辑：`addDHSIntervalRow()` 和 `addFlowIntervalRow()`
- [ ] 实现徽章组件渲染函数
- [ ] 添加tooltip显示完整车型列表
- [ ] 手动测试：选择多个车型，验证显示效果

**相关文件**:
- `frontend/control/js/parameter_form.js` (addDHSIntervalRow, addFlowIntervalRow)
- `frontend/control/css/templates-forms.css` (或新建 vehicle-type-badges.css)

---

### 问题3: 配置参数步骤缺少模板卡片显示 ⏳

**严重程度**: P1 (中)
**状态**: 待实现

**问题描述**:
- 在步骤2（选择路段）中，用户可以看到所选模板的卡片（模板名称、策略类型、描述）
- 在步骤3（配置参数）中，缺少模板卡片，用户只能看到参数表单
- 这导致用户在配置参数时无法快速确认当前模板信息

**期望效果**:
在步骤3（配置参数）顶部显示模板卡片，包含：
- 模板名称（如 "应急车道开放 定时管控"）
- 策略类型标签（DHS）
- 路段信息（14个路段，3.69 km，G4202 K35+101 - K34+890）
- 简短描述

**当前步骤流程**:
1. **步骤1: 选择模板** → 显示模板卡片列表
2. **步骤2: 选择路段** → 显示所选模板卡片 + 路段选择器
3. **步骤3: 配置参数** → ❌ 缺少模板卡片，仅显示参数表单

**解决方案设计**:

**HTML结构**:
```html
<div id="step3-config-params" class="step-content">
  <!-- [NEW] 添加模板摘要卡片 -->
  <div class="template-summary-card">
    <div class="card-header">
      <h3 class="template-name">应急车道开放 定时管控</h3>
      <span class="strategy-type-badge badge-dhs">DHS</span>
    </div>
    <div class="card-body">
      <div class="segment-info">
        <span class="segment-count">14个路段</span>
        <span class="segment-length">3.69 km</span>
        <span class="segment-range">G4202 K35+101 - K34+890</span>
      </div>
      <p class="template-description">在交通拥堵时段开放应急车道...</p>
    </div>
  </div>

  <!-- 现有的参数表单 -->
  <div id="params-form-container">
    ...
  </div>
</div>
```

**CSS样式** (复用现有 `.template-card` 样式):
```css
.template-summary-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.template-summary-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.template-name {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.strategy-type-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-dhs {
  background-color: #10b981;
  color: white;
}

.segment-info {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
  color: #6b7280;
  font-size: 14px;
}

.template-description {
  color: #4b5563;
  font-size: 14px;
  margin: 0;
}
```

**JavaScript实现**:
```javascript
/**
 * Render template summary card in configure parameters step
 */
function renderTemplateSummaryCard(template, selectedSegments) {
  const card = document.createElement('div');
  card.className = 'template-summary-card';

  // Header
  const header = document.createElement('div');
  header.className = 'card-header';

  const title = document.createElement('h3');
  title.className = 'template-name';
  title.textContent = template.strategy_name;

  const badge = document.createElement('span');
  badge.className = `strategy-type-badge badge-${template.strategy_type.toLowerCase()}`;
  badge.textContent = template.strategy_type;

  header.appendChild(title);
  header.appendChild(badge);

  // Body
  const body = document.createElement('div');
  body.className = 'card-body';

  // Segment info
  const segmentInfo = document.createElement('div');
  segmentInfo.className = 'segment-info';

  const segmentCount = document.createElement('span');
  segmentCount.className = 'segment-count';
  segmentCount.textContent = `${selectedSegments.count}个路段`;

  const segmentLength = document.createElement('span');
  segmentLength.className = 'segment-length';
  segmentLength.textContent = `${selectedSegments.totalLength} km`;

  const segmentRange = document.createElement('span');
  segmentRange.className = 'segment-range';
  segmentRange.textContent = selectedSegments.range;

  segmentInfo.appendChild(segmentCount);
  segmentInfo.appendChild(segmentLength);
  segmentInfo.appendChild(segmentRange);

  // Description
  const description = document.createElement('p');
  description.className = 'template-description';
  description.textContent = template.description || '';

  body.appendChild(segmentInfo);
  body.appendChild(description);

  card.appendChild(header);
  card.appendChild(body);

  return card;
}

// 在 showStep3ConfigureParameters() 中调用
function showStep3ConfigureParameters() {
  const container = document.getElementById('params-form-container');
  container.innerHTML = '';

  // [NEW] 添加模板摘要卡片
  const summaryCard = renderTemplateSummaryCard(
    currentTemplate,
    {
      count: selectedEdges.length,
      totalLength: calculateTotalLength(selectedEdges),
      range: calculateSegmentRange(selectedEdges)
    }
  );
  container.parentElement.insertBefore(summaryCard, container);

  // 现有的参数表单渲染逻辑
  ...
}
```

**修复计划**:
- [ ] 分析步骤2中模板卡片的实现（`frontend/control/templates.html`）
- [ ] 创建可复用的 `renderTemplateSummaryCard()` 函数
- [ ] 修改 `showStep3ConfigureParameters()` 添加卡片渲染
- [ ] 添加CSS样式（复用或新建）
- [ ] 计算路段统计信息（段数、总长度、范围）
- [ ] 手动测试：进入步骤3，验证卡片显示正确

**相关文件**:
- `frontend/control/templates.html` (步骤3的HTML结构)
- `frontend/control/js/` (showStep3ConfigureParameters 函数所在文件)
- `frontend/control/css/templates-base.css` (卡片样式)

---

## 额外发现的问题

### 问题4: Edge选择器控件缺少name属性 ✅ 已修复

**严重程度**: P0 (高)
**状态**: 已修复 (2025-10-31)

**问题描述**:
- 在E2E测试过程中，edge选择器总是失败
- 根本原因：路线代码和路段代码控件缺乏`name`属性
- Playwright无法使用语义化选择器（如 `select[name="route_code"]`）找到这些元素

**修复内容**:
已为以下控件添加`name`属性：
- ✅ 路线代码: `<select id="route-codes" name="route_code" multiple>`
- ✅ 路段代码: `<select id="section-codes" name="section_code" multiple>`
- ✅ 行驶方向: `<select id="route-direction" name="direction">`
- ✅ 最小/最大桩号: `name="min_stake"`, `name="max_stake"`
- ✅ 最小/最大长度: `name="min_length"`, `name="max_length"`
- ✅ 最小车道数: `name="min_lanes"`
- ✅ 节点类型: `name="node_types"`
- ✅ 示范段: `name="demonstration_ids"`
- ✅ 包含门架: `name="with_gantry"`

**修改文件**:
- `frontend/control/templates.html` (Lines 111-198)

**影响范围**:
- 所有需要选择路段的E2E测试现在可以使用更稳定的选择器
- 示例：`page.locator('select[name="route_code"]')` 代替 `page.locator('.route-select').first()`

---

## 修复优先级

| 优先级 | 问题 | 状态 | 预估工作量 |
|--------|------|------|------------|
| P0 | Edge选择器name属性 | ✅ 已完成 | 0.5天 |
| P0 | DHS时间轴同步问题 | ⏳ 待修复 | 1-2天 |
| P1 | 车型表格样式优化 | ⏳ 待实现 | 1-2天 |
| P1 | 模板卡片显示 | ⏳ 待实现 | 1天 |

## 总工作量估算

- **已完成**: 0.5天 (Edge选择器name属性)
- **待完成**: 4-5天 (DHS同步 + 车型样式 + 模板卡片)
- **总计**: 4.5-5.5天

## 测试计划

### E2E自动化测试

**已创建**:
- ✅ `tests/e2e/test_dhs_timeline_sync.spec.js` (8个测试用例)
  - DHS timeline显示
  - begin_hours改变时时间轴更新
  - end_hours改变时时间轴更新
  - status改变时颜色更新
  - 添加行时时间轴增加段
  - 删除行时时间轴移除段
  - 时间轴布局和样式
  - 无控制台错误

**待创建**:
- [ ] 车型徽章样式测试
- [ ] 模板卡片显示测试

### 手动测试清单

- [ ] **DHS时间轴同步**:
  1. 启动API服务器
  2. 访问 `http://localhost:8000/control/templates.html`
  3. 选择 "应急车道开放 定时管控" 模板
  4. 选择路段（任意）
  5. 进入配置参数步骤
  6. 修改时间配置表的值
  7. 观察时间轴是否实时更新
  8. 检查控制台是否有错误

- [ ] **车型表格样式**:
  1. 在DHS配置步骤
  2. 选择多个车型（>3个）
  3. 验证显示为徽章样式
  4. 验证显示 "+N more"
  5. 悬停查看完整列表

- [ ] **模板卡片显示**:
  1. 选择任意模板
  2. 选择路段
  3. 进入配置参数步骤
  4. 验证顶部显示模板卡片
  5. 验证卡片包含：模板名、策略类型、路段信息、描述

## 后续步骤

1. **立即执行** (需API服务器):
   - [ ] 运行DHS timeline sync测试，验证edge selector修复有效
   - [ ] 调试DHS时间轴同步问题（如果测试失败）
   - [ ] 手动测试DHS配置流程，确认问题复现

2. **本周完成**:
   - [ ] 修复DHS时间轴同步问题
   - [ ] 实现车型徽章样式
   - [ ] 实现模板卡片显示

3. **验收标准**:
   - [ ] 所有E2E测试通过（100%通过率）
   - [ ] 手动测试清单全部通过
   - [ ] 无控制台错误
   - [ ] 用户验收测试通过

## 参考资料

- 原始反馈：用户手动测试截图 (DHS配置步骤)
- Tasks清单：`openspec/changes/add-streamlined-time-selector-visualization/tasks.md`
- E2E测试：`tests/e2e/test_dhs_timeline_sync.spec.js`
- 相关代码：
  - `frontend/control/js/parameter_form.js` (DHS渲染和更新逻辑)
  - `frontend/control/js/timeline_visualizer.js` (时间轴可视化)
  - `frontend/control/templates.html` (HTML结构和步骤流程)
