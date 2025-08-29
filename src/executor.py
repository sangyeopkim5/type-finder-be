"""
executor.py
===========

Execute SymPy code steps from GPT-4o TOT JSON output.

Purpose
-------
- Run each step's sympy_code in isolated namespace
- Collect results for inspection or further verification
- Print execution log for debugging

Usage
-----
from src.executor import run_sympy_steps

results = run_sympy_steps(result_json)
"""

from __future__ import annotations
from typing import Any, Dict, List


def run_sympy_steps(result_json: Dict[str, Any]) -> Dict[str, List[Any]]:
    """
    Execute all sympy_code snippets from branches.

    Parameters
    ----------
    result_json : dict
        JSON result returned by GPT-4o.

    Returns
    -------
    dict
        { branch_id: [step_results...] }
    """
    branch_results: Dict[str, List[Any]] = {}

    for branch in result_json.get("branches", []):
        bid = branch.get("branch_id", "unknown")
        strategy = branch.get("strategy", "")
        print(f"\n=== Executing {bid} ({strategy}) ===")

        branch_results[bid] = []
        for step in branch.get("steps", []):
            sid = step.get("step_id", "?")
            desc = step.get("description", "")
            code = step.get("sympy_code", "")

            print(f"\n-- Step {sid}: {desc}")
            try:
                ns: Dict[str, Any] = {}
                exec(code, {}, ns)  # execute in isolated namespace
                result_val = ns.get("result", None)
                branch_results[bid].append(result_val)
                print("Result:", result_val)
            except Exception as e:
                branch_results[bid].append(f"ERROR: {e}")
                print("Execution error:", e)

    return branch_results
