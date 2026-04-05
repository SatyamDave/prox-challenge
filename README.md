---
title: Vulcan Agent
emoji: 🔥
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
---

# Vulcan OmniPro 220 Agent

An executable knowledge engine for physical systems - starting with the Vulcan OmniPro 220 multiprocess welder.

## What This Does

This system converts technical documentation into a machine-understanding layer that can:
- Reason over machine state
- Retrieve across text, tables, procedures, and diagrams  
- Simulate outcomes from configuration changes
- Explain results with visual artifacts

## Architecture

- **Backend**: FastAPI server with advanced RAG agent
- **Frontend**: React + TypeScript chat interface
- **Knowledge Base**: Structured extraction from PDFs
- **Vector Store**: Multi-type node retrieval

## Quick Start

The app will start automatically on port 7860.

## Environment Variables

Set these in Hugging Face Space secrets:
- `OPENROUTER_API_KEY`: Your OpenRouter API key (starts with `sk-or-`)
- or `ANTHROPIC_API_KEY`: Your Anthropic API key (starts with `sk-ant-`)

## Demo Queries

- "What happens if polarity is reversed for TIG?"
- "What's the duty cycle for MIG welding at 200A on 240V?"
- "I'm getting porosity in my flux-cored welds. What should I check?"
