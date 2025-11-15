# 批量删除功能 - 快速参考指南

**功能**: 在批量创建完成后，提供一键删除案例及其scenario_index.json关联的功能

---

## 🎯 核心功能

**一键删除**:
```
UI: 批量创建完成 → 点击 "🗑️ 删除此案例" → 确认 → 自动删除
```

**删除内容**:
1. ✅ 删除cases/{case_id}/文件夹（所有文件）
2. ✅ 清除scenario_index.json中的created_cases关联

---

## 📍 UI位置

**文件**: `frontend/scenarios/scenario_browser.html`
**位置**: 批量创建完成Modal的按钮区域
**按钮**: 红色的"🗑️ 删除此案例"（右对齐）

```html
<!-- 在"关闭"和"刷新数据"按钮的右侧 -->
<button class="btn btn-danger" onclick="deleteBatchCreatedCase()">🗑️ 删除此案例</button>
```

---

## 🔧 技术实现

### 前端流程
```
点击按钮
  ↓
显示确认对话框
  ↓
确认后调用API: DELETE /api/v1/case/{caseId}/delete-with-reset
  ↓
显示成功/失败提示
  ↓
关闭Modal，刷新数据
```

### 后端流程
```
API: DELETE /api/v1/case/{caseId}/delete-with-reset
  ↓
1. 删除cases目录
2. 更新scenario_index.json
  ↓
返回删除统计信息
```

---

## 🚀 使用示例

### 用户操作流程

1. **创建批量案例**
   - 选择scenarios
   - 点击"批量创建"
   - 等待创建完成

2. **批量创建完成**
   - 显示完成信息
   - 出现"🗑️ 删除此案例"按钮

3. **删除案例**
   - 点击"删除此案例"
   - 确认删除
   - 等待删除完成
   - 显示"✓ 案例已删除"

4. **完成**
   - Modal自动关闭
   - 页面自动刷新
   - 案例消失

---

## 💻 API调用

### 直接调用示例

```bash
# 删除案例
curl -X DELETE \
  http://localhost:8000/api/v1/case/case_event_10754/delete-with-reset \
  -H "Content-Type: application/json"

# 响应
{
  "code": 200,
  "message": "案例删除成功",
  "data": {
    "success": true,
    "case_id": "case_event_10754",
    "scenarios_affected": 3,
    "message": "✓ 案例已删除，已清除3个scenario关联"
  }
}
```

---

## 📊 删除详情

### 删除的文件
```
cases/case_event_10754/          ← 整个目录删除
├── config/
├── simulations/
├── analysis/
├── metadata.json
└── od_file_info.json
```

### 清除的关联
```
scenario_index.json
├── scenario_10754_no_control.created_cases[] ← 删除case_event_10754
├── scenario_10754_vss.created_cases[] ← 删除case_event_10754
└── scenario_10754_tec.created_cases[] ← 删除case_event_10754
```

---

## ⚠️ 注意事项

### 安全确认
- ✅ 删除前显示确认对话框
- ✅ 说明删除的后果
- ⚠️ 此操作不可撤销！

### 错误处理
- 如果案例不存在：返回404错误
- 如果权限不足：返回403错误
- 如果scenario_index.json更新失败：仍然完成删除（非致命）

### 日志
所有删除操作都会在服务日志中记录：
```
✓ 案例文件夹已删除: case_event_10754
✓ scenario_index.json已更新: 从3个scenario中删除了case_event_10754
```

---

## 🔍 调试技巧

### 验证删除是否成功

```bash
# 1. 检查文件是否被删除
ls cases/case_event_10754  # 应该返回"No such file"

# 2. 检查scenario_index.json是否被清空
grep -c "case_event_10754" output/scenarios/scenario_index.json
# 应该返回 0

# 3. 查看服务日志
# 查看是否有"✓ 案例文件夹已删除"的日志消息
```

### 常见问题

**Q: 删除后案例还显示在列表中？**
A: 刷新页面或等待自动刷新（调用了refreshData()）

**Q: scenario_index.json没有被更新？**
A: 查看服务日志，可能有权限问题或文件不存在

**Q: 无法删除案例？**
A: 检查案例是否存在或是否有正在运行的仿真

---

## 📁 代码位置参考

| 功能 | 文件 | 行数 |
|------|------|------|
| UI按钮 | scenario_browser.html | 516 |
| JavaScript函数 | scenario_browser.js | 814-872 |
| 按钮样式 | scenario_browser.css | 146-161 |
| API路由 | case_routes.py | 93-117 |
| 服务实现 | case_service.py | 975-1026 |

---

## 🎓 学习资源

### 相关文档
1. `BATCH_DELETE_FEATURE_SUMMARY.md` - 完整实现文档
2. `SCENARIO_INDEX_INTEGRATION_SUMMARY.md` - scenario_index.json集成
3. `SCENARIO_INDEX_INTEGRATION_CHECKLIST.md` - 集成清单

### API文档
访问 http://localhost:8000/docs 查看Swagger API文档

---

## ✅ 快速检查清单

部署前检查：
- [ ] 已重启服务
- [ ] API文档中显示新增的DELETE端点
- [ ] 批量创建完成后显示"删除此案例"按钮
- [ ] 点击删除显示确认对话框
- [ ] 删除成功后显示"案例已删除"提示
- [ ] 案例文件夹已删除
- [ ] scenario_index.json已更新
- [ ] 日志中显示删除信息

---

## 📞 支持

如有问题，请检查：
1. 服务日志（查看是否有错误信息）
2. 浏览器控制台（查看JavaScript错误）
3. 网络请求（F12开发者工具查看API响应）

---

**现在您可以轻松删除批量创建的案例！** 🗑️✨

