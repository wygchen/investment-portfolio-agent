"""
Configuration Module for Equity Selection Agent (ESA) V1.0

This module defines all static and adjustable parameters including:
- Universe Index configuration
- Target ticker count
- Risk and quality thresholds
- Technical analysis parameters
- Factor weights for composite scoring
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass
import os


@dataclass
class UniverseConfig:
    """Configuration for equity universe definition"""
    # US Market Configuration
    us_index: str = "SP500"  # S&P 500 components
    
    # HK Market Configuration (placeholder for future expansion)
    hk_index: Optional[str] = None  # To be defined
    
    # Data file paths
    universe_file: str = "data/full_universe_tickers.csv"
    
    # Caching configuration
    fundamental_refresh_days: int = 7  # Weekly refresh for fundamental data
    price_refresh_days: int = 1  # Daily refresh for price data


@dataclass
class ScreeningThresholds:
    """Quantitative screening thresholds for the layered filtering approach"""
    
    # Quality and Efficiency Thresholds
    min_roe: float = 0.05  # Minimum 5% Return on Equity (more reasonable threshold)
    # Note: Positive equity filter removed since we don't have balance sheet data
    
    # Risk and Leverage Thresholds
    max_debt_equity_absolute: float = 1.5  # Maximum D/E ratio for non-financials
    max_beta: float = 1.8  # Maximum market risk tolerance
    debt_equity_zscore_threshold: float = 0.0  # Peer-relative D/E screening
    
    # Valuation Thresholds
    pe_zscore_threshold: float = 0.0  # Must be cheaper than sector average
    max_pe_absolute: float = 40.0  # Absolute P/E cap to avoid extreme outliers
    
    # Technical Analysis Thresholds
    max_rsi_overbought: float = 70.0  # RSI overbought threshold
    require_positive_trend: bool = True  # Price > SMA 50 or bullish MACD


@dataclass
class TechnicalParameters:
    """Parameters for technical analysis indicators using pandas-ta"""
    
    # Moving Average Convergence Divergence (MACD)
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    
    # Relative Strength Index (RSI)
    rsi_period: int = 14
    
    # Bollinger Bands
    bb_period: int = 20
    bb_std: float = 2.0
    
    # Simple Moving Averages
    sma_short: int = 50
    sma_long: int = 200
    
    # Historical data lookback for technical analysis
    lookback_period: str = "1y"  # One year for long-term indicators


@dataclass
class CompositeScoreWeights:
    """Weights for calculating the final composite score (Σ weights = 1.0)"""
    
    # Value Factor Weight (P/E, P/B Z-scores)
    w_value: float = 0.25
    
    # Quality Factor Weight (ROE)
    w_quality: float = 0.20
    
    # Risk Factor Weight (Beta, D/E - inverse scoring)
    w_risk: float = 0.20
    
    # Momentum Factor Weight (Technical indicators)
    w_momentum: float = 0.20
    
    # Qualitative Factor Weight (LLM-derived score)
    w_qualitative: float = 0.15
    
    def __post_init__(self):
        """Validate that weights sum to 1.0"""
        total = self.w_value + self.w_quality + self.w_risk + self.w_momentum + self.w_qualitative
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Composite score weights must sum to 1.0, got {total}")


@dataclass
class OutputConfig:
    """Configuration for agent output and reporting"""
    
    # Target number of selected stocks for shortlist
    target_stock_count: int = 25
    
    # Logging configuration
    log_directory: str = "../logs"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level: str = "INFO"
    
    # Output format
    output_format: str = "JSON"  # JSON or CSV
    include_audit_trail: bool = True
    
    # Sample exclusion logging (for debugging)
    log_sample_exclusions: int = 5  # Log first N exclusions per layer


class Config:
    """Main configuration class for the Equity Selection Agent"""
    
    def __init__(self, 
                 universe_config: Optional[UniverseConfig] = None,
                 screening_thresholds: Optional[ScreeningThresholds] = None,
                 technical_parameters: Optional[TechnicalParameters] = None,
                 score_weights: Optional[CompositeScoreWeights] = None,
                 output_config: Optional[OutputConfig] = None):
        
        self.universe = universe_config or UniverseConfig()
        self.screening = screening_thresholds or ScreeningThresholds()
        self.technical = technical_parameters or TechnicalParameters()
        self.weights = score_weights or CompositeScoreWeights()
        self.output = output_config or OutputConfig()
        
        # Validate configuration
        self.validate_config()
    
    def validate_config(self):
        """Validate configuration parameters"""
        # Ensure positive thresholds where applicable
        assert self.screening.min_roe > 0, "ROE threshold must be positive"
        assert self.screening.max_debt_equity_absolute > 0, "D/E threshold must be positive"
        assert self.screening.max_beta > 0, "Beta threshold must be positive"
        assert self.output.target_stock_count > 0, "Target stock count must be positive"
        
        # Ensure technical parameters are sensible
        assert self.technical.macd_fast < self.technical.macd_slow, "MACD fast period must be < slow period"
        assert 0 < self.technical.rsi_period <= 50, "RSI period should be between 1-50"
        assert self.technical.sma_short < self.technical.sma_long, "Short SMA must be < long SMA"
    
    def get_sector_specific_thresholds(self, sector: str) -> Dict[str, float]:
        """
        Get sector-specific threshold adjustments
        
        Args:
            sector: Sector name from yfinance
            
        Returns:
            Dictionary of adjusted thresholds for the specific sector
        """
        # Sector-specific adjustments (can be expanded)
        sector_adjustments = {
            "Financial Services": {
                "max_debt_equity_absolute": 3.0,  # Banks naturally have higher leverage
                "min_roe": 0.12  # Slightly lower ROE expectation for financials
            },
            "Utilities": {
                "max_debt_equity_absolute": 2.5,  # Utilities typically carry more debt
                "max_beta": 1.2  # Utilities are generally less volatile
            },
            "Technology": {
                "max_pe_absolute": 60.0,  # Tech stocks can have higher P/E ratios
                "min_roe": 0.20  # Higher ROE expectation for tech companies
            },
            "Real Estate": {
                "max_debt_equity_absolute": 2.0,  # REITs often have higher leverage
                "min_roe": 0.10  # Lower ROE expectation for REITs
            }
        }
        
        # Return base thresholds with sector-specific adjustments
        base_thresholds = {
            "max_debt_equity_absolute": self.screening.max_debt_equity_absolute,
            "min_roe": self.screening.min_roe,
            "max_pe_absolute": self.screening.max_pe_absolute,
            "max_beta": self.screening.max_beta
        }
        
        if sector in sector_adjustments:
            base_thresholds.update(sector_adjustments[sector])
        
        return base_thresholds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        return {
            "universe": self.universe.__dict__,
            "screening": self.screening.__dict__,
            "technical": self.technical.__dict__,
            "weights": self.weights.__dict__,
            "output": self.output.__dict__
        }


# Default configuration instance
default_config = Config()


def load_config_from_env() -> Config:
    """Load configuration with environment variable overrides"""
    config = Config()
    
    # Override with environment variables if present
    if os.getenv("ESA_TARGET_STOCKS"):
        config.output.target_stock_count = int(os.getenv("ESA_TARGET_STOCKS", "25"))
    
    if os.getenv("ESA_MIN_ROE"):
        config.screening.min_roe = float(os.getenv("ESA_MIN_ROE", "0.05"))
    
    if os.getenv("ESA_MAX_BETA"):
        config.screening.max_beta = float(os.getenv("ESA_MAX_BETA", "1.8"))
    
    # Weight overrides
    if os.getenv("ESA_WEIGHT_VALUE"):
        config.weights.w_value = float(os.getenv("ESA_WEIGHT_VALUE", "0.25"))
    
    if os.getenv("ESA_WEIGHT_QUALITY"):
        config.weights.w_quality = float(os.getenv("ESA_WEIGHT_QUALITY", "0.20"))
    
    if os.getenv("ESA_WEIGHT_RISK"):
        config.weights.w_risk = float(os.getenv("ESA_WEIGHT_RISK", "0.20"))
    
    if os.getenv("ESA_WEIGHT_MOMENTUM"):
        config.weights.w_momentum = float(os.getenv("ESA_WEIGHT_MOMENTUM", "0.20"))
    
    if os.getenv("ESA_WEIGHT_QUALITATIVE"):
        config.weights.w_qualitative = float(os.getenv("ESA_WEIGHT_QUALITATIVE", "0.15"))
    
    # Re-validate after environment overrides
    try:
        config.validate_config()
    except Exception as e:
        print(f"Warning: Configuration validation failed after environment overrides: {e}")
    
    return config