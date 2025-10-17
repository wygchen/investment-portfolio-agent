"""
Feature Engineering Module for Equity Selection Agent (ESA) V1.0

This module transforms raw data into standardized, actionable metrics used for 
filtering and ranking. Implements peer-relative Z-score calculations and technical analysis.

Classes:
- FundamentalCalculator: Computes financial ratios and peer-relative Z-scores
- TechnicalAnalyzer: Calculates technical indicators using pandas-ta
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any

from .config import Config

# Set up logging
logger = logging.getLogger(__name__)


class FundamentalCalculator:
    """
    Calculates core financial metrics and peer-relative Z-scores for systematic screening.
    
    Handles computation of:
    - Price-to-Earnings (P/E) Ratio and Z-Score
    - Return on Equity (ROE)
    - Debt-to-Equity (D/E) Ratio and Z-Score
    - Price-to-Book (P/B) Ratio
    - Price/Earnings-to-Growth (PEG) Ratio
    """
    
    def __init__(self, config: Config):
        self.config = config
    
    def calculate_pe_ratio(self, price: Optional[float], eps: Optional[float]) -> Optional[float]:
        """
        Calculate Price-to-Earnings ratio.
        
        Args:
            price: Current stock price
            eps: Earnings per share (trailing 12 months)
            
        Returns:
            P/E ratio or None if calculation not possible
        """
        if eps is None or eps <= 0 or price is None or price <= 0:
            return None
        
        return price / eps
    
    # Note: ROE, D/E, and P/B calculations removed since we use pre-calculated values from database
    
    def calculate_peg_ratio(self, pe_ratio: Optional[float], earnings_growth_rate: Optional[float]) -> Optional[float]:
        """
        Calculate Price/Earnings-to-Growth ratio.
        
        Args:
            pe_ratio: P/E ratio
            earnings_growth_rate: Expected earnings growth rate (as percentage)
            
        Returns:
            PEG ratio or None if calculation not possible
        """
        if (pe_ratio is None or earnings_growth_rate is None or 
            earnings_growth_rate <= 0 or pe_ratio <= 0):
            return None
        
        return pe_ratio / earnings_growth_rate
    
    def calculate_sector_zscore(self, value: Optional[float], sector_values: List[Optional[float]]) -> Optional[float]:
        """
        Calculate Z-score relative to sector peers.
        
        Args:
            value: The value to normalize
            sector_values: List of values for all stocks in the same sector
            
        Returns:
            Z-score or None if calculation not possible
        """
        if value is None or not sector_values or len(sector_values) < 2:
            return None
        
        # Remove None values and the current value from sector comparison
        clean_sector_values = [v for v in sector_values if v is not None and not np.isnan(v)]
        
        if len(clean_sector_values) < 2:
            return None
        
        sector_mean = np.mean(clean_sector_values)
        sector_std = np.std(clean_sector_values)
        
        if sector_std == 0:
            return 0.0  # All values are the same
        
        return float((value - sector_mean) / sector_std)
    
    def process_fundamental_data(self, 
                               fundamental_data: Dict[str, Dict[str, Any]], 
                               universe_df: pd.DataFrame) -> pd.DataFrame:
        """
        Process fundamental data for all tickers and calculate metrics with Z-scores.
        
        Args:
            fundamental_data: Dictionary of fundamental data by ticker
            universe_df: DataFrame with ticker and sector information
            
        Returns:
            DataFrame with calculated fundamental metrics and Z-scores
        """
        results = []
        
        # Create sector mapping
        sector_mapping = dict(zip(universe_df['ticker'], universe_df['sector']))
        
        # First pass: Calculate raw metrics for all tickers
        raw_metrics = {}
        for ticker, data in fundamental_data.items():
            if 'error' in data:
                continue
            
            try:
                # Extract key data points
                info = data.get('info', {})
                balance_sheet = data.get('balance_sheet', {})
                income_statement = data.get('income_statement', {})
                
                # Current price and EPS
                current_price = data.get('current_price') or info.get('regularMarketPrice')
                trailing_eps = data.get('trailing_eps') or info.get('trailingEps')
                
                # Get pre-calculated metrics from database (since we don't have full financial statements)
                roe = data.get('return_on_equity') or info.get('returnOnEquity')
                debt_to_equity = data.get('debt_to_equity') or info.get('debtToEquity')
                price_to_book = data.get('price_to_book') or info.get('priceToBook')
                
                # Calculate P/E ratio
                pe_ratio = self.calculate_pe_ratio(current_price, trailing_eps)
                
                # Debug: Log fundamental data for first few tickers
                if len(raw_metrics) < 3:
                    logger.info(f"Ticker {ticker}: roe={roe}, debt_to_equity={debt_to_equity}, "
                               f"price_to_book={price_to_book}")
                
                # Get other useful metrics from yfinance
                beta = data.get('beta') or info.get('beta')
                market_cap = data.get('market_cap') or info.get('marketCap')
                
                metrics = {
                    'ticker': ticker,
                    'sector': sector_mapping.get(ticker, 'Unknown'),
                    'current_price': current_price,
                    'market_cap': market_cap,
                    'pe_ratio': pe_ratio,
                    'roe': roe,
                    'debt_to_equity': debt_to_equity,
                    'price_to_book': price_to_book,
                    'beta': beta,
                    'trailing_eps': trailing_eps
                }
                
                raw_metrics[ticker] = metrics
                
            except Exception as e:
                logger.warning(f"Error processing fundamental data for {ticker}: {e}")
                continue
        
        # Second pass: Calculate sector Z-scores
        sectors = set(m['sector'] for m in raw_metrics.values() if m['sector'] != 'Unknown')
        
        for sector in sectors:
            sector_tickers = [t for t, m in raw_metrics.items() if m['sector'] == sector]
            
            if len(sector_tickers) < 2:
                continue
            
            # Collect sector values for P/E and D/E ratios
            sector_pe_values = [raw_metrics[t]['pe_ratio'] for t in sector_tickers 
                              if raw_metrics[t]['pe_ratio'] is not None]
            sector_de_values = [raw_metrics[t]['debt_to_equity'] for t in sector_tickers 
                              if raw_metrics[t]['debt_to_equity'] is not None]
            
            # Calculate Z-scores for each ticker in the sector
            for ticker in sector_tickers:
                metrics = raw_metrics[ticker]
                
                # P/E Z-score (lower is better for value)
                if metrics['pe_ratio'] is not None:
                    pe_zscore = self.calculate_sector_zscore(metrics['pe_ratio'], sector_pe_values)
                    metrics['pe_zscore'] = pe_zscore
                else:
                    metrics['pe_zscore'] = None
                
                # D/E Z-score (lower is better for safety)
                if metrics['debt_to_equity'] is not None:
                    de_zscore = self.calculate_sector_zscore(metrics['debt_to_equity'], sector_de_values)
                    metrics['de_zscore'] = de_zscore
                else:
                    metrics['de_zscore'] = None
        
        # Convert to DataFrame
        results_df = pd.DataFrame(list(raw_metrics.values()))
        
        # Add quality flags
        if not results_df.empty:
            results_df['meets_roe_threshold'] = (
                (results_df['roe'].notna()) & 
                (results_df['roe'] >= self.config.screening.min_roe)
            )
            
            results_df['meets_de_threshold'] = (
                (results_df['debt_to_equity'].notna()) & 
                (results_df['debt_to_equity'] <= self.config.screening.max_debt_equity_absolute)
            )
            
            results_df['meets_pe_threshold'] = (
                (results_df['pe_ratio'].notna()) & 
                (results_df['pe_ratio'] <= self.config.screening.max_pe_absolute) &
                (results_df['pe_ratio'] > 0)
            )
            
            results_df['meets_beta_threshold'] = (
                (results_df['beta'].notna()) & 
                (results_df['beta'] <= self.config.screening.max_beta)
            )
        
        logger.info(f"Processed fundamental data for {len(results_df)} tickers")
        return results_df


class TechnicalAnalyzer:
    """
    Calculates technical indicators using pandas-ta library for momentum and volatility analysis.
    """
    
    def __init__(self, config: Config):
        self.config = config
    
    def calculate_sma(self, prices: pd.Series, window: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return prices.rolling(window=window).mean()
    
    def calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index using Wilder's smoothing method.
        
        Args:
            prices: Price series (typically closing prices)
            window: RSI calculation window (default 14)
            
        Returns:
            RSI series
        """
        # Ensure prices are numeric and calculate price differences
        numeric_prices = pd.to_numeric(prices, errors='coerce').astype(float)
        delta = numeric_prices.diff()
        
        # Separate gains and losses using numpy operations for better type handling
        gain = delta.copy()
        gain[delta <= 0] = 0.0
        
        loss = -delta.copy()
        loss[delta >= 0] = 0.0
        
        # Use Wilder's smoothing (exponential moving average with alpha = 1/window)
        alpha = 1.0 / window
        avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
        avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()
        
        # Avoid division by zero
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, prices: pd.Series, 
                      fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Price series
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line EMA period
            
        Returns:
            DataFrame with MACD, signal, and histogram
        """
        # Calculate exponential moving averages
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        # MACD line is the difference between fast and slow EMAs
        macd_line = ema_fast - ema_slow
        
        # Signal line is EMA of MACD line
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        
        # Histogram is the difference between MACD line and signal line
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            f'MACD_{fast}_{slow}_{signal}': macd_line,
            f'MACDs_{fast}_{slow}_{signal}': signal_line,
            f'MACDh_{fast}_{slow}_{signal}': histogram
        })
    
    def calculate_bollinger_bands(self, prices: pd.Series, 
                                 window: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: Price series
            window: Moving average window
            std_dev: Standard deviation multiplier
            
        Returns:
            DataFrame with upper, middle, and lower bands
        """
        # Calculate simple moving average (middle band)
        sma = prices.rolling(window=window, min_periods=1).mean()
        
        # Calculate rolling standard deviation
        rolling_std = prices.rolling(window=window, min_periods=1).std()
        
        # Calculate upper and lower bands
        upper_band = sma + (rolling_std * std_dev)
        lower_band = sma - (rolling_std * std_dev)
        
        return pd.DataFrame({
            f'BBL_{window}_{std_dev}': lower_band,
            f'BBM_{window}_{std_dev}': sma,
            f'BBU_{window}_{std_dev}': upper_band
        })
    
    def calculate_beta(self, stock_prices: pd.Series, market_prices: pd.Series, 
                      window: int = 252) -> Optional[float]:
        """
        Calculate stock beta relative to market.
        
        Args:
            stock_prices: Stock price series
            market_prices: Market index price series (e.g., S&P 500)
            window: Calculation window in days (default 252 for 1 year)
            
        Returns:
            Beta coefficient or None if calculation not possible
        """
        try:
            # Calculate returns
            stock_returns = stock_prices.pct_change().dropna()
            market_returns = market_prices.pct_change().dropna()
            
            # Align the series
            aligned_data = pd.concat([stock_returns, market_returns], axis=1).dropna()
            
            if len(aligned_data) < window // 2:  # Need at least half the window
                return None
            
            # Take the last 'window' observations
            recent_data = aligned_data.tail(window)
            
            if len(recent_data) < 30:  # Need minimum observations
                return None
            
            # Calculate covariance and variance
            covariance = np.cov(recent_data.iloc[:, 0], recent_data.iloc[:, 1])[0, 1]
            market_variance = np.var(recent_data.iloc[:, 1])
            
            if market_variance == 0:
                return None
            
            beta = covariance / market_variance
            return beta
            
        except Exception as e:
            logger.warning(f"Error calculating beta: {e}")
            return None
    
    def process_technical_data(self, 
                              price_data: pd.DataFrame,
                              market_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Process technical indicators for all tickers in the price data.
        
        Args:
            price_data: DataFrame with price data (from database or yfinance)
            market_data: Market index data for beta calculation (optional)
            
        Returns:
            DataFrame with technical indicators for each ticker
        """
        if price_data.empty:
            return pd.DataFrame()
        
        results = []
        
        # Check if this is database format (has 'ticker' column) or yfinance format
        if 'ticker' in price_data.columns:
            # Database format: convert to wide format for technical analysis
            tickers = price_data['ticker'].unique()
            
            for ticker in tickers:
                try:
                    # Filter data for this ticker
                    ticker_data = price_data[price_data['ticker'] == ticker].copy()
                    
                    if len(ticker_data) < 50:  # Need minimum data for meaningful analysis
                        logger.warning(f"Insufficient data for {ticker}")
                        continue
                    
                    # Sort by date and set as index
                    ticker_data = ticker_data.sort_values('date').set_index('date')
                    
                    # Get closing prices
                    close_prices = ticker_data['close'].dropna()
                    
                    if len(close_prices) < 50:
                        logger.warning(f"Insufficient closing price data for {ticker}")
                        continue
                    
                    # Calculate technical indicators
                    rsi = self.calculate_rsi(close_prices, self.config.technical.rsi_period)
                    
                    # MACD
                    macd_data = self.calculate_macd(
                        close_prices, 
                        self.config.technical.macd_fast,
                        self.config.technical.macd_slow,
                        self.config.technical.macd_signal
                    )
                    
                    # Bollinger Bands
                    bb_data = self.calculate_bollinger_bands(
                        close_prices,
                        self.config.technical.bb_period,
                        self.config.technical.bb_std
                    )
                    
                    # Simple Moving Averages
                    sma_50 = self.calculate_sma(close_prices, self.config.technical.sma_short)
                    sma_200 = self.calculate_sma(close_prices, self.config.technical.sma_long)
                    
                    # Get current (latest) values
                    current_price = close_prices.iloc[-1]
                    current_rsi = rsi.iloc[-1] if not rsi.empty else None
                    current_sma_50 = sma_50.iloc[-1] if not sma_50.empty else None
                    current_sma_200 = sma_200.iloc[-1] if not sma_200.empty else None
                    
                    # MACD signals
                    macd_columns = list(macd_data.columns)
                    macd_line = macd_data[macd_columns[0]].iloc[-1] if len(macd_columns) > 0 else None
                    macd_signal = macd_data[macd_columns[1]].iloc[-1] if len(macd_columns) > 1 else None
                    macd_histogram = macd_data[macd_columns[2]].iloc[-1] if len(macd_columns) > 2 else None
                    
                    # Calculate beta if market data available
                    beta = None
                    if market_data is not None and not market_data.empty:
                        market_close = market_data['Close'] if 'Close' in market_data.columns else market_data.iloc[:, 0]
                        beta = self.calculate_beta(close_prices, market_close)
                    
                    # Technical signals
                    price_above_sma50 = current_sma_50 is not None and current_price > current_sma_50
                    price_above_sma200 = current_sma_200 is not None and current_price > current_sma_200
                    macd_bullish = (macd_line is not None and macd_signal is not None and 
                                   macd_line > macd_signal)
                    rsi_overbought = current_rsi is not None and current_rsi > self.config.screening.max_rsi_overbought
                    
                    # Compile results
                    technical_metrics = {
                        'ticker': ticker,
                        'current_price': current_price,
                        'rsi': current_rsi,
                        'sma_50': current_sma_50,
                        'sma_200': current_sma_200,
                        'macd_line': macd_line,
                        'macd_signal': macd_signal,
                        'macd_histogram': macd_histogram,
                        'beta': beta,
                        'price_above_sma50': price_above_sma50,
                        'price_above_sma200': price_above_sma200,
                        'macd_bullish': macd_bullish,
                        'rsi_overbought': rsi_overbought,
                        'positive_trend': price_above_sma50 or macd_bullish,
                        'meets_rsi_threshold': not rsi_overbought if current_rsi is not None else True
                    }
                    
                    results.append(technical_metrics)
                    
                except Exception as e:
                    logger.error(f"Error processing technical data for {ticker}: {e}")
                    continue
        
        else:
            # yfinance format: handle multi-level columns
            if isinstance(price_data.columns, pd.MultiIndex):
                tickers = price_data.columns.get_level_values(1).unique()
            else:
                # Single ticker case
                tickers = ['SINGLE_TICKER']
                # Restructure for consistent processing
                price_data.columns = pd.MultiIndex.from_product([price_data.columns, ['SINGLE_TICKER']])
            
            for ticker in tickers:
                try:
                    # Extract price data for this ticker
                    if ticker in price_data.columns.get_level_values(1):
                        ticker_data = price_data.xs(ticker, axis=1, level=1)
                    else:
                        continue
                    
                    # Get closing prices
                    close_prices = ticker_data['Close'].dropna()
                    
                    if len(close_prices) < 50:  # Need minimum data for meaningful analysis
                        logger.warning(f"Insufficient data for {ticker}")
                        continue
                    
                    # Calculate technical indicators
                    rsi = self.calculate_rsi(close_prices, self.config.technical.rsi_period)
                    
                    # MACD
                    macd_data = self.calculate_macd(
                        close_prices, 
                        self.config.technical.macd_fast,
                        self.config.technical.macd_slow,
                        self.config.technical.macd_signal
                    )
                    
                    # Bollinger Bands
                    bb_data = self.calculate_bollinger_bands(
                        close_prices,
                        self.config.technical.bb_period,
                        self.config.technical.bb_std
                    )
                    
                    # Simple Moving Averages
                    sma_50 = self.calculate_sma(close_prices, self.config.technical.sma_short)
                    sma_200 = self.calculate_sma(close_prices, self.config.technical.sma_long)
                    
                    # Get current (latest) values
                    current_price = close_prices.iloc[-1]
                    current_rsi = rsi.iloc[-1] if not rsi.empty else None
                    current_sma_50 = sma_50.iloc[-1] if not sma_50.empty else None
                    current_sma_200 = sma_200.iloc[-1] if not sma_200.empty else None
                    
                    # MACD signals
                    macd_columns = list(macd_data.columns)
                    macd_line = macd_data[macd_columns[0]].iloc[-1] if len(macd_columns) > 0 else None
                    macd_signal = macd_data[macd_columns[1]].iloc[-1] if len(macd_columns) > 1 else None
                    macd_histogram = macd_data[macd_columns[2]].iloc[-1] if len(macd_columns) > 2 else None
                    
                    # Calculate beta if market data available
                    beta = None
                    if market_data is not None and not market_data.empty:
                        market_close = market_data['Close'] if 'Close' in market_data.columns else market_data.iloc[:, 0]
                        beta = self.calculate_beta(close_prices, market_close)
                    
                    # Technical signals
                    price_above_sma50 = current_sma_50 is not None and current_price > current_sma_50
                    price_above_sma200 = current_sma_200 is not None and current_price > current_sma_200
                    macd_bullish = (macd_line is not None and macd_signal is not None and 
                                   macd_line > macd_signal)
                    rsi_overbought = current_rsi is not None and current_rsi > self.config.screening.max_rsi_overbought
                    
                    # Compile results
                    technical_metrics = {
                        'ticker': ticker,
                        'current_price': current_price,
                        'rsi': current_rsi,
                        'sma_50': current_sma_50,
                        'sma_200': current_sma_200,
                        'macd_line': macd_line,
                        'macd_signal': macd_signal,
                        'macd_histogram': macd_histogram,
                        'beta': beta,
                        'price_above_sma50': price_above_sma50,
                        'price_above_sma200': price_above_sma200,
                        'macd_bullish': macd_bullish,
                        'rsi_overbought': rsi_overbought,
                        'positive_trend': price_above_sma50 or macd_bullish,
                        'meets_rsi_threshold': not rsi_overbought if current_rsi is not None else True
                    }
                    
                    results.append(technical_metrics)
                    
                except Exception as e:
                    logger.error(f"Error processing technical data for {ticker}: {e}")
                    continue
        
        results_df = pd.DataFrame(results)
        logger.info(f"Processed technical data for {len(results_df)} tickers")
        return results_df


def calculate_composite_features(fundamental_df: pd.DataFrame, 
                               technical_df: pd.DataFrame) -> pd.DataFrame:
    """
    Combine fundamental and technical features into a single DataFrame.
    
    Args:
        fundamental_df: DataFrame with fundamental metrics
        technical_df: DataFrame with technical indicators
        
    Returns:
        Combined DataFrame with all features
    """
    if fundamental_df.empty and technical_df.empty:
        return pd.DataFrame()
    
    # Merge on ticker
    if not fundamental_df.empty and not technical_df.empty:
        combined_df = pd.merge(fundamental_df, technical_df, on='ticker', how='outer', suffixes=('_fund', '_tech'))
        
        # Resolve conflicts in current_price
        if 'current_price_fund' in combined_df.columns and 'current_price_tech' in combined_df.columns:
            combined_df['current_price'] = combined_df['current_price_tech'].fillna(combined_df['current_price_fund'])
            combined_df = combined_df.drop(['current_price_fund', 'current_price_tech'], axis=1)
            
    elif not fundamental_df.empty:
        combined_df = fundamental_df.copy()
    else:
        combined_df = technical_df.copy()
    
    logger.info(f"Combined features for {len(combined_df)} tickers")
    return combined_df