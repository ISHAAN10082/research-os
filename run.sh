#!/bin/bash
# ResearchOS Quick Start - Just run: ./run.sh

# Auto-activate conda env
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate research_os

# Environment fixes for macOS
export DEBATE_MODEL_PATH="mlx-community/phi-3.5-mini-instruct-4bit"
export PYTHONPATH=$PYTHONPATH:.
export KMP_DUPLICATE_LIB_OK=TRUE
export OMP_NUM_THREADS=1
export USE_TF=0
export USE_TORCH=1

echo "🚀 Starting ResearchOS..."
python3 research_os/web/server.py
