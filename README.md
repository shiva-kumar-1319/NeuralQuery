# NeuralQuery

NeuralQuery is an end-to-end full-stack AI research assistant that pairs real-time multi-source web and news retrieval with grounded LLM synthesis. Built with Flask, PostgreSQL, and a dual-engine AI provider layer, it supports both cloud-hosted inference via Google Gemini and a custom fine-tuned Qwen2.5-1.5B LoRA adapter specialized in evidence-grounded research, factual consistency, and unsupported claim refusal.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?logo=pytorch&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-PEFT%20LoRA-FFD21E?logo=huggingface&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Waitress](https://img.shields.io/badge/WSGI-Waitress-blue)

---

## Overview

Traditional generative search engines often hallucinate facts, invent nonexistent URLs, or speculate when retrieved search results lack sufficient evidence. NeuralQuery addresses these challenges by combining:

1. **Multi-Source Evidence Gathering:** Automated retrieval through DuckDuckGo and NewsAPI with polite DOM extraction and text cleaning.
2. **Pluggable LLM Provider Architecture:** A clean abstraction layer switching seamlessly between Google Gemini (zero-setup cloud inference) and NeuralQuery's custom fine-tuned local model.
3. **Evidence-Grounded Synthesis:** A fine-tuned LoRA adapter based on Qwen2.5-1.5B trained to answer strictly from retrieved snippets, highlight contradictions, and reject unsupported claims.
4. **Citation & Accuracy Heuristics:** Preserves verified source metadata for transparent frontend citation drawers and scores response accuracy via deterministic keyword and citation overlap algorithms.
5. **Production Web Application:** Complete with JWT authentication, password hashing, conversation trees, document upload parsing (PDF/DOCX/TXT), and deployment manifests.

---

## Key Features

- **Live Web & News Retrieval:** Queries DuckDuckGo for organic search and NewsAPI for breaking news coverage.
- **Deep Web Page Content Extraction:** HTML parsing via BeautifulSoup extracting core article text while filtering boilerplate, navigation, and ads.
- **Configurable Model Provider:** Switch effortlessly between `MODEL_PROVIDER=gemini` and `MODEL_PROVIDER=neuralquery` via environment configuration.
- **Custom Fine-Tuned LLM (Qwen2.5-1.5B LoRA):** Specialized PEFT adapter trained on Grounded-RAG tasks to prioritize supported evidence, cite sources, and refuse ungrounded claims.
- **Citation Preservation:** Retains verified URLs and titles from source to UI; the model never invents links.
- **Deterministic Accuracy Scoring:** Calculates lexical overlap and citation density to provide a transparent confidence metric for every answer.
- **JWT Authentication & Relational Persistence:** Robust user management, bcrypt salted hashes, conversation history, and message logging using SQLAlchemy and PostgreSQL.
- **Document Ingestion:** Drag-and-drop document upload parsing for `.pdf`, `.docx`, and `.txt` files.

---

## Architecture

NeuralQuery is architected as a modular monolith with clean separation between client presentation, HTTP routing, multi-source retrieval, LLM provider abstraction, heuristic evaluation, and relational persistence.

```mermaid
flowchart TB
    subgraph Client["🖥️ Tier 1: Client & Presentation Layer"]
        UI["Browser UI\n(landing.html, chat.html, admin.html)"]
        Engine["Vanilla JS Engine (static/js/main.js)\nJWT Store | Markdown Renderer | Source Drawer"]
        UI --- Engine
    end

    subgraph Edge["🛡️ Tier 2: Ingress & Security Gateway"]
        Waitress["Waitress Production WSGI Server"]
        CORS["Flask-CORS Middleware"]
        AuthMid["JWT Auth Route Guard (auth.py)"]
        Waitress --> CORS --> AuthMid
    end

    subgraph Service["⚙️ Tier 3: Research Orchestration & Retrieval Engine (research.py)"]
        Orchestrator["Research Orchestrator\n(perform_research)"]
        DDG["DuckDuckGo Search\n(duckduckgo_search)"]
        News["NewsAPI Engine\n(newsapi-python)"]
        Extractor["Polite DOM Extractor\n(requests + BeautifulSoup)"]

        Orchestrator --> DDG & News
        DDG & News --> Extractor
        Extractor -->|Extracted Evidence + Source Metadata| Orchestrator
    end

    subgraph Providers["🧠 Tier 4: Pluggable LLM Provider Layer (llm_providers.py)"]
        Factory["Provider Factory: get_llm_provider()"]
        Gemini["GeminiProvider\n(gemini-2.0-flash / fallback cascade)"]
        NeuralQueryProv["NeuralQueryProvider\n(Qwen2.5-1.5B-Instruct + LoRA Adapter)"]

        Factory -->|MODEL_PROVIDER=gemini| Gemini
        Factory -->|MODEL_PROVIDER=neuralquery| NeuralQueryProv
    end

    subgraph Heuristics["📊 Tier 5: Accuracy & Confidence Heuristics (accuracy.py)"]
        AccuracyCalc["Deterministic Accuracy Evaluator\nKeyword Overlap | Citation Verification | Confidence Level"]
    end

    subgraph Persistence["🗄️ Tier 6: Relational Persistence Layer (models.py)"]
        ORM["SQLAlchemy ORM"]
        DB[(PostgreSQL / SQLite Database\nUsers, Conversations, Messages, Uploads)]
        ORM --- DB
    end

    Engine -->|POST /api/research| Waitress
    AuthMid --> Orchestrator
    Orchestrator --> Factory
    Gemini & NeuralQueryProv -->|Synthesized Analysis| AccuracyCalc
    AccuracyCalc -->|Accuracy Score & Metrics| Orchestrator
    Orchestrator --> ORM
    Orchestrator -->|Grounded Response + Verified Sources + Score| Engine
```

For complete architectural specifications and sequence diagrams, see [docs/architecture.md](docs/architecture.md).

---

## Research Pipeline

Every research interaction follows a deterministic six-stage lifecycle:

```mermaid
flowchart LR
    Q["1. User Query"] --> S["2. Multi-Source Search\n(DDG + NewsAPI)"]
    S --> E["3. HTML Extraction\n(DOM Cleaning)"]
    E --> P["4. Prompt Assembly\n(Query + Evidence)"]
    P --> M["5. LLM Synthesis\n(Gemini or Qwen LoRA)"]
    M --> A["6. Accuracy & Sources\n(Verification)"]
    A --> R["7. Grounded Answer\n+ Citations"]
```

1. **User Query:** User inputs a research question via the chat UI or REST API.
2. **Search Retrieval:** Concurrently queries DuckDuckGo (organic web) and NewsAPI (topical news).
3. **Content Extraction:** Fetches top matching URLs, strips scripts/navigation, and extracts body text.
4. **Prompt Assembly:** Formats evidence into clearly demarcated `[Source X]` blocks separating question from facts.
5. **LLM Synthesis:** The configured provider generates a research response strictly referencing the evidence.
6. **Accuracy Calculation:** Evaluates token overlap and citation presence, producing an overall accuracy score (60–98%) and confidence rating.
7. **Response Delivery:** Returns structured JSON with response markdown, source metadata, and confidence scores.

---

## Custom LLM (NeuralQuery Qwen LoRA)

> [!IMPORTANT]
> **Foundation Disclosure:**
> The model was fine-tuned from an existing foundation model (`Qwen/Qwen2.5-1.5B-Instruct`); it was **NOT** trained from scratch. Parameter-Efficient Fine-Tuning (PEFT) with LoRA was used to adapt the base instruction model specifically for research grounding and refusal of ungrounded queries.

### Model Specification

| Property | Value |
|---|---|
| **Base Model** | `Qwen/Qwen2.5-1.5B-Instruct` |
| **Adapter Type** | PEFT LoRA (Low-Rank Adaptation) |
| **Task Type** | `CAUSAL_LM` |
| **LoRA Rank ($r$)** | 16 |
| **LoRA Alpha ($\alpha$)** | 32 |
| **LoRA Dropout** | 0.05 |
| **Target Modules** | `q_proj`, `k_proj`, `v_proj`, `o_proj` |
| **Trainable Parameters** | ~9.4M (0.6% of base model) |
| **Adapter Storage Size** | ~30 MB (`adapter_model.safetensors`) |

### Why Add a Custom Model?

General foundation models are prone to hallucinating facts when queried about niche topics absent from their pre-training memory. When deployed behind web retrieval, base models often ignore the provided snippets or fail to state when the search failed to answer the question. 

The NeuralQuery LoRA adapter enforces strict adherence to retrieved evidence:
- **Prioritizes supported evidence:** Only draws conclusions backed by retrieved text.
- **Identifies conflicting sources:** Points out disagreements across sources instead of merging them arbitrarily.
- **Filters irrelevant noise:** Ignores boilerplate and advertising content.
- **Refuses unsupported claims:** Explicitly states when the evidence lacks the required facts rather than guessing.
- **Communicates uncertainty:** Expresses calibrated hedging for preliminary or partial evidence.

---

## Training Pipeline

The adapter was fine-tuned using Hugging Face Transformers, PEFT, and BitsAndBytes on a Google Colab NVIDIA T4 GPU (16GB VRAM).

```mermaid
flowchart TD
    D["Grounded-RAG Dataset\n(Supported, Unsupported, Conflicting, Noise)"] --> F["Formatting & Chat Template\n(Qwen2.5 Format)"]
    F --> B["Base Model Loading\n(Qwen2.5-1.5B-Instruct in 4-bit NF4)"]
    B --> L["LoRA Adapter Injection\n(r=16, alpha=32 on attention projections)"]
    L --> T["Supervised Fine-Tuning\n(SFTTrainer, Cosine LR 2e-4, 3 Epochs)"]
    T --> E["Grounding Evaluation Benchmark"]
    E --> A["Production LoRA Artifact\n(model/neuralquery-production-adapter/)"]
```

### Dataset Formulation

The training data was balanced across five functional scenarios:
1. **Direct Supported Inferences (40%):** Synthesis with clear source attribution (`[Source 1]`, `[Source 2]`).
2. **Unsupported Claim Rejection (20%):** Explicit refusals stating that the evidence does not contain the answer.
3. **Conflicting Evidence Resolution (15%):** Contrasting diverging reports without fabricating consensus.
4. **Irrelevant Noise Filtering (15%):** Discarding off-topic web snippets.
5. **Incomplete Evidence & Uncertainty (10%):** Calibrated qualifiers for preliminary facts.

For full dataset samples and training reproduction scripts, see [training/README.md](training/README.md).

---

## Evaluation

The model was evaluated against 100 benchmark scenarios testing common RAG failure modes. The fine-tuned adapter demonstrated marked improvements in grounding discipline, alongside measurable constraints:

| Evaluation Dimension | Base Qwen2.5-1.5B | NeuralQuery LoRA Adapter | Observed Impact |
|---|:---:|:---:|---|
| **Unsupported Claim Rejection** | 38% | **89%** | Substantial reduction in hallucinated answers when evidence is missing |
| **Hallucination on Negative Controls** | 62% | **11%** | Reliability in acknowledging when data is unavailable |
| **Conflicting Evidence Detection** | 44% | **83%** | Accurately identifies disagreements between competing sources |
| **Citation Attribution Faithfulness** | 56% | **92%** | Cites sources consistently without inventing URLs |
| **Irrelevant Noise Filtering** | 71% | **86%** | Ignores boilerplate and off-topic web snippets |

### Honest Limitations

- **Parameter Size (1.5B):** While compact and fast, 1.5B parameters limits deep multi-step mathematical reasoning compared to 70B+ models or Gemini 2.0 Flash.
- **Retrieval Dependency:** The model treats retrieved text as source truth. If search results are inaccurate or misleading, the synthesis will reflect those flaws.
- **Not Universally Superior:** The custom adapter was trained for evidence synthesis; it is not superior to the base model on open-ended general knowledge or creative writing.

For complete evaluation methodologies and benchmark test cases, see [evaluation/README.md](evaluation/README.md).

---

## Model Provider Configuration

NeuralQuery supports two primary runtime model providers:

```bash
# Option 1: Cloud-Hosted Inference (Default)
MODEL_PROVIDER=gemini

# Option 2: Local Custom Model (Qwen2.5-1.5B + LoRA Adapter)
MODEL_PROVIDER=neuralquery
```

| Feature | `MODEL_PROVIDER=gemini` | `MODEL_PROVIDER=neuralquery` |
|---|---|---|
| **Inference Engine** | Google Gemini API | Local PyTorch + Hugging Face Transformers |
| **Hardware Requirement** | Any machine (Cloud API) | GPU recommended (NVIDIA T4 or better) |
| **Base Model** | Gemini 2.0 Flash (with cascade) | Qwen/Qwen2.5-1.5B-Instruct |
| **Adapter** | N/A | Local PEFT LoRA adapter (~30MB) |
| **Offline / Local** | Requires Internet connection | Runs locally once weights are downloaded |
| **Setup Cost** | Gemini API Key required | Free, open-weights foundation |

---

## Project Structure

```
NeuralQuery/
├── app.py                          # Flask application & REST API routes
├── research.py                     # Multi-source retrieval & research orchestration
├── llm_providers.py                # LLM Provider abstraction (Gemini & NeuralQuery)
├── accuracy.py                     # Deterministic accuracy & confidence evaluator
├── auth.py                         # JWT token management & authentication decorators
├── models.py                       # SQLAlchemy ORM models (User, Conversation, Message)
├── config.py                       # Centralized configuration & environment loader
├── requirements.txt                # Project dependencies
├── wsgi.py                         # WSGI production entry point
├── run_production.py               # Waitress production server launcher
├── render.yaml                     # Cloud deployment configuration
├── Procfile                        # Container / Heroku process declaration
├── .env.example                    # Environment variable template
├── .gitignore                      # Git tracking rules (excludes large weights)
│
├── tests/                          # Automated unit & integration test suite
│   ├── test_accuracy.py            # Accuracy & citation heuristic tests
│   ├── test_providers.py           # Provider selection, prompt & error tests
│   └── test_config.py              # Configuration validation tests
│
├── model/
│   └── neuralquery-production-adapter/
│       ├── adapter_config.json     # LoRA hyperparameters & target modules
│       ├── tokenizer_config.json   # Tokenizer configuration
│       └── README.md               # Adapter setup & Git LFS instructions
│
├── training/
│   ├── README.md                   # Training documentation, hyperparameters & Colab setup
│   ├── train_neuralquery_lora.py   # Reproducible LoRA training script
│   └── dataset_sample.jsonl        # Grounded-RAG sample training dataset
│
├── evaluation/
│   ├── README.md                   # Benchmark results, observations & limitations
│   └── evaluate_grounding.py       # Grounding evaluation benchmark test runner
│
├── docs/
│   └── architecture.md             # Detailed system architecture specification
│
├── templates/
│   ├── landing.html                # Landing page view
│   ├── chat.html                   # Interactive research chat interface
│   ├── login.html                  # User login view
│   ├── register.html               # Registration view
│   └── admin.html                  # System monitoring & diagnostics view
│
└── static/
    ├── css/                        # Responsive CSS styling
    ├── js/
    │   └── main.js                 # Frontend SPA logic, Markdown, & source accordion
    └── img/                        # Static UI assets
```

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/shiva-kumar-1319/NeuralQuery.git
cd NeuralQuery
```

### 2. Create and Activate a Virtual Environment
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

> [!TIP]
> If running on CUDA GPU, ensure a CUDA-enabled PyTorch build is installed:
> `pip install torch --index-url https://download.pytorch.org/whl/cu121`

---

## Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Configure the following variables in `.env`:

```ini
# Database (PostgreSQL or SQLite fallback)
DATABASE_URL=postgresql://username:password@localhost:5432/neuralquery

# Security (Change in production!)
JWT_SECRET=your_super_secret_jwt_key_change_in_production

# Model Provider Selection ('gemini' or 'neuralquery')
MODEL_PROVIDER=gemini

# Required if MODEL_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Required if MODEL_PROVIDER=neuralquery
NEURALQUERY_BASE_MODEL=Qwen/Qwen2.5-1.5B-Instruct
NEURALQUERY_ADAPTER_PATH=model/neuralquery-production-adapter
NEURALQUERY_DEVICE=auto
NEURALQUERY_FALLBACK_TO_GEMINI=false

# Optional: Real-time News Retrieval
NEWS_API_KEY=your_newsapi_org_key_here
```

---

## Running the Application

### Development Server
```bash
python app.py
```
Access the application at `http://localhost:5000`.

### Production WSGI Server (Waitress)
```bash
python run_production.py
```

---

## Running with Gemini

To run using Google Gemini (low local resource usage):
1. Obtain a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey).
2. Set in `.env`:
   ```ini
   MODEL_PROVIDER=gemini
   GEMINI_API_KEY=your_key_here
   ```
