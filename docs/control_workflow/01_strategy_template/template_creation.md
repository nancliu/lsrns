# 策略模板创建流程

本文档说明如何创建新的策略模板。

---

## 一、模板创建概述

### 1.1 创建前提

创建新模板前，需要确认：
- ✅ 是否有新的管控场景需要新模板
- ✅ 现有模板是否无法满足需求
- ✅ 新模板与现有模板的区别

### 1.2 创建步骤

1. **需求分析** - 确定模板适用场景
2. **参数设计** - 设计参数结构
3. **模板实现** - 创建JSON文件
4. **索引更新** - 注册到模板索引
5. **测试验证** - 测试模板功能

---

## 二、详细创建流程

### 2.1 需求分析

#### 识别场景

分析新模板需要解决的交通问题：
- 拥堵类型：路段拥堵、入口排队、容量不足
- 管控目标：限速、扩容、限流
- 特殊要求：天气、事故、车型限制

#### 对比现有模板

检查现有模板是否已覆盖：
- 如果现有模板可满足，优先使用现有模板
- 如果现有模板部分满足，考虑扩展现有模板
- 如果现有模板无法满足，创建新模板

---

### 2.2 参数设计

#### 设计参数Schema

参考现有模板的参数结构：

```json
{
  "parameters_schema": [
    {
      "parameter_name": "affected_edges",
      "parameter_type": "edge_array",
      "description": "受影响的路段列表",
      "required": true,
      "default_value": []
    },
    {
      "parameter_name": "speed_steps",
      "parameter_type": "speed_steps_array",
      "description": "速度时刻表",
      "required": true,
      "default_value": [
        {"time_hours": 7, "speed_kmh": 80},
        {"time_hours": 9, "speed_kmh": 100}
      ],
      "validation": {
        "min_items": 2,
        "time_range": [0, 24],
        "speed_range": [30, 120]
      }
    }
  ]
}
```

#### 设置默认值

- 提供合理的默认参数
- 减少用户配置工作量
- 确保默认值符合安全要求

#### 定义验证规则

- 参数范围：最小值、最大值
- 格式要求：数据类型、格式
- 依赖关系：参数间的依赖

---

### 2.3 模板实现

#### 创建JSON文件

在`templates/control_strategies/`目录创建模板文件：

```bash
templates/control_strategies/vss_custom.json
```

#### 文件结构

```json
{
  "template_id": "vss_custom",
  "template_name": "自定义可变限速",
  "strategy_type": "VSS",
  "description": "适用于自定义场景的可变限速控制",
  "version": "1.0",
  "created_at": "2025-01-XX",
  "parameters_schema": [
    // 参数定义
  ],
  "validation_rules": {
    // 验证规则
  },
  "sumo_mapping": {
    // SUMO XML映射
  }
}
```

---

### 2.4 索引更新

#### 更新templates_index.json

在`templates/control_strategies/templates_index.json`中添加新模板：

```json
{
  "templates": [
    {
      "template_id": "vss_custom",
      "template_name": "自定义可变限速",
      "strategy_type": "VSS",
      "file_path": "vss_custom.json"
    }
  ]
}
```

---

### 2.5 测试验证

#### 功能测试

1. **模板加载**: 验证模板能正确加载
2. **参数验证**: 验证参数验证规则生效
3. **实例生成**: 验证能生成策略实例
4. **XML生成**: 验证能生成SUMO XML

#### 测试用例

```python
def test_template_loading():
    """测试模板加载"""
    template = load_template("vss_custom")
    assert template["template_id"] == "vss_custom"

def test_parameter_validation():
    """测试参数验证"""
    params = {"speed_steps": [{"time_hours": 7, "speed_kmh": 80}]}
    result = validate_parameters("vss_custom", params)
    assert result["valid"] == True

def test_instance_generation():
    """测试实例生成"""
    instance = create_strategy_instance("vss_custom", params)
    assert instance["strategy_type"] == "VSS"
```

---

## 三、模板创建示例

### 3.1 创建VSS模板示例

**场景**: 需要创建一个适用于夜间施工的可变限速模板

**步骤1: 需求分析**
- 场景: 夜间施工（22:00-6:00）
- 特点: 限速较低（40-60 km/h），持续时段长
- 现有模板: `vss_moderate`不适用（限速范围80-100）

**步骤2: 参数设计**
```json
{
  "template_id": "vss_night_construction",
  "template_name": "夜间施工限速",
  "strategy_type": "VSS",
  "description": "适用于夜间施工路段的可变限速控制",
  "parameters_schema": [
    {
      "parameter_name": "affected_edges",
      "parameter_type": "edge_array",
      "required": true
    },
    {
      "parameter_name": "speed_steps",
      "parameter_type": "speed_steps_array",
      "default_value": [
        {"time_hours": 22, "speed_kmh": 60},
        {"time_hours": 6, "speed_kmh": 100}
      ],
      "validation": {
        "speed_range": [40, 60]
      }
    }
  ]
}
```

**步骤3: 创建文件**
- 文件: `templates/control_strategies/vss_night_construction.json`
- 内容: 完整的模板JSON

**步骤4: 更新索引**
- 在`templates_index.json`中添加条目

**步骤5: 测试**
- 加载模板
- 创建策略实例
- 生成SUMO XML

---

## 四、模板维护

### 4.1 版本管理

模板应包含版本信息：
```json
{
  "version": "1.0",
  "created_at": "2025-01-XX",
  "updated_at": "2025-01-XX",
  "changelog": [
    {
      "version": "1.0",
      "date": "2025-01-XX",
      "changes": "初始版本"
    }
  ]
}
```

### 4.2 向后兼容

修改模板时注意：
- ✅ 新增参数: 设为可选，提供默认值
- ✅ 修改参数: 保持参数名不变，扩展功能
- ❌ 删除参数: 谨慎，可能影响现有实例

### 4.3 文档更新

创建模板后更新：
- 模板类型说明文档
- 用户指南
- API文档

---

## 五、相关文档

- [模板设计原理](template_design.md)
- [模板类型说明](template_types.md)
- [策略创建用户指南](../../user_guides/strategy_creation_guide.md)

---

**文档版本**: v1.0
**创建日期**: 2025-01-XX





