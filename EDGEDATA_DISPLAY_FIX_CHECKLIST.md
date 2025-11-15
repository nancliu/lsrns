# EdgeData显示修复实施清单

**日期**: 2025-11-15
**修复范围**: 批量创建模态框中EdgeData信息显示
**优先级**: 🔴 高

---

## 修复内容总览

### ✅ 已完成的修复

#### 修复1：初始显示改进
- **文件**: `frontend/scenarios/scenario_browser.js`
- **函数**: `showBatchCreationComplete()`
- **改进**:
  - ✅ 现在使用完整的`decision_action`文本（如："✅ 启用edgedata输出 (2条已验证的边, 验证率50.0%)"）
  - ✅ 添加颜色编码（绿色=启用，红色=禁用，灰色=未定义）
  - ✅ 添加详细的调试日志到浏览器Console
  - ✅ 更好的错误处理（显示"⚠️ 未生成EdgeData配置"而不是空白）

#### 修复2：动态轮询支持
- **文件**: `frontend/scenarios/scenario_browser.js`
- **新函数**: `pollEdgeDataInfo()`, `updateEdgeDataDisplay()`
- **改进**:
  - ✅ 每5秒从metadata刷新一次EdgeData信息
  - ✅ 与OD轮询集成
  - ✅ 确保显示最新状态

---

## 实施步骤

### 步骤1: 部署前端代码

```bash
# 修改文件已自动保存：
# frontend/scenarios/scenario_browser.js

# 验证语法
cd D:\\projects\\OD_SIM
node -c frontend/scenarios/scenario_browser.js
# ✓ 输出为空（表示通过）
```

### 步骤2: 清除浏览器缓存

```bash
# 方式1：Hard Refresh（推荐）
打开浏览器 → 按下 Ctrl+Shift+R (或 Cmd+Shift+R for Mac)

# 方式2：Chrome开发者工具
F12 → Settings → Network → ☑️ Disable cache (while DevTools is open)
```

### 步骤3: 重新启动FastAPI服务

```powershell
# 如果服务已启动，先停止
Ctrl+C  # 在PowerShell窗口中

# 重新启动
cd D:\\projects\\OD_SIM
.\\start_api.ps1

# 应该看到：
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 步骤4: 测试批量创建功能

```
1. 打开浏览器 → http://localhost:8000
2. 导航到 "场景浏览器" → "批量创建事件案例"
3. 选择一个事件（如event_10754）
4. 点击"批量创建"按钮
5. 在弹出的模态框中观察EdgeData信息
```

---

## 验证清单

### 🎯 应该看到的效果

| 项目 | 预期行为 | 检查方式 |
|------|--------|--------|
| 边缘数显示 | 显示具体数字（如2） | 查看"总边缘数"字段 |
| 验证率显示 | 显示百分比（如50.0%） | 查看"验证率"字段 |
| 输出状态 | ✅ 启用edgedata输出 (2条已验证的边...) | 查看"输出状态"字段，应该是绿色 |
| 动态更新 | 5秒后信息会刷新一次 | 等待5秒，观察是否重新获取 |
| 调试信息 | F12 Console中有详细日志 | F12 → Console → 搜索"EdgeData显示信息" |

### ❌ 问题排查

| 问题现象 | 可能原因 | 排查步骤 |
|--------|--------|--------|
| 什么都不显示 | 浏览器缓存 | Ctrl+Shift+R刷新 |
| 显示"未生成EdgeData" | edgedata_info为null | 检查scenarios是否为空 |
| 显示"禁用输出" | edge_count=0 | 检查事件标签和路网匹配 |
| Console中无日志 | 前端代码未更新 | 手动验证文件修改内容 |
| OD状态更新但Edge不动 | 轮询失败 | F12 Network查看API调用 |

---

## 浏览器调试指南

### 打开开发者工具

```bash
# Windows / Linux
F12

# Mac
Cmd + Option + I
```

### 查看EdgeData显示日志

```
1. F12打开开发者工具
2. 进入Console标签
3. 批量创建，完成后应该看到：

   EdgeData显示信息: {
     statusText: "✅ 启用edgedata输出 (2条已验证的边, 验证率50.0%)",
     statusColor: "#28a745",
     edgeDataInfo: {
       edge_count: 2,
       validation_rate: 0.5,
       should_enable: true,
       decision_action: "✅ 启用edgedata输出 (2条已验证的边, 验证率50.0%)"
     }
   }
```

### 查看API响应

```
1. F12 → Network标签
2. 执行批量创建
3. 找到 POST /api/v1/scenario/create-case-batch 请求
4. 点击该请求 → Response标签
5. 搜索 "edgedata_info"

