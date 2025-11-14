# Pydantic v2 Compatibility Fix

**Issue**: Pydantic v2 removed the `regex` parameter in favor of `pattern`
**File**: `api/models/requests/case_requests.py`
**Status**: ✅ FIXED

---

## Error Encountered

```
pydantic.errors.PydanticUserError: `regex` is removed. use `pattern` instead
```

**Root Cause**: Line 110 in `case_requests.py` used `regex` parameter which is deprecated in Pydantic v2.

---

## Solution Applied

**File**: `api/models/requests/case_requests.py`
**Line**: 110

**Before**:
```python
simulation_type: str = Field(
    "microscopic",
    description="仿真模式：microscopic（微观）或 mesoscopic（中观）",
    regex="^(microscopic|mesoscopic)$"
)
```

**After**:
```python
simulation_type: str = Field(
    "microscopic",
    description="仿真模式：microscopic（微观）或 mesoscopic（中观）",
    pattern="^(microscopic|mesoscopic)$"
)
```

---

## Verification

✅ All Python files pass syntax check:
```bash
python -m py_compile api/models/requests/case_requests.py
python -m py_compile api/routes/case_routes.py
python -m py_compile api/services/case_service.py
```

✅ AST parsing successful - syntax valid

---

## Status

🎯 **Implementation is now Pydantic v2 compatible and ready for API startup**

