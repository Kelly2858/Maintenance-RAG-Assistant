# Intelligent Maintenance Agent — Design Document

This document outlines the architectural decisions, trade-offs, and future improvements for the Retrieval-Augmented Generation (RAG) maintenance assistant.

## Assumptions Made
1. **Document Structure**: The knowledge base consists of semi-structured text files where distinct topics are separated by Markdown-style `## Section` headers.
2. **Offline Embedding**: The embeddings (`all-MiniLM-L6-v2`) are generated locally using CPU. This assumes the server has sufficient memory to run the lightweight SentenceTransformers model.
3. **Low-Latency Priority**: The system prioritizes response speed and accuracy. The use of Groq (Llama-3.3-70b) as a fallback mechanism assumes the need for high-throughput generation when the primary Gemini API is rate-limited.
4. **Local Vector Storage**: ChromaDB is used in persistent local mode, assuming the application runs on a single node and does not require distributed database architecture.

## Trade-offs Considered

1. **Local Embeddings vs API Embeddings**
   - *Decision*: Used local `SentenceTransformers` instead of OpenAI/Gemini embedding APIs.
   - *Trade-off*: Saved API costs and rate limits at the expense of slight CPU overhead during ingestion and querying. The MiniLM model is highly optimized so the latency impact is negligible (typically <50ms per query).

2. **Chunking Strategy**
   - *Decision*: Implemented section-aware chunking combined with paragraph/sentence boundaries (500 chars with 80 overlap).
   - *Trade-off*: Slower ingestion parsing compared to naive fixed-length chunking, but drastically improves the semantic coherence of the retrieved context, preventing sentences from being cut in half.

3. **Multi-LLM Fallback Architecture**
   - *Decision*: The pipeline attempts to use Google Gemini 2.0 Flash first, and automatically falls back to Groq (Llama 3) if quota limits are hit.
   - *Trade-off*: Increases codebase complexity and requires two separate SDKs (`google-generativeai` and `groq`), but provides significantly higher reliability and uptime for the end user.

4. **Streamlit vs Custom React/FastAPI Frontend**
   - *Decision*: Built the entire UI and backend orchestration into a single Streamlit application.
   - *Trade-off*: Less customizable UI state management compared to a decoupled React frontend, but allowed for rapid development of a premium, data-rich dashboard with built-in metric visualizations.

## Improvements for Production

1. **Distributed Vector Database**: Migrate from local persistent ChromaDB to a cloud-managed vector database (e.g., Pinecone, Weaviate, or managed Chroma) to support multi-node scaling and larger document collections.
2. **Hybrid Search (BM25 + Dense)**: Implement hybrid retrieval. Currently, the system uses purely dense vector embeddings (cosine similarity). Adding sparse keyword search (BM25) would improve retrieval for specific part numbers or exact maintenance codes.
3. **Asynchronous Processing**: Shift document ingestion to an asynchronous background worker (e.g., Celery/Redis) so large document uploads don't block the main application thread.
4. **Continuous Evaluation**: Integrate RAG evaluation frameworks (like Ragas or TruLens) to programmatically evaluate answer relevancy, faithfulness, and context recall over time.
5. **Streaming Responses**: Update the LLM generation calls to use streaming (yielding tokens as they are generated) to drastically reduce perceived latency for the user, especially for longer maintenance procedures.
