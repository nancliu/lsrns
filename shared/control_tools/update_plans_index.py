"""
Update plans_index.json with new morning peak plans
"""

import json
from pathlib import Path
from datetime import datetime


def update_plans_index():
    """Update plans_index.json with new morning peak plans"""

    plans_dir = Path("control_data/plans")
    index_file = plans_dir / "plans_index.json"

    # Load existing index
    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)

    # Morning peak plan entries to add
    new_plans = [
        # Batch 1: Single strategy plans
        {
            "plan_id": "plan_morning_peak_g4202_vss_g4202k0k20_moderate_v1",
            "plan_name": "G4202早高峰VSS东段中度综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "东段VSS可变限速中度控制方案",
            "strategies": ["VSS"],
            "severity": "moderate",
            "location": "K0-K20"
        },
        {
            "plan_id": "plan_morning_peak_g4202_vss_g4202k40k60_severe_v1",
            "plan_name": "G4202早高峰VSS西段严重综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "西段VSS可变限速严重控制方案",
            "strategies": ["VSS"],
            "severity": "severe",
            "location": "K40-K60"
        },
        {
            "plan_id": "plan_morning_peak_g4202_tec_k0_mild_v1",
            "plan_name": "G4202早高峰TEC东入口轻度综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "K0入口TEC流量轻度控制方案",
            "strategies": ["TEC"],
            "severity": "mild",
            "location": "K0"
        },
        {
            "plan_id": "plan_morning_peak_g4202_tec_k40_moderate_v1",
            "plan_name": "G4202早高峰TEC西入口中度综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "K40入口TEC流量中度控制方案",
            "strategies": ["TEC"],
            "severity": "moderate",
            "location": "K40"
        },
        {
            "plan_id": "plan_morning_peak_g4202_dhs_g4202k40k60_moderate_v1",
            "plan_name": "G4202早高峰DHS西段中度综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "西段DHS应急车道中度开放方案",
            "strategies": ["DHS"],
            "severity": "moderate",
            "location": "K40-K60"
        },
        {
            "plan_id": "plan_morning_peak_g4202_dhs_g4202k0k20_severe_v1",
            "plan_name": "G4202早高峰DHS东段严重综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "东段DHS应急车道严重开放方案",
            "strategies": ["DHS"],
            "severity": "severe",
            "location": "K0-K20"
        },

        # Batch 2: Dual strategy plans
        {
            "plan_id": "plan_morning_peak_g4202_vss_tec_g4202k20k40_mild_v1",
            "plan_name": "G4202早高峰VSS+TEC南段轻度综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "南段VSS+TEC复合轻度控制方案",
            "strategies": ["VSS", "TEC"],
            "severity": "mild",
            "location": "K20-K40"
        },
        {
            "plan_id": "plan_morning_peak_g4202_vss_tec_g4202k40k60_moderate_v1",
            "plan_name": "G4202早高峰VSS+TEC西段中度综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "西段VSS+TEC复合中度控制方案",
            "strategies": ["VSS", "TEC"],
            "severity": "moderate",
            "location": "K40-K60"
        },
        {
            "plan_id": "plan_morning_peak_g4202_vss_tec_g4202k60k85_severe_v1",
            "plan_name": "G4202早高峰VSS+TEC北段严重综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "北段VSS+TEC复合严重控制方案",
            "strategies": ["VSS", "TEC"],
            "severity": "severe",
            "location": "K60-K85"
        },
        {
            "plan_id": "plan_morning_peak_g4202_vss_dhs_g4202k0k20_moderate_v1",
            "plan_name": "G4202早高峰VSS+DHS东段中度综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "东段VSS+DHS复合中度控制方案",
            "strategies": ["VSS", "DHS"],
            "severity": "moderate",
            "location": "K0-K20"
        },
        {
            "plan_id": "plan_morning_peak_g4202_vss_dhs_g4202k40k60_severe_v1",
            "plan_name": "G4202早高峰VSS+DHS西段严重综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "西段VSS+DHS复合严重控制方案",
            "strategies": ["VSS", "DHS"],
            "severity": "severe",
            "location": "K40-K60"
        },
        {
            "plan_id": "plan_morning_peak_g4202_tec_dhs_g4202k20k40_moderate_v1",
            "plan_name": "G4202早高峰TEC+DHS南段中度综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "南段TEC+DHS复合中度控制方案",
            "strategies": ["TEC", "DHS"],
            "severity": "moderate",
            "location": "K20-K40"
        },
        {
            "plan_id": "plan_morning_peak_g4202_tec_dhs_g4202k60k85_severe_v1",
            "plan_name": "G4202早高峰TEC+DHS北段严重综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "北段TEC+DHS复合严重控制方案",
            "strategies": ["TEC", "DHS"],
            "severity": "severe",
            "location": "K60-K85"
        },

        # Batch 3: Triple strategy and phased plans
        {
            "plan_id": "plan_morning_peak_g4202_vss_tec_dhs_g4202k0k20_severe_v1",
            "plan_name": "G4202早高峰全策略东段严重综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "东段VSS+TEC+DHS全策略严重控制方案",
            "strategies": ["VSS", "TEC", "DHS"],
            "severity": "severe",
            "location": "K0-K20"
        },
        {
            "plan_id": "plan_morning_peak_g4202_vss_tec_dhs_g4202k40k60_severe_v1",
            "plan_name": "G4202早高峰全策略西段严重综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "西段VSS+TEC+DHS全策略严重控制方案",
            "strategies": ["VSS", "TEC", "DHS"],
            "severity": "severe",
            "location": "K40-K60"
        },
        {
            "plan_id": "plan_morning_peak_g4202_vss_tec_dhs_g4202k60k85_moderate_v1",
            "plan_name": "G4202早高峰全策略北段中度综合管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "北段VSS+TEC+DHS全策略中度控制方案",
            "strategies": ["VSS", "TEC", "DHS"],
            "severity": "moderate",
            "location": "K60-K85"
        },
        {
            "plan_id": "plan_morning_peak_g4202_vss_g4202k20k40_mild_v1",
            "plan_name": "G4202早高峰VSS南段轻度分阶段管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "南段VSS分阶段轻度控制方案",
            "strategies": ["VSS"],
            "severity": "mild",
            "location": "K20-K40",
            "time_pattern": "phased"
        },
        {
            "plan_id": "plan_morning_peak_g4202_vss_tec_g4202k0k20_moderate_v1",
            "plan_name": "G4202早高峰VSS+TEC东段自适应中度管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "东段VSS+TEC自适应中度控制方案",
            "strategies": ["VSS", "TEC"],
            "severity": "moderate",
            "location": "K0-K20",
            "time_pattern": "adaptive"
        },
        {
            "plan_id": "plan_morning_peak_g4202_tec_dhs_g4202k40k60_mild_v1",
            "plan_name": "G4202早高峰TEC+DHS西段分阶段轻度管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "西段TEC+DHS分阶段轻度控制方案",
            "strategies": ["TEC", "DHS"],
            "severity": "mild",
            "location": "K40-K60",
            "time_pattern": "phased"
        },
        {
            "plan_id": "plan_morning_peak_g4202_dhs_g4202k60k85_moderate_v1",
            "plan_name": "G4202早高峰DHS北段自适应中度管控方案V1",
            "collection": "morning_peak_g4202",
            "collection_name": "G4202早高峰综合管控方案集",
            "is_baseline": False,
            "created_at": datetime.now().isoformat(),
            "description": "北段DHS自适应中度控制方案",
            "strategies": ["DHS"],
            "severity": "moderate",
            "location": "K60-K85",
            "time_pattern": "adaptive"
        }
    ]

    # Add new plans to index
    for plan in new_plans:
        # Check if plan already exists
        existing = next((p for p in index_data["plans"] if p["plan_id"] == plan["plan_id"]), None)
        if not existing:
            index_data["plans"].append(plan)
            print(f"Added: {plan['plan_id']}")
        else:
            print(f"Already exists: {plan['plan_id']}")

    # Update or create metadata
    if "metadata" not in index_data:
        index_data["metadata"] = {}

    index_data["metadata"]["total_plans"] = len(index_data["plans"])
    index_data["metadata"]["last_updated"] = datetime.now().isoformat()

    if "collections" not in index_data["metadata"]:
        index_data["metadata"]["collections"] = {}

    index_data["metadata"]["collections"]["morning_peak_g4202"] = {
        "name": "G4202早高峰综合管控方案集",
        "count": len([p for p in index_data["plans"] if p.get("collection") == "morning_peak_g4202"]),
        "prefix": "plan_morning_peak_g4202_"
    }

    # Save updated index
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Updated plans_index.json")
    print(f"Total plans: {index_data['metadata']['total_plans']}")
    print(f"Morning peak collection: {index_data['metadata']['collections']['morning_peak_g4202']['count']} plans")


if __name__ == "__main__":
    update_plans_index()