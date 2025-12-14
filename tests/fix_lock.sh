#!/bin/bash
# Force cleanup all Kuzu-related processes and files
echo "🔫 Killing all Kuzu processes..."
pkill -9 -f kuzu 2>/dev/null || true
pkill -9 -f python 2>/dev/null || true

echo "🧹 Cleaning temp directories..."
find /tmp -name "*kuzu*" -type d -exec rm -rf {} + 2>/dev/null || true
find /var/folders -name "*jrvis*" -type d -exec rm -rf {} + 2>/dev/null || true

echo "🗑️  Removing lock files..."
find . -name "*.lock" -delete 2>/dev/null || true
find ~/.cache/huggingface -name "*.lock" -delete 2>/dev/null || true
find ~/.gemini/antigravity/brain -name "*.lock" -delete 2>/dev/null || true



echo "🚀 Starting fresh verification..."

# 1. Run Infra Verification (Isolated) -> Should PASS
echo "👉 Running Infra Verification..."
python3 tests/verify_production_suite.py
RET_INFRA=$?

# 2. Run AI Verification (Isolated) -> Should PASS (if env is good)
echo "👉 Running AI Verification (FastEmbed)..."
export KMP_DUPLICATE_LIB_OK=TRUE
python3 tests/verify_fastembed.py
RET_AI=$?

if [ $RET_INFRA -eq 0 ] && [ $RET_AI -eq 0 ]; then
    echo "✅ ALL SYSTEMS GO"
    exit 0
else
    echo "❌ VERIFICATION FAILED"
    echo "Infra: $RET_INFRA"
    echo "AI: $RET_AI"
    exit 1
fi
