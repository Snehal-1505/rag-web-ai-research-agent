"""
RAG + Web AI Research Agent - Streamlit Application
Redesigned Modern Dashboard UI Structure
"""
import os
import sys
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st

# Add project root to path so our src modules work correctly
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import GEMINI_API_KEY, TAVILY_API_KEY, UPLOADS_DIR
from src.ingestion.document_loader import load_document
from src.ingestion.chunker import chunk_documents
from src.ingestion.indexer import generate_document_embeddings
from src.rag.document_store import DocumentStoreManager
from src.rag.pipeline import run_rag_pipeline
from src.agent.research_agent import ResearchAgent

# ─────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="RAG + Web AI Research Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "doc_store_manager" not in st.session_state:
    st.session_state.doc_store_manager = DocumentStoreManager()

if "doc_count" not in st.session_state:
    st.session_state.doc_count = 0

if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0

if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []

if "indexed_chunks_preview" not in st.session_state:
    st.session_state.indexed_chunks_preview = []

if "api_key" not in st.session_state or not st.session_state.api_key:
    from src.config import GEMINI_API_KEY
    st.session_state.api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY or "")

if "tavily_key" not in st.session_state or not st.session_state.tavily_key:
    from src.config import TAVILY_API_KEY
    st.session_state.tavily_key = os.getenv("TAVILY_API_KEY", TAVILY_API_KEY or "")

if "top_k_docs" not in st.session_state:
    st.session_state.top_k_docs = 5

if "max_web_results" not in st.session_state:
    st.session_state.max_web_results = 5

if "agent_mode" not in st.session_state:
    st.session_state.agent_mode = "🤖 Autonomous AI Agent (Hybrid)"


