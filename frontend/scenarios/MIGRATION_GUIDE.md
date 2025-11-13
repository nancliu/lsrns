# 场景案例管理迁移指南

**完成日期**: 2025-11-13
**版本**: 1.0
**状态**: ✅ 完成

---

## 📋 变更摘要

### 页面架构重构

通过整合 `case_manager.html` 和 `simulation_monitor.html`，创建了新的 `case-simulation-center.html` 统一的场景案例管理页面。

#### 迁移后的页面结构

```
frontend/scenarios/
├── scenario_browser.html          → 🎬 仿真推演场景集 (保留)
├── case-simulation-center.html    → 🔄 场景案例管理 (新建，合并两个页面)
├── analysis_viewer.html           → 📈 影响分析 (保留)
├── scenario_browser.js            → 已更新
├── scenario_browser.css           → 共享样式 (无变更)
│
├── case_manager.html              → ⚠️ 已废弃 (向后兼容跳转)
└── simulation_monitor.html        → ⚠️ 已废弃 (向后兼容跳转)
```

---

## 🎯 工作流程

### 新的三页工作流

```
1️⃣ 仿真推演场景集 (scenario_browser.html)
   ├─ 二维筛选场景（事件类型 × 管控策略）
   ├─ 搜索场景
   └─ [创建案例] → 弹出模态框配置参数
      └─ [启动仿真] → 跳转到
                      ↓
2️⃣ 场景案例管理 (case-simulation-center.html)
   ├─ Tab1: 📋 案例管理
   │  ├─ 案例列表
   │  ├─ 统计信息（总、仿真中、完成、失败）
   │  └─ 创建新案例
   │
   └─ Tab2: ▶️ 仿真监控
      ├─ 批次进度条
      ├─ 仿真详情表格
      ├─ 实时轮询更新（每10秒）
      └─ [查看分析] → 跳转到
                      ↓
3️⃣ 影响分析 (analysis_viewer.html)
   ├─ 概览统计
   ├─ 路段分析
   ├─ 对比分析
   └─ 详细指标
```

---

## 📍 导航栏更新

### 左侧导航栏结构

```html
<!-- 在所有三个页面中保持一致 -->
<li class="nav-section-title">事件触发仿真</li>
<li><a href="scenario_browser.html" class="nav-item">🎬 仿真推演场景集</a></li>
<li><a href="case-simulation-center.html" class="nav-item">🔄 场景案例管理</a></li>
<li><a href="analysis_viewer.html" class="nav-item">📈 影响分析</a></li>
```

### 页面更新清单

| 页面 | 更新内容 | 状态 |
|------|--------|------|
| `scenario_browser.html` | ✅ 导航栏更新；页面标题保持不变 | ✓ |
| `case-simulation-center.html` | ✅ 新建（案例+监控合并）；页面标题改为"场景案例管理" | ✓ |
| `analysis_viewer.html` | ✅ 导航栏更新；页面标题改为"影响分析" | ✓ |
| `scenario_browser.js` | ✅ 添加跳转逻辑 | ✓ |
| `case_manager.html` | ⚠️ 已废弃（可删除或保留向后兼容） | - |
| `simulation_monitor.html` | ⚠️ 已废弃（可删除或保留向后兼容） | - |

---

## 🔄 关键功能集成

### 1. Tab 切换机制

`case-simulation-center.html` 包含两个主功能Tab：

```javascript
// Tab切换函数
window.switchTab = function(tabName) {
    // 更新按钮样式
    // 显示/隐藏内容
    // 加载对应数据
}

// 通过URL参数初始化
// case-simulation-center.html?activeTab=cases
// case-simulation-center.html?activeTab=monitor
```

### 2. 案例创建到跳转流程

#### 旧流程
```
scenario_browser.html → 创建案例 → alert → 停止
```

#### 新流程
```
scenario_browser.html → 创建案例 → alert → 500ms延迟 → case-simulation-center.html?activeTab=cases&caseId=xxx
```

**实现代码** (`scenario_browser.js`):
```javascript
setTimeout(() => {
    window.location.href = `case-simulation-center.html?activeTab=cases&caseId=${result.case_id}`;
}, 500);
```

### 3. 实时监控轮询

保留原有轮询机制（10秒刷新一次）：

```javascript
monitoringInterval = setInterval(refreshBatchStatus, 10000);
```

### 4. 影响分析查看

从仿真监控表格的"📊"按钮跳转到影响分析页面：

```javascript
window.viewResults = function(simId) {
    window.location.href = `analysis_viewer.html?simulation_id=${simId}`;
};
```

---

## 📊 代码复杂度对比

### 迁移前

| 文件 | 行数 | 职责 |
|------|-----|------|
| `case_manager.html` | 373 | 案例管理 |
| `simulation_monitor.html` | 492 | 仿真监控 |
| 合计 | **865** | 两个独立页面 |

### 迁移后

| 文件 | 行数 | 职责 |
|------|-----|------|
| `case-simulation-center.html` | ~800 | 案例+监控合并 |
| **减少** | **65** | 共享CSS、JS简化 |

