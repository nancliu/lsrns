# Plan IDs 配置来源修复 - 2025-11-05

**问题**: Strategy Ranking API 找不到任何方案
**错误信息**: `400 Bad Request: 未找到任何方案`
**根本原因**: 代码读取的配置文件错误，且该文件中没有所需数据
**状态**: ✅ 已修复
**Commit**: 37c6a83

---

## 问题诊断

### 错误发生的过程

1. ✅ API 路由找对了
2. ✅ Batch 目录找到了
3. ❌ 尝试读取方案列表时失败

### 根本原因

**代码期望的**: 从 `simulation_config.json` 读取 `plan_configs` 字段

```python
config_path = batch_dir / "simulation_config.json"
with open(config_path) as f:
    config = json.load(f)
    plan_ids = list(config.get("plan_configs", {}).keys())  # ❌ 这个字段不存在
```

**实际的**: `simulation_config.json` 中没有 `plan_configs` 字段

```json
{
  "output_level": null,
  "num_seeds": 3,
  "base_seed": 66,
  "output_tripinfo": true,
  "output_edgedata": true,
  "simulation_duration": { ... },
  "simulation_params": { ... }
  // ❌ 没有 "plan_configs" 字段
}
```

### 正确的位置

**方案列表实际在**: `batch_metadata.json` 文件中

```json
{
  "batch_id": "batch_20251105_000102",
  "case_id": "case_20251103_141612",
  "plan_ids": [         // ✅ 在这里！
    "baseline_plan",
    "plan_dhs_morning_peak_severe",
    "plan_tec_morning_peak_severe",
    "plan_vss_dhs_morning_peak_severe",
    "plan_vss_morning_peak_severe"
  ],
  "num_seeds": 3,
  "base_seed": 66,
  "total_tasks": 15,
  "status": "completed",
  ...
}
```

---

## 文件对比

### simulation_config.json

**内容**: 仿真参数和配置
```json
{
  "output_level": null,
  "num_seeds": 3,
  "base_seed": 66,
  "output_tripinfo": true,
  "output_edgedata": true,
  "simulation_params": { ... }
}
```

**用途**: 仿真运行的配置参数

**包含内容**: 不包含 plan_ids

### batch_metadata.json

**内容**: Batch 的元数据
```json
{
  "batch_id": "batch_20251105_000102",
  "case_id": "case_20251103_141612",
  "plan_ids": [
    "baseline_plan",
    "plan_dhs_morning_peak_severe",
    ...
  ],
  "status": "completed",
  ...
}
```

**用途**: 存储 batch 的信息，包括所有方案列表

**包含内容**: 包含 plan_ids、状态、创建/完成时间等

---

## 修复

### 修改位置

**文件**: `api/routes/batch_optimization_routes.py`
**行数**: 467-481
**Commit**: 37c6a83

### 修改前

```python
# 读取 simulation_config.json（错误的地方）
config_path = batch_dir / "simulation_config.json"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        plan_ids = list(config.get("plan_configs", {}).keys())  # ❌ 这个字段不存在
```

### 修改后

```python
# 读取 batch_metadata.json（正确的地方）
metadata_path = batch_dir / "batch_metadata.json"
if metadata_path.exists():
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
        plan_ids = metadata.get("plan_ids", [])  # ✅ 这个字段存在
```

---

## 为什么会犯这个错误？

### 设计和实现的差异

在设计 batch 的数据结构时，方案信息应该存在。但实际实现中：

1. **设计时**: 可能假设方案信息在 simulation_config.json 中
2. **实现时**: 实际把方案信息放在 batch_metadata.json 中（更合理）
3. **新功能**: Strategy Ranking 是新功能，代码写得时候用了设计时的假设，而不是实际的实现

### 为什么之前没发现？

因为 Strategy Ranking 是新功能，之前没有人调用 `rank_strategies` 函数，所以这个 bug 一直隐藏着。

---

## 修复步骤

### 1. 代码已修改 ✅
修改了 `api/routes/batch_optimization_routes.py`

### 2. 需要重启 API 服务器 ⏳

```bash
# 停止当前服务
Ctrl+C

# 重启
.\start_api.ps1
```

### 3. 清除浏览器缓存 ⏳

```
Ctrl+Shift+Delete
```

### 4. 重新加载页面 ⏳

```
http://localhost:8000/control/optimization.html?batch_id=batch_20251105_000102&case_id=case_20251103_141612
```

---

## 预期结果

重启 API 服务器后：

1. ✅ 不再出现 "未找到任何方案" 错误
2. ✅ API 能正确读取 5 个方案：
   - baseline_plan
   - plan_dhs_morning_peak_severe
   - plan_tec_morning_peak_severe
   - plan_vss_dhs_morning_peak_severe
   - plan_vss_morning_peak_severe
3. ✅ 显示排序结果

---

## 相关文件对照

| 文件 | 内容 | 访问时机 |
|------|------|----------|
| `simulation_config.json` | 仿真参数 | 创建仿真时 |
| `batch_metadata.json` | Batch 信息 + 方案列表 | Strategy Ranking 时 |
| `batch_progress.json` | Batch 进度 | 轮询进度时 |
| `batch_results_cache.json` | 结果缓存 | 获取结果时 |

---

## 验证清单

- [ ] API 服务器已重启
- [ ] 浏览器缓存已清除
- [ ] 打开开发者工具 (F12 → Console)
- [ ] 访问 optimization.html
- [ ] 查看 Network 标签
  - [ ] POST 请求状态应该是 200 (不是 400)
  - [ ] 响应应该包含排序结果
- [ ] 应该能看到以下内容：
  - [ ] 加载指示器消失
  - [ ] 排序表格显示 5 个方案
  - [ ] 推荐等级显示
  - [ ] 雷达图和对比图显示

---

## 总结

### ✅ 问题解决

1. **错误的文件**: simulation_config.json
   - 问题: 没有 plan_configs 字段
   - 原因: 该文件只存储仿真参数

2. **正确的文件**: batch_metadata.json
   - 包含: plan_ids 列表
   - 用途: 存储 batch 的完整信息

3. **修复**: 改为读取 batch_metadata.json 中的 plan_ids

### 🚀 立即行动

1. 重启 API 服务器
2. 清除浏览器缓存
3. 重新加载 optimization.html
4. Strategy Ranking 应该能正常工作了！

---

**修复完成日期**: 2025-11-05
**Commit**: 37c6a83
**状态**: ✅ 代码修复完成，等待服务器重启和测试

