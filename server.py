"""
Loomi AI — FastAPI Backend Adapter
Exposes typed REST endpoints and SSE streaming for the React/Vite frontend.
Directly reuses existing ChromaDB, SQLite, Haystack pipelines, and Gemini integrations.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# ── Ensure project root in sys.path ──────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.config import (
    UPLOADS_DIR, SQLITE_DB_PATH, CHROMA_DB_DIR,
    GEMINI_API_KEY, TAVILY_API_KEY
)
from src.database.chat_database import ChatDatabase
from src.rag.chroma_store import get_chroma_store
from src.agent.research_agent import ResearchAgent
from src.ingestion.document_loader import load_document
from src.ingestion.chunker import chunk_documents
from src.ingestion.indexer import generate_document_embeddings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("loomi-api")

# ── App & Singletons ──────────────────────────────────────────────────────────
app = FastAPI(
    title="Loomi AI API",
    description="Backend API adapter for Loomi AI research assistant",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if frontend_origin and frontend_origin not in allowed_origins:
    allowed_origins.append(frontend_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_db = ChatDatabase(SQLITE_DB_PATH)
chroma_store = get_chroma_store()
agent = ResearchAgent()


# ── Pydantic Request / Response Schemas ────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    indexed_documents: int
    indexed_files: List[str]
    gemini_configured: bool
    tavily_configured: bool


class SessionCreateRequest(BaseModel):
    title: Optional[str] = "New Chat"


class SessionUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)


class SessionItem(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0


class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class SessionDetailResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[MessageItem]


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    question: str = Field(..., min_length=1)
    top_k_docs: Optional[int] = 5
    max_web_results: Optional[int] = 5


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    strategy: str
    sources: Dict[str, List[Any]]


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str


# ── 1. Health & Stats ─────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
def get_health():
    """Health check and high-level knowledge base stats."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        indexed_documents=chroma_store.count_documents(),
        indexed_files=chroma_store.get_indexed_filenames(),
        gemini_configured=bool(GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")),
        tavily_configured=bool(TAVILY_API_KEY or os.getenv("TAVILY_API_KEY")),
    )


# ── 2. Chat Sessions ──────────────────────────────────────────────────────────

@app.get("/api/sessions", response_model=List[SessionItem])
def list_sessions():
    """Lists all conversation sessions ordered by most recently updated."""
    convs = chat_db.list_conversations()
    results = []
    for c in convs:
        count = chat_db.count_messages(c["id"])
        results.append(
            SessionItem(
                id=c["id"],
                title=c["title"],
                created_at=c["created_at"],
                updated_at=c["updated_at"],
                message_count=count,
            )
        )
    return results


@app.post("/api/sessions", response_model=SessionItem, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreateRequest):
    """Creates a new chat session."""
    conv_id = chat_db.create_conversation(title=payload.title or "New Chat")
    convs = chat_db.list_conversations()
    target = next((c for c in convs if c["id"] == conv_id), None)
    if not target:
        raise HTTPException(status_code=500, detail="Failed to create session.")
    return SessionItem(
        id=target["id"],
        title=target["title"],
        created_at=target["created_at"],
        updated_at=target["updated_at"],
        message_count=0,
    )


