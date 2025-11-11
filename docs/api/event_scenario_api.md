# Event Scenario API 文档

## 概述

Event Scenario API 提供了完整的事件场景管理和模拟功能，包括场景浏览、快速创建案例和事件相关的仿真执行。

## 快速开始

### 1. 浏览事件场景

```bash
# 前端：访问事件场景库页面
http://localhost:8000/control/scenario_browser.html

# 后端：获取场景索引JSON
GET /output/scenarios/scenario_index.json
```

### 2. 快速创建案例

```bash
POST /api/v1/case/quick-create-from-event

# 请求体：
{
  "case_name": "交通事故_VSS_20251111",
  "event_type": "交通事故",
  "strategy": "VSS",
  "scenario_id": "scenario_12547_vss",
  "network_file": "templates/network_files/sichuan202508v7.net.xml",
  "od_file": "baseline.od_data_sichuan_202507",
  "taz_file": "templates/taz_files/sichuan_taz.taz.xml",  # 可选
  "description": "从事件场景快速创建的案例"
}

# 响应：
{
  "code": "200",
  "message": "案例创建成功",
  "data": {
    "case_id": "case_12547_vss_20251111",
    "case_name": "交通事故_VSS_20251111",
    "created_at": "2025-11-11T12:34:56",
    "scenario_id": "scenario_12547_vss"
  }
}
```

### 3. 运行事件相关仿真

```bash
POST /api/v1/simulation/start-with-event/

# 请求体：
{
  "case_id": "case_12547_vss_20251111",
  "scenario_id": "scenario_12547_vss",
  "gui": false  # 是否启用SUMO GUI
}

# 响应：
{
  "code": "200",
  "message": "仿真启动成功",
  "data": {
    "simulation_id": "sim_20251111_143000",
    "case_id": "case_12547_vss_20251111",
    "scenario_id": "scenario_12547_vss",
    "status": "running",
    "start_time": "2025-11-11T14:30:00"
  }
}
```

## 核心模块

### `shared/control_tools/event_injector.py`

事件注入模块，负责生成事件相关的SUMO XML元素。

#### 主要类和函数

```python
class EventInjector(ABC):
    """事件注入基类"""

    def generate_xml(self, event_data: Dict[str, Any]) -> str:
        """生成事件注入XML，子类必须实现"""
        pass

class AccidentInjector(EventInjector):
    """交通事故注入器 - 生成closedLane XML"""

    def generate_xml(self, event_data: Dict[str, Any]) -> str:
        """
        为交通事故生成车道关闭XML

        Args:
            event_data: 包含以下字段的事件数据：
                - report_id: 事件报告ID
                - edge_id: SUMO edge ID (e.g., "-4688")
                - affected_lanes: 占用车道列表 (e.g., ["应急车道"])
                - start_time: 事件开始时间 (YYYY-MM-DD HH:MM:SS)
                - end_time: 事件结束时间 (YYYY-MM-DD HH:MM:SS)

        Returns:
            XML字符串，例如：
            <closedLane id="accident_12547" edge="-4688" lanes="-4688_0"
                        disallow="all" begin="0" end="5330"/>

        Raises:
            ValueError: 数据验证失败时
        """
        pass

def create_event_injector(event_type: str, network_file: Optional[str] = None) -> EventInjector:
    """
    工厂函数：根据事件类型创建相应的注入器

    Args:
        event_type: 事件类型 (交通事故、交通阻塞、交通管制、地质灾害、车辆故障、恶劣天气)
        network_file: SUMO网络文件路径（可选，用于lane ID解析）

    Returns:
        相应的EventInjector子类实例

    Example:
        >>> injector = create_event_injector('交通事故', 'network.net.xml')
        >>> xml = injector.generate_xml(event_data)
    """
    pass
```

#### 使用示例

```python
from shared.control_tools.event_injector import create_event_injector

# 创建注入器
injector = create_event_injector('交通事故', network_file='templates/network_files/sichuan202508v7.net.xml')

# 事件数据
event_data = {
    'report_id': '12547',
    'edge_id': '-4688',
    'affected_lanes': ['应急车道'],
    'start_time': '2025-07-14 01:53:49',
    'end_time': '2025-07-14 03:22:39',
    'event_type': '交通事故'
}

# 生成XML
event_xml = injector.generate_xml(event_data)
print(event_xml)
```

