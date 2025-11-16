# 场景索引结构文档

**文件**: `/output/scenarios/scenario_index.json`
**生成脚本**: `scripts/generate_scenario_index.py`
**最后更新**: 2025-11-17

---

## 概述

场景索引（scenario_index.json）是一个JSON文件，包含了所有可用场景的完整元数据。该文件由 `generate_scenario_index.py` 脚本自动生成，通过扫描 `/output/scenarios` 目录并从每个场景的 `event_description.json` 文件中提取数据。

---

## 文件统计

| 指标 | 值 |
|------|-----|
| 总场景数 | 477 |
| 文件大小 | 492.7 KB |
| 格式 | JSON (UTF-8) |
| 更新时间 | 自动生成 |

---

## 顶级结构

```json
{
  "timestamp": "2025-11-17T...",
  "total_scenarios": 478,
  "scenarios": [...]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | string (ISO 8601) | 索引生成的时间戳 |
| `total_scenarios` | number | 场景总数 |
| `scenarios` | array | 场景对象数组 |

---

## 场景对象结构

每个场景对象包含以下字段：

```json
{
  "event_id": "10754",
  "event_type": "交通事故",
  "strategy": "NO_CONTROL",
  "event_description": "...",
  "location": {...},
  "time": {...},
  "files": {...},
  "created_cases": [],
  "case_count": 0
}
```

### 完整字段说明

#### 基本信息

| 字段 | 类型 | 说明 | 示例 | 填充率 |
|------|------|------|------|--------|
| `event_id` | string | 事件ID | "10754" | 100% |
| `event_type` | string | 事件类型 | "交通事故" | 100% |
| `strategy` | string | 控制策略 | "TEC" | 100% |
| `event_description` | string | 事件详细描述 | "【交通事故首报】..." | 99.8% |

#### 事件类型枚举值

目前包含以下事件类型：

| 事件类型 | 数量 | 说明 |
|---------|------|------|
| 交通事故 | 362 | 道路交通事故 |
| 交通拥堵 | 46 | 交通路段拥堵 |
| 道路管制 | 44 | 道路管制措施 |
| 流量激增工况 | 19 | 流量激增工况 |
| 恶劣天气 | 3 | 恶劣天气条件 |
| 车辆故障 | 3 | 车辆故障事件 |

#### 策略枚举值

| 策略 | 数量 | 说明 |
|------|------|------|
| NO_CONTROL | 162 | 不干预（基准线） |
| TEC | 171 | 收费站管控 |
| VSS | 140 | 可变限速 |
| DHS | 4 | 动态硬路肩 |

#### 位置信息 (`location` 对象)

```json
{
  "location": {
    "road": "G5京昆高速（成雅段）",
    "direction": "下行",
    "mileage": "K1834.3+000",
    "junction_id": "-55409",
    "edge_id": "-3734"
  }
}
```

| 字段 | 类型 | 说明 | 示例 | 填充率 |
|------|------|------|------|--------|
| `road` | string | 道路名称 | "G5京昆高速（成雅段）" | 99.8% |
| `direction` | string | 行驶方向 | "下行"、"上行" | 99.8% |
| `mileage` | string | 里程桩号 | "K1834.3+000" | 99.8% |
| `junction_id` | string | 路段ID | "-55409" | 99.8% |
| `edge_id` | string | 边界ID | "-3734" | 95% |

#### 时间信息 (`time` 对象)

```json
{
  "time": {
    "start_time": "2025-06-10 10:43:48",
    "end_time": "2025-06-10 11:14:50",
    "duration_hours": 0.52
  }
}
```

| 字段 | 类型 | 说明 | 格式 | 填充率 |
|------|------|------|------|--------|
| `start_time` | string | 事件开始时间 | "YYYY-MM-DD HH:MM:SS" | 99.8% |
| `end_time` | string | 事件结束时间 | "YYYY-MM-DD HH:MM:SS" | 99.8% |
| `duration_hours` | number | 事件持续时间（小时） | 0.52 | 99.8% |

#### 文件信息 (`files` 对象)

```json
{
  "files": {
    "scenario_dir": "scenario_10754_no_control",
    "add_xml": "",
    "event_description": "event_description.json",
    "traffic_config": "traffic_input_config.json",
    "control_config": "control_strategy_config.json"
  }
}
```

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `scenario_dir` | string | 场景目录名 | "scenario_10754_no_control" |
| `add_xml` | string | SUMO附加文件 | "" |
| `event_description` | string | 事件描述文件名 | "event_description.json" |
| `traffic_config` | string | 交通配置文件名 | "traffic_input_config.json" |
| `control_config` | string | 控制配置文件名 | "control_strategy_config.json" |

#### 案例信息

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `created_cases` | array | 从该场景创建的案例ID列表 | [] |
| `case_count` | number | 创建的案例总数 | 0 |

---

## 数据来源

### 从哪些文件提取

场景索引从以下源提取数据：

1. **目录结构** (位置 + 策略)
   ```
   /output/scenarios/
   ├── 01_accident/              → event_type
   │   └── scenario_10754_tec/   → strategy
   └── ...
   ```

2. **event_description.json** (详细信息)
   ```json
   {
     "event_id": "10754",
     "event_type": "交通事故",
     "event_description": "...",
     "location": {...},
     "time": {...},
     "impact": {...}
   }
   ```

### 映射规则

#### 事件类型映射（从目录前缀）

| 目录前缀 | 事件类型 |
|---------|---------|
| 01_accident | 交通事故 |
| 02_congestion | 交通拥堵 |
| 03_road_control | 道路管制 |
| 05_breakdown | 车辆故障 |
| 06_weather | 恶劣天气 |
| 07_flowsurge | 流量激增 |

#### 策略规范化（从目录后缀）

| 目录后缀 | 规范化后 |
|---------|---------|
| no_control | NO_CONTROL |
| tec | TEC |
| vss | VSS |
| dhs | DHS |

---

## 使用示例

### 加载索引

```javascript
// 在浏览器中
fetch('/output/scenarios/scenario_index.json')
  .then(r => r.json())
  .then(data => {
    console.log(`共有 ${data.total_scenarios} 个场景`);
    data.scenarios.forEach(scenario => {
      console.log(`${scenario.event_type} - ${scenario.strategy}: ${scenario.location.road}`);
    });
  });
