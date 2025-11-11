"""
Morning Peak Control Plan Generator
生成G4202早高峰综合管控方案集合
"""

import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid
from dataclasses import dataclass, asdict
from shared.control_tools import strategy_file_manager
from shared.control_tools.template_loader import get_template_by_id


@dataclass
class ControlPlan:
    """Control plan data structure"""
    plan_id: str
    plan_name: str
    chinese_name: str
    collection: str
    collection_name: str
    description: str
    strategies: List[Dict]
    metadata: Dict[str, Any]
    is_baseline: bool = False
    status: str = "active"
    created_at: str = ""
    version: int = 1


class MorningPeakPlanGenerator:
    """
    Generator for morning peak control plans
    生成早高峰综合管控方案
    """

    def __init__(self, base_path: str = "control_data/plans"):
        """Initialize plan generator"""
        self.base_path = Path(base_path)
        self.plan_prefix = "plan_morning_peak_g4202"
        self.collection_id = "morning_peak_g4202"
        self.collection_name = "G4202早高峰综合管控方案集"

        # Load templates
        self.segments = self._load_json("g4202_segments.json")
        self.interchanges = self._load_json("g5_interchange_zones.json")
        self.vss_templates = self._load_json("vss_severity_templates.json")
        self.tec_templates = self._load_json("tec_severity_templates.json")
        self.dhs_templates = self._load_json("dhs_severity_templates.json")
        self.temporal_templates = self._load_json("temporal_interval_templates.json")
        self.flow_analysis = self._load_json("morning_peak_flow_analysis.json")

    def _load_json(self, filename: str) -> Dict:
        """Load JSON template file"""
        filepath = self.base_path / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def generate_plan_id(self, strategy: str, location: str, severity: str, version: int = 1) -> str:
        """Generate standardized plan ID"""
        # Convert location to safe string
        location_safe = location.lower().replace("-", "").replace("_", "")
        return f"{self.plan_prefix}_{strategy}_{location_safe}_{severity}_v{version}"

    def generate_chinese_name(self, strategy: str, location: str, severity: str, version: int = 1) -> str:
        """Generate Chinese plan name"""
        strategy_map = {
            "vss": "VSS",
            "tec": "TEC",
            "dhs": "DHS",
            "vss_tec": "VSS+TEC",
            "vss_dhs": "VSS+DHS",
            "tec_dhs": "TEC+DHS",
            "full_composite": "全策略"
        }

        location_map = {
            "k0k20": "东段",
            "k20k40": "南段",
            "k40k60": "西段",
            "k60k85": "北段",
            "g5_south": "G5南立交",
            "g5_north": "G5北立交",
            "g5_west": "G5西连接",
            "all": "全线"
        }

        severity_map = {
            "mild": "轻度",
            "moderate": "中度",
            "severe": "严重"
        }

        strategy_cn = strategy_map.get(strategy, strategy.upper())
        location_cn = location_map.get(location, location)
        severity_cn = severity_map.get(severity, severity)

        return f"G4202早高峰{strategy_cn}{location_cn}{severity_cn}综合管控方案V{version}"

    def create_vss_strategy(self, segment: str, severity: str, time_pattern: str) -> Dict:
        """Create VSS strategy based on templates"""
        segment_data = next((s for s in self.segments["segments"] if segment in s["segment_id"]), None)
        if not segment_data:
            return {}

        vss_params = self.vss_templates["severities"][severity]["parameters"]
        temporal = self.temporal_templates["interval_patterns"][time_pattern]

        # Generate unique strategy ID
        strat_id = f"strat_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

        # Adjust speed steps based on temporal pattern
        speed_steps = []
        base_hour = 7  # Morning peak starts at 7:00
        for step in vss_params["speed_steps_template"]:
            speed_steps.append({
                "time_hours": base_hour + step["time_offset_hours"],
                "speed_kmh": step["speed_kmh"]
            })

        # 根据严重程度选择模板
        template_map = {
            "mild": "vss_moderate",
            "moderate": "vss_moderate",
            "severe": "vss_strict"
        }
        template_id = template_map.get(severity, "vss_moderate")
        
        return {
            "strategy_id": strat_id,
            "strategy_name": f"{segment_data['segment_name']}可变限速",
            "template_id": template_id,
            "strategy_type": "VSS",
            "parameters": {
                "affected_edges": segment_data["edge_ids"][:8],  # Use subset of edges
                "speed_steps": speed_steps
            }
        }

    def create_tec_strategy(self, location: str, severity: str, time_pattern: str) -> Dict:
        """Create TEC strategy based on templates"""
        tec_params = self.tec_templates["severities"][severity]["parameters"]
        temporal = self.temporal_templates["interval_patterns"][time_pattern]

        # Generate unique strategy ID
        strat_id = f"strat_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

        # Determine edge IDs based on location
        if "g5" in location.lower():
            interchange = next((i for i in self.interchanges["interchanges"]
                              if location in i["zone_id"]), None)
            edge_ids = interchange["control_zones"]["interchange"]["ramp_edges"] if interchange else []
            location_name = interchange["zone_name"] if interchange else location
        else:
            # Use segment entry points
            edge_ids = ["-1000", "-2000"]  # Placeholder for entry points
            location_name = f"K{location.split('k')[1] if 'k' in location else '0'}入口"

        # Adjust flow control based on temporal pattern
        # TEC 使用 flow_intervals 格式
        flow_intervals = []
        base_hour = 7
        for step in tec_params.get("control_steps_template", []):
            flow_intervals.append({
                "begin_hours": base_hour + step.get("time_offset_hours", 0),
                "end_hours": base_hour + step.get("time_offset_hours", 0) + step.get("duration_hours", 2),
                "vehsPerHour": step.get("flow_limit_veh_hr", 300),
                "target_speed": step.get("target_speed", 15)
            })

        # 根据严重程度选择模板
        template_map = {
            "mild": "tec_flow_metering",
            "moderate": "tec_flow_metering",
            "severe": "tec_flow_metering"
        }
        template_id = template_map.get(severity, "tec_flow_metering")
        
        return {
            "strategy_id": strat_id,
            "strategy_name": f"{location_name}流量控制",
            "template_id": template_id,
            "strategy_type": "TEC",
            "parameters": {
                "entrance_edges": edge_ids if edge_ids else ["-1000"],  # TEC 使用 entrance_edges
                "position": 0,
                "flow_intervals": flow_intervals  # TEC 使用 flow_intervals
            }
        }

    def create_dhs_strategy(self, segment: str, severity: str, time_pattern: str) -> Dict:
        """Create DHS strategy based on templates"""
        segment_data = next((s for s in self.segments["segments"] if segment in s["segment_id"]), None)
        if not segment_data:
            return {}

        dhs_params = self.dhs_templates["severities"][severity]["parameters"]
        temporal = self.temporal_templates["interval_patterns"][time_pattern]

        # Generate unique strategy ID
        strat_id = f"strat_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

        # Adjust opening schedule based on temporal pattern
        # DHS 使用 intervals 格式
        intervals = []
        base_hour = 7
        for step in dhs_params.get("opening_schedule_template", []):
            intervals.append({
                "begin_hours": base_hour + step.get("time_offset_hours", 0),
                "end_hours": base_hour + step.get("time_offset_hours", 0) + step.get("duration_hours", 2),
                "status": step.get("status", "OPEN"),
                "allowed_vehicle_types": step.get("allowed_types", ["passenger", "truck"])
            })

        # 根据严重程度选择模板
        template_map = {
            "mild": "dhs_peak_hours",
            "moderate": "dhs_peak_hours",
            "severe": "dhs_peak_multi_interval"
        }
        template_id = template_map.get(severity, "dhs_peak_hours")
        
        return {
            "strategy_id": strat_id,
            "strategy_name": f"{segment_data['segment_name']}应急车道开放",
            "template_id": template_id,
            "strategy_type": "DHS",
            "parameters": {
                "affected_edges": segment_data["edge_ids"][:6],  # Use subset for DHS
                "hard_shoulder_lane_index": 0,
                "intervals": intervals  # DHS 使用 intervals
            }
        }

    def generate_single_strategy_plan(self, strategy_type: str, location: str,
                                     severity: str, time_pattern: str = "core_morning") -> ControlPlan:
        """Generate a plan with single strategy type"""
        plan_id = self.generate_plan_id(strategy_type, location, severity)
        chinese_name = self.generate_chinese_name(strategy_type, location, severity)

        # Create strategy based on type
        strategies = []
        if strategy_type == "vss":
            strategy = self.create_vss_strategy(location, severity, time_pattern)
        elif strategy_type == "tec":
            strategy = self.create_tec_strategy(location, severity, time_pattern)
        elif strategy_type == "dhs":
            strategy = self.create_dhs_strategy(location, severity, time_pattern)
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        if strategy:
            strategies.append(strategy)

        # Create plan metadata
        metadata = {
            "highway": ["G4202"],
            "segments": [location],
            "time_pattern": time_pattern,
            "time_range": self.temporal_templates["interval_patterns"][time_pattern]["time_range"],
            "severity": severity,
            "strategies": [strategy_type],
            "expected_volume": "high" if severity == "severe" else "moderate",
            "optimization_goal": "minimize_delay"
        }

        return ControlPlan(
            plan_id=plan_id,
            plan_name=chinese_name,
            chinese_name=chinese_name,
            collection=self.collection_id,
            collection_name=self.collection_name,
            description=f"针对{location}区段{severity}拥堵的{strategy_type.upper()}管控方案",
            strategies=strategies,
            metadata=metadata,
            created_at=datetime.now().isoformat()
        )

    def generate_composite_plan(self, strategy_types: List[str], location: str,
                               severity: str, time_pattern: str = "extended_morning") -> ControlPlan:
        """Generate a plan with multiple strategy types"""
        strategy_str = "_".join(strategy_types)
        plan_id = self.generate_plan_id(strategy_str, location, severity)
        chinese_name = self.generate_chinese_name(strategy_str, location, severity)

        strategies = []
        for strategy_type in strategy_types:
            if strategy_type == "vss":
                strategy = self.create_vss_strategy(location, severity, time_pattern)
            elif strategy_type == "tec":
                # Place TEC at different location for composite plans
                tec_location = "g5_south" if "g5" not in location else location
                strategy = self.create_tec_strategy(tec_location, severity, time_pattern)
            elif strategy_type == "dhs":
                strategy = self.create_dhs_strategy(location, severity, time_pattern)
            else:
                continue

            if strategy:
                strategies.append(strategy)

        # Create plan metadata
        metadata = {
            "highway": ["G4202", "G5"] if "g5" in location.lower() else ["G4202"],
            "segments": [location],
            "time_pattern": time_pattern,
            "time_range": self.temporal_templates["interval_patterns"][time_pattern]["time_range"],
            "severity": severity,
            "strategies": strategy_types,
            "expected_volume": "very_high" if severity == "severe" else "high",
            "optimization_goal": "balanced_optimization"
        }

        return ControlPlan(
            plan_id=plan_id,
            plan_name=chinese_name,
            chinese_name=chinese_name,
            collection=self.collection_id,
            collection_name=self.collection_name,
            description=f"针对{location}区段{severity}拥堵的复合管控方案",
            strategies=strategies,
            metadata=metadata,
            created_at=datetime.now().isoformat()
        )

    def save_plan(self, plan: ControlPlan) -> str:
        """
        Save plan to file system
        
        1. 为每个策略创建并保存策略实例
        2. 在方案元数据中设置 strategy_ids
        3. 更新 plans_index.json 时设置 strategy_count
        """
        plan_dir = self.base_path / plan.plan_id
        plan_dir.mkdir(parents=True, exist_ok=True)

        strategies_dir = Path("control_data/strategies")
        strategies_dir.mkdir(parents=True, exist_ok=True)
        templates_dir = Path("templates/control_strategies")

        strategy_ids = []
        current_time = datetime.now(timezone.utc).isoformat()
        created_by = socket.gethostname() if socket.gethostname() else "system"

        # 为每个策略创建并保存策略实例
        for strategy in plan.strategies:
            if not strategy or not strategy.get("strategy_id"):
                continue

            # 获取模板信息以获取 template_name
            template_id = strategy.get("template_id")
            template_name = strategy.get("template_name", "")
            
            if not template_name and template_id:
                # 尝试从模板文件加载 template_name
                template = get_template_by_id(template_id, templates_dir)
                if template:
                    template_name = template.template_name if hasattr(template, 'template_name') else template.get("template_name", template_id)
                else:
                    # 如果模板不存在，使用默认名称
                    template_name = template_id.replace("_", " ").title()

            # 构建完整的策略实例数据
            strategy_instance = {
                "strategy_id": strategy["strategy_id"],
                "strategy_name": strategy.get("strategy_name", ""),
                "template_id": template_id,
                "template_name": template_name,
                "strategy_type": strategy.get("strategy_type", ""),
                "parameters": strategy.get("parameters", {}),
                "metadata": {
                    "created_at": current_time,
                    "updated_at": current_time,
                    "created_by": created_by,
                    "version": 1
                }
            }

            # 保存策略实例
            success = strategy_file_manager.save_strategy(strategy_instance, str(strategies_dir))
            if success:
                strategy_ids.append(strategy["strategy_id"])
            else:
                print(f"警告: 保存策略实例失败: {strategy['strategy_id']}")

        # 准备方案元数据
        plan_metadata = {
            "plan_id": plan.plan_id,
            "plan_name": plan.chinese_name,
            "description": plan.description,
            "strategy_ids": strategy_ids,
            "tags": plan.metadata.get("tags", []),
            "target_scenario": plan.metadata.get("time_range", {}).get("display", ""),
            "additional_file_path": f"control_data/plans/{plan.plan_id}/control.add.xml",
            "created_at": plan.created_at,
            "updated_at": plan.created_at,
        }

        # 添加集合相关字段
        if plan.collection:
            plan_metadata["collection"] = plan.collection
        if plan.collection_name:
            plan_metadata["collection_name"] = plan.collection_name

        # 添加其他元数据字段
        if plan.metadata:
            plan_metadata.update({
                "highway": plan.metadata.get("highway", []),
                "segments": plan.metadata.get("segments", []),
                "time_pattern": plan.metadata.get("time_pattern"),
                "time_range": plan.metadata.get("time_range", {}),
                "severity": plan.metadata.get("severity"),
                "strategies": plan.metadata.get("strategies", []),
                "location": plan.metadata.get("location"),
            })

        # 保存方案元数据
        plan_file = plan_dir / "plan_metadata.json"
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan_metadata, f, ensure_ascii=False, indent=2)

        # 保存策略引用
        refs_file = plan_dir / "strategy_refs.json"
        with open(refs_file, 'w', encoding='utf-8') as f:
            json.dump(strategy_ids, f, ensure_ascii=False, indent=2)

        # 创建 control.add.xml 占位符
        xml_file = plan_dir / "control.add.xml"
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
    <!-- Control plan: {plan.plan_id} -->
    <!-- Generated: {datetime.now().isoformat()} -->
    <!-- Strategies: {', '.join([s.get('strategy_type', '') for s in plan.strategies])} -->
