"""Single 8765 SS application: restored 0.8.4 Brain + read-only workspace."""
from app import APP, VERSION
from workspace_min import router as workspace_router
APP.include_router(workspace_router)
assert VERSION == '0.8.4'
