# OpenSpec 工作流程详解与协作指南

## 📚 目录

1. [OpenSpec 是什么](#openspec-是什么)
2. [三阶段工作流](#三阶段工作流)
3. [我们如何协作](#我们如何协作)
4. [常见场景和流程](#常见场景和流程)
5. [最佳实践](#最佳实践)

---

## OpenSpec 是什么？

**OpenSpec** 是一个 spec-driven development（规格驱动开发）框架，帮助你：

- 📋 **规划变更** - 创建清晰的提案（proposal）
- 🎯 **追踪进度** - 维护任务清单（tasks）
- 📖 **文档化决策** - 记录技术方案（design）
- ✅ **验证完整性** - 确保需求完整（specs）
- 📦 **管理部署** - 从草稿到归档的完整生命周期

### 核心概念

| 概念 | 说明 | 位置 |
|------|------|------|
| **Spec** | 已实现的功能规格（current truth） | `openspec/specs/[capability]/spec.md` |
| **Change** | 待实现的变更提案（proposed changes） | `openspec/changes/[change-id]/` |
| **Proposal** | 变更的"为什么、什么、影响" | `proposal.md` |
| **Tasks** | 具体实现任务的检查清单 | `tasks.md` |
| **Design** | 技术决策和架构说明 | `design.md` |
| **Scenario** | 需求的具体验收标准（WHEN/THEN） | `spec.md` |

---

## 三阶段工作流

### 🟢 Stage 1: 创建变更（Creating Changes）

**何时触发**：
- ✅ 添加新功能/特性
- ✅ 进行破坏性改变（API、数据结构）
- ✅ 改变架构或设计模式
- ✅ 性能优化（改变行为）
- ✅ 更新安全模式

**何时跳过**：
- ❌ Bug 修复（恢复预期行为）
- ❌ 代码格式、注释调整
- ❌ 非破坏性的依赖更新
- ❌ 配置变更
- ❌ 现有功能的测试

#### 阶段 1 的输出物

```
openspec/changes/[change-id]/
├── proposal.md              # 为什么要做这个变更
├── design.md                # 技术决策（如果复杂）
├── tasks.md                 # 实现任务检查清单
├── README.md                # 快速指南（可选）
└── specs/                   # 需求变更（delta）
    └── [capability]/
        └── spec.md          # ADDED/MODIFIED/REMOVED 需求
```

#### 阶段 1 的工作流

```
1. 理解现状
   ├─ 阅读 openspec/project.md（项目约定）
   ├─ 运行 openspec list（查看活跃变更）
   └─ 运行 openspec list --specs（查看现有规格）

2. 设计变更
   ├─ 选择唯一的 change-id（kebab-case，动词开头）
   ├─ 创建目录结构
   ├─ 编写 proposal.md（Why, What, Impact）
   ├─ 编写 design.md（技术决策）
   └─ 编写 tasks.md（实现任务）

3. 编写规格
   ├─ 确定受影响的功能（capability）
   ├─ 编写 spec.md delta（ADDED/MODIFIED/REMOVED）
   ├─ 每个需求至少一个场景（Scenario）
   └─ 使用 WHEN/THEN 格式描述

4. 验证和提交
   ├─ 运行 openspec validate [change-id] --strict
   ├─ 解决所有验证错误
   ├─ 请求审批（不要开始实现！）
   └─ 等待批准
```

**示例：我刚才创建的两个变更提案**

```bash
# 第一个提案
openspec/changes/add-control-plan-management/
├── proposal.md        # 为什么需要方案管理功能
├── design.md          # 方案数据模型、XML生成设计
├── tasks.md           # 50+个具体任务
└── specs/control-plans/spec.md

# 第二个提案
openspec/changes/update-strategy-templates-sumo-verified/
├── proposal.md        # 基于SUMO验证的模板更新
├── design.md          # 单位转换、参数验证设计
├── tasks.md           # 模板更新 + 后端 + 前端任务
└── specs/strategy-templates/spec.md
```

---

### 🟡 Stage 2: 实现变更（Implementing Changes）

**前置条件**：
- ✅ 提案已被审批
- ✅ 理解了 proposal 的目标
- ✅ 准备好开始编码

#### 阶段 2 的步骤

```
1. 准备工作
   ├─ 阅读 proposal.md（理解目标）
   ├─ 阅读 design.md（理解技术方案）
   └─ 阅读 tasks.md（获取任务清单）

2. 实现任务（按顺序）
   ├─ 创建新文件/模块（如需要）
   ├─ 实现第一个任务
   ├─ 编写单元测试
   ├─ 运行测试验证
   ├─ 标记任务完成 [x]
   └─ 重复以上步骤直到所有任务完成

3. 代码质量检查
   ├─ black code_path/  （代码格式化）
   ├─ flake8 code_path/  （代码检查）
   ├─ pytest            （运行测试）
   └─ 确保 >90% 覆盖率

4. 最终验证
   ├─ 所有任务 [x] 标记完成
   ├─ 所有测试通过
   ├─ 代码审查通过
   └─ 无 linting 警告
```

#### 在这个阶段我的角色

我会：
1. **逐个实现任务** - 按 tasks.md 顺序完成
2. **跟踪进度** - 使用 TodoWrite 工具维护检查清单
3. **写测试** - 每个功能都有对应的测试
4. **代码审查** - 确保质量标准
5. **提供反馈** - 遇到问题立即报告

你可以：
1. **监督进度** - 查看完成的任务
2. **审查代码** - 在 git 提交中查看
3. **提出调整** - 如果需求有变化
4. **合并代码** - 当完成时集成到主分支

---

### 🔵 Stage 3: 归档变更（Archiving Changes）

**触发条件**：
- ✅ 所有代码已编写
- ✅ 所有测试已通过
- ✅ 已部署到生产环境
- ✅ 需要从 `changes/` 移到 `changes/archive/`

#### 阶段 3 的步骤

```
1. 准备归档
   ├─ 确认所有功能已完成
   ├─ 运行最终测试
   └─ 代码已合并到主分支

2. 更新主规格
   ├─ 复制 changes/[id]/specs/[cap]/spec.md
   ├─ 粘贴到 openspec/specs/[cap]/spec.md
   ├─ 归并 ADDED/MODIFIED 需求到主规格
   └─ 删除已完成的 REMOVED 需求

3. 执行归档
   ├─ 运行 openspec archive [change-id] --yes
   │  （或使用 --skip-specs 仅进行工具更新）
   ├─ 验证：openspec validate --strict
   └─ 变更移到 changes/archive/YYYY-MM-DD-[id]/

4. 创建归档提交
   ├─ git add openspec/changes/archive/
   ├─ git add openspec/specs/
   ├─ git commit -m "Archive: [change-id] - [Description]"
   └─ git push
```

**示例**：
```bash
# 待实现（现在的状态）
openspec/changes/add-control-plan-management/
                 ↓
                 （实现完成）
                 ↓
# 已归档（完成后）
openspec/changes/archive/2025-10-24-add-control-plan-management/
openspec/specs/control-plans/spec.md（更新）
```

---

## 我们如何协作

### 💬 沟通模式

#### 场景 1：你有一个新想法

```
你：
"我想添加一个新的分析功能，用来计算交通流量变化率"

我：
1. 提出澄清问题（如果需要）
2. 创建 OpenSpec 提案
   - proposal.md（为什么需要）
   - design.md（如何实现）
   - tasks.md（具体任务）
   - spec.md（需求+场景）
3. 展示给你审批

你：
- 审查提案
- 提意见修改
- 批准后通知我

我：
- 按 tasks.md 逐个实现
- 每个重要里程碑汇报进度
- 遇到问题立即沟通
```

#### 场景 2：你想优化现有功能

```
你：
"Phase 1B 的边选择器性能可以进一步优化吗？"

我：
1. 分析现有代码和性能瓶颈
2. 创建优化提案
   - 描述性能问题（当前 vs 目标）
   - 提出具体优化方案
   - 估计工作量和影响
3. 向你展示提案

你：
- 评估优化价值
- 决定是否进行
- 批准或打回

我：
- 实现优化
- 验证性能改进
- 完成测试
```

#### 场景 3：实现过程中遇到问题

```
我：
"在实现参数验证时，发现需要修改数据模型结构。
这会影响现有策略实例的兼容性。建议：
1. 版本化数据模型（v1.0 vs v2.0）
2. 迁移脚本转换旧数据
或者
3. 完全向后兼容（保留旧字段）

请选择或提出其他方案。"

你：
- 了解影响范围
- 提出决策
- 我继续实现
```

### 📊 进度追踪

我会使用 **TodoWrite 工具** 维护任务进度：

```markdown
## 任务清单

- [x] 1.1 创建数据模型
- [x] 1.2 实现API端点
- [ ] 1.3 添加前端组件      ← 当前工作
- [ ] 1.4 编写测试
- [ ] 2.1 代码格式化
- [ ] 2.2 性能测试
```

你可以随时：
- 查看当前完成的任务
- 了解下一步计划
- 提出优先级调整

### 🗂️ 代码组织

每个变更对应一个 git 分支和 PR：

```bash
# 我的工作分支
git checkout -b add-control-plan-management

# 定期提交，与你讨论
git commit -m "task: 1.1 Create Plan data model"
git commit -m "task: 1.2 Implement plan service"
git commit -m "task: 1.3 Add API routes"

# 完成后
git push origin add-control-plan-management
# → 创建 Pull Request，请求审查
```

---

## 常见场景和流程

### 📌 场景 1：添加全新功能（如 Phase 2）

```
用户说：
"我想要方案管理功能，用户可以组合多个策略成为一个方案"

工作流：
1. 我创建 OpenSpec 提案 (update-strategy-templates-sumo-verified)
   ├─ Proposal：说明为什么需要此功能
   ├─ Design：展示架构设计
   ├─ Tasks：列出 50+ 个具体任务
   └─ Spec：定义 30+ 个需求和场景

2. 你审查提案
   ├─ 修改建议？告诉我
   ├─ 优先级调整？告诉我
   └─ 批准？我开始实现

3. 我实现功能
   ├─ 后端（3-4 天）
   │  ├─ 数据模型
   │  ├─ 服务层
   │  ├─ API 路由
   │  └─ 单元测试
   ├─ 前端（2-3 天）
   │  ├─ 组件开发
   │  ├─ 表单验证
   │  └─ E2E 测试
   └─ 集成（1-2 天）
      ├─ 集成测试
      ├─ 代码审查
      └─ 文档更新

4. 完成后
   ├─ 所有测试通过
   ├─ 代码审查通过
   ├─ 合并到 main
   └─ 归档 OpenSpec 变更
```

**时间线**：7-9 天（取决于复杂度）

### 📌 场景 2：增强现有功能（如 Phase 1C 优化）

```
用户说：
"能否改进策略参数配置 UI，支持实时验证和 XML 预览？"

工作流：
1. 我创建小规模提案
   ├─ Proposal：当前痛点 + 改进方案
   ├─ Design：参数验证流程 + XML 生成
   ├─ Tasks：前后端任务（20-30 个）
   └─ Spec：4-5 个新需求

2. 你批准

3. 我实现
   ├─ 后端验证模块（1 天）
   ├─ 前端表单生成（1.5 天）
   ├─ XML 预览功能（0.5 天）
   └─ 测试（1 天）

4. 完成
```

**时间线**：3-4 天

### 📌 场景 3：修复 Bug（不需要 OpenSpec）

```
用户说：
"策略删除时没有正确清理文件"

我直接：
1. 识别问题位置
2. 修复代码
3. 添加测试
4. 创建 PR（引用 issue）
5. 合并到 main

无需 OpenSpec 流程（这是 Bug 修复，不是新功能）
```

**时间线**：<1 天

---

## 最佳实践

### ✅ 做什么

1. **创建清晰的提案**
   ```
   好：提案明确说明目标、技术方案、预期收益
   坏：模糊的描述，缺少具体需求
   ```

2. **详细的任务分解**
   ```
   好：每个任务 <2 小时工作量，有清晰的验收标准
   坏：笼统的任务如"实现整个系统"
   ```

3. **完整的场景定义**
   ```
   好：每个需求有 WHEN/THEN 格式的场景
   坏：只有需求名称，没有验收标准
   ```

4. **频繁的沟通**
   ```
   好：遇到问题立即报告，讨论解决方案
   坏：做到一半才发现思路错了
   ```

5. **及时的审查反馈**
   ```
   好：提案完成后 24 小时内审查
   坏：提案悬挂很久没有反馈
   ```

### ❌ 不要做什么

1. **不要跳过 Stage 1**
   ```
   错误：直接开始编码而不写提案
   正确：先写提案，获得批准，再编码
   ```

2. **不要混淆目的和实现**
   ```
   错误：Proposal 详细描述每行代码
   正确：Proposal 解释"为什么"和"什么"，不涉及"怎么样"
   ```

3. **不要忽略验证**
   ```
   错误：跳过 openspec validate 检查
   正确：运行 openspec validate --strict 确保完整性
   ```

4. **不要修改已审批的提案**
   ```
   错误：实现中修改需求
   正确：如需修改，创建新的变更提案
   ```

5. **不要忽视向后兼容性**
   ```
   错误：破坏现有 API 或数据格式
   正确：考虑迁移路径和兼容性策略
   ```

---

## 当前项目状态

### 🟢 已完成（Phase 1）

- ✅ Phase 1A：策略模板系统
- ✅ Phase 1B：数据库驱动边选择器
- ✅ Phase 1C：策略配置与 CRUD

### 🟡 草稿阶段（需要批准）

```
openspec/changes/add-control-plan-management/
  状态：Draft - 等待审批
  时间线：1-2 周（后端 3-4 天 + 前端 2-3 天）

openspec/changes/update-strategy-templates-sumo-verified/
  状态：Draft - 等待审批
  时间线：1-2 周（模板 1 天 + 后端 2 天 + 前端 2 天）
```

### 🔵 未开始

- Phase 2：方案管理（等待 template 更新完成）
- Phase 3：批量仿真
- Phase 4：方案优化

---

## 如何开始

### 对于提案审批

```
1. 打开 openspec/changes/[change-id]/README.md
2. 了解概述和关键决策
3. 如需深入了解，阅读 proposal.md 和 design.md
4. 查看 spec.md 中的具体需求
5. 提供反馈或批准
```

### 对于开始实现

```
1. 我获得批准后
2. 创建功能分支（如 git checkout -b add-control-plan-management）
3. 按 tasks.md 逐个完成任务
4. 定期 commit 和 push
5. 完成后创建 Pull Request
6. 你审查和合并
```

### 对于跟踪进度

```
1. 查看最新的 git commits
2. 查看打开的 Pull Request
3. 与我沟通了解细节
```

---

## 总结：三阶段快速参考

| 阶段 | 责任 | 输出 | 关键步骤 |
|------|------|------|---------|
| **Stage 1: 提案** | 我草稿，你审批 | proposal.md, design.md, tasks.md, spec.md | 创建 → 验证 → 请求审批 |
| **Stage 2: 实现** | 我编码，你监督 | 功能代码、测试、PR | 逐任务实现 → 测试 → 审查 |
| **Stage 3: 归档** | 我负责，你合并 | 归档变更、更新主规格 | 部署 → 更新 specs/ → 归档 |

---

## 问题？

- **我应该什么时候创建提案？**
  → 添加功能、破坏性改变、架构改变时创建。Bug 修复、注释调整、依赖更新不需要。

- **提案需要多久才能开始实现？**
  → 等待你批准。建议你 24 小时内审查。

- **如果实现中发现问题怎么办？**
  → 立即告诉你，讨论解决方案。不要自行修改需求。

- **如何追踪进度？**
  → 查看 git commits、查看 TodoWrite 任务清单、查看 Pull Request。

- **完成后怎么做？**
  → 创建 PR → 代码审查 → 合并 → 归档 OpenSpec 变更。

---

希望这个指南能帮助我们更有效地协作！有任何问题，请随时问我。🚀
