# PortfolioAI Backend API

FastAPI backend for the AI-powered investment portfolio management application.

## Overview

This backend provides REST API endpoints for:
- User risk assessment data collection
- AI-powered portfolio generation and recommendations
- Real-time market data and analytics
- Portfolio risk analysis and stress testing
- Dashboard data aggregation and performance metrics

## Features

- **FastAPI Framework**: Modern, fast web framework with automatic API documentation
- **Comprehensive Endpoints**: Full REST API for frontend integration
- **Data Validation**: Pydantic models for request/response validation
- **CORS Support**: Cross-origin resource sharing for frontend integration
- **Error Handling**: Proper HTTP status codes and error responses
- **Testing Suite**: Comprehensive pytest test coverage
- **Environment Configuration**: Flexible configuration via environment variables

## Project Structure

```
backend/
├── main.py                 # FastAPI application with all endpoints
├── test_main.py           # Comprehensive test suite
├── start_server.py        # Server startup script
├── env.template           # Environment variables template
├── wx-langgraph-env.yml   # Conda environment specification
├── watsonx_utils.py       # Watsonx AI utilities
└── README.md             # This file
```

## Setup Instructions

### 1. Prerequisites
- **Conda** (Miniforge/Anaconda recommended)
- **Python 3.11**
- **Git** (for cloning the repository)

For Windows, ensure PowerShell is configured with conda:
```powershell
conda init powershell
```

### 2. Create Conda Environment

```bash
# From the backend folder
conda env create -f wx-langgraph-env.yml

# Or with mamba (faster):
mamba env create -f wx-langgraph-env.yml
```

### 3. Activate Environment

```bash
conda activate wx-langgraph-env
```

### 4. Configure Environment Variables

```bash
# Copy the template
cp env.template .env

# Edit .env file with your configuration
# At minimum, update:
# - WATSONX_APIKEY (if using AI features)
# - PROJ_ID (Watsonx project ID)
# - SECRET_KEY (for production)
```

### 5. Install Additional Dependencies (if needed)

The conda environment should install all required packages, but if you need to install manually:

```bash
pip install fastapi uvicorn[standard] pytest python-dotenv
```

## Running the Server

### Method 1: Using the startup script (Recommended)
```bash
python start_server.py
```

### Method 2: Direct uvicorn command
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Method 3: Python execution
```bash
python main.py
```

## API Documentation

Once the server is running, you can access:

- **Interactive API Docs (Swagger)**: http://127.0.0.1:8000/docs
- **ReDoc Documentation**: http://127.0.0.1:8000/redoc
- **OpenAPI Schema**: http://127.0.0.1:8000/openapi.json

## API Endpoints

### Core Endpoints
- `GET /` - API information and status
- `GET /health` - Health check endpoint

### Assessment Endpoints
- `POST /api/assessment` - Submit user risk assessment
- `GET /api/assessment/{user_id}` - Retrieve assessment data

### Portfolio Endpoints
- `POST /api/portfolio/generate` - Generate AI portfolio recommendation
- `GET /api/portfolio/{user_id}` - Retrieve portfolio data

### Market Data Endpoints
- `GET /api/market-data/overview` - Market overview and indices
- `GET /api/market-data/assets/{asset_class}` - Asset performance data

### Risk Analytics Endpoints
- `GET /api/risk-analytics/portfolio/{user_id}` - Portfolio risk metrics
- `GET /api/risk-analytics/market-conditions` - Market risk conditions

### Dashboard Endpoints
- `GET /api/dashboard/overview/{user_id}` - Dashboard overview data
- `GET /api/dashboard/performance/{user_id}` - Performance analytics

## Testing

### Run All Tests
```bash
pytest test_main.py -v
```

### Run Specific Test Categories
```bash
# Test basic endpoints
pytest test_main.py::TestBasicEndpoints -v

# Test assessment functionality
pytest test_main.py::TestAssessmentEndpoints -v

# Test portfolio generation
pytest test_main.py::TestPortfolioEndpoints -v

# Test error handling
pytest test_main.py::TestErrorHandling -v
```

### Test Coverage
The test suite includes:
- ✅ Basic endpoint functionality
- ✅ Data validation and error handling
- ✅ Portfolio generation logic
- ✅ Market data endpoints
- ✅ Risk analytics
- ✅ Dashboard functionality
- ✅ Edge cases and boundary testing

## Development

### Adding New Endpoints

1. Define Pydantic models for request/response validation
2. Add endpoint function with proper decorators
3. Include error handling and logging
4. Add corresponding tests in `test_main.py`
5. Update API documentation

### Environment Variables

Key environment variables (see `env.template` for complete list):

```bash
# Server Configuration
HOST=127.0.0.1
PORT=8000
RELOAD=true
LOG_LEVEL=info

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# IBM Watsonx Configuration
WATSONX_APIKEY=your_api_key
WATSONX_URL=https://us-south.ml.cloud.ibm.com
PROJ_ID=your_project_id
```

