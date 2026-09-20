# NeuralQuery Architecture Specification

NeuralQuery is a modular full-stack research intelligence application that pairs real-time web and news retrieval with grounded LLM synthesis. This document details the technical architecture, component boundaries, execution flows, provider abstractions, model loading mechanics, citation preservation, and deployment patterns.

---

## 1. High-Level Architecture Topology

NeuralQuery is structured as a decoupled Modular Monolith:

```mermaid
flowchart TB
    subgraph ClientTier["Client Tier (SPA / Vanilla JS)"]
        direction TB
        UI["Browser UI\n(landing.html, chat.html, admin.html)"]
        ClientEngine["Client Engine (static/js/main.js)\nJWT State | Markdown Render | Source Drawer"]
        UI --- ClientEngine
    end

    subgraph ApiTier["Ingress & Application Gateway (app.py)"]
        direction TB
        WSGI["Waitress WSGI / Flask Gateway"]
        CORS["Flask-CORS Guard"]
        AuthMid["JWT Auth Guard (auth.py)"]
        WSGI --> CORS --> AuthMid
    end

    subgraph ServiceTier["Core Orchestration & Research Pipeline (research.py)"]
        direction TB
        Orchestrator["Research Orchestrator\n(perform_research)"]
        
        subgraph RetrievalPipeline["Multi-Source Retrieval Engine"]
            DDG["DuckDuckGo Search\n(duckduckgo_search)"]
            News["NewsAPI Engine\n(newsapi-python)"]
            Scraper["Content Fetcher & Cleaner\n(requests + BeautifulSoup)"]
            DDG & News --> Scraper
        end

        Orchestrator --> RetrievalPipeline
    end

    subgraph ProviderTier["Pluggable LLM Provider Boundary (llm_providers.py)"]
        direction TB
        Factory["Provider Factory: get_llm_provider()"]
        
        Gemini["GeminiProvider\n(gemini-2.0-flash / fallback cascade)"]
        NeuralQuery["NeuralQueryProvider\n(Qwen2.5-1.5B-Instruct + LoRA Adapter)"]
        
        Factory -->|MODEL_PROVIDER=gemini| Gemini
        Factory -->|MODEL_PROVIDER=neuralquery| NeuralQuery
    end

    subgraph EvaluationTier["Accuracy & Grounding Layer (accuracy.py)"]
        AccCalc["Deterministic Accuracy Evaluator\nKeyword Overlap | Citation Verification | Confidence"]
    end

    subgraph PersistenceTier["Persistence Layer (models.py)"]
        SQLAlchemy["SQLAlchemy ORM Engine"]
        PostgresDB[(PostgreSQL / SQLite Storage\nUsers, Conversations, Messages, Uploads)]
        SQLAlchemy --- PostgresDB
    end

    ClientEngine -->|HTTP POST /api/research| WSGI
    AuthMid --> Orchestrator
    Scraper -->|Extracted Evidence + Metadata| Factory
    Gemini & NeuralQuery -->|Synthesized Research| AccCalc
    AccCalc -->|Accuracy Score & Metrics| Orchestrator
    Orchestrator --> SQLAlchemy
    Orchestrator -->|Grounded Response + Preserved Sources + Score| ClientEngine
```

---

## 2. End-to-End Request Flow

When an authenticated user submits a query from the chat interface, the system executes through the following sequence:

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser
    participant App as Flask Router (app.py)
    participant Auth as Auth Manager (auth.py)
    participant Res as Orchestrator (research.py)
    participant Search as Search & Scraper
    participant Prov as LLM Provider (llm_providers.py)
    participant Acc as Accuracy Engine (accuracy.py)
    participant DB as Database (models.py)

    User->>App: POST /api/research {query, conversation_id}
    App->>Auth: Validate JWT Bearer Token
    Auth-->>App: current_user_id
    App->>DB: Record user message
    App->>Res: perform_research(query)
    Res->>Search: search_web(query) + search_news(query)
    Search-->>Res: Top 8 combined search hits
    Res->>Search: fetch_article_content(url) [concurrent/sequential with delays]
    Search-->>Res: List of valid sources [url, title, snippet, content]
    Res->>Prov: get_llm_provider().generate(query, valid_sources)
    alt MODEL_PROVIDER == 'neuralquery'
        Prov->>Prov: Lazy-load Qwen2.5 + LoRA on detected device
        Prov->>Prov: Generate grounded synthesis
    else MODEL_PROVIDER == 'gemini'
        Prov->>Prov: Query Gemini 2.0 Flash (with cascade fallback)
    end
    Prov-->>Res: Synthesized research markdown
    Res->>Acc: calculate_accuracy(valid_sources, ai_response)
    Acc-->>Res: {overall_accuracy, confidence_level, sources_analyzed}
    Res-->>App: {success, response, sources, accuracy}
    App->>DB: Persist assistant message & accuracy metrics
    App-->>User: 200 OK JSON {response, accuracy, sources, conversation_id}
    User->>User: Render markdown + interactive source accordion
