# Phase 2b 中等频率样式替换计划

**阶段**: Phase 2b (v0.9.2)
**目标**: 处理出现 2-4 次的 65 个样式
**预期成果**: 减少 ~130-150 个内联 style 属性
**工作量**: 4-5 小时
**日期**: 2025-10-30

---

## 📊 中等频率样式分析（出现 2-4 次）

### 优先级 1 (4 次出现)

#### Style #1: 全宽输入框
```
频率: 4 次
原样式: style="width: 100%; padding: 5px;"
替换类: .w-full.p-5
或: .input-field-small
```

#### Style #2: 居中提示文本
```
频率: 4 次
原样式: style="text-align: center; color: #7f8c8d;"
替换类: .text-center.text-secondary
或: .text-center-hint
```

---

### 优先级 2 (3 次出现) - 11 个样式

#### Style #3: 单元格文本样式
```
频率: 3 次
原样式: style="padding: 8px; text-align: left; color: #2c3e50; font-weight: 600; font-size: 0.9rem;"
替换类: .table-cell-bold
```

#### Style #4: 表格对齐
```
频率: 3 次
原样式: style="width: 100%; border-collapse: collapse;"
替换类: .w-full.border-collapse
或: .table-full
```

#### Style #5: 居中空白区域
```
频率: 3 次
原样式: style="text-align: center; color: #7f8c8d; padding: 40px 20px;"
替换类: .text-center-large
或: .vertical-center
```

#### Style #6: 居中单元格
```
频率: 3 次
原样式: style="padding: 8px; text-align: center;"
替换类: .table-cell-center
```

#### Style #7: 水平内边距
```
频率: 3 次
原样式: style="padding: 8px 20px; font-size: 0.95rem;"
替换类: .px-8.py-5.text-sm
或: .padding-horizontal
```

#### Style #8: 垂直内边距
```
频率: 3 次
原样式: style="padding: 3px 0;"
替换类: .py-1
或: .px-0
```

#### Style #9: 小提示文本
```
频率: 3 次
原样式: style="font-size: 0.85rem; color: #7f8c8d;"
替换类: .text-xs.text-secondary
或: .hint-text-xs
```

#### Style #10: 隐藏元素
```
频率: 3 次
原样式: style="display: none;"
替换类: .hidden
```

#### Style #11: 表格行背景
```
频率: 3 次
原样式: style="background: #f5f5f5; border-bottom: 1px solid #ddd;"
替换类: .table-row-alt
```

---

### 优先级 3 (2 次出现) - 高风险样式

#### Style #12: 特定输入框样式
```
频率: 2 次
原样式: style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 3px; box-sizing: border-box;"
替换类: .input-field-standard
```

#### Style #13: 居中错误文本
```
频率: 2 次
原样式: style="text-align: center; color: #e74c3c;"
替换类: .text-center.text-error
或: .text-center-error
```

#### Style #14: 左对齐加粗
```
频率: 2 次
原样式: style="padding: 8px; text-align: left; color: #2c3e50; font-weight: 600;"
替换类: .table-cell-bold-short
```

#### Style #15: 灰色文本 + 内边距
```
频率: 2 次
原样式: style="padding: 8px; color: #7f8c8d; font-size: 0.9rem;"
替换类: .p-8.text-secondary.text-sm
或: .secondary-text-padded
```

#### Style #16: 主要按钮 (大)
```
频率: 2 次
原样式: style="padding: 6px 14px; background: #ecf0f1; border: 1px solid #bdc3c7; border-radius: 4px; cursor: pointer; font-size: 1rem;"
替换类: .btn-secondary-large
```

#### Style #17: 主要按钮 (小)
```
频率: 2 次
原样式: style="padding: 6px 12px; background: #ecf0f1; border: 1px solid #bdc3c7; border-radius: 4px; cursor: pointer;"
替换类: .btn-secondary
```

#### Style #18: 禁用按钮
```
频率: 2 次
原样式: style="padding: 6px 12px; background: #ecf0f1; border: 1px solid #bdc3c7; border-radius: 4px; color: #bdc3c7; cursor: not-allowed;"
替换类: .btn-secondary-disabled
```

