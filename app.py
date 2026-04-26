""""""
import streamlit as st
import os
import sys
import time
st.set_page_config(page_title='RAG Maintenance Assistant', page_icon='🔧', layout='wide', initial_sidebar_state='expanded')
st.markdown("\n<style>\n    /* ── Global ─── */\n    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');\n\n    .stApp {\n        font-family: 'Inter', sans-serif;\n    }\n\n    /* ── Hero Header ─── */\n    .hero-header {\n        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);\n        padding: 2rem 2.5rem;\n        border-radius: 16px;\n        margin-bottom: 1.5rem;\n        color: white;\n        position: relative;\n        overflow: hidden;\n    }\n    .hero-header::before {\n        content: '';\n        position: absolute;\n        top: -50%;\n        right: -20%;\n        width: 400px;\n        height: 400px;\n        background: radial-gradient(circle, rgba(99, 102, 241, 0.3) 0%, transparent 70%);\n        border-radius: 50%;\n    }\n    .hero-header h1 {\n        font-size: 2rem;\n        font-weight: 700;\n        margin: 0;\n        position: relative;\n        z-index: 1;\n    }\n    .hero-header p {\n        font-size: 1rem;\n        opacity: 0.85;\n        margin: 0.5rem 0 0 0;\n        position: relative;\n        z-index: 1;\n    }\n\n    /* ── Metric Cards ─── */\n    .metric-row {\n        display: flex;\n        gap: 1rem;\n        margin: 1rem 0;\n        flex-wrap: wrap;\n    }\n    .metric-card {\n        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);\n        border: 1px solid rgba(99, 102, 241, 0.2);\n        border-radius: 12px;\n        padding: 1rem 1.25rem;\n        flex: 1;\n        min-width: 140px;\n        color: white;\n        text-align: center;\n        transition: transform 0.2s, box-shadow 0.2s;\n    }\n    .metric-card:hover {\n        transform: translateY(-2px);\n        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.15);\n    }\n    .metric-value {\n        font-size: 1.6rem;\n        font-weight: 700;\n        color: #818cf8;\n    }\n    .metric-label {\n        font-size: 0.75rem;\n        text-transform: uppercase;\n        letter-spacing: 0.05em;\n        opacity: 0.7;\n        margin-top: 0.25rem;\n    }\n\n    /* ── Answer Box ─── */\n    .answer-box {\n        background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%);\n        border-left: 4px solid #818cf8;\n        border-radius: 12px;\n        padding: 1.5rem;\n        margin: 1rem 0;\n        color: #e2e8f0;\n        line-height: 1.7;\n        font-size: 0.95rem;\n    }\n\n    /* ── Chunk Cards ─── */\n    .chunk-card {\n        background: #0f1419;\n        border: 1px solid rgba(255, 255, 255, 0.08);\n        border-radius: 12px;\n        padding: 1.25rem;\n        margin: 0.75rem 0;\n        transition: border-color 0.2s;\n    }\n    .chunk-card:hover {\n        border-color: rgba(99, 102, 241, 0.4);\n    }\n    .chunk-header {\n        display: flex;\n        justify-content: space-between;\n        align-items: center;\n        margin-bottom: 0.75rem;\n        flex-wrap: wrap;\n        gap: 0.5rem;\n    }\n    .chunk-source {\n        background: rgba(99, 102, 241, 0.15);\n        color: #a5b4fc;\n        padding: 0.25rem 0.75rem;\n        border-radius: 20px;\n        font-size: 0.75rem;\n        font-weight: 500;\n    }\n    .chunk-relevance {\n        font-size: 0.75rem;\n        font-weight: 600;\n    }\n    .relevance-high { color: #34d399; }\n    .relevance-mid { color: #fbbf24; }\n    .relevance-low { color: #f87171; }\n    .chunk-text {\n        color: #94a3b8;\n        font-size: 0.85rem;\n        line-height: 1.6;\n    }\n\n    /* ── Source Badge ─── */\n    .source-badge {\n        display: inline-block;\n        background: linear-gradient(135deg, #312e81, #4338ca);\n        color: white;\n        padding: 0.3rem 0.8rem;\n        border-radius: 20px;\n        font-size: 0.8rem;\n        font-weight: 500;\n        margin: 0.2rem 0.3rem;\n    }\n\n    /* ── Status Dot ─── */\n    .status-online {\n        display: inline-flex;\n        align-items: center;\n        gap: 0.5rem;\n        color: #34d399;\n        font-weight: 500;\n        font-size: 0.85rem;\n    }\n    .status-dot {\n        width: 8px;\n        height: 8px;\n        background: #34d399;\n        border-radius: 50%;\n        display: inline-block;\n        animation: pulse 2s infinite;\n    }\n    @keyframes pulse {\n        0%, 100% { opacity: 1; }\n        50% { opacity: 0.4; }\n    }\n\n    /* ── Sidebar Styling ─── */\n    .sidebar-section {\n        background: rgba(255, 255, 255, 0.03);\n        border: 1px solid rgba(255, 255, 255, 0.06);\n        border-radius: 10px;\n        padding: 1rem;\n        margin: 0.5rem 0;\n    }\n    .sidebar-title {\n        font-size: 0.8rem;\n        text-transform: uppercase;\n        letter-spacing: 0.08em;\n        opacity: 0.6;\n        margin-bottom: 0.5rem;\n    }\n\n    /* ── History Item ─── */\n    .history-item {\n        background: rgba(255, 255, 255, 0.03);\n        border: 1px solid rgba(255, 255, 255, 0.06);\n        border-radius: 8px;\n        padding: 0.75rem;\n        margin: 0.5rem 0;\n        font-size: 0.85rem;\n        color: #94a3b8;\n    }\n    .history-query {\n        color: #e2e8f0;\n        font-weight: 500;\n    }\n\n    /* ── Hide Streamlit branding ─── */\n    #MainMenu {visibility: hidden;}\n    footer {visibility: hidden;}\n    header {visibility: hidden;}\n\n    /* ── Input styling ─── */\n    .stTextInput > div > div > input {\n        border-radius: 12px;\n        padding: 0.75rem 1rem;\n        font-size: 1rem;\n    }\n</style>\n", unsafe_allow_html=True)
if 'pipeline' not in st.session_state:
    st.session_state.pipeline = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'ingestion_done' not in st.session_state:
    st.session_state.ingestion_done = False

