#!/bin/bash
# Force cleanup and run verification
echo "🧹 Cleaning up background processes..."
pkill -f "research_os/web/server.py"
pkill -f "verify_production_suite.py"

# Wait for lock release
sleep 2

echo "🚀 Running 30s Verification Suite..."
python3 tests/verify_production_suite.py
