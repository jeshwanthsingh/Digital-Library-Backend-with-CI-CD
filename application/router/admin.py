from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from application.database.database import get_db
from application.database import crud, models
from application import schemas
from application.security import get_current_admin_user # Import the new admin dependency

router = APIRouter(
    prefix="/admin", # This will be the prefix for admin endpoints
    tags=["admin"],
)

@router.get("/listings/pending", response_model=List[schemas.Listing])
async def get_pending_listings(
    db: Session = Depends(get_db),
    current_admin_user: models.User = Depends(get_current_admin_user), # Requires admin authentication
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200)
):
    """
    Get a list of listings that are pending admin approval.
    Accessible only by administrators.
    """
    # This will require a new CRUD function to fetch listings by status
    # For now, we'll call a placeholder and define the CRUD function next.
    print(f"<<<<< DEBUG: GET /admin/listings/pending ENDPOINT WAS HIT by admin {current_admin_user.user_id} >>>>>")
    
    # Use the CRUD function to get listings by status, with pagination
    listings = crud.get_listings_by_status(db, status="pending_approval", skip=skip, limit=limit)
    
    return listings

@router.get("/listings", response_model=List[schemas.Listing]) # Admin view for all listings
async def get_all_listings_admin(
    db: Session = Depends(get_db),
    current_admin_user: models.User = Depends(get_current_admin_user), # Requires admin authentication
    # Use the same query parameters as the public search endpoint
    q: Optional[str] = Query(None, description="Search query for title, description, or keywords"),
    category_id: Optional[int] = Query(None, description="Filter by category ID. 0 means all categories."),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter."),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter."),
    item_condition: Optional[str] = Query(None, description="Filter by item condition (e.g., 'new', 'used')."),
    is_skill_sharing: Optional[bool] = Query(None, description="Filter by skill sharing status."),
    status: Optional[str] = Query(None, description="Filter by listing status (e.g., 'available', 'sold', 'pending_approval'). Set to None to get listings of all statuses."),
    skip: int = Query(0, ge=0, description="Number of listings to skip for pagination."),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of listings to return."),
):
    """
    Get a list of all listings with optional filters, for administrators.
    Admins can view listings regardless of status by not providing a status filter.
    """
    print(f"<<<<< DEBUG: GET /admin/listings ENDPOINT WAS HIT by admin {current_admin_user.user_id} >>>>>") # Debug print

    # Pass through all filters to crud.get_listings
    # Explicitly pass the status filter received from the query parameter
    # If status is None in the query, pass None to crud.get_listings to get all statuses.
    # crud.get_listings now defaults status to 'approved' if None is passed in its definition,
    # but we are explicitly passing the *query parameter* status here.
    # If the admin wants all statuses, the query param 'status' will be None,
    # and we pass status=None to crud.get_listings to override its default 'approved'.
    
    # The crud.get_listings function's default handling of `status=Optional[str] = 'approved'`
    # means if we call `crud.get_listings(db, status=None, ...)` it *will* return all statuses.
    # If we call `crud.get_listings(db, status='pending_approval', ...)` it will return pending.
    # If we call `crud.get_listings(db, ...)` without the status keyword, it defaults to 'approved'.
    # The current code passes the query parameter status directly.
    # So, if the admin endpoint receives no status query param (status is None), it will call crud.get_listings(db, status=None, ...) which returns all.
    # If the admin provides status=pending_approval, it calls crud.get_listings(db, status='pending_approval', ...).
    # This seems correct with the current crud.get_listings definition.

    listings = crud.get_listings(
        db,
        skip=skip,
        limit=limit,
        search=q,
        category_id=category_id if category_id and category_id > 0 else None, # Handle 0 for all categories
        min_price=min_price,
        max_price=max_price,
        item_condition=item_condition,
        is_skill_sharing=is_skill_sharing,
        status=status # Pass the status query parameter value directly
    )

    return listings

@router.put("/listings/{listing_id}/approve", response_model=schemas.Listing)
async def approve_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    current_admin_user: models.User = Depends(get_current_admin_user) # Requires admin authentication
):
    """
    Approve a listing, changing its status to 'approved'.
    Accessible only by administrators.
    """
    print(f"<<<<< DEBUG: PUT /admin/listings/{listing_id}/approve ENDPOINT WAS HIT by admin {current_admin_user.user_id} >>>>>") # Debug print

    updated_listing = crud.update_listing_status(db, listing_id=listing_id, new_status="approved", admin_notes=None)
    if not updated_listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    # Send a notification message to the seller
    if updated_listing.seller_id != current_admin_user.user_id: # Avoid admin self-notifying if they are the seller
        seller_id = updated_listing.seller_id
        admin_id = current_admin_user.user_id
        listing_title = updated_listing.title

        # Find or create a conversation
        conversation = crud.get_conversation_by_users_and_listing(
            db, user1_id=admin_id, user2_id=seller_id, listing_id=listing_id
        )
        if not conversation:
            # Ensure correct order for user1_id and user2_id if your get function doesn't handle both orders
            # For simplicity, assuming get_conversation_by_users_and_listing checks both permutations or we create with a fixed order
            conversation = crud.create_conversation(
                db, user1_id=min(admin_id, seller_id), user2_id=max(admin_id, seller_id), listing_id=listing_id
            )
        
        if conversation:
            message_content = f"Congratulations! Your listing '{listing_title}' (ID: {listing_id}) has been approved by an administrator."
            try:
                crud.create_message(
                    db=db,
                    conversation_id=conversation.conversation_id,
                    sender_id=admin_id, # Message from the admin
                    content=message_content
                )
                print(f"Approval notification sent for listing {listing_id} to seller {seller_id}")
            except Exception as e:
                # Log error, but don't let notification failure break the approval response
                print(f"Error sending approval notification for listing {listing_id}: {e}")
        else:
            print(f"Could not find or create conversation to notify seller for listing {listing_id}")

    return updated_listing

