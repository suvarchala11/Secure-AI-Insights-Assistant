"""
Document Tools — secure FAISS semantic search over internal PDFs.

The LLM receives only the top-k relevant chunks,
never the full document corpus.
"""
import logging
from backend.data_loader import get_vector_store

log = logging.getLogger(__name__)


def search_internal_docs(query: str, top_k: int = 4) -> str:
    """
    Semantic search over internal company documents
    (quarterly reports, campaign summaries, policy guidelines, etc.)

    Returns the most relevant text chunks — never full documents.
    Source: docs/*.txt (FAISS vector index)
    """
    try:
        vs = get_vector_store()
        docs = vs.similarity_search(query, k=top_k)

        if not docs:
            return "No relevant internal documents found for this query."

        results = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "internal document")
            # Strip full path for security — show filename only
            source = source.split("/")[-1].split("\\")[-1]
            results.append(
                f"[Source {i}: {source}]\n{doc.page_content.strip()}"
            )

        log.info(f"[Tool] search_internal_docs(query='{query}', hits={len(docs)})")
        return "\n\n---\n\n".join(results)
    except Exception as e:
        log.error(f"[Tool Error] search_internal_docs: {e}")
        return f"Error searching documents: {str(e)}"
