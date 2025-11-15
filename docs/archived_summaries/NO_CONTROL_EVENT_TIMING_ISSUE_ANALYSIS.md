# NO_CONTROL场景事件加载时间计算问题分析

## 完成时间
2025-11-14

## 问题发现

在检查NO_CONTROL场景的事件加载时间计算时，发现**事件加载时间计算存在严重错误**。

### 问题现象

**示例场景：scenario_10754_no_control**

**事件信息** (event_description.json):
```json
{
  "time": {
    "start_time": "2025-06-10 10:43:48",
    "end_time": "2025-06-10 11:14:50"
  }
}
```

**仿真配置** (traffic_input_config.json):
```json
{
  "od_time_range": {
    "start": "2025-06-10 10:13:48",  // 事件开始 - 30分钟
    "end": "2025-06-10 11:44:50",    // 事件结束 + 30分钟
    "event_start": "2025-06-10 10:43:48",
    "event_end": "2025-06-10 11:14:50",
    "buffer_before_minutes": 30,
    "buffer_after_minutes": 30
  }
}
```

**实际生成的事件加载XML** (scenario_accident_event_10754.add.xml):
```xml
<closedLane id="accident_10754" edge="-3734" lanes="-3734_0"
            disallow="all" begin="0" end="1862"/>
```

### 问题分析

**预期的正确值：**
- 仿真开始时间：10:13:48
- 事件开始时间：10:43:48
- 事件结束时间：11:14:50
- **begin应该 = (10:43:48 - 10:13:48) = 30分钟 = 1800秒** ✅
- **end应该 = (11:14:50 - 10:13:48) = 61分钟2秒 = 3662秒** ✅

**实际错误值：**
- **begin = 0** ❌ (错误：应该是1800秒)
- **end = 1862** ❌ (错误：应该是3662秒)

**问题原因：**
- `begin=0`: 事件从仿真开始就加载了，而不是在实际事件发生时间加载
- `end=1862`: 这是事件持续时长（约31分钟），而不是事件结束时相对于仿真开始的时间

### 验证其他场景

**示例场景：scenario_10762_no_control**

**事件信息：**
- 事件开始：15:12:57
- 事件结束：17:14:35
- 事件持续时长：~2小时2分钟 = 7298秒

**仿真配置：**
- 仿真开始：14:42:57 (事件开始 - 30分钟)
- 仿真结束：17:44:35 (事件结束 + 30分钟)

**实际生成的XML：**
```xml
<closedLane id="accident_10762" edge="-7016" lanes="-7016_1"
            disallow="all" begin="0" end="7298"/>
```

**预期正确值：**
- begin = (15:12:57 - 14:42:57) = 30分钟 = **1800秒** ✅
- end = (17:14:35 - 14:42:57) = 2小时31分38秒 = **9098秒** ✅

**实际错误值：**
- begin = 0 ❌
- end = 7298 (事件持续时长) ❌

## 根本原因分析

### 代码流程追踪

#### 1. 事件数据准备 (`scripts/generate_scenarios_from_events.py:492-527`)

```python
def prepare_event_data(event_row: pd.Series) -> Dict[str, Any]:
    return {
        "report_id": str(event_row.get("report_id", "")),
        "event_type": normalized_type,
        ...
        "start_time": event_row.get("开始时间", ""),
        "end_time": event_row.get("结束时间", ""),
        # ❌ 缺少 sim_start_time 字段！
    }
```

**问题1**: `event_data`字典中**没有包含`sim_start_time`字段**。

#### 2. 场景生成调用 (`shared/control_tools/scenario_generator.py:104-158`)

```python
def generate_scenario(self, event_data: Dict[str, Any], ...):
    # 生成顺序：
    # 1. 生成 .add.xml (第134行)
    add_xml_path = self._generate_add_xml(
        scenario_dir, event_data, strategy_type, control_params
    )

    # 2. 生成 event_description.json (第140行)
    # 3. 生成 traffic_input_config.json (第145行) - 这里才计算sim_start_time！
    traffic_config_path = self._generate_traffic_input_config(
        scenario_dir, event_data
    )

    # 4. 生成 control_strategy_config.json (第152行)
```

**问题2**: .add.xml是**第一个**生成的文件，此时`sim_start_time`还没有计算！

#### 3. 事件注入XML生成 (`shared/control_tools/scenario_generator.py:224-229`)

```python
def _generate_add_xml(self, scenario_dir: Path, event_data: Dict, ...):
    # 创建事件注入器
    event_injector = create_event_injector(
        event_data['event_type'],
        network_file=self.network_file
    )
    # ❌ event_data中没有sim_start_time！
    event_xml = event_injector.generate_xml(event_data)
```

**问题3**: `event_data`字典直接传给`generate_xml()`，但缺少`sim_start_time`字段。

#### 4. 时间转换逻辑 (`shared/control_tools/event_injector.py:143-205`)

```python
def _convert_event_time(self, start_time: str, end_time: str,
                       sim_start_time: Optional[str] = None) -> Tuple[int, int]:
    event_start = datetime.strptime(start_time, time_format)
    event_end = datetime.strptime(end_time, time_format)

    # 确定仿真开始时间参考点
    if sim_start_time:
        sim_start = datetime.strptime(sim_start_time, time_format)
    else:
        # ❌ 默认：仿真从事件开始时间开始
        sim_start = event_start
        logger.debug("No sim_start_time provided, using event start as simulation start")

    # 计算相对秒数
    begin_seconds = int((event_start - sim_start).total_seconds())  # = 0
    end_seconds = int((event_end - sim_start).total_seconds())      # = 事件持续时长
```

