# Debug Reports Archive

本目录存储项目调试过程中产生的临时文档和诊断脚本。

## 目录结构

### dhs_template_inheritance/
DHS（应急车道开放）模板继承修复相关文档（2025-10-30）

**问题**: DHS 策略创建失败，缺少 `intervals` 参数

**根本原因**: `template_loader.py` 的 `load_template_with_schema()` 函数未解析模板继承

**修复**: 添加 `_resolve_template_inheritance()` 调用

**文档**:
- `DHS_FIX_SUCCESS_REPORT.md` - 修复成功报告（API 验证）
- `DHS_TEMPLATE_INHERITANCE_FIX.md` - 完整修复报告
- `DHS_INTERVALS_FIX_COMPLETE.md` - 修复详细说明
- `DHS_TEC_TIMELINE_COMPLETE.md` - 时间轴渲染修复
- `DHS_DEBUG_GUIDE.md` - 诊断指南
- `DHS_QUICK_FIX.md` - 快速修复指南
- `DHS_TIMELINE_TEST_GUIDE.md` - 时间轴测试指南
- `STRATEGY_CREATE_VERIFICATION.md` - 策略创建验证指南
- `SERVER_RESTART_GUIDE.md` - 服务器重启指南
- `VERIFY_DHS_FIX.md` - 验证指南
- `QUICK_VERIFICATION_STEPS.md` - 快速验证步骤
- `QUICK_FIX_SUMMARY.md` - 快速修复摘要

**脚本**:
- `test_template_inheritance.py` - 模板继承测试脚本
- `fix_dhs_timeline.js` - 前端时间轴诊断脚本
- `debug_batch_progress.py` - 批量进度调试脚本

### batch_monitoring/
批量仿真监控功能相关文档

**文档**:
- `BATCH_MONITORING_DEBUG_GUIDE.md` - 批量监控调试指南
- `BATCH_PROGRESS_ENHANCEMENT_REPORT.md` - 进度增强报告
- `BATCH_PROGRESS_FIX_REPORT.md` - 进度修复报告
- `E2E_TEST_REPORT_BATCH_MONITORING.md` - E2E 测试报告
- `NOTIFICATION_UPDATE_SUMMARY.md` - 通知更新摘要
- `NEXT_STEPS_BATCH_MONITORING.md` - 后续步骤
- `REAL_TIME_E2E_VALIDATION_REPORT.md` - 实时验证报告
- `REAL_TIME_E2E_VALIDATION_SUCCESS.md` - 实时验证成功报告
- `LIVE_CURVE_TOGGLE_QUICK_REFERENCE.md` - 实时曲线切换参考

## 使用说明

这些文档是调试过程中产生的临时记录，主要用于：

1. **问题诊断**: 记录问题现象和诊断步骤
2. **修复记录**: 详细记录修复过程和技术细节
3. **验证指南**: 提供修复后的验证步骤
4. **知识沉淀**: 为类似问题提供参考

**注意**:
- 这些文档是过程性记录，不是正式文档
- 正式文档请参考 `docs/` 目录下的主文档
- 如果问题已完全解决，这些文档可以归档或删除

## 清理建议

当对应功能稳定运行后（例如 3 个月无相关问题），可以考虑：

1. 将关键技术细节整合到正式文档
2. 删除临时诊断文档
3. 保留修复报告作为历史记录

---

**创建时间**: 2025-10-30
**最后更新**: 2025-10-30
