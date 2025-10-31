# OpenSpec 变更完成行动计划
**目标**: 完成 `add-streamlined-time-selector-visualization` 中的所有剩余任务
**优先级**: P0 (立即)
**估计工作量**: 3-5 天

---

## 执行摘要

根据参数分析报告的发现，以下任务是完成此 OpenSpec 变更所需的：

### ✅ 已完成的任务
- [x] Phase 1: 核心时间轴可视化 (VSS)
- [x] Phase 1.5: TEC 车型限制集成 (tec_interval_array)
- [x] Phase 4: 手动测试发现的问题修复

### ⚠️ 需要完成的任务
- [ ] 验证 DHS 时间轴的颜色映射
- [ ] 实现 TEC 流量时间轴的颜色映射
- [ ] 完成 DHS 和 TEC 的 E2E 测试

### 📋 整体完成度
- **Parameter Analysis**: 100% 完成
- **VSS Timeline**: 100% 完成 + 已测试
- **DHS Timeline**: 实现 ✅ + 需验证 ⚠️
- **TEC Timeline**: 部分实现 (tec_interval_array ✅, flow_interval_array ❌)

---

## 任务分解

### 任务1: DHS 时间轴验证 (High Priority)
**目标**: 确保 DHS 时间轴正确显示 OPEN (绿色) 和 CLOSED (红色)
**时间估计**: 1-2 小时

#### 1.1 代码检查
```
文件: timeline_visualizer.js
检查项:
  - getColorForValue(value, 'dhs') 是否正确处理 "OPEN"/"CLOSED"
  - getSlotLabel() 是否正确显示时间范围
  - renderTimeline() 时 dhs 类型的数据结构
```

**检查清单**:
```javascript
// Lines 34-38: DHS 颜色映射
function getColorForValue(value, type) {
  ...
  if (type === 'dhs') {
    return value === 'OPEN' ? '#22c55e' : '#ef4444'; // ← 验证值类型
  }
  ...
}

// Lines 95-96: 颜色映射选择
case 'dhs':
  return getColorForValue(slot.status, type); // ← status字段是否正确

// Lines 116-120: 标签生成
case 'simple_interval':
case 'dhs':
  return `${slot.begin_hours}:00 - ${slot.end_hours}:00`; // ✅ 正确
```

#### 1.2 数据流验证
```
追踪数据流:
  parameter_form.js renderDHSIntervalControl()
    ↓ 收集 interval 数据
    ↓ 传给 TimelineVisualizer.renderTimeline(intervals, {type: 'dhs'})
    ↓ timeline_visualizer.js 处理
    ↓ 生成颜色编码的时间轴
```

**验证代码** (parameter_form.js):
```javascript
// Lines 1110-1171: renderDHSIntervalControl()
// 查找时间轴更新逻辑
const updateDHSTimelineFromTable = function(tbody) {
  // ← 确认从表格收集了 begin_hours, end_hours, status
  // ← 确认传给 updateTimeline() 的格式正确
}
```

#### 1.3 手动测试
**步骤**:
1. 打开浏览器开发者工具 (F12)
2. 访问 templates.html
3. 选择 DHS 模板 (如 dhs_peak_hours)
4. 进入配置参数步骤
5. 检查时间轴是否显示
   - OPEN 区间: 绿色
   - CLOSED 区间: 红色
6. 修改 interval 的 status，验证颜色实时更新

**预期结果**:
```
时间轴应显示为:
[0-7h: 红色] [7-10h: 绿色] [10-17h: 红色] [17-19h: 绿色] [19-24h: 红色]
```

#### 1.4 创建/更新 E2E 测试
**文件**: `tests/e2e/test_dhs_timeline_sync.spec.js`