@router.put("/listings/{listing_id}/reject", response_model=schemas.Listing)
async def reject_listing(
    listing_id: int,
    notes: schemas.AdminListingUpdateNotes, # Accept admin notes
    db: Session = Depends(get_db),
    current_admin_user: models.User = Depends(get_current_admin_user) # Requires admin authentication
):
    """
    Reject a listing, changing its status to 'rejected' and adding admin notes.
    Accessible only by administrators.
    """
    print(f"<<<<< DEBUG: PUT /admin/listings/{listing_id}/reject ENDPOINT WAS HIT by admin {current_admin_user.user_id} >>>>>") # Debug print

    updated_listing = crud.update_listing_status(db, listing_id=listing_id, new_status="rejected", admin_notes=notes.admin_notes)
    if not updated_listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    # Send a notification message to the seller
    if updated_listing.seller_id != current_admin_user.user_id: # Avoid admin self-notifying
        seller_id = updated_listing.seller_id
        admin_id = current_admin_user.user_id
        listing_title = updated_listing.title
        rejection_notes = updated_listing.admin_notes # These are the notes from the input

        conversation = crud.get_conversation_by_users_and_listing(
            db, user1_id=admin_id, user2_id=seller_id, listing_id=listing_id
        )
        if not conversation:
            conversation = crud.create_conversation(
                db, user1_id=min(admin_id, seller_id), user2_id=max(admin_id, seller_id), listing_id=listing_id
            )
        
        if conversation:
            message_content = f"Your listing '{listing_title}' (ID: {listing_id}) has been rejected by an administrator. Reason: {rejection_notes}"
            try:
                crud.create_message(
                    db=db,
                    conversation_id=conversation.conversation_id,
                    sender_id=admin_id,
                    content=message_content
                )
                print(f"Rejection notification sent for listing {listing_id} to seller {seller_id}")
            except Exception as e:
                print(f"Error sending rejection notification for listing {listing_id}: {e}")
        else:
            print(f"Could not find or create conversation to notify seller of rejection for listing {listing_id}")

    return updated_listing

@router.put("/listings/{listing_id}/needs-changes", response_model=schemas.Listing)
async def needs_changes_listing(
    listing_id: int,
    notes: schemas.AdminListingUpdateNotes, # Accept admin notes
    db: Session = Depends(get_db),
    current_admin_user: models.User = Depends(get_current_admin_user) # Requires admin authentication
):
    """
    Mark a listing as needing changes, changing its status to 'needs_changes' and adding admin notes.
    Accessible only by administrators.
    """
    print(f"<<<<< DEBUG: PUT /admin/listings/{listing_id}/needs-changes ENDPOINT WAS HIT by admin {current_admin_user.user_id} >>>>>") # Debug print

    updated_listing = crud.update_listing_status(db, listing_id=listing_id, new_status="needs_changes", admin_notes=notes.admin_notes)
    if not updated_listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    # Send a notification message to the seller
    if updated_listing.seller_id != current_admin_user.user_id: # Avoid admin self-notifying
        seller_id = updated_listing.seller_id
        admin_id = current_admin_user.user_id
        listing_title = updated_listing.title
        feedback_notes = updated_listing.admin_notes

        conversation = crud.get_conversation_by_users_and_listing(
            db, user1_id=admin_id, user2_id=seller_id, listing_id=listing_id
        )
        if not conversation:
            conversation = crud.create_conversation(
                db, user1_id=min(admin_id, seller_id), user2_id=max(admin_id, seller_id), listing_id=listing_id
            )
        
        if conversation:
            message_content = f"Your listing '{listing_title}' (ID: {listing_id}) requires changes. Administrator feedback: {feedback_notes}"
            try:
                crud.create_message(
                    db=db,
                    conversation_id=conversation.conversation_id,
                    sender_id=admin_id,
                    content=message_content
                )
                print(f"'Needs changes' notification sent for listing {listing_id} to seller {seller_id}")
            except Exception as e:
                print(f"Error sending 'needs changes' notification for listing {listing_id}: {e}")
        else:
            print(f"Could not find or create conversation to notify seller of 'needs changes' for listing {listing_id}")

    return updated_listing

# TODO: Add other admin endpoints (view all listings)
# The GET /admin/listings endpoint added earlier covers viewing all listings with filters.
# Remaining admin tasks include frontend implementation and integration.