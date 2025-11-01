"""
Vehicle Type Expansion Utilities

Provides two-layer vehicle type system:
- Layer 1 (User Interface): 3 high-level categories (客车/货车/特种车辆)
- Layer 2 (SUMO Simulation): 6 detailed types (passenger_small/large, truck_small/large, special_small/large)

This module handles automatic expansion from categories to detailed types.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional

logger = logging.getLogger(__name__)


class VehicleTypeExpander:
    """Handles expansion of vehicle type categories to detailed SUMO types."""

    def __init__(self):
        """Initialize expander with configuration from JSON files."""
        self._category_mapping: Dict[str, List[str]] = {}
        self._valid_categories: Set[str] = set()
        self._valid_detailed_types: Set[str] = set()
        self._load_configurations()

    def _load_configurations(self):
        """Load vehicle type configurations from JSON files."""
        # Load enum configuration (category definitions)
        enum_path = Path(__file__).parent.parent.parent / "control_data" / "templates" / "common" / "vehicle_types_enum.json"

        try:
            with open(enum_path, "r", encoding="utf-8") as f:
                enum_data = json.load(f)

            # Build category mapping: category -> [detailed_types]
            for value_item in enum_data.get("values", []):
                category = value_item.get("value")
                includes = value_item.get("includes", [])

                if category and includes:
                    self._category_mapping[category] = includes
                    self._valid_categories.add(category)
                    self._valid_detailed_types.update(includes)

            logger.info(f"Loaded {len(self._category_mapping)} vehicle type categories")

        except FileNotFoundError:
            logger.error(f"Vehicle types enum file not found: {enum_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in vehicle types enum: {e}")
            raise

    def expand_vehicle_types(
        self,
        input_types: List[str],
        preserve_user_selection: bool = True
    ) -> Dict[str, List[str]]:
        """
        Expand vehicle type categories to detailed SUMO types.

        Args:
            input_types: List of vehicle types (can be categories or detailed types)
            preserve_user_selection: If True, return both expanded and original selection

        Returns:
            Dictionary with:
            - "expanded": List of detailed SUMO types
            - "user_selection": Original input (only if preserve_user_selection=True)

        Raises:
            ValueError: If input contains invalid vehicle types

        Examples:
            >>> expander = VehicleTypeExpander()
            >>> expander.expand_vehicle_types(["passenger", "truck"])
            {
                "expanded": ["passenger_small", "passenger_large", "truck_small", "truck_large"],
                "user_selection": ["passenger", "truck"]
            }
        """
        if not input_types:
            logger.warning("Empty vehicle types list provided")
            return {"expanded": [], "user_selection": []} if preserve_user_selection else {"expanded": []}

        expanded_types: Set[str] = set()
        invalid_types: List[str] = []

        for vtype in input_types:
            if vtype in self._valid_categories:
                # It's a category - expand it
                expanded_types.update(self._category_mapping[vtype])
            elif vtype in self._valid_detailed_types:
                # It's already a detailed type - keep it
                expanded_types.add(vtype)
            else:
                # Invalid type
                invalid_types.append(vtype)

        if invalid_types:
            raise ValueError(
                f"Invalid vehicle types: {invalid_types}. "
                f"Valid categories: {list(self._valid_categories)}. "
                f"Valid detailed types: {list(self._valid_detailed_types)}."
            )

        result = {"expanded": sorted(list(expanded_types))}

        if preserve_user_selection:
            result["user_selection"] = input_types

        return result

    def validate_vehicle_types(self, vehicle_types: List[str]) -> bool:
        """
        Validate if vehicle types are valid (categories or detailed types).

        Args:
            vehicle_types: List of vehicle types to validate

        Returns:
            True if all types are valid, False otherwise
        """
        if not vehicle_types:
            return False

        all_valid = all(
            vtype in self._valid_categories or vtype in self._valid_detailed_types
            for vtype in vehicle_types
        )

        return all_valid

    def get_category_for_detailed_type(self, detailed_type: str) -> Optional[str]:
        """
        Get the category for a given detailed vehicle type.

        Args:
            detailed_type: Detailed SUMO type (e.g., "passenger_small")

        Returns:
            Category name (e.g., "passenger") or None if not found
        """
        for category, detailed_types in self._category_mapping.items():
            if detailed_type in detailed_types:
                return category
        return None

    def collapse_to_categories(self, detailed_types: List[str]) -> List[str]:
        """
        Collapse detailed types to categories (reverse of expand).

        Useful for displaying existing strategy configurations in UI.

        Args:
            detailed_types: List of detailed SUMO types

        Returns:
            List of categories that cover all detailed types

        Example:
            >>> expander.collapse_to_categories(["passenger_small", "passenger_large"])
            ["passenger"]
        """
        categories_needed: Set[str] = set()

        for dtype in detailed_types:
            category = self.get_category_for_detailed_type(dtype)
            if category:
                categories_needed.add(category)

        return sorted(list(categories_needed))

    @property
    def valid_categories(self) -> List[str]:
        """Get list of valid category names."""
        return sorted(list(self._valid_categories))

    @property
    def valid_detailed_types(self) -> List[str]:
        """Get list of valid detailed type names."""
        return sorted(list(self._valid_detailed_types))

    @property
    def category_mapping(self) -> Dict[str, List[str]]:
        """Get full category to detailed types mapping."""
        return self._category_mapping.copy()


# Singleton instance for global use
_expander_instance: Optional[VehicleTypeExpander] = None


def get_vehicle_type_expander() -> VehicleTypeExpander:
    """Get singleton instance of VehicleTypeExpander."""
    global _expander_instance
    if _expander_instance is None:
        _expander_instance = VehicleTypeExpander()
    return _expander_instance


# Convenience functions for quick access
def expand_vehicle_types(input_types: List[str]) -> Dict[str, List[str]]:
    """Convenience function to expand vehicle types using singleton instance."""
    return get_vehicle_type_expander().expand_vehicle_types(input_types)


def validate_vehicle_types(vehicle_types: List[str]) -> bool:
    """Convenience function to validate vehicle types using singleton instance."""
    return get_vehicle_type_expander().validate_vehicle_types(vehicle_types)


def collapse_to_categories(detailed_types: List[str]) -> List[str]:
    """Convenience function to collapse detailed types to categories."""
    return get_vehicle_type_expander().collapse_to_categories(detailed_types)
