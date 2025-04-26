#!/bin/bash
# Script to commit and push all changes to the Hydra News repository

cd /home/ubuntu/hydra-news

# Initialize git repository if needed
if [ ! -d .git ]; then
  git init
  echo "Initialized new git repository"
fi

# Add all changes to staging
git add .

# Commit with descriptive message
git commit -m "Integrate C and Go with stable cryptographic implementation

- Implemented complete logical entanglement in C
- Created CGO-friendly interface for cryptographic primitives
- Added robust Go bindings for C cryptographic functions
- Implemented session management for keys and secure channels
- Created example application demonstrating cryptographic features
- Added comprehensive build system for C/Go integration"

echo "Changes committed successfully"

# Check if remote exists and push if it does
if git remote | grep -q origin; then
  echo "Pushing to remote repository..."
  git push origin
else
  echo "No remote repository configured. To push changes:"
  echo "  git remote add origin <your-repository-url>"
  echo "  git push -u origin main"
fi
