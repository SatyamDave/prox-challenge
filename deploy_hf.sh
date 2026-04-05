#!/bin/bash

# Deployment script for Hugging Face Spaces
# This script prepares and pushes the Vulcan Agent to Hugging Face Spaces

set -e

echo "🚀 Deploying Vulcan Agent to Hugging Face Spaces..."
echo ""

# Check if logged in
if ! hf auth whoami &>/dev/null; then
    echo "❌ Not logged in to Hugging Face"
    echo "Please run: huggingface-cli login"
    echo "Or: hf auth login"
    exit 1
fi

echo "✓ Logged in to Hugging Face"
echo ""

# Check if space exists
SPACE_NAME="vulcan-agent"
USERNAME=$(hf auth whoami --json 2>/dev/null | grep -o '"username":"[^"]*"' | cut -d'"' -f4)

if [ -z "$USERNAME" ]; then
    echo "❌ Could not determine username"
    exit 1
fi

echo "Username: $USERNAME"
echo "Space: $SPACE_NAME"
echo ""

# Create space if it doesn't exist
if ! huggingface-cli repo info $USERNAME/$SPACE_NAME &>/dev/null; then
    echo "📦 Creating Hugging Face Space: $SPACE_NAME"
    huggingface-cli repo create $SPACE_NAME --type space --space_sdk docker
    echo "✓ Space created"
    echo ""
fi

# Add HF remote if not exists
if ! git remote | grep -q "huggingface"; then
    echo "🔗 Adding Hugging Face remote..."
    git remote add huggingface https://huggingface.co/spaces/$USERNAME/$SPACE_NAME
    echo "✓ Remote added: huggingface"
    echo ""
fi

# Build frontend
echo "🔨 Building frontend..."
cd frontend
npm install
npm run build
cd ..
echo "✓ Frontend built"
echo ""

# Temporarily allow dist/ in git for this push
echo "📝 Preparing files for deployment..."

# Create .git/info/exclude to allow pushing dist without modifying .gitignore
echo "frontend/node_modules/" > .git/info/exclude

# Add all necessary files
git add -A
git add frontend/dist/ -f  # Force add dist despite .gitignore

# Check if there are changes
if git diff --cached --quiet; then
    echo "⚠️  No changes to commit"
else
    echo "💾 Committing changes..."
    git commit -m "Deploy to Hugging Face Spaces"
fi

echo ""
echo "🚀 Pushing to Hugging Face..."
git push huggingface main

echo ""
echo "✅ Deployment complete!"
echo "Your app should be available at: https://huggingface.co/spaces/$USERNAME/$SPACE_NAME"
echo ""
echo "⚠️  Don't forget to set your API key in Space secrets:"
echo "   - OPENROUTER_API_KEY or ANTHROPIC_API_KEY"
echo ""
