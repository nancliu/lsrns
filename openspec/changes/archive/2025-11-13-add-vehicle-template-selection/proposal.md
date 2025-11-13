# Add Vehicle Template Selection to OD Data Processing

## Why

Currently, OD data processing uses a hardcoded vehicle type configuration file (`vehicle_types.json`). Users cannot choose different vehicle simulation parameters for different cases, limiting flexibility in traffic simulation scenarios. Different vehicle type configurations (e.g., conservative vs aggressive driver behavior, different truck classifications) can significantly impact simulation outcomes.

## What Changes

- Add a vehicle template selector to the OD data processing form (frontend/index.html)
- Load available vehicle template files from `templates/config_templates/vehicle_templates/` directory
- Add `vehicle_template` field to `TimeRangeRequest` model
- Pass selected vehicle template path to ODProcessor during case creation
- Store vehicle template choice in case metadata for traceability
- Default to `vehicle_types.json` when no template is explicitly selected

## Impact

**Affected specs**:
- New capability: `od-data-processing` (creating new spec)

**Affected code**:
- `frontend/index.html` - Add vehicle template dropdown selector
- `frontend/script.js` - Add vehicle template loading and selection logic
- `api/models/requests/data_requests.py` - Add `vehicle_template` field to `TimeRangeRequest`
- `api/services/data_service.py` - Pass vehicle template to ODProcessor
- `shared/data_processors/od_processor.py` - Already supports `vehicle_config_path` parameter (no changes needed)
- `api/routes/template_routes.py` - Add endpoint to list vehicle templates (if not exists)

**Breaking changes**: None. This is a backward-compatible addition with sensible defaults.

**Dependencies**: None. This change is self-contained.
