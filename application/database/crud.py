import os # Added for file deletion
from pathlib import Path # Added for file deletion
from sqlalchemy.orm import Session, joinedload, selectinload # Import joinedload and selectinload
from sqlalchemy import or_, case, desc # Import desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from . import models
# Define Project Root for constructing absolute file paths for deletion
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
# BACKEND_STATIC_DIR is PROJECT_ROOT_DIR / "static", image paths in DB are relative to this after /static/
# e.g., /static/images/listings/listing_id/image.jpg

from application.schemas import ListingCreate, CategoryCreate, UserMinimal, ListingMinimal, ConversationInboxItem, ReviewCreate # Import necessary schemas for potential type hinting or direct use

# User operations
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, username: str, email: str, hashed_password: str, is_admin: bool = False):
    user = models.User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_admin=is_admin
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def search_users_by_username_or_email(db: Session, query_str: str, limit: int = 10) -> List[models.User]:
    """
    Search for users by username or email.
    Returns a list of users matching the query string in either username or email.
    The search is case-insensitive.
    """
    search_term = f"%{query_str}%"
    return (
        db.query(models.User)
        .filter(
            or_(
                models.User.username.ilike(search_term),
                models.User.email.ilike(search_term)
            )
        )
        .limit(limit)
        .all()
    )


# Category operations
def get_categories(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    parent_id: Optional[int] = None,
    is_skill: Optional[bool] = None, # Add filter for skill/item categories
    active_only: bool = True
) -> List[models.Category]:
    """
    Get categories with optional filtering by parent_id, active status, and skill category type.
    """
    query = db.query(models.Category)
    
    if parent_id is not None:
        query = query.filter(models.Category.parent_id == parent_id)
    
    if active_only:
        query = query.filter(models.Category.is_active == True)
        
    # Add filter for skill/item category type if specified
    if is_skill is not None:
        query = query.filter(models.Category.is_skill_category == is_skill)
    
    return query.order_by(models.Category.display_order).offset(skip).limit(limit).all()

def get_category(db: Session, category_id: int) -> Optional[models.Category]:
    """
    Get a single category by ID.
    """
    return db.query(models.Category).filter(models.Category.category_id == category_id).first()

def create_category(db: Session, category: CategoryCreate) -> models.Category:
    """
    Create a new category.
    """
    db_category = models.Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# Listing operations
def get_listings(
    db: Session, 
    skip: int = 0, 
    limit: int = 20,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    item_condition: Optional[str] = None,
    is_skill_sharing: Optional[bool] = None, # Add skill sharing filter
    status: Optional[str] = 'approved'  # Default to 'approved' status for general views
) -> List[models.Listing]:
    """
    Get listings with optional filtering and search.
    Defaults to returning 'approved' listings for general public views.
    Set status to None to get listings regardless of status (e.g., for admin).
    """
    query = db.query(models.Listing)
    print(f"crud.get_listings: Initial query created.")
    print(f"crud.get_listings: Received params: search='{search}', category_id={category_id}, status='{status}', is_skill_sharing={is_skill_sharing}")

    # Filter by status unless status is explicitly set to None
    if status is not None:
        query = query.filter(models.Listing.status == status)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Listing.title.ilike(search_term),
                models.Listing.description.ilike(search_term),
                models.Listing.search_keywords.ilike(search_term)
            )
        )
        
        # Prioritize matches in title
        query = query.order_by(
            case(
                (models.Listing.title.ilike(search_term), 1),
                else_=2
            ),
            models.Listing.created_at.desc()
        )
    else:
        # Default sorting by creation date (newest first)
        query = query.order_by(models.Listing.created_at.desc())
    
    # Apply category filter if provided
    if category_id:
        query = query.filter(models.Listing.category_id == category_id)
    
    # Apply price range filters if provided
    if min_price is not None:
        query = query.filter(models.Listing.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Listing.price <= max_price)
    
    # Apply condition filter if provided
    if item_condition:
        query = query.filter(models.Listing.item_condition == item_condition)
        
    # Apply skill sharing filter if provided (True or False)
    if is_skill_sharing is not None:
        query = query.filter(models.Listing.is_skill_sharing == is_skill_sharing)
        print(f"crud.get_listings: Applied is_skill_sharing filter: {is_skill_sharing}")
    
    # Log the final query before pagination
    try:
        print(f"crud.get_listings: Final query before pagination and execution: {query.statement.compile(compile_kwargs={'literal_binds': True})}")
    except Exception as e:
        print(f"crud.get_listings: Could not compile query for logging: {e}")

    results_before_pagination = query.all()
    print(f"crud.get_listings: Found {len(results_before_pagination)} results BEFORE pagination. First 5: {[(r.listing_id, r.title, r.status, r.is_skill_sharing) for r in results_before_pagination[:5]]}")

    paginated_results = query.offset(skip).limit(limit).all()
    print(f"crud.get_listings: Returning {len(paginated_results)} paginated results. Skip: {skip}, Limit: {limit}")
    return paginated_results

