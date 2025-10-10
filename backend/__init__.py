"""Backend package initializer.

Ensures the `backend` directory is treated as a Python package so absolute
imports like `backend.profile_processor_agent` resolve reliably across
environments and runners.
"""

from __future__ import annotations

from importlib import import_module
from typing import List

# Package version
__version__ = "0.1.0"

# Expose commonly used submodules at package level for convenience, e.g.:
#   from backend import profile_processor_agent
_optional_modules: List[str] = [
    "profile_processor_agent",
    "main_agent",
    "communication_agent",
    "watsonx_utils",
    "selection",
    "services",
]

for _name in _optional_modules:
    try:
        globals()[_name] = import_module(f"{__name__}.{_name}")
    except Exception:
        # Optional dependency/submodule may not be available in some environments
        # (e.g., CI without certain extras). Fail softly to keep package importable.
        pass

__all__ = [
    "__version__",
    *[n for n in _optional_modules if n in globals()],
]


