import logging
import sys
import os

# Ensure backend is on sys.path when run from backend folder
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

# Ensure stdout logging
logging.basicConfig(level=logging.INFO)

print("=== run_selection_debug.py ===")
print(f"cwd: {os.getcwd()}")
print("sys.path head:")
for p in sys.path[:5]:
    print(" -", p)

try:
    from selection.selection_agent import run_selection_agent
    print("Imported run_selection_agent from selection.selection_agent")
except Exception as e:
    print("FAILED to import selection.selection_agent:", e)
    print("Attempting to install missing dependencies (langgraph) for debug...")
    try:
        import subprocess, sys as _sys
        subprocess.check_call([_sys.executable, '-m', 'pip', 'install', 'langgraph'])
        from selection.selection_agent import run_selection_agent
        print("Imported run_selection_agent after installing langgraph")
    except Exception as ee:
        print("Still failed to import selection.selection_agent:", ee)
        raise

# Minimal call
res = run_selection_agent(regions=['US'], sectors=['Information Technology'], selected_tickers={'bonds': ['BND']})
print("success:", res.get('success'))
print("keys:", list(res.keys()))
print("processing_summary:", res.get('processing_summary'))
print("final_selections keys:", list(res.get('final_selections', {}).keys()))

print("=== end run_selection_debug.py ===")
