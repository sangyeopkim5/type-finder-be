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
import sympy as sp
import signal

# 1. Allowed function whitelist
ALLOWED_FUNCS = {
    "simplify","expand","factor","collect","cancel","together","apart",
    "Eq","solve","solveset","linsolve","reduce_inequalities",
    "diff","integrate","limit","series",
    "Matrix","det","rref","eigenvals",
    "sqrt","Rational","nsimplify","N","radsimp",
    "Interval","FiniteSet","Union","Intersection","EmptySet"
}

# 2. Alias mapping
ALIAS = {
    "evaluate": "N",
    "rationalize": "radsimp",
    "combine_like_terms": "collect"
}

def timeout_handler(signum, frame):
    raise TimeoutError("CAS execution timed out")

def execute_cas_step(cas_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single CAS step safely.
    """
    fn = cas_spec.get("fn")
    args = cas_spec.get("args", [])
    kwargs = cas_spec.get("kwargs", {})

    # Alias normalization
    if fn in ALIAS:
        fn = ALIAS[fn]

    # Whitelist check
    if fn not in ALLOWED_FUNCS:
        return {"ok": False, "error": f"Disallowed CAS function: {fn}"}

    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(3)  # 3 second timeout

        sympy_fn = getattr(sp, fn)
        parsed_args = [sp.sympify(a) for a in args]
        result = sympy_fn(*parsed_args, **kwargs)

        signal.alarm(0)
        return {"ok": True, "result_str": str(result), "result_latex": sp.latex(result)}

    except Exception as e:
        return {"ok": False, "error": str(e)}

def run_sympy_steps(result_json: Dict[str, Any]) -> Dict[str, List[Any]]:
    """
    Execute all CAS steps from branches in GPT-4o output JSON.
    """
    branch_results: Dict[str, List[Any]] = {}

    for branch in result_json.get("branches", []):
        bid = branch.get("branch_id", "unknown")
        strategy = branch.get("strategy", "")
        print(f"\n=== Executing {bid} ({strategy}) ===")

        branch_results[bid] = []
        for step in branch.get("steps", []):
            sid = step.get("step_id", "?")
            label = step.get("label", "")
            cas_spec = step.get("cas", {})

            print(f"\n-- Step {sid}: {label}")
            exec_res = execute_cas_step(cas_spec)
            branch_results[bid].append(exec_res)
            print("Exec result:", exec_res)

    return branch_results
