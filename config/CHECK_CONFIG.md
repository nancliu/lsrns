# 配置生效检查方法

## 方法1: 查看启动日志

重启服务后，查看日志输出，应该看到类似这样的信息：

```
INFO: Loaded concurrent_simulations_ratio=1.0 from ...\config\system_config.json
INFO: Concurrency calculation: 24 CPUs * 1.0 = 24, clamped to [4, 80] -> 24
```

或者如果使用了环境变量：
```
INFO: Using MAX_CONCURRENT_SIMULATIONS_RATIO=1.0
```

## 方法2: 创建新批次测试

1. 创建一个新的批量仿真批次
2. 启动该批次
3. 检查实际运行的并发任务数

新批次会使用最新配置，已运行的批次不受影响。

## 方法3: Python命令行测试

```powershell
python -c "from shared.control_tools.batch_simulation_scheduler import get_max_concurrent_simulations; print(f'当前配置的并发数: {get_max_concurrent_simulations()}')"
```

期望输出（24核，比例1.0）：
```
当前配置的并发数: 24
```

如果看到 18，说明还在使用旧配置（0.75比例）。

