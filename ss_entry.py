"""Canonical SS v0.8.4 entry point for 8765.

Loads the integrated Brain, installs the conservative resource-aware routing
policy, and explicitly mounts the read-only workspace handlers. This is the
only supported 8765 application composition entry.
"""
import app_integrated as brain
from workspace_min import workspace, scan, extract_route, duplicates, context
from ss_policy import install_policy

# Install routing policy before the application is served so both the HTTP
# endpoints and app_integrated.auto_chat use the same deterministic policy.
install_policy(brain)
APP = brain.APP

_existing = {getattr(r, "path", "") for r in APP.routes}
_routes = [
    ("/workspace", workspace, ["GET"]),
    ("/api/workspace/scan", scan, ["POST"]),
    ("/api/workspace/extract", extract_route, ["POST"]),
    ("/api/workspace/duplicates", duplicates, ["POST"]),
    ("/api/workspace/context", context, ["POST"]),
]
for _path, _handler, _methods in _routes:
    if _path not in _existing:
        APP.add_api_route(_path, _handler, methods=_methods)

VERSION = "0.8.4"
assert VERSION == "0.8.4"
