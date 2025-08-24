import os
from crewai_tools import PDFSearchTool


PDF_tool = PDFSearchTool(
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