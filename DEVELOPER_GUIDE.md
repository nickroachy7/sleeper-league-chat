# Developer Guide - First-Time Developer Cheat Sheet

Welcome! This guide explains how your Fantasy League AI Assistant works in simple terms. No prior experience required!

## 🗂️ Project Structure

```
Sleeper League Chat/
├── 🐍 PYTHON FILES (Backend - The Brain)
│   ├── api_server.py          # Web server that handles requests
│   ├── fantasy_assistant.py   # AI chat logic with OpenAI
│   ├── dynamic_queries.py     # Database query functions
│   ├── external_stats.py      # NFL stats API integration
│   ├── sync_sleeper_data.py   # Gets data from Sleeper
│   ├── league_queries.py      # Legacy query functions
│   ├── logger_config.py       # Logging setup
│   └── config.py              # Configuration settings
│
├── 🌐 WEB-UI/ (Frontend - The Face)
│   ├── app/
│   │   ├── page.tsx           # Main chat interface
│   │   ├── layout.tsx         # App wrapper
│   │   └── globals.css        # Styles
│   ├── package.json           # JavaScript dependencies
│   └── node_modules/          # JavaScript libraries
│
├── 📊 DATABASE STUFF
│   └── database_improvements.sql  # Database schema
│
├── 🚀 DEPLOYMENT
│   ├── Dockerfile             # Container configuration
│   ├── start.sh              # Startup script
│   ├── requirements.txt       # Python dependencies
│   └── render.yaml           # Deployment config
│
└── 📚 DOCUMENTATION
    ├── README.md              # Main documentation
    ├── PRODUCT_SPEC.md        # What this is
    ├── DEVELOPER_GUIDE.md     # This file!
    └── SYSTEM_OVERVIEW.md     # Architecture diagram
```

## 🧠 How It All Works (The Big Picture)

### Step 1: User Asks a Question
```
You → Type "What are the standings?" → Web UI (page.tsx)
```

### Step 2: Web UI Sends Request
```
Web UI → HTTP POST to http://localhost:5001/api/chat → API Server (api_server.py)
```

### Step 3: AI Processes the Question
```
API Server → Calls fantasy_assistant.py → OpenAI GPT-4o → 
Understands question → Decides which function to call
```

### Step 4: AI Calls Functions
```
AI → "I need standings data" → Calls get_standings() function →
dynamic_queries.py → Queries Supabase database → Returns data
```

### Step 5: AI Formats Response
```
AI → Takes data → Formats as nice table → Returns natural language answer
```

### Step 6: You See the Answer
```
API Server → Sends response back → Web UI displays it → You read it!
```

## 📁 Key Files Explained (What Each Does)

### Backend (Python Files)

#### `api_server.py` - The Web Server
**What it does:** Receives requests from the web UI and sends back responses

**Key endpoints:**
- `POST /api/chat` - Send a message, get AI response
- `POST /api/reset` - Clear conversation history
- `GET /api/health` - Check if server is running

**Think of it as:** The receptionist who takes your question and delivers the answer

#### `fantasy_assistant.py` - The AI Brain
**What it does:** Talks to OpenAI and manages the conversation

**Key function:**
```python
chat(message, conversation_history)
  → Sends message to OpenAI
  → OpenAI decides which function to call
  → Executes function(s)
  → Gets final answer
  → Returns response
```

**Think of it as:** The smart assistant who understands what you're asking

#### `dynamic_queries.py` - Database Functions
**What it does:** Contains all functions that get data from the database

**Key functions:**
- `find_team_by_name()` - Find a team (handles typos!)
- `find_player_by_name()` - Find a player
- `get_recent_trades()` - Get trade history
- `get_weekly_matchups()` - Get matchup results
- `query_with_filters()` - General database queries

**Think of it as:** The librarian who knows where to find every piece of information

#### `external_stats.py` - NFL Stats
**What it does:** Connects to Ball Don't Lie API for real NFL statistics

**Key functions:**
- `get_player_game_stats()` - Player's game performance
- `get_player_season_stats()` - Player's season totals

**Think of it as:** The sports statistician with all the NFL numbers

#### `sync_sleeper_data.py` - Data Sync Script
**What it does:** Fetches data from Sleeper API and saves to database

**Run it with:**
```bash
python3 sync_sleeper_data.py
```

**When to run:** Weekly, to keep data up to date

**Think of it as:** The data collector who updates your records

#### `config.py` - Configuration
**What it does:** Loads settings from `.env` file

**Contains:**
- API keys (OpenAI, Supabase)
- League ID
- Port numbers

**Think of it as:** The settings file

### Frontend (Web UI Files)

#### `web-ui/app/page.tsx` - Chat Interface
**What it does:** The chat page you see in your browser

**Built with:** React (a JavaScript library for building interfaces)

