# 参数配置系统 - 快速参考卡片

## 🎯 一页纸总结

### VSS 参数配置的关键函数链

```
generateParamsForm()
   ↓ (检测 step_array)
renderStepArrayControl()
   ├─ TimelineVisualizer.renderTimeline({type: 'speed'})
   │  └─ calculateStepSlots() ✅ VSS专用
   └─ addStepRow() × N
      └─ updateTimelineFromTable()
         └─ TimelineVisualizer.updateTimeline({type: 'speed'})
```

### 为什么时间轴正确？

1. **类型分支** → `{type: 'speed'}` 告诉可视化器用 VSS 算法
2. **算法选择** → `calculateStepSlots()` 计算相邻步骤间隔 ✅
3. **实时更新** → 防抖机制确保高效响应 ✅
4. **颜色映射** → 速度值→RGB 颜色 ✅

---

## 📍 文件位置速查表

| 功能 | 文件 | 行号 | 关键代码 |
|------|------|------|--------|
| **表单生成** | templates.html | 1439 | `generateParamsForm(template)` |
| **参数类型检测** | templates.html | 1554 | `if (param.parameter_type === 'step_array')` |
| **VSS 渲染** | parameter_form.js | 526 | `renderStepArrayControl()` |
| **时间轴初始化** | parameter_form.js | 544 | `TimelineVisualizer.renderTimeline()` |
| **行编辑** | parameter_form.js | 621 | `addStepRow()` |
| **实时更新** | parameter_form.js | 39 | `updateTimelineFromTable()` |
| **时间轴渲染** | timeline_visualizer.js | 223 | `renderTimeline()` |
| **时间槽计算** | timeline_visualizer.js | 179 | `calculateStepSlots()` |
| **颜色映射** | timeline_visualizer.js | 52 | `getSpeedColor()` |
| **数据提交** | templates.html | 2941 | `createStrategy()` |

---

## 🔍 关键选择器速查

| 选择器 | 用途 | 定位方式 |
|--------|------|--------|
| `[data-parameter-name="speed_steps"] .steps-tbody` | 查找表格体（编辑时） | 由 renderStepArrayControl 创建 |
| `.step-row` | 选择所有步骤行 | tbody 的子元素 |
| `.step-time` | 时间输入框 | row 中的第一个 input |
| `.step-speed` | 速度输入框 | row 中的第二个 input |
| `.parameter-timeline` | 时间轴容器 | 由 TimelineVisualizer 创建 |

---

## ⚡ 快速排故指南

### 问题：时间轴不显示

**检查清单**:
1. 浏览器控制台 → 是否有 JS 错误？
2. `window.TimelineVisualizer` 是否存在？ (`timeline_visualizer.js` 是否加载？)
3. `defaultSteps` 数据是否为空？
4. `renderTimeline()` 返回的 DOM 是否被 append？

### 问题：编辑表格后时间轴不更新

**检查清单**:
1. input 事件是否触发？ (打开浏览器开发工具，监听 input 事件)
2. `debouncedUpdateTimelineFromTable()` 是否被调用？
3. 表格 tbody 的选择器是否正确？
4. 防抖延迟 (300ms) 是否过长？

### 问题：保存策略时数据为空

**检查清单**:
1. 表格行是否有 `step-row` class？
2. input 的 class 是否为 `step-time` 和 `step-speed`？
3. tbody 的 class 是否为 `steps-tbody`？
4. 控制台中 `console.log()` 输出是否显示提取的数据？

---

## 🧪 测试验证步骤

### 1. 验证时间轴渲染

```javascript
// 在浏览器控制台执行
const container = document.querySelector('[data-parameter-name="speed_steps"]');
const timeline = container.querySelector('.parameter-timeline');
console.log(timeline);  // 应该输出 DOM 元素，不是 null
```

### 2. 验证数据提取

```javascript
// 编辑表格后，执行
const tbody = document.querySelector('[data-parameter-name="speed_steps"] .steps-tbody');
const rows = tbody.querySelectorAll('.step-row');
rows.forEach(row => {
  const time = row.querySelector('.step-time').value;
  const speed = row.querySelector('.step-speed').value;
  console.log({time, speed});
});
```

### 3. 验证实时更新

```javascript
// 在表格输入框中输入数据，观察
// 1. 控制台是否有 updateTimelineFromTable 日志？
// 2. 时间轴是否立即更新？(注意防抖延迟 300ms)
```

### 4. 验证提交数据

```javascript
// 打开浏览器网络标签，点击"生成策略实例"
// 检查 POST /api/v1/control/strategies/create 的请求体
// speed_steps 字段是否包含编辑后的数据？
```

---

## 💾 核心数据结构

### 模板定义 (vss_moderate.json)

```json
{
  "parameter_name": "speed_steps",
  "parameter_type": "step_array",
  "default_value": [
    {"time_hours": 7, "speed_kmh": 100},
    {"time_hours": 9, "speed_kmh": 80},
    {"time_hours": 17, "speed_kmh": 100},
    {"time_hours": 19, "speed_kmh": 80}
  ]
}
```

### 表格行结构（addStepRow 创建）

```html
<tr class="step-row">
  <td>
    <input type="number" class="step-time" value="7" min="0" max="24">
  </td>
  <td>
    <input type="number" class="step-speed" value="100" min="30" max="130">
  </td>
  <td>
    <button type="button" class="btn-remove-step">Remove</button>
  </td>
</tr>
```

### API 提交格式（createStrategy 构造）

```json
{
  "strategy_name": "用户输入",
  "speed_steps": [
    {"time_hours": 7, "speed_kmh": 100},
    {"time_hours": 9, "speed_kmh": 80},
    ...
  ]
}
```

