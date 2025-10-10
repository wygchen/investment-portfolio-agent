## SetUp
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

## Running the Server
```bash
uvicorn main:app --host 127.0.0.1 --port 8003 --reload
```

## Example frontend assessment data
```json
    sample_frontend_data = {
     "goals": [
         {"id": "retirement", "label": "Retirement Planning", "priority": 1},
         {"id": "house", "label": "Buy a Home", "priority": 2}
     ],
     "timeHorizon": 15,
     "riskTolerance": "moderate",
     "annualIncome": 75000,
     "monthlySavings": 2000,
     "totalDebt": 25000,
     "emergencyFundMonths": "6 months",
     "values": {
         "avoidIndustries": ["tobacco", "weapons"],
         "preferIndustries": ["technology", "renewable_energy"],
         "customConstraints": "Focus on sustainable investments"
     },
     "esgPrioritization": True,
     "marketSelection": ["US", "HK"]
 }
```

## Project Structure
TODO: fill project structure

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