**测试用例**:
```javascript
test('DHS timeline displays OPEN/CLOSED status with correct colors', async ({ page }) => {
  // 加载 DHS 模板
  // 检查时间轴出现
  // 验证 OPEN 区间为绿色 (#22c55e)
  // 验证 CLOSED 区间为红色 (#ef4444)
  // 修改 status，验证颜色更新
});

test('DHS timeline updates when interval table changes', async ({ page }) => {
  // 添加新行
  // 修改 begin_hours
  // 修改 end_hours
  // 修改 status
  // 每次都验证时间轴实时更新
});
```

**运行命令**:
```bash
conda activate od_project
npx playwright test tests/e2e/test_dhs_timeline_sync.spec.js
```

---

### 任务2: TEC 流量时间轴实现 (Medium Priority)
**目标**: 为 flow_interval_array 实现流量值的颜色映射
**时间估计**: 1-2 小时
**依赖**: 任务1 (DHS 验证完成后进行)

#### 2.1 实现流量颜色映射

**文件**: `frontend/control/js/timeline_visualizer.js`

**修改方案**:

```javascript
// 在 getColorForValue() 中添加 flow 分支 (约 Line 95-96)

function getColorForValue(value, type) {
  if (type === 'speed') {
    // ... 现有 VSS 逻辑 ...
  } else if (type === 'dhs') {
    // ... 现有 DHS 逻辑 ...
  } else if (type === 'simple_interval') {
    return '#3b82f6'; // 蓝色
  } else if (type === 'flow') {
    // ← 新增: TEC 流量颜色映射
    const vph = parseFloat(value);
    if (isNaN(vph)) return '#9ca3af'; // 灰色 (无效值)

    // 颜色映射规则:
    // vph >= 400: 红色 (严重拥堵)
    // vph 200-399: 橙色 (中等流量)
    // vph < 200: 绿色 (低流量，正常)

    if (vph >= 400) return '#ef4444';      // 红
    if (vph >= 200) return '#f97316';      // 橙
    return '#22c55e';                       // 绿
  }
  return '#9ca3af'; // 默认灰色
}
```

#### 2.2 更新标签生成函数

**文件**: `frontend/control/js/timeline_visualizer.js`

**修改方案**:

```javascript
// 在 getSlotLabel() 中添加 flow 分支 (约 Line 116-120)

function getSlotLabel(slot, type) {
  switch (type) {
    case 'speed':
      return `${slot.speed_kmh} km/h`;
    case 'dhs':
    case 'simple_interval':
      return `${slot.begin_hours}:00 - ${slot.end_hours}:00`;
    case 'flow':
      // ← 新增: TEC 流量标签
      const vph = slot.vehsPerHour || slot.value;
      return `${vph} vph (${slot.begin_hours}:00-${slot.end_hours}:00)`;
    default:
      return '';
  }
}
```

#### 2.3 验证 TEC 流量数据结构

**文件**: `frontend/control/js/parameter_form.js`

**检查**:

```javascript
// 在 renderFlowIntervalControl() 中查找时间轴更新逻辑 (约 1000+ 行)
// 确认以下数据流:
//   1. 表格中收集 flow_intervals
//   2. 传给 TimelineVisualizer.renderTimeline(intervals, {type: 'flow'})
//   3. 每个 interval 包含: begin_hours, end_hours, vehsPerHour
```

#### 2.4 创建 TEC 流量时间轴 E2E 测试

**文件**: `tests/e2e/test_tec_flow_timeline_visualization.spec.js`

**测试用例**:

```javascript
test('TEC flow timeline displays correct color coding', async ({ page }) => {
  // 加载 TEC 流量模板
  // 检查时间轴出现
  // 验证不同 vph 值的颜色:
  //   - ≥400 vph: 红色
  //   - 200-399 vph: 橙色
  //   - <200 vph: 绿色
});

test('TEC flow timeline updates when flow intervals change', async ({ page }) => {
  // 修改 vehsPerHour
  // 验证颜色实时更新
  // 添加行、删除行、修改时间
});
```

---

### 任务3: E2E 测试完善 (Medium Priority)
**目标**: 确保所有时间轴相关的 E2E 测试通过
**时间估计**: 2-3 小时

