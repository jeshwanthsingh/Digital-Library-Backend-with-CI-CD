from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File # Removed Form, Annotated for create_listing
from sqlalchemy.orm import Session
from typing import List, Optional # Keep List from typing
import shutil
import os
from pathlib import Path
from PIL import Image # Added PIL
import re # For sanitization
import uuid # For sanitization

from application.database import crud, models
from application.database.database import get_db
from application import schemas
from application.security import get_current_active_user, get_current_active_user_optional # Import the new optional dependency

router = APIRouter(
    prefix="/listings",
    tags=["listings"],
)

# Define Project Root and Backend Static Dir relative to this file (application/router/listings.py)
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_STATIC_DIR = PROJECT_ROOT_DIR / "static"

images_base_dir = BACKEND_STATIC_DIR / "images" / "listings"
if not os.path.exists(images_base_dir):
    os.makedirs(images_base_dir, exist_ok=True)

def make_safe_filename(orig: str) -> str:
    # give it a random prefix so you never collide
    ext = os.path.splitext(orig)[1]
    base = os.path.splitext(orig)[0]
    # normalize whitespace → underscore, strip out any non-alphanumeric / dot / underscore
    safe_base = re.sub(r'\s+', '_', base)
    safe_base = re.sub(r'[^\w\.-]', '', safe_base)
    # Truncate if too long, ensure it's not empty
    safe_base = (safe_base[:50]) if safe_base else 'image'
    return f"{uuid.uuid4().hex[:8]}_{safe_base}{ext}" # Shortened UUID prefix


