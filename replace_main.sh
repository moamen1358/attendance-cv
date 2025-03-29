#!/bin/bash
# Script to replace main with test_branch

# Make sure we're in the project directory
cd /home/invisa/Desktop/my_grad_streamlit

# Rename test_branch locally to temp-main
git checkout test_branch
git branch -m temp-main

# Delete the old main branch locally
git branch -D main

# Rename temp-main to main
git branch -m main

# Push the new main branch to remote
git push -f origin main

# Set tracking for the new main branch
git branch --set-upstream-to=origin/main main

echo "Successfully replaced main branch with test_branch!"
