# 实施任务清单：策略参数配置前端重构

## 阶段 1：准备与设计 (4h) ✅

- [x] **Task 1.1**: 创建 E2E 测试基线
  - 运行现有策略创建测试，记录当前行为
  - 截图当前 UI 状态（VSS、TEC、DHS）
  - 验证：所有现有测试通过
  - 文件：`tests/e2e/baseline_strategy_creation.md`

- [x] **Task 1.2**: CSS 变量扩展
  - 在 `frontend/control/css/variables.css` 添加表单相关变量
  - 定义：`--form-spacing-*`, `--input-width-*`, `--button-min-width`
  - 验证：无语法错误，其他页面不受影响
  - 文件：`frontend/control/css/variables.css`

- [x] **Task 1.3**: 文档化当前数据流
  - 记录 Step 2 → Step 3 的数据传递方式
  - 记录当前参数提取逻辑 (`extractFormParameters`)
  - 验证：文档准确反映代码
  - 文件：`docs/frontend_analysis/parameter_form_data_flow.md`

## 阶段 2：代码重构（无功能变更） (12h) ✅

- [x] **Task 2.1**: 合并时间轴更新函数
  - 创建 `updateTimeline(tbody, config)` 统一函数（参数化配置）
  - 创建 `TIMELINE_CONFIGS` 预设配置对象（vss, dhs, tec_simple）
  - 创建 `updateTimelineByType(tbody, type)` 简化调用函数
  - 删除 4 个旧函数：`updateTimelineFromTable`, `updateDHSTimelineFromTable`, `updateFlowTimelineFromTable`, `updateTECTimelineFromTable`
  - 替换所有旧函数调用点为 `updateTimelineByType(tbody, 'vss'|'dhs'|'tec_simple')`
  - 运行 E2E 测试验证 VSS、DHS、TEC 时间轴更新正常
  - 验证：时间轴更新功能无回归，保持 `TimelineVisualizer.updateTimeline()` 不变
  - 参考：`TIMELINE_CLARIFICATION.md` 中的合并方案
  - 文件：`frontend/control/js/parameter_form.js:39-95`

- [x] **Task 2.2**: 合并行添加函数
  - 创建 `addRow(tbody, config)` 统一函数
  - 创建辅助函数 `getColumnsForRowType()`, `createCell()`
  - 替换 `addDHSIntervalRow`, `addFlowIntervalRow`, `addTECIntervalRow`
  - 运行 E2E 测试验证
  - 验证：表格行添加功能无回归
  - 文件：`frontend/control/js/parameter_form.js:834-1400`

- [x] **Task 2.3**: 提取验证函数
  - 创建 `validators` 对象（`timeOrder`, `timeRange`, `speedRange`）
  - 创建 `showError(input, message)` 和 `clearError(input)`
  - 替换分散的验证逻辑
  - 验证：验证逻辑功能一致
  - 文件：`frontend/control/js/parameter_form.js` 顶部新增区域

- [x] **Task 2.4**: 代码分区注释
  - 添加明确的区域注释（工具、加载、渲染等）
  - 调整函数顺序按区域分组
  - 更新函数 JSDoc 注释
  - 验证：代码可读性提升，无语法错误
  - 文件：`frontend/control/js/parameter_form.js`

## 阶段 3：UI 布局改进 (8h) ✅

- [x] **Task 3.1**: 修复策略名称/描述布局
  - 在 `templates-forms.css` 添加 `.flex-start` 样式规则
  - 设置按钮 `flex-shrink: 0` 和 `min-width`
  - 添加响应式规则（768px 断点）
  - 验证：桌面和移动端布局正常
  - 文件：`frontend/control/css/templates-forms.css`

- [x] **Task 3.2**: 统一参数表单间距
  - 为所有 `.form-group` 使用统一的 `margin-bottom`
  - 为表格添加统一的 `margin-top` 和 `padding`
  - 调整时间轴与表格的间距（margin 从 10px 增加到 15px）
  - 验证：VSS、TEC、DHS 间距一致
  - 文件：`frontend/control/css/templates-forms.css`

- [x] **Task 3.3**: 添加响应式设计
  - 为窄屏（<768px）添加媒体查询
  - 按钮容器改为垂直布局（.flex-start 使用 flex-direction: column）
  - 表格横向滚动
  - 验证：移动设备模拟测试通过
  - 文件：`frontend/control/css/templates-forms.css`

- [x] **Task 3.4**: 修复表格列宽
  - 为时间列、速度列、操作列设定固定宽度
  - 使用 `table-layout: fixed` 确保列宽一致
  - 验证：所有策略类型表格列宽一致
  - 文件：`frontend/control/css/templates-forms.css`

## 阶段 4：模板默认值加载 (6h) ✅ (已存在实现)