---

## 🔌 API 端点映射

### 案例管理 Tab

```javascript
// 加载案例列表
GET /api/v1/case/list

// 创建案例
POST /api/v1/case/create-from-scenario
{
    scenario_id, event_id, event_type,
    control_strategy_type, simulation_duration_hours, random_seed
}
```

### 仿真监控 Tab

```javascript
// 获取批次状态
GET /api/v1/simulation/batch-status/{batch_id}

// 取消批次
POST /api/v1/simulation/batch-cancel
{ batch_id }
```

### 影响分析页面

```javascript
// 获取影响分析结果
GET /api/v1/analysis/results/{simulation_id}
```

---

## 🧪 测试场景

### 完整工作流测试

#### 场景1: 快速创建案例
```
1. 打开 http://localhost:8000/frontend/scenarios/scenario_browser.html
2. 在场景表中找一个场景
3. 点击"创建案例"按钮
4. 弹出模态框，填写参数（可选）
5. 点击"创建案例"
   → ✓ 显示创建成功的alert
   → ✓ 500ms后自动跳转到 case-simulation-center.html?activeTab=cases
```

#### 场景2: Tab切换
```
1. 在案例仿真中心页面
2. 点击"▶️ 仿真监控" tab
   → ✓ 显示仿真监控内容
   → ✓ 顶栏按钮变为"🔄 刷新"和灰显
3. 点击"📋 案例管理" tab
   → ✓ 显示案例列表
   → ✓ 顶栏按钮变为"+ 从场景创建案例"
```

#### 场景3: 仿真进度监控
```
1. 在仿真监控 tab
2. 如果有活跃仿真（batch_id 有效）
   → ✓ 自动开始轮询（10秒刷新一次）
   → ✓ 进度条实时更新
   → ✓ 仿真完成后停止轮询
3. 点击仿真行的"📊"按钮
   → ✓ 跳转到 analysis_viewer.html?simulation_id=xxx
```

---

## ⚙️ 配置说明

### URL 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `activeTab` | 初始化Tab名称 | `?activeTab=monitor` |
| `caseId` | 高亮指定案例 | `?caseId=case_001` |
| `batch_id` | 批次ID（监控页面） | `?batch_id=batch_123` |

### 环境配置

无需额外配置，使用现有的：
- `scenario_browser.css` - 共享样式
- `../components/shared-utils.js` - 工具函数
- `../components/api-client.js` - API客户端

---

## 📝 浏览器兼容性

- ✅ Chrome/Edge (最新版)
- ✅ Firefox (最新版)
- ✅ Safari 12+
- ⚠️ IE11 (不支持 ES6+ 语法)

---

## 🚀 后续优化方向

### Phase 2 (可选)

- [ ] 添加案例搜索和过滤
- [ ] 实现案例批量删除
- [ ] 添加仿真日志下载
- [ ] 支持自定义轮询间隔
- [ ] 添加暗色主题支持

### Phase 3 (未来)

- [ ] 缓存优化（避免频繁API调用）
- [ ] 离线支持（IndexedDB）
- [ ] 权限控制（多用户隔离）
- [ ] 国际化支持 (i18n)

---

## ✅ 验证检查清单

部署前请确认：

- [ ] `case-simulation-center.html` 已创建
- [ ] `scenario_browser.html` 导航栏已更新
- [ ] `scenario_browser.html` 跳转逻辑已添加（submitQuickCreate）
- [ ] `scenario_browser.js` 已更新（跳转代码）
- [ ] `analysis_viewer.html` 导航栏已更新
- [ ] 三个页面的导航栏一致性已验证
- [ ] 测试了完整的工作流（创建→监控→分析）

---

## 📞 故障排查

### 问题1: 创建案例后没有自动跳转

**原因**: `scenario_browser.js` 中的跳转代码可能未更新

**解决**:
```javascript
// 在 submitQuickCreate 函数中检查:
setTimeout(() => {
    window.location.href = `case-simulation-center.html?activeTab=cases&caseId=${result.case_id}`;
}, 500);
```

### 问题2: Tab 切换没有加载数据

**原因**: `switchTab` 函数中的数据加载可能失败

**解决**: 在浏览器控制台检查：
```javascript
// 打开开发者工具 (F12)
// 检查 Console 中的错误信息
// 检查 Network 中的 API 调用
```

### 问题3: 监控页面不自动刷新

**原因**: `batchId` 未正确传递或 API 端点错误

**解决**:
```javascript
// 检查URL中是否包含 batch_id 参数
let batchId = new URLSearchParams(window.location.search).get('batch_id');
console.log('Current batch ID:', batchId);
```

---

## 📚 相关文档

- [Phase 2 前端页面集成指南](./PHASE_2_FRONTEND_GUIDE.md)
- [仿真场景库设计说明](./DESIGN_NOTES.md)
- [API 参考](../../docs/PHASE_2_API_REFERENCE.md)

---

**维护者**: OD仿真系统开发团队
**最后更新**: 2025-11-13
**反馈**: 提交 Issue 或 PR