def get_listings_by_seller_id(db: Session, seller_id: int) -> List[models.Listing]:
    """
    Get all listings for a specific seller, regardless of status.
    """
    return (
        db.query(models.Listing)
        .options(
            joinedload(models.Listing.seller),
            joinedload(models.Listing.category),
            selectinload(models.Listing.images)
        )
        .filter(models.Listing.seller_id == seller_id)
        .order_by(models.Listing.created_at.desc()) # Optional: order them
        .all()
    )

def get_listings_by_status(db: Session, status: str, skip: int = 0, limit: int = 100) -> List[models.Listing]:
    """
    Get listings filtered by a specific status, with pagination.
    """
    return (
        db.query(models.Listing)
        .filter(models.Listing.status == status)
        .offset(skip)
        .limit(limit)
        .all()
    )

def update_listing_status(db: Session, listing_id: int, new_status: str, admin_notes: Optional[str] = None) -> Optional[models.Listing]:
    """
    Update the status and optionally admin notes for a specific listing.
    Returns the updated listing or None if not found.
    """
    db_listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if not db_listing:
        return None # Listing not found

    # Validate the new status against the model's check constraint if necessary,
    # although SQLAlchemy might handle this on commit.
    # It's safer to rely on the database constraint for validation.

    db_listing.status = new_status
    if new_status == "approved":
        db_listing.admin_notes = None
    else:
        db_listing.admin_notes = admin_notes
    db.commit()
    db.refresh(db_listing)
    return db_listing

def update_listing_status_by_admin(db: Session, listing_id: int, new_status: str, admin_notes: Optional[str] = None) -> Optional[models.Listing]:
    """
    Update listing status and admin notes, typically by an admin.
    Clears admin_notes if the new status is 'approved'.
    """
    db_listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if db_listing:
        db_listing.status = new_status
        if new_status == "approved":
            db_listing.admin_notes = None  # Clear notes on approval
        else:
            db_listing.admin_notes = admin_notes # Set notes if provided for other statuses
        db.commit()
        db.refresh(db_listing)
    return db_listing

def get_listing(db: Session, listing_id: int) -> Optional[models.Listing]:
    """
    Get a single listing by ID, with the associated user and images.
    Reviews are intended to be fetched via a separate endpoint if needed.
    """
    return (
        db.query(models.Listing)
        .options(
            joinedload(models.Listing.seller),
            joinedload(models.Listing.images)
            # Reviews are not eager-loaded here; assumed to be fetched via /listings/{id}/reviews
        )
        .filter(models.Listing.listing_id == listing_id)
        .first()
    )

def create_listing(db: Session, listing: ListingCreate, seller_id: int) -> models.Listing:
    """
    Create a new listing.
    """
    db_listing = models.Listing(**listing.dict(), seller_id=seller_id, status="pending_approval") # Set default status to pending_approval
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return db_listing

