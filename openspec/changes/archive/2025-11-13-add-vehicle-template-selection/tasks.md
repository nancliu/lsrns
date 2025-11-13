# Implementation Tasks

## 1. Backend API Changes
- [x] 1.1 Add `vehicle_template` optional field to `TimeRangeRequest` model in `api/models/requests/data_requests.py`
- [x] 1.2 Add vehicle template listing endpoint in `api/routes/template_routes.py` (GET `/api/v1/templates/vehicle`)
- [x] 1.3 Update `data_service.py` to pass `vehicle_template` to ODProcessor initialization
- [x] 1.4 Update case metadata creation to store `vehicle_template` choice in templates section
- [x] 1.5 Add validation to ensure selected vehicle template file exists

## 2. Frontend UI Changes
- [x] 2.1 Add vehicle template selector dropdown to OD processing form in `frontend/index.html`
- [x] 2.2 Add vehicle template loading function in `frontend/script.js`
- [x] 2.3 Update template refresh logic to load vehicle templates
- [x] 2.4 Update `processODData()` to include `vehicle_template` in request payload
- [x] 2.5 Set default selection to `vehicle_types.json`

## 3. Testing and Validation
- [x] 3.1 Test OD data processing with default vehicle template
- [x] 3.2 Test OD data processing with alternative vehicle template (`vehicle_types_tj1.json`)
- [x] 3.3 Verify case metadata correctly stores vehicle template choice
- [x] 3.4 Verify error handling when invalid template is selected
- [x] 3.5 Test backward compatibility (existing cases without vehicle_template field)

## 4. Documentation
- [x] 4.1 Update API documentation to reflect new `vehicle_template` parameter
- [x] 4.2 Add inline help text explaining vehicle template selection purpose
- [x] 4.3 Document vehicle template format requirements (if needed)
