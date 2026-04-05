# Hugging Face Spaces Deployment Guide

## Overview
This guide will help you deploy the Vulcan Agent to Hugging Face Spaces with both frontend and backend working correctly.

## Prerequisites
1. Hugging Face account (sign up at https://huggingface.co)
2. Hugging Face CLI installed: `pip install huggingface_hub`
3. Logged in: `huggingface-cli login` or `hf auth login`

## Quick Deploy (Recommended)

### Option 1: Using the deployment script
```bash
cd prox-challenge
chmod +x deploy_hf.sh
./deploy_hf.sh
```

### Option 2: Manual deployment

#### Step 1: Login to Hugging Face
```bash
huggingface-cli login
# Enter your HF token when prompted
```

#### Step 2: Create the Space (if it doesn't exist)
```bash
huggingface-cli repo create vulcan-agent --type space --space_sdk docker
```

#### Step 3: Add the HF remote
```bash
git remote add huggingface https://huggingface.co/spaces/<your-username>/vulcan-agent
```

#### Step 4: Build the frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

#### Step 5: Commit and push (including dist folder)
```bash
git add -A
git add frontend/dist/ -f  # Force add dist folder
git commit -m "Deploy to Hugging Face Spaces"
git push huggingface main
```

## Important Configuration

### Space README.md
The README.md must have this YAML frontmatter at the top:

```yaml
---
title: Vulcan Agent
emoji: 🔥
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
---
```

This tells HF Spaces to use Docker SDK, which will build and run our Dockerfile.

### Setting API Keys

After deployment, you need to set your API key:

1. Go to your Space: https://huggingface.co/spaces/<your-username>/vulcan-agent
2. Click "Settings" tab
3. Scroll to "Variables and secrets"
4. Add a secret:
   - Name: `OPENROUTER_API_KEY` (or `ANTHROPIC_API_KEY`)
   - Value: Your API key
   - Description: (optional)

Or using CLI:
```bash
huggingface-cli repo settings <your-username>/vulcan-agent
```

## How It Works

1. **Dockerfile**: Builds both frontend (Node.js) and backend (Python)
2. **Frontend build**: Vite builds the React app to `frontend/dist/`
3. **Backend serving**: FastAPI serves the frontend statically from `/app`
4. **Port**: The app runs on port 7860 (required by HF Spaces)

## Troubleshooting

### Error: "Directory '/app/frontend/dist/public' does not exist"
**Status**: ✅ FIXED

The new code checks if the frontend dist exists before mounting it. If you still see this error:
- Make sure `frontend/dist/` folder exists
- Check that `frontend/dist/index.html` exists
- The Dockerfile should build the frontend automatically

### Frontend not showing
If you only see the API but not the frontend:
1. Check that `frontend/dist/` was committed to git
2. Look for "Serving frontend from:" in container logs
3. If you see "Frontend dist not found" - the build failed

### Backend errors
If the backend fails to start:
1. Check container logs in HF Spaces
2. Verify API keys are set in Space secrets
3. Make sure all Python dependencies are in `requirements.txt`

### Building locally to test
```bash
cd prox-challenge

# Build frontend
cd frontend && npm install && npm run build && cd ..

# Build and run Docker container
docker build -t vulcan-agent .
docker run -p 7860:7860 vulcan-agent
```

## Files Structure for HF Spaces

```
prox-challenge/
├── README.md              # Must have YAML frontmatter for HF
├── Dockerfile             # Builds and runs everything
├── backend/
│   ├── main.py           # FastAPI app
│   ├── requirements.txt  # Python dependencies
│   └── ... (other backend files)
└── frontend/
    ├── dist/             # Built frontend (MUST be in git)
    │   ├── index.html
    │   ├── assets/
    │   └── ...
    └── ... (source files)
```

## Alternative: Connect to GitHub

Instead of pushing to HF git, you can connect your Space to GitHub:

1. Go to Space Settings → "Manage → GitHub"
2. Connect your GitHub account
3. Select the repo: `SatyamDave/take-home-prox`
4. Set up automatic deployments

Note: When using GitHub integration, the Dockerfile will build the frontend automatically, so you don't need to commit `frontend/dist/` to GitHub.

## Next Steps

After deployment:
1. Test the app at https://huggingface.co/spaces/<your-username>/vulcan-agent
2. Set up your API key in Space secrets
3. Try the demo queries:
   - "What happens if polarity is reversed for TIG?"
   - "What's the duty cycle for MIG welding at 200A on 240V?"
   - "I'm getting porosity in my flux-cored welds. What should I check?"
