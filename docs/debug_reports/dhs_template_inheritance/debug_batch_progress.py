"""
批量仿真进度监控诊断脚本

用途：
- 检查API是否返回 live_status 和 live_time_series
- 检查 summary.xml 文件是否存在
- 帮助定位车辆数和动态曲线不显示的问题

使用方法：
python debug_batch_progress.py <case_id> <batch_id>
"""

import sys
import json
import requests
from pathlib import Path

def check_batch_progress(case_id: str, batch_id: str):
    """检查批量仿真进度API响应"""

    api_url = f"http://localhost:8000/api/v1/control/optimization/batch/{batch_id}/progress"

    print(f"=== 诊断批量仿真进度 ===")
    print(f"案例ID: {case_id}")
    print(f"批次ID: {batch_id}")
    print(f"API URL: {api_url}")
    print()

    # 1. 检查API响应
    print("1. 检查API响应...")
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        print(f"   ✓ API响应成功 (HTTP {response.status_code})")
        print(f"   - 批次状态: {data.get('status')}")
        print(f"   - 总任务数: {data.get('total_tasks')}")
        print(f"   - 运行中任务: {data.get('running_tasks')}")
        print(f"   - 已完成任务: {data.get('completed_tasks')}")
        print()

    except Exception as e:
        print(f"   ✗ API请求失败: {e}")
        return

    # 2. 检查 live_time_series
    print("2. 检查动态曲线数据 (live_time_series)...")
    live_time_series = data.get('live_time_series')
    if live_time_series:
        time_points = live_time_series.get('time_points', [])
        total_running = live_time_series.get('total_running', [])
        print(f"   ✓ live_time_series 存在")
        print(f"   - time_points 长度: {len(time_points)}")
        print(f"   - total_running 长度: {len(total_running)}")
        print(f"   - task_count: {live_time_series.get('task_count')}")
        if len(time_points) > 0:
            print(f"   - 时间范围: {time_points[0]} ~ {time_points[-1]} 秒")
            print(f"   - 车辆数范围: {min(total_running)} ~ {max(total_running)} 辆")
        else:
            print("   ⚠ 警告: time_points 为空数组！")
    else:
        print("   ✗ live_time_series 不存在或为空")
    print()

    # 3. 检查每个任务的 live_status
    print("3. 检查任务实时状态 (live_status)...")
    tasks = data.get('tasks', [])
    running_tasks = [t for t in tasks if t.get('status') == 'running']

    if not running_tasks:
        print("   ⚠ 警告: 没有运行中的任务！")
    else:
        for idx, task in enumerate(running_tasks):
            task_id = task.get('task_id')
            simulation_id = task.get('simulation_id')
            live_status = task.get('live_status')

            print(f"   任务 {idx + 1}/{len(running_tasks)}: {task_id}")
            print(f"     - simulation_id: {simulation_id or '未分配'}")

            if live_status:
                print(f"     ✓ live_status 存在")
                print(f"       - running_vehicles: {live_status.get('running_vehicles', 'N/A')}")
                print(f"       - current_step: {live_status.get('current_step', 0)}")
                print(f"       - progress_percent: {live_status.get('progress_percent', 0):.1f}%")
            else:
                print(f"     ✗ live_status 不存在")
            print()

    # 4. 检查 summary.xml 文件是否存在
    print("4. 检查 summary.xml 文件...")
    cases_base = Path("cases")

    for task in running_tasks:
        task_id = task.get('task_id')
        plan_id = task.get('plan_id')
        seed = task.get('seed')

        if plan_id and seed:
            simulation_dir = (
                cases_base / case_id / "simulations" / "plan_opti" /
                batch_id / plan_id / f"sim_{seed}"
            )
            summary_file = simulation_dir / "summary.xml"

            print(f"   任务 {task_id}:")
            print(f"     路径: {summary_file}")
            if summary_file.exists():
                file_size = summary_file.stat().st_size
                print(f"     ✓ 文件存在 (大小: {file_size:,} 字节)")
            else:
                print(f"     ✗ 文件不存在")
            print()

    # 5. 输出完整API响应（用于深度调试）
    print("5. 完整API响应 (JSON):")
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python debug_batch_progress.py <case_id> <batch_id>")
        print("示例: python debug_batch_progress.py case_20251015_baseline batch_20251029_143000")
        sys.exit(1)

    case_id = sys.argv[1]
    batch_id = sys.argv[2]

    check_batch_progress(case_id, batch_id)
