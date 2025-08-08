# Agora Marketplace Deployment Guide

This document provides instructions for deploying the Agora Marketplace application both locally and on AWS.

## Local Development Deployment

### Using Docker (Recommended)

1. **Prerequisites**:
   - Docker and Docker Compose
   - Git

2. **Setup**:
   ```bash
   # Clone the repository (if not already done)
   git clone <repository-url>
   cd csc648-fa25-0104-team02
   
   # Make the development script executable
   chmod +x dev.sh
   
   # Run the development environment
   ./dev.sh
   ```

3. **Access the Application**:
   - Open your browser and go to: http://localhost:8000
   - The application will automatically use a local MySQL database
   - Any code changes will trigger hot-reloading

4. **View Logs**:
   ```bash
   # Using the modern Docker Compose
   docker compose -f docker-compose.dev.yml logs -f web
   
   # Or using the legacy docker-compose command if needed
   docker-compose -f docker-compose.dev.yml logs -f web
   ```

5. **Stop the Environment**:
   ```bash
   # Using the modern Docker Compose
   docker compose -f docker-compose.dev.yml down
   
   # Or using the legacy docker-compose command if needed
   docker-compose -f docker-compose.dev.yml down
   ```

### Without Docker (Using start_local.sh)

1. **Prerequisites**:
   - Python 3.11+
   - pip

2. **Setup**:
   ```bash
   # Create and activate virtual environment (recommended)
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   
   # Make the script executable
   chmod +x start_local.sh
   
   # Run the local development script
   ./start_local.sh
   ```
   
   The script will:
   - Check if you're in a virtual environment
   - Install required dependencies
   - Set up the Python path
   - Initialize the SQLite database
   - Start the application with hot-reloading

3. **Manual Setup** (if you prefer not to use the script):
   ```bash
   # Create and activate virtual environment
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set Python path
   export PYTHONPATH=$(pwd)
   
   # Initialize database
   python -m application.seed
   
   # Run the application
   uvicorn application.app:app --reload
   ```

## AWS Deployment

### Manual Deployment

1. **Set Up EC2 Instance**:
   ```bash
   # SSH into your EC2 instance
   ssh -i /path/to/key.pem ubuntu@your-ec2-ip
   
   # Clone the repository
   git clone <repository-url>
   cd csc648-fa25-0104-team02
   
   # Run the setup script
   chmod +x setup-aws.sh
   ./setup-aws.sh
   
   # Log out and log back in for Docker permissions to take effect
   exit
   ssh -i /path/to/key.pem ubuntu@your-ec2-ip
   ```

2. **Deploy the Application**:
   ```bash
   cd csc648-fa25-0104-team02
   
   # Create or update .env file with your RDS credentials
   nano .env
   # Add:
   # DB_HOST=team02-mysql.c7u0smm4uoyx.us-east-2.rds.amazonaws.com
   # DB_PORT=3306
   # DB_USER=admin
   # DB_PASSWORD=Team02Password123
   # DB_NAME=team02db
   
   # Build and start the application
   docker-compose up -d --build
   
   # Initialize the database (if needed)
   docker-compose exec web python -m application.seed
   ```

3. **Access the Application**:
   - Open your browser and go to: http://your-ec2-ip

### GitHub Actions CI/CD Setup

1. **Add GitHub Secrets**:
   - Go to your GitHub repository → Settings → Secrets and variables → Actions
   - Add the following secrets:
     - `AWS_ACCESS_KEY_ID` - Your AWS access key
     - `AWS_SECRET_ACCESS_KEY` - Your AWS secret key
     - `EC2_HOST` - Your EC2 instance IP
     - `EC2_USERNAME` - Your EC2 username (usually 'ubuntu')
     - `EC2_SSH_KEY` - Your private SSH key for the EC2 instance

2. **Push Changes to Main Branch**:
   ```bash
   git add .
   git commit -m "Update application"
   git push origin main
   ```

3. **Monitor Deployment**:
   - Go to your GitHub repository → Actions
   - Check the status of the deployment workflow

## Troubleshooting

### Docker Issues

- **Database Connection Errors**:
  - Check your .env or .env.dev file for correct database credentials
  - Ensure the database service is running: `docker-compose ps`

- **Port Conflicts**:
  - If ports 8000 or 3306 are already in use, modify the port mappings in docker-compose.yml

### AWS Deployment Issues

- **EC2 Connection Timeouts**:
  - Check security groups to ensure traffic is allowed on ports 22 and 80
  
- **RDS Connection Issues**:
  - Verify that the EC2 security group has access to the RDS instance
  - Check that the RDS credentials in .env are correct
  
- **GitHub Actions Deployment Failures**:
  - Check that all required secrets are correctly configured
  - Verify that the EC2 instance is running and accessible
