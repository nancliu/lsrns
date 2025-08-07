# 快速参考指南

## 🚀 快速开始

### 1. 启动服务
```bash
python DLLtest2025_6_3.py
```

### 2. 处理OD数据 (curl示例)
```bash
curl -X POST "http://127.0.0.1:7999/process_od_data/" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "2024/08/22 16:00:00",
    "end_time": "2024/08/22 17:00:00",
    "interval_minutes": 5
  }'
```

### 3. 运行仿真
```bash
curl -X POST "http://127.0.0.1:7999/run_simulation/" \
  -H "Content-Type: application/json" \
  -d '{
    "run_folder": "run_20250708_143022",
    "od_file": "路径",
    "route_file": "路径",
    "sumocfg_file": "路径"
  }'
```

## 📋 常用参数

### 时间格式
- **标准格式**: `"YYYY/MM/DD HH:MM:SS"`
- **示例**: `"2024/08/22 16:00:00"`

### 车辆类型映射
| 原始ID | 分类 | 描述 |
|--------|------|------|
| k1, k2 | passenger_small | 小型客车 |
| k3, k4 | passenger_large | 大型客车 |
| h1, h2 | truck_small | 小型货车 |
| h3-h6 | truck_large | 大型货车 |
| t1, t2 | special_small | 小型专用车 |
| t3-t6 | special_large | 大型专用车 |

### 输出选项
| 参数 | 默认值 | 说明 |
|------|--------|------|
| output_summary | true | 仿真总结 |
| output_tripinfo | false | 车辆行程信息 |
| output_vehroute | false | 车辆路径 |
| output_fcd | false | 浮动车数据 |
| output_netstate | false | 网络状态 |
| output_emission | false | 排放数据 |

## 🔧 故障排除

### 数据库连接问题
```python
# 检查连接
import psycopg2
conn = psycopg2.connect(
    dbname="sdzg",
    user="lsrns", 
    password="Abcd@1234",
    host="10.149.235.123",
    port="5432"
)
```

### SUMO路径问题
```bash
# 检查SUMO安装
sumo --version
sumo-gui --version

# 添加到PATH (Windows)
set PATH=%PATH%;C:\Program Files (x86)\Eclipse\Sumo\bin

# 添加到PATH (Linux/Mac)
export PATH=$PATH:/usr/local/bin
```

### 常见错误代码
- **500**: 数据库连接失败
- **422**: 请求参数格式错误
- **404**: 文件路径不存在

## 📊 性能优化

### 大数据量处理
- 减少 `interval_minutes` (如改为15或30分钟)
- 启用 `enable_mesoscopic: true`
- 关闭不必要的输出选项

### 内存使用
- 监控 `run_*` 文件夹大小
- 定期清理旧的仿真结果
- 使用数据库分页查询

## 📁 文件位置

### 输入文件
- TAZ配置: `TAZ_4.add.xml`
- 路网文件: `sichuan202503v5.net.xml`
- 车辆配置: `vehicle_types.json`

### 输出文件
- 运行目录: `run_YYYYMMDD_HHMMSS/`
- 路由文件: `*.rou.xml`
- 配置文件: `simulation.sumocfg`
- 仿真结果: `summary.xml`, `tripinfo.xml`等

## 🔍 调试技巧

### 查看生成的文件
```bash
# 查看最新的运行目录
ls -la run_*/

# 检查路由文件内容
head -20 run_*/表名_*.rou.xml

# 查看SUMO配置
cat run_*/simulation.sumocfg
```

### 验证数据
```python
# 检查TAZ ID
import xml.etree.ElementTree as ET
tree = ET.parse('TAZ_4.add.xml')
taz_ids = [taz.get('id') for taz in tree.findall('taz')]
print(f"TAZ数量: {len(taz_ids)}")
```

### 日志分析
- 查看控制台输出的处理进度
- 检查数据库查询结果数量
- 验证时间段分割结果

## 📞 获取帮助

### API文档
访问 http://127.0.0.1:7999/docs 查看交互式API文档

### 日志信息
系统会输出详细的处理日志，包括：
- 数据库连接状态
- 数据筛选统计
- 文件生成进度
- 错误详情

### 联系支持
- 检查 [SUMO_REFERENCE.md](./SUMO_REFERENCE.md) 获取SUMO相关问题
- 查看 [README.md](./README.md) 获取完整文档
- 运行 `python accuracytest.py` 验证仿真精度
