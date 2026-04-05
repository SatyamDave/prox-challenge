# Executable Knowledge Engine For Physical Systems

> Manuals are not text. They are compressed machine behavior. This project turns a welding manual into an executable knowledge system that can reason over state, simulate outcomes, and explain the machine visually.

![Vulcan OmniPro 220](product.webp)

## What This Is

This is not a chatbot.

This is a system that converts technical documentation for a physical product into a machine-understanding layer that can:

- reason over machine state
- retrieve across text, tables, procedures, and diagrams
- simulate outcomes from configuration changes
- generate the right explanation format for the job

The current implementation targets the Vulcan OmniPro 220 multiprocess welder, but the architecture is meant for a broader class of complex physical systems.

## The Problem

Technical support for physical products breaks because product knowledge does not live in plain text.

A welder manual is not just paragraphs. It is:

- wiring topology
- duty-cycle constraints
- process-dependent polarity rules
- setup procedures
- troubleshooting logic
- implicit technician knowledge

Traditional RAG systems flatten this into chunks and lose the structure that matters. They can quote a page, but they struggle to explain how the machine behaves.

## The Core Idea

Instead of retrieving text from manuals, this system:

1. builds a structured model of the machine
2. retrieves evidence across node types
3. simulates behavior from the current state
4. explains results with visual artifacts

That changes the product from “ask questions about a manual” to “interact with a system that understands the machine.”

## What The System Does

### 1. Structured Knowledge Extraction

The backend converts PDFs into typed knowledge:

- `text` nodes for explanatory sections
- `table` nodes for constraint matrices and specs
- `procedure` nodes for step-by-step operations
- `diagram` candidates for visual configuration context
- relationships connecting related nodes on the same topic

### 2. Multi-Hop Retrieval

Queries are expanded, retrieved across structured nodes, and enriched by following relationships. The system is designed to pull together the table, the setup guidance, and the visual context for the same question.

### 3. Reasoning + Simulation

The agent constructs an internal machine state and runs a lightweight simulation loop over it.

Example:

`wrong polarity -> cable state -> current flow -> heat distribution -> weld outcome`

This is especially visible in polarity questions, where the system distinguishes between expected polarity and actual polarity, then predicts the effect of the mismatch.

### 4. Representation Engine

The response is not locked to text. The system chooses an artifact based on the task:

- polarity visualizer
- duty-cycle visualizer
- troubleshooting tree
- parameter explorer
- interactive spec table

## Example

User asks:

`What happens if polarity is reversed?`

The system:

1. constructs machine state
2. infers expected polarity for the process
3. simulates reversed current flow
4. propagates effects to heat balance and weld quality
5. visualizes the failure mode

That is the difference between documentation retrieval and machine reasoning.

## Demo Narrative

Open the demo with:

> Manuals are not text. They are systems. So I built a system that understands machines.

Then show three moments:

### 1. Polarity Simulation

Ask:

`What happens if polarity is reversed for TIG?`

Show:

- machine state
- expected vs actual polarity
- current-flow effect
- predicted weld failure mode
- visual polarity artifact

Frame it as:

> This is not answering from a paragraph. It is simulating the consequence of a machine configuration.

### 2. Duty Cycle Reasoning

Ask:

`What's the duty cycle for MIG welding at 200A on 240V?`

Show:

- structured spec retrieval
- duty-cycle visualization
- operating window in a 10-minute cycle

Frame it as:

> The answer is not just a number. It is an operating constraint represented visually.

### 3. Troubleshooting

Ask:

`I'm getting porosity in my flux-cored welds. What should I check?`

Show:

- reasoning summary
- simulated diagnosis path
- troubleshooting tree

Frame it as:

> The system turns diagnostic knowledge into an actionable path instead of a wall of advice.

## Why This Matters

This is a first step toward replacing human technical support for complex physical products.

The value is not only better answers. It is a new interface for product knowledge:

- faster support resolution
- better onboarding for non-experts
- lower dependence on tribal knowledge
- a foundation for simulation-driven support experiences

## Architecture

### Backend

- `backend/knowledge_extractor.py`
  Extracts structured nodes and lightweight relationships from manuals.

- `backend/vector_store.py`
  Indexes structured knowledge nodes for retrieval.

- `backend/advanced_agent.py`
  Runs retrieval, evidence synthesis, simulation, artifact selection, and guarded fallback behavior.

- `backend/main.py`
  Serves the API and exposes the technical response package.

### Frontend

- `frontend/src/App.tsx`
  Chat UI with reasoning summary, evidence, assumptions, and simulation loop.

- `frontend/src/components/ArtifactRenderer.tsx`
  Renders visual explanations including the polarity simulator and duty-cycle visualizer.

## Response Shape

The system returns a structured response with the pieces needed for product-grade UX:

```json
{
  "state": { "process": "TIG", "connections": { "torch": "positive" } },
  "simulation": [
    { "step": 1, "event": "Apply cable state", "effect": "Torch on positive" }
  ],
  "artifact": { "type": "polarity_diagram", "data": {} },
  "explanation": "Reversed polarity shifts heat and destabilizes the arc.",
  "confidence": { "label": "medium", "score": 0.72 },
  "assumptions": ["Assumed steel unless material specified."]
}
```

## Quick Start

```bash
cd prox-challenge

cd backend
pip install -r requirements.txt
python main.py
```

In a second terminal:

```bash
cd prox-challenge/frontend
npm install
npm run dev
```

Then open [http://localhost:5173](http://localhost:5173).

## Best Demo Queries

- `What happens if polarity is reversed for TIG?`
- `What's the duty cycle for MIG welding at 200A on 240V?`
- `I'm getting porosity in my flux-cored welds. What should I check?`
- `What are the recommended settings for welding 1/4 inch mild steel?`

## What I Would Build Next

- higher-fidelity diagram extraction from PDFs
- richer executable state models for wire feed, gas flow, and thermal limits
- interactive state editing in the UI so users can modify machine setup directly
- support workflows that auto-generate technician-grade visual instructions

## Bottom Line

This project is a prototype for a new category of support software:

an executable knowledge engine for physical systems.
