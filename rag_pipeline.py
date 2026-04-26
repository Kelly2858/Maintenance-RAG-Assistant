""""""
import os
import time
import logging
from typing import Dict, Any, List
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)-14s | %(levelname)-5s | %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger('rag_pipeline')
VECTOR_DB_DIR = os.path.join(os.path.dirname(__file__), 'vector_db')
COLLECTION_NAME = 'maintenance_docs'
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
TOP_K = 5
SCORE_THRESHOLD = 0.3
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 1024
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'auto').lower()
GEMINI_MODEL = 'gemini-2.0-flash'
GROQ_MODEL = 'llama-3.3-70b-versatile'
LLM_MODEL = GEMINI_MODEL
SYSTEM_PROMPT = "You are an expert industrial maintenance assistant. Your sole purpose is to answer questions based ONLY on the provided context retrieved from the maintenance knowledge base.\n\nRULES:\n1. GROUNDING: Construct your answer strictly from the provided context.\n2. NO HALLUCINATION: Do NOT add outside information or invent steps/details.\n3. CITATIONS: Include the source document name in parentheses, e.g. (Source: hvac_guide.txt).\n4. PARTIAL DATA: If the context contains relevant information but does not fully answer the question, provide what IS available and note what is missing.\n5. INSUFFICIENT DATA: If the context is completely irrelevant, reply EXACTLY with: 'I don't have sufficient information in the knowledge base to answer this question.'\n6. FORMAT: Use clear, concise language suitable for maintenance technicians.\n"

def _init_gemini():
    """"""
    import google.generativeai as genai
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError('GOOGLE_API_KEY not set')
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name=GEMINI_MODEL, system_instruction=SYSTEM_PROMPT, generation_config=genai.GenerationConfig(temperature=LLM_TEMPERATURE, max_output_tokens=LLM_MAX_TOKENS))
    return (model, GEMINI_MODEL)

def _init_groq():
    """"""
    from groq import Groq
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key or api_key.startswith('your_'):
        raise ValueError('GROQ_API_KEY not set or is still placeholder')
    client = Groq(api_key=api_key)
    return (client, GROQ_MODEL)

def _call_gemini(model, prompt: str) -> str:
    """"""
    response = model.generate_content(prompt)
    return response.text

