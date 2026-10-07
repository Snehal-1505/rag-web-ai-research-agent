"""
Unit tests for Basic RAG Pipeline (Phase 5)
"""
import pytest
from haystack import Document, component, Pipeline

from src.rag.document_store import DocumentStoreManager
from src.ingestion.indexer import generate_document_embeddings
from src.rag.prompt import get_prompt_builder
from src.rag.pipeline import create_rag_pipeline, run_rag_pipeline


@component
class MockLLMGenerator:
    """Mock LLM component for deterministic offline unit testing."""

    @component.output_types(replies=list)
    def run(self, prompt: str):
        return {"replies": [f"Mock Response for prompt length {len(prompt)}"]}


def test_prompt_builder():
    """Test PromptBuilder template rendering with question and context documents."""
    builder = get_prompt_builder()
    docs = [
        Document(content="Haystack AI is a framework for building RAG applications.", meta={"filename": "doc1.txt", "page_number": 1}),
        Document(content="Vector search enables fast semantic document retrieval.", meta={"filename": "doc2.txt", "page_number": 2}),
    ]
    res = builder.run(question="What is Haystack?", documents=docs)
    prompt = res["prompt"]

    assert "You are an AI research assistant." in prompt
    assert "What is Haystack?" in prompt
    assert "Haystack AI is a framework" in prompt
    assert "doc1.txt" in prompt


def test_rag_pipeline_flow():
    """Test full pipeline data flow connecting Embedder -> Retriever -> Prompt -> LLM."""
    manager = DocumentStoreManager()
    
    docs = [
        Document(
            content="Haystack 2.0 provides pipelines to connect embedders, retrievers, and LLMs.",
            meta={"filename": "haystack_pipeline.txt", "file_type": "txt", "page_number": 1}
        )
    ]
    embedded_docs = generate_document_embeddings(docs)
    manager.write_documents(embedded_docs)

    pipeline = create_rag_pipeline(
        document_store=manager.store,
        top_k=1,
        llm_component=MockLLMGenerator(),
    )

    res = pipeline.run(
        {
            "text_embedder": {"text": "How do Haystack pipelines work?"},
            "prompt_builder": {"question": "How do Haystack pipelines work?"},
        },
        include_outputs_from={"retriever"}
    )

    replies = res["llm"]["replies"]
    retrieved_docs = res["retriever"]["documents"]

    assert len(replies) == 1
    assert "Mock Response" in replies[0]
    assert len(retrieved_docs) == 1
    assert retrieved_docs[0].meta["filename"] == "haystack_pipeline.txt"


def test_missing_api_key_graceful_handling():
    """Test that missing GEMINI_API_KEY returns a clear warning instead of crashing."""
    manager = DocumentStoreManager()
    
    res = run_rag_pipeline(
        question="Test query",
        document_store=manager.store,
        api_key="",  # Empty API key
    )

    assert "Gemini API key is missing" in res["answer"]
