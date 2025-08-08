#!/bin/bash
# Agora Marketplace Deployment Script
# This script deploys the application without Docker to save server space

set -e # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Agora Marketplace deployment...${NC}"

# Define paths
APP_DIR="$PWD" 
LOGS_DIR="$APP_DIR/logs" 
WEB_ROOT="/var/www/html"
VENV_DIR="$APP_DIR/venv"

echo -e "${YELLOW}Using current directory as application directory: $APP_DIR...${NC}"

# --- CRITICAL CHECK: Ensure DB environment variables AND SECRET_KEY are set ---
if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ] || [ -z "$DB_NAME" ] || [ -z "$SECRET_KEY" ]; then
  echo -e "${RED}ERROR: One or more required environment variables are not set in the script's environment.${NC}"
  echo -e "${RED}Ensure they are correctly exported in the GitHub Actions workflow.${NC}"
  exit 1
fi
echo -e "${GREEN}Required environment variables found.${NC}"

# Create and update Python virtual environment
if [ ! -d "$VENV_DIR" ]; then
  echo -e "${YELLOW}Setting up Python virtual environment at $VENV_DIR...${NC}"
  python3 -m venv "$VENV_DIR"
fi

echo -e "${YELLOW}Activating virtual environment and installing Python dependencies...${NC}"
source "$VENV_DIR/bin/activate"
pip install -U pip
if [ -f "$APP_DIR/requirements.txt" ]; then
  pip install -r "$APP_DIR/requirements.txt"
else
  echo -e "${RED}ERROR: requirements.txt not found in $APP_DIR.${NC}"
  exit 1
fi

# --- Set permissions for backend static directory ---
echo -e "${YELLOW}Setting permissions for backend static directory: $APP_DIR/static...${NC}"
# Ensure the images/listings and thumbs subdirectories exist and have correct permissions
mkdir -p "$APP_DIR/static/images/listings/thumbs"
# Set ownership to the systemd service user
sudo chown -R ${SYSTEMD_USER}:${SYSTEMD_USER} "$APP_DIR/static"
# Set read/write permissions for the owner (backend service user)
sudo chmod -R u+rw "$APP_DIR/static"
# Optionally, allow read access for others (if static files need to be served directly by Nginx without backend proxying for /static)
sudo chmod -R a+r "$APP_DIR/static"
echo -e "${GREEN}Backend static directory permissions set.${NC}"

# Set up environment file
echo -e "${YELLOW}Configuring application environment in $APP_DIR/.env...${NC}"
cat > "$APP_DIR/.env" << EOL
DB_TYPE=mysql
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}
SECRET_KEY=${SECRET_KEY}
EOL
echo -e "${GREEN}.env file created successfully.${NC}"

# Create logs directory
echo -e "${YELLOW}Ensuring logs directory exists at $LOGS_DIR...${NC}"
mkdir -p "$LOGS_DIR"
CURRENT_SCRIPT_USER=${SUDO_USER:-$USER}
sudo chown -R ${CURRENT_SCRIPT_USER}:${CURRENT_SCRIPT_USER} "$LOGS_DIR"
sudo chmod -R u+w "$LOGS_DIR"
echo -e "${GREEN}Logs directory ready.${NC}"

# Initialize/Seed the database
echo -e "${YELLOW}Initializing/Seeding database...${NC}"
"$VENV_DIR/bin/python3" -m application.seed
echo -e "${GREEN}Database seeding script executed.${NC}"

# Create web directory and set permissions
echo -e "${YELLOW}Setting up web directory: $WEB_ROOT...${NC}"
sudo mkdir -p "$WEB_ROOT"

