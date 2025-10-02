# SUMO Summary文件实时监测技术方案

**版本**: v1.0
**创建日期**: 2025-10-02
**适用场景**: 管控方案优化子系统 - 峰值车辆数实时监测
**关联Epic**: Epic 2 (并行实例管理增强)

---

## 一、SUMO Summary文件特性分析

### 1.1 Summary文件是实时输出的吗？

**✅ 是的，summary.xml是实时追加写入的文件**

#### 工作机制

```
SUMO仿真运行过程:
时间步 0  → 写入 <step time="0.00" .../>    ← 立即写入磁盘
时间步 1  → 写入 <step time="1.00" .../>    ← 立即写入磁盘
时间步 2  → 写入 <step time="2.00" .../>    ← 立即写入磁盘
...
时间步 N  → 写入 <step time="N.00" .../>    ← 立即写入磁盘
```

**关键特性**：
1. ✅ **逐步追加**: SUMO每完成一个时间步，就追加一行 `<step>` 元素到文件末尾
2. ✅ **立即刷新**: 数据会立即刷新到磁盘（buffered I/O，但频率很高）
3. ✅ **无需等待**: 不需要等仿真完成，可以边运行边读取
4. ✅ **线性增长**: 文件大小随仿真时间线性增长

#### 实际验证

从示例文件可以看出：
```xml
<!-- 文件头部：仿真配置信息 -->
<summary>
    <step time="0.00" loaded="2322" inserted="212" running="212" .../>
    <step time="1.00" loaded="2322" inserted="212" running="212" .../>
    <step time="2.00" loaded="2322" inserted="215" running="215" .../>
    ...
    <step time="900.00" .../>  <!-- 仿真结束时间 -->
</summary>
```

文件从时间0开始逐步追加到结束时间（本例中为900秒）。

### 1.2 Summary文件可以获取哪些指标？

#### 每个时间步的完整指标（每行数据）

根据实际示例文件分析，每个 `<step>` 元素包含以下属性：

| 指标类别 | 属性名 | 含义 | 单位 | 示例值 |
|---------|--------|------|------|--------|
| **时间** | `time` | 当前仿真时间 | 秒 | 800.00 |
| **车辆加载** | `loaded` | 累计加载的车辆总数 | 辆 | 24089 |
| **车辆插入** | `inserted` | 累计插入到路网的车辆数 | 辆 | 15776 |
| **在网车辆** | `running` | **当前在路网中运行的车辆数** ⭐ | 辆 | 10647 |
| **等待车辆** | `waiting` | 等待进入路网的车辆数 | 辆 | 8313 |
| **完成车辆** | `ended` | 累计完成行程的车辆数 | 辆 | 5129 |
| **到达车辆** | `arrived` | 累计到达目的地的车辆数 | 辆 | 5129 |
| **碰撞次数** | `collisions` | 累计碰撞次数 | 次 | 216 |
| **瞬移次数** | `teleports` | 累计瞬移次数 | 次 | 0 |
| **停车车辆** | `halting` | 当前停止的车辆数 | 辆 | 762 |
| **停靠车辆** | `stopped` | 当前在停靠站的车辆数 | 辆 | 0 |
| **平均等待时间** | `meanWaitingTime` | 当前车辆的平均等待时间 | 秒 | 101.92 |
| **平均行程时间** | `meanTravelTime` | 当前车辆的平均行程时间 | 秒 | 284.88 |
| **平均速度** | `meanSpeed` | 当前车辆的平均速度 | m/s | 23.28 |
| **相对平均速度** | `meanSpeedRelative` | 相对限速的平均速度 | 比例 | 0.65 |
| **执行耗时** | `duration` | 该时间步的计算耗时 | 毫秒 | 262 |

#### 核心监测指标（重点）

1. **峰值车辆数监测** ⭐⭐⭐
   - **指标**: `running` - 当前在网车辆数
   - **实时性**: 每个时间步更新
   - **用途**: 找出峰值时刻和峰值数量

2. **流量平衡监测**
   - **公式**: `loaded = inserted + waiting`
   - **用途**: 验证OD数据加载是否正常