```

### 过滤场景

```javascript
// 获取所有"交通事故"类型的场景
const accidents = scenarios.filter(s => s.event_type === '交通事故');

// 获取特定策略的场景
const tecScenarios = scenarios.filter(s => s.strategy === 'TEC');

// 获取特定道路的场景
const g5Scenarios = scenarios.filter(s => s.location.road.includes('G5'));
```

### 按位置和时间过滤

```javascript
// 获取特定时间范围内的场景
const startDate = new Date('2025-06-10');
const endDate = new Date('2025-06-15');

const scenariosInRange = scenarios.filter(s => {
  const eventStart = new Date(s.time.start_time);
  return eventStart >= startDate && eventStart <= endDate;
});

// 按道路方向分组
const byDirection = {};
scenarios.forEach(s => {
  const direction = s.location.direction || 'unknown';
  if (!byDirection[direction]) byDirection[direction] = [];
  byDirection[direction].push(s);
});
```

---

## 生成和更新

### 自动生成

```bash
# 使用默认路径
python3 scripts/generate_scenario_index.py

# 指定输出目录
python3 scripts/generate_scenario_index.py /path/to/output/scenarios
```

### 脚本参数

```
用法: generate_scenario_index.py [output_dir]

参数:
  output_dir    output/scenarios 目录的路径，默认为 ../output/scenarios
```

### 输出

脚本生成：
- `scenario_index.json` - 主索引文件
- 控制台输出 - 统计信息和任何错误

---

## 数据质量

### 填充率统计

| 字段 | 填充率 | 说明 |
|------|--------|------|
| event_id | 100% | 从目录名提取 |
| event_type | 100% | 从目录结构和event_description.json |
| strategy | 100% | 从目录名提取 |
| location.road | 99.8% | 从event_description.json |
| location.direction | 99.8% | 从event_description.json |
| location.mileage | 99.8% | 从event_description.json |
| location.junction_id | 99.8% | 从event_description.json |
| time.start_time | 99.8% | 从event_description.json |
| time.end_time | 99.8% | 从event_description.json |
| time.duration_hours | 99.8% | 从event_description.json |
| event_description | 99.8% | 从event_description.json |

### 已知问题

✅ **已解决**:
- 测试场景 `scenario_TEST_DHS_001_dhs` 已从索引中过滤
- 流量激增命名已统一为 "流量激增工况"
- 所有477个生产场景均已成功处理，无错误

---

## 最佳实践

### 1. 在前端使用

```javascript
// 加载并缓存索引
let scenarioCache = null;

async function getScenarios() {
  if (!scenarioCache) {
    const response = await fetch('/output/scenarios/scenario_index.json');
    scenarioCache = await response.json();
  }
  return scenarioCache.scenarios;
}
```

### 2. 索引的维护

- 添加新场景后，运行脚本重新生成索引
- 定期验证索引的JSON格式
- 检查缺失的event_description.json文件

### 3. 性能优化

- 对大量场景进行客户端过滤时，考虑使用Web Worker
- 实现场景列表的虚拟滚动（virtual scrolling）
- 缓存过滤结果

---

## 扩展字段建议

### 未来可能添加的字段

1. **impact 对象** - 事件影响信息
   ```json
   "impact": {
     "affected_lanes": ["应急车道"],
     "lane_ids": ["-3734_0"]
   }
   ```

2. **simulation_results** - 仿真结果摘要
   ```json
   "simulation_results": {
     "status": "completed",
     "completion_time": "2025-06-10 12:00:00"
   }
   ```

3. **tags** - 自定义标签
   ```json
   "tags": ["severe", "multi-vehicle", "morning-peak"]
   ```

---

## 相关文件

- `scripts/generate_scenario_index.py` - 索引生成脚本
- `/output/scenarios/scenario_index.json` - 生成的索引文件
- `/output/scenarios/*/event_description.json` - 个别场景的元数据

---

**文档版本**: 1.0
**最后更新**: 2025-11-17
**维护者**: Claude Code
