#!/bin/bash

# Backend Startup Script
# This script helps start the backend server without needing conda in PATH

echo "🚀 Starting PortfolioAI Backend Server..."
echo "========================================"
echo ""

# Check if we're in the correct directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found in current directory"
    echo "Please run this script from the backend folder:"
    echo "  cd /Users/limkaixin/Desktop/investment-portfolio-agent-4/backend"
    echo "  ./start-backend.sh"
    exit 1
fi

# Try to find conda
CONDA_PATHS=(
    "$HOME/miniforge3/bin/conda"
    "$HOME/miniconda3/bin/conda"
    "$HOME/anaconda3/bin/conda"
    "/opt/homebrew/Caskroom/miniforge/base/bin/conda"
    "/usr/local/Caskroom/miniforge/base/bin/conda"
)

CONDA_CMD=""
for path in "${CONDA_PATHS[@]}"; do
    if [ -f "$path" ]; then
        CONDA_CMD="$path"
        echo "✅ Found conda at: $path"
        break
    fi
done

if [ -z "$CONDA_CMD" ]; then
    echo "❌ Error: Conda not found in common locations"
    echo ""
    echo "Please find your conda installation:"
    echo "  find ~ -name conda -type f 2>/dev/null | head -5"
    echo ""
    echo "Or install the required packages globally:"
    echo "  python3 -m pip install -r requirements.txt"
    echo ""
    echo "Then run directly:"
    echo "  python3 main.py"
    exit 1
fi

# Initialize conda for this shell
eval "$($CONDA_CMD shell.bash hook)"

# Activate environment
echo "🔄 Activating wx-langgraph-env environment..."
conda activate wx-langgraph-env

if [ $? -eq 0 ]; then
    echo "✅ Environment activated"
    echo ""
    echo "📍 Server starting at: http://127.0.0.1:8000"
    echo "🔗 Frontend should connect from: http://localhost:3000"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo "========================================"
    echo ""
    
    # Start the server
    python main.py
else
    echo "❌ Error: Failed to activate conda environment"
    echo "Please make sure wx-langgraph-env exists:"
    echo "  conda env list"
    exit 1
fi
