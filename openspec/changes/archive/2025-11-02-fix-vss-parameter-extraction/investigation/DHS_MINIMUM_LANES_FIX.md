# DHS模板最小车道数过滤修复 (DHS Minimum Lanes Filter Fix)

## 问题 (Problem)
DHS (动态硬路肩) 模板在筛选路段时,需要设置"最小车道数"过滤条件为4。

### 症状
- DHS提交按钮被禁用 (disabled状态)
- 错误消息: "存在验证错误，请返回第2步修正路段选择"

### 根本原因
DHS策略只对4车道及以上的路段有效。测试脚本没有设置最小车道数过滤条件,导致:
1. 查询返回的边中包含3车道或更少的路段
2. 表单验证失败,因为被选中的边不符合DHS要求

---

## 解决方案 (Solution)

### 修改位置
**文件**: `tests/e2e/test_frontend_smart.spec.js`
**第**: 208-248行

### 改动内容
添加DHS模板特定的最小车道数处理:

```javascript
// 对于DHS模板,第一个数字字段可能是最小车道数
if (template.type === 'DHS') {
  const firstInputPlaceholder = await numberInputs[0].getAttribute('placeholder');

  // 检查是否是最小车道数字段,填充4
  if (firstInputPlaceholder && firstInputPlaceholder.includes('车道')) {
    await numberInputs[0].clear();
    await numberInputs[0].fill('4');
    console.log(`  ✓ 最小车道数: 4`);
  }
}
```

### 关键点
1. **自动检测**: 通过placeholder属性自动识别最小车道数字段
2. **灵活处理**: 如果不是车道字段,则填充最小桩号
3. **DHS特定**: 仅对DHS模板应用此逻辑

---

## 验证方法 (Verification)

### 运行DHS测试
```bash
npx playwright test tests/e2e/test_frontend_smart.spec.js -g "DHS"
```

### 预期输出
```
[步骤4] 设置路段查询条件...
  ✓ 路线: G4202
  ℹ 找到 3 个数字输入框
    输入框0 placeholder="最小车道数"
  ✓ 最小车道数: 4
  ✓ 最小桩号: 33
  ✓ 最大桩号: 44
[步骤5] 查询路段...
  ✓ 查询已启动
  ✓ 结果已加载
[步骤6] 选择 3 条路段...
  ✓ 已选择第 2 条路段
  ✓ 已选择第 3 条路段
  ✓ 已选择第 4 条路段
```

### 成功标志
- ✅ 最小车道数被正确填充为4
- ✅ 查询路段成功返回结果
- ✅ 能选择3条路段 (满足DHS需要)
- ✅ 提交按钮不再禁用

---

## 相关的DHS模板信息 (DHS Template Information)

### DHS的三个变种
1. **dhs_peak_hours** (应急车道开放-高峰时段)
   - 路线: G4202
   - 范围: K33-K44
   - 最小车道: 4

2. **dhs_passenger_only** (应急车道-仅客车)
   - 路线: G4202
   - 范围: K25-K40
   - 最小车道: 4

3. **dhs_peak_multi_interval** (应急车道-多时段管理)
   - 路线: G4202
   - 范围: K45-K55
   - 最小车道: 4

### DHS的必需参数
- **affected_edges**: 选中的路段ID列表
- **hard_shoulder_lane_index**: 应急车道索引 (通常为0)
- **intervals**: 时间间隔数组,每个包含:
  - begin_hours: 起始时间 (0-24)
  - end_hours: 结束时间 (0-24)
  - status: 状态 ("OPEN" 或 "CLOSED")
  - allowed_vehicle_types: 允许的车型 (["passenger"], ["truck"], ["passenger", "truck"] 等)

---

## 后续改进 (Follow-up Improvements)

### 优先级: 🔴 高
实现DHS时间间隔表格填充(参考FRONTEND_TEST_ACTION_PLAN.md P2任务)

### 优化建议
1. 提高路段过滤的鲁棒性
2. 自动填充时间间隔默认值
3. 验证车道数是否 >= 4

---

## 测试状态 (Test Status)

| 模板 | 状态 | 注 | 预期修复后状态 |
|------|------|-----|-----------------|
| dhs_peak_hours | ❌ 按钮禁用 | 缺少车道过滤+时间间隔 | ✅ 应通过 |
| dhs_passenger_only | ❌ 按钮禁用 | 缺少车道过滤+时间间隔 | ✅ 应通过 |
| dhs_peak_multi_interval | ❌ 按钮禁用 | 缺少车道过滤+时间间隔 | ✅ 应通过 |

---

## 文件修改记录 (File Changes)

**文件**: tests/e2e/test_frontend_smart.spec.js
**修改**: 2025-11-01
**行数**: 208-248行
**类型**: 增强功能

---

## 相关文档 (Related Documents)

- [FRONTEND_UI_TEST_ANALYSIS_REPORT.md](FRONTEND_UI_TEST_ANALYSIS_REPORT.md) - DHS问题分析
- [FRONTEND_TEST_ACTION_PLAN.md](FRONTEND_TEST_ACTION_PLAN.md) - P2任务:DHS表格填充
- [SESSION_SUMMARY.md](SESSION_SUMMARY.md) - 总体会话总结

---

**更新时间**: 2025-11-01
**版本**: 1.0

