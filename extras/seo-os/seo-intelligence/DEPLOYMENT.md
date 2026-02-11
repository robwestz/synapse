# 🚀 DEPLOYMENT GUIDE

## Production Deployment Options

### Option 1: Docker Compose (Recommended for VPS/Self-Hosted)

#### Prerequisites
- VPS with 4GB+ RAM, 2+ CPU cores
- Docker & Docker Compose installed
- Domain name pointed to your VPS

#### Steps

1. **Clone repository to server**
```bash
ssh user@your-server.com
cd /opt
git clone your-repo-url competitive-intel
cd competitive-intel
```

2. **Configure environment**
```bash
cp .env.example .env
nano .env

# Set these:
ANTHROPIC_API_KEY=sk-ant-api03-your-key
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=https://yourdomain.com
DATABASE_URL=postgresql+asyncpg://postgres:STRONG_PASSWORD@postgres:5432/competitive_intel
SECRET_KEY=generate-strong-secret-key
```

3. **Configure Nginx reverse proxy**
```nginx
# /etc/nginx/sites-available/competitive-intel

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /docs {
        proxy_pass http://localhost:8000/docs;
    }
}
```

4. **Enable site**
```bash
sudo ln -s /etc/nginx/sites-available/competitive-intel /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

5. **Setup SSL with Let's Encrypt**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

6. **Start services**
```bash
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose logs -f backend
```

7. **Setup automatic backups**
```bash
# Add to crontab
crontab -e

# Backup database daily at 2 AM
0 2 * * * /opt/competitive-intel/scripts/backup.sh
```

---

### Option 2: Vercel (Frontend) + Railway (Backend)

#### Frontend (Vercel)

1. **Push to GitHub**
```bash
git push origin main
```

2. **Import to Vercel**
- Go to vercel.com
- Click "New Project"
- Import from GitHub
- Root directory: `frontend`
- Framework preset: Next.js
- Environment variables:
  ```
  NEXT_PUBLIC_API_URL=https://your-backend.railway.app
  ```

3. **Deploy**
- Vercel will auto-deploy on push to main

#### Backend (Railway)

1. **Create Railway project**
- Go to railway.app
- Click "New Project"
- Select "Deploy from GitHub repo"

2. **Add PostgreSQL**
- Click "New"
- Select "Database" → "PostgreSQL"
- Railway will auto-provision

3. **Add Redis**
- Click "New"
- Select "Database" → "Redis"

4. **Configure backend service**
- Root directory: `backend`
- Environment variables:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  DATABASE_URL=${{Postgres.DATABASE_URL}}
  REDIS_URL=${{Redis.REDIS_URL}}
  ENVIRONMENT=production
  ALLOWED_ORIGINS=https://your-frontend.vercel.app
  ```

5. **Deploy**
- Railway will auto-build and deploy

---

### Option 3: AWS (Fully Managed)

#### Architecture
- **Frontend:** S3 + CloudFront
- **Backend:** ECS Fargate
- **Database:** RDS PostgreSQL
- **Cache:** ElastiCache Redis
- **Storage:** S3 for uploads

#### Terraform deployment
```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

See `infrastructure/terraform/README.md` for details.

---

## Environment Variables (Production)

### Critical Variables
```bash
# AI
ANTHROPIC_API_KEY=sk-ant-api03-...  # REQUIRED

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Redis
REDIS_URL=redis://host:6379/0

# Security
SECRET_KEY=GENERATE_STRONG_RANDOM_KEY_HERE
ALLOWED_ORIGINS=https://yourdomain.com

# Environment
ENVIRONMENT=production
DEBUG=false
```

### Optional Variables
```bash
# Voyage AI (better embeddings)
VOYAGE_API_KEY=pa-...

# Monitoring
SENTRY_DSN=https://...

# File Upload
MAX_UPLOAD_SIZE_MB=10
UPLOAD_DIR=/var/lib/competitive-intel/uploads

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

---

## Security Checklist

### Pre-Deployment
- [ ] Change default passwords in `.env`
- [ ] Generate strong `SECRET_KEY`
- [ ] Set `DEBUG=false`
- [ ] Configure `ALLOWED_ORIGINS` to your domain only
- [ ] Enable SSL/HTTPS
- [ ] Setup firewall (UFW or cloud firewall)
- [ ] Restrict database access to localhost/VPC
- [ ] Setup backup strategy

