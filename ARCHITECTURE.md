# System Architecture

Comprehensive architecture documentation for the Fantasy League AI Assistant.

## High-Level Overview

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────────────────────────────┐
│          Load Balancer / CDN            │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌─────────┐         ┌──────────┐
│ Next.js │         │  Flask   │
│Frontend │         │   API    │
│(Port    │         │(Port     │
│ 3000)   │         │  5001)   │
└─────────┘         └────┬─────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ Supabase │   │ OpenAI   │   │ Sleeper  │
   │PostgreSQL│   │   API    │   │   API    │
   └──────────┘   └──────────┘   └──────────┘
```

## Component Architecture

### 1. Frontend (Next.js)

**Purpose:** User interface for chat interactions

**Technology Stack:**
- Next.js 15
- React 19
- TailwindCSS
- TypeScript

**Key Features:**
- Real-time chat interface
- Message history
- Loading states
- Error handling
- Responsive design

**Files:**
- `web-ui/app/page.tsx` - Main chat page
- `web-ui/app/layout.tsx` - App layout wrapper
- `web-ui/app/globals.css` - Global styles

---

### 2. Backend API (Flask)

**Purpose:** REST API server handling requests and orchestrating AI responses

**Technology Stack:**
- Python 3.10+
- Flask 3.0
- OpenAI SDK
- Supabase Client

**Core Modules:**

#### `api_server.py`
- Main Flask application
- Route definitions
- Request/response handling
- Error handling integration

#### `fantasy_assistant.py`
- OpenAI integration
- Function calling orchestration
- Conversation management
- System prompt configuration

#### `dynamic_queries.py`
- Database query functions
- Supabase integration
- Data transformation

#### `validators.py`
- Input validation
- Request sanitization
- Data integrity checks

#### `error_handlers.py`
- Centralized error handling
- Custom exception classes
- Consistent error responses

#### `middleware.py`
- Rate limiting
- API authentication
- Request logging
- Client IP detection

#### `health_checks.py`
- Service health monitoring
- Dependency checking
- Performance metrics

#### `security.py`
- Security utilities
- CORS configuration
- Environment validation
- Security headers

---

### 3. Database (Supabase PostgreSQL)

**Schema:**

```sql
leagues
├── league_id (PK)
├── name
├── season
└── status

users
├── user_id (PK)
├── display_name
├── team_name
└── league_id (FK)

rosters
├── roster_id (PK)
├── league_id (FK)
├── owner_id (FK -> users)
├── wins
├── losses
├── fpts
├── players (JSONB array)
├── starters (JSONB array)
├── reserve (JSONB array - IR)
└── taxi (JSONB array)

players
├── player_id (PK)
├── full_name
├── position
├── team
└── metadata (JSONB)

matchups
├── matchup_id (PK)
├── league_id (FK)
├── week
├── roster_id (FK)
└── points

transactions
├── transaction_id (PK)
├── league_id (FK)
├── type
├── week
├── adds (JSONB)
├── drops (JSONB)
└── draft_picks (JSONB)
```

**Indexes:** See `database_improvements.sql`

---

### 4. External Services

#### OpenAI API
- **Purpose:** Natural language processing and function calling
- **Model:** GPT-4o
- **Integration:** OpenAI Python SDK
- **Rate Limits:** Managed by OpenAI
- **Fallback:** None (required for core functionality)

#### Supabase
- **Purpose:** PostgreSQL database hosting
- **Features Used:** 
  - Database (PostgreSQL)
  - Row-level security
  - Automatic backups
  - RESTful API
- **Fallback:** Health check marks as unhealthy

#### Sleeper API
- **Purpose:** Fantasy football data source
- **Usage:** Data synchronization (sync_sleeper_data.py)
- **Rate Limits:** Not enforced
- **Frequency:** Weekly or on-demand

---

## Security Architecture

### 1. Authentication Layers

```
Request
   │
   ├─► CORS Check (allowed origins)
   │
   ├─► Rate Limiting (per IP, per endpoint)
   │
   ├─► API Key Validation (optional, if configured)
   │
   ├─► Input Validation (request body/params)
   │
   └─► Request Processing
```

### 2. Security Features

- **CORS:** Configurable allowed origins
- **Rate Limiting:** Per-endpoint, IP-based
- **API Authentication:** Optional API key
- **Input Validation:** All inputs sanitized
- **Security Headers:** CSP, X-Frame-Options, HSTS, etc.
- **Environment Validation:** Startup checks
- **XSS Prevention:** Input sanitization

### 3. Secret Management

**Development:**
- `.env` file (gitignored)
- Local configuration

**Production:**
- Platform environment variables
- Secrets manager (AWS, 1Password, etc.)

---

## Data Flow

### Chat Request Flow

```
1. User sends message in frontend
   │
   ├─► POST /api/chat
   │   ├─ Validate request (validators.py)
   │   ├─ Check rate limit (middleware.py)
   │   └─ Log request (middleware.py)
   │
2. API processes request
   │
   ├─► fantasy_assistant.chat()
   │   ├─ Build conversation context
   │   ├─ Call OpenAI API
   │   └─ Receive response/tool calls
   │