def update_listing(
    db: Session,
    listing_id: int,
    seller_id: int, # Used to authorize the update
    update_data: Dict[str, Any]
) -> Optional[models.Listing]:
    """
    Update an existing listing.
    - Only the listing owner (seller_id) can update.
    - Handles setting `buyer_id`, `sold_at`, and `status` when a listing is sold.
    - Handles reverting to "available" status.
    """
    db_listing = db.query(models.Listing).filter(
        models.Listing.listing_id == listing_id,
        models.Listing.seller_id == seller_id  # Ensure current user is the seller
    ).first()

    if not db_listing:
        # Listing not found or current user is not the seller
        return None

    data_to_process = update_data.copy() # Work with a copy

    # --- Re-moderation logic for approved listings ---
    # If the listing is currently approved and substantive fields are being updated,
    # revert its status to 'pending_approval' for re-moderation.
    substantive_fields_for_remoderation = {
        'title', 'description', 'price', 'category_id', 'item_condition',
        'is_skill_sharing', 'rate', 'rate_type', 'availability', 'search_keywords'
    }
    updated_substantive_fields = substantive_fields_for_remoderation.intersection(data_to_process.keys())

    if db_listing.status == "approved" and updated_substantive_fields:
        db_listing.status = "pending_approval"
        # Ensure 'status' from update_data doesn't override this if also present
        # and is not one of the explicit status handling scenarios below.
        # If user is trying to sell it, that takes precedence.
        if 'status' in data_to_process and data_to_process['status'] not in ["sold", "available"]:
             data_to_process.pop('status') # Remove if it's not for selling/making available

    # --- End Re-moderation logic ---

    # Scenario 1: Listing is being marked as sold (buyer_id provided)
    if 'buyer_id' in data_to_process and data_to_process['buyer_id'] is not None:
        new_buyer_id = data_to_process.pop('buyer_id')
        
        # Prevent seller from being the buyer
        if new_buyer_id == db_listing.seller_id:
            # Or raise ValueError("Seller cannot be the buyer.")
            return None

        db_listing.buyer_id = new_buyer_id
        db_listing.status = "sold"
        db_listing.sold_at = data_to_process.pop('sold_at', datetime.now(timezone.utc))
        data_to_process.pop('status', None) # Remove status if it was also passed, as it's now "sold"

    # Scenario 2: Listing is being made available again
    elif 'status' in data_to_process and data_to_process['status'] == "available":
        db_listing.status = data_to_process.pop('status')
        db_listing.buyer_id = None
        db_listing.sold_at = None
        # Remove buyer_id/sold_at if they were also in update_data, ensuring clean state
        data_to_process.pop('buyer_id', None)
        data_to_process.pop('sold_at', None)
        
    # Scenario 3: Other status updates (e.g., "pending", "delisted")
    # Or if 'status' is 'sold' but buyer_id was already set (e.g. updating other fields on a sold item)
    elif 'status' in data_to_process:
        new_status = data_to_process['status']
        if new_status == "sold":
            # If trying to set status to "sold" directly without buyer_id having been set via Scenario 1
            if db_listing.buyer_id is None:
                # This is an invalid state. Cannot be "sold" without a buyer.
                # Prevent this update by removing 'status' from processing.
                data_to_process.pop('status')
            else: # buyer_id exists, status is "sold" (could be a re-affirmation or no-op if already sold)
                db_listing.status = data_to_process.pop('status')
        else: # For any other status like "pending", "delisted", etc.
            db_listing.status = data_to_process.pop('status')


    # Update other general attributes from the remaining data_to_process
    for key, value in data_to_process.items():
        # Prevent updating restricted or specially-handled fields again
        if key in [
            'listing_id', 'seller_id', 'created_at', 'updated_at',
            'buyer_id', 'sold_at', 'status' # These are handled above or immutable
        ]:
            continue
            
        # Prevent setting item_condition to None, as it's nullable=False in the model
        if key == 'item_condition' and value is None:
            continue

        # Only update attributes that exist on the model
        if hasattr(db_listing, key):
             setattr(db_listing, key, value)
        else:
            # Log a warning if the frontend is trying to update a non-existent attribute
            import logging # Ensure logging is imported at the top if not already
            logger = logging.getLogger(__name__) # Get logger if not already defined
            logger.warning(f"Attempted to update non-existent attribute '{key}' on Listing model for listing ID {listing_id}.")

    db.commit()
    db.refresh(db_listing)
    return db_listing

