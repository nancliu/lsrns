# Phase 1 Unit Tests Runner
# Run all Phase 1 plan management unit tests

Write-Host "=== Running Phase 1 Plan Management Unit Tests ===" -ForegroundColor Cyan
Write-Host ""

# Activate conda environment
Write-Host "Activating od_project environment..." -ForegroundColor Yellow
conda activate od_project

# Run pytest with coverage
Write-Host "`nRunning tests..." -ForegroundColor Yellow
pytest tests/unit/test_plan_entity.py `
       tests/unit/test_plan_file_manager.py `
       tests/unit/test_plan_validator.py `
       tests/unit/test_additional_generator_plan.py `
       tests/unit/test_strategy_reference_protection.py `
       tests/unit/test_control_plan_service.py `
       -v `
       --cov=api/services/control_plan_service `
       --cov=api/models/control/entities/plan `
       --cov=shared/control_tools/plan_file_manager `
       --cov=shared/control_tools/plan_validator `
       --cov=shared/control_tools/additional_generator `
       --cov=shared/control_tools/strategy_file_manager `
       --cov-report=term-missing `
       --cov-report=html:htmlcov

Write-Host "`n=== Test Results ===" -ForegroundColor Cyan
Write-Host "Coverage report generated in: htmlcov/index.html" -ForegroundColor Green
Write-Host ""
Write-Host "To view coverage report:" -ForegroundColor Yellow
Write-Host "  Start-Process htmlcov/index.html" -ForegroundColor White
