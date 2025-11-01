# 策略参数配置前端重构 - OpenSpec 提案

## 📋 提案概览

**变更 ID**: `refactor-strategy-parameter-configuration`
**状态**: 提案中 (Proposal)
**创建日期**: 2025-11-01
**预计工时**: 58小时 (~7.5工作日)

## 🎯 核心目标

修正优化策略管理-配置参数部分的前端功能，同时进行该部分前端的重构，解决布局、数据加载、控件设计方面的8大类问题。

## 📂 文档结构

### 核心文档

| 文件 | 大小 | 说明 |
|------|------|------|
| [proposal.md](./proposal.md) | 7.3KB | **提案主文档** - 问题描述、变更范围、影响评估 |
| [design.md](./design.md) | 15KB | **架构设计** - 技术决策、代码结构、实现方案 |
| [tasks.md](./tasks.md) | 13KB | **任务清单** - 45个任务，10个阶段，依赖关系 |
| [TIMELINE_CLARIFICATION.md](./TIMELINE_CLARIFICATION.md) | 12KB | **澄清文档** - 时间轴函数合并策略详解 |

### 规范文件

| 文件 | 说明 |
|------|------|
| [specs/parameter-form-layout/spec.md](./specs/parameter-form-layout/spec.md) | **需求规范** - 7个需求，15个场景用例 |

## 🔍 解决的核心问题

### 1. 布局问题
- ✅ 参数表单控件宽度、间距不统一
- ✅ 策略名称/描述输入框与按钮布局混乱
- ✅ 响应式设计缺失

### 2. 数据加载问题
- ✅ 模板默认值未从 `default_value` 正确加载
- ✅ 表单打开时是空表格
- ✅ 参数约束信息未正确展示

### 3. 时间语义混乱
- ✅ VSS（时刻点）vs TEC/DHS（时间段）语义不明确
- ✅ UI 标签无区分
- ✅ 时间轴可视化不一致

### 4. 车型配置错误
- ✅ 车型混在 DHS/TEC 间隔表中（应为全局配置）
- ✅ 文本输入车型易出错
- ✅ 允许/禁止逻辑未区分

### 5. 验证和提示不足
- ✅ 表格操作无验证
- ✅ 删除行无确认提示
- ✅ Hint 文本重复

### 6. 路段来源混乱
- ✅ Step 2 和 Step 3 都有路段输入
- ✅ 用户困惑于使用哪个来源

### 7. 代码质量债务
- ✅ 4 个重复的时间轴更新函数
- ✅ 3 个重复的行添加函数
- ✅ 多个 >100 行的大型函数

## 🔧 关键技术决策

### 时间轴更新函数合并（详见 TIMELINE_CLARIFICATION.md）

**策略类型差异**：
- **VSS**: 时刻点 (`time_hours`) → 段状可视化
- **DHS**: 时间段 (`begin_hours`, `end_hours`, `status`) → 段状可视化
- **TEC**: 时间段 + 开关状态（本次）或流量（Phase 2）

**合并方案**：
```javascript
// 删除 4 个重复函数
❌ updateTimelineFromTable()
❌ updateDHSTimelineFromTable()
❌ updateFlowTimelineFromTable()
❌ updateTECTimelineFromTable()

// 新增统一函数
✅ updateTimeline(tbody, config)
✅ TIMELINE_CONFIGS = {vss, dhs, tec_simple}
✅ updateTimelineByType(tbody, type)
```

**保持不变**：
- `TimelineVisualizer.updateTimeline()` - 已有良好设计，无需修改

### 本次重构范围 vs 未来扩展

**包含**：
- ✅ VSS 时间轴（时刻点 → 段状可视化）
- ✅ DHS 时间轴（时段 + 开关状态）
- ✅ TEC 简化时间轴（时段 + 开关状态）
- ✅ 代码重复消除

**不包含（未来扩展）**：
- ⏸️ TEC 流量控制（时段 + 流量值 + 目标速度）
- ⏸️ VSS + DHS 双层叠加显示
- ⏸️ 策略图形化编辑器（可视化时间轴拖拽）

## 📊 实施计划