- [x] **Task 4.1**: 创建 `initializeDefaultValues()` 函数
  - 实现基础类型初始化（number, string, enum）
  - 实现数组类型初始化（step_array, interval_array）
  - 添加错误处理和日志
  - 验证：已验证现有实现中各参数渲染函数已正确读取 `schema.default_value`
  - 文件：`frontend/control/js/parameter_form.js`

- [x] **Task 4.2**: 集成到 `generateFormFromTemplate()`
  - 在表单生成后调用 `initializeDefaultValues()`
  - 传递 `param.default_value` 和 `param.parameter_type`
  - 处理 `default_value` 为 null 的情况（已有 fallback 示例数据）
  - 验证：表单打开时显示初始数据（已验证各 render 函数正确加载）
  - 文件：`frontend/control/js/parameter_form.js:105-184`

- [x] **Task 4.3**: 修复参数约束显示
  - 确保必填字段显示红色 `*`
  - 在 Hint 中显示范围和单位
  - 从 `schema.constraints` 动态生成提示
  - 验证：所有约束信息正确显示（现有实现已处理）
  - 文件：`frontend/control/js/parameter_form.js:766-850`

## 阶段 5：时间语义明确化 (4h) ✅

- [x] **Task 5.1**: 更新 VSS 表格列标签
  - 列标签改为：`时间(小时)` | `限速(km/h)` | `操作`
  - 添加 Hint：`时刻表示：例如 7 表示从 7:00 开始执行该限速，直到下一个时刻点`
  - 验证：UI 标签清晰
  - 文件：`frontend/control/js/parameter_form.js:806-814, 775-779`

- [x] **Task 5.2**: 更新 TEC/DHS/Flow 表格说明文字
  - DHS 描述：`时段表示：例如 7-9 表示 7:00-9:00 硬路肩开放（必须覆盖完整24小时）`
  - TEC 描述：`时段表示：例如 7-9 表示 7:00-9:00 执行车型限制/入口控制`
  - Flow 描述：`时段表示：例如 7-9 表示 7:00-9:00 执行流量控制，限制流量和目标速度`
  - 验证：UI 标签清晰
  - 文件：`frontend/control/js/parameter_form.js:1189-1193, 1639-1643, 1430-1434`

- [x] **Task 5.3**: 调整时间轴可视化
  - VSS 使用段状可视化（`type: 'speed'`）- 保持现有设计
  - DHS 使用段状着色（`type: 'dhs'`）- 已实现
  - TEC 使用简单区间（`type: 'simple_interval'`）- 已实现
  - Flow 使用流量可视化（`type: 'flow'`）- 已实现
  - 验证：时间轴视觉符合语义
  - 文件：已验证现有 TimelineVisualizer 调用正确

## 阶段 6：Phase 5 修复 - Step 3 显示和自动生成 (6h) ✅

**背景**：Phase 5 完成后，手动检查发现Step 3页面显示和自动生成功能不完整。本阶段修复这些问题。

- [x] **Task 6.0**: 在 Step 3 顶部添加已选模板信息展示区
  - 添加新的HTML容器 `step3-template-info` 用于显示已选模板
  - 创建 `showTemplateInfoStep3(template)` 函数
  - 在 `updateStepDisplay()` 中调用 `showTemplateInfoStep3()`
  - 验证：Step 3 顶部显示已选模板名称和类型
  - 文件：`frontend/control/templates.html:296-308, 595-596, 636-663`

- [x] **Task 6.1**: 绑定策略名称自动生成按钮事件
  - 在 `generateParamsForm()` 中绑定"建议名称"按钮 click 事件
  - 委托给已有的 `autoPopulateStrategyName()` 函数（在 initializeEdgeDisplay 中调用）
  - 验证：按钮点击后调用 autoPopulateStrategyName()
  - 文件：`frontend/control/templates.html:956-968`
  - **说明**：策略名称自动填充由 initializeEdgeDisplay() 中的 autoPopulateStrategyName() 负责（500ms 延迟，此时有完整的 Edge 对象）

- [x] **Task 6.2**: 绑定策略描述自动生成按钮事件
  - 在 `generateParamsForm()` 中绑定"重新生成描述"按钮 click 事件
  - 委托给已有的 `autoPopulateStrategyDescription()` 函数（在 initializeEdgeDisplay 中调用）
  - 验证：按钮点击后调用 autoPopulateStrategyDescription()
  - 文件：`frontend/control/templates.html:970-982`
  - **说明**：策略描述自动填充由 initializeEdgeDisplay() 中的 autoPopulateStrategyDescription() 负责（500ms 延迟，此时有完整的 Edge 对象）

- [x] **Task 6.3**: 确保车型配置区域正确渲染
  - 验证：车型多选框在表单中正确显示
  - 验证：根据 `allowed_vehicle_types` 或 `banned_vehicle_types` 参数动态显示
  - 验证：Hint 提示清晰
  - 文件：`frontend/control/templates.html:871-901`

