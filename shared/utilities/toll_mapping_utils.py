#!/usr/bin/env python
"""
Toll Station Mapping Utilities.

This module provides utilities for loading and resolving toll station mappings
from CSV to SUMO network elements (edge_id, junction_id, TAZ).
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from functools import lru_cache

logger = logging.getLogger(__name__)


class TollMappingLoader:
    """Loader for toll station mapping data."""

    _instance = None
    _mapping_df = None
    _toll_to_edges = None

    def __new__(cls):
        """Singleton pattern to ensure single instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def load(cls, mapping_file: Optional[Path] = None) -> 'TollMappingLoader':
        """
        Load toll station mapping from CSV file.

        Args:
            mapping_file: Path to mapping CSV file. Defaults to standard location.

        Returns:
            TollMappingLoader instance with loaded data
        """
        instance = cls()

        if instance._mapping_df is None:
            if mapping_file is None:
                mapping_file = Path("events/reference/toll_station_mapping.csv")

            if not mapping_file.exists():
                logger.error(f"Toll station mapping file not found: {mapping_file}")
                instance._mapping_df = pd.DataFrame()
                instance._toll_to_edges = {}
                return instance

            try:
                logger.info(f"Loading toll station mapping from {mapping_file}")
                df = pd.read_csv(mapping_file, dtype=str)

                # Store the dataframe
                instance._mapping_df = df

                # Build lookup dictionary for fast access
                instance._toll_to_edges = {}
                for _, row in df.iterrows():
                    toll_id = str(row['toll_station_id']).strip()
                    edge_id = row.get('edge_id')

                    if pd.notna(edge_id):
                        if toll_id not in instance._toll_to_edges:
                            instance._toll_to_edges[toll_id] = []
                        if edge_id not in instance._toll_to_edges[toll_id]:
                            instance._toll_to_edges[toll_id].append(edge_id)

                logger.info(
                    f"Loaded {len(df)} toll station entries, "
                    f"{len(instance._toll_to_edges)} unique toll IDs"
                )

            except Exception as e:
                logger.error(f"Failed to load toll station mapping: {e}")
                instance._mapping_df = pd.DataFrame()
                instance._toll_to_edges = {}

        return instance

    def resolve_edges(self, toll_ids: List[str]) -> List[str]:
        """
        Resolve toll station IDs to SUMO edge IDs.

        Args:
            toll_ids: List of toll station IDs to resolve

        Returns:
            List of unique edge IDs for the given toll stations
        """
        if self._toll_to_edges is None:
            logger.warning("Toll mapping not loaded, returning empty list")
            return []

        edges = []
        for toll_id in toll_ids:
            toll_id = str(toll_id).strip().lstrip('0')  # Normalize ID

            if toll_id in self._toll_to_edges:
                edges.extend(self._toll_to_edges[toll_id])
                logger.debug(f"Resolved toll {toll_id} to edges: {self._toll_to_edges[toll_id]}")
            else:
                logger.warning(f"Toll station {toll_id} not found in mapping")

        # Return unique edges maintaining order
        seen = set()
        unique_edges = []
        for edge in edges:
            if edge not in seen:
                seen.add(edge)
                unique_edges.append(edge)

        return unique_edges

    def get_toll_info(self, toll_id: str) -> Optional[Dict]:
        """
        Get complete information for a toll station.

        Args:
            toll_id: Toll station ID

        Returns:
            Dictionary with toll station information or None if not found
        """
        if self._mapping_df is None or self._mapping_df.empty:
            return None

        toll_id = str(toll_id).strip().lstrip('0')  # Normalize ID

        # Find all entries for this toll ID
        matches = self._mapping_df[
            self._mapping_df['toll_station_id'].str.strip().str.lstrip('0') == toll_id
        ]

        if matches.empty:
            return None

        # Aggregate information from all matching entries
        info = {
            'toll_station_id': toll_id,
            'station_names': matches['station_name'].unique().tolist(),
            'route_codes': matches['route_code'].unique().tolist(),
            'edge_ids': matches['edge_id'].dropna().unique().tolist(),
            'junction_ids': matches['junction_id'].dropna().unique().tolist(),
            'taz_ids': matches['taz_id'].dropna().unique().tolist(),
            'entrance_exit': matches['entrance_exit'].unique().tolist(),
            'coordinates': []
        }

        # Add coordinates if available
        for _, row in matches.iterrows():
            if pd.notna(row.get('longitude')) and pd.notna(row.get('latitude')):
                info['coordinates'].append({
                    'longitude': float(row['longitude']),
                    'latitude': float(row['latitude']),
                    'type': row.get('entrance_exit', 'unknown')
                })

        return info

    def get_tolls_by_route(self, route_code: str) -> List[str]:
        """
        Get all toll station IDs for a specific route.

        Args:
            route_code: Route code (e.g., 'G5', 'G4202')

        Returns:
            List of toll station IDs on the specified route
        """
        if self._mapping_df is None or self._mapping_df.empty:
            return []

        route_tolls = self._mapping_df[
            self._mapping_df['route_code'] == route_code
        ]['toll_station_id'].unique().tolist()

        return [str(tid).strip().lstrip('0') for tid in route_tolls]

    def validate_edge_exists(self, edge_id: str) -> bool:
        """
        Check if an edge ID exists in the mapping.

        Args:
            edge_id: SUMO edge ID to check

        Returns:
            True if edge exists in any toll station mapping
        """
        if self._mapping_df is None or self._mapping_df.empty:
            return False

        return edge_id in self._mapping_df['edge_id'].values

    def get_statistics(self) -> Dict:
        """
        Get statistics about the loaded toll station mapping.

        Returns:
            Dictionary with mapping statistics
        """
        if self._mapping_df is None or self._mapping_df.empty:
            return {
                'total_entries': 0,
                'unique_toll_ids': 0,
                'mapped_toll_ids': 0,
                'routes': {}
            }

        df = self._mapping_df
        return {
            'total_entries': len(df),
            'unique_toll_ids': df['toll_station_id'].nunique(),
            'mapped_toll_ids': len(self._toll_to_edges),
            'stations_with_edges': df['edge_id'].notna().sum(),
            'stations_with_taz': df['taz_id'].notna().sum(),
            'routes': df['route_code'].value_counts().to_dict()
        }

    def clear_cache(self):
        """Clear the cached mapping data."""
        self._mapping_df = None
        self._toll_to_edges = None
        logger.info("Toll mapping cache cleared")


