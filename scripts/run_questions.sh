#!/bin/bash
# Redirect stdin from /dev/null so Python does not crash with
# "Bad file descriptor" when run via nohup (stdin is closed).
exec < /dev/null

cd /Users/colizej/Documents/webApp/prava
for law in 1975 1968 1976 1998 2005 2006 1968b 1985 1989 2001; do
    echo "=== LAW $law ==="
    venv/bin/python3 scripts/pipeline/04_questions.py --law $law
done
echo "=== ALL DONE ==="
