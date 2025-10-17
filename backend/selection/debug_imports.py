import os
import sys
import traceback

# Ensure parent (backend) directory is on sys.path when running from selection/
_here = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(_here)
if _parent not in sys.path:
    sys.path.insert(0, _parent)

print("=== debug_imports.py ===")
print(f"CWD: {os.getcwd()}")
print("sys.path (first 10):")
for p in sys.path[:10]:
    print(f" - {p}")

print("\nAttempting import: selection.equity_selection_agent.src.equity_selection_agent")
try:
    import importlib
    mod = importlib.import_module('selection.equity_selection_agent.src.equity_selection_agent')
    print("OK: imported selection.equity_selection_agent.src.equity_selection_agent")
    print(f"Module file: {getattr(mod, '__file__', 'unknown')}")
except Exception as e:
    print("FAIL: selection.equity_selection_agent.src.equity_selection_agent")
    traceback.print_exc()

print("\nAttempting import: selection.equity_selection_agent.src.config")
try:
    import importlib
    cfg = importlib.import_module('selection.equity_selection_agent.src.config')
    print("OK: imported selection.equity_selection_agent.src.config")
    print(f"Module file: {getattr(cfg, '__file__', 'unknown')}")
except Exception:
    print("FAIL: selection.equity_selection_agent.src.config")
    traceback.print_exc()

print("\nAttempting relative import via package execution check")
try:
    from selection.equity_selection_agent.src import config as _cfg
    print("OK: package-level import of config")
    print(getattr(_cfg, '__file__', 'unknown'))
except Exception:
    print("FAIL: package-level import of config")
    traceback.print_exc()

print("=== end debug_imports.py ===")
