# 事件场景库（Event Scenario Library）

## 简介

事件场景库是一套基于真实交通事件数据的SUMO仿真场景集合，包含18+个代表性交通事件和多种控制策略的组合。该库支持快速评估不同控制策略在真实事件下的有效性。

## 核心功能

### 1. 场景浏览与筛选
- 按事件类型（交通事故、交通管制、交通阻塞等）筛选
- 按控制策略（VSS、DHS、TEC）筛选
- 关键字搜索
- 实时预览场景详情

### 2. 快速创建案例
- 从事件场景快速创建SUMO仿真案例
- 自动填充事件信息和控制参数
- 支持自定义案例名称和描述

### 3. 仿真执行
- 运行事件相关的SUMO仿真
- 对比事件前后的交通状态
- 评估控制策略效果

## 快速开始

### 第一步：生成场景库

```bash
cd /d/projects/OD_SIM
python scripts/generate_scenarios_from_events.py
```

预期输出：
- 18个事件 × 3个策略 = 54个场景
- 生成时间：~8-10分钟
- 输出目录：`output/scenarios/`

### 第二步：浏览场景

打开浏览器访问：
```
http://localhost:8000/control/scenario_browser.html
```

功能：
- 查看所有生成的场景
- 按事件类型和策略筛选
- 查看事件详情和时间范围

### 第三步：创建案例并运行仿真

1. 在场景浏览器中点击"创建案例"
2. 填写案例信息（名称、网络文件、OD数据）
3. 系统自动关联事件场景
4. 在案例详情中运行仿真

## 目录结构

```
docs/scenarios_library/
├── README.md                           # 本文件
├── SCENARIO_GENERATION_GUIDE.md        # 场景生成完整指南
├── SCENARIO_LIBRARY_README.md          # 库使用指南
├── SCENARIO_XML_REFERENCE.md           # XML格式参考
├── PROJECT_WORKFLOW.md                 # 项目工作流（已更新）
├── 事件数据字段说明.csv                # 事件数据说明
└── 典型场景集成果总结.md              # 集成测试结果

frontend/control/
├── scenario_browser.html               # 场景浏览UI
└── js/scenario_browser.js             # 浏览器脚本

api/
├── routes/case_routes.py              # 案例创建API
└── routes/simulation_routes.py        # 仿真执行API

shared/control_tools/
├── event_injector.py                  # 事件注入模块
├── scenario_generator.py              # 场景生成模块
└── scenario_sumocfg_generator.py      # SUMO配置生成

scripts/
└── generate_scenarios_from_events.py   # 批量生成脚本

output/scenarios/                       # 生成的场景库
├── 01_交通事故/
│   ├── scenario_12547_vss/
│   │   ├── scenario_交通事故_vss_12547.add.xml
│   │   ├── event_description.json
│   │   ├── traffic_input_config.json
│   │   ├── control_strategy_config.json
│   │   └── simulation.sumocfg
│   └── ...
└── scenario_index.json
```

## 支持的事件类型

| 事件类型 | 代码 | 目录名 | 数据源 | 数量 |
|---------|------|--------|--------|------|
| 交通事故 | ACCIDENT | 01_交通事故 | CSV | 5+ |
| 交通管制 | CONTROL | 03_交通管制 | CSV | 3+ |
| 交通阻塞 | CONGESTION | 02_交通阻塞_流量激增 | CSV | 3+ |
| 地质灾害 | GEOLOGICAL | 04_地质灾害 | CSV | 1+ |
| 车辆故障 | BREAKDOWN | 05_车辆故障 | CSV | 1+ |
| 恶劣天气 | WEATHER | 06_恶劣天气 | CSV | 1+ |

## 支持的控制策略

### VSS（可变限速 / Variable Speed Sign）

**原理**：通过可变限速标志动态调整速度限制

**参数**：
- 限速范围：50-70 km/h
- 响应延迟：300秒（5分钟）
- 恢复期：600秒（10分钟）

**适用场景**：所有交通事件

**效果示例**：
```
基线：80 km/h → VSS激活：60 km/h → 事件结束：80 km/h
```

### DHS（动态硬路肩 / Dynamic Hard Shoulder）

**原理**：开放应急车道/硬路肩增加通行容量

**参数**：
- 开放条件：应急车道未被事件占用
- 响应延迟：300秒
- 恢复期：600秒

**适用场景**：主车道被占用的事件

**效果示例**：
```
正常：2条主车道 → DHS激活：2条主车道 + 硬路肩 → 恢复：2条主车道
```

### TEC（收费站控制 / Toll Entrance Control）

**原理**：限制收费站入口流量缓解拥堵

**模式**：
- **模式1**（优先）：使用CSV中的实际收费站数据（管控收费站）
- **模式2**（备选）：根据事件严重程度计算流量控制系数（0.2-0.8）

**参数**：
- 流量缩减：0.2（轻度） ~ 0.8（重度）
- 响应延迟：300秒
- 恢复期：600秒

**适用场景**：需要源头控制的拥堵事件

## 数据规范

### 事件数据来源

