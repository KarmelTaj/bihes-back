"""
Custom middleware.

Re-exports each middleware so settings can reference them by a stable path
(e.g. ``core.middleware.RequestIDMiddleware``) regardless of which module they
live in. Add new middleware as its own module and export it here.
"""

from .request_id import RequestIDMiddleware

__all__ = ["RequestIDMiddleware"]
