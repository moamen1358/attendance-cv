#!/bin/bash

# Get current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
CURRENT_COMMIT=$(git rev-parse HEAD)

echo "Current branch: $CURRENT_BRANCH"
echo "Current commit: $CURRENT_COMMIT"

# Checkout main branch
git checkout main

# Reset main branch to the commit you want
git reset --hard $CURRENT_COMMIT

# Push to remote if needed (use --force with caution)
echo "Would you like to push to remote? This will overwrite the remote main branch. (y/N)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    git push --force origin main
    echo "✅ Main branch has been updated and pushed to remote."
else
    echo "✅ Main branch has been updated locally. Use 'git push --force origin main' to update remote."
fi

# Return to original branch if different from main
if [ "$CURRENT_BRANCH" != "main" ]; then
    git checkout $CURRENT_BRANCH
    echo "Returned to branch: $CURRENT_BRANCH"
fi

echo "Done! The current commit is now the main state of the repository."
