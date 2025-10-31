# 📁 Updated Folder Structure

## Complete Project Structure

```
project/
├── api/                          # Vercel serverless functions
│   └── index.py                 # Main Flask API handler (all routes)
│
├── lib/                          # Shared Python library (used by API)
│   ├── __init__.py
│   ├── config.py                # Configuration with env var fallbacks
│   ├── database.py              # Database initialization & seeding
│   ├── models.py                # SQLAlchemy models (User, Equipment, Comment)
│   └── utils.py                 # Utility functions (password hashing, Excel parsing)
│
├── frontend/                     # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx              # Main app component
│   │   ├── index.jsx            # Entry point
│   │   ├── components/          # React components
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── EquipmentTable.jsx
│   │   │   ├── CommentModal.jsx
│   │   │   └── ExcelImport.jsx
│   │   └── services/
│   │       ├── api.js           # API client (uses /api in production)
│   │       └── socket.js        # Mock socket (serverless-compatible)
│   ├── package.json
│   ├── vite.config.js
│   └── vercel.json              # Frontend build config
│
├── backend/                      # OLD - Keep for local dev if needed
│   └── ...                      # Original Flask app (can be removed)
│
├── vercel.json                   # Main Vercel configuration
├── requirements.txt              # Python dependencies for API
├── README.md                     # Project overview
├── DEPLOY.md                     # Deployment instructions
└── .gitignore                    # Git ignore rules
```

## Key Changes from Original Structure

### ✅ New Files
- `api/index.py` - Single Flask app for all API routes (serverless-compatible)
- `lib/` - Shared Python code used by serverless functions
- `vercel.json` - Vercel deployment configuration
- `DEPLOY.md` - Step-by-step deployment guide

### 🔄 Modified Files
- `frontend/src/services/api.js` - Uses `/api` in production (Vercel routing)
- `frontend/src/services/socket.js` - Mock implementation (no Socket.IO)
- `frontend/package.json` - Removed `socket.io-client` dependency

### 📝 Removed/Deprecated
- Socket.IO functionality (not supported in serverless)
- Render-specific configurations
- Eventlet/async dependencies

## File Descriptions

### API Layer (`api/`)
- **`index.py`**: Main serverless function
  - Exports Flask app for Vercel
  - Handles all `/api/*` routes
  - Auto-initializes database on first request
  - All auth, equipment, and comment endpoints

### Library Layer (`lib/`)
- **`config.py`**: Environment configuration
  - Default values for all env vars
  - SQLite in `/tmp` for serverless
  - CORS configured for all origins

- **`database.py`**: Database setup
  - SQLAlchemy initialization
  - Auto-creates tables
  - Seeds initial data (admin/user accounts)

- **`models.py`**: Data models
  - User (authentication)
  - Equipment (main entity)
  - Comment (related to equipment)

- **`utils.py`**: Helper functions
  - Password hashing/verification
  - Excel parsing
  - Email validation

### Frontend (`frontend/`)
- React SPA built with Vite
- Material-UI components
- Auto-detects API URL (local dev vs production)

## Deployment Flow

1. **Build Frontend**
   ```bash
   cd frontend
   npm run build  # Creates dist/
   ```

2. **Package API**
   - `api/index.py` is loaded as serverless function
   - `lib/` is imported by the function
   - `requirements.txt` provides dependencies

3. **Vercel Routes**
   - `/api/*` → `api/index.py` (serverless function)
   - `/*` → `frontend/dist/*` (static files)

## Environment Variables

All have defaults, but can be set in Vercel:

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `dev-secret-change-in-production` | Flask secret |
| `JWT_SECRET_KEY` | `dev-jwt-secret-change-in-production` | JWT signing key |
| `DATABASE_URL` | `sqlite:////tmp/data.db` | Database connection |
| `VITE_API_BASE_URL` | `/api` (prod) | Frontend API URL |

## Database Location

- **Local Dev**: `backend/app.sqlite3` (or custom path)
- **Vercel**: `/tmp/data.db` (ephemeral)
- **Production**: Set `DATABASE_URL` for persistent storage

