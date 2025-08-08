from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from .database import Base

# User model for authentication
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False) # Added for admin functionality

    # Relationship to listings
    listings = relationship("Listing", foreign_keys="Listing.seller_id", back_populates="seller")
    
    # Relationships for reviews
    reviews_written = relationship("Review", foreign_keys="Review.reviewer_id", back_populates="reviewer", lazy="dynamic")
    reviews_received = relationship("Review", foreign_keys="Review.reviewee_id", back_populates="reviewee", lazy="dynamic")

class Category(Base):
    __tablename__ = "categories"
    
    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.category_id"), nullable=True)
    display_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    is_skill_category = Column(Boolean, default=False, nullable=False) # Flag for skill/service categories
    
    # Self-referential relationship
    subcategories = relationship("Category", 
                                backref=backref("parent", remote_side=[category_id]),
                                cascade="all, delete-orphan")
    
    # Relationship to listings
    listings = relationship("Listing", back_populates="category")

class Listing(Base):
    __tablename__ = "listings"
    
    listing_id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    search_keywords = Column(String(255), nullable=True)
    price = Column(Float, nullable=True) # Make price nullable
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    item_condition = Column(String(20), nullable=False)  # Changed from 'condition'
    status = Column(String(50), default="pending_approval", nullable=False) # Increased size, default to pending_approval
    admin_notes = Column(Text, nullable=True) # Added for admin feedback

    # Skill-specific fields (optional)
    rate = Column(Float, nullable=True)
    rate_type = Column(String(50), nullable=True) # e.g., 'hourly', 'fixed'
    availability = Column(Text, nullable=True)

    # Relationship to seller (User)
    seller = relationship("User", foreign_keys=[seller_id], back_populates="listings")
    is_skill_sharing = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    views_count = Column(Integer, default=0)
    buyer_id = Column(Integer, ForeignKey("users.user_id"), nullable=True, index=True) # Added to track buyer
    sold_at = Column(DateTime(timezone=True), nullable=True) # Added to track when item was sold
    
    # Relationships
    category = relationship("Category", back_populates="listings")
    images = relationship("ListingImage", back_populates="listing", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="listing", cascade="all, delete-orphan", lazy="dynamic") # Added relationship to Reviews
    
    # Condition and status validation
    __table_args__ = (
        CheckConstraint("item_condition IN ('new', 'like_new', 'good', 'fair', 'poor')", name="check_condition"),  # Changed from 'condition'
        CheckConstraint("status IN ('available', 'pending', 'sold', 'pending_approval', 'approved', 'rejected', 'needs_changes')", name="check_status"), # Added new statuses
    )
class ListingImage(Base):
    __tablename__ = "listing_images"
    
    image_id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.listing_id"), nullable=False)
    image_path = Column(String(255), nullable=False) # Path to full-resolution image
    thumbnail_path = Column(String(255), nullable=False) # Path to thumbnail image
    display_order = Column(Integer, nullable=False, default=0)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    listing = relationship("Listing", back_populates="images")

class Conversation(Base):
   __tablename__ = "conversations"

   conversation_id = Column(Integer, primary_key=True, index=True)
   # Link to the two users involved in the conversation
   user1_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
   user2_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
   # Link to the listing the conversation is about (optional, but good for context)
   listing_id = Column(Integer, ForeignKey("listings.listing_id"), nullable=True)
   created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
   updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True) # Track last message time

   # Relationships to users and listing
   user1 = relationship("User", foreign_keys=[user1_id])
   user2 = relationship("User", foreign_keys=[user2_id])
   listing = relationship("Listing") # No back_populates needed if not navigating from Listing to Conversation directly

   # Relationship to messages in this conversation
   messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
   __tablename__ = "messages"

   message_id = Column(Integer, primary_key=True, index=True)
   conversation_id = Column(Integer, ForeignKey("conversations.conversation_id"), nullable=False)
   sender_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
   content = Column(Text, nullable=False)
   created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

   # Relationships to conversation and sender
   conversation = relationship("Conversation", back_populates="messages")
   sender = relationship("User") # No back_populates needed if not navigating from User to Message directly

# Review model
class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.listing_id"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    reviewee_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    
    rating = Column(Integer, nullable=False) # e.g., 1 to 5
    comment = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    listing = relationship("Listing", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_written")
    reviewee = relationship("User", foreign_keys=[reviewee_id], back_populates="reviews_received")

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
        UniqueConstraint('listing_id', 'reviewer_id', name='uq_listing_reviewer_one_review')
    )
