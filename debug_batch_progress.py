#!/usr/bin/env python3
"""
批量仿真进度监控诊断工具

用途：
  - 检查API响应数据结构
  - 验证live_status和live_time_series字段
  - 检查summary.xml文件存在性和大小
  - 输出完整JSON响应供手动分析

使用方法：
  python debug_batch_progress.py <case_id> <batch_id>

示例：
  python debug_batch_progress.py case_001 batch_20251029_103000
"""

import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# 配置
API_BASE_URL = "http://localhost:8000/api/v1"
CASES_BASE_DIR = Path("cases")


def print_section(title):
    """打印分隔标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def check_api_response(case_id: str, batch_id: str):
    """检查API响应数据结构"""
    print_section("1. 获取批量仿真进度API响应")

    url = f"{API_BASE_URL}/control/batch-optimization/batch/{batch_id}/progress"
    print(f"请求URL: {url}\n")

    try:
        response = requests.get(url, timeout=10)
        print(f"HTTP状态码: {response.status_code}\n")

        if response.status_code != 200:
            print(f"❌ API请求失败: {response.text}")
            return None

        data = response.json()

        # 美化输出JSON
        print("API响应数据结构:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # 验证关键字段
        print_section("2. 关键字段验证")

        checks = [
            ("batch_id存在", "batch_id" in data),
            ("status存在", "status" in data),
            ("tasks存在", "tasks" in data),
            ("live_time_series存在", "live_time_series" in data),
        ]

        for check_name, result in checks:
            status = "✓" if result else "✗"
            print(f"{status} {check_name}")

        # 检查任务列表
        if "tasks" in data:
            print(f"\n任务数量: {len(data['tasks'])}")

            running_tasks = [t for t in data['tasks'] if t.get('status') == 'running']
            print(f"运行中的任务: {len(running_tasks)}\n")

            for task in running_tasks:
                print(f"  任务ID: {task.get('task_id')}")
                print(f"  状态: {task.get('status')}")

                if 'live_status' in task:
                    live = task['live_status']
                    print(f"  ✓ 包含live_status")
                    print(f"    - current_step: {live.get('current_step', '未设置')}")
                    print(f"    - running_vehicles: {live.get('running_vehicles', '未设置')}")
                    print(f"    - progress_percent: {live.get('progress_percent', '未设置')}%")
                    if 'estimated_remaining_display' in live:
                        print(f"    - 剩余时间: {live.get('estimated_remaining_display')}")
                else:
                    print(f"  ✗ 缺少live_status字段")
                print()

        # 检查live_time_series
        if "live_time_series" in data:
            lts = data['live_time_series']
            print(f"动态时序数据:")
            print(f"  - 时间点数量: {len(lts.get('time_points', []))}")
            print(f"  - 在网车辆数据点: {len(lts.get('total_running', []))}")
            print(f"  - 任务数量: {lts.get('task_count', 0)}")
            if lts.get('last_update'):
                print(f"  - 最后更新: {lts.get('last_update')}")
        else:
            print("✗ 缺少live_time_series字段")

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        print("   可能原因:")
        print("   1. API服务器未启动")
        print("   2. 地址或端口错误")
        print("   3. batch_id不存在")
        return None


def check_summary_files(case_id: str, batch_id: str, tasks_data=None):
    """检查summary.xml文件存在性"""
    print_section("3. summary.xml文件检查")

    batch_dir = CASES_BASE_DIR / case_id / "simulations" / "plan_opti" / batch_id
    print(f"批次目录: {batch_dir}\n")

    if not batch_dir.exists():
        print(f"✗ 批次目录不存在: {batch_dir}")
        return

    summary_files = []
    for summary_file in batch_dir.rglob("summary.xml"):
        size_kb = summary_file.stat().st_size / 1024
        summary_files.append({
            'path': summary_file,
            'size_kb': size_kb,
            'mtime': datetime.fromtimestamp(summary_file.stat().st_mtime)
        })

    print(f"找到 {len(summary_files)} 个summary.xml文件\n")

    if not summary_files:
        print("⚠ 警告: 未找到summary.xml文件")
        print("  可能原因:")
        print("  1. 仿真刚启动，文件尚未生成（需等待10-30秒）")
        print("  2. 仿真进程已完成，输出文件已被清理")
        print("  3. plan_opti目录结构不正确")
        return

    for i, file_info in enumerate(summary_files[:5], 1):  # 仅显示前5个
        print(f"{i}. {file_info['path'].relative_to(CASES_BASE_DIR)}")
        print(f"   大小: {file_info['size_kb']:.1f} KB")
        print(f"   修改时间: {file_info['mtime']}\n")

    if len(summary_files) > 5:
        print(f"... 以及 {len(summary_files) - 5} 个其他文件\n")


def check_batches_index(case_id: str):
    """检查批次索引文件"""
    print_section("4. 批次索引文件检查")

    index_file = CASES_BASE_DIR / case_id / "simulations" / "plan_opti" / "batches_index.json"
    print(f"索引文件: {index_file}\n")

    if not index_file.exists():
        print("⚠ 警告: batches_index.json不存在（可能是首次创建批次）")
        return

    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)

        print("✓ 索引文件存在")
        print(f"  - 批次数量: {len(index_data.get('batches', []))}")
        print(f"  - 最后更新: {index_data.get('last_updated', '未记录')}")

    except Exception as e:
        print(f"✗ 索引文件读取失败: {e}")


def print_diagnostics_summary():
    """打印诊断汇总和常见问题"""
    print_section("5. 诊断汇总与常见问题")

    print("常见根因（按概率排序）:\n")

    issues = [
        {
            "rank": "1. 高概率",
            "cause": "API服务器未重启",
            "description": "代码更新后未重启API服务器，导致旧代码继续运行",
            "solution": "重启API服务器: .\\start_api.ps1"
        },
        {
            "rank": "2. 中高概率",
            "cause": "simulation_id未分配",
            "description": "任务刚启动，仿真进程尚未启动或未分配simulation_id",
            "solution": "检查API日志中的simulation_id分配过程，等待10-30秒后重试"
        },
        {
            "rank": "3. 中概率",
            "cause": "summary.xml不存在",
            "description": "SUMO仿真刚启动，输出文件尚未生成",
            "solution": "在浏览器控制台查看DEBUG日志，确认文件路径正确"
        },
        {
            "rank": "4. 低概率",
            "cause": "文件路径错误",
            "description": "plan_opti目录结构不正确或批次目录不存在",
            "solution": "检查后端日志中的文件路径定位过程"
        },
        {
            "rank": "5. 很低概率",
            "cause": "解析失败",
            "description": "summary.xml格式异常或文件损坏",
            "solution": "检查summary.xml文件内容是否完整，查看后端日志的解析错误"
        }
    ]

    for issue in issues:
        print(f"【{issue['rank']}】{issue['cause']}")
        print(f"  描述: {issue['description']}")
        print(f"  解决: {issue['solution']}\n")

    print("\n数据流追踪:\n")
    print("✓ 后端生成流程:")
    print("  get_batch_progress() → _get_simulation_live_status() → _extract_summary_last_step()")
    print("                      → _aggregate_live_time_series() → 返回响应")
    print("\n✓ 前端渲染流程:")
    print("  fetch API → updateProgress() → renderTaskList() + renderLiveCurve()")
    print("\n")


def main():
    """主函数"""
    if len(sys.argv) != 3:
        print(f"用法: {sys.argv[0]} <case_id> <batch_id>")
        print(f"示例: {sys.argv[0]} case_001 batch_20251029_103000")
        sys.exit(1)

    case_id = sys.argv[1]
    batch_id = sys.argv[2]

    print(f"\n批量仿真进度监控诊断工具")
    print(f"Case: {case_id} | Batch: {batch_id}")
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 执行诊断
    api_data = check_api_response(case_id, batch_id)
    check_summary_files(case_id, batch_id, api_data)
    check_batches_index(case_id)
    print_diagnostics_summary()

    print("\n" + "="*60)
    print("  诊断完成")
    print("="*60 + "\n")
    print("后续步骤:")
    print("1. 检查浏览器控制台 (F12) 查看DEBUG日志")
    print("2. 检查API服务器日志查看WARNING/ERROR")
    print("3. 如果问题仍未解决，参考BATCH_MONITORING_DEBUG_GUIDE.md")
    print()


if __name__ == "__main__":
    main()
