# Local Development Setup Guide

This guide explains how to set up and run the full Agora application stack (backend and frontend) on your local machine. The default configuration uses a local SQLite database.

## Prerequisites

*   **Python**: Version 3.10 or higher. Verify with `python3 --version`.
*   **Node.js**: Version 16 or higher. Verify with `node --version` and `npm --version`.
*   **pip**: Python package installer (usually comes with Python). Verify with `pip --version`.
*   **Git**: For cloning the repository. Verify with `git --version`.
*   **Make**: (Optional, but recommended for using Makefile shortcuts). Verify with `make --version`.

## Setup Options

We provide two main ways to set up and run the project locally:

1.  **Using the `Makefile` (Recommended & Easiest):** Automates most setup and run commands.
2.  **Manual Step-by-Step Setup:** For a detailed understanding of the process or if `make` is not available.

---

## Option 1: Using the `Makefile` (Recommended)

The `Makefile` in the project root provides convenient targets to automate common tasks.

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd csc648-fa25-0104-team02
    ```

2.  **Create `.env` File (Good Practice):**
    Copy the example environment file. For the default SQLite setup, no changes are strictly necessary in `.env`, but it's good practice to have it.
    ```bash
    cp .env.example .env
    ```
    *This file is pre-configured for SQLite. If you plan to use MySQL, you'll need to edit `.env` later (see `docs/setup/database_setup.md`).*

3.  **Run Full Setup (Virtual Env, Dependencies, Database Seed):**
    This command will:
    *   Create a Python virtual environment named `myenv`.
    *   Activate it (for the current script execution).
    *   Install backend Python dependencies from `requirements.txt`.
    *   Install frontend Node.js dependencies from `application/Frontend/package.json`.
    *   Seed the database using `application/seed.py` (creates `db/agora.db` if it doesn't exist).
    ```bash
    make setup
    ```
    *If you prefer to manage virtual environment activation manually, you can run `make setup-venv`, then activate it (`source myenv/bin/activate` or `.\myenv\Scripts\activate`), then run `make install-deps`, and `make seed-db`.*

4.  **Run the Backend Server:**
    Open a terminal window. Ensure your virtual environment is active if you didn't use `make setup` or if you opened a new terminal.
    ```bash
    # If venv not active: source myenv/bin/activate (macOS/Linux) or .\myenv\Scripts\activate (Windows)
    make run-backend
    ```
    *The backend API will be running at `http://localhost:8000`.* Keep this terminal open.

5.  **Run the Frontend Development Server:**
    Open a **new, separate terminal window/tab**.
    ```bash
    make run-frontend
    ```
    *The frontend will typically be available at `http://localhost:5173`.* Keep this terminal open.
    *The Vite development server (used by `npm run dev` via `make run-frontend`) proxies API requests (`/api`) and static asset requests (`/static`) to the backend at port 8000.*

6.  **Access the Application:**
    Open your web browser and navigate to `http://localhost:5173`.

---

## Option 2: Manual Step-by-Step Setup

