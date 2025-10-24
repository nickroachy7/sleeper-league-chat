# Fantasy League AI Assistant - Product Specification

## What Is This?

An AI-powered chatbot that answers questions about your Sleeper fantasy football league using natural language. Ask questions like "Who's in first place?" or "How many touchdowns did AJ Brown score last week?" and get instant answers.

## The Problem It Solves

Fantasy football managers need quick answers about:
- League standings and team performance
- Player ownership and rosters
- Trade history and analysis
- Weekly matchup results
- Real NFL player statistics

Instead of manually checking multiple apps and websites, you can just ask the AI assistant.

## How It Works

```
You type a question → Web UI sends to API → AI understands question → 
Queries database or NFL stats API → Returns formatted answer
```

**Example Flow:**
1. You: "Show me the standings"
2. AI calls `get_standings()` function
3. Retrieves data from Supabase database
4. Formats results as a table
5. Returns: "Here are the current standings..." (with full table)

## Core Features

### 1. Fantasy League Queries (From Supabase Database)
- **Standings**: Current league rankings with records and points
- **Rosters**: View any team's players (active, bench, IR, taxi squad)
- **Matchups**: Weekly scores and results
- **Trades**: Recent trades, player trade history, team trade history
- **Ownership**: Find who owns any player
- **Draft History**: See who drafted players in which season

### 2. Real NFL Stats (From Ball Don't Lie API via MCP)
- Player game statistics (touchdowns, yards, etc.)
- Season totals and averages
- Team performance data
- Injury reports

### 3. Natural Language Interface
- Web UI: Beautiful chat interface (Next.js + React)
- CLI: Command-line version for terminal use
- Context-aware: Remembers conversation history

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Next.js 15, React 19, TailwindCSS | Web chat interface |
| **Backend** | Flask (Python) | API server |
| **AI** | OpenAI GPT-4o | Natural language processing |
| **Database** | Supabase (PostgreSQL) | Fantasy league data storage |
| **Data Sync** | Sleeper API | Pull league data |
| **NFL Stats** | Ball Don't Lie MCP | Real NFL statistics |

## Data Architecture

### Supabase Database Tables
1. **leagues** - League settings and info
2. **users** - Team owners and display names
3. **rosters** - Team rosters with player IDs and standings
4. **players** - NFL player database (3,900+ players)
5. **matchups** - Weekly matchup scores
6. **transactions** - All trades, adds, drops
7. **drafts** - Draft information by season
8. **draft_picks** - Individual draft selections
9. **traded_picks** - Tracked draft pick trades

### Data Sync Process
```bash
python3 sync_sleeper_data.py
```
This script:
1. Fetches latest data from Sleeper API
2. Transforms it for database storage
3. Upserts to Supabase (updates existing, inserts new)
4. Run weekly to keep data current

## Key Capabilities

### Smart Search
- **Fuzzy matching**: "Jaxson 5" finds "The Jaxon 5"
- **Partial names**: "Mahomes" finds "Patrick Mahomes"
- **Owner names**: "seahawkcalvin" finds their team

### Dual Data Sources
The AI automatically routes questions to the right data source:
- Fantasy questions → Supabase
- NFL stats questions → Ball Don't Lie API

### Rich Formatting
- Tables for standings, matchups, trades
- Player details with position and team
- Draft pick resolution (shows who was drafted with traded picks)

## User Experience

### Example Questions You Can Ask

**League Management:**
- "What are the current standings?"
- "Show me week 5 results"
- "Who's on my IR?"
- "What are the recent trades?"

**Player Information:**
- "Who owns Justin Jefferson?"
- "Show me AJ Brown's season stats"
- "Has Cooper Kupp been traded?"
- "Who drafted Patrick Mahomes?"

**Analysis:**
- "How many trades has each team made?"
- "Show me FDR's trade history"
- "What did Team X draft in 2024?"

## Deployment Options

### Local Development (Current)
- API: `http://localhost:5001`
- Web UI: `http://localhost:3000`
- Start with: `./start.sh`

### Production
- Dockerfile included for containerization
- Can deploy to Railway, Render, Heroku, or any container platform
- Environment variables for configuration

## Configuration

All settings in `.env` file (created from config.py):
```bash
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-key
OPENAI_API_KEY=your-openai-key
SLEEPER_LEAGUE_ID=your-league-id
API_PORT=5001
```

## Costs

- **Supabase**: Free tier (sufficient for single league)
- **OpenAI API**: ~$0.01-0.03 per conversation
- **Sleeper API**: Free
- **Ball Don't Lie API**: Free
- **Hosting**: $0 (local) or $5-20/month (cloud)

**Estimated Monthly Cost**: $5-15 for moderate use

## Limitations

1. **Historical NFL data**: Ball Don't Lie API may have limited current season data
2. **Single league**: Currently configured for one Sleeper league
3. **No authentication**: Open access (add auth for multi-user deployment)
4. **Rate limits**: OpenAI and external APIs have usage limits

## Future Enhancements

- Multi-league support
- Trade value analyzer
- Playoff projections
- Discord bot integration
- Email/SMS notifications for trades
- Mobile app
- More sports (NBA, MLB, NFL available via Ball Don't Lie MCP)

## Success Metrics

✅ **Working System**
- All components functional
- Data syncing correctly
- AI responding accurately
- Web UI operational

✅ **Complete Features**
- 13 fantasy league query functions
- 4 NFL stats query functions
- Fuzzy search for teams and players
- Trade history tracking across seasons
- Draft pick resolution

## Your League

**Dynasty Reloaded**
- League ID: `1180365427496943616`
- Format: 12-team Dynasty
- Season: 2025
- Database: Fully synced and operational

---

**Built with ❤️ for fantasy football managers who want instant answers**

