# 🚀 Deployment Guide

Complete guide for deploying the Fantasy League AI Assistant to production.

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Deployment Options](#deployment-options)
5. [Post-Deployment](#post-deployment)
6. [Monitoring](#monitoring)
7. [Maintenance](#maintenance)

---

## Pre-Deployment Checklist

Before deploying, ensure:

- ✅ All environment variables are configured
- ✅ Database schema is created
- ✅ Database indexes are added
- ✅ Initial data sync completed
- ✅ All tests passing
- ✅ API keys are valid and funded
- ✅ `.gitignore` is configured
- ✅ Logs directory exists

```bash
# Run pre-deployment checks
python -m pytest tests/ -v
python sync_sleeper_data.py
```

---

## Environment Setup

### 1. Environment Variables

Create production `.env` file:

```bash
# Supabase (production)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-production-key

# OpenAI (with rate limits)
OPENAI_API_KEY=sk-proj-your-production-key

# Sleeper
SLEEPER_LEAGUE_ID=your-league-id

# Server Configuration
API_PORT=5001
WEB_PORT=3000
FLASK_ENV=production

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/fantasy-assistant/app.log
```

### 2. Security Hardening

```bash
# Set proper file permissions
chmod 600 .env
chmod 700 logs/

# Ensure no secrets in git
git status --ignored
```

---

## Database Setup

### 1. Run Schema Migrations

```bash
# Apply database improvements
psql $DATABASE_URL < database_improvements.sql
```

Or via Supabase Dashboard:
1. Go to SQL Editor
2. Paste contents of `database_improvements.sql`
3. Run query

### 2. Initial Data Load

```bash
python sync_sleeper_data.py
```

### 3. Verify Database

```sql
-- Check table counts
SELECT 
    'leagues' as table_name, COUNT(*) as rows FROM leagues
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'rosters', COUNT(*) FROM rosters
UNION ALL
SELECT 'players', COUNT(*) FROM players
UNION ALL
SELECT 'matchups', COUNT(*) FROM matchups
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions;
```

---

## Deployment Options

### Option 1: Traditional VPS (DigitalOcean, Linode, AWS EC2)

**Recommended for: Full control, custom setup**

#### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+
sudo apt install python3.9 python3-pip python3-venv -y

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install nginx
sudo apt install nginx -y

# Install supervisor (process manager)
sudo apt install supervisor -y
```

#### Step 2: Application Setup

```bash
# Create app directory
sudo mkdir -p /var/www/fantasy-assistant
cd /var/www/fantasy-assistant

# Clone or upload your code
git clone your-repo-url .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup web UI
cd web-ui
npm install
npm run build
cd ..

# Create logs directory
sudo mkdir -p /var/log/fantasy-assistant
sudo chown $USER:$USER /var/log/fantasy-assistant
```

#### Step 3: Process Management (Supervisor)

Create `/etc/supervisor/conf.d/fantasy-assistant.conf`:

```ini
[program:fantasy-api]
command=/var/www/fantasy-assistant/venv/bin/python api_server.py
directory=/var/www/fantasy-assistant
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/fantasy-assistant/api-error.log
stdout_logfile=/var/log/fantasy-assistant/api-out.log
environment=PATH="/var/www/fantasy-assistant/venv/bin"

[program:fantasy-web]
command=/usr/bin/npm run start
directory=/var/www/fantasy-assistant/web-ui
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/fantasy-assistant/web-error.log
stdout_logfile=/var/log/fantasy-assistant/web-out.log
```

```bash
# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status
```

#### Step 4: Nginx Configuration

Create `/etc/nginx/sites-available/fantasy-assistant`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Web UI
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:5001/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type' always;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/fantasy-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 5: SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

### Option 2: Docker Deployment

**Recommended for: Containerized, scalable deployment**

#### Dockerfile (API)

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["python", "api_server.py"]
```

#### Dockerfile (Web UI)

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY web-ui/package*.json ./
RUN npm ci

COPY web-ui/ .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5001:5001"
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  web:
    build:
      context: .
      dockerfile: Dockerfile.web
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://api:5001
    depends_on:
      - api
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - api
      - web
    restart: unless-stopped
```

```bash
# Deploy with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Update deployment
docker-compose pull
docker-compose up -d --build
```

---

### Option 3: Platform as a Service (Heroku, Railway, Render)

**Recommended for: Quick deployment, managed infrastructure**

#### Railway Deployment

1. **Create Railway account** at railway.app

2. **New Project from GitHub**
   - Connect your repository
   - Add environment variables

3. **API Service**
   ```toml
   # railway.toml
   [build]
   builder = "NIXPACKS"

   [deploy]
   startCommand = "python api_server.py"
   ```

4. **Web UI Service**
   ```json
   {
     "build": {
       "command": "cd web-ui && npm install && npm run build"
     },
     "deploy": {
       "command": "cd web-ui && npm start"
     }
   }
   ```

5. **Add Environment Variables** in Railway dashboard

---

### Option 4: Serverless (Vercel + Cloud Functions)

**Recommended for: Auto-scaling, pay-per-use**

#### Vercel (for Web UI)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd web-ui
vercel --prod
```

#### AWS Lambda (for API)

1. **Package Lambda function**
```bash
pip install -r requirements.txt -t package/
cd package
zip -r ../lambda-deployment.zip .
cd ..
zip -g lambda-deployment.zip api_server.py league_queries.py
```

2. **Deploy via AWS Console or CLI**

---

## Post-Deployment

### 1. Verify Deployment

```bash
# Check API health
curl https://your-domain.com/api/health

# Check web UI
curl https://your-domain.com

# Test chat endpoint
curl -X POST https://your-domain.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the standings?", "session_id": "test"}'
```

### 2. Setup Automated Data Sync

Create cron job for weekly sync:

```bash
# Edit crontab
crontab -e

# Add weekly sync (Tuesdays at 2 AM)
0 2 * * 2 cd /var/www/fantasy-assistant && /var/www/fantasy-assistant/venv/bin/python sync_sleeper_data.py >> /var/log/fantasy-assistant/sync.log 2>&1
```

### 3. Setup Log Rotation

Create `/etc/logrotate.d/fantasy-assistant`:

```
/var/log/fantasy-assistant/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    sharedscripts
    postrotate
        supervisorctl restart fantasy-api fantasy-web
    endscript
}
```

---

## Monitoring

### 1. Application Monitoring

**Using Sentry (recommended):**

```bash
pip install sentry-sdk
```

Add to `api_server.py`:

```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)
```

### 2. Server Monitoring

**Uptime monitoring:**
- UptimeRobot (free)
- Pingdom
- Better Uptime

**Log monitoring:**
```bash
# Install and configure Promtail + Loki (optional)
# Or use cloud logging (CloudWatch, Stackdriver)
```

### 3. Cost Monitoring

Track API usage:
- OpenAI Dashboard: https://platform.openai.com/usage
- Supabase Dashboard: Usage tab
- Set up billing alerts

---

## Maintenance

### Weekly Tasks

- [ ] Review error logs
- [ ] Check OpenAI costs
- [ ] Verify data sync completed
- [ ] Review system metrics

### Monthly Tasks

- [ ] Update Python dependencies
- [ ] Update Node dependencies
- [ ] Review and archive old logs
- [ ] Database maintenance (vacuum, analyze)
- [ ] Security updates

### As Needed

- [ ] Scale resources if needed
- [ ] Update KTC values
- [ ] Add new features
- [ ] Update player database

---

## Rollback Plan

If deployment fails:

```bash
# Docker
docker-compose down
git checkout previous-version
docker-compose up -d

# Traditional VPS
sudo supervisorctl stop all
git checkout previous-version
sudo supervisorctl start all

# Verify
curl https://your-domain.com/api/health
```

---

## Security Best Practices

1. **API Keys**
   - Use environment variables
   - Rotate keys quarterly
   - Never commit to version control

2. **Database**
   - Use service role key only in backend
   - Enable RLS if exposing Supabase directly
   - Regular backups

3. **Server**
   - Keep OS and packages updated
   - Use firewall (ufw)
   - SSH key authentication only
   - Fail2ban for brute force protection

4. **Application**
   - Rate limiting on API endpoints
   - Input validation
   - HTTPS only
   - CORS properly configured

---

## Troubleshooting Deployment

**Port already in use:**
```bash
sudo lsof -i :5001
sudo kill -9 <PID>
```

**Permission denied:**
```bash
sudo chown -R www-data:www-data /var/www/fantasy-assistant
```

**Service won't start:**
```bash
sudo supervisorctl tail fantasy-api stderr
sudo journalctl -u nginx -n 50
```

**Database connection failed:**
- Check Supabase service status
- Verify connection string
- Check firewall rules

---

## Support

For deployment issues:
1. Check logs: `/var/log/fantasy-assistant/`
2. Review error messages
3. Check GitHub Issues
4. Contact support

---

**Last Updated:** October 22, 2025  
**Maintainer:** Fantasy League AI Team





