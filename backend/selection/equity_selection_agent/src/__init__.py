"""
Equity Selection Agent (ESA) - Core Modules

This package contains the core components for the equity selection agent:
- stock_universe: Universe management and data fetching
- stock_database: Enhanced SQLite-based data provider
- collect_data: Data collection script
- feature_engine: Feature engineering utilities
- selector_logic: Stock selection algorithms
"""

# Import core classes to make them available at package level
try:
    from .stock_universe import TickerManager, StockDataFetcher
    from .stock_database import StockDatabase
except ImportError:
    # Fallback imports for direct script execution
    import sys
    import os
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    try:
        from stock_universe import TickerManager, StockDataFetcher
        from stock_database import StockDatabase
    except ImportError as e:
        # If still failing, provide informative error
        import warnings
        warnings.warn(f"Could not import core modules: {e}")

# Package metadata
__version__ = "1.0.0"
__author__ = "ESA Development Team"

# Export main classes
__all__ = [
    'TickerManager',
    'StockDataFetcher', 
    'StockDatabase'
]
