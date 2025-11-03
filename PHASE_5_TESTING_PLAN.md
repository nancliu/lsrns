# Phase 5: E2E测试和文档编写 - 测试计划

**日期**: 2025-11-03
**状态**: 计划中 (待执行)
**预计工作量**: 3小时

---

## 📋 Phase 5 任务分解

### Task 1: 单元测试编写 (1小时)

**目标**: 对新添加的业务逻辑进行单元测试

**测试覆盖**:

1. **OutputConfig模型测试** (`test_output_config.py`)
   - ✅ 默认值验证
   - ✅ 序列化/反序列化
   - ✅ 字段验证

2. **SimulationDuration验证测试** (待创建 `test_simulation_duration.py`)
   - ✅ 有效的时长组合 (1分钟-24小时)
   - ✅ 边界值测试 (0分钟, 1分钟, 24小时, 25小时)
   - ✅ 无效输入处理

3. **向后兼容性测试**
   - ✅ output_level映射到output_config
   - ✅ 旧API格式兼容性

**测试文件位置**:
```
tests/unit/
├── test_output_config.py (新增)
├── test_simulation_duration.py (新增)
└── test_backward_compatibility.py (新增)
```

---

### Task 2: 集成测试编写 (1小时)

**目标**: 验证Batch创建的完整流程

**测试覆盖**:

1. **创建Batch with新参数**
   - ✅ 有效的output_config
   - ✅ 有效的vehicle_types_template
   - ✅ 有效的simulation_duration
   - ✅ 完整的请求body

2. **错误处理测试**
   - ✅ 无效的时长 (0分钟, 25小时)
   - ✅ 缺失必填字段
   - ✅ 无效的case_id/plan_ids

3. **数据格式验证**
   - ✅ simulation_config.json格式
   - ✅ SUMO配置生成

**测试文件位置**:
```
tests/integration/
├── test_batch_creation_output_config.py
├── test_batch_creation_duration.py
└── test_batch_creation_complete.py
```

**测试用例示例**:
```python
def test_create_batch_with_custom_duration():
    """测试创建batch with 自定义时长"""
    response = client.post('/api/v1/control/batch-optimization/batch', json={
        'case_id': 'test_case',
        'plan_ids': ['baseline_plan'],
        'num_seeds': 3,
        'base_seed': 66,
        'output_config': {
            'summary_xml': True,
            'e1_detector_data': True,
            'edgedata_xml': True,
            'tripinfo_xml': False
        },
        'vehicle_types_template': 'vehicle_types.json',
        'simulation_duration': {
            'use_default': False,
            'hours': 8,
            'minutes': 30,
            'total_minutes': 510
        }
    })
    assert response.status_code == 201
    assert response.json()['batch_id']
```

---

### Task 3: E2E Playwright测试 (0.5小时)

**目标**: 验证前端UI交互和用户流程

**测试覆盖**:

1. **输出配置交互**
   - ✅ Checkbox勾选/取消勾选
   - ✅ 性能提示显示
   - ✅ Summary和E1始终启用

2. **车辆模板选择**
   - ✅ Dropdown加载
   - ✅ 选项切换

3. **时长配置交互**
   - ✅ Radio按钮切换
   - ✅ 输入框启用/禁用
   - ✅ 验证错误提示
   - ✅ 有效值范围

4. **Batch创建流程**
   - ✅ 选择案例
   - ✅ 选择方案
   - ✅ 配置输出选项
   - ✅ 选择模板
   - ✅ 设置时长
   - ✅ 点击创建批次
   - ✅ 验证成功消息

**测试文件位置**:
```
tests/e2e/
└── test_batch_simulation_enhancements.spec.js
```

**测试脚本示例**:
```javascript
test('应该能够创建batch with 自定义时长和输出配置', async ({ page }) => {
    await page.goto('http://localhost:8000/control/simulations.html');

    // 选择案例
    await page.selectOption('#caseSelector', 'test_case');

    // 勾选输出配置
    await page.check('#outputEdgedata');

    // 选择时长
    await page.click('#durationCustom');
    await page.fill('#simHours', '8');
    await page.fill('#simMinutes', '30');

    // 创建批次
    await page.click('#createBatchBtn');

    // 验证成功
    await expect(page.locator('text=批次创建成功')).toBeVisible();
});
```

---

### Task 4: 文档编写 (0.5小时)

**目标**: 完整的项目文档

**文档清单**:

1. **API文档更新**
   - ✅ `/api/v1/control/batch-optimization/batch` 端点更新
   - ✅ 新增OutputConfig和SimulationDuration模型文档
   - ✅ 请求/响应示例

