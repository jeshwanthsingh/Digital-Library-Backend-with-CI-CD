import os
import sys
import logging # Import logging
from sqlalchemy.orm import Session
from PIL import Image, ImageDraw, ImageFont
import random
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: [%(name)s] %(message)s')
logger = logging.getLogger(__name__) # Get a logger for this module

# --- Determine Project Root and Load .env ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root) # Add project root to Python path

dotenv_path = os.path.join(project_root, '.env')
if os.path.exists(dotenv_path):
    logger.info(f"Attempting to load environment variables from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
else:
    logger.warning(f".env file not found at {dotenv_path}. Environment variables might not be loaded for seeding if not set externally.")
    # Consider exiting if .env is critical and not found:
    # sys.exit("CRITICAL: .env file not found. Halting seed script.")

# --- Application-Specific Imports ---
# These modules should have their own load_dotenv() calls if they directly access os.getenv() at module level
try:
    from application.database.database import SessionLocal, engine, Base # Ensure Base is imported if create_tables uses it
    from application.database.models import Category, Listing, ListingImage, User, Conversation, Message, Review # Import all models
    from application.security import get_password_hash
except ImportError as e:
    logger.critical(f"Failed to import necessary application modules: {e}. Check PYTHONPATH and module availability.")
    sys.exit(1)


def create_tables():
    """Drop and recreate all tables in the database based on models imported via Base."""
    logger.warning("Dropping existing tables (if any)...")
    try:
        Base.metadata.drop_all(bind=engine) # Drop tables first
        logger.info("Existing tables dropped successfully.")
        Base.metadata.create_all(bind=engine) # Recreate tables with current schema
        logger.info("Database tables created successfully based on current models.")
    except Exception as e:
        logger.critical(f"Error during table creation/dropping: {e}")
        # Depending on the error, you might want to exit or handle it differently
        raise # Re-raise the exception to halt the script if table creation fails


def seed_users(db: Session):
    """Seed initial users with hashed passwords."""
    if db.query(User).count() > 0:
        logger.warning("Users already exist, skipping seeding users but fetching existing ones.")
        return db.query(User).order_by(User.user_id).all()

    users_data = [
        {"username": "user1", "email": "user1@sfsu.edu", "password": "password123", "is_admin": False},
        {"username": "user2", "email": "user2@sfsu.edu", "password": "password123", "is_admin": False},
        {"username": "user3", "email": "user3@sfsu.edu", "password": "password123", "is_admin": False},
        {"username": "user4", "email": "user4@sfsu.edu", "password": "password123", "is_admin": False},
        {"username": "admin1", "email": "admin1@sfsu.edu", "password": "adminpassword1", "is_admin": True},
        {"username": "admin2", "email": "admin2@sfsu.edu", "password": "adminpassword2", "is_admin": True},
    ]

    logger.info(f"Seeding {len(users_data)} users...")
    added_users = []
    for user_data in users_data:
        hashed_password = get_password_hash(user_data["password"])
        db_user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=hashed_password,
            is_active=True,
            is_admin=user_data.get("is_admin", False) # Get is_admin, default to False if not present
        )
        db.add(db_user)

    db.flush()

    for user_data in users_data: # This loop re-queries.
        user = db.query(User).filter_by(email=user_data["email"]).first()
        if user:
            added_users.append(user)
        else:
            logger.warning(f"Could not retrieve user {user_data['email']} after flush.")

    logger.info(f"Added {len(added_users)} users to the session.")
    return added_users