- [x] **Task 6.4**: 运行 E2E 测试验证完整流程
  - 运行 Playwright 测试套件
  - 验证：VSS、DHS、TEC 所有策略类型都能正确加载和配置
  - 验证：参数表格正确渲染
  - 文件：`tests/e2e/test_strategy_creation_workflow.spec.js`

## 阶段 6b：车型配置分离 (6h) ✅

- [x] **Task 6b.1**: 从 DHS/TEC 表格移除车型列
  - 修改 `renderDHSIntervalControl()` 移除 `allowed_vehicle_types` 列（行 1231-1239）
  - 修改 `addDHSIntervalRow()` 移除车型参数和复选框代码（行 1327-1355）
  - 更新两处调用位置（行 1252, 1268）移除 `allowedVehicles` 参数
  - 添加 `dhs_interval_array` 提取逻辑（行 2415-2430）
  - 添加 `tec_interval_array` 提取逻辑（行 2442-2456）
  - 验证：✅ 表格中无车型列，E2E 测试全部通过
  - 文件：`frontend/control/js/parameter_form.js:1221-1370, 2415-2456`

- [x] **Task 6b.2**: 创建全局车型配置区域
  - 创建 `renderGlobalVehicleTypeControl(vehicleTypeParams, template)` 函数（行 2513-2607）
  - 支持动态车型参数识别（allowed/disallow/applicable）
  - 生成复选框网格布局（grid 自适应 120px 列宽）
  - 添加 CSS 样式 `.vehicle-type-config-global` 等（templates-forms.css:600-653）
  - 导出函数到 `window` 对象（行 2754）
  - 验证：✅ 车型配置区域独立显示，CSS 样式美观
  - 文件：`frontend/control/js/parameter_form.js:2513-2607, 2754` + `templates-forms.css:600-653`

- [x] **Task 6b.3**: 动态标签和提示
  - 检测 `allowed_vehicle_types` 或 `disallow_vehicle_types` 参数
  - 动态标签：`allowed_vehicle_types` → "允许的车型"、`disallow_vehicle_types` → "禁止的车型"
  - 动态 Hint：允许模式 → "仅选中的车型可使用此策略"、禁止模式 → "选中的车型禁止使用此策略"
  - 验证：✅ 标签和提示符合参数类型
  - 文件：`frontend/control/js/parameter_form.js:2538-2552`

- [x] **Task 6b.4**: 更新提交逻辑
  - 复选框使用 `enum-checkbox` 类（行 2583）
  - 现有 `extractFormParameters()` 逻辑自动提取 `.enum-checkbox:checked` 元素（行 2396-2399）
  - 验证：✅ 策略实例 JSON 正确，E2E 测试验证完整流程
  - 文件：`frontend/control/js/parameter_form.js:2396-2399, 2583`

## 阶段 7：路段来源统一 (4h) ✅

- [x] **Task 7.1**: 隐藏旧的 `affected_edges` 输入框
  - 已验证 `templates.html:796-798` 中已有跳过逻辑
  - 参数名称：`affected_edges`、`affected_segments`、`entrance_ids` 被跳过
  - 验证：✅ Step 3 不显示这些旧输入框
  - 文件：`frontend/control/templates.html:796-798`

- [x] **Task 7.2**: 显示 Step 2 路段只读列表
  - 创建 `renderSelectedEdgesSummary()` 函数（parameter_form.js:2754-2851）
  - 从 `sessionStorage` 获取 `strategy_selected_edges`
  - 生成只读表格，列：Edge ID、路线、路段代码、桩号、方向
  - 添加 CSS 样式 `.selected-edges-summary` 等（templates-forms.css:655-740）
  - 集成到 `generateParamsForm()` (templates.html:794-798)
  - 验证：✅ 路段列表正确显示
  - 文件：`frontend/control/js/parameter_form.js:2754-2851, 2861` + `frontend/control/templates.html:794-798` + `templates-forms.css:655-740`

- [x] **Task 7.3**: 添加"返回修改路段"按钮
  - 在路段列表下方添加"返回修改路段"按钮（templates.html:799-817）
  - 点击事件调用 `previousStep()` 返回 Step 2
  - 添加 CSS 样式 `.return-to-step2-button-container` 等（templates-forms.css:742-763）
  - 验证：✅ 按钮功能正常，E2E 测试全部通过
  - 文件：`frontend/control/templates.html:799-817` + `templates-forms.css:742-763`

## 阶段 8：验证和提示改进 (4h)

- [ ] **Task 8.1**: 实现时间顺序验证
  - 在 `endInput` blur 事件绑定 `validators.timeOrder`
  - 显示错误提示：`showError(input, message)`
  - 添加视觉错误状态（红色边框）
  - 验证：输入非法顺序时显示错误
  - 文件：`frontend/control/js/parameter_form.js`

