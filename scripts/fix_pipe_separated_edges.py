#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix Pipe-Separated Edge IDs in VSS Scenarios

This script fixes the 7 VSS scenarios that have pipe-separated edge IDs (e.g., "-8982|-2000000377")
by using only the first valid edge from the pair.

Background:
- Some event data contains edge IDs with pipe separators representing OR conditions
- The second edge is often a special/temporary edge not in the network file
- The first edge exists in the network and can be used for VSS control

Author: Claude
Date: 2025-11-14
"""

import json
import logging
from pathlib import Path
from typing import List, Tuple
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_scenarios_with_pipe_edges(base_dir: Path) -> List[Path]:
    """Find all scenarios with pipe-separated edge IDs."""
    scenarios = []

    scenarios_dir = base_dir / "output" / "scenarios"
    if not scenarios_dir.exists():
        logger.warning(f"Scenarios directory not found: {scenarios_dir}")
        return scenarios

    for config_path in scenarios_dir.rglob("control_strategy_config.json"):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Check for pipe-separated edges
            parameters = config.get('parameters', {})
            affected_edges = parameters.get('affected_edges', [])
            entrance_edges = parameters.get('entrance_edges', [])

            has_pipe = any('|' in str(edge) for edge in affected_edges + entrance_edges)

            if has_pipe:
                scenarios.append(config_path.parent)

        except Exception as e:
            logger.warning(f"Failed to read {config_path}: {e}")

    return sorted(scenarios)


def fix_edge_id(edge_id: str) -> str:
    """
    Fix a pipe-separated edge ID by taking the first part.

    Args:
        edge_id: Edge ID that may contain pipe separator

    Returns:
        First valid edge ID (before pipe if present)
    """
    if '|' in edge_id:
        return edge_id.split('|')[0]
    return edge_id


def fix_scenario(scenario_dir: Path, dry_run: bool = False) -> Tuple[bool, str]:
    """
    Fix pipe-separated edge IDs in a scenario's config file.

    Args:
        scenario_dir: Path to scenario directory
        dry_run: If True, don't save changes

    Returns:
        (success: bool, message: str)
    """
    try:
        config_path = scenario_dir / "control_strategy_config.json"

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        parameters = config.get('parameters', {})
        modified = False
        changes = []

        # Fix affected_edges
        if 'affected_edges' in parameters:
            original_edges = parameters['affected_edges']
            fixed_edges = [fix_edge_id(edge) for edge in original_edges]

            if original_edges != fixed_edges:
                parameters['affected_edges'] = fixed_edges
                modified = True
                for orig, fixed in zip(original_edges, fixed_edges):
                    if orig != fixed:
                        changes.append(f"affected_edges: {orig} → {fixed}")

        # Fix entrance_edges
        if 'entrance_edges' in parameters:
            original_edges = parameters['entrance_edges']
            fixed_edges = [fix_edge_id(edge) for edge in original_edges]

            if original_edges != fixed_edges:
                parameters['entrance_edges'] = fixed_edges
                modified = True
                for orig, fixed in zip(original_edges, fixed_edges):
                    if orig != fixed:
                        changes.append(f"entrance_edges: {orig} → {fixed}")

        # Fix affected_lanes (if they reference pipe-separated edges)
        if 'affected_lanes' in parameters:
            original_lanes = parameters['affected_lanes']
            fixed_lanes = [fix_edge_id(lane) for lane in original_lanes]

            if original_lanes != fixed_lanes:
                parameters['affected_lanes'] = fixed_lanes
                modified = True

        # Save if modified
        if modified and not dry_run:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        if modified:
            return True, "; ".join(changes)
        else:
            return False, "No pipe-separated edges found"

    except Exception as e:
        return False, f"Error: {e}"


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Fix pipe-separated edge IDs in VSS/TEC scenarios'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '--base-dir',
        type=Path,
        default=Path(__file__).parent.parent,
        help='Base directory of the project (default: parent of scripts/)'
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("Fix Pipe-Separated Edge IDs")
    logger.info("=" * 80)

    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be modified")

    # Find scenarios with pipe-separated edges
    logger.info(f"\nSearching for scenarios with pipe-separated edge IDs in {args.base_dir}")
    scenarios = find_scenarios_with_pipe_edges(args.base_dir)
    logger.info(f"Found {len(scenarios)} scenarios with pipe-separated edges")

    if not scenarios:
        logger.info("✅ No scenarios need fixing")
        return 0

    # Fix each scenario
    success_count = 0
    failed_count = 0

    for scenario_dir in scenarios:
        scenario_name = scenario_dir.name

        success, message = fix_scenario(scenario_dir, dry_run=args.dry_run)

        if success:
            status = "Would fix" if args.dry_run else "Fixed"
            logger.info(f"  ✓ {scenario_name}: {status} - {message}")
            success_count += 1
        else:
            logger.warning(f"  ✗ {scenario_name}: {message}")
            failed_count += 1

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total scenarios found: {len(scenarios)}")
    logger.info(f"Successfully fixed: {success_count}")
    logger.info(f"Failed: {failed_count}")

    if args.dry_run and success_count > 0:
        logger.info("\n⚠️  This was a dry run. Re-run without --dry-run to apply changes.")
    elif success_count > 0:
        logger.info("\n✅ Edge IDs fixed successfully!")
        logger.info("Next steps:")
        logger.info("  1. Run: python scripts/regenerate_all_add_xml.py")
        logger.info("  2. Run: python scripts/verify_vss_tec_xml.py")

    logger.info("=" * 80)

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