### `shared/control_tools/scenario_generator.py`

场景生成模块，负责生成完整的场景配置包（XML + JSON元数据）。

#### 主要类

```python
class ScenarioGenerator:
    """生成完整的事件场景配置包"""

    def __init__(self, network_file: str, output_base_dir: str = "output/scenarios"):
        """
        初始化场景生成器

        Args:
            network_file: SUMO网络文件路径
            output_base_dir: 输出基目录
        """
        pass

    def generate_scenario(
        self,
        event_data: Dict[str, Any],
        strategy_type: str,
        control_params: Dict[str, Any]
    ) -> Dict[str, Path]:
        """
        生成完整的场景配置包

        Args:
            event_data: 事件数据
            strategy_type: 控制策略类型 (VSS、DHS、TEC)
            control_params: 控制参数

        Returns:
            生成文件的路径字典：
            {
                "add_xml": Path("scenario_交通事故_vss_12547.add.xml"),
                "event_description": Path("event_description.json"),
                "traffic_input_config": Path("traffic_input_config.json"),
                "control_strategy_config": Path("control_strategy_config.json")
            }

        Example:
            >>> generator = ScenarioGenerator('network.net.xml')
            >>> files = generator.generate_scenario(event_data, 'VSS', params)
        """
        pass
```

#### 生成的文件结构

```
output/scenarios/01_交通事故/scenario_12547_vss/
├── scenario_交通事故_vss_12547.add.xml          # SUMO配置（事件+控制）
├── event_description.json                       # 事件描述
├── traffic_input_config.json                    # OD数据时间范围配置
├── control_strategy_config.json                 # 控制策略参数
└── simulation.sumocfg                          # SUMO仿真配置文件
```

#### 配置文件格式

**event_description.json**:
```json
{
  "event_id": "12547",
  "event_type": "交通事故",
  "event_description": "两货车追尾事故",
  "location": {
    "road": "G5京昆高速（绵广段）",
    "direction": "下行",
    "mileage": "K1576+000",
    "junction_id": "-35882",
    "edge_id": "-4688"
  },
  "time": {
    "start_time": "2025-07-14 01:53:49",
    "end_time": "2025-07-14 03:22:39",
    "duration_hours": 1.48
  },
  "impact": {
    "affected_lanes": ["应急车道"],
    "lane_ids": ["-4688_0"]
  }
}
```

**traffic_input_config.json**:
```json
{
  "od_time_range": {
    "start": "2025-07-14 01:23:49",
    "end": "2025-07-14 03:52:39",
    "event_start": "2025-07-14 01:53:49",
    "event_end": "2025-07-14 03:22:39",
    "buffer_before_minutes": 30,
    "buffer_after_minutes": 30
  },
  "od_table": "baseline.od_data_sichuan_202507",
  "simulation_duration_hours": 2.48,
  "vehicle_types": ["passenger", "truck", "bus"]
}
```

**control_strategy_config.json**:
```json
{
  "strategy_type": "VSS",
  "strategy_name": "可变限速标志",
  "parameters": {
    "speed_limit_kmh": 70,
    "affected_edges": ["-4688"],
    "affected_lanes": ["-4688_0", "-4688_1"],
    "response_delay_seconds": 300,
    "recovery_period_seconds": 600
  },
  "timing": {
    "activation_time": "2025-07-14 01:58:49",
    "deactivation_time": "2025-07-14 03:32:39"
  }
}
```

### `scripts/generate_scenarios_from_events.py`

批量场景生成脚本，从事件CSV文件批量生成场景库。

#### 命令行使用

```bash
# 基础使用
python scripts/generate_scenarios_from_events.py

# 指定输入/输出目录
python scripts/generate_scenarios_from_events.py \
    --events-csv events/all_extracted_events.csv \
    --output-dir output/scenarios \
    --network-file templates/network_files/sichuan202508v7.net.xml

# 指定目标事件数量
python scripts/generate_scenarios_from_events.py --target-events 30
```

#### 主要函数

