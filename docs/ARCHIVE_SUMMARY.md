# 文档归档总结

**归档日期**: 2025-11-02  
**原因**: 保持项目根目录整洁（符合RULE-ROOT-001）

## 归档规则

### 会话总结类
**位置**: `docs/session-summaries/`
- SESSION_CONTINUATION_SUMMARY_20251102.md
- VEHICLE_TYPES_SESSION_SUMMARY.md

### 开发文档类
**位置**: `docs/development/`
- IMPLEMENTATION_SUMMARY_20251102.md
- STRATEGY_VALIDATION_REPORT_20251102.md
- PHASE1_STATUS_BOARD.md
- multiprocessing-pool-concurrency-enhancement.md

### 并发相关文档
**位置**: `docs/development/concurrency/`
- MULTIPROCESSING_POOL_ANALYSIS.md
- POOL_TEST_RESULTS_ANALYSIS.md
- TROUBLESHOOTING_28_TASK_LIMIT.md
- scripts/ (测试脚本)

### 清理相关文档
**位置**: `docs/cleanup/`
- REDUNDANT_CONTROL_CLEANUP_SUMMARY.md

### 模板相关文档
**位置**: `docs/templates/`
- VEHICLE_TYPES_UNIFICATION_RECOMMENDATION.md

### UI相关文档
**位置**: `docs/`
- BATCH_CARD_QUICK_REFERENCE.txt
- BATCH_CARD_UI_COMPLETION_REPORT.md
- BUTTON_COLOR_DISTINCTION_UPDATE.md
- BUTTON_COLOR_ENHANCEMENT.md
- BUTTON_COLOR_REFERENCE.txt
- DUAL_TABS_IMPLEMENTATION_SUMMARY.txt
- BATCH_CARD_BUTTON_LAYOUT.md
- BATCH_CARD_COLOR_SCHEME.md
- BATCH_CARD_UI_DESIGN.md
- BATCH_CARD_UI_UPDATE_SUMMARY.md
- BATCH_CARD_VISUAL_REFERENCE.txt
- BATCH_SIMULATION_DUAL_TABS_IMPLEMENTATION.md
- BATCH_SIMULATION_USER_GUIDE.md

### 测试脚本
**位置**: `tests/unit/`
- test_all_11_templates_fixed.py
- test_create_all_templates.py
- test_strategy_creation.py

### 已删除（临时文件）
- test_output.txt
- test_output_v2.txt

## 根目录保留文件

以下文件保留在根目录（符合RULE-ROOT-001）：
- README.md - 项目说明文档
- CLAUDE.md - AI助手开发指南
- AGENTS.md - OpenSpec代理说明
- CHANGELOG.md - 变更日志
- requirements.txt - Python依赖
- package.json - Node.js依赖
- start_api.* - 启动脚本

## 查找文档

如果找不到某个文档，可以：
1. 在对应的分类目录中查找
2. 使用 `git log --all --full-history -- <filename>` 查找文件历史位置
3. 查看本归档总结文档

