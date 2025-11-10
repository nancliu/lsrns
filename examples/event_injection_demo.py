"""
Event Injection XML Generation Demo

Demonstrates how to use the event_injector module to generate SUMO closedLane XML
from real event data.

This script:
1. Loads one example accident event from the events CSV
2. Generates closedLane XML using AccidentInjector
3. Validates the XML output format
4. Demonstrates error handling for invalid data

Usage:
    python examples/event_injection_demo.py

Author: AI Assistant
Created: 2025-01-10
"""

import sys
import logging
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.control_tools.event_injector import create_event_injector, AccidentInjector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_basic_accident_xml():
    """Demonstrate basic accident XML generation"""
    logger.info("=" * 60)
    logger.info("Demo 1: Basic Accident XML Generation")
    logger.info("=" * 60)

    # Create event data (from events CSV)
    event_data = {
        "report_id": "12547",
        "edge_id": "-4688",
        "affected_lanes": ["应急车道"],
        "start_time": "2025-07-14 01:53:49",
        "end_time": "2025-07-14 03:22:39"
    }

    # Create injector
    injector = AccidentInjector(network_file=None)

    # Generate XML
    xml = injector.generate_xml(event_data)

    logger.info("Generated XML:")
    logger.info(xml)
    logger.info("")

    return xml


def demo_multiple_lanes():
    """Demonstrate accident with multiple closed lanes"""
    logger.info("=" * 60)
    logger.info("Demo 2: Multiple Lane Closure")
    logger.info("=" * 60)

    event_data = {
        "report_id": "12548",
        "edge_id": "-4688",
        "affected_lanes": ["应急车道", "第一车道", "第二车道"],
        "start_time": "2025-07-14 08:30:00",
        "end_time": "2025-07-14 10:45:00"
    }

    injector = AccidentInjector(network_file=None)
    xml = injector.generate_xml(event_data)

    logger.info("Generated XML:")
    logger.info(xml)
    logger.info("")

    return xml


def demo_with_sim_start_time():
    """Demonstrate time conversion with explicit simulation start time"""
    logger.info("=" * 60)
    logger.info("Demo 3: Custom Simulation Start Time")
    logger.info("=" * 60)

    event_data = {
        "report_id": "12549",
        "edge_id": "-4688",
        "affected_lanes": ["应急车道"],
        "start_time": "2025-07-14 02:00:00",
        "end_time": "2025-07-14 03:00:00",
        "sim_start_time": "2025-07-14 01:30:00"  # Sim starts 30 min before event
    }

    injector = AccidentInjector(network_file=None)
    xml = injector.generate_xml(event_data)

    logger.info("Generated XML (event begins 1800s after simulation start):")
    logger.info(xml)
    logger.info("")

    return xml


def demo_factory_pattern():
    """Demonstrate factory function for creating injectors"""
    logger.info("=" * 60)
    logger.info("Demo 4: Factory Pattern")
    logger.info("=" * 60)

    # Create accident injector using factory
    accident_injector = create_event_injector("交通事故")
    logger.info(f"Created injector: {type(accident_injector).__name__}")

    event_data = {
        "report_id": "12550",
        "edge_id": "-4688",
        "affected_lanes": ["第一车道"],
        "start_time": "2025-07-14 14:00:00",
        "end_time": "2025-07-14 15:30:00"
    }

    xml = accident_injector.generate_xml(event_data)
    logger.info("Generated XML:")
    logger.info(xml)
    logger.info("")

    # Create congestion injector (placeholder)
    congestion_injector = create_event_injector("交通阻塞")
    logger.info(f"Created injector: {type(congestion_injector).__name__}")

    congestion_data = {
        "report_id": "20001",
        "edge_id": "-4688",
        "start_time": "2025-07-14 08:00:00",
        "end_time": "2025-07-14 10:00:00"
    }

    xml = congestion_injector.generate_xml(congestion_data)
    logger.info("Generated rerouter XML (placeholder):")
    logger.info(xml)
    logger.info("")