3. **完成率监测**
   - **公式**: `completion_rate = arrived / loaded * 100%`
   - **用途**: 评估路网通行能力

4. **平均速度监测**
   - **指标**: `meanSpeed`
   - **用途**: 评估路网运行效率

5. **拥堵指标监测**
   - **指标**: `halting` - 停止车辆数
   - **指标**: `meanWaitingTime` - 平均等待时间
   - **用途**: 识别拥堵程度

6. **实时比监测**
   - **公式**: `real_time_ratio = duration / 1000`（如果仿真时间步长为1秒）
   - **用途**: 评估仿真性能

---

## 二、实时监测技术方案

### 2.1 方案A：文件尾部追踪（✅ 已选定）

**原理**: 类似 `tail -f`，持续读取文件新增内容

**监测间隔**:
- **默认**: 30秒
- **可配置**: 支持通过环境变量或配置文件调整
- **设计考虑**: 60实例并行时，30秒间隔可确保系统负载可控

#### 优点
- ✅ 实时性适中（30秒延迟可接受，满足业务需求）
- ✅ 资源占用低（只读增量，60实例×30秒=低I/O负载）
- ✅ 实现简单
- ✅ 适合长时间仿真
- ✅ 扩展性好（支持更大规模并行）

#### 实现方式

```python
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional
import time

class SummaryRealTimeMonitor:
    """
    SUMO summary.xml 实时监测器

    Args:
        summary_file_path: summary.xml文件路径
        monitoring_interval: 监测间隔（秒），默认30秒
    """
    def __init__(self, summary_file_path: str, monitoring_interval: int = 30):
        self.summary_file = Path(summary_file_path)
        self.monitoring_interval = monitoring_interval
        self.last_position = 0
        self.current_stats = {
            "current_time": 0,
            "running": 0,
            "peak_running": 0,
            "peak_time": 0,
            "loaded": 0,
            "inserted": 0,
            "waiting": 0,
            "arrived": 0,
            "mean_speed": 0.0,
            "mean_waiting_time": 0.0
        }

    def read_new_steps(self) -> list:
        """
        读取自上次位置以来新增的step元素
        """
        if not self.summary_file.exists():
            return []

        new_steps = []
        try:
            with open(self.summary_file, 'r', encoding='utf-8') as f:
                # 跳到上次读取位置
                f.seek(self.last_position)

                # 读取新内容
                new_content = f.read()

                # 更新位置
                self.last_position = f.tell()

                # 解析新增的step行
                for line in new_content.split('\n'):
                    if '<step ' in line and '/>' in line:
                        new_steps.append(line.strip())

        except Exception as e:
            print(f"Error reading summary file: {e}")

        return new_steps

    def parse_step_line(self, step_line: str) -> Optional[Dict]:
        """
        解析单个step行
        """
        try:
            # 包装成完整的XML元素进行解析
            wrapped = f"<root>{step_line}</root>"
            root = ET.fromstring(wrapped)
            step_elem = root.find('step')

            if step_elem is None:
                return None

            return {
                "time": float(step_elem.get('time', 0)),
                "running": int(step_elem.get('running', 0)),
                "loaded": int(step_elem.get('loaded', 0)),
                "inserted": int(step_elem.get('inserted', 0)),
                "waiting": int(step_elem.get('waiting', 0)),
                "arrived": int(step_elem.get('arrived', 0)),
                "halting": int(step_elem.get('halting', 0)),
                "mean_speed": float(step_elem.get('meanSpeed', 0)),
                "mean_waiting_time": float(step_elem.get('meanWaitingTime', 0)),
                "duration_ms": int(step_elem.get('duration', 0))
            }
        except Exception as e:
            print(f"Error parsing step line: {e}")
            return None

    def update_statistics(self, step_data: Dict):
        """
        更新统计数据
        """
        self.current_stats['current_time'] = step_data['time']
        self.current_stats['running'] = step_data['running']
        self.current_stats['loaded'] = step_data['loaded']
        self.current_stats['inserted'] = step_data['inserted']
        self.current_stats['waiting'] = step_data['waiting']
        self.current_stats['arrived'] = step_data['arrived']
        self.current_stats['mean_speed'] = step_data['mean_speed']
        self.current_stats['mean_waiting_time'] = step_data['mean_waiting_time']

        # 更新峰值
        if step_data['running'] > self.current_stats['peak_running']:
            self.current_stats['peak_running'] = step_data['running']
            self.current_stats['peak_time'] = step_data['time']

    def poll_updates(self):
        """
        轮询监测（读取自上次以来的新数据）

        注意：调用频率由外部控制（建议30秒，适配60实例并行规模）
        """
        new_steps = self.read_new_steps()

        for step_line in new_steps:
            step_data = self.parse_step_line(step_line)
            if step_data:
                self.update_statistics(step_data)

        return self.current_stats

    def get_current_stats(self) -> Dict:
        """
        获取当前统计数据
        """
        return self.current_stats.copy()
```

