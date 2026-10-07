"""
Phase 1 Verification Script: Test Haystack AI Installation & Basic DocumentStore
"""
import sys
from haystack import Document, Pipeline
from haystack.document_stores.in_memory import InMemoryDocumentStore

def test_haystack_setup():
    print("=" * 50)
    print("Testing Haystack AI Installation...")
    print(f"Python Version: {sys.version}")
    
    # 1. Initialize InMemoryDocumentStore
    doc_store = InMemoryDocumentStore()
    print("[OK] InMemoryDocumentStore initialized successfully.")
    
    # 2. Write test document
    test_doc = Document(
        content="Haystack 2.0 is an open-source AI framework for building RAG applications.",
        meta={"source": "test_script", "page": 1}
    )
    doc_store.write_documents([test_doc])
    
    # 3. Retrieve document count
    stored_count = doc_store.count_documents()
    print(f"[OK] Document written. Total documents in store: {stored_count}")
    
    assert stored_count == 1, "Document store should contain 1 document."
    print("[OK] Phase 1 Haystack verification passed!")
    print("=" * 50)

if __name__ == "__main__":
    test_haystack_setup()