2. **用户指南**
   - ✅ 输出配置说明
   - ✅ 车辆模板选择指南
   - ✅ 时长设置说明
   - ✅ 性能提示解释

3. **Release Notes**
   - ✅ 新功能总结
   - ✅ 改进项
   - ✅ 向后兼容性说明
   - ✅ 已知限制

**文档文件位置**:
```
docs/
├── api_docs/
│   └── 新架构API指南.md (更新)
├── features/
│   └── batch_simulation_enhancements.md (新增)
└── user_guide/
    └── batch_simulation_setup.md (新增)
```

---

## ✅ 测试验收标准

### 单元测试
- [ ] 所有输出配置模型测试通过
- [ ] 时长验证规则测试通过
- [ ] 向后兼容性映射正确
- [ ] 覆盖率 ≥ 90%

### 集成测试
- [ ] Batch创建with新参数成功
- [ ] 时长验证规则有效
- [ ] 错误处理正确
- [ ] simulation_config.json格式正确

### E2E测试
- [ ] 完整用户流程通过
- [ ] UI交互正确
- [ ] 验证错误提示显示
- [ ] 性能提示显示正确

### 文档
- [ ] API文档完整
- [ ] 用户指南清晰
- [ ] Release Notes准备完毕

---

## 🧪 运行测试命令

```bash
# 激活环境
conda activate od_project

# 运行单元测试
pytest tests/unit/test_output_config.py
pytest tests/unit/test_simulation_duration.py
pytest tests/unit/test_backward_compatibility.py

# 运行集成测试
pytest tests/integration/test_batch_creation_*.py

# 运行所有测试with覆盖率
pytest --cov=api --cov=shared tests/

# 运行E2E测试
npx playwright test tests/e2e/test_batch_simulation_enhancements.spec.js

# 运行E2E测试with headed模式
npx playwright test tests/e2e/test_batch_simulation_enhancements.spec.js --headed
```

---

## 📊 测试计划时间表

| 任务 | 预计时间 | 状态 |
|------|---------|------|
| 单元测试编写 | 1h | ⏳ 待开始 |
| 集成测试编写 | 1h | ⏳ 待开始 |
| E2E测试编写 | 0.5h | ⏳ 待开始 |
| 文档编写 | 0.5h | ⏳ 待开始 |
| **总计** | **3h** | |

---

## 🎯 优先级顺序

1. **高优先级** (必须做):
   - ✅ 单元测试 (确保业务逻辑正确)
   - ✅ 集成测试 (确保API集成正确)
   - ✅ API文档更新 (确保使用者理解)

2. **中优先级** (应该做):
   - ✅ E2E测试 (确保用户流程正确)
   - ✅ 用户指南 (帮助最终用户)

3. **低优先级** (可以做):
   - ✅ Release Notes (版本发布时需要)

---

## 💡 测试最佳实践

### 单元测试
- 使用pytest + monkeypatch进行隔离测试
- 测试边界值和异常情况
- 清晰的测试命名 (test_xxx_should_yyy)

### 集成测试
- 使用真实的数据库/文件系统
- 验证完整的API请求/响应流程
- 测试错误处理和验证

### E2E测试
- 使用Playwright进行浏览器自动化
- 模拟真实用户操作
- 验证UI交互和业务流程

---

## 📝 质量检查清单

### 前端质量
- [ ] HTML语义化
- [ ] CSS响应式设计测试
- [ ] JavaScript无console错误
- [ ] 无hardcoded值
- [ ] 清晰的注释

### 后端质量
- [ ] 类型提示完整
- [ ] 异常处理完善
- [ ] Logging信息充分
- [ ] 函数长度 ≤ 30行
- [ ] 清晰的文档

### 整体质量
- [ ] 代码review完成
- [ ] 向后兼容性验证
- [ ] 性能基准测试
- [ ] 安全审计

---

## 🚀 后续步骤

### 完成Phase 5后
1. **代码review**: PR审查并合并
2. **版本标记**: 创建v1.0-Phase5-Complete标签
3. **发布**:
   - 更新CHANGELOG
   - 准备Release Notes
   - 部署到staging
   - 用户通知

### 可选优化 (Phase 6+)
1. **性能优化**:
   - 模板列表缓存
   - 前端表单状态优化

2. **功能扩展**:
   - 更多vehicle模板类型
   - 模板预设保存
   - 时长预设

3. **UX改进**:
   - 拖拽选择时长
   - 预览性能影响
   - 更详细的错误提示

---

**计划创建时间**: 2025-11-03
**预计完成时间**: 2025-11-05
**责任人**: Claude Code Assistant
