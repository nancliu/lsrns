# Batch 目录路径修复 - 2025-11-05

**问题**: Strategy Ranking API 找不到存在的 batch
**错误信息**: `404 Not Found: 批次不存在: batch_20251105_000102`
**根本原因**: 代码中的目录路径与实际结构不一致
**状态**: ✅ 已修复
**Commit**: 39607bf

---

## 问题诊断

### 实际发生的情况

1. **Batch 确实存在**
   ```
   cases/case_20251103_141612/simulations/plan_opti/batch_20251105_000102/
   ```

2. **代码期望的路径**
   ```
   cases/case_20251103_141612/simulations/batch_20251105_000102/
   ```

3. **缺少的路径段**
   ```
   plan_opti/  ← 代码中没有这一层
   ```

### 错误产生的原因

**文件**: `api/routes/batch_optimization_routes.py:463`

```python
batch_dir = case_dir / "simulations" / batch_id  # ❌ 缺少 "plan_opti"
if not batch_dir.exists():
    raise FileNotFoundError(f"批次不存在: {batch_id}")
```

虽然 batch 目录确实存在，但代码找错了地方，所以返回 404。

---

## 实际的目录结构

```
cases/
└── case_20251103_141612/
    ├── config/
    ├── metadata.json
    ├── simulations/
    │   ├── sim_1104_062836528_micro/  (旧的单次仿真)
    │   ├── simulations_index.json
    │   └── plan_opti/
    │       ├── batch_20251105_000102/  ← Batch 在这里！
    │       ├── batches_index.json
    │       └── ... (其他 batches)
    └── analysis/
```

关键点：
- Batch 存储在 `simulations/plan_opti/` 下
- 不是直接在 `simulations/` 下

---

## 修复

### 修改位置

**文件**: `api/routes/batch_optimization_routes.py`
**行号**: 463
**Commit**: 39607bf

### 修改前

```python
batch_dir = case_dir / "simulations" / batch_id
```

### 修改后

```python
batch_dir = case_dir / "simulations" / "plan_opti" / batch_id
```

### 验证

修改后，路径变为：
```
case_dir / "simulations" / "plan_opti" / batch_id
= cases/case_20251103_141612/simulations/plan_opti/batch_20251105_000102
```

这样就能正确找到 batch 了。

---

## 为什么之前没有发现这个 bug？

### 代码中的不一致性

虽然 `rank_strategies` 函数有 bug，但其他地方用了正确的路径：

**正确的例子** (`batch_optimization_routes.py:59`):
```python
metadata_path = case_dir / "simulations" / "plan_opti" / batch_id / "batch_metadata.json"
```

**错误的例子** (`batch_optimization_routes.py:463`):
```python
batch_dir = case_dir / "simulations" / batch_id  # ❌ 缺少 plan_opti
```

这说明：
1. **Batch 创建时** 用了 `plan_opti`
2. **Batch 获取结果时** 也用了 `plan_opti`
3. **但 Strategy Ranking 时** 忘了用 `plan_opti`

### 为什么现在才发现？

Strategy Ranking 是新功能，之前没有人调用它，所以 bug 一直隐藏着。现在集成后才被暴露出来。

---

## 修复步骤

### 1. 已完成：代码修改
✅ 修改了 `api/routes/batch_optimization_routes.py`

### 2. 需要执行：重启 API 服务器

```bash
# 停止当前服务
Ctrl+C

# 重启
.\start_api.ps1
# 或
python api/main.py
```

**为什么需要重启？** Python 代码修改需要重新加载模块。

### 3. 需要执行：清除浏览器缓存

```
Ctrl+Shift+Delete
选择"所有时间"
清除"Cookies and cached images and files"
```

**为什么需要清除？** 确保加载最新的 HTML/JS 文件。

### 4. 需要执行：重新测试

访问：
```
http://localhost:8000/control/optimization.html?batch_id=batch_20251105_000102&case_id=case_20251103_141612
```

**预期结果**:
- ✅ 不再出现 404 错误
- ✅ 显示"正在生成优化方案..."加载指示器
- ✅ 3-5 秒后显示排序结果

---

## 技术细节

### Batch 创建流程

```python
# 创建 batch 时的目录结构
case_dir / "simulations" / "plan_opti" / batch_id
```

这个结构在多个地方被使用：
1. ✅ `create_batch()` - 创建 batch
2. ✅ `get_batch_progress()` - 获取进度
3. ✅ `get_batch_results()` - 获取结果
4. ❌ `rank_strategies()` - 排序策略 (有 bug)

现在都修复了。

### 为什么叫 "plan_opti"？

`plan_opti` 可能代表 "Plan Optimization"（方案优化），这与 Layer 2 的功能相符。

---

## 相关的其他修复

这次修复与之前的修复相关但独立：

| 修复 | 问题 | 原因 |
|-----|------|------|
| URL 路由前缀 | `/control/batch-optimization` 缺失 | 前端 URL 错误 |
| 全局变量冲突 | 脚本加载顺序 | JavaScript 设计问题 |
| **Batch 目录路径** | **`plan_opti` 缺失** | **Python 代码 bug** |

现在三个问题都已解决。

---

## 验证清单

- [ ] API 服务器已重启
- [ ] 浏览器缓存已清除
- [ ] 打开开发者工具 (F12)
- [ ] 进入 Network 标签
- [ ] 访问 optimization.html
- [ ] 检查 POST 请求
  - [ ] URL 应该包含 `/control/batch-optimization/`
  - [ ] 状态应该是 200 (不是 404)
  - [ ] 响应应该包含排序结果
- [ ] 应该能看到加载指示器
- [ ] 应该能看到排序表格
- [ ] 应该能看到推荐等级
- [ ] 应该能看到雷达图

---

## 总结

### ✅ 问题解决

1. **根本原因找到**: Batch 在 `plan_opti/` 下，但代码没有找对路径
2. **代码修复**: 添加 `plan_opti` 路径段
3. **影响范围**: 仅涉及 Strategy Ranking 功能，其他功能不受影响

### 🚀 立即行动

1. 重启 API 服务器
2. 清除浏览器缓存
3. 重新加载 optimization.html
4. Strategy Ranking 应该能正常工作了！

---

**修复完成日期**: 2025-11-05
**Commit**: 39607bf
**状态**: ✅ 代码修复完成，等待服务器重启和测试