def delete_listing(db: Session, listing_id: int, seller_id: int) -> bool:
    """
    Delete a listing. Only the listing owner can delete it.
    """
    db_listing = db.query(models.Listing).filter(
        models.Listing.listing_id == listing_id,
        models.Listing.seller_id == seller_id
    ).first()
    
    if not db_listing:
        return False # Listing not found or doesn't belong to the seller
    
    # Before deleting the listing, delete its associated images (DB records and files)
    # The delete_listing_image CRUD function handles both DB and file system.
    # Ensure the listing's images are loaded if not already (though direct access should trigger lazy load if session is active)
    # For safety, explicitly query them if db_listing.images might not be populated or if session issues arise with lazy load here.
    # However, SQLAlchemy's default cascade options might handle DB deletion of images if configured on the model relationship.
    # Let's assume we need to manually trigger our CRUD for file deletion.
    
    # Iterate over a copy of the images list if modifying it during iteration (not the case here as we delete via image_id)
    # or ensure the session is flushed before accessing related items that might be affected by cascade.
    # A simple approach is to fetch image_ids first.
    
    image_ids_to_delete = [img.image_id for img in db_listing.images] # Assuming db_listing.images is populated

    for image_id in image_ids_to_delete:
        # `delete_listing_image` checks ownership (seller_id) internally again.
        delete_listing_image(db=db, image_id=image_id, seller_id=seller_id)
        # Note: delete_listing_image commits its own transaction.

    # Now delete the listing itself
    db.delete(db_listing)
    db.commit() # Commit the deletion of the listing
    return True

# Listing image operations
def get_listing_images(db: Session, listing_id: int) -> List[models.ListingImage]:
    """
    Get all images for a listing.
    """
    return db.query(models.ListingImage).filter(
        models.ListingImage.listing_id == listing_id
    ).order_by(models.ListingImage.display_order).all()