@router.post("/", response_model=schemas.Listing, status_code=status.HTTP_201_CREATED)
async def create_listing(
    listing_create: schemas.ListingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    print("<<<<< DEBUG: CREATE_LISTING ENDPOINT WAS HIT! >>>>>") # <-- ADD THIS LINE
    db_listing = crud.create_listing(db=db, listing=listing_create, seller_id=current_user.user_id)
    # db.commit() # This was my previous suggestion; ensure it's here if crud.create_listing doesn't commit.
                  # For now, the print statement is the main diagnostic.
                  # NOTE: We confirmed crud.create_listing DOES commit, so no db.commit() is needed here.
    db.refresh(db_listing)
    return db_listing


@router.post("/{listing_id}/images", response_model=dict)
async def upload_listing_images(
    listing_id: int,
    file: List[UploadFile] = File(..., alias="file"), # Keep alias as 'file' since frontend sends that
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_listing = crud.get_listing(db, listing_id=listing_id)
    if not db_listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    if db_listing.seller_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to upload images for this listing")

    saved_files_info = []
    listing_image_dir = BACKEND_STATIC_DIR / "images" / "listings" / str(listing_id)
    thumbnail_dir = listing_image_dir / "thumbs"
    
    listing_image_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_dir.mkdir(parents=True, exist_ok=True)

    primary_set = not any(img.is_primary for img in db_listing.images)

    for img_upload_file in file: # Renamed loop variable for clarity
        if not img_upload_file.filename:
            continue

        contents = await img_upload_file.read()
        
        # Sanitize filename using the new function
        safe_filename = make_safe_filename(img_upload_file.filename)
        
        file_path = listing_image_dir / safe_filename
        thumb_filename = f"thumb_{safe_filename}" # Use safe_filename for thumb
        thumb_path = thumbnail_dir / thumb_filename

        with open(file_path, "wb") as f:
            f.write(contents)

        try:
            with Image.open(file_path) as pil_img:
                pil_img.thumbnail((200, 200))
                pil_img.save(thumb_path, optimize=True, quality=75)
        except Exception as e:
            # Log the specific error with traceback on the backend
            import logging # Ensure logging is imported at the top if not already
            logger = logging.getLogger(__name__) # Get logger if not already defined
            logger.error(f"Error processing image {img_upload_file.filename} for listing {listing_id}: {e}", exc_info=True)
            # Consider removing file_path if thumbnail generation fails critically
            # os.remove(file_path)
            # Raise a generic HTTPException to the client
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing image. Check server logs for details.")

        image_schema_data = schemas.ListingImageCreate(
            image_path=f"/static/images/listings/{listing_id}/{safe_filename}",
            thumbnail_path=f"/static/images/listings/{listing_id}/thumbs/{thumb_filename}",
            is_primary=primary_set
        )
        crud.create_listing_image(
            db=db,
            listing_id=listing_id,
            image_path=image_schema_data.image_path,
            thumbnail_path=image_schema_data.thumbnail_path,
            display_order=image_schema_data.display_order,
            is_primary=image_schema_data.is_primary
        )
        if primary_set:
            primary_set = False

        saved_files_info.append({
            "original_filename": img_upload_file.filename, # Keep original for reference if needed
            "saved_filename": safe_filename,
            "url": image_schema_data.image_path,
            "thumbnail_url": image_schema_data.thumbnail_path
        })
    
    db.commit()
    db.refresh(db_listing) # Refresh to get updated images collection if needed, though not strictly necessary for this response
    return {"uploaded": saved_files_info, "listing_images": [schemas.ListingImage.from_orm(img) for img in db_listing.images]}

@router.delete("/{listing_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing_image_endpoint(
    listing_id: int, # Though not directly used by crud.delete_listing_image if it only takes image_id
    image_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # The CRUD function `delete_listing_image` takes image_id and seller_id.
    # It internally verifies that the image belongs to a listing owned by the seller.
    # We don't strictly need listing_id here if the image_id is globally unique
    # and the CRUD function handles all checks.
    # However, having listing_id in the path is good RESTful practice.
    # We can add an initial check if the image actually belongs to the specified listing_id for extra safety,
    # or rely on the CRUD function's internal check against current_user.seller_id.

    # Let's ensure the image belongs to the listing specified in the path first.
    db_image = db.query(models.ListingImage).filter(
        models.ListingImage.image_id == image_id,
        models.ListingImage.listing_id == listing_id
    ).first()

    if not db_image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found or does not belong to this listing.")

    # Now call the CRUD function which also checks for ownership by current_user
    deleted = crud.delete_listing_image(db=db, image_id=image_id, seller_id=current_user.user_id)
    if not deleted:
        # This could mean the image was found (passed previous check) but ownership check in CRUD failed,
        # or some other issue in CRUD.
        # The CRUD already returns False if not found or ownership fails.
        # If db_image was found, but deleted is False, it strongly implies an ownership issue.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this image or image not found.")
    
    return None # FastAPI handles 204 No Content

@router.get("/", response_model=List[schemas.Listing])
async def read_listings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    listings = crud.get_listings(db, skip=skip, limit=limit)
    return listings

@router.get("/my-listings", response_model=List[schemas.Listing])
async def read_my_listings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Requires authentication
):
    """
    Get all listings created by the current authenticated user, regardless of status.
    """
    print(f"<<<<< DEBUG: READ_MY_LISTINGS ENDPOINT WAS HIT for user {current_user.user_id} >>>>>") # Debug print
    return crud.get_listings_by_seller_id(db=db, seller_id=current_user.user_id)

@router.get("/{listing_id}", response_model=schemas.Listing)
async def read_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_active_user_optional) # Use optional dependency
):
    db_listing = crud.get_listing(db, listing_id=listing_id)
    if db_listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    # Access Control:
    is_owner = current_user and db_listing.seller_id == current_user.user_id

    if not is_owner and db_listing.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Use 404 to not reveal existence to non-owners
            detail="Listing not found or not available for viewing."
        )

    # Increment views count. Consider if this should only be for non-owners or 'approved' listings.
    # For simplicity, incrementing if view access is granted.
    db_listing.views_count = (db_listing.views_count or 0) + 1
    db.commit()
    db.refresh(db_listing)
    return db_listing