def seed_categories(db: Session):
    """Seed initial categories."""
    if db.query(Category).count() > 0:
        logger.warning("Categories already exist, skipping seeding categories.")
        return

    categories_data = [
        # 5 Item Categories
        {"name": "Electronics", "parent_id": None, "display_order": 1, "is_active": True, "is_skill_category": False},
        {"name": "Textbooks & Notes", "parent_id": None, "display_order": 2, "is_active": True, "is_skill_category": False},
        {"name": "Furniture & Decor", "parent_id": None, "display_order": 3, "is_active": True, "is_skill_category": False},
        {"name": "Clothing & Accessories", "parent_id": None, "display_order": 4, "is_active": True, "is_skill_category": False},
        {"name": "Miscellaneous Items", "parent_id": None, "display_order": 5, "is_active": True, "is_skill_category": False},

        # 5 Skill Categories
        {"name": "Tutoring Services", "parent_id": None, "display_order": 6, "is_active": True, "is_skill_category": True},
        {"name": "Creative Services", "parent_id": None, "display_order": 7, "is_active": True, "is_skill_category": True},
        {"name": "Technical Services", "parent_id": None, "display_order": 8, "is_active": True, "is_skill_category": True},
        {"name": "Personal Assistance", "parent_id": None, "display_order": 9, "is_active": True, "is_skill_category": True},
        {"name": "Workshops & Lessons", "parent_id": None, "display_order": 10, "is_active": True, "is_skill_category": True},
    ]
    logger.info(f"Seeding {len(categories_data)} categories...")
    for category_data in categories_data:
        db_category = Category(**category_data)
        db.add(db_category)
    logger.info(f"Added {len(categories_data)} categories to the session.")


