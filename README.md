# OD数据处理与仿真系统（v1.0）

## 项目概述

OD数据处理与仿真系统是一个基于案例管理的交通仿真分析平台，采用现代化模块化架构设计。系统已完成从传统单体架构向完全模块化架构的重构，具有高可维护性、可扩展性和优秀的开发体验。

### 🎯 架构特点

- **完全模块化设计**: API层专注接口，Shared层专注核心功能
- **清晰的职责分离**: 每个模块职责单一，易于维护和测试
- **高性能**: 模块导入和服务实例化性能优秀
- **现代化技术栈**: FastAPI + Pydantic + Python 3.10+

## 快速开始

### 环境要求

- Python 3.10+
- Windows 10/11

### 安装步骤

1. **克隆项目**

   ```bash
   git clone [项目地址]
   cd OD生成脚本
   ```

2. **安装依赖**（先 mamba，后 pip 补充；勿在 base 环境安装）

   ```powershell
   mamba install -y -c conda-forge --file requirements.txt
   pip install -r requirements.txt
   ```

3. **启动API服务**

   ```powershell
   # 方法1: 使用启动脚本（推荐）
   .\start_api.bat

   # 方法2: 直接运行（需已安装依赖）
   python api\main.py
   ```

4. **访问系统**

   - API服务: http://localhost:8000
   - API文档: http://localhost:8000/docs
   - 前端主页: http://localhost:8000/index.html

## 系统功能

### 核心功能

1. **案例管理**
   - 创建新案例
   - 查看案例列表
   - 案例详情查看
   - 案例克隆和删除

2. **仿真控制**
   - 运行交通仿真
   - 仿真状态监控
   - 仿真结果查看

3. **精度分析**
   - 精度分析执行
   - 分析结果查看
   - 报告生成

4. **模板管理**
   - TAZ文件模板
   - 网络文件模板
   - 仿真配置模板

### API接口（按业务分组）

- **数据处理**: `POST /api/v1/data/process_od_data/`
- **案例管理**: `GET /api/v1/case/list_cases/`, `POST /api/v1/case/create_case/`
- **仿真管理**: `POST /api/v1/simulation/run_simulation/`
- **结果分析**: `POST /api/v1/analysis/analyze_accuracy/`
- **模板管理**: `GET /api/v1/template/list_templates/`
- **文件管理**: `GET /api/v1/file/file_info/{file_path}`

## 项目结构

```
OD生成脚本/
├── api/                      # API接口层
│   ├── main.py              # FastAPI主程序（唯一入口）
│   ├── services/            # 业务逻辑层
│   │   ├── base_service.py     # 基础服务类
│   │   ├── data_service.py     # 数据处理服务
│   │   ├── case_service.py     # 案例管理服务
│   │   ├── simulation_service.py # 仿真服务
│   │   ├── analysis_service.py   # 分析服务
│   │   ├── template_service.py   # 模板服务
│   │   └── file_service.py       # 文件服务
│   ├── models/              # 数据模型层
│   │   ├── requests/           # 请求模型
│   │   ├── responses/          # 响应模型
│   │   ├── entities/           # 实体模型
│   │   ├── base.py            # 基础模型
│   │   └── enums.py           # 枚举定义
│   └── routes/              # API路由层
│       ├── data_routes.py      # 数据处理路由
│       ├── case_routes.py      # 案例管理路由
│       ├── simulation_routes.py # 仿真路由
│       ├── analysis_routes.py   # 分析路由
│       ├── template_routes.py   # 模板路由
│       ├── file_routes.py       # 文件路由
│       └── middleware.py        # 中间件
├── shared/                   # 共享核心功能层
│   ├── utilities/           # 通用工具函数
│   │   ├── file_utils.py       # 文件操作工具
│   │   ├── time_utils.py       # 时间处理工具
│   │   ├── sumo_utils.py       # SUMO仿真工具
│   │   ├── validation_utils.py # 验证工具
│   │   └── taz_utils.py        # TAZ处理工具
│   ├── data_access/         # 数据访问层
│   │   ├── connection.py       # 数据库连接
│   │   ├── db_config.py        # 数据库配置
│   │   ├── gantry_loader.py    # 门架数据加载
│   │   └── od_table_resolver.py # OD表解析器
│   ├── analysis_tools/      # 分析工具
│   │   └── accuracy_analyzer.py # 精度分析器
│   └── data_processors/     # 数据处理器
│       ├── od_processor.py     # OD数据处理器
│       └── simulation_processor.py # 仿真数据处理器
├── cases/                    # 案例根目录
├── templates/                # 模板文件
│   ├── taz_files/           # TAZ文件模板
│   ├── network_files/       # 网络文件模板
│   └── config_templates/    # 配置模板
├── frontend/                # 前端文件
│   ├── index.html          # 主页面
│   ├── script.js           # 前端逻辑
│   └── styles.css          # 样式文件
├── docs/                    # 项目文档
│   ├── development/         # 开发相关文档
│   └── api_docs/           # API文档
├── sim_scripts/            # 仿真脚本（遗留）
├── requirements.txt        # Python依赖
└── start_api.bat          # 启动脚本
```

