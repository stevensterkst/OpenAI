"""Single 8765 SS application: restored 0.8.4 Brain + integrated console + read-only workspace."""
from app import APP, VERSION
from workspace_min import router as workspace_router
from ss_hardening import register

APP.include_router(workspace_router)
register(APP)
assert VERSION == '0.8.4'
