# 统一案例+仿真创建 - 快速开始指南

**Status**: ✅ IMPLEMENTATION COMPLETE
**Last Updated**: 2025-11-13

---

## 🚀 快速启动

### 1. 启动后端
```bash
cd d:\projects\OD_SIM
.\start_api.ps1
```

### 2. 打开前端
```
http://localhost:8000/frontend/scenarios/scenario_browser.html
```

### 3. 测试工作流
1. 在场景表中找到任意场景
2. 点击"创建"按钮（蓝色按钮）
3. 模态框打开，显示场景信息和仿真参数
4. 可选修改仿真参数（或使用默认值）
5. 点击"🚀 启动仿真案例创建"
6. 等待响应（几秒钟）
7. 自动跳转到案例管理中心

---

## 📁 关键文件修改

### Frontend (3 个文件)

**1. scenario_browser.html** (+110 lines)
- 添加模态框 HTML 结构
- 场景信息展示
- 仿真参数表单

**2. scenario_browser.js** (+190 lines)
- `openCreateCaseModal()` - 打开模态框
- `submitCreateCaseWithSimulation()` - 提交请求
- 更改"创建"按钮处理器

**3. scenario_browser.css** (无需修改)
- 使用现有样式

### Backend (3 个文件)

**1. case_requests.py** (+62 lines)
- 新增 `CreateCaseWithSimulationRequest` 类

**2. case_routes.py** (+25 lines)
- 新增导入：`CreateCaseWithSimulationRequest`
- 新增端点：`POST /api/v1/case/create-case-with-simulation`

**3. case_service.py** (+161 lines)
- `create_case_with_simulation()` - 主要实现
- `_prepare_simulation_for_case()` - 仿真准备

---

## 🔄 工作流程

```
用户在场景表中点击"创建"
         ↓
模态框打开，预填参数
         ↓
用户可编辑仿真参数或使用默认值
         ↓
用户点击"启动仿真案例创建"
         ↓ 发送 POST 请求
POST /api/v1/case/create-case-with-simulation
         ↓
Backend 原子性地：
  1. 创建案例目录和元数据 ✅
  2. 启动OD处理（异步）⏳
  3. 复制TAZ文件 ✅
  4. 生成sumocfg ✅
  5. 创建simulation_metadata.json ✅ KEY!
  6. 注册到scenario_index.json ✅
  7. 更新案例状态为ready_to_simulate ✅
         ↓ 返回响应
关闭模态框
更新场景表
自动导航到案例管理中心
         ↓
✓ 完成！案例已创建，仿真已准备
```

---

## 📊 API 端点

### 新增端点

**POST** `/api/v1/case/create-case-with-simulation`

**Request Body**:
```json
{
  "scenario_id": "scenario_12547_vss",
  "event_id": "12547",
  "event_type": "01_accident",
  "strategy": "vss",
  "case_name": "my_case",
  "simulation_duration_hours": 2.5,
  "random_seed": null,
  "simulation_type": "microscopic",
  "output_config": {
    "generate_edgedata": true,
    "generate_summary": true,
    "generate_tripinfo": true,
    "generate_vehroute": false
  },
  "network_file": "templates/network_files/sichuan202508v7.net.xml",
  "od_file": "dwd.dwd_od_weekly",
  "taz_file": null,
  "description": "从场景12547创建的案例"
}
```

**Response**:
```json
{
  "success": true,
  "code": 200,
  "message": "统一案例+仿真创建成功",
  "data": {
    "success": true,
    "case_id": "case_20251113_120000",
    "simulation_id": "sim_20251113_120530",
    "case_status": "ready_to_simulate",
    "simulation_status": "pending",
    "files_created": {
      "case_metadata": ".../metadata.json",
      "simulation_metadata": ".../simulation_metadata.json",
      "sumocfg": ".../simulation.sumocfg"
    }
  }
}
```

---

## 🧪 测试清单

