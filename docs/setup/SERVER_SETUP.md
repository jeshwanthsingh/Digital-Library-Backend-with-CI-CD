# Server Setup Guide for Agora Marketplace

This guide explains how to set up the Agora Marketplace on your AWS EC2 instances without using Docker, to conserve server space.

## Prerequisites

- Ubuntu 20.04 or newer
- SSH access to your EC2 instance
- Python 3.8 or newer
- Nginx
- Node.js 16 or newer (for building the frontend)

## Server Preparation

1. Connect to your server via SSH:
   ```bash
   ssh -i "credentials/web_server_key.pem" ubuntu@ec2-18-223-28-173.us-east-2.compute.amazonaws.com
   ```

2. Install required packages:
   ```bash
   sudo apt update
   sudo apt install -y python3-venv python3-pip nginx
   
   # Install Node.js
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt install -y nodejs
   ```

## Deployment Options

### Option 1: Automated Deployment

The easiest way to deploy is to use the provided `deploy.sh` script:

1. Copy the deployment script to your server:
   ```bash
   scp -i "credentials/web_server_key.pem" deploy.sh ubuntu@ec2-18-223-28-173.us-east-2.compute.amazonaws.com:~/
   ```

2. Connect to your server and run the script:
   ```bash
   ssh -i "credentials/web_server_key.pem" ubuntu@ec2-18-223-28-173.us-east-2.compute.amazonaws.com
   chmod +x ~/deploy.sh
   ~/deploy.sh
   ```

This script will:
- Clone or update the repository
- Set up a Python virtual environment
- Install dependencies
- Configure environment variables for the RDS database
- Set up a systemd service for the backend
- Configure Nginx to serve the frontend and proxy API requests
- Start the application

### Option 2: Manual Deployment

If you prefer to deploy manually or the script doesn't work for your environment:

1. Create application directory:
   ```bash
   mkdir -p ~/agora
   cd ~/agora
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/csc648-fa25-0104-team02.git .
   ```

3. Set up virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   cat > .env << EOL
   DB_HOST=team02-mysql.c7u0smm4uoyx.us-east-2.rds.amazonaws.com
   DB_PORT=3306
   DB_USER=admin
   DB_PASSWORD=Team02Password123
   DB_NAME=team02db
   EOL
   ```

5. Build frontend:
   ```bash
   cd application/Frontend
   npm install
   npm run build
   ```

6. Copy frontend files:
   ```bash
   sudo mkdir -p /var/www/html
   sudo cp -r dist/* /var/www/html/
   sudo chown -R www-data:www-data /var/www/html
   ```

7. Create systemd service:
   ```bash
   sudo nano /etc/systemd/system/agora.service
   # (paste the service configuration)
   sudo systemctl daemon-reload
   sudo systemctl enable agora
   sudo systemctl start agora
   ```

8. Configure Nginx:
   ```bash
   sudo nano /etc/nginx/sites-available/agora
   # (paste the Nginx configuration)
   sudo ln -s /etc/nginx/sites-available/agora /etc/nginx/sites-enabled/
   sudo rm -f /etc/nginx/sites-enabled/default
   sudo systemctl restart nginx
   ```

## GitHub Actions for CI/CD

We've set up GitHub Actions to automate the build process:

1. When you push to the main branch, GitHub Actions will:
   - Build the frontend
   - Run tests
   - Create an artifact with the frontend build

2. You can then download this artifact to deploy to your server:
   ```bash
   # Download from GitHub Actions and deploy
   cd ~/agora
   # (download artifact)
   unzip frontend-build.zip -d frontend-dist
   sudo cp -r frontend-dist/* /var/www/html/
   ```

## Troubleshooting

- **Permission issues**: Ensure your user has permission to access files or use sudo
- **Nginx issues**: Check nginx logs with `sudo nginx -t` and `sudo journalctl -u nginx`
- **Application issues**: Check application logs with `sudo journalctl -u agora`
- **Database connection issues**: Verify your .env file has the correct database credentials
- **Port conflicts**: Make sure nothing else is running on ports 80 or 8000

## Verification

After deployment, verify your application is running:
1. Visit your server's IP address in a browser
2. Test search and listing functionality
3. Verify the frontend and API are communicating correctly

---

For any questions or issues, please contact the team lead.
