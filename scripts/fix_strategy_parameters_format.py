"""
修复策略实例的参数格式

将旧格式的参数转换为新格式：
- TEC: control_points -> entrance_edges, flow_steps -> flow_intervals
- DHS: opening_schedule -> intervals
"""

import json
from pathlib import Path
from typing import Dict, Any

STRATEGIES_DIR = Path("control_data/strategies")


def fix_tec_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """修复TEC策略的参数格式"""
    fixed_params = parameters.copy()
    
    # 转换 control_points -> entrance_edges
    if "control_points" in fixed_params and "entrance_edges" not in fixed_params:
        fixed_params["entrance_edges"] = fixed_params.pop("control_points", [])
    
    # 转换 flow_steps -> flow_intervals
    if "flow_steps" in fixed_params and "flow_intervals" not in fixed_params:
        flow_steps = fixed_params.pop("flow_steps", [])
        flow_intervals = []
        
        for i, step in enumerate(flow_steps):
            time_hours = step.get("time_hours", 0)
            # 计算结束时间（下一个步骤的开始时间，或当前时间+2小时）
            if i + 1 < len(flow_steps):
                end_hours = flow_steps[i + 1].get("time_hours", time_hours + 2)
            else:
                end_hours = time_hours + 2
            
            flow_intervals.append({
                "begin_hours": time_hours,
                "end_hours": end_hours,
                "vehsPerHour": step.get("flow_limit_veh_hr", 300),
                "target_speed": step.get("target_speed", 15)
            })
        
        fixed_params["flow_intervals"] = flow_intervals
    
    # 添加 position 字段（如果不存在）
    if "position" not in fixed_params:
        fixed_params["position"] = 0
    
    return fixed_params


def fix_dhs_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """修复DHS策略的参数格式"""
    fixed_params = parameters.copy()
    
    # 转换 opening_schedule -> intervals
    if "opening_schedule" in fixed_params and "intervals" not in fixed_params:
        opening_schedule = fixed_params.pop("opening_schedule", [])
        intervals = []
        
        for i, step in enumerate(opening_schedule):
            begin_hours = step.get("begin_hours", 0)
            # 计算结束时间（下一个步骤的开始时间，或24小时）
            if i + 1 < len(opening_schedule):
                end_hours = opening_schedule[i + 1].get("begin_hours", 24)
            else:
                end_hours = 24
            
            # 转换状态
            status = step.get("status", "CLOSED")
            if status == "EMERGENCY_OPEN" or status == "FULLY_OPEN":
                status = "OPEN"
            elif status == "CONTROLLED_CLOSING":
                status = "CLOSED"
            
            intervals.append({
                "begin_hours": begin_hours,
                "end_hours": end_hours,
                "status": status,
                "allowed_vehicle_types": step.get("allowed_vehicle_types", [])
            })
        
        fixed_params["intervals"] = intervals
    
    return fixed_params


def fix_strategy_file(strategy_file: Path) -> bool:
    """修复单个策略文件"""
    try:
        # 读取策略文件
        with open(strategy_file, 'r', encoding='utf-8') as f:
            strategy = json.load(f)
        
        strategy_type = strategy.get("strategy_type", "")
        parameters = strategy.get("parameters", {})
        
        # 根据策略类型修复参数
        if strategy_type == "TEC":
            fixed_params = fix_tec_parameters(parameters)
        elif strategy_type == "DHS":
            fixed_params = fix_dhs_parameters(parameters)
        else:
            # VSS不需要修复
            return True
        
        # 更新参数
        strategy["parameters"] = fixed_params
        
        # 保存修复后的文件
        with open(strategy_file, 'w', encoding='utf-8') as f:
            json.dump(strategy, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ 修复策略: {strategy_file.name}")
        return True
        
    except Exception as e:
        print(f"  ❌ 修复策略失败 {strategy_file.name}: {e}")
        return False


def main():
    """主函数"""
    print("开始修复策略实例的参数格式...")
    print("=" * 60)
    
    # 查找所有策略文件
    strategy_files = list(STRATEGIES_DIR.glob("strat_*.json"))
    
    fixed_count = 0
    for strategy_file in sorted(strategy_files):
        if fix_strategy_file(strategy_file):
            fixed_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ 完成！共修复 {fixed_count} 个策略文件")


if __name__ == "__main__":
    main()

