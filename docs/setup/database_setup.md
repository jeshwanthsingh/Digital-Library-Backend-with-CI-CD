# Database Configuration Guide

This guide explains how to configure the Agora application database for different environments, including local development (SQLite or local MySQL) and deployed environments (AWS RDS MySQL).

## 1. Core Concept: The `.env` File

Database connection details and type selection are managed through environment variables, loaded from a `.env` file in the project root.

**Action Required (First Step):**
If you haven't already, copy the example environment file. This file will be your primary configuration point for the database.
```bash
cp .env.example .env
```
**Important:** The `.env` file contains sensitive information if you configure it for remote databases and **should NOT be committed to Git**. It's already listed in `.gitignore`.

The key environment variables in `.env` for database configuration are:
*   `DB_TYPE`: Determines the database system. Can be `sqlite` (default if not specified or if `.env` is missing) or `mysql`.
*   `DB_SQLITE_PATH`: Path to the SQLite database file (if `DB_TYPE=sqlite`). Defaults to `db/agora.db`.
*   `DB_HOST`: Hostname for MySQL server.
*   `DB_PORT`: Port for MySQL server (usually `3306`).
*   `DB_USER`: Username for MySQL.
*   `DB_PASSWORD`: Password for MySQL.
*   `DB_NAME`: Database name in MySQL.

The application (`application/database/database.py`) reads these variables to establish the correct database connection.

## 2. Database Options

You can choose one of the following database setups:

### Option A: Local SQLite Database (Default for Quick Start)

*   **Simplicity**: Uses a single file, no separate server installation needed. Ideal for getting started quickly.
*   **Configuration**:
    *   If your `.env` file has `DB_TYPE=sqlite` (or if `DB_TYPE` is commented out/absent), SQLite will be used.
    *   The default path is `db/agora.db` (relative to project root).
    *   To change the path, modify `DB_SQLITE_PATH` in your `.env` file:
        ```dotenv
        # .env
        DB_TYPE=sqlite
        DB_SQLITE_PATH=path/to/your/custom_agora.db
        ```
*   **Initialization**: See Section 3 (Database Initialization and Seeding).

### Option B: Local MySQL Server (For Closer-to-Production Development)

This involves running a MySQL server directly on your local machine.