- [ ] **Task 8.2**: 实现数值范围验证
  - 绑定 `validators.timeRange` 和 `validators.speedRange`
  - 从 schema 读取 min/max 值
  - 显示错误提示
  - 验证：范围外输入显示错误
  - 文件：`frontend/control/js/parameter_form.js`

- [ ] **Task 8.3**: 添加删除确认对话框
  - 在删除按钮 click 事件添加 `confirm()`
  - 提示：`确定要删除这一行吗？`
  - 用户取消时不删除
  - 验证：删除前有确认
  - 文件：`frontend/control/js/parameter_form.js`

- [ ] **Task 8.4**: 优化 Hint 文本
  - 分离参数级Hint（`generateParameterHint()`）
  - 分离控制级Hint（`controlHints` 对象）
  - 避免重复，使用 `·` 分隔
  - 验证：Hint 清晰、不重复
  - 文件：`frontend/control/js/parameter_form.js:658, 825, 1080`

## 阶段 9：测试与文档 (8h)

- [ ] **Task 9.1**: 更新 E2E 测试
  - 更新策略创建测试以匹配新UI
  - 添加验证测试（时间顺序、范围）
  - 添加车型配置测试
  - 验证：所有 E2E 测试通过
  - 文件：`tests/e2e/test_strategy_creation_workflow.spec.js`

- [ ] **Task 9.2**: 添加单元测试
  - 测试 `validators` 函数
  - 测试 `initializeDefaultValues()`
  - 测试 `updateTimeline()` 和 `addRow()`
  - 验证：代码覆盖率 >80%
  - 文件：`tests/unit/frontend/test_parameter_form.js` (新建)

- [ ] **Task 9.3**: 手动测试所有策略类型
  - 创建 VSS 策略（时刻）
  - 创建 TEC 策略（时段）
  - 创建 DHS 策略（时段）
  - 验证表单布局、默认值、车型、路段、时间轴
  - 文档：`docs/frontend_analysis/manual_test_checklist.md`

- [ ] **Task 9.4**: 更新前端重构进度文档
  - 在 `REFACTORING_PROGRESS.md` 标记已完成任务
  - 更新技术债务估算（应减少 ~200 行重复代码）
  - 记录下一步计划
  - 文件：`docs/frontend_analysis/REFACTORING_PROGRESS.md`

- [ ] **Task 9.5**: 编写用户文档
  - 更新策略创建指南
  - 说明时间语义（时刻 vs 时段）
  - 说明车型配置逻辑
  - 文件：`docs/user_guides/strategy_creation_guide.md`

## 阶段 10：验收与归档 (2h)

- [ ] **Task 10.1**: 性能测试
  - 测试大量路段（100+）加载性能
  - 测试表格操作响应时间
  - 验证：无明显性能退化
  - 文档：性能基准

- [ ] **Task 10.2**: 浏览器兼容性测试
  - 测试 Chrome、Edge、Firefox
  - 测试移动端 Safari（响应式）
  - 验证：所有浏览器正常
  - 文档：兼容性报告

- [ ] **Task 10.3**: 代码审查
  - 团队审查重构代码
  - 检查函数长度、复杂度
  - 确认符合 CLAUDE.md 标准
  - 验证：审查通过

- [ ] **Task 10.4**: 合并与部署
  - 创建 PR：`refactor: 策略参数配置前端重构`
  - 运行 CI/CD 流程
  - 合并到 main 分支
  - 验证：生产环境正常

- [ ] **Task 10.5**: 归档变更
  - 运行 `openspec archive refactor-strategy-parameter-configuration`
  - 更新 specs（如有变更）
  - 更新 project.md 记录重构
  - 验证：归档完成

## 依赖关系

**并行任务**：
- 阶段 1 所有任务可并行
- 阶段 3 所有任务可并行
- 阶段 9.1-9.3 可并行

**顺序依赖**：
- 阶段 2 必须在阶段 3-8 之前（重构为基础）
- 阶段 4-8 可以部分并行但需要阶段 2 完成
- 阶段 9 必须在阶段 2-8 全部完成后
- 阶段 10 必须在阶段 9 完成后

## 估算汇总

- 阶段 1: 4h
- 阶段 2: 12h
- 阶段 3: 8h
- 阶段 4: 6h
- 阶段 5: 4h
- 阶段 6: 6h
- 阶段 7: 4h
- 阶段 8: 4h
- 阶段 9: 8h
- 阶段 10: 2h

**总计**: 58h (~7.5 工作日)

## 备注

- 每完成一个阶段，运行完整的 E2E 测试套件
- 每个 Task 完成后提交独立 commit
- 遇到阻塞问题立即记录并寻求帮助
- 优先级：P0 任务优先，P1 任务其次
