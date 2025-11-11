# 事件场景XML格式参考

## 概述

本文档详细说明事件场景SUMO `.add.xml` 文件的格式和结构。

## 文件结构

### 基本框架

```xml
<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">

    <!-- 注释：事件注入 -->
    <!-- 注释：控制策略 -->

</additional>
```

## 事件注入元素

### 1. closedLane（车道关闭）

用于模拟事故或交通管制造成的车道关闭。

#### 属性说明

| 属性 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | ✓ | 元素唯一ID，格式：`{event_type}_{event_id}` |
| `edge` | string | ✓ | SUMO edge ID，例如 `-4688` |
| `lanes` | string | ✓ | 关闭的lane ID，空格分隔，例如 `-4688_0 -4688_1` |
| `disallow` | string | ✓ | 禁止通行的车辆类型，通常 `all` |
| `begin` | int | ✓ | 开始时间（仿真秒数） |
| `end` | int | ✓ | 结束时间（仿真秒数） |

#### 示例

**简单车道关闭**：
```xml
<!-- 交通事故：G5京昆高速应急车道关闭 -->
<closedLane id="accident_12547"
            edge="-4688"
            lanes="-4688_0"
            disallow="all"
            begin="0"
            end="5330"/>
```

**多车道关闭**：
```xml
<!-- 交通管制：两条车道关闭 -->
<closedLane id="road_control_12637"
            edge="-11410"
            lanes="-11410_0 -11410_1"
            disallow="all"
            begin="0"
            end="4260"/>
```

**长期交通管制**：
```xml
<!-- 恶劣天气：整天关闭 -->
<closedLane id="weather_11554"
            edge="-13472"
            lanes="-13472_0 -13472_1 -13472_2"
            disallow="all"
            begin="0"
            end="86400"/>  <!-- 24小时 -->
```

#### 时间计算

仿真时间（秒数）的计算方法：

```
仿真开始时间：event.start_time（如 2025-07-14 01:53:49）
仿真时间0 = 01:53:49

event.begin_seconds = (event.start_time - sim_start).total_seconds()
event.end_seconds = (event.end_time - sim_start).total_seconds()

示例：
event.start_time = 01:53:49
event.end_time = 03:22:39
持续时间 = 1小时29分钟 = 5330秒

→ begin="0"
→ end="5330"
```

### 2. rerouter（重定向）

用于模拟拥堵或路线管制时的自动重定向。（当前实现为占位符）

```xml
<rerouter id="congestion_13287"
          edges="-13472"
          begin="0"
          end="3600">
    <interval begin="0" end="3600"/>
</rerouter>
```

## 控制策略元素

### 1. variableSpeedSign（可变限速）

模拟可变限速标志控制交通流量。

#### 属性说明

| 属性 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | ✓ | 元素ID，格式：`vss_{event_id}` |
| `lanes` | string | ✓ | 受控车道，空格分隔 |

#### 内部元素

**`<step>`**：速度限制的时间步长

| 属性 | 类型 | 说明 |
|------|------|------|
| `time` | int | 时间点（仿真秒数） |
| `speed` | float | 速度限制（m/s） |

#### 示例

**基础限速**：
```xml
<!-- 单一速度限制 -->
<variableSpeedSign id="vss_12547"
                   lanes="-4688_0 -4688_1">
    <step time="0" speed="16.67"/>  <!-- 60 km/h = 16.67 m/s -->
</variableSpeedSign>
```

**分阶段限速**：
```xml
<!-- 事件期间逐步降低速度 -->
<variableSpeedSign id="vss_12587"
                   lanes="-2000000059_0 -2000000059_1">
    <step time="0" speed="16.67"/>      <!-- 0-300秒：60 km/h -->
    <step time="300" speed="13.89"/>    <!-- 300-4945秒：50 km/h -->
    <step time="4945" speed="22.22"/>   <!-- 4945秒后：80 km/h -->
</variableSpeedSign>
```

#### 常见速度转换表

| km/h | m/s | 说明 |
|------|-----|------|
| 30 | 8.33 | 城市道路 |
| 40 | 11.11 | 拥堵区域 |
| 50 | 13.89 | 轻度拥堵 |
| 60 | 16.67 | 中度拥堵 |
| 70 | 19.44 | 轻度减速 |
| 80 | 22.22 | 正常速度 |
| 100 | 27.78 | 高速公路正常 |
| 120 | 33.33 | 高速公路最高 |

### 2. rerouter（重定向/收费站控制）

用于模拟收费站流量控制。

#### 属性说明

| 属性 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | ✓ | 元素ID，格式：`tec_{event_id}` |
| `edges` | string | ✓ | 受控收费站入口edge ID |

#### 示例

**收费站入口控制**：
```xml
<!-- 常州北站入口控制 -->
<rerouter id="tec_12637"
          edges="-11410">
    <interval begin="0" end="4260">
        <parkingArea id="zone_1" visible="0"/>
    </interval>
</rerouter>
```