def seed_listings(db: Session):
    """Seed sample listings."""
    if db.query(Listing).count() > 0:
        logger.warning("Listings already exist, skipping seeding listings but fetching existing ones.")
        return db.query(Listing).order_by(Listing.listing_id).all()

    # Category IDs:
    # Items: 1-Electronics, 2-Textbooks & Notes, 3-Furniture & Decor, 4-Clothing & Accessories, 5-Miscellaneous Items
    # Skills: 6-Tutoring Services, 7-Creative Services, 8-Technical Services, 9-Personal Assistance, 10-Workshops & Lessons
    listings_data = [
        # --- Approved Item Listings (using new category IDs) ---
        {"seller_id": 1, "title": "MacBook Pro 2023", "description": "Barely used MacBook Pro M2 chip, 16GB RAM, 512GB SSD. Comes with original charger and box.", "search_keywords": "laptop, apple, macbook, M2, electronics", "price": 1299.99, "category_id": 1, "item_condition": "like_new", "status": "approved", "is_skill_sharing": False, "rate": None, "rate_type": None, "availability": None},
        {"seller_id": 1, "title": "Dell XPS 13", "description": "Dell XPS 13 with Intel i7, 8GB RAM, 256GB SSD. Good for students.", "search_keywords": "laptop, dell, xps, windows, electronics", "price": 899.99, "category_id": 1, "item_condition": "good", "status": "approved", "is_skill_sharing": False, "rate": None, "rate_type": None, "availability": None},
        {"seller_id": 2, "title": "Database Systems Textbook", "description": "Textbook by Garcia-Molina for CSC675. Slightly used.", "search_keywords": "database, textbook, CSC675, SFSU, books", "price": 45.00, "category_id": 2, "item_condition": "good", "status": "approved", "is_skill_sharing": False, "rate": None, "rate_type": None, "availability": None},
        {"seller_id": 4, "title": "Standing Desk", "description": "Adjustable standing desk, black, 48x30 inches. Excellent for study or work.", "search_keywords": "desk, standing desk, furniture, home office", "price": 120.00, "category_id": 3, "item_condition": "like_new", "status": "approved", "is_skill_sharing": False, "rate": None, "rate_type": None, "availability": None},
        {"seller_id": 1, "title": "Winter Coat (Size M)", "description": "Warm winter coat, blue, size medium. Used for one season.", "search_keywords": "coat, jacket, winter, clothes, apparel", "price": 55.00, "category_id": 4, "item_condition": "good", "status": "approved", "is_skill_sharing": False, "rate": None, "rate_type": None, "availability": None},
        {"seller_id": 3, "title": "Wireless Mouse", "description": "Logitech wireless mouse, lightly used. Great for portability.", "search_keywords": "mouse, wireless, electronics, accessories", "price": 15.00, "category_id": 1, "item_condition": "like_new", "status": "sold", "buyer_id": 2, "sold_at": datetime.now(timezone.utc), "is_skill_sharing": False, "rate": None, "rate_type": None, "availability": None},
        {"seller_id": 2, "title": "SFSU Hoodie (Size L)", "description": "Official SFSU Gators hoodie, purple, size large. Good condition.", "search_keywords": "hoodie, sfsu, gators, apparel, clothing", "price": 25.00, "category_id": 4, "item_condition": "good", "status": "approved", "is_skill_sharing": False, "rate": None, "rate_type": None, "availability": None},
        {"seller_id": 3, "title": "Desk Lamp", "description": "LED desk lamp with adjustable brightness. Black.", "search_keywords": "lamp, light, desk, furniture, decor", "price": 20.00, "category_id": 3, "item_condition": "like_new", "status": "approved", "is_skill_sharing": False, "rate": None, "rate_type": None, "availability": None},

        # --- Pending Item Listings ---
        {"seller_id": 3, "title": "CSC648 Lecture Notes", "description": "Comprehensive notes from CSC648, Fall 2024.", "search_keywords": "notes, CSC648, software engineering, textbooks", "price": 15.00, "category_id": 2, "item_condition": "new", "status": "pending_approval", "is_skill_sharing": False, "rate": None, "rate_type": None, "availability": None},
        {"seller_id": 4, "title": "Vintage SFSU T-Shirt", "description": "Rare vintage SFSU t-shirt, good condition for its age.", "search_keywords": "vintage, sfsu, t-shirt, clothing, apparel", "price": 30.00, "category_id": 4, "item_condition": "good", "status": "pending_approval", "is_skill_sharing": False, "rate": None, "rate_type": None, "availability": None}, # Changed 'used' to 'good'
        # --- Approved Skill Listings (using new category IDs) ---
        {"seller_id": 4, "title": "Python Programming Tutoring", "description": "One-on-one Python programming tutoring for beginners to intermediate.", "search_keywords": "python, programming, tutoring, coding, education, skills", "price": None, "category_id": 6, "item_condition": "new", "status": "approved", "is_skill_sharing": True, "rate": 25.00, "rate_type": "hourly", "availability": "Weekends and evenings"},
        {"seller_id": 2, "title": "Math Tutoring for Calculus", "description": "Experienced tutor offering help with Calculus I & II. SFSU curriculum familiar.", "search_keywords": "math, calculus, tutoring, education, skills", "price": None, "category_id": 6, "item_condition": "new", "status": "approved", "is_skill_sharing": True, "rate": 30.00, "rate_type": "hourly", "availability": "Flexible, contact for details"},
        {"seller_id": 1, "title": "Event Photography", "description": "Professional event photography for campus events or personal shoots.", "search_keywords": "photography, event, skills, creative, services", "price": None, "category_id": 7, "item_condition": "new", "status": "approved", "is_skill_sharing": True, "rate": 100.00, "rate_type": "fixed", "availability": "Weekends primarily, book in advance"},
        {"seller_id": 3, "title": "Resume Writing & Review", "description": "Get help crafting a professional resume or cover letter.", "search_keywords": "resume, career, writing, editing, services, skills", "price": None, "category_id": 9, "item_condition": "new", "status": "approved", "is_skill_sharing": True, "rate": 40.00, "rate_type": "fixed", "availability": "By appointment"},
        {"seller_id": 4, "title": "Guitar Lessons for Beginners", "description": "Learn basic guitar chords and songs. Acoustic or electric.", "search_keywords": "guitar, music, lessons, education, skills, workshops", "price": None, "category_id": 10, "item_condition": "new", "status": "approved", "is_skill_sharing": True, "rate": 20.00, "rate_type": "hourly", "availability": "Tuesday and Thursday evenings"},

        # --- Pending Skill Listings ---
        {"seller_id": 2, "title": "Laptop Repair & Troubleshooting", "description": "Software troubleshooting and minor hardware repairs for laptops.", "search_keywords": "laptop, repair, tech, IT, services, skills", "price": None, "category_id": 8, "item_condition": "new", "status": "pending_approval", "is_skill_sharing": True, "rate": 50.00, "rate_type": "hourly", "availability": "Contact for availability"},
    ]
    logger.info(f"Seeding {len(listings_data)} listings...")
    added_listings = []
    for listing_data in listings_data:
        db_listing = Listing(**listing_data)
        db.add(db_listing)
        added_listings.append(db_listing)

    db.flush()
    refreshed_listings = []
    for l in added_listings:
        db.refresh(l)
        refreshed_listings.append(l)

    logger.info(f"Added {len(refreshed_listings)} listings to the session.")
    return refreshed_listings

