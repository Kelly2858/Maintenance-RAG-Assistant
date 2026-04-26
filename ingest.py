""""""
import os
import re
import logging
from typing import List, Dict
import chromadb
from sentence_transformers import SentenceTransformer
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
VECTOR_DB_DIR = os.path.join(os.path.dirname(__file__), 'vector_db')
COLLECTION_NAME = 'maintenance_docs'
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
logging.basicConfig(level=logging.INFO, format='%(asctime)s │ %(name)-14s │ %(levelname)-5s │ %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger('ingest')

def clean_text(text: str) -> str:
    """"""
    text = re.sub('https?://\\S+', '', text)
    text = re.sub('[^\\w\\s.,;:!?\'\\"\\n#()/°-]', '', text)
    text = re.sub('[ \\t]+', ' ', text)
    text = re.sub('\\n{3,}', '\n\n', text)
    return text.strip()

def chunk_document(text: str, source: str) -> List[Dict]:
    """"""
    parts = re.split('(?m)^##\\s+(.*)$', text)
    chunks: List[Dict] = []
    preamble = parts[0].strip()
    preamble = re.sub('(?m)^#\\s+.*$', '', preamble).strip()
    if preamble:
        chunks.extend(_split_into_sized_chunks(preamble, 'Overview', source))
    for i in range(1, len(parts), 2):
        section_title = parts[i].strip()
        section_body = parts[i + 1].strip() if i + 1 < len(parts) else ''
        if section_body:
            chunks.extend(_split_into_sized_chunks(section_body, section_title, source))
    return chunks

def _split_into_sized_chunks(text: str, section: str, source: str) -> List[Dict]:
    """"""
    text = re.sub('\\n+', '\n', text).strip()
    chunks: List[Dict] = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        if end >= len(text):
            chunk_text = text[start:].strip()
            if chunk_text:
                chunks.append({'text': chunk_text, 'section': section, 'source': source})
            break
        last_nl = text.rfind('\n', start, end)
        if last_nl != -1 and last_nl > start + CHUNK_SIZE // 2:
            end = last_nl
        else:
            last_period = text.rfind('. ', start, end)
            if last_period != -1 and last_period > start + CHUNK_SIZE // 2:
                end = last_period + 1
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({'text': chunk_text, 'section': section, 'source': source})
        start = end - CHUNK_OVERLAP
    return chunks

def ingest_docs() -> Dict:
    """"""
    if not os.path.exists(DATA_DIR):
        raise FileNotFoundError(f'Data directory not found: {DATA_DIR}')
    files = sorted((f for f in os.listdir(DATA_DIR) if f.endswith('.txt')))
    if not files:
        raise ValueError(f'No .txt files found in {DATA_DIR}')
    logger.info("Found %d document(s) in '%s'", len(files), DATA_DIR)
    all_chunks: List[Dict] = []
    doc_stats: List[Dict] = []
    for filename in files:
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as fh:
            raw = fh.read()
        cleaned = clean_text(raw)
        chunks = chunk_document(cleaned, filename)
        all_chunks.extend(chunks)
        stat = {'document': filename, 'raw_chars': len(raw), 'cleaned_chars': len(cleaned), 'chunks': len(chunks)}
        doc_stats.append(stat)
        logger.info('  → %s: %d chars → %d chunks', filename, len(cleaned), len(chunks))
    logger.info('Total chunks: %d', len(all_chunks))
    logger.info("Loading embedding model '%s'...", EMBEDDING_MODEL_NAME)
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    texts = [c['text'] for c in all_chunks]
    logger.info('Generating embeddings for %d chunks...', len(texts))
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    embeddings_list = embeddings.tolist()
    logger.info('Storing embeddings in ChromaDB (%s)...', VECTOR_DB_DIR)
    os.makedirs(VECTOR_DB_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
    try:
        client.delete_collection(COLLECTION_NAME)
    except (ValueError, Exception):
        pass
    collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={'hnsw:space': 'cosine'})
    ids = [f'chunk_{i}' for i in range(len(all_chunks))]
    metadatas = [{'source': c['source'], 'section': c['section']} for c in all_chunks]
    batch_size = 50
    for i in range(0, len(ids), batch_size):
        collection.add(ids=ids[i:i + batch_size], embeddings=embeddings_list[i:i + batch_size], documents=texts[i:i + batch_size], metadatas=metadatas[i:i + batch_size])
        logger.info('  Ingested batch %d–%d', i, min(i + batch_size, len(ids)))
    summary = {'total_documents': len(files), 'total_chunks': len(all_chunks), 'embedding_model': EMBEDDING_MODEL_NAME, 'embedding_dimension': embeddings.shape[1], 'vector_db_path': VECTOR_DB_DIR, 'collection_name': COLLECTION_NAME, 'documents': doc_stats}
    logger.info('✓ Ingestion complete! %d chunks stored.', len(all_chunks))
    return summary
if __name__ == '__main__':
    result = ingest_docs()
    print('\n-- Ingestion Summary --')
    for doc in result['documents']:
        print(f"  {doc['document']}: {doc['chunks']} chunks")
    print(f"  Total: {result['total_chunks']} chunks  |  Model: {result['embedding_model']}")