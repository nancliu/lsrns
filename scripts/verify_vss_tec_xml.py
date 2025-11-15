"""
Verify VSS and TEC XML generation issues.

Scans all scenarios to check if .add.xml files contain valid
variableSpeedSign and calibrator elements with required attributes.

Usage:
    python scripts/verify_vss_tec_xml.py

Author: AI Assistant
Created: 2025-11-14
Version: 1.0.0
"""

import sys
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_vss_xml(xml_path: Path) -> Tuple[bool, str]:
    """
    Check if VSS XML is valid (contains step elements with time and speed).

    Args:
        xml_path: Path to .add.xml file

    Returns:
        Tuple of (is_valid, issue_description)
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find variableSpeedSign elements
        vss_elements = root.findall('.//variableSpeedSign')

        if not vss_elements:
            return True, "No VSS elements (expected for non-VSS scenarios)"

        for vss in vss_elements:
            vss_id = vss.get('id', 'unknown')

            # Check if VSS has lanes attribute
            if not vss.get('lanes'):
                return False, f"VSS {vss_id}: missing 'lanes' attribute"

            # Check for step elements
            steps = vss.findall('step')

            if not steps:
                return False, f"VSS {vss_id}: no <step> elements"

            # Check each step has time and speed attributes
            for i, step in enumerate(steps):
                if not step.get('time'):
                    return False, f"VSS {vss_id} step {i}: missing 'time' attribute"
                if not step.get('speed'):
                    return False, f"VSS {vss_id} step {i}: missing 'speed' attribute"

        return True, "Valid VSS XML"

    except ET.ParseError as e:
        return False, f"XML parse error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def check_tec_xml(xml_path: Path) -> Tuple[bool, str]:
    """
    Check if TEC XML is valid (contains calibrator elements).

    Args:
        xml_path: Path to .add.xml file

    Returns:
        Tuple of (is_valid, issue_description)
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find calibrator elements (TEC uses calibrator in SUMO)
        calibrators = root.findall('.//calibrator')

        if not calibrators:
            return True, "No TEC elements (expected for non-TEC scenarios)"

        for cal in calibrators:
            cal_id = cal.get('id', 'unknown')

            # Check required attributes
            if not cal.get('edge'):
                return False, f"Calibrator {cal_id}: missing 'edge' attribute"

            # Check for flow elements
            flows = cal.findall('flow')

            if not flows:
                return False, f"Calibrator {cal_id}: no <flow> elements"

            # Check each flow has required attributes
            for i, flow in enumerate(flows):
                if not flow.get('begin'):
                    return False, f"Calibrator {cal_id} flow {i}: missing 'begin' attribute"
                if not flow.get('end'):
                    return False, f"Calibrator {cal_id} flow {i}: missing 'end' attribute"

        return True, "Valid TEC XML"

    except ET.ParseError as e:
        return False, f"XML parse error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def scan_all_scenarios(scenarios_base_dir: Path) -> Dict[str, any]:
    """
    Scan all scenarios and check VSS/TEC XML validity.

    Args:
        scenarios_base_dir: Base scenarios directory

    Returns:
        Statistics dictionary
    """
    logger.info("=" * 80)
    logger.info("VSS/TEC XML VALIDATION SCAN")
    logger.info("=" * 80)

    stats = {
        'total_scenarios': 0,
        'vss_scenarios': 0,
        'vss_valid': 0,
        'vss_invalid': 0,
        'tec_scenarios': 0,
        'tec_valid': 0,
        'tec_invalid': 0,
        'vss_issues': [],
        'tec_issues': []
    }

    # Find all scenario directories
    event_dirs = [d for d in scenarios_base_dir.iterdir() if d.is_dir() and d.name[:2].isdigit()]

    for event_dir in event_dirs:
        scenario_dirs = [
            d for d in event_dir.iterdir()
            if d.is_dir() and d.name.startswith('scenario_')
        ]

        for scenario_dir in scenario_dirs:
            stats['total_scenarios'] += 1

            # Find .add.xml file
            add_xml_files = list(scenario_dir.glob("*.add.xml"))

            if not add_xml_files:
                continue

            add_xml_path = add_xml_files[0]
            scenario_name = scenario_dir.name

            # Check if VSS scenario
            if '_vss' in scenario_name.lower():
                stats['vss_scenarios'] += 1
                is_valid, message = check_vss_xml(add_xml_path)

                if is_valid:
                    stats['vss_valid'] += 1
                else:
                    stats['vss_invalid'] += 1
                    stats['vss_issues'].append({
                        'scenario': scenario_name,
                        'file': str(add_xml_path.relative_to(scenarios_base_dir)),
                        'issue': message
                    })
                    logger.warning(f"  ✗ VSS {scenario_name}: {message}")

            # Check if TEC scenario
            if '_tec' in scenario_name.lower():
                stats['tec_scenarios'] += 1
                is_valid, message = check_tec_xml(add_xml_path)

                if is_valid:
                    stats['tec_valid'] += 1
                else:
                    stats['tec_invalid'] += 1
                    stats['tec_issues'].append({
                        'scenario': scenario_name,
                        'file': str(add_xml_path.relative_to(scenarios_base_dir)),
                        'issue': message
                    })
                    logger.warning(f"  ✗ TEC {scenario_name}: {message}")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total scenarios scanned: {stats['total_scenarios']}")
    logger.info(f"\nVSS Scenarios:")
    logger.info(f"  Total: {stats['vss_scenarios']}")
    logger.info(f"  Valid: {stats['vss_valid']} ({stats['vss_valid']/stats['vss_scenarios']*100:.1f}%)" if stats['vss_scenarios'] > 0 else "  N/A")
    logger.info(f"  Invalid: {stats['vss_invalid']} ({stats['vss_invalid']/stats['vss_scenarios']*100:.1f}%)" if stats['vss_scenarios'] > 0 else "  N/A")
    logger.info(f"\nTEC Scenarios:")
    logger.info(f"  Total: {stats['tec_scenarios']}")
    logger.info(f"  Valid: {stats['tec_valid']} ({stats['tec_valid']/stats['tec_scenarios']*100:.1f}%)" if stats['tec_scenarios'] > 0 else "  N/A")
    logger.info(f"  Invalid: {stats['tec_invalid']} ({stats['tec_invalid']/stats['tec_scenarios']*100:.1f}%)" if stats['tec_scenarios'] > 0 else "  N/A")

    # Show sample issues
    if stats['vss_invalid'] > 0:
        logger.info(f"\nSample VSS Issues (showing first 5):")
        for issue in stats['vss_issues'][:5]:
            logger.info(f"  - {issue['scenario']}: {issue['issue']}")

    if stats['tec_invalid'] > 0:
        logger.info(f"\nSample TEC Issues (showing first 5):")
        for issue in stats['tec_issues'][:5]:
            logger.info(f"  - {issue['scenario']}: {issue['issue']}")

    logger.info("=" * 80)

    return stats


def main():
    """Main entry point."""
    scenarios_base_dir = project_root / 'output' / 'scenarios'

    if not scenarios_base_dir.exists():
        logger.error(f"Scenarios directory not found: {scenarios_base_dir}")
        return 1

    try:
        stats = scan_all_scenarios(scenarios_base_dir)

        # Check if issues found
        if stats['vss_invalid'] > 0 or stats['tec_invalid'] > 0:
            logger.error("\n⚠️  XML validation issues found!")
            logger.error("VSS/TEC control strategies may not work correctly in SUMO.")
            return 1
        else:
            logger.info("\n✓ All VSS/TEC XML files are valid")
            return 0

    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
