# 仿真引擎脚本定义说明文档

---

**文档版本信息**

- 文档版本：v1.0.0
- 最后更新时间：2024-07-09

**修改记录**

| 版本   | 日期       | 修改人 | 说明                         |
| ------ | ---------- | ------ | ---------------------------- |
| v1.0.0 | 2024-07-09 | XXX    | 初始版本，增加版本与修改记录 |

---

## 项目概述

本项目是一个基于FastAPI的交通仿真数据处理系统，主要功能是从PostgreSQL数据库中提取OD（Origin-Destination）数据，生成大规模路网交通仿真所需的配置文件，并支持运行仿真和精度验证。

## 项目结构

```
OD生成脚本0708/
├── DLLtest2025_6_3.py      # 主要的FastAPI服务器文件
├── accuracytest.py         # 仿真精度验证脚本
├── vehicle_types.json      # 车辆类型配置文件
├── TAZ_4.add.xml          # TAZ（交通分析区域）配置文件
├── E1_detector.add.xml     # 检测器配置文件
├── sichuan202503v5.net.xml # 仿真路网文件
├── README.md              # 本说明文档
└── run_*/                # 仿真运行任务配置目录
```

## 核心功能

### 1. OD数据处理服务 (DLLtest2025_6_3.py)

#### 主要特性

- **FastAPI Web服务**：提供RESTful API接口
- **数据库连接池**：使用PostgreSQL连接池管理数据库连接
- **时间分段处理**：支持将长时间段分割为多个小时间段处理
- **车辆类型映射**：支持多种车辆类型的分类和参数配置
- **配置文件生成**：自动生成路由文件(.rou.xml)和配置文件(.sumocfg)

#### API接口

##### 1. `/process_od_data/` (POST)

处理OD数据并生成仿真输入文件(修改后补充E1_detector.add.xml参数)

**请求参数**：

```json
{
    "start_time": "2024/08/22 16:00:00",
    "end_time": "2024/08/22 17:00:00",
    "schemas_name": "dwd",
    "table_name": "dwd_od_g4202",
    "taz_file": "TAZ_4.add.xml",
    "net_file": "sichuan202503v5.net.xml",
    "interval_minutes": 5,
    "enable_mesoscopic": false,
    "output_summary": true,
    "output_tripinfo": false,
    "output_vehroute": false,
    "output_fcd": false,
    "output_netstate": false,
    "output_emission": false
}
```

**响应**：

```json
{
    "run_folder": "run_20250708_143022",
    "od_file": "绝对路径/od文件.od.xml",
    "route_file": "绝对路径/路由文件.rou.xml",
    "sumocfg_file": "绝对路径/simulation.sumocfg"
}
```

##### 2. `/run_simulation/` (POST)

运行仿真

**请求参数**：

```json
{
    "run_folder": "run_20250708_143022",
    "od_file": "路径",
    "route_file": "路径", 
    "sumocfg_file": "路径"
}
```

#### 核心算法

1. **时间分段处理**：

   - 将用户指定的时间范围按指定间隔（默认5分钟）分割
   - 每个时间段独立查询数据库并处理
2. **OD数据筛选**：

   - 验证起点和终点是否在TAZ配置中存在
   - 过滤单向TAZ的无效OD对
   - 处理缺失的收费广场代码
3. **车辆流量计算**：

   - 按车辆类型统计OD对数量
   - 计算每小时车辆流量：`(车辆数 / 时间段秒数) * 3600`

### 2. 车辆类型配置 (vehicle_types.json)

定义了6种车辆类型，每种类型包含：

- **物理参数**：长度、最大速度、加速度、减速度
- **行为参数**：跟车模型、随机性参数
- **映射关系**：原始车辆ID到分类的映射

```json
{
  "vehicle_types": {
    "passenger_small": {
      "accel": 2.6,
      "decel": 4.5,
      "length": 5.0,
      "maxSpeed": 70.0,
      "valid_ids": ["k1", "k2"]
    }
  }
}
```

### 3. 精度验证脚本 (accuracytest.py)

#### 功能

- 读取仿真输出的检测器数据
- 从数据库获取真实观测数据
- 计算GEH（Geoffrey E. Havers）指标评估仿真精度

#### GEH指标计算

```python
GEH = sqrt(((E - V)^2) / ((E + V) / 2))
```

其中：E为仿真流量，V为观测流量

#### 使用方法

```bash
python accuracytest.py
```

## 环境配置

### 依赖包

```bash
pip install fastapi uvicorn psycopg2-binary pandas lxml
```

### 数据库配置

- **数据库**：PostgreSQL
- **主机**：10.149.235.123:5432
- **数据库名**：sdzg
- **用户名**：lsrns

## 使用指南

### 1. 启动服务

```bash
python DLLtest2025_6_3.py
```

服务将在 http://127.0.0.1:7999 启动

### 2. 处理OD数据

发送POST请求到 `/process_od_data/` 接口，系统将：

1. 从数据库查询指定时间段的OD数据
2. 按时间间隔分段处理
3. 生成路由文件和配置文件
4. 返回生成的文件路径

### 3. 运行仿真

使用返回的配置信息调用 `/run_simulation/` 接口运行仿真

### 4. 精度验证

仿真完成后运行 `accuracytest.py` 验证仿真精度

## 输出文件说明

### 生成的文件夹结构

```
run_YYYYMMDD_HHMMSS/
├── 表名_时间段.rou.xml      # 路由文件
├── 表名_时间段.od.xml       # OD矩阵文件
├── simulation.sumocfg       # 配置文件
└── [仿真输出文件]           # summary.xml, tripinfo.xml等
```

### 路由文件(.rou.xml)

包含：

- 车辆类型定义
- Flow元素定义（指定时间段的车辆流）

### 配置文件(.sumocfg)

包含：

- 输入文件路径
- 仿真时间设置
- 输出选项配置
- 中观仿真选项

## 注意事项

1. **数据库连接**：确保数据库服务可访问且表结构正确
2. **文件路径**：TAZ文件、检测器文件和路网文件需要在项目根目录
3. **时间格式**：使用 "YYYY/MM/DD HH:MM:SS" 格式
4. **车辆类型**：确保数据库中的vehicle_type字段值在配置文件中有对应映射
5. **内存使用**：大时间段处理可能消耗较多内存，建议适当调整时间间隔

## 故障排除

### 常见问题

1. **数据库连接失败**：检查网络连接和数据库配置
2. **TAZ ID不匹配**：确保数据库中的起点终点代码在TAZ文件中存在
3. **运行失败**：检查仿真引擎安装和文件路径
4. **内存不足**：减少时间间隔或分批处理

### 日志信息

系统会输出详细的处理日志，包括：

- 数据库查询状态
- 数据筛选结果
- 文件生成进度
- 错误信息

## 技术架构

- **Web框架**：FastAPI + Uvicorn
- **数据库**：PostgreSQL + psycopg2连接池
- **数据处理**：Pandas
- **XML处理**：xml.etree.ElementTree + minidom
- **并发处理**：支持CORS的异步API

## 相关文档

- [API文档](http://127.0.0.1:7999/docs) - FastAPI自动生成的交互式API文档
- [车辆类型配置说明](./vehicle_types.json) - 车辆参数配置文件
