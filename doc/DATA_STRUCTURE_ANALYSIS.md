# OD数据预处理流程 - 数据结构详细分析

## 📊 执行流程概览

基于代码分析，OD数据预处理的完整数据流转如下：

```
原始数据库数据 → 时间分段 → TAZ筛选 → 车辆映射 → OD聚合 → Flow生成 → 文件输出
```

## 1. 📋 原始数据库查询结果结构

### 1.1 数据库表结构 (dwd.dwd_od_g4202)
```sql
SELECT * FROM "dwd"."dwd_od_g4202" 
WHERE "start_time" >= TO_TIMESTAMP('2024/08/22 16:00:00', 'YYYY/MM/DD HH24:MI:SS')
AND "start_time" < TO_TIMESTAMP('2024/08/22 16:05:00', 'YYYY/MM/DD HH24:MI:SS');
```

**预期字段结构:**
| 字段名 | 类型 | 说明 | 示例值 |
|--------|------|------|--------|
| start_time | timestamp | 出行开始时间 | 2024-08-22 16:01:30 |
| start_square_code | varchar | 起点收费广场代码 | G000551005003710010 |
| end_square_code | varchar | 终点收费广场代码 | G000551005003720010 |
| start_station_code | varchar | 起点收费站代码 | ST001 |
| end_station_code | varchar | 终点收费站代码 | ST002 |
| vehicle_type | varchar | 车辆类型 | k1, h3, t2 等 |
| [其他字段] | various | 其他业务字段 | ... |

**数据特点:**
- 每行代表一次车辆通行记录
- `start_square_code`和`end_square_code`可能为空
- `vehicle_type`需要映射到标准分类

## 2. 🕒 时间分段处理结构

### 2.1 时间分段算法
```python
def split_time_range(start_time: str, end_time: str, interval_minutes: int) -> List[Tuple[str, str]]
```

**输入示例:**
- start_time: "2024/08/22 16:00:00"
- end_time: "2024/08/22 17:00:00"  
- interval_minutes: 5

**输出结构:**
```python
[
    ("2024/08/22 16:00:00", "2024/08/22 16:05:00"),
    ("2024/08/22 16:05:00", "2024/08/22 16:10:00"),
    ("2024/08/22 16:10:00", "2024/08/22 16:15:00"),
    # ... 共12个时间段
    ("2024/08/22 16:55:00", "2024/08/22 17:00:00")
]
```

## 3. 🗺️ TAZ配置数据结构

### 3.1 TAZ文件结构分析 (TAZ_4.add.xml)

**基于实际文件分析:**
- 总TAZ数量: 355个
- TAZ ID格式: G + 数字编码 (如 G000551005003710010)

**TAZ类型分布:**
| TAZ类型 | 数量 | 说明 | 示例ID |
|---------|------|------|--------|
| 仅作起点 (source only) | ~177 | 只有tazSource | G000551005003720010 |
| 仅作终点 (sink only) | ~178 | 只有tazSink | G000551005003710010 |
| 双向TAZ | 0 | 既有source又有sink | 无 |

**单个TAZ结构:**
```xml
<taz id="G000551005003710010" 
     shape="坐标点序列" 
     name="chengya(baijia-shuangliubei)" 
     color="blue">
    <tazSink id="-4878.749" weight="1.00"/>
</taz>
```

### 3.2 TAZ处理后的数据结构

**load_taz_ids() 返回:**
```python
taz_ids = {
    "G000551005003710010",
    "G000551005003720010", 
    "G00055100501601010",
    # ... 355个TAZ ID
}
```

**load_single_direction_tazs() 返回:**
```python
single_direction_tazs = {
    "G000551005003710010": "sink",     # 只能作终点
    "G000551005003720010": "source",   # 只能作起点
    "G00055100501601010": "source",    # 只能作起点
    # ...
}
```

## 4. 🚗 车辆类型配置结构

### 4.1 车辆配置文件 (vehicle_types.json)

**配置结构:**
```json
{
  "vehicle_types": {
    "passenger_small": {
      "accel": 2.6,
      "decel": 4.5, 
      "length": 5.0,
      "maxSpeed": 70.0,
      "color": "yellow",
      "valid_ids": ["k1", "k2"],
      "vClass": "passenger",
      "carFollowModel": "IDM"
    }
    // ... 6种车辆类型
  }
}
```

**车辆类型映射关系:**
| 原始ID | 车辆分类 | 描述 |
|--------|----------|------|
| k1, k2 | passenger_small | 小型客车 |
| k3, k4 | passenger_large | 大型客车 |
| h1, h2 | truck_small | 小型货车 |
| h3, h4, h5, h6 | truck_large | 大型货车 |
| t1, t2 | special_small | 小型专用车 |
| t3, t4, t5, t6 | special_large | 大型专用车 |

**处理后的映射字典:**
```python
vehicle_mapping = {
    "k1": "passenger_small",
    "k2": "passenger_small", 
    "k3": "passenger_large",
    "h3": "truck_large",
    # ... 总共14个映射关系
}
```

## 5. 📊 数据处理各阶段的结构变化

