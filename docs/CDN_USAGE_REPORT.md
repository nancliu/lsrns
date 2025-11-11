# CDN 使用情况报告

**日期**: 2025-11-10  
**问题**: jsDelivr.net 经常不可访问，影响前端功能  
**状态**: 需要替换

---

## 📊 CDN 使用统计

### 1. jsDelivr.net (❌ 经常不可访问)

#### Chart.js 库
- **版本**: 3.9.1 和 4.4.0
- **使用位置**:
  - `frontend/control/simulations.html` - Chart.js 4.4.0
  - `frontend/control/optimization.html` - Chart.js 4.4.0
  - `shared/templates/ranking_report_template.html` - Chart.js 3.9.1
  - 所有生成的 `ranking_report_*.html` 文件 - Chart.js 3.9.1

#### Bootstrap 库
- **版本**: 5.3.2
- **使用位置**:
  - `frontend/scenarios/scenario_browser.html` - Bootstrap CSS + JS
  - `frontend/scenarios/scenario_browser.html` - Bootstrap Icons 1.11.1

### 2. cdnjs.cloudflare.com (✅ 可用)

#### 测试库
- **使用位置**: `frontend/tests/unit/test_runner.html`
  - Mocha 10.2.0
  - Chai 4.3.7
  - Sinon.js 17.0.1

---

## 🔄 替换方案

### 方案 1: 替换为 cdnjs.cloudflare.com (推荐)

**优点**:
- Cloudflare CDN 稳定性高，国内访问相对较好
- 与现有测试文件使用的 CDN 一致
- 无需下载文件，保持 CDN 优势

**替换映射**:

| 原 CDN (jsDelivr) | 新 CDN (cdnjs.cloudflare) |
|------------------|---------------------------|
| `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js` | `https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js` |
| `https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js` | `https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js` |
| `https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css` | `https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/css/bootstrap.min.css` |
| `https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js` | `https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/js/bootstrap.bundle.min.js` |
| `https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css` | `https://unpkg.com/bootstrap-icons@1.11.1/font/bootstrap-icons.css` (注：cdnjs 不提供字体文件，使用 unpkg) |

### 方案 2: 替换为 unpkg.com

**优点**:
- npm 官方 CDN，资源丰富
- 国内访问相对稳定

**替换映射**:
- Chart.js: `https://unpkg.com/chart.js@4.4.0/dist/chart.umd.min.js`
- Bootstrap: `https://unpkg.com/bootstrap@5.3.2/dist/css/bootstrap.min.css`

### 方案 3: 下载到本地 (备选)

**优点**:
- 完全离线可用
- 不依赖外部 CDN

**缺点**:
- 需要维护版本更新
- 增加项目体积

**建议目录结构**:
```
frontend/
  libs/
    chart.js/
      4.4.0/
        chart.umd.min.js
      3.9.1/
        chart.min.js
    bootstrap/
      5.3.2/
        css/bootstrap.min.css
        js/bootstrap.bundle.min.js
    bootstrap-icons/
      1.11.1/
        font/bootstrap-icons.css
```

---

## 📝 需要修改的文件

### 主要文件（必须修改）

1. **`frontend/control/simulations.html`**
   - Chart.js 4.4.0

2. **`frontend/control/optimization.html`**
   - Chart.js 4.4.0

3. **`frontend/scenarios/scenario_browser.html`**
   - Bootstrap 5.3.2 CSS
   - Bootstrap Icons 1.11.1
   - Bootstrap 5.3.2 JS

### 模板文件（必须修改）

4. **`shared/templates/ranking_report_template.html`**
   - Chart.js 3.9.1
   - ⚠️ 注意：此模板会生成所有 ranking_report_*.html 文件

### 生成的报告文件（可选）

5. **所有 `frontend/control/ranking_report_*.html` 文件**
   - Chart.js 3.9.1
   - ⚠️ 这些是生成的报告文件，修改模板后新生成的报告会自动使用新 CDN

---

## ✅ 推荐操作

**优先方案**: 使用 **cdnjs.cloudflare.com** 替换所有 jsDelivr.net 链接

**理由**:
1. 与现有测试文件使用的 CDN 一致
2. Cloudflare CDN 稳定性高
3. 无需下载文件，保持 CDN 优势
4. 修改简单，只需替换 URL

---

## 🔍 验证步骤

替换后需要验证：
1. ✅ Chart.js 图表正常显示
2. ✅ Bootstrap 样式正常加载
3. ✅ Bootstrap Icons 图标正常显示
4. ✅ 批量仿真进度曲线正常显示
5. ✅ 方案优化页面图表正常显示
6. ✅ 场景浏览器页面样式正常

---

## 📌 注意事项

1. **模板文件**: `shared/templates/ranking_report_template.html` 修改后，新生成的报告会自动使用新 CDN
2. **旧报告文件**: 已生成的 `ranking_report_*.html` 文件仍使用旧 CDN，如需更新可批量替换或重新生成
3. **版本一致性**: 确保替换后的版本号与原版本一致，避免 API 不兼容问题