@app.get("/api/sessions/{session_id}", response_model=SessionDetailResponse)
def get_session(session_id: str):
    """Loads a conversation and all its messages in chronological order."""
    convs = chat_db.list_conversations()
    target = next((c for c in convs if c["id"] == session_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Session not found.")

    raw_messages = chat_db.load_messages(session_id)
    messages = [
        MessageItem(
            id=m["id"],
            role=m["role"],
            content=m["content"],
            timestamp=m["timestamp"],
            metadata=m.get("metadata") or {},
        )
        for m in raw_messages
    ]

    return SessionDetailResponse(
        id=target["id"],
        title=target["title"],
        created_at=target["created_at"],
        updated_at=target["updated_at"],
        messages=messages,
    )


@app.patch("/api/sessions/{session_id}", response_model=SessionItem)
def update_session(session_id: str, payload: SessionUpdateRequest):
    """Renames an existing session."""
    convs = chat_db.list_conversations()
    target = next((c for c in convs if c["id"] == session_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Session not found.")

    chat_db.rename_conversation(session_id, payload.title.strip())
    updated_convs = chat_db.list_conversations()
    updated = next((c for c in updated_convs if c["id"] == session_id), None)
    return SessionItem(
        id=updated["id"],
        title=updated["title"],
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
        message_count=chat_db.count_messages(session_id),
    )


@app.delete("/api/sessions/{session_id}", status_code=status.HTTP_200_OK)
def delete_session(session_id: str):
    """Deletes a conversation session and all its messages."""
    convs = chat_db.list_conversations()
    target = next((c for c in convs if c["id"] == session_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Session not found.")

    chat_db.delete_conversation(session_id)
    return {"message": "Session deleted successfully", "id": session_id}


# ── 3. Chat Generation (Standard JSON) ────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    """
    Standard synchronous chat endpoint. Runs research agent, saves user and assistant
    messages in SQLite, auto-sets session title on first message, and returns answer + sources.
    """
    session_id = payload.session_id
    if not session_id:
        session_id = chat_db.create_conversation()

    # Save user message
    chat_db.save_message(session_id, "user", payload.question)
    chat_db.set_title_from_first_message(session_id, payload.question)

    # Run agent
    try:
        result = agent.run(
            question=payload.question,
            document_store=chroma_store,
            top_k_docs=payload.top_k_docs or 5,
            max_web_results=payload.max_web_results or 5,
        )
        answer = result.get("answer", "I couldn't generate a response.")
        strategy = result.get("strategy", "unknown")
        doc_results = result.get("doc_results", [])
        web_results = result.get("web_results", [])
    except Exception as e:
        logger.error(f"Chat generation error: {e}", exc_info=True)
        answer = "Something went wrong while generating the answer. Please try again."
        strategy = "error"
        doc_results = []
        web_results = []

    # Save assistant message with metadata
    meta = {
        "strategy": strategy,
        "doc_results": doc_results,
        "web_results": web_results,
    }
    chat_db.save_message(session_id, "assistant", answer, metadata=meta)

    return ChatResponse(
        session_id=session_id,
        answer=answer,
        strategy=strategy,
        sources={"documents": doc_results, "web": web_results},
    )


# ── 4. Chat Generation (SSE Streaming) ────────────────────────────────────────

@app.post("/api/chat/stream")
def chat_stream_endpoint(payload: ChatRequest):
    """
    Real Server-Sent Events (SSE) streaming endpoint.
    Emits events:
      - 'status': {"stage": "searching"|"generating", "strategy": "..."}
      - 'sources': {"strategy": "...", "doc_results": [...], "web_results": [...]}
      - 'delta': {"text": "..."}
      - 'done': {"session_id": "...", "full_answer": "..."}
    """
    session_id = payload.session_id
    if not session_id:
        session_id = chat_db.create_conversation()

    # Save user message & set initial title
    chat_db.save_message(session_id, "user", payload.question)
    chat_db.set_title_from_first_message(session_id, payload.question)

    def event_generator():
        accumulated_chunks = []
        doc_results = []
        web_results = []
        strategy = "hybrid"

        # Emit initial session metadata
        yield f"event: session\ndata: {json.dumps({'session_id': session_id})}\n\n"

        try:
            for event in agent.run_stream(
                question=payload.question,
                document_store=chroma_store,
                top_k_docs=payload.top_k_docs or 5,
                max_web_results=payload.max_web_results or 5,
            ):
                event_type = event.get("type")
                if event_type == "status":
                    strategy = event.get("strategy", strategy)
                    yield f"event: status\ndata: {json.dumps({'stage': event.get('stage'), 'strategy': strategy})}\n\n"
                elif event_type == "sources":
                    doc_results = event.get("doc_results", [])
                    web_results = event.get("web_results", [])
                    strategy = event.get("strategy", strategy)
                    yield f"event: sources\ndata: {json.dumps({'strategy': strategy, 'doc_results': doc_results, 'web_results': web_results})}\n\n"
                elif event_type == "delta":
                    delta_text = event.get("delta", "")
                    accumulated_chunks.append(delta_text)
                    yield f"event: delta\ndata: {json.dumps({'text': delta_text})}\n\n"
                elif event_type == "done":
                    break

            full_answer = "".join(accumulated_chunks)
            if not full_answer:
                full_answer = "No response was generated. Please try again."

            # Save full assistant message with sources to SQLite
            meta = {
                "strategy": strategy,
                "doc_results": doc_results,
                "web_results": web_results,
            }
            chat_db.save_message(session_id, "assistant", full_answer, metadata=meta)

            yield f"event: done\ndata: {json.dumps({'session_id': session_id, 'full_answer': full_answer})}\n\n"

        except Exception as err:
            logger.error(f"Error during streaming chat: {err}", exc_info=True)
            fallback = "Something went wrong while generating the answer. Please try again."
            chat_db.save_message(session_id, "assistant", fallback)
            yield f"event: error\ndata: {json.dumps({'error': str(err)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── 5. Documents & Knowledge Base ─────────────────────────────────────────────

@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
):
    """
    Uploads a document (PDF, TXT, DOCX), verifies duplicates via SHA-256 hash,
    indexes chunks into ChromaDB, and tracks status in SQLite.
    """
    allowed_exts = {".pdf", ".txt", ".docx"}
    filename = Path(file.filename or "uploaded_file").name
    ext = Path(filename).suffix.lower()

    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Allowed: .pdf, .txt, .docx",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 1. Duplicate check via SHA-256
    file_hash = ChatDatabase.compute_file_hash(file_bytes)
    existing = chat_db.find_document_by_hash(file_hash)
    if existing and existing["status"] == "ready":
        return DocumentUploadResponse(
            document_id=existing["id"],
            filename=filename,
            status="duplicate",
            message=f"'{filename}' is already indexed and ready for retrieval.",
        )

    # 2. Save original file to disk
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    dest_path = UPLOADS_DIR / filename
    dest_path.write_bytes(file_bytes)

    # 3. Register in SQLite with status 'processing'
    doc_id = chat_db.register_document(
        filename=filename,
        stored_path=str(dest_path),
        file_hash=file_hash,
        conversation_id=session_id,
    )
    chat_db.update_document_status(doc_id, "processing")

    # 4. Ingestion & Indexing
    try:
        raw_docs = load_document(dest_path)
        if not raw_docs:
            raise ValueError("No text content could be extracted from document.")

        for doc in raw_docs:
            doc.meta["filename"] = filename
            doc.meta["source"] = filename
            doc.meta["file_hash"] = file_hash
            doc.meta["doc_registry_id"] = doc_id

        chunks = chunk_documents(raw_docs)
        embedded = generate_document_embeddings(chunks, file_hash=file_hash)
        chroma_store.write_documents(embedded)

        chat_db.update_document_status(doc_id, "ready")

        return DocumentUploadResponse(
            document_id=doc_id,
            filename=filename,
            status="ready",
            message=f"'{filename}' successfully processed and indexed into ChromaDB ({len(embedded)} chunks).",
        )

    except Exception as e:
        logger.error(f"Error indexing {filename}: {e}", exc_info=True)
        chat_db.update_document_status(doc_id, "error", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}",
        )


@app.get("/api/documents")
def list_documents():
    """Lists all registered documents and indexed filenames."""
    docs = chat_db.list_documents()
    indexed_files = chroma_store.get_indexed_filenames()
    total_chunks = chroma_store.count_documents()
    return {
        "documents": docs,
        "indexed_filenames": indexed_files,
        "total_chunks": total_chunks,
    }


@app.get("/api/documents/{document_id}/status")
def get_document_status(document_id: str):
    """Polls processing status for an uploaded document."""
    docs = chat_db.list_documents()
    target = next((d for d in docs if d["id"] == document_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {
        "id": target["id"],
        "filename": target["filename"],
        "status": target["status"],
        "error_message": target.get("error_message"),
        "upload_time": target["upload_time"],
    }


# ── 6. Static Files (Production React Build) ───────────────────────────────────
frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.is_dir():
    assets_dir = frontend_dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        # Allow API routes to be handled by FastAPI
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")

        target_file = frontend_dist / full_path
        if full_path and target_file.is_file():
            return FileResponse(target_file)

        index_file = frontend_dist / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)

        raise HTTPException(status_code=404, detail="Not Found")
