# 🚀 Vercel Deployment Guide for news-pdf2 Branch

## Prerequisites
- GitHub account
- Vercel account (free)
- Railway account (free) - for backend

## Step 1: Deploy Frontend on Vercel

### 1.1 Push to GitHub
```bash
git add .
git commit -m "Prepare for Vercel deployment"
git push origin news-pdf2
```

### 1.2 Deploy on Vercel
1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Click "New Project"
4. Import your repository: `wygchen/investment-portfolio-agent`
5. Select branch: `news-pdf2`
6. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
7. Click "Deploy"

### 1.3 Get Frontend URL
After deployment, you'll get a URL like: `https://your-app-name.vercel.app`

## Step 2: Deploy Backend on Railway

### 2.1 Deploy Backend
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Create new project from GitHub repo
4. Select your repository and `news-pdf2` branch
5. Railway will auto-detect Python/FastAPI
6. Set root directory to `backend`
7. Deploy

### 2.2 Get Backend URL
After deployment, you'll get a URL like: `https://your-backend.railway.app`

## Step 3: Update Frontend API Configuration

### 3.1 Update Environment Variables in Vercel
1. Go to your Vercel project dashboard
2. Click "Settings" → "Environment Variables"
3. Add:
   - `NEXT_PUBLIC_API_URL`: `https://your-backend.railway.app/api`

### 3.2 Redeploy Frontend
1. Go to "Deployments" tab in Vercel
2. Click "Redeploy" on the latest deployment

## Step 4: Test Your Deployment

### 4.1 Test Frontend
- Visit your Vercel URL
- Check if the UI loads correctly
- Test the assessment flow

### 4.2 Test Backend
- Visit `https://your-backend.railway.app/api/health`
- Should return: `{"status": "healthy", "message": "Backend server is running"}`

## Alternative: Deploy Both on Vercel

If you prefer to keep everything on Vercel:

### Option A: Separate Vercel Projects
1. Deploy frontend as one Vercel project
2. Deploy backend as another Vercel project
3. Update frontend to use backend URL

### Option B: Monorepo with Vercel
1. Use the `vercel.json` in the root directory
2. Deploy both frontend and backend together
3. Update API routes to proxy to backend

## Troubleshooting

### Common Issues:
1. **CORS Errors**: Backend CORS is set to allow all origins
2. **API Not Found**: Check environment variables are set correctly
3. **Build Failures**: Check build logs in Vercel dashboard
4. **Environment Variables**: Make sure all env vars are set in Vercel

### Check Logs:
- **Frontend**: Vercel dashboard → Deployments → View Function Logs
- **Backend**: Railway dashboard → Deployments → View Logs

## File Structure After Deployment

```
investment-portfolio-agent/
├── frontend/                 # Deployed on Vercel
│   ├── .env.local           # Environment variables
│   ├── lib/api.ts           # Updated for production
│   └── ...
├── backend/                 # Deployed on Railway
│   ├── main.py              # Updated CORS settings
│   ├── requirements.txt     # Dependencies
│   └── ...
├── vercel.json              # Frontend deployment config
└── DEPLOYMENT_GUIDE.md      # This guide
```

## Success! 🎉

Your website should now be live at:
- **Frontend**: `https://your-app-name.vercel.app`
- **Backend**: `https://your-backend.railway.app`

## Next Steps:
- Test all functionality
- Set up custom domain if desired
- Monitor performance in dashboards
- Set up automatic deployments on git push