Follow these steps if you prefer a manual setup or don't have `make`.

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd csc648-fa25-0104-team02
    ```

2.  **Create `.env` File (Good Practice):**
    Copy the example environment file. This step is recommended.
    ```bash
    cp .env.example .env
    ```
    *The default `.env` content is set up for SQLite. For MySQL, refer to `docs/setup/database_setup.md` after this initial setup.*

3.  **Set up Python Virtual Environment:**
    ```bash
    # Navigate to the project root directory
    python3 -m venv myenv

    # Activate the virtual environment
    # macOS/Linux:
    source myenv/bin/activate
    # Windows (Command Prompt):
    # .\myenv\Scripts\activate
    # Windows (PowerShell):
    # .\myenv\Scripts\Activate.ps1
    ```
    *Your terminal prompt should now indicate the active environment (e.g., `(myenv)`).*

4.  **Install Backend Dependencies:**
    ```bash
    # Ensure your virtual environment is active
    pip install -r requirements.txt
    ```

5.  **Set up Local Database (SQLite - Default):**
    The application uses a local SQLite database (`db/agora.db`) by default. This file is created by the seeding step if it doesn't exist. No separate database server installation is needed for SQLite.

6.  **Seed the Database:**
    This populates the database with initial data.
    ```bash
    # Ensure your virtual environment is active
    python application/seed.py
    ```
    *Troubleshooting `ModuleNotFoundError`: If `application/seed.py` has import errors, your `PYTHONPATH` might need to include the project root. Try:*
    ```bash
    # export PYTHONPATH=$(pwd) # macOS/Linux
    # set PYTHONPATH=%cd%     # Windows CMD
    # $env:PYTHONPATH = (Get-Location).Path # Windows PowerShell
    # Then retry: python application/seed.py
    ```

7.  **Install Frontend Dependencies:**
    ```bash
    cd application/Frontend
    npm install
    cd ../.. # Return to project root
    ```

8.  **Run the Backend Server:**
    Ensure your virtual environment is active. Run from the project root.
    ```bash
    # Ensure venv is active
    uvicorn application.app:app --reload --host 0.0.0.0 --port 8000
    ```
    *Keep this terminal open. Backend at `http://localhost:8000`.*

9.  **Run the Frontend Development Server:**
    Open a **new, separate terminal**. Navigate to the frontend directory.
    ```bash
    cd application/Frontend
    npm run dev
    ```
    *Keep this terminal open. Frontend usually at `http://localhost:5173`.*
    *Vite proxies `/api` and `/static` requests to `http://localhost:8000`.*

10. **Access the Application:**
    Open your browser to `http://localhost:5173`.

---

## Stopping the Local Servers

*   Go to the terminal running the **backend server** (Uvicorn or `make run-backend`) and press `Ctrl + C`.
*   Go to the terminal running the **frontend server** (`npm run dev` or `make run-frontend`) and press `Ctrl + C`.
*   To deactivate the Python virtual environment:
    ```bash
    deactivate
    ```

## Database Configuration

*   **SQLite (Default):** No special configuration is needed if you've copied `.env.example` to `.env`. The database file will be `db/agora.db`.
*   **MySQL:** For instructions on setting up and using MySQL, please refer to the detailed guide: [`docs/setup/database_setup.md`](./database_setup.md). You will need to update your `.env` file with MySQL credentials.

## Common Issues & Troubleshooting

*   **Port Conflicts:**
    *   If port `8000` (backend) or `5173` (frontend) is in use, Uvicorn or Vite will usually report an error.
    *   For backend: `uvicorn application.app:app --port <new_port_number>` and update `target` in `application/Frontend/vite.config.mjs` proxy settings.
    *   For frontend: `npm run dev -- --port <new_port_number>`.
*   **`ModuleNotFoundError` for `application.seed`:**
    *   Ensure your Python virtual environment is active.
    *   Ensure you are running `python application/seed.py` from the **project root directory**.
    *   If issues persist, try setting `PYTHONPATH` as described in the manual seeding step.
*   **Frontend Shows "Cannot GET /" or API Errors:**
    *   Ensure the backend server is running and accessible at `http://localhost:8000`.
    *   Check the terminal output of both backend and frontend servers for any error messages.
    *   Verify the proxy settings in `application/Frontend/vite.config.mjs` are correct if you've changed backend port.
*   **Permissions Issues (especially with `.sh` scripts or `make`):**
    *   For `.sh` scripts: `chmod +x scripts/your_script.sh`.
    *   `make` should generally work if it's installed. If `make` itself has permission errors, it might be an issue with your system's `make` installation or how you're invoking it.

## Production Build (Frontend)

For deploying the application, you'll need a production build of the frontend:
```bash
make build-frontend
# OR manually:
# cd application/Frontend
# npm run build
```
This generates optimized static files in `application/Frontend/dist`. This is **not** for local development.

---

You have now successfully set up and run the Agora application locally!
