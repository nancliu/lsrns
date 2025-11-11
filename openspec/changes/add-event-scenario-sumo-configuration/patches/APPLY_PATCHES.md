# 如何应用架构更新补丁

**日期**: 2025-11-11
**状态**: 等待手动应用

---

## 📋 补丁文件清单

| 补丁文件 | 目标文件 | 位置 | 状态 |
|---------|---------|------|------|
| `01_tasks_md_header.patch` | `tasks.md` | Line ~7 (after Timeline) | ⏳ 待应用 |
| `02_tasks_md_architecture.patch` | `tasks.md` | Line ~1219 (Architecture section) | ⏳ 待应用 |
| `03_PROJECT_WORKFLOW_architecture.patch` | `docs/scenarios_library/PROJECT_WORKFLOW.md` | Line ~386 (场景分类体系) | ⏳ 待应用 |

---

## 🔧 手动应用步骤

### 方法1: 直接复制粘贴（推荐）

1. **打开目标文件** (如 `tasks.md`)
2. **打开对应补丁文件** (如 `01_tasks_md_header.patch`)
3. **找到补丁中标注的位置** (如"After line 7")
4. **复制补丁内容** (从`INSERT:`或`REPLACE:`后到`=== END PATCH ===`前)
5. **粘贴到目标文件的指定位置**
6. **保存文件**

### 方法2: 使用编辑器搜索

1. **在目标文件中搜索关键字** (补丁中的"Location"部分)
2. **定位到具体行**
3. **根据补丁类型**:
   - `INSERT:` → 在指定位置插入内容
   - `REPLACE:` → 替换从"REPLACE THIS SECTION"开始的内容
4. **保存文件**

---

## 📝 详细应用指南

### Patch 1: tasks.md Header

**目标**: 在Overview部分后添加架构更新通知

**步骤**:
1. 打开 `openspec/changes/add-event-scenario-sumo-configuration/tasks.md`
2. 找到第7行: `**Timeline**: 3-4 weeks (15-20 person-days)`
3. 在该行后面插入空行，然后粘贴补丁内容
4. 保存

**验证**: 应该看到标题 `## ⚠️ ARCHITECTURE UPDATE (2025-11-11)`

---

### Patch 2: tasks.md Architecture Section

**目标**: 更新架构图和数据流部分

**步骤**:
1. 打开 `tasks.md`
2. 搜索 `**Architecture: Option A - Separate Systems**`（大约在1219行）
3. 从该标题开始，替换整个架构图和数据流部分
4. 替换内容到下一个大标题（如`**2. Case Creation**`）之前
5. 粘贴补丁内容
6. 保存

**验证**:
- 应该看到 `✏️ **UPDATED 2025-11-11**`
- 目录名使用英文 (如 `01_accident/`)
- 文件名无中文 (如 `scenario_accident_vss_12547.add.xml`)

---

### Patch 3: PROJECT_WORKFLOW.md Architecture

**目标**: 更新中文文档的场景库结构

**步骤**:
1. 打开 `docs/scenarios_library/PROJECT_WORKFLOW.md`
2. 搜索 `### 场景分类体系`（大约在386行）
3. 从该标题下一行开始，替换原有的场景库结构图
4. 替换到 `### 场景元数据索引` 标题之前
5. 粘贴补丁内容
6. 保存

**验证**:
- 应该看到 `**⚠️ 架构更新 (2025-11-11)**:`
- 有事件类型英文映射表
- 目录结构使用英文名称

---

## ✅ 验证清单

应用所有补丁后，检查：

### tasks.md
- [ ] Overview部分后有架构更新通知
- [ ] 架构图使用英文目录名 (`01_accident/`)
- [ ] 文件名无中文 (`scenario_accident_vss_12547.add.xml`)
- [ ] 提到4种仿真类型
- [ ] 提到per-scenario metadata

### PROJECT_WORKFLOW.md
- [ ] 场景分类体系有架构更新通知（中文）
- [ ] 有事件类型英文映射表
- [ ] 场景库结构使用英文目录
- [ ] 说明了仿真执行在cases分支

---

## 🚀 完成后的下一步

1. **Commit更新**:
   ```bash
   git add openspec/changes/add-event-scenario-sumo-configuration/tasks.md
   git add docs/scenarios_library/PROJECT_WORKFLOW.md
   git commit -m "docs: Update architecture to move simulations to cases branch

   - Scenario library now read-only (no sumocfg/results)
   - Simulations moved to cases/xxx/simulations/
   - English-only filenames for SUMO compatibility
   - Per-scenario metadata files
   - Added no_control scenario type

   Refs: ARCHITECTURE_CHANGES.md"
   ```

2. **开始代码实施** (6小时):
   - Step 1: 文件命名更新 (1h)
   - Step 2: 元数据结构调整 (1h)
   - Step 3: Cases集成 (2h)
   - Step 4: SUMO配置相对路径 (1h)
   - Step 5: 测试更新 (1h)

---

## 📞 遇到问题？

如果应用补丁时遇到问题：

1. **位置找不到**: 使用搜索功能找关键字
2. **内容不匹配**: 文件可能已被修改，参考 `ARCHITECTURE_SUMMARY_ZH.md` 手动更新
3. **格式问题**: 注意保持Markdown格式（空行、缩进等）

---

**状态**: 📦 补丁包已准备就绪
**预计时间**: 30分钟手动应用所有补丁
