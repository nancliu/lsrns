# EdgeData输出显示故障排除指南

**日期**: 2025-11-15
**问题**: 批量创建事件案例页面，没有监测到EdgeData输出已经启用
**状态**: 🔧 故障排除中

---

## 问题描述

用户报告：在批量创建事件案例的模态框中，**没有看到EdgeData输出已经启用的状态**。

这可能表现为：
- EdgeData监测信息区域为空
- 显示"禁用输出"但应该是"启用"
- 显示"未知状态"或"未生成EdgeData配置"

---

## 根本原因分析

EdgeData显示信息来自API响应中的`edgedata_info`字段。该字段在**初始API响应**中返回，包含以下信息：

### 数据流向

```
批量创建请求
  ↓
后端生成EdgeData配置（同步）
  ├─ 收集事件location
  ├─ 聚合所有策略的边缘
  ├─ 生成edgeData.add.xml文件
  └─ 调用should_enable_edgedata_output()决策
  ↓
返回edgedata_info到前端
  ├─ edge_count: 聚合的边数
  ├─ validation_rate: 验证通过率
  ├─ should_enable: 是否启用（true/false）
  ├─ decision_action: "✅ 启用edgedata输出 (N条已验证的边...)"
  └─ decision_reason: 决策原因
  ↓
前端显示在模态框中
```

---

## 可能的故障原因

### 1️⃣ 后端未生成EdgeData配置

**症状**: `edgedata_info` 为 `null/undefined`

**原因**:
- 没有scenarios（request.scenarios为空）
- EdgeData生成函数失败（但没有抛出异常）

**检查方式**:
```javascript
// 打开浏览器开发者工具 (F12) → Console
// 查看显示的日志：
// "EdgeData显示信息: { edgeDataInfo: {} ... }"
// 如果edgeDataInfo为空对象或undefined，检查后端日志
```

**后端日志检查**:
```bash
# 查看FastAPI服务日志
# 搜索: "EdgeData配置生成" 或 "EdgeData决策"
# 如果没有这些日志，说明没有进入EdgeData生成代码块
```

### 2️⃣ decision_action为空字符串

**症状**: 应该显示"✅ 启用edgedata输出..."但什么都没显示

**原因**:
- decision_action字段为空('')
- 后端返回的decision_action不包含预期的文本

**检查方式**:
```javascript
// 浏览器Console中查看：
// 如果看到: statusText: ""
// 说明decision_action为空
```

**解决方案**:
后端应该总是生成decision_action。如果为空，检查：
- `shared/utilities/sumo_utils.py` 第73行是否正确生成了action字符串
- `should_enable_edgedata_output()`函数是否被调用

### 3️⃣ should_enable逻辑错误

**症状**: 显示"✗ 禁用输出"但应该是启用

**原因**:
- edge_count = 0（没有验证通过的边）
- P2 v2规则判断：edge_count > 0 不满足

**检查方式**:
```javascript
// 浏览器Console中查看edgedata_info：
{
  edge_count: 0,           // ← 如果为0，会禁用
  validation_rate: 0.5,
  should_enable: false,    // ← 对应的决策
  decision_action: "❌ 禁用edgedata输出 (无验证通过的边...)"
}
```

**原因排查**:
1. OD数据与事件标签不匹配
2. 事件location的edge_id在路网中不存在
3. 所有管控策略都没有有效的edge_id

---

## 故障排除清单

### 步骤1: 确认API返回了edgedata_info

```bash
# 方法A：浏览器Network标签
1. 打开F12 → Network标签
2. 执行批量创建
3. 找到 POST /api/v1/scenario/create-case-batch 请求
4. 查看Response，搜索"edgedata_info"
   ✅ 如果有：edgedata_info { ... }
   ❌ 如果没有：edgedata_info: null
```

### 步骤2: 检查edgedata_info包含的内容

```javascript
// 方法B：浏览器Console
1. F12 → Console标签
2. 批量创建后，Console会显示日志：
   "EdgeData显示信息: { ... }"
3. 展开该对象，检查：
   ✅ edge_count > 0
   ✅ should_enable: true
   ✅ decision_action: "✅ 启用edgedata输出..."
```

### 步骤3: 检查后端EdgeData生成日志

```bash
# 查看FastAPI服务输出（应该能看到）：
INFO:api.services.case_service:✓ EdgeData配置生成: 2 edges
INFO:api.services.case_service:  ✅ 启用edgedata输出 (2条已验证的边, 验证率50.0%)

# 如果看不到这些日志：
# 说明EdgeData生成代码没有被执行（scenarios可能为空）
```

### 步骤4: 检查页面缓存

