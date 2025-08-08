from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging # Add logging import
import datetime
from application.security import get_current_active_user

from application.database.database import get_db
from application.database import crud
# Import ListingCreate along with other schemas
from application.schemas import SearchResults, Listing as ListingSchema, Category as CategorySchema, ListingCreate, ListingUpdate, Review as ReviewSchema, ReviewCreate # Renamed Listing to ListingSchema to avoid conflict

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from application.database.models import User
from application.schemas import UserRead, UserCreate, Listing # Renamed Listing to ListingSchema
from sqlalchemy.orm import Session
from fastapi import status

router = APIRouter()

# JWT settings and get_current_user are now centralized in application.security
# Endpoints in this router requiring authentication should import and use
# get_current_active_user from application.security

# @router.post("/listings", response_model=ListingSchema)
# def create_listing(listing: ListingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
#     # The create_listing CRUD function expects a ListingCreate schema
#     return crud.create_listing(db, listing, seller_id=current_user.user_id)

# @router.put("/listings/{listing_id}", response_model=ListingSchema) # Use ListingSchema for response
# def update_listing(
#     listing_id: int,
#     listing_data: ListingUpdate, # Use ListingUpdate for request body
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     # Authorization: Check if the listing exists and if the current user is the seller
#     # This check is also performed within crud.update_listing, but an early check here is good practice.
#     existing_listing = crud.get_listing(db, listing_id)
#     if not existing_listing:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
#     if existing_listing.seller_id != current_user.user_id:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this listing")
#
#     # Convert Pydantic model to dict, excluding unset fields to only update provided values
#     update_data_dict = listing_data.model_dump(exclude_unset=True)
#
#     if not update_data_dict:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided")
#
#     updated_listing = crud.update_listing(
#         db,
#         listing_id=listing_id,
#         seller_id=current_user.user_id, # Pass seller_id for authorization in CRUD
#         update_data=update_data_dict
#     )
#
#     if not updated_listing:
#         # This might happen if crud.update_listing returns None due to an internal issue
#         # or if the seller cannot be buyer condition was met in crud.
#         # The get_listing check above should catch most "not found" or "not authorized".
#         # If crud.update_listing itself can return None for specific business logic failures (e.g. seller = buyer),
#         # then a more specific error might be needed. For now, a generic 400 or 404 if not found after all.
#         # Re-checking the existing_listing for seller_id == buyer_id (if buyer_id in update_data_dict)
#         if 'buyer_id' in update_data_dict and update_data_dict['buyer_id'] == existing_listing.seller_id:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seller cannot be the buyer.")
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found or update failed")
#
#     return updated_listing

# @router.delete("/listings/{listing_id}")
# def delete_listing(listing_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
#     db_listing = crud.get_listing(db, listing_id)
#     if not db_listing or db_listing.seller_id != current_user.user_id:
#         raise HTTPException(status_code=403, detail="Not authorized to delete this listing")
#     success = crud.delete_listing(db, listing_id, seller_id=current_user.user_id)
#     if not success:
#         raise HTTPException(status_code=404, detail="Listing not found or not deleted")
#     return {"detail": "Listing deleted"}

@router.get("/search", response_model=SearchResults)
async def search_listings(
    q: Optional[str] = Query(None, description="Search query for title, description, or keywords", min_length=0, max_length=40, regex="^[a-zA-Z0-9 ]*$"),
    category_id: Optional[int] = Query(None, description="Filter by category ID. 0 means all categories."),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter."),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter."),
    item_condition: Optional[str] = Query(None, description="Filter by item condition (e.g., 'new', 'used')."),
    is_skill_sharing: Optional[bool] = Query(None, description="Filter by skill sharing status."),
    status: Optional[str] = Query('approved', description="Filter by listing status (e.g., 'available', 'sold', 'approved'). Defaults to 'approved'."),
    page: int = Query(1, ge=1, description="Page number for pagination."),
    page_size: int = Query(20, ge=1, le=100, description="Number of results per page."),
    db: Session = Depends(get_db)
):
    """
    Search for listings with optional filters including skill sharing status and listing status.
    
    - q: Search query.
    - category_id: Filter by category.
    - status: Filter by listing status (e.g., 'available', 'sold').
    - All filters are applied with AND condition.
    """
    logging.info(
        f"Searching listings with q='{q}', category_id={category_id}, status='{status}', "
        f"min_price={min_price}, max_price={max_price}, item_condition='{item_condition}', "
        f"is_skill_sharing={is_skill_sharing}, page={page}, page_size={page_size}"
    )
    try:
        # Calculate skip for pagination
        skip = (page - 1) * page_size
        
        # Get results and total count
        results = crud.get_listings(
            db, 
            skip=skip, 
            limit=page_size,
            search=q,
            category_id=category_id if category_id and category_id > 0 else None,
            min_price=min_price,
            max_price=max_price,
            item_condition=item_condition,
            is_skill_sharing=is_skill_sharing,
            status=status # Pass status parameter
        )
        
        total_count = crud.count_search_results( 
            db,
            search=q,
            category_id=category_id if category_id and category_id > 0 else None,
            min_price=min_price,
            max_price=max_price,
            item_condition=item_condition,
            is_skill_sharing=is_skill_sharing,
            status=status # Pass status parameter
        )
        
        logging.info(f"Found {total_count} results for search criteria.")
        return SearchResults(total=total_count, results=results)
    except Exception as e:
        logging.error(f"Error in search_listings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during search")