#### 使用示例

```python
# 在worker进程中使用
def _run_simulation_worker_with_monitoring(
    shared_dict: Dict,
    instance_id: int,
    config_path: str
):
    """
    单个SUMO仿真实例工作进程 - 带实时监测
    """
    import subprocess
    from pathlib import Path

    instance_dir = Path(config_path).parent
    summary_file = instance_dir / "summary.xml"

    # 创建监测器（默认30秒间隔）
    monitor = SummaryRealTimeMonitor(str(summary_file), monitoring_interval=30)

    # 启动SUMO进程（非阻塞）
    process = subprocess.Popen(
        ["sumo", "-c", "simulation.sumocfg"],
        cwd=str(instance_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # 实时监测循环（默认30秒间隔）
    monitoring_interval = 30  # 可配置，考虑60实例并行规模

    while process.poll() is None:  # 进程还在运行
        time.sleep(monitoring_interval)  # 默认30秒检查一次

        # 读取新数据
        stats = monitor.poll_updates()

        # 更新共享字典（供主进程读取）
        shared_dict[f'instance_{instance_id}'] = {
            'status': 'running',
            'current_time': stats['current_time'],
            'running_vehicles': stats['running'],
            'peak_vehicles': stats['peak_running'],
            'peak_time': stats['peak_time'],
            'mean_speed': stats['mean_speed'],
            'completion_percentage': (stats['current_time'] / 3600) * 100  # 假设总时长3600秒
        }

    # 仿真完成，最后读取一次
    final_stats = monitor.poll_updates()
    shared_dict[f'instance_{instance_id}'] = {
        'status': 'completed',
        'final_stats': final_stats
    }

    process.wait()
```

### 2.2 方案B：定期全文解析（备选）

**原理**: 定期重新解析整个summary.xml文件

#### 优点
- ✅ 实现更简单
- ✅ 数据完整性高
- ✅ 无需维护读取位置

#### 缺点
- ⚠️ 资源占用高（重复解析）
- ⚠️ 大文件时性能差
- ⚠️ 不适合长时间仿真

#### 实现方式

```python
import xml.etree.ElementTree as ET

def parse_summary_full(summary_file: str) -> Dict:
    """
    完整解析summary.xml（适合小文件或仿真完成后）
    """
    tree = ET.parse(summary_file)
    root = tree.getroot()

    running_vehicles = []
    times = []

    for step in root.findall('step'):
        time_val = float(step.get('time', 0))
        running_val = int(step.get('running', 0))

        times.append(time_val)
        running_vehicles.append(running_val)

    # 找出峰值
    peak_idx = running_vehicles.index(max(running_vehicles))

    return {
        'total_steps': len(running_vehicles),
        'peak_vehicles': running_vehicles[peak_idx],
        'peak_time': times[peak_idx],
        'final_time': times[-1] if times else 0,
        'final_running': running_vehicles[-1] if running_vehicles else 0
    }
```

---

## 三、实时监测集成方案

### 3.1 元数据文件更新

在 `instance_status.json` 中实时更新：