@st.cache_resource(show_spinner=False)
def init_pipeline():
    """"""
    from rag_pipeline import RAGPipeline
    return RAGPipeline()
with st.sidebar:
    st.markdown('## ⚙️ Control Panel')
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">System Status</div>', unsafe_allow_html=True)
    try:
        pipeline = init_pipeline()
        st.session_state.pipeline = pipeline
        status = pipeline.get_status()
        st.markdown('<div class="status-online"><span class="status-dot"></span> Online</div>', unsafe_allow_html=True)
        st.caption(f"📂 Collection: `{status['collection_name']}`")
        st.caption(f"📊 Documents in store: `{status['document_count']}`")
        st.caption(f"🧠 Embedding: `{status['embedding_model']}`")
        st.caption(f"🤖 LLM: `{status['llm_model']}`")
    except Exception as e:
        st.error(f'❌ Pipeline init failed: {e}')
        st.session_state.pipeline = None
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('---')
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Document Ingestion</div>', unsafe_allow_html=True)
    st.caption('Process and index maintenance documents from the `data/` folder.')
    if st.button('🔄 Ingest Documents', use_container_width=True, type='primary'):
        with st.spinner('Reading, chunking & embedding documents...'):
            try:
                from ingest import ingest_docs
                summary = ingest_docs()
                st.session_state.ingestion_done = True
                st.cache_resource.clear()
                st.session_state.pipeline = init_pipeline()
                st.success(f"✅ Ingested **{summary['total_chunks']}** chunks from **{summary['total_documents']}** documents")
                with st.expander('📋 Ingestion Details'):
                    for doc in summary['documents']:
                        st.write(f"- **{doc['document']}**: {doc['chunks']} chunks")
                    st.write(f"- Embedding model: `{summary['embedding_model']}`")
                    st.write(f"- Dimension: `{summary['embedding_dimension']}`")
            except Exception as e:
                st.error(f'❌ Ingestion failed: {e}')
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('---')
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Pipeline Configuration</div>', unsafe_allow_html=True)
    from rag_pipeline import EMBEDDING_MODEL_NAME, LLM_MODEL, TOP_K, SCORE_THRESHOLD, LLM_TEMPERATURE
    from ingest import CHUNK_OVERLAP, CHUNK_SIZE
    config_data = {'Embedding Model': EMBEDDING_MODEL_NAME, 'LLM Model': LLM_MODEL, 'Chunk Size': f'{CHUNK_SIZE} chars', 'Chunk Overlap': f'{CHUNK_OVERLAP} chars', 'Top-K Retrieval': TOP_K, 'Score Threshold': SCORE_THRESHOLD, 'Temperature': LLM_TEMPERATURE}
    for k, v in config_data.items():
        st.caption(f'**{k}:** `{v}`')
    st.markdown('</div>', unsafe_allow_html=True)
    if st.session_state.history:
        st.markdown('---')
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">Recent Queries</div>', unsafe_allow_html=True)
        for i, h in enumerate(reversed(st.session_state.history[-5:])):
            st.markdown(f"""<div class="history-item"><div class="history-query">💬 {h['query'][:60]}...</div><span style="font-size:0.7rem; opacity:0.5;">⏱ {h['metrics']['total_latency_sec']}s  •  📊 {h['metrics']['confidence_pct']}%</span></div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
st.markdown('\n<div class="hero-header">\n    <h1>🔧 RAG Maintenance Assistant</h1>\n    <p>Ask any maintenance question — answers are grounded in your uploaded knowledge base documents.</p>\n</div>\n', unsafe_allow_html=True)
st.markdown('##### 💡 Try a sample question:')
sample_cols = st.columns(4)
sample_questions = ['How often should HVAC filters be replaced?', 'What causes pump cavitation?', 'How to test motor insulation?', 'What is LOTO procedure?']
if 'form_question' not in st.session_state:
    st.session_state.form_question = ''

def _set_sample(q):
    st.session_state.form_question = q
for i, q in enumerate(sample_questions):
    with sample_cols[i]:
        st.button(q, key=f'sample_{i}', use_container_width=True, on_click=_set_sample, args=(q,))
st.markdown('---')
with st.form('ask_form', clear_on_submit=False):
    user_question = st.text_input('🔍 Ask your maintenance question:', placeholder='e.g., What is the procedure for pump alignment?', label_visibility='collapsed', key='form_question')
    submit = st.form_submit_button('🚀 Ask', type='primary', use_container_width=True)
if submit and user_question.strip():
    pipeline = st.session_state.pipeline
    if not pipeline:
        st.error('⚠️ Pipeline not initialized. Please check your API key and try again.')
    else:
        with st.spinner('🔍 Searching knowledge base & generating answer...'):
            try:
                result = pipeline.query(user_question.strip())
            except Exception as e:
                st.error(f'❌ Query failed: {e}')
                st.stop()
        st.session_state.history.append({'query': user_question.strip(), 'answer': result['answer'], 'metrics': result['metrics'], 'sources': result['sources_used']})
        m = result['metrics']
        st.markdown(f"""\n        <div class="metric-row">\n            <div class="metric-card">\n                <div class="metric-value">{m['confidence_pct']}%</div>\n                <div class="metric-label">Confidence</div>\n            </div>\n            <div class="metric-card">\n                <div class="metric-value">{m['avg_relevance_pct']}%</div>\n                <div class="metric-label">Avg Relevance</div>\n            </div>\n            <div class="metric-card">\n                <div class="metric-value">{m['total_latency_sec']}s</div>\n                <div class="metric-label">Total Latency</div>\n            </div>\n            <div class="metric-card">\n                <div class="metric-value">{m['chunks_after_threshold']}/{m['chunks_retrieved']}</div>\n                <div class="metric-label">Chunks Used</div>\n            </div>\n            <div class="metric-card">\n                <div class="metric-value">{m['precision_at_k_pct']}%</div>\n                <div class="metric-label">Precision@K</div>\n            </div>\n        </div>\n        """, unsafe_allow_html=True)
        st.markdown('### 🤖 Generated Answer')
        st.markdown(f"""<div class="answer-box">{result['answer']}</div>""", unsafe_allow_html=True)
        if result['sources_used']:
            st.markdown('### 📂 Source Documents')
            badges = ' '.join((f'<span class="source-badge">📄 {src}</span>' for src in result['sources_used']))
            st.markdown(badges, unsafe_allow_html=True)
        if result['chunks']:
            st.markdown('### 📑 Retrieved Chunks')
            for i, chunk in enumerate(result['chunks']):
                relevance = chunk['relevance'] * 100
                rel_class = 'relevance-high' if relevance >= 70 else 'relevance-mid' if relevance >= 50 else 'relevance-low'
                st.markdown(f"""\n                <div class="chunk-card">\n                    <div class="chunk-header">\n                        <span class="chunk-source">\n                            📄 {chunk['metadata']['source']} — {chunk['metadata']['section']}\n                        </span>\n                        <span class="chunk-relevance {rel_class}">\n                            ● {relevance:.1f}% relevance\n                        </span>\n                    </div>\n                    <div class="chunk-text">{chunk['text'][:500]}{('...' if len(chunk['text']) > 500 else '')}</div>\n                </div>\n                """, unsafe_allow_html=True)
        with st.expander('📊 Detailed Performance Metrics'):
            col1, col2 = st.columns(2)
            with col1:
                st.metric('Total Latency', f"{m['total_latency_sec']}s")
                st.metric('Retrieval Latency', f"{m['retrieval_latency_sec']}s")
                st.metric('LLM Latency', f"{m['llm_latency_sec']}s")
            with col2:
                st.metric('Avg Relevance', f"{m['avg_relevance_pct']}%")
                st.metric('Confidence', f"{m['confidence_pct']}%")
                st.metric('Precision@K', f"{m['precision_at_k_pct']}%")
elif submit:
    st.warning('⚠️ Please enter a question first.')
if not st.session_state.history and (not submit):
    st.markdown('---')
    st.markdown('\n    <div style="text-align: center; padding: 3rem; opacity: 0.5;">\n        <h3>🔧 Ready to assist</h3>\n        <p>Type a maintenance question above or click a sample question to get started.<br/>\n        If this is your first time, click <strong>Ingest Documents</strong> in the sidebar first.</p>\n    </div>\n    ', unsafe_allow_html=True)