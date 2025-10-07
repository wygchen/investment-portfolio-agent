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
#from fredapi import Fred
import matplotlib.pyplot as plt

# Import market sentiment score function
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sentiment_market'))
from market_sentiment import analyze_market_sentiment

# Section 1: Define Tickers and Time Range 
tickers = ['SPY', 'BND', 'GLD', 'QQQ', 'VTI']       
"""SPY: most popular S&P500 index
    BND: bond index
    GLD: largest commmodity base ETF
    QQQ: NASDAQ ETF
    VTI: encompasses the entire world stock market
     
    Different asset classes with low correlation with each other
"""

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
# User risk tolerance (max allowed portfolio variance)
user_risk_tolerance = 0.03              # Example: user sets max variance (adjust as needed)

# Get market sentiment score from external module (analyze_market_sentiment returns a list of dicts)
sentiment_results = analyze_market_sentiment(tickers)
# Extract numeric average sentiment score per ticker into a float numpy array.
try:
    market_sentiment = np.array([
        float(r.get("Average Sentiment Score", 0.0)) if isinstance(r, dict) else 0.0
        for r in sentiment_results
    ], dtype=float)
    # If lengths mismatch, ensure it matches tickers length
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
fred = Fred(api_key='189872e56e87c2a674b98c905c49a289')
ten_year_treasury_rate = fred.get_series_latest_release('GS10') / 100       # get GS10 from API. GS10 means 10 years treasury rate, the /100 to get in % form
risk_free_rate = ten_year_treasury_rate.iloc[-1]                            # set the GS10 as the risk_free_rate
 """

# Define the function to minimize (negative Sharpe Ratio)
# we do ourselves as scipy only have minimum function dh max so we just myltiply by -1 ourselves
def neg_sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate, sentiment=None):
    return -sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate, sentiment)



# Helper function to test a list of max bounds and return the best one
def find_best_bound(max_bounds_list, tickers, log_returns, cov_matrix, risk_free_rate, market_sentiment, user_risk_tolerance):
    best_sharpe = -np.inf
    best_bound = None
    best_result = None
    for max_bound in max_bounds_list:
        bounds = [(0, max_bound) for _ in range(len(tickers))]
        constraints = [
            {'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1},
            {'type': 'ineq', 'fun': lambda weights: user_risk_tolerance - (weights.T @ cov_matrix @ weights)}
        ]
        initial_weights = np.array([1 / len(tickers)] * len(tickers))
        result = minimize(
            neg_sharpe_ratio,
            initial_weights,
            args=(log_returns, cov_matrix, risk_free_rate, market_sentiment),
            method='SLSQP',
            constraints=constraints,
            bounds=bounds
        )
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
    best_bound, optimized_results = find_best_bound(
        max_bounds_to_test,
        tickers,
        log_returns,
        cov,
        risk_free_rate,
        market_sentiment,
        user_risk_tolerance
    )
    print(f"\nBest max bound (SciPy): {best_bound}")
    return optimized_results.x, cov


# Run optimization (default: use PyPortfolioOpt if available)
opt_method = "pypfopt" if PYPFOPT_AVAILABLE else "scipy"
optimal_weights, cov_matrix = run_optimization(method=opt_method, cov_method=("ledoit_wolf" if PYPFOPT_AVAILABLE else "sample"), max_bounds_to_test=max_bounds_to_test)
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

# Filter out zero or near-zero weights
threshold = 0.0001  # Adjust as needed
filtered_tickers = [tickers[i] for i in range(len(tickers)) if optimal_weights[i] > threshold]
filtered_weights = [optimal_weights[i] for i in range(len(tickers)) if optimal_weights[i] > threshold]

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