```

---

## 3. Retrieval Pipeline & Multi-Source Gathering

The retrieval pipeline in [research.py](file:///c:/Users/kesha/OneDrive/Desktop/NeuralQuery/research.py) coordinates two complementary search layers:
1. **DuckDuckGo Search (`search_web`):**
   - Free, legal search API via `duckduckgo_search` library.
   - Requires no API key.
   - Fetches organic web search results with title, URL, and snippet.
   - Incorporates retry logic with jitter sleep to handle temporary network interruptions.
2. **NewsAPI (`search_news`):**
   - When `NEWS_API_KEY` is configured, queries the `get_everything` endpoint for recent news articles.
   - Prioritizes timely reporting for breaking queries and attaches an `is_news: true` flag.

Both result streams are combined (news prioritized for timeliness) and capped at the top 8 candidates for deep extraction.

---

## 4. Web Content Extraction & Evidence Processing

Raw HTML search snippets are often incomplete. The function `fetch_article_content(url)` enhances evidence quality:
- **Polite Crawling:** Applies `Config.REQUEST_DELAY` (1 second) and a descriptive User-Agent header (`NeuralQuery/1.0`).
- **DOM Cleaning:** Removes `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>`, `<aside>`, and `<iframe>` elements using BeautifulSoup.
- **Semantic Heuristics:** Searches for standard content containers (`article`, `main`, `[role="main"]`, `.content`, `.post-content`) before falling back to `<body>`.
- **Text Normalization:** Strips boilerplate, discards one-line navigation links (< 20 characters), and limits body text to the most relevant 2,000 characters to conserve context length.

---

## 5. LLM Provider Abstraction

The LLM abstraction in [llm_providers.py](file:///c:/Users/kesha/OneDrive/Desktop/NeuralQuery/llm_providers.py) decouples research orchestration from the concrete language model:

```python
class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, query: str, sources: List[Dict]) -> str:
        """Synthesize response from query and retrieved sources."""
```

The factory `get_llm_provider()` inspects `Config.MODEL_PROVIDER` (`'gemini'` vs `'neuralquery'`) and instantiates the selected provider.

---

## 6. Gemini Provider (`GeminiProvider`)

- **Model Cascade:** Attempts inference against a prioritized sequence of models:
  1. `models/gemini-2.0-flash`
  2. `models/gemini-flash-latest`
  3. `models/gemini-pro-latest`
  4. `models/gemini-2.0-flash-lite-preview`
  5. `models/gemini-1.5-flash-latest`
  6. `models/gemma-3-27b-it`
- **Error Boundaries:** Catches rate-limit (HTTP 429) errors, safety blocks, and network timeouts.
- **Fallback Display:** If API generation fails but sources were retrieved, it formats the raw sources cleanly for the user rather than failing silently.

---

## 7. NeuralQuery Qwen Provider (`NeuralQueryProvider`)

- **Base Architecture:** `Qwen/Qwen2.5-1.5B-Instruct`
- **LoRA Adaptation:** Attaches low-rank weights from `model/neuralquery-production-adapter/`.
- **Prompt Structure:** Strictly bifurcates the prompt:
  ```
  Research Question:
  <query>

  Retrieved Evidence:
  [Source 1]: <title>
  URL: <url>
  Evidence Content:
  <content>
  ```
- **Grounding Operational Constraints:** Instructs the model to:
  - Base answers strictly on retrieved evidence.
  - Explicitly refuse unsupported claims when facts are absent.
  - Highlight discrepancies between conflicting sources.
  - Filter irrelevant web noise.
  - Express calibrated uncertainty for preliminary or partial evidence.

---

## 8. Lazy Loading & Device Detection

The custom LLM is loaded **lazily on the first invocation** of `generate()`, preventing unnecessary memory consumption when running with Gemini:

```mermaid
flowchart TD
    Start["First generate() call"] --> CheckLoaded{"Model already loaded?"}
    CheckLoaded -- Yes --> RunInference["Execute PyTorch Inference"]
    CheckLoaded -- No --> CheckDevice["Detect Device Setting (NEURALQUERY_DEVICE)"]
    
    CheckDevice -->|auto| CheckCUDA{"torch.cuda.is_available()?"}
    CheckCUDA -- Yes --> SetupCUDA["Select CUDA + float16\n(device_map='auto')"]
    CheckCUDA -- No --> CheckMPS{"torch.backends.mps.is_available()?"}
    CheckMPS -- Yes --> SetupMPS["Select Apple Silicon MPS + float16"]
    CheckMPS -- No --> SetupCPU["Select CPU + float32\n(log warning on latency)"]
    
    SetupCUDA & SetupMPS & SetupCPU --> LoadTok["Load AutoTokenizer (left-padding)"]
    LoadTok --> LoadBase["Load AutoModelForCausalLM (Qwen2.5-1.5B)"]
    LoadBase --> CheckAdapter{"adapter_model.safetensors exists?"}
    CheckAdapter -- Yes --> AttachLoRA["Attach PeftModel LoRA weights"]
    CheckAdapter -- No --> WarnBase["Run base model + log advisory notice"]
    AttachLoRA & WarnBase --> RunInference
