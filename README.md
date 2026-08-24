# NeuralQuery

NeuralQuery is a full-stack AI research assistant. A user asks a question in a chat interface; the application gathers current web and optional news results, extracts useful page content, asks Google Gemini to synthesize the evidence, and returns an answer with source links and a transparent, heuristic confidence score.

Built as a portfolio project, it demonstrates an end-to-end product surface: browser UI, authentication, REST APIs, AI and third-party integrations, relational data modelling, document upload, and cloud deployment configuration.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-AI-4285F4)

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

## Architecture

NeuralQuery is intentionally deployed as a **modular monolith**: one Flask application owns the HTTP interface, application coordination, and persistence boundary, while focused modules isolate authentication, research orchestration, configuration, and data access. This is a good fit for an early product: it keeps deployment simple while preserving seams that can be extracted later if demand requires it.

```mermaid
flowchart LR
    U[User] --> B[Browser client\nHTML + CSS + vanilla JS]
    B -->|Pages, static assets, JSON API| F[Flask application\napp.py]

    F --> A[Authentication module\nauth.py]
    A -->|JWT validation| F
    F --> M[SQLAlchemy models\nmodels.py]
    M --> P[(PostgreSQL)]

    F --> R[Research orchestrator\nresearch.py]
    R --> D[DuckDuckGo Search]
    R --> N[NewsAPI\noptional]
    R --> W[Article fetch + cleanup\nRequests + BeautifulSoup]
    W --> X[Public web pages]
    R --> G[Google Gemini]
    R --> Q[Accuracy heuristic\naccuracy.py]

    F --> L[Local upload storage]
    F --> T[Text extractors\nPyPDF2 / python-docx]
```

### Component responsibilities

| Component | Responsibility | Key implementation detail |
| --- | --- | --- |
| `static/` + `templates/` | Presents the landing, auth, chat, and admin experiences. | `main.js` attaches the JWT to authenticated API calls and keeps the active conversation in browser state. |
| `app.py` | HTTP composition root and application service layer. | Owns route handlers, validation, per-user resource checks, file workflow, and response shaping. |
| `auth.py` | Keeps identity concerns out of route implementations. | Decorator validates `Authorization: Bearer <JWT>` and injects `current_user_id` into protected handlers. |
| `models.py` | Defines the domain entities and database session factory. | SQLAlchemy relationships and database foreign keys express ownership and cascade rules. |
| `research.py` | Encapsulates external research and generation workflow. | Combines search results, retrieves readable content, builds the prompt, and retries Gemini across model identifiers. |
| `accuracy.py` | Produces explainable response metadata. | Scores source-to-answer word overlap and citation presence; it does not claim to fact-check the model. |
| `config.py` | Centralises environment-derived settings. | Handles production database URL compatibility and validates required secrets/API keys. |

### Research request sequence

The diagram below follows the implementation of `POST /api/research` from browser input to the persisted response.

```mermaid
sequenceDiagram
    actor User
    participant UI as Chat UI
    participant API as Flask API
    participant Auth as JWT guard
    participant DB as PostgreSQL
    participant Search as Search providers
    participant Web as Result pages
    participant AI as Gemini

    User->>UI: Submit research question
    UI->>API: POST /api/research + Bearer token
    API->>Auth: Validate and decode JWT
    Auth-->>API: current_user_id
    API->>DB: Find/create owned conversation
    API->>DB: Save user message
    API->>Search: DuckDuckGo + optional NewsAPI lookup
    Search-->>API: Candidate URLs, titles, snippets
    loop Up to 8 results
        API->>Web: Fetch page with timeout and user agent
        Web-->>API: HTML or failure
        API->>API: Extract main readable text / fall back to snippet
    end
    API->>AI: Query + assembled source context
    AI-->>API: Markdown research synthesis
    API->>API: Calculate source-use heuristic
    API->>DB: Save assistant message + metrics
    API-->>UI: Answer, sources, metrics, conversation ID
    UI-->>User: Render answer and expandable source list
```

### Failure handling and graceful degradation

The research pipeline is deliberately resilient at its external boundaries:

- DuckDuckGo searches retry up to three times with jitter; a failed search returns an empty result set rather than breaking the request.
- News retrieval is skipped cleanly when `NEWS_API_KEY` is not configured.
- Individual article failures and timeouts retain the search snippet when available, so one unavailable site does not discard the rest of the evidence.
- Gemini tries multiple configured model identifiers. If generation still fails, the UI receives a human-readable diagnostic and, when possible, a list of sources that were found.
- Flask returns consistent JSON error responses for invalid input, unauthorized access, missing resources, oversized files, and unexpected server errors.

### Scaling path

The current synchronous request path is appropriate for a portfolio-scale deployment. A production evolution can keep the existing interfaces while moving the slowest work behind queues:

```text
Current:  Browser -> Flask request -> retrieval + Gemini -> PostgreSQL -> response
Future:   Browser -> Flask API -> job queue -> research worker -> PostgreSQL
                                \-> status/stream endpoint -> Browser
```

That change would protect web workers from long external calls, enable retries and rate controls, and make it easier to add streaming responses or a durable object store for uploads. The existing separation of `app.py`, `research.py`, and `models.py` provides the natural extraction points.
