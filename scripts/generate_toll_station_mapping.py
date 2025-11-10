#!/usr/bin/env python
"""
Generate toll station mapping CSV from database.

This script extracts toll station data from database tables and creates
a comprehensive mapping file that links toll station IDs to SUMO network elements.
"""

import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
import sys
import os
import logging
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from shared.data_access.connection import get_pooled_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_toll_stations_from_db() -> pd.DataFrame:
    """Extract toll station data from database tables."""
    logger.info("Extracting toll station data from database...")

    query = """
    SELECT DISTINCT
        -- Extract last 3 digits as toll_station_id
        SUBSTRING(sq.station_code_js FROM '.{3}$') as toll_station_id,
        sq.station_name,
        sq.square_code,
        sq.route_code,
        sq.section_code,
        sq.lng_84 as longitude,
        sq.lat_84 as latitude,
        -- Direction can indicate entrance/exit
        CASE
            WHEN sq.direction = '入口' THEN 'entrance'
            WHEN sq.direction = '出口' THEN 'exit'
            ELSE 'entrance'
        END as entrance_exit,
        sq.station_code_js as full_station_code
    FROM dim.point_toll_square sq
    WHERE sq.lng_84 IS NOT NULL
        AND sq.lat_84 IS NOT NULL
    ORDER BY sq.route_code, sq.section_code
    """

    try:
        conn = get_pooled_connection()
        df = pd.read_sql(query, conn)
        conn.close()

        # Remove leading zeros from toll_station_id for consistency
        df['toll_station_id'] = df['toll_station_id'].str.lstrip('0')
        logger.info(f"Extracted {len(df)} toll stations from database")
        return df
    except Exception as e:
        logger.error(f"Failed to extract toll stations: {e}")
        raise


def get_taz_mappings() -> pd.DataFrame:
    """Extract TAZ-to-toll mappings from database."""
    logger.info("Extracting TAZ mappings from database...")

    query = """
    SELECT
        tdm.source_id as square_code,
        tdm.taz_id,
        NULL as taz_edge_id  -- This table doesn't have edge_id
    FROM dim.taz_demonstration_mapping tdm
    WHERE tdm.source_type = 'toll_square'
        AND tdm.source_id IS NOT NULL
    """

    try:
        conn = get_pooled_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        logger.info(f"Found {len(df)} TAZ mappings")
        return df
    except Exception as e:
        logger.error(f"Failed to extract TAZ mappings: {e}")
        return pd.DataFrame()


def parse_taz_file(taz_file_path: Path) -> Dict[str, str]:
    """Parse TAZ XML file to extract TAZ-to-edge mappings."""
    logger.info(f"Parsing TAZ file: {taz_file_path}")

    taz_to_edge = {}
    try:
        tree = ET.parse(taz_file_path)
        root = tree.getroot()

        for taz in root.findall('.//taz'):
            taz_id = taz.get('id')
            edges = taz.get('edges', '').strip()
            if taz_id and edges:
                # For toll stations, usually the first edge is the entrance
                first_edge = edges.split()[0] if edges else None
                if first_edge:
                    taz_to_edge[taz_id] = first_edge

        logger.info(f"Parsed {len(taz_to_edge)} TAZ definitions")
        return taz_to_edge
    except Exception as e:
        logger.error(f"Failed to parse TAZ file: {e}")
        return {}


def get_network_edges() -> pd.DataFrame:
    """Get SUMO network edges from database for validation."""
    logger.info("Extracting network edges from database...")

    query = """
    SELECT
        edge_id,
        from_junction,
        to_junction,
        type,
        ST_X(ST_StartPoint(geom)) as start_lon,
        ST_Y(ST_StartPoint(geom)) as start_lat,
        ST_X(ST_EndPoint(geom)) as end_lon,
        ST_Y(ST_EndPoint(geom)) as end_lat
    FROM dim.sim_network_edges
    WHERE type IS NOT NULL
    """

    try:
        conn = get_pooled_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        logger.info(f"Found {len(df)} network edges")
        return df
    except Exception as e:
        logger.error(f"Failed to extract network edges: {e}")
        return pd.DataFrame()


def find_nearest_edge(lat: float, lon: float, edges_df: pd.DataFrame,
                     max_distance_m: float = 500) -> Optional[str]:
    """Find nearest edge to given coordinates within threshold."""
    if edges_df.empty:
        return None

    # Create a copy to avoid modifying the original dataframe
    edges_copy = edges_df.copy()

    # Simple Euclidean distance (approximate for small distances)
    # For more accuracy, use haversine formula
    edges_copy['distance'] = (
        ((edges_copy['start_lat'] - lat) ** 2 +
         (edges_copy['start_lon'] - lon) ** 2) ** 0.5 * 111000  # Convert to approx meters
    )

    min_idx = edges_copy['distance'].idxmin()
    if edges_copy.loc[min_idx, 'distance'] <= max_distance_m:
        return edges_copy.loc[min_idx, 'edge_id']
    return None