### 5.1 原始DataFrame (从数据库查询)
```python
# 形状: (N, 7+) - N条记录，7+个字段
df_original = pd.DataFrame({
    'start_time': [...],
    'start_square_code': [...],  # 可能有空值
    'end_square_code': [...],    # 可能有空值  
    'start_station_code': [...],
    'end_station_code': [...],
    'vehicle_type': [...],       # k1, h3, t2 等
    # 其他字段...
})
```

### 5.2 缺失代码处理后
```python
# 使用 handle_missing_codes() 处理
# 空的 square_code 用对应的 station_code 替代
df_processed = df_original.copy()
# 处理逻辑已应用，无空值
```

### 5.3 TAZ筛选后
```python
# 使用 filter_od_by_taz() 筛选
# 只保留起点和终点都在TAZ列表中的记录
df_taz_filtered = pd.DataFrame({
    'start_square_code': [...],  # 都在taz_ids中
    'end_square_code': [...],    # 都在taz_ids中
    'vehicle_type': [...],
    # 其他保留字段...
})
# 形状: (M, 7+) - M <= N，筛选后的记录数
```

### 5.4 单向TAZ验证后
```python
# 使用 filter_invalid_od_data() 进一步筛选
# 移除违反单向限制的OD对
df_valid_od = pd.DataFrame({
    'start_square_code': [...],  # 符合单向限制
    'end_square_code': [...],    # 符合单向限制
    'vehicle_type': [...],
})
# 形状: (L, 3) - L <= M，只保留3个关键字段
```

### 5.5 车辆类型映射后
```python
# 添加 vehicle_category 字段
df_mapped = df_valid_od.copy()
df_mapped['vehicle_category'] = df_mapped['vehicle_type'].map(vehicle_mapping)

# 结果结构:
# 形状: (L, 4)
# 字段: start_square_code, end_square_code, vehicle_type, vehicle_category
```

### 5.6 OD统计聚合后
```python
# 使用 groupby 聚合
od_counts = df_mapped.groupby([
    'start_square_code', 
    'end_square_code', 
    'vehicle_category'
]).size().reset_index(name='count')

# 结果结构:
# 形状: (K, 4) - K为唯一的OD-车型组合数
# 字段: start_square_code, end_square_code, vehicle_category, count
```

**示例数据:**
| start_square_code | end_square_code | vehicle_category | count |
|-------------------|-----------------|------------------|-------|
| G000551005003710010 | G000551005003720010 | passenger_small | 15 |
| G000551005003720010 | G00055100501601010 | truck_large | 8 |
| G00055100501601010 | G000551005003710010 | passenger_small | 12 |

## 6. 🌊 Flow数据生成结构

### 6.1 单个Flow元素结构
```python
flow_data = {
    "id": "f_0",                           # Flow唯一标识
    "type": "passenger_small",             # 车辆类型分类
    "begin": "0",                          # 开始时间(秒)
    "end": "300",                          # 结束时间(秒)  
    "fromTaz": "G000551005003710010",      # 起始TAZ
    "toTaz": "G000551005003720010",        # 目标TAZ
    "vehsPerHour": "72.00"                 # 每小时车辆数
}
```

### 6.2 流量计算公式
```python
# 每小时流量 = (时间段内车辆数 / 时间段长度(秒)) * 3600
vehs_per_hour = (vehicle_count / segment_duration) * 3600

# 示例: 5分钟内有6辆车
# vehs_per_hour = (6 / 300) * 3600 = 72.0 辆/小时
```

### 6.3 所有时间段的Flow集合
```python
all_flow_data = [
    # 第一个时间段 (0-300秒)
    {"id": "f_0", "begin": "0", "end": "300", ...},
    {"id": "f_1", "begin": "0", "end": "300", ...},
    
    # 第二个时间段 (300-600秒)  
    {"id": "f_2", "begin": "300", "end": "600", ...},
    {"id": "f_3", "begin": "300", "end": "600", ...},
    
    # ... 所有时间段的所有Flow
]
```

## 7. 📁 输出文件结构

### 7.1 路由文件 (.rou.xml) 结构
```xml
<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">

    <!-- 车辆类型定义部分 -->
    <vType id="passenger_small" accel="2.6" decel="4.5" sigma="0.5"
           length="5.0" maxSpeed="70.0" color="yellow"
           vClass="passenger" carFollowModel="IDM"/>
    <vType id="truck_large" accel="0.8" decel="4.5" sigma="0.5"
           length="10.0" maxSpeed="80.0" color="green"
           vClass="truck" carFollowModel="IDM"/>
    <!-- ... 其他车辆类型 -->

    <!-- Flow定义部分 -->
    <flow id="f_0" type="passenger_small" begin="0" end="300"
          fromTaz="G000551005003710010" toTaz="G000551005003720010"
          vehsPerHour="72.00"/>
    <flow id="f_1" type="truck_large" begin="300" end="600"
          fromTaz="G000551005003720010" toTaz="G00055100501601010"
          vehsPerHour="36.00"/>
    <!-- ... 所有Flow元素 -->
</routes>
```