```json
{
  "instance_id": 0,
  "status": "running",
  "updated_at": "2025-10-02T15:16:32",

  "simulation_progress": {
    "current_sim_time": 800,
    "total_sim_time": 3600,
    "completion_percentage": 22.2
  },

  "vehicle_statistics": {
    "current_running": 10647,        // ← 从summary实时读取
    "peak_vehicles": 10680,           // ← 实时更新峰值
    "peak_time": 782,                 // ← 峰值发生时间
    "loaded_vehicles": 24089,
    "arrived_vehicles": 5129,
    "waiting_vehicles": 8313
  },

  "traffic_metrics": {
    "mean_speed": 23.28,              // ← 平均速度
    "mean_waiting_time": 101.92,      // ← 平均等待时间
    "halting_vehicles": 762           // ← 停止车辆数
  },

  "performance_metrics": {
    "last_step_duration_ms": 262,     // ← 上一步计算耗时
    "estimated_real_time_ratio": 6.1  // ← 估算实时比
  }
}
```

### 3.2 Worker进程集成

修改 `parallel_simulator.py` 的worker函数：

```python
def _run_simulation_worker(
    shared_dict: Dict,
    instance_id: int,
    config_path: str,
    port: int
):
    """
    单个SUMO仿真实例的工作进程 - Epic 2增强版
    """
    import os
    import subprocess
    import json
    import time
    from pathlib import Path
    from datetime import datetime

    abs_config_path = os.path.abspath(config_path)
    config_dir = os.path.dirname(abs_config_path)
    parent_dir = Path(config_dir).parent
    instance_dir = parent_dir / f"instance_{instance_id}"

    # 创建实例元数据
    instance_metadata = {
        "instance_id": instance_id,
        "instance_dir": str(instance_dir),
        "created_at": datetime.now().isoformat()
    }
    metadata_file = instance_dir / "instance_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(instance_metadata, f, indent=2, ensure_ascii=False)

    # 创建实时监测器（默认30秒间隔，可通过环境变量配置）
    monitoring_interval = int(os.environ.get('MONITORING_INTERVAL', '30'))
    summary_file = instance_dir / "summary.xml"
    monitor = SummaryRealTimeMonitor(str(summary_file), monitoring_interval=monitoring_interval)

    # 启动SUMO进程
    process = subprocess.Popen(
        ["sumo", "-c", "simulation.sumocfg", "--no-step-log"],
        cwd=str(instance_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    start_time = time.time()

    # 实时监测循环（使用配置的间隔）
    while process.poll() is None:
        time.sleep(monitoring_interval)  # 默认30秒，可配置

        # 读取summary新数据
        stats = monitor.poll_updates()

        # 计算进度
        current_time = time.time()
        elapsed_seconds = current_time - start_time

        # 更新实例状态文件
        status_data = {
            "instance_id": instance_id,
            "status": "running",
            "updated_at": datetime.now().isoformat(),
            "simulation_progress": {
                "current_sim_time": stats['current_time'],
                "total_sim_time": 3600,  # TODO: 从配置读取
                "completion_percentage": (stats['current_time'] / 3600) * 100
            },
            "vehicle_statistics": {
                "current_running": stats['running'],
                "peak_vehicles": stats['peak_running'],
                "peak_time": stats['peak_time'],
                "loaded_vehicles": stats['loaded'],
                "arrived_vehicles": stats['arrived'],
                "waiting_vehicles": stats['waiting']
            },
            "traffic_metrics": {
                "mean_speed": stats['mean_speed'],
                "mean_waiting_time": stats['mean_waiting_time']
            },
            "execution": {
                "started_at": datetime.fromtimestamp(start_time).isoformat(),
                "elapsed_seconds": int(elapsed_seconds),
                "estimated_real_time_ratio": elapsed_seconds / stats['current_time'] if stats['current_time'] > 0 else 0
            }
        }

        # 原子性写入状态文件
        status_file = instance_dir / "instance_status.json"
        atomic_write_json(status_file, status_data)

        # 更新共享字典（供主进程快速查询）
        shared_dict[f'instance_{instance_id}'] = {
            'status': 'running',
            'current_time': stats['current_time'],
            'peak_vehicles': stats['peak_running'],
            'completion_percentage': status_data['simulation_progress']['completion_percentage']
        }

    # 等待进程结束
    return_code = process.wait()

    # 最终状态更新
    final_stats = monitor.poll_updates()
    end_time = time.time()
    total_duration = end_time - start_time

    final_status = {
        "instance_id": instance_id,
        "status": "completed" if return_code == 0 else "failed",
        "updated_at": datetime.now().isoformat(),
        "execution": {
            "started_at": datetime.fromtimestamp(start_time).isoformat(),
            "completed_at": datetime.fromtimestamp(end_time).isoformat(),
            "duration_seconds": int(total_duration),
            "real_time_ratio": total_duration / final_stats['current_time'] if final_stats['current_time'] > 0 else 0
        },
        "simulation_progress": {
            "current_sim_time": final_stats['current_time'],
            "total_sim_time": final_stats['current_time'],
            "completion_percentage": 100.0
        },
        "vehicle_statistics": {
            "total_vehicles": final_stats['loaded'],
            "peak_vehicles": final_stats['peak_running'],
            "peak_time": final_stats['peak_time'],
            "arrived_vehicles": final_stats['arrived']
        },
        "output_validation": {
            "summary_xml_exists": (instance_dir / "summary.xml").exists(),
            "tripinfo_xml_exists": (instance_dir / "tripinfo.xml").exists()
        }
    }

    if return_code != 0:
        stderr_output = process.stderr.read() if process.stderr else ""
        final_status["error"] = {
            "return_code": return_code,
            "stderr": stderr_output[:500]  # 只保存前500字符
        }

    status_file = instance_dir / "instance_status.json"
    atomic_write_json(status_file, final_status)

    shared_dict[f'instance_{instance_id}'] = {
        'status': final_status['status'],
        'final_stats': final_stats
    }
```

