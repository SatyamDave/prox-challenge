# Architecture Deep Dive

This document explains the technical architecture and design decisions in detail.

## System Overview

```
┌─────────────────┐
│   User Browser  │
│   (React App)   │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  FastAPI Server │
│   (Port 8000)   │
└────────┬────────┘
         │
         ├──────────┐
         │          │
         ▼          ▼
┌──────────────┐ ┌────────────────┐
│ Vector Store │ │ Claude 3.5 API │
│  (ChromaDB)  │ │  (Anthropic)   │
└──────────────┘ └────────────────┘
```

## Data Flow

### 1. Knowledge Extraction (Offline)

When the backend starts for the first time:

1. **PDF Processing** (`knowledge_extractor.py`)
   ```
   PDF → PyMuPDF → Text Extraction
                 └─→ Image Extraction (base64)
                 └─→ Semantic Chunking
   ```

2. **Chunking Strategy**
   - Detect section headings (ALL CAPS or ending with `:`)
   - Group related content (lists, procedures, tables)
   - Target chunk size: ~500 characters
   - Preserve metadata: page number, heading, source file

   **Why this matters**: Traditional fixed-size chunking breaks tables in half and splits procedures. Semantic chunking keeps context intact.

3. **Storage**
   - Save full KB (with images) to memory for image retrieval
   - Save lite KB (without images) to JSON for quick restart
   - Embed text chunks into ChromaDB

### 2. Vector Embedding

**Model**: `all-MiniLM-L6-v2` from sentence-transformers

**Why this model?**
- Fast: 384-dim embeddings (vs 1536 for OpenAI)
- Good quality: ~80% accuracy on semantic similarity benchmarks
- Local: No API calls, no latency
- Free: No per-request costs

**Alternative considered**: OpenAI's `text-embedding-ada-002`
- Pros: Slightly better quality
- Cons: API costs, latency, requires internet
- Decision: Quality difference minimal for this use case

### 3. Query Processing (Online)

User query flow:

```
User Input
    ↓
Frontend (React)
    ↓ [POST /chat]
FastAPI Server
    ↓
Claude Agent
    ├─→ [Tool: search_manual]
    │      ↓
    │   Vector Store Query
    │      ↓
    │   Return top 5 chunks
    │
    ├─→ [Tool: get_images_for_topic]
    │      ↓
    │   Filter images by page/context
    │      ↓
    │   Return relevant images
    │
    └─→ [Tool: create_artifact]
           ↓
        Generate artifact spec
           ↓
        Return {type, title, data}
    ↓
Synthesize response
    ↓
Return {text, artifacts, images}
    ↓
Frontend Renders
```

## Agent Design

### Tool Calling Flow

Claude uses **function calling** (tool use) to orchestrate actions:

1. **Initial Request**: User asks "What's the duty cycle at 200A on 240V?"

2. **First Tool Call**: Claude decides to search
   ```json
   {
     "name": "search_manual",
     "input": {"query": "duty cycle 200A 240V MIG"}
   }
   ```

3. **Tool Execution**: Vector store returns relevant chunks
   ```python
   [
     {
       "text": "Duty Cycle @ 240V: 200A = 60%, 180A = 100%, ...",
       "page": 12,
       "source": "owner-manual.pdf"
     },
     ...
   ]
   ```

4. **Second Tool Call**: Claude decides to create artifact
   ```json
   {
     "name": "create_artifact",
     "input": {
       "type": "calculator",
       "title": "Duty Cycle Calculator",
       "data": {
         "processes": ["MIG", "Flux-Cored", "TIG", "Stick"],
         "dutyCycles": {
           "MIG_200A_240V": "60%",
           "MIG_180A_240V": "100%",
           ...
         }
       }
     }
   }
   ```

5. **Final Response**: Claude synthesizes natural language + artifact
   ```
   "The duty cycle for MIG welding at 200A on 240V is 60% (page 12).
    This means you can weld continuously for 6 minutes out of every 10.

    I've created an interactive calculator below where you can explore
    duty cycles for different settings."
   ```

### System Prompt

Key parts of the system prompt:

```
1. Always search the manual for technical details
2. Cite page numbers
3. Create artifacts for visual/interactive content
4. Friendly but not condescending tone
5. If unsure, say so - don't hallucinate
```

## Frontend Architecture

### Component Hierarchy

```
App
├─→ Header
│   ├─→ Title
│   ├─→ Stats
│   └─→ Reset Button
│
├─→ Message List
│   └─→ Message (repeated)
│       ├─→ Text (Markdown)
│       ├─→ Artifacts (repeated)
│       │   └─→ ArtifactRenderer
│       │       ├─→ Calculator
│       │       ├─→ Diagram
│       │       ├─→ Table
│       │       ├─→ Flowchart
│       │       └─→ Configurator
│       └─→ Images (repeated)
│
└─→ Input Area
    ├─→ Textarea
    └─→ Send Button
```

### State Management

Simple React state (no Redux/Zustand needed):

```typescript
const [messages, setMessages] = useState<Message[]>([])
const [input, setInput] = useState('')
const [loading, setLoading] = useState(false)
const [stats, setStats] = useState(null)
```

**Why no complex state management?**
- Linear message flow (no branching)
- No cross-component shared state
- Simple CRUD operations
- Easier to understand and maintain

### Artifact Rendering

Each artifact type has custom rendering logic:

**Calculator**:
```typescript
const [voltage, setVoltage] = useState(240)
const [amperage, setAmperage] = useState(200)

const dutyCycle = data.dutyCycles[`${process}_${amperage}A_${voltage}V`]
```

**Diagram** (SVG):
```typescript
<svg viewBox="0 0 400 300">
  {connections.map(conn => (
    <g>
      <rect {...conn} />
      <line {...conn.wire} />
    </g>
  ))}
</svg>
```

**Flowchart**:
```typescript
{steps.map((step, idx) => (
  <div>
    <div className="step-number">{idx + 1}</div>
    <div>{step.title}</div>
    {step.options && <ul>{step.options.map(...)}</ul>}
  </div>
))}
```

## Performance Considerations

### Backend

**Vector Search**:
- ChromaDB uses HNSW (Hierarchical Navigable Small World) index
- Query time: O(log n) where n = number of chunks
- For ~500 chunks: < 10ms per search

**Embedding**:
- Pre-computed during startup
- Cached in ChromaDB persistent storage
- No re-embedding on subsequent runs

**API Response Time**:
- Vector search: ~10ms
- Claude API call: ~1-3 seconds (depends on response length)
- Total: ~1.5-4 seconds per query

### Frontend

**Bundle Size**:
- React + React-DOM: ~130KB gzipped
- Axios: ~10KB
- TailwindCSS: ~5KB (purged)
- Total: ~150KB initial load

**Rendering**:
- Virtual DOM for efficient updates
- Lazy rendering of artifacts (only when in viewport)
- Image lazy loading for manual images

## Security Considerations

### Current Implementation (Development)

- CORS: Allow all origins (for local dev)
- API keys: In `.env` file (gitignored)
- No authentication

### Production Recommendations

1. **API Keys**:
   - Use environment variables (Vercel/Railway secrets)
   - Rotate keys regularly
   - Use separate keys for dev/prod

2. **CORS**:
   - Whitelist specific frontend domains
   - No wildcards

3. **Rate Limiting**:
   - Implement per-IP rate limiting
   - Prevent API abuse

4. **Authentication**:
   - Add user sessions
   - Implement JWT tokens
   - Track usage per user

## Scalability

### Current Limitations

- **Single instance**: No horizontal scaling
- **In-memory state**: Conversation history lost on restart
- **Local vector store**: Limited to single machine

### Scaling Recommendations

1. **Stateless Backend**:
   - Move conversation history to Redis
   - Use session IDs for user tracking

2. **Distributed Vector Store**:
   - Migrate ChromaDB → Pinecone/Weaviate
   - Enable multi-region deployment

3. **Caching**:
   - Cache common queries (duty cycle tables)
   - CDN for frontend assets
   - Redis for API responses

4. **Load Balancing**:
   - Multiple FastAPI instances
   - Nginx reverse proxy
   - Auto-scaling based on traffic

## Testing Strategy

### Unit Tests (TODO)

```python
# test_knowledge_extractor.py
def test_semantic_chunking():
    chunks = extractor._create_semantic_chunks(sample_text, 0, "test.pdf")
    assert len(chunks) > 0
    assert all('page' in c for c in chunks)

# test_vector_store.py
def test_search_relevance():
    results = store.search("duty cycle 200A")
    assert "duty cycle" in results[0]['text'].lower()
```

### Integration Tests (TODO)

```python
# test_agent.py
def test_duty_cycle_query():
    response = agent.chat("What's the duty cycle at 200A on 240V?")
    assert "60%" in response['text']
    assert len(response['artifacts']) > 0
```

### End-to-End Tests (TODO)

```typescript
// test/e2e.spec.ts
test('user can ask about duty cycle', async () => {
  await page.fill('textarea', "What's the duty cycle at 200A?")
  await page.click('button:has-text("Send")')
  await expect(page.locator('text=60%')).toBeVisible()
})
```

## Cost Analysis

### Development Costs (per 1000 queries)

**Claude API**:
- Input tokens: ~2,000 per query (manual chunks + conversation)
- Output tokens: ~500 per query (response + tool calls)
- Cost: ~$0.015 input + ~$0.038 output = **$0.053 per query**
- 1000 queries = **~$53**

**Alternatives**:
- GPT-4: ~$0.12 per query (2-3x more expensive)
- GPT-3.5: ~$0.002 per query (cheaper but worse quality)

**Hosting** (if deployed):
- Backend: Railway (512MB) = $5/month
- Frontend: Vercel (free tier) = $0
- Total: **$5/month** for hobby use

## Future Improvements

### Short Term

1. **Error Handling**:
   - Retry failed API calls
   - Graceful degradation
   - User-friendly error messages

2. **Caching**:
   - Cache common queries
   - Reduce API costs by 50-70%

3. **Logging**:
   - Track query patterns
   - Identify knowledge gaps
   - Monitor performance

### Long Term

1. **Voice Interface**:
   - Use Anthropic's voice API
   - Simulate phone support
   - Handle audio input/output

2. **Multi-modal Input**:
   - Upload photos of weld defects
   - Claude vision for diagnosis
   - Reference manual images

3. **Fine-tuning**:
   - Collect user feedback
   - Fine-tune retrieval
   - Improve artifact generation

4. **Multi-product**:
   - Extend to other Harbor Freight tools
   - Shared infrastructure
   - Product-specific knowledge bases

---

Built with attention to detail and a lot of coffee ☕️
