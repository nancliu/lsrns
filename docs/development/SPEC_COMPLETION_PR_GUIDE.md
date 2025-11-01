# 如何以 PR 方式补全 OpenSpec 规格文档

**目标**: 为已归档的 `add-streamlined-time-selector-visualization` change 补全规格文档

**状态**: 已归档在 `openspec/changes/archive/2025-10-31-add-streamlined-time-selector-visualization/`

---

## 分步指南

### Step 1: 创建新分支

```bash
# 从 main 分支创建新分支
git checkout main
git pull origin main
git checkout -b spec/add-streamlined-time-selector-visualization-docs
```

**分支命名规则**:
- `spec/` 前缀表示这是规格文档更新
- 包含 change ID

---

### Step 2: 补全 proposal.md 中缺失的部分

位置: `openspec/changes/archive/2025-10-31-add-streamlined-time-selector-visualization/proposal.md`

**当前缺失**:
- "## Why" 部分（虽然有内容但需要标准化）
- "## What Changes" 部分

**应该添加的内容**:

```markdown
## Why

**问题**: 当前的交通管控策略配置完全依赖表格式输入，用户难以直观地看到基于时间的参数在24小时周期内的分布情况。

**影响**:
1. 配置错误增加 - 用户难以快速发现时间间隙、重叠或错误的配置模式
2. 用户体验差 - 从数字表格数据构建时间轴需要较高的认知负荷
3. 工作流程缓慢 - 缺少对管控策略模式的快速视觉概览

**解决方案**: 添加时间轴可视化组件，为基于时间的管控参数提供即时的视觉反馈。

## What Changes

### 新增文件
- `frontend/control/js/timeline_visualizer.js` - 时间轴渲染模块
- `tests/e2e/test_timeline_visualization.spec.js` - E2E 测试

### 修改文件
- `frontend/control/js/parameter_form.js`
  - 修改 `renderStepArrayControl()` - 集成 VSS 时间轴
  - 修改 `renderDHSIntervalControl()` - 集成 DHS 时间轴
  - 修改 `renderFlowIntervalControl()` - 集成 TEC 时间轴
  - 添加 `updateDHSTimelineFromTable()` - DHS 实时更新
  - 添加 `updateFlowTimelineFromTable()` - TEC 实时更新

- `frontend/control/templates.html`
  - 删除硬编码的参数控制函数 (207 行)
  - 添加 TimelineVisualizer 脚本加载

### 修改的模板
- `templates/control_strategies/dynamic_hard_shoulder/dhs_peak_hours.json`
- `templates/control_strategies/dynamic_hard_shoulder/dhs_peak_multi_interval.json`
- `templates/control_strategies/toll_entrance_control/tec_flow_metering.json`

## Deltas

### Delta 1: Frontend Parameter Control Refactor
- **Location**: `frontend/control/js/parameter_form.js`
- **Changes**: Add timeline visualization and real-time update mechanisms
- **Impact**: Enhanced user experience with visual timeline feedback

### Delta 2: Templates HTML Cleanup
- **Location**: `frontend/control/templates.html`
- **Changes**: Remove hardcoded parameter control functions
- **Impact**: Elimination of code duplication and compliance with RULE-FE-001

### Delta 3: Time Selector Visualization Capability
- **Location**: `openspec/specs/time-selector-visualization/`
- **Changes**: Define new time-selector-visualization capability
- **Impact**: Enable time-based parameter visualization for all control strategies
```

---

### Step 3: 修复 spec.md 中的 MUST/SHALL 关键词

位置: `openspec/changes/archive/2025-10-31-add-streamlined-time-selector-visualization/specs/time-selector-visualization/spec.md`

**当前问题**: 规格中的 Requirement 缺少 "SHALL" 或 "MUST" 关键词

**修复方法**:

找到所有 Requirement 块，修改为：

```markdown
### Requirement: 时间轴必须渲染24小时可视化表示

**ID**: `TSV-001`
**优先级**: P0

时间轴组件 **SHALL** 显示24小时时间段的可视化表示，带有显示不同时间参数值的明确段。
```

**需要修改的 Requirements**:

