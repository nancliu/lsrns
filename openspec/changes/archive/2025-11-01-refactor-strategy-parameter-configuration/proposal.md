# 提案：重构策略参数配置前端功能

**变更ID**: refactor-strategy-parameter-configuration
**状态**: 提案中 (Proposal)
**创建日期**: 2025-11-01
**作者**: Claude Code
**实施范围**: 前端重构 (UI/UX 改进 + 代码质量)

## Why

当前策略参数配置界面（创建工作流第3步）存在多个布局、数据加载、控件设计方面的问题，导致用户体验差、易出错、代码难维护。

### 当前问题

1. **布局与样式不一致**
   - 参数表单的控件宽度、间距不统一（VSS、TEC、DHS 差异大）
   - 策略名称/描述输入框与按钮容器布局混乱，按钮被挤压
   - 时间轴图表与配置表格的间距不规则
   - 响应式设计缺失，窄屏布局混乱

2. **模板数据加载不完整**
   - 默认值未从模板 JSON 的 `default_value` 正确加载
   - 表单打开时是空表格，需要手动添加行
   - 参数约束信息（范围、单位、必填标记）未正确展示

3. **时间语义定义混乱**
   - VSS 使用 `time_hours`（时刻点）
   - TEC/DHS 使用 `begin_hours/end_hours`（时间段）
   - UI 标签无区分，时间轴可视化不一致

4. **车型配置错误地混在参数表中**
   - DHS/TEC 每个时间区间都配置 `allowed_vehicle_types`
   - 车型应是全局配置，不应按区间配置
   - 用文本输入车型易出错，无多选UI

5. **控件验证和用户提示不足**
   - 表格操作无验证（时间顺序、数值范围）
   - 删除行无确认提示
   - Hint 文本重复，指导不清

6. **路段来源混乱**
   - Step 2 已完成路段选择
   - Step 3 仍显示旧的路段填写框
   - 用户困惑于使用哪个来源

7. **车型允许/禁止逻辑未区分**
   - 混用 `allowed_vehicle_types` 和 `disallow_vehicle_types`
   - 前端标签和Hint 未根据参数类型动态变化

8. **代码质量债务**
   - `parameter_form.js` 2258 行，含多个 >100 行函数
   - 4 个重复的时间轴更新函数
   - 3 个重复的行添加函数
   - 函数职责不清，难以维护

## What Changes

### 1. 统一参数配置表单布局

- 所有参数控件宽度、间距、对齐一致
- 策略名称/描述输入框宽度充足
- 响应式设计确保窄屏显示正常
- 使用 Grid/Flexbox 和 CSS 变量

### 2. 正确加载模板默认值

- 从模板的 `default_value` 初始化参数值
- 表单打开时显示示例数据
- 参数约束从 Schema 动态生成

### 3. 明确时间轴参数语义

**策略类型差异**（详见 `TIMELINE_CLARIFICATION.md`）：

VSS (时刻表示):
- 列标签：时间(小时) | 限速(km/h)
- 数据：`[{ time_hours: 7, speed_kmh: 60 }]`
- 语义：从 7:00 开始限速 60 km/h，直到下一个时刻点
- 时间轴：段状着色（每段显示当前速度）

TEC/DHS (时段表示):
- 列标签：开始时间(小时) | 结束时间(小时) | [状态/流量]
- 数据：`[{ begin_hours: 7, end_hours: 9, status: 'OPEN' }]`
- 语义：7:00-9:00 硬路肩开放/入口开放
- 时间轴：段状着色（绿=开放，红=关闭）

**TEC 流量控制**（未来扩展）：
- 时间段 + 流量值（400 vph）+ 目标速度（60 km/h）
- 本次重构仅支持 TEC 开关模式，流量控制作为 Phase 2 扩展

### 4. 移除时间轴/配置表中的车型配置

- 删除 DHS/TEC 间隔表中的车型列
- 车型配置集中在单独的全局区域
- 策略级车型决定生成的 rou.xml

### 5. 车型配置UI根据模式动态变化

- `allowed_vehicle_types` → UI 显示"允许的车型"
- `disallow_vehicle_types` → UI 显示"禁止的车型"
- Hint 文本相应变化

