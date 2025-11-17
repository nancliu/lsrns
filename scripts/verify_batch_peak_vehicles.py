"""
验证批次在网车辆数峰值
"""
import json
from pathlib import Path

batch_id = "batch_20251102_235406"
case_id = "case_20251028_091831"

batch_dir = Path(f"cases/{case_id}/simulations/plan_opti/{batch_id}")
progress_file = batch_dir / "batch_progress.json"

if not progress_file.exists():
    print(f"批次文件不存在: {progress_file}")
    exit(1)

# 读取批次进度
with open(progress_file, 'r', encoding='utf-8') as f:
    progress = json.load(f)

tasks = progress['tasks']
completed_tasks = [t for t in tasks if t.get('status') == 'completed']

print(f"批次ID: {batch_id}")
print(f"总任务数: {len(tasks)}")
print(f"已完成任务数: {len(completed_tasks)}")
print(f"批次状态: {progress.get('status')}")
print()

# 读取每个已完成任务的live_curve_cache.json，汇总在网车辆数
all_time_series = {}
task_count = 0

for task in completed_tasks:
    plan_id = task.get('plan_id')
    seed = task.get('seed')
    
    if not plan_id or not seed:
        continue
    
    cache_file = batch_dir / plan_id / f"sim_{seed}" / "live_curve_cache.json"
    
    if not cache_file.exists():
        print(f"警告: {plan_id}/sim_{seed} 的缓存文件不存在")
        continue
    
    with open(cache_file, 'r', encoding='utf-8') as f:
        cache_data = json.load(f)
    
    # 汇总该任务的时序数据
    for entry in cache_data:
        time_step = entry.get('time', 0)
        running = entry.get('running', 0)
        
        if time_step not in all_time_series:
            all_time_series[time_step] = []
        all_time_series[time_step].append(running)
    
    task_count += 1

print(f"成功读取 {task_count} 个任务的时序数据")
print()

# 计算每个时间点的总在网车辆数（所有任务在同一时刻的车辆数之和）
aggregated_data = {}
for time_step, running_values in all_time_series.items():
    # 对于每个时间点，汇总所有任务的车辆数
    total_running = sum(running_values)
    aggregated_data[time_step] = {
        'total_running': total_running,
        'task_count': len(running_values),
        'avg_per_task': total_running / len(running_values) if running_values else 0
    }

# 找到峰值
if aggregated_data:
    sorted_times = sorted(aggregated_data.keys())
    peak_time = max(aggregated_data.keys(), key=lambda t: aggregated_data[t]['total_running'])
    peak_value = aggregated_data[peak_time]['total_running']
    
    print(f"时间点总数: {len(sorted_times)}")
    print(f"时间范围: {sorted_times[0]}s - {sorted_times[-1]}s")
    print()
    print(f"峰值信息:")
    print(f"  峰值时间: {peak_time}s")
    print(f"  峰值在网车辆数: {peak_value:,.0f} 辆")
    print(f"  参与汇总的任务数: {aggregated_data[peak_time]['task_count']}")
    print(f"  平均每任务: {aggregated_data[peak_time]['avg_per_task']:,.0f} 辆")
    print()
    
    # 显示前10个最高值
    print("前10个最高值:")
    sorted_by_value = sorted(aggregated_data.items(), key=lambda x: x[1]['total_running'], reverse=True)[:10]
    for i, (time_step, data) in enumerate(sorted_by_value, 1):
        print(f"  {i}. 时间 {time_step}s: {data['total_running']:,.0f} 辆 (任务数: {data['task_count']})")
else:
    print("未找到时序数据")












