#!/usr/bin/env python
"""
检查Windows系统限制
"""
import subprocess
import sys
import ctypes
from ctypes import wintypes

def check_process_limits():
    """检查Windows进程和句柄限制"""
    print("=" * 60)
    print("Windows系统限制检查")
    print("=" * 60)
    
    # 1. 检查当前进程句柄数
    try:
        current_process = subprocess.run(
            ["powershell", "-Command", "(Get-Process -Id $PID).Handles"],
            capture_output=True,
            text=True
        )
        print(f"\n1. 当前Python进程句柄数: {current_process.stdout.strip()}")
    except:
        pass
    
    # 2. 检查系统句柄限制（Windows默认）
    print("\n2. Windows默认限制:")
    print("   - 进程句柄数: 默认10,000个")
    print("   - 用户进程数: 默认约1000个（可通过策略调整）")
    print("   - 每个进程子进程数: 通常受内存限制")
    
    # 3. 检查ULONG_MAX（32位进程限制）
    print("\n3. 可能的限制来源:")
    print("   - Windows 32位进程: 句柄数限制 ~2048")
    print("   - 子进程创建限制: 可能受系统策略限制")
    print("   - 文件句柄限制: 每个进程默认 ~2048")
    
    # 4. Python subprocess限制
    print("\n4. Python subprocess限制:")
    print("   - subprocess.Popen无内置限制")
    print("   - 限制主要来自操作系统")
    
    print("\n" + "=" * 60)
    print("建议检查:")
    print("1. 查看Windows事件日志，是否有资源不足错误")
    print("2. 检查任务管理器中的句柄数")
    print("3. 考虑使用多进程池而非subprocess直接创建")
    print("=" * 60)

if __name__ == "__main__":
    check_process_limits()

