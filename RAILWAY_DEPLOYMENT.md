# Railway Deployment Guide 🚂

This guide will help you deploy the Fantasy League AI Assistant on Railway.

## Prerequisites

- Railway account (https://railway.app)
- GitHub repository connected
- Supabase database
- OpenAI API key
- Sleeper League ID

## Deployment Steps

### 1. Create a New Project on Railway

1. Go to [Railway](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `sleeper-league-chat` repository

### 2. Configure Environment Variables

In your Railway project settings, add these environment variables:

```
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
OPENAI_API_KEY=your_openai_api_key
SLEEPER_LEAGUE_ID=your_league_id
FLASK_ENV=production
LOG_LEVEL=INFO
```

**Important**: Do NOT set the `PORT` variable - Railway assigns this automatically.

### 3. Deploy Backend (API Server)

Railway will automatically detect the Python application and deploy it using the configuration in:
- `railway.toml` - Railway-specific configuration
- `nixpacks.toml` - Build configuration
- `Procfile` - Start command
- `requirements.txt` - Python dependencies

The API will be available at: `https://your-service-name.up.railway.app`

### 4. Deploy Frontend (Optional - Separate Service)

If you want to deploy the Next.js frontend on Railway:

1. Click "New Service" in your Railway project
2. Select the same GitHub repository
3. Set the **Root Directory** to `web-ui`
4. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-service.up.railway.app
   ```
5. Railway will auto-detect Next.js and deploy it

### 5. Run Initial Data Sync

After deployment, you need to sync your Sleeper data. You have two options:

#### Option A: Run via Railway CLI
```bash
railway run python3 sync_sleeper_data.py
```

#### Option B: Add as a one-time job in Railway
1. In Railway, click your service
2. Go to "Settings" → "Deploys"
3. Add a one-time deployment with command:
   ```
   python3 sync_sleeper_data.py
   ```

### 6. Test Your Deployment

1. Visit your Railway service URL: `https://your-service.up.railway.app/api/health`
2. You should see a health check response
3. Try the chat endpoint or connect your frontend

## Architecture Options

### Option 1: Backend Only on Railway
- Deploy API server on Railway
- Host frontend elsewhere (Vercel, Netlify)
- Frontend connects to Railway API URL

### Option 2: Both on Railway
- Deploy backend as Service 1
- Deploy frontend as Service 2
- Both in same Railway project

### Option 3: Monorepo (Advanced)
- Use Railway's monorepo support
- Deploy both from same service with custom build

## Troubleshooting

### Build Fails with "Error creating build plan"
- Check that `railway.toml` and `nixpacks.toml` are in the root directory
- Verify `requirements.txt` is present
- Ensure Python version is specified in `runtime.txt`

### Environment Variables Not Loading
- Double-check variable names match exactly in Railway dashboard
- Restart the service after adding variables
- Check logs for "Missing required environment variables" error

### Database Connection Issues
- Verify Supabase URL and key are correct
- Check that your Supabase project allows connections from Railway IPs
- Test connection using the health endpoint

### API Returns 500 Errors
- Check Railway logs: Click service → "View Logs"
- Look for Python tracebacks
- Verify all environment variables are set
- Ensure data has been synced to Supabase

## Monitoring & Logs

View logs in Railway:
1. Click your service
2. Click "Logs" tab
3. Use filters to search specific errors

## Cost Considerations

Railway free tier includes:
- $5 credit per month
- Suitable for development/testing
- Pay-as-you-go after credits

For production:
- Monitor usage in Railway dashboard
- Consider upgrading to hobby plan ($5/month + usage)

## Automatic Deployments

Railway automatically deploys when you push to GitHub:
1. Make code changes locally
2. Commit and push to GitHub
3. Railway detects changes and redeploys
4. Check deployment status in Railway dashboard

## Health Check

Your API includes a health endpoint:
```
GET https://your-service.up.railway.app/api/health
```

Use this to:
- Verify deployment is running
- Check environment configuration
- Monitor service status

## Next Steps

1. ✅ Deploy backend to Railway
2. ✅ Set environment variables
3. ✅ Run data sync
4. ✅ Test API endpoints
5. 🎯 Deploy frontend (if hosting on Railway)
6. 🎯 Configure custom domain (optional)
7. 🎯 Set up monitoring and alerts

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Issues: Create an issue in your repository

---

**Ready to deploy?** Push these changes to GitHub and Railway will automatically redeploy! 🚀

