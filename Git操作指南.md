# Git操作指南 - 工程结构优化项目

## 📋 **项目概述**

### **项目信息**
- **项目名称**: OD数据处理与仿真系统
- **开发模式**: 单人开发
- **Git策略**: 阶段Checkpoint + 主分支开发
- **远程仓库**: GitHub (lsrns/main)

### **当前状态**
- **当前分支**: main
- **最新提交**: ab17b87 - 更新工程结构优化设计方案和TODO清单
- **工作目录**: 干净状态

---

## 🎯 **Git操作策略**

### **核心原则**
1. **简单高效**: 单人开发，避免复杂分支管理
2. **阶段Checkpoint**: 每个阶段都有明确的保存点
3. **频繁提交**: 每完成小功能就提交
4. **及时推送**: 重要更改后立即推送到GitHub
5. **详细记录**: commit信息要详细描述完成内容

### **操作流程**
```
开始工作 → 完成小功能 → 提交 → 完成阶段 → 阶段Checkpoint → 推送 → 继续下一阶段
```

---

## 📋 **日常操作命令**

### **查看状态**
```bash
# 查看当前状态
git status

# 查看提交历史
git log --oneline -10

# 查看远程仓库信息
git remote -v
```

### **基本操作**
```bash
# 添加文件到暂存区
git add .

# 提交更改
git commit -m "描述：完成的具体内容"

# 推送到远程仓库
git push lsrns main

# 拉取最新更改
git pull lsrns main
```

### **查看历史**
```bash
# 查看最近10次提交
git log --oneline -10

# 查看某个文件的修改历史
git log --follow "文件名.md"

# 查看某个阶段的提交
git log --oneline --grep="阶段"
```

---

## 🚀 **阶段Checkpoint操作**

### **阶段1: 基础架构搭建**

#### **开始前**
```bash
# 创建阶段1开始checkpoint
git add .
git commit -m "阶段1开始：基础架构搭建 - 准备创建新目录结构"
git push lsrns main
```

#### **完成后**
```bash
# 创建阶段1完成checkpoint
git add .
git commit -m "阶段1完成：基础架构搭建
- 创建新的目录结构
- 实现基础API框架
- 迁移核心文件
- 建立模板管理机制"
git push lsrns main
```

### **阶段2: 数据迁移和兼容性**

#### **开始前**
```bash
# 创建阶段2开始checkpoint
git add .
git commit -m "阶段2开始：数据迁移和兼容性 - 准备迁移现有数据"
git push lsrns main
```

#### **完成后**
```bash
# 创建阶段2完成checkpoint
git add .
git commit -m "阶段2完成：数据迁移和兼容性
- 实现数据迁移工具
- 保持API兼容性
- 创建案例转换功能
- 实现新旧系统并行运行"
git push lsrns main
```

### **阶段3: 功能迁移和优化**

#### **开始前**
```bash
# 创建阶段3开始checkpoint
git add .
git commit -m "阶段3开始：功能迁移和优化 - 准备迁移核心功能"
git push lsrns main
```

#### **完成后**
```bash
# 创建阶段3完成checkpoint
git add .
git commit -m "阶段3完成：功能迁移和优化
- 迁移OD数据处理功能
- 迁移仿真运行功能
- 迁移精度分析功能
- 优化数据流向"
git push lsrns main
```

### **阶段4: 测试和优化**

#### **开始前**
```bash
# 创建阶段4开始checkpoint
git add .
git commit -m "阶段4开始：测试和优化 - 准备进行全面测试"
git push lsrns main
```

#### **完成后**
```bash
# 创建阶段4完成checkpoint
git add .
git commit -m "阶段4完成：测试和优化
- 完成功能测试
- 完成性能测试
- 完成文档完善
- 工程结构优化完成"
git push lsrns main
```

---

## 🔄 **恢复操作指南**

### **查看可恢复的版本**
```bash
# 查看所有提交历史
git log --oneline

# 查看详细提交信息
git show [commit ID]
```

### **恢复到某个阶段**
```bash
# 恢复到阶段1完成
git reset --hard [阶段1完成的commit ID]

# 恢复到阶段2完成
git reset --hard [阶段2完成的commit ID]

# 恢复到最新保存版本
git reset --hard ab17b87
```

