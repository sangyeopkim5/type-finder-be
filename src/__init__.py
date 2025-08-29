"""
src package init
================

Exposes key functions and classes for Manion CAS-Compiler.
Ensures stable imports even if underlying client function names evolve.
"""

import os
from pathlib import Path

__all__ = [
    "load_system_prompt",
    "infer_routing",
    "call_manion_model",
    "call_gpt4o",          # alias for backward compatibility
    "ManionCASCompiler",
    "run_sympy_steps",
]

# ------------------------
# System prompt loader
# ------------------------
def load_system_prompt() -> str:
    """
    Load system prompt text from prompts/system_prompt.txt.
    Falls back to a minimal placeholder if file missing.
    """
    here = Path(__file__).resolve().parent
    prompt_path = here.parent / "prompts" / "system_prompt.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return "You are Manion CAS-Compiler. Always output strict JSON."

# ------------------------
# Router
# ------------------------
try:
    from .router import infer_routing
except Exception:
    def infer_routing(*args, **kwargs):
        raise ImportError("router.py not found or failed to import.")

# ------------------------
# GPT client
# ------------------------
try:
    from .client_gpt import call_manion_model
    # backward compatibility alias
    call_gpt4o = call_manion_model
except Exception:
    def call_manion_model(*args, **kwargs):
        raise ImportError("client_gpt.py not found or failed to import.")
    call_gpt4o = call_manion_model

# ------------------------
# Compiler
# ------------------------
try:
    from .compiler import ManionCASCompiler
except Exception:
    class ManionCASCompiler:
        def __init__(self, *args, **kwargs):
            raise ImportError("compiler.py not found or failed to import.")

# ------------------------
# Executor
# ------------------------
try:
    from .executor import run_sympy_steps
except Exception:
    def run_sympy_steps(*args, **kwargs):
        raise ImportError("executor.py not found or failed to import.")
