import pathlib, sys
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

import types
import pytest
from apps.codegen import codegen
from libs.schemas import ProblemDoc, OCRItem


class DummyResp:
    choices = [
        types.SimpleNamespace(
            message=types.SimpleNamespace(
                content="print('x [[CAS:a:1+1]]')\n---CAS-JOBS---\n[[CAS:a:1+1]]"
            )
        )
    ]


def test_codegen_sort_and_parse(monkeypatch):
    called = {}

    def fake_order(items):
        called["ordered"] = items
        return list(reversed(items))

    def fake_chat(client, **kw):
        return DummyResp()

    def fake_sys(with_image):
        called["with_image"] = with_image
        return ""

    monkeypatch.setattr(codegen, "reading_order", fake_order)
    monkeypatch.setattr(codegen, "_chat_completion_with_retry", fake_chat)
    monkeypatch.setattr(codegen, "_sys_text", fake_sys)
    monkeypatch.setattr(codegen, "get_openai_client", lambda: object())

    doc = ProblemDoc(
        items=[
            OCRItem(bbox=[1, 0, 2, 1], category="Text"),
            OCRItem(bbox=[0, 0, 1, 1], category="Picture"),
        ]
    )
    res = codegen.generate_manim(doc)
    assert "ordered" in called
    assert called["with_image"] is True
    assert res.cas_jobs[0]["id"] == "a"
    assert "[[CAS:a]]" in res.manim_code_draft


def test_codegen_no_cas_block(monkeypatch):
    """When the CAS block is missing the function should return empty jobs."""

    monkeypatch.setattr(codegen, "reading_order", lambda x: x)
    monkeypatch.setattr(codegen, "get_openai_client", lambda: object())

    class Resp:
        choices = [types.SimpleNamespace(message=types.SimpleNamespace(content="print('hi')"))]

    monkeypatch.setattr(codegen, "_chat_completion_with_retry", lambda *a, **k: Resp())
    doc = ProblemDoc(items=[OCRItem(bbox=[0, 0, 1, 1], category="Text")])
    res = codegen.generate_manim(doc)
    assert res.cas_jobs == []
    assert res.manim_code_draft.strip() == "print('hi')"
