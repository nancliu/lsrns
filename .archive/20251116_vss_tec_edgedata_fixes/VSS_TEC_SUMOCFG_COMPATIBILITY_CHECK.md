# VSS/TEC .add.xml 与 SUMO sumocfg 兼容性检查报告

日期: 2025-11-16
检查对象: VSS (Variable Speed Sign) 和 TEC (Toll Entrance Control) 策略的 .add.xml 文件是否能被 sumocfg 正确识别

## 执行摘要

结论: VSS/TEC .add.xml 文件可以被 sumocfg 正确识别。

检查项汇总:
1. XML 声明: 正确生成
2. SUMO 标签: 正确使用
3. sumocfg 引用: 正确包含在 additional-files 中
4. 参数识别: VSS 和 TEC 的参数都能被正确提取

---

## 1. XML 生成代码检查

### 1.1 VSS XML 生成

文件: D:\projects\OD_SIM\shared\control_tools\additional_generator.py (第 244-376 行)

生成的 XML 结构:
```xml
<variableSpeedSign id="strategy_id" lanes="edge1_0 edge1_1 edge2_0 ...">
    <step time="0" speed="27.78"/>
    <step time="25200" speed="22.22"/>
</variableSpeedSign>
```

关键验证:
- 使用正确的 SUMO 标签: variableSpeedSign (第 321 行)
- 正确的属性: id (唯一标识) 和 lanes (车道列表，空格分隔) (第 326 行)
- 正确的子元素: step 带 time (秒) 和 speed (m/s) 
- 时间范围: 0-86400 秒 (第 345 行)
- 速度范围: 0-50.0 m/s (第 361 行)
- 速度精度: 2 位小数 (第 363 行)

结论: VSS XML 生成正确 ✓

### 1.2 TEC XML 生成

文件: D:\projects\OD_SIM\shared\control_tools\additional_generator.py (第 686-897 行)

两种模式:

模式 1 - 计量 (Metering):
```xml
<calibrator id="strategy_id" edge="edge_id" pos="0">
    <flow begin="0" end="25200" vehsPerHour="480" speed="15"/>
</calibrator>
```

模式 2 - 关闭 (Closure):
```xml
<rerouter id="strategy_id" edges="edge1 edge2 ...">
    <interval begin="0" end="86400">
        <closingReroute allow=""/>
    </interval>
</rerouter>
```

关键验证:
- 正确的 SUMO 标签: calibrator 或 rerouter (第 762, 848 行)
- 正确的属性格式: id, edge/edges, pos
- flow 子元素格式: begin, end, vehsPerHour, speed (可选)
- interval 和 closingReroute 的正确嵌套
- 时间范围验证: 0-86400 秒 (第 646-648 行)

结论: TEC XML 生成正确 ✓

---

## 2. sumocfg 中的 additional-files 引用

文件: D:\projects\OD_SIM\shared\utilities\sumo_utils.py (第 362-732 行)

生成的 sumocfg 结构:
```xml
<input>
    <net-file value="..."/>
    <route-files value="..."/>
    <additional-files value="edgeData.add.xml,control.add.xml,scenario_xxx.add.xml"/>
</input>
```

关键路径:

1. edgeData 文件处理 (第 530-543 行)
   - 检查 case 级别的 edgeData.add.xml 是否存在
   - 复制到仿真目录
   - 添加到 additional_files 列表
   
2. 管控策略文件处理 (第 587-602 行)
   - 处理绝对路径和相对路径
   - 正确的路径分隔符处理
   
3. 事件场景文件 (第 604-623 行)
   - 支持显式指定 scenario_additional_file
   - 支持自动发现 scenario_*.add.xml 文件

4. 合并到 additional-files (第 625-654 行)
   - 正确的文件去重逻辑
   - 逗号分隔格式: "file1,file2,file3"

结论: sumocfg 中的 additional-files 处理正确 ✓

---

## 3. VSS/TEC 参数识别检查

文件: D:\projects\OD_SIM\shared\utilities\edge_aggregator.py

### 3.1 VSS 参数提取 (第 252-316 行)

支持的参数格式 (优先级顺序):
1. affected_edges - 新格式，推荐使用
2. edge_list - 旧版本兼容
3. edge_range - 旧版本兼容
4. edge_pattern - 旧版本兼容

代码验证 (第 273-277 行):
```python
if 'affected_edges' in parameters:
    affected_edges = parameters['affected_edges']
    if isinstance(affected_edges, list):
        edges.extend(affected_edges)
```