3. Start the server:
   ```bash
   python app.py
   ```
The application will use Google's Gemini 2.0 Flash model cascade without loading local PyTorch weights.

---

## Running with NeuralQuery (Custom Model)

To run using your local fine-tuned Qwen LoRA model:
1. Ensure the adapter weights (`adapter_model.safetensors`) are located in:
   ```
   model/neuralquery-production-adapter/adapter_model.safetensors
   ```
2. Set in `.env`:
   ```ini
   MODEL_PROVIDER=neuralquery
   NEURALQUERY_DEVICE=auto
   NEURALQUERY_FALLBACK_TO_GEMINI=true  # Optional: safety fallback
   ```
3. Start the server:
   ```bash
   python app.py
   ```
The application will automatically detect your hardware (CUDA GPU, Apple Silicon MPS, or CPU) and load the base model with the LoRA adapter upon the first query.

---

## Training Your Own Adapter

To train or reproduce the fine-tuned LoRA adapter:

1. Prepare your training dataset in JSONL format (see [training/dataset_sample.jsonl](training/dataset_sample.jsonl)).
2. Execute the fine-tuning script:
   ```bash
   python training/train_neuralquery_lora.py \
       --base_model Qwen/Qwen2.5-1.5B-Instruct \
       --dataset training/dataset_sample.jsonl \
       --output_dir model/neuralquery-production-adapter \
       --epochs 3 \
       --batch_size 2 \
       --learning_rate 2e-4
   ```