def _call_groq(client, prompt: str) -> str:
    """"""
    response = client.chat.completions.create(messages=[{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': prompt}], model=GROQ_MODEL, temperature=LLM_TEMPERATURE, max_tokens=LLM_MAX_TOKENS)
    return response.choices[0].message.content

class RAGPipeline:
    """"""

    def __init__(self):
        """"""
        global LLM_MODEL
        logger.info("Loading embedding model '%s'...", EMBEDDING_MODEL_NAME)
        self.embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info("Connecting to ChromaDB at '%s'...", VECTOR_DB_DIR)
        self.chroma_client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
        self.collection = self.chroma_client.get_or_create_collection(name=COLLECTION_NAME, metadata={'hnsw:space': 'cosine'})
        self.gemini_model = None
        self.groq_client = None
        self.active_provider = None
        if LLM_PROVIDER in ('gemini', 'auto'):
            try:
                self.gemini_model, _ = _init_gemini()
                self.active_provider = 'gemini'
                LLM_MODEL = GEMINI_MODEL
                logger.info('Gemini LLM initialized (%s)', GEMINI_MODEL)
            except Exception as e:
                logger.warning('Gemini init failed: %s', e)
        if LLM_PROVIDER in ('groq', 'auto'):
            try:
                self.groq_client, _ = _init_groq()
                if self.active_provider is None:
                    self.active_provider = 'groq'
                    LLM_MODEL = GROQ_MODEL
                logger.info('Groq LLM initialized (%s)', GROQ_MODEL)
            except Exception as e:
                logger.warning('Groq init failed: %s', e)
        if self.gemini_model is None and self.groq_client is None:
            raise ValueError('No LLM provider available. Set GOOGLE_API_KEY and/or GROQ_API_KEY in .env')
        logger.info('RAG Pipeline initialized (active LLM: %s).', self.active_provider)

    def _call_llm(self, prompt: str) -> str:
        """"""
        providers = []
        if self.active_provider == 'gemini':
            if self.gemini_model:
                providers.append(('gemini', self.gemini_model))
            if self.groq_client:
                providers.append(('groq', self.groq_client))
        else:
            if self.groq_client:
                providers.append(('groq', self.groq_client))
            if self.gemini_model:
                providers.append(('gemini', self.gemini_model))
        last_error = None
        for provider_name, backend in providers:
            try:
                if provider_name == 'gemini':
                    answer = _call_gemini(backend, prompt)
                else:
                    answer = _call_groq(backend, prompt)
                logger.info('LLM response from %s (%d chars)', provider_name, len(answer))
                return answer
            except Exception as exc:
                logger.warning('LLM call to %s failed: %s — trying fallback...', provider_name, exc)
                last_error = exc
        return f'Error: All LLM providers failed. Last error: {last_error}'

    def query(self, question: str) -> Dict[str, Any]:
        """"""
        start_time = time.time()
        query_embedding = self.embed_model.encode(question, normalize_embeddings=True).tolist()
        retrieval_start = time.time()
        doc_count = self.collection.count()
        if doc_count == 0:
            return self._empty_response(time.time() - start_time)
        results = self.collection.query(query_embeddings=[query_embedding], n_results=min(TOP_K, doc_count), include=['documents', 'metadatas', 'distances'])
        retrieval_latency = time.time() - retrieval_start
        retrieved_chunks = self._format_results(results)
        logger.info('Retrieved %d chunks (%.2fs), %d above threshold %.2f', len(results['ids'][0]) if results['ids'] else 0, retrieval_latency, len(retrieved_chunks), SCORE_THRESHOLD)
        if not retrieved_chunks:
            return self._empty_response(time.time() - start_time)
        context = self._build_context(retrieved_chunks)
        prompt = f'Context:\n{context}\n\nQuestion: {question}\nAnswer:'
        llm_start = time.time()
        answer = self._call_llm(prompt)
        llm_latency = time.time() - llm_start
        total_latency = time.time() - start_time
        metrics = self._compute_metrics(retrieved_chunks, answer, total_latency, retrieval_latency, llm_latency)
        sources_used = list(dict.fromkeys((ch['metadata']['source'] for ch in retrieved_chunks)))
        return {'answer': answer, 'chunks': retrieved_chunks, 'sources_used': sources_used, 'metrics': metrics}

    def _format_results(self, results: Dict) -> List[Dict]:
        """"""
        formatted = []
        if not results or not results['ids'] or (not results['ids'][0]):
            return formatted
        for i in range(len(results['ids'][0])):
            distance = results['distances'][0][i]
            relevance = max(0.0, 1.0 - distance)
            if relevance < SCORE_THRESHOLD:
                continue
            formatted.append({'id': results['ids'][0][i], 'text': results['documents'][0][i], 'metadata': results['metadatas'][0][i], 'distance': round(distance, 4), 'relevance': round(relevance, 4)})
        return formatted

    def _build_context(self, chunks: List[Dict]) -> str:
        """"""
        parts = []
        for i, ch in enumerate(chunks):
            src = ch['metadata']['source']
            sec = ch['metadata']['section']
            parts.append(f"--- Chunk {i + 1} | Document: {src} | Section: {sec} ---\n{ch['text']}\n")
        return '\n'.join(parts)

    def _compute_metrics(self, chunks: List[Dict], answer: str, total_latency: float, retrieval_latency: float, llm_latency: float) -> Dict[str, Any]:
        """"""
        avg_relevance = sum((c['relevance'] for c in chunks)) / len(chunks) if chunks else 0
        relevant = [c for c in chunks if c['relevance'] > SCORE_THRESHOLD]
        precision_at_k = len(relevant) / len(chunks) * 100 if chunks else 0
        insufficient = "I don't have sufficient information"
        if insufficient.lower() in answer.lower():
            confidence = avg_relevance * 20
        else:
            confidence = avg_relevance * 70 + 30
        return {'total_latency_sec': round(total_latency, 2), 'retrieval_latency_sec': round(retrieval_latency, 2), 'llm_latency_sec': round(llm_latency, 2), 'avg_relevance_pct': round(avg_relevance * 100, 1), 'confidence_pct': round(min(confidence, 100), 1), 'precision_at_k_pct': round(precision_at_k, 1), 'chunks_retrieved': TOP_K, 'chunks_after_threshold': len(chunks)}

    def _empty_response(self, latency: float) -> Dict[str, Any]:
        """"""
        return {'answer': "I don't have sufficient information in the knowledge base to answer this question.", 'chunks': [], 'sources_used': [], 'metrics': {'total_latency_sec': round(latency, 2), 'retrieval_latency_sec': round(latency, 2), 'llm_latency_sec': 0, 'avg_relevance_pct': 0, 'confidence_pct': 0, 'precision_at_k_pct': 0, 'chunks_retrieved': 0, 'chunks_after_threshold': 0}}

    def get_status(self) -> Dict[str, Any]:
        """"""
        return {'collection_name': COLLECTION_NAME, 'document_count': self.collection.count(), 'embedding_model': EMBEDDING_MODEL_NAME, 'llm_model': LLM_MODEL, 'top_k': TOP_K, 'score_threshold': SCORE_THRESHOLD}