应该看到:
{
  "edgedata_info": {
    "edge_count": 2,
    "validation_rate": 0.5,
    "should_enable": true,
    "decision_action": "✅ 启用edgedata输出 (2条已验证的边, 验证率50.0%)"
  }
}
```

---

## 功能测试

### 测试场景1：成功显示EdgeData启用

```
操作步骤：
1. 打开批量创建对话框
2. 选择有事件标签和有效manage的event
3. 点击"确认创建"

预期结果：
✅ 总边缘数: 2 或更多
✅ 验证率: 40-100%
✅ 输出状态: ✅ 启用edgedata输出 (N条已验证的边...) [绿色显示]
✅ F12 Console有日志输出
✅ 5秒后状态会刷新一次（动态轮询）
```

### 测试场景2：EdgeData禁用（无verified edges）

```
操作步骤：
1. 如果有某个event没有有效的edge聚合
2. 执行批量创建该event

预期结果：
✅ 总边缘数: 0
✅ 验证率: 0.0%
✅ 输出状态: ❌ 禁用edgedata输出 (无验证通过的边...) [红色显示]
✅ F12 Console有warning日志: "⚠️ EdgeData边缘数为0"
```

### 测试场景3：EdgeData配置缺失

```
操作步骤：
1. 修改scenarios为空数组（仅用于测试）
2. 执行批量创建

预期结果：
✅ 总边缘数: 0
✅ 验证率: 0.0%
✅ 输出状态: ⚠️ 未生成EdgeData配置 [灰色显示]
✅ F12 Console有log: "EdgeData显示信息: { edgeDataInfo: {} ... }"
```

---

## 后期维护

### 日志和监控

修改后，浏览器Console会输出调试信息：

```javascript
// 每次批量创建都会输出：
EdgeData显示信息: {
  statusText: "...",
  statusColor: "#...",
  edgeDataInfo: {...},
  should_enable: true/false,
  decision_action: "..."
}

// 如果边缘数为0也会输出warning：
⚠️ EdgeData边缘数为0，检查edgedata_info: {...}
```

### 性能影响

- ✅ 无性能影响（初始显示无额外开销）
- ✅ 动态轮询使用现有的API调用（单个GET /case/{id}）
- ✅ 浏览器Console日志可通过生产环境关闭

### 兼容性

- ✅ 向后兼容（如果没有edgedata_info会优雅降级）
- ✅ 支持所有现代浏览器（Chrome, Firefox, Safari, Edge）
- ✅ 移动设备友好

---

## 常见问题 (FAQ)

### Q1: 修改后需要重启服务吗？
**A**: 只需要清除浏览器缓存（Ctrl+Shift+R）。如果前端代码和后端代码都有改动，需要重启服务。

### Q2: 为什么有时候显示的是旧数据？
**A**: 浏览器可能缓存了响应。使用Ctrl+Shift+R强制刷新，或在开发者工具中禁用缓存。

### Q3: EdgeData信息在轮询时会变化吗？
**A**: 一般不会。EdgeData是在批量创建时生成的，之后不会改变。轮询只是为了确保显示最新的元数据状态。

### Q4: 如果edge_count为0怎么办？
**A**: 这说明事件标签或策略配置中没有有效的edge_id。需要检查：
- 事件location的edge_id是否在路网中存在
- 所有策略配置是否正确
- OD数据与事件标签是否匹配

### Q5: decision_action为空怎么办？
**A**: 这说明后端的should_enable_edgedata_output()函数没有正确生成action字符串。检查：
- shared/utilities/sumo_utils.py第73或79行
- 确保都有返回'action'字段

---

## 相关文档

| 文档 | 说明 |
|------|------|
| EDGEDATA_DYNAMIC_MONITORING.md | 动态监测实现详解 |
| EDGEDATA_DECISION_RULE_V2.md | P2 v2决策规则详解 |
| EDGEDATA_DISPLAY_TROUBLESHOOTING.md | 详细故障排除指南 |
| SESSION_FIXES_SUMMARY.md | 完整修复总结 |

---

## 成功标志 ✅

修复成功的标志：
1. ✅ 批量创建完成后，EdgeData监测信息明确显示
2. ✅ 能看到"✅ 启用edgedata输出 (N条已验证的边...)"
3. ✅ 按钮、数字和文本颜色正确（绿色=启用，红色=禁用）
4. ✅ F12 Console有调试日志
5. ✅ OD轮询期间EdgeData信息会自动刷新

---

**下一步**: 按照"实施步骤"逐步操作，然后根据"验证清单"确认修复成功。如有问题，参考"浏览器调试指南"或"常见问题"。

