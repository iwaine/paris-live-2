#!/bin/bash
# Execute historical scraper in background with monitoring

set -e

PROJECT_DIR="/workspaces/paris-live/football-live-prediction"
VENV_DIR="/workspaces/paris-live/.venv"

echo "🚀 HISTORICAL SCRAPER - EXECUTION START"
echo "========================================"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Ensure output directory exists
mkdir -p "$PROJECT_DIR/data"
mkdir -p "$PROJECT_DIR/logs"

# Run scraper with timeout and logging
LOG_FILE="$PROJECT_DIR/logs/historical_scraper_$(date +%Y%m%d_%H%M%S).log"

echo "📝 Logging to: $LOG_FILE"
echo "Starting scraper at $(date)..." >> "$LOG_FILE"

# Run scraper with Python timeout
timeout 3600 python "$PROJECT_DIR/historical_scraper.py" 2>&1 | tee -a "$LOG_FILE" || {
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo "⏱️  Scraper timed out after 1 hour" >> "$LOG_FILE"
    fi
}

# Check output files
if [ -f "$PROJECT_DIR/historical_matches.csv" ]; then
    MATCH_COUNT=$(tail -n +2 "$PROJECT_DIR/historical_matches.csv" | wc -l)
    echo "✅ Scraper completed. Matches: $(expr $MATCH_COUNT / 2)" >> "$LOG_FILE"
    echo "✅ Scraper completed. Total records: $MATCH_COUNT (labels)"
else
    echo "❌ Output file not created" >> "$LOG_FILE"
fi

echo "========================================"
echo "✅ HISTORICAL SCRAPER - EXECUTION DONE"
