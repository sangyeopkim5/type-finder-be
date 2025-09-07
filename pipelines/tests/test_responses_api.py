import types
from apps.codegen import codegen

class DummyClient:
    def __init__(self):
        self.kwargs = None
        class Responses:
            def __init__(self, outer):
                self.outer = outer
            def create(self, **kwargs):
                self.outer.kwargs = kwargs
                return types.SimpleNamespace()
        self.responses = Responses(self)

def test_response_format_included():
    client = DummyClient()
    codegen._responses_create_with_retry(
        client,
        model="gpt-5",
        messages=[],
        max_tokens=1,
    )
    assert client.kwargs["response_format"] == {"type": "text"}
    assert "modalities" not in client.kwargs

