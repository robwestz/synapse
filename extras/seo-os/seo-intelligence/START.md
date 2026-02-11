# 🚀 QUICK START GUIDE

## Start Everything in 3 Commands

### Option 1: Docker (Recommended)

```bash
# Start entire stack
docker-compose up -d

# Frontend: http://localhost:3001
# Backend:  http://localhost:8000
# Database: localhost:5432
```

### Option 2: Manual (Development)

```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev

# Terminal 3: Database (if not using Docker)
# Make sure PostgreSQL is running on localhost:5432
```

---

## Complete User Flow Test

### 1. Go to Upload Page
```
http://localhost:3001/upload
```

### 2. Upload Test Data
- Drag & drop Ahrefs CSV files
- Or click "SELECT FILES"
- Select report type for each file
- Mark YOUR site as "Primary"
- Mark competitors as NOT primary
- Click "UPLOAD ALL"

### 3. Browse Modes
```
http://localhost:3001/modes
```
- See all 20 operational modes
- Filter by category
- Search modes
- Click "EXECUTE →" on any LIVE mode

### 4. Execute Intelligence Mode
```
http://localhost:3001/execute
```
- Select mode from dropdown
- Click "EXECUTE ANALYSIS"
- Wait for AI processing
- View strategic insights

---

## Test with Demo Data

If you don't have Ahrefs data, you can test API directly:

```bash
# Test backend health
curl http://localhost:8000/api/health

# Test mode execution (will fail without data)
curl -X POST http://localhost:8000/api/v1/intelligence/execute \
  -H "Content-Type: application/json" \
  -d '{"mode": "1.1_cluster_dominance", "user_id": "demo"}'
```

---

## Environment Variables

Create `.env` in backend folder:

```bash
# Backend .env
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/competitive_intel
ENVIRONMENT=development
DEBUG=true
```

---

## Verify Everything Works

### ✅ Backend Check
```bash
curl http://localhost:8000/api/health
# Expected: {"status": "healthy"}
```

### ✅ Frontend Check
```
Open: http://localhost:3001
# Expected: Homepage with "OBLITERATE AHREFS"
```

### ✅ Database Check
```bash
# If using Docker
docker exec -it competitive-intel-db psql -U postgres -d competitive_intel -c "\dt"
# Expected: List of tables
```

---

## Common Issues

### Frontend won't start
```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### Backend won't start
```bash
cd backend
pip install -r requirements.txt --upgrade
python -m uvicorn app.main:app --reload
```

### Database connection failed
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Or start manually
docker-compose up -d postgres
```

### CORS errors
Make sure backend has:
```python
# backend/app/main.py
ALLOWED_ORIGINS = [
    "http://localhost:3001",
    "http://localhost:3000",
]
```

---

## Development Workflow

### 1. Start Services
```bash
docker-compose up -d postgres redis
cd backend && uvicorn app.main:app --reload &
cd frontend && npm run dev &
```

### 2. Make Changes
- Edit backend: Auto-reloads on save
- Edit frontend: Hot-reloads on save

### 3. Test
- Backend: http://localhost:8000/docs (Swagger)
- Frontend: http://localhost:3001

### 4. Stop Services
```bash
# Stop all
docker-compose down

# Or Ctrl+C in each terminal
```

---

## Ready to Obliterate?

✅ **Backend**: 20 intelligence modes operational
✅ **Frontend**: 3 core pages functional
✅ **Integration**: Upload → Modes → Execute → Results
✅ **Design**: Extraordinary brutalist UI

**Next**: Upload Ahrefs data and start extracting intelligence! 🔥
