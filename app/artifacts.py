"""Compatibility shim for the repository-root Render entrypoint.

The Render service starts with ``uvicorn app.main:app`` from the repository
root. That entrypoint imports ``backend.app.main``, whose artifact router
import uses the root ``app`` package in that launch mode. Re-export the real
router here so both the root and backend working-directory launch modes work.
"""

from backend.app.artifacts import router

__all__ = ["router"]