@router.put("/{listing_id}", response_model=schemas.Listing)
async def update_listing(
    listing_id: int,
    listing_update: schemas.ListingUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_listing = crud.get_listing(db, listing_id=listing_id)
    if db_listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    if db_listing.seller_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this listing")

    # Check if the listing was approved and is now being updated by the owner
    # If so, set the status back to pending_approval for re-moderation.
    update_data = listing_update.model_dump(exclude_unset=True) # Get dictionary of provided fields
    if db_listing.status == "approved":
        # If the incoming update data specifically *includes* a status change
        # (e.g., owner is trying to change it to 'available' or 'pending'),
        # we respect that. Otherwise, if they are just updating other fields,
        # and the status was 'approved', we revert it to 'pending_approval'.
        # This logic assumes the owner's update *should* trigger re-approval.
        # A more complex flow might allow minor edits without re-approval.
        # For this plan, we revert approved listings on update.
        if 'status' not in update_data or update_data['status'] != 'pending_approval':
             # If the status wasn't explicitly set to pending_approval or another allowed status,
             # or if it was 'approved', we force it back to pending_approval.
             # If it was already pending/rejected/needs_changes, keep its current status unless explicitly changed.
             if db_listing.status == "approved": # Only revert if it was previously approved
                update_data['status'] = "pending_approval"


    try:
        updated_listing = crud.update_listing(db=db, listing_id=listing_id, seller_id=current_user.user_id, update_data=update_data)
        if updated_listing is None:
            # This case should ideally be caught by the initial checks, but as a fallback:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found or not authorized for update.")
        return updated_listing
    except Exception as e:
        # Log the specific error with traceback on the backend
        import logging # Ensure logging is imported at the top if not already
        logger = logging.getLogger(__name__) # Get logger if not already defined
        logger.error(f"Error updating listing {listing_id} for user {current_user.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating listing. Check server logs for details.")

@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_listing = crud.get_listing(db, listing_id=listing_id)
    if db_listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    if db_listing.seller_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this listing")

    # Pass current_user.user_id as seller_id to the CRUD function for ownership check
    deleted = crud.delete_listing(db=db, listing_id=listing_id, seller_id=current_user.user_id)
    if not deleted:
        # This case should ideally be caught by the checks above (lines 249-252)
        # or indicates an issue within the CRUD operation despite passing initial checks.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete listing")
    return None


# Buyer reviews Seller
@router.post("/{listing_id}/reviews", response_model=schemas.Review, status_code=status.HTTP_201_CREATED)
async def create_listing_review_for_seller(
    listing_id: int,
    review: schemas.ReviewCreate, # Contains rating, comment
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    listing = crud.get_listing(db, listing_id=listing_id)
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    # crud.create_listing_review handles validation (buyer, sold status)
    return crud.create_listing_review(
        db=db,
        review_data=review,
        listing_id=listing_id,
        reviewer_id=current_user.user_id # Current user is the buyer (reviewer)
    )

@router.get("/{listing_id}/reviews", response_model=List[schemas.Review])
async def get_listing_reviews(listing_id: int, db: Session = Depends(get_db)):
    # Fetches reviews FOR A LISTING (i.e., reviews of the seller for that transaction)
    reviews = crud.get_reviews_for_listing(db, listing_id=listing_id)
    if not reviews: # Depending on how crud.get_reviews_for_listing handles "no reviews"
        # If it returns empty list, this check is not strictly needed unless you want 404 for no reviews
        pass # Allow empty list to be returned
    return reviews


# Seller reviews Buyer
@router.post("/{listing_id}/review-buyer", response_model=schemas.Review, status_code=status.HTTP_201_CREATED)
async def create_review_for_buyer(
    listing_id: int,
    review: schemas.ReviewCreate, # Contains rating, comment
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    listing = crud.get_listing(db, listing_id=listing_id)
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    if listing.seller_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the seller can review the buyer for this listing.")
    if not listing.buyer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Listing has no assigned buyer.")
    if listing.status != "sold": # Ensure listing is sold
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Listing is not sold. Cannot review buyer yet.")

    # Assumes a generic create_user_review or a specific crud.create_buyer_review_by_seller
    return crud.create_seller_review_for_buyer(
        db=db,
        review_data=review, # review is already schemas.ReviewCreate
        listing_id=listing_id,
        seller_id=current_user.user_id # Current user is the seller (reviewer)
    )

# Endpoint to check if the current buyer has already reviewed the seller for a specific listing
@router.get("/{listing_id}/has-buyer-reviewed", response_model=schemas.HasReviewedResponse)
async def check_if_buyer_has_reviewed_seller(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    listing = crud.get_listing(db, listing_id=listing_id)
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    if listing.status != "sold":
        # If the listing isn't sold, no review should exist from the buyer yet.
        # Frontend might handle this, but API should be robust.
        return {"has_reviewed": False, "detail": "Listing not sold."}

    if listing.buyer_id != current_user.user_id:
        # This endpoint is for the buyer to check their own review status for this seller.
        # Not for others to check.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not the buyer of this listing.")

    has_reviewed = crud.get_specific_review_existence(
        db=db,
        listing_id=listing_id,
        reviewer_id=current_user.user_id, # The buyer
        reviewee_id=listing.seller_id     # The seller
    )
    return {"has_reviewed": has_reviewed}

# TODO: Add endpoints for image management if needed (e.g., delete image, set primary image)
# TODO: Ensure all schemas and CRUD functions are correctly defined and imported.
