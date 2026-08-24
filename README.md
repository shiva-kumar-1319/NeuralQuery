# NeuralQuery

NeuralQuery is a full-stack AI research assistant. A user asks a question in a chat interface; the application gathers current web and optional news results, extracts useful page content, asks Google Gemini to synthesize the evidence, and returns an answer with source links and a transparent, heuristic confidence score.

Built as a portfolio project, it demonstrates an end-to-end product surface: browser UI, authentication, REST APIs, AI and third-party integrations, relational data modelling, document upload, and cloud deployment configuration.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-AI-4285F4)
![JWT](https://img.shields.io/badge/Auth-JWT%20%2B%20bcrypt-orange)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render&logoColor=white)

---

## Architecture

NeuralQuery is architected as an enterprise-grade **Modular Monolith** optimized for low-latency retrieval-augmented generation (RAG), clean separation of concerns, and resilient failover across external services.

The system decouples the client presentation, HTTP routing, security & identity boundary, multi-source retrieval pipeline, document processing engine, LLM inference cascade, deterministic accuracy heuristics, and relational persistence layer.

---

### High-Level System Architecture Topology

The diagram below maps every component, boundary, protocol, and external service in the NeuralQuery ecosystem:

```mermaid
flowchart TB
    %% ==========================================
    %% CLIENT & PRESENTATION TIER
    %% ==========================================
    subgraph Tier1["🖥️ Tier 1: Client & Presentation Layer (Browser SPA)"]
        direction TB
        UI_Templates["Semantic HTML5 Views<br/><code>landing.html</code> | <code>login.html</code> | <code>register.html</code><br/><code>chat.html</code> | <code>admin.html</code>"]
        
        subgraph JS_Engine["Vanilla JavaScript Client Engine (<code>main.js</code>)"]
            AuthStore["Auth State Manager<br/><code>localStorage (JWT + User Profile)</code>"]
            ChatDispatch["Message & Conversation Dispatcher<br/><code>Dynamic fetch & conversation tree</code>"]
            DocUpload["Document Ingestion UI<br/><code>Drag & Drop | File size & MIME validator</code>"]
            MD_Render["Markdown & Citation Renderer<br/><code>marked.js + DOMPurify Sanitization</code>"]
            SourceDrawer["Interactive Source Drawer<br/><code>Accordion view | Confidence score pill</code>"]
        end
        
        UI_Templates --> JS_Engine
    end

    %% ==========================================
    %% INGRESS & EDGE SECURITY TIER
    %% ==========================================
    subgraph Tier2["🛡️ Tier 2: Ingress & Edge Security Gateway"]
        direction TB
        Waitress["Waitress Production WSGI Server<br/><code>Multi-threaded HTTP Worker Pool</code>"]
        CORS_Guard["Flask-CORS Middleware<br/><code>Origin Whitelist & Credentials Support</code>"]
        PayloadGuard["Payload Size Enforcer<br/><code>MAX_CONTENT_LENGTH = 10 MB</code>"]
        ErrBoundary["Global Error Boundaries<br/><code>HTTP 400 | 401 | 404 | 413 | 500 JSON Handlers</code>"]
        
        Waitress --> CORS_Guard --> PayloadGuard --> ErrBoundary
    end

    %% ==========================================
    %% APPLICATION SERVICE LAYER
    %% ==========================================
    subgraph Tier3["⚙️ Tier 3: Core Application & Routing Controller (<code>app.py</code>)"]
        direction TB
        AuthController["Auth Controller<br/><code>/api/auth/register</code><br/><code>/api/auth/login</code>"]
        ResearchController["Research Orchestrator<br/><code>/api/research</code>"]
        ConvController["Conversation Manager<br/><code>/api/conversations</code><br/><code>GET / DELETE /:id</code>"]
        DocController["File Ingestion Controller<br/><code>/api/upload</code><br/><code>/api/analyze-file</code>"]
        AdminController["Admin & Health Controller<br/><code>/api/admin/users</code><br/><code>/api/health</code>"]
    end

    %% ==========================================
    %% SECURITY & AUTH SUBSYSTEM
    %% ==========================================
    subgraph Tier4["🔐 Tier 4: Identity, Cryptography & Security Subsystem (<code>auth.py</code>)"]
        direction TB
        JWT_Engine["JWT Token Engine (<code>HS256</code>)<br/><code>generate_token()</code> | <code>decode_token()</code><br/><code>24-Hour Expiration Window</code>"]
        AuthGuard["<code>@require_auth</code> Decorator<br/><code>Authorization: Bearer <token></code><br/><code>Context Injection (current_user_id)</code>"]
        BcryptEngine["Password Cryptography Engine<br/><code>bcrypt (12 rounds auto-salt)</code><br/><code>Constant-time verify_password()</code>"]
        Sanitizer["Input Sanitization & Defenses<br/><code>sanitize_input() (Null-byte & control char strip)</code><br/><code>secure_filename() + is_safe_filename() (Anti-Traversal)</code>"]
    end

    %% ==========================================
    %% DOCUMENT PROCESSING PIPELINE
    %% ==========================================
    subgraph Tier5["📄 Tier 5: Multi-Format Document Ingestion Subsystem"]
        direction TB
        PDFParser["PDF Parser<br/><code>PyPDF2.PdfReader (Multi-page extraction)</code>"]
        DOCXParser["DOCX Parser<br/><code>python-docx (Paragraph structure parser)</code>"]
        TXTParser["TXT Parser<br/><code>UTF-8 Safe Stream Reader</code>"]
        LocalVault["Secure Local Storage Vault<br/><code>uploads/{user_id}_{timestamp}_{filename}</code>"]
    end

    %% ==========================================
    %% RETRIEVAL & CRAWLING ENGINE
    %% ==========================================
    subgraph Tier6["🌐 Tier 6: Multi-Source Web Retrieval & Scraper (<code>research.py</code>)"]
        direction TB
        SearchRouter["Dual-Provider Search Router<br/><code>Blended Search Aggregator</code>"]
        DDG_Search["DuckDuckGo Search Provider<br/><code>DDGS.text() | 3x Retry + Jitter (2-5s)</code>"]
        News_Search["NewsAPI Provider<br/><code>NewsApiClient (Relevancy sorted)</code>"]
        WebScraper["Polite Content Scraper (<code>fetch_article_content</code>)<br/><code>User-Agent: NeuralQuery/1.0</code><br/><code>1.0s Politeness Delay | 10s Timeout</code>"]
        DOMCleaner["DOM Cleaner & Text Normalizer<br/><code>bs4: Strip script, style, nav, footer, iframe</code><br/><code>Fallback hierarchy: article -> main -> body</code><br/><code>Length truncation: 2,000 chars/source</code>"]
        
        SearchRouter --> DDG_Search
        SearchRouter --> News_Search
        SearchRouter --> WebScraper --> DOMCleaner
    end

    %% ==========================================
    %% AI SYNTHESIS & MODEL CASCADE
    %% ==========================================
    subgraph Tier7["🧠 Tier 7: AI Synthesis & 6-Tier Model Cascade (Google Gemini)"]
        direction TB
        PromptBuilder["Context-Aware Prompt Assembler<br/><code>Structured Multi-Source Prompt Template</code>"]
        ModelCascade["Resilient 6-Tier Model Failover Cascade<br/><code>1. models/gemini-2.0-flash (Primary)</code><br/><code>2. models/gemini-flash-latest</code><br/><code>3. models/gemini-pro-latest</code><br/><code>4. models/gemini-2.0-flash-lite-preview</code><br/><code>5. models/gemini-1.5-flash-latest</code><br/><code>6. models/gemma-3-27b-it (Guaranteed Fallback)</code>"]
        SafetyGuard["Safety & Finish Reason Inspector<br/><code>Candidate finish_reason != 1 interceptor</code>"]
        QuotaRecovery["429 Quota & Error Recovery Handler<br/><code>Graceful fallback + Direct source disclosure</code>"]
        
        PromptBuilder --> ModelCascade --> SafetyGuard --> QuotaRecovery
    end

    %% ==========================================
    %% ACCURACY & CITATION HEURISTIC ENGINE
    %% ==========================================
    subgraph Tier8["📊 Tier 8: Explainable Accuracy Heuristic (<code>accuracy.py</code>)"]
        direction TB
        LexicalOverlap["Lexical Overlap Calculator<br/><code>Word token set intersection (\b\w{4,}\b)</code>"]
        CitationDensity["Citation & URL Verifier<br/><code>Verbatim URL & Title substring occurrences</code>"]
        ScoreFormula["Weighted Bounded Accuracy Formula<br/><code>Score = (Overlap * 0.6) + (Citation * 0.4)</code><br/><code>Bounded range: [60%, 98%]</code>"]
        ConfidenceRank["Confidence Tier Classifier<br/><code>High (>=90%) | Moderate (75-89%) | Low (<75%)</code>"]
        
        LexicalOverlap --> ScoreFormula
        CitationDensity --> ScoreFormula --> ConfidenceRank
    end

    %% ==========================================
    %% PERSISTENCE & DATA LAYER
    %% ==========================================
    subgraph Tier9["🗄️ Tier 9: Persistence & Relational Layer (PostgreSQL 16)"]
        direction TB
        SessionFactory["SQLAlchemy Session Factory<br/><code>get_db() Context-Managed Generator</code><br/><code>Guaranteed connection close & recycling</code>"]
        
        subgraph Tables["PostgreSQL Relational Schema (<code>schema.sql</code>)"]
            T_Users["<code>users</code><br/>PK: id | email (unique) | password_hash"]
            T_Convs["<code>conversations</code><br/>PK: id | FK: user_id | title | updated_at"]
            T_Msgs["<code>messages</code><br/>PK: id | FK: conversation_id | role enum<br/>accuracy_score (0-100 check) | sources_count"]
            T_Files["<code>uploaded_files</code><br/>PK: id | FK: user_id | FK: conversation_id<br/>file_path | file_size | uploaded_at"]
        end
        
        DB_Trigger["PL/pgSQL Trigger & Cascades<br/><code>trigger_update_conversation_timestamp</code><br/><code>ON DELETE CASCADE Referential Integrity</code>"]
        
        SessionFactory --> Tables
        Tables --- DB_Trigger
    end

    %% ==========================================
    %% CROSS-TIER CONNECTIVITY
    %% ==========================================
    Tier1 ==>|HTTPS JSON API + Bearer JWT| Tier2
    Tier2 ==>|Routed WSGI Request| Tier3
    
    Tier3 <-->|Token validation & Password hash| Tier4
    Tier3 -->|File streams & parsing| Tier5
    Tier3 -->|Dispatch research query| Tier6
    Tier6 -->|Sanitized context & sources| Tier7
    Tier7 -->|AI synthesis & sources| Tier8
    Tier3 <-->|Scoped ORM Queries (user_id + id)| Tier9

    %% External Connections
    DDG_Search -.->|HTTP Search Query| Ext_DDG[("🦆 DuckDuckGo Engine")]
    News_Search -.->|REST API Request| Ext_News[("📰 NewsAPI.org")]
    WebScraper -.->|Polite GET Request| Ext_Web[("🌍 Public Web Pages")]
    ModelCascade -.->|REST Transport SDK| Ext_Gemini[("✨ Google Gemini Cloud AI")]
```

---

### Sequence Diagram 1: Real-Time Multi-Source Research Lifecycle

The following sequence details every synchronous step, fallback branch, data transformation, and security boundary during a `POST /api/research` request:

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 User (Browser)
    participant UI as 🖥️ Client UI (main.js)
    participant Edge as 🛡️ Ingress Gateway (Waitress)
    participant App as ⚙️ Flask API (app.py)
    participant Auth as 🔐 Auth Guard (auth.py)
    participant DB as 🗄️ PostgreSQL (models.py)
    participant Retr as 🌐 Research Engine (research.py)
    participant Web as 🌍 Public Web / NewsAPI
    participant AI as 🧠 Google Gemini AI
    participant Acc as 📊 Accuracy Engine (accuracy.py)

    User->>UI: Types query & submits research question
    UI->>Edge: POST /api/research { query, conversation_id }<br/>[Header: Authorization: Bearer <JWT>]
    Edge->>App: Forward sanitized WSGI request
    
    App->>Auth: Validate JWT token signature & expiration
    alt Invalid / Expired Token
        Auth-->>App: Token Error / ExpiredSignatureError
        App-->>UI: HTTP 401 Unauthorized { success: false, error }
        UI-->>User: Redirect to /login
    else Valid Token
        Auth-->>App: Return current_user_id
    end

    App->>App: sanitize_input(query, max_length=1000)
    
    rect rgb(240, 248, 255)
        note over App,DB: Conversation & User Message Persistence
        alt conversation_id provided
            App->>DB: Query Conversation (id=conversation_id, user_id=current_user_id)
        else new conversation
            App->>DB: INSERT INTO conversations (user_id, title=query[:100])
        end
        App->>DB: INSERT INTO messages (conversation_id, role='user', content=query)
        DB-->>App: Persisted User Message ID
    end

    rect rgb(255, 250, 240)
        note over App,Web: Multi-Source Web & News Retrieval
        App->>Retr: perform_research(query)
        par DuckDuckGo Search (3x retry with jitter)
            Retr->>Web: DDGS.text(query, max_results=10)
            Web-->>Retr: Raw Web Hits (url, title, snippet)
        and NewsAPI Lookup (if NEWS_API_KEY set)
            Retr->>Web: newsapi.get_everything(q=query, sort_by='relevancy')
            Web-->>Retr: News Articles (url, title, snippet, published_at)
        end
        Retr->>Retr: Merge & rank top 8 candidate results
        
        loop For each candidate URL (up to 8)
            Retr->>Web: HTTP GET with User-Agent & 1.0s delay
            alt Fetch Successful (HTTP 200)
                Web-->>Retr: HTML Document
                Retr->>Retr: BeautifulSoup DOM cleaning (strip script/style/nav)<br/>Extract main content & truncate to 2000 chars
            else Timeout / Blocked / Error
                Retr->>Retr: Fall back to search snippet text
            end
        end
    end

    rect rgb(245, 255, 245)
        note over Retr,AI: Dynamic Context Assembly & LLM Synthesis
        Retr->>Retr: Assemble structured prompt with source metadata & constraints
        loop 6-Tier Model Cascade (gemini-2.0-flash -> flash-latest -> pro-latest -> 2.0-lite -> 1.5-flash -> gemma-3-27b)
            Retr->>AI: generate_content(prompt, temperature=0.7, max_tokens=2048)
            alt Model Success
                AI-->>Retr: Generated Markdown Synthesis
            else Model Blocked / Quota Error / Rate Limit
                Retr->>Retr: Log failure & failover to next model in cascade
            end
        end
    end

    rect rgb(255, 245, 255)
        note over Retr,Acc: Explainable Accuracy Heuristic Calculation
        Retr->>Acc: calculate_accuracy(valid_sources, ai_response)
        Acc->>Acc: Calculate lexical word set overlap (>= 4 char tokens)
        Acc->>Acc: Calculate verbatim citation & source title density
        Acc->>Acc: Compute bounded overall_accuracy = clamp(60..98, overlap*0.6 + cite*0.4)
        Acc-->>Retr: { overall_accuracy, relevance_score, citation_score, confidence_level }
    end

    Retr-->>App: Return { response, sources, accuracy, success: true }

    rect rgb(240, 248, 255)
        note over App,DB: Assistant Message Persistence & Trigger Execution
        App->>DB: INSERT INTO messages (conversation_id, role='assistant', content, accuracy_score, sources_count)
        DB->>DB: Fire trigger: trigger_update_conversation_timestamp (touch conversations.updated_at)
        DB-->>App: Commit transaction & refresh assistant_message.id
    end

    App-->>Edge: HTTP 200 OK { success: true, response, accuracy, sources, conversation_id, message_id }
    Edge-->>UI: JSON Payload Delivery
    UI->>UI: Parse Markdown (marked.js) + Sanitize HTML (DOMPurify)
    UI->>UI: Render response bubble, interactive citation pills, and accuracy meter
    UI-->>User: Displays structured research answer with expandable source disclosures
```

---

### Sequence Diagram 2: Document Ingestion, Parsing & In-Context File Analysis

The following sequence details the multi-format document processing pipeline (`POST /api/upload` and `POST /api/analyze-file`):

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 User
    participant UI as 🖥️ Client UI (main.js)
    participant API as ⚙️ Flask API (app.py)
    participant Auth as 🔐 Auth Guard (auth.py)
    participant FS as 💾 Local Storage (uploads/)
    participant Extractor as 📄 Text Extractors (PyPDF2 / python-docx)
    participant DB as 🗄️ PostgreSQL (models.py)
    participant AI as 🧠 Google Gemini AI

    User->>UI: Selects or drops file (PDF, DOCX, DOC, TXT)
    UI->>API: POST /api/upload (multipart/form-data: file)<br/>[Header: Authorization: Bearer <JWT>]
    API->>Auth: Verify JWT & extract current_user_id
    API->>API: allowed_file(filename) & is_safe_filename(secure_filename)
    
    alt File Size > 10MB or Disallowed Extension
        API-->>UI: HTTP 400/413 Error (Invalid format or size exceeded)
    else Valid Document
        API->>API: Generate unique name: {user_id}_{timestamp}_{secure_filename}
        API->>FS: Save file to Config.UPLOAD_FOLDER
        
        alt Extension == 'pdf'
            API->>Extractor: PyPDF2.PdfReader -> extract_text() across all pages
        else Extension in ['docx', 'doc']
            API->>Extractor: docx.Document -> parse and join all paragraph texts
        else Extension == 'txt'
            API->>Extractor: UTF-8 safe streaming file.read()
        end
        Extractor-->>API: Extracted raw text buffer
        
        API->>DB: INSERT INTO uploaded_files (user_id, filename, file_path, file_size)
        DB-->>API: Persisted file_id
        API-->>UI: HTTP 200 OK { success: true, file_id, filename, extracted_text: text[:5000] }
        UI-->>User: Displays document attachment pill & enables document QA
    end

    User->>UI: Submits question about uploaded document
    UI->>API: POST /api/analyze-file { file_text, query, conversation_id }
    API->>Auth: Verify JWT & extract current_user_id
    API->>API: Wrap file_text into synthetic source structure
    API->>AI: Analyze document text with user query prompt
    AI-->>API: Generated document analysis synthesis
    API->>DB: Persist user query and assistant document analysis in conversation
    API-->>UI: HTTP 200 OK { success: true, response, accuracy }
    UI-->>User: Renders verified document insights with citation markers
```

---

### Sequence Diagram 3: Authentication, Cryptography & Scoped Session Security

The diagram below illustrates the password hashing, token generation, and multi-tenant authorization workflow:

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 User
    participant UI as 🖥️ Client UI (main.js)
    participant AuthAPI as ⚙️ Auth Controller (app.py)
    participant AuthLib as 🔐 Auth Utility (auth.py)
    participant DB as 🗄️ PostgreSQL (models.py)

    == Registration Flow ==
    User->>UI: Enters full_name, email, password
    UI->>AuthAPI: POST /api/auth/register { email, password, full_name }
    AuthAPI->>AuthLib: sanitize_input(full_name) & validate password length >= 6
    AuthAPI->>DB: SELECT id FROM users WHERE email = :email
    alt Email already exists
        DB-->>AuthAPI: User record found
        AuthAPI-->>UI: HTTP 400 Bad Request { success: false, error: "Email already registered" }
    else New User
        AuthAPI->>AuthLib: bcrypt.gensalt(rounds=12) -> bcrypt.hashpw(password, salt)
        AuthAPI->>DB: INSERT INTO users (email, password_hash, full_name) RETURNING id
        DB-->>AuthAPI: user.id
        AuthAPI->>AuthLib: generate_token(user.id) -> jwt.encode(payload, JWT_SECRET, HS256)
        AuthAPI-->>UI: HTTP 201 Created { success: true, token, user: { id, email, full_name } }
        UI->>UI: localStorage.setItem('token', token)
    end

    == Protected Request & IDOR Prevention Flow ==
    User->>UI: Access conversation history
    UI->>AuthAPI: GET /api/conversations/123 [Header: Authorization: Bearer <token>]
    AuthAPI->>AuthLib: @require_auth -> decode_token(token)
    AuthLib-->>AuthAPI: Extracted current_user_id
    AuthAPI->>DB: SELECT * FROM conversations WHERE id = 123 AND user_id = :current_user_id
    alt Conversation belongs to another user / Not found
        DB-->>AuthAPI: None (No match due to user_id scope)
        AuthAPI-->>UI: HTTP 404 Not Found { success: false, error: "Conversation not found" }
    else Authorized Owner
        DB-->>AuthAPI: Conversation + Joined Messages
        AuthAPI-->>UI: HTTP 200 OK { success: true, conversation: { id, messages: [...] } }
    end
```

---

### Component Responsibility & Design Pattern Matrix

| Subsystem / Module | File Location | Architectural Responsibility | Key Design Patterns & Technical Mechanisms |
| --- | --- | --- | --- |
| **Presentation Tier** | `static/js/main.js`<br/>`templates/*.html`<br/>`static/css/*.css` | Client SPA rendering, reactive state management, asynchronous fetch dispatch, dynamic citation inspection, and responsive glassmorphism UI. | **Model-View Pattern**, Client-side token storage (`localStorage`), Markdown parser with HTML sanitizer (`marked.js` + `DOMPurify`), Event Delegation. |
| **Application Gateway** | `app.py`<br/>`wsgi.py`<br/>`run_production.py` | HTTP composition root, API endpoint routing, request/response validation, global error handling, and WSGI execution. | **Front Controller Pattern**, Dependency Injection (`get_db`), Multi-threaded WSGI worker pool (`Waitress`), Centralized Error Boundaries. |
| **Security & Auth** | `auth.py` | Cryptographic password hashing, stateless JWT issuance/validation, input sanitization, and path traversal defense. | **Interceptor / Decorator Pattern** (`@require_auth`), Salted slow-hashing (`bcrypt` 12 rounds), Defense-in-depth sanitization (`\x00` stripping, `secure_filename`). |
| **Data Access Layer** | `models.py`<br/>`schema.sql` | Relational domain entity definitions, database connection lifecycle, foreign key cascade enforcement, and automated timestamp triggers. | **Data Mapper / ORM Pattern** (`SQLAlchemy`), Unit of Work, Session Lifecycle Generator (`yield db` with `finally: close()`), PL/pgSQL Triggers. |
| **Research Orchestrator** | `research.py` | Multi-source search aggregation, polite web crawling, HTML DOM sanitization, dynamic prompt construction, and LLM synthesis. | **Orchestrator Pattern**, **Circuit Breaker / Exponential Backoff** (DuckDuckGo 3x retry with jitter), Polite Scraper (`User-Agent` + delay), Fallback Cascade. |
| **AI Inference Cascade** | `research.py`<br/>(Gemini Integration) | Fault-tolerant model invocation, safety finish-reason verification, token budgeting, and quota error mitigation. | **Chain of Responsibility / Multi-Tier Failover** (6 model aliases from Gemini 2.0 Flash down to Gemma-3-27B), REST Transport Adapter. |
| **Accuracy Evaluator** | `accuracy.py` | Deterministic evidence verification, lexical overlap measurement, source citation detection, and confidence classification. | **Strategy Pattern**, Normalized Lexical Set Intersection (`\b\w{4,}\b`), Weighted Multi-Factor Scoring Formula, Bounded Heuristic Clamp. |
| **Configuration Manager** | `config.py` | 12-Factor App environment configuration, URL dialect compatibility, credential assertion, and runtime defaults. | **Singleton Configuration Pattern**, Dynamic dialect adaptation (`postgres://` -> `postgresql://`), Strict production credential validation. |

---

### Architectural Design Decisions & Interview Defense Guide

When discussing the architecture of NeuralQuery in technical interviews, the following design rationale highlights engineering maturity and trade-off awareness:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        CORE ARCHITECTURAL DECISIONS & TRADE-OFFS                       │
├────────────────────────────────┬───────────────────────────────────────────────────────┤
│ Architectural Choice           │ Engineering Justification & Interview Talking Points │
├────────────────────────────────┼───────────────────────────────────────────────────────┤
│ 1. Modular Monolith vs.        │ • Keeps operational complexity low and zero-overhead. │
│    Microservices               │ • Clear module seams (auth, research, models, config) │
│                                │   allow seamless extraction into Celery workers later.│
├────────────────────────────────┼───────────────────────────────────────────────────────┤
│ 2. Deterministic Heuristics    │ • Zero added LLM latency (instant execution, O(N)).   │
│    vs. LLM-as-a-Judge          │ • Zero API cost and immunity to evaluation hallucination.│
│                                │ • Provides transparent, explainable lexical metrics.  │
├────────────────────────────────┼───────────────────────────────────────────────────────┤
│ 3. 6-Tier LLM Failover Cascade │ • Ensures high availability despite model deprecations│
│                                │   or regional quota throttles (HTTP 429).             │
│                                │ • Gracefully degrades to raw sources if all AI fails. │
├────────────────────────────────┼───────────────────────────────────────────────────────┤
│ 4. Relational Ownership &      │ • IDOR defense: Every query filters by user_id.       │
│    Cascade Integrity           │ • ON DELETE CASCADE prevents orphaned records.        │
│                                │ • PL/pgSQL triggers maintain updated_at timestamps.   │
├────────────────────────────────┼───────────────────────────────────────────────────────┤
│ 5. Scraper DOM Decomposition   │ • Removes noisy script/style/nav boilerplate.         │
│    & Semantic Hierarchy        │ • Content selectors target <article> and <main> first.│
│                                │ • Respects crawl politeness with custom User-Agent.   │
└────────────────────────────────┴───────────────────────────────────────────────────────┘
```

#### 1. Why a Modular Monolith over Microservices?
- **Decision**: Centralized all core workflows (Auth, RAG, File Ingestion, Data Access) within a modular Flask application instead of prematurely splitting into distributed microservices.
- **Trade-off & Rationale**: Microservices introduce network overhead, distributed transaction complexity, and deployment friction. NeuralQuery enforces strict modular boundaries (`auth.py`, `research.py`, `models.py`) so that CPU-bound document parsing or network-bound web scraping can be extracted into asynchronous background task queues (e.g., Celery + Redis) without rewriting core business logic.

#### 2. Why a Lexical Heuristic for Accuracy rather than an LLM-as-a-Judge?
- **Decision**: Computed evidence overlap and citation density using tokenized set intersection (`\b\w{4,}\b`) and substring matches instead of dispatching a secondary LLM call.
- **Trade-off & Rationale**: Running an "LLM-as-a-Judge" doubles inference latency (adding 2–5 seconds per turn), incurs extra API costs, and is susceptible to its own hallucinations. A deterministic heuristic executes in `<2ms`, is fully explainable, transparently penalizes uncited generation, and provides a dependable lower-bound confidence metric.

#### 3. How does the system achieve Resilient Fault Tolerance?
- **Search Failover**: DuckDuckGo search queries are wrapped in a 3-attempt retry loop with randomized jitter (`2.0s + uniform(0, 3.0s)`). If search fails entirely, the system gracefully falls back to internal model knowledge rather than throwing a 500 error.
- **Scraping Isolation**: Each page fetch has a strict 10-second timeout and per-source error handlers. If an external website blocks the crawler or times out, the search snippet is preserved, ensuring partial evidence is never lost.
- **6-Tier Model Cascade**: If `gemini-2.0-flash` encounters a safety filter (`finish_reason != 1`) or rate limit (`429 Quota Exceeded`), the orchestrator sequentially cascades through 5 fallback model identifiers (`gemini-flash-latest`, `gemini-pro-latest`, `gemini-2.0-flash-lite-preview`, `gemini-1.5-flash-latest`, `gemma-3-27b-it`).
- **Quota Recovery Mode**: If all AI models are temporarily throttled, the application returns a structured diagnostic accompanied by all extracted web sources, ensuring the user still receives actionable research findings.

#### 4. How is Security & Multi-Tenant Data Isolation Enforced?
- **Cryptographic Password Storage**: Passwords are never stored in plaintext; they are hashed with `bcrypt` using 12 salt rounds.
- **Stateless Bearer JWT**: Protected routes validate signed HMAC-SHA256 (`HS256`) tokens with a 24-hour expiration window.
- **Insecure Direct Object Reference (IDOR) Defense**: Database lookups for conversations and files enforce compound ownership checks (`Conversation.id == conversation_id AND Conversation.user_id == current_user_id`). Users cannot view, modify, or delete another user's conversations by guessing numerical IDs.
- **Path Traversal Protection**: Uploaded files pass through `werkzeug.secure_filename()` and custom `is_safe_filename()` checks, preventing directory traversal attacks (`../../`). Files are stored under a prefixed namespace `{user_id}_{timestamp}_{filename}`.
- **Input Sanitization**: All user queries pass through `sanitize_input()`, which strips dangerous null bytes (`\x00`), removes unprintable control characters, and enforces strict character limits.

---

### Distributed Scaling Roadmap (Production Evolution)

For enterprise scale (>100,000 active users), the modular monolith transitions cleanly into an event-driven architecture:

```mermaid
flowchart LR
    Browser["🖥️ Browser Client"] -->|HTTPS / WebSocket| API_Gateway["🛡️ Ingress API Gateway (Nginx / Cloudflare)"]
    API_Gateway --> WebNodes["⚙️ Flask API Web Cluster (Gunicorn / Waitress)"]
    
    WebNodes -->|Read / Write Auth & Metadata| PG_Cluster[("🗄️ PostgreSQL (Primary + Read Replicas)")]
    WebNodes -->|Push Research Job| TaskQueue[("📨 Redis / RabbitMQ Task Queue")]
    
    TaskQueue --> Workers["👷 Celery Research Worker Pool"]
    Workers --> SearchCluster["🔍 Distributed Scraping & Search Cluster"]
    Workers --> LLM_Gateway["🧠 LLM Inference Gateway (Gemini + Rate Limiter)"]
    Workers --> ObjectStore[("☁️ AWS S3 / Cloud Storage (Encrypted Uploads)")]
    
    Workers -->|Publish Token Stream| PubSub[("⚡ Redis Pub/Sub Stream Engine")]
    PubSub -->|SSE / WebSocket Stream| Browser
```

---


---

## What it does

- Registers and authenticates users with bcrypt password hashes and JWT bearer tokens.
- Runs evidence-oriented research over DuckDuckGo and, when configured, NewsAPI.
- Fetches and cleans the most relevant result pages before Gemini generates a concise Markdown answer.
- Persists chat history, message-level source counts, and an accuracy heuristic in PostgreSQL.
- Accepts PDF, DOCX, DOC, and TXT uploads and extracts text from supported formats.
- Provides a responsive, framework-free chat UI with conversation history and source disclosure.

## Technology choices

| Concern | Technology | Why it is here |
| --- | --- | --- |
| Web application | Flask + Flask-CORS | Small, explicit Python HTTP layer for the UI and JSON API. |
| Browser client | HTML, CSS, vanilla JavaScript | Keeps the interface lightweight and makes request/auth behaviour easy to inspect. |
| Persistence | PostgreSQL + SQLAlchemy | Relational ownership model for users, conversations, messages, and file metadata. |
| Authentication | PyJWT + bcrypt | Stateless bearer authentication and slow password hashing. |
| Research retrieval | DuckDuckGo Search, NewsAPI, Requests, BeautifulSoup | Blends general web results with optional news coverage and extracts readable content. |
| AI synthesis | Google Gemini | Turns retrieved evidence into a structured, source-aware research answer. |
| Document processing | PyPDF2 + python-docx | Extracts text from user-provided documents for follow-up analysis. |
| Production serving | Waitress + Render blueprint | Provides a Windows-friendly production server and repeatable Render deployment settings. |

## Quick start

### Prerequisites

- Python 3.11 or newer
- PostgreSQL 12 or newer
- A Google Gemini API key
- Optional: a NewsAPI key for news-specific results

### Install and configure

```bash
git clone https://github.com/shiva-kumar-1319/NeuralQuery.git
cd NeuralQuery

python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env`, then supply your own values. At minimum, configure `DATABASE_URL`, `GEMINI_API_KEY`, and a strong `JWT_SECRET`.

```env
DATABASE_URL=postgresql://username:password@localhost:5432/neuralquery
GEMINI_API_KEY=your_key_here
JWT_SECRET=replace_with_a_long_random_secret
FLASK_ENV=development
FLASK_DEBUG=true
```

Create the database and initialise its schema using either approach below.

```bash
createdb neuralquery
psql -U postgres -d neuralquery -f schema.sql

# Alternative: create tables from SQLAlchemy models
python models.py
```

Start the application and open <http://localhost:5000>.

```bash
python app.py
```

## Project layout

```text
NeuralQuery/
├── app.py               # Flask routes: pages, API, uploads, error responses
├── auth.py              # JWT generation/validation and request guards
├── config.py            # Environment-backed application configuration
├── models.py            # SQLAlchemy entities and session factory
├── research.py          # Search, article extraction, Gemini synthesis pipeline
├── accuracy.py          # Evidence/response overlap scoring heuristic
├── schema.sql           # PostgreSQL DDL, indexes, and conversation timestamp trigger
├── static/              # CSS, JavaScript, and image assets served to the browser
├── templates/           # Landing, authentication, chat, and admin pages
├── uploads/             # Runtime document storage (gitignored)
├── run_production.py    # Waitress application entry point
└── render.yaml          # Render web service and PostgreSQL provisioning blueprint
```

## Core user journey

1. The browser registers or logs in and stores the issued JWT in `localStorage`.
2. The chat page sends the query with `Authorization: Bearer <token>`.
3. Flask validates the token, scopes the request to that user, creates or reuses a conversation, and saves the user message.
4. The research pipeline searches, extracts content from up to eight results, and sends the assembled context to Gemini.
5. NeuralQuery calculates evidence-related metrics, saves the assistant message, and returns the answer, metrics, and source links.
6. The client renders the answer and lets the user inspect sources or reload the saved conversation later.

## Features and boundaries

| Feature | Current behaviour | Important boundary |
| --- | --- | --- |
| Research | Uses live DuckDuckGo results; NewsAPI is included only when `NEWS_API_KEY` is configured. | Third-party search and model availability can affect response time and output. |
| Source extraction | Removes common non-content HTML elements and limits fetched text to 2,000 characters per page. | Extraction is best-effort; pages may block, time out, or use layouts that are hard to parse. |
| AI response | Gemini is tried with several configured fallback model identifiers. | A response is generated from supplied context where available; it should still be reviewed for important decisions. |
| Accuracy score | Measures lexical source overlap and citation signals, then reports a bounded heuristic score. | It is an evidence-use indicator, not an independent guarantee of factual correctness. |
| File uploads | Stores a uniquely named file locally and extracts PDF, DOCX, or TXT text. | Files are limited by `MAX_UPLOAD_SIZE` (10 MB by default); legacy `.doc` is accepted but has no dedicated extractor. |

## Data model

PostgreSQL 16 is the system of record. The schema enforces relational integrity with foreign keys, cascaded deletions, check constraints, custom enum types, and an automated PL/pgSQL timestamp trigger.

```mermaid
erDiagram
    USERS ||--o{ CONVERSATIONS : "owns (1:N)"
    USERS ||--o{ UPLOADED_FILES : "uploads (1:N)"
    CONVERSATIONS ||--o{ MESSAGES : "contains (1:N)"
    CONVERSATIONS o|--o{ UPLOADED_FILES : "associates (0:N)"

    USERS {
        int id PK "SERIAL PRIMARY KEY"
        varchar email UK "VARCHAR(255) UNIQUE INDEX"
        varchar password_hash "VARCHAR(255) NOT NULL (bcrypt)"
        varchar full_name "VARCHAR(255)"
        timestamp created_at "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }

    CONVERSATIONS {
        int id PK "SERIAL PRIMARY KEY"
        int user_id FK "INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE"
        varchar title "VARCHAR(255)"
        timestamp created_at "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        timestamp updated_at "TIMESTAMP DEFAULT CURRENT_TIMESTAMP (Trigger Updated)"
    }

    MESSAGES {
        int id PK "SERIAL PRIMARY KEY"
        int conversation_id FK "INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE"
        enum role "message_role ENUM ('user', 'assistant')"
        text content "TEXT NOT NULL"
        int accuracy_score "INTEGER CHECK (0 <= score <= 100)"
        int sources_count "INTEGER"
        timestamp timestamp "TIMESTAMP DEFAULT CURRENT_TIMESTAMP INDEX"
    }

    UPLOADED_FILES {
        int id PK "SERIAL PRIMARY KEY"
        int user_id FK "INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE"
        int conversation_id FK "INTEGER REFERENCES conversations(id) ON DELETE CASCADE"
        varchar filename "VARCHAR(255) NOT NULL"
        varchar file_path "VARCHAR(500) NOT NULL"
        int file_size "INTEGER"
        timestamp uploaded_at "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }
```

| Entity | Purpose | Notable constraints, indexes, and triggers |
| --- | --- | --- |
| `users` | Identity, authentication, and password-hash repository. | Primary key `id`, unique indexed `email` (`idx_users_email`), 12-round bcrypt hash. |
| `conversations` | Grouping entity for a continuous research chat thread. | Foreign key `user_id` with `ON DELETE CASCADE`. Indexed by owner (`idx_conversations_user_id`) and recency (`idx_conversations_updated_at DESC`). |
| `messages` | Immutable turn-by-turn conversation messages. | Foreign key `conversation_id` with `ON DELETE CASCADE`. Custom Postgres enum `message_role` (`'user'`, `'assistant'`). Check constraint on `accuracy_score` (0–100). Indexed on `conversation_id` and `timestamp`. |
| `uploaded_files` | Metadata and storage pointers for user documents. | Foreign keys to `users` and `conversations` with `ON DELETE CASCADE`. Indexed on `user_id` and `conversation_id`. |
| `trigger_update_conversation_timestamp` | Database automation trigger on `messages`. | PL/pgSQL function executing `AFTER INSERT ON messages` to automatically refresh parent `conversations.updated_at`. |

## API reference

All responses use JSON. Endpoints marked **Auth** require `Authorization: Bearer <token>`.

| Method | Endpoint | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/auth/register` | No | Create an account and return a JWT. |
| `POST` | `/api/auth/login` | No | Verify credentials and return a JWT. |
| `POST` | `/api/research` | Yes | Persist a user query, run research, and persist/return the AI response. |
| `GET` | `/api/conversations` | Yes | List only the requesting user’s conversations. |
| `GET` | `/api/conversations/:id` | Yes | Read one owned conversation and its messages. |
| `DELETE` | `/api/conversations/:id` | Yes | Delete one owned conversation and its dependent messages/uploads. |
| `POST` | `/api/upload` | Yes | Validate, store, and extract text from a document. |
| `POST` | `/api/analyze-file` | Yes | Send supplied extracted text and a question to the Gemini analysis path. |
| `GET` | `/api/admin/users` | Yes | Returns users with chat counts; see the access-control note below. |
| `GET` | `/api/health` | No | Lightweight liveness response for deployment checks. |

Example research request:

```bash
curl -X POST http://localhost:5000/api/research \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query":"How is retrieval-augmented generation used in enterprise search?"}'
```

## Security and operational notes

### Controls implemented today

- Passwords are hashed with bcrypt using 12 rounds; plaintext passwords are not persisted.
- Protected routes use signed, expiring JWTs (`HS256`, 24-hour lifetime).
- Conversation lookups and deletes include both `conversation_id` and the authenticated `user_id`, preventing cross-user access through guessed IDs.
- SQLAlchemy ORM queries and database constraints reduce SQL injection risk.
- Uploads enforce extension allowlisting, path-safety checks, filename normalisation, unique names, and an application-wide size limit.
- Inputs are trimmed, null bytes removed, and capped before they enter the research or file-analysis flow.
- CORS origins and secrets are environment-configured rather than hard-coded in application logic.

### Production hardening backlog

These are deliberate interview talking points: the project contains the foundations, but a public deployment should add the controls below.

- Add role-based access control before exposing `/api/admin/users`; it currently accepts any authenticated user.
- Add server-side rate limits, request tracing, structured logs, and monitoring around external providers.
- Use a virus scanner and object storage with private, expiring access for uploads instead of local disk.
- Protect against SSRF and strengthen URL/content policy before fetching arbitrary search result URLs at larger scale.
- Use database migrations, connection pooling, background workers, and a secret manager as the service grows.
- Keep API keys out of Git history, rotate any credential that was ever committed, and use deployment environment variables instead.

## Deployment

`render.yaml` provisions a Render web service and PostgreSQL database. The service installs from `requirements.txt`, starts `run_production.py`, and serves Flask through Waitress. `wsgi.py` imports the Flask application and runs `init_db()` before serving, which creates missing tables.

Set the following environment variables in the deployment platform:

| Variable | Required | Notes |
| --- | --- | --- |
| `DATABASE_URL` | Yes | Render can inject the PostgreSQL connection string. Both `postgres://` and `postgresql://` are accepted. |
| `GEMINI_API_KEY` | Yes | Required for AI synthesis. |
| `JWT_SECRET` | Yes | Use a long, unique random secret in production. |
| `NEWS_API_KEY` | No | Enables the optional news retrieval path. |
| `CORS_ORIGINS` | Yes for a separate frontend | Comma-separated allowed browser origins. |
| `UPLOAD_FOLDER` | No | Defaults to `./uploads`; use durable storage for production uploads. |

Before releasing, set `FLASK_ENV=production`, `FLASK_DEBUG=false`, restrict CORS to the real frontend origin, rotate credentials, and verify database backups and health checks.

## License

This repository is provided as a portfolio and educational project. Add an explicit license file before distributing it for reuse.