def generate_toll_mapping(output_path: Path):
    """Generate comprehensive toll station mapping CSV."""
    logger.info("Starting toll station mapping generation...")

    # Extract data
    toll_df = extract_toll_stations_from_db()
    taz_map_df = get_taz_mappings()
    edges_df = get_network_edges()

    # Parse TAZ file
    taz_file = Path("templates/taz_files/TAZ_6.add.xml")
    taz_edges = parse_taz_file(taz_file) if taz_file.exists() else {}

    # Merge TAZ mappings
    if not taz_map_df.empty:
        toll_df = toll_df.merge(
            taz_map_df[['square_code', 'taz_id', 'taz_edge_id']],
            on='square_code',
            how='left'
        )
    else:
        toll_df['taz_id'] = None
        toll_df['taz_edge_id'] = None

    # Resolve edge_id for each toll station
    edge_ids = []
    junction_ids = []

    for idx, row in toll_df.iterrows():
        edge_id = None
        junction_id = None

        # Priority 1: Use TAZ edge if available
        if pd.notna(row.get('taz_edge_id')):
            edge_id = row['taz_edge_id']
            logger.debug(f"Station {row['toll_station_id']}: Using TAZ edge {edge_id}")

        # Priority 2: Check TAZ file
        elif pd.notna(row.get('taz_id')) and row['taz_id'] in taz_edges:
            edge_id = taz_edges[row['taz_id']]
            logger.debug(f"Station {row['toll_station_id']}: Using TAZ file edge {edge_id}")

        # Priority 3: Find nearest edge by coordinates
        elif pd.notna(row['latitude']) and pd.notna(row['longitude']):
            edge_id = find_nearest_edge(
                row['latitude'],
                row['longitude'],
                edges_df
            )
            if edge_id:
                logger.debug(f"Station {row['toll_station_id']}: Found nearest edge {edge_id}")
            else:
                logger.warning(f"Station {row['toll_station_id']}: No edge within 500m")

        # Get junction_id if edge found
        if edge_id and not edges_df.empty:
            edge_info = edges_df[edges_df['edge_id'] == edge_id]
            if not edge_info.empty:
                junction_id = edge_info.iloc[0]['from_junction']

        edge_ids.append(edge_id)
        junction_ids.append(junction_id)

    toll_df['edge_id'] = edge_ids
    toll_df['junction_id'] = junction_ids

    # Select and reorder columns for final output
    output_columns = [
        'toll_station_id', 'station_name', 'square_code',
        'route_code', 'section_code', 'longitude', 'latitude',
        'taz_id', 'entrance_exit', 'edge_id', 'junction_id'
    ]

    # Ensure all columns exist
    for col in output_columns:
        if col not in toll_df.columns:
            toll_df[col] = None

    result_df = toll_df[output_columns]

    # Save to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_path, index=False, encoding='utf-8-sig')

    # Log summary statistics
    logger.info(f"Generated mapping for {len(result_df)} toll stations")
    logger.info(f"Stations with edge_id: {result_df['edge_id'].notna().sum()}")
    logger.info(f"Stations with TAZ: {result_df['taz_id'].notna().sum()}")
    logger.info(f"Stations by route: {result_df['route_code'].value_counts().to_dict()}")

    # Save metadata
    metadata = {
        'total_stations': len(result_df),
        'stations_with_edges': int(result_df['edge_id'].notna().sum()),
        'stations_with_taz': int(result_df['taz_id'].notna().sum()),
        'routes': result_df['route_code'].value_counts().to_dict(),
        'generation_timestamp': pd.Timestamp.now().isoformat()
    }

    metadata_path = output_path.with_suffix('.metadata.json')
    pd.Series(metadata).to_json(metadata_path, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")

    return result_df


def validate_mapping(df: pd.DataFrame):
    """Validate the generated mapping."""
    logger.info("Validating toll station mapping...")

    issues = []

    # Check for duplicate IDs
    duplicates = df[df.duplicated('toll_station_id', keep=False)]
    if not duplicates.empty:
        issues.append(f"Found {len(duplicates)} duplicate toll_station_ids")
        logger.warning(f"Duplicate IDs: {duplicates['toll_station_id'].unique()}")

    # Check for missing edge_ids
    missing_edges = df[df['edge_id'].isna()]
    if not missing_edges.empty:
        issues.append(f"Found {len(missing_edges)} stations without edge_id")
        logger.warning(f"Stations without edges: {missing_edges[['toll_station_id', 'station_name']].values}")

    # Validate known G5 stations
    g5_validations = {
        '1232': '-1232',  # 双流南站
        '15': 'E15',      # 白家站
        '15818': '-15818' # 新都站
    }

    for station_id, expected_edge in g5_validations.items():
        station = df[df['toll_station_id'] == station_id]
        if station.empty:
            issues.append(f"G5 validation: Station {station_id} not found")
        elif station.iloc[0]['edge_id'] != expected_edge:
            issues.append(f"G5 validation: Station {station_id} edge mismatch")
            logger.error(f"Expected {expected_edge}, got {station.iloc[0]['edge_id']}")

    if issues:
        logger.warning(f"Validation found {len(issues)} issues:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    else:
        logger.info("Validation passed: No issues found")

    return len(issues) == 0


def main():
    """Main execution function."""
    output_path = Path("events/reference/toll_station_mapping.csv")

    try:
        # Generate mapping
        df = generate_toll_mapping(output_path)
        logger.info(f"Successfully generated toll station mapping: {output_path}")

        # Validate
        is_valid = validate_mapping(df)

        # Display sample
        logger.info("\nSample of generated mapping:")
        print(df.head(10).to_string())

        if is_valid:
            logger.info("\n✅ Toll station mapping generated and validated successfully!")
        else:
            logger.warning("\n⚠️ Toll station mapping generated with validation warnings")

        return 0 if is_valid else 1

    except Exception as e:
        logger.error(f"Failed to generate toll station mapping: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())