"""
Traffic Control Strategy Template Entity Models (API Layer Re-export)

This module re-exports entity models from the shared layer for backward compatibility.
The actual implementation has been moved to shared/control_tools/entities.py to fix
circular dependency issues.

All models are now defined in the shared layer and re-exported here for API responses.
"""

# Re-export all entities from shared layer
from shared.control_tools.entities import (
    StrategyType,
    ParameterSchema,
    ControlTemplate,
    TemplateIndexEntry,
    TemplatesIndex
)

__all__ = [
    "StrategyType",
    "ParameterSchema",
    "ControlTemplate",
    "TemplateIndexEntry",
    "TemplatesIndex"
]