### 3.3 主进程监控

```python
class ParallelSimulator:
    """
    并行仿真执行器 - Epic 2增强版
    """

    def get_batch_realtime_status(self) -> Dict:
        """
        获取批次实时状态（汇总所有实例）
        """
        total_instances = len(self.workers)
        running_count = 0
        completed_count = 0
        failed_count = 0

        total_peak_vehicles = 0
        instance_stats = []

        for instance_id in range(total_instances):
            status_file = self.batch_dir / f"instance_{instance_id}" / "instance_status.json"

            if status_file.exists():
                with open(status_file, 'r', encoding='utf-8') as f:
                    instance_data = json.load(f)

                status = instance_data.get('status', 'unknown')
                if status == 'running':
                    running_count += 1
                elif status == 'completed':
                    completed_count += 1
                elif status == 'failed':
                    failed_count += 1

                # 汇总峰值
                peak = instance_data.get('vehicle_statistics', {}).get('peak_vehicles', 0)
                total_peak_vehicles += peak

                instance_stats.append({
                    'instance_id': instance_id,
                    'status': status,
                    'peak_vehicles': peak,
                    'completion': instance_data.get('simulation_progress', {}).get('completion_percentage', 0)
                })

        return {
            'total_instances': total_instances,
            'running': running_count,
            'completed': completed_count,
            'failed': failed_count,
            'total_peak_vehicles': total_peak_vehicles,
            'instances': instance_stats
        }
```

---

## 四、前端实时展示

### 4.1 实时峰值曲线

```html
<div class="peak-monitoring">
  <h3>峰值车辆数实时监控</h3>
  <canvas id="peakVehiclesChart"></canvas>
  <div class="current-stats">
    <p>当前最高峰值: <span id="currentPeak">0</span> 辆</p>
    <p>峰值出现时间: <span id="peakTime">--</span></p>
    <p>总峰值（所有实例）: <span id="totalPeak">0</span> 辆</p>
  </div>
</div>
```

### 4.2 实时刷新脚本

