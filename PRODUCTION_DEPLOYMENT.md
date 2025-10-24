# Production Deployment Guide

Complete guide for deploying the Fantasy League AI Assistant to production.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Configuration](#environment-configuration)
3. [Deployment Options](#deployment-options)
4. [Post-Deployment](#post-deployment)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### ✅ Code Quality

- [ ] All tests passing: `pytest tests/ -v`
- [ ] Code linted: `black . && ruff check .`
- [ ] Security scan clean: `bandit -r . && safety check`
- [ ] No secrets in code: Check with `git diff`

### ✅ Configuration

- [ ] Environment variables configured (see `.env.example`)
- [ ] Database migrations applied
- [ ] API keys valid and active
- [ ] CORS origins configured for production domain
- [ ] API authentication enabled (set `API_KEY`)

### ✅ Infrastructure

- [ ] Database accessible from deployment platform
- [ ] SSL/TLS certificates configured
- [ ] Domain DNS configured
- [ ] CDN configured (optional)

---

## Environment Configuration

### Required Environment Variables

```bash
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# AI Service
OPENAI_API_KEY=sk-your-openai-api-key

# League Configuration
SLEEPER_LEAGUE_ID=your-league-id

# Server
API_PORT=5001
FLASK_ENV=production
LOG_LEVEL=INFO
```

### Security Variables (Recommended)

```bash
# API Authentication
API_KEY=your-secure-random-key-here

# CORS Configuration
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Session Security
SESSION_SECRET=your-session-secret-here
```

### Generating Secure Keys

```bash
# Generate API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate session secret
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Deployment Options

### Option 1: Railway (Recommended)

**Pros:** Easy setup, automatic deployments, built-in monitoring  
**Cons:** Costs ~$5-20/month

#### Steps:

1. **Create Railway Account**
   - Visit [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create New Project**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login
   railway login
   
   # Initialize project
   railway init
   ```

3. **Configure Environment**
   - Go to project settings → Variables
   - Add all required environment variables
   - Set `PORT` (Railway provides this automatically)

4. **Deploy**
   ```bash
   # Link to GitHub repo
   railway link
   
   # Deploy
   git push origin main
   ```

5. **Domain Setup**
   - Settings → Domains → Add custom domain
   - Update DNS records as shown
   - SSL certificate auto-provisioned

---

### Option 2: Render

**Pros:** Free tier available, simple setup  
**Cons:** Cold starts on free tier

#### Steps:

1. **Create Render Account**
   - Visit [render.com](https://render.com)
   - Connect GitHub

2. **Create Web Service**
   - New → Web Service
   - Connect repository
   - Configure:
     ```
     Name: fantasy-assistant-api
     Environment: Python 3
     Build Command: pip install -r requirements-prod.txt
     Start Command: python api_server.py
     ```

3. **Environment Variables**
   - Add all required variables in Environment section
   - Set `PORT` to 5001 or use Render's default

4. **Deploy**
   - Click "Create Web Service"
   - Automatic deployment on git push

---

### Option 3: Docker (Any Platform)

**Pros:** Platform agnostic, reproducible  
**Cons:** Requires container orchestration knowledge

#### Build Image:

```bash
# Build
docker build -t fantasy-assistant-api .

# Test locally
docker run -p 5001:5001 \
  -e SUPABASE_URL=$SUPABASE_URL \
  -e SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e SLEEPER_LEAGUE_ID=$SLEEPER_LEAGUE_ID \
  -e API_KEY=$API_KEY \
  fantasy-assistant-api
```

#### Deploy to Docker Hub:

```bash
# Tag
docker tag fantasy-assistant-api username/fantasy-assistant-api:latest

# Push
docker push username/fantasy-assistant-api:latest
```

#### Deploy Platforms:
- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Instances**
- **DigitalOcean App Platform**

---

### Option 4: Heroku

**Pros:** Easy setup, good documentation  
**Cons:** Costs increased, limited free tier

#### Steps:

1. **Install Heroku CLI**
   ```bash
   brew install heroku/brew/heroku  # macOS
   ```

2. **Create App**
   ```bash
   heroku create fantasy-assistant-api
   ```

3. **Configure**
   ```bash
   heroku config:set SUPABASE_URL=$SUPABASE_URL
   heroku config:set SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY
   heroku config:set OPENAI_API_KEY=$OPENAI_API_KEY
   heroku config:set SLEEPER_LEAGUE_ID=$SLEEPER_LEAGUE_ID
   heroku config:set API_KEY=$API_KEY
   heroku config:set FLASK_ENV=production
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

---

## Post-Deployment

### 1. Verify Deployment

```bash
# Health check
curl https://your-domain.com/api/health

# Detailed health (with external services)
curl https://your-domain.com/api/health/detailed?include_external=true

# API documentation
open https://your-domain.com/api/docs
```

### 2. Test Functionality

```bash
# Test chat endpoint (with API key)
curl -X POST https://your-domain.com/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"message": "What are the standings?", "session_id": "test"}'

# Test league endpoint
curl https://your-domain.com/api/league \
  -H "X-API-Key: your-api-key"
```

### 3. Configure Frontend

Update your Next.js `.env.local`:

```bash
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

---

## Monitoring & Maintenance

### Health Monitoring

Set up monitoring with:
- **Uptime monitoring:** UptimeRobot, Pingdom
- **Application monitoring:** Sentry, Datadog
- **Log aggregation:** Papertrail, Logtail

### Scheduled Tasks

#### Weekly Data Sync

Set up cron job or scheduled task:

```bash
# Cron (every Monday at 2am)
0 2 * * 1 cd /path/to/app && python sync_sleeper_data.py >> logs/sync.log 2>&1
```

Or use platform-specific schedulers:
- **Railway:** Railway Cron Jobs
- **Render:** Render Cron Jobs
- **Heroku:** Heroku Scheduler addon

### Log Management

```bash
# View logs (Railway)
railway logs

# View logs (Render)
# Check dashboard logs tab

# View logs (Heroku)
heroku logs --tail
```

### Backup Strategy

1. **Database:** Supabase handles automatic backups
2. **Code:** Git repository is source of truth
3. **Configuration:** Store environment variables securely (1Password, AWS Secrets Manager)

---

## Security Best Practices

### 1. API Key Rotation

```bash
# Generate new key
NEW_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Update environment variable
# ... platform-specific commands ...

# Update clients
# Announce downtime window, update, verify
```

### 2. Rate Limiting

Current limits (configured in `middleware.py`):
- Chat: 30 requests/minute
- Reset: 10 requests/minute
- Data endpoints: 60 requests/minute

Adjust based on usage patterns.

### 3. CORS Configuration

Update `ALLOWED_ORIGINS` when adding new domains:

```bash
ALLOWED_ORIGINS=https://domain1.com,https://domain2.com,https://www.domain1.com
```

### 4. Dependency Updates

```bash
# Check for vulnerabilities
safety check

# Update dependencies
pip install --upgrade -r requirements.txt
pip freeze > requirements-prod.txt
```

---

## Performance Optimization

### 1. Caching (Optional)

For high-traffic deployments, add Redis:

```bash
# Install
pip install redis

# Configure
REDIS_URL=redis://your-redis-instance:6379
```

### 2. CDN for Static Assets

Use CDN for Swagger UI assets:
- Currently using CDN (cdn.jsdelivr.net)
- No additional configuration needed

### 3. Database Optimization

```sql
-- Run database improvements
-- See database_improvements.sql
```

---

## Troubleshooting

### Issue: 503 Service Unavailable

**Causes:**
- Database connection failed
- OpenAI API unavailable
- Configuration error

**Solutions:**
```bash
# Check detailed health
curl https://your-domain.com/api/health/detailed?include_external=true

# Check logs
# ... platform-specific ...

# Verify environment variables
# ... platform-specific ...
```

### Issue: 429 Rate Limit Exceeded

**Solution:** Adjust rate limits in `middleware.py` or implement Redis-based distributed rate limiting.

### Issue: CORS Errors

**Solution:** 
1. Check `ALLOWED_ORIGINS` environment variable
2. Verify frontend URL matches exactly (including protocol and port)
3. Check browser console for specific error

### Issue: High Memory Usage

**Solution:**
```bash
# Check memory status
curl https://your-domain.com/api/health/detailed

# Scale up instance
# ... platform-specific ...

# Clear conversation history periodically
```

---

## Scaling

### Horizontal Scaling

Most platforms support automatic scaling:

```bash
# Railway: Auto-scaling in settings
# Render: Configure instance count
# Heroku: heroku ps:scale web=2
```

### Vertical Scaling

Upgrade instance size when:
- Memory usage consistently >75%
- Response times >1s
- Rate limit errors increasing

---

## Cost Estimation

### Monthly Costs (Approximate)

| Service | Tier | Cost |
|---------|------|------|
| **Hosting** |
| Railway (Starter) | 500 hours | $5 |
| Render (Starter) | Free/Paid | $0-7 |
| Heroku (Hobby) | Dyno | $7 |
| **Services** |
| Supabase (Free) | 500MB DB | $0 |
| OpenAI API | Usage-based | $10-50 |
| **Total** | - | **$15-65/month** |

### Cost Optimization

1. Use free tiers where possible
2. Monitor OpenAI token usage
3. Implement caching for repeated queries
4. Use efficient prompts

---

## Support & Resources

- **Documentation:** `/api/docs` endpoint
- **Health Status:** `/api/health/detailed`
- **Logs:** Check platform-specific dashboards
- **Issues:** GitHub repository issues page

---

**Last Updated:** 2025-10-24  
**Version:** 1.0.0