### 6. 使用 Step 2 路段列表

- Step 3 显示 Step 2 已选路段的只读列表
- 移除旧的 `affected_edges` 输入框
- 需修改返回 Step 2 重新选择

### 7. 统一验证规则和用户提示

- 表格行操作有验证（时间顺序、数值范围）
- 删除行有确认对话框
- 参数级Hint：仅显示约束
- 控制级Hint：仅显示操作说明

### 8. 代码重构

**时间轴更新函数合并**（详见 `TIMELINE_CLARIFICATION.md`）：
- 删除 4 个重复函数：`updateTimelineFromTable`, `updateDHSTimelineFromTable`, `updateFlowTimelineFromTable`, `updateTECTimelineFromTable`
- 新增统一函数：`updateTimeline(tbody, config)` + 预设配置 `TIMELINE_CONFIGS`
- 保持 `TimelineVisualizer.updateTimeline()` 不变（已有良好设计）

**行添加函数合并**：
- 消除 3 个重复的行添加函数
- 新增统一函数：`addRow(tbody, config)`

**其他重构**：
- 减少函数长度（<50行）
- 提取公共验证和DOM操作

## Impact

### 收益

1. **UI 一致性**：所有参数表单布局统一、响应式友好
2. **数据完整性**：模板默认值正确加载
3. **语义清晰**：时间语义明确
4. **设计合理**：车型配置分离
5. **用户体验**：验证提示清晰
6. **可维护性**：代码重复减少 200+ 行
7. **长期收益**：为功能增强奠定基础

### 包含范围

- 参数表单布局（CSS）改进
- 模板默认值加载逻辑修复
- 时间参数语义明确
- 车型配置从表格中移除
- 车型UI根据模式动态变化
- 路段来源统一
- 验证规则和提示改进
- 代码重构（消除重复）
- E2E 测试更新

### 不包含范围

- Step 2 工作流变更
- 后端 API 修改
- 模板 Schema 修改
- 新增参数类型
- 策略图形化编辑器（可视化时间轴拖拽等）
- TEC 流量控制（时段 + 流量值 + 目标速度，Phase 2 扩展）
- VSS + DHS 双层叠加显示（Phase 2 扩展）
- OA 系统集成

## 依赖项

- 现有策略模板 v2.0 Schema
- 路段选择器 UI
- CSS 框架变量
- E2E 测试框架 (Playwright)

## 成功标准

1. **布局一致**：VSS、TEC、DHS 页面布局统一，响应式测试通过
2. **数据正确**：表单打开时显示模板初始数据
3. **语义明确**：时间轴和表格清晰表达时刻/时段
4. **车型正确**：表格无车型，全局配置，逻辑正确
5. **路段统一**：Step 3 仅显示 Step 2 列表
6. **验证清晰**：非法输入有提示，删除有确认
7. **Hint清晰**：不重复，易扫读
8. **代码干净**：消除重复，函数 <50 行
9. **测试通过**：所有 E2E 测试通过

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| CSS 改动影响其他页面 | 中 | 使用命名空间和变量 |
| 模板数据加载逻辑复杂 | 中 | 先创建单元测试 |
| 时间语义变更影响现有策略 | 低 | 向后兼容 |
| 代码重构引入回归 | 高 | 充分 E2E 测试覆盖 |

## 参考资料

- [TIMELINE_CLARIFICATION.md](./TIMELINE_CLARIFICATION.md) - 时间轴更新函数合并策略详解
- [design.md](./design.md) - 架构设计和技术决策
- [tasks.md](./tasks.md) - 实施任务清单
- [FRONTEND_CODE_COMPLIANCE_REPORT.md](../../docs/frontend_analysis/FRONTEND_CODE_COMPLIANCE_REPORT.md) - 前端代码分析
- [REFACTORING_STRATEGY.md](../../docs/frontend_analysis/REFACTORING_STRATEGY.md) - 重构指南
- [strategy-templates spec](../../openspec/specs/strategy-templates/spec.md) - 模板规范
- [CLAUDE.md](../../CLAUDE.md) - 代码标准
