"""Canonical SS v0.8.4 entry point for 8765.

Loads the integrated Brain and guarantees the read-only workspace router is
mounted exactly once. This tiny composition layer prevents accidental launch
of the retired/legacy server modules.
"""
from app_integrated import APP
from workspace_min import router as workspace_router

_existing = {getattr(r, "path", "") for r in APP.routes}
if "/api/workspace/scan" not in _existing:
    APP.include_router(workspace_router)

VERSION = "0.8.4"
assert VERSION == "0.8.4"