### 基础功能测试
- [ ] 打开scenario_browser.html
- [ ] 点击"创建"按钮 → 模态框显示
- [ ] 模态框中场景信息正确（只读）
- [ ] 默认仿真参数正确
- [ ] 能修改案例名称
- [ ] 能修改仿真时长
- [ ] 能选择仿真模式
- [ ] 能修改输出配置

### 提交测试
- [ ] 点击"启动仿真案例创建"
- [ ] API 返回成功响应
- [ ] case_id 和 simulation_id 返回正确
- [ ] 模态框关闭
- [ ] 自动导航到 case-simulation-center.html

### 文件验证
```bash
# 验证案例目录结构
ls cases/{case_id}/
  metadata.json              ✓ 应该存在
  config/
    od_*.xml                 ⏳ 可能正在生成
  simulations/{sim_id}/
    simulation.sumocfg       ✓ 应该存在
    simulation_metadata.json ✓ 应该存在

# 验证元数据内容
cat cases/{case_id}/metadata.json | grep status
  "status": "ready_to_simulate"  ✓

cat cases/{case_id}/simulations/{sim_id}/simulation_metadata.json | grep source_scenario
  "source_scenario": {...}  ✓

# 验证scenario_index.json
grep -A5 created_cases output/scenarios/scenario_index.json
  应该包含新创建的案例信息  ✓
```

### 错误处理测试
- [ ] 仿真时长 < 1 小时 → 显示错误
- [ ] 仿真时长 > 24 小时 → 显示错误
- [ ] 网络断开 → 显示错误信息
- [ ] 点取消 → 模态框关闭，无创建

---

## 📝 故障排除

### 问题1：模态框不显示
**解决**：检查浏览器控制台
```javascript
// 在浏览器控制台运行
document.getElementById('caseCreationModal').style.display  // 应该返回某个值
allScenarios.length  // 应该 > 0
```

### 问题2：提交按钮无反应
**解决**：检查网络
```javascript
// 检查 API 端点是否存在
fetch('/api/v1/case/create-case-with-simulation', {method: 'OPTIONS'})
```

### 问题3：后端返回 404
**解决**：检查路由注册
```python
# 在api/main.py或routes/__init__.py中
# 确保 case_routes.router 被正确注册
```

### 问题4：文件创建失败
**解决**：检查路径和权限
```bash
# 验证cases目录存在
ls -la cases/

# 验证权限
stat cases/
```

---

## 🔍 相关文档

| 文档 | 内容 |
|------|------|
| IMPLEMENTATION_UNIFIED_CASE_SIMULATION_CREATION.md | 完整实现总结 |
| WORKFLOW_REDESIGN_CASE_CREATION.md | 工作流详细设计 |
| CASE_SIMULATION_CREATION_REDESIGN.md | 设计摘要 |
| openspec/changes/.../CASE_SIMULATION_UNIFIED_CREATION.md | OpenSpec 实现指南 |
| CLAUDE.md | 项目架构原则（AD-12等） |

---

## 🎯 下一步

### 短期（立即）
1. [ ] 运行本指南中的测试清单
2. [ ] 验证文件系统中的文件创建
3. [ ] 检查数据库/元数据变化

### 中期（本周）
1. [ ] 编写单元测试
2. [ ] 编写集成测试
3. [ ] 运行完整的 E2E 测试
4. [ ] 性能基准测试

### 长期（下个阶段）
1. [ ] 实时进度反馈
2. [ ] 批量创建支持
3. [ ] 高级参数配置
4. [ ] 案例复制和对比

---

## ⚡ 关键改进点

✅ **问题解决**：simulation_metadata.json 现在在案例创建时立即创建（不是稍后）

✅ **关系可见**：案例-场景-仿真关系在创建完成后立即可见

✅ **用户体验**：从两步流程简化为一步，参数可定制

✅ **数据完整**：三层元数据链接（AD-12）在创建时原子性建立

---

**Ready to Test!** 🚀

