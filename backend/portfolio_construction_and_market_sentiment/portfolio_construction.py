# Import Required Librarires 
import yfinance as yf                       # pull in stock prices from yahoofinance
import pandas as pd                         # put the data into dataframe table
from datetime import datetime, timedelta    # select a certain time range how far back we wanna analyse data 
import numpy as np                          # use for calculating statistic
from scipy.optimize import minimize         # use for calculating statistic
import argparse                             # can parse --tickers into a usable variable --> python3 market_sentiment.py --tickers AAPL TSLA AMZN
try:
    # PyPortfolioOpt for covariance estimation and optimization
    from pypfopt import EfficientFrontier, risk_models, expected_returns
    PYPFOPT_AVAILABLE = True
except Exception:
    PYPFOPT_AVAILABLE = False               # if not available, will not do the pypfopt optimization (use normal covariance)
import matplotlib.pyplot as plt
from portfolio_types import PortfolioResult
# import json

# Import market sentiment score function
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from market_sentiment import analyze_market_sentiment
try:
    # Import dataclass type from dedicated module
    from market_sentiment_types import MarketSentiment  # type: ignore
except Exception:
    MarketSentiment = None
# Import local preference helpers
try:
    from preferences import derive_preferences, equity_indices_for_tickers
except Exception:
    derive_preferences = None
    equity_indices_for_tickers = None

# Section 1: Define Tickers and Time Range 
# Asset class -> representative tickers mapping. Consumers can reference individual lists
# or use default_tickers (flattened across classes) when no profile exists.
asset_class_tickers = {
    'US_EQUITIES': ['VTI', 'SPY', 'IVV'],           # Total US vs S&P 500
    'HONG_KONG_EQUITIES': ['EWH', 'FXI', 'YINN'],   # Hong Kong only ETFs
    'BONDS': ['BND', 'AGG', 'BNDW'],                # US Bonds vs Global Bonds
    'REITS': ['VNQ', 'SCHH', 'IYR'],                # US REITs
    'COMMODITIES': ['DBC', 'GSG', 'PDBC'],          # Broad commodities
    'CRYPTO': ['BTC-USD', 'GBTC', 'BITO'],          # Direct crypto vs ETFs
}

# Default tickers (flattened list across asset classes). Order preserved; duplicates removed.
seen = set()
default_tickers = []
for assets in asset_class_tickers.values():
    for t in assets:
        if t not in seen:
            seen.add(t)
            default_tickers.append(t)



# Try to load market selection from the latest discovery profile saved by DiscoveryAgent
shared_profile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shared_data', 'latest_profile.json')

def _select_tickers_from_profile(path: str):
    """Read a discovery profile JSON and return a list of tickers based on market_selection.

    Expected `market_selection` values in the profile: list containing any of 'US', 'HK'.
    Returns default_tickers on error or unknown selection.
    """
    try:
        import json
        if not os.path.exists(path):
            print(f"Discovery profile not found at {path}; using default tickers")
            return default_tickers
        with open(path, 'r') as f:
            profile = json.load(f)
        market_selection = profile.get('market_selection') or profile.get('marketSelection') or []
        # Normalize to uppercase strings
        market_selection = [m.upper() for m in market_selection if isinstance(m, str)]
        tickers = []
        if 'US' in market_selection:
            # US equity/ETF basket
            tickers.extend(['SPY', 'QQQ'])
        if 'HK' in market_selection:
            # Common Hong Kong tickers (HKEX listings use .HK suffix)
            # These are example large-cap HK tickers; adjust as needed for your data sources
            tickers.extend(['0700.HK', '0988.HK', '0939.HK', 'EWH'])
        # If user asked for other markets or list is empty, fall back to defaults
        if not tickers:
            return default_tickers
        return tickers
    except Exception as e:
        print(f"Failed to read discovery profile ({e}); using default tickers")
        return default_tickers


# Resolve tickers to use for portfolio construction
# Resolve tickers to use for portfolio construction
tickers = _select_tickers_from_profile(shared_profile_path)

# Set the end date to today
end_date = datetime.today()         # get today's date

# Set the start date to 5 years ago
start_date = end_date - timedelta(days=8 * 365)         #  current time - 5 years ago --> so we get the data within 5 years
""" we can adjust the start date """

# Section 2: Download Close Prices (adjusted close price)
""" Adjusted close price --> more accurate for optimal portfolio 
    because included dividend and stock split
    
    normal close price will underweight a stock that pays more dividends because 
    the dividend is not reflected
    
"""