**问题4**: 由于没有提供`sim_start_time`，函数**默认使用事件开始时间作为仿真开始时间**，导致：
- `begin = (event_start - event_start) = 0`
- `end = (event_end - event_start) = 事件持续时长`

#### 5. 仿真开始时间计算 (`shared/control_tools/scenario_generator.py:360-415`)

```python
def _generate_traffic_input_config(self, scenario_dir: Path, event_data: Dict, ...):
    event_start = datetime.strptime(event_data['start_time'], "%Y-%m-%d %H:%M:%S")
    event_end = datetime.strptime(event_data['end_time'], "%Y-%m-%d %H:%M:%S")
    buffer = timedelta(minutes=buffer_minutes)

    traffic_config = {
        "od_time_range": {
            "start": (event_start - buffer).strftime("%Y-%m-%d %H:%M:%S"),  # ✅ 这里才计算sim_start_time
            "end": (event_end + buffer).strftime("%Y-%m-%d %H:%M:%S"),
            ...
        }
    }
```

**问题5**: 仿真开始时间在`_generate_traffic_input_config()`中计算，但这个方法在生成.add.xml**之后**才调用，**为时已晚**！

### 根本原因总结

1. **生成顺序错误**: .add.xml在第一步生成，但仿真时间范围在第三步才计算
2. **数据传递缺失**: `event_data`字典缺少`sim_start_time`字段
3. **默认行为不符合预期**: `event_injector._convert_event_time()`在没有`sim_start_time`时，默认使用事件开始时间作为仿真开始时间

## 影响范围

### 受影响场景

**所有NO_CONTROL场景的事件加载时间都是错误的！**

经扫描，受影响的场景包括：
- 01_accident (交通事故): ~54个NO_CONTROL场景
- 02_congestion (交通阻塞): ~15个NO_CONTROL场景
- 03_road_control (交通管制): ~22个NO_CONTROL场景
- 05_breakdown (车辆故障): 部分NO_CONTROL场景
- 06_weather (恶劣天气): 部分NO_CONTROL场景

**预估受影响场景总数: ~100个**

### 仿真结果影响

由于事件加载时间错误：

1. **事件提前发生**: 事件从仿真开始（t=0）就加载，而不是在实际事件时间加载
2. **仿真前30分钟失真**: 本应是正常交通流的前30分钟buffer时段，被错误地加载了事件
3. **对照基准失效**: NO_CONTROL场景作为对照基准，其仿真结果不准确，影响与VSS/TEC场景的对比分析
4. **精度分析失真**: 基于NO_CONTROL场景的精度分析结果可能不准确

### 不受影响的场景

**VSS和TEC场景的控制策略时间是正确的**（已在之前修复）：
- VSS场景的`speed_steps[].begin/end`时间正确 ✅
- TEC场景的`flow_intervals[].begin/end`时间正确 ✅

但是，**VSS和TEC场景的事件加载时间也可能有相同问题**！
需要进一步验证VSS/TEC场景的.add.xml中的事件加载时间。

## 解决方案

### 方案1: 修改`scenario_generator.py`生成顺序（推荐）

**优点**:
- 从根源解决问题
- 适用于所有场景类型
- 未来新生成的场景自动正确

**实施步骤**:

1. 在`_generate_add_xml()`中，先计算仿真开始时间：

```python
def _generate_add_xml(self, scenario_dir: Path, event_data: Dict, ...):
    # 计算仿真开始时间（与_generate_traffic_input_config一致）
    event_start = datetime.strptime(event_data['start_time'], "%Y-%m-%d %H:%M:%S")
    buffer = timedelta(minutes=30)
    sim_start_time = (event_start - buffer).strftime("%Y-%m-%d %H:%M:%S")

    # 添加sim_start_time到event_data
    event_data_with_sim_time = event_data.copy()
    event_data_with_sim_time['sim_start_time'] = sim_start_time

    # 生成事件注入XML
    event_injector = create_event_injector(...)
    event_xml = event_injector.generate_xml(event_data_with_sim_time)  # ✅ 传入sim_start_time
```

2. 确保VSS/TEC场景的事件加载时间也正确

### 方案2: 创建修复脚本（临时措施）

创建`fix_no_control_event_timing.py`修复已生成的NO_CONTROL场景：

```python
def fix_no_control_event_timing(scenario_dir: Path) -> bool:
    # 读取文件
    event_desc = read_json(scenario_dir / 'event_description.json')
    traffic_config = read_json(scenario_dir / 'traffic_input_config.json')

    # 计算正确时间
    sim_start = traffic_config['od_time_range']['start']
    event_start = event_desc['time']['start_time']
    event_end = event_desc['time']['end_time']

    begin_seconds = calculate_seconds(event_start - sim_start)
    end_seconds = calculate_seconds(event_end - sim_start)

    # 更新.add.xml
    update_add_xml(scenario_dir, begin_seconds, end_seconds)
```

### 推荐实施顺序

1. **立即**: 创建修复脚本，修复所有已生成的NO_CONTROL场景
2. **长期**: 修改`scenario_generator.py`，确保未来生成的场景自动正确
3. **验证**: 检查VSS/TEC场景的事件加载时间是否也有相同问题

## 验证清单

修复后需要验证：

- [ ] scenario_10754_no_control: begin=1800, end=3662
- [ ] scenario_10762_no_control: begin=1800, end=9098
- [ ] 所有NO_CONTROL场景的begin=1800 (30分钟buffer)
- [ ] end时间 = (事件结束时间 - 仿真开始时间)的秒数
- [ ] VSS/TEC场景的事件加载时间也正确

---

**最后更新**: 2025-11-14
**状态**: ❌ 问题已确认，待修复
**优先级**: 🔴 高（影响所有NO_CONTROL对照基准场景）
