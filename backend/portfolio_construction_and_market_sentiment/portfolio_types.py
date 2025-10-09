from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np


@dataclass
class PortfolioResult:
    tickers: List[str]
    weights: List[float]
    covariance_matrix: Optional[np.ndarray] = None
    expected_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    risk_free_rate: float = 0.0
    weights_map: Optional[Dict[str, float]] = None      # dictionary storing all weights and its final weight mapping e.g. {"AAPL": 0.3, ...}
    asset_class_allocations: Optional[Dict[str, float]] = None  # allocation summed by asset class

    def to_dict(self) -> Dict[str, object]:
        cov = None
        if self.covariance_matrix is not None:
            try:
                cov = self.covariance_matrix.tolist()
            except Exception:
                try:
                    cov = getattr(self.covariance_matrix, 'values', None)
                    if cov is not None:
                        cov = cov.tolist()
                except Exception:
                    cov = None

        return {
            "tickers": list(self.tickers),
            "weights": list(self.weights),
            "covariance_matrix": cov,
            "expected_return": float(self.expected_return),
            "volatility": float(self.volatility),
            "sharpe_ratio": float(self.sharpe_ratio),
            "risk_free_rate": float(self.risk_free_rate),
            "weights_map": dict(self.weights_map) if self.weights_map is not None else None,
            "asset_class_allocations": dict(self.asset_class_allocations) if self.asset_class_allocations is not None else None,
        }