@router.get("/categories", response_model=List[CategorySchema])
async def get_categories(
    parent_id: Optional[int] = None, 
    is_skill: Optional[bool] = None, # Add query parameter for skill/item type
    db: Session = Depends(get_db)
):
    """
    Get all active categories, optionally filtered by parent_id and is_skill_category.
    """
    logging.info(f"Getting categories with parent_id={parent_id}, is_skill={is_skill}")
    try:
        # Pass the is_skill filter to the CRUD function
        categories = crud.get_categories(db, parent_id=parent_id, is_skill=is_skill, active_only=True) 
        logging.info(f"Found {len(categories)} categories matching criteria.")
        return categories
    except Exception as e:
        logging.error(f"Error in get_categories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error getting categories")

@router.get("/categories/{category_id}", response_model=CategorySchema)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    """
    Get a specific category by ID.
    """
    category = crud.get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

# @router.get("/listings/{listing_id}", response_model=ListingSchema)
# async def get_listing(listing_id: int, db: Session = Depends(get_db)):
#     """
#     Get a specific listing by ID.
#     """
#     listing = crud.get_listing(db, listing_id)
#     if listing is None:
#         raise HTTPException(status_code=404, detail="Listing not found")
#
#     # Increment view count
#     if listing:
#         listing.views_count += 1 # This should be an ORM attribute access, not +=1 on an int if it's from a dict.
                                   # models.Listing.views_count should be used.
#         db.commit()
#
#     return listing

from fastapi import UploadFile, File
import shutil
import os
from PIL import Image

# @router.post("/listings/{listing_id}/images")
# def upload_listing_image(
#     listing_id: int,
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     # Check listing ownership
#     db_listing = crud.get_listing(db, listing_id)
#     if not db_listing or db_listing.seller_id != current_user.user_id:
#         raise HTTPException(status_code=403, detail="Not authorized to upload images for this listing")
#
#     # Save uploaded file
#     # Ensure this path aligns with BACKEND_STATIC_DIR if reactivated
#     images_dir = os.path.join("application", "static", "images", "listings")
#     os.makedirs(images_dir, exist_ok=True)
#     file_ext = os.path.splitext(file.filename)[1]
#     # Corrected datetime usage:
#     # image_filename = f"listing_{listing_id}_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}{file_ext}"
#     image_filename = f"listing_{listing_id}_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}{file_ext}" # Corrected
#     image_path = os.path.join(images_dir, image_filename)
#
#     with open(image_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
#
#     # Generate thumbnail
#     thumb_filename = f"thumb_{image_filename}"
#     thumb_path = os.path.join(images_dir, thumb_filename)
#     with Image.open(image_path) as img:
#         img.thumbnail((256, 256))
#         img.save(thumb_path)
#
#     # Store relative paths for serving
#     rel_image_path = f"images/listings/{image_filename}"
#     rel_thumb_path = f"images/listings/{thumb_filename}"
#
#     # Add to database
#     listing_image = crud.create_listing_image(
#         db,
#         listing_id=listing_id,
#         image_path=rel_image_path,
#         thumbnail_path=rel_thumb_path,
#         display_order=0,
#         is_primary=False
#     )
#     return {"image_id": listing_image.image_id, "image_path": rel_image_path, "thumbnail_path": rel_thumb_path}