### 10 个阶段，45 个任务

| 阶段 | 工时 | 关键任务 |
|------|------|----------|
| 阶段 1: 准备与设计 | 4h | E2E 基线、CSS 变量、数据流文档 |
| 阶段 2: 代码重构 | 12h | 合并时间轴函数、行添加函数、提取验证 |
| 阶段 3: UI 布局改进 | 8h | 修复布局、统一间距、响应式设计 |
| 阶段 4: 模板默认值加载 | 6h | 初始化函数、集成到表单生成、约束显示 |
| 阶段 5: 时间语义明确化 | 4h | 更新标签、调整可视化 |
| 阶段 6: 车型配置分离 | 6h | 移除表格列、全局配置、动态标签 |
| 阶段 7: 路段来源统一 | 4h | 隐藏旧输入框、显示只读列表 |
| 阶段 8: 验证和提示改进 | 4h | 时间顺序验证、范围验证、确认对话框 |
| 阶段 9: 测试与文档 | 8h | E2E 测试、单元测试、手动测试 |
| 阶段 10: 验收与归档 | 2h | 性能测试、浏览器兼容性、归档 |

**总计**: 58小时

## ✅ 成功标准

1. ✅ 布局一致：VSS、TEC、DHS 布局统一，响应式测试通过
2. ✅ 数据正确：表单打开时显示模板初始数据
3. ✅ 语义明确：时间轴和表格清晰表达时刻/时段
4. ✅ 车型正确：表格无车型，全局配置，逻辑正确
5. ✅ 路段统一：Step 3 仅显示 Step 2 列表
6. ✅ 验证清晰：非法输入有提示，删除有确认
7. ✅ Hint清晰：不重复，易扫读
8. ✅ 代码干净：消除重复，函数 <50 行
9. ✅ 测试通过：所有 E2E 测试通过

## 📖 阅读指南

### 快速了解（5分钟）
1. 阅读本 README
2. 阅读 [proposal.md](./proposal.md) 的 "Why" 和 "What Changes" 部分

### 深入理解（30分钟）
1. 阅读 [TIMELINE_CLARIFICATION.md](./TIMELINE_CLARIFICATION.md) - 理解时间轴合并策略
2. 阅读 [design.md](./design.md) - 理解架构设计
3. 浏览 [tasks.md](./tasks.md) - 了解实施步骤

### 实施准备（1小时）
1. 详细阅读 [tasks.md](./tasks.md)
2. 阅读 [specs/parameter-form-layout/spec.md](./specs/parameter-form-layout/spec.md)
3. 查看参考资料中的代码分析报告

## 🔗 相关资源

### 内部文档
- [FRONTEND_CODE_COMPLIANCE_REPORT.md](../../docs/frontend_analysis/FRONTEND_CODE_COMPLIANCE_REPORT.md) - 前端代码分析
- [REFACTORING_STRATEGY.md](../../docs/frontend_analysis/REFACTORING_STRATEGY.md) - 重构指南
- [strategy-templates spec](../../openspec/specs/strategy-templates/spec.md) - 模板规范
- [CLAUDE.md](../../CLAUDE.md) - 代码标准

### 代码位置
- `frontend/control/js/parameter_form.js` (2258 行) - 主要重构目标
- `frontend/control/js/timeline_visualizer.js` - 时间轴可视化（保持不变）
- `frontend/control/css/templates-forms.css` - 表单样式
- `frontend/control/templates.html` - HTML 模板

## 📝 验证状态

```bash
openspec validate refactor-strategy-parameter-configuration --strict
# Result: Change 'refactor-strategy-parameter-configuration' is valid ✓
```

## 🎯 下一步

1. **项目经理审批**：审阅 proposal.md
2. **技术团队评审**：评审 design.md 和 TIMELINE_CLARIFICATION.md
3. **开始实施**：按照 tasks.md 顺序执行
4. **测试验证**：E2E 测试 + 手动测试
5. **归档**：`openspec archive refactor-strategy-parameter-configuration`

---

**Created**: 2025-11-01
**Last Updated**: 2025-11-01
**Status**: Ready for Review ✓
