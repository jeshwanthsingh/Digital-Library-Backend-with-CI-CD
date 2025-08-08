<script>
  import { onMount, onDestroy } from 'svelte';
  import { get } from 'svelte/store'; // Import get
  import { push, pop, replace, params } from 'svelte-spa-router'; // Correct import for 'push'
  import { isAuthenticated } from '../stores/authStore.js';
  import { categories as categoryStore, loadCategories } from '../stores/categoryStore.js';
  import { conditionOptions as postConditionOptions } from '../lib/constants.js';

  let listing = null;
  let originalStatus = null; // To store the status when the component loads
  let isLoading = true;
  let error = null;
  let isSubmitting = false;
  let successMessage = '';

  // Form fields - initialize as empty, will be populated from fetched listing
  let title = '';
  let description = '';
  let selectedCategoryId = '';
  let price = '';
  let item_condition = ''; // For items
  let location = '';
  let images = []; // Will handle file objects for new uploads, existing images need separate display/management
  let existingImages = [];

  // Skill-specific fields
  let rate = '';
  let rateType = 'hourly';
  let availability = '';

  let listingId;
  let unsubscribeParams;
  let unsubscribeCategories;

  const postingConditionOptions = postConditionOptions.filter(opt => opt.value !== '');


  onMount(async () => {
    unsubscribeParams = params.subscribe(async (newParams) => {
      listingId = newParams ? newParams.id : null;
      if (listingId) {
        await fetchListingDetails();
      }
    });

    const auth = get(isAuthenticated); // Use get() to read store value once
    if (!auth) {
      push('/login');
      return;
    }
    // Load all categories initially, can be filtered in template or by listing type
    loadCategories(null); 
    unsubscribeCategories = categoryStore.subscribe(_ => {});

  });

  onDestroy(() => {
    if (unsubscribeParams) unsubscribeParams();
    if (unsubscribeCategories) unsubscribeCategories();
  });

  async function fetchListingDetails() {
    isLoading = true;
    error = null;
    const token = localStorage.getItem('access_token');
    if (!token) {
      error = 'Authentication token not found. Please log in.';
      isLoading = false;
      push('/login');
      return;
    }

    try {
      const response = await fetch(`/api/listings/${listingId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.status === 401) { push('/login'); return; }
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Failed to fetch listing details. Status: ${response.status}`);
      }
      listing = await response.json();
      populateFormFields(listing);
      originalStatus = listing.status; // Store the original status
      existingImages = listing.images || [];
    } catch (e) {
      console.error('Error fetching listing details:', e);
      error = e.message;
    } finally {
      isLoading = false;
    }
  }

  function populateFormFields(data) {
    title = data.title || '';
    description = data.description || '';
    selectedCategoryId = data.category_id || '';
    price = data.price !== null ? data.price.toString() : '';
    item_condition = data.item_condition || '';
    location = data.location || '';
    
    if (data.is_skill_sharing) {
      rate = data.rate !== null ? data.rate.toString() : '';
      rateType = data.rate_type || 'hourly';
      availability = data.availability || '';
    }
  }

  function handleImageUpload(event) {
    images = [...images, ...Array.from(event.target.files)];
  }

  function removeNewImage(index) {
    images = images.filter((_, i) => i !== index);
  }
  
  async function removeExistingImage(imageId) {
    if (!confirm('Are you sure you want to remove this existing image?')) return;
    const token = localStorage.getItem('access_token');
    // TODO: Implement API call to delete existing image, then update `existingImages`
    console.log(`Request to delete existing image ${imageId} for listing ${listingId}`);
     try {
        const response = await fetch(`/api/listings/${listingId}/images/${imageId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` },
        });
        if (response.ok) {
            existingImages = existingImages.filter(img => img.image_id !== imageId);
            alert('Image removed successfully.');
        } else {
            const errData = await response.json().catch(() => ({}));
            alert(`Failed to remove image: ${errData.detail || response.statusText}`);
        }
    } catch (e) {
        alert(`Error removing image: ${e.message}`);
    }
  }


  async function handleUpdateListing() {
    isSubmitting = true;
    successMessage = '';
    error = null;
    const token = localStorage.getItem('access_token');

    if (!token) {
      error = 'Authentication token not found. Please log in.';
      isSubmitting = false;
      push('/login');
      return;
    }

    const updatedData = {
      title: title.trim(),
      description: description.trim(),
      category_id: parseInt(selectedCategoryId),
      location: location.trim() || null,
      // Conditionally add fields based on listing type
    };

    if (listing.is_skill_sharing) {
      updatedData.is_skill_sharing = true;
      updatedData.rate = rate ? parseFloat(rate) : null;
      updatedData.rate_type = rateType;
      updatedData.availability = availability.trim() || null;
      updatedData.price = null; // Explicitly nullify price for skills
      updatedData.item_condition = null; // Explicitly nullify condition for skills
    } else {
      updatedData.is_skill_sharing = false;
      updatedData.price = price ? parseFloat(price) : null;
      updatedData.item_condition = item_condition || null;
      updatedData.rate = null; // Explicitly nullify skill fields for items
      updatedData.rate_type = null;
      updatedData.availability = null;
    }
    
    // Filter out undefined or empty string values that should not be sent if schema doesn't allow null
    // For example, if an optional field is empty, you might want to send null or not send it at all.
    // The backend PUT operation should handle partial updates.

    try {
      const response = await fetch(`/api/listings/${listingId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updatedData)
      });

      if (response.status === 401) { push('/login'); return; }
      
      const responseData = await response.json();

      if (!response.ok) {
        let errorMessage = `Failed to update listing. Status: ${response.status}`;
        if (responseData.detail) {
            if (Array.isArray(responseData.detail)) {
                errorMessage += '\nDetails: ' + responseData.detail.map(err => `${err.loc.join('->')}: ${err.msg}`).join('; ');
            } else {
                errorMessage += ` Details: ${responseData.detail}`;
            }
        }
        throw new Error(errorMessage);
      }
      
      // Handle new image uploads if any
      if (images.length > 0) {
          const imageFormData = new FormData();
          images.forEach(file => imageFormData.append('file', file));
          
          const imageUploadResponse = await fetch(`/api/listings/${listingId}/images`, {
              method: 'POST',
              headers: { 'Authorization': `Bearer ${token}` },
              body: imageFormData
          });
          if (!imageUploadResponse.ok) {
              // Non-critical error, listing was updated but images failed.
              const imgErr = await imageUploadResponse.json().catch(() => ({}));
              console.warn('Listing updated, but failed to upload new images:', imgErr.detail || imageUploadResponse.statusText);
              successMessage = 'Listing updated, but new image uploads failed. ';
          } else {
            console.log("New images uploaded successfully for listing:", listingId);
          }
      }
      images = []; // Clear new images after attempting upload


      if (originalStatus === 'approved' && responseData.status === 'pending_approval') {
        successMessage += 'Your changes have been submitted. The listing is now pending re-approval.';
      } else {
        successMessage += 'Listing updated successfully!';
      }
      alert(successMessage);
      originalStatus = responseData.status; // Update original status for subsequent edits without page reload

      // Optionally, re-fetch or update local `listing` object with `responseData`
      listing = {...listing, ...responseData}; 
      populateFormFields(listing); // Re-populate form in case backend modified some data
      existingImages = responseData.images || existingImages;


      // Consider navigation strategy, e.g., back to My Listings or stay on page
      // push('/my-listings'); 

    } catch (e) {
      console.error('Error updating listing:', e);
      error = e.message;
      alert(`Error: ${e.message}`);
    } finally {
      isSubmitting = false;
    }
  }

  $: itemCategories = $categoryStore.filter(c => !c.is_skill_category);
  $: skillCategories = $categoryStore.filter(c => c.is_skill_category);

</script>

<main class="form-container">
  <h1>Edit Listing</h1>

  {#if isLoading}
    <p>Loading listing details...</p>
  {:else if error}
    <p class="error-message">{error}</p>
  {:else if listing}
    <div class="form-card">
      <!-- Title -->
      <div class="form-group">
        <label for="title">Title</label>
        <input id="title" bind:value={title} />
      </div>

      <!-- Description -->
      <div class="form-group">
        <label for="description">Description</label>
        <textarea id="description" bind:value={description} rows="4"></textarea>
      </div>

      <!-- Category Dropdown -->
      <div class="form-group">
        <label for="category">Category</label>
        <select id="category" bind:value={selectedCategoryId}>
          <option value="">Select category</option>
          {#if listing.is_skill_sharing}
            {#each skillCategories as category (category.category_id)}
              <option value={category.category_id}>{category.name}</option>
            {/each}
          {:else}
            {#each itemCategories as category (category.category_id)}
              <option value={category.category_id}>{category.name}</option>
            {/each}
          {/if}
        </select>
      </div>

      {#if !listing.is_skill_sharing}
        <!-- Item Specific Fields -->
        <div class="form-row">
          <div class="form-group">
            <label for="condition">Condition</label>
            <select id="condition" bind:value={item_condition}>
              {#each postingConditionOptions as option (option.value)}
                <option value={option.value}>{option.label}</option>
              {/each}
            </select>
          </div>
          <div class="form-group">
            <label for="price">Price ($)</label>
            <input id="price" type="number" bind:value={price} min="0" step="0.01" />
          </div>
        </div>
      {/if}

      {#if listing.is_skill_sharing}
        <!-- Skill Specific Fields -->
        <div class="form-row">
          <div class="form-group">
            <label for="rate">Rate ($)</label>
            <div class="rate-input">
              <input id="rate" type="number" bind:value={rate} min="0" step="0.01" />
              <select bind:value={rateType}>
                <option value="hourly">per hour</option>
                <option value="fixed">fixed</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label for="availability">Availability</label>
            <input id="availability" bind:value={availability} />
          </div>
        </div>
      {/if}

      <!-- Location -->
      <div class="form-group">
        <label for="location">Suggested Meetup Location</label>
        <input id="location" bind:value={location} />
      </div>

      <!-- Existing Images -->
      <div class="form-group">
        <label>Existing Images</label>
        {#if existingImages.length > 0}
          <ul class="image-list existing-image-list">
            {#each existingImages as img (img.image_id)}
              <li>
                <img src={img.thumbnail_path || img.image_path} alt="Listing image {img.image_id}" class="thumbnail" />
                <span class="image-name">{img.image_path.split('/').pop()}</span>
                <button type="button" class="delete-btn small-delete-btn" on:click={() => removeExistingImage(img.image_id)} title="Remove Existing Image">🗑️</button>
              </li>
            {/each}
          </ul>
        {:else}
          <p>No existing images.</p>
        {/if}
      </div>

      <!-- New Images Upload -->
      <div class="form-group">
        <label for="image-upload">Upload New Images</label>
        <div class="upload-box">
          <input type="file" id="image-upload" multiple on:change={handleImageUpload} class="hidden" accept="image/*" />
          <label for="image-upload" class="upload-label">Click or Drag to Upload New Images</label>
        </div>
        {#if images.length > 0}
          <ul class="image-list new-image-list">
            {#each images as img, index (img.name + index)}
              <li>
                <span class="image-name">{img.name}</span>
                <button type="button" class="delete-btn small-delete-btn" on:click={() => removeNewImage(index)} title="Remove New Image">🗑️</button>
              </li>
            {/each}
          </ul>
        {/if}
      </div>

      <button class="submit-btn" on:click={handleUpdateListing} disabled={isSubmitting}>
        {isSubmitting ? 'Updating...' : 'Update Listing'}
      </button>
      
      {#if successMessage && !error}
        <p class="success-message">{successMessage}</p>
      {/if}
    </div>
  {:else}
    <p>Listing not found or you do not have permission to edit it.</p>
  {/if}
</main>

<style>
  /* Shared styles from Post.svelte - consider moving to a global stylesheet or a shared component style */
  .form-container { max-width: 700px; margin: 2rem auto; padding: 1.5rem; font-family: system-ui, sans-serif; }
  .form-title { font-size: 2rem; font-weight: bold; margin-bottom: 1.5rem; text-align: center; }
  .form-card { background: #fff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); padding: 1.5rem; position: relative; overflow: hidden; }
  .form-card::before { content: ''; position: absolute; top: 0; left: 0; height: 6px; width: 100%; background: linear-gradient(90deg, #5E35B1, #FFC107); }
  .form-group { margin-bottom: 1rem; display: flex; flex-direction: column; }
  label { font-weight: 500; margin-bottom: 0.5rem; }
  input, textarea, select { border: 1px solid #ccc; border-radius: 4px; padding: 0.5rem; font-size: 1rem; width: 100%; box-sizing: border-box; }
  textarea { min-height: 80px; }
  .form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
  .rate-input { display: flex; gap: 5px; }
  .rate-input input { flex-grow: 1; }
  .rate-input select { flex-shrink: 0; max-width: 100px; }
  .upload-box { border: 2px dashed #ccc; border-radius: 6px; padding: 1rem; text-align: center; }
  .hidden { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border-width: 0; }
  .upload-label { cursor: pointer; color: #6a1b9a; text-decoration: underline; }
  .submit-btn { margin-top: 1.5rem; width: 100%; padding: 0.75rem; background-color: #6a1b9a; color: white; border: none; border-radius: 6px; font-size: 1rem; cursor: pointer; transition: background-color 0.3s ease; }
  .submit-btn:hover { background-color: #5a0f8a; }
  .submit-btn:disabled { background-color: #ccc; }
  .error-message { color: #d32f2f; margin-top: 1rem; text-align: center; }
  .success-message { color: #4CAF50; margin-top: 1rem; text-align: center; font-weight: bold; }
  
  .image-list { list-style-type: none; padding: 0; margin-top: 0.5rem; }
  .image-list li { display: flex; align-items: center; justify-content: space-between; padding: 0.3rem 0; border-bottom: 1px solid #eee; font-size: 0.9rem; }
  .image-list li:last-child { border-bottom: none; }
  .thumbnail { width: 50px; height: 50px; object-fit: cover; border-radius: 4px; margin-right: 10px; }
  .image-name { flex-grow: 1; word-break: break-all; }
  .small-delete-btn { background: none; border: none; cursor: pointer; font-size: 1rem; color: #cc0000; padding: 0 0.3rem; }
</style>