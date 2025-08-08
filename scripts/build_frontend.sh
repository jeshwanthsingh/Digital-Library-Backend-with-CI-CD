#!/bin/bash
# Script to build the frontend for Agora Marketplace
# This should be run on the server as part of the non-Docker deployment

set -e # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting frontend build...${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Node.js not found. Installing...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
fi

# Check Node.js version
NODE_VERSION=$(node -v)
echo -e "${YELLOW}Using Node.js version: $NODE_VERSION${NC}"

# Navigate to the frontend directory
cd "application/Frontend"
echo -e "${YELLOW}Building frontend in $(pwd)...${NC}"

# Install dependencies
echo -e "${YELLOW}Installing npm dependencies...${NC}"
npm install

# Build the frontend
echo -e "${YELLOW}Building frontend...${NC}"
npm run build

if [ -d "dist" ]; then
    echo -e "${GREEN}Frontend build successful!${NC}"
    echo -e "${YELLOW}Built files are in $(pwd)/dist${NC}"
else
    echo -e "${RED}ERROR: Frontend build failed. Check the logs above for errors.${NC}"
    exit 1
fi

echo -e "${GREEN}Frontend build process complete. You can now run deploy.sh to deploy the application.${NC}"
