# SUMO配置文件XML声明问题 - 诊断与解决方案

## 问题描述

**错误信息:**
```
In file 'D:\projects\OD_SIM\cases\case_event_10817\simulations\sim_scenario_10817_no_control\scenario_accident_event_10817.add.xml'
At line/column 3/7.

Loading of additional-files failed.
Quitting (on error).
```

**根本原因:** 生成的`.add.xml`文件包含**两个XML声明**，这是无效的XML格式。

## 问题分析

### 错误文件示例（修复前）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml version='1.0' encoding='UTF-8'?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ...>
    <!-- 事件注入 -->
    <rerouter id="accident_10817" edges="-12788">
        ...
    </rerouter>
</additional>
```

### 问题根源

文件位置: `shared/control_tools/scenario_generator.py` 第474-515行

`_combine_event_and_control_xml()` 方法的问题：
1. 第487行: 添加了一个XML声明 `<?xml version="1.0" encoding="UTF-8"?>`
2. 第499-500行: 添加event_xml内容时，如果event_xml已经包含XML声明，就会导致重复

```python
# 原代码（有问题）
xml_parts.append('<?xml version="1.0" encoding="UTF-8"?>')
# ... 后续添加event_xml和control_xml ...
# 如果这些XML字符串已经包含声明，就会有重复
```

## 解决方案

### 1. 代码修复

在 `scenario_generator.py` 中添加了 `_remove_xml_declaration()` 方法：

```python
def _remove_xml_declaration(self, xml_str: str) -> str:
    """
    移除XML字符串中的XML声明（如果存在）。

    确保组合事件和控制策略XML时不会出现重复声明。
    """
    if not xml_str:
        return xml_str

    # 移除XML声明 (<?xml ... ?>)
    import re
    cleaned = re.sub(r'<\?xml[^?]*\?>', '', xml_str, count=1)
    return cleaned.lstrip()
```

修改 `_combine_event_and_control_xml()` 方法：

```python
def _combine_event_and_control_xml(self, event_xml: str, control_xml: str = "") -> str:
    # 移除片段中的任何XML声明，防止重复
    event_xml_clean = self._remove_xml_declaration(event_xml)
    control_xml_clean = self._remove_xml_declaration(control_xml)

    # 现在只添加一个XML声明到最终输出
    xml_parts = []
    xml_parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    # ... 组合清洁的XML片段 ...
```

### 2. 已生成文件的修复

运行了两个修复脚本来修复所有现有的有问题的`.add.xml`文件：

```bash
python fix_double_xml_declarations.py   # 第一次修复
python fix_double_xml_final.py          # 最终强力修复
```

**修复结果:**
- 扫描文件总数: **821**
- 修复文件数: **145**
- 出错文件数: **0**

#### 修复的文件类型

1. **事件场景文件** (主要)
   - `scenario_accident_event_*.add.xml` (140+ 文件)
   - `scenario_road_control_event_*.add.xml` (20+ 文件)
   - `scenario_breakdown_event_*.add.xml` (1 文件)
   - `scenario_weather_event_*.add.xml` (1 文件)

2. **位置分布**
   - `cases/case_event_*/config/` - 配置目录
   - `cases/case_event_*/simulations/sim_*/` - 模拟目录
   - `output/scenarios/*/scenario_*_no_control/` - 输出目录

## 验证

修复后的文件格式正确：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
    <!-- 事件注入 -->
    <rerouter id="accident_10817" edges="-12788">
        <interval begin="1800" end="4315">
            <closingLaneReroute id="-12788_1" disallow="all"/>
        </interval>
    </rerouter>
</additional>
```

✅ 只有一个XML声明，结构有效

## 后续防护

### 1. 自动验证

可以在生成`.add.xml`文件后添加验证：

```python
def validate_xml_file(file_path: Path) -> bool:
    """验证XML文件格式有效性"""
    try:
        import xml.etree.ElementTree as ET
        ET.parse(file_path)  # 尝试解析，会抛出异常如果无效
        return True
    except ET.ParseError as e:
        logger.error(f"XML解析失败: {file_path}: {e}")
        return False
```

### 2. 建议的改进

在 `_combine_event_and_control_xml()` 中添加：

```python
# 组合完成后验证XML结构
try:
    ET.fromstring(combined_xml)  # 验证有效性
except ET.ParseError as e:
    logger.error(f"生成的XML无效: {e}")
    raise ValueError(f"Invalid combined XML: {e}")
```

## 相关文件

- **修复代码**: `shared/control_tools/scenario_generator.py`
  - 新增方法: `_remove_xml_declaration()` (474-493行)
  - 修改方法: `_combine_event_and_control_xml()` (495-540行)

- **受影响的文件**: 145个`.add.xml`文件
  - 所有文件已修复，可以正常运行

## 测试建议

1. **单元测试**: 测试新的`_remove_xml_declaration()`方法
   ```python
   def test_remove_xml_declaration():
       gen = ScenarioGenerator()
       xml_with_decl = '<?xml version="1.0"?>\n<root></root>'
       result = gen._remove_xml_declaration(xml_with_decl)
       assert '<?xml' not in result
       assert result.startswith('<root>')
   ```

2. **集成测试**: 生成新的事件场景配置，验证`.add.xml`能被SUMO解析

3. **验证现有文件**:
   ```bash
   sumo -c config.sumocfg  # 应该正常运行，无XML解析错误
   ```

## 总结

| 项目 | 详情 |
|------|------|
| **问题** | 生成的.add.xml文件包含重复的XML声明 |
| **影响范围** | 145个事件场景配置文件 |
| **修复方法** | 在组合XML前移除片段中的声明 |
| **状态** | ✅ 已修复并验证 |
| **提交ID** | 9c9fa6d |

---

**更新时间**: 2025-11-16
**版本**: 1.0