def create_listing_image(
    db: Session, 
    listing_id: int,
    image_path: str,
    thumbnail_path: Optional[str] = None, # Add thumbnail_path parameter
    display_order: int = 0,
    is_primary: bool = False
) -> models.ListingImage:
    """
    Add an image to a listing, including its thumbnail path.
    """
    db_image = models.ListingImage(
        listing_id=listing_id,
        image_path=image_path,
        thumbnail_path=thumbnail_path, # Save the thumbnail path
        display_order=display_order,
        is_primary=is_primary
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

# Messaging operations
def create_conversation(db: Session, user1_id: int, user2_id: int, listing_id: Optional[int] = None) -> models.Conversation:
    """
    Create a new conversation.
    """
    db_conversation = models.Conversation(
        user1_id=user1_id,
        user2_id=user2_id,
        listing_id=listing_id
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

def get_specific_review_existence(db: Session, reviewer_id: int, reviewee_id: int, listing_id: int) -> bool:
    """
    Checks if a specific review exists given the reviewer, reviewee, and listing.
    This is a generic check that can be used for buyer-reviews-seller or seller-reviews-buyer.
    """
    return db.query(models.Review.review_id).filter(
        models.Review.reviewer_id == reviewer_id,
        models.Review.reviewee_id == reviewee_id,
        models.Review.listing_id == listing_id
    ).first() is not None

def get_conversation_by_users_and_listing(
    db: Session,
    user1_id: int,
    user2_id: int,
    listing_id: Optional[int] = None
) -> Optional[models.Conversation]:
    """
    Get a conversation between two users for a specific listing, if it exists.
    Considers both user orders (user1_id, user2_id) and (user2_id, user1_id).
    """
    # Query for conversations where the users match and the listing matches
    query = db.query(models.Conversation).filter(
        or_(
            # Case 1: user1 is user1_id and user2 is user2_id
            (models.Conversation.user1_id == user1_id) & (models.Conversation.user2_id == user2_id),
            # Case 2: user1 is user2_id and user2 is user1_id
            (models.Conversation.user1_id == user2_id) & (models.Conversation.user2_id == user1_id)
        )
    )

    # Filter by listing_id if provided
    if listing_id is not None:
        query = query.filter(models.Conversation.listing_id == listing_id)
    else:
        # If listing_id is None, only match conversations with no listing_id
        query = query.filter(models.Conversation.listing_id.is_(None))

    return query.first()


def get_conversations_for_user(db: Session, user_id: int) -> List[models.Conversation]:
    """
    Get all conversations for a specific user, with eager-loaded user details,
    associated listing, and messages (for deriving last message).
    Conversations are ordered by the most recent activity (updated_at).
    """
    return (
        db.query(models.Conversation)
        .options(
            joinedload(models.Conversation.user1),  # Eager load user1
            joinedload(models.Conversation.user2),  # Eager load user2
            joinedload(models.Conversation.listing), # Eager load associated listing
            selectinload(models.Conversation.messages).options( # Eager load messages
                joinedload(models.Message.sender) # And the sender of each message
            )
        )
        .filter(
            or_(
                models.Conversation.user1_id == user_id,
                models.Conversation.user2_id == user_id,
            )
        )
        .order_by(desc(models.Conversation.updated_at)) # Order by last update
        .all()
    )

def get_conversation_by_id(db: Session, conversation_id: int) -> Optional[models.Conversation]:
    """
    Get a single conversation by its ID, with eager-loaded user and listing details.
    """
    return (
        db.query(models.Conversation)
        .options(
            joinedload(models.Conversation.user1),      # Eager load user1
            joinedload(models.Conversation.user2),      # Eager load user2
            joinedload(models.Conversation.listing)     # Eager load associated listing
            # We might not need messages here, as they are fetched separately by the frontend if needed
            # If last message preview is needed on this object, messages could be selectinloaded
        )
        .filter(models.Conversation.conversation_id == conversation_id)
        .first()
    )

def get_messages_for_conversation(db: Session, conversation_id: int) -> List[models.Message]:
    """
    Get all messages within a conversation, ordered by creation time.
    """
    return db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.created_at).all()

def create_message(db: Session, conversation_id: int, sender_id: int, content: str) -> models.Message:
    """
    Create a new message within a conversation.
    """
    db_message = models.Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def delete_listing_image(db: Session, image_id: int, seller_id: int) -> bool:
    """
    Delete a listing image. Only the listing owner can delete it.
    """
    db_image = db.query(models.ListingImage).filter(
        models.ListingImage.image_id == image_id
    ).first()
    
    # Check if image exists
    if not db_image:
        return False
    
    # Check if the image belongs to a listing owned by the seller
    # Use a fresh query for the listing to ensure accuracy
    listing = db.query(models.Listing).filter(
        models.Listing.listing_id == db_image.listing_id,
        models.Listing.seller_id == seller_id
    ).first()
    
    if not listing:
        return False # Listing not found or doesn't belong to the seller
    
    # Store paths before deleting the DB record, as they might become inaccessible
    image_file_path_str = db_image.image_path
    thumbnail_file_path_str = db_image.thumbnail_path

    db.delete(db_image)
    db.commit()

    # Attempt to delete the actual files from the filesystem
    # Assumes paths in DB are like "/static/images/listings/listing_id/image.jpg"
    # We need to form an absolute path from PROJECT_ROOT_DIR
    if image_file_path_str and image_file_path_str.startswith("/static/"):
        abs_image_path = PROJECT_ROOT_DIR / image_file_path_str[1:] # Remove leading '/'
        try:
            if abs_image_path.is_file():
                os.remove(abs_image_path)
                print(f"Deleted image file: {abs_image_path}")
        except OSError as e:
            print(f"Error deleting image file {abs_image_path}: {e}")
            # Decide if this should be a critical error or just logged

    if thumbnail_file_path_str and thumbnail_file_path_str.startswith("/static/"):
        abs_thumbnail_path = PROJECT_ROOT_DIR / thumbnail_file_path_str[1:] # Remove leading '/'
        try:
            if abs_thumbnail_path.is_file():
                os.remove(abs_thumbnail_path)
                print(f"Deleted thumbnail file: {abs_thumbnail_path}")
        except OSError as e:
            print(f"Error deleting thumbnail file {abs_thumbnail_path}: {e}")
            # Decide if this should be a critical error or just logged
            
    return True

# Review operations
def create_listing_review(db: Session, review_data: ReviewCreate, listing_id: int, reviewer_id: int) -> models.Review:
    """
    Create a new review for a specific listing.
    - The reviewer_id is taken from the authenticated user.
    - The reviewee_id is the seller of the listing.
    - Prevents users from reviewing their own listings.
    - Relies on DB unique constraint (listing_id, reviewer_id) to prevent multiple reviews by the same user for the same listing.
    """
    # Ensure the listing exists
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if not listing:
        # This exception should be caught in the API layer and converted to HTTPException
        raise ValueError(f"Listing with ID {listing_id} not found.")

    # Check if the listing is sold
    if listing.status != "sold":
        raise ValueError(f"Listing with ID {listing_id} must be 'sold' to be reviewed by a buyer.")

    # Check if the reviewer is the buyer of the listing
    if listing.buyer_id != reviewer_id:
        raise ValueError(f"User (ID: {reviewer_id}) is not the buyer of listing (ID: {listing_id}) and cannot review the seller.")

    # Prevent user from reviewing their own listing (this check is more for data integrity,
    # as buyer_id should not be seller_id for a sold item, but good to keep)
    if listing.seller_id == reviewer_id:
        raise ValueError("User cannot review their own listing.")

    reviewee_id = listing.seller_id

    # Check if this reviewer has already reviewed this reviewee for this listing
    existing_review = get_specific_review_existence(
        db, reviewer_id=reviewer_id, reviewee_id=reviewee_id, listing_id=listing_id
    )
    if existing_review:
        raise ValueError(
            f"User (ID: {reviewer_id}) has already submitted a review for listing (ID: {listing_id}) regarding seller (ID: {reviewee_id})."
        )

    db_review = models.Review(
        listing_id=listing_id,
        reviewer_id=reviewer_id,
        reviewee_id=reviewee_id,
        rating=review_data.rating,
        comment=review_data.comment
    )
    db.add(db_review)
    db.commit() # Database will raise IntegrityError if uq_listing_reviewer_one_review is violated
    db.refresh(db_review)
    return db_review

def get_reviews_for_listing(db: Session, listing_id: int, skip: int = 0, limit: int = 20) -> List[models.Review]:
    """
    Get reviews for a specific listing, ordered by creation date (newest first).
    Includes reviewer and reviewee details (eager-loaded).
    Supports pagination.
    """
    # First, check if the listing exists. Optional, but good practice if this function
    # could be called with arbitrary listing_ids.
    listing_exists = db.query(models.Listing.listing_id).filter(models.Listing.listing_id == listing_id).first()
    if not listing_exists:
        return [] # Or raise an exception if preferred, e.g., ValueError("Listing not found")

    return (
        db.query(models.Review)
        .options(
            joinedload(models.Review.reviewer).load_only(models.User.user_id, models.User.username), # Load only essential fields for reviewer
            joinedload(models.Review.reviewee).load_only(models.User.user_id, models.User.username)  # Load only essential fields for reviewee
        )
        .filter(models.Review.listing_id == listing_id)
        .order_by(desc(models.Review.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

# Note: get_reviews_by_reviewer and get_reviews_for_reviewee are kept as they were.
# They might need adjustments if their schemas (e.g. for reviewer/reviewee details)
# or pagination are to be standardized with get_reviews_for_listing.
# For now, they remain untouched.


def get_reviews_by_reviewer(db: Session, reviewer_id: int) -> List[models.Review]:
    """
    Get all reviews written by a specific user.
    Includes reviewee details.
    """
    return (
        db.query(models.Review)
        .options(joinedload(models.Review.reviewee)) # Eager load the person being reviewed
        .filter(models.Review.reviewer_id == reviewer_id)
        .order_by(desc(models.Review.created_at))
        .all()
    )

def get_reviews_for_reviewee(db: Session, reviewee_id: int) -> List[models.Review]:
    """
    Get all reviews received by a specific user.
    Includes reviewer details.
    """
    return (
        db.query(models.Review)
        .options(joinedload(models.Review.reviewer)) # Eager load the person who wrote the review
        .filter(models.Review.reviewee_id == reviewee_id)
        .order_by(desc(models.Review.created_at))
        .all()
    )

def create_seller_review_for_buyer(db: Session, review_data: ReviewCreate, listing_id: int, seller_id: int) -> models.Review:
    """
    Create a new review where the seller reviews the buyer of a completed transaction.
    - The seller_id (authenticated user) is the reviewer.
    - The reviewee_id is the buyer of the listing.
    - Prevents sellers from reviewing if they are not the seller of the listing.
    - Prevents reviews if the listing is not "sold" or has no buyer.
    - Relies on DB unique constraint (listing_id, reviewer_id) to prevent multiple reviews
      by the same seller for the same buyer for the same listing transaction.
    """
    # Ensure the listing exists
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if not listing:
        raise ValueError(f"Listing with ID {listing_id} not found.")

    # Verify the authenticated user (seller_id) is the actual seller of this listing
    if listing.seller_id != seller_id:
        raise ValueError("User is not the seller of this listing and cannot review the buyer.")

    # Verify the listing is sold and has a buyer
    if listing.status != "sold" or listing.buyer_id is None:
        raise ValueError("Listing must be 'sold' and have a buyer to be reviewed by the seller.")
    
    # The seller cannot review themselves (buyer_id should not be seller_id)
    # This should also be implicitly handled by listing.buyer_id being different from listing.seller_id
    # due to checks in update_listing, but an explicit check here is good.
    if listing.buyer_id == seller_id:
        raise ValueError("Seller cannot review themselves as the buyer for this transaction.")

    reviewee_id = listing.buyer_id

    # Check if this seller (reviewer) has already reviewed this buyer (reviewee) for this listing
    existing_review = get_specific_review_existence(
        db, reviewer_id=seller_id, reviewee_id=reviewee_id, listing_id=listing_id
    )
    if existing_review:
        raise ValueError(
            f"Seller (ID: {seller_id}) has already submitted a review for listing (ID: {listing_id}) regarding buyer (ID: {reviewee_id})."
        )

    db_review = models.Review(
        listing_id=listing_id,      # This is review_data.listing_id from the input schema
        reviewer_id=seller_id,      # The seller is the reviewer
        reviewee_id=reviewee_id,    # The buyer is the reviewee
        rating=review_data.rating,
        comment=review_data.comment
    )
    db.add(db_review)
    db.commit() # Database will raise IntegrityError if uq_listing_reviewer_one_review is violated
    db.refresh(db_review)
    return db_review

# Search operations
def count_search_results(
    db: Session,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    item_condition: Optional[str] = None,
    is_skill_sharing: Optional[bool] = None, # Add skill sharing filter
    status: Optional[str] = None # Add status filter, None means all statuses
) -> int:
    """
    Count the number of search results for the given parameters.
    Can filter by status. If status is None, no status filter is applied for counting.
    """
    query = db.query(models.Listing.listing_id) # Optimize by selecting only one column for count
    
    # Filter by status if provided
    if status:
        query = query.filter(models.Listing.status == status)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Listing.title.ilike(search_term),
                models.Listing.description.ilike(search_term),
                models.Listing.search_keywords.ilike(search_term)
            )
        )
    
    # Apply category filter if provided
    if category_id:
        query = query.filter(models.Listing.category_id == category_id)
    
    # Apply price range filters if provided
    if min_price is not None:
        query = query.filter(models.Listing.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Listing.price <= max_price)
    
    # Apply condition filter if provided
    if item_condition:
        query = query.filter(models.Listing.item_condition == item_condition)
        
    # Apply skill sharing filter if provided (True or False)
    if is_skill_sharing is not None:
        query = query.filter(models.Listing.is_skill_sharing == is_skill_sharing)
    
    return query.count()
