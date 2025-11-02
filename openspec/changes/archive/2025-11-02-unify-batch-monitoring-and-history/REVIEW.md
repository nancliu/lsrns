# Proposal Review: Unify Batch Monitoring and History

**Review Date**: 2025-11-02  
**Reviewer**: AI Assistant  
**Change ID**: `unify-batch-monitoring-and-history`  
**Status**: ✅ **Overall Approved with Minor Recommendations**

---

## Executive Summary

该提案质量高，结构完整，技术方案合理。建议在实施前统一时间估算，并补充一些实施细节说明。总体**建议批准**，但需要修复以下问题后再开始实施。

---

## ✅ Strengths

### 1. **提案结构完整**
- ✅ 包含所有必要章节（Why, What Changes, Proposed Solution, Success Criteria, Risks, Implementation Phases）
- ✅ 问题陈述清晰，痛点分析到位
- ✅ 方案描述详细，易于理解

### 2. **技术方案合理**
- ✅ 基于现有代码架构（已验证 `progressView` 和 `historyView` 存在）
- ✅ 可展开卡片设计符合现代 UI 模式
- ✅ 渐进式披露（Progressive Disclosure）策略恰当
- ✅ 保留 Results 标签页独立的设计决策正确

### 3. **Spec 文件一致**
- ✅ `spec.md` 中的需求与提案内容匹配
- ✅ MODIFIED Requirements 格式正确（虽然有验证器解析问题，但不影响功能）
- ✅ 场景描述详细，包含所有边界情况

### 4. **实施计划详细**
- ✅ `tasks.md` 提供了清晰的实施步骤
- ✅ 每个阶段都有验证标准
- ✅ 依赖关系明确（依赖 `fix-batch-history-data-display`）

---

## ⚠️ Issues Found

### 1. **时间估算不一致** (必须修复)

**问题**：
- `proposal.md`: **29-38 小时** (4-5 工作日)
- `tasks.md`: **39-51 小时** (5-7 工作日)

**原因**：
- `proposal.md` 只包含 5 个阶段
- `tasks.md` 更详细，包含 8 个阶段（增加了响应式设计、文档等）

**建议**：
- 以 `tasks.md` 为准（更全面准确）
- 更新 `proposal.md` 的时间估算部分，使其与 `tasks.md` 一致
- 或合并 `proposal.md` 的 Phase 4-5，使其与 `tasks.md` 对应

**修复位置**：`proposal.md` 第 364-375 行

---

### 2. **实施阶段划分不一致**

**问题**：
- `proposal.md`: 5 个阶段
- `tasks.md`: 8 个阶段

**差异**：
- `tasks.md` 增加了：
  - Phase 5: Filtering & Utilities (4-5h)
  - Phase 6: Responsive Design (4-5h)
  - Phase 8: Documentation (2-3h)
- `proposal.md` 将 Filtering 和 Styling 合并

**建议**：
- 保持 `tasks.md` 的详细划分（更适合实施跟踪）
- 在 `proposal.md` 中补充说明阶段划分的详细程度

---

### 3. **缺少“重新运行”功能的技术细节**

**问题**：
- 提案提到 Failed 批次有"重新运行"按钮
- 但未说明"重新运行"的具体实现方式：
  - 是使用相同的参数创建新批次？
  - 还是恢复失败的任务继续执行？

**建议**：
在 `Design Decisions` 或 `Proposed Solution` 中补充：
```markdown
### Batch Retry Mechanism

**For Failed Batches**:
- "重新运行"按钮将创建一个新的批次，使用原批次的相同配置（case_id, plan_ids）
- 新批次将使用新的 batch_id（避免覆盖原批次数据）
- 原批次保留，用户可对比失败和成功的执行
```

---

### 4. **执行时间线可视化复杂度未充分评估**

**问题**：
- 提案要求 Gantt-chart 风格的时间线可视化
- `tasks.md` 中的实现使用纯 HTML/CSS（无图表库）
- 对于复杂的并行任务可视化，纯 CSS 可能不够灵活

**建议**：
- 如果任务数量 >10 且存在大量并行执行，考虑使用轻量级图表库（如 Chart.js 的 timeline plugin）
- 或明确说明：初始版本仅支持简单的水平条形图，高级功能（缩放、拖拽）在后续迭代中实现

---

### 5. **状态持久化策略未明确**

**问题**：
- Open Questions 中提到："Should we persist expanded/collapsed state in localStorage?"
- 决策是"Deferred"，但未说明如何处理
- 用户可能期望记住展开的批次

