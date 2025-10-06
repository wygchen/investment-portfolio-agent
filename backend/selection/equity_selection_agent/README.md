# Equity Selection Agent (ESA) V1.0

A specialized, decoupled component focused on systematic security selection for generating alpha through multi-factor criteria analysis.

## ⚠️ IMPORTANT LEGAL DISCLAIMER

**THIS SOFTWARE IS FOR RESEARCH AND EDUCATIONAL PURPOSES ONLY**

This Equity Selection Agent (ESA) is intended solely for research, educational, and informational purposes. It is NOT intended to provide investment advice, recommendations, or guidance for actual trading decisions.

### Data Source Disclaimer

This project uses the `yfinance` library to retrieve financial data from Yahoo Finance's publicly available APIs. **IMPORTANT DISCLAIMERS:**

- `yfinance` is **NOT** affiliated with, endorsed, or vetted by Yahoo, Inc.
- The Yahoo! Finance API is primarily intended for **personal use**
- Users must comply with [Yahoo's Terms of Use](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html) when using this software
- **You are responsible for ensuring your usage rights for any downloaded data**

### Investment Disclaimer

- **No Investment Advice**: This software does not provide investment advice or recommendations
- **No Guarantees**: Past performance does not guarantee future results
- **Risk Warning**: All investments carry risk of loss
- **Professional Advice**: Consult qualified financial professionals before making investment decisions
- **Personal Responsibility**: Users are solely responsible for their investment decisions

### Liability Limitation

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. THE AUTHORS SHALL NOT BE LIABLE FOR ANY DAMAGES ARISING FROM THE USE OF THIS SOFTWARE.

## Features

- **Multi-Factor Analysis**: Combines Value, Quality, Risk, and Momentum factors
- **Peer-Relative Scoring**: Sector-normalized Z-scores for fair comparison
- **Technical Analysis**: RSI, MACD, Bollinger Bands, and trend indicators
- **Configurable Screening**: Layered filtering with customizable thresholds
- **Comprehensive Reporting**: JSON, CSV, and detailed audit logs
- **Qualitative Integration**: Hook for LLM-based analysis (optional)

## Architecture

The ESA follows a modular, sequential architecture:

1. **Data Acquisition** (`data_provider.py`): Universe definition and data retrieval
2. **Feature Engineering** (`feature_engine.py`): Financial ratios and technical indicators
3. **Screening Logic** (`selector_logic.py`): Layered quantitative filters
4. **Ranking & Output** (`agent_output.py`): Composite scoring and reporting

## Enhanced Data Provider with CSV Storage

The ESA now includes an enhanced data provider that collects data once and saves it to CSV files for efficient reuse:

### Key Features
- **Run Once, Use Many**: Collect data once and save to CSV files
- **Intelligent Caching**: Uses yfinance-cache for smart data management  
- **Automatic Refresh**: Checks data age and refreshes when needed
- **Easy Access**: Simple functions to access stored data
- **Sector Filtering**: Built-in sector-based data filtering

### Quick Start with Enhanced Data Provider

```bash
# Install yfinance-cache for better performance
pip install yfinance-cache

# Run data collection (creates CSV files in data/ directory)
python collect_data.py

# Or use the convenience function
python -c "from src.data_provider_enhanced import run_full_data_collection; run_full_data_collection(save_to_csv=True)"
```

### Using CSV Data in Other Scripts

Instead of calling fetch functions repeatedly, other scripts should use the CSV data:

```python
# NEW: Use CSV-based data access (recommended)
from data_access import get_universe, get_price_data, get_fundamental_data

# Get universe data
universe_df = get_universe()

# Get price data for specific tickers  
price_data = get_price_data(['AAPL', 'MSFT', 'GOOGL'])

# Get fundamental data
fund_data = get_fundamental_data(['AAPL', 'MSFT', 'GOOGL'])

# Get sector-specific data
from data_access import get_sector_data
tech_universe, tech_prices, tech_fundamentals = get_sector_data('Technology')
```

### Data Files Created

After running data collection, these CSV files are created in the `data/` directory:

- `full_universe_tickers.csv` - Investment universe with sector/industry data
- `price_data_1y_1d_latest.csv` - Historical price data (OHLCV) for all tickers
- `fundamental_data_latest.csv` - Key fundamental metrics for all tickers

### Benefits Over Original Implementation

- **50-80% fewer API calls** through intelligent caching
- **2-5x faster** data retrieval from CSV files
- **Market-aware updates** (only when markets are open)
- **Automatic split/dividend adjustments** in cached data
- **Data persistence** across application restarts

### Integration with ESA Components

```python
# In selector_logic.py or feature_engine.py
from data_access import get_universe, get_fundamental_data, get_price_data

def your_analysis_function():
    # Use CSV data instead of calling APIs directly
    universe = get_universe()
    fundamentals = get_fundamental_data()
    prices = get_price_data(universe['ticker'].tolist())
    
    # Your analysis logic here
    return results
```

## Installation

### Prerequisites

- Python 3.8+
- pip package manager

### Required Dependencies

```bash
pip install yfinance
pip install pandas
pip install pandas-ta
pip install pytickersymbols
pip install numpy
```

### Installation Commands

```bash
# Clone or download the project
cd equity_selection_agent

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```bash
# Run with default settings (US S&P 500 stocks)
python main.py

# Select from specific regions
python main.py --regions US

# Filter by sectors
python main.py --sectors Technology Financial

# Select top 50 stocks instead of default 25
python main.py --target-count 50

# Enable verbose logging
python main.py --verbose
```

### Advanced Usage

```bash
# Force refresh of cached data
python main.py --force-refresh

# Custom output directory
python main.py --output-dir ./custom_results

# Enable qualitative analysis (experimental)
python main.py --enable-qualitative

# Combine multiple options
python main.py --regions US --sectors Technology Healthcare --target-count 30 --verbose
```

## Configuration

The ESA uses a hierarchical configuration system:

1. **Default Configuration**: Built-in sensible defaults
2. **Environment Variables**: Override via `ESA_*` environment variables
3. **Command Line**: Override via command-line arguments

### Key Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `target_stock_count` | 25 | Number of stocks to select |
| `min_roe` | 0.15 | Minimum Return on Equity (15%) |
| `max_debt_equity_absolute` | 1.5 | Maximum Debt-to-Equity ratio |
| `max_beta` | 1.8 | Maximum market risk (Beta) |
| `max_rsi_overbought` | 70.0 | RSI overbought threshold |

### Environment Variable Examples

```bash
export ESA_TARGET_STOCKS=50
export ESA_MIN_ROE=0.20
export ESA_MAX_BETA=1.5
export ESA_WEIGHT_VALUE=0.30
export ESA_WEIGHT_QUALITY=0.25
```

## Output Files

The ESA generates multiple output formats:

### 1. JSON Output (`esa_output_YYYYMMDD_HHMMSS.json`)
Complete machine-readable results with:
- Selected stocks with all metrics
- Screening process details
- Configuration used
- Summary statistics

### 2. CSV Output (`esa_selections_YYYYMMDD_HHMMSS.csv`)
Spreadsheet-friendly format with selected stocks and key metrics

### 3. Audit Log (`run_YYYYMMDD_HHMM.log`)
Detailed execution log with:
- Screening layer breakdown
- Sample exclusion reasons
- Performance statistics
- Configuration summary

## Screening Process

The ESA applies a systematic 6-layer screening process:

1. **Region Filter**: US, HK, or both
2. **Sector Filter**: Industry-specific selection
3. **Quality Screen**: ROE > 15%, positive equity
4. **Risk Screen**: D/E < 1.5, Beta < 1.8, peer-relative risk
5. **Valuation Screen**: P/E below sector average
6. **Technical Screen**: Positive trend, RSI not overbought

## Factor Scoring

Final scores combine five factors with configurable weights:

- **Value (25%)**: P/E and P/B ratios (sector-relative)
- **Quality (20%)**: Return on Equity
- **Risk (20%)**: Beta and Debt-to-Equity (inverse scoring)
- **Momentum (20%)**: Technical indicators
- **Qualitative (15%)**: LLM-based analysis (optional)

## Data Sources and Caching

- **Price Data**: Cached daily via yfinance
- **Fundamental Data**: Cached weekly via yfinance
- **Universe**: S&P 500 via pytickersymbols
- **Cache Location**: `data/cache/` directory

## Extending the ESA

### Custom Sectors

Modify `get_sector_specific_thresholds()` in `config.py` to add sector-specific rules.

### Additional Technical Indicators

Add indicators to `TechnicalAnalyzer` class in `feature_engine.py`.

### Custom Screening Rules

Implement additional screening layers in `EquityScreener` class in `selector_logic.py`.

### Qualitative Analysis

Integrate LLM APIs in the `QualitativeIntegrator` class for business analysis.

## Troubleshooting

### Common Issues

1. **"Import yfinance could not be resolved"**
   - Install: `pip install yfinance`

2. **"No data returned from yfinance"**
   - Check internet connection
   - Try with `--force-refresh` flag

3. **"Insufficient data for technical analysis"**
   - Some stocks may lack sufficient price history
   - These are automatically excluded

4. **Rate limiting errors**
   - The ESA includes automatic delays to respect API limits
   - Consider running during off-peak hours

### Debug Mode

```bash
python main.py --verbose
```

### Cache Management

```bash
# Clear all cached data
rm -rf data/cache/

# Force refresh
python main.py --force-refresh
```

## Development

### Project Structure

```
equity_selection_agent/
├── data/                    # Cached data and universe files
├── logs/                    # Execution logs and reports
├── src/                     # Core source code
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── data_provider.py    # Data acquisition
│   ├── feature_engine.py   # Metric calculations
│   ├── selector_logic.py   # Screening logic
│   └── agent_output.py     # Ranking and reporting
├── tests/                   # Unit tests (future)
├── main.py                  # Main orchestrator
├── README.md               # This file
└── LICENSE.txt             # License information
```

### Running Tests

```bash
# Unit tests (when implemented)
python -m pytest tests/

# Integration test
python main.py --target-count 5 --verbose
```

## Performance Notes

- **Execution Time**: 2-5 minutes for full S&P 500 analysis
- **Memory Usage**: ~200-500 MB depending on universe size
- **Cache Benefits**: Subsequent runs are much faster with cached data
- **API Limits**: Built-in rate limiting respects yfinance constraints

## Version History

- **V1.0**: Initial implementation with full system design specifications

## Contributing

This is an educational/research project. Contributions welcome for:
- Additional technical indicators
- Alternative data sources
- Performance optimizations
- Documentation improvements

## License

See `LICENSE.txt` for full license information.

## Support

This is a research project provided as-is. For questions:
1. Check this README
2. Review the code documentation
3. Examine the generated audit logs
4. Consult the system design document

---

**Remember: This software is for educational purposes only. Always consult qualified financial professionals before making investment decisions.**