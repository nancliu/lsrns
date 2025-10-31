# CSS 优化快速参考指南

**目的**: 在执行 CSS 优化时快速查看映射关系和替换规则

---

## 🎨 颜色替换映射（按频率排序）

### 最常用的颜色（优先替换）

| 原值 | CSS 变量 | 用途 | 出现次数 |
|------|---------|------|-------:|
| #2c3e50 | `var(--color-dark)` | 深色/标题/主文本 | **38** |
| #7f8c8d | `var(--color-secondary-hover)` | 淡化文本/灰色 | **35** |
| #3498db | `var(--color-primary)` | 蓝色/链接/主按钮 | **27** |
| #ecf0f1 | `var(--color-light-border)` | 浅色文本/边框 | **19** |
| #e74c3c | `var(--color-danger)` | 红色/错误/删除 | **16** |
| #f8f9fa | `var(--color-light-hover)` | 浅色悬停背景 | **14** |
| #bdc3c7 | `var(--color-gray-200)` | 灰色背景/边框 | **13** |
| #667eea | `var(--color-info)` | 紫蓝/渐变颜色 | **10** |
| #e9ecef | `var(--color-border-light)` | 浅色边框 | **9** |
| #95a5a6 | `var(--color-secondary)` | 次要按钮 | **7** |
| #f9fafb | `var(--color-gray-50)` | 最浅灰背景 | **5** |
| #34495e | `var(--color-dark-hover)` | 深色悬停状态 | **5** |
| #2ecc71 | `var(--color-success)` | 绿色/成功 | **5** |

### 实施步骤

**方法 1: 使用 IDE 查找替换**

```
查找: #2c3e50
替换: var(--color-dark)
替换范围: frontend/control/css/ 目录

(或使用你的 IDE 的多文件替换功能)
```

**方法 2: 使用命令行 (Windows PowerShell)**

```powershell
# 替换单个颜色
Get-ChildItem "D:\projects\OD_SIM\frontend\control\css\*.css" |
    ForEach-Object { (Get-Content $_) -replace "#2c3e50", "var(--color-dark)" |
    Set-Content $_ }

# 或使用 sed (需要 Git Bash)
sed -i 's/#2c3e50/var(--color-dark)/g' frontend/control/css/*.css
sed -i 's/#7f8c8d/var(--color-secondary-hover)/g' frontend/control/css/*.css
# ... 继续其他颜色
```

---

## 📐 间距/尺寸替换映射

### 边距（Margin）替换

| 原值 | CSS 变量 | 备注 |
|------|---------|------|
| 3px | `var(--spacing-xs)` | 极小间距 |
| 4px | `var(--spacing-sm)` | 很小间距 |
| 5px | `var(--spacing-3)` | 小间距 |
| 8px | `var(--spacing-base)` | 基础间距 |
| 10px | `var(--spacing-10)` | 常用间距 |
| 12px | `var(--spacing-12)` | 常用间距 |
| 15px | `var(--spacing-15)` | 常用间距 |
| 20px | `var(--spacing-20)` | 常用大间距 |
| 30px | `var(--spacing-30)` | 主要间距 |
| 40px | `var(--spacing-40)` | 大间距 |

**替换命令示例**:
```bash
sed -i 's/\bpadding: 10px 25px;/padding: var(--spacing-10) var(--spacing-20);/g' frontend/control/css/*.css
```

### 圆角（Border-radius）替换

| 原值 | CSS 变量 | 用途 |
|------|---------|------|
| 3px | `var(--radius-sm)` | 细微圆角 |
| 4px | `var(--radius-base)` | 基础圆角 |
| 6px | `var(--radius-md)` | 中等圆角 |
| 8px | `var(--radius-lg)` | 大圆角 |
| 12px | `var(--radius-xl)` | 徽章/标签圆角 |
| 15px | `var(--radius-2xl)` | 更大圆角 |
| 20px | `var(--radius-3xl)` | 最大圆角 |

---

## ⏱️ 过渡时间替换

| 原值 | CSS 变量 | 用途 |
|------|---------|------|
| 0.15s | `var(--transition-fast)` | 快速反应（如按钮点击） |
| 0.2s | `var(--transition-fast)` | 快速反应 |
| 0.3s | `var(--transition-base)` | 标准过渡 |
| 0.5s | `var(--transition-slow)` | 缓慢过渡（动画） |

---

## 🎯 文件优化优先级

### 第 1 优先级（变量替换最有效）

1. **templates-base.css**
   - 包含最多的色值和间距
   - 影响范围广
   - 颜色数量最多

2. **templates-forms.css**
   - 表单相关的色值和间距
   - 影响所有表单页面

3. **simulations.css**
   - 需要删除 229 行重复代码
   - 优先级最高

### 第 2 优先级（代码清理）

4. **templates-inline-utilities.css**
   - 删除重复定义
   - 清理冗余类

5. **templates-layout.css**
   - 布局相关的变量替换

6. **templates-results.css**
   - 结果显示相关的变量替换

---

## ✅ 检查清单

### 颜色替换检查

