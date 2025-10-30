# DHS 时间轴问题快速修复指南

**问题**: 应急车道开放策略配置页面有表格但没有时间轴，生成策略实例失败

**修复时间**: 5-10 分钟

---

## 🚀 快速修复步骤

### 步骤 1: 运行诊断脚本（必须）

1. **打开 DHS 参数配置页面**:
   - 访问: `http://localhost:8000/control/templates.html`
   - 选择"应急车道开放"模板
   - 选择路段
   - 进入步骤3（参数配置）

2. **打开浏览器开发者工具**:
   - 按 `F12` 键
   - 或右键点击页面 → "检查"

3. **切换到 Console 标签**

4. **复制并运行诊断脚本**:
   - 打开文件: `D:\projects\OD_SIM\fix_dhs_timeline.js`
   - 复制全部内容
   - 粘贴到控制台
   - 按 `Enter` 运行

5. **查看诊断结果**:
   - 脚本会自动检测所有问题
   - 绿色 ✅ 表示正常
   - 红色 ❌ 表示有问题
   - **截图保存诊断结果**（如果需要进一步帮助）

---

### 步骤 2: 根据诊断结果修复

#### 情况 A: "TimelineVisualizer 未加载"

**症状**:
```
❌ TimelineVisualizer 未加载！
```

**原因**: `timeline_visualizer.js` 脚本未正确加载

**修复方案**:

1. **检查文件是否存在**:
   ```bash
   ls frontend/control/js/timeline_visualizer.js
   ```

   如果文件不存在，说明代码未正确保存。

2. **强制刷新页面**:
   - 按 `Ctrl+F5`（Windows）
   - 或 `Cmd+Shift+R`（Mac）
   - 这会清除缓存并重新加载所有脚本

3. **清除浏览器缓存**:
   - Chrome: 按 `F12` → Settings → Clear cache
   - 或直接: `Ctrl+Shift+Delete` → 清除缓存

4. **重启浏览器**

5. **再次访问页面并重新运行诊断脚本**

---

#### 情况 B: "DHS 表格未找到"

**症状**:
```
❌ DHS 表格未找到！
```

**原因**: `renderDHSIntervalControl()` 函数未被调用或出错

**修复方案**:

1. **检查控制台是否有 JavaScript 错误**:
   - 查找红色错误消息
   - 特别注意 `Uncaught TypeError` 或 `Uncaught ReferenceError`

2. **检查模板是否正确**:
   - 确认选择的是 DHS 模板（"应急车道开放"）
   - 不是 VSS 或 TEC 模板

3. **检查参数类型路由**:
   在控制台运行：
   ```javascript
   // 检查当前模板的参数
   const params = window.currentTemplate?.parameters_schema;
   if (params) {
     params.forEach(p => {
       console.log(p.parameter_name, ':', p.parameter_type);
     });
   }
   ```

   应该看到：
   ```
   intervals : dhs_interval_array
   ```

4. **强制刷新并重新选择模板**

---

#### 情况 C: "时间轴未渲染"

**症状**:
```
✅ DHS 表格已找到
❌ 时间轴元素未找到！
```

**原因**: 时间轴创建失败或被跳过

**修复方案**:

1. **检查是否有错误提示**:
   - 在参数配置页面查找红色错误框
   - 如果看到 "⚠️ 时间轴可视化模块未加载"，说明 TimelineVisualizer 未加载

2. **手动测试时间轴创建**:
   在控制台运行：
   ```javascript
   // 测试时间轴渲染
   const testIntervals = [
     {begin_hours: 0, end_hours: 7, status: 'CLOSED'},
     {begin_hours: 7, end_hours: 9, status: 'OPEN'},
     {begin_hours: 9, end_hours: 17, status: 'CLOSED'},
     {begin_hours: 17, end_hours: 19, status: 'OPEN'},
     {begin_hours: 19, end_hours: 24, status: 'CLOSED'}
   ];

   if (typeof window.TimelineVisualizer !== 'undefined') {
     const timeline = window.TimelineVisualizer.renderTimeline(
       'test_intervals',
       testIntervals,
       { type: 'dhs', description: '测试DHS时间轴' }
     );

     // 添加到页面顶部（临时测试）
     document.body.insertBefore(timeline, document.body.firstChild);

     console.log('✅ 测试时间轴已添加到页面顶部');
   } else {
     console.error('❌ TimelineVisualizer 仍然未加载');
   }
   ```

   **预期结果**: 页面顶部出现时间轴（5 个时间槽：红-绿-红-绿-红）

3. **如果测试成功但参数页面仍无时间轴**:
   - 说明 `renderDHSIntervalControl()` 函数有问题
   - 检查 `parameter_form.js` 是否最新版本
   - 强制刷新页面

---

#### 情况 D: "生成策略实例失败（缺少 intervals）"

**症状**:
- 点击"生成策略实例"按钮后报错
- 错误消息包含 "intervals 参数缺失" 或类似内容

**原因**: 参数提取逻辑选择器错误

**修复方案**:

1. **检查表格 data 属性**:
   在控制台运行：
   ```javascript
   const tbody = document.querySelector('.dhs-intervals-tbody');
   console.log('tbody:', tbody);
   console.log('data-parameter-name:', tbody?.dataset.parameterName);
   ```

   **应该输出**:
   ```
   tbody: <tbody class="dhs-intervals-tbody" data-parameter-name="intervals">
   data-parameter-name: intervals
   ```

   **如果 `data-parameter-name` 为空或不是 "intervals"**:
   - 参数名称不匹配
   - 需要检查 `parameter_form.js` 中的 `tbody.dataset.parameterName = paramName;`

2. **手动测试参数提取**:
   在控制台运行：
   ```javascript
   const tbody = document.querySelector('.dhs-intervals-tbody[data-parameter-name="intervals"]');

   if (tbody) {
     const rows = tbody.querySelectorAll('.dhs-interval-row');
     console.log('找到', rows.length, '行');

     const intervals = Array.from(rows).map(row => ({
       begin_hours: parseFloat(row.querySelector('.dhs-interval-begin').value),
       end_hours: parseFloat(row.querySelector('.dhs-interval-end').value),
       status: row.querySelector('.dhs-interval-status').value,
       allowed_vehicle_types: row.querySelector('.dhs-interval-vehicles').value
         .split(',').map(v => v.trim()).filter(v => v)
     }));

     console.log('提取的 intervals:', intervals);
   } else {
     console.error('未找到表格！');
   }
   ```

   **预期输出**: 显示 5 个区间对象（与表格内容匹配）

3. **如果手动提取成功但策略创建仍失败**:
   - 检查 Network 标签中的请求 Payload
   - 查看是否包含 `intervals` 参数
   - 检查后端验证规则

---

## 🔧 通用修复方法

如果上述方法都不work，尝试以下通用方法：

### 方法 1: 完全重置

```bash
# 1. 停止服务器
# 按 Ctrl+C 停止正在运行的服务器

# 2. 激活 conda 环境
conda activate od_project

# 3. 清除 __pycache__
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# 4. 重启服务器
.\start_api.ps1

# 5. 强制刷新浏览器（Ctrl+F5）
```

---

### 方法 2: 检查文件完整性

确保以下文件存在且最新：

```bash
# 检查关键文件
ls -lh frontend/control/js/timeline_visualizer.js
ls -lh frontend/control/js/parameter_form.js
ls -lh frontend/control/templates.html

# 检查 DHS 模板
ls -lh templates/control_strategies/dynamic_hard_shoulder/dhs_base.json
ls -lh templates/control_strategies/dynamic_hard_shoulder/dhs_peak_hours.json
```

**所有文件都应该存在**。如果任何文件缺失，说明代码未正确保存。

---

### 方法 3: 比对最新代码

检查关键代码是否为最新版本：

**1. parameter_form.js 应该有 `renderDHSIntervalControl` 函数**:
```bash
grep -n "function renderDHSIntervalControl" frontend/control/js/parameter_form.js
```

应该输出类似: `674:function renderDHSIntervalControl(paramName, schema) {`

**2. templates.html 应该有 DHS 参数提取逻辑**:
```bash
grep -n "dhs_interval_array" frontend/control/templates.html
```

应该有多处匹配，包括参数提取部分（约 2971-2995 行）

**3. timeline_visualizer.js 应该有 DHS 颜色函数**:
```bash
grep -n "getDHSColor" frontend/control/js/timeline_visualizer.js
```

应该有定义和调用

---

## 📞 仍然无法解决？

如果以上所有方法都尝试过仍然无法解决，请提供以下信息：

### 1. 诊断脚本输出截图
   - 运行 `fix_dhs_timeline.js` 的完整输出
   - 包含所有 ✅ 和 ❌ 标记

### 2. 控制台错误截图
   - 所有红色错误消息
   - 包含完整的错误堆栈

### 3. Network 请求截图
   - 点击"生成策略实例"时的请求
   - 包含 Request Payload 和 Response

### 4. 页面截图
   - 显示表格但没有时间轴的页面

### 5. 文件版本信息
   ```bash
   # 运行此命令并提供输出
   ls -lh frontend/control/js/timeline_visualizer.js
   head -20 frontend/control/js/parameter_form.js | grep -A 5 "renderDHSIntervalControl"
   ```

---

## ✅ 验证修复成功

修复后，运行以下验证：

### 1. 视觉检查
- [ ] 参数配置页面显示时间轴（在表格上方）
- [ ] 时间轴有 5 个时间槽
- [ ] OPEN 槽为绿色，CLOSED 槽为红色
- [ ] 每个槽显示标签（"开启" 或 "关闭"）

### 2. 功能测试
- [ ] 修改表格值，时间轴自动更新（等待 300ms）
- [ ] 修改状态（OPEN ↔ CLOSED），槽颜色改变
- [ ] 添加新行，时间轴出现新槽
- [ ] 删除行，时间轴槽消失

### 3. 策略创建测试
- [ ] 填写所有必填参数
- [ ] 点击"生成策略实例"
- [ ] 策略创建成功
- [ ] 在策略列表中看到新策略

如果以上所有项都打勾 ✅，说明 DHS 时间轴功能已完全恢复！

---

**文档创建时间**: 2025-10-30
**预计修复时间**: 5-10 分钟
**难度**: ⭐⭐ 中等
