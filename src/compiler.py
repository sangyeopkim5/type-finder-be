"""
compiler.py
===========

Core compiler orchestration:
1) Routing decision (need_image?)
2) Auto-attach image_path (search Probleminput recursively)
3) GPT call (text-only → gpt-4o-mini, multimodal → gpt-4o)
4) Save JSON result

Usage
-----
from src.compiler import ManionCASCompiler
result = ManionCASCompiler().compile(segments_json, {"problem_id":"ex-001"})
"""

from __future__ import annotations
import os
import json
from typing import Any, Dict, List
from pathlib import Path

from .router import infer_routing
from .client_gpt import call_manion_model


class ManionCASCompiler:
    def __init__(self, output_dir: str = "output_results", input_dir: str = "Probleminput") -> None:
        self.output_dir = Path(output_dir)
        self.input_dir = Path(input_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _find_image(self, stem: str) -> str | None:
        """
        Find an image file matching problem_id (stem) under input_dir recursively.
        Priority: top-level match first, then first match in subtree.
        """
        exts = (".jpg", ".jpeg", ".png")
        # Top-level
        for ext in exts:
            p = self.input_dir / f"{stem}{ext}"
            if p.exists():
                return str(p.resolve())
        # Recursive search
        for ext in exts:
            for p in self.input_dir.rglob(f"{stem}{ext}"):
                return str(p.resolve())
        return None

    def compile(self, segments_json: List[Dict[str, Any]], problem_meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compile math problem into a strict JSON (TOT branches + SymPy steps).

        Parameters
        ----------
        segments_json : list[dict]
        problem_meta  : dict  (must include "problem_id")

        Returns
        -------
        dict : JSON result from the model
        """
        if "problem_id" not in problem_meta:
            raise ValueError("problem_meta must include 'problem_id'.")

        problem_id = problem_meta["problem_id"]

        # 1) Routing (if no hint provided)
        if "router_hint" not in problem_meta:
            problem_meta["router_hint"] = infer_routing(segments_json)

        routing = problem_meta["router_hint"]
        need_image = bool(routing.get("need_image"))

        # 2) Attach image if needed and not provided
        if need_image and not problem_meta.get("image_path"):
            img_path = self._find_image(problem_id)
            if img_path:
                problem_meta["image_path"] = img_path

        # 3) Call model with appropriate mode (text-only vs multimodal)
        result_json = call_manion_model(
            segments_json,
            problem_meta,
            need_image=need_image,
            # You can override models here if needed:
            model_text="gpt-4o-mini",  # default text-only
            model_vision="gpt-4o",     # multimodal when image used
            temperature=0.0,
        )

        # 4) Save result JSON
        out_path = self.output_dir / f"{problem_id}_result.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result_json, f, ensure_ascii=False, indent=2)

        return result_json
