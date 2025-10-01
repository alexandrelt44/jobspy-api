# JobSpy API Deployment

This document contains instructions for deploying the JobSpy API to your Docker server.

## Server Setup

The application is configured to work with your existing nginx-proxy setup that handles SSL certificates and routing.

## Manual Deployment Steps

### 1. SSH into the server
```bash
ssh root@resumebot.alexandreleite.pro
```

### 2. Clone the repository
```bash
mkdir -p /opt/jobspy-api
cd /opt/jobspy-api
git clone https://github.com/alexandrelt44/jobspy-api.git .
```

### 3. Build and start the container
```bash
docker-compose up -d --build
```

### 4. Check the container status
```bash
docker-compose ps
docker-compose logs -f jobspy-api
```

### 5. Test the deployment
```bash
# Test health endpoint
curl -f http://localhost:8000/health

# Test from outside (after nginx-proxy picks it up)
curl https://jobspy.alexandreleite.pro/health
```

## Configuration

The docker-compose.yml is configured with:
- **Domain**: jobspy.alexandreleite.pro
- **SSL**: Automatic via Let's Encrypt
- **Network**: mup-network (connects to existing nginx-proxy)
- **Port**: 8000 (internal)

## Updating

To update the application:

```bash
cd /opt/jobspy-api
git pull origin main
docker-compose up -d --build
```

## Troubleshooting

### Check logs
```bash
docker-compose logs jobspy-api
```

### Check nginx-proxy
```bash
docker logs mup-nginx-proxy
```

### Restart container
```bash
docker-compose restart jobspy-api
```

### Clean rebuild
```bash
docker-compose down
docker-compose up -d --build --force-recreate
```

## API Endpoints

Once deployed, the API will be available at:

- **Base URL**: https://jobspy.alexandreleite.pro
- **Health**: https://jobspy.alexandreleite.pro/health  
- **Documentation**: https://jobspy.alexandreleite.pro/docs
- **Stats**: https://jobspy.alexandreleite.pro/stats

### Test API Call
```bash
curl -X POST https://jobspy.alexandreleite.pro/api/jobs/search \
  -H 'Content-Type: application/json' \
  -d '{
    "search_term": "python developer", 
    "sites": ["indeed"], 
    "results_wanted": 5,
    "location": "Remote"
  }'
```