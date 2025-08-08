<script>
    import { tick } from 'svelte';
  
    // Review form state
    let newReview = {
      username: '',
      rating: 0,
      comment: '',
    };
  
    // UI state
    let formError = '';
    let showSuccessMessage = false;
    let isSubmitting = false;
  
    async function handleSubmit() {
      // reset UI
      formError = '';
      showSuccessMessage = false;
  
      // client-side validation
      if (!newReview.username) {
        formError = 'Please enter your name';
        return;
      }
      if (!newReview.rating) {
        formError = 'Please select a rating';
        return;
      }
  
      isSubmitting = true;
  
      try {
        const res = await fetch('/api/reviews', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newReview)
        });
  
        if (!res.ok) {
          const text = await res.text();
          throw new Error(text || res.statusText);
        }
  
        showSuccessMessage = true;
        // let Svelte render the success message before resetting fields
        await tick();
  
        // clear form
        newReview = { username: '', rating: 0, comment: '' };
  
        // auto-hide
        setTimeout(() => {
          showSuccessMessage = false;
        }, 3000);
  
      } catch (error) {
        // safely extract a message from any thrown value
        const msg = error instanceof Error
          ? error.message
          : String(error);
        formError = msg || 'Failed to submit review. Please try again.';
      } finally {
        isSubmitting = false;
      }
    }
  </script>
  
  <main>
    <div class="container">
      <header>
        <h1>Customer Reviews</h1>
        <p class="subtitle">See what others are saying or share your experience</p>
      </header>
  
      <section class="card">
        <h2>Write a Review</h2>
  
        {#if showSuccessMessage}
          <div class="success-message">
            Thank you! Your review has been submitted successfully.
          </div>
        {/if}
  
        {#if formError}
          <div class="error-message" role="alert">
            {formError}
          </div>
        {/if}
  
        <form on:submit|preventDefault={handleSubmit} class="form-fields">
          <!-- Name -->
          <div class="form-group">
            <label for="username">Name</label>
            <input
              id="username"
              type="text"
              bind:value={newReview.username}
              aria-invalid={formError && !newReview.username ? 'true' : 'false'}
              placeholder="Enter your name"
            />
          </div>
  
          <!-- Rating -->
          <fieldset class="form-group">
            <legend>Rating</legend>
            <div class="star-rating">
              {#each [5,4,3,2,1] as n}
                <input
                  type="radio"
                  id="star-{n}"
                  name="rating"
                  value={n}
                  bind:group={newReview.rating}
                />
                <label for="star-{n}" aria-label="{n} stars">★</label>
              {/each}
            </div>
          </fieldset>
  
          <!-- Comment -->
          <div class="form-group">
            <label for="comment">Review</label>
            <textarea
              id="comment"
              rows="4"
              bind:value={newReview.comment}
              maxlength="126"
              placeholder="Share your experience with this product..."
            ></textarea>
            <div class="char-count">
              {newReview.comment.length} / 126
            </div>
          </div>
  
          <!-- Submit -->
          <button
            type="submit"
            class="submit-button"
            disabled={isSubmitting}
          >
            {#if isSubmitting}Submitting…{:else}Submit Review{/if}
          </button>
        </form>
      </section>
    </div>
  </main>
  
  <style>
    main {
      background-color: #f9fafb;
      min-height: 100vh;
      padding: 2rem 1rem;
    }
  
    .container {
      max-width: 800px;
      margin: 0 auto;
    }
  
    header {
      text-align: center;
      margin-bottom: 2rem;
    }
  
    h1 {
      font-size: 1.875rem;
      font-weight: 700;
      color: #1f2937;
      margin-bottom: 0.5rem;
    }
  
    h2 {
      font-size: 1.25rem;
      font-weight: 600;
      color: #1f2937;
      margin-bottom: 1rem;
    }
  
    .subtitle {
      color: #6b7280;
    }
  
    .card {
      background: white;
      border-radius: 0.5rem;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }
  
    /* Form styles */
    .form-fields {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
  
    .form-group {
      display: flex;
      flex-direction: column;
      gap: 0.375rem;
    }
  
    label {
      font-size: 0.875rem;
      font-weight: 500;
      color: #4b5563;
    }
  
    input,
    textarea {
      border: 1px solid #d1d5db;
      border-radius: 0.375rem;
      padding: 0.625rem;
      width: 100%;
      font-size: 0.875rem;
    }
  
    input:focus,
    textarea:focus {
      outline: none;
      border-color: #3b82f6;
      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
    }
  
    .star-rating {
      display: flex;
      flex-direction: row-reverse;
      justify-content: flex-end;
      gap: 0.25rem;
    }
  
    .star-rating input {
      display: none;
    }
  
    .star-rating label {
      font-size: 2rem;
      color: #d1d5db;
      cursor: pointer;
      transition: color 0.2s;
    }
  
    .star-rating input:checked ~ label,
    .star-rating label:hover,
    .star-rating label:hover ~ label {
      color: #f59e0b;
    }
  
    .char-count {
      font-size: 0.75rem;
      color: #6b7280;
      text-align: right;
    }
  
    .submit-button {
      background-color: #3b82f6;
      color: white;
      border: none;
      border-radius: 0.375rem;
      padding: 0.625rem 1rem;
      font-size: 0.875rem;
      font-weight: 500;
      cursor: pointer;
      transition: background-color 0.2s;
    }
  
    .submit-button:hover {
      background-color: #2563eb;
    }
  
    /* Success and error messages */
    .success-message {
      background-color: #d1fae5;
      color: #065f46;
      padding: 0.75rem;
      border-radius: 0.375rem;
      margin-bottom: 1rem;
    }
  
    .error-message {
      background-color: #fee2e2;
      color: #b91c1c;
      padding: 0.75rem;
      border-radius: 0.375rem;
      margin-bottom: 1rem;
    }
  
    fieldset.form-group {
      border: none;
      margin: 0;
      padding: 0;
    }
  
    legend {
      font-size: 0.875rem;
      font-weight: 500;
      color: #4b5563;
      margin-bottom: 0.375rem;
    }
  </style>