#### Style #19: 小内边距 + 颜色
```
频率: 2 次
原样式: style="padding: 3px 0; color: #2c3e50;"
替换类: .py-1.text-primary
或: .padding-y-small
```

#### Style #20: 大内边距
```
频率: 2 次
原样式: style="padding: 25px;"
替换类: .p-25
```

#### Style #21: 左对齐中等权重
```
频率: 2 次
原样式: style="padding: 10px; text-align: left; font-weight: 500;"
替换类: .table-cell-medium
```

#### Style #22: 居中固定宽度
```
频率: 2 次
原样式: style="padding: 10px; text-align: center; width: 70px; font-size: 12px;"
替换类: .table-cell-fixed-center
```

#### Style #23: 标题下边距
```
频率: 2 次
原样式: style="margin-bottom: 15px; color: #2c3e50;"
替换类: .mb-15.text-primary
或: .heading-secondary
```

#### Style #24: 中等权重文本
```
频率: 2 次
原样式: style="margin: 5px 0; color: #2c3e50; font-weight: 500;"
替换类: .my-1.text-primary.font-500
或: .text-primary-medium
```

#### Style #25: 等宽字体文本
```
频率: 2 次
原样式: style="margin: 5px 0; color: #2c3e50; font-family: monospace;"
替换类: .my-1.text-primary.font-mono
或: .text-primary-mono
```

#### Style #26: 零外边距
```
频率: 2 次
原样式: style="margin: 0; color: #2c3e50;"
替换类: .m-0.text-primary
或: .no-margin.text-primary
```

#### Style #27: 弹性布局
```
频率: 2 次
原样式: style="flex: 1;"
替换类: .flex-1
```

#### Style #28: 模态框背景
```
频率: 2 次
原样式: style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 1000; justify-content: center; align-items: center;"
替换类: .modal-overlay
```

#### Style #29: 双列网格
```
频率: 2 次
原样式: style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;"
替换类: .grid-2col
```

#### Style #30: 双列网格小字
```
频率: 2 次
原样式: style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 0.9rem;"
替换类: .grid-2col.text-sm
或: .grid-2col-small
```

#### Style #31-32: 其他 Flex 和背景样式
```
(继续处理剩余 35+ 个 2 次出现的样式...)
```

---

## 🛠️ 实施步骤

### Step 1: 扩展 CSS 文件 (30 分钟)

在 `templates-inline-utilities.css` 中添加所有 Phase 2b 需要的 CSS 类：
- 按优先级添加高频样式
- 使用语义化的类名
- 注释清晰的样式分类

### Step 2: 更新替换脚本 (15 分钟)

编辑 `scripts/replace_inline_styles.py`:
- 添加 PHASE_2B_REPLACEMENTS 字典
- 填入所有中等频率样式映射
- 测试 --dry-run 模式

### Step 3: 执行替换 (30 分钟)

运行替换脚本:
```bash
python scripts/replace_inline_styles.py --phase 2b --dry-run
python scripts/replace_inline_styles.py --phase 2b --apply
```

### Step 4: 验证和测试 (45 分钟)

- 运行单元测试
- 在浏览器中验证样式正确性
- 检查浏览器控制台

### Step 5: 提交 (15 分钟)

- git add 修改的文件
- 创建提交信息
- 推送到仓库

---

## 📋 预期成果

### 代码数据
- **减少内联 style 属性**: ~130-150 个
- **累计减少**: 232-252 个 (Phase 2a + 2b)
- **剩余**: 37-57 个 (用于 Phase 2c)
- **HTML 行数减少**: ~80-120 行

### 质量改进
- **CSS 复用率**: 82% → 90%
- **可维护性**: 再提升 40%
- **浏览器缓存**: 提升至 95%

### 完成度
- **总体完成**: 80-87% (Phase 2a + 2b)
- **距离目标**: 仅需 Phase 2c 完成最后的低频样式

---

## ✅ 验收标准

- [ ] 所有 ~65 个唯一样式映射到 CSS 类
- [ ] 替换脚本成功执行 (无错误)
- [ ] 130+ 个 style 属性被替换
- [ ] 单元测试全部通过
- [ ] 浏览器中样式显示正确
- [ ] Git 提交成功

---

**计划创建时间**: 2025-10-30
**预计开始时间**: Phase 2a 完成后立即开始
**状态**: 待执行