**Key parts:**
- Message display
- Input box
- Send button
- Example questions

**Think of it as:** The user interface you interact with

#### `web-ui/app/layout.tsx` - App Wrapper
**What it does:** Wraps the entire app with common elements

**Contains:**
- Page title
- Favicon
- Font settings
- Global styles

**Think of it as:** The frame around your app

## 🔄 How Data Flows

### Example: "What are the standings?"

```
1. YOU type question in web browser
   ↓
2. WEB UI (page.tsx) sends to API:
   POST /api/chat
   Body: { "message": "What are the standings?", "session_id": "abc123" }
   ↓
3. API SERVER (api_server.py) receives request
   ↓
4. FANTASY ASSISTANT (fantasy_assistant.py) sends to OpenAI:
   "User asked: What are the standings?"
   ↓
5. OPENAI GPT-4o decides:
   "I need to call the query_with_filters() function"
   ↓
6. DYNAMIC QUERIES (dynamic_queries.py) executes:
   query_with_filters(
     table="rosters",
     filters={"league_id": "1180365427496943616"},
     order_column="wins",
     order_desc=True
   )
   ↓
7. SUPABASE DATABASE returns:
   [
     {"team_name": "The Jaxon 5", "wins": 6, "losses": 1, ...},
     {"team_name": "Horse Cock Churchill", "wins": 5, "losses": 2, ...},
     ...
   ]
   ↓
8. OPENAI formats data as table
   ↓
9. API SERVER sends response back to web UI
   ↓
10. WEB UI displays formatted answer
    ↓
11. YOU see the standings table!
```

## 🗄️ Database Structure (Supabase)

Your data is stored in a PostgreSQL database on Supabase. Think of it like Excel spreadsheets:

### Table: `leagues`
Stores league information
```
| league_id | name | season | status |
|-----------|------|--------|--------|
| 118036... | Dynasty Reloaded | 2025 | in_season |
```

### Table: `users`
Stores team owners
```
| user_id | display_name | team_name |
|---------|--------------|-----------|
| abc123  | nickroachy   | Oof That Hurts |
| def456  | seahawkcalvin | The Jaxon 5 |
```

### Table: `rosters`
Stores team rosters and standings
```
| roster_id | wins | losses | players[] | starters[] | reserve[] (IR) |
|-----------|------|--------|-----------|------------|----------------|
| 1         | 6    | 1      | [player1, player2...] | [player1...] | [injured1...] |
```

### Table: `players`
Stores NFL player information
```
| player_id | full_name | position | team |
|-----------|-----------|----------|------|
| 4866      | Patrick Mahomes | QB | KC |
| 7523      | Justin Jefferson | WR | MIN |
```

### Table: `matchups`
Stores weekly scores
```
| week | roster_id | points | matchup_id |
|------|-----------|--------|------------|
| 5    | 1         | 138.59 | 1 |
| 5    | 2         | 64.30  | 1 |
```

### Table: `transactions`
Stores trades and moves
```
| type  | week | adds | drops | draft_picks |
|-------|------|------|-------|-------------|
| trade | 6    | {...} | {...} | [...] |
```

## 🛠️ Common Tasks

### Starting the App

**Option 1: One command (recommended)**
```bash
./start.sh
```

**Option 2: Manual (two terminals)**

Terminal 1 - Start API:
```bash
cd "/Users/n.roach/Desktop/Sleeper League Chat"
python3 api_server.py
```

Terminal 2 - Start Web UI:
```bash
cd "/Users/n.roach/Desktop/Sleeper League Chat/web-ui"
npm run dev
```

Then open: http://localhost:3000

### Updating League Data

Run this weekly:
```bash
python3 sync_sleeper_data.py
```

### Stopping the App

Press `Ctrl+C` in each terminal window

### Checking Logs

If something breaks, check these files (they auto-regenerate):
- `api_server.log` - API server logs
- `app.log` - AI assistant logs

## 🔑 How AI Functions Work