### 3. calibrator（流量校准）

用于在仿真中注入车辆流，模拟上游交通。

```xml
<calibrator id="calib_12547"
            edge="-4688"
            friendlyPos="true"
            pos="-1000">
    <flow begin="0" end="5330" queueType="fifo"/>
</calibrator>
```

## 完整场景示例

### 示例1：简单交通事故 + VSS控制

```xml
<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">

    <!-- 事件注入：货车追尾事故 -->
    <closedLane id="accident_12547"
                edge="-4688"
                lanes="-4688_0"
                disallow="all"
                begin="0"
                end="5330"/>

    <!-- 控制策略：可变限速 -->
    <variableSpeedSign id="vss_12547"
                       lanes="-4688_0 -4688_1">
        <step time="0" speed="16.67"/>  <!-- 60 km/h -->
    </variableSpeedSign>

</additional>
```

### 示例2：道路管制 + 收费站控制

```xml
<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">

    <!-- 事件注入：因暴雨关闭收费站入口 -->
    <closedLane id="road_control_11831"
                edge="-11410"
                lanes="-11410_0"
                disallow="all"
                begin="0"
                end="3776"/>

    <!-- 控制策略：限制流量 -->
    <rerouter id="tec_11831"
              edges="-11410">
        <interval begin="0" end="3776">
            <parkingArea id="toll_control" visible="0"/>
        </interval>
    </rerouter>

</additional>
```

### 示例3：复杂场景 - 多车道关闭 + 分阶段限速

```xml
<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">

    <!-- 事件注入：多辆车事故导致两条车道关闭 -->
    <closedLane id="accident_14688"
                edge="-9698"
                lanes="-9698_0 -9698_1"
                disallow="all"
                begin="0"
                end="7200"/>

    <!-- 控制策略1：可变限速（分阶段） -->
    <variableSpeedSign id="vss_14688"
                       lanes="-9698_0 -9698_1 -9698_2">
        <step time="0" speed="13.89"/>      <!-- 事件期间：50 km/h -->
        <step time="7200" speed="22.22"/>   <!-- 事件后：80 km/h -->
    </variableSpeedSign>

    <!-- 控制策略2：动态硬路肩（开放肩道增加容量） -->
    <lane id="shoulder_14688" speed="0"/>

</additional>
```

## 验证和常见错误

### 验证方法

```bash
# 使用SUMO工具验证XML格式
python -m sumolib.xml validate scenario_12547_vss.add.xml

# 或在仿真前检查
sumo -c simulation.sumocfg --check
```

### 常见错误

#### 错误1：无效的edge ID

```xml
<!-- ❌ 错误：edge不存在 -->
<closedLane edge="invalid_edge" lanes="invalid_0"/>

<!-- ✓ 正确：使用有效的edge ID -->
<closedLane edge="-4688" lanes="-4688_0"/>
```

#### 错误2：无效的lane索引

```xml
<!-- ❌ 错误：lane索引超出范围 -->
<closedLane edge="-4688" lanes="-4688_5"/>  <!-- 该edge只有3条车道 -->

<!-- ✓ 正确：使用有效的lane索引 -->
<closedLane edge="-4688" lanes="-4688_0 -4688_1"/>
```

#### 错误3：时间范围错误

```xml
<!-- ❌ 错误：end时间小于begin时间 -->
<closedLane begin="5330" end="0"/>

<!-- ✓ 正确：begin < end -->
<closedLane begin="0" end="5330"/>
```

#### 错误4：缺失必需属性

```xml
<!-- ❌ 错误：缺少lanes属性 -->
<closedLane id="accident_12547" edge="-4688" disallow="all" begin="0" end="5330"/>

<!-- ✓ 正确：包含所有必需属性 -->
<closedLane id="accident_12547" edge="-4688" lanes="-4688_0"
            disallow="all" begin="0" end="5330"/>
```

## 性能考虑

### 优化建议

1. **最小化关闭车道数**：
   - 只关闭实际受影响的车道
   - 避免关闭不必要的车道

2. **优化控制策略时间**：
   - 仅在必要时激活控制
   - 避免过长的仿真时间

3. **合理设置缓冲区**：
   - 事件前：30分钟捕捉基线
   - 事件后：30分钟观察恢复

### 性能影响

| 因素 | 影响 | 建议 |
|------|------|------|
| 关闭车道数 | 高 | 只关闭必需车道 |
| 事件持续时间 | 中 | 保持在0.5-3小时 |
| 仿真区域大小 | 高 | 限制到相关区域 |
| OD对数 | 高 | 使用代表性OD数据 |

## 参考资源

- SUMO官方XML文档：https://sumo.dlr.de/docs/Networks/File_Formats.html
- 控制策略说明：`docs/scenarios_library/PROJECT_WORKFLOW.md`
- API文档：`docs/api/event_scenario_api.md`
- 生成指南：`docs/scenarios_library/SCENARIO_GENERATION_GUIDE.md`
