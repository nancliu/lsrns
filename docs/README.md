# OD_SIM 项目文档目录

本目录包含OD数据处理与仿真系统的各类文档。

## 📁 目录结构

### 🚦 [`control_strategies/`](control_strategies/) - 控制策略配置文档
**最常用** | 基于真实数据的交通控制策略分析、配置和实施文档

包含文档：
- 真实策略生成指南.md - 策略设计方法论
- 真实数据分析与策略建议_G4202_G5综合.md - G4202/G5路线分析
- TAZ边缘映射_TEC策略配置指南.md - TEC策略技术配置
- TEC边缘验证报告.md - 边缘ID技术验证
- README.md - 详细的文档索引和使用指南

**适用人群**: 策略设计人员、实施工程师、数据分析师

---

### 📖 [`api_docs/`](api_docs/) - API接口文档
新架构API使用指南和端点说明

主要文档：
- 新架构API指南.md - 完整的API使用文档
- 各业务模块的API端点说明

**适用人群**: 前端开发人员、API用户

---

### 🏗️ [`design/`](design/) - 设计文档
系统设计、需求分析、架构设计文档

包含：
- 功能设计文档
- 系统架构设计
- OpenSpec变更提案
- 策略工作流设计

**适用人群**: 系统架构师、产品经理、设计人员

---

### 💻 [`development/`](development/) - 开发指南
开发规范、架构说明、实施指南

主要文档：
- 新架构开发指南.md - 开发规范和最佳实践
- 架构重构完成报告.md - 架构演进历史

**适用人群**: 后端开发人员、新加入团队成员

---

### 🗄️ [`data_in_db/`](data_in_db/) - 数据库文档
数据库schema说明、数据字典、查询示例

**适用人群**: 数据库管理员、数据分析师

---

### 📊 [`performance/`](performance/) - 性能分析
系统性能测试、优化建议、基准测试结果

**适用人群**: 性能工程师、运维人员

---

### 🧪 [`testing/`](testing/) - 测试文档
测试计划、测试用例、Playwright E2E测试文档

主要文档：
- Playwright_MCP_测试任务清单.md - E2E测试任务

**适用人群**: QA工程师、测试人员

---

## 🔥 快速导航

### 我想...

#### 实施交通控制策略
→ [`control_strategies/README.md`](control_strategies/README.md) - 从这里开始

#### 调用API接口
→ [`api_docs/新架构API指南.md`](api_docs/新架构API指南.md)

#### 理解系统架构
→ [`development/新架构开发指南.md`](development/新架构开发指南.md)

#### 部署系统
→ [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md)

#### 查看设计文档
→ [`design/`](design/) 目录

---

## 📝 根目录重要文档

### DEPLOYMENT_GUIDE.md
系统部署指南，包含环境配置、依赖安装、启动步骤

### DOCUMENT_STATUS_v0.6.md
文档状态跟踪（v0.6版本）

### 策略相关文档
- control_progress_report.md - 控制功能进度报告
- TEC_OPTIMIZATION_SUMMARY.md - TEC优化总结
- VSS_ANALYSIS_REPORT.md - VSS分析报告
- bugfix_array_parameters.md - 数组参数修复说明

---

## 🎯 按角色推荐阅读

### 策略设计人员
1. [`control_strategies/真实策略生成指南.md`](control_strategies/真实策略生成指南.md)
2. [`control_strategies/真实数据分析与策略建议_G4202_G5综合.md`](control_strategies/真实数据分析与策略建议_G4202_G5综合.md)
3. [`design/traffic_control_optimization_overview.md`](design/traffic_control_optimization_overview.md)

### 开发人员
1. [`development/新架构开发指南.md`](development/新架构开发指南.md)
2. [`api_docs/新架构API指南.md`](api_docs/新架构API指南.md)
3. [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md)

### 数据分析师
1. [`control_strategies/真实数据分析与策略建议_G4202_G5综合.md`](control_strategies/真实数据分析与策略建议_G4202_G5综合.md)
2. [`data_in_db/`](data_in_db/) - 数据库文档
3. [`control_strategies/真实策略生成指南.md`](control_strategies/真实策略生成指南.md)

### QA测试人员
1. [`testing/Playwright_MCP_测试任务清单.md`](testing/Playwright_MCP_测试任务清单.md)
2. [`control_strategies/TEC边缘验证报告.md`](control_strategies/TEC边缘验证报告.md)
3. [`api_docs/新架构API指南.md`](api_docs/新架构API指南.md)

---

## 📌 文档维护

- **文档版本**: 以各文档内部标注为准
- **最后更新**: 2025-10-26
- **维护负责**: 项目团队

如有文档问题或改进建议，请联系项目维护者。
