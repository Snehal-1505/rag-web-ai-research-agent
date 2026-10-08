"""
Research Agent Module
Implements Haystack Agent / Router logic for hybrid RAG + Web AI research.
"""
from typing import List, Dict, Any, Optional
from haystack import Document

from src.agent.tools import document_search_func, web_search_func
from src.llm.generator import GeminiGenerator


class ResearchAgent:
    """
    Intelligent AI Agent that routes questions between local document search and web search,
    synthesizing an authoritative answer with full source citations.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.generator = GeminiGenerator(api_key=api_key)

    def determine_search_strategy(self, question: str, has_documents: bool) -> str:
        """
        Determines search strategy based on question content and document availability.

        Returns one of: 'documents', 'web', 'hybrid'
        """
        if not has_documents:
            return "web"

        q_lower = question.lower()

        # Keywords indicating web-specific intent
        web_keywords = ["latest", "recent", "today", "current", "news", "weather", "stock", "price", "who is", "what is happening", "browse"]
        if any(kw in q_lower for kw in web_keywords) and not any(kw in q_lower for kw in ["my doc", "file", "pdf", "uploaded"]):
            return "web"

        # Keywords indicating document-specific intent
        doc_keywords = ["my document", "in the pdf", "uploaded file", "summary of doc", "this text", "the file", "according to my doc"]
        if any(kw in q_lower for kw in doc_keywords):
            return "documents"

        # Default to hybrid search when documents are present for comprehensive research
        return "hybrid"

    def run(
        self,
        question: str,
        document_store,
        top_k_docs: int = 5,
        max_web_results: int = 5,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Executes the agent workflow:
        1. Determines search strategy (documents, web, or hybrid)
        2. Gathers document and/or web context
        3. Synthesizes final response via Gemini
        4. Returns answer and source metadata

        Args:
            question: User's query string.
            document_store: InMemoryDocumentStore instance.
            top_k_docs: Number of document chunks to retrieve.
            max_web_results: Number of web results to retrieve.

        Returns:
            Dict containing 'answer', 'strategy', 'doc_results', and 'web_results'.
        """
        has_docs = document_store is not None and document_store.count_documents() > 0
        strategy = self.determine_search_strategy(question, has_documents=has_docs)

        doc_results: List[Dict[str, Any]] = []
        web_results: List[Dict[str, Any]] = []

        if strategy in ("documents", "hybrid") and has_docs:
            doc_results = document_search_func(query=question, document_store=document_store, top_k=top_k_docs)

        if strategy in ("web", "hybrid"):
            web_results = web_search_func(query=question, max_results=max_web_results)

        # Build context for LLM prompt
        context_parts = []

        if doc_results:
            context_parts.append("=== LOCAL DOCUMENT CONTEXT ===")
            for i, d in enumerate(doc_results, 1):
                if "content" in d:
                    context_parts.append(f"[{i}] Document: {d.get('filename')} (Page {d.get('page')})\nContent: {d.get('content')}")

        if web_results:
            context_parts.append("\n=== WEB SEARCH CONTEXT ===")
            for i, w in enumerate(web_results, 1):
                if "content" in w:
                    context_parts.append(f"[{i}] Web Page: {w.get('title')} ({w.get('url')})\nSnippet: {w.get('content')}")

        full_context = "\n\n".join(context_parts) if context_parts else "No background search context available."

        # Prompt construction — uses system instructions passed from caller
        system_instr = kwargs.get("system_prompt", """You are an intelligent AI Research Assistant.

Answer questions clearly based on the retrieved context below. Choose the best format automatically:
- Short paragraph for simple questions
- Numbered steps for procedures / how-to questions
- Bullet list for advantages, lists, features
- Comparison table for X vs Y questions
- Structured sections (## Short Answer, ## Key Findings, ## Explanation) for complex research
- Simple plain language for beginner/explain-simply questions
- Code blocks for programming questions

Keep answers concise. Do not include source URLs or citations unless explicitly asked.
Do not mention Haystack, vector stores, embeddings, or other backend details.""")

        prompt = f"""{system_instr}

Retrieved Context:
{full_context}

User Question: {question}

Answer:"""

        # Generate answer using GeminiGenerator component
        gen_output = self.generator.run(prompt=prompt)
        answer = gen_output.get("replies", ["No response generated."])[0]

        return {
            "question": question,
            "answer": answer,
            "strategy": strategy,
            "doc_results": doc_results,
            "web_results": web_results,
        }