```
□ #2c3e50 已全部替换为 var(--color-dark)
□ #7f8c8d 已全部替换为 var(--color-secondary-hover)
□ #3498db 已全部替换为 var(--color-primary)
□ #ecf0f1 已全部替换为 var(--color-light-border)
□ #e74c3c 已全部替换为 var(--color-danger)
□ #f8f9fa 已全部替换为 var(--color-light-hover)
□ #bdc3c7 已全部替换为 var(--color-gray-200)
□ #667eea 已全部替换为 var(--color-info)
□ ... 其他颜色已替换
```

### 间距替换检查

```
□ padding: Xpx 已改为使用 var(--spacing-*)
□ margin: Xpx 已改为使用 var(--spacing-*)
□ border-radius: Xpx 已改为使用 var(--radius-*)
□ gap: Xpx 已改为使用 var(--spacing-*)
□ 所有过渡时间已改为使用 var(--transition-*)
```

### simulations.css 清理检查

```
□ 行 3-7: * { margin: 0; ... } 已删除
□ 行 9-23: body { ... } 已删除
□ 行 20-48: .top-bar, .back-btn 已删除
□ 行 58-93: .sidebar 及其子元素已删除
□ 行 96-123: .content-area, .view 已删除
□ 其他重复的 layout 代码已删除
□ .plan-item, .config-section 等特定代码已保留
```

### 文件大小验证

```
优化前:
  - templates-inline-utilities.css: 950 行
  - simulations.css: 579 行
  - 总计: 2,350 行

优化后:
  - templates-inline-utilities.css: ~750 行 (-200)
  - simulations.css: ~350 行 (-229)
  - 总计: ~2,035 行 (-315)
```

---

## 🔍 验证步骤

### 1. 语法验证

```bash
# 使用 VS Code、WebStorm 或其他 IDE 的 CSS 检查功能
# 或使用在线工具: https://jigsaw.w3.org/css-validator/
```

### 2. 视觉验证

```bash
# 在浏览器中打开所有页面
# 检查颜色是否正确显示
# 检查间距是否正确应用
# 检查边框、阴影是否正常
```

### 3. 搜索验证

```bash
# 确保所有硬编码值都被替换
# 搜索: #[0-9a-f]{6}  (查找未替换的颜色值)
# 搜索: padding: [0-9]+px  (查找未替换的间距)
# 搜索: margin: [0-9]+px  (查找未替换的边距)
# 搜索: border-radius: [0-9]+px  (查找未替换的圆角)
```

---

## 💡 技巧和建议

### 使用 CSS 变量的最佳实践

```css
/* ✅ 好的做法 */
.button {
    padding: var(--spacing-10) var(--spacing-20);
    border-radius: var(--radius-base);
    background: var(--color-primary);
    transition: all var(--transition-base);
}

/* ❌ 不好的做法 */
.button {
    padding: 10px 25px;  /* 硬编码值 */
    border-radius: 4px;
    background: #3498db;  /* 硬编码颜色 */
    transition: all 0.3s;  /* 硬编码时间 */
}
```

### 调试 CSS 变量

```css
/* 使用 fallback 值，以防变量未定义 */
.element {
    color: var(--color-primary, #3498db);
}

/* 在浏览器开发工具中查看变量值 */
/* 右键 -> 检查 -> Styles 标签 -> 向下滚动到 :root 变量 */
```

### 性能优化

CSS 变量对性能的影响很小，甚至可能改善：
- 减少重复代码 = 更小的 CSS 文件
- 浏览器缓存整个 CSS 文件
- 变量计算开销极小 (< 1ms)

---

## 📞 常见问题

**Q: 替换后页面看起来不对？**
A: 检查是否遗漏了某些替换。使用搜索工具确保所有硬编码值都被替换了。

**Q: CSS 变量在哪个版本的浏览器中支持？**
A:
- Chrome 49+
- Firefox 31+
- Safari 9.1+
- Edge 15+
- IE 11: 不支持（需要 PostCSS fallback）

**Q: 如何回滚更改？**
A: 使用 Git：
```bash
git checkout frontend/control/css/  # 恢复单个目录
git checkout -- .  # 恢复所有更改
```

**Q: 优化对性能有影响吗？**
A: 没有负面影响，反而可能：
- 减少 CSS 文件大小
- 改善加载时间
- 变量计算开销极小

---

## 📊 预期结果

| 指标 | 优化前 | 优化后 | 改善 |
|------|--------|--------|------|
| CSS 文件大小 | 75 KB | 65 KB | ↓ 13% |
| 代码行数 | 2,350 | 2,035 | ↓ 19% |
| 颜色修改位置 | 28 | 1 | ↓ 97% |
| 修改配色时间 | 2-4 小时 | 5 分钟 | ↓ 95% |
| 新组件开发速度 | 100% | 130% | ↑ 30% |

---

## 🔗 相关文档

- [完整优化总结报告](../../CSS_OPTIMIZATION_SUMMARY.md)
- [详细实施计划](../../docs/css_optimization_plan.md)
- [CSS 变量定义](./variables.css)

---

**最后更新**: 2025-10-30
**版本**: v1.0