# ─────────────────────────────────────────────
# DESIGN SYSTEM & CUSTOM CSS STYLING
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at top right, #1a1c36 0%, #0d0e1b 50%, #080911 100%);
        color: #e2e8f0;
    }

    /* Top Glass Navbar */
    .top-navbar {
        background: rgba(18, 20, 39, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.2rem 1.8rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    .nav-brand {
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }

    .nav-title {
        font-size: 1.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #a78bfa 0%, #818cf8 50%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
        margin: 0;
    }

    .nav-subtitle {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 400;
        margin: 0;
    }

    /* Status Pills */
    .status-pill-group {
        display: flex;
        gap: 0.6rem;
        align-items: center;
    }

    .status-pill {
        background: rgba(30, 34, 64, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    .dot-green {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 8px #10b981;
    }

    .dot-purple {
        width: 8px;
        height: 8px;
        background-color: #a78bfa;
        border-radius: 50%;
        box-shadow: 0 0 8px #a78bfa;
    }

    /* Tabs UI */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 17, 33, 0.8);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        white-space: pre;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0 16px;
        border: none;
        transition: all 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
    }

    /* Suggestion Chips */
    .suggestion-chip-btn {
        background: rgba(30, 34, 64, 0.6);
        border: 1px solid rgba(167, 139, 250, 0.2);
        border-radius: 12px;
        padding: 0.6rem 1rem;
        color: #cbd5e1;
        font-size: 0.82rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: left;
        width: 100%;
        margin-bottom: 0.5rem;
    }

    .suggestion-chip-btn:hover {
        background: rgba(99, 102, 241, 0.2);
        border-color: #6366f1;
        color: #ffffff;
        transform: translateY(-1px);
    }

    /* Cards */
    .glass-card {
        background: rgba(18, 20, 39, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }

    /* Strategy Badges */
    .strategy-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 0.6rem;
    }

    .badge-docs {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .badge-web {
        background: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }

    .badge-hybrid {
        background: rgba(168, 85, 247, 0.15);
        color: #c084fc;
        border: 1px solid rgba(168, 85, 247, 0.3);
    }

    /* Source Items */
    .source-box-doc {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin-top: 0.4rem;
        font-size: 0.82rem;
        color: #6ee7b7;
    }

    .source-box-web {
        background: rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin-top: 0.4rem;
        font-size: 0.82rem;
        color: #93c5fd;
    }

    .source-box-web a {
        color: #60a5fa;
        text-decoration: underline;
    }

    /* Primary Button override */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3);
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: rgba(12, 14, 28, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
def process_uploaded_file(uploaded_file) -> tuple[List, int]:
    """Saves and indexes uploaded files."""
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = Path(tmp.name)

    try:
        raw_docs = load_document(tmp_path)
        if not raw_docs:
            return [], 0

        for doc in raw_docs:
            doc.meta["filename"] = uploaded_file.name
            doc.meta["source"] = uploaded_file.name

        chunks = chunk_documents(raw_docs)
        embedded_chunks = generate_document_embeddings(chunks)

        return embedded_chunks, len(embedded_chunks)
    finally:
        tmp_path.unlink(missing_ok=True)


def format_citations_html(doc_results: List[Dict], web_results: List[Dict]) -> str:
    """Formats formatted citations."""
    if not doc_results and not web_results:
        return ""

    html = '<div style="margin-top:1rem; padding-top:0.8rem; border-top:1px dashed rgba(255,255,255,0.1);">'
    html += '<b style="color:#a78bfa; font-size:0.88rem;">📌 Research Citations & Sources:</b>'

    if doc_results:
        seen = set()
        for d in doc_results:
            fname = d.get("filename", "Document")
            page = d.get("page", 1)
            key = f"{fname}|{page}"
            if key not in seen:
                seen.add(key)
                html += f'<div class="source-box-doc">📄 <b>{fname}</b> &nbsp;|&nbsp; Page {page}</div>'

    if web_results:
        seen_web = set()
        for w in web_results:
            title = w.get("title", "Web Page")
            url = w.get("url", "")
            if url and url not in seen_web:
                seen_web.add(url)
                html += f'<div class="source-box-web">🌐 <b>{title}</b> — <a href="{url}" target="_blank">{url}</a></div>'
            elif title and title not in seen_web:
                seen_web.add(title)
                html += f'<div class="source-box-web">🌐 <b>{title}</b></div>'

    html += '</div>'
    return html


# ─────────────────────────────────────────────
# HEADER NAVBAR
# ─────────────────────────────────────────────
api_status_color = "dot-green" if st.session_state.api_key else "dot-purple"
api_status_text = "Gemini Ready" if st.session_state.api_key else "API Key Needed"

st.markdown(f"""
<div class="top-navbar">
    <div class="nav-brand">
        <span style="font-size: 2.2rem;">🧠</span>
        <div>
            <h1 class="nav-title">RAG + Web AI Research Agent</h1>
            <p class="nav-subtitle">Next-Gen Hybrid Research Assistant powered by Haystack AI & Gemini</p>
        </div>
    </div>
    <div class="status-pill-group">
        <div class="status-pill"><span class="{api_status_color}"></span> {api_status_text}</div>
        <div class="status-pill">📁 {st.session_state.doc_count} Chunks Indexed</div>
        <div class="status-pill">⚡ Haystack 2.x</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SIDEBAR CONTROL CENTER
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Control Center")
    st.markdown("---")

    # Reasoning Mode Selector
    st.markdown("**🧠 Agent Mode**")
    mode_selection = st.radio(
        "Mode:",
        ["🤖 Autonomous AI Agent (Hybrid)", "📚 Strict Local Document RAG"],
        index=0 if "Autonomous" in st.session_state.agent_mode else 1,
        key="sidebar_agent_mode",
    )
    st.session_state.agent_mode = mode_selection

    st.markdown("---")

    # Fast Document Processing Widget
    st.markdown("**📂 Quick Ingest**")
    quick_files = st.file_uploader(
        "Upload PDF, TXT, DOCX",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True,
        key="quick_uploader",
    )

    if st.button("⚡ Process & Index", key="quick_process_btn"):
        if not quick_files:
            st.warning("Select files first.")
        else:
            total_chunks = 0
            new_files = []
            prog = st.progress(0)
            status_lbl = st.empty()

            for idx, f in enumerate(quick_files):
                if f.name in st.session_state.indexed_files:
                    continue
                status_lbl.info(f"Embedding {f.name}...")
                try:
                    chunks, c_len = process_uploaded_file(f)
                    if chunks:
                        st.session_state.doc_store_manager.write_documents(chunks)
                        total_chunks += c_len
                        new_files.append(f.name)
                        st.session_state.indexed_chunks_preview.extend(chunks[:3])
                except Exception as ex:
                    st.error(f"Error: {str(ex)}")
                prog.progress((idx + 1) / len(quick_files))

            prog.empty()
            status_lbl.empty()

            if new_files:
                st.session_state.indexed_files.extend(new_files)
                st.session_state.doc_count = st.session_state.doc_store_manager.count_documents()
                st.session_state.chunk_count += total_chunks
                st.success(f"Indexed {len(new_files)} file(s) ({total_chunks} chunks)")

    st.markdown("---")
    st.markdown("**🧹 Reset Options**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", key="clear_chat_side"):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("♻️ Reset DB", key="reset_db_side"):
            st.session_state.doc_store_manager = DocumentStoreManager()
            st.session_state.doc_count = 0
            st.session_state.chunk_count = 0
            st.session_state.indexed_files = []
            st.session_state.indexed_chunks_preview = []
            st.rerun()


# ─────────────────────────────────────────────
# NAVIGATION TABS (NEW UI STRUCTURE)
# ─────────────────────────────────────────────
tab_chat, tab_kb, tab_settings, tab_analytics = st.tabs([
    "💬 AI Research Workspace",
    "📚 Knowledge Base Hub",
    "⚙️ Settings & Configuration",
    "📊 System Analytics"
])

# =============================================================================
# TAB 1: AI RESEARCH WORKSPACE
# =============================================================================
with tab_chat:
    col_main, col_side = st.columns([3, 1])

    with col_side:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 💡 Prompt Starters")
        st.markdown("Click any chip to insert into research prompt:")

        starters = [
            "Summarize the key findings from my uploaded documents.",
            "Search the web for recent developments in AI agents.",
            "Compare local document technical details with live web news.",
            "What are the main risks or limitations discussed in the text?",
        ]

        for s in starters:
            if st.button(f"✨ {s}", key=f"starter_{hash(s)}"):
                st.session_state.pending_prompt = s
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### ⚡ Active Mode")
        st.info(f"Current: **{st.session_state.agent_mode}**")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_main:
        # Display Message Stream
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                if msg.get("badge_html"):
                    st.markdown(msg["badge_html"], unsafe_allow_html=True)
                st.markdown(msg["content"], unsafe_allow_html=True)
                if msg.get("citations_html"):
                    st.markdown(msg["citations_html"], unsafe_allow_html=True)

        # Check for preset prompt starter
        default_val = ""
        if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
            default_val = st.session_state.pending_prompt
            del st.session_state.pending_prompt

        # Chat Input
        if user_query := st.chat_input("Ask any complex research question...", key="chat_input"):

            with st.chat_message("user"):
                st.markdown(user_query)
            st.session_state.messages.append({"role": "user", "content": user_query})

            if not st.session_state.api_key:
                err = "⚠️ **Gemini API Key missing.** Configure your key in the **Settings** tab."
                with st.chat_message("assistant"):
                    st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})

            else:
                with st.chat_message("assistant"):
                    is_agent = "Autonomous" in st.session_state.agent_mode

                    if is_agent:
                        with st.spinner("🤖 AI Agent deliberating (routing between vector DB & live web)..."):
                            try:
                                agent = ResearchAgent(api_key=st.session_state.api_key)
                                res = agent.run(
                                    question=user_query,
                                    document_store=st.session_state.doc_store_manager.store,
                                    top_k_docs=st.session_state.top_k_docs,
                                    max_web_results=st.session_state.max_web_results,
                                )

                                answer = res["answer"]
                                strategy = res["strategy"]
                                doc_res = res.get("doc_results", [])
                                web_res = res.get("web_results", [])

                                badge_map = {
                                    "documents": '<span class="strategy-badge badge-docs">📄 Strategy: Local Documents</span>',
                                    "web": '<span class="strategy-badge badge-web">🌐 Strategy: Live Web Search</span>',
                                    "hybrid": '<span class="strategy-badge badge-hybrid">🔀 Strategy: Hybrid (Docs + Web)</span>',
                                }
                                badge_html = badge_map.get(strategy, "")
                                citations_html = format_citations_html(doc_res, web_res)

                                if badge_html:
                                    st.markdown(badge_html, unsafe_allow_html=True)
                                st.markdown(answer)
                                if citations_html:
                                    st.markdown(citations_html, unsafe_allow_html=True)

                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": answer,
                                    "badge_html": badge_html,
                                    "citations_html": citations_html,
                                })

                            except Exception as e:
                                err_msg = f"❌ **Error during agent execution:** {str(e)}"
                                st.error(err_msg)
                                st.session_state.messages.append({"role": "assistant", "content": err_msg})

                    else:
                        # Document RAG Only Mode
                        if st.session_state.doc_store_manager.count_documents() == 0:
                            warn_msg = "📂 **No documents indexed yet.** Upload files in **Knowledge Base Hub**."
                            st.warning(warn_msg)
                            st.session_state.messages.append({"role": "assistant", "content": warn_msg})
                        else:
                            with st.spinner("📚 Querying local vector store..."):
                                try:
                                    res = run_rag_pipeline(
                                        question=user_query,
                                        document_store=st.session_state.doc_store_manager.store,
                                        top_k=st.session_state.top_k_docs,
                                        api_key=st.session_state.api_key,
                                    )
                                    answer = res["answer"]
                                    docs = res["documents"]
                                    doc_results = [
                                        {"filename": d.meta.get("filename", "Doc"), "page": d.meta.get("page_number", 1)}
                                        for d in docs
                                    ]
                                    citations_html = format_citations_html(doc_results, [])

                                    badge_html = '<span class="strategy-badge badge-docs">📄 Strategy: Local Document RAG</span>'
                                    st.markdown(badge_html, unsafe_allow_html=True)
                                    st.markdown(answer)
                                    if citations_html:
                                        st.markdown(citations_html, unsafe_allow_html=True)

                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": answer,
                                        "badge_html": badge_html,
                                        "citations_html": citations_html,
                                    })
                                except Exception as e:
                                    err_msg = f"❌ **RAG Error:** {str(e)}"
                                    st.error(err_msg)
                                    st.session_state.messages.append({"role": "assistant", "content": err_msg})


# =============================================================================
# TAB 2: KNOWLEDGE BASE HUB
# =============================================================================
with tab_kb:
    st.markdown("### 📚 Knowledge Base & Ingestion Inspector")
    st.write("Manage your uploaded files, view indexed chunk counts, and inspect raw vector snippets.")

    k_col1, k_col2 = st.columns([1, 1])

    with k_col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 📥 Document Upload Dropzone")
        kb_files = st.file_uploader(
            "Batch upload PDF, TXT, or DOCX documents",
            type=["pdf", "txt", "docx"],
            accept_multiple_files=True,
            key="kb_dropzone",
        )

        if st.button("🚀 Process Knowledge Base", key="kb_process_btn"):
            if not kb_files:
                st.warning("Please attach files to process.")
            else:
                total_c = 0
                added_f = []
                p_bar = st.progress(0)

                for idx, kf in enumerate(kb_files):
                    if kf.name in st.session_state.indexed_files:
                        continue
                    chunks, c_cnt = process_uploaded_file(kf)
                    if chunks:
                        st.session_state.doc_store_manager.write_documents(chunks)
                        total_c += c_cnt
                        added_f.append(kf.name)
                        st.session_state.indexed_chunks_preview.extend(chunks[:3])
                    p_bar.progress((idx + 1) / len(kb_files))

                p_bar.empty()
                if added_f:
                    st.session_state.indexed_files.extend(added_f)
                    st.session_state.doc_count = st.session_state.doc_store_manager.count_documents()
                    st.session_state.chunk_count += total_c
                    st.success(f"Successfully indexed {len(added_f)} file(s) ({total_c} vector chunks).")
        st.markdown('</div>', unsafe_allow_html=True)

    with k_col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 📄 Indexed Document List")
        if st.session_state.indexed_files:
            for fname in st.session_state.indexed_files:
                ext = Path(fname).suffix.upper().lstrip(".")
                icon = "📕" if ext == "PDF" else "📝" if ext == "TXT" else "📘"
                st.markdown(f"- {icon} **`{fname}`** &nbsp; *(Status: Indexed in InMemoryStore)*")
        else:
            st.info("No files in knowledge base.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🔍 Chunk Preview Inspector")
    if st.session_state.indexed_chunks_preview:
        for i, doc in enumerate(st.session_state.indexed_chunks_preview[:6]):
            with st.expander(f"Chunk #{i+1} — {doc.meta.get('filename', 'Doc')} (Page {doc.meta.get('page_number', 1)})"):
                st.code(doc.content, language="markdown")
    else:
        st.info("Upload documents to inspect vector chunks here.")


# =============================================================================
# TAB 3: SETTINGS & CONFIGURATION
# =============================================================================
with tab_settings:
    st.markdown("### ⚙️ System Settings & Model Configuration")

    s_col1, s_col2 = st.columns(2)

    with s_col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 🔑 API Keys")
        g_key = st.text_input(
            "Gemini API Key",
            value=st.session_state.api_key,
            type="password",
            help="Get free key at https://aistudio.google.com",
            key="settings_gkey",
        )
        if g_key != st.session_state.api_key:
            st.session_state.api_key = g_key
            st.success("Updated Gemini API Key!")

        t_key = st.text_input(
            "Tavily Search API Key (Optional)",
            value=st.session_state.tavily_key,
            type="password",
            help="Optional. If omitted, DuckDuckGo search is used automatically.",
            key="settings_tkey",
        )
        if t_key != st.session_state.tavily_key:
            st.session_state.tavily_key = t_key
            st.success("Updated Tavily API Key!")
        st.markdown('</div>', unsafe_allow_html=True)

    with s_col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 🎛️ Agent & Retrieval Hyperparameters")
        st.session_state.top_k_docs = st.slider(
            "Vector Retrieval Top-K (Document Chunks)",
            min_value=1,
            max_value=10,
            value=st.session_state.top_k_docs,
            help="Number of document chunks to retrieve per search.",
            key="top_k_slider",
        )

        st.session_state.max_web_results = st.slider(
            "Max Web Search Results",
            min_value=1,
            max_value=10,
            value=st.session_state.max_web_results,
            help="Number of web pages to retrieve per query.",
            key="web_results_slider",
        )
        st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# TAB 4: SYSTEM ANALYTICS
# =============================================================================
with tab_analytics:
    st.markdown("### 📊 System Architecture & Metrics")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Indexed Documents", len(st.session_state.indexed_files))
    m2.metric("Total Vector Chunks", st.session_state.doc_count)
    m3.metric("Chat Messages", len(st.session_state.messages))
    m4.metric("Embedding Model", "MiniLM-L6-v2")

    st.markdown("---")
    st.markdown("#### 🏗️ Pipeline Flow Architecture")
    st.markdown("""
    ```mermaid
    graph TD
        User[User Question] --> Agent{Research Agent Router}
        Agent -->|Document Intent / Hybrid| DocTool[Document Retrieval Tool]
        Agent -->|Web Intent / Hybrid| WebTool[Web Search Tool]
        
        DocTool --> DocStore[(InMemory Vector Store)]
        WebTool --> WebSearch[Tavily / DuckDuckGo]
        
        DocStore --> Synthesis[Context Aggregator]
        WebSearch --> Synthesis
        
        Synthesis --> Gemini[Gemini LLM Component]
        Gemini --> Response[Final Answer + Sources UI]
    ```
    """)
