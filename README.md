# 🔧 RAG Maintenance Assistant

> **Retrieval-Augmented Generation (RAG)** system for answering industrial maintenance questions grounded in uploaded knowledge base documents.

## Architecture

```
User uploads/keeps maintenance documents
        ↓
System reads documents (ingest.py)
        ↓
Documents are split into section-aware chunks
        ↓
Chunks are converted into embeddings (SentenceTransformers)
        ↓
Embeddings are stored in vector database (ChromaDB)
        ↓
User asks maintenance question (Streamlit UI)
        ↓
Question is converted into embedding
        ↓
Relevant chunks are retrieved (cosine similarity + threshold)
        ↓
LLM generates grounded answer (Google Gemini or Groq auto-fallback)
        ↓
Answer + retrieved chunks + metrics are displayed
```

## Tech Stack

| Component         | Technology                          |
|-------------------|-------------------------------------|
| Language          | Python 3.10+                        |
| UI Framework      | Streamlit                           |
| Vector Database   | ChromaDB (persistent, HNSW index)   |
| Embeddings        | SentenceTransformers (all-MiniLM-L6-v2) |
| Primary LLM       | Google Gemini 2.0 Flash             |
| Fallback LLM      | Groq (llama-3.3-70b-versatile)      |
| Config Management | python-dotenv                       |

## Folder Structure

```
rag-maintenance-assistant/
│
├── data/                        # Maintenance documents (source of truth)
│   ├── pump_maintenance.txt
│   ├── motor_maintenance.txt
│   └── hvac_guide.txt
│
├── vector_db/                   # ChromaDB persistent storage (auto-generated)
│
├── app.py                       # Streamlit UI (main entry point)
├── ingest.py                    # Document ingestion pipeline
├── rag_pipeline.py              # RAG query pipeline (Multi-LLM)
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # This documentation file
```

## Setup & Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Keys

Rename `.env.example` to `.env` (or create a new `.env` file) and add your API keys:

```
GOOGLE_API_KEY=your_google_api_key_here
GROQ_API_KEY=your_groq_api_key_here
LLM_PROVIDER=auto
```

> **Multi-LLM Fallback**: The `LLM_PROVIDER=auto` setting makes the app highly resilient. It will attempt to use Google Gemini first. If the API key is rate-limited or exhausted, it seamlessly falls back to the free and fast Groq API. You only need to provide *one* working API key for the app to run!

### 3. Add Maintenance Documents

Place `.txt` files in the `data/` folder. Sample documents are already included covering HVAC, electrical, pumps, conveyors, and safety procedures.

### 4. Run the Application

```bash
streamlit run app.py
```

The application dashboard will automatically open at `http://localhost:8501`.

## How to Use

### First-Time Setup
1. Click **🔄 Ingest Documents** in the sidebar to process, chunk, and embed all documents into the ChromaDB vector store.
2. Wait for ingestion to complete (you'll see a success message with chunk counts).

### Asking Questions
1. Type your maintenance question in the input box **or** click a sample question button.
2. Click **🚀 Ask**.
3. View the grounded answer alongside the source documents and raw retrieved chunks.

### UI Features
- **📊 Metric Cards** — Instant readout of Confidence, Relevance, Latency, and Precision.
- **🤖 Generated Answer** — Strict LLM-grounded response citing source files.
- **📂 Source Documents** — Clear tagging of which documents contributed to the answer.
- **📑 Retrieved Chunks** — The exact text chunks extracted from your `.txt` files, color-coded by vector relevance score.
- **⚙️ Config Panel** — Exposes system status (Embedding model, LLM, chunk size).

## Sample Queries & Expected Output

### Query: "What causes pump cavitation?"

**Expected Answer:**
> Cavitation occurs when the Net Positive Suction Head Available (NPSHa) is lower than required (NPSHr). It can be identified by a sound similar to pumping marbles. (Source: pump_maintenance.txt)

**Expected Metrics:** 
- Relevance: > 60%
- Confidence: > 70%
- Precision@K: 100%

### Query: "How often should HVAC filters be replaced?"

**Expected Answer:**
> HVAC air filters should be replaced every 1 to 3 months, depending on the system's usage and the specific environment. In environments with high dust or industrial debris, monthly replacement is recommended. (Source: hvac_guide.txt)

## Key Design Decisions

1. **Auto-Fallback LLM System** — Designed for robustness. By natively integrating `google-generativeai` and `groq` SDKs, the app protects against quota exhaustion by routing traffic to the active, free-tier provider.
2. **Local Vector Embeddings** — `SentenceTransformers` runs completely locally and offline. This yields zero-cost embeddings, prevents rate limits, and processes data instantly while maintaining 384-dimensional semantic accuracy.
3. **Section-Aware Chunking** — The document ingestor applies smart logic that breaks text on Markdown `## Section` boundaries first, before sub-dividing. This prevents critical instructions from being arbitrarily sliced in half.
4. **Strict Grounded System Prompt** — The LLM is explicitly barred from utilizing any external knowledge. If the search query yields irrelevant context from ChromaDB (based on threshold filtering), the assistant refuses to hallucinate and states the info is unavailable.
