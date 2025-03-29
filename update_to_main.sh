#!/bin/bash
# Script to merge test_branch into main

# Make sure we're in the project directory
cd /home/invisa/Desktop/my_grad_streamlit

# Checkout main branch
git checkout main

# Make sure main is up to date
git pull

# Merge test_branch into main
git merge test_branch

# Push the updated main branch to remote
git push

echo "Successfully merged test_branch into main branch!"
