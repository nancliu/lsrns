# 场景详情模态框 - event_description.json 数据增强

**日期**: 2025-11-14
**状态**: ✅ 实现完成
**目标**: 从 event_description.json 提取完整的事件信息到详情模态框

---

## 概述

场景详情模态框现已支持从 `event_description.json` 文件动态加载详细的事件信息，包括：

✅ **事件描述** - 从 `event_description.event_description` 字段提取
✅ **位置信息** - road, direction, mileage, edge_id, junction_id
✅ **时间信息** - start_time, end_time, duration_hours
✅ **影响描述** - 从 `impact.affected_lanes` 和 `impact.lane_ids` 提取

---

## event_description.json 数据结构

```json
{
  "event_id": "10754",
  "event_type": "交通事故",
  "event_description": "【交通事故首报】2025/6/10 10:43:48,接沈雁飞报：京昆高速成雅段雅安至成都方向K1834+300发生一起两小车事故事故，占用应急车道，目前造成0死亡1受伤，已通知高速交警,执法,路维,",
  "location": {
    "road": "G5京昆高速（成雅段）",
    "direction": "下行",
    "mileage": "K1834.3+000",
    "junction_id": "-55409",
    "edge_id": "-3734"
  },
  "time": {
    "start_time": "2025-06-10 10:43:48",
    "end_time": "2025-06-10 11:14:50",
    "duration_hours": 0.52
  },
  "impact": {
    "affected_lanes": ["应急车道"],
    "lane_ids": ["-3734_0"]
  }
}
```

---

## 实现细节

### 文件路径构建

模态框使用以下路径加载 event_description.json：

```
/output/scenarios/{event_folder}/{scenario_id}/event_description.json
```

**路径映射说明**:

- scenario_index.json 中的 `event_type` 是**中文**（如"交通事故"）
- 实际的文件夹名称是**英文编码**（如"01_accident"）
- 代码中使用 `mapEventTypeToFolder()` 函数进行自动转换

**示例**:

```
event_type: "交通事故" → event_folder: "01_accident"
/output/scenarios/01_accident/scenario_10754_no_control/event_description.json
```

**支持的事件类型映射**:

| 中文事件类型 | 英文文件夹 | 说明 |
|-----------|----------|------|
| 交通事故 | 01_accident | 道路交通事故 |
| 交通阻塞 | 02_congestion | 交通拥堵/阻塞 |
| 交通管制 | 03_road_control | 道路管制措施 |
| 恶劣天气 | 06_weather | 恶劣天气状况 |
| 路面异常 | 06_weather | 路面异常/天气相关 |

**备选/兼容映射**: 拥堵 → 02_congestion | 道路管制 → 03_road_control | 车辆故障 → 05_breakdown

### 数据提取映射

| 模态框字段 | 数据来源 | 备选来源 |
|-----------|---------|---------|
| 事件描述 | event_description.event_description | scenario.description |
| 道路 | location.road | scenario.road |
| 方向 | location.direction | scenario.location |
| 里程 | location.mileage | scenario.mileage |
| Edge ID | location.edge_id | scenario.edge_id |
| Junction ID | location.junction_id | scenario.junction_id |
| 开始时间 | time.start_time | scenario.time.start_time |
| 结束时间 | time.end_time | scenario.time.end_time |
| 持续时长 | time.duration_hours | scenario.time.duration_hours |
| 影响描述 | impact.affected_lanes + impact.lane_ids | scenario.impact |

### 代码变更

**文件**: `frontend/scenarios/scenario_browser.js`

**新增函数**: `openScenarioDetailsModal(scenarioId)` (async)
- 异步加载 event_description.json
- 优先使用 event_description.json 的数据
- 自动回退到 scenario 数据
- 错误处理机制

**新增函数**: `populateScenarioDetailsFromScenario(scenario)`
- 纯回退方案，使用 scenario 数据填充
- 用于 event_description.json 加载失败时

---

## 影响描述处理

event_description.json 中的 `impact` 字段被解析为可读文本：

**示例转换**:
```javascript
{
  "affected_lanes": ["应急车道"],
  "lane_ids": ["-3734_0"]
}
```

↓ 转换为 ↓

```
影响车道: 应急车道
车道ID: -3734_0
```

---

## 工作流程

### 用户打开详情模态框时

1. **立即显示模态框** (使用 scenario_index.json 的基础数据)
2. **异步加载** event_description.json
3. **更新所有字段** 使用 event_description.json 的完整数据
4. **如果加载失败** 使用 scenario 数据作为备选

