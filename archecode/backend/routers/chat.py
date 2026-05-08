"""
Chat API endpoints.
Handles AI-powered Q&A about projects with context awareness.
"""

import uuid
from fastapi import APIRouter, HTTPException

from models.chat import ChatRequest, ChatResponse, ChatMessage, Conversation, MessageRole
from services.ai_service import ai_service
from services.project_service import project_service

router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory conversation store
_conversations: dict[str, Conversation] = {}


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message to the AI about a project."""
    project = await project_service.get_project(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get or create conversation
    conversation_id = request.conversation_id
    if conversation_id and conversation_id in _conversations:
        conversation = _conversations[conversation_id]
    else:
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            project_id=request.project_id,
        )

    # Add user message
    user_message = ChatMessage(
        id=str(uuid.uuid4()),
        role=MessageRole.USER,
        content=request.message,
    )
    conversation.messages.append(user_message)

    # Get AI response
    if not ai_service.is_configured():
        assistant_message = ChatMessage(
            id=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            content=(
                "AI chat is not available. Please configure OPENAI_API_KEY in the backend "
                "environment to enable AI-powered analysis.\n\n"
                "In the meantime, here's what I can tell you about the project:\n\n"
                f"**{project.name}** is a "
                f"{project.metadata.project_type.value.replace('_', ' ') if project.metadata else 'unknown'} "
                f"project using "
                f"{', '.join(t.name for t in project.metadata.tech_stack) if project.metadata else 'unknown technologies'}.\n\n"
                f"It has {project.metadata.total_files if project.metadata else 0} files "
                f"with {project.metadata.total_lines if project.metadata else 0:,} total lines of code."
            ),
        )
    else:
        assistant_message = await ai_service.chat_with_context(
            project=project,
            question=request.message,
            history=conversation.messages[:-1],  # Exclude the just-added user message
        )
        assistant_message.id = str(uuid.uuid4())

    conversation.messages.append(assistant_message)
    _conversations[conversation_id] = conversation

    return ChatResponse(
        message=assistant_message,
        conversation_id=conversation_id,
    )


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a conversation by ID."""
    conversation = _conversations.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/conversations/project/{project_id}")
async def get_project_conversations(project_id: str):
    """Get all conversations for a project."""
    conversations = [
        c for c in _conversations.values() if c.project_id == project_id
    ]
    return {"conversations": conversations}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    if conversation_id in _conversations:
        del _conversations[conversation_id]
    return {"message": "Conversation deleted"}


@router.get("/suggestions/{project_id}")
async def get_suggested_questions(project_id: str):
    """Get suggested questions for a project."""
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Generate contextual suggestions based on project type and structure
    suggestions = [
        f"What is {project.name} and what does it do?",
        "What is the overall architecture of this project?",
        "What are the main entry points of the application?",
    ]

    if project.metadata:
        if project.metadata.has_tests:
            suggestions.append("What testing framework is used and how are tests organized?")
        if project.metadata.has_docker:
            suggestions.append("How is the project containerized?")
        if project.metadata.tech_stack:
            tech_names = [t.name for t in project.metadata.tech_stack[:3]]
            suggestions.append(f"What are the key dependencies ({', '.join(tech_names)}) and how are they used?")

    suggestions.extend([
        "Are there any security vulnerabilities in this codebase?",
        "What are the main technical debt issues?",
        "What refactoring would you recommend?",
    ])

    return {"suggestions": suggestions[:8]}
