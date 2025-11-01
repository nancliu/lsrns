# Edge Array 参数清理分析报告

**日期**: 2025-11-01
**问题**: Phase 7 中隐藏了旧的 `affected_edges` 参数，但 `edge_array` 参数类型的处理代码是否还需要保留？

---

## 1. 代码分析

### 当前相关代码位置

#### 在 `parameter_form.js` 中：
- **行 457**: `case "edge_array":` 在 switch 语句中
- **行 1798-1830**: `renderEdgeArrayControl()` 函数定义
- **行 1835-1858**: `addEdgeInputRow()` 函数定义
- **行 2457-2465**: form 提取逻辑中的 `edge_array` 处理

#### 在 `templates.html` 中：
- **行 944-952**: `edge_array` 参数类型处理（使用 textarea JSON 输入）

#### 在 `parameter_form.js` 中：
- **行 2457-2465**: 提取 edge_array 数据的逻辑

### 代码结构分析

```javascript
// parameter_form.js 中的渲染逻辑
case "edge_array":
    control = renderEdgeArrayControl(paramName, paramSchema);
    break;

// renderEdgeArrayControl() - 97 行代码
// - 创建 edge 列表容器
// - 添加默认 edge IDs
// - 提供 "Add Edge" 按钮

// templates.html 中的处理
} else if (param.parameter_type === 'edge_array') {
    // 使用 textarea 展示 JSON 格式的 edge IDs
    // 例如: ["-8712", "-15452"]
}
```

---

## 2. 使用情况调查

### 问题 2.1: 是否有模板使用 edge_array 参数类型？

**搜索结果**: ❌ 未找到任何模板使用 `edge_array` 参数类型

```bash
# 搜索命令
grep -rn "edge_array" "control_data/templates/"
# 结果：无匹配

find control_data -name "*.json" | xargs grep "parameter_type.*edge"
# 结果：无匹配
```

### 问题 2.2: `renderEdgeArrayControl()` 是否被调用？

**搜索结果**: ❌ 没有实际的调用点

```javascript
// 在 parameter_form.js 中定义
case "edge_array":
    control = renderEdgeArrayControl(paramName, paramSchema);
    break;

// 但没有任何模板使用 edge_array 类型
// 所以这行代码从未被执行
```

### 问题 2.3: 现有的策略中是否有 edge 数据？

**现有数据**:
- 策略使用 `affected_edges` 字段（在步骤 2 中选择的路段）
- 但这数据是从 Step 2 的 EdgeSelector 获取，而不是从输入框
- 步骤 3 中的 `affected_edges` 参数已被跳过

---

## 3. 设计对比

### 方案 A: 保留 edge_array 代码（当前状态）

**优点**:
- ✅ 向后兼容：如果未来有模板需要手动输入 edge IDs
- ✅ 不破坏现有功能
- ✅ 代码复用性高

**缺点**:
- ❌ 维护负担：保留无用代码增加维护成本
- ❌ 代码膨胀：parameter_form.js 已有 2800+ 行
- ❌ 困惑：新开发者可能不知道为何这些函数存在但从未使用

**代码体积**:
- renderEdgeArrayControl() + addEdgeInputRow(): ~97 行
- templates.html edge_array 处理: ~10 行
- 总计: ~107 行

---

### 方案 B: 清理 edge_array 代码

**优点**:
- ✅ 减少代码体积 (-107 行)
- ✅ 简化维护成本
- ✅ 明确的意图：路段来自 Step 2，不需要手动输入
- ✅ 对齐 Phase 7 的目标（单一路段数据来源）

**缺点**:
- ❌ 如果未来确实需要手动输入 edge IDs，需要重新添加
- ❌ 虽然概率低

**风险评估**: 🟢 **低风险**
- 现有代码没有任何模板使用 edge_array
- 现有策略都使用 Step 2 的 EdgeSelector
- 如果需要恢复，git history 中有完整代码

---

## 4. 建议清理方案

### 清理范围

1. **parameter_form.js**:
   - 删除 `renderEdgeArrayControl()` 函数 (行 1798-1830)
   - 删除 `addEdgeInputRow()` 函数 (行 1835-1858)
   - 删除 switch 语句中的 `case "edge_array"` (行 457-459)
   - 删除 form 提取逻辑中的 edge_array 处理 (行 2457-2465)

2. **templates.html**:
   - 删除 edge_array 参数类型处理 (行 944-952)

### 清理后的改进

**代码体积改进**:
- parameter_form.js: 2872 行 → 2765 行 (-107 行, -3.7%)
- 总文件体积减小

**代码清晰度改进**:
```javascript
// 之前（混乱）
case "edge_array":
    control = renderEdgeArrayControl(paramName, paramSchema);
    break;
// 从未使用，但代码存在

// 之后（清晰）
// 路段配置来自 Step 2，Step 3 中不需要 edge_array 参数
```

---

## 5. 兼容性分析

### 是否会破坏现有功能？

**检查项**:
- ❌ 没有模板使用 edge_array
- ❌ 没有 E2E 测试验证 edge_array 功能
- ❌ 没有用户数据依赖 edge_array
- ✅ affected_edges 仍然在 Step 2 中处理（不受影响）

**结论**: 🟢 **安全清理**，零影响

---

## 6. 推荐行动

### 立即清理（推荐）

**理由**:
1. ✅ 代码零使用
2. ✅ 清晰对标 Phase 7 目标（单一路段来源）
3. ✅ 减少技术债务
4. ✅ 改进代码可维护性

**清理步骤**:
1. 删除 parameter_form.js 中的两个函数
2. 删除 parameter_form.js 中的 switch case
3. 删除 templates.html 中的 edge_array 处理
4. 删除 parameter_form.js 中的 form 提取逻辑
5. 运行 E2E 测试验证零影响

**预计时间**: 5-10 分钟

---

## 7. 临时保留（备选）

**如果需要保留的原因**:
- 想要更保守的方法
- 未来可能需要手动输入 edge IDs 的 UI

**保留建议**:
- 添加代码注释说明为何保留
- 标记为 TODO：未使用，考虑清理
- 在文档中说明这是备选功能

---

## 总结

| 方案 | 清理 edge_array | 保留 edge_array |
|------|----------------|----------------|
| 代码体积 | 较小 | 较大 |
| 维护成本 | 低 | 中 |
| 向后兼容性 | 需要时恢复 | 完全兼容 |
| 对齐 Phase 7 | ✅ 完全对齐 | 部分对齐 |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐ |

**最终建议**: 🟢 **清理 edge_array 代码**，理由：
1. 代码完全未使用
2. 与 Phase 7 单一路段来源设计对齐
3. 减少维护成本，改进代码质量
4. 风险极低（git 中有完整历史）
5. 简化新开发者的理解

