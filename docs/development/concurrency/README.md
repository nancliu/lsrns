# 并发仿真配置和优化文档

本目录包含批量仿真并发配置、性能优化和问题诊断的相关文档。

## 文档列表

### 配置文档

- **`../multiprocessing-pool-concurrency-enhancement.md`** - 使用multiprocessing.Pool突破Windows 28任务限制的未来计划（主文档）

### 分析和测试文档

- **`MULTIPROCESSING_POOL_ANALYSIS.md`** - multiprocessing.Pool方案分析
- **`POOL_TEST_RESULTS_ANALYSIS.md`** - Pool测试结果分析
- **`TROUBLESHOOTING_28_TASK_LIMIT.md`** - Windows 28任务限制问题诊断

### 测试脚本

- **`scripts/test_multiprocessing_pool.py`** - Pool方案测试脚本
- **`scripts/test_36_workers.py`** - 36个工作进程测试脚本
- **`scripts/test_concurrent_config.py`** - 并发配置验证脚本

## 快速参考

### 当前配置

- **位置**: `config/system_config.json`
- **当前并发比例**: 1.17（24核 × 1.17 = 28个任务）
- **配置优先级**: 环境变量 > 配置文件 > 默认值(0.75)

### 常用脚本

诊断和测试脚本位于项目根目录的 `scripts/` 目录：
- `check_concurrent_tasks.ps1` - 并发配置检查
- `diagnose_28_limit.ps1` - 28限制诊断
- `check_windows_limits.py` - Windows系统限制检查

### 相关配置文档

- `config/README.md` - 配置文件使用指南
- `config/PERFORMANCE_TUNING.md` - 性能调优指南
- `config/TROUBLESHOOTING.md` - 配置问题排查

## 文档说明

### 测试脚本

`scripts/` 目录下的测试脚本用于：
- 验证Pool方案可行性
- 测试36个工作进程创建
- 验证并发配置正确性

这些脚本**仅用于测试和验证**，不属于生产代码。

### 归档说明

本目录中的文档和脚本已从根目录归档，保持项目根目录整洁。