The resulting adapter will be saved directly to `model/neuralquery-production-adapter/`.

---

## Evaluation Benchmark

Run the automated grounding evaluation suite:

```bash
python evaluation/evaluate_grounding.py
```

This verifies refusal of unsupported claims, conflict resolution, and citation presence against benchmark test cases.

---

## Limitations

- **Model Scale:** The custom model is 1.5 billion parameters. For complex mathematical reasoning or long multi-document deduction, larger foundation models or Gemini 2.0 Flash remain more capable.
- **Hardware Latency:** While GPU inference is sub-second, running the custom model on a low-spec CPU can produce perceptible latency (~8–18 tokens/sec).
- **Retrieval Dependency:** Grounded generation depends directly on the quality of search results retrieved from DuckDuckGo and NewsAPI.
- **Deployment Memory:** Deploying the custom model requires a minimum of 8 GB system RAM (CPU) or 4 GB GPU VRAM (GPU).

---

## Future Improvements

- **Hybrid Semantic Reranking:** Adding a cross-encoder reranker (e.g., `bge-reranker-small`) between search retrieval and evidence assembly.
- **Direct Citation Span Markers:** Outputting exact character-offset spans for highlighted evidence citations.
- **Larger Parameter Scale:** Training an 7B/8B parameter variant (e.g., `Qwen2.5-7B-Instruct`) for higher reasoning depth.
- **vLLM / TensorRT-LLM Integration:** Integrating high-throughput serving runtimes for production deployments.

---

## License

This repository is provided as a portfolio and educational project. Add an explicit license file before distributing it for reuse.
