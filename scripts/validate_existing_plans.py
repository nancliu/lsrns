#!/usr/bin/env python
"""
Validation Script for Existing Control Plans

Purpose:
    Scans all existing control plans and validates their control.add.xml files
    against SUMO v1.19+ format and parameter constraints.

Usage:
    python scripts/validate_existing_plans.py [--case-dir PATH] [--output-report FILE] [--verbose]

OpenSpec Change: validate-strategy-xml-generation
Author: OpenSpec Migration Tool
Date: 2025-11-02
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.control_tools.xml_validator import validate_xml_string, ValidationResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


class PlanValidationReport:
    """Stores validation results for a plan."""

    def __init__(
        self,
        plan_id: str,
        case_id: str,
        xml_file_path: str,
        validation_result: ValidationResult
    ):
        self.plan_id = plan_id
        self.case_id = case_id
        self.xml_file_path = xml_file_path
        self.validation_result = validation_result

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export."""
        return {
            "plan_id": self.plan_id,
            "case_id": self.case_id,
            "xml_file_path": str(self.xml_file_path),
            "is_valid": self.validation_result.is_valid,
            "errors": [
                {"message": e.message, "field": e.field, "value": str(e.value) if e.value is not None else None}
                for e in self.validation_result.errors
            ],
            "warnings": [
                {"message": w.message, "field": w.field, "value": str(w.value) if w.value is not None else None}
                for w in self.validation_result.warnings
            ]
        }


def find_all_control_plans(plans_base_dir: Path) -> List[Tuple[str, Path]]:
    """
    Find all control.add.xml files in the plans directory.

    Args:
        plans_base_dir: Base directory containing plan subdirectories

    Returns:
        List of (plan_id, xml_file_path) tuples
    """
    plans = []

    if not plans_base_dir.exists():
        logger.warning(f"Plans directory not found: {plans_base_dir}")
        return plans

    # Iterate over plan subdirectories
    for plan_dir in plans_base_dir.iterdir():
        if not plan_dir.is_dir():
            continue

        xml_file = plan_dir / "control.add.xml"

        if xml_file.exists():
            plan_id = plan_dir.name
            plans.append((plan_id, xml_file))

    return plans


def validate_plan_xml(plan_id: str, xml_file_path: Path, verbose: bool = False) -> PlanValidationReport:
    """
    Validate a single plan's XML file.

    Args:
        plan_id: Plan identifier
        xml_file_path: Path to control.add.xml file
        verbose: If True, log detailed validation results

    Returns:
        PlanValidationReport object
    """
    # Extract case_id from path (assumes structure: control_data/plans/{plan_id}/...)
    # For now, use "unknown" as case_id since we don't have case context
    case_id = "unknown"

    try:
        # Read XML content
        with open(xml_file_path, "r", encoding="utf-8") as f:
            xml_content = f.read()

        # Validate XML
        validation_result = validate_xml_string(xml_content)

        if verbose:
            if validation_result.is_valid:
                logger.info(f"✓ Plan [{plan_id}] validation passed")
                if validation_result.warnings:
                    for warning in validation_result.warnings:
                        logger.info(f"  ⚠ Warning: {warning.message}")
            else:
                logger.error(f"✗ Plan [{plan_id}] validation failed")
                for error in validation_result.errors:
                    logger.error(f"  ✗ Error: {error.message}")

        return PlanValidationReport(plan_id, case_id, str(xml_file_path), validation_result)

    except FileNotFoundError:
        logger.error(f"XML file not found for plan [{plan_id}]: {xml_file_path}")
        # Return invalid result with file not found error
        validation_result = ValidationResult(
            is_valid=False,
            errors=[],
            warnings=[]
        )
        validation_result.errors.append(
            type('obj', (object,), {
                'message': f'XML file not found: {xml_file_path}',
                'field': 'file',
                'value': None
            })
        )
        return PlanValidationReport(plan_id, case_id, str(xml_file_path), validation_result)

    except Exception as e:
        logger.error(f"Error validating plan [{plan_id}]: {e}")
        # Return invalid result with exception error
        validation_result = ValidationResult(
            is_valid=False,
            errors=[],
            warnings=[]
        )
        validation_result.errors.append(
            type('obj', (object,), {
                'message': f'Validation error: {str(e)}',
                'field': 'exception',
                'value': None
            })
        )
        return PlanValidationReport(plan_id, case_id, str(xml_file_path), validation_result)