The AI has access to **17 functions** total:
- 13 for fantasy league data (Supabase)
- 4 for NFL stats (Ball Don't Lie)

### Example: How `find_team_by_name()` Works

1. User asks: "Show me Jaxson 5's roster"
2. AI recognizes this needs team data
3. AI calls: `find_team_by_name(team_name_search="Jaxson 5")`
4. Function does fuzzy search in database
5. Finds: "The Jaxon 5" (even though user typed "Jaxson")
6. Returns: roster data with all player IDs
7. AI formats and displays the roster

### Function Definition Format

Functions are defined like this:
```python
{
    "name": "find_team_by_name",
    "description": "Find a team using fuzzy matching...",
    "parameters": {
        "type": "object",
        "properties": {
            "team_name_search": {
                "type": "string",
                "description": "Team name to search for"
            }
        },
        "required": ["team_name_search"]
    }
}
```

OpenAI reads these definitions to know what functions are available!

## 🌐 API Endpoints

Your API server has these endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Check if server is alive |
| `/api/chat` | POST | Send a message, get response |
| `/api/reset` | POST | Clear conversation history |
| `/api/league` | GET | Get basic league info |
| `/api/standings` | GET | Get current standings |

### Example API Call

Using curl:
```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the standings?",
    "session_id": "test-123"
  }'
```

Response:
```json
{
  "response": "Here are the current standings:\n\n| Rank | Team | Record |...",
  "session_id": "test-123"
}
```

## 🐛 Troubleshooting

### "Cannot connect to server"
**Problem:** API server isn't running  
**Solution:** Start it with `python3 api_server.py`

### "OpenAI API error"
**Problem:** API key invalid or out of credits  
**Solution:** Check `.env` file has correct `OPENAI_API_KEY`

### "No data returned"
**Problem:** Database is empty  
**Solution:** Run `python3 sync_sleeper_data.py`

### Changes not showing up
**Problem:** Need to restart server  
**Solution:** Press Ctrl+C and restart

### Web UI not loading
**Problem:** Port 3000 already in use  
**Solution:** Kill other process or change port in `next.config.ts`

## 📚 Technologies Used

### Python Libraries
- `flask` - Web server
- `openai` - Talk to OpenAI API
- `supabase` - Database connection
- `requests` - HTTP requests
- `python-dotenv` - Load environment variables

Install with:
```bash
pip install -r requirements.txt
```

### JavaScript Libraries  
- `next` - React framework
- `react` - UI library
- `tailwindcss` - Styling
- `typescript` - Type safety

Install with:
```bash
cd web-ui && npm install
```

## 🎓 Learning Resources

### If you want to understand the code better:

**Python:**
- Python for Beginners: https://www.python.org/about/gettingstarted/
- Flask Tutorial: https://flask.palletsprojects.com/tutorial/

**JavaScript/React:**
- React Tutorial: https://react.dev/learn
- Next.js Tutorial: https://nextjs.org/learn

**Databases:**
- SQL Basics: https://www.w3schools.com/sql/
- Supabase Docs: https://supabase.com/docs

**AI/OpenAI:**
- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling

## 💡 Key Concepts for Beginners

### What is an API?
**API = Application Programming Interface**

Think of it as a waiter at a restaurant:
- You (client) order food (request)
- Waiter takes order to kitchen (API server)
- Kitchen prepares food (processes request)
- Waiter brings food back (response)

Your `api_server.py` is the waiter!

### What is a Database?
A place to store data permanently. Like a filing cabinet with organized folders.

- **Table** = A folder (e.g., "Rosters")
- **Row** = A document in that folder (e.g., one team's data)
- **Column** = A field on that document (e.g., team name)

### What is Frontend vs Backend?

**Frontend** = What users see and interact with (web-ui/)
- HTML, CSS, JavaScript
- Runs in the browser
- Your `page.tsx` file

**Backend** = Behind-the-scenes logic (Python files)
- Handles requests
- Talks to database
- Processes data
- Your `api_server.py` file

### What is OpenAI Function Calling?

A way for AI to use tools!

Normal AI:
- You: "What's 2+2?"
- AI: "4"

With functions:
- You: "What are the standings?"
- AI: "I need to call `get_standings()` function"
- AI: Calls function, gets data
- AI: "Here are the standings: [data]"

Your assistant has 17 tools (functions) it can use!

## 🎯 What to Explore Next

1. **Read a Python file**: Start with `api_server.py` - it's simple!
2. **Look at a function**: Check out `find_team_by_name()` in `dynamic_queries.py`
3. **Modify the UI**: Change text in `web-ui/app/page.tsx`
4. **Add example questions**: Edit the examples in `page.tsx`
5. **Read the logs**: Watch `api_server.log` while using the app

## 📞 Quick Reference

### File Locations
- **Config**: `config.py` and `.env`
- **Main API**: `api_server.py`
- **AI Logic**: `fantasy_assistant.py`
- **Database Functions**: `dynamic_queries.py`
- **Web Interface**: `web-ui/app/page.tsx`

### Important URLs (when running)
- Web UI: http://localhost:3000
- API Server: http://localhost:5001
- API Health Check: http://localhost:5001/api/health

### Important Commands
```bash
# Start everything
./start.sh

# Start API only
python3 api_server.py

# Start web UI only (in web-ui directory)
npm run dev

# Sync data
python3 sync_sleeper_data.py

# Install Python dependencies
pip install -r requirements.txt

# Install web UI dependencies
cd web-ui && npm install
```

---

**Remember:** Every developer was a beginner once! Take your time, experiment, and don't be afraid to break things (you can always restore from Git). The best way to learn is by doing! 🚀

