import os
from crewai_tools import PDFSearchTool

# Create a fresh RAG tool for each PDF
def create_pdf_rag_tool():
    rag_tool = PDFSearchTool(
        config=dict(
            llm=dict(
                provider="google",
                config=dict(
                    model="gemini/gemini-2.0-flash-lite"
                ),
            ),
            embedder=dict(
                provider="google",
                config=dict(
                    model="text-embedding-004",  # or "text-embedding-preview-0409"
                    task_type="retrieval_document"
                    )
                )
            )
        )
    return rag_tool