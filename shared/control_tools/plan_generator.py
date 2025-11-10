"""
Morning Peak Control Plan Generator
生成G4202早高峰综合管控方案集合
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid
from dataclasses import dataclass, asdict


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

        return {
            "strategy_id": strat_id,
            "strategy_name": f"{segment_data['segment_name']}可变限速",
            "template_id": f"vss_{severity}",
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
        flow_steps = []
        base_hour = 7
        for step in tec_params["control_steps_template"]:
            flow_steps.append({
                "time_hours": base_hour + step["time_offset_hours"],
                "flow_limit_veh_hr": step["flow_limit_veh_hr"],
                "green_time_ratio": step["green_time_ratio"]
            })

        return {
            "strategy_id": strat_id,
            "strategy_name": f"{location_name}流量控制",
            "template_id": f"tec_{severity}",
            "strategy_type": "TEC",
            "parameters": {
                "control_points": edge_ids,
                "flow_steps": flow_steps,
                "ramp_metering": tec_params["ramp_metering"]
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
        opening_schedule = []
        base_hour = 7
        for step in dhs_params["opening_schedule_template"]:
            opening_schedule.append({
                "begin_hours": base_hour + step["time_offset_hours"],
                "status": step["status"],
                "allowed_vehicle_types": step.get("allowed_types", [])
            })

        return {
            "strategy_id": strat_id,
            "strategy_name": f"{segment_data['segment_name']}应急车道开放",
            "template_id": f"dhs_{severity}",
            "strategy_type": "DHS",
            "parameters": {
                "affected_edges": segment_data["edge_ids"][:6],  # Use subset for DHS
                "hard_shoulder_lane_index": 0,
                "opening_schedule": opening_schedule
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
        """Save plan to file system"""
        plan_dir = self.base_path / plan.plan_id
        plan_dir.mkdir(parents=True, exist_ok=True)

        # Save plan metadata
        plan_file = plan_dir / "plan_metadata.json"
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(plan), f, ensure_ascii=False, indent=2)

        # Create empty control.add.xml placeholder
        xml_file = plan_dir / "control.add.xml"
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
    <!-- Control plan: {plan.plan_id} -->
    <!-- Generated: {datetime.now().isoformat()} -->
    <!-- Strategies: {', '.join([s['strategy_type'] for s in plan.strategies])} -->
</additional>"""

        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)

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