#### 3.1 更新现有测试的选择器

**问题**: 一些测试使用 CSS 类选择器，可能不稳定

**解决方案**:
```javascript
// 旧选择器 (不稳定):
page.locator('.route-select').first()
page.locator('.section-select')

// 新选择器 (使用 name 属性，更稳定):
page.locator('select[name="route_code"]')
page.locator('select[name="section_code"]')
```

**需要更新的文件**:
- `tests/e2e/test_dhs_timeline_sync.spec.js` (已创建框架)
- `tests/e2e/test_tec_restriction_timeline.spec.js` (已创建)
- `tests/e2e/test_complete_parameter_flow.spec.js` (如果存在)

#### 3.2 完整的测试矩阵

| 测试文件 | 测试范围 | 状态 | 优先级 |
|--------|--------|------|-------|
| test_timeline_visualization.spec.js | VSS 时间轴 (基础) | ✅ 完成 | P0 |
| test_dhs_timeline_sync.spec.js | DHS 时间轴 + 同步 | ⚠️ 框架存在，需完善 | P0 |
| test_tec_restriction_timeline.spec.js | TEC 车型限制时间轴 | ✅ 完成 | P1 |
| test_tec_flow_timeline_visualization.spec.js | TEC 流量时间轴 | ❌ 需创建 | P1 |
| test_complete_parameter_flow.spec.js | 完整工作流 (所有策略) | ✅ 存在 | P0 |

#### 3.3 测试运行检查清单

```bash
# 1. 运行所有时间轴测试
conda activate od_project
npx playwright test tests/e2e/test_*timeline*.spec.js

# 2. 运行完整参数流测试
npx playwright test tests/e2e/test_complete_parameter_flow.spec.js

# 3. 运行所有 E2E 测试
npx playwright test

# 预期: 所有测试通过 ✅
```

---

### 任务4: 文档更新 (Low Priority)
**目标**: 更新项目文档，反映新的时间轴可视化功能
**时间估计**: 1-2 小时

#### 4.1 更新 tasks.md

**位置**: `openspec/changes/add-streamlined-time-selector-visualization/tasks.md`

**更新内容**:
```markdown
- [x] Phase 1: 核心时间轴可视化 (VSS) ✅ 完成
- [x] Phase 1.5: TEC 车型限制集成 ✅ 完成
- [x] Phase 4: 手动测试问题修复 ✅ 完成
- [x] DHS 时间轴验证 (新) ✅ 需完成
- [x] TEC 流量时间轴实现 (新) ✅ 需完成
- [x] E2E 测试完善 (新) ✅ 需完成
```

#### 4.2 创建完成总结文档

**文件**: `FINAL_COMPLETION_REPORT.md`

内容包括:
- 功能完整性清单
- 测试覆盖率统计
- 性能指标 (如加载时间)
- 已知限制或 TODO

---

## 按优先级排序的任务列表

### 🔴 P0 - 立即执行
1. **任务1**: DHS 时间轴验证
   - 预计: 1-2 小时
   - 关键路径: 必须完成
   - 风险: 中等

2. **任务3.1**: E2E 测试选择器更新
   - 预计: 30 分钟
   - 关键路径: 提高测试稳定性
   - 风险: 低

### 🟡 P1 - 本周完成
3. **任务2**: TEC 流量时间轴实现
   - 预计: 1-2 小时
   - 关键路径: 功能完整性
   - 风险: 低

4. **任务3.2-3.3**: E2E 测试完善 + 运行
   - 预计: 2-3 小时
   - 关键路径: 验证所有功能
   - 风险: 中等

### 🟢 P2 - 本月完成
5. **任务4**: 文档更新
   - 预计: 1-2 小时
   - 关键路径: 项目维护
   - 风险: 低

---

## 技术详情与代码引用

### timeline_visualizer.js 的完整改动

**文件**: `frontend/control/js/timeline_visualizer.js`

