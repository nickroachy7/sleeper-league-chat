# 🏈 Fantasy League AI Assistant

A **production-grade** AI-powered assistant for Sleeper fantasy football leagues with enterprise-level architecture, security, and monitoring.

## 🌟 Features

### Core Functionality
- **AI Chat Interface**: Natural language queries powered by OpenAI GPT-4o
- **Real-time League Data**: Automatic data sync from Sleeper API
- **Comprehensive Analytics**: Standings, rosters, matchups, trades, player stats
- **Beautiful Web UI**: Modern React/Next.js interface with TailwindCSS

### Production Features ✨
- **Rate Limiting**: Per-endpoint, IP-based protection (30-60 req/min)
- **API Authentication**: Optional API key security
- **Input Validation**: Comprehensive request validation and sanitization
- **Health Monitoring**: Basic + detailed health checks with metrics
- **API Documentation**: Interactive Swagger UI at `/api/docs`
- **Security Headers**: CSP, HSTS, X-Frame-Options, etc.
- **Error Handling**: Centralized error management with structured logging
- **CI/CD Pipeline**: Automated testing, linting, and security scans
- **Multi-platform Deployment**: Railway, Render, Docker, Heroku ready

## 🎯 Deployment Options

This project can be deployed in two ways:

### Option 1: Full Stack (Python + Next.js) ⭐ Original
Traditional deployment with Flask API backend and Next.js frontend. Full UI experience.
- See instructions below in [Quick Start](#quick-start)

### Option 2: n8n Workflow (No-Code) 🚀 NEW
Deploy as a no-code n8n workflow. No Flask server or Next.js UI needed!
- **Fastest setup**: 5 minutes to chat
- **Easiest to maintain**: Visual workflow editor
- **Built-in chat UI**: No web development required
- **Read**: [N8N_QUICKSTART.md](./N8N_QUICKSTART.md) for 5-minute setup
- **Full guide**: [N8N_DEPLOYMENT_GUIDE.md](./N8N_DEPLOYMENT_GUIDE.md)

## 📚 Documentation

- **[Quick Start](#quick-start)** - Get started in 5 minutes
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System design and architecture
- **[PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)** - Production deployment guide
- **[DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)** - Developer reference
- **[API Documentation](http://localhost:5001/api/docs)** - Interactive Swagger UI (when running)

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Supabase account (free tier works)
- OpenAI API key
- Sleeper fantasy league

### 1. Configuration

Your `config.py` is already set up with:
- Supabase URL and API key
- OpenAI API key
- Sleeper League ID: `1180365427496943616`

### 2. Install Dependencies

```bash
# Python dependencies
pip3 install -r requirements.txt

# Web UI dependencies
cd web-ui
npm install
cd ..
```

### 3. Database Setup

The database schema is already created with these tables:
- `leagues` - League information
- `users` - League members
- `rosters` - Team rosters and standings
- `players` - NFL player data
- `matchups` - Weekly matchup results
- `transactions` - Trades and roster moves

### 4. Sync Data

Run the data sync script to populate your database:

```bash
python3 sync_sleeper_data.py
```

This will sync:
- League information
- All team rosters
- League members
- Weeks 1-7 matchups
- All transactions
- 3,900+ NFL players

### 5. Start the Application

#### Option A: Using the startup script (recommended)

```bash
chmod +x start.sh
./start.sh
```

This starts both the API server and web UI automatically.

#### Option B: Manual startup

Terminal 1 - Start API Server:
```bash
python3 api_server.py
```

Terminal 2 - Start Web UI:
```bash
cd web-ui
npm run dev
```

### 6. Use the Assistant

Open your browser to: **http://localhost:3000**

The API server runs on: **http://localhost:5001**

Try asking questions like:
- "What are the current standings?"
- "Show me week 5 results"
- "Who owns Justin Jefferson?"
- "Show me my roster" (use your team name)
- "What are the recent trades?"
- "Who's in playoff position?"
- "Analyze this trade for me"

## 🛠️ Project Structure

```
Sleeper League Chat/
├── config.py                    # Configuration (API keys, IDs)
├── sync_sleeper_data.py        # Data sync script
├── league_queries.py           # Database query functions
├── fantasy_assistant.py        # OpenAI assistant (CLI version)
├── api_server.py               # Flask REST API
├── start.sh                    # Startup script
├── requirements.txt            # Python dependencies
└── web-ui/                     # Next.js web interface
    ├── app/
    │   ├── page.tsx           # Chat interface
    │   └── layout.tsx         # App layout
    └── package.json           # Node dependencies
```

## 📊 Database Schema

**leagues**: League settings and information  
**users**: League members with team names  
**rosters**: Team rosters with wins/losses and points  
**players**: NFL player metadata (name, position, team)  
**matchups**: Weekly matchup scores  
**transactions**: All league transactions (trades, adds, drops)

## 🤖 AI Functions

The assistant has access to these functions:

1. `get_league_info()` - Basic league information
2. `get_standings()` - Current standings with records
3. `get_team_roster(team_name)` - Specific team's roster
4. `get_matchup_results(week)` - Matchup results for a week
5. `get_top_scorers(week)` - Top scoring teams
6. `get_recent_transactions()` - Recent trades and moves
7. `search_player(name)` - Search for a player
8. `get_player_ownership(player_name)` - Find who owns a player
9. `get_playoff_picture()` - Current playoff standings

## 🔄 Updating Data

To refresh your league data with the latest information:

```bash
python3 sync_sleeper_data.py
```

Run this weekly to keep matchups and transactions up to date.

## 🎨 Web Interface

The web UI features:
- Beautiful gradient background
- Real-time chat interface
- Message history
- Loading indicators
- Responsive design
- Example questions to get started

## 📝 API Endpoints

### Core Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/api/health` | Basic health check | None |
| GET | `/api/health/detailed` | Detailed health + dependencies | 10/min |
| POST | `/api/chat` | Send message to AI | 30/min |
| POST | `/api/reset` | Reset conversation | 10/min |
| GET | `/api/league` | Get league info | 60/min |
| GET | `/api/standings` | Get standings | 60/min |
| GET | `/api/docs` | API documentation (Swagger UI) | None |

### Authentication (Optional)

Include API key in requests when configured:

```bash
# Header
X-API-Key: your-api-key

# Or Bearer token
Authorization: Bearer your-api-key

# Or query parameter
?api_key=your-api-key
```

**Full API documentation:** Visit `/api/docs` when server is running

## 🔒 Security Features

### Implemented Security Measures

- ✅ **Input Validation**: All inputs validated and sanitized
- ✅ **Rate Limiting**: IP-based rate limiting per endpoint
- ✅ **CORS Protection**: Configurable allowed origins
- ✅ **Security Headers**: CSP, HSTS, X-Frame-Options, XSS protection
- ✅ **API Authentication**: Optional API key requirement
- ✅ **Environment Validation**: Startup checks for configuration
- ✅ **Error Handling**: Secure error messages (no sensitive data leaks)
- ✅ **Dependency Scanning**: Automated security checks (Bandit, Safety)

### Configuration

Set these environment variables for production:

```bash
API_KEY=your-secure-api-key
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
FLASK_ENV=production
```

See [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md) for complete security guide.

## 🐛 Troubleshooting

**"Could not connect to server"**
- Make sure the API server is running on port 5001 (check `api_server.log`)
- Verify the web UI is connecting to the correct port in `web-ui/app/page.tsx`
- Check firewall settings aren't blocking the port

**"Missing environment variables"**
- Ensure `.env` file exists in project root
- Copy `.env.example` and fill in your values
- Restart the API server after updating `.env`

**"No data returned"**
- Run `sync_sleeper_data.py` to populate the database
- Verify your Supabase connection in `.env`
- Check database tables exist (run `database_improvements.sql`)

**OpenAI API errors**
- Verify your OpenAI API key is valid in `.env`
- Check you have credits available
- Review `app.log` for detailed error messages

**Performance issues**
- Run `database_improvements.sql` to add indexes
- Check log files for slow queries
- Consider adding Redis caching for production

## 🏗️ Architecture

```
Frontend (Next.js) ←→ API (Flask) ←→ Supabase (PostgreSQL)
                          ↓
                     OpenAI GPT-4o
                          ↓
                     Sleeper API
```

### Technology Stack

**Frontend:**
- Next.js 15, React 19, TypeScript, TailwindCSS

**Backend:**
- Python 3.10+, Flask 3.0, OpenAI SDK, Supabase Client

**Infrastructure:**
- PostgreSQL (Supabase), Docker, GitHub Actions

**Monitoring:**
- Health checks, structured logging, error tracking

**Security:**
- Rate limiting, CORS, input validation, security headers

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design.

## 📊 Testing & Quality

### Test Coverage

```bash
# Run all tests
pytest tests/ -v --cov=.

# Run with coverage report
pytest tests/ -v --cov=. --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Security scan
bandit -r .
safety check
```

### CI/CD

- ✅ Automated testing on push/PR
- ✅ Code quality checks (Black, Ruff)
- ✅ Security scanning (Bandit, Safety)
- ✅ Multi-version Python testing (3.9, 3.10, 3.11)
- ✅ Code coverage reporting
- ✅ Conventional commit enforcement

See [.github/workflows/](./.github/workflows/) for CI/CD configuration.

## 📄 License

This project is for personal use with your fantasy league.

## 🎯 Your League

**Dynasty Reloaded**  
League ID: `1180365427496943616`  
Season: 2025  
Format: 12-team Dynasty  
Database: Connected to Supabase

---

Built with ❤️ for fantasy football fans

