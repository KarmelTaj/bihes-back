"""
Settings package entry point.

Django reads ``core.settings`` (this package). It assembles the full settings
namespace from the concern-specific modules, then applies per-environment
overrides from ``local_settings.py`` (not in version control).

Order matters: ``base`` defines the foundations (BASE_DIR, DEBUG, …) that the
other modules build on, and ``local_settings`` is loaded last so it can override
anything.
"""

from .base import *  # noqa: F401,F403
from .rest_framework import *  # noqa: F401,F403
from .logging import *  # noqa: F401,F403

try:
    from local_settings import *  # noqa: F401,F403
except ImportError:
    pass