```python
def filter_representative_events(
    events_df: pd.DataFrame,
    target_count: int = 18
) -> pd.DataFrame:
    """
    筛选代表性事件

    Filters:
    - 事件持续时间：0.5-3小时
    - 数据完整性：包含必需字段
    - 地理分布：选择不同路段

    Returns:
        筛选后的事件DataFrame
    """
    pass

def map_event_to_strategies(event_row: pd.Series) -> List[Dict[str, Any]]:
    """
    将事件映射到控制策略

    Returns:
        控制策略列表，每项包括：
        {
            "strategy_type": "VSS"/"DHS"/"TEC",
            "params": {...}
        }
    """
    pass

def generate_scenario_library(
    events_csv: str,
    output_dir: str
) -> Dict[str, Any]:
    """
    批量生成场景库

    Returns:
        生成结果摘要
    """
    pass
```

## API端点

### Case Management

#### 快速从事件创建案例

```
POST /api/v1/case/quick-create-from-event
Content-Type: application/json

{
  "case_name": "string",          # 案例名称（必需）
  "event_type": "string",          # 事件类型（必需）
  "strategy": "string",            # 控制策略 VSS/DHS/TEC（必需）
  "scenario_id": "string",         # 场景ID（必需）
  "network_file": "string",        # 网络文件路径（必需）
  "od_file": "string",             # OD文件路径或表名（必需）
  "taz_file": "string",            # TAZ文件路径（可选）
  "description": "string"          # 案例描述（可选）
}

Response:
{
  "code": "200",
  "message": "案例创建成功",
  "data": {
    "case_id": "string",
    "case_name": "string",
    "scenario_id": "string",
    "created_at": "ISO8601 datetime"
  }
}
```

### Simulation

#### 运行事件相关仿真

```
POST /api/v1/simulation/start-with-event/
Content-Type: application/json

{
  "case_id": "string",             # 案例ID（必需）
  "scenario_id": "string",         # 场景ID（必需）
  "gui": boolean                   # 是否启用SUMO GUI（可选，默认false）
}

Response:
{
  "code": "200",
  "message": "仿真启动成功",
  "data": {
    "simulation_id": "string",
    "case_id": "string",
    "scenario_id": "string",
    "status": "running|completed|failed",
    "start_time": "ISO8601 datetime"
  }
}
```

## 错误处理

所有API端点遵循统一的错误响应格式：

```json
{
  "code": "400",
  "message": "错误描述",
  "detail": "详细错误信息"
}
```

常见错误：

| 错误码 | 说明 |
|-------|------|
| 400 | 请求参数无效 |
| 404 | 资源不存在（网络文件、OD文件等） |
| 500 | 服务器错误（SUMO执行失败等） |

## 最佳实践

### 1. 场景生成

- 确保SUMO网络文件存在且有效
- 使用统一的事件ID命名约定
- 验证edge_id和lane描述的准确性

### 2. 案例创建

- 提供有意义的case_name，便于后续查找
- 确认OD数据时间范围与traffic_input_config匹配
- 可选TAZ文件用于复杂的OD分析

### 3. 仿真执行

- 选择合适的scenario_id
- 监控仿真进度
- 检查结果目录中的SUMO输出文件

## 故障排除

### 问题：场景生成失败 - "Unknown lane description"

**原因**：lane description在支持列表中不存在

**解决方案**：
- 检查event_injector.py中的lane_mapping字典
- 添加新的lane类型（如需）
- 参考event数据中的"占用车道情况"字段值

### 问题：仿真失败 - "SUMO executable not found"

**原因**：SUMO未正确安装或SUMO_HOME未配置

**解决方案**：
```bash
# 设置SUMO环境变量
export SUMO_HOME=/path/to/sumo
export PATH=$SUMO_HOME/bin:$PATH
```

### 问题：案例创建失败 - "OD file not found"

**原因**：OD文件路径不正确或文件不存在

**解决方案**：
- 使用绝对路径
- 验证文件权限
- 检查traffic_input_config中的OD表名

## 参考资源

- SUMO官方文档：https://sumo.dlr.de/docs/
- 项目工作流：`docs/scenarios_library/PROJECT_WORKFLOW.md`
- 事件数据说明：`docs/scenarios_library/事件数据字段说明.csv`
