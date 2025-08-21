# OD系统API文档

## 📋 概述

本文档提供了OD数据处理与仿真系统的完整API参考。系统采用完全模块化的架构设计，按业务领域组织API端点，提供清晰、易用的接口。

## 🏗️ 架构特点

### 1. 模块化设计
- **API层** (`api/`) - 专注于请求/响应处理和业务协调
- **共享层** (`shared/`) - 包含核心业务逻辑、算法和数据访问
- 清晰的职责分离，提高代码可维护性

### 2. 业务分组
- **数据处理组** - OD数据处理相关API
- **仿真管理组** - 仿真运行和管理API
- **案例管理组** - 案例CRUD操作API
- **分析结果组** - 结果分析和查看API
- **模板管理组** - 模板资源管理API
- **文件管理组** - 文件操作相关API

### 3. 统一标准
- 一致的请求/响应格式
- 统一的错误处理机制
- 标准化的状态码和消息

## 📚 文档结构

### 核心文档
- **[新架构API指南](新架构API指南.md)** - 完整的API参考和开发指南
- **[API变更日志](API变更日志.md)** - API版本变更记录

### 相关文档
- **[架构重构完成报告](../development/架构重构完成报告.md)** - 系统架构重构详情
- **[新架构开发指南](../development/新架构开发指南.md)** - 开发者指南
- **[门架数据管理说明](../development/门架数据管理说明.md)** - 门架数据管理详情

## 🚀 快速开始

### 1. 环境要求
- Python 3.8+
- FastAPI
- PostgreSQL数据库

### 2. 启动服务
```bash
# 安装依赖
pip install -r requirements.txt

# 启动API服务
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 访问API文档
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 核心功能

### OD数据处理
```bash
# 处理OD数据并创建案例
POST /api/v1/data/process_od_data/
```

### 仿真管理
```bash
# 运行仿真
POST /api/v1/simulation/run_simulation/

# 获取仿真进度
GET /api/v1/simulation/simulation_progress/{case_id}
```

### 案例管理
```bash
# 列出所有案例
GET /api/v1/case/list_cases/

# 获取案例详情
GET /api/v1/case/case_detail/{case_id}
```

### 精度分析
```bash
# 执行精度分析
POST /api/v1/analysis/analyze_accuracy/

# 获取分析结果
GET /api/v1/analysis/analysis_results/{case_id}/{simulation_id}
```

## 📊 响应格式

### 成功响应
```json
{
  "success": true,
  "message": "操作成功",
  "data": {
    // 具体数据
  }
}
```

### 错误响应
```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "details": {
    // 错误详情
  }
}
```

## 🔐 认证与授权

当前版本支持基础认证，未来版本将支持JWT认证和角色权限管理。

## 📈 性能指标

- **响应时间**: 简单查询 < 100ms，复杂计算 < 2s
- **并发支持**: 多用户并发访问
- **数据量**: 支持大规模OD数据处理

## 🧪 测试

### 单元测试
```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/unit/services/

# 生成覆盖率报告
pytest --cov=api --cov-report=html
```

### API测试
```bash
# 使用内置测试客户端
python -m pytest tests/integration/ -v
```

## 🔄 版本管理

### 当前版本
- **v2.0.0** - 完全重构版本，采用模块化架构

### 版本策略
- 主版本号：重大架构变更
- 次版本号：新功能添加
- 修订版本号：Bug修复和性能优化

## 🚨 重要变更

### v2.0.0 重大变更
- ✅ 完成架构重构，实现完全模块化
- ✅ 移除向后兼容性，采用全新架构
- ✅ 优化API组织结构，按业务分组
- ✅ 提升开发体验和代码质量

## 🤝 贡献指南

### 报告问题
- 使用GitHub Issues报告Bug
- 提供详细的错误信息和复现步骤

### 功能建议
- 通过GitHub Discussions讨论新功能
- 提交Feature Request Issue

### 代码贡献
- Fork项目并创建功能分支
- 遵循代码风格指南
- 添加适当的测试和文档

## 📞 支持

### 获取帮助
- 查看[常见问题解答](../FAQ.md)
- 搜索现有Issues
- 创建新的Issue

### 联系方式
- 开发团队：dev-team@yourorg.com
- 项目维护者：maintainer@yourorg.com

## 📄 许可证

本项目采用MIT许可证，详见[LICENSE](../../LICENSE)文件。

---

*最后更新: 2025年1月19日*
*文档版本: v2.0.0* 