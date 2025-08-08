# Agora Marketplace Deployment Guide

## Application URLs
- **HTTPS**: [https://team02sfsu.org](https://team02sfsu.org) (Recommended)
- **HTTP**: [http://18.223.28.173](http://18.223.28.173) (Alternative)

## Server Configuration Overview

We've transitioned from a Docker-based deployment to a more space-efficient direct deployment using systemd and Nginx. This change has saved approximately 1.69GB of server space.

### Current Server Setup
- **Backend**: Running as a systemd service on port 8000
- **Frontend**: Static files served by Nginx from `/var/www/html`
- **HTTPS**: Configured with Let's Encrypt SSL certificates (valid until May 19, 2025)
- **Database**: AWS RDS MySQL instance

## Deployment Scripts

### Essential Scripts

1. **deploy.sh**  
   Main deployment script for setting up the application on a server.
   ```bash
   # Usage on server
   ./deploy.sh
   ```

2. **build_frontend.sh**  
   Standalone script to build the Svelte frontend.
   ```bash
   # Usage on server
   ./build_frontend.sh
   ```

3. **local_build.sh**  
   For local development without Docker.
   ```bash
   # Local usage
   ./local_build.sh
   ```

4. **transfer_to_server.sh**  
   Helper script to transfer deployment files to a server.
   ```bash
   # Usage from local machine
   ./transfer_to_server.sh -i SERVER_IP
   ```

### Documentation Files

- **SERVER_INSTALLATION.md**: Step-by-step server installation instructions
- **SERVER_SETUP.md**: Technical server configuration details
- **requirements.txt**: Backend dependencies list

## Maintenance Tasks

### Updating the Application

```bash
# 1. Pull latest code
git pull

# 2. Rebuild frontend if needed
cd application/Frontend
npm install
npm run build

# 3. Copy new frontend files
sudo cp -r dist/* /var/www/html/

# 4. Restart services
sudo systemctl restart agora
sudo systemctl restart nginx
```

### SSL Certificate Renewal

Certificates will expire on May 19, 2025. To renew:

```bash
sudo certbot renew
```

### Checking Service Status

```bash
# Backend service status
sudo systemctl status agora

# Web server status
sudo systemctl status nginx
```

## Legacy Docker Files (Not Used in Current Deployment)

The following files are kept for reference but are not used in the current deployment:

- `docker-compose.yml`
- `Dockerfile`
- `docker/` directory
- `start_agora.sh` (Docker-specific startup script)

## Troubleshooting

### Database Connection Issues
Check the `.env` file to ensure database credentials are correct:
```bash
cat .env
```

### Service Startup Failures
Check the service logs:
```bash
sudo journalctl -u agora -e
```

### Nginx Configuration Issues
Test Nginx configuration:
```bash
sudo nginx -t
```

### API Endpoint Testing
Verify API endpoints directly:
```bash
curl http://localhost:8000/api/categories
