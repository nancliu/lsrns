# 策略实例功能测试清单

## 访问方式
```
http://localhost:8000/control/templates.html
```

## 功能测试

### ✓ 1. 查看详情（蓝色按钮）
- [ ] 打开详情模态框
- [ ] 显示策略名称、类型、模板
- [ ] 显示配置参数（格式正确）
- [ ] 显示受影响路段列表
- [ ] 显示元数据（时间、版本）
- [ ] 关闭功能正常

**测试用例**: `strategy_vss_001`, `strategy_tec_001`, `strategy_dhs_001`

---

### ✓ 2. 编辑策略（橙色按钮）
- [ ] 打开编辑模态框
- [ ] 表单预填充当前值
- [ ] 修改策略名称
- [ ] 修改参数值
- [ ] 保存成功，显示消息
- [ ] 列表自动刷新
- [ ] 验证错误提示正确

---

### ✓ 3. 复制策略（紫色按钮）
- [ ] 打开名称输入对话框
- [ ] 默认名称 `[复制] 原名称`
- [ ] 可修改新名称
- [ ] 复制成功，显示新ID
- [ ] 列表刷新，新策略在顶部
- [ ] 取消操作正常

**验证**: 新策略拥有独立ID、新时间戳、版本号=1

---

### ✓ 4. 删除策略（红色按钮）
- [ ] 打开确认对话框
- [ ] 警告信息显示
- [ ] 确认删除成功
- [ ] 列表刷新，策略消失
- [ ] 取消操作正常

---

## 按钮顺序验证
```
查看(蓝) → 编辑(橙) → 复制(紫) → 删除(红)
```

---

## 快速API测试

```bash
# 查看
curl http://localhost:8000/api/v1/control/strategy-instances/strategy_vss_001

# 复制
curl -X POST http://localhost:8000/api/v1/control/strategy-instances/strategy_vss_001/copy

# 删除（使用复制的策略ID）
curl -X DELETE http://localhost:8000/api/v1/control/strategy-instances/strat_...
```

---

## 问题排查

### 按钮无反应
- 清除浏览器缓存 (Ctrl+F5)
- 检查控制台错误
- 确认 strategy_manager.js 已加载

### "策略管理器未加载"
- 刷新页面
- 查看控制台是否有 "[StrategyManager] Module loaded successfully"

---

**所有测试通过即可部署** ✓