# Create an empty DataFrame to store the adjusted close prices
adj_close_df = pd.DataFrame()

# Download the close prices for each ticker
for ticker in tickers:
    data = yf.download(ticker, start=start_date, end=end_date)
    """ make a dataframe to hold all the stock information for these tickers"""

    adj_close_df[ticker] = data['Close']            # extract the adjusted close price  column from the data
                                                    # adj_close_df[ticker] = data['Close'] creates a new column in adj_close_df with the name of the ticker 
                                                    # (e.g., "AAPL") and fills it with the closing prices from data['Close'].



# Section 3: Calculate Logarithmic Returns
# Calculate the logonormal returns for each tickers
log_returns = np.log(adj_close_df / adj_close_df.shift(1))
""" log normal return is used for easy the calculation """
# .shift(1) is taking the data from one row above
""" so eg 2025-09-29 xxx
          2025-09-30 yyy       --> log(yyy/xxx)
"""
log_returns = log_returns.dropna()      # removes rows or columns from a DataFrame that contain missing values

# Section 4: Calculate Covariance Matrix
# Calculate the covariance matrix using annualized log returns
cov_matrix = log_returns.cov() * 252            # Why 252? This is the approximate number of trading days in a year for most stock markets (e.g., US markets).

# Helper to compute covariance matrix using PyPortfolioOpt risk models when available
def compute_cov_matrix(prices_or_returns, method="sample"):
    """Compute an annualized covariance matrix.

    method: one of 'sample', 'ledoit_wolf', 'oas', 'shrunk'
    If PyPortfolioOpt is not available, falls back to sample covariance.
    """
    if PYPFOPT_AVAILABLE and method in ("ledoit_wolf", "oas", "sample", "shrunk"):
        # risk_models expects price series (DataFrame of prices) for some functions
        # If we were given returns, convert back by assuming cumulative product isn't necessary here;
        # risk_models.CovarianceShrinkage will accept returns as well.
        if method == "sample":
            return (prices_or_returns.cov() * 252)
        elif method == "ledoit_wolf":
            return risk_models.CovarianceShrinkage(prices_or_returns).ledoit_wolf()
        elif method == "oas":
            return risk_models.CovarianceShrinkage(prices_or_returns).oas()
        elif method == "shrunk":
            return risk_models.CovarianceShrinkage(prices_or_returns).shrunk_covariance()
    # Fallback: sample covariance from returns
    return (prices_or_returns.cov() * 252)

# Section 5: Define Portfolio Performance Metrics
# --- Agent Inputs ---
# Load profile and derive preferences (risk tolerance, target equity allocation)
profile = {}
try:
    import json
    if os.path.exists(shared_profile_path):
        with open(shared_profile_path, 'r') as pf:
            profile = json.load(pf)
except Exception:
    profile = {}

if derive_preferences is not None:
    user_risk_tolerance, target_equity_allocation = derive_preferences(profile)
else:
    user_risk_tolerance, target_equity_allocation = 0.03, 0.6

# Determine equity indices (simple classifier)
if equity_indices_for_tickers is not None:
    equity_indices = equity_indices_for_tickers(tickers)
else:
    equity_indices = [i for i, t in enumerate(tickers) if t not in ("BND", "GLD")]

# Get market sentiment score from external module (analyze_market_sentiment returns a list of dicts)
sentiment_results = analyze_market_sentiment(tickers)
# Extract numeric average sentiment score per ticker into a float numpy array.
def _extract_avg_score(entry):
    """Support both dicts and MarketSentiment dataclass instances."""
    try:
        if MarketSentiment is not None and isinstance(entry, MarketSentiment):
            return float(entry.average_sentiment_score)
        if isinstance(entry, dict):
            return float(entry.get("Average Sentiment Score", 0.0) or 0.0)
        # Fallback: try attribute access
        return float(getattr(entry, "average_sentiment_score", 0.0) or 0.0)
    except Exception:
        return 0.0

try:
    market_sentiment = np.array([_extract_avg_score(r) for r in sentiment_results], dtype=float)
    if market_sentiment.shape[0] != len(tickers):
        market_sentiment = np.full(len(tickers), 0.0)
except Exception:
    market_sentiment = np.full(len(tickers), 0.0)

# Calculate the Portfolio Standard Deviation
def standard_deviation(weights, cov_matrix):
    variance = weights.T @ cov_matrix @ weights
    """ weights.T is doing transpose
        @ is multiplying two arrays
        @ multiply another matrix called weights
    """
    return np.sqrt(variance)

