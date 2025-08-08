<script>
    import { onMount, onDestroy } from 'svelte';
    import { push } from 'svelte-spa-router'; // Import push for navigation
    import { isAuthenticated, setAuthenticated, setUser } from '../stores/authStore.js'; // Import auth store and setters
    import { categories as categoryStore, loadCategories } from '../stores/categoryStore.js';
   // --- Import constants ---
   import { conditionOptions as postConditionOptions } from '../lib/constants.js'; // Only import conditionOptions
   // --- Use a different name for conditionOptions if needed to avoid conflict ---

    let title = '';
    let description = '';
    let selectedCategoryId = '';
    let selectedCondition = ''; // Use this for binding
    let price = '';
    let location = '';
    let images = [];
    let isPosting = false; // Add loading state for posting
    // Removed listingType as this component is now item-only
    // let listingType = 'item';

    // Removed skill-specific fields as this component is now item-only
    // let rate = '';
    // let rateType = 'hourly';
    // let availability = '';
    // let selectedFormat = '';

    // --- Remove the local definitions of skillCategories, formats, conditionOptions ---
    // const skillCategories = [...]; // REMOVED
    // const formats = [...]; // REMOVED
    // const conditionOptions = [...]; // REMOVED

    // --- Adjust condition options for posting (e.g., remove 'Any Condition') ---
    const postingConditionOptions = postConditionOptions.filter(opt => opt.value !== '');
    // Or adjust the imported constant directly if it only serves Post.svelte

    let unsubscribeCategories;

    onMount(() => {
      // Removed isAuthenticated check here; route guard handles it.
      // const unsubscribeAuth = isAuthenticated.subscribe(authenticated => {
      //   if (!authenticated) {
      //     console.log('Post.svelte (Items): User not authenticated. Redirecting to login.');
      //     push('/login');
      //   }
      // });

      // Load item categories specifically for this form
      console.log("Post.svelte (Items): Loading item categories");
      loadCategories(false); // Load ONLY item categories

      unsubscribeCategories = categoryStore.subscribe(value => {
          // No action needed here usually, reactivity handles it
      });

      // Removed auth unsubscribe as the subscription was removed.
      // return () => {
      //   if (unsubscribeAuth) unsubscribeAuth();
      // };
    });

    onDestroy(() => {
        if (unsubscribeCategories) unsubscribeCategories();
    });

    function handleImageUpload(event) {
      const files = Array.from(event.target.files); 
      images = [...images, ...files];
    }

    function removeImage(index) {
      images = images.filter((_, i) => i !== index);
    }

    async function postItem() {
      const token = localStorage.getItem('access_token');
      if (!token) {
        alert('You must be logged in to post an item.');
        push('/login');
        return;
      }

      // Client-side validation for required fields
      if (!title.trim()) {
        alert('Title is required.');
        return;
      }
      if (!description.trim()) {
        alert('Description is required.');
        return;
      }
      if (!selectedCategoryId) {
        alert('Category is required.');
        return;
      }
       // Price is optional in the schema, but if provided, ensure it's valid
      const parsedPrice = price ? parseFloat(price) : null;
      if (price && (isNaN(parsedPrice) || parsedPrice < 0)) {
        alert('Price must be a valid non-negative number if provided.');
        return;
      }


      isPosting = true;

      // Step 1: Create the listing with text data (JSON)
      const listingPayload = {
        title: title.trim(),
        description: description.trim(),
        category_id: parseInt(selectedCategoryId),
        price: parsedPrice, // Send null if price is empty or invalid after parsing
        item_condition: selectedCondition || null, // Send null if no condition selected, backend defaults
        location: location.trim() || null,
        is_skill_sharing: false,
        // Skill-specific fields like rate, rate_type, availability are not included for 'item'
      };
      
      let newListing;

      try {
        const listingResponse = await fetch('/api/listings/', { // Use relative path, add trailing slash
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(listingPayload),
        });

        if (!listingResponse.ok) {
          const errorData = await listingResponse.json().catch(() => null);
          console.error('Failed to create listing:', listingResponse.status, listingResponse.statusText, errorData);
          let errorMessage = `Failed to create listing. Status: ${listingResponse.status}`;
          if (errorData && errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              errorMessage += '\nDetails:';
              errorData.detail.forEach(err => {
                errorMessage += `\n- ${err.loc ? err.loc.join(' -> ') : 'field'}: ${err.msg}`;
              });
            } else if (typeof errorData.detail === 'string') {
              errorMessage += ` Details: ${errorData.detail}`;
            }
          } else {
            errorMessage += `\n${listingResponse.statusText}`;
          }
          alert(errorMessage);
          isPosting = false;
          return;
        }

        newListing = await listingResponse.json();
        console.log('Listing created successfully:', newListing);

        // Step 2: If listing creation is successful and there are images, upload them
        if (images.length > 0 && newListing && newListing.listing_id) {
          console.log(`Uploading ${images.length} images for listing ${newListing.listing_id}`);
          const imageFormData = new FormData();
          images.forEach(imageFile => {
            imageFormData.append('file', imageFile, imageFile.name); // Match backend parameter name 'file'
          });

          // Debug: Log FormData entries for image upload
          console.log("Image FormData entries for listing:", newListing.listing_id);
          for (let [key, value] of imageFormData.entries()) {
            console.log(`  ${key}:`, value);
          }
          const imageUploadResponse = await fetch(`/api/listings/${newListing.listing_id}/images`, { // Use relative path
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`
              // 'Content-Type' is NOT set for FormData; browser handles it
            },
            body: imageFormData,
          });

          if (!imageUploadResponse.ok) {
            const imageErrorData = await imageUploadResponse.json().catch(() => null);
            console.error('Failed to upload images:', imageUploadResponse.status, imageUploadResponse.statusText, imageErrorData);
            // Alert user, but the listing itself was created.
            alert(`Listing created, but failed to upload some/all images. Status: ${imageUploadResponse.status}. Check console for details.`);
          } else {
            const uploadedImagesResult = await imageUploadResponse.json();
            console.log('Images uploaded successfully:', uploadedImagesResult);
            alert('Your item and images have been submitted successfully and are now pending approval. You can check its status on your "My Listings" page.');
          }
        } else {
          alert('Your item has been submitted successfully and is now pending approval. You can check its status on your "My Listings" page.');
        }

        // Clear form and redirect to My Listings page
        title = '';
        description = '';
        selectedCategoryId = '';
        selectedCondition = '';
        price = '';
        location = '';
        images = [];
        // TODO: Confirm the correct route for "My Listings" page. Assuming '/my-listings' for now.
        push('/my-listings');

      } catch (error) {
        console.error('Error posting item or uploading images:', error);
        alert(`An error occurred: ${error.message}`);
      } finally {
        isPosting = false;
      }
    }
   // Renamed postItem to submitItemPost for clarity (optional)
   // function submitItemPost() { ... }
</script>

<main class="form-container">
  <h1 class="form-title">Post an Item</h1>

  <div class="form-card">
    <!-- Title -->
    <div class="form-group">
      <label for="title">Item Title</label>
      <input id="title" bind:value={title} placeholder="e.g. iPhone 14 Pro Max" />
    </div>

    <!-- Description -->
    <div class="form-group">
      <label for="description">Description</label>
      <textarea id="description" bind:value={description} rows="4" placeholder="Describe the item..."></textarea>
    </div>

    <!-- Category Dropdown -->
    <div class="form-group">
      <label for="category">Category</label>
      <select id="category" bind:value={selectedCategoryId}>
        <option value="">Select category</option>
        {#each $categoryStore as category}
          <option value={category.category_id}>{category.name}</option>
        {/each}
      </select>
    </div>

    <!-- Item Specific Fields -->
    <div class="form-row">
      <div class="form-group">
        <label for="condition">Condition</label>
        <select id="condition" bind:value={selectedCondition}>
          {#each postingConditionOptions as option}
            <option value={option.value}>{option.label}</option>
          {/each}
        </select>
      </div>
      <div class="form-group">
        <label for="price">Price ($)</label>
        <input id="price" type="number" bind:value={price} min="0" step="0.01" placeholder="e.g., 150.00" />
      </div>
    </div>

    <!-- Location -->
    <div class="form-group">
      <label for="location">Suggested Meetup Location</label>
      <input id="location" bind:value={location} placeholder="e.g. Library Lobby, Main Quad" />
    </div>

    <!-- Images -->
    <div class="form-group">
      <label for="image-upload">Images</label>
      <div class="upload-box">
        <input type="file" id="image-upload" multiple on:change={handleImageUpload} class="hidden" accept="image/*" />
        <label for="image-upload" class="upload-label">Click or Drag to Upload Images</label>
        <p class="hint">Max 5 images. PNG, JPG, GIF accepted.</p>
      </div>
      {#if images.length > 0}
        <ul class="file-list">
          {#each images as img, index (img.name || index)}
            <li>
              {img.name}
              <button type="button" class="delete-btn" on:click={() => removeImage(index)} title="Remove">🗑️</button>
            </li>
          {/each}
        </ul>
      {/if}
    </div>

    <!-- Submit Button -->
    <button class="submit-btn" on:click={postItem} disabled={isPosting}>
      {isPosting ? 'Posting...' : 'Post Item'}
    </button>
  </div>
</main>

<style>
  /* Styles remain the same */
  /* Add styles for radio buttons */ 
    .listing-type-selector {
        margin-bottom: 1.5rem;
        border-bottom: 1px solid #eee;
        padding-bottom: 1.5rem;
    }
    .radio-group {
        display: flex;
        gap: 1.5rem;
        margin-top: 0.5rem;
    }
    .radio-group label {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
        font-weight: normal; /* Override default label weight */
    }
    .radio-group input[type="radio"] {
       accent-color: #6a1b9a; /* Style radio button */
    }

    .form-container {
      max-width: 700px;
      margin: 2rem auto;
      padding: 1.5rem;
      font-family: system-ui, sans-serif;
    }

    .form-title {
      font-size: 2rem;
      font-weight: bold;
      margin-bottom: 1.5rem;
      text-align: center;
    }

    .form-card {
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
      padding: 1.5rem;
      position: relative; /* Add this */
      overflow: hidden;   /* So the bar doesn't overflow rounded corners */
    }

    .form-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      height: 6px;
      width: 100%;
      background: linear-gradient(90deg, #5E35B1, #FFC107);
    }


    .form-group {
      margin-bottom: 1rem;
      display: flex;
      flex-direction: column;
    }

    label {
      font-weight: 500;
      margin-bottom: 0.5rem;
    }

    input,
    textarea,
    select {
      border: 1px solid #ccc;
      border-radius: 4px;
      padding: 0.5rem;
      font-size: 1rem;
    }

    .form-row {
      display: grid; /* Use grid for better alignment */
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); /* Responsive columns */
      gap: 1rem;
    }
    .rate-input {
      display: flex;
      gap: 5px;
    }
    .rate-input input {
        flex-grow: 1;
    }
    .rate-input select {
        flex-shrink: 0;
        max-width: 100px; /* Adjust as needed */
    }

    .upload-box {
      border: 2px dashed #ccc;
      border-radius: 6px;
      padding: 1rem;
      text-align: center;
    }

    /* --- Style to visually hide file input but keep accessible --- */
    .hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border-width: 0;
    }
    /* ------------------------------------------------------------- */

    .upload-label {
      cursor: pointer;
      color: #6a1b9a; /* Theme color */
      text-decoration: underline;
    }

    .hint {
      font-size: 0.85rem;
      color: #666;
      margin-top: 0.5rem;
    }

    .file-list {
      margin-top: 0.5rem;
      padding-left: 0; /* Remove default padding */
      font-size: 0.9rem;
      list-style-type: none;
    }

    .file-list li {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
      padding: 0.3rem 0; /* Add some padding */
      border-bottom: 1px solid #eee; /* Separator */
    }
    .file-list li:last-child {
        border-bottom: none; /* Remove border for last item */
    }


    .delete-btn {
      background: none;
      border: none;
      cursor: pointer;
      font-size: 1.1rem;
      color: #cc0000;
      padding: 0 0.5rem; /* Add padding for easier clicking */
    }

    .submit-btn {
      margin-top: 1.5rem;
      width: 100%;
      padding: 0.75rem;
      background-color: #6a1b9a; /* Theme color */
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 1rem;
      cursor: pointer;
      transition: background-color 0.3s ease; /* Add transition */
    }

    .submit-btn:hover {
      background-color: #5a0f8a; /* Darker theme color */
    }
</style>
