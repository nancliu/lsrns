#!/usr/bin/env python3
"""
API测试脚本
"""

import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

def test_health_check():
    """测试健康检查"""
    print("测试健康检查...")
    response = requests.get("http://localhost:8000/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()

def test_root():
    """测试根路径"""
    print("测试根路径...")
    response = requests.get("http://localhost:8000/")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()

def test_list_cases():
    """测试获取案例列表"""
    print("测试获取案例列表...")
    response = requests.get(f"{BASE_URL}/list_cases/")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()

def test_templates():
    """测试模板API"""
    print("测试TAZ模板...")
    response = requests.get(f"{BASE_URL}/templates/taz")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()

def test_create_case():
    """测试创建案例"""
    print("测试创建案例...")
    case_data = {
        "time_range": {
            "start": "2025/07/21 08:00:00",
            "end": "2025/07/21 09:00:00"
        },
        "config": {},
        "case_name": "测试案例",
        "description": "这是一个测试案例"
    }
    
    response = requests.post(
        f"{BASE_URL}/create_case/",
        json=case_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()

def main():
    """主函数"""
    print("开始API测试...")
    print("=" * 50)
    
    try:
        test_health_check()
        test_root()
        test_list_cases()
        test_templates()
        test_create_case()
        
        print("所有测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到API服务，请确保服务正在运行")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main() 