**改动1: 添加 flow 颜色映射** (Line ~95)
```javascript
// 在 getColorForValue() 函数中添加
else if (type === 'flow') {
  const vph = parseFloat(value);
  if (isNaN(vph)) return '#9ca3af';
  if (vph >= 400) return '#ef4444';  // Red: severe
  if (vph >= 200) return '#f97316';  // Orange: medium
  return '#22c55e';                  // Green: low
}
```

**改动2: 添加 flow 标签** (Line ~116)
```javascript
// 在 getSlotLabel() 函数中添加
case 'flow':
  const vph = slot.vehsPerHour || slot.value;
  return `${vph} vph (${slot.begin_hours}:00-${slot.end_hours}:00)`;
```

### parameter_form.js 的检查项

**检查**: renderFlowIntervalControl() 的时间轴集成 (Line ~1000+)

```javascript
// 确认存在以下逻辑:
const updateFlowTimelineFromTable = function(tbody) {
  // 收集 flow_intervals 数据
  // 调用 TimelineVisualizer.renderTimeline(intervals, {type: 'flow'})
  // 添加防抖 (debouncedUpdateFlowTimelineFromTable)
}
```

---

## 质量保证清单

在标记任务为"完成"之前，请检查:

### 代码质量
- [ ] 遵循 JavaScript 风格指南 (camelCase, 最大30行函数)
- [ ] 添加 JSDoc 注释
- [ ] 无控制台错误 (使用 console.warn 表示警告)
- [ ] 单元测试覆盖主要逻辑

### 测试覆盖
- [ ] 所有新增代码都有对应的 E2E 测试
- [ ] 所有现有测试仍通过
- [ ] 手动测试验证 UI 表现

### 文档完整性
- [ ] README 中添加新功能说明
- [ ] 代码注释清晰
- [ ] 已知限制已文档化

### 兼容性
- [ ] 浏览器兼容性 (Chromium, Firefox, Safari)
- [ ] 响应式设计 (移动端)
- [ ] 无性能回归

---

## 风险评估与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|-----|------|------|--------|
| DHS 时间轴颜色不正确 | 中 | 中 | 早期手动测试验证 |
| TEC 流量数据结构不匹配 | 低 | 高 | 代码审查 + E2E 测试 |
| E2E 测试选择器仍不稳定 | 低 | 中 | 使用 name 属性 + CSS等待 |
| 性能下降 | 低 | 高 | 防抖 (已实现) + 性能监测 |

---

## 成功标志

此 OpenSpec 变更将在以下条件满足时视为完成:

1. ✅ **代码质量**
   - 无 lint 错误
   - 遵循项目代码风格
   - 有适当的注释

2. ✅ **功能完整**
   - VSS 时间轴: 100% 完成 + 已测试
   - DHS 时间轴: 100% 验证
   - TEC 时间轴: 100% 实现 (tec_interval_array + flow_interval_array)

3. ✅ **测试通过**
   - 所有 E2E 测试通过 (包括新增测试)
   - 所有现有功能回归测试通过
   - 手动测试验证无问题

4. ✅ **文档完整**
   - 任务清单更新
   - 完成总结文档
   - README 更新

5. ✅ **OpenSpec 验证**
   ```bash
   openspec validate add-streamlined-time-selector-visualization --strict
   # → ✅ 通过
   ```

6. ✅ **准备合并**
   ```bash
   openspec apply add-streamlined-time-selector-visualization
   # → 所有文件正确提交
   # → 提交消息包含实现摘要
   ```

---

## 后续工作 (Future Enhancements)

如果还有时间或资源，可考虑以下增强:

- [ ] DHS/TEC 车型表格样式改进 (徽章样式)
- [ ] 时间轴的交互功能 (点击高亮, 拖拽边界)
- [ ] 时间轴导出为图片功能
- [ ] 性能进一步优化 (虚拟化长表格)

---

**报告完成时间**: 2025-10-31
**下一步**: 开始任务1 (DHS 时间轴验证)
