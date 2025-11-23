# Deployment Guide

This guide covers deploying AI Resume Analyzer to production environments.

## Table of Contents
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Environment Variables](#environment-variables)
- [Security Considerations](#security-considerations)
- [Monitoring](#monitoring)

## Docker Deployment

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/UNC-GDSC/AI-Resume-Analyzer.git
cd AI-Resume-Analyzer
```

2. **Configure environment variables**
```bash
# Update docker-compose.yml with production values
# Set strong SECRET_KEY and JWT_SECRET_KEY
# Configure ALLOWED_ORIGINS for your domain
```

3. **Start services**
```bash
docker-compose up -d
```

4. **Initialize database**
```bash
docker-compose exec backend python -c "from app.database import init_db; init_db()"
```

### Production Configuration

Update `docker-compose.yml` for production:

```yaml
backend:
  environment:
    SECRET_KEY: ${SECRET_KEY}  # Use environment variable
    JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    DEBUG: "False"
    ENVIRONMENT: production
    ALLOWED_ORIGINS: https://yourdomain.com
    DATABASE_URL: ${DATABASE_URL}
```

## Cloud Deployment

### AWS Deployment

#### Using ECS (Elastic Container Service)

1. **Build and push Docker images**
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t ai-resume-backend ./backend
docker tag ai-resume-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-resume-backend:latest

# Push
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-resume-backend:latest
```

2. **Set up RDS PostgreSQL**
- Create PostgreSQL instance
- Configure security groups
- Note connection string

3. **Create ECS Task Definition**
- Use ECR image
- Configure environment variables
- Set up CloudWatch logs

4. **Create ECS Service**
- Use Application Load Balancer
- Configure auto-scaling
- Set health checks

#### Using EC2

1. **Launch EC2 instance**
```bash
# Ubuntu 22.04 LTS, t3.medium or larger
```

2. **Install Docker and Docker Compose**
```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER
```

3. **Deploy application**
```bash
git clone https://github.com/UNC-GDSC/AI-Resume-Analyzer.git
cd AI-Resume-Analyzer
docker-compose up -d
```

4. **Set up Nginx reverse proxy**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

5. **Set up SSL with Let's Encrypt**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### Google Cloud Platform

#### Using Cloud Run

1. **Build containers**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/ai-resume-backend ./backend
gcloud builds submit --tag gcr.io/PROJECT_ID/ai-resume-frontend ./frontend
```

2. **Deploy to Cloud Run**
```bash
gcloud run deploy ai-resume-backend \
  --image gcr.io/PROJECT_ID/ai-resume-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

gcloud run deploy ai-resume-frontend \
  --image gcr.io/PROJECT_ID/ai-resume-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

3. **Set up Cloud SQL**
- Create PostgreSQL instance
- Configure connection
- Update DATABASE_URL

### Heroku

1. **Create apps**
```bash
heroku create ai-resume-backend
heroku create ai-resume-frontend
```

2. **Add PostgreSQL**
```bash
heroku addons:create heroku-postgresql:hobby-dev -a ai-resume-backend
```

3. **Deploy backend**
```bash
cd backend
git push heroku main
```

4. **Deploy frontend**
```bash
cd frontend
git push heroku main
```

## Environment Variables

### Critical Variables

**Backend:**
- `SECRET_KEY`: Strong random string (32+ characters)
- `JWT_SECRET_KEY`: Different strong random string
- `DATABASE_URL`: PostgreSQL connection string
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins
- `ENVIRONMENT`: Set to `production`
- `DEBUG`: Set to `False`

**Frontend:**
- `REACT_APP_API_URL`: Backend API URL

### Generate Secrets

```python
import secrets
print(secrets.token_urlsafe(32))
```

Or use:
```bash
openssl rand -base64 32
```

## Security Considerations

### 1. Secrets Management
- Never commit secrets to version control
- Use environment variables or secret managers
- Rotate secrets regularly

### 2. Database Security
- Use strong passwords
- Enable SSL connections
- Restrict network access
- Regular backups

### 3. API Security
- Enable rate limiting
- Use HTTPS only
- Implement CORS properly
- Validate all inputs

### 4. File Upload Security
- Validate file types
- Scan for malware
- Limit file sizes
- Store in secure location

### 5. Authentication
- Use strong password requirements
- Implement account lockout
- Enable 2FA (future enhancement)

## Monitoring

### Application Monitoring

**Logs:**
```bash
# Docker
docker-compose logs -f

# View specific service
docker-compose logs -f backend
```

**Health Checks:**
- Backend: `http://your-domain/health`
- Check response time and status

### Database Monitoring

Monitor:
- Connection pool usage
- Query performance
- Disk usage
- Backup status

### Performance Metrics

Track:
- API response times
- Resume processing time
- Memory usage
- CPU usage
- Error rates

### Recommended Tools

- **Logging**: ELK Stack, CloudWatch, Datadog
- **APM**: New Relic, Datadog, Sentry
- **Uptime**: UptimeRobot, Pingdom
- **Errors**: Sentry, Rollbar

## Backup and Recovery

### Database Backups

**Automated backups:**
```bash
# PostgreSQL
pg_dump -U postgres -h localhost resume_analyzer > backup_$(date +%Y%m%d).sql
```

**Restore:**
```bash
psql -U postgres -h localhost resume_analyzer < backup_20240101.sql
```

### File Backups

Backup uploads directory:
```bash
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/
```

### Disaster Recovery Plan

1. Maintain offsite backups
2. Document recovery procedures
3. Test recovery regularly
4. Keep configuration in version control

## Scaling

### Horizontal Scaling

1. **Load Balancer**: Distribute traffic across multiple instances
2. **Database**: Use read replicas for scaling reads
3. **Caching**: Implement Redis caching
4. **CDN**: Serve static files from CDN

### Vertical Scaling

- Upgrade instance size
- Increase database resources
- Optimize application code

## Maintenance

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build

# Restart services
docker-compose up -d
```

### Database Migrations

```bash
# If using Alembic
docker-compose exec backend alembic upgrade head
```

## Troubleshooting

### Common Issues

**Database connection failed:**
- Check DATABASE_URL
- Verify database is running
- Check firewall rules

**Upload fails:**
- Check file permissions
- Verify MAX_FILE_SIZE
- Check disk space

**High memory usage:**
- Monitor NLP model loading
- Check for memory leaks
- Adjust worker count

### Debug Mode

Only enable for troubleshooting:
```bash
DEBUG=True
LOG_LEVEL=DEBUG
```

## Support

For deployment issues:
- Check logs: `docker-compose logs`
- Review documentation
- Open GitHub issue
- Contact maintainers
