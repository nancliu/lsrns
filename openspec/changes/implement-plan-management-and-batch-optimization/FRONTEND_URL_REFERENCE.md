# 前端URL路径快速参考

**变更**: implement-plan-management-and-batch-optimization
**版本**: 1.0
**最后更新**: 2025-10-27

---

## 管控优化四大界面URL路径

**重要提示**: 所有管控优化页面必须使用 `/control/` 前缀访问

| 序号 | 功能模块 | 页面文件 | 完整访问URL | Phase | 实现状态 |
|-----|---------|---------|-----------|-------|---------|
| 1 | **策略管理** | `templates.html` | `http://localhost:8000/control/templates.html` | Phase 1A | ✅ 已实现 |
| 2 | **方案管理** | `plans.html` | `http://localhost:8000/control/plans.html` | Phase 1B | ✅ 已实现 |
| 3 | **并行仿真** | `simulations.html` | `http://localhost:8000/control/simulations.html` | Phase 2-3 | ✅ 已实现 |
| 4 | **方案优化** | `optimization.html` | `http://localhost:8000/control/optimization.html` | Phase 4 | 🔜 待实现 |

---

## 快速访问链接（开发环境）

在浏览器中直接访问：

### Phase 1 - 策略和方案管理
- 策略管理: http://localhost:8000/control/templates.html
- 方案管理: http://localhost:8000/control/plans.html

### Phase 2-3 - 批量仿真和优化
- 并行仿真: http://localhost:8000/control/simulations.html

### Phase 4 - 高级评估（待实现）
- 方案优化: http://localhost:8000/control/optimization.html

---

## 文件系统映射

### 物理文件位置
```
D:/projects/OD_SIM/frontend/control/
├── templates.html       # 策略管理页面
├── plans.html          # 方案管理页面
├── simulations.html    # 并行仿真页面
├── optimization.html   # 方案优化页面（Phase 4）
└── js/
    ├── templates.js         # 策略管理逻辑
    ├── plans.js            # 方案管理逻辑
    ├── batch_simulation.js # 并行仿真逻辑
    └── optimization.js     # 方案优化逻辑（Phase 4）
```

### URL路径映射规则

| 浏览器请求URL | FastAPI查找路径 | 说明 |
|-------------|---------------|------|
| `/control/templates.html` | `frontend/control/templates.html` | 策略管理 |
| `/control/plans.html` | `frontend/control/plans.html` | 方案管理 |
| `/control/simulations.html` | `frontend/control/simulations.html` | 并行仿真 |
| `/control/optimization.html` | `frontend/control/optimization.html` | 方案优化 |
| `/control/js/plans.js` | `frontend/control/js/plans.js` | JavaScript资源 |

---

## 后端静态文件配置

### 主配置文件: `api/main.py`

```python
from fastapi.staticfiles import StaticFiles

# 挂载整个frontend目录到根路径
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

### 映射原理

1. **根路径挂载**: `frontend`目录挂载到`/`
2. **自动子路径**: `frontend/control/`自动映射到`/control/`
3. **HTML自动索引**: `html=True`参数允许访问`.html`文件

**示例流程**:
```
用户访问: http://localhost:8000/control/plans.html
    ↓
FastAPI接收: GET /control/plans.html
    ↓
StaticFiles查找: frontend/control/plans.html
    ↓
返回文件: 200 OK + HTML内容
```

---

## API后端路径对比

为保持一致性，API路径也使用`/control/`前缀：

| 功能 | 前端页面URL | 后端API路径 |
|-----|-----------|-----------|
| 策略管理 | `/control/templates.html` | `/api/v1/control/strategy-instances/` |
| 方案管理 | `/control/plans.html` | `/api/v1/control/plans/` |
| 批量优化 | `/control/simulations.html` | `/api/v1/control/optimization/batch` |

**设计优势**: 前后端路径风格统一，易于理解和维护

---

## 侧边导航链接配置

所有四个页面共享相同的侧边导航栏，链接配置如下：

```html
<!-- 侧边导航栏 HTML -->
<div class="sidebar">
    <ul class="sidebar-nav">
        <li><a href="templates.html">策略管理</a></li>
        <li><a href="plans.html">方案管理</a></li>
        <li><a href="simulations.html">并行仿真</a></li>
        <li><a href="optimization.html">方案优化</a></li>
    </ul>
</div>
```

**注意**: 导航链接使用相对路径（如`plans.html`），因为所有页面都在同一目录`/control/`下

---

## 常见问题排查

### Q1: 访问页面返回404
**原因**: URL路径未使用`/control/`前缀
- ❌ 错误: `http://localhost:8000/plans.html`
- ✅ 正确: `http://localhost:8000/control/plans.html`

### Q2: JavaScript资源加载失败
**检查**: JS文件路径是否正确
- HTML中引用: `<script src="js/plans.js"></script>`
- 浏览器请求: `http://localhost:8000/control/js/plans.js`
- 物理文件: `frontend/control/js/plans.js`

### Q3: 页面样式丢失
**检查**: CSS是否使用内联样式或相对路径
- ✅ 推荐: 使用内联`<style>`标签
- ⚠️  外部CSS需要确保路径正确: `<link rel="stylesheet" href="css/control.css">`

### Q4: API请求跨域
**不会发生**: 前端页面和API都在`localhost:8000`下，无跨域问题

---

## 页面间跳转

### 跳转到方案管理（从策略管理）
```javascript
// 在 templates.html 中
window.location.href = 'plans.html';
```

### 跳转到并行仿真（从方案详情）
```javascript
// 在 plans.html 中点击"应用到仿真"按钮
function applyToSimulation(planId) {
    window.location.href = `simulations.html?preselect_plan=${planId}`;
}
```

### 返回主系统
```html
<!-- 所有页面顶栏都有返回按钮 -->
<a href="../index.html" class="back-btn">返回主系统</a>
```

**路径说明**: `../index.html` 从 `/control/` 目录返回到 `/` 根目录的 `index.html`

---

## 开发规范

### 1. 新增页面命名规范
- 文件名: 小写英文，使用下划线或连字符（如`optimization.html`）
- 存放位置: `frontend/control/` 目录下
- 访问URL: `http://localhost:8000/control/{文件名}.html`

### 2. JavaScript模块化
- JS文件统一放在 `frontend/control/js/` 目录
- 文件名与页面对应（如`plans.html` → `js/plans.js`）
- 使用模块化模式，避免全局变量污染

### 3. 样式管理
- 推荐使用内联`<style>`标签，保持页面独立性
- 如需共享样式，创建 `frontend/control/css/control-common.css`
- 使用相对路径引用: `<link rel="stylesheet" href="css/control-common.css">`

---

## 相关文档

- **总体设计**: `docs/design/traffic_control_optimization_overview.md`
- **详细设计**: `openspec/changes/implement-plan-management-and-batch-optimization/design.md`
- **导航澄清**: `openspec/changes/implement-plan-management-and-batch-optimization/NAVIGATION_CLARIFICATION.md`
- **任务清单**: `openspec/changes/implement-plan-management-and-batch-optimization/tasks.md`

---

**文档维护**: 每次新增或修改control相关页面时，请同步更新本文档