### 时间轴数据流

```javascript
// 输入 (模板 default_value)
[{time_hours: 7, speed_kmh: 100}, ...]

// 计算 (calculateStepSlots)
[{start: 7, width: 2, speed_kmh: 100}, ...]

// 渲染 (DOM)
<div class="parameter-timeline">
  <div class="timeline-slots">
    <div style="left: 29.16%; width: 8.33%; background: #10b981;"></div>
    ...
  </div>
</div>
```

---

## 🎨 样式类名速查

| Class 名 | 用途 | 定义位置 |
|---------|------|--------|
| `step-array-control-enhanced` | 容器 | renderStepArrayControl |
| `timeline-description` | 时间轴说明文字 | renderStepArrayControl |
| `parameter-timeline` | 时间轴容器 | TimelineVisualizer.renderTimeline |
| `timeline-hours` | 小时标记行 | TimelineVisualizer.renderTimeline |
| `timeline-slots` | 时间槽容器 | TimelineVisualizer.renderTimeline |
| `steps-table` | 编辑表格 | renderStepArrayControl |
| `steps-tbody` | 表格体 | renderStepArrayControl |
| `step-row` | 表格行 | addStepRow |
| `step-time` | 时间输入 | addStepRow |
| `step-speed` | 速度输入 | addStepRow |
| `step-buttons` | 按钮容器 | renderStepArrayControl |
| `btn-add-step` | Add 按钮 | renderStepArrayControl |
| `btn-remove-step` | Remove 按钮 | addStepRow |

---

## 🚫 冗余部分（可删除）

| 函数 | 文件 | 行号 | 原因 |
|------|------|------|------|
| `renderTimeIntervalArrayControl()` | parameter_form.js | 1459 | DHS 旧版本，已被 renderDHSIntervalControl 替代 |
| `addTimeIntervalRow()` | parameter_form.js | 1511 | 对应旧版本已过时 |

**删除影响**: ✅ 无（只要 renderDHSIntervalControl 被加载）

---

## 📚 相关文档导航

| 文档 | 用途 |
|------|------|
| `VSS_PARAMETER_CONFIG_FLOW_ANALYSIS.md` | 详细的执行流程分析 |
| `PARAMETER_CONFIG_ACTIVE_VS_REDUNDANT.md` | 活跃部分 vs 冗余部分对比表 |
| `ACTIVE_CODE_FLOW_DIAGRAM.md` | 可视化流程图和调用关系 |
| `PARAMETER_CONFIG_VERIFICATION_SUMMARY.md` | 完整验证总结 |

---

## ❓ 常见问题快速解答

**Q: 时间轴用的是什么算法？**
A: `calculateStepSlots()` - 相邻步骤间的时间间隔作为当前步骤的持续时间

**Q: VSS 和 DHS 的时间轴有什么区别？**
A:
- VSS: 使用 `time_hours` 字段，自动计算间隔
- DHS: 使用 `begin_hours` 和 `end_hours` 字段，明确指定时间范围

**Q: 防抖延迟 300ms 是否太长？**
A:
- 优点: 避免频繁重新计算
- 缺点: 编辑时略有延迟
- 可调整: 在 `debounce(updateTimelineFromTable, 300)` 处修改

**Q: 为什么有两个 DHS 渲染函数？**
A: 故障转移设计，但实际不需要（新版本总是定义），可删除旧版本

**Q: 如何添加新的参数类型？**
A:
1. 在 `generateParamsForm()` 中添加 if 分支检测
2. 创建对应的 `renderXxxControl()` 函数
3. 如需时间轴，在 `TimelineVisualizer.renderTimeline()` 中添加类型支持

---

## 🔗 关键的调用约定

### renderStepArrayControl 的约定

**输入**:
```javascript
renderStepArrayControl(paramName, schema)
// paramName: "speed_steps"
// schema: { parameter_name, parameter_type, default_value, step_structure }
```

**输出**:
```javascript
// 返回一个 <div class="step-array-control-enhanced"> 元素
// 内部结构:
// - .timeline-description (说明文字)
// - .parameter-timeline (时间轴容器)
// - .steps-table
//   - thead (表头)
//   - .steps-tbody (表格体)
// - .step-buttons (按钮行)
```

### updateTimelineFromTable 的约定

**输入**:
```javascript
updateTimelineFromTable(tbody)
// tbody: 包含 .step-row 行的表格体元素
```

**操作**:
1. 查询最近的 `.step-array-control-enhanced` 容器
2. 查询其内的 `.parameter-timeline` 元素
3. 从所有 `.step-row` 提取数据
4. 调用 `TimelineVisualizer.updateTimeline()`

### createStrategy 对 step_array 的约定

**查询**:
```javascript
document.querySelector(`[data-parameter-name="speed_steps"] .steps-tbody`)
```

**期望结构**:
```html
<div data-parameter-name="speed_steps">
  <table>
    <tbody class="steps-tbody">
      <tr class="step-row">
        <td><input class="step-time" ...></td>
        <td><input class="step-speed" ...></td>
      </tr>
    </tbody>
  </table>
</div>
```

---

## ✅ 验证清单

在修改相关代码前，运行此清单确保功能正常：

- [ ] VSS 参数配置页面加载正常
- [ ] 时间轴显示 4 个默认速度步骤
- [ ] 编辑速度值，时间轴颜色立即改变
- [ ] 编辑时间值，时间轴宽度立即改变
- [ ] Add Step 按钮能添加新行
- [ ] Remove 按钮能删除行
- [ ] 填写策略名称后点"生成策略实例"成功
- [ ] API 请求中 `speed_steps` 包含正确的数据