### Post-Deployment
- [ ] Test file upload with 10MB file
- [ ] Test intelligence mode execution
- [ ] Check logs for errors
- [ ] Setup monitoring (Sentry, DataDog, etc.)
- [ ] Setup uptime monitoring (UptimeRobot, Pingdom)
- [ ] Configure alerts for failures
- [ ] Test backup restoration

---

## Monitoring & Logging

### Check application logs
```bash
# Backend
docker-compose logs -f backend

# Celery workers
docker-compose logs -f celery

# Frontend
docker-compose logs -f frontend

# Database
docker-compose logs -f postgres
```

### Health checks
```bash
# Backend health
curl https://yourdomain.com/api/health

# Frontend
curl https://yourdomain.com

# Database
docker exec competitive-intel-db pg_isready
```

### Metrics to monitor
- API response time (p95, p99)
- Error rate
- Database connection pool usage
- Redis memory usage
- Celery queue length
- AI API cost per day

---

## Backup & Recovery

### Database backup
```bash
# Backup
docker exec competitive-intel-db pg_dump -U postgres competitive_intel > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i competitive-intel-db psql -U postgres competitive_intel < backup_20241219.sql
```

### Full backup script
```bash
#!/bin/bash
# scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/competitive-intel"

mkdir -p $BACKUP_DIR

# Backup database
docker exec competitive-intel-db pg_dump -U postgres competitive_intel | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup uploads (if any)
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /tmp/competitive-intel-uploads

# Keep only last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

---

## Scaling

### Horizontal Scaling (Multiple instances)

1. **Frontend:** Vercel auto-scales
2. **Backend:** Add more containers
```yaml
# docker-compose.prod.yml
backend:
  replicas: 3  # Run 3 instances
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 2G
```

3. **Database:** Use read replicas
4. **Celery:** Add more workers
```bash
docker-compose scale celery=5
```

### Vertical Scaling (Bigger machines)

- **4GB RAM** → **8GB RAM**
- **2 CPUs** → **4 CPUs**

### Caching Strategy

- **Redis:** Cache intelligence mode results (1 hour TTL)
- **CDN:** CloudFlare for static assets
- **Database:** pg_bouncer for connection pooling

---

## Cost Estimates

### Self-Hosted VPS
- **VPS:** $20-40/month (Hetzner, DigitalOcean)
- **AI API:** Variable ($50-500/month depending on usage)
- **Total:** $70-540/month

### Serverless (Vercel + Railway)
- **Vercel:** $20/month (Pro plan)
- **Railway:** $20-100/month
- **AI API:** $50-500/month
- **Total:** $90-620/month

### AWS (Production-grade)
- **ECS Fargate:** $50-150/month
- **RDS:** $50-200/month
- **ElastiCache:** $20-50/month
- **S3 + CloudFront:** $10-30/month
- **AI API:** $50-500/month
- **Total:** $180-930/month

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Common issues:
# - DATABASE_URL wrong
# - ANTHROPIC_API_KEY missing
# - Port 8000 already in use

# Restart
docker-compose restart backend
```

### High AI costs
```bash
# Check usage
grep "AI cost" logs/backend.log | awk '{sum+=$NF} END {print sum}'

# Solutions:
# - Use Sonnet instead of Opus where possible
# - Implement more aggressive caching
# - Add rate limiting per user
```

### Database running slow
```bash
# Check connections
docker exec competitive-intel-db psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Add indexes
# See database/optimizations.sql

# Upgrade to larger instance
```

---

## Updates & Maintenance

### Update application
```bash
git pull origin main
docker-compose build
docker-compose up -d
docker-compose restart
```

### Database migrations
```bash
# Run migrations
docker exec competitive-intel-backend alembic upgrade head

# Rollback if needed
docker exec competitive-intel-backend alembic downgrade -1
```

### Update dependencies
```bash
# Backend
cd backend
pip install -r requirements.txt --upgrade

# Frontend
cd frontend
npm update
```

---

## Support & Monitoring

### Setup Sentry (Error tracking)
```bash
# Add to .env
SENTRY_DSN=https://...@sentry.io/...

# Errors auto-reported to Sentry dashboard
```

### Setup UptimeRobot (Uptime monitoring)
- Monitor: https://yourdomain.com/api/health
- Alert: Email/SMS if down

### Setup CloudFlare (CDN + DDoS protection)
- Point domain to CloudFlare
- Enable "Proxy" mode
- Free DDoS protection + CDN

---

**You're now ready to obliterate Ahrefs at scale.** 🚀
