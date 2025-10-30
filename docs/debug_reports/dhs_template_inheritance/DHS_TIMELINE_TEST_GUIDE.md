# DHS 时间轴可视化功能测试指南

**功能**: 应急车道开放（DHS）策略模板参数配置页面的时间轴可视化
**实施日期**: 2025-10-30
**状态**: ✅ 代码已实现，待测试验证

---

## 📋 实施概述

### 已完成的工作

1. **✅ 添加 DHS 参数渲染函数** ([parameter_form.js:670-843](../frontend/control/js/parameter_form.js#L670-L843))
   - `renderDHSIntervalControl()` - 主渲染函数
   - `addDHSIntervalRow()` - 添加区间行
   - `updateDHSTimelineFromTable()` - 更新时间轴
   - `debouncedUpdateDHSTimelineFromTable()` - 防抖更新

2. **✅ 添加 DHS 参数类型路由** ([parameter_form.js:233-235](../frontend/control/js/parameter_form.js#L233-L235))
   ```javascript
   case "dhs_interval_array":
     control = renderDHSIntervalControl(paramName, paramSchema);
     break;
   ```

3. **✅ 修复参数提取逻辑** ([templates.html:2971-2995](../frontend/control/templates.html#L2971-L2995))
   - 更新选择器匹配新的 CSS 类名
   - `.dhs-intervals-tbody` 和 `.dhs-interval-row`
   - 正确提取 `begin_hours`, `end_hours`, `status`, `allowed_vehicle_types`

4. **✅ 时间轴可视化集成** ([timeline_visualizer.js](../frontend/control/js/timeline_visualizer.js))
   - DHS 色彩编码：OPEN（绿色）、CLOSED（红色）
   - 标签显示："开启" / "关闭"
   - 支持区间数组（`begin_hours`, `end_hours`, `status`）

---

## 🚀 如何测试

### 前置条件

1. **激活 conda 环境**（必须）:
   ```bash
   conda activate od_project
   ```

2. **启动 API 服务器**:
   ```bash
   # Windows PowerShell
   .\start_api.ps1

   # 或者 Batch
   .\start_api.bat

   # 或者直接 Python（确保已激活 od_project）
   python api\main.py
   ```

3. **访问管控前端**:
   ```
   http://localhost:8000/control/templates.html
   ```

---

## 📝 测试步骤

### 测试 1: DHS 模板加载和时间轴渲染

**目标**: 验证 DHS 模板能正确加载，并显示时间轴可视化

**步骤**:
1. 打开管控策略页面：`http://localhost:8000/control/templates.html`
2. 在左侧导航栏点击"策略管理"
3. 点击"步骤1: 选择模板"
4. 找到并选择 **"应急车道开放"** 模板（`dhs_peak_hours`）
5. 点击"下一步"

**预期结果**:
- ✅ 进入步骤2（路段选择页面）
- ✅ 页面无 JavaScript 错误
- ✅ 模板加载成功

---

### 测试 2: 路段选择和参数配置页面

**目标**: 验证路段选择流程正常，参数配置页面能显示时间轴

**步骤**:
1. 在步骤2中，选择路线（如 G4202）
2. ⏳ 等待 ~7 秒，让路段代码刷新
3. 选择路段
4. 点击"查询路段"按钮
5. 点击"全选"复选框选择路段
6. 点击"下一步"进入参数配置页面（步骤3）

**预期结果**:
- ✅ 参数配置页面正确加载
- ✅ 看到"intervals"参数（DHS 区间配置）
- ✅ **时间轴可视化显示在表格上方** ⭐
- ✅ 时间轴显示默认的 5 个区间：
  - 0-7 小时: 红色（CLOSED）
  - 7-9 小时: 绿色（OPEN）
  - 9-17 小时: 红色（CLOSED）
  - 17-19 小时: 绿色（OPEN）
  - 19-24 小时: 红色（CLOSED）

---

### 测试 3: 时间轴基础渲染

**目标**: 验证时间轴的视觉元素正确显示

**检查项**:
- [ ] **时间轴容器**: 白色背景，灰色边框，8px 圆角
- [ ] **24 小时标记**: 显示 0, 1, 2, ..., 24 小时标记（至少 20 个）
- [ ] **时间槽**:
  - [ ] OPEN 区间：**绿色** (`#22c55e` 或 `rgb(34, 197, 94)`）
  - [ ] CLOSED 区间：**红色** (`#ef4444` 或 `rgb(239, 68, 68)`）
- [ ] **标签文本**:
  - [ ] OPEN 区间显示："开启"
  - [ ] CLOSED 区间显示："关闭"
- [ ] **时间槽宽度**: 与表格中的时间区间匹配
  - 7-9 小时（2小时）: 宽度约 8.33%（2/24）
  - 17-19 小时（2小时）: 宽度约 8.33%

**如何检查颜色**:
1. 打开浏览器开发者工具（F12）
2. 使用"检查元素"工具
3. 悬停在时间槽上
4. 在 Styles 面板中查看 `background-color` 属性

---

### 测试 4: 实时同步（表格 → 时间轴）

**目标**: 验证修改表格值时，时间轴自动更新

**步骤**:
1. 在参数配置页面，找到 DHS intervals 表格
2. 修改第2行（7-9 OPEN）的结束时间：从 `9` 改为 `10`
3. 点击表格外部或按 Tab 键让输入框失去焦点
4. ⏳ 等待 300ms（防抖延迟）
5. 观察时间轴变化

**预期结果**:
- ✅ 时间轴第2个槽（绿色 OPEN）宽度增加
- ✅ 新宽度反映 7-10 小时（3小时），约 12.5%（3/24）
- ✅ 第3个槽（红色 CLOSED）起始位置从 9 小时移动到 10 小时
- ✅ 过渡动画平滑（无闪烁）

**进一步测试**:
1. 修改状态：将第2行的状态从 "开放 (OPEN)" 改为 "关闭 (CLOSED)"
2. 观察时间轴变化

**预期结果**:
- ✅ 第2个槽颜色从绿色变为红色
- ✅ 标签文本从"开启"变为"关闭"

---

### 测试 5: 添加/删除区间

**目标**: 验证添加和删除区间时，时间轴正确更新

**步骤 - 添加区间**:
1. 点击表格下方的"+ 添加时间区间"按钮
2. 新行出现，默认值：begin=0, end=1, status=CLOSED
3. 观察时间轴

**预期结果**:
- ✅ 时间轴添加新的时间槽（红色，0-1 小时）
- ✅ 新槽可能与第1个槽（0-7）重叠（这是预期行为，验证覆盖完整24小时的验证在后端）

**步骤 - 删除区间**:
1. 点击某一行的"删除"按钮
2. 观察时间轴

**预期结果**:
- ✅ 对应的时间槽从时间轴中消失
- ✅ 其他槽保持不变

---

### 测试 6: 控制台无错误

**目标**: 验证整个流程无 JavaScript 错误

**步骤**:
1. 打开浏览器开发者工具（F12）
2. 切换到 Console 标签
3. 执行测试 1-5 的所有步骤
4. 检查控制台输出

**预期结果**:
- ✅ 无红色错误消息
- ✅ 可以看到信息日志（蓝色/黑色），如：
  ```
  [timeline_visualizer] Rendering timeline for intervals with 5 intervals
  [updateDHSTimelineFromTable] Updating timeline with 5 intervals
  ```
- ✅ 无 "Uncaught TypeError" 或 "Cannot read property" 错误

---

### 测试 7: 创建策略实例

**目标**: 验证参数提取逻辑正确，能成功创建 DHS 策略实例

**步骤**:
1. 在参数配置页面，配置所有必填参数：
   - `affected_edges`: 选择路段（应该在步骤2已选择）
   - `intervals`: 使用默认的 5 个区间（或自定义）
   - `allowed_vehicle_types`: 选择车辆类型（可选）
2. 填写策略名称：`测试DHS时间轴_G4202`
3. 填写策略描述（可选）
4. 点击"生成策略实例"按钮

**预期结果**:
- ✅ 策略创建成功
- ✅ 弹出成功提示消息
- ✅ 在"已创建的策略实例"列表中看到新策略
- ✅ 策略类型显示为"应急车道开放"（绿色标签）
- ✅ 控制台日志显示正确的参数结构：
  ```javascript
  {
    "strategy_id": "...",
    "configured_params": {
      "affected_edges": [...],
      "intervals": [
        {"begin_hours": 0, "end_hours": 7, "status": "CLOSED", "allowed_vehicle_types": ["emergency", "authority"]},
        {"begin_hours": 7, "end_hours": 9, "status": "OPEN", "allowed_vehicle_types": ["passenger", "bus", "truck", "emergency"]},
        ...
      ]
    }
  }
  ```

---

### 测试 8: 可选参数处理

**目标**: 验证可选参数未填写时，策略仍能成功创建

**步骤**:
1. 选择 DHS 模板
2. 选择路段
3. 在参数配置页面：
   - **删除所有区间行**（点击每一行的"删除"按钮）
   - 注意：`intervals` 参数是 `required: true`，所以至少需要1个区间
   - 如果模板中有可选参数（如 `allowed_vehicle_types`），留空
4. 尝试创建策略

**预期结果（intervals 为必填）**:
- ❌ 如果删除所有区间，策略创建应该失败（前端或后端验证）
- ✅ 错误消息清晰："intervals 参数为必填项"

**预期结果（可选参数）**:
- ✅ 未填写的可选参数不会阻止策略创建
- ✅ 控制台日志：`Skipping optional parameter with empty value: allowed_vehicle_types`

---

## 🎨 视觉效果检查清单

### 时间轴容器样式
- [ ] 背景颜色：白色 (`#ffffff` 或 `rgb(255, 255, 255)`)
- [ ] 边框：1px 实线灰色 (`#e5e7eb` 或 `rgb(229, 231, 235)`)
- [ ] 圆角：8px
- [ ] 内边距：16px
- [ ] 外边距底部：16px

### 小时标记
- [ ] 字体大小：12px
- [ ] 颜色：灰色 (`#6b7280`)
- [ ] 位置：时间轴上方，均匀分布

### 时间槽
- [ ] OPEN 槽：绿色背景 (`#22c55e`)，70% 不透明度
- [ ] CLOSED 槽：红色背景 (`#ef4444`)，70% 不透明度
- [ ] 标签文本：白色，12px，居中对齐
- [ ] 边框：半透明白色 1px
- [ ] 圆角：4px
- [ ] 悬停效果：不透明度增加到 85%

### 使用提示
- [ ] 文本："使用表格编辑器配置应急车道开放/关闭区间。时间单位：小时。注意：必须覆盖完整24小时，不能有时间重叠或间隙。"
- [ ] 字体大小：12px
- [ ] 颜色：灰色 (`#6b7280`)
- [ ] 背景：浅灰色 (`#f9fafb`)

---

## 🐛 常见问题排查

### 问题 1: 时间轴不显示

**可能原因**:
- Timeline Visualizer 模块未加载
- `window.TimelineVisualizer` 未定义

**排查步骤**:
1. 打开控制台（F12）
2. 输入：`window.TimelineVisualizer`
3. 检查输出：
   - 应该显示：`{renderTimeline: ƒ, updateTimeline: ƒ, utils: {...}}`
   - 如果显示 `undefined`，说明 `timeline_visualizer.js` 未加载

**解决方案**:
- 检查 `templates.html` 中是否包含：
  ```html
  <script src="/static/control/js/timeline_visualizer.js"></script>
  ```

---

### 问题 2: 时间轴颜色错误

**可能原因**:
- DHS_COLORS 常量未定义或值错误

**排查步骤**:
1. 控制台输入：`window.TimelineVisualizer.utils.getDHSColor('OPEN')`
2. 检查输出：应该显示 `"#22c55e"`（绿色）

**解决方案**:
- 检查 `timeline_visualizer.js` 中的 DHS_COLORS 定义：
  ```javascript
  const DHS_COLORS = {
    open: '#22c55e',   // 绿色
    closed: '#ef4444'  // 红色
  };
  ```

---

### 问题 3: 时间轴不更新

**可能原因**:
- 防抖函数未触发
- 选择器错误，找不到时间轴元素

**排查步骤**:
1. 修改表格值后，等待 300ms
2. 控制台输入：`document.querySelector('.parameter-timeline')`
3. 检查是否返回时间轴元素

**解决方案**:
- 确保表格 `tbody` 有 `data-parameter-name` 属性
- 确保时间轴元素在同一个 `.dhs-interval-control-enhanced` 容器内

---

### 问题 4: 策略创建失败

**可能原因**:
- 参数提取逻辑错误
- 选择器不匹配

**排查步骤**:
1. 打开控制台
2. 查找错误消息：`tbody not found for dhs_interval_array!`
3. 检查 `tbody` 元素的类名：
   ```javascript
   document.querySelector('.dhs-intervals-tbody')
   ```

**解决方案**:
- 确认 `templates.html` 中的选择器为：
  ```javascript
  const tbody = document.querySelector('.dhs-intervals-tbody[data-parameter-name="' + param.parameter_name + '"]');
  ```

---

## 📊 测试结果记录

| # | 测试项 | 状态 | 备注 |
|---|--------|------|------|
| 1 | DHS 模板加载 | ⏹️ 待测试 | |
| 2 | 路段选择流程 | ⏹️ 待测试 | |
| 3 | 时间轴基础渲染 | ⏹️ 待测试 | |
| 4 | 实时同步 | ⏹️ 待测试 | |
| 5 | 添加/删除区间 | ⏹️ 待测试 | |
| 6 | 控制台无错误 | ⏹️ 待测试 | |
| 7 | 创建策略实例 | ⏹️ 待测试 | |
| 8 | 可选参数处理 | ⏹️ 待测试 | |

**测试状态图例**:
- ⏹️ 待测试
- ✅ 通过
- ❌ 失败
- ⚠️ 部分通过

---

## 🔍 代码位置索引

### 前端文件

1. **parameter_form.js** ([frontend/control/js/parameter_form.js](../frontend/control/js/parameter_form.js))
   - Line 233-235: `dhs_interval_array` case 路由
   - Line 670-843: DHS 参数渲染函数
     - `renderDHSIntervalControl()` (670-760)
     - `addDHSIntervalRow()` (762-843)
     - `updateDHSTimelineFromTable()` (845-879)
     - `debouncedUpdateDHSTimelineFromTable()` (881-884)

2. **timeline_visualizer.js** ([frontend/control/js/timeline_visualizer.js](../frontend/control/js/timeline_visualizer.js))
   - Line 10-18: DHS_COLORS 常量定义
   - Line 64-66: `getDHSColor()` 函数
   - Line 89-90: DHS 类型颜色映射
   - Line 108-109: DHS 类型标签文本

3. **templates.html** ([frontend/control/templates.html](../frontend/control/templates.html))
   - Line 2971-2995: DHS 参数提取逻辑
   - Line 574-764: 时间轴 CSS 样式（共享）

### 模板文件

4. **dhs_base.json** ([templates/control_strategies/dynamic_hard_shoulder/dhs_base.json](../templates/control_strategies/dynamic_hard_shoulder/dhs_base.json))
   - Line 31-83: `intervals` 参数定义（`dhs_interval_array` 类型）

5. **dhs_peak_hours.json** ([templates/control_strategies/dynamic_hard_shoulder/dhs_peak_hours.json](../templates/control_strategies/dynamic_hard_shoulder/dhs_peak_hours.json))
   - Line 2-4: DHS 模板基本信息
   - Line 5: 继承自 `dhs_base`

---

## 📸 预期截图

### 1. 参数配置页面（含时间轴）

```
┌─────────────────────────────────────────────────────────────┐
│ 步骤3：配置策略参数                                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ intervals (应急车道开放/关闭时间区间列表)                     │
│                                                               │
│ ╔═══════════════════════════════════════════════════════════╗ │
│ ║ Timeline (24 hours)                                       ║ │
│ ║ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 ║
│ ║ [────────CLOSED─────][OP][────CLOSED────────][OP][──CLOSED─] ║ │
│ ║   红色 0-7           绿色  红色 9-17         绿色 红色19-24  ║ │
│ ╚═══════════════════════════════════════════════════════════╝ │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 开始时间 │ 结束时间 │ 状态           │ 允许车型        │ 操作 │
│ ├─────────┼─────────┼──────────────┼─────────────┼─────┤ │
│ │ 0       │ 7       │ 关闭 (CLOSED) │ emergency   │ 删除│ │
│ │ 7       │ 9       │ 开放 (OPEN)   │ passenger,bus│删除│ │
│ │ 9       │ 17      │ 关闭 (CLOSED) │ emergency   │ 删除│ │
│ │ 17      │ 19      │ 开放 (OPEN)   │ passenger,bus│删除│ │
│ │ 19      │ 24      │ 关闭 (CLOSED) │ emergency   │ 删除│ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ [+ 添加时间区间]                                              │
│                                                               │
│ 💡 使用表格编辑器配置应急车道开放/关闭区间。时间单位：小时。  │
│    注意：必须覆盖完整24小时，不能有时间重叠或间隙。           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2. 时间轴色彩示例

**OPEN 区间（绿色）**:
```
Background: #22c55e (rgb(34, 197, 94))
Label: "开启"
Opacity: 0.7
```

**CLOSED 区间（红色）**:
```
Background: #ef4444 (rgb(239, 68, 68))
Label: "关闭"
Opacity: 0.7
```

---

## 📝 测试完成后的操作

### 如果测试通过 ✅

1. **更新任务清单**:
   - 在任务清单中标记"测试 DHS 时间轴可视化功能"为完成

2. **创建测试报告**:
   - 记录所有测试结果
   - 截图保存关键界面
   - 记录任何发现的问题

3. **更新 OpenSpec 文档**:
   - 更新 `proposal.md` 状态为"P1 DHS 功能完成"
   - 更新 `tasks.md` 标记 DHS 相关任务为完成

4. **（可选）创建 Playwright 测试**:
   - 参考 VSS 的测试：`tests/e2e/test_timeline_visualization.spec.js`
   - 创建 DHS 专用测试：`tests/e2e/test_dhs_timeline_visualization.spec.js`

### 如果测试失败 ❌

1. **记录错误信息**:
   - 控制台错误消息
   - 网络请求失败（如果有）
   - 截图保存错误界面

2. **分析问题原因**:
   - 参考"常见问题排查"部分
   - 检查相关代码位置

3. **修复并重新测试**:
   - 修改代码
   - 重启服务器
   - 重新执行测试步骤

---

## 🎯 后续步骤

完成 DHS 时间轴可视化测试后，可以考虑：

1. **TEC（收费站管控）时间轴可视化**
   - `flow_interval_array` 参数类型
   - 已有渲染函数 `renderFlowIntervalControl()`
   - 需要添加时间轴集成

2. **交互式功能**（P2）
   - 点击时间槽高亮对应表格行
   - 悬停显示详细信息
   - 拖拽调整区间边界

3. **跨浏览器测试**
   - Firefox
   - Edge
   - Safari

4. **性能优化**
   - 路段代码加载性能（减少 6-7 秒延迟）
   - 时间轴渲染性能（大量区间场景）

---

**文档生成日期**: 2025-10-30
**作者**: AI Assistant (Claude)
**相关 OpenSpec**: `add-streamlined-time-selector-visualization`