def print_summary(reports: List[PlanValidationReport]):
    """
    Print validation summary to console.

    Args:
        reports: List of PlanValidationReport objects
    """
    total = len(reports)
    valid = sum(1 for r in reports if r.validation_result.is_valid)
    invalid = total - valid
    with_warnings = sum(1 for r in reports if r.validation_result.warnings)

    print("\n" + "=" * 60)
    print("=== Validation Summary ===")
    print("=" * 60)
    print(f"Total plans scanned: {total}")
    print(f"Valid plans: {valid} ({valid / total * 100:.1f}%)" if total > 0 else "Valid plans: 0")
    print(f"Invalid plans: {invalid} ({invalid / total * 100:.1f}%)" if total > 0 else "Invalid plans: 0")
    print(f"Plans with warnings: {with_warnings}")
    print("=" * 60)

    # Print invalid plans details
    if invalid > 0:
        print("\n=== Invalid Plans ===")
        count = 0
        for report in reports:
            if not report.validation_result.is_valid:
                count += 1
                print(f"\n{count}. Plan: {report.plan_id} (Case: {report.case_id})")
                for error in report.validation_result.errors:
                    print(f"   Error: {error.message}")
                print(f"   File: {report.xml_file_path}")

    # Print plans with warnings
    if with_warnings > 0:
        print("\n=== Plans with Warnings ===")
        count = 0
        for report in reports:
            if report.validation_result.warnings:
                count += 1
                print(f"\n{count}. Plan: {report.plan_id} (Case: {report.case_id})")
                for warning in report.validation_result.warnings:
                    print(f"   Warning: {warning.message}")
                print(f"   File: {report.xml_file_path}")

    print("\n" + "=" * 60)


def save_report_json(reports: List[PlanValidationReport], output_file: Path):
    """
    Save validation report to JSON file.

    Args:
        reports: List of PlanValidationReport objects
        output_file: Output JSON file path
    """
    report_data = {
        "summary": {
            "total": len(reports),
            "valid": sum(1 for r in reports if r.validation_result.is_valid),
            "invalid": sum(1 for r in reports if not r.validation_result.is_valid),
            "with_warnings": sum(1 for r in reports if r.validation_result.warnings)
        },
        "plans": [r.to_dict() for r in reports]
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Validation report saved to: {output_file}")


def main():
    """Main script entry point."""
    parser = argparse.ArgumentParser(
        description="Validate existing control plan XML files against SUMO v1.19+ format"
    )
    parser.add_argument(
        "--plans-dir",
        type=Path,
        default=Path("control_data/plans"),
        help="Directory containing plan subdirectories (default: control_data/plans)"
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        help="Save detailed JSON report to this file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed validation output for each plan"
    )

    args = parser.parse_args()

    # Find all control plans
    logger.info(f"Scanning plans directory: {args.plans_dir}")
    plans = find_all_control_plans(args.plans_dir)

    if not plans:
        logger.warning("No control plans found!")
        logger.info("Make sure the --plans-dir path is correct")
        return 1

    logger.info(f"Found {len(plans)} control plans")

    # Validate each plan
    reports = []
    for plan_id, xml_file_path in plans:
        report = validate_plan_xml(plan_id, xml_file_path, verbose=args.verbose)
        reports.append(report)

    # Print summary
    print_summary(reports)

    # Save JSON report if requested
    if args.output_report:
        save_report_json(reports, args.output_report)

    # Return exit code based on validation results
    invalid_count = sum(1 for r in reports if not r.validation_result.is_valid)

    if invalid_count == 0:
        logger.info("✓ All plans passed validation!")
        return 0
    else:
        logger.warning(f"⚠ {invalid_count} plan(s) failed validation")
        logger.info("Review the errors above and fix the affected plans before deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())