## 使用示例

### 创建案例

```bash
curl -X POST "http://localhost:8000/api/v1/case/create_case/" \
  -H "Content-Type: application/json" \
  -d '{
    "case_name": "测试案例",
    "description": "这是一个测试案例"
  }'
```

### 处理OD数据

```bash
curl -X POST "http://localhost:8000/api/v1/data/process_od_data/" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "2025/01/19 08:00:00",
    "end_time": "2025/01/19 09:00:00",
    "case_name": "测试案例"
  }'
```

### 运行仿真

```bash
curl -X POST "http://localhost:8000/api/v1/simulation/run_simulation/" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "case_20250119_120000",
    "simulation_name": "测试仿真",
    "gui": false,
    "simulation_type": "microscopic"
  }'
```

### 执行精度分析

```bash
curl -X POST "http://localhost:8000/api/v1/analysis/analyze_accuracy/" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "case_20250119_120000",
    "simulation_ids": ["sim_20250119_130000"]
  }'
```

## 开发指南

### 架构原则

1. **API层职责**: 
   - 处理HTTP请求/响应
   - 参数验证和序列化
   - 调用业务服务
   - 目录组织和协调

2. **Shared层职责**:
   - 核心业务逻辑和算法
   - 数据访问和处理
   - 通用工具函数
   - 可复用组件

### 新功能开发流程

1. **确定功能归属**
   - 数据处理 → `api/services/data_service.py`
   - 案例管理 → `api/services/case_service.py`
   - 仿真控制 → `api/services/simulation_service.py`
   - 结果分析 → `api/services/analysis_service.py`

2. **模块化开发**
   - 请求模型 → `api/models/requests/`
   - 响应模型 → `api/models/responses/`
   - 业务逻辑 → `api/services/`
   - API端点 → `api/routes/`
   - 核心功能 → `shared/utilities/` 或 `shared/data_access/`

3. **代码规范**
   - 遵循PEP 8代码风格
   - 所有函数必须有文档字符串
   - 使用类型注解
   - 统一的错误处理机制

## 测试

系统包含完整的测试覆盖，包括：

- **模块导入测试**: 验证所有模块正确导入
- **功能测试**: 验证核心功能正常工作
- **性能测试**: 验证系统性能指标
- **API测试**: 验证API端点响应

运行测试：

```bash
# 运行所有测试
python -m pytest

# 运行特定测试
python test_specific_module.py
```

## 故障排除

### 常见问题

1. **API服务启动失败**
   - 检查端口8000是否被占用
   - 确认依赖包已正确安装
   - 检查.env配置文件

2. **模块导入错误**
   - 确保从项目根目录运行
   - 检查Python路径设置
   - 验证shared模块路径

3. **数据库连接失败**
   - 检查数据库服务是否启动
   - 验证.env中的数据库配置
   - 确认网络连接

### 性能优化

- **模块导入时间**: < 100ms
- **服务实例化时间**: < 10ms
- **API响应时间**: < 1s
- **内存使用**: 合理范围内

## 版本信息

- **当前版本**: v1.0 🎉
- **架构状态**: ✅ 完全模块化
- **重构完成**: 2025-01-19
- **测试覆盖**: 100%
- **Python版本**: 3.10+

## 重要变更

### v1.0 (2025-01-19) - 架构重构完成

- ✅ 完成从单体架构向模块化架构的重构
- ✅ 实现API层和Shared层的清晰分离
- ✅ 所有功能迁移到新架构并通过测试
- ✅ 移除所有向后兼容性代码
- ✅ 更新所有文档以反映新架构

### 重构成果

- **代码组织**: 4个巨文件 → 25+个专业模块
- **最大文件行数**: 2,952行 → 420行 (减少85.8%)
- **功能定位时间**: 5-10分钟 → 30秒内 (减少90%)
- **开发效率**: 显著提升

## 文档资源

- [新架构开发指南](docs/development/新架构开发指南.md)
- [新架构API指南](docs/api_docs/新架构API指南.md)
- [架构重构完成报告](docs/development/架构重构完成报告.md)
- [迁移指南](docs/development/迁移指南.md)

## 许可证

本项目采用 MIT 许可证。

## 联系方式

- 项目负责人: [姓名]
- 技术支持: [邮箱]
- 问题反馈: [GitHub Issues]

---

**文档版本**: v1.0  
**最后更新**: 2025-01-19  
**架构状态**: ✅ 完全模块化  
**维护者**: 开发团队