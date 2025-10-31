# Equipment Management System

Full-stack equipment management application with authentication, comments, and Excel import/export.

## 🚀 Quick Deploy to Vercel

### One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=YOUR_REPO_URL)

### Manual Deployment

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy**
   ```bash
   vercel
   ```

3. **Set Environment Variables** (optional, has defaults)
   - `SECRET_KEY` - Flask secret key (default: dev secret)
   - `JWT_SECRET_KEY` - JWT secret key (default: dev secret)
   - `DATABASE_URL` - Database URL (default: SQLite in /tmp)

   You can set these in Vercel Dashboard → Settings → Environment Variables

## 📁 Project Structure

```
project/
├── api/
│   └── index.py          # Vercel serverless function (Flask API)
├── lib/                  # Shared library code
│   ├── config.py         # Configuration
│   ├── database.py       # Database setup
│   ├── models.py         # SQLAlchemy models
│   └── utils.py          # Utility functions
├── frontend/             # React + Vite frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── vercel.json           # Vercel configuration
└── requirements.txt      # Python dependencies
```

## 🔧 Local Development

### Backend (Flask API)

```bash
cd project
python -m venv .venv
.venv/Scripts/activate  # Windows
# or
source .venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
python -m backend.app  # Runs on http://localhost:5000
```

### Frontend (React)

```bash
cd project/frontend
npm install
npm run dev  # Runs on http://localhost:5173
```

## 🔐 Default Credentials

- **Admin**: `admin` / `Admin@123`
- **User**: `user` / `User@123`

## 📝 Features

- ✅ User authentication (JWT)
- ✅ Equipment management (CRUD)
- ✅ Comments system
- ✅ Excel import/export
- ✅ Search and filtering
- ✅ Admin panel
- ✅ SQLite database (works out of the box)

## 🗄️ Database

The app uses **SQLite** stored in `/tmp/data.db` on Vercel serverless functions.

**Note**: SQLite in `/tmp` is ephemeral in serverless. For production with persistent data, consider:
- Vercel Postgres
- External database (set `DATABASE_URL` env var)
- Vercel KV or Blob storage for SQLite backup

## 🌐 API Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user
- `GET /api/equipment` - List equipment
- `POST /api/equipment/import` - Import Excel
- `GET /api/equipment/export` - Export Excel
- `GET /api/comments/equipment/<id>` - Get comments
- `POST /api/comments` - Add comment

## 🛠️ Tech Stack

- **Backend**: Flask, SQLAlchemy, JWT
- **Frontend**: React, Vite, Material-UI
- **Database**: SQLite (default)
- **Deployment**: Vercel

## 📦 Dependencies

See `requirements.txt` for Python dependencies and `frontend/package.json` for Node dependencies.

## ⚠️ Limitations

- Socket.IO removed (not supported in serverless)
- Real-time updates disabled (comments still work, just no live updates)
- SQLite database resets on serverless function cold starts (use external DB for production)

## 🚀 Production Considerations

1. **Database**: Use Vercel Postgres or external database for persistence
2. **Secrets**: Set `SECRET_KEY` and `JWT_SECRET_KEY` in Vercel environment variables
3. **CORS**: Already configured for all origins (adjust if needed)
4. **File Uploads**: Limited to `/tmp` (16MB max)

## 📄 License

MIT

