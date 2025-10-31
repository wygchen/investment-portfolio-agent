"""
Monte Carlo Simulation Engine for Portfolio Projections

This module implements Monte Carlo simulation for portfolio value projections
using historical data and statistical models.
"""

import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class MonteCarloEngine:
    """
    Monte Carlo simulation engine for portfolio projections.
    
    Simulates future portfolio values based on historical returns and volatility,
    accounting for expected returns, volatility, and market randomness.
    """
    
    def __init__(self, initial_value: float = 100000, num_simulations: int = 10000):
        """
        Initialize the Monte Carlo engine.
        
        Args:
            initial_value: Starting portfolio value
            num_simulations: Number of simulations to run
        """
        self.initial_value = initial_value
        self.num_simulations = num_simulations
        self.random_seed = None
        
    def run_simulation(
        self,
        expected_return: float,
        volatility: float,
        time_horizon_years: int = 10,
        monthly_deposits: float = 0
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for portfolio projections.
        
        Args:
            expected_return: Annual expected return (as decimal, e.g., 0.08 for 8%)
            volatility: Annual volatility (as decimal, e.g., 0.15 for 15%)
            time_horizon_years: Years to project forward
            monthly_deposits: Monthly contributions (optional)
            
        Returns:
            Dictionary with simulation results including percentiles and statistics
        """
        try:
            # Set random seed for reproducibility
            if self.random_seed:
                np.random.seed(self.random_seed)
            
            # Convert annual values to monthly
            months = time_horizon_years * 12
            monthly_return = expected_return / 12
            monthly_vol = volatility / np.sqrt(12)  # Annual to monthly volatility
            
            # Initialize results array
            final_values = np.zeros(self.num_simulations)
            
            # Run simulations
            for sim in range(self.num_simulations):
                value = self.initial_value
                
                # Simulate each month
                for month in range(months):
                    # Generate random return from normal distribution
                    random_shock = np.random.normal(monthly_return, monthly_vol)
                    
                    # Apply return
                    value = value * (1 + random_shock)
                    
                    # Add monthly deposits at the end of the month
                    if monthly_deposits > 0:
                        value += monthly_deposits
                
                final_values[sim] = value
            
            # Calculate statistics
            percentiles = self._calculate_percentiles(final_values)
            statistics = self._calculate_statistics(final_values)
            
            return {
                "success": True,
                "initial_value": self.initial_value,
                "num_simulations": self.num_simulations,
                "time_horizon_years": time_horizon_years,
                "expected_return": expected_return,
                "volatility": volatility,
                "percentiles": percentiles,
                "statistics": statistics,
                "final_values": final_values.tolist()  # Convert to list for JSON serialization
            }
            
        except Exception as e:
            logger.error(f"Error running Monte Carlo simulation: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_percentiles(self, final_values: np.ndarray) -> Dict[str, float]:
        """Calculate percentile values from simulation results."""
        return {
            "5th": float(np.percentile(final_values, 5)),
            "10th": float(np.percentile(final_values, 10)),
            "25th": float(np.percentile(final_values, 25)),
            "50th": float(np.percentile(final_values, 50)),  # Median
            "75th": float(np.percentile(final_values, 75)),
            "90th": float(np.percentile(final_values, 90)),
            "95th": float(np.percentile(final_values, 95))
        }
    
    def _calculate_statistics(self, final_values: np.ndarray) -> Dict[str, float]:
        """Calculate statistical metrics from simulation results."""
        mean = np.mean(final_values)
        std = np.std(final_values)
        
        # Calculate probability of reaching certain targets
        # Using initial value as baseline for comparison
        prob_break_even = float(np.mean(final_values >= self.initial_value))
        prob_double = float(np.mean(final_values >= self.initial_value * 2))
        prob_half = float(np.mean(final_values <= self.initial_value * 0.5))
        
        return {
            "mean": float(mean),
            "median": float(np.median(final_values)),
            "std_dev": float(std),
            "min": float(np.min(final_values)),
            "max": float(np.max(final_values)),
            "probability_break_even": prob_break_even,
            "probability_double": prob_double,
            "probability_half": prob_half
        }
    
    def estimate_portfolio_metrics(
        self,
        tickers: List[str],
        weights: Optional[List[float]] = None,
        lookback_years: int = 5
    ) -> Dict[str, float]:
        """
        Estimate expected return and volatility from historical data.
        
        Args:
            tickers: List of stock tickers
            weights: Portfolio weights (optional, defaults to equal weight)
            lookback_years: Years of historical data to use
            
        Returns:
            Dictionary with expected_return and volatility estimates
        """
        try:
            if weights is None:
                weights = [1.0 / len(tickers)] * len(tickers)
            
            if len(weights) != len(tickers):
                raise ValueError("Number of weights must match number of tickers")
            
            # Download historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_years * 365)
            
            logger.info(f"Downloading historical data for {tickers}")
            
            # Get price data for all tickers
            prices = yf.download(tickers, start=start_date, end=end_date, progress=False)
            
            if prices.empty:
                logger.warning("No historical data available, using default values")
                return {
                    "expected_return": 0.08,
                    "volatility": 0.15
                }
            
            # Calculate returns
            if 'Close' in prices.columns:
                # Multiple tickers
                returns = prices['Close'].pct_change().dropna()
            else:
                # Single ticker
                returns = prices.pct_change().dropna()
            
            # Calculate portfolio returns (weighted average)
            if isinstance(returns, pd.DataFrame):
                portfolio_returns = (returns * weights).sum(axis=1)
            else:
                portfolio_returns = returns
            
            # Annualize metrics
            expected_return = float(portfolio_returns.mean() * 252)  # Trading days
            volatility = float(portfolio_returns.std() * np.sqrt(252))
            
            logger.info(f"Estimated return: {expected_return:.2%}, volatility: {volatility:.2%}")
            
            return {
                "expected_return": expected_return,
                "volatility": volatility
            }
            
        except Exception as e:
            logger.error(f"Error estimating portfolio metrics: {str(e)}")
            # Return conservative defaults
            return {
                "expected_return": 0.07,
                "volatility": 0.15
            }


def run_monte_carlo_for_portfolio(
    tickers: List[str],
    weights: Optional[List[float]] = None,
    initial_value: float = 100000,
    time_horizon_years: int = 10,
    num_simulations: int = 10000,
    monthly_deposits: float = 0
) -> Dict[str, Any]:
    """
    Convenience function to run Monte Carlo simulation for a portfolio.
    
    Args:
        tickers: List of stock tickers
        weights: Portfolio weights (optional)
        initial_value: Starting portfolio value
        time_horizon_years: Years to project
        num_simulations: Number of simulations
        monthly_deposits: Monthly contributions
        
    Returns:
        Complete Monte Carlo results dictionary
    """
    engine = MonteCarloEngine(initial_value=initial_value, num_simulations=num_simulations)
    
    # Estimate metrics from historical data
    metrics = engine.estimate_portfolio_metrics(tickers, weights)
    
    # Run simulation
    results = engine.run_simulation(
        expected_return=metrics["expected_return"],
        volatility=metrics["volatility"],
        time_horizon_years=time_horizon_years,
        monthly_deposits=monthly_deposits
    )
    
    # Add the metrics used
    if results.get("success"):
        results["estimated_metrics"] = metrics
    
    return results
