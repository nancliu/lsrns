#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix VSS/TEC Configuration Field Names

This script fixes the field name mismatch between scenario_generator.py and additional_generator.py
that caused all VSS/TEC XML files to be invalid.

Problem:
- scenario_generator.py generated: 'begin', 'end'
- additional_generator.py expected: 'time_seconds' (VSS), 'begin_seconds'/'end_seconds' (TEC)
- Result: Empty <step> elements in XML, control strategies didn't work

Fix:
- VSS: Add 'time_seconds' field to speed_steps (using 'begin' value)
- TEC: Add 'begin_seconds' and 'end_seconds' fields to flow_intervals

Author: Claude
Date: 2025-11-14
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_all_control_strategy_configs(base_dir: Path) -> List[Path]:
    """Find all control_strategy_config.json files in scenario directories."""
    config_files = []

    # Search in output/scenarios directory
    scenarios_dir = base_dir / "output" / "scenarios"
    if scenarios_dir.exists():
        config_files.extend(scenarios_dir.rglob("control_strategy_config.json"))

    return sorted(config_files)


def fix_vss_config(config: Dict[str, Any]) -> tuple[bool, str]:
    """
    Fix VSS configuration by adding 'time_seconds' field to speed_steps.

    Returns:
        (modified: bool, message: str)
    """
    if config.get('strategy_type') != 'VSS':
        return False, "Not a VSS config"

    parameters = config.get('parameters', {})
    speed_steps = parameters.get('speed_steps', [])

    if not speed_steps:
        return False, "No speed_steps found"

    modified = False
    for step in speed_steps:
        # Check if time_seconds already exists
        if 'time_seconds' not in step and 'begin' in step:
            # Add time_seconds using begin value
            step['time_seconds'] = step['begin']
            modified = True

    if modified:
        return True, f"Added time_seconds to {len(speed_steps)} speed_steps"
    else:
        return False, "time_seconds already exists or begin not found"


def fix_tec_config(config: Dict[str, Any]) -> tuple[bool, str]:
    """
    Fix TEC configuration by adding 'begin_seconds' and 'end_seconds' fields.

    Returns:
        (modified: bool, message: str)
    """
    if config.get('strategy_type') != 'TEC':
        return False, "Not a TEC config"

    parameters = config.get('parameters', {})
    flow_intervals = parameters.get('flow_intervals', [])

    if not flow_intervals:
        return False, "No flow_intervals found"

    modified = False
    for interval in flow_intervals:
        # Check if begin_seconds/end_seconds already exist
        needs_begin = 'begin_seconds' not in interval and 'begin' in interval
        needs_end = 'end_seconds' not in interval and 'end' in interval

        if needs_begin:
            interval['begin_seconds'] = interval['begin']
            modified = True

        if needs_end:
            interval['end_seconds'] = interval['end']
            modified = True

    if modified:
        return True, f"Added begin_seconds/end_seconds to {len(flow_intervals)} flow_intervals"
    else:
        return False, "Fields already exist or begin/end not found"


def fix_config_file(config_path: Path, dry_run: bool = False) -> tuple[bool, str]:
    """
    Fix a single control_strategy_config.json file.

    Args:
        config_path: Path to the config file
        dry_run: If True, don't save changes

    Returns:
        (modified: bool, message: str)
    """
    try:
        # Read config
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Determine strategy type and fix
        strategy_type = config.get('strategy_type', '').upper()

        if strategy_type == 'VSS':
            modified, message = fix_vss_config(config)
        elif strategy_type == 'TEC':
            modified, message = fix_tec_config(config)
        else:
            return False, f"Unknown strategy type: {strategy_type}"

        # Save if modified
        if modified and not dry_run:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        return modified, message

    except Exception as e:
        return False, f"Error: {e}"


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Fix VSS/TEC configuration field names for XML generation'
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
    logger.info("VSS/TEC Configuration Field Fix")
    logger.info("=" * 80)

    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be modified")

    # Find all config files
    logger.info(f"\nSearching for control_strategy_config.json files in {args.base_dir}")
    config_files = find_all_control_strategy_configs(args.base_dir)
    logger.info(f"Found {len(config_files)} config files")

    # Fix each file
    vss_fixed = 0
    tec_fixed = 0
    vss_skipped = 0
    tec_skipped = 0
    errors = 0

    for config_path in config_files:
        # Get scenario name from path
        scenario_name = config_path.parent.name

        # Read strategy type first to categorize
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            strategy_type = config.get('strategy_type', '').upper()
        except Exception as e:
            logger.error(f"  ✗ {scenario_name}: Failed to read config: {e}")
            errors += 1
            continue

        # Fix the file
        modified, message = fix_config_file(config_path, dry_run=args.dry_run)

        if modified:
            status = "Would fix" if args.dry_run else "Fixed"
            logger.info(f"  ✓ {scenario_name} ({strategy_type}): {status} - {message}")
            if strategy_type == 'VSS':
                vss_fixed += 1
            elif strategy_type == 'TEC':
                tec_fixed += 1
        else:
            if strategy_type == 'VSS':
                vss_skipped += 1
            elif strategy_type == 'TEC':
                tec_skipped += 1

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total config files scanned: {len(config_files)}")
    logger.info(f"\nVSS Scenarios:")
    logger.info(f"  Fixed: {vss_fixed}")
    logger.info(f"  Skipped (already valid or no changes needed): {vss_skipped}")
    logger.info(f"\nTEC Scenarios:")
    logger.info(f"  Fixed: {tec_fixed}")
    logger.info(f"  Skipped (already valid or no changes needed): {tec_skipped}")
    logger.info(f"\nErrors: {errors}")

    if args.dry_run and (vss_fixed + tec_fixed) > 0:
        logger.info("\n⚠️  This was a dry run. Re-run without --dry-run to apply changes.")
    elif (vss_fixed + tec_fixed) > 0:
        logger.info("\n✅ Configuration files fixed successfully!")
        logger.info("Next step: Run regenerate_all_add_xml.py to regenerate XML files")
    else:
        logger.info("\n✅ All configuration files are already valid!")

    logger.info("=" * 80)

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
