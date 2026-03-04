"""
Chat API Routes

Natural language interface for querying carbon emissions.
"""
from __future__ import annotations

from fastapi import APIRouter

from chatbot.chat_engine import chat
from models import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Ask a natural language question about your carbon emissions.

    Example queries:
    - "What was our carbon footprint last month?"
    - "Which department produced the most emissions?"
    - "How can we reduce emissions by 20%?"
    - "Compare emissions between January and February"
    """
    result = chat(request.message)
    return ChatResponse(
        answer=result["answer"],
        data=result.get("data"),
    )