</additional>"""

        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)

        # 更新 plans_index.json
        # 直接读取和写入索引文件
        index_file = Path("control_data/plans/plans_index.json")
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {"plans": []}
        
        # 检查是否已存在
        existing_index = next((i for i in index["plans"] if i["plan_id"] == plan.plan_id), None)
        if existing_index:
            # 更新现有条目
            existing_index.update({
                "plan_name": plan.chinese_name,
                "is_baseline": False,
                "strategy_count": len(strategy_ids),
                "tags": plan_metadata.get("tags", []),
                "created_at": plan.created_at,
            })
            # 添加集合相关字段
            if plan.collection:
                existing_index["collection"] = plan.collection
            if plan.collection_name:
                existing_index["collection_name"] = plan.collection_name
            # 添加其他字段
            if plan.metadata:
                existing_index["description"] = plan.description
                existing_index["strategies"] = plan.metadata.get("strategies", [])
                existing_index["severity"] = plan.metadata.get("severity")
                existing_index["location"] = plan.metadata.get("location")
        else:
            # 添加新条目
            index_entry = {
                "plan_id": plan.plan_id,
                "plan_name": plan.chinese_name,
                "is_baseline": False,
                "strategy_count": len(strategy_ids),
                "tags": plan_metadata.get("tags", []),
                "created_at": plan.created_at,
            }
            # 添加集合相关字段
            if plan.collection:
                index_entry["collection"] = plan.collection
            if plan.collection_name:
                index_entry["collection_name"] = plan.collection_name
            # 添加其他字段
            index_entry["description"] = plan.description
            if plan.metadata:
                index_entry["strategies"] = plan.metadata.get("strategies", [])
                index_entry["severity"] = plan.metadata.get("severity")
                index_entry["location"] = plan.metadata.get("location")
            
            index["plans"].append(index_entry)

        # 保存索引文件
        index_file.parent.mkdir(parents=True, exist_ok=True)
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        return str(plan_dir)

    def generate_batch_1_plans(self) -> List[ControlPlan]:
        """Generate first batch: 6 single-strategy plans"""
        plans = []

        # 2 VSS-only plans
        plans.append(self.generate_single_strategy_plan("vss", "g4202_k0k20", "moderate", "early_morning"))
        plans.append(self.generate_single_strategy_plan("vss", "g4202_k40k60", "severe", "core_morning"))

        # 2 TEC-only plans
        plans.append(self.generate_single_strategy_plan("tec", "k0", "mild", "early_morning"))
        plans.append(self.generate_single_strategy_plan("tec", "k40", "moderate", "core_morning"))

        # 2 DHS-only plans
        plans.append(self.generate_single_strategy_plan("dhs", "g4202_k40k60", "moderate", "extended_morning"))
        plans.append(self.generate_single_strategy_plan("dhs", "g4202_k0k20", "severe", "core_morning"))

        return plans

    def generate_batch_2_plans(self) -> List[ControlPlan]:
        """Generate second batch: 7 dual-strategy plans"""
        plans = []

        # 3 VSS+TEC plans
        plans.append(self.generate_composite_plan(["vss", "tec"], "g4202_k20k40", "mild", "early_morning"))
        plans.append(self.generate_composite_plan(["vss", "tec"], "g4202_k40k60", "moderate", "core_morning"))
        plans.append(self.generate_composite_plan(["vss", "tec"], "g4202_k60k85", "severe", "extended_morning"))

        # 2 VSS+DHS plans
        plans.append(self.generate_composite_plan(["vss", "dhs"], "g4202_k0k20", "moderate", "core_morning"))
        plans.append(self.generate_composite_plan(["vss", "dhs"], "g4202_k40k60", "severe", "extended_morning"))

        # 2 TEC+DHS plans
        plans.append(self.generate_composite_plan(["tec", "dhs"], "g4202_k20k40", "moderate", "phased_morning"))
        plans.append(self.generate_composite_plan(["tec", "dhs"], "g4202_k60k85", "severe", "core_morning"))

        return plans

    def generate_batch_3_plans(self) -> List[ControlPlan]:
        """Generate third batch: 7 triple-strategy and phased plans"""
        plans = []

        # 3 VSS+TEC+DHS full composite plans
        plans.append(self.generate_composite_plan(["vss", "tec", "dhs"], "g4202_k0k20", "severe", "extended_morning"))
        plans.append(self.generate_composite_plan(["vss", "tec", "dhs"], "g4202_k40k60", "severe", "adaptive_morning"))
        plans.append(self.generate_composite_plan(["vss", "tec", "dhs"], "g4202_k60k85", "moderate", "phased_morning"))

        # 4 phased activation pattern plans
        plans.append(self.generate_single_strategy_plan("vss", "g4202_k20k40", "mild", "phased_morning"))
        plans.append(self.generate_composite_plan(["vss", "tec"], "g4202_k0k20", "moderate", "adaptive_morning"))
        plans.append(self.generate_composite_plan(["tec", "dhs"], "g4202_k40k60", "mild", "phased_morning"))
        plans.append(self.generate_single_strategy_plan("dhs", "g4202_k60k85", "moderate", "adaptive_morning"))

        return plans


def main():
    """Main function to generate all plans"""
    generator = MorningPeakPlanGenerator()

    print("开始生成G4202早高峰综合管控方案集...")
    print(f"方案集名称: {generator.collection_name}")
    print(f"方案前缀: {generator.plan_prefix}_*")
    print("-" * 60)

    all_plans = []

    # Generate Batch 1
    print("\n生成第一批次 (6个单策略方案)...")
    batch1 = generator.generate_batch_1_plans()
    for plan in batch1:
        path = generator.save_plan(plan)
        all_plans.append(plan)
        print(f"  ✓ {plan.plan_id} - {plan.chinese_name}")

    # Generate Batch 2
    print("\n生成第二批次 (7个双策略组合方案)...")
    batch2 = generator.generate_batch_2_plans()
    for plan in batch2:
        path = generator.save_plan(plan)
        all_plans.append(plan)
        print(f"  ✓ {plan.plan_id} - {plan.chinese_name}")

    # Generate Batch 3
    print("\n生成第三批次 (7个三策略及分阶段方案)...")
    batch3 = generator.generate_batch_3_plans()
    for plan in batch3:
        path = generator.save_plan(plan)
        all_plans.append(plan)
        print(f"  ✓ {plan.plan_id} - {plan.chinese_name}")

    print(f"\n✅ 成功生成 {len(all_plans)} 个早高峰管控方案")
    print(f"方案保存位置: control_data/plans/plan_morning_peak_g4202_*/")

    return all_plans


if __name__ == "__main__":
    plans = main()