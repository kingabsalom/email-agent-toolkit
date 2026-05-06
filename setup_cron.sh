#!/bin/bash
# Sets up a cron job to run the daily email digest at 7:00am every morning.

PYTHON=$(which python3)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="$SCRIPT_DIR/run_digest.py"
LOG="$SCRIPT_DIR/digest.log"
CRON_LINE="0 7 * * * $PYTHON $RUNNER >> $LOG 2>&1"

if ! crontab -l 2>/dev/null | grep -qF "$RUNNER"; then
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    echo "Cron job added. Digest will run daily at 7:00am."
    echo "Logs will be written to: $LOG"
else
    echo "Cron job already exists — no changes made."
fi

echo ""
echo "To remove the cron job later, run:  crontab -e"
echo "To run the digest manually right now:  $PYTHON $RUNNER"
