from pydantic import BaseModel, Field, computed_field, validator, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

# --- Enums ---
class ItemCondition(str, Enum):
    NEW = "new"
    LIKE_NEW = "like_new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    USED = "used"

class RateType(str, Enum):
    HOURLY = "hourly"
    FIXED = "fixed"

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: str # Reverted from EmailStr to avoid email-validator dependency

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    is_admin: bool = False
    terms_accepted: bool = Field(..., alias="termsAccepted") # Frontend might send as termsAccepted

    @validator('email')
    def email_must_be_sfsu(cls, v):
        if not (v.endswith('@sfsu.edu') or v.endswith('@mail.sfsu.edu')):
            raise ValueError('Email must be a valid SFSU email address (ending in @sfsu.edu or @mail.sfsu.edu)')
        return v.lower() # Normalize email to lowercase

    @validator('terms_accepted')
    def terms_must_be_true(cls, v):
        if not v:
            raise ValueError('You must accept the terms and conditions to register.')
        return v

class UserLogin(BaseModel):
    email: str
    password: str

class UserRead(UserBase):
    user_id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserInDB(UserRead): # Not typically returned directly in API responses but used internally
    hashed_password: str

class UserMinimal(BaseModel):
    user_id: int
    username: Optional[str] = None

    class Config:
        from_attributes = True

# --- Category Schemas ---
class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    parent_id: Optional[int] = None
    display_order: int = 0
    is_active: bool = True
    is_skill_category: bool = False

class Category(CategoryBase):
    category_id: int
    parent_id: Optional[int] = None
    display_order: int
    is_active: bool
    is_skill_category: bool

    class Config:
        from_attributes = True

# --- Listing Image Schemas ---
class ListingImageBase(BaseModel):
    image_path: str
    thumbnail_path: Optional[str] = None
    display_order: int = 0
    is_primary: bool = False

class ListingImageCreate(ListingImageBase):
    pass

class ListingImage(ListingImageBase):
    image_id: int
    listing_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Listing Schemas ---
class ListingBase(BaseModel):
    title: str
    description: str
    search_keywords: Optional[str] = None
    price: Optional[float] = Field(None, gt=0 if Field else 0) # Logic implies Field might not always be used, ensure gt=0 is appropriate
    category_id: int
    item_condition: Optional[ItemCondition] = None
    is_skill_sharing: bool = False
    rate: Optional[float] = Field(None, gt=0 if Field else 0) # Same as price
    rate_type: Optional[RateType] = None
    availability: Optional[str] = None

class ListingCreate(ListingBase):
    pass

class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    search_keywords: Optional[str] = None
    price: Optional[float] = Field(None, gt=0 if Field else 0)
    category_id: Optional[int] = None
    item_condition: Optional[ItemCondition] = None
    is_skill_sharing: Optional[bool] = None
    rate: Optional[float] = Field(None, gt=0 if Field else 0)
    rate_type: Optional[RateType] = None
    availability: Optional[str] = None
    status: Optional[str] = None
    buyer_id: Optional[int] = None
    sold_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Listing(ListingBase):
    listing_id: int
    seller_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    views_count: int
    buyer_id: Optional[int] = None
    sold_at: Optional[datetime] = None

    images: List[ListingImage] = []
    seller: UserRead
    buyer: Optional[UserMinimal] = None
    category: Optional[Category] = None

    class Config:
        from_attributes = True

class ListingMinimal(BaseModel):
    listing_id: int
    title: str
    is_skill_sharing: bool

    class Config:
        from_attributes = True

# --- Search Results Schema ---
class SearchResults(BaseModel):
    total: int
    results: List[Listing] = []

    class Config:
        from_attributes = True

# --- Admin Schemas ---
class AdminListingUpdateNotes(BaseModel):
    """Schema for admin updates that include notes."""
    admin_notes: Optional[str] = Field(None, description="Admin notes or feedback for the listing.")

# --- Review Schemas ---
# MODIFIED: Renamed ReviewCreateInput to ReviewCreate to match import in crud.py
class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: Optional[str] = Field(None, description="Text comment for the review")
    # listing_id is typically a path parameter for POST /listings/{id}/reviews
    # reviewer_id is from the authenticated user
    # reviewee_id is derived (e.g. seller of the listing, or buyer for seller_reviews_buyer)
    # If your crud.create_listing_review expects listing_id in the body, add it here.
    # Based on previous discussions, listing_id was part of ReviewCreate.
    # For example: listing_id: int (if it's passed in the request body for this schema)

class Review(BaseModel): # This is the main read model for a review
    review_id: int
    listing_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    reviewer: UserMinimal
    reviewee: UserMinimal

    class Config:
        from_attributes = True

# --- Messaging Schemas ---
class MessageBase(BaseModel):
   content: str

class MessageCreate(MessageBase):
   pass

class Message(MessageBase):
   message_id: int
   conversation_id: int
   sender_id: int
   created_at: datetime
   sender: UserRead

   class Config:
       from_attributes = True

class ConversationBase(BaseModel):
   user1_id: int
   user2_id: int
   listing_id: Optional[int] = None

class ConversationCreate(ConversationBase):
   pass

class Conversation(ConversationBase):
   conversation_id: int
   created_at: datetime
   updated_at: Optional[datetime] = None

   user1: UserRead
   user2: UserRead
   listing: Optional[ListingMinimal] = None

   messages: List[Message] = []

   class Config:
       from_attributes = True

class ConversationInboxItem(BaseModel):
   conversation_id: int
   created_at: datetime
   updated_at: Optional[datetime] = None
   user1: UserRead
   user2: UserRead
   listing: Optional[ListingMinimal] = None

   @computed_field
   @property
   def last_message(self) -> Optional[Message]:
       if hasattr(self, '_orm_instance') and hasattr(self._orm_instance, 'messages') and self._orm_instance.messages:
           return Message.from_orm(self._orm_instance.messages[0]) if self._orm_instance.messages else None
       return None

   class Config:
       from_attributes = True

class InitiateConversationRequest(BaseModel):
   recipient_id: int
   listing_id: int
   initial_message: str = Field(..., min_length=1, max_length=2000)

class InitiateConversationResponse(BaseModel):
   conversation_id: int
   message_id: int

   class Config:
       from_attributes = True

class HasReviewedResponse(BaseModel):
    has_reviewed: bool