1.  **Install MySQL Server:**
    *   **macOS:** Use Homebrew: `brew install mysql`
    *   **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install mysql-server`
    *   **Windows/Other:** Download from the official MySQL website and follow their installation instructions.
    *   Ensure the MySQL service is started after installation.

2.  **Create Database and User (Example using MySQL CLI):**
    Log into your local MySQL server (you might need `sudo` for the first command depending on your setup):
    ```bash
    sudo mysql # or mysql -u root -p
    ```
    Then, execute the following SQL commands. Replace `agora_dev_user` and `your_strong_password` with your desired credentials.
    ```sql
    CREATE DATABASE agora_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    CREATE USER 'agora_dev_user'@'localhost' IDENTIFIED BY 'your_strong_password';
    GRANT ALL PRIVILEGES ON agora_db.* TO 'agora_dev_user'@'localhost';
    FLUSH PRIVILEGES;
    EXIT;
    ```

3.  **Configure `.env` for Local MySQL:**
    Update your `.env` file with the details of your local MySQL setup:
    ```dotenv
    # .env
    DB_TYPE=mysql
    DB_HOST=127.0.0.1   # Or localhost
    DB_PORT=3306        # Or your MySQL port if different
    DB_USER=agora_dev_user
    DB_PASSWORD=your_strong_password
    DB_NAME=agora_db
    # DB_SQLITE_PATH= (can be commented out or removed if DB_TYPE=mysql)
    ```

4.  **Initialization**: See Section 3 (Database Initialization and Seeding).

### Option C: AWS RDS (MySQL) or Other Remote MySQL Server (For Staging/Production)

This is typically for deployed environments.

1.  **Ensure RDS/MySQL Instance is Ready:** You need an existing MySQL server (like AWS RDS) with an endpoint, database name, username, and password.

2.  **Configure `.env` for Remote MySQL:**
    On the server where the application will run (e.g., your EC2 instance), create or update the `.env` file:
    ```dotenv
    # .env on the server
    DB_TYPE=mysql
    DB_HOST=<your-rds-endpoint-or-mysql-server-ip>
    DB_PORT=3306 # Or your RDS port
    DB_USER=<your-rds-username>
    DB_PASSWORD=<your-rds-password>
    DB_NAME=<your-rds-database-name>
    ```

3.  **Initialization**: See Section 3 (Database Initialization and Seeding). For RDS, initial table creation might also be part of a deployment script.

## 3. Database Initialization and Seeding

Once your `.env` file is configured for your chosen database (SQLite, Local MySQL, or Remote MySQL), you need to create the tables and populate them with initial data.

The `application/seed.py` script is designed to:
*   Connect to the database specified in your `.env` file.
*   Drop all existing application tables (if any) in that database.
*   Recreate the tables based on the current SQLAlchemy models (`application/database/models.py`).
*   Populate the tables with initial sample data (categories, users, listings, images).

**How to Run the Seed Script:**

1.  Ensure your Python virtual environment is activated (see `docs/setup/LOCAL_SETUP.md`).
2.  From the **project root directory**, run:
    ```bash
    python application/seed.py
    ```
    Or, using the Makefile:
    ```bash
    make seed-db
    ```

This single seeding process works for SQLite, local MySQL, or remote MySQL, depending on your active `.env` configuration.

*For AWS RDS during initial deployment, table creation (`Base.metadata.create_all`) and seeding might be handled by the deployment script (`scripts/deploy.sh`) or run manually on the server after configuring the `.env` file there.*

## 4. Troubleshooting

### Database Connection Issues

**General:**
*   **Check `.env` Carefully:** Typos in `DB_TYPE`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, or `DB_PORT` are common.
*   **Backend Logs:** Check the FastAPI/Uvicorn server logs for detailed error messages when the application tries to connect.

**Local SQLite:**
*   **File Permissions**: Ensure the application has write permissions for the directory containing the SQLite file (e.g., `db/`) and the file itself (`agora.db`).
*   **Path**: Verify `DB_SQLITE_PATH` in `.env` (if used) or the default path is correct relative to the project root.
*   **Corrupted File**: If issues persist, delete the SQLite file (e.g., `db/agora.db`) and re-run the seed script (`python application/seed.py` or `make seed-db`).

**Local or Remote MySQL:**
*   **MySQL Server Running?**: Ensure your MySQL server (local or RDS) is running and accessible.
*   **Credentials**: Double-check username, password, database name.
*   **Host/Port**: Confirm `DB_HOST` and `DB_PORT`. For local, `127.0.0.1` is often more reliable than `localhost`.
*   **User Privileges (MySQL)**: Verify the MySQL user has the necessary privileges (SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, etc.) on the specified database. The `GRANT ALL PRIVILEGES` command shown earlier for local setup should suffice.
*   **Network/Security Groups (for RDS/Remote MySQL)**:
    *   Verify that the machine running the Python application (e.g., your local machine or EC2 instance) can reach the MySQL server over the network.
    *   For AWS RDS: Check that the EC2 instance's security group allows outbound traffic to the RDS instance on the MySQL port (usually 3306). Also, ensure the RDS instance's security group allows inbound traffic from the EC2 instance's security group or IP address.

### Frontend Data Loading Issues (e.g., "Failed to load search results")

If the frontend has issues loading data:
1.  **Backend First**: Confirm the backend can connect to the database and that the seed script ran successfully.
2.  **Verify Tables & Data**:
    *   **SQLite**: Use a tool like DB Browser for SQLite to open the `.db` file and check if tables (`categories`, `listings`, `users`, `listing_images`) exist and contain data.
    *   **MySQL**: Connect to your MySQL instance using a client (MySQL Workbench, DataGrip, `mysql` CLI) and verify tables and data.
3.  **Test API Directly**: Use `curl` or Postman to test API endpoints (e.g., `curl http://localhost:8000/api/categories`). Check backend server logs.

## 5. Migrating Data Between Environments (Advanced)

Moving data between SQLite and MySQL can be complex due to SQL dialect differences.

*   **SQLite to MySQL:**
    1.  Dump SQLite: `sqlite3 path/to/your/agora.db .dump > sqlite_dump.sql`
    2.  This `sqlite_dump.sql` will likely need significant manual editing or conversion using a specialized tool (e.g., `sed`/`awk` scripts, or dedicated migration software) before it can be imported into MySQL. Differences include data types, AUTO_INCREMENT syntax, and quoting.
*   **MySQL to MySQL (e.g., Local MySQL to RDS, or vice-versa):**
    Use `mysqldump` for exporting and `mysql` CLI for importing.
    ```bash
    # Export from source MySQL
    mysqldump -h <source_host> -u <user> -p<password> <db_name> > mysql_dump.sql

    # Import to target MySQL
    mysql -h <target_host> -u <user> -p<password> <db_name> < mysql_dump.sql
    ```
*   **MySQL to SQLite:**
    This is also challenging. It's often easier to re-seed the local SQLite database or use a third-party tool designed for MySQL to SQLite conversion.

For development, frequently re-running the `seed.py` script (`make seed-db`) is the simplest way to reset your database to a known state.
