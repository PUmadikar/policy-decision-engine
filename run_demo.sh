#!/bin/bash
set -e

echo "============================================================"
echo "  Starting Policy-Aware RAG Claim Decision Engine"
echo "============================================================"
echo ""

echo "Running End-to-End Evaluation Suite..."
python -m eval.evaluate

echo ""
echo "Starting Streamlit Reviewer Dashboard..."
streamlit run ui/app.py
