# 系统配置文件

本目录包含系统级别的配置文件。

## 文件说明

### `system_config.json.example`

批量仿真并发配置示例文件。复制此文件为 `system_config.json` 来覆盖默认设置。

**使用方法**：

1. **复制示例文件**：
   ```bash
   # Windows PowerShell
   Copy-Item config\system_config.json.example config\system_config.json
   
   # Linux/Mac
   cp config/system_config.json.example config/system_config.json
   ```

2. **编辑配置文件**：
   打开 `config/system_config.json`，修改 `concurrent_simulations_ratio` 值：
   ```json
   {
     "batch_simulation": {
       "concurrent_simulations_ratio": 0.75,  // 修改为你需要的比例
       "min_concurrent": 4,
       "max_concurrent": 80
     }
   }
   ```

3. **常用比例示例**：
   - `0.75` - 75%（默认，保守配置）
   - `1.0` - 100%（充分利用CPU）
   - `1.2` - 120%（激进配置，需谨慎使用）

## 配置优先级

配置生效的优先级（从高到低）：

1. **环境变量 `MAX_CONCURRENT_SIMULATIONS`**（绝对数值）
   ```bash
   # Windows PowerShell
   $env:MAX_CONCURRENT_SIMULATIONS = "12"
   
   # Linux/Mac
   export MAX_CONCURRENT_SIMULATIONS=12
   ```

2. **环境变量 `MAX_CONCURRENT_SIMULATIONS_RATIO`**（比例系数）
   ```bash
   # Windows PowerShell
   $env:MAX_CONCURRENT_SIMULATIONS_RATIO = "1.2"
   
   # Linux/Mac
   export MAX_CONCURRENT_SIMULATIONS_RATIO=1.2
   ```

3. **配置文件 `config/system_config.json`**（本文件）

4. **默认值**：0.75（75%）

## 配置项说明

### `concurrent_simulations_ratio`

- **类型**: 浮点数
- **默认值**: 0.75
- **说明**: CPU线程数的比例系数
- **示例**: 
  - 8核CPU × 0.75 = 6个并发任务
  - 8核CPU × 1.0 = 8个并发任务
  - 8核CPU × 1.2 = 9个并发任务（9.6取整）

### `min_concurrent`

- **类型**: 整数
- **默认值**: 4
- **说明**: 最小并发数，即使计算结果小于此值也会使用此值
- **用途**: 保证低CPU服务器也能有足够的并发

### `max_concurrent`

- **类型**: 整数
- **默认值**: 80
- **说明**: 最大并发数，即使计算结果大于此值也会限制在此值
- **用途**: 防止在高CPU服务器上创建过多任务导致资源竞争

## 注意事项

⚠️ **重要提示**：

1. **超过100%需谨慎**：设置为120%意味着任务数超过CPU核心数，可能导致：
   - CPU上下文切换开销增加
   - 内存压力增大
   - 单个任务执行变慢
   - 整体性能可能下降

2. **建议范围**：
   - **开发环境**: 0.5 - 0.75（50%-75%）
   - **生产环境**: 0.75 - 1.0（75%-100%）
   - **高性能服务器**: 可以尝试 1.0 - 1.2（需监控性能）

3. **监控指标**：
   - CPU使用率（应保持在合理范围）
   - 内存使用率
   - 任务执行时间（对比不同配置）

4. **配置文件位置**：
   - `config/system_config.json` 已被 `.gitignore` 忽略
   - 不会提交到版本控制系统
   - 每个环境可以有自己的配置

## 示例场景

### 场景1: 8核开发机，希望快速测试

```json
{
  "batch_simulation": {
    "concurrent_simulations_ratio": 1.0,
    "min_concurrent": 4,
    "max_concurrent": 80
  }
}
```
结果: 8核 × 1.0 = 8个并发任务

### 场景2: 16核生产服务器，保守配置

```json
{
  "batch_simulation": {
    "concurrent_simulations_ratio": 0.75,
    "min_concurrent": 4,
    "max_concurrent": 80
  }
}
```
结果: 16核 × 0.75 = 12个并发任务

### 场景3: 64核高性能服务器，最大化利用

```json
{
  "batch_simulation": {
    "concurrent_simulations_ratio": 1.0,
    "min_concurrent": 4,
    "max_concurrent": 80
  }
}
```
结果: 64核 × 1.0 = 64，但受 `max_concurrent: 80` 限制，实际为 64（未超过80）

### 场景4: 使用环境变量（临时测试）

```bash
# Windows PowerShell
$env:MAX_CONCURRENT_SIMULATIONS_RATIO = "1.2"
python api/main.py

# Linux/Mac
export MAX_CONCURRENT_SIMULATIONS_RATIO=1.2
python api/main.py
```

## 验证配置

启动API后，查看日志输出：

```
INFO: Concurrency calculation: 8 CPUs * 0.75 = 6, clamped to [4, 80] -> 6
```

这表明配置已正确加载并应用。

