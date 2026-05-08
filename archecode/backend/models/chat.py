"""
Chat and conversation data models.
Defines structures for AI chat interactions with project context.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Role of a chat message participant."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class CodeReference(BaseModel):
    """A reference to a specific code location in a chat response."""
    file_path: str
    line_start: int
    line_end: Optional[int] = None
    description: Optional[str] = None


class ChatMessage(BaseModel):
    """A single chat message."""
    id: str
    role: MessageRole
    content: str
    code_references: list[CodeReference] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Request to send a chat message."""
    project_id: str
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from the AI chat."""
    message: ChatMessage
    conversation_id: str
    context_files: list[str] = []


class Conversation(BaseModel):
    """A chat conversation about a project."""
    id: str
    project_id: str
    messages: list[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