- **数据源**：`events/all_extracted_events.csv`
- **总事件数**：399条
- **选择标准**：
  - 时长：0.5-3小时（最优1-2小时）
  - 完整性：包含必需字段（edge_id, lanes, time等）
  - 多样性：地理分布均匀，事件类型多元

### 关键字段

| 字段名 | 说明 | 用途 |
|--------|------|------|
| report_id | 事件报告ID | 场景唯一标识 |
| 类型 | 事件类型（交通事故等） | 目录分类 |
| edge_id | SUMO网络中的edge ID | 空间定位 |
| 占用车道情况 | 被占用的车道列表 | 生成closedLane |
| 开始时间 | 事件开始时间 | OD时间范围计算 |
| 结束时间 | 事件结束时间 | OD时间范围计算 |

### OD时间范围规则

```
OD_start = event_start - 30分钟  （捕捉基线交通）
OD_end = event_end + 30分钟      （观察恢复）

示例：
事件时间：08:00 - 09:00
OD时间：07:30 - 09:30（共2.5小时）
```

## API接口速查表

### 场景浏览

```
GET /output/scenarios/scenario_index.json
```

获取所有场景索引，支持前端筛选和搜索。

### 快速创建案例

```
POST /api/v1/case/quick-create-from-event
{
  "case_name": "string",
  "event_type": "string",
  "strategy": "string",
  "scenario_id": "string",
  "network_file": "string",
  "od_file": "string",
  "taz_file": "string (optional)",
  "description": "string (optional)"
}
```

### 运行事件相关仿真

```
POST /api/v1/simulation/start-with-event/
{
  "case_id": "string",
  "scenario_id": "string",
  "gui": boolean
}
```

## 常见问题

### Q1: 如何自定义控制策略参数？

编辑 `scripts/generate_scenarios_from_events.py` 中的 `map_event_to_strategies()` 函数。

示例：修改VSS限速为50 km/h

```python
"speed_limit_kmh": 50,  # 默认60，改为50
```

### Q2: 如何添加新的事件类型？

1. 在 `event_injector.py` 中创建新的Injector子类
2. 在 `create_event_injector()` 工厂函数中注册
3. 更新 `scripts/generate_scenarios_from_events.py` 中的映射逻辑

### Q3: 为什么有些场景生成失败？

常见原因：
- **Missing edge_id**：事件数据不完整
- **Unknown lane description**：车道描述不在支持列表中
- **Network file not found**：SUMO网络文件不存在

查看日志获取具体错误信息。

### Q4: OD数据在哪里获取？

选项：
1. 使用默认OD表：`baseline.od_data_sichuan_202507`
2. 指定本地OD文件路径：`/path/to/od_data.xml`
3. 使用数据库连接：`database.schema.table_name`

### Q5: 如何对比事件前后的交通状态？

创建两个案例：
1. **基准案例**（Baseline）：同一时段，无事件
2. **事件案例**（With Event）：使用event scenario

然后对比两个仿真结果。

## 性能指标

### 生成性能

| 参数 | 数值 |
|------|------|
| 18个事件生成时间 | ~8-10分钟 |
| 输出文件数量 | ~200个文件 |
| 输出目录大小 | ~200 KB |

### 仿真性能

| 参数 | 数值 |
|------|------|
| 单场景仿真时间 | 2-5分钟（取决于OD数据量） |
| 内存占用 | 500 MB - 1 GB |
| 磁盘占用（结果） | 10-50 MB（取决于输出配置） |

## 故障排除

### 生成过程卡顿

**现象**：脚本运行超过15分钟

**原因**：可能是网络文件加载慢或系统资源不足

**解决**：
```bash
# 查看资源占用
top

# 减少生成数量
python scripts/generate_scenarios_from_events.py --target-events 10
```

### 仿真失败 - "SUMO not found"

**原因**：SUMO未正确安装或未配置环境变量

**解决**：
```bash
export SUMO_HOME=/path/to/sumo
export PATH=$SUMO_HOME/bin:$PATH
```

### 文件权限错误

**现象**：Permission denied when creating directories

**原因**：输出目录无写入权限

**解决**：
```bash
chmod 755 output/
```

## 下一步

1. **浏览场景**：访问 `scenario_browser.html`
2. **生成更多场景**：调整筛选条件和策略参数
3. **运行仿真**：创建案例并执行仿真
4. **分析结果**：对比不同策略的效果
5. **优化参数**：基于结果反复调整控制参数

## 相关文档

- 📖 **生成指南**：`SCENARIO_GENERATION_GUIDE.md` - 详细的生成流程和参数说明
- 📖 **XML参考**：`SCENARIO_XML_REFERENCE.md` - XML格式详细说明
- 📖 **API文档**：`docs/api/event_scenario_api.md` - API端点和数据模型
- 📖 **工作流**：`PROJECT_WORKFLOW.md` - 项目整体工作流程

## 贡献

如有建议或问题，请：
1. 查阅相关文档
2. 检查常见问题部分
3. 查看日志获取错误详情
4. 提交issue或PR

## 许可证

本项目遵循项目主许可证。详见根目录 LICENSE 文件。

---

**最后更新**：2025-11-11
**维护者**：交通仿真团队
**版本**：1.0.0
