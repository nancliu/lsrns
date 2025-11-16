# case-simulation-center.html 范围定义

**最关键的一个原则**：

## ⚠️ 核心规则

**case-simulation-center.html 只管理和监测事件案例批次。**

---

## ✅ 什么是"事件案例批次"？

事件案例批次是通过以下流程创建的：

```
1. 用户发现一个交通事件
   ↓
2. 在系统中创建"事件"记录（event_8210655）
   ↓
3. 为该事件定义多个"应对场景"
   ↓
4. 为每个场景创建"仿真案例"
   ↓
5. 通过 /api/batch/create-from-event API 创建事件批次
   ↓
6. 返回一个 batch_id（格式：batch_event_8210655_20251115_100000）
   ↓
7. 这个批次包含该事件下的所有案例和仿真
```

**关键点**：事件批次的所有案例和仿真都来自同一个事件。

---

## ❌ case-simulation-center.html 不做什么

### 1. 不管理优化批次

```javascript
❌ 不支持这样的工作流：
   用户手动选择多个仿真 → 创建优化批次 → 启动

✅ 这是后续"方案优化"工作的范围，不在 Phase 2 中
```

### 2. 不处理用户手动仿真选择

```javascript
❌ case-simulation-center.html 中不会出现：
   - 复选框选择仿真
   - "创建自定义批次"按钮
   - "导入仿真列表"功能

✅ 案例列表来自事件，不是用户手动选择的
```

### 3. 不进行方案优化

```javascript
❌ case-simulation-center.html 不包含：
   - 方案参数调整界面
   - 方案效果排名
   - "推荐最优方案"功能
   - 成本效益分析

✅ 这些属于"方案优化管理"，是后续的独立项目
```

### 4. 不管理控制策略

```javascript
❌ case-simulation-center.html 不包含：
   - VSS/TEC/DHS 策略的创建和编辑
   - 策略参数库
   - 策略版本管理

✅ 这些属于"控制策略管理"，是独立模块
```

---

## ✅ case-simulation-center.html 要做什么

### 1. 管理事件批次的案例列表

```javascript
// 页面加载时：
1. 接收事件 ID 或批次 ID
2. 调用 API 获取该事件的所有案例
3. 显示案例列表
   - 案例 ID
   - 场景名称
   - 控制策略
   - 创建时间
```

### 2. 批量启动事件仿真

```javascript
// 用户操作：
1. 多选案例（可选）
2. 点击"启动"按钮
3. 弹窗确认
4. 调用 /api/batch/start-batch（传递 batch_id）
5. 监控面板自动打开
```

### 3. 实时监控仿真进度

```javascript
// 展开/折叠式面板：
1. 折叠状态：进度条 + 统计卡片
   - 总仿真数
   - 已完成数
   - 运行中数
   - 失败数

2. 展开状态：详细表格
   - 仿真 ID
   - 状态（运行中/已完成/失败）
   - 进度百分比
   - "查看分析"按钮

3. 根据展开/折叠状态调整刷新频率：
   - 展开：5-10 秒
   - 折叠：30 秒
```

### 4. 跳转到分析页面

```javascript
// 用户点击"查看分析"按钮：
1. 获取 case_id 和 simulation_id
2. 跳转到 analysis_viewer.html
3. 传递 URL 参数：
   ?case_id=case_001&simulation_id=sim_001
```

---

## 🎯 工作流示意

```
事件发生
  ↓
创建事件（event_8210655）
  ↓
定义应对场景 → 创建案例
  ↓
通过 /api/batch/create-from-event 创建批次
  ↓
获得 batch_id（batch_event_8210655_...）
  ↓
▶︎ case-simulation-center.html 接管 ◀︎
  ├─ 显示事件的所有案例列表
  ├─ 支持多选和批量启动
  ├─ 实时监控进度（展开/折叠面板）
  └─ 提供"查看分析"入口
  ↓
用户点击"查看分析"
  ↓
跳转到 analysis_viewer.html
  ├─ 查看单案例分析
  └─ 对比多个事件应对方案

（不涉及方案优化或控制策略管理）
```

---

## 🚨 常见错误检查

### 错误 1：混淆"事件批次"和"优化批次"

```javascript
❌ 错误想法：
   case-simulation-center.html 应该支持创建任意仿真的批次

✅ 正确想法：
   case-simulation-center.html 只显示事件创建的批次
```

### 错误 2：添加"选择仿真"功能

```javascript
❌ 错误代码：
   document.getElementById('simulationSelector').addEventListener('change', () => {
     // 让用户手动选择仿真？不应该！
   });

✅ 正确想法：
   仿真列表由事件确定，不由用户选择
```

### 错误 3：实现"批次对比优化"功能

```javascript
❌ 错误代码：
   function optimizeBatchStrategy() {
     // 尝试推荐最优方案？不在范围内！
   }

✅ 正确想法：
   只显示对比数据，不做优化推荐
```

### 错误 4：添加"策略编辑"功能

```javascript
❌ 错误代码：
   <button onclick="editStrategy()">编辑控制策略</button>

✅ 正确想法：
   策略由已有的方案确定，不在此页面编辑
```

---

## 📋 实现检查清单

在开发 case-simulation-center.html 时，检查：

- [ ] 页面接收 event_id 或 batch_id 作为参数
- [ ] 案例列表来自 API，不是硬编码
- [ ] 支持多选和批量启动（传递 batch_id 给 /api/batch/start-batch）
- [ ] 展开/折叠式进度监控面板正常工作
- [ ] 根据展开/折叠状态调整刷新频率
- [ ] "查看分析"按钮能正确跳转到 analysis_viewer
- [ ] 页面中**没有**任何优化、策略编辑、方案推荐的功能
- [ ] 所有UI元素都与"事件影响分析"相关，不与"方案优化"相关

---

## 🔗 关联文档

- [SCOPE_CLARIFICATION.md](SCOPE_CLARIFICATION.md) - 详细的范围界定
- [BATCH_ID_CLARIFICATION.md](BATCH_ID_CLARIFICATION.md) - 批次 ID 的用法区别
- [README.md](README.md) - 总体指南

---

**版本**: 1.0
**创建日期**: 2025-11-16
**适用范围**: Phase 2 开发期间
**重要性**: 🔴 关键 - 定义了这个项目的核心边界
