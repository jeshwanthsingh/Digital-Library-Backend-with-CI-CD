#!/bin/bash
# Script to transfer deployment files to AWS EC2 server
# This should be run from your local machine

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default server details
SERVER_USER="ubuntu"
KEY_PATH="credentials/web_server_key.pem"
REPO_PATH="csc648-fa25-0104-team02"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--ip)
            SERVER_IP="$2"
            shift 2
            ;;
        -k|--key)
            KEY_PATH="$2"
            shift 2
            ;;
        -u|--user)
            SERVER_USER="$2"
            shift 2
            ;;
        -p|--path)
            REPO_PATH="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if SERVER_IP is provided
if [ -z "$SERVER_IP" ]; then
    echo -e "${YELLOW}Enter the server IP address or hostname:${NC}"
    read SERVER_IP
fi

# Confirm server details
echo -e "${YELLOW}Transferring files to:${NC}"
echo "  Server: $SERVER_IP"
echo "  User: $SERVER_USER"
echo "  Key: $KEY_PATH"
echo "  Repository path: $REPO_PATH"
echo

# Confirm before proceeding
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Operation cancelled${NC}"
    exit 1
fi

# Check if key file exists
if [ ! -f "$KEY_PATH" ]; then
    echo -e "${RED}Error: Key file not found at $KEY_PATH${NC}"
    exit 1
fi

# Make key file permissions secure
chmod 600 "$KEY_PATH"

# List of files to transfer
FILES_TO_TRANSFER=(
    "deploy.sh"
    "build_frontend.sh"
    "requirements.txt"
    "SERVER_INSTALLATION.md"
)

echo -e "${GREEN}Starting file transfer...${NC}"

# Transfer each file
for file in "${FILES_TO_TRANSFER[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${YELLOW}Transferring $file...${NC}"
        scp -i "$KEY_PATH" "$file" "$SERVER_USER@$SERVER_IP:~/$REPO_PATH/"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Successfully transferred $file${NC}"
        else
            echo -e "${RED}Failed to transfer $file${NC}"
        fi
    else
        echo -e "${RED}File not found: $file${NC}"
    fi
done

echo -e "${GREEN}File transfer complete.${NC}"
echo

# Instructions for next steps
echo -e "${YELLOW}Next steps:${NC}"
echo "1. SSH into your server: ssh -i \"$KEY_PATH\" $SERVER_USER@$SERVER_IP"
echo "2. Navigate to the repository: cd ~/$REPO_PATH"
echo "3. Make scripts executable: chmod +x deploy.sh build_frontend.sh"
echo "4. Build the frontend: ./build_frontend.sh"
echo "5. Deploy the application: ./deploy.sh"
echo
echo -e "${YELLOW}For more details, refer to SERVER_INSTALLATION.md on your server.${NC}"
