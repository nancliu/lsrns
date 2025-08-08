# OD数据处理与仿真系统

## 项目概述

OD数据处理与仿真系统是一个基于案例管理的交通仿真分析平台，旨在解决当前系统中存在的文件夹管理混乱、数据流向不清晰、扩展性差等问题。

## 快速开始

### 环境要求

- Python 3.8+
- Windows 10/11

### 安装步骤

1. **克隆项目**
   ```bash
   git clone [项目地址]
   cd OD生成脚本
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **启动API服务**
   ```bash
   # 方法1: 使用启动脚本
   start_api.bat
   
   # 方法2: 直接运行
   python api/main.py
   ```

4. **访问系统**
   - API服务: http://localhost:8000
   - API文档: http://localhost:8000/docs
   - 前端界面: 打开 `frontend/index.html`

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

5. **工具功能**
   - TAZ文件验证
   - TAZ文件修复
   - TAZ文件比较

### API接口

系统提供16个核心API接口：

- **数据处理API** (3个): OD数据处理、仿真运行、精度分析
- **案例管理API** (5个): 案例的增删改查和克隆
- **文件管理API** (2个): 文件夹列表和分析状态
- **模板管理API** (3个): 各类模板的获取
- **工具API** (3个): TAZ文件相关工具

## 项目结构

```
OD生成脚本/
├── cases/                    # 案例根目录
├── templates/                # 模板文件
│   ├── taz_files/           # TAZ文件模板
│   ├── network_files/       # 网络文件模板
│   └── config_templates/    # 配置模板
├── shared/                  # 共享资源
│   ├── e1_detectors/       # E1检测器配置
│   ├── gantry_locations/   # 门架位置
│   ├── analysis_tools/     # 分析工具
│   ├── data_processors/    # 数据处理器
│   └── utilities/          # 通用工具
├── api/                     # API服务
│   ├── main.py             # FastAPI主程序
│   ├── models.py           # 数据模型
│   ├── routes.py           # API路由
│   ├── services.py         # 业务逻辑
│   ├── utils.py            # 工具函数
│   └── __init__.py         # 包初始化
├── frontend/               # 前端界面
│   ├── index.html          # 主页面
│   ├── styles.css          # 样式文件
│   └── script.js           # JavaScript逻辑
├── docs/                   # 文档
├── requirements.txt         # Python依赖
├── start_api.bat           # 启动脚本
└── test_api.py             # API测试脚本
```

## 使用示例

### 创建案例

```bash
curl -X POST "http://localhost:8000/api/v1/create_case/" \
  -H "Content-Type: application/json" \
  -d '{
    "time_range": {
      "start": "2025/07/21 08:00:00",
      "end": "2025/07/21 09:00:00"
    },
    "config": {},
    "case_name": "测试案例",
    "description": "这是一个测试案例"
  }'
```

### 获取案例列表

```bash
curl "http://localhost:8000/api/v1/list_cases/"
```

### 运行仿真

```bash
curl -X POST "http://localhost:8000/api/v1/run_simulation/" \
  -H "Content-Type: application/json" \
  -d '{
    "run_folder": "cases/case_20250108_120000/simulation",
    "gui": false,
    "simulation_type": "microscopic"
  }'
```

## 测试

运行API测试：

```bash
python test_api.py
```

## 开发

### 代码规范

- 遵循PEP 8代码风格
- 所有函数必须有文档字符串
- 使用类型注解
- 统一的错误处理机制

### 提交规范

- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 代码重构
- test: 测试相关
- chore: 构建过程或辅助工具的变动

## 故障排除

### 常见问题

1. **API服务启动失败**
   - 检查端口8000是否被占用
   - 确认依赖包已正确安装

2. **模块导入错误**
   - 确保从项目根目录运行
   - 检查Python路径设置

3. **编码问题**
   - 确保文件使用UTF-8编码
   - 避免在配置文件中使用中文注释

### 日志查看

- API日志: 控制台输出
- 错误信息: 查看控制台错误信息

## 版本信息

- **当前版本**: v1.0.0
- **发布日期**: 2025-01-08
- **Python版本**: 3.8+

## 许可证

本项目采用 MIT 许可证。

## 联系方式

- 项目负责人: [姓名]
- 技术支持: [邮箱]
- 问题反馈: [GitHub Issues]

---

**文档版本**: v1.0.0  
**最后更新**: 2025-01-08  
**维护者**: 开发团队 