| ID | 当前状态 | 修复 |
|-----|---------|------|
| TSV-001 | "should" | "SHALL" |
| TSV-002 | "should" | "SHALL" |
| TSV-003 | "should" | "SHALL" |
| TSV-004 | "should" | "SHALL" |
| TSV-005 | "should" | "SHALL" |
| TSV-006 | "should" | "SHALL" |
| TSV-007 | "should" | "SHALL" |
| TSV-008 | "should" | "SHALL" |

**替换命令**:

```bash
# 在 spec.md 中替换 "should" 为 "SHALL"
sed -i 's/should /SHALL /g' openspec/changes/archive/2025-10-31-add-streamlined-time-selector-visualization/specs/time-selector-visualization/spec.md

# 验证替换结果
grep "SHALL" openspec/changes/archive/2025-10-31-add-streamlined-time-selector-visualization/specs/time-selector-visualization/spec.md
```

---

### Step 4: 验证规格文档

```bash
# 验证 OpenSpec 结构
cd D:\projects\OD_SIM
npx openspec validate --strict

# 查看归档的 change
npx openspec show 2025-10-31-add-streamlined-time-selector-visualization

# 检查规格是否有错误
npx openspec list --specs
```

---

### Step 5: 创建 PR

```bash
# 提交更改
git add openspec/changes/archive/2025-10-31-add-streamlined-time-selector-visualization/

git commit -m "docs: Complete OpenSpec specification for time-selector-visualization

## 概述
补全时间轴可视化 OpenSpec change 的规格文档。

## 修改内容

### proposal.md
- 添加标准的 '## Why' 部分（问题、影响、解决方案）
- 添加标准的 '## What Changes' 部分（新增/修改文件清单）
- 添加 '## Deltas' 部分（变更影响描述）

### spec.md
- 修改所有 Requirement 使用 'SHALL' 关键词
- 符合 OpenSpec 规范要求

## 验证
✅ npx openspec validate --strict
✅ 所有规格验证通过

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
"

# 推送分支
git push origin spec/add-streamlined-time-selector-visualization-docs
```

---

## 详细修复清单

### proposal.md 需要添加的完整内容

```markdown
## Why

**Background**: 交通管控策略配置是复杂的操作，涉及多个参数在不同时间段的配置。

**Problem**:
- 用户必须通过数字表格理解24小时周期内的参数分布
- 无法直观看到时间间隙、重叠或错误的配置
- 认知负荷高，容易出错

**Impact**:
- ❌ 配置错误率高
- ❌ 用户体验差
- ❌ 工作流程低效

## What Changes

### Files Added
1. `frontend/control/js/timeline_visualizer.js` (800 lines)
   - 时间轴渲染核心模块
   - 支持 VSS、DHS、TEC 参数类型
   - 色彩编码和实时更新

2. `tests/e2e/test_timeline_visualization.spec.js` (200 lines)
   - 时间轴功能 E2E 测试

### Files Modified
1. `frontend/control/js/parameter_form.js`
   - `renderStepArrayControl()` - 添加时间轴支持
   - `renderDHSIntervalControl()` - 添加时间轴支持
   - `renderFlowIntervalControl()` - 添加时间轴支持
   - 新增 `updateDHSTimelineFromTable()`
   - 新增 `updateFlowTimelineFromTable()`

2. `frontend/control/templates.html`
   - 移除硬编码参数控制函数 (207 行)
   - 改进代码模块化

3. Template configuration files
   - 更新默认值配置

## Deltas

### Delta 1: Time Axis Visualization System

**Affected Specs**:
- `time-selector-visualization` (ADDED)

**Description**:
Introduces new capability for visualizing time-based parameters as interactive 24-hour timelines with color-coded segments.

**Impact**:
- ✅ Enhanced VSS (Variable Speed Sign) parameter visualization
- ✅ Enhanced DHS (Dynamic Hard Shoulder) parameter visualization
- ✅ Enhanced TEC (Toll Entrance Control) parameter visualization
- ✅ Real-time synchronization between table and timeline

### Delta 2: Frontend Code Quality Improvement

**Affected Code**:
- Parameter form rendering system
- Template HTML cleanup

**Changes**:
- Removed 207 lines of code duplication
- Applied RULE-FE-001 (Frontend Data Rules)
- Unified parameter initialization mechanism

**Impact**:
- ✅ Better code maintainability
- ✅ Clearer separation of concerns
- ✅ Consistent frontend patterns
```

