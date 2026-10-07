"""
Complete RAG Pipeline Module for Haystack AI Application.

Connects:
1. SentenceTransformersTextEmbedder ->
2. InMemoryEmbeddingRetriever ->
3. PromptBuilder ->
4. GeminiGenerator LLM
"""
from typing import Dict, Any, List, Optional
from haystack import Pipeline
from haystack.document_stores.in_memory import InMemoryDocumentStore

from src.ingestion.indexer import get_text_embedder
from src.rag.retriever import get_retriever
from src.rag.prompt import get_prompt_builder
from src.llm.generator import GeminiGenerator


def create_rag_pipeline(
    document_store: InMemoryDocumentStore,
    top_k: int = 5,
    api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-flash",
    llm_component: Optional[Any] = None,
) -> Pipeline:
    """
    Assembles and returns a complete Haystack RAG Pipeline.

    Args:
        document_store: Active Haystack document store.
        top_k: Number of documents to retrieve.
        api_key: Optional Gemini API key.
        model_name: Gemini model name.
        llm_component: Optional custom LLM component (useful for testing or swapping LLMs).

    Returns:
        Configured Haystack Pipeline instance.
    """
    pipeline = Pipeline()

    # 1. Add components
    text_embedder = get_text_embedder()
    retriever = get_retriever(document_store=document_store, top_k=top_k)
    prompt_builder = get_prompt_builder()
    llm = llm_component if llm_component is not None else GeminiGenerator(api_key=api_key, model_name=model_name)

    pipeline.add_component("text_embedder", text_embedder)
    pipeline.add_component("retriever", retriever)
    pipeline.add_component("prompt_builder", prompt_builder)
    pipeline.add_component("llm", llm)

    # 2. Connect components
    pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
    pipeline.connect("retriever.documents", "prompt_builder.documents")
    pipeline.connect("prompt_builder.prompt", "llm.prompt")

    return pipeline


def run_rag_pipeline(
    question: str,
    document_store: InMemoryDocumentStore,
    top_k: int = 5,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes RAG Pipeline for a given question.

    Returns dict with:
        - "answer": LLM generated text answer
        - "documents": List of retrieved Haystack Document objects used as context
    """
    pipeline = create_rag_pipeline(
        document_store=document_store,
        top_k=top_k,
        api_key=api_key,
    )

    results = pipeline.run(
        {
            "text_embedder": {"text": question},
            "prompt_builder": {"question": question},
        },
        include_outputs_from={"retriever"}
    )

    replies = results.get("llm", {}).get("replies", [])
    retrieved_docs = results.get("retriever", {}).get("documents", [])

    answer = replies[0] if replies else "No answer generated."

    return {
        "answer": answer,
        "documents": retrieved_docs,
    }