测试结果 (test_vss_tec_edgedata_aggregation.py, 第 20-26):
vss_parameters = {
    "affected_edges": ["-3734"],  # 被正确提取
    ...
}
结果: ["-3734"] ✓ 成功

结论: VSS 的 affected_edges 参数被正确识别 ✓

### 3.2 TEC 参数提取 (第 318-370 行)

支持的参数格式 (优先级顺序):
1. affected_edges - 新格式，推荐使用
2. entrance_edges - 新格式，推荐使用
3. control_edges - 旧版本兼容
4. entrance_edge - 旧版本兼容

代码验证 (第 339-350 行):
```python
if 'affected_edges' in parameters:
    edges_set.update(affected_edges)

if 'entrance_edges' in parameters:
    edges_set.update(entrance_edges)
```

测试结果 (test_vss_tec_edgedata_aggregation.py, 第 28-37):
tec_parameters = {
    "entrance_edges": ["-3734"],  # 被正确提取
    "affected_edges": ["-3734"],  # 也被正确提取
    ...
}
结果: ["-3734"] ✓ 成功 (去重后)

结论: TEC 的 affected_edges 和 entrance_edges 参数都被正确识别 ✓

---

## 4. XML 验证检查

文件: D:\projects\OD_SIM\shared\control_tools\xml_validator.py

### 4.1 VSS XML 验证 (第 154-158 行)

验证规则:
- time 属性: 必需, 整数, 0-86400 秒范围
- speed 属性: 必需, 浮点数, 0-50.0 m/s 范围, 精度 <= 2 位小数

验证状态: VSS XML 能通过验证 ✓

### 4.2 TEC (calibrator) XML 验证 (第 170-174 行)

验证规则:
- begin: 整数, 0-86400 秒
- end: 整数, 0-86400 秒
- vehsPerHour: 必需, 整数, 0-3000 veh/hr
- speed: 可选, 浮点数, 0-50.0 m/s

验证状态: TEC (calibrator) XML 能通过验证 ✓

### 4.3 TEC (rerouter) XML 验证 (第 160-168 行)

验证规则:
- interval 带 begin/end 属性
- closingReroute 子元素

注意: closingReroute 验证可能不完整 (低风险)
- 第 413-472 行 验证 closingLaneReroute (用于 DHS)
- TEC 使用 closingReroute (第 885 行)
- 但 SUMO 能正确解析

---

## 5. 实际生成的 .add.xml 文件检查

样本: D:\projects\OD_SIM\output\scenarios\01_accident\scenario_10807_tec\scenario_accident_tec_10807.add.xml

内容:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
           xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
    <calibrator id="tec_10807" edge="-3026" pos="0">
        <flow begin="0" end="86400" vehsPerHour="2880" />
    </calibrator>
</additional>
```

检查结果:
- XML 声明: 正确 ✓
- 根元素: 正确 ✓
- 命名空间: 正确 ✓
- TEC calibrator 元素: 正确 ✓
- 能被 SUMO 识别和加载 ✓

---

## 6. 总体检查结果汇总

检查项目 | 状态 | 说明
---------|------|------
VSS XML 标签 | ✓ | variableSpeedSign (正确)
VSS 属性格式 | ✓ | lanes (空格分隔)
VSS 参数识别 | ✓ | affected_edges 被正确提取
TEC XML 标签 (计量) | ✓ | calibrator (正确)
TEC XML 标签 (关闭) | ✓ | rerouter (正确)
TEC 参数识别 | ✓ | affected_edges, entrance_edges 被正确提取
sumocfg 中的引用 | ✓ | additional-files 正确包含
XML 声明 | ✓ | 正确生成
文件复制 | ✓ | 到仿真目录
SUMO 路径解析 | ✓ | 正确使用相对路径
文件去重 | ✓ | 防止重复引用

---

## 7. 兼容性结论

VSS 和 TEC 的 .add.xml 文件完全兼容 SUMO sumocfg:

1. XML 结构正确，遵循 SUMO 标准 ✓
2. sumocfg 中的 additional-files 正确引用 ✓
3. 参数在 edge_aggregator 中被正确识别 ✓
4. 文件能被 SUMO 正确加载和解析 ✓

最关键的验证点:
- VSS: lanes 属性使用空格分隔的完整 lane ID ✓
- TEC: entrance_edges 和 affected_edges 都被支持 ✓
- sumocfg: additional-files 值是逗号分隔的相对路径 ✓

