import os
import sys
import types
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pytest


def _import_equity_selection_agent():
    """Import the equity_selection_agent module from the src directory.

    This adjusts sys.path at runtime so tests work without altering the package layout.
    """
    tests_dir = Path(__file__).resolve().parent
    src_dir = (tests_dir / ".." / "selection" / "equity_selection_agent" / "src").resolve()
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    # Provide a lightweight stub for the qualitative_agent module to avoid importing
    # external dependencies during tests.
    if "qualitative_agent" not in sys.modules:
        qa_module = types.ModuleType("qualitative_agent")

        class QualitativeAnalysisAgent:  # minimal stub used only for import resolution
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                pass

            def analyze_company(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
                return {"qualitative_score": 0.1, "notes": "stub"}

        setattr(qa_module, "QualitativeAnalysisAgent", QualitativeAnalysisAgent)
        sys.modules["qualitative_agent"] = qa_module
    import equity_selection_agent as esa  # type: ignore
    return esa


class DummyOutput:
    def __init__(self, target_stock_count: int = 2):
        self.target_stock_count = target_stock_count
        self.log_level = "INFO"
        self.log_format = "%(asctime)s - %(levelname)s - %(message)s"
        self.log_directory = "."


class DummyConfig:
    def __init__(self, target_stock_count: int = 2):
        self.output = DummyOutput(target_stock_count=target_stock_count)


def _dummy_universe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"ticker": "AAA", "sector": "Tech", "region": "US"},
            {"ticker": "BBB", "sector": "Tech", "region": "US"},
            {"ticker": "CCC", "sector": "Finance", "region": "US"},
        ]
    )


def _dummy_fundamentals(tickers: List[str]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for i, t in enumerate(tickers):
        rows.append({"ticker": t, "revenue": 1000 + i * 10, "eps": 5 + i})
    return pd.DataFrame(rows)


def test_equity_selection_agent_happy_path(monkeypatch: pytest.MonkeyPatch):
    esa = _import_equity_selection_agent()

    # 1) Stub data availability and loading
    monkeypatch.setattr(esa, "ensure_data_available", lambda max_age_hours=24: True)
    monkeypatch.setattr(esa, "get_universe", lambda: _dummy_universe())

    def _dummy_price_data(_tickers: List[str]) -> pd.DataFrame:
        # Minimal placeholder; real values aren't used by our dummy analyzer
        return pd.DataFrame({"date": ["2024-01-01", "2024-01-02"], "AAA": [10, 11], "BBB": [20, 21]})

    monkeypatch.setattr(esa, "get_price_data", _dummy_price_data)
    monkeypatch.setattr(esa, "get_fundamental_data", lambda tickers: _dummy_fundamentals(tickers))

    # 2) Stub feature engine
    class DummyFundamentalCalculator:
        def __init__(self, _config: Any):
            pass

        def process_fundamental_data(self, fundamental_data: Dict[str, Any], universe_df: pd.DataFrame) -> pd.DataFrame:
            # Build a small features df keyed by ticker
            return pd.DataFrame({
                "ticker": universe_df["ticker"].tolist(),
                "fundamental_score": [0.6] * len(universe_df),
            })

    class DummyTechnicalAnalyzer:
        def __init__(self, _config: Any):
            pass

        def process_technical_data(self, price_data: pd.DataFrame) -> pd.DataFrame:
            cols = [c for c in price_data.columns if c not in {"date"}]
            return pd.DataFrame({
                "ticker": cols,
                "technical_score": [0.4] * len(cols),
            })

    def dummy_calculate_composite_features(fundamental_features: pd.DataFrame, technical_features: pd.DataFrame) -> pd.DataFrame:
        return fundamental_features.merge(technical_features, on="ticker", how="inner")

    monkeypatch.setattr(esa, "FundamentalCalculator", DummyFundamentalCalculator)
    monkeypatch.setattr(esa, "TechnicalAnalyzer", DummyTechnicalAnalyzer)
    monkeypatch.setattr(esa, "calculate_composite_features", dummy_calculate_composite_features)

    # 3) Stub screening
    class DummyScreener:
        def __init__(self, _config: Any):
            self._summary = {"filters_applied": 1, "survivors": 2}

        def apply_full_screening_pipeline(self, combined: pd.DataFrame) -> pd.DataFrame:
            # Keep only Tech tickers present in combined
            keep = combined[combined["ticker"].isin(["AAA", "BBB"])]
            return keep.reset_index(drop=True)

        def add_qualitative_scores(self, screened: pd.DataFrame, _fundamental_data: Dict[str, Any]) -> pd.DataFrame:
            screened["qualitative_score"] = 0.1
            return screened

        def get_screening_summary(self) -> Dict[str, Any]:
            return self._summary

    monkeypatch.setattr(esa, "EquityScreener", DummyScreener)

    # 4) Stub ranking engine
    class DummyRankingEngine:
        def __init__(self, _config: Any):
            pass

        def calculate_composite_score(self, df: pd.DataFrame) -> pd.DataFrame:
            df = df.copy()
            df["final_score"] = df["fundamental_score"] + df["technical_score"] + df.get("qualitative_score", 0)
            return df

        def rank_candidates(self, df: pd.DataFrame) -> pd.DataFrame:
            return df.sort_values("final_score", ascending=False).reset_index(drop=True)

        def select_top_candidates(self, df: pd.DataFrame) -> pd.DataFrame:
            return df.head(2).reset_index(drop=True)

    monkeypatch.setattr(esa, "RankingEngine", DummyRankingEngine)

    # Provide an explicit config to avoid depending on environment
    config = DummyConfig(target_stock_count=2)

    results = esa.run_agent_workflow(
        regions=["US"], sectors=["Tech"], force_refresh=False, config=config
    )

    assert results["success"] is True
    assert results["final_selection_count"] == 2
    assert "final_selections" in results
    assert isinstance(results["final_selections"], pd.DataFrame)
    assert results["final_selections"]["ticker"].tolist() == ["AAA", "BBB"]


