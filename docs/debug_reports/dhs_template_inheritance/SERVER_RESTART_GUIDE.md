# 服务器重启指南 - DHS 模板继承修复验证

**目的**: 验证 DHS 模板继承修复（`template_loader.py` 修改）是否生效

---

## 重要提示

✅ **服务器已配置自动重载模式**
- 启动脚本使用 `uvicorn --reload` 参数
- Python 文件修改后会自动重启
- **理论上不需要手动重启**

但是，由于你当前在 **conda base** 环境，服务器无法启动。

---

## 方法 1: 正确启动服务器（推荐）

### 步骤 1: 激活 od_project 环境

```powershell
# 在 PowerShell 或命令提示符中执行
conda activate od_project
```

### 步骤 2: 启动服务器

```powershell
# 确保在项目根目录
cd D:\projects\OD_SIM

# 运行启动脚本
.\start_api.ps1
```

### 步骤 3: 确认服务器启动成功

看到以下输出表示成功：
```
[INFO] 启动 API 服务（http://localhost:8000/）
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [PID]
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 步骤 4: 验证自动重载

服务器启动后，uvicorn 会监控文件变化：
- **监控目录**: `api/`, `shared/` 下的所有 `.py` 文件
- **检测变化**: 文件保存后自动触发重载
- **重载日志**: 看到 `INFO: Reloading...` 表示已重新加载

你刚才修改的 `shared/control_tools/template_loader.py` 会自动生效，无需手动重启。

---

## 方法 2: 检查是否已自动重载（如果服务器已在运行）

如果你之前在 `od_project` 环境下启动了服务器，并且服务器仍在运行：

### 步骤 1: 检查服务器日志

在服务器终端窗口查找：
```
INFO:     Reloading...
INFO:     Started reloader process [PID]
```

如果看到这些日志（且时间在你修改文件之后），说明已自动重载。

### 步骤 2: 检查继承解析日志

在服务器日志中搜索（或刷新前端页面后查看）：
```
INFO: Resolving inheritance for template: dhs_peak_hours
```

如果看到此日志，说明修改已生效。

---

## 方法 3: 强制手动重启（如果自动重载失败）

如果自动重载没有触发，或者想确保使用最新代码：

### 步骤 1: 停止服务器

在运行服务器的终端窗口按 `Ctrl+C`

### 步骤 2: 确认环境

```powershell
# 检查当前环境
conda info --envs

# 确保激活了 od_project
conda activate od_project
```

### 步骤 3: 重新启动

```powershell
.\start_api.ps1
```

---

## 方法 4: 使用 Python 直接启动（备用）

如果 PowerShell 脚本有问题，可以直接用 Python 启动：

```powershell
# 确保在 od_project 环境
conda activate od_project

# 切换到项目目录
cd D:\projects\OD_SIM

# 直接启动 uvicorn
python -X utf8 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 验证修复是否生效

### 1. 后端验证

服务器启动后，在日志中查找：
```
INFO: Resolving inheritance for template: dhs_peak_hours
```

**何时出现**:
- 选择 DHS 模板时
- 首次加载 DHS 模板 schema 时

**如果没看到此日志**:
- 清除浏览器缓存（Ctrl+F5）
- 重新选择 DHS 模板
- 查看后端日志

### 2. 前端验证

打开浏览器控制台（F12），运行：

```javascript
// 检查模板参数
console.log('Parameters:', window.currentTemplate?.parameters_schema?.map(p => p.parameter_name));
```

**预期输出**:
```
Parameters: ["affected_edges", "intervals", "hard_shoulder_lane_index", "allowed_vehicle_types"]
```

✅ 如果看到 **"intervals"**，说明继承解析成功！

### 3. 功能验证

1. 访问: `http://localhost:8000/control/templates.html`
2. 选择 DHS 模板
3. 选择路段
4. 进入参数配置页面

**预期结果**:
- ✅ 表格上方显示 24 小时时间轴
- ✅ 时间轴有 5 个默认时间槽
- ✅ 时间槽颜色正确（绿色=OPEN，红色=CLOSED）

5. 填写必填参数并点击"生成策略实例"

**预期结果**:
- ✅ 请求成功（200 OK）
- ✅ 策略实例创建成功
- ✅ 无 "intervals not provided" 错误

---

## 常见问题

### Q1: 为什么必须使用 od_project 环境？

**A**: 项目规范要求：
- **base 环境**: 仅用于 conda 自身管理，禁止安装业务包
- **od_project 环境**: 包含所有项目依赖（FastAPI, uvicorn, pandas, SUMO, Playwright 等）
- 启动脚本会检查环境，防止污染 base 环境

### Q2: 如何确认当前在哪个环境？

**A**: 查看命令提示符前缀：
```
(base) PS D:\projects\OD_SIM>          # ❌ base 环境
(od_project) PS D:\projects\OD_SIM>    # ✅ od_project 环境
```

或运行：
```powershell
conda info --envs
# 当前激活的环境前面有 * 标记
```

### Q3: uvicorn --reload 会监控哪些文件？

**A**: 默认监控：
- `api/` 目录下的所有 `.py` 文件
- `shared/` 目录下的所有 `.py` 文件
- 不监控 `.json`, `.html`, `.js` 文件

你修改的 `shared/control_tools/template_loader.py` 会被监控，保存后自动重载。

### Q4: 自动重载失败怎么办？

**A**: 可能原因：
1. **文件保存未成功**: 检查编辑器是否保存（Ctrl+S）
2. **监控未生效**: 手动重启服务器（Ctrl+C 停止，重新运行 `.\start_api.ps1`）
3. **缓存问题**: 清除浏览器缓存（Ctrl+F5）

### Q5: 如何查看完整的服务器日志？

**A**:
- 服务器日志输出到终端
- 关键日志级别: `INFO`, `WARNING`, `ERROR`
- 查找 "Resolving inheritance" 日志确认修复生效

---

## 快速操作清单

### 首次启动（从 base 环境）
```powershell
# 1. 激活环境
conda activate od_project

# 2. 启动服务器
.\start_api.ps1

# 3. 等待启动完成（看到 "Application startup complete"）
```

### 已经启动（在 od_project 环境）
```
✅ 无需重启！
- uvicorn --reload 已自动监控文件变化
- 修改 .py 文件后会自动重载
- 刷新浏览器即可测试
```

### 强制重启（如果自动重载失败）
```powershell
# 1. 停止服务器
按 Ctrl+C

# 2. 重新启动
.\start_api.ps1
```

---

## 验证完整流程

1. **激活环境**: `conda activate od_project`
2. **启动服务器**: `.\start_api.ps1`
3. **等待启动**: 看到 "Application startup complete"
4. **打开前端**: `http://localhost:8000/control/templates.html`
5. **选择 DHS 模板**: "应急车道开放 - 早晚高峰"
6. **检查日志**: 后端应显示 "Resolving inheritance for template: dhs_peak_hours"
7. **检查前端**: 控制台运行 `console.log(window.currentTemplate.parameters_schema.map(p => p.parameter_name))`，应包含 "intervals"
8. **测试时间轴**: 参数配置页面应显示时间轴
9. **测试创建**: 点击"生成策略实例"，应成功创建无错误

✅ **所有步骤通过 = 修复成功！**

---

**文档创建时间**: 2025-10-30
**预计操作时间**: 2-3 分钟（首次启动）
