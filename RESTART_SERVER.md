# How to Restart the API Server

## Quick Restart

If your API server is running, you need to restart it to pick up the changes:

### Option 1: Using your start script
```bash
./start.sh
```

### Option 2: Manual restart
```bash
# Stop the server (if running)
pkill -f api_server.py

# Start it again
python3 api_server.py
```

### Option 3: Using screen/tmux (if applicable)
```bash
# Reattach to your session
screen -r  # or tmux attach

# Press Ctrl+C to stop the server
# Then run: python3 api_server.py
```

## Verify It's Working

After restarting, try these queries in your web UI:

1. "Who are players on nickroachys IR?"
2. "Whos on Jaxson 5s IR?"

Both should now work perfectly! ✅

## What Was Fixed

The AI now:
- ✅ Recognizes ALL team queries (including IR queries)
- ✅ Handles typos ("Jaxson" finds "Jaxon")
- ✅ Handles possessives ("nickroachys" finds "nickroachy")
- ✅ Uses fuzzy matching for ANY team/owner name mention

See `FUZZY_SEARCH_FIX.md` for full details.


