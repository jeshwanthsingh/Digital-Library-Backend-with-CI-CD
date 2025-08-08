<script>
  import { onMount } from 'svelte';
  import { push } from 'svelte-spa-router';
  import { get } from 'svelte/store'; // Import the get function
  import { formatRate } from '../lib/formatters.js'; // Import the formatRate utility
  // import { createConversation } from '../stores/messagingStore.js'; // Removed, handled by ContactUserButton
  import { user as authUserStore, isAuthenticated } from '../stores/authStore.js'; // Import auth store and user
  import ContactUserButton from './messaging/ContactUserButton.svelte'; // Import the new button

  // Props passed by the router
  export let params = {};

  // State
  let listing = null;
  let loading = true;
  let error = null;
  let activeImageIndex = 0;
  let reviews = [];
  let reviewsLoading = false;
  let reviewsError = null;

  // State for review submission
  let showReviewForm = false;
  let reviewRating = null; // Initial rating, e.g., 1-5 stars
  let reviewComment = '';
  let reviewSubmitting = false;
  let reviewSubmitError = null;
  let reviewSubmittedSuccessfully = false; // To hide form or show success message

  // State for seller review submission (seller reviews buyer)
  let showSellerReviewForm = false;
  let sellerReviewRating = null;
  let sellerReviewComment = '';
  let sellerReviewSubmitting = false;
  let sellerReviewSubmitError = null;
  let sellerReviewSubmittedSuccessfully = false;

  // Reactive statement to determine if the current user can leave a review

  // Helper function to check if the user (buyer) has already reviewed this listing (seller)
  function hasUserAlreadyReviewed(userId) {
    console.log('[DEBUG] hasUserAlreadyReviewed called with userId:', userId, 'Type:', typeof userId);
    console.log('[DEBUG] current listing.listing_id:', listing?.listing_id, 'Type:', typeof listing?.listing_id);
    console.log('[DEBUG] current listing.seller?.user_id:', listing?.seller?.user_id, 'Type:', typeof listing?.seller?.user_id);
    if (!reviews || reviews.length === 0 || !userId || !listing) {
      console.log('[DEBUG] hasUserAlreadyReviewed: Guard clause hit (no reviews, userId, or listing). Returning false.');
      return false;
    }
    let foundReview = false;
    const result = reviews.some((review, index) => {
      // Ensure consistent types for comparison, especially if IDs might be numbers or strings
      const currentUserId = String(userId);
      const reviewReviewerUserId = String(review.reviewer?.user_id);
      const currentListingId = String(listing.listing_id);
      const reviewListingId = String(review.listing_id);
      const currentSellerUserId = String(listing.seller?.user_id);
      const reviewRevieweeUserId = String(review.reviewee?.user_id);

      const reviewerIdMatch = reviewReviewerUserId === currentUserId;
      const listingIdMatch = reviewListingId === currentListingId; // Corrected: compare review's listing_id
      const revieweeIdMatch = reviewRevieweeUserId === currentSellerUserId;
          
      if (index < 3 || (reviewerIdMatch && listingIdMatch)) { // Log first few or potential matches
          console.log(`[DEBUG] hasUserAlreadyReviewed - Review #${index}:`, {
              review_reviewer_id: review.reviewer?.user_id, review_listing_id: review.listing_id, review_reviewee_id: review.reviewee?.user_id,
              type_review_reviewer_id: typeof review.reviewer?.user_id, type_review_listing_id: typeof review.listing_id, type_review_reviewee_id: typeof review.reviewee?.user_id,
              currentUserId, reviewReviewerUserId, currentListingId, reviewListingId, currentSellerUserId, reviewRevieweeUserId, // Log casted values
              reviewerIdMatch, listingIdMatch, revieweeIdMatch
          });
      }

      if (reviewerIdMatch && listingIdMatch && revieweeIdMatch) {
        foundReview = true;
        console.log(`[DEBUG] hasUserAlreadyReviewed: Match found at index ${index}`);
        return true; 
      }
      return false;
    });
    console.log('[DEBUG] hasUserAlreadyReviewed: Result:', result, '(Found Review:', foundReview, ')');
    return result;
  }

  // Helper function to check if the seller has already reviewed the buyer for this listing
  function hasSellerAlreadyReviewedBuyer(sellerId, buyerId, listingId) {
    if (!reviews || reviews.length === 0 || !sellerId || !buyerId || !listingId) return false;
    return reviews.some(review =>
        review.reviewer?.user_id === sellerId &&
        review.reviewee?.user_id === buyerId &&
        review.listing_id === listingId
    );
  }

  $: canLeaveReview = $isAuthenticated &&
                        listing &&
                        listing.status === 'sold' && // Only allow reviews for 'sold' listings
                        $authUserStore && $authUserStore.user_id &&
                        listing.buyer_id === $authUserStore.user_id && // Only the buyer can leave a review for the seller
                        listing.seller?.user_id !== $authUserStore.user_id && // Buyer is not the seller
                        !hasUserAlreadyReviewed($authUserStore.user_id) &&
                        !reviewSubmittedSuccessfully;

  // This should be AFTER your existing $: canLeaveReview = ...
  $: {
    if (listing && $authUserStore && typeof $authUserStore.user_id !== 'undefined') { // Added check for authUserStore.user_id
      const _isAuthenticated = $isAuthenticated;
      const _isSold = listing?.status === 'sold';
      const _isBuyer = listing.buyer_id === $authUserStore.user_id;
      const _isNotSeller = listing.seller?.user_id !== $authUserStore.user_id;
          
      // Temporarily store the result of hasUserAlreadyReviewed to avoid double logging if it's complex
      // or ensure hasUserAlreadyReviewed is idempotent if called multiple times.
      // The previous call within canLeaveReview definition would have already logged.
      const _hasNotReviewedCheckValue = !hasUserAlreadyReviewed($authUserStore.user_id);                                                                 // This call will trigger its own logs again.
      const _reviewNotSubmittedThisSession = !reviewSubmittedSuccessfully;

      console.log('[DEBUG] canLeaveReview constituents check (values used by canLeaveReview):', {
        _isAuthenticated,
        listingExists: !!listing,
        listingStatus: listing?.status,
        _isSold,
        authUserStoreExists: !!$authUserStore,
        authUserId: $authUserStore?.user_id,
        authUserIdExists: typeof $authUserStore?.user_id !== 'undefined',
        listingBuyerId: listing?.buyer_id,
        _isBuyer,
        listingSellerUserId: listing?.seller?.user_id,
        _isNotSeller,
        _hasNotReviewedValueFromThisBlock: _hasNotReviewedCheckValue, // Reflects the check from this block
        _reviewNotSubmittedThisSession,
        finalCanLeaveReviewValue: canLeaveReview // Log the actual calculated value of canLeaveReview
      });
    } else {
      // console.log('[DEBUG] canLeaveReview constituents: Waiting for listing or authUserStore.user_id');
    }
  }

  $: canSellerLeaveReviewForBuyer = $isAuthenticated &&
                                    listing &&
                                    listing.status === 'sold' && // Listing must be sold
                                    listing.buyer_id && // There must be a buyer
                                    $authUserStore && $authUserStore.user_id &&
                                    listing.seller?.user_id === $authUserStore.user_id && // Current user is the seller
                                    listing.buyer_id !== $authUserStore.user_id && // Seller is not reviewing themselves as buyer
                                    !hasSellerAlreadyReviewedBuyer($authUserStore.user_id, listing.buyer_id, listing.listing_id) &&
                                    !sellerReviewSubmittedSuccessfully;
  // let isInitiatingConversation = false; // Removed, handled by ContactUserButton

  // API base URL
  const API_BASE_URL = window.location.origin + '/api';

  // Fetch listing reviews
  async function fetchListingReviews(listingId) {
    if (!listingId) return;
    reviewsLoading = true;
    reviewsError = null;
    try {
      const response = await fetch(`${API_BASE_URL}/listings/${listingId}/reviews`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Failed to load reviews with status: ${response.status}` }));
        throw new Error(errorData.detail || `Failed to load reviews with status: ${response.status}`);
      }
      reviews = await response.json();
      console.log('Listing reviews loaded:', reviews);
    } catch (err) {
      console.error(`Error loading reviews for listing ${listingId}:`, err);
      reviewsError = err.message || 'Failed to load reviews';
      reviews = [];
    } finally {
      reviewsLoading = false;
    }
  }

  // Fetch listing details
  async function fetchListingDetails() {
    if (!params.id) return;

    try {
      loading = true;
      error = null;
      listing = null; // Reset listing
      reviews = []; // Reset reviews
      reviewsError = null; // Reset reviews error

      const token = localStorage.getItem('access_token');
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      // If no token, and the endpoint strictly requires auth, it will fail.
      // The endpoint GET /listings/{id} currently requires auth.
      const response = await fetch(`${API_BASE_URL}/listings/${params.id}`, { headers });

      if (!response.ok) {
        throw new Error(`Failed to load listing with status: ${response.status}`);
      }

      listing = await response.json();
      console.log('Listing details loaded:', listing);

      // If listing is loaded successfully, fetch its reviews
      if (listing && listing.listing_id) {
        await fetchListingReviews(listing.listing_id);
      }

    } catch (err) {
      console.error(`Error loading listing ${params.id}:`, err);
      error = err.message || 'Failed to load listing details';
      listing = null;
    } finally {
      loading = false;
    }
  }

  // Function to get image path
  function getImagePath(listing, index = 0) {
    // Use the test image as fallback if no images are present
    if (!listing || !listing.images || listing.images.length === 0) {
      return '/static/images/listings/testimage.jpg'; // Use the test image
    }

    let imgPath;

    // Prioritize primary image if available and index is 0 (or default)
    if (index === 0 && listing.images.some(img => img.is_primary)) {
      const primaryImage = listing.images.find(img => img.is_primary);
      imgPath = primaryImage.image_path;
    } else {
      // Otherwise, get image at specified index or fall back to first image
      const targetIndex = Math.min(index, listing.images.length - 1);
      imgPath = listing.images[targetIndex].image_path;
    }

    // Ensure image path is absolute relative to the backend server root
    if (imgPath && imgPath.startsWith('/')) {
        // No need to add window.location.origin, proxy handles it
        // return window.location.origin + imgPath; // Incorrect for proxied requests
        return imgPath; // Return the path as is, e.g., /static/images/listings/foo.jpg
    } else if (imgPath) {
        // If it's somehow not starting with /, prepend /static/
        // This case might indicate an issue with how paths are stored in DB
        console.warn("Image path doesn't start with /:", imgPath);
        return `/static/images/listings/${imgPath}`;
    }

    // Final fallback if imgPath logic fails
    return '/static/images/listings/testimage.jpg';
  }

  function setActiveImage(index) {
    activeImageIndex = index;
  }

  function nextImage() {
    if (listing && listing.images && listing.images.length > 0) {
      activeImageIndex = (activeImageIndex + 1) % listing.images.length;
    }
  }

  function prevImage() {
    if (listing && listing.images && listing.images.length > 0) {
      activeImageIndex = (activeImageIndex - 1 + listing.images.length) % listing.images.length;
    }
  }

  function goBack() {
    // Read the 'from' query parameter
    const urlParams = new URLSearchParams(window.location.search);
    const fromPath = urlParams.get('from') || '/'; // Default to home if not present
    push(fromPath);
  }

  // Fetch listing on mount
  onMount(async () => { // Make onMount async
    console.log('[DEBUG] ListingDetail onMount: Fetching details...');
    await fetchListingDetails(); // Ensure fetchListingDetails is awaited
    console.log('[DEBUG] ListingDetail onMount - Data after fetch:');
    console.log('[DEBUG] Listing:', listing);
    console.log('[DEBUG] AuthUserStore:', $authUserStore);
    console.log('[DEBUG] Reviews array (first 3):', reviews.slice(0, 3));
    if (reviews && reviews.length > 0) { // Added a check for reviews existence
      console.log('[DEBUG] Sample review object:', reviews[0]);
    } else {
      console.log('[DEBUG] Reviews array is empty or undefined.');
    }
  });

  // Removed handleContactSeller function as its logic is now in ContactUserButton.svelte
  // async function handleContactSeller() { ... }
  // Handle review submission (buyer reviews listing/seller)
  async function handleSubmitReview() {
    if (!listing || !listing.listing_id || reviewRating === null || reviewComment.trim() === '') {
      reviewSubmitError = 'Please provide a rating and a comment.';
      return;
    }

    reviewSubmitting = true;
    reviewSubmitError = null;
    reviewSubmittedSuccessfully = false;

    try {
      const token = get(authUserStore)?.token; // Get token from authStore
      if (!token) {
        throw new Error('Authentication token not found. Please log in.');
      }

      // Buyer reviews the listing (implicitly the seller of the listing)
      const response = await fetch(`${API_BASE_URL}/listings/${listing.listing_id}/reviews`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
                  rating: reviewRating,
          comment: reviewComment.trim(),
          listing_id: listing.listing_id, // Add listing_id to the request body
          // reviewee_id is not sent here; backend derives it from listing for buyer reviews

          // reviewee_id is not sent here; backend derives it from listing for buyer reviews
        }),
      });

      if (!response.ok) {
                const errorData = await response.json().catch(() => ({})); // Catch if JSON parsing fails, return empty object
        let errorMessage = `Failed to submit review. Status: ${response.status}`; // Default message
        if (errorData && errorData.detail) {
            if (typeof errorData.detail === 'string') {
                errorMessage = errorData.detail;
            } else if (Array.isArray(errorData.detail)) {
                // Format Pydantic-like validation errors for better readability
                errorMessage = errorData.detail.map(err => {
                    const loc = err.loc && err.loc.length > 1 ? err.loc.slice(1).join(' > ') : (err.loc && err.loc.length === 1 ? err.loc[0] : '');
                    return `${loc ? `Field '${loc}': ` : ''}${err.msg}`;
                }).join('; ');
            } else if (typeof errorData.detail === 'object') {
                // Fallback for other object-based error details
                errorMessage = JSON.stringify(errorData.detail);
            }
        } else if (response.statusText && response.status !== 422) { // Use statusText if no JSON detail, unless it's a generic 422 message
            errorMessage = response.statusText;
        }
        throw new Error(errorMessage);

      }

      const newReview = await response.json();
      reviews = [newReview, ...reviews]; // Add new review to the top of the list
      reviewSubmittedSuccessfully = true;
      showReviewForm = false; // Hide form after successful submission
      // Reset form fields
      reviewRating = null;
      reviewComment = '';

    } catch (err) {
      console.error('Error submitting review:', err);
      reviewSubmitError = err.message || 'An unexpected error occurred while submitting your review.';
    } finally {
      reviewSubmitting = false;
    }
  }

  // Handle seller's review submission (seller reviews buyer)
  async function handleSubmitSellerReview() {
    if (!listing || !listing.listing_id || !listing.buyer_id || sellerReviewRating === null || sellerReviewComment.trim() === '') {
      sellerReviewSubmitError = 'Please select a buyer, provide a rating, and a comment.';
      return;
    }

    sellerReviewSubmitting = true;
    sellerReviewSubmitError = null;
    sellerReviewSubmittedSuccessfully = false;

    try {
      const token = get(authUserStore)?.token;
      if (!token) {
        throw new Error('Authentication token not found. Please log in.');
      }

      const response = await fetch(`${API_BASE_URL}/listings/${listing.listing_id}/review-buyer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          rating: sellerReviewRating,
          comment: sellerReviewComment.trim(),
          // The buyer_id is implicit in the endpoint and listing context for the backend
          // but the backend will expect reviewee_id in the body.
          // The backend /seller-review-buyer endpoint will take care of associating with the listing's buyer.
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Failed to submit seller review with status: ${response.status}` }));
        throw new Error(errorData.detail || `Failed to submit seller review.`);
      }

      const newSellerReview = await response.json();
      reviews = [newSellerReview, ...reviews]; // Add new review to the top of the list
      sellerReviewSubmittedSuccessfully = true;
      showSellerReviewForm = false; // Hide form
      // Reset form fields
      sellerReviewRating = null;
      sellerReviewComment = '';

    } catch (err) {
      console.error('Error submitting seller review:', err);
      sellerReviewSubmitError = err.message || 'An unexpected error occurred while submitting your review for the buyer.';
    } finally {
      sellerReviewSubmitting = false;
    }
  }
</script>

<div class="back-button">
  <button on:click={goBack} class="back-link">← Back to Search</button>
</div>

{#if loading}
  <div class="loading">
   <div class="spinner"></div>
   <p>Loading listing details...</p>
  </div>
{:else if error}
  <div class="error">
   <h2>Error</h2>
   <p>{error}</p>
    <button class="retry-button" on:click={fetchListingDetails}>
      Try Again
    </button>
  </div>
{:else if listing}
  <div class="listing-detail">
   <div class="listing-header">
     <h1>{listing.title}</h1>
      <div class="listing-meta">
        {#if listing.is_skill_sharing}
          <p class="price">{formatRate(listing)}</p>
          {:else}
          <p class="price">${parseFloat(listing.price).toFixed(2)}</p>
          <p class="condition">{listing.item_condition.replace('_', ' ')}</p>
        {/if}
      </div>
    </div>

    <div class="listing-content">
      <div class="listing-images">
        <div class="carousel-container">
          <img
            src={getImagePath(listing, activeImageIndex)}
            alt={listing.title}
            class="main-image"
          />
          {#if listing.images && listing.images.length > 1}
            <button class="carousel-control prev" on:click={prevImage}>&#10094;</button>
            <button class="carousel-control next" on:click={nextImage}>&#10095;</button>
          {/if}
        </div>

        {#if listing.images && listing.images.length > 1}
          <div class="thumbnail-container">
            {#each listing.images as image, i}
              <button type="button" class="thumbnail-button {i === activeImageIndex ? 'active' : ''}" on:click={() => setActiveImage(i)}>
                <img
                  class="thumbnail"
                  src={getImagePath(listing, i)}
                  alt={`Thumbnail ${i + 1}`}
                />
              </button>
            {/each}
          </div>
        {/if}
      </div>

      <div class="listing-info">
        <div class="section">
          <h2>Description</h2>
          <p>{listing.description}</p>
        </div>

        <div class="section">
          <h2>Details</h2>
          <div class="details-grid">
            <div class="detail-item">
              <span class="detail-label">Category</span>
              <span class="detail-value">{listing.category?.name || 'Uncategorized'}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Category</span>
              <span class="detail-value">{listing.category?.name || 'Uncategorized'}</span>
            </div>
            {#if !listing.is_skill_sharing}
              <div class="detail-item">
                <span class="detail-label">Condition</span>
                <span class="detail-value">{listing.item_condition.replace('_', ' ')}</span>
              </div>
            {/if}
            <div class="detail-item">
              <span class="detail-label">Listed</span>
              <span class="detail-value">{new Date(listing.created_at).toLocaleDateString()}</span>
            </div>
            {#if listing.is_skill_sharing && listing.availability}
              <div class="detail-item">
                <span class="detail-label">Availability</span>
                <span class="detail-value">{listing.availability}</span>
              </div>
            {/if}
            <div class="detail-item">
              <span class="detail-label">Views</span>
              <span class="detail-value">{listing.views_count || 0}</span>
            </div>
          </div>
        </div>

        <div class="section">
          <h2>Contact Seller</h2>
          {#if listing.seller && listing.listing_id && listing.title}
            {#if $authUserStore && $authUserStore.user_id === listing.seller.user_id}
              <p class="seller-message">This is your listing.</p>
            {:else}
              <ContactUserButton
                sellerUser={listing.seller}
                listingId={listing.listing_id}
                listingTitle={listing.title}
              />
            {/if}
          {:else}
            <p class="seller-message">Contact information is currently unavailable for this listing.</p>
          {/if}
        </div>
      </div>
    </div>

    {#if listing.seller}
      <div class="section">
        <h2>Seller Information</h2>
        <div class="details-grid">
          <div class="detail-item">
            <span class="detail-label">Username</span>
            <span class="detail-value">{listing.seller.username}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Email</span>
            <span class="detail-value">{listing.seller.email}</span>
          </div>
        </div>
      </div>
    {/if}
  </div>
{:else}
  <div class="not-found-container">
    <div class="not-found">
      <h2>Listing Not Found</h2>
      <p>The listing you're looking for doesn't exist or has been removed.</p>
      <button on:click={goBack} class="back-link">Return to Search</button>
    </div>
  </div>
{/if}

<div class="section reviews-section">
  <h2>Listing Reviews</h2>
  {#if canLeaveReview && !showReviewForm && !reviewSubmittedSuccessfully}
    <button class="btn-leave-review" on:click={() => showReviewForm = true}>
      Leave a Review
    </button>
  {:else if reviewSubmittedSuccessfully}
    <div class="review-submission-success">
      <p>Your review has been submitted successfully!</p>
    </div>
  {/if}

  {#if showReviewForm && canLeaveReview}
    <div class="review-form-container">
      <h3>Write a Review</h3>
      <form on:submit|preventDefault={handleSubmitReview}>
        <div class="form-group">
          <label for="review-rating">Rating:</label>
          <div class="star-rating">
            {#each [5, 4, 3, 2, 1] as star}
              <input type="radio" id="star-{star}" name="rating" bind:group={reviewRating} value={star} required />
              <label for="star-{star}" title="{star} stars">★</label>
            {/each}
          </div>
        </div>
        <div class="form-group">
          <label for="review-comment">Comment:</label>
          <textarea id="review-comment" bind:value={reviewComment} rows="4" required placeholder="Share your experience..."></textarea>
        </div>
        {#if reviewSubmitError}
          <p class="error-message review-submit-error">{reviewSubmitError}</p>
        {/if}
        <button type="submit" class="btn-submit-review" disabled={reviewSubmitting}>
          {#if reviewSubmitting}Submitting...{:else}Submit Review{/if}
        </button>
        <button type="button" class="btn-cancel-review" on:click={() => { showReviewForm = false; reviewSubmitError = null; }}>
          Cancel
        </button>
      </form>
    </div>
  {/if}
  {#if reviewsLoading}
    <p>Loading reviews...</p>
  {:else if reviewsError}
    <p class="error-message review-error">Error loading reviews: {reviewsError}</p>
  {:else}
    <div class="reviews-sub-section">
      <h4>Reviews for this Listing/Seller:</h4>
      {#if reviews && reviews.filter(r => r.reviewee?.user_id === listing?.seller?.user_id && r.listing_id === listing?.listing_id).length > 0}
        <ul class="reviews-list">
          {#each reviews.filter(r => r.reviewee?.user_id === listing?.seller?.user_id && r.listing_id === listing?.listing_id) as review (review.review_id)}
            <li class="review-item">
              <div class="review-header">
                <span class="review-author">Reviewer: {review.reviewer?.username || 'Anonymous'}</span>
                <span class="review-rating">Rating: {'★'.repeat(review.rating)}{'☆'.repeat(5 - review.rating)}</span>
              </div>
              <p class="review-comment">{review.comment}</p>
              {#if review.created_at}
              <span class="review-date">
                Reviewed on: {new Date(review.created_at).toLocaleDateString()}
              </span>
              {/if}
            </li>
          {/each}
        </ul>
      {:else}
        <p>No reviews yet for this listing/seller.</p>
      {/if}
    </div>

  {#if canSellerLeaveReviewForBuyer}
    <div class="seller-review-buyer-section review-form-container"> {#if !showSellerReviewForm && !sellerReviewSubmittedSuccessfully}
        <button class="btn-leave-review" on:click={() => showSellerReviewForm = true}>Review Buyer</button>
      {:else if showSellerReviewForm && !sellerReviewSubmittedSuccessfully}
        <h3>Review Buyer ({listing.buyer?.username || 'This Buyer'})</h3>
        <form on:submit|preventDefault={handleSubmitSellerReview}>
          <div class="form-group">
            <label for="seller-review-rating">Rating for Buyer:</label>
            <div class="star-rating">
              {#each [5, 4, 3, 2, 1] as star}
                <input type="radio" id="seller-star-{star}" name="seller-rating" bind:group={sellerReviewRating} value={star} required />
                <label for="seller-star-{star}" title="{star} stars">★</label>
              {/each}
            </div>
          </div>
          <div class="form-group">
            <label for="seller-review-comment">Comment for Buyer:</label>
            <textarea id="seller-review-comment" bind:value={sellerReviewComment} rows="4" required placeholder="Share your experience with the buyer..."></textarea>
          </div>
          {#if sellerReviewSubmitError}
            <p class="error-message review-submit-error">{sellerReviewSubmitError}</p>
          {/if}
          <button type="submit" class="btn-submit-review" disabled={sellerReviewSubmitting}>
            {sellerReviewSubmitting ? 'Submitting...' : 'Submit Review for Buyer'}
          </button>
          <button type="button" class="btn-cancel-review" on:click={() => { showSellerReviewForm = false; sellerReviewSubmitError = null; }}>Cancel</button>
        </form>
      {/if}
      {#if sellerReviewSubmittedSuccessfully}
        <div class="review-submission-success">
          <p>Your review for the buyer has been submitted successfully!</p>
        </div>
      {/if}
    </div>
  {/if}

    {#if listing && listing.buyer_id}
      <div class="reviews-sub-section buyer-reviews-list">
        <h4>Reviews for Buyer ({listing.buyer?.username || 'Buyer'}):</h4>
        {#if reviews && reviews.filter(r => r.reviewee?.user_id === listing?.buyer_id && r.listing_id === listing?.listing_id && r.reviewer?.user_id === listing?.seller?.user_id).length > 0}
          <ul class="reviews-list">
            {#each reviews.filter(r => r.reviewee?.user_id === listing?.buyer_id && r.listing_id === listing?.listing_id && r.reviewer?.user_id === listing?.seller?.user_id) as review (review.review_id)}
              <li class="review-item">
                <div class="review-header">
                  <span class="review-author">Reviewed by Seller ({review.reviewer?.username || 'Seller'}):</span>
                  <span class="review-rating">Rating: {'★'.repeat(review.rating)}{'☆'.repeat(5 - review.rating)}</span>
                </div>
                <p class="review-comment">{review.comment}</p>
                {#if review.created_at}
                <span class="review-date">
                  Reviewed on: {new Date(review.created_at).toLocaleDateString()}
                </span>
                {/if}
              </li>
            {/each}
          </ul>
        {:else}
          <p>No reviews from the seller for the buyer on this listing yet.</p>
        {/if}
      </div>
    {/if}

    {#if reviews && reviews.length === 0 && !reviewsLoading && !reviewsError}
        <p>No reviews yet for this listing.</p> {/if}
  {/if}
</div>

<style>
  /* Base container for the whole detail view */

  /* Applied to the main div holding the listing content */
  .listing-detail {
    background-color: #ffffff;
    padding: 24px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    max-width: 1200px; /* Max width for better readability on large screens */
    margin: 0 auto; /* Center the content */
  }

  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin: 40px 0;
    padding: 20px;
  }

  .spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #6a1b9a; /* Purple spinner */
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin-bottom: 20px;
  }


  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .error {
    background-color: #ffebee; /* Light red */
    border: 1px solid #ef9a9a; /* Softer red border */
    color: #c62828; /* Darker red text */
    border-radius: 8px;
    padding: 20px;
    margin: 20px auto;
    text-align: center;
    max-width: 600px;
  }

  .error h2 {
    color: #c62828;
    margin-top: 0;
  }

  .retry-button {
    background-color: #6a1b9a;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    margin-top: 15px;
    transition: background-color 0.2s ease;
  }
  .retry-button:hover {
    background-color: #5a0f8a;
  }


  .back-button {
    margin: 0 0 20px 0; /* Adjusted margin to be outside the main content box if .listing-detail is used */
    /* If .listing-detail becomes the outermost styled box, back-button might be better inside it or styled globally */
  }

  .back-link {
    display: inline-flex;
    align-items: center;
    padding: 8px 16px;
    font-size: 15px;
    font-weight: 500;
    color: #6a1b9a;
    background-color: #f0e6f6;
    border: 1px solid #d1c4e9;
    border-radius: 5px;
    text-decoration: none;
    cursor: pointer;
    transition: background-color 0.2s ease-in-out, border-color 0.2s ease-in-out, color 0.2s ease-in-out;
  }

  .back-link:hover {
    background-color: #e9d8f2;
    border-color: #b39dba;
    color: #5a0f8a;
    text-decoration: none;
  }

  .listing-header {
    margin-bottom: 25px;
    border-bottom: 1px solid #e0e0e0; /* Slightly softer border */
    padding-bottom: 25px;
  }

  .listing-header h1 {
    font-size: 28px; /* Slightly larger */
    color: #333; /* Darker for better contrast, purple used a lot elsewhere */
    margin: 0 0 10px 0;
    font-weight: 600;
  }

  .listing-meta {
    display: flex;
    align-items: center;
    gap: 20px; /* Add gap between price and condition */
  }

  .price {
    font-size: 26px; /* Slightly larger */
    font-weight: bold;
    color: #6a1b9a; /* Keep price purple */
    margin: 0;
  }

  .condition {
    display: inline-block;
    background-color: #e8eaf6; /* Indigo light background for variety */
    padding: 6px 12px; /* More padding */
    border-radius: 16px; /* Pill shape */
    font-size: 14px;
    color: #3f51b5; /* Indigo text */
    /* margin-left: 15px; Removed, using gap in .listing-meta */
    font-weight: 500;
  }

  .listing-content {
    display: grid;
    grid-template-columns: 1.2fr 0.8fr; /* Give images slightly more space */
    gap: 30px; /* Increased gap */
  }

  @media (max-width: 900px) { /* Adjust breakpoint for 2-column layout */
    .listing-content {
      grid-template-columns: 1fr;
    }
  }

  .listing-images {
    display: flex;
    flex-direction: column;
  }

  .main-image {
    width: 100%;
    height: auto;
    max-height: 450px; /* Increased max height */
    object-fit: contain;
    border-radius: 8px;
    margin-bottom: 15px; /* Increased margin */
    background-color: #f5f5f5; /* Lighter grey */
    border: 1px solid #eee; /* Subtle border */
  }

  .carousel-container {
    position: relative;
    width: 100%;
    max-height: 450px;
    overflow: hidden;
    margin-bottom: 15px;
    border-radius: 8px;
    background-color: #f5f5f5;
  }

  .carousel-container .main-image {
    display: block;
    width: 100%;
    height: 450px;
    object-fit: contain;
    border: none; /* Remove border if container has one */
  }

  .carousel-control {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    background-color: rgba(40, 40, 40, 0.6); /* Darker, more contrast */
    color: white;
    border: none;
    padding: 12px; /* Slightly larger */
    cursor: pointer;
    z-index: 10;
    font-size: 22px; /* Larger icons */
    line-height: 1;
    border-radius: 50%;
    width: 44px; /* Slightly larger touch target */
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.3s ease;
  }

  .carousel-control:hover {
    background-color: rgba(0, 0, 0, 0.85);
  }

  .carousel-control.prev { left: 15px; }
  .carousel-control.next { right: 15px; }

  .thumbnail-container {
    display: flex;
    gap: 12px; /* Increased gap */
    flex-wrap: wrap;
  }

  .thumbnail {
    width: 85px; /* Slightly larger */
    height: 85px;
    object-fit: cover;
    border-radius: 6px; /* Softer radius */
    display: block;
  }

  .thumbnail-button {
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    border: 2px solid transparent;
    border-radius: 6px;
    line-height: 0;
    transition: border-color 0.2s ease;
  }

  .thumbnail-button:hover,
  .thumbnail-button:focus {
    border-color: #7e57c2; /* Lighter purple for hover */
    outline: none;
  }

  .thumbnail-button.active {
     border-color: #5e35b1; /* Primary purple for active */
     box-shadow: 0 0 0 2px #c5b3e6; /* Outer glow for active */
  }

  .listing-info {
    display: flex;
    flex-direction: column;
    gap: 25px; /* Space between sections in the info column */
  }

  .section {
    /* margin-bottom: 20px; Removed, using gap in .listing-info or directly */
    background-color: #fff; /* Sections on white, if page bg is #f9f9f9 */
    padding: 20px;
    border-radius: 6px;
    border: 1px solid #e0e0e0; /* Consistent border */
    box-shadow: 0 2px 4px rgba(0,0,0,0.04); /* Subtle shadow for sections */
  }

  .section h2 {
    font-size: 20px; /* Slightly larger section titles */
    color: #4a148c; /* Darker purple for section titles */
    margin-top: 0; /* Remove top margin if padding is on .section */
    margin-bottom: 15px; /* Spacing after title */
    padding-bottom: 10px;
    border-bottom: 1px solid #eee; /* Underline for section titles */
    font-weight: 500;
  }

  /* Style for the description paragraph */
  .section p {
    line-height: 1.7; /* Improved readability */
    color: #444; /* Slightly softer black */
    font-size: 16px;
  }


  .details-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); /* Responsive columns */
    gap: 20px; /* Increased gap */
  }

  .detail-item {
    display: flex;
    flex-direction: column;
    background-color: #f7f7f7; /* Very light grey for item background */
    padding: 15px;
    border-radius: 5px;
    border: 1px solid #eaeaea;
  }

  .detail-label {
    font-size: 14px;
    color: #555; /* Slightly darker grey */
    margin-bottom: 6px; /* Space between label and value */
    font-weight: 500;
  }

  .detail-value {
    font-size: 16px;
    font-weight: 500;
    color: #222; /* Darker text for value */
  }

  .seller-message {
    background-color: #e3f2fd; /* Light blue background */
    color: #1565c0; /* Darker blue text */
    padding: 15px;
    border-radius: 6px;
    border: 1px solid #bbdefb; /* Blue border */
    font-size: 15px;
    text-align: center;
  }

  .not-found-container { /* New container for centering */
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: calc(100vh - 200px); /* Adjust as needed based on header/footer height */
    padding: 20px;
  }

  .not-found {
    background-color: #fff;
    padding: 30px 40px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    text-align: center;
    max-width: 500px;
  }
  .not-found h2 {
    font-size: 22px;
    color: #d32f2f; /* Red for emphasis */
    margin-bottom: 15px;
  }
  .not-found p {
    font-size: 16px;
    color: #555;
    margin-bottom: 20px;
  }
  /* Reviews Section Styles */
  .reviews-section {
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid #e0e0e0;
  }

  .reviews-section h2 {
    font-size: 22px;
    color: #333;
    margin-bottom: 20px;
  }

  .reviews-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .review-item {
    background-color: #f9f9f9;
    border: 1px solid #eeeeee;
    border-radius: 6px;
    padding: 15px;
    margin-bottom: 15px;
  }

  .review-item:last-child {
    margin-bottom: 0;
  }

  .review-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .review-author {
    font-weight: 600;
    color: #444;
  }

  .review-rating {
    font-size: 0.9em;
    color: #6a1b9a; /* Theme purple */
    font-weight: 500;
  }

  .review-comment {
    font-size: 0.95em;
    color: #555;
    line-height: 1.6;
    margin-bottom: 8px;
    white-space: pre-wrap; /* Preserve line breaks in comments */
  }

  .review-date {
    font-size: 0.8em;
    color: #777;
    display: block;
    text-align: right;
  }
  
  .review-error {
    color: #c62828; /* Match other error messages */
    font-size: 0.9em;
  }
  /* Review Submission Form Styles */
  .btn-leave-review {
    background-color: #6a1b9a; /* Purple */
    color: white;
    padding: 10px 18px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 1em;
    margin-bottom: 20px;
    transition: background-color 0.2s ease;
  }
  .btn-leave-review:hover {
    background-color: #5a0f8a;
  }

  .review-form-container {
    background-color: #fdfdfd;
    padding: 20px;
    border-radius: 6px;
    border: 1px solid #e0e0e0;
    margin-bottom: 25px;
  }

  .review-form-container h3 {
    font-size: 1.3em;
    color: #333;
    margin-top: 0;
    margin-bottom: 15px;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
  }

  .form-group {
    margin-bottom: 15px;
  }

  .form-group label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
    color: #444;
  }

  .star-rating {
    display: flex;
    flex-direction: row-reverse; /* To make stars select from right to left */
    justify-content: flex-end; /* Align to the start */
  }

  .star-rating input[type="radio"] {
    display: none; /* Hide actual radio buttons */
  }

  .star-rating label {
    font-size: 2em; /* Larger stars */
    color: #ddd; /* Default empty star color */
    cursor: pointer;
    padding: 0 2px; /* Spacing between stars */
    margin-bottom: 0; /* Override default label margin */
  }

  /* Change color of stars on hover and when selected */
  .star-rating input[type="radio"]:checked ~ label,
  .star-rating label:hover,
  .star-rating label:hover ~ label {
    color: #f5b300; /* Gold color for selected/hovered stars */
  }

  .form-group textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    box-sizing: border-box;
    font-size: 1em;
    min-height: 80px;
  }
  .form-group textarea:focus {
    border-color: #6a1b9a;
    outline: none;
    box-shadow: 0 0 0 2px rgba(106, 27, 154, 0.2);
  }

  .review-submit-error {
    color: #c62828;
    margin-bottom: 10px;
    font-size: 0.9em;
  }

  .btn-submit-review, .btn-cancel-review {
    padding: 10px 18px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 1em;
    transition: background-color 0.2s ease;
    margin-right: 10px;
  }

  .btn-submit-review {
    background-color: #4CAF50; /* Green */
    color: white;
  }
  .btn-submit-review:hover {
    background-color: #45a049;
  }
  .btn-submit-review:disabled {
    background-color: #a5d6a7;
    cursor: not-allowed;
  }

  .btn-cancel-review {
    background-color: #f44336; /* Red */
    color: white;
  }
  .btn-cancel-review:hover {
    background-color: #e53935;
  }

  .review-submission-success {
    background-color: #e8f5e9; /* Light green */
    color: #2e7d32; /* Darker green text */
    padding: 15px;
    border-radius: 6px;
    border: 1px solid #a5d6a7;
    margin-bottom: 20px;
    text-align: center;
  }

  /* Styles for new review sections */
  .reviews-section h3, /* For "Write a Review" */
  .reviews-sub-section h4 { /* For "Reviews for this Listing/Seller" and "Reviews for Buyer" */
    color: var(--text-color-dark, #333);
    margin-bottom: 1rem;
    margin-top: 1.5rem;
    font-size: 1.4rem;
    border-bottom: 1px solid var(--border-color-light, #eee);
    padding-bottom: 0.5rem;
  }

  .reviews-section > h2 { /* "Listing Reviews" main title */
    margin-bottom: 1.5rem;
    font-size: 1.8rem;
  }

  .seller-review-buyer-section {
    margin-top: 2rem;
    margin-bottom: 2rem;
    padding: 1.5rem;
    background-color: var(--background-color-light-accent, #f9f9f9);
    border: 1px solid var(--border-color-light, #ddd);
    border-radius: var(--border-radius-base, 8px);
  }

  .seller-review-buyer-section h3 { /* Title inside the seller review form container */
    font-size: 1.3rem;
    margin-top: 0;
    margin-bottom: 1rem;
    color: var(--text-color-dark, #333);
  }

  .reviews-sub-section {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px dashed var(--border-color-medium, #ccc);
  }

  /* Remove top border and adjust margin if it's the first review group */
  .reviews-sub-section:first-of-type {
    /* border-top: none; */ /* Uncomment if no visual separation is desired for the very first group */
    /* margin-top: 1rem; */ /* Adjust if it follows a form closely */
  }

  .reviews-list {
    list-style: none;
    padding: 0;
    margin-top: 1rem;
  }

  /* .review-item is already styled, these are just for context if needed */
  /* .review-item { ... } */
  /* .review-header { ... } */
  /* .review-author { ... } */
  /* .review-rating { ... } */
  /* .review-comment { ... } */
  /* .review-date { ... } */

  /* Style for "No reviews yet" messages within sub-sections */
  .reviews-sub-section > p:not([class]) { /* Target plain <p> tags directly under sub-section */
    color: var(--text-color-secondary, #666);
    font-style: italic;
    margin-top: 1rem;
    text-align: center;
  }


  /* Styles for star rating within the seller review form, if not already covered by general .star-rating */
  .seller-review-buyer-section .star-rating {
    /* Ensure these match buyer review form if necessary, most are already general */
    /* display: flex; */
    /* flex-direction: row-reverse; */
    /* justify-content: flex-end; */
    margin-bottom: 1rem; /* Consistent margin */
  }

  .seller-review-buyer-section .star-rating input[type="radio"] {
    /* display: none; */ /* Already general */
  }

  .seller-review-buyer-section .star-rating label {
    /* font-size: 2rem; */ /* Already general */
    /* color: var(--border-color-medium, #ccc); */ /* Already general */
    /* cursor: pointer; */ /* Already general */
    /* padding: 0 0.1em; */ /* Already general */
  }

  .seller-review-buyer-section .star-rating input[type="radio"]:checked ~ label,
  .seller-review-buyer-section .star-rating label:hover,
  .seller-review-buyer-section .star-rating label:hover ~ label {
    /* color: var(--star-rating-color, #ffc107); */ /* Already general */
  }

  /* Specific styling for buyer-reviews-list if needed, e.g., if it appears after seller reviews */
  .buyer-reviews-list {
    /* margin-top: 1.5rem; */ /* Add specific margin if it's a distinct list */
  }
</style>