# Calcualte the Expected Return based on the historical returns --> future return = average old return
def expected_return(weights, log_returns, sentiment=None):
    base_returns = log_returns.mean() * 252
    if sentiment is not None:
        base_returns = base_returns + sentiment
    return np.sum(base_returns * weights)

# Calculate the Sharpe Ratio
def sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate, sentiment=None):
    return (expected_return(weights, log_returns, sentiment) - risk_free_rate) / standard_deviation(weights, cov_matrix)

# Section 6: Portfolio Optimization
def get_risk_free_rate(default_rate: float = 0.02) -> float:
    """Fetch the latest 3-month Treasury bill (^IRX) close value using yfinance.

    Returns the rate in decimal form (e.g., 0.02 for 2%). Falls back to default_rate if fetch fails.
    """
    try:
        t = yf.Ticker("^IRX")
        hist = t.history(period="7d")
        if hist is None or hist.empty:
            return default_rate
        latest_rate = hist['Close'].dropna().iloc[-1]
        # ^IRX returns percent (e.g., 2.5) so convert to decimal
        return float(latest_rate) / 100.0
    except Exception:
        return default_rate

# Set risk-free rate (use T-bill if available)
risk_free_rate = get_risk_free_rate(default_rate=0.02)

"""alternative use the follows:
# Setting up the FredAPI Key
fred_api_key = os.getenv('FRED_API_KEY')
if fred_api_key:
    fred = Fred(api_key=fred_api_key)
    ten_year_treasury_rate = fred.get_series_latest_release('GS10') / 100       # get GS10 from API. GS10 means 10 years treasury rate, the /100 to get in % form
    risk_free_rate = ten_year_treasury_rate.iloc[-1]                            # set the GS10 as the risk_free_rate
else:
    # Use default risk-free rate if FRED API key not available
    risk_free_rate = 0.02
 """

# Define the function to minimize (negative Sharpe Ratio)
# we do ourselves as scipy only have minimum function dh max so we just myltiply by -1 ourselves
def neg_sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate, sentiment=None):
    return -sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate, sentiment)


def neg_sharpe_with_penalty(weights, log_returns, cov_matrix, risk_free_rate, sentiment, target_equity, equity_idx, lam=50.0):
    """Negative Sharpe with quadratic penalty for missing equity allocation."""
    base = neg_sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate, sentiment)
    try:
        equity_sum = float(np.sum(np.array(weights)[equity_idx])) if equity_idx else 0.0
    except Exception:
        equity_sum = 0.0
    penalty = lam * max(0.0, target_equity - equity_sum) ** 2
    return base + penalty