```bash
# 新代码可能被浏览器缓存
# 解决方式：
1. Hard refresh (Ctrl+Shift+R 或 Cmd+Shift+R)
2. 打开浏览器开发者工具
3. 禁用缓存 (Settings → Network → Disable cache)
4. 重新执行批量创建
```

### 步骤5: 检查scenarios是否为空

```bash
# 从API日志或前端验证
# POST /api/v1/scenario/create-case-batch 的request payload中：
{
  "event_id": "10754",
  "scenarios": [           # ← 必须不为空
    {
      "scenario_id": "scenario_10754_no_control",
      ...
    },
    ...                    # ← 至少需要一个scenario
  ]
}

# 如果scenarios为空，不会生成EdgeData
```

---

## 现象vs原因对应表

| 观察到的现象 | 可能的原因 | 检查方式 | 解决方案 |
|-----------|---------|--------|--------|
| 显示0条边，禁用输出 | edge_count=0（没有验证通过的边） | 检查事件location和策略配置 | 验证edge_id匹配 |
| 显示0条边，启用输出 | 不可能（P2 v2规则）| 检查是否手动修改了should_enable | 不要手动修改 |
| 什么都不显示（空白） | decision_action为空 | F12→Console | 检查后端生成逻辑 |
| 显示"未生成EdgeData配置" | edgedata_info为null | Network标签查看response | scenarios可能为空 |
| 显示启用但有N条边 | 正常！（P2 v2） | N/A | 这是预期行为 ✓ |

---

## 详细调试步骤

### 方法1：浏览器开发者工具

```javascript
// 1. 打开浏览器F12
// 2. 进入Console标签
// 3. 批量创建后，会自动输出日志：

EdgeData显示信息: {
  statusText: "✅ 启用edgedata输出 (2条已验证的边, 验证率50.0%)",
  statusColor: "#28a745",
  edgeDataInfo: {
    edge_count: 2,
    validation_rate: 0.5,
    should_enable: true,
    decision_action: "✅ 启用edgedata输出 (2条已验证的边, 验证率50.0%)",
    decision_reason: "Have verified edges (2), enable output for analysis"
  },
  should_enable: true,
  decision_action: "✅ 启用edgedata输出 (2条已验证的边, 验证率50.0%)"
}

// ✅ 如果看到这样的输出，表示前端代码正确运行
// ✅ 如果statusText为空，说明edgedata_info有问题
```

### 方法2：Network标签检查API响应

```
1. F12 → Network
2. 找到 POST /api/v1/scenario/create-case-batch
3. 点击该请求，查看Response标签
4. 搜索 "edgedata_info"

正常响应（✅）:
{
  "data": {
    "case_id": "case_event_10754",
    "edgedata_info": {
      "edge_count": 2,
      "validation_rate": 0.5,
      "should_enable": true,
      "decision_action": "✅ 启用edgedata输出 (2条已验证的边, 验证率50.0%)",
      ...
    }
  }
}

异常响应（❌）:
{
  "data": {
    "case_id": "case_event_10754",
    "edgedata_info": null
  }
}
```

### 方法3：查看后端日志

```bash
# 启动FastAPI服务时的输出（Windows PowerShell）：
PS> .\\start_api.ps1

# 在服务输出中搜索这些日志：
INFO:api.services.case_service:开始批量创建事件案例: event_id=10754, scenarios=3
INFO:api.services.case_service:✓ EdgeData配置生成: 2 edges
INFO:api.services.case_service:  ✅ 启用edgedata输出 (2条已验证的边, 验证率50.0%)

# 如果看不到EdgeData相关的日志：
# 1. 检查scenarios是否为空
# 2. 检查是否有异常（Exception...）
```

---

## 常见解决方案

### 方案1：清除浏览器缓存

```bash
# Windows Chrome
Ctrl + Shift + Del  # 打开清除浏览器数据对话框
# 选择 "所有时间"，勾选 "缓存的图片和文件"，点击清除

# 或使用Hard Refresh
Ctrl + Shift + R    # 强制刷新，忽略缓存
```

### 方案2：检查scenarios数据

```javascript
// 在发送请求前，检查scenarios是否为空
// 在scenario_browser.js中，找到创建请求的地方
// 确保scenarios数组不为空
```

### 方案3：重启FastAPI服务

```bash
# 如果后端代码有更新但服务未重新加载
cd D:\\projects\\OD_SIM
.\\start_api.ps1  # 重启服务
```

### 方案4：检查网络状态

```bash
# 如果API调用超时或失败
# 打开F12 → Network → 检查HTTP状态码
# ✅ 200-299: 成功
# ❌ 4xx: 请求错误
# ❌ 5xx: 服务器错误
```

---

## 最新改进（2025-11-15）

### 改进1：更详细的初始显示