# Review Endpoints
# @router.post("/listings/{listing_id}/reviews", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
# def create_listing_review(
#     listing_id: int,
#     review_data: ReviewCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     listing = crud.get_listing(db, listing_id)
#     if not listing:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
#
#     # Determine reviewee_id:
#     # If current_user is the seller, then reviewee is the buyer.
#     # If current_user is the buyer, then reviewee is the seller.
#     reviewee_id: Optional[int] = None
#     if listing.status != "sold":
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reviews can only be left for sold listings.")
#
#     if listing.buyer_id is None: # Should not happen if status is "sold" but good to check
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Listing has no buyer.")
#
#     if current_user.user_id == listing.seller_id:
#         reviewee_id = listing.buyer_id
#     elif current_user.user_id == listing.buyer_id:
#         reviewee_id = listing.seller_id
#     else:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to review this transaction.")
#
#     if reviewee_id == current_user.user_id: # Should be caught by previous logic, but as a safeguard
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot review yourself.")
#
#     # Check if a review already exists from this user for this transaction role
#     # (e.g., buyer reviewing seller for this listing)
#     # This depends on how crud.create_review handles uniqueness. Assuming it might raise an IntegrityError.
#     # For now, we let the CRUD handle potential duplicates or add a specific check here if needed.
#
#     # The ReviewCreate schema doesn't have reviewer_id or reviewee_id, these are set here.
#     # The schema *does* have them, but they are filled by the endpoint logic not by the client.
#     # Let's adjust how we pass to crud.create_review. It expects a ReviewCreate schema.
#     # We should ensure the review_data passed to crud.create_review has these fields correctly set.
#     # The schema definition has listing_id, reviewer_id, reviewee_id, rating, comment.
#     # Client should only send rating and comment. listing_id is path param. reviewer_id is current_user. reviewee_id is derived.
#
#
#     # We should populate reviewer_id and reviewee_id directly for the crud.create_review call
#     # The ReviewCreate schema is used as a base, so the client shouldn't send reviewer_id or reviewee_id.
#     # The `review_data` from the client should be a subset.
#     # Let's assume ReviewCreate can be instantiated with all fields.
#     # The Pydantic model `ReviewCreate` as defined includes `reviewer_id` and `reviewee_id`.
#     # It's better if client *doesn't* send these.
#
#     try:
#         if current_user.user_id == listing.buyer_id:
#             # Current user is the buyer, reviewing the seller
#             created_review = crud.create_listing_review(
#                 db=db,
#                 review_data=review_data,  # Pass the ReviewCreate schema from request
#                 listing_id=listing_id,
#                 reviewer_id=current_user.user_id
#             )
#         elif current_user.user_id == listing.seller_id:
#             # Current user is the seller, reviewing the buyer
#             # Ensure reviewee_id (buyer_id) was determined correctly and is not None
#             if reviewee_id is None: # reviewee_id was listing.buyer_id
#                  raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot review: Listing buyer not found.")
#             created_review = crud.create_seller_review_for_buyer(
#                 db=db,
#                 review_data=review_data, # Pass the ReviewCreate schema from request
#                 listing_id=listing_id,
#                 seller_id=current_user.user_id # seller_id is the reviewer
#             )
#         else:
#             # This case should have been caught by earlier authorization checks (lines 281-282)
#             # If somehow reached, it's an internal logic error or unforeseen state.
#             logging.error(f"Review authorization logic failure: user {current_user.user_id} not buyer or seller for listing {listing_id}")
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Review processing error due to authorization mismatch.")
#
#         return created_review
#     except ValueError as e:
#         # Catch ValueErrors raised from CRUD functions (e.g., listing not sold, not buyer)
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
#     except Exception as e:
#         logging.error(f"Unhandled error creating review in search.py for listing {listing_id}: {e}", exc_info=True)
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the review.")

# @router.get("/listings/{listing_id}/reviews", response_model=List[ReviewSchema])
# def get_reviews_for_listing(
#     listing_id: int,
#     db: Session = Depends(get_db)
#     # No current_user needed as reviews are public for a listing.
# ):
#     """
#     Get all reviews for a specific listing.
#     """
#     # Optional: Check if listing exists first, though crud.get_reviews_by_listing might be fine
#     listing = crud.get_listing(db, listing_id)
#     if not listing:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
#
#     reviews = crud.get_reviews_for_listing(db, listing_id=listing_id)
#     # crud.get_reviews_by_listing should return an empty list if no reviews, which is fine.
#     return reviews

@router.get("/users/{user_id}/reviews", response_model=List[ReviewSchema])
def get_reviews_for_user(
    user_id: int,
    db: Session = Depends(get_db)
    # No current_user needed if reviews are public once created.
    # If only involved parties (or admins) can see reviews, add current_user and authorization.
):
    """
    Get all reviews where the specified user is the reviewee.
    """
    # Optional: Check if user exists, though crud.get_reviews_for_user might handle it gracefully
    # user = crud.get_user(db, user_id) # Assuming a get_user by ID exists in crud
    # if not user:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    reviews = crud.get_reviews_for_user(db, reviewee_id=user_id)
    if not reviews:
        # Return empty list if no reviews, or 404 if user not found and that's a desired behavior
        # For now, consistent with returning an empty list.
        pass
    return reviews

@router.get("/reviews/{review_id}", response_model=ReviewSchema)
def get_review_by_id(
    review_id: int,
    db: Session = Depends(get_db)
    # No current_user needed if reviews are public.
):
    """
    Get a specific review by its ID.
    """
    review = crud.get_review_by_id(db, review_id=review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review
