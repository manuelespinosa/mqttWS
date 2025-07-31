#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Check for required environment variables
if [ -z "$GITHUB_API_KEY" ]; then
  echo "Error: GITHUB_API_KEY environment variable is not set."
  exit 1
fi

if [ -z "$REPO_URL" ]; then
  echo "Error: REPO_URL environment variable is not set."
  exit 1
fi

# Construct the authenticated repository URL
# Assuming REPO_URL is in the format https://github.com/user/repo.git
AUTH_REPO_URL=$(echo "$REPO_URL" | sed "s|https://|https://$GITHUB_API_KEY@|")

# Target directory for cloning
CLONE_DIR="/app"

# Ensure the target directory exists
mkdir -p "$CLONE_DIR"
cd "$CLONE_DIR"

# Check if the .git directory exists to determine if repo is already cloned
if [ -d ".git" ]; then
  echo "Repository already cloned. Attempting to pull latest changes..."
  # Stash any local changes
  git stash || echo "No local changes to stash or git stash failed."
  # Pull the latest changes
  git pull --rebase origin $(git rev-parse --abbrev-ref HEAD) || (echo "Git pull failed. Attempting to recover..." && git rebase --abort && git stash pop || echo "Could not recover automatically.")
  # Attempt to pop the stash if it exists and has content
  if git stash show > /dev/null; then
    git stash pop || echo "Failed to pop stash. Manual intervention may be required if there were important local changes."
  fi
else
  echo "Cloning repository..."
  # Clone the repository. Use --depth 1 for a shallow clone if full history isn't needed.
  # Using a temporary directory for cloning to avoid issues with non-empty /app if bind-mounted
  TEMP_CLONE_DIR=$(mktemp -d)
  git clone --quiet "$AUTH_REPO_URL" "$TEMP_CLONE_DIR"
  # Move contents to /app, excluding .git if it's already there from a previous failed attempt
  # but we want the .git from the new clone.
  # Using rsync to handle this more robustly.
  rsync -av --remove-source-files "$TEMP_CLONE_DIR/." "$CLONE_DIR/"
  rm -rf "$TEMP_CLONE_DIR"
  cd "$CLONE_DIR" # Ensure we are in the app directory
fi

# Install/update dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
  echo "Installing/updating dependencies from requirements.txt..."
  pip install --no-cache-dir -r requirements.txt
else
  echo "requirements.txt not found. Skipping dependency installation."
fi

echo "Starting application..."
# Execute the command passed to the docker run or docker-compose
exec "$@"
