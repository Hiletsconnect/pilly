# Railway Deployment Guide

This guide will help you deploy the ESP32 Management System to Railway.

## Prerequisites

1. A [Railway](https://railway.app) account (free tier available)
2. A GitHub account
3. This repository

## Step-by-Step Deployment

### 1. Prepare Repository

1. **Fork or Upload to GitHub**
   - Fork this repository to your GitHub account, OR
   - Create a new repository and push this code

### 2. Deploy to Railway

1. **Go to Railway Dashboard**
   - Visit [railway.app](https://railway.app)
   - Sign in with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your GitHub repos
   - Select your `esp32-management-system` repository

3. **Automatic Detection**
   - Railway will automatically detect:
     - Python runtime
     - `requirements.txt` for dependencies
     - `Procfile` for start command
   - Click "Deploy"

4. **Wait for Build**
   - Initial build takes 2-3 minutes
   - You'll see build logs in real-time
   - When complete, you'll see "Success" status

### 3. Configure Your Deployment

1. **Generate Domain**
   - Click on your deployment
   - Go to "Settings" tab
   - Under "Domains", click "Generate Domain"
   - Your app will be available at `https://your-app-name.railway.app`

2. **Set Environment Variables (Optional)**
   - Go to "Variables" tab
   - Add variables if needed:
     ```
     SECRET_KEY=your-secure-random-key
     ```
   - Railway automatically sets `PORT`

### 4. Verify Deployment

1. **Open Your App**
   - Click the generated domain URL
   - You should see the login page

2. **Login**
   - Username: `admin`
   - Password: `admin123`

3. **Check Dashboard**
   - After login, verify all pages load correctly
   - Dashboard, Devices, Releases, Alarms

## Connecting ESP32 Devices

Once deployed, configure your ESP32 code:

```cpp
const char* SERVER_URL = "https://your-app-name.railway.app";
```

Upload to your ESP32 and it will connect to your Railway deployment!

## Database Persistence

⚠️ **Important:** Railway's free tier uses ephemeral storage. Your SQLite database will reset if:
- You redeploy
- The service restarts
- The container moves

### Solutions for Persistent Storage:

1. **Upgrade to Railway Pro** ($5/month)
   - Includes persistent volumes
   - Add volume in Railway dashboard

2. **Use Railway's PostgreSQL** (Recommended)
   - Add PostgreSQL plugin in Railway
   - Update `app.py` to use PostgreSQL instead of SQLite
   - Connection string available in environment variables

3. **External Database**
   - Use managed PostgreSQL (Supabase, Neon, etc.)
   - Update connection in `app.py`

## Monitoring

Railway provides:
- **Logs**: Real-time application logs
- **Metrics**: CPU, Memory, Network usage
- **Deployments**: History of all deployments

Access these in the Railway dashboard.

## Updating Your Deployment

### Automatic Deployments

Railway automatically redeploys when you push to GitHub:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

Railway detects the push and redeploys automatically!

### Manual Deployment

1. Go to Railway dashboard
2. Click your project
3. Click "Deploy" → "Redeploy"

## Custom Domain (Optional)

1. **Buy a domain** (Namecheap, Google Domains, etc.)

2. **Add to Railway**
   - Go to Settings → Domains
   - Click "Custom Domain"
   - Enter your domain (e.g., esp32.yourdomain.com)

3. **Configure DNS**
   - Add CNAME record:
     ```
     esp32.yourdomain.com → your-app.railway.app
     ```

4. **SSL Certificate**
   - Railway automatically provides SSL
   - Your site will be `https://esp32.yourdomain.com`

## Troubleshooting

### Build Failed
- Check build logs in Railway dashboard
- Verify `requirements.txt` is correct
- Ensure Python version compatibility

### App Won't Start
- Check runtime logs
- Verify `Procfile` is correct
- Check if port binding is working

### Can't Access App
- Verify domain is generated
- Check if deployment is running
- Look for errors in logs

### Database Issues
- SQLite works but is ephemeral
- Consider upgrading to PostgreSQL for persistence

## Cost Estimates

**Railway Free Tier:**
- $5 credit per month
- Good for development and light usage
- Database resets on redeploy

**Railway Pro ($5/month):**
- $5 base + usage
- Persistent volumes
- Better for production
- ~$10-15/month typical usage

## Security Recommendations

1. **Change Default Password**
   - Do this immediately after deployment
   - Access SQLite database via Railway CLI

2. **Set SECRET_KEY**
   - Generate secure key:
     ```python
     import secrets
     print(secrets.token_hex(32))
     ```
   - Add to Railway environment variables

3. **HTTPS Only**
   - Railway provides HTTPS automatically
   - Don't allow HTTP connections from ESP32

4. **Rate Limiting**
   - Consider adding rate limiting to API endpoints
   - Protect against abuse

## Getting Help

- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- Railway Docs: [docs.railway.app](https://docs.railway.app)
- GitHub Issues: [Your repo issues page]

## Next Steps

After deployment:
1. ✅ Change default password
2. ✅ Configure ESP32 devices with your URL
3. ✅ Upload your first firmware
4. ✅ Test OTA updates
5. ✅ Monitor devices in dashboard

Congratulations! Your ESP32 Management System is live! 🎉