修改了`showBatchCreationComplete()`函数，现在会：
- 使用完整的`decision_action`文本（如果可用）
- 设置正确的颜色编码（绿色=启用，红色=禁用）
- 添加调试日志到浏览器Console

### 改进2：动态轮询支持

添加了`pollEdgeDataInfo()`函数，会在OD轮询期间定期刷新EdgeData显示。

### 改进3：更好的错误处理

如果`edgedata_info`为null，显示"⚠️ 未生成EdgeData配置"而不是空白。

---

## 调试输出示例

### ✅ 成功案例

```
创建事件案例 → 完成
├─ 创建结果: case_event_10754
├─ 成功: 3/3场景
├─ EdgeData显示:
│  ├─ 总边缘数: 2
│  ├─ 验证率: 50.0%
│  └─ 输出状态: ✅ 启用edgedata输出 (2条已验证的边, 验证率50.0%) [绿色]
└─ OD生成状态: ⏳ 处理中...

浏览器Console输出:
EdgeData显示信息: {
  statusText: "✅ 启用edgedata输出 (2条已验证的边, 验证率50.0%)",
  statusColor: "#28a745",
  edgeDataInfo: { edge_count: 2, should_enable: true, ... }
}
```

### ❌ 失败案例1：无verified edges

```
创建事件案例 → 完成
├─ 创建结果: case_event_10755
├─ 成功: 3/3场景
├─ EdgeData显示:
│  ├─ 总边缘数: 0
│  ├─ 验证率: 0.0%
│  └─ 输出状态: ❌ 禁用edgedata输出 (无验证通过的边...) [红色]
└─ OD生成状态: ⏳ 处理中...

浏览器Console输出:
⚠️ EdgeData边缘数为0，检查edgedata_info: { edge_count: 0, should_enable: false, ... }
```

### ❌ 失败案例2：edgedata_info为null

```
创建事件案例 → 完成
├─ 创建结果: case_event_10756
├─ 成功: 3/3场景
├─ EdgeData显示:
│  ├─ 总边缘数: 0
│  ├─ 验证率: 0.0%
│  └─ 输出状态: ⚠️ 未生成EdgeData配置 [灰色]
└─ OD生成状态: ⏳ 处理中...

浏览器Console输出:
EdgeData显示信息: { edgeDataInfo: {}, should_enable: undefined, ... }
```

---

## 相关文件

| 文件 | 修改内容 |
|------|--------|
| frontend/scenarios/scenario_browser.js | 改进showBatchCreationComplete()、添加pollEdgeDataInfo()、updateEdgeDataDisplay() |
| shared/utilities/sumo_utils.py | should_enable_edgedata_output()函数（P2 v2规则） |
| api/services/case_service.py | 创建batch时的edgedata_info生成（第1569-1579行） |

---

## 后续改进建议

### 短期
- [ ] 添加EdgeData生成过程的详细日志
- [ ] 在模态框中显示EdgeData生成失败的具体原因
- [ ] 提供"重新生成EdgeData"的选项

### 中期
- [ ] WebSocket实时推送EdgeData生成进度
- [ ] 显示EdgeData的详细分析结果（边的来源、验证情况等）

### 长期
- [ ] 支持用户自定义EdgeData聚合规则
- [ ] 支持多个EdgeData配置方案选择

---

## 快速诊断流程图

```
问题: 看不到EdgeData启用状态
  │
  ├─→ F12 → Console看是否有日志？
  │   ├─→ 有日志: decision_action字段是否为空？
  │   │   ├─→ 不为空：✅ 前端代码正常，检查显示问题
  │   │   └─→ 为空：❌ 后端decision_action生成有问题
  │   └─→ 无日志：❌ 前端代码没执行（可能缓存问题）
  │       └─→ 解决：Ctrl+Shift+R清缓存并刷新
  │
  ├─→ Network看API Response的edgedata_info？
  │   ├─→ edgedata_info存在且有值：✅ 后端正常
  │   │   └─→ 继续查看decision_action
  │   └─→ edgedata_info为null：❌ scenarios可能为空
  │       └─→ 检查scenarios数组不为空
  │
  └─→ 都确认没问题：检查后端日志是否有错误
      └─→ 重启FastAPI服务试试
```

---

**建议下一步**: 按照"快速诊断流程图"逐步检查，然后在浏览器Console中执行步骤1的检查，获取详细的edgedata_info数据，这样就能快速定位问题。

---

**相关阅读**:
- `EDGEDATA_DYNAMIC_MONITORING.md` - 动态监测实现
- `EDGEDATA_DECISION_RULE_V2.md` - P2 v2决策规则
- `SESSION_FIXES_SUMMARY.md` - 完整修复总结