```

---

## 9. Citation & Source Preservation

Preserving verifiable source citations is fundamental to NeuralQuery's design:
1. **Metadata Retention:** Original source URLs, titles, snippets, and publishing metadata are retained in the `valid_sources` list within `research.py`.
2. **Attribution Tags:** The prompt assigns indexed identifiers (`[Source 1]`, `[Source 2]`) to each evidence block. The LLM references these markers in its text.
3. **No Hallucinated URLs:** The system instructions explicitly forbid the LLM from inventing URLs.
4. **Interactive UI Drawer:** The frontend renders an interactive accordion (`main.js: addMessage`) populated with the verified source URLs and titles returned directly from the backend JSON payload.

---

## 10. Accuracy & Confidence Heuristics Layer

The deterministic evaluation engine in [accuracy.py](file:///c:/Users/kesha/OneDrive/Desktop/NeuralQuery/accuracy.py) calculates grounded confidence metrics without secondary LLM calls:
1. **Keyword Overlap Score:** Measures the intersection of significant vocabulary (length $\ge 4$ characters) between source evidence and the generated synthesis.
2. **Citation Check Score:** Verifies that source titles or URLs appear in the generated synthesis.
3. **Composite Metric:**
   $$\text{Overall Accuracy} = \text{clamp}(60, 98, (0.6 \times \text{Overlap}) + (0.4 \times \text{Citation}))$$
4. **Confidence Level Mapping:**
   - $\ge 90\% \rightarrow \textbf{High}$
   - $75\% - 89\% \rightarrow \textbf{Moderate}$
   - $< 75\% \rightarrow \textbf{Low}$

---

## 11. Relational Persistence & Authentication

- **Database Engine:** SQLAlchemy ORM with PostgreSQL (production) or SQLite (local testing).
- **Core Entities:**
  - `User`: Email index, bcrypt salted hash (`bcrypt.gensalt(12)`), timestamps.
  - `Conversation`: User foreign key, auto-generated title from initial research prompt.
  - `Message`: Linked to conversation, stores role (`user` vs `assistant`), response content, accuracy score, and sources count.
  - `UploadedFile`: User document attachments (PDF, DOCX, TXT) with secure filename sanitation and MIME validation.
- **Authentication:** Stateless HS256 JWT tokens with 24-hour expiration, passed in the `Authorization: Bearer <token>` header and validated via the `@require_auth` decorator.

---

## 12. Deployment Considerations

| Component | Minimum Requirements | Recommended Production Spec |
|---|---|---|
| **Gemini Provider** | 1 vCPU, 512MB RAM | 1 vCPU, 1GB RAM (Render Free/Starter tier) |
| **NeuralQuery Provider (GPU)** | 4 vCPU, 8GB RAM, 1x NVIDIA T4 (16GB VRAM) | 4 vCPU, 16GB RAM, NVIDIA A10G or T4 GPU |
| **NeuralQuery Provider (CPU)** | 4 vCPU, 8GB System RAM | 8 vCPU, 16GB System RAM (AVX2 support) |
| **Database** | PostgreSQL 14+ | PostgreSQL 16 Managed DB |
| **WSGI Server** | Waitress (included) / Gunicorn | Waitress multi-threaded WSGI |
