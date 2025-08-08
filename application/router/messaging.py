from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime # Added for timestamp updates

from application.database.database import get_db
from application.database import crud, models # Assuming messaging CRUD will be added here, added models
from application.database.models import User # Import User model for dependency
# Import MessageCreate along with other messaging schemas
from application.schemas import (
    Conversation, ConversationCreate, Message, MessageCreate,
    InitiateConversationRequest, InitiateConversationResponse, ConversationInboxItem # Added new schemas
)

from application.security import get_current_active_user as get_current_user # Import centralized authentication dependency

router = APIRouter(tags=["messaging"]) # No prefix here, main app.py will add /api

@router.post("/messages/conversations", response_model=Conversation, status_code=status.HTTP_201_CREATED) # Changed prefix to /messages
def create_conversation_only( # Renamed to avoid confusion with the new endpoint
    conversation_create: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initiate a new conversation (without an initial message).
    This is kept separate in case there's a use case for creating a conversation
    without an immediate message, though the new initiate_conversation endpoint is preferred for UI flows.
    """
    # Ensure the current user is one of the participants
    if current_user.user_id not in [conversation_create.user1_id, conversation_create.user2_id]:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create conversations you are a part of."
        )

    # Prevent creating a conversation with oneself
    if conversation_create.user1_id == conversation_create.user2_id:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a conversation with yourself."
        )

    # Check if a conversation between these two users for this listing already exists
    existing_conversation = crud.get_conversation_by_users_and_listing(
        db,
        conversation_create.user1_id,
        conversation_create.user2_id,
        conversation_create.listing_id
    )
    if existing_conversation:
        return existing_conversation

    # Create the new conversation
    db_conversation = crud.create_conversation(
        db,
        user1_id=conversation_create.user1_id,
        user2_id=conversation_create.user2_id,
        listing_id=conversation_create.listing_id
    )
    return db_conversation

@router.post("/messages/initiate_conversation", response_model=InitiateConversationResponse, status_code=status.HTTP_201_CREATED)
def initiate_conversation_with_message(
    request_data: InitiateConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initiates a conversation with a user regarding a specific listing and sends an initial message.
    If a conversation already exists between the two users for this listing,
    the message is added to the existing conversation.
    """
    if current_user.user_id == request_data.recipient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot start a conversation with yourself."
        )

    # Check for existing conversation or create a new one
    # crud.get_conversation_by_users_and_listing should handle user1_id/user2_id order internally
    conversation = crud.get_conversation_by_users_and_listing(
        db,
        user1_id=current_user.user_id,
        user2_id=request_data.recipient_id,
        listing_id=request_data.listing_id
    )

    if not conversation:
        conversation = crud.create_conversation(
            db,
            user1_id=current_user.user_id,
            user2_id=request_data.recipient_id,
            listing_id=request_data.listing_id
        )
        # If create_conversation doesn't commit and refresh, we might need to fetch it again or ensure it returns the full object.
        # Assuming crud.create_conversation returns the persisted Conversation object.

    # Create the initial message
    new_message = crud.create_message(
        db,
        conversation_id=conversation.conversation_id,
        sender_id=current_user.user_id,
        content=request_data.initial_message
    )

    # Update conversation's updated_at timestamp
    # This requires the 'conversation' object to be a SQLAlchemy model instance
    db_conversation_instance = db.query(models.Conversation).filter(models.Conversation.conversation_id == conversation.conversation_id).first()
    if db_conversation_instance:
        db_conversation_instance.updated_at = datetime.utcnow()
        db.add(db_conversation_instance) # Mark as dirty
        db.commit()
        db.refresh(db_conversation_instance) # Refresh to get updated state if needed elsewhere
    else:
        # This should ideally not happen if conversation was just created/fetched
        # Log an error or raise an exception if critical
        pass

    return InitiateConversationResponse(
        conversation_id=conversation.conversation_id,
        message_id=new_message.message_id
    )

@router.get("/messages/conversations", response_model=List[ConversationInboxItem]) # Changed prefix to /messages
def get_user_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all conversations for the current user.
    """
    conversations = crud.get_conversations_for_user(db, current_user.user_id)
    return conversations

@router.get("/messages/conversations/{conversation_id}", response_model=Conversation) # Path updated to match frontend, response model is single Conversation
def get_conversation_detail( # New function to get a single conversation's details
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get details for a specific conversation.
    """
    conversation = crud.get_conversation_by_id(db, conversation_id=conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found."
        )
    
    # Verify that the current user is part of this conversation
    if current_user.user_id not in [conversation.user1_id, conversation.user2_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this conversation."
        )
    
    return conversation

@router.get("/messages/conversations/{conversation_id}/messages", response_model=List[Message]) # Added /messages prefix
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all messages within a specific conversation thread.
    """
    # Verify that the current user is part of this conversation
    conversation = db.query(models.Conversation).filter(models.Conversation.conversation_id == conversation_id).first()
    if not conversation or current_user.user_id not in [conversation.user1_id, conversation.user2_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this conversation."
        )

    messages = crud.get_messages_for_conversation(db, conversation_id)
    return messages

@router.post("/messages/conversations/{conversation_id}/messages", response_model=Message, status_code=status.HTTP_201_CREATED) # Added /messages prefix
def send_message(
    conversation_id: int,
    message_create: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a new message within a conversation thread.
    """
    # Verify that the current user is part of this conversation
    conversation = db.query(models.Conversation).filter(models.Conversation.conversation_id == conversation_id).first()
    if not conversation or current_user.user_id not in [conversation.user1_id, conversation.user2_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this conversation."
        )

    # Create the new message using the CRUD function
    db_message = crud.create_message(
        db,
        conversation_id=conversation_id,
        sender_id=current_user.user_id,
        content=message_create.content
    )

    # Optional: Update conversation's updated_at timestamp
    conversation.updated_at = datetime.utcnow()
    db.commit()

    return db_message