3. If tool calls needed
   │
   ├─► Execute functions (dynamic_queries.py)
   │   ├─ Query Supabase
   │   ├─ Transform data
   │   └─ Return results
   │
   ├─► Send results to OpenAI
   │   └─ Get formatted response
   │
4. Return response to client
   │
   └─► JSON response with:
       ├─ Response text
       ├─ Session ID
       └─ Message count
```

---

## Monitoring & Observability

### Health Checks

**Basic Health (`/api/health`):**
- Service status
- Active sessions
- Version info
- Fast (<10ms)

**Detailed Health (`/api/health/detailed`):**
- Database connectivity + latency
- OpenAI API connectivity
- Memory usage
- Disk usage
- Slower (100-500ms)

### Logging

**Log Levels:**
- `DEBUG`: Development debugging
- `INFO`: General information, request/response
- `WARNING`: Security warnings, degraded service
- `ERROR`: Errors with stack traces

**Log Destinations:**
- `app.log` - General application logs
- `api_server.log` - API server logs
- stdout - Container/platform logs

### Metrics

**Performance Metrics:**
- Request duration (via request_logger)
- Rate limit hit rate
- Database query latency
- OpenAI API latency

**Business Metrics:**
- Active sessions
- Messages per session
- Most used endpoints
- Error rates

---

## Scalability

### Current Architecture

**Stateless API:**
- Conversation history in memory
- No sticky sessions required
- Horizontal scaling ready

**Limitations:**
- In-memory conversation storage
- In-memory rate limiting

### Scaling Strategy

#### Horizontal Scaling (1-10 instances)
**Current:** Single instance  
**Target:** Auto-scaling 2-10 instances

**Requirements:**
- Shared Redis for rate limiting
- Shared Redis for conversation storage

#### Vertical Scaling
**Memory:** 512MB → 1GB → 2GB  
**CPU:** 1 core → 2 cores

**Triggers:**
- Memory >75% consistently
- Response time >1s
- Rate limit errors increasing

---

## Performance Characteristics

### Latency Targets

| Endpoint | Target | Typical |
|----------|--------|---------|
| `/api/health` | <50ms | ~10ms |
| `/api/health/detailed` | <500ms | ~200ms |
| `/api/chat` (simple) | <2s | ~1s |
| `/api/chat` (complex) | <5s | ~2-3s |
| `/api/league` | <200ms | ~100ms |
| `/api/standings` | <200ms | ~100ms |

### Throughput

**Current Capacity (single instance):**
- 30 chat requests/min/IP
- 60 data requests/min/IP
- ~500 concurrent sessions

**Bottlenecks:**
1. OpenAI API rate limits
2. Database connection pool
3. Memory (conversation storage)

---

## Deployment Architecture

### Development

```
Local Machine
├── api_server.py (Flask)
├── Next.js dev server
├── .env file
└── Local development
```

### Production (Railway/Render)

```
Cloud Platform
├── Container (Docker)
│   ├── Python 3.10
│   ├── Flask API
│   └── Gunicorn (optional)
├── Environment Variables
├── SSL/TLS (automatic)
└── CDN (optional)

Separate Frontend Deployment
├── Vercel/Netlify
├── Next.js Production
└── API_URL → Backend
```

---

## Error Handling Strategy

### Error Categories

1. **Client Errors (4xx)**
   - 400: Validation errors
   - 401: Authentication required
   - 404: Not found
   - 405: Method not allowed
   - 429: Rate limit exceeded

2. **Server Errors (5xx)**
   - 500: Internal server error
   - 503: Service unavailable

### Error Response Format

```json
{
  "error": "Error type",
  "message": "Human-readable message",
  "field": "field_name (if applicable)",
  "status_code": 400
}
```

### Recovery Strategies

- **Database errors:** Return 503, log, retry
- **OpenAI errors:** Return 500, log, user retry
- **Validation errors:** Return 400, clear message
- **Rate limits:** Return 429 with retry-after

---

## Testing Strategy

### Unit Tests
- Validators
- Middleware
- Health checks
- Utility functions

### Integration Tests
- API endpoints
- Database queries
- External API mocks

### End-to-End Tests
- Full request flow
- Multi-turn conversations
- Error scenarios

### CI/CD Pipeline
- Linting (Black, Ruff)
- Security (Bandit, Safety)
- Tests (pytest)
- Code coverage
- Deployment

---

## Dependencies

### Production (`requirements-prod.txt`)
- flask==3.0.0
- flask-cors==4.0.0
- openai==1.12.0
- supabase==2.3.4
- requests==2.31.0
- python-dotenv==1.0.0
- psutil==5.9.6

### Development (additional)
- pytest==7.4.3
- pytest-cov==4.1.0
- black==23.12.1
- ruff==0.1.9
- bandit==1.7.6

---

## Future Enhancements

### Phase 1: Optimization
- [ ] Redis for distributed rate limiting
- [ ] Redis for conversation storage
- [ ] Response caching
- [ ] Database query optimization

### Phase 2: Features
- [ ] Multi-league support
- [ ] User authentication
- [ ] Email notifications
- [ ] Discord bot integration

### Phase 3: Scale
- [ ] Distributed tracing (Jaeger)
- [ ] Metrics (Prometheus)
- [ ] Auto-scaling rules
- [ ] Multi-region deployment

---

**Version:** 1.0.0  
**Last Updated:** 2025-10-24