```javascript
// Phase 1: 30秒轮询
async function refreshPeakMonitoring(batchId) {
  try {
    const response = await fetch(`/api/v1/control_optimization/batches/${batchId}/realtime_status`);
    const data = await response.json();

    // 更新总峰值
    document.getElementById('totalPeak').textContent = data.total_peak_vehicles.toLocaleString();

    // 更新各实例峰值
    let maxPeak = 0;
    let maxPeakInstance = null;

    data.instances.forEach(inst => {
      if (inst.peak_vehicles > maxPeak) {
        maxPeak = inst.peak_vehicles;
        maxPeakInstance = inst;
      }
    });

    document.getElementById('currentPeak').textContent = maxPeak.toLocaleString();
    document.getElementById('peakTime').textContent = `实例${maxPeakInstance.instance_id}`;

    // 更新图表（Chart.js）
    updatePeakChart(data.instances);

    // 继续刷新
    if (data.running > 0) {
      setTimeout(() => refreshPeakMonitoring(batchId), 30000);  // 30秒
    }
  } catch (error) {
    console.error('Failed to refresh peak monitoring:', error);
  }
}
```

---

## 五、性能优化

### 5.1 监测频率优化（已确定方案）

**默认配置**: 30秒间隔（适配60实例并行规模）

| 场景 | 推荐频率 | 原因 | 60实例总I/O负载 |
|------|---------|------|----------------|
| **标准配置（推荐）** | **30秒** | **平衡实时性和系统负载** | **60次/30秒 = 2次/秒** ✅ |
| 小规模测试（<10实例） | 10秒 | 提高实时性 | 10次/10秒 = 1次/秒 |
| 短时仿真（<30分钟） | 15秒 | 适度提高响应 | 60次/15秒 = 4次/秒 |
| 调试模式 | 5秒 | 快速反馈 | 60次/5秒 = 12次/秒 ⚠️ |

**配置方式**:
```bash
# 通过环境变量配置
export MONITORING_INTERVAL=30  # 秒

# 或在代码中配置
monitor = SummaryRealTimeMonitor(file_path, monitoring_interval=30)
```

**性能考虑**:
- ✅ 30秒间隔下，60实例每秒仅2次I/O操作，系统负载极低
- ✅ Summary文件通常<10MB，读取耗时<10ms
- ✅ 总I/O吞吐: 60实例 × 10KB/次 × 2次/秒 ≈ 1.2MB/s（可忽略）

### 5.2 文件读取优化

```python
# 使用缓冲I/O
with open(summary_file, 'r', buffering=8192, encoding='utf-8') as f:
    # 读取操作
```

### 5.3 内存优化

```python
# 只保留最近N个时间步的数据
class SummaryRealTimeMonitor:
    def __init__(self, summary_file_path: str, history_limit: int = 100):
        self.history_limit = history_limit
        self.recent_steps = []  # 只保留最近100个step

    def update_statistics(self, step_data: Dict):
        self.recent_steps.append(step_data)
        if len(self.recent_steps) > self.history_limit:
            self.recent_steps.pop(0)  # 删除最旧的
```

---

## 六、总结

### 6.1 Summary文件核心特性

1. ✅ **实时输出**: SUMO逐步追加写入，无需等待仿真完成
2. ✅ **丰富指标**: 16+个指标涵盖车辆、速度、拥堵、性能
3. ✅ **峰值可监测**: `running` 属性直接反映当前在网车辆数
4. ✅ **轻量解析**: XML格式，单行解析即可提取数据

### 6.2 已确定方案

**Epic 2 Phase 1** ✅:
- 使用方案A（文件尾部追踪）
- **30秒监测间隔**（默认配置，可通过环境变量调整）
- 更新 `instance_status.json`
- 30秒前端轮询（与后端监测同步）
- 支持60实例并行规模

**Phase 2扩展**:
- WebSocket实时推送
- 多实例峰值曲线对比
- 历史峰值数据库存储

### 6.3 实施优先级

**P0 (本周)**:
1. 实现 `SummaryRealTimeMonitor` 类
2. 集成到 `parallel_simulator.py` worker进程
3. 更新 `instance_status.json` 包含峰值数据

**P1 (下周)**:
4. 实现批次级汇总API
5. 前端峰值监控页面
6. 峰值曲线图表（Chart.js）

---

**文档维护**: 随实现进展持续更新
**关联文档**:
- [并行任务状态管理与监测方案.md](./并行任务状态管理与监测方案.md)
- [TODO.md](./TODO.md)