### 7.2 OD矩阵文件 (.od.xml) 结构
```xml
<?xml version="1.0" encoding="UTF-8"?>
<demand>
    <actorConfig id="DEFAULT_VEHTYPE">
        <timeSlice duration="3600000" startTime="0">
            <odPair amount="25.5" origin="G000551005003710010"
                    destination="G000551005003720010"/>
            <odPair amount="18.0" origin="G000551005003720010"
                    destination="G00055100501601010"/>
            <!-- ... 所有非零OD对 -->
        </timeSlice>
    </actorConfig>
</demand>
```

### 7.3 SUMO配置文件 (.sumocfg) 结构
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
    <input>
        <net-file value="../sichuan202503v5.net.xml"/>
        <route-files value="表名_时间段.rou.xml"/>
        <additional-files value="../TAZ_4.add.xml"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="3600"/>
    </time>
    <output>
        <statistic-output value="static.xml"/>
        <duration-log.statistics value="true"/>
        <summary-output value="summary.xml"/>
        <!-- 可选输出 -->
        <tripinfo-output value="tripinfo.xml"/>
        <vehroute-output value="vehroute.xml"/>
    </output>
    <gui_only>
        <start value="true"/>
        <quit-on-end value="false"/>
    </gui_only>
</configuration>
```

## 8. 📈 数据量级估算

### 8.1 典型数据规模
**假设场景: 1小时数据，5分钟间隔**

| 处理阶段 | 数据量级 | 说明 |
|----------|----------|------|
| 原始数据库记录 | 10,000-100,000条 | 取决于交通流量 |
| TAZ筛选后 | 8,000-80,000条 | ~80%保留率 |
| 单向验证后 | 7,000-70,000条 | ~90%保留率 |
| OD聚合后 | 500-5,000组 | 唯一OD-车型组合 |
| Flow元素数量 | 500-5,000个 | 每个聚合组生成1个Flow |
| 时间段数量 | 12段 | 60分钟/5分钟间隔 |

### 8.2 内存使用估算
- **原始DataFrame**: ~10-100MB (取决于字段数和记录数)
- **处理过程中间数据**: ~5-50MB
- **最终Flow数据**: ~1-10MB
- **XML文件大小**: ~100KB-10MB

## 9. 🔍 关键数据验证点

### 9.1 数据完整性检查
```python
# 1. TAZ ID存在性验证
assert all(od['fromTaz'] in taz_ids for od in all_flow_data)
assert all(od['toTaz'] in taz_ids for od in all_flow_data)

# 2. 车辆类型映射验证
assert all(od['type'] in vehicle_config.keys() for od in all_flow_data)

# 3. 时间范围验证
assert all(0 <= int(od['begin']) < int(od['end']) <= total_duration
          for od in all_flow_data)

# 4. 流量数值验证
assert all(float(od['vehsPerHour']) >= 0 for od in all_flow_data)
```

### 9.2 业务逻辑验证
```python
# 1. 单向TAZ限制验证
for flow in all_flow_data:
    from_taz = flow['fromTaz']
    to_taz = flow['toTaz']

    # 起点不能是sink-only TAZ
    if from_taz in single_direction_tazs:
        assert single_direction_tazs[from_taz] != 'sink'

    # 终点不能是source-only TAZ
    if to_taz in single_direction_tazs:
        assert single_direction_tazs[to_taz] != 'source'
```

## 10. 🚀 性能优化建议

### 10.1 数据处理优化
1. **向量化操作**: 使用pandas的向量化方法替代逐行处理
2. **内存管理**: 及时删除不需要的中间DataFrame
3. **批量处理**: 考虑分批处理大数据集

### 10.2 数据库查询优化
1. **索引优化**: 在start_time字段建立索引
2. **查询优化**: 只选择必要的字段
3. **连接池**: 使用数据库连接池(已实现)

## 11. 📊 实际执行示例

### 11.1 模拟执行结果
**输入参数:**
```json
{
    "start_time": "2024/08/22 16:00:00",
    "end_time": "2024/08/22 16:15:00",
    "interval_minutes": 5
}
```

**处理结果统计:**
```
时间段数量: 3段
- 段1: 2024/08/22 16:00:00 - 2024/08/22 16:05:00
- 段2: 2024/08/22 16:05:00 - 2024/08/22 16:10:00
- 段3: 2024/08/22 16:10:00 - 2024/08/22 16:15:00

TAZ配置: 355个TAZ (177个source, 178个sink)
车辆类型: 6种分类，14个原始ID映射

数据处理统计:
- 原始记录: 1,250条
- TAZ筛选后: 1,000条 (80%保留)
- 单向验证后: 900条 (90%保留)
- OD聚合后: 45组唯一组合
- 生成Flow: 45个Flow元素

输出文件:
- run_20250708_160000/
  ├── dwd_od_g4202_20240822160000_20240822161500.rou.xml (15KB)
  ├── dwd_od_g4202_20240822160000_20240822161500.od.xml (8KB)
  └── simulation.sumocfg (2KB)
```

这个详细的数据结构分析文档应该能帮助您全面理解OD数据预处理流程中每个步骤的数据变化、结构特点和性能考虑！