def load_toll_station_mapping(mapping_file: Optional[Path] = None) -> TollMappingLoader:
    """
    Convenience function to load toll station mapping.

    Args:
        mapping_file: Optional path to mapping CSV file

    Returns:
        Loaded TollMappingLoader instance
    """
    return TollMappingLoader.load(mapping_file)


def resolve_toll_edges(toll_ids: List[str], mapping: Optional[TollMappingLoader] = None) -> List[str]:
    """
    Convenience function to resolve toll station IDs to edge IDs.

    Args:
        toll_ids: List of toll station IDs (can be comma-separated string)
        mapping: Optional TollMappingLoader instance (will load if not provided)

    Returns:
        List of unique edge IDs

    Example:
        >>> edges = resolve_toll_edges("250,255,256")
        >>> edges = resolve_toll_edges(["250", "255", "256"])
    """
    # Handle comma-separated string input
    if isinstance(toll_ids, str):
        toll_ids = [tid.strip() for tid in toll_ids.split(',') if tid.strip()]

    if mapping is None:
        mapping = TollMappingLoader.load()

    return mapping.resolve_edges(toll_ids)


def get_toll_station_info(toll_id: str, mapping: Optional[TollMappingLoader] = None) -> Optional[Dict]:
    """
    Get complete information for a toll station.

    Args:
        toll_id: Toll station ID
        mapping: Optional TollMappingLoader instance

    Returns:
        Dictionary with toll station information
    """
    if mapping is None:
        mapping = TollMappingLoader.load()

    return mapping.get_toll_info(toll_id)


def get_route_toll_stations(route_code: str, mapping: Optional[TollMappingLoader] = None) -> List[str]:
    """
    Get all toll stations for a specific route.

    Args:
        route_code: Route code (e.g., 'G5', 'G4202')
        mapping: Optional TollMappingLoader instance

    Returns:
        List of toll station IDs
    """
    if mapping is None:
        mapping = TollMappingLoader.load()

    return mapping.get_tolls_by_route(route_code)