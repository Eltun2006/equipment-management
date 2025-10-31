# 🚀 Vercel Deployment Guide

## Step-by-Step Deployment Instructions

### 1. Prepare Your Repository

Ensure your code is pushed to GitHub/GitLab/Bitbucket:

```bash
git add .
git commit -m "Prepare for Vercel deployment"
git push
```

### 2. Deploy to Vercel

#### Option A: Using Vercel CLI (Recommended)

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy**
   ```bash
   cd project
   vercel
   ```
   
   Follow the prompts:
   - Link to existing project? **No** (first time)
   - Project name: **your-project-name**
   - Directory: **./** (project root)
   - Override settings? **No**

4. **Deploy to Production**
   ```bash
   vercel --prod
   ```

#### Option B: Using Vercel Dashboard

1. Go to [vercel.com](https://vercel.com)
2. Click **"New Project"**
3. Import your Git repository
4. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: `./` (or leave empty)
   - **Build Command**: Leave empty (Vercel auto-detects)
   - **Output Directory**: `frontend/dist`
5. Add Environment Variables (optional):
   - `SECRET_KEY` - A random secret (generate with `openssl rand -hex 32`)
   - `JWT_SECRET_KEY` - Another random secret
6. Click **Deploy**

### 3. Environment Variables (Optional)

Set these in Vercel Dashboard → Settings → Environment Variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `dev-secret-change-in-production` |
| `JWT_SECRET_KEY` | JWT signing key | `dev-jwt-secret-change-in-production` |
| `DATABASE_URL` | Database connection string | SQLite in `/tmp/data.db` |

**Generate secure secrets:**
```bash
# Linux/Mac
openssl rand -hex 32

# Or use Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Verify Deployment

1. Visit your Vercel deployment URL (e.g., `https://your-project.vercel.app`)
2. Test login:
   - Username: `admin`
   - Password: `Admin@123`

### 5. Custom Domain (Optional)

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your custom domain
3. Follow DNS configuration instructions

## 📁 Project Structure

```
project/
├── api/
│   └── index.py              # Vercel serverless function (Flask API)
├── lib/                       # Shared Python library
│   ├── __init__.py
│   ├── config.py             # Configuration with defaults
│   ├── database.py           # Database initialization
│   ├── models.py             # SQLAlchemy models
│   └── utils.py              # Utility functions
├── frontend/                  # React frontend
│   ├── src/
│   ├── package.json
│   └── dist/                  # Build output (created on build)
├── vercel.json                # Vercel configuration
├── requirements.txt           # Python dependencies
└── README.md
```

## 🔧 How It Works

1. **API Routes** (`/api/*`) → Handled by `api/index.py` (Flask serverless function)
2. **Frontend Routes** (`/*`) → Served from `frontend/dist` (static files)
3. **Database** → SQLite stored in `/tmp/data.db` (ephemeral in serverless)

## ⚠️ Important Notes

### Database Persistence

SQLite in `/tmp` is **ephemeral** - data may be lost on:
- Serverless function cold starts
- Deployments
- Function instances spinning down

**For production**, use:
- **Vercel Postgres** (recommended)
- External database (PostgreSQL, MySQL, etc.)
- Set `DATABASE_URL` environment variable

### File Size Limits

- Maximum file upload: 16MB
- Serverless function timeout: 30 seconds (configured in `vercel.json`)

### Socket.IO

Real-time features are disabled (not supported in serverless). Comments still work, but updates require page refresh.

## 🐛 Troubleshooting

### Build Fails

1. Check `vercel.json` configuration
2. Ensure `requirements.txt` has all dependencies
3. Check Vercel build logs

### API Returns 500

1. Check serverless function logs in Vercel Dashboard
2. Verify environment variables are set
3. Check database initialization

### Frontend Can't Connect to API

1. Verify `VITE_API_BASE_URL` is not set (uses `/api` automatically)
2. Check CORS configuration in `api/index.py`
3. Ensure API routes are working (`/api/health`)

### Database Issues

1. SQLite in `/tmp` may not persist - use external database for production
2. Check database initialization in logs
3. Verify SQLAlchemy is creating tables correctly

## 📞 Support

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Python Runtime](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)

## ✨ Success Checklist

- [ ] Code pushed to Git repository
- [ ] Vercel project created
- [ ] Environment variables set (optional but recommended)
- [ ] Deployment successful
- [ ] Can access frontend at Vercel URL
- [ ] Can login with admin credentials
- [ ] API endpoints working (`/api/health`)
- [ ] Database seeding working (initial data visible)