# Helper function to test a list of max bounds and return the best one
def find_best_bound(max_bounds_list, tickers, log_returns, cov_matrix, risk_free_rate, market_sentiment, user_risk_tolerance, target_equity_allocation=None, equity_indices=None):
    best_sharpe = -np.inf
    best_bound = None
    best_result = None
    for max_bound in max_bounds_list:
        bounds = [(0, max_bound) for _ in range(len(tickers))]
        constraints = [
            {'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1},
            {'type': 'ineq', 'fun': lambda weights: user_risk_tolerance - (weights.T @ cov_matrix @ weights)}
        ]

        # Add hard equity allocation constraint if requested
        if target_equity_allocation is not None and equity_indices:
            constraints.append({
                'type': 'ineq',
                'fun': lambda weights, idx=equity_indices, target=target_equity_allocation: np.sum(np.array(weights)[idx]) - target
            })
        initial_weights = np.array([1 / len(tickers)] * len(tickers))
        result = minimize(
            neg_sharpe_ratio,
            initial_weights,
            args=(log_returns, cov_matrix, risk_free_rate, market_sentiment),
            method='SLSQP',
            constraints=constraints,
            bounds=bounds
        )
        # If the constrained optimization failed, try a soft-penalty objective
        if (not result.success) and (target_equity_allocation is not None and equity_indices):
            penalty_lambda = 50.0
            result_pen = minimize(
                neg_sharpe_with_penalty,
                initial_weights,
                args=(log_returns, cov_matrix, risk_free_rate, market_sentiment, target_equity_allocation, equity_indices, penalty_lambda),
                method='SLSQP',
                bounds=bounds,
                constraints=[{'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1},
                             {'type': 'ineq', 'fun': lambda weights: user_risk_tolerance - (weights.T @ cov_matrix @ weights)}]
            )
            if result_pen.success:
                result = result_pen
        if result.success:
            weights = result.x
            sharpe = sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate, market_sentiment)
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_bound = max_bound
                best_result = result
    return best_bound, best_result

# Example usage: test max bounds 0.2, 0.3, 0.4, 0.5
max_bounds_to_test = [0.2, 0.3, 0.4, 0.5]
def run_optimization(method="pypfopt", cov_method="ledoit_wolf", max_bounds_to_test=None):
    """Run portfolio optimization.

    method: 'pypfopt' to use PyPortfolioOpt EfficientFrontier if available, 'scipy' to use existing scipy SLSQP.
    cov_method: covariance estimation method for compute_cov_matrix (sample, ledoit_wolf, oas, shrunk)
    max_bounds_to_test: list of upper bounds per-asset to search over (None uses defaults)
    """
    if max_bounds_to_test is None:
        max_bounds_to_test = [0.2, 0.3, 0.4, 0.5]

    # (re)compute covariance using chosen method
    cov = compute_cov_matrix(log_returns, method=cov_method)

    if method == "pypfopt" and PYPFOPT_AVAILABLE:
        # Use PyPortfolioOpt's EfficientFrontier to maximize Sharpe ratio subject to constraints
        mu = expected_returns.mean_historical_return(adj_close_df, frequency=252)
        ef_best = None
        best_sharpe = -np.inf
        best_bound = None
        for max_bound in max_bounds_to_test:
            # Build EfficientFrontier with bounds and covariance
            ef = EfficientFrontier(mu, cov, weight_bounds=(0, max_bound))
            # Add risk (variance) constraint: we want portfolio variance <= user_risk_tolerance
            # PyPortfolioOpt supports adding objective/constraint via add_constraint
            ef.add_constraint(lambda w: user_risk_tolerance - w.T @ cov @ w)
            try:
                weights = ef.max_sharpe(risk_free_rate=risk_free_rate)
                cleaned_weights = ef.clean_weights()
                # compute Sharpe for this solution
                w_array = np.array([cleaned_weights.get(t, 0.0) for t in tickers])
                sr = sharpe_ratio(w_array, log_returns, cov, risk_free_rate, market_sentiment)
                if sr > best_sharpe:
                    best_sharpe = sr
                    ef_best = (ef, cleaned_weights)
                    best_bound = max_bound
            except Exception as e:
                # If EF fails, continue to next bound
                print(f"PyPortfolioOpt optimization failed for bound {max_bound}: {e}")
                continue
        if ef_best is None:
            raise RuntimeError("PyPortfolioOpt optimization unable to find a feasible solution.")
        print(f"\nBest max bound (PyPortfolioOpt): {best_bound}")
        return ef_best[1], cov

    # Fallback to SciPy approach
    # compute equity indices for this universe
    if equity_indices_for_tickers is not None:
        eq_idx = equity_indices_for_tickers(tickers)
    else:
        eq_idx = [i for i, t in enumerate(tickers) if t not in ("BND", "GLD")]

    best_bound, optimized_results = find_best_bound(
        max_bounds_to_test,
        tickers,
        log_returns,
        cov,
        risk_free_rate,
        market_sentiment,
        user_risk_tolerance,
        target_equity_allocation=target_equity_allocation,
        equity_indices=eq_idx,
    )
    print(f"\nBest max bound (SciPy): {best_bound}")
    return optimized_results.x, cov


# Run optimization (default: use PyPortfolioOpt if available)
opt_method = "pypfopt" if PYPFOPT_AVAILABLE else "scipy"
optimal_weights, cov_matrix = run_optimization(method=opt_method, cov_method=("ledoit_wolf" if PYPFOPT_AVAILABLE else "sample"), max_bounds_to_test=max_bounds_to_test)

def run_optimization_with_tickers(tickers, method="pypfopt", cov_method="ledoit_wolf", max_bounds_to_test=None):
    """
    Run portfolio optimization with specific tickers.
    
    Args:
        tickers: List of ticker symbols to include in optimization
        method: 'pypfopt' or 'scipy' optimization method
        cov_method: Covariance estimation method
        max_bounds_to_test: List of upper bounds to test
        
    Returns:
        Tuple of (optimal_weights, cov_matrix)
    """
    global adj_close_df, log_returns
    
    if max_bounds_to_test is None:
        max_bounds_to_test = [0.2, 0.3, 0.4, 0.5]
    
    # Filter data to only include specified tickers
    if not all(ticker in adj_close_df.columns for ticker in tickers):
        # Download missing ticker data
        for ticker in tickers:
            if ticker not in adj_close_df.columns:
                try:
                    data = yf.download(ticker, start=start_date, end=end_date)
                    adj_close_df[ticker] = data['Close']
                except Exception as e:
                    print(f"Warning: Could not download data for {ticker}: {e}")
        
        # Recalculate log returns with new tickers
        log_returns = np.log(adj_close_df / adj_close_df.shift(1))
        log_returns = log_returns.dropna()
    
    # Filter to only use specified tickers
    available_tickers = [t for t in tickers if t in adj_close_df.columns]
    if not available_tickers:
        # Fallback: use equal weights
        return ([1.0/len(tickers) for _ in tickers], np.eye(len(tickers)))
    
    ticker_log_returns = log_returns[available_tickers]
    ticker_cov = compute_cov_matrix(ticker_log_returns, method=cov_method)
    
    # Get market sentiment for these tickers
    sentiment_results = analyze_market_sentiment(available_tickers)
    try:
        ticker_sentiment = np.array([_extract_avg_score(r) for r in sentiment_results], dtype=float)
        if ticker_sentiment.shape[0] != len(available_tickers):
            ticker_sentiment = np.full(len(available_tickers), 0.0)
    except Exception:
        ticker_sentiment = np.full(len(available_tickers), 0.0)
    
    if method == "pypfopt" and PYPFOPT_AVAILABLE:
        # Use PyPortfolioOpt
        try:
            mu = expected_returns.mean_historical_return(adj_close_df[available_tickers])
            
            best_sharpe = -np.inf
            best_weights = None
            
            for max_bound in max_bounds_to_test:
                try:
                    ef = EfficientFrontier(mu, ticker_cov, weight_bounds=(0, max_bound))
                    weights = ef.max_sharpe()
                    weights_array = np.array([weights.get(ticker, 0.0) for ticker in available_tickers])
                    
                    # Calculate Sharpe ratio
                    portfolio_return = expected_return(weights_array, ticker_log_returns, ticker_sentiment)
                    portfolio_volatility = standard_deviation(weights_array, ticker_cov)
                    current_sharpe = (portfolio_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
                    
                    if current_sharpe > best_sharpe:
                        best_sharpe = current_sharpe
                        best_weights = weights_array
                        
                except Exception as e:
                    print(f"PyPortfolioOpt failed for bound {max_bound}: {e}")
                    continue
            
            if best_weights is not None:
                # Pad with zeros for missing tickers
                result_weights = []
                for ticker in tickers:
                    if ticker in available_tickers:
                        idx = available_tickers.index(ticker)
                        result_weights.append(best_weights[idx])
                    else:
                        result_weights.append(0.0)
                
                return result_weights, ticker_cov
                
        except Exception as e:
            print(f"PyPortfolioOpt optimization failed: {e}")
    
    # Fallback to SciPy optimization
    try:
        # Determine equity indices for these tickers
        if equity_indices_for_tickers is not None:
            eq_idx = equity_indices_for_tickers(available_tickers)
        else:
            eq_idx = [i for i, t in enumerate(available_tickers) if t not in ("BND", "GLD")]
        
        best_bound, optimized_results = find_best_bound(
            max_bounds_to_test,
            available_tickers,
            ticker_log_returns,
            ticker_cov,
            risk_free_rate,
            ticker_sentiment,
            user_risk_tolerance,
            target_equity_allocation=target_equity_allocation,
            equity_indices=eq_idx,
        )
        
        if optimized_results is not None:
            # Pad with zeros for missing tickers
            result_weights = []
            for ticker in tickers:
                if ticker in available_tickers:
                    idx = available_tickers.index(ticker)
                    result_weights.append(optimized_results.x[idx])
                else:
                    result_weights.append(0.0)
            
            return result_weights, ticker_cov
            
    except Exception as e:
        print(f"SciPy optimization failed: {e}")
    
    # Final fallback: equal weights
    return ([1.0/len(tickers) for _ in tickers], np.eye(len(tickers)))
"""
This will test each max bound for all assets and select the one with the highest Sharpe ratio.
"""

# Get the Optimal Weights
# `optimal_weights` is returned from run_optimization


# Section 7: Analyze the Optimal Portfolio
# Display analytics of the optimal portfolio
print("Optimal Weights:")
for ticker, weight in zip(tickers, optimal_weights):
    print(f"{ticker}: {weight:.4f}")


# Use sentiment-adjusted returns for analytics
optimal_portfolio_return = expected_return(optimal_weights, log_returns, market_sentiment)
optimal_portfolio_volatility = standard_deviation(optimal_weights, cov_matrix)
optimal_sharpe_ratio = sharpe_ratio(optimal_weights, log_returns, cov_matrix, risk_free_rate, market_sentiment)

print(f"\nExpected Annual Return: {optimal_portfolio_return:.4f}")
print(f"Expected Volatility: {optimal_portfolio_volatility:.4f}")
print(f"Sharpe Ratio: {optimal_sharpe_ratio:.4f}")

"""
# Display the final portfolio in a plot
plt.figure(figsize=(10, 6))
plt.bar(tickers, optimal_weights)
plt.xlabel('Assets')
plt.ylabel('Optimal Portfolio Weights')
plt.title('Optimized Portfolio Allocation')
plt.show()
"""
"""
# Filter out zero or near-zero weights
threshold = 0.0001  # Adjust as needed
filtered_tickers = [tickers[i] for i in range(len(tickers)) if optimal_weights[i] > threshold]
filtered_weights = [optimal_weights[i] for i in range(len(tickers)) if optimal_weights[i] > threshold]
"""

# Build a PortfolioResult dataclass instance for easier passing to other modules
try:
    # full mapping of all tickers to their final weights
    weights_map_full = {t: float(w) for t, w in zip(tickers, optimal_weights)}

    # Compute allocation by the predefined asset classes (asset_class_tickers)
    try:
        # Build reverse mapping ticker -> asset class name (first match wins)
        ticker_to_class = {}
        for class_name, tlist in asset_class_tickers.items():
            for t in tlist:
                if t not in ticker_to_class:
                    ticker_to_class[t] = class_name

        # Sum weights per class; tickers not in mapping go into 'OTHER'
        asset_class_allocations = {cn: 0.0 for cn in asset_class_tickers.keys()}
        asset_class_allocations['OTHER'] = 0.0
        for t, w in weights_map_full.items():
            cls = ticker_to_class.get(t)
            if cls is None:
                asset_class_allocations['OTHER'] += float(w)
            else:
                asset_class_allocations[cls] += float(w)

        portfolio_result = PortfolioResult(
            tickers=tickers,
            weights=list(optimal_weights),
            covariance_matrix=cov_matrix if 'cov_matrix' in globals() else None,
            expected_return=float(optimal_portfolio_return),
            volatility=float(optimal_portfolio_volatility),
            sharpe_ratio=float(optimal_sharpe_ratio),
            risk_free_rate=float(risk_free_rate),
            weights_map=weights_map_full,
            asset_class_allocations=asset_class_allocations,
        )
        # Print the allocation by asset class
        print("\nAsset class allocations:")
        for cls, alloc in asset_class_allocations.items():
            print(f"  {cls}: {alloc:.4f}")
    except Exception as e:
        print("Failed to compute asset-class allocations:", e)
    '''
    # Print JSON-friendly dict of portfolio result
    print(json.dumps(portfolio_result.to_dict(), indent=2))
    # Optionally save to file
    with open("portfolio_result.json", "w") as f:
        json.dump(portfolio_result.to_dict(), f, indent=2)
    '''
except Exception as e:
    print("Failed to build PortfolioResult dataclass:", e)

"""
# Assuming tickers and optimal_weights are defined (e.g., from portfolio optimization)
# Example: tickers = ["AAPL", "MSFT"], optimal_weights = [0.6, 0.4]

# bar chart
plt.figure(figsize=(10, 6))
plt.pie(optimal_weights, labels=tickers, autopct='%1.1f%%', startangle=90)
plt.title('Optimized Portfolio Allocation', y=1.05)
plt.axis('equal')  # Equal aspect ratio ensures the pie chart is circular
plt.show()


# or pie chart
plt.figure(figsize=(10, 6))
plt.pie(filtered_weights, labels=filtered_tickers, autopct='%1.1f%%', startangle=90)
plt.title('Optimized Portfolio Allocation', y=1.05)
plt.axis('equal')  # Equal aspect ratio ensures the pie chart is circular
plt.show()
"""

"""
import json

# make sure numeric types are native floats for JSON
weights_map = {t: float(w) for t, w in zip(filtered_tickers, filtered_weights)}

# print to stdout
print(json.dumps(weights_map, indent=2))

# save to file
with open("filtered_weights.json", "w") as f:
    json.dump(weights_map, f, indent=2)

"""