**建议**：
- 补充说明：初始版本不持久化（每次刷新页面都折叠所有卡片）
- 后续迭代可添加 localStorage 支持（如果用户反馈需要）

---

### 6. **Mobile Modal 实现细节缺失**

**问题**：
- 提案提到移动端使用 Modal 对话框
- 但未说明 Modal 与现有代码的集成方式（是否会影响其他视图）

**建议**：
- 在 `tasks.md` 中已经包含 Modal 实现（Phase 6.1-6.2），但建议在 `proposal.md` 的 `Design Decisions` 中补充说明：
  - Modal 仅在 `monitoringView` 中激活
  - 其他视图不受影响
  - Modal 关闭后状态如何处理

---

## 📋 Recommended Actions

### 必须修复（Before Approval）

1. **统一时间估算**
   - [ ] 更新 `proposal.md` 第 364-375 行，使用 `tasks.md` 的时间估算
   - [ ] 或将 `proposal.md` 的阶段划分与 `tasks.md` 对齐

2. **补充技术细节**
   - [ ] 在 `Design Decisions` 中说明"重新运行"的实现方式
   - [ ] 明确执行时间线的初始功能范围（是否支持高级交互）

### 建议改进（Nice to Have）

3. **澄清状态管理**
   - [ ] 明确说明 expanded/collapsed 状态在页面刷新时的行为
   - [ ] 考虑是否需要 sessionStorage（当前会话）vs localStorage（永久）

4. **风险评估补充**
   - [ ] 增加"执行时间线可视化复杂度"的风险项
   - [ ] 评估纯 CSS 实现的可行性和性能

---

## ✅ Approval Checklist

### 功能性需求
- [x] 统一批次列表显示所有状态
- [x] 可展开卡片显示详细信息
- [x] 实时监控数据自动更新
- [x] Results 标签页集成
- [x] 执行时间线可视化
- [x] 响应式布局
- [x] 批次删除功能

### 技术可行性
- [x] 基于现有架构（已验证代码存在）
- [x] 无需后端 API 修改
- [x] 依赖项明确（`fix-batch-history-data-display`）
- [x] 代码复用策略清晰

### 文档完整性
- [x] Spec 文件完整
- [x] Tasks 文件详细
- [x] 提案逻辑清晰
- [ ] **时间估算需统一** ⚠️

### 风险评估
- [x] 风险识别充分
- [x] 缓解措施合理
- [ ] **执行时间线复杂度需补充** ⚠️

---

## 📊 Overall Assessment

| 维度 | 评分 | 说明 |
|------|------|------|
| **提案质量** | ⭐⭐⭐⭐⭐ | 结构完整，逻辑清晰 |
| **技术可行性** | ⭐⭐⭐⭐⭐ | 基于现有代码，方案合理 |
| **Spec 一致性** | ⭐⭐⭐⭐⭐ | Spec 与提案匹配 |
| **实施计划** | ⭐⭐⭐⭐☆ | 任务详细，但时间估算需统一 |
| **风险评估** | ⭐⭐⭐⭐☆ | 风险识别充分，但可补充技术风险 |

**综合评分**: ⭐⭐⭐⭐⭐ (4.8/5.0)

---

## 🎯 Final Recommendation

**建议：批准，但需要在修复上述问题后开始实施**

### 优先级修复（Blocking）
1. 统一时间估算（`proposal.md` vs `tasks.md`）
2. 补充"重新运行"功能的技术细节

### 非阻塞改进（Can be done during implementation）
3. 执行时间线可视化的技术选择（CSS vs Chart.js）
4. 状态持久化策略的最终决定

---

## 📝 Additional Notes

### 代码审查点
在实施时，特别关注以下代码位置：
- `frontend/control/js/batch_simulation.js:130-158` - `switchView()` 函数需要修改
- `frontend/control/js/batch_simulation.js:1180-1240` - `loadBatchHistory()` 需要重构
- `frontend/control/simulations.html:91-150` - `progressView` 需要移除
- `frontend/control/simulations.html:188-213` - `historyView` 需要移除

### 测试重点
- 确保 Live Curve 轮询逻辑在可展开卡片上下文中正常工作
- 验证多个批次同时运行时的性能（防止过多轮询）
- 测试移动端 Modal 的滚动和关闭行为

---

## ✅ Review Status

**Status**: ⚠️ **Approved with Conditions**

**Conditions**:
1. 修复时间估算不一致问题
2. 补充"重新运行"功能的技术说明

**Estimated Time to Fix**: 30-60 分钟

修复后，提案可以进入实施阶段。

---

**Reviewed by**: AI Assistant  
**Date**: 2025-11-02
