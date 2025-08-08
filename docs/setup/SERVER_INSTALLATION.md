# Server Installation Guide (Non-Docker Approach)

This guide covers how to deploy the Agora Marketplace application directly on your AWS EC2 instance without using Docker, to conserve server space.

## Prerequisites

You already have:
- The repository cloned at `~/csc648-fa25-0104-team02`
- Docker containers removed (which you've already done)

## Step 1: Upload the deployment scripts

First, upload the necessary deployment scripts to your server:

```bash
# From your local machine
scp -i "credentials/web_server_key.pem" deploy.sh build_frontend.sh requirements.txt ubuntu@ec2-18-223-28-173.us-east-2.compute.amazonaws.com:~/csc648-fa25-0104-team02/
```

## Step 2: Make scripts executable on the server

SSH into your server and make the scripts executable:

```bash
ssh -i "credentials/web_server_key.pem" ubuntu@ec2-18-223-28-173.us-east-2.compute.amazonaws.com

cd ~/csc648-fa25-0104-team02
chmod +x deploy.sh build_frontend.sh
```

## Step 3: Install dependencies and build the frontend

```bash
# Make sure necessary packages are installed
sudo apt update
sudo apt install -y python3-venv python3-pip

# Build the frontend
./build_frontend.sh
```

This script will:
- Check and install Node.js if needed
- Install npm dependencies
- Build the frontend application

## Step 4: Run the deployment script

```bash
./deploy.sh
```

This script will:
- Set up a Python virtual environment
- Install Python dependencies
- Configure environment for RDS database connection
- Copy the built frontend to the web root
- Set up systemd service for the backend
- Configure Nginx 
- Start all services

## Step 5: Verify the installation

After the scripts complete, verify that your application is running:

```bash
# Check the backend service status
sudo systemctl status agora

# Check Nginx status
sudo systemctl status nginx

# Check the application logs
sudo journalctl -u agora -f
```

Visit your server's IP address in a browser to confirm the application is working:
- http://18.223.28.173 (or your server's actual IP address)

## Troubleshooting

If you encounter any issues:

1. **Frontend build fails**:
   ```bash
   # Check Node.js version
   node -v
   
   # Manually build frontend
   cd ~/csc648-fa25-0104-team02/application/Frontend
   npm install
   npm run build
   ```

2. **Backend service fails to start**:
   ```bash
   # Check logs
   sudo journalctl -u agora -e
   
   # Ensure database connection is correct
   cat ~/csc648-fa25-0104-team02/.env
   ```

3. **Web server issues**:
   ```bash
   # Check Nginx config
   sudo nginx -t
   
   # Check Nginx logs
   sudo journalctl -u nginx -e
   ```

4. **Check if the port is in use**:
   ```bash
   sudo lsof -i :80
   sudo lsof -i :8000
   ```

5. **Restart services**:
   ```bash
   sudo systemctl restart agora
   sudo systemctl restart nginx
   ```

## Additional Notes

- The application uses the RDS database configured in `.env` file
- The backend API runs on port 8000
- Nginx serves static files and proxies API requests
- If you need to rebuild the frontend, run `./build_frontend.sh` again
- If you need to restart the deployment, run `./deploy.sh` again