## Integration with Frontend

The API is designed to work with the Next.js frontend running on `http://localhost:3000`. Key integration points:

1. **Assessment Flow**: Frontend assessment form → `POST /api/assessment`
2. **Portfolio Generation**: Assessment data → `POST /api/portfolio/generate`
3. **Dashboard Data**: User ID → `GET /api/dashboard/overview/{user_id}`
4. **Market Data**: Real-time updates → `GET /api/market-data/overview`

## Production Deployment

For production deployment:

1. Set `ENVIRONMENT=production` in environment variables
2. Update `SECRET_KEY` with a secure random key
3. Configure proper database (update `DATABASE_URL`)
4. Set up proper logging and monitoring
5. Use a production WSGI server like Gunicorn
6. Configure reverse proxy (nginx/Apache)
7. Set up SSL/TLS certificates

## Troubleshooting

### Python Interpreter
If you see a lot of red lines showing missing import, you likely have the wrong python interpreter.
In VS code, ctrl+shift+p, search python: choose interpreter, find your conda environment

### Debugging

Enable debug logging:
```bash
export LOG_LEVEL=debug
python start_server.py
```

## Contributing

1. Follow existing code style and patterns
2. Add tests for new functionality
3. Update documentation
4. Ensure all tests pass before submitting

## License

This project is part of the PortfolioAI application suite.

### b) Edit `.env` with your actual credentials:
```bash
# Use your preferred editor
nano .env  # or: vim .env, code .env, etc.
```

### c) Required credentials:
```dotenv
# Your actual .env should contain:
WATSONX_APIKEY=your-actual-api-key-here
WATSONX_URL=https://us-south.ml.cloud.ibm.com  # or your region
PROJ_ID=your-project-id-here
```

### Where to find your credentials:
- **API Key**: [IBM Cloud API Keys](https://cloud.ibm.com/iam/apikeys)
- **Project ID**: In your Watsonx.ai project settings
- **URL**: Based on your region (us-south, eu-de, eu-gb, jp-tok)

> In Python you can read these via:
> ```python
> from dotenv import load_dotenv; load_dotenv()
> import os
> api_key = os.getenv("WATSONX_APIKEY")
> url = os.getenv("WATSONX_URL")
> project_id = os.getenv("PROJ_ID")
> ```

## 5) Verify the installation

### a) Test package imports:
```bash
conda run -n wx-langgraph-env python -c "
from importlib import import_module
mods = ['langgraph', 'langchain_core', 'langchain_ibm', 'ibm_watsonx_ai', 'pydantic']
for m in mods:
    import_module(m)
print('✓ All core packages import correctly.')
"
```

### b) Test Watsonx connection:
```bash
# This will test your credentials and model access
conda run -n wx-langgraph-env python watsonx_utils.py
```

Expected output:
- ✓ Models created successfully
- ✓ LLM and embedding tests pass

## 6) Run the notebook
```bash
jupyter lab
# In Jupyter: Kernel → Change Kernel → select "wx-langgraph-env"
```

## 7) Troubleshooting

### Common Issues:
- **Solver slow / conflicts** → Use `mamba` instead of `conda` for faster solving
- **Apple Silicon (M1/M2/M3)** → Prefer Miniforge/conda-forge builds
- **Proxy/Firewall** → Set `HTTPS_PROXY`/`HTTP_PROXY` before creating the env
- **Jupyter kernel not showing** → Re-run step 3
- **Import errors** → Ensure you activated the environment: `conda activate wx-langgraph-env`
- **Watsonx connection errors** → Double-check your `.env` credentials
- **Graph visualization errors** → The Mermaid API may be down; visualization is optional

## 8) Update / Rebuild
```bash
# Pull in changes from the YAML (add/remove packages)
conda env update -n wx-langgraph-env -f wx-langgraph-env.yml --prune

# Export a lean, reproducible spec (conda-only history)
conda env export --from-history -n wx-langgraph-env > conda-from-history.yml
```

## 9) Test the Complete Setup

```bash
# Quick integration test
conda run -n wx-langgraph-env python -c "
import os
from dotenv import load_dotenv
load_dotenv()

# Test credentials are loaded
assert os.getenv('WATSONX_APIKEY'), 'WATSONX_APIKEY not found'
assert os.getenv('WATSONX_URL'), 'WATSONX_URL not found'
assert os.getenv('PROJ_ID'), 'PROJ_ID not found'

# Test model creation
from watsonx_utils import create_models_by_config
llm, embeddings = create_models_by_config('default')
print('✓ Complete setup verified!')
"
```

## 10) Optional Dev Tools
If you want formatting/linting:
```bash
conda activate wx-langgraph-env
pip install black ruff
```

---

**You’re set.** Activate the env, load your `.env` secrets, and run the notebook or scripts.
