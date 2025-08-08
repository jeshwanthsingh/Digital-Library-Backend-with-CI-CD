<script>
    import { onMount, onDestroy } from 'svelte';
    import { push } from 'svelte-spa-router'; // Import push for navigation
    import { isAuthenticated, setAuthenticated, setUser } from '../stores/authStore.js'; // Import auth store and setters
    import { categories as categoryStore, loadCategories } from '../stores/categoryStore.js';
   // Removed imports for skillCategories and formats as they are no longer used
   // import { skillCategories, formats } from '../lib/constants.js';
 
    // Skill‐only form state
    let title = '';
    let description = '';
    let selectedCategory = '';
    let rate = '';
    let rateType = 'hourly';
    let availability = '';
    let location = '';
    let images = [];
    let isPosting = false; // Add loading state for posting
    // Removed selectedFormat as the Format field is removed
    // let selectedFormat = '';
  
    let unsubscribeCategories;
    onMount(() => {
      // Removed isAuthenticated check here; route guard handles it.
      // const unsubscribeAuth = isAuthenticated.subscribe(authenticated => {
      //   if (!authenticated) {
      //     console.log('PostSkill.svelte: User not authenticated. Redirecting to login.');
      //     push('/login');
      //   }
      // });

      // Load skill categories specifically for this form
      console.log("PostSkill.svelte: Loading skill categories");
      loadCategories(true); // Load ONLY skill categories
      unsubscribeCategories = categoryStore.subscribe(() => {});

      // Removed auth unsubscribe as the subscription was removed.
      // return () => {
      //   if (unsubscribeAuth) unsubscribeAuth();
      // };
    });
    onDestroy(() => unsubscribeCategories && unsubscribeCategories());
  
    function handleImageUpload(e) {
      images = [...images, ...Array.from(e.target.files)];
    }
    function removeImage(i) {
      images = images.filter((_, idx) => idx !== i);
    }
    async function postSkill() {
      const skillData = {
          title,
          description,
          category_id: parseInt(selectedCategory), // Use category_id for backend, ensure integer
          price: null, // Skills don't have a fixed price in this model
          item_condition: "new", // Default condition for skills (or remove if not needed in backend)
          rate: rate ? parseFloat(rate) : null,
          rate_type: rateType,
          availability,
          location,
          is_skill_sharing: true
      };

      // Get JWT token from localStorage
      const token = localStorage.getItem('access_token');
      if (!token) {
          alert('You must be logged in to post a skill.');
          push('/login'); // Redirect to login if no token
          return;
      }

      isPosting = true; // Set loading state to true
      try {
          // TODO: Handle image uploads separately after getting listing ID
          // For now, just submit the main listing data

          const response = await fetch('/api/listings/', { // Use relative path, add trailing slash
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}` // Include JWT token
              },
              body: JSON.stringify(skillData),
          });

          if (response.ok) {
              const newListing = await response.json();
              console.log('Skill posted successfully:', newListing);

              // Upload images after successful listing creation
              if (images.length > 0) {
                  console.log(`Uploading ${images.length} images for skill listing ${newListing.listing_id}`);
                  const uploadPromises = images.map(image => {
                      const formData = new FormData();
                      formData.append('file', image);

                      return fetch(`/api/listings/${newListing.listing_id}/images`, { // Use relative path
                          method: 'POST',
                          headers: {
                              'Authorization': `Bearer ${token}` // Include JWT token
                              // Note: Do NOT set Content-Type for FormData, browser sets it
                          },
                          body: formData,
                      })
                      .then(uploadResponse => {
                          if (!uploadResponse.ok) {
                              // Handle individual image upload errors
                              console.error(`Failed to upload image ${image.name}:`, uploadResponse.statusText);
                              // Optionally return an error object or throw
                              return { success: false, fileName: image.name, status: uploadResponse.status };
                          }
                          console.log(`Image ${image.name} uploaded successfully.`);
                          return { success: true, fileName: image.name };
                      })
                      .catch(uploadError => {
                          console.error(`Error uploading image ${image.name}:`, uploadError);
                          return { success: false, fileName: image.name, error: uploadError };
                      });
                  });

                  // Wait for all image uploads to complete
                  const uploadResults = await Promise.all(uploadPromises);
                  console.log('Image upload results:', uploadResults);

                  // Check if all images uploaded successfully (optional, for stricter feedback)
                  const allUploadsSuccessful = uploadResults.every(result => result.success);

                  if (allUploadsSuccessful) {
                      alert('Your skill/service and images have been submitted successfully and are now pending approval. You can check its status on your "My Listings" page.');
                  } else {
                      alert('Your skill/service has been submitted and is pending approval, but some images failed to upload. Check console for details and your "My Listings" page for status.');
                  }

              } else {
                  // No images to upload
                  alert('Your skill/service has been submitted successfully and is now pending approval. You can check its status on your "My Listings" page.');
              }

              // Redirect to My Listings page and clear the form
              // TODO: Confirm the correct route for "My Listings" page. Assuming '/my-listings' for now.
              push('/my-listings');
              title = '';
              description = '';
              selectedCategory = '';
              rate = '';
              rateType = 'hourly';
              availability = '';
              location = '';
              images = []; // Clear selected images

          } else {
              const errorData = await response.json();
              console.error('Failed to post skill:', errorData);

              let errorMessage = 'Failed to post skill.';
              if (errorData.detail) {
                  if (Array.isArray(errorData.detail)) {
                      // Handle FastAPI validation errors (array of error objects)
                      errorMessage += '\nDetails:';
                      errorData.detail.forEach(err => {
                          errorMessage += `\n- ${err.loc.join(' -> ')}: ${err.msg}`;
                      });
                  } else if (typeof errorData.detail === 'string') {
                      // Handle simple string error details
                      errorMessage += ` Details: ${errorData.detail}`;
                  }
              } else if (response.statusText) {
                  // Fallback to status text if no detail is provided
                  errorMessage += ` Status: ${response.statusText}`;
              }
              alert(errorMessage);
          }
      } catch (error) {
          console.error('Error posting skill:', error);
          alert('An error occurred while posting the skill.');
      } finally {
          isPosting = false; // Set loading state to false
      }
    }
  </script>
  
  <main class="form-container">
    <h1 class="form-title">Post a Skill/Service</h1>
    <div class="form-card">
      <!-- Title & Description -->
      <div class="form-group">
        <label for="title">Skill/Service Title</label>
        <input id="title" bind:value={title} placeholder="e.g. Python Tutoring" />
      </div>
  
      <div class="form-group">
        <label for="description">Description</label>
        <textarea id="description" bind:value={description} rows="4" placeholder="Describe the skill/service..."></textarea>
      </div>
  
      <!-- Skill Category -->
      <div class="form-group">
        <label for="skill-category">Skill Category</label>
        <select id="skill-category" bind:value={selectedCategory}>
          <option value="">Select skill category</option>
          {#each $categoryStore as category}
            <option value={category.category_id}>{category.name}</option>
          {/each}
        </select>
      </div>
  
      <!-- Rate & Availability -->
      <div class="form-row">
        <div class="form-group">
          <label for="rate">Rate ($)</label>
          <div class="rate-input">
            <input id="rate" type="number" bind:value={rate} min="0" step="0.01" placeholder="e.g. 25.00" />
            <select bind:value={rateType}>
              <option value="hourly">per hour</option>
              <option value="fixed">fixed</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label for="availability">Availability</label>
          <input id="availability" bind:value={availability} placeholder="e.g. Weekends, Mon/Wed evenings" />
        </div>
      </div>
  
      <!-- Format field removed as it's not part of the core listing model -->
      <!--
      <div class="form-group">
        <label for="format">Format</label>
        <select id="format" bind:value={selectedFormat}>
          <option value="">Select format</option>
          {#each formats as fmt}
            <option value={fmt}>{fmt}</option>
          {/each}
        </select>
      </div>
      -->
  
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
        {#if images.length}
          <ul class="file-list">
            {#each images as img, idx}
              <li>
                {img.name}
                <button type="button" class="delete-btn" on:click={() => removeImage(idx)}>🗑️</button>
              </li>
            {/each}
          </ul>
        {/if}
      </div>
  
      <button class="submit-btn" on:click={postSkill} disabled={isPosting}>
        {isPosting ? 'Posting...' : 'Post Skill/Service'}
      </button>
      </div>
    </main>
  
  <style>

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