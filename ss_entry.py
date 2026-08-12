"""Canonical SS v0.8.4 entry point for 8765.

Loads the integrated Brain and explicitly mounts the read-only workspace
handlers. Explicit registration is intentional: it makes the canonical
composition testable and prevents an accidental launch of a retired server.
"""
from app_integrated import APP
from workspace_min import workspace, scan, extract_route, duplicates, context

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
