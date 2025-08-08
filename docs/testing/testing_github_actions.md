# Step-by-Step Guide to Test GitHub Actions for Agora

This guide walks you through testing the GitHub Actions workflows (`deploy.yml` and `super-linter.yml`) by creating a feature branch and pull request. This is the standard way to ensure changes pass linting and tests before merging into `main`.

The project uses two main workflows:
1.  **`super-linter.yml`**: Runs automatically on pushes and pull requests to `main` and `feature-name` branches. It uses Super-Linter to check code quality for various languages (Python, CSS, HTML, etc.).
2.  **`deploy.yml`**: Runs automatically on pushes and pull requests to `main`. It performs backend tests (`pytest`), builds the frontend (`npm run build`), and (on pushes to `main` only) deploys the application to the server.

## Prerequisites

- Git installed on your local machine
- Access to the GitHub repository (with push permissions)
- A local clone of the repository

## Step 1: Make Sure You Have the Latest Code

```bash
# Navigate to your local repository (replace with your actual path)
cd /path/to/csc648-fa25-0104-team02

# Check current branch
git branch

# Switch to the main branch
git checkout main

# Pull the latest changes from the main branch
git pull origin main

# Check your current status
git status
```

## Step 2: Create a Feature Branch

Work on your changes in a dedicated feature branch. Give it a descriptive name.
```bash
# Create and switch to a new feature branch (replace <feature-description> appropriately)
git checkout -b feature/<feature-description> 

# Verify you're on the new branch
git branch 
```

## Step 3: Make Your Code Changes

Make the necessary code modifications for your feature or bug fix on this branch.

## Step 4: Commit Your Changes

```bash
# Add the changed file(s)
git add .

# Commit the changes with a descriptive message
git commit -m "Feat: Implement feature X" 
# Or: git commit -m "Fix: Resolve issue Y"
```

## Step 5: Push Your Changes to GitHub

```bash
# Push your feature branch to GitHub
# The -u flag sets the upstream branch for future pushes
git push -u origin feature/<feature-description>
```

## Step 6: Create a Pull Request on GitHub

1.  Go to your repository page on GitHub.
2.  You should see a notification about your recently pushed branch. Click "Compare & pull request".
3.  Ensure the base branch is `main` and the compare branch is your feature branch.
4.  Add a clear title and description for your pull request.
5.  Click "Create pull request".

## Step 7: Wait for GitHub Actions Checks

1.  After creating the PR, scroll down to the "Checks" section near the bottom.
2.  You should see checks corresponding to your workflows (e.g., `Lint Code Base`, `Test, Build, and Deploy / test (pull_request)`). They might take a minute to start.
3.  Click on "Details" next to each workflow run to see its progress.

## Step 8: Check Workflow Execution

1.  **Linting (`Lint Code Base` workflow):** Check if the `Lint Code Base / run-lint` job passes. If it fails, examine the logs for specific linting errors reported by Super-Linter.
2.  **Testing & Building (`Test, Build, and Deploy` workflow):**
    *   Check if the `Run Backend Tests` job passes. If it fails, review the `pytest` output in the logs.
    *   Check if the `Build Frontend` job passes and successfully creates the `frontend-dist` artifact.
3.  **Deployment:** Note that the `Deploy to Server` job in `deploy.yml` is configured to run *only* on pushes/merges to `main`, so it will not run on the pull request itself.

## Step 9: Review Build Artifacts (If Needed)

1.  Navigate to the "Summary" page for the `Test, Build, and Deploy` workflow run associated with your PR.
2.  Scroll down to the "Artifacts" section.
3.  You should see the `frontend-dist` artifact listed if the `Build Frontend` job completed successfully.
4.  You can download it to inspect the contents if needed.

## Step 10: Check for Any Errors

If there are any errors in the workflow:
1. Look at the error messages in the logs
2. Check the failing step
3. Make necessary corrections to your code or workflow file

## Step 11: Address Feedback / Merge the PR

-   If checks fail or reviewers request changes, make the necessary commits on your feature branch and push them. The checks will re-run automatically.
-   Once all checks pass and the PR is approved, merge it into the `main` branch.

## Step 12: Clean Up Locally (After Merging)

```bash
# Switch back to the main branch
git checkout main

# Pull the latest changes (including your merged PR)
git pull origin main

# Delete the local feature branch
git branch -D feature/<feature-description>

# Optional: Delete the remote feature branch (GitHub often provides a button for this after merging)
# git push origin --delete feature/<feature-description>
```

## Common Issues and Solutions

### Workflow Not Triggering

- Make sure your workflow file is in `.github/workflows/`
- Check the syntax in your YAML file
- Verify the trigger events match your action (e.g., `push` to branch)

### Build Failures

- Check Node.js version compatibility
- Verify all dependencies are properly listed
- Look for syntax errors in your code

### Test Failures (`Run Backend Tests` job)

-   Review the `pytest` output logs for specific assertion errors or exceptions.
-   Ensure the test environment setup in the workflow (`deploy.yml`) is correct (Python version, dependencies in `requirements-dev.txt`).
-   Verify test dependencies are installed correctly during the workflow run.

### Linting Failures (`Lint Code Base` job)

-   Check the Super-Linter output for specific files and line numbers causing errors.
-   Ensure code formatting matches the expected style for the respective language.
-   Verify the `FILTER_REGEX_EXCLUDE` in `super-linter.yml` is correctly ignoring build artifacts or unwanted directories (like `application/Frontend/dist/`).

## Understanding Workflow Results

When reviewing your workflow run:

- ✅ Green checkmarks indicate success
- ❌ Red X marks indicate failures
- ⚠️ Yellow warnings indicate potential issues
- Logs show detailed output from each step
