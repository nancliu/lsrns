# 根目录文件清理快速参考

## 📊 文件统计

- **MD文件**: 35个
- **TXT文件**: 1个  
- **JS文件**: 2个
- **总计**: 38个文件

---

## 🎯 快速分类

### ✅ 保留在根目录（3个）
- `README.md` - 项目主文档
- `START_HERE.md` - 项目导航
- `CLAUDE.md` - AI助手指南

### 🗑️ 立即删除（2个JS）
- `test_batch_progress.js` - 临时测试脚本
- `test_batch_live_monitoring_complete.js` - 临时测试脚本

### 📦 归档到 docs/progress/（27个）

**DAY_6_7系列** → `docs/progress/day_6_7/`
- DAY_6_7_CODE_METRICS_ANALYSIS.md
- DAY_6_7_CODE_REVIEW_CHECKLIST.md
- DAY_6_7_FINAL_SUMMARY.md
- DAY_6_7_README.md
- DAY_6_7_TEST_FIX_GUIDE.md
- DAY_6_7_VERIFICATION_REPORT.md

**PHASE2系列** → `docs/progress/phase2/`
- PHASE2a_COMPLETION_REPORT.md
- PHASE2b_COMPLETION_REPORT.md
- PHASE2c_EXTENDED_COMPLETION_SUMMARY.md

**CSS优化** → `docs/progress/css_optimization/`
- CSS_OPTIMIZATION_COMPLETED.md
- CSS_OPTIMIZATION_SUMMARY.md
- CSS_SEPARATION_COMPLETE_FINAL_REPORT.md
- CSS_SEPARATION_PHASE2_SUMMARY.md

**TEMPLATES重构** → `docs/progress/templates_refactoring/`
- TEMPLATES_CSS_SEPARATION_COMPLETION.md
- TEMPLATES_HTML_CODE_REVIEW.md
- TEMPLATES_REFACTORING_COMPLETION_REPORT.md
- TEMPLATES_REFACTORING_QUICK_GUIDE.md
- TEMPLATES_REFACTORING_STRATEGY.md

**实现总结** → `docs/progress/`
- IMPLEMENTATION_STATUS_2025-10-30.md
- IMPLEMENTATION_SUMMARY.md
- SESSION_COMPLETION_SUMMARY_2025-10-30.md
- DOCUMENTATION_ORGANIZATION_COMPLETE.md

### 📦 归档到 docs/debug_reports/（11个）

**批量监控** → `docs/debug_reports/batch_monitoring/`
- BATCH_MONITORING_DEBUG_GUIDE.md
- BATCH_MONITORING_QUICK_FIX_PLAN.md
- BATCH_PROGRESS_MONITORING_ANALYSIS.md
- LIVETIMESERIES_DATA_FLOW.md

**前端调试** → `docs/debug_reports/frontend/`
- FRONTEND_DEBUG_GUIDE.md
- FRONTEND_PROGRESS_MONITORING_FUNCTIONS.md

**其他调试** → `docs/debug_reports/`
- CONCURRENT_FILEACCESS_FIX.md
- MONITORING_ANALYSIS_SUMMARY.md
- UNIFIED_SUMMARY_XML_READING_ANALYSIS.md
- COMPREHENSIVE_VALIDATION_REPORT.md
- CLEANUP_SUMMARY.md → `docs/cleanup/`

### 📦 归档到 docs/testing/（3个）
- TEST_RESULTS_SUMMARY.md
- PLAYWRIGHT_TESTING_GUIDE.md
- VALIDATION_ARTIFACTS_INDEX.md

### 📦 归档到 docs/openspec/（2个）
- OPENSPEC_APPLY_SUMMARY.md
- OPENSPEC_WORKFLOW_GUIDE.md

### ⚠️ 检查重复（1个）
- `AGENTS.md` - 检查是否与 `openspec/AGENTS.md` 重复

### 🗑️ 删除或归档（1个TXT）
- `ANALYSIS_SUMMARY.txt` - 如有MD版本则删除

---

## 🚀 快速执行命令

### 1. 创建归档目录
```powershell
@('progress/day_6_7', 'progress/phase2', 'progress/css_optimization', 'progress/templates_refactoring', 'debug_reports/batch_monitoring', 'debug_reports/frontend', 'openspec') | ForEach-Object { New-Item -ItemType Directory -Path "docs\$_" -Force }
```

### 2. 删除临时脚本
```powershell
Remove-Item test_batch_progress.js, test_batch_live_monitoring_complete.js -ErrorAction SilentlyContinue
```

### 3. 批量移动文件（示例：DAY_6_7系列）
```powershell
@('DAY_6_7_CODE_METRICS_ANALYSIS.md', 'DAY_6_7_CODE_REVIEW_CHECKLIST.md', 'DAY_6_7_FINAL_SUMMARY.md', 'DAY_6_7_README.md', 'DAY_6_7_TEST_FIX_GUIDE.md', 'DAY_6_7_VERIFICATION_REPORT.md') | ForEach-Object { if (Test-Path $_) { Move-Item $_ "docs\progress\day_6_7\" -Force } }
```

---

## 📈 预期效果

- **清理前**: 38个文件在根目录
- **清理后**: 3个核心文档在根目录
- **归档**: 35个文档按主题组织到 `docs/` 子目录

---

**详细分析**: 参见 `docs/ROOT_FILES_ANALYSIS.md`

