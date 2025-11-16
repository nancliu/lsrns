# EdgeData规则更新 - 需要重启服务

**时间**: 2025-11-15
**问题**: 新规则代码已修改，但现有/新创建的cases仍显示旧规则结果
**原因**: FastAPI服务还在运行旧的Python代码
**解决方案**: 重启FastAPI服务

---

## 问题现象

新创建的case（如case_event_10754）显示：
```
总边缘数: 2
验证率: 50.0%
输出状态: ✗ 禁用输出
```

但根据P2 v2新规则，应该显示：
```
总边缘数: 2
验证率: 50.0%
输出状态: ✅ 启用输出
```

---

## 根本原因

**代码已修改但进程未重新加载**

```
修改时间:    2025-11-15 XX:XX:XX
修改文件:    shared/utilities/sumo_utils.py
修改内容:    should_enable_edgedata_output() 函数规则升级

当前问题:    FastAPI服务进程还在运行修改前的代码
```

---

## 解决方案

### 步骤1: 停止FastAPI服务

**Windows (PowerShell)**:
```powershell
# 找到运行FastAPI的进程
Get-Process python | Where-Object {$_.Path -like "*start_api*"}

# 停止进程
Stop-Process -Id <PID>
```

或者直接按 `Ctrl+C` 停止运行的FastAPI窗口。

### 步骤2: 重启FastAPI服务

```powershell
cd "D:\projects\OD_SIM"
.\start_api.ps1
```

或

```bash
conda activate od_project
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 步骤3: 验证服务重启

- 打开浏览器访问: http://localhost:8000
- 查看FastAPI自动文档: http://localhost:8000/docs
- 应该看到新的API文档

### 步骤4: 重新创建case测试

创建新的批量案例，验证EdgeData输出状态：

**预期结果**：
```
总边缘数: 2
验证率: 50.0%
输出状态: ✅ 启用输出
```

---

## 验证清单

### ✅ 代码修改已完成

```python
# 文件: shared/utilities/sumo_utils.py
# 函数: should_enable_edgedata_output()

# 旧规则 (P2 v1)
should_enable = edge_count >= 10 AND validation_rate >= 0.5

# 新规则 (P2 v2) - 已更新
should_enable = edge_count > 0
```

### ✅ 现有cases已更新

```python
# 脚本: update_edgedata_rule.py
# 已运行并更新以下cases:
# - case_event_12028: False → True
# - 其他cases: 已自动适应或无需更新

# 结果: 1个已更新, 8个无需更新
```

### ⏳ 待完成: 重启FastAPI服务

服务重启后，新创建的cases会使用新规则。

---

## 时间线

```
11:15 AM - 代码修改完成
11:20 AM - 脚本运行，更新现有cases
11:25 AM - 用户重新创建case_event_10754
11:26 AM - 发现仍显示旧规则 → 需要重启服务 ⚠️
11:30 AM - 需要重启FastAPI服务
```

---

## 重启后会发生什么？

### 新的案例行为

```
1. 用户创建批量案例
   ↓
2. 后端调用 should_enable_edgedata_output(edge_count=2, validation_rate=0.5)
   ↓
3. P2 v2规则执行: edge_count > 0? ✓ (2 > 0)
   ↓
4. should_enable = True
   ↓
5. metadata保存: "should_enable": true
   ↓
6. 前端显示: "✅ 启用edgedata输出"
```

### 现有案例的变化

已更新的cases（case_event_12028等）会立即应用新规则。

---

## 常见问题

### Q1: 为什么还是显示旧规则结果？

**A**: FastAPI服务进程还在运行旧代码。Python程序需要重新启动才能加载新的源代码。

### Q2: 重启后需要重新创建cases吗？

**A**: 不需要。重启后新创建的cases会自动使用新规则。

### Q3: 已经存在的case会自动应用新规则吗？

**A**: 已更新的metadata.json会应用新规则，但显示需要重新创建case或手动刷新才能看到。

---

## 命令参考

### Windows

**停止服务**:
```powershell
taskkill /IM python.exe /F
# 或在FastAPI窗口按 Ctrl+C
```

**启动服务**:
```powershell
cd D:\projects\OD_SIM
.\start_api.ps1
```

### Linux/Mac

**停止服务**:
```bash
pkill -f "uvicorn"
# 或在终端按 Ctrl+C
```

**启动服务**:
```bash
cd /path/to/OD_SIM
conda activate od_project
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 验证服务已重启

访问这个URL检查API是否更新：

```
http://localhost:8000/api/v1/case/list_cases/
```

如果能访问且返回正确的case列表，说明服务已成功重启。

---

## 下一步

1. ✅ 重启FastAPI服务
2. ✅ 重新创建case_event_10754
3. ✅ 验证EdgeData显示"✅ 启用输出"
4. ✅ 确认OD监控正常显示"已就绪"

**预计时间**: 2-3分钟

---

**重要**: 服务必须重启才能加载新的P2 v2规则！

🔄 **需要行动**: 请重启FastAPI服务，然后重新创建case进行测试
