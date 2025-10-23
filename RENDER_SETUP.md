# Deploy to Render.com (Backup Option)

If Railway continues to timeout, Render.com is a great alternative with better Python support.

## Why Render?
- ✅ 20-minute build timeout (vs Railway's 10 minutes)
- ✅ Excellent Python/Flask support
- ✅ Free tier available
- ✅ Fast builds with better caching
- ✅ Auto-detects requirements.txt

## Quick Deploy Steps

### 1. Create Render Account
Go to https://render.com and sign up (free)

### 2. Connect GitHub
- Click "New +" → "Web Service"
- Connect your GitHub account
- Select `sleeper-league-chat` repository

### 3. Configure Service
Render will auto-detect Python. Use these settings:

**Name:** `sleeper-league-api`
**Environment:** `Python 3`
**Build Command:** `pip install -r requirements-prod.txt`
**Start Command:** `python api_server.py`
**Instance Type:** `Free`

### 4. Add Environment Variables
In Render dashboard, add these environment variables:

```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
OPENAI_API_KEY=your_openai_key
SLEEPER_LEAGUE_ID=1180365427496943616
FLASK_ENV=production
PORT=10000
```

### 5. Deploy
Click "Create Web Service" - Render will:
- Clone your repo
- Install dependencies (fast with caching!)
- Deploy your API
- Give you a URL like: `https://sleeper-league-api.onrender.com`

### 6. Test
Visit: `https://your-service.onrender.com/api/health`

## Advantages Over Railway
- Longer build timeout (20 min vs 10 min)
- Better Python caching
- More reliable builds
- Great free tier
- Easier environment variable management

## Run Data Sync
After deployment, you can run the sync script locally and it will populate the Supabase database:

```bash
python3 sync_sleeper_data.py
```

The API will then read from the populated database!