### 数据优先级

```
event_description.json (首选)
    ↓ 回退 ↓
scenario_index.json (备选)
    ↓ 回退 ↓
scenario browser 内存数据 (最后)
```

---

## 使用示例

### 场景详情模态框中的数据显示

**📋 基本信息**
- 场景ID: `scenario_10754_no_control` (from scenario_index.json)
- 事件ID: `10754` (from scenario_index.json)
- 事件类型: `交通事故` (from scenario_index.json)
- 管控策略: `NO_CONTROL` (from scenario_index.json)
- 事件描述: `【交通事故首报】2025/6/10 10:43:48...` ✨ (from event_description.json)

**🌍 事件发生地点与时间**
- 道路: `G5京昆高速（成雅段）` ✨ (from event_description.json)
- 方向: `下行` ✨ (from event_description.json)
- 里程: `K1834.3+000` ✨ (from event_description.json)
- Edge ID: `-3734` ✨ (from event_description.json)
- Junction ID: `-55409` ✨ (from event_description.json)

**⏰ 时间信息**
- 开始时间: `2025-06-10 10:43:48` ✨ (from event_description.json)
- 结束时间: `2025-06-10 11:14:50` ✨ (from event_description.json)
- 持续时长: `0.52h` ✨ (from event_description.json)

**⚠️ 事件影响**
- 影响车道: `应急车道` ✨ (from event_description.json)
- 车道ID: `-3734_0` ✨ (from event_description.json)

✨ = 从 event_description.json 动态加载

---

## 技术细节

### 异步加载机制

```javascript
// 打开模态框（立即显示，使用基础数据）
const modal = document.getElementById('scenarioDetailsModal');
if (modal) {
    modal.style.display = 'flex';
}

// 异步加载详细数据
try {
    const eventDescUrl = `/output/scenarios/${eventType}/${scenarioDir}/event_description.json`;
    const response = await fetch(eventDescUrl);
    let eventDesc = null;

    if (response.ok) {
        eventDesc = await response.json();
    }

    // 使用加载的数据更新所有字段...
} catch (error) {
    // 使用回退方案...
}
```

### 错误处理

- 如果 event_description.json 不存在 → 自动使用 scenario 数据
- 如果网络错误 → 自动回退
- 如果 JSON 格式错误 → 自动回退
- **用户体验**: 不会出现错误提示，始终显示数据

---

## 测试清单

### 数据加载验证
- [ ] 打开详情模态框时，基础信息立即显示
- [ ] 事件描述正确加载并显示
- [ ] 位置信息（道路、方向、里程、ID）正确显示
- [ ] 时间信息正确显示
- [ ] 影响描述正确解析并显示

### 回退机制验证
- [ ] 删除 event_description.json，详情模态框仍能显示
- [ ] 使用浏览器开发者工具检查网络请求
- [ ] 确认回退到 scenario 数据时仍有有效数据

### 多场景验证
- [ ] 测试不同的 event_type（01_accident, 02_congestion 等）
- [ ] 测试不同的 strategy（NO_CONTROL, VSS, TEC 等）
- [ ] 确认路径构建正确

---

## 后续改进空间

### 可选增强
1. 加载动画 - 异步加载时显示加载指示器
2. 缓存机制 - 避免重复加载相同的 event_description.json
3. 预加载 - 在表格渲染时预加载常见场景的详情
4. 策略参数显示 - 从 control_strategy_config.json 加载策略参数

---

## 相关文件

| 文件 | 描述 |
|-----|------|
| frontend/scenarios/scenario_browser.js | 主要实现，包含 openScenarioDetailsModal() |
| frontend/scenarios/scenario_browser.html | 模态框 HTML，场景详情字段定义 |
| output/scenarios/{event_type}/{scenario_id}/event_description.json | 数据源 |

---

## 验证命令

### 检查 event_description.json 是否可访问

```bash
curl http://localhost:8000/output/scenarios/01_accident/scenario_10754_no_control/event_description.json
```

### 检查 JavaScript 语法

```bash
node -c frontend/scenarios/scenario_browser.js
# 输出: ✓ JavaScript syntax valid
```

---

## 总结

✅ **完整的事件信息展示** - 所有字段从 event_description.json 提取
✅ **智能数据回退** - 自动处理缺失文件或数据
✅ **无缝用户体验** - 异步加载，无需等待
✅ **充分的容错能力** - 始终能显示数据，不会出错

**系统现已准备就绪，可以进行功能测试。**

