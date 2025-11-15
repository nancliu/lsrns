# 事件场景 XML 格式修复记录

**日期**: 2025-11-15
**问题**: SUMO v1.24.0 不支持 `<closedLane>` 元素导致仿真报错
**状态**: ✅ 已完成

## 问题描述

运行事件场景仿真时，SUMO 报错：
```
Error: no declaration found for element 'closedLane'
```

原因：事件场景 .add.xml 文件使用了已废弃的 `<closedLane>` 元素格式，SUMO v1.24.0 不再支持该格式。

## 解决方案

### 1. 更新 XML 生成逻辑

**修改文件**: `shared/control_tools/event_injector.py`

**涉及的注入器类**:
- `AccidentInjector` (交通事故)
- `RoadControlInjector` (道路管控)
- `GeologicalInjector` (地质灾害)
- `BreakdownInjector` (车辆故障)
- `WeatherInjector` (恶劣天气)

**修改内容**:

#### 旧格式 (不正确)
```xml
<closedLane id="accident_12345"
            edge="-3026"
            lanes="-3026_0"
            disallow="all"
            begin="1800"
            end="10858"/>
```

#### 新格式 (正确)
```xml
<rerouter id="accident_12345" edges="-3026">
    <interval begin="1800" end="10858">
        <closingLaneReroute id="-3026_0" disallow="all"/>
    </interval>
</rerouter>
```

**关键变化**:
- 使用 `<rerouter>` 替代 `<closedLane>`
- 添加 `<interval>` 子元素定义时间范围
- 使用 `<closingLaneReroute>` 子元素定义车道关闭
- `edges` 属性（单数edge变为复数edges）
- 支持多车道关闭（每个车道一个 `<closingLaneReroute>` 元素）

### 2. 迁移现有文件

**迁移脚本**: `scripts/migrate_event_xml_format.py`

**受影响的事件类型**:
- 01_accident (交通事故): 123 个文件
- 03_road_control (道路管控): 22 个文件
- 05_breakdown (车辆故障): 1 个文件
- 06_weather (恶劣天气): 1 个文件

**总计**: 168 个文件成功迁移 (147 个在 output/scenarios/, 21 个在 cases/)

**迁移命令**:
```bash
# 预览（dry-run）
python scripts/migrate_event_xml_format.py --dry-run

# 执行转换
python scripts/migrate_event_xml_format.py
```

**迁移结果**: 所有文件成功转换，无错误

### 3. 更新前端过滤逻辑

**问题**: 事件场景案例元数据格式有多种变体，需要统一识别

**修改文件**:
1. `frontend/control/js/batch_simulation.js` - OD仿真页面（排除事件场景）
2. `frontend/scenarios/case-simulation-center.html` - 事件场景仿真页面（仅显示事件场景）

**元数据格式识别**:
```javascript
// 识别3种事件场景元数据格式
const isEventScenario = sourceType.includes('event_scenario') ||
                       caseType === 'event_based' ||
                       caseType === 'event_scenario_case';
```

### 4. 验证新场景生成

**测试文件**: `test_new_scenario_generation.py` (临时测试，已清理)

**验证结果**: ✅ 新生成的场景自动使用正确的 rerouter 格式

**生成工作流**:
```
CSV Events → generate_scenarios_from_events.py
           → ScenarioGenerator
           → event_injector.generate_xml()
           → 正确的 XML 格式
```

## 技术细节

### XML Schema 对比

| 属性/元素 | closedLane (旧) | rerouter (新) |
|----------|----------------|---------------|
| 根元素 | `<closedLane>` | `<rerouter>` |
| 边属性 | `edge="..."` | `edges="..."` |
| 时间范围 | `begin/end` 属性 | `<interval>` 子元素 |
| 车道关闭 | `lanes` 属性 | `<closingLaneReroute>` 子元素 |
| 多车道 | 逗号分隔字符串 | 多个子元素 |

### 车道 ID 映射

**应急车道映射**:
```python
emergency_lane_mapping = {
    'S向应急车道': '_0',  # 最右侧车道（应急车道）
    'N向应急车道': '_0',
    '应急车道': '_0'
}
```

**行车道映射** (从右到左):
```python
lane_index_mapping = {
    '第1车道': '_0',  # 最右
    '第2车道': '_1',
    '第3车道': '_2',
    '第4车道': '_3'   # 最左
}
```

## 影响范围

### 已修复的功能
1. ✅ 事件场景 XML 生成逻辑（event_injector.py）
2. ✅ 现有事件场景文件迁移（168个文件）
3. ✅ 前端事件场景案例过滤逻辑
4. ✅ 新场景生成工作流验证

### 未来场景生成
- 所有新生成的事件场景将自动使用正确的 rerouter 格式
- 无需手动干预或转换

### SUMO 兼容性
- ✅ SUMO v1.24.0+
- ✅ 符合官方 XML Schema 规范

## 文件清单

### 修改的核心文件
- `shared/control_tools/event_injector.py` - XML 生成逻辑
- `frontend/control/js/batch_simulation.js` - OD仿真过滤
- `frontend/scenarios/case-simulation-center.html` - 事件场景过滤

### 新增工具
- `scripts/migrate_event_xml_format.py` - 迁移脚本（保留，可用于未来迁移）

### 已清理的临时文件
- `test_new_scenario_generation.py` - 测试脚本（已删除）

## 验证清单

- [x] 所有 5 种事件类型注入器已更新
- [x] 168 个现有 XML 文件已迁移
- [x] 新生成场景使用正确格式
- [x] 前端过滤逻辑正确识别事件场景
- [x] SUMO 仿真运行无错误
- [x] 临时测试文件已清理

## 维护建议

1. **不要修改已迁移的 XML 文件** - 它们已经是正确格式
2. **event_injector.py 是唯一的真理源** - 所有 XML 生成都通过这个模块
3. **迁移脚本保留** - 未来如有新的格式变更可以参考
4. **元数据格式统一** - 建议逐步将旧格式元数据迁移到新格式

## 参考资料

- SUMO Documentation: [Rerouter](https://sumo.dlr.de/docs/Simulation/Rerouter.html)
- SUMO XML Schema: `http://sumo.dlr.de/xsd/additional_file.xsd`
- 项目文档: `openspec/changes/event-scenario-simulation-integration/`

---

**文档版本**: 1.0
**最后更新**: 2025-11-15
**维护者**: AI Assistant (Claude Code)
