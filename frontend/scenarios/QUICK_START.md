# 场景浏览器快速开始指南

**文件**: scenario_browser.html

**预计时间**: 5分钟

---

## 🚀 快速测试（无需场景数据）

场景浏览器内置了**模拟数据**，可以直接测试所有功能。

### 步骤1: 启动API服务

```powershell
# 在项目根目录执行
.\start_api.ps1
```

等待服务启动完成（出现 "Uvicorn running on http://0.0.0.0:8000"）

### 步骤2: 打开浏览器

在浏览器中访问：

```
http://localhost:8000/frontend/scenarios/scenario_browser.html
```

### 步骤3: 体验功能

即使没有真实场景数据，浏览器会自动加载3个模拟场景：

1. **京昆高速K1576交通事故+VSS限速** (评分: 85)
2. **厦蓉高速K1821交通事故+DHS应急车道开放** (评分: 78)
3. **京昆高速K1685交通阻塞+TEC收费管控** (未评分)

### 测试功能清单

- ✅ 查看统计卡片（总场景数、已仿真、事件类型、平均分）
- ✅ 使用筛选功能（事件类型、管控策略）
- ✅ 搜索场景
- ✅ 改变排序方式
- ✅ 点击「查看详情」
- ✅ 点击「快速应用」（会提示演示模式）

---

## 📊 加载真实场景数据

### 前置条件

需要先生成场景配置文件和索引文件。

### 方法1: 使用Python脚本（推荐）

```bash
# 运行场景生成脚本（待创建）
python scripts/generate_scenarios_from_events.py

# 输出文件:
# - output/scenarios/scenario_index.json
# - output/scenarios/01_交通事故/vss/*.json
# - ...
```

### 方法2: 手动创建索引文件

创建 `output/scenarios/scenario_index.json`：

```json
{
  "metadata": {
    "total_scenarios": 1,
    "last_updated": "2025-01-09T16:00:00",
    "version": "1.0"
  },
  "scenarios": [
    {
      "scenario_id": "SC_TEST_001",
      "scenario_name": "测试场景",
      "event_type": "交通事故",
      "control_strategy": "VSS",
      "source_event_id": "test",
      "road": "G5京昆高速",
      "location": "K1000",
      "direction": "上行",
      "duration_hours": 1.5,
      "created_date": "2025-01-09",
      "file_path": "scenarios/test.json",
      "tags": ["测试"],
      "effectiveness_score": null,
      "simulation_count": 0,
      "preview": {
        "event_time": "2025-01-09 10:00:00 - 11:30:00",
        "affected_lanes": "第一车道",
        "control_params": {
          "speed_limit": 60
        }
      }
    }
  ]
}
```

刷新浏览器即可看到新场景。

---

## 🔧 常见问题

### Q1: 浏览器显示"无法加载场景索引文件"

**原因**: `output/scenarios/scenario_index.json` 不存在

**解决**:
- 浏览器会自动使用模拟数据，可以继续测试
- 或按照上述方法创建索引文件

### Q2: 点击"快速应用"后提示错误

**原因**: 演示模式下API调用会失败（这是正常的）

**解决**:
- 测试阶段可以忽略此提示
- 真实使用时需要确保后端API已实现相应接口

### Q3: 样式显示异常

**原因**: CDN加载失败或网络问题

**解决**:
- 检查网络连接
- 刷新页面重试
- 或下载Bootstrap到本地引用

### Q4: 场景卡片颜色不正确

**原因**: 事件类型名称不匹配预定义样式

**解决**:
- 检查场景数据中的 `event_type` 字段
- 确保使用以下类型之一：
  - 交通事故
  - 交通阻塞
  - 交通管制
  - 地质灾害
  - 车辆故障
  - 恶劣天气

---

## 📝 数据字段说明

### 必填字段

场景索引文件中每个场景必须包含：

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| scenario_id | string | 场景唯一ID | "SC_EVT_001" |
| scenario_name | string | 场景名称 | "交通事故+VSS限速" |
| event_type | string | 事件类型 | "交通事故" |
| control_strategy | string | 管控策略 | "VSS" |
| road | string | 高速公路 | "G5京昆高速" |
| location | string | 位置 | "K1576+000" |
| direction | string | 方向 | "上行/下行" |
| duration_hours | number | 持续时间(小时) | 1.5 |
| created_date | string | 创建日期 | "2025-01-09" |
| tags | array | 标签列表 | ["夜间", "追尾"] |

### 可选字段

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| effectiveness_score | number | 效果评分(0-100) | null |
| simulation_count | number | 仿真次数 | 0 |
| preview | object | 预览信息 | {} |

---

## 🎨 自定义样式

### 修改主题色

在 `scenario_browser.html` 的 `<style>` 部分修改：

```css
:root {
    --primary-color: #1976d2;      /* 主色调 */
    --secondary-color: #388e3c;    /* 辅助色 */
    --background-color: #f5f7fa;   /* 背景色 */
}
```

### 添加新的事件类型颜色

在样式中添加：

```css
.badge-event-新类型 {
    background-color: #颜色背景;
    color: #颜色文字;
}
```

---

## 🔗 相关链接

- [场景集工作流程文档](../../docs/scenarios_library/PROJECT_WORKFLOW.md)
- [UI简化建议文档](../../docs/scenarios_library/UI页面评估与简化建议.md)
- [完整README](README.md)

---

## 📞 下一步

测试完成后，可以：

1. ✅ 查看 [PROJECT_WORKFLOW.md](../../docs/scenarios_library/PROJECT_WORKFLOW.md) 了解完整流程
2. ✅ 运行场景生成脚本创建真实场景
3. ✅ 使用批量仿真功能测试场景

---

**更新日期**: 2025-01-09

**版本**: v1.0
