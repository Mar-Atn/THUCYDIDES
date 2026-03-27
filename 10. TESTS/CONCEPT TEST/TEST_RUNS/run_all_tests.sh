#!/bin/bash
# TTT Concept Test -- Run 4 simulations with different random seeds
# Each run produces a subdirectory with per-round JSON outputs and a final analysis.

cd "$(dirname "$0")"

echo "============================================="
echo "  TTT Concept Test: 4 Simulation Runs"
echo "============================================="
echo ""

echo "--- Run 1 (seed=42) ---"
python3 run_test.py run_1 42 6
echo ""

echo "--- Run 2 (seed=123) ---"
python3 run_test.py run_2 123 6
echo ""

echo "--- Run 3 (seed=777) ---"
python3 run_test.py run_3 777 6
echo ""

echo "--- Run 4 (seed=2026) ---"
python3 run_test.py run_4 2026 6
echo ""

echo "============================================="
echo "  All runs complete."
echo "  Results in: run_1/ run_2/ run_3/ run_4/"
echo "============================================="
