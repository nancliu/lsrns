# 批次结果页面仿真配置显示 - 诊断指南

**日期**: 2025-11-04
**问题**: 仿真配置卡片只显示种子数和起始种子，缺少仿真时长和输出配置
**状态**: 🔍 诊断中

---

## 🔍 诊断步骤

### 第一步：打开浏览器开发者工具

1. 打开批次结果页面
2. 按 `F12` 或 `Ctrl+Shift+I` 打开开发者工具
3. 切换到 **Console** 标签页

### 第二步：查看调试日志

当页面加载时，应该看到以下调试日志：

```
[DEBUG] Batch simulation config: {
  num_seeds: 3,
  base_seed: 66,
  simulation_duration: {...},
  output_config: {...}
}
```

### 第三步：分析日志内容

#### 情况1️⃣: `simulation_duration` 为 `undefined` 或 `null`
```
[DEBUG] simulation_duration not available: undefined
```

**原因**: 后端API未返回此字段或值为空
**解决**: 检查batch_metadata.json中是否存储了这个字段

#### 情况2️⃣: `simulation_duration` 不是对象格式
```
[DEBUG] simulation_duration displayed: "4h 0m"
```

**说明**: 数据格式正确，应该显示了仿真时长
**检查**: 在页面上查看是否真的显示了仿真时长

#### 情况3️⃣: `output_config` 为 `undefined` 或 `null`
```
[DEBUG] output_config not available or empty: {}
```

**原因**: 后端API未返回此字段或为空对象
**解决**: 检查batch_metadata.json中的output_config内容

#### 情况4️⃣: `output_config` 有内容但没有启用任何选项
```
[DEBUG] output_config has no enabled options
```

**原因**: output_config 对象中所有output_*字段都为false
**解决**: 检查创建批次时是否传入了正确的output_config

#### 情况5️⃣: 输出配置正确显示
```
[DEBUG] output_config displayed: ['✓ tripinfo', '✓ E1检测器', '✓ edgedata', '✓ summary']
```

**说明**: 数据格式正确，应该显示了输出配置

---

## 🛠️ 进阶诊断

### 检查完整的API响应

在浏览器开发者工具的 **Network** 标签页中：

1. 找到 `/control/batch-optimization/batch/{batchId}/results` 请求
2. 点击该请求
3. 查看 **Response** 标签页
4. 搜索以下字段：
   - `simulation_duration`
   - `output_config`

### 预期的响应格式

```json
{
  "batch_id": "batch_20251104_001",
  "num_seeds": 3,
  "base_seed": 66,
  "simulation_duration": {
    "hours": 4,
    "minutes": 0,
    "total_minutes": 240
  },
  "output_config": {
    "output_tripinfo": true,
    "output_emission": true,
    "output_edgedata": true,
    "output_netstate": true,
    "output_vehroute": false,
    "output_fcd": false
  },
  ...
}
```

---

## 📋 检查清单

当看不到仿真时长和输出配置时，按顺序检查：

### 后端数据存储 (batch_metadata.json)

```bash
# 查看批次元数据文件
cat /path/to/case_id/simulations/plan_opti/batch_id/batch_metadata.json
```

检查是否包含：
- [ ] `"simulation_duration": { "hours": ..., "minutes": ... }`
- [ ] `"output_config": { "output_tripinfo": true, ... }`

### 后端API响应

检查 `get_batch_results()` 方法是否返回了这些字段：
- [ ] `simulation_duration` (line 1420 in batch_optimization_service.py)
- [ ] `output_config` (line 1422 in batch_optimization_service.py)

### 前端显示逻辑

检查 `renderBatchInfoPanel()` 函数：
- [ ] 有仿真时长的条件判断 (line 224)
- [ ] 有输出配置的条件判断 (line 237)
- [ ] 类型检查正确 (`typeof === 'object'`)

---

## 🔐 数据流完整性验证

```
Batch创建时
  ↓
simulation_duration 和 output_config 保存到 batch_metadata.json
  ↓
get_batch_results() 读取 batch_metadata.json
  ↓
这两个字段包含在API响应中
  ↓
前端 renderBatchInfoPanel() 接收数据
  ↓
条件判断检查数据可用性
  ↓
如果数据存在且有效 → 显示
  ↓
如果数据不存在或无效 → 打印DEBUG日志
```

---

## 📊 常见问题及解决方案

### 问题1: 看到 DEBUG 日志但页面上不显示

**可能原因**:
1. CSS 样式隐藏了内容（不太可能）
2. HTML 生成了但渲染有问题
3. 浏览器缓存

**解决方案**:
1. 清除浏览器缓存 (`Ctrl+Shift+Delete`)
2. 硬刷新页面 (`Ctrl+Shift+R`)
3. 在浏览器开发者工具检查页面元素 (F12 → Elements)
4. 搜索 `仿真时长` 或 `仿真输出配置` 查看是否存在于DOM中

### 问题2: 日志显示数据不可用

**可能原因**:
1. batch_metadata.json 中这些字段为空或未保存
2. 创建批次时没有提供这些参数
3. 旧批次没有这些数据

**解决方案**:
1. 创建一个新批次，确保提供完整的 output_config 和 simulation_duration
2. 验证新创建批次的 batch_metadata.json 文件内容
3. 检查 API 创建批次的请求参数

### 问题3: 显示格式不正确

**症状**: 看到 DEBUG 日志表示数据已显示，但格式不对

**可能原因**:
1. simulation_duration 格式不是 `{hours: X, minutes: Y}`
2. output_config 中的字段名不匹配 (拼写错误)
3. 字段值类型不对 (应为 boolean)

**解决方案**:
1. 在浏览器控制台打印实际数据: `console.log(batchData.simulation_duration)`
2. 检查字段名拼写是否正确
3. 确认 output_config 中的布尔值正确

---

## 🧪 快速测试命令

在浏览器开发者工具 Console 中，可以直接测试：

```javascript
// 测试数据是否存在
console.log('simulation_duration:', batchResultsData?.simulation_duration);
console.log('output_config:', batchResultsData?.output_config);

// 测试条件判断
console.log('simulation_duration 是否有效:',
  batchResultsData?.simulation_duration &&
  typeof batchResultsData.simulation_duration === 'object'
);

console.log('output_config 是否有效:',
  batchResultsData?.output_config &&
  typeof batchResultsData.output_config === 'object' &&
  Object.keys(batchResultsData.output_config).length > 0
);
```

---

## 📝 调试日志记录

当向技术支持报告问题时，请提供：

1. **浏览器 Console 的完整日志输出**:
   ```
   [DEBUG] Batch simulation config: {...}
   [DEBUG] simulation_duration displayed/not available: ...
   [DEBUG] output_config displayed/not available: ...
   ```

2. **Network 标签中 API 响应的完整 JSON** (至少 simulation_duration 和 output_config 部分)

3. **batch_metadata.json 的内容** (可通过服务器文件系统查看)

4. **页面HTML源代码中的仿真配置卡片内容** (F12 → Elements → 搜索 "仿真配置")

---

## ✅ 预期结果

修复后的页面应该显示：

```
⚙️ 仿真配置
├─ 种子数: 3
├─ 起始种子: 66
├─ 仿真时长: 4h 0m          ← 新增（目前缺失）
└─ 仿真输出配置:             ← 新增（目前缺失）
   ├─ ✓ tripinfo
   ├─ ✓ E1检测器
   ├─ ✓ edgedata
   └─ ✓ summary
```

---

**诊断工具已准备就绪。请按照上述步骤诊断问题，并使用生成的日志信息来定位根本原因。**

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
