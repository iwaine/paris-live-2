#!/bin/bash

# ============================================================================
# PARIS LIVE - START LIVE MONITORING
# ============================================================================
# Lance le monitoring en temps réel avec log persistant
# ============================================================================

set -e

PROJECT_DIR="/workspaces/paris-live"
APP_DIR="$PROJECT_DIR/football-live-prediction"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
LOG_DIR="$APP_DIR/logs"
LOG_FILE="$LOG_DIR/live_monitoring_$(date +%Y%m%d_%H%M%S).log"

# Telegram Configuration
export TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-8085055094:AAG2DnroWUhR0vISl5XGNND1OZCLm1GF41c}"
export TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-6942358056}"

# Strategy Configuration
export CONFIDENCE_THRESHOLD=0.50
export DANGER_SCORE_THRESHOLD=0.50
export SIGNAL_TTL=300
export UPDATE_INTERVAL=45

# Create log directory
mkdir -p "$LOG_DIR"

echo "=========================================="
echo "🚀 PARIS LIVE - LIVE MONITORING"
echo "=========================================="
echo ""
echo "📊 Configuration:"
echo "   - Strategy: Conservative (50% / 50%)"
echo "   - Expected Win Rate: 35.1%"
echo "   - Signal TTL: 300 seconds"
echo "   - Update Interval: 45 seconds"
echo ""
echo "📝 Log File: $LOG_FILE"
echo ""
echo "Monitoring en cours... (Ctrl+C pour arrêter)"
echo ""

# Start monitoring
cd "$APP_DIR"
$PYTHON_BIN main_live_predictor.py 2>&1 | tee "$LOG_FILE"