### spec.md 需要的具体修改

在每个 Requirement 前面添加 "**SHALL**" 关键词：

```markdown
### Requirement: 时间轴必须渲染24小时可视化表示

**ID**: `TSV-001`
**优先级**: P0

时间轴组件 **SHALL** 显示24小时时间段的可视化表示，带有显示不同时间参数值的明确段。
```

---

## 完整的 PR 模板

```markdown
# Spec: Complete time-selector-visualization OpenSpec Documentation

## 描述

补全已归档的 `add-streamlined-time-selector-visualization` OpenSpec change 的规格文档。

## 修改内容

### proposal.md
- [x] 添加 "## Why" 部分（问题、影响、解决方案）
- [x] 添加 "## What Changes" 部分（文件清单）
- [x] 添加 "## Deltas" 部分（变更影响）

### spec.md
- [x] 修改 Requirement 使用 "SHALL" 关键词
- [x] 符合 OpenSpec 规范

## 验证步骤

- [x] 运行 `npx openspec validate --strict`
- [x] 查看 `npx openspec show 2025-10-31-add-streamlined-time-selector-visualization`
- [x] 验证所有规格有效

## 相关 Issue/Change

- Relates to: `add-streamlined-time-selector-visualization` (archived)
- Type: documentation
- Priority: P2 (non-blocking)

## 检查清单

- [x] 规格文档完整
- [x] MUST/SHALL 关键词正确
- [x] 文件清单准确
- [x] Deltas 清晰
- [x] OpenSpec 验证通过
```

---

## 问题排查

### 如果 OpenSpec 验证仍然失败

**检查 1**: 确保 "## Why" 部分正确

```bash
grep -n "## Why" openspec/changes/archive/2025-10-31-add-streamlined-time-selector-visualization/proposal.md
```

**检查 2**: 确保 "## What Changes" 部分正确

```bash
grep -n "## What Changes" openspec/changes/archive/2025-10-31-add-streamlined-time-selector-visualization/proposal.md
```

**检查 3**: 确保所有 Requirement 有 "SHALL" 或 "MUST"

```bash
grep -n "Requirement:" openspec/changes/archive/2025-10-31-add-streamlined-time-selector-visualization/specs/time-selector-visualization/spec.md | head -10
```

**检查 4**: 运行完整验证

```bash
npx openspec validate --strict 2>&1 | grep -A 5 "time-selector-visualization"
```

---

## PR 审查检查清单

在提交 PR 时，请确保：

- [ ] proposal.md 有 "## Why" 部分
- [ ] proposal.md 有 "## What Changes" 部分
- [ ] proposal.md 有 "## Deltas" 部分（可选但建议）
- [ ] spec.md 中所有 Requirement 都有 "SHALL" 或 "MUST"
- [ ] `npx openspec validate --strict` 通过
- [ ] `npx openspec show` 输出无错误
- [ ] Git 提交信息清晰

---

## 时间估计

| 任务 | 时间 |
|------|------|
| 更新 proposal.md | 15 分钟 |
| 修复 spec.md 关键词 | 10 分钟 |
| 验证 OpenSpec | 5 分钟 |
| 创建 PR | 5 分钟 |
| **总计** | **35 分钟** |

---

## 完成后

### PR 合并后的下一步

```bash
# 1. 删除本地分支
git branch -d spec/add-streamlined-time-selector-visualization-docs

# 2. 删除远程分支
git push origin --delete spec/add-streamlined-time-selector-visualization-docs

# 3. 更新本地 main
git checkout main
git pull origin main
```

### 验证归档 change 已完全就绪

```bash
npx openspec show 2025-10-31-add-streamlined-time-selector-visualization
```

应该显示:
- ✅ 完整的规格
- ✅ 清晰的 Why 和 What Changes
- ✅ 所有 Requirement 都有 SHALL/MUST
- ✅ 无验证错误

---

## 参考资源

- OpenSpec 规范: `openspec/AGENTS.md`
- 示例提案: `openspec/changes/archive/*/proposal.md`
- 示例规格: `openspec/changes/archive/*/specs/*/spec.md`

---

**总结**: 这是一个直接的文档补全 PR，只需要添加缺失的规格部分，无需修改代码。预计 30-40 分钟完成。
