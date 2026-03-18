"""
EduScout Document Analyst Agent
RAG tool that queries Gradient Knowledge Bases for school documents.

Uses the Gradient Python SDK to retrieve relevant document chunks
from indexed school PDFs (regulations, study plans, policies).

Prerequisites:
1. Upload PDFs to DO Spaces bucket (eduscout-docs)
2. Create Knowledge Base in DO Control Panel pointing to that bucket
3. Set KNOWLEDGE_BASE_ID in .env
"""

import os
import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger("eduscout.document_analyst")


def _get_gradient_client():
    """Get the Gradient Python SDK client."""
    try:
        from gradient import Gradient
        return Gradient()
    except ImportError:
        logger.error("gradient SDK not installed. Run: pip install gradient")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Gradient client: {e}")
        return None


@tool
def search_school_documents(
    query: str,
    num_results: int = 5,
) -> str:
    """Search school documents (regulations, policies, study plans) using RAG.

    Use this tool when a parent asks about:
    - School regulations or policies (dress code, behavior, attendance)
    - Admission requirements or enrollment procedures
    - Curriculum details or study plans
    - Special needs accommodations documented in school policy
    - Any question that might be answered by official school documents

    Args:
        query: The question to search for in school documents.
               Be specific. Examples:
               - "ADHD accommodations policy Trinity School"
               - "dress code regulations Stuyvesant"
               - "admission requirements IDEAL School"
               - "wheelchair accessibility policy"
        num_results: Number of document chunks to retrieve (default 5, max 10).
    """
    kb_id = os.environ.get("KNOWLEDGE_BASE_ID", "")

    if not kb_id:
        return (
            "Knowledge Base is not configured yet. "
            "I can only answer from our structured database for now. "
            "Document-based answers will be available soon."
        )

    client = _get_gradient_client()
    if not client:
        return "Unable to connect to the document system. Please try again."

    try:
        num_results = min(max(num_results, 1), 10)

        response = client.retrieve.documents(
            knowledge_base_id=kb_id,
            num_results=num_results,
            query=query,
        )

        if not response or not response.results:
            return (
                f"No relevant documents found for: '{query}'. "
                "This might mean we don't have that specific document indexed yet. "
                "I can try answering from our school database instead."
            )

        # Format results with source attribution
        output = f"Found {len(response.results)} relevant document sections:\n\n"

        for i, result in enumerate(response.results, 1):
            logger.debug(f"Result object attributes ===============================================================: {vars(result)}")
            content = result.text_content.strip() if result.text_content else ""
            score = getattr(result, "score", None)
            source = getattr(result, "source", None) or getattr(result, "metadata", {})

            # Extract source filename if available
            source_name = ""
            if isinstance(source, dict):
                source_name = source.get("filename", source.get("source", ""))
            elif isinstance(source, str):
                source_name = source

            output += f"--- Document {i}"
            if source_name:
                output += f" (Source: {source_name})"
            if score is not None:
                output += f" [Relevance: {score:.2f}]"
            output += " ---\n"
            output += f"{content}\n\n"

        output += (
            "\nIMPORTANT: Cite the source document when sharing this information "
            "with the parent. Say 'According to [school name]'s [document type]...'"
        )

        return output

    except Exception as e:
        logger.exception(f"RAG query error: {e}")
        return f"Error searching documents: {str(e)}. I'll answer from our database instead."


# Export
document_analyst_tools = [search_school_documents]