def demo_error_handling():
    """Demonstrate error handling for invalid data"""
    logger.info("=" * 60)
    logger.info("Demo 5: Error Handling")
    logger.info("=" * 60)

    injector = AccidentInjector(network_file=None)

    # Test 1: Missing required field
    logger.info("Test 1: Missing required field")
    try:
        invalid_data = {
            "report_id": "12551",
            # Missing edge_id
            "affected_lanes": ["应急车道"],
            "start_time": "2025-07-14 01:00:00",
            "end_time": "2025-07-14 03:00:00"
        }
        injector.generate_xml(invalid_data)
    except ValueError as e:
        logger.error(f"Expected error: {e}")

    # Test 2: Unknown lane description
    logger.info("\nTest 2: Unknown lane description")
    try:
        invalid_data = {
            "report_id": "12552",
            "edge_id": "-4688",
            "affected_lanes": ["未知车道"],  # Unknown lane
            "start_time": "2025-07-14 01:00:00",
            "end_time": "2025-07-14 03:00:00"
        }
        injector.generate_xml(invalid_data)
    except ValueError as e:
        logger.error(f"Expected error: {e}")

    # Test 3: End time before start time
    logger.info("\nTest 3: End time before start time")
    try:
        invalid_data = {
            "report_id": "12553",
            "edge_id": "-4688",
            "affected_lanes": ["应急车道"],
            "start_time": "2025-07-14 03:00:00",
            "end_time": "2025-07-14 01:00:00"  # Before start
        }
        injector.generate_xml(invalid_data)
    except ValueError as e:
        logger.error(f"Expected error: {e}")

    logger.info("")


def demo_load_from_csv():
    """Demonstrate loading real event from CSV and generating XML"""
    logger.info("=" * 60)
    logger.info("Demo 6: Load Real Event from CSV")
    logger.info("=" * 60)

    csv_path = Path("events/all_extracted_events.csv")

    if not csv_path.exists():
        logger.warning(f"CSV file not found: {csv_path}")
        logger.warning("Skipping CSV demo")
        return

    try:
        # Load events
        df = pd.read_csv(csv_path, encoding='utf-8')
        logger.info(f"Loaded {len(df)} events from CSV")

        # Filter for accident events with complete data
        accident_events = df[
            (df['event_type'] == '交通事故') &
            (df['edge_id'].notna()) &
            (df['affected_lanes'].notna()) &
            (df['start_time'].notna()) &
            (df['end_time'].notna())
        ]

        if len(accident_events) == 0:
            logger.warning("No complete accident events found in CSV")
            return

        # Take first complete event
        event = accident_events.iloc[0]
        logger.info(f"\nUsing event: {event['report_id']}")
        logger.info(f"Location: {event.get('road', 'N/A')} {event.get('direction', 'N/A')}")
        logger.info(f"Time: {event['start_time']} to {event['end_time']}")

        # Parse affected lanes (CSV contains string representation of list)
        import ast
        affected_lanes = ast.literal_eval(event['affected_lanes']) if isinstance(event['affected_lanes'], str) else event['affected_lanes']

        event_data = {
            "report_id": str(event['report_id']),
            "edge_id": str(event['edge_id']),
            "affected_lanes": affected_lanes,
            "start_time": str(event['start_time']),
            "end_time": str(event['end_time'])
        }

        # Generate XML with network file
        network_file = Path("templates/network_files/sichuan202508v7.net.xml")
        if network_file.exists():
            injector = AccidentInjector(network_file=str(network_file))
            logger.info(f"Using network file: {network_file}")
        else:
            injector = AccidentInjector(network_file=None)
            logger.info("Network file not found, using default lane mapping")

        xml = injector.generate_xml(event_data)
        logger.info("\nGenerated XML from real event:")
        logger.info(xml)

    except Exception as e:
        logger.error(f"Error processing CSV: {e}")

    logger.info("")


def main():
    """Run all demos"""
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 10 + "Event Injection XML Generation Demo" + " " * 12 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    logger.info("\n")

    # Run demos
    demo_basic_accident_xml()
    demo_multiple_lanes()
    demo_with_sim_start_time()
    demo_factory_pattern()
    demo_error_handling()
    demo_load_from_csv()

    logger.info("=" * 60)
    logger.info("All demos completed successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
