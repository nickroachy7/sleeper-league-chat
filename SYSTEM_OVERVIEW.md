# 🏈 Fantasy League AI Assistant - System Overview

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER                                │
│                    (Web Browser)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  WEB UI (Next.js)                           │
│              http://localhost:3000                          │
│  • Beautiful chat interface                                 │
│  • Real-time messaging                                      │
│  • React 19 + TailwindCSS                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ REST API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              API SERVER (Flask)                             │
│             http://localhost:5000                           │
│  • /api/chat - Send messages                                │
│  • /api/standings - Get standings                           │
│  • Session management                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Python
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          AI ASSISTANT (OpenAI GPT-4o)                       │
│  • Natural language understanding                           │
│  • Function calling                                         │
│  • Conversational responses                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Function Calls
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           QUERY FUNCTIONS (league_queries.py)               │
│  1. get_league_info()                                       │
│  2. get_standings()                                         │
│  3. get_team_roster(team_name)                              │
│  4. get_matchup_results(week)                               │
│  5. get_top_scorers(week, limit)                            │
│  6. get_recent_transactions(limit, type)                    │
│  7. search_player(name)                                     │
│  8. get_player_ownership(player_name)                       │
│  9. get_playoff_picture()                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ SQL Queries
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              SUPABASE DATABASE                              │
│       https://scgikyekgjbyenzifdjo.supabase.co              │
│                                                             │
│  📊 Tables:                                                 │
│    • leagues (1 record)                                     │
│    • users (13 records)                                     │
│    • rosters (12 records)                                   │
│    • players (3,968 records)                                │
│    • matchups (84 records)                                  │
│    • transactions (501 records)                             │
└────────────────────────┬────────────────────────────────────┘
                         ▲
                         │
                         │ HTTP API
                         │
┌─────────────────────────────────────────────────────────────┐
│              SLEEPER API                                    │
│           https://api.sleeper.app/v1                        │
│  • League data                                              │
│  • Rosters & users                                          │
│  • Matchups & scores                                        │
│  • Transactions                                             │
│  • Player database                                          │
└─────────────────────────────────────────────────────────────┘
                         ▲
                         │
                         │ Sync Script
┌─────────────────────────────────────────────────────────────┐
│           DATA SYNC (sync_sleeper_data.py)                  │
│  • Fetches from Sleeper API                                 │
│  • Transforms data                                          │
│  • Upserts to Supabase                                      │
│  • Run weekly to update                                     │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Initial Setup
```
Sleeper API → sync_sleeper_data.py → Supabase Database
```

### 2. User Question
```
User → Web UI → API Server → AI Assistant → Query Functions → Supabase → Response
```

## Key Components

### 1. Database Schema (Supabase)

**leagues**
- league_id (PK)
- name, season, status
- scoring_settings, roster_positions
- metadata (JSONB)

**users**
- user_id (PK)
- league_id (FK)
- display_name, team_name
- avatar, metadata

**rosters**
- roster_id, league_id (PK)
- owner_id (FK)
- players[], starters[], reserve[], taxi[]
- wins, losses, ties
- fpts, fpts_against
- waiver_position, total_moves

**players**
- player_id (PK)
- full_name, position, team
- status, injury_status
- metadata (age, experience, etc.)

**matchups**
- id (PK)
- league_id, roster_id, matchup_id, week
- points, players_points
- starters[], players[]

**transactions**
- transaction_id (PK)
- league_id, type, status, week
- creator, adds, drops
- draft_picks, roster_ids

### 2. AI Query Functions

Each function:
1. Accepts parameters from OpenAI
2. Queries Supabase database
3. Transforms data into readable format
4. Returns structured JSON
5. AI formats into natural language

### 3. OpenAI Function Calling

The assistant:
1. Receives user question
2. Determines which function(s) to call
3. Extracts parameters from question
4. Calls function(s)
5. Receives structured data
6. Formats natural response
7. Returns to user

### 4. Web Interface

Built with:
- Next.js 15 (App Router)
- React 19 (Client Components)
- TailwindCSS 4 (Styling)
- TypeScript (Type Safety)

Features:
- Real-time chat
- Message history
- Loading states
- Example questions
- Session management
- Responsive design

## Configuration

All configuration in `config.py`:

```python
# Supabase
SUPABASE_URL = "https://scgikyekgjbyenzifdjo.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "your-key"

# OpenAI
OPENAI_API_KEY = "your-key"

# Sleeper
SLEEPER_LEAGUE_ID = "1180365427496943616"
```

## Deployment Options

### Local (Current Setup)
- API: localhost:5000
- Web: localhost:3000
- Database: Supabase Cloud

### Production Options

**Option 1: Single Server**
- Deploy Flask + Next.js on VPS
- Use PM2 or systemd for processes
- Nginx reverse proxy

**Option 2: Separate Services**
- API: Heroku, Railway, or Render
- Web: Vercel or Netlify
- Database: Supabase (already cloud)

**Option 3: Containers**
- Docker Compose
- API + Web in separate containers
- Deploy to any container platform

## Security Considerations

1. **API Keys**: Stored in config.py (not in version control)
2. **CORS**: Enabled for localhost (restrict in production)
3. **Database**: Using service role key (full access)
4. **OpenAI**: Usage limits based on your account
5. **Rate Limiting**: Not implemented (add for production)

## Performance

- **Database**: Indexed on common queries
- **API**: In-memory session storage (use Redis for scale)
- **Sync**: Batch operations, ~30 seconds full sync
- **AI**: ~2-5 seconds per response
- **Concurrent Users**: Limited by OpenAI rate limits

## Maintenance

### Weekly
```bash
python3 sync_sleeper_data.py  # Update matchups & transactions
```

### Monthly
- Check OpenAI usage/costs
- Review Supabase storage
- Update player database

### As Needed
- Update Python packages
- Update npm packages
- Redeploy after updates

## Extensibility

Easy to add:
- ✅ More query functions
- ✅ Additional data sources
- ✅ Custom analytics
- ✅ Trade analysis
- ✅ Playoff projections
- ✅ Email/SMS notifications
- ✅ Discord bot integration

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Next.js | 15.5.6 |
| Frontend | React | 19.1.0 |
| Frontend | TailwindCSS | 4.0 |
| Backend | Flask | 3.0.0 |
| Backend | Python | 3.9+ |
| Database | Supabase/PostgreSQL | Cloud |
| AI | OpenAI GPT-4o | Latest |
| Data Source | Sleeper API | v1 |

## Costs

- **Supabase**: Free tier (500MB, 2GB egress)
- **OpenAI**: Pay-per-use (~$0.01-0.03 per chat)
- **Sleeper API**: Free
- **Hosting**: Free (local) or $5-20/month (cloud)

**Estimated Monthly Cost**: $5-15 for moderate use

## Success Metrics

✅ **Built Successfully**
- All components working
- Data synced
- AI responding correctly
- Web UI functional

✅ **Tested**
- Database queries working
- Function calling working
- Natural responses
- Error handling

✅ **Ready for Use**
- Complete documentation
- Startup scripts
- User guides
- Full README

---

**Your Dynasty Reloaded AI Assistant is ready to go! 🏈**