# Clean web directory
echo -e "${YELLOW}Cleaning web directory $WEB_ROOT/* ...${NC}"
sudo rm -rf "$WEB_ROOT"/*

# Copy frontend files
echo -e "${YELLOW}Copying frontend files from $APP_DIR/frontend-dist/ to $WEB_ROOT/...${NC}"
if [ -d "$APP_DIR/frontend-dist" ] && [ -n "$(ls -A $APP_DIR/frontend-dist)" ]; then
  sudo cp -r "$APP_DIR/frontend-dist"/* "$WEB_ROOT"/
  sudo chown -R www-data:www-data "$WEB_ROOT" 
  sudo chmod -R 755 "$WEB_ROOT" 
  echo -e "${GREEN}Frontend files copied successfully.${NC}"
else
  echo -e "${RED}ERROR: Frontend build directory '$APP_DIR/frontend-dist' not found or is empty.${NC}"
  exit 1
fi

# Create systemd service file
echo -e "${YELLOW}Setting up systemd service (agora.service)...${NC}"
SYSTEMD_USER=${SUDO_USER:-$USER} 
sudo tee /etc/systemd/system/agora.service > /dev/null << EOL
[Unit]
Description=Agora Marketplace Application
After=network.target 

[Service]
User=${SYSTEMD_USER}
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker application.app:app --bind 0.0.0.0:8000 --log-level debug
Restart=always 
RestartSec=5s  
StandardOutput=journal 
StandardError=journal  
SyslogIdentifier=agora 

[Install]
WantedBy=multi-user.target 
EOL
echo -e "${GREEN}Systemd service file created/updated.${NC}"

# Create Nginx configuration
echo -e "${YELLOW}Setting up Nginx configuration...${NC}"
sudo tee /etc/nginx/sites-available/agora > /dev/null << EOL
server {
  listen 80;
  server_name _; 
  location / {
    root $WEB_ROOT;
    try_files \$uri \$uri/ /index.html; 
  }
  location /api {
    proxy_pass http://127.0.0.1:8000; 
    proxy_set_header Host \$host; 
    proxy_set_header X-Real-IP \$remote_addr; 
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for; 
    proxy_set_header X-Forwarded-Proto \$scheme; 
    proxy_read_timeout 300s; 
    proxy_connect_timeout 75s;
  }
  location ~ /\. {
    deny all;
  }
}
EOL
echo -e "${GREEN}Nginx configuration created/updated.${NC}"

# Enable the Nginx site
NGINX_SITES_ENABLED_PATH="/etc/nginx/sites-enabled/agora"
NGINX_SITES_AVAILABLE_PATH="/etc/nginx/sites-available/agora"
if [ -L "$NGINX_SITES_ENABLED_PATH" ] && [ "$(readlink -f "$NGINX_SITES_ENABLED_PATH")" = "$NGINX_SITES_AVAILABLE_PATH" ]; then
  echo -e "${GREEN}Nginx site 'agora' is already correctly enabled.${NC}"
else
  echo -e "${YELLOW}Enabling Nginx site 'agora'...${NC}"
  sudo ln -sf "$NGINX_SITES_AVAILABLE_PATH" "$NGINX_SITES_ENABLED_PATH"
  if [ -f /etc/nginx/sites-enabled/default ]; then
    echo -e "${YELLOW}Removing default Nginx site configuration...${NC}"
    sudo rm -f /etc/nginx/sites-enabled/default
  fi
  echo -e "${GREEN}Nginx site 'agora' enabled.${NC}"
fi

# Test Nginx configuration
echo -e "${YELLOW}Testing Nginx configuration...${NC}"
if sudo nginx -t; then
  echo -e "${GREEN}Nginx configuration test successful.${NC}"
else
  echo -e "${RED}ERROR: Nginx configuration test failed.${NC}"
  sudo tail -n 20 /var/log/nginx/error.log || echo "No Nginx error log found."
  exit 1 
fi

# --- Modified Service Restart Sequence ---
echo -e "${YELLOW}Attempting to stop existing services to ensure clean restart...${NC}"
sudo systemctl stop agora.service || echo "agora.service was not running or failed to stop."
sudo systemctl stop nginx || echo "nginx was not running or failed to stop."

echo -e "${YELLOW}Forcefully terminating any lingering Gunicorn processes...${NC}"
sudo pkill -KILL gunicorn || echo "No Gunicorn processes to kill or failed to kill."
echo -e "${YELLOW}Waiting a few seconds for ports to free up...${NC}"
sleep 5 # Wait for 5 seconds

echo -e "${YELLOW}Reloading systemd daemon and restarting services...${NC}"
sudo systemctl daemon-reload    
sudo systemctl enable agora.service # Ensure it's enabled
sudo systemctl restart agora.service 
sudo systemctl restart nginx      

echo -e "${GREEN}Deployment completed successfully!${NC}"
SERVER_IP=$(hostname -I | awk '{print $1}') 
echo -e "${GREEN}Your application should be accessible at http://${SERVER_IP} (frontend)${NC}"
echo -e "${YELLOW}To check application status:${NC}"
echo "sudo systemctl status agora.service"
echo "sudo systemctl status nginx"
echo ""
echo -e "${YELLOW}To view live application logs (via journald):${NC}"
echo "sudo journalctl -u agora.service -f -n 50" 
