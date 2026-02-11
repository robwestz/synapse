# 🚀 QUICKSTART GUIDE

## Get Running in 5 Minutes

### Prerequisites

- Docker & Docker Compose installed
- Anthropic API key ([get one here](https://console.anthropic.com/))
- Ahrefs account (to download exports)

### Step 1: Environment Setup

```bash
# Clone or navigate to project
cd competitive-intelligence-maximizer

# Copy environment file
cp .env.example .env

# Edit .env and add your API key
# ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Step 2: Start Services

```bash
# Start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

Services will be running at:
- **Frontend:** http://localhost:3001
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Step 3: Download Ahrefs Data

1. Login to Ahrefs
2. Navigate to your site or competitor
3. Download these reports (CSV format):
   - **Organic Keywords** - All organic rankings
   - **Backlinks** - Link profile
   - **Referring Domains** - Linking domains
   - **SERP Overview** - SERP features for keywords
   - (Any of the 10 supported report types)

### Step 4: Upload Data

1. Go to http://localhost:3001/upload
2. Drag & drop your Ahrefs CSV files
3. Mark YOUR site as "Primary"
4. Mark competitor sites as competitors
5. Wait for processing (30-60 seconds per file)

### Step 5: Run Intelligence Modes

1. Go to http://localhost:3001/modes
2. Select an intelligence mode (e.g., "Cluster Dominance")
3. Click "Analyze"
4. Get AI-powered strategic insights in seconds

---

## Example Workflow

### Scenario: Find Quick SEO Wins

```
1. Upload YOUR Organic Keywords (mark as primary)
2. Upload TOP 3 COMPETITORS' Organic Keywords
3. Run MODE 1.2: Longtail Gap Finder
4. Get list of 847 longtail keywords competitors rank for
5. Sort by volume, filter for low difficulty
6. Create content for top 20 opportunities
7. Profit 🚀
```

### Scenario: Link Building Opportunities

```
1. Upload YOUR Referring Domains (mark as primary)
2. Upload COMPETITORS' Referring Domains
3. Run MODE 3.1: Common Linker Discovery
4. Get list of 87 domains linking to 3+ competitors but not you
5. AI provides pitch angles for each domain
6. Start outreach
7. Acquire high-DR links 🔗
```

---

## Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose logs backend

# Restart services
docker-compose restart backend

# Rebuild if needed
docker-compose build backend
docker-compose up -d backend
```

### Upload fails

- **File too large:** Max 10MB by default (change MAX_UPLOAD_SIZE_MB in .env)
- **Wrong format:** Must be CSV or XLSX
- **Not an Ahrefs export:** File must match one of 10 report types
- **Check logs:** `docker-compose logs backend` for details

### No intelligence modes available

- **No data uploaded:** Upload Organic Keywords or Backlinks first
- **Processing not complete:** Wait for upload to finish processing
- **Check status:** Go to /upload/status/{upload_id}

---

## Advanced Usage

### API Access

```bash
# API docs
open http://localhost:8000/docs

# Example: Execute mode via API
curl -X POST http://localhost:8000/api/v1/intelligence/execute \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "1.1_cluster_dominance",
    "user_id": "your_user_id"
  }'
```

### Batch Processing

```bash
# Upload multiple files
for file in ahrefs_exports/*.csv; do
  curl -X POST http://localhost:8000/api/v1/upload/ahrefs \
    -F "file=@$file" \
    -F "user_id=your_user_id"
done
```

### Run Presets

```bash
# E-commerce pack
curl -X POST http://localhost:8000/api/v1/intelligence/execute-preset/ecommerce_domination?user_id=your_user_id

# SaaS pack
curl -X POST http://localhost:8000/api/v1/intelligence/execute-preset/saas_crusher?user_id=your_user_id
```

---

## What's Next?

1. **Try all 50+ modes** - Each reveals different insights
2. **Compare multiple competitors** - Upload up to 10 competitors
3. **Export results** - Download insights as PDF/CSV
4. **Schedule analysis** - Set up cron jobs for weekly analysis
5. **Build dashboards** - Combine multiple modes for custom views

---

## Getting Help

- **Documentation:** See `/docs` folder
- **API Reference:** http://localhost:8000/docs
- **GitHub Issues:** (link to repo)
- **Examples:** See `/examples` folder

---

**Now go obliterate Ahrefs.** 🔥