### **恢复特定文件**
```bash
# 恢复特定文件到某个版本
git checkout [commit ID] -- "文件名"

# 恢复设计文档到最新版本
git checkout ab17b87 -- "工程结构优化设计方案.md"
git checkout ab17b87 -- "工程结构优化实施TODO清单.md"
```

### **紧急恢复**
```bash
# 如果出现严重问题，立即恢复到最新保存版本
git reset --hard ab17b87
git status
```

---

## 📊 **进度跟踪**

### **查看当前进度**
```bash
# 查看所有阶段checkpoint
git log --oneline --grep="阶段"

# 查看某个阶段的详细内容
git show [commit ID]

# 查看最近的工作
git log --oneline -10
```

### **创建进度报告**
```bash
# 查看某个文件的修改历史
git log --follow "工程结构优化实施TODO清单.md"

# 查看某个日期的提交
git log --oneline --since="2025-01-08"
```

---

## ⚠️ **重要提醒**

### **提交前检查**
```bash
# 检查当前状态
git status

# 检查要提交的文件
git diff --cached

# 检查工作目录的更改
git diff
```

### **推送前确认**
```bash
# 确认本地提交
git log --oneline -3

# 推送到远程
git push lsrns main

# 确认推送成功
git status
```

### **备份策略**
```bash
# 每日备份
git add .
git commit -m "日期: 2025-01-XX - 完成的任务描述"
git push lsrns main

# 重要节点备份
git add .
git commit -m "重要节点: 完成XXX功能
- 具体完成内容1
- 具体完成内容2
- 遇到的问题和解决方案"
git push lsrns main
```

---

## 💡 **最佳实践**

### **Commit信息规范**
```bash
# 好的commit信息示例
git commit -m "功能: 完成API路由重构
- 将DLLtest2025_6_3.py拆分为5个文件
- 实现main.py, models.py, routes.py, services.py, utils.py
- 保持原有功能完整性
- 解决导入路径问题"

# 阶段checkpoint示例
git commit -m "阶段1完成：基础架构搭建
- 创建api/目录结构
- 迁移核心业务逻辑
- 实现基础API框架
- 建立模板管理机制"
```

### **文件管理**
```bash
# 添加新文件
git add "新文件名.py"

# 删除文件
git rm "要删除的文件.py"

# 重命名文件
git mv "旧文件名.py" "新文件名.py"
```

### **问题处理**
```bash
# 如果提交信息写错了
git commit --amend -m "正确的提交信息"

# 如果推送到错误的分支
git push lsrns main --force

# 如果本地有未提交的更改但需要切换
git stash
git reset --hard [commit ID]
git stash pop
```

---

## 📞 **常用命令速查**

### **状态查看**
```bash
git status                    # 查看当前状态
git log --oneline -10        # 查看最近10次提交
git diff                     # 查看未暂存的更改
git diff --cached           # 查看已暂存的更改
```

### **文件操作**
```bash
git add .                    # 添加所有文件
git add "文件名"             # 添加特定文件
git rm "文件名"              # 删除文件
git mv "旧名" "新名"         # 重命名文件
```

### **提交操作**
```bash
git commit -m "信息"         # 提交更改
git commit --amend          # 修改最后一次提交
git push lsrns main         # 推送到远程
git pull lsrns main         # 拉取最新更改
```

### **恢复操作**
```bash
git reset --hard [commit]   # 恢复到指定提交
git checkout [commit] -- "文件" # 恢复特定文件
git log --oneline           # 查看提交历史
```

---

## 🎯 **项目特定操作**

### **当前项目状态**
```bash
# 查看当前状态
git status

# 查看最新提交
git log --oneline -1

# 查看远程仓库
git remote -v
```

### **开始实施前**
```bash
# 创建实施开始checkpoint
git add .
git commit -m "工程结构优化实施开始 - 基于设计方案v1.1"
git push lsrns main
```

### **每日工作流程**
```bash
# 开始工作前
git pull lsrns main

# 完成工作后
git add .
git commit -m "日期: 2025-01-XX - 完成的任务描述"
git push lsrns main
```

---

**文档版本**: v1.0
**创建日期**: 2025-01-08
**适用项目**: OD数据处理与仿真系统工程结构优化
**开发模式**: 单人开发
**Git策略**: 阶段Checkpoint + 主分支开发 