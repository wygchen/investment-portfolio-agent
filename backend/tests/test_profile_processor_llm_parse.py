import json
import types
import os
import sys

# Ensure project root is on sys.path when running tests directly from backend/tests
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, os.pardir, os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pytest


def test_llm_parse_specific_assets_monkeypatched(monkeypatch):
    # Import target after monkeypatching to avoid caching issues if needed
    import importlib
    module = importlib.import_module("backend.profile_processor_agent")

    # Ensure LLM is considered available
    monkeypatch.setattr(module, "_LLM_AVAILABLE", True, raising=False)

    # Create a fake LLM object with an invoke method returning desired JSON
    class FakeResponse:
        def __init__(self, content: str):
            self.content = content

    class FakeLLM:
        def invoke(self, messages):
            # Simulate the model correcting misspelling and ignoring non-tickers like 'pear'
            payload = {
                "tickers": ["AAPL", "TSLA"],
                "asset_classes": ["equities"],
            }
            return FakeResponse(json.dumps(payload))

    # Monkeypatch the LLM factory to return our fake LLM
    def fake_create_watsonx_llm(**kwargs):
        return FakeLLM()

    monkeypatch.setattr(module, "create_watsonx_llm", fake_create_watsonx_llm, raising=False)

    # Now call the function under test
    tickers, asset_classes = module._llm_parse_specific_assets("appple, tesla, pear")

    assert tickers == ["AAPL", "TSLA"]
    # asset_classes should include 'equities'
    assert asset_classes == ["equities"]


