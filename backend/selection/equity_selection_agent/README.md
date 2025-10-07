## Architecture

The ESA follows a modular, sequential architecture with SQLite database storage:

1. **Data Acquisition** (`stock_universe.py`, `stock_database.py`): Universe definition and data retrieval with SQLite storage
2. **Feature Engineering** (`feature_engine.py`): Financial ratios and technical indicators
3. **Screening Logic** (`selector_logic.py`): Layered quantitative filters
4. **Ranking & Output** (`agent_output.py`): Composite scoring and reporting

## Enhanced Data Provider with SQLite Storage

The ESA includes an enhanced data provider that uses SQLite database for efficient storage and incremental updates:

### Key Features
- **SQLite Database**: Efficient storage and querying with `stock_database.py`
- **Incremental Updates**: Smart updates instead of full refreshes
- **Three Operations**: Refresh (full rebuild), Update (incremental), Load (cached)
- **Intelligent Caching**: Price data updated daily, fundamentals updated weekly
- **Data Migration**: Utilities to migrate from existing data sources

### Quick Start with Enhanced Data Provider

```bash
# Initial setup - collect all data
python src/collect_data.py --operation refresh --include-us --include-hk --db-path data/test_stock_data.db

# Daily updates (recommended for cron jobs)
python src/collect_data.py --operation update --db-path data/test_stock_data.db

# Use existing cached data
python src/collect_data.py --operation load --db-path data/test_stock_data.db
```


## Quick Start

### Prerequisites

```bash
# Ensure you have collected data first
python src/collect_data.py --operation refresh --include-us --include-hk --db-path data/test_stock_data.db
```

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
- **Qualitative (15%)**: LLM-based analysis

## Data Sources and Storage

- **Price Data**: Stored in SQLite database, updated daily via yfinance
- **Fundamental Data**: Stored in SQLite database, updated weekly via yfinance  
- **Universe**: S&P 500 components via Wikipedia scraping
- **Database Location**: `data/test_stock_data.db` (SQLite database)
- **Cache Management**: Intelligent incremental updates with configurable refresh intervals

### Database Schema
The SQLite database includes tables for:
- **universe**: Stock tickers with region and sector information
- **price_data**: Historical price data with OHLCV information
- **fundamental_data**: Key financial metrics and ratios
- **metadata**: Data collection timestamps and refresh tracking

## Troubleshooting

### Common Issues

1. **"No module named 'yfinance'"**
   - Install: `pip install yfinance yfinance-cache`

2. **"No data returned from yfinance"**
   - Check internet connection
   - Try with `--force-refresh` flag
   - Check if market is open (some data may be delayed)

3. **"Database locked" or SQLite errors**
   - Ensure no other processes are accessing the database
   - Try deleting `data/test_stock_data.db` and refreshing

4. **"Insufficient data for technical analysis"**
   - Some stocks may lack sufficient price history
   - These are automatically excluded from selection

5. **Rate limiting errors**
   - The ESA includes automatic delays to respect API limits
   - Consider running during off-peak hours
   - Use incremental updates instead of full refreshes

### Debug Mode

```bash
python main.py --verbose
```

### Database Management

```bash
# Force refresh all data (rebuilds SQLite database)
python src/collect_data.py --operation refresh --include-us --include-hk --db-path data/test_stock_data.db

# Incremental update (daily updates)
python src/collect_data.py --operation update --db-path data/test_stock_data.db

# Load existing data without updates
python src/collect_data.py --operation load --db-path data/test_stock_data.db

# Force refresh with main script
python main.py --force-refresh
```

## Development

### Project Structure

```
equity_selection_agent/
├── data/                           # SQLite database and cached data
│   └── test_stock_data.db         # Main SQLite database
├── logs/                          # Execution logs and reports
├── src/                           # Core source code
│   ├── __init__.py
│   ├── config.py                  # Configuration management
│   ├── stock_universe.py          # Universe management and yfinance client
│   ├── stock_database.py          # SQLite database management
│   ├── collect_data.py            # Data collection script
│   ├── data_access.py             # Data access utilities
│   ├── feature_engine.py          # Metric calculations
│   ├── selector_logic.py          # Screening logic
│   └── agent_output.py            # Ranking and reporting
├── tests/                         # Test scripts and examples
│   ├── example_usage.py           # Usage demonstration
│   ├── quick_demo.py              # Quick demo script
│   ├── test_agent.py              # Agent testing
│   └── performance_comparison.py  # Performance analysis
├── main.py                        # Main orchestrator
├── README.md                      # This file
└── SYSTEM DESIGN DOCUMENT*.pdf    # System design documentation
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