def seed_listing_images(db: Session, listings: list[Listing]):
    if not listings:
        logger.warning("No listings provided to seed_listing_images, skipping.")
        return
    if db.query(ListingImage).count() > 0:
        logger.warning("Listing images already exist, skipping seeding listing images.")
        return

    base_static_dir = Path(__file__).resolve().parent.parent / "static"
    images_dir = base_static_dir / "images" / "listings"
    try:
        os.makedirs(images_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Could not create directory {images_dir}: {e}")
        return

    source_filename = "testimage.jpg"
    source_fs_path = images_dir / source_filename

    if not source_fs_path.exists():
        logger.error(f"Dummy image '{source_filename}' not found in '{images_dir}'. Attempting to create placeholder.")
        try:
            img = Image.new('RGB', (600, 400), color = (150, 150, 150))
            d = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except IOError:
                font = ImageFont.load_default()
            d.text((100,150), "Placeholder Image", fill=(255,255,0), font=font)
            img.save(source_fs_path, "JPEG")
            logger.info(f"Created dummy placeholder image: {source_fs_path}")
        except Exception as e:
            logger.error(f"Failed to create placeholder image: {e}")
            return

    thumb_filename = "testimage_thumb.jpg"
    thumb_fs_path = images_dir / thumb_filename
    thumb_size = (150, 100)

    if not thumb_fs_path.exists():
        try:
            logger.info(f"Generating thumbnail '{thumb_filename}' from '{source_filename}'...")
            with Image.open(source_fs_path) as img:
                img.thumbnail(thumb_size)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(thumb_fs_path, "JPEG")
            logger.info(f"Thumbnail '{thumb_filename}' created.")
        except Exception as e:
            logger.error(f"Failed to generate thumbnail for '{source_filename}': {e}")

    full_res_url_path = f"/static/images/listings/{source_filename}"
    thumb_url_path = f"/static/images/listings/{thumb_filename}" if thumb_fs_path.exists() else None

    images_added_count = 0
    logger.info(f"Assigning image paths to {len(listings)} listings...")
    for listing in listings:
        if not listing.listing_id:
            logger.error(f"Listing '{listing.title}' missing ID, cannot add image. Skipping.")
            continue
        image_data = {
            "listing_id": listing.listing_id,
            "image_path": full_res_url_path,
            "thumbnail_path": thumb_url_path,
            "display_order": 1,
            "is_primary": True
        }
        db_image = ListingImage(**image_data)
        db.add(db_image)
        images_added_count += 1
    logger.info(f"Added {images_added_count} listing image records to the session.")


def seed_conversations_and_messages(db: Session, users: list[User], listings: list[Listing]):
    if not users or not listings:
        logger.warning("Users or listings not provided, skipping conversation/message seeding.")
        return [], []

    if db.query(Conversation).count() > 0 or db.query(Message).count() > 0:
        logger.warning("Conversations or messages already exist, skipping seeding.")
        return db.query(Conversation).all(), db.query(Message).all()

    logger.info(f"Seeding conversations and messages for {len(users)} users and {len(listings)} listings...")
    added_conversations = []
    added_messages = []

    for user in users:
        if not user.user_id: logger.error(f"User {user.username} missing ID."); return [],[]
    for listing in listings:
        if not listing.listing_id: logger.error(f"Listing {listing.title} missing ID."); return [],[]

    if len(users) >= 2 and listings:
        buyer = users[0]
        potential_listing = next((l for l in listings if l.seller_id != buyer.user_id and not l.is_skill_sharing), None)
        if potential_listing:
            listing_seller = db.query(User).filter(User.user_id == potential_listing.seller_id).first()
            if listing_seller:
                conversation_data = {
                    "listing_id": potential_listing.listing_id,
                    "user1_id": buyer.user_id,
                    "user2_id": listing_seller.user_id
                }
                db_conversation = Conversation(**conversation_data)
                db.add(db_conversation)
                db.flush()
                added_conversations.append(db_conversation)
                messages_data = [
                    {"conversation_id": db_conversation.conversation_id, "sender_id": buyer.user_id, "content": f"Hi {listing_seller.username}, is your {potential_listing.title} still available?"},
                    {"conversation_id": db_conversation.conversation_id, "sender_id": listing_seller.user_id, "content": f"Hello {buyer.username}, yes it is! Are you interested?"},
                ]
                for msg_data in messages_data:
                    db_message = Message(**msg_data) # Create instance before adding
                    db.add(db_message)
                    added_messages.append(db_message)
            else:
                logger.warning(f"Seller for listing ID {potential_listing.listing_id} not found.")
        else:
            logger.warning("Could not find a suitable item listing for conversation 1.")
    else:
        logger.warning("Not enough users/listings for item conversation 1.")

    if len(users) >= 4:
        user_seeking_skill = users[2]
        skill_provider_user = next((u for u in users if u.user_id == 4), None) # Assuming user with ID 4 is a skill provider
        skill_listing = next((l for l in listings if l.title == "Python Programming Tutoring" and l.seller_id == (skill_provider_user.user_id if skill_provider_user else -1)), None)

        if skill_listing and skill_provider_user:
            conversation_data = {
                "listing_id": skill_listing.listing_id,
                "user1_id": user_seeking_skill.user_id,
                "user2_id": skill_provider_user.user_id
            }
            db_conversation = Conversation(**conversation_data)
            db.add(db_conversation)
            db.flush()
            added_conversations.append(db_conversation)
            messages_data = [
                {"conversation_id": db_conversation.conversation_id, "sender_id": user_seeking_skill.user_id, "content": "Hi, I'm interested in your Python tutoring services."},
                {"conversation_id": db_conversation.conversation_id, "sender_id": skill_provider_user.user_id, "content": "Sure, I'd be happy to help. What are you looking to learn?"},
            ]
            for msg_data in messages_data:
                db_message = Message(**msg_data)
                db.add(db_message)
                added_messages.append(db_message)
        else:
            logger.warning("Could not find 'Python Programming Tutoring' by user4 or user4 not found for skill conversation 2.")
    else:
        logger.warning("Not enough users for skill conversation 2.")

    logger.info(f"Added {len(added_conversations)} conversations and {len(added_messages)} messages to the session.")
    return added_conversations, added_messages


def seed_reviews(db: Session, users: list[User], listings: list[Listing]):
    if not users or not listings:
        logger.warning("Users or listings not provided, skipping review seeding.")
        return []

    if db.query(Review).count() > 0:
        logger.warning("Reviews already exist, skipping seeding reviews.")
        return db.query(Review).all()

    logger.info(f"Seeding reviews...")
    added_reviews = []

    for user in users:
        if not user.user_id: logger.error(f"User {user.username} missing ID."); return []
    for listing in listings:
        if not listing.listing_id: logger.error(f"Listing {listing.title} missing ID."); return []

    if len(users) >= 2:
        reviewer = users[0] # user1
        iphone_listing = next((l for l in listings if l.title == "iPhone 14 Pro" and l.status == "sold"), None)
        if not iphone_listing: # Fallback to any sold listing if iPhone 14 Pro is not sold or doesn't exist.
             iphone_listing = next((l for l in listings if l.status == "sold" and l.buyer_id == reviewer.user_id), None)

        if iphone_listing and iphone_listing.buyer_id == reviewer.user_id: # Ensure user1 is the buyer
            if iphone_listing.seller_id != reviewer.user_id :
                seller = db.query(User).filter(User.user_id == iphone_listing.seller_id).first()
                if seller:
                    review_data = {"listing_id": iphone_listing.listing_id, "reviewer_id": reviewer.user_id, "reviewee_id": seller.user_id, "rating": 5, "comment": "Great phone, exactly as described! Seller was very responsive."}
                    db_review = Review(**review_data)
                    db.add(db_review)
                    added_reviews.append(db_review)
                else: logger.warning(f"Seller for listing '{iphone_listing.title}' not found for review 1.")
            else: logger.warning(f"Skipping review for '{iphone_listing.title}' because reviewer {reviewer.username} is the seller.")
        else: logger.warning(f"Could not find a suitable sold listing where user1 is the buyer for review 1, or 'iPhone 14 Pro' (sold) not found.")
    else: logger.warning("Not enough users for review 1.")

    if len(users) >= 4:
        reviewer = users[2] # user3
        skill_provider_user = next((u for u in users if u.user_id == 4), None)
        python_tutoring_listing = next((l for l in listings if l.title == "Python Programming Tutoring" and l.seller_id == (skill_provider_user.user_id if skill_provider_user else -1) and l.status == "sold"), None) # Assuming skills can be "sold"

        if python_tutoring_listing and skill_provider_user and python_tutoring_listing.buyer_id == reviewer.user_id : # Ensure user3 is the "buyer" of the skill
            if python_tutoring_listing.seller_id != reviewer.user_id:
                review_data = {"listing_id": python_tutoring_listing.listing_id, "reviewer_id": reviewer.user_id, "reviewee_id": skill_provider_user.user_id, "rating": 4, "comment": "Very helpful tutoring. Explained concepts clearly."}
                db_review = Review(**review_data)
                db.add(db_review)
                added_reviews.append(db_review)
            else: logger.warning(f"Skipping review for '{python_tutoring_listing.title}' because reviewer {reviewer.username} is the seller.")
        else: logger.warning(f"Could not find 'Python Programming Tutoring' by user4 as a sold skill to user3, or user4 not found for review 2.")
    else: logger.warning("Not enough users for review 2.")

    logger.info(f"Added {len(added_reviews)} reviews to the session.")
    return added_reviews


def run_all():
    db = SessionLocal()
    try:
        logger.info("Starting all seeding operations...")
        create_tables()
        all_users = seed_users(db)
        seed_categories(db)
        all_listings = seed_listings(db)

        if all_listings:
            seed_listing_images(db, all_listings)
        else:
            logger.warning("No listings available to seed images for.")

        if all_users and all_listings:
            seed_conversations_and_messages(db, all_users, all_listings)
        else:
            logger.warning("Skipping conversation/message seeding due to missing users or listings.")

        if all_users and all_listings:
            seed_reviews(db, all_users, all_listings)
        else:
            logger.warning("Skipping review seeding due to missing users or listings.")

        db.commit()
        logger.info("All seeding operations completed and data committed successfully.")

    except Exception as e:
        logger.critical(f"An error occurred during seeding: {e}", exc_info=True)
        db.rollback()
        logger.error("Seeding failed. Database has been rolled back.")
    finally:
        db.close()
        logger.info("Database session closed.")

if __name__ == "__main__":
    logger.info("Executing seed script directly.")
    run_all()