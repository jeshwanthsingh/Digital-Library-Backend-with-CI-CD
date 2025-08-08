<script>
  import { push } from 'svelte-spa-router';

  export let results = [];
  export let loading = false;
  export let error = null;
  // resultType prop removed

  function goToListing(id) {
    // Always set originPath to '/skill-sharing' for skill results
    const originPath = '/skill-sharing';
    push(`/listings/${id}?from=${encodeURIComponent(originPath)}`);
  }

  function handleKeyDown(event, id) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      goToListing(id);
    }
  }

  function getImagePath(item) {
    if (!item.images || item.images.length === 0) {
      return '/static/images/listings/testimage.jpg';
    }
    const primaryImage = item.images.find(img => img.is_primary) || item.images[0];
    let imgPath = primaryImage.thumbnail_path || primaryImage.image_path;
    if (imgPath.startsWith('http') || imgPath.startsWith('/')) {
      return imgPath;
    }
    return '/static/images/listings/' + imgPath;
  }

  // Import the formatRate utility function
  import { formatRate } from '../lib/formatters.js';
</script>

{#if loading}
  <div class="loading">
    <div class="spinner"></div>
    <p>Loading...</p>
  </div>
{:else if error}
  <div class="error">{error}</div>
{:else if results.length === 0}
  <div class="no-results">No skills found.</div>
{:else}
  <div class="results-grid">
    {#each results as item (item.listing_id)}
      <div
        class="result-card-link"
        role="link"
        tabindex="0"
        on:click={() => goToListing(item.listing_id)}
        on:keydown={(e) => handleKeyDown(e, item.listing_id)}
      >
        <div class="result-card">
          <img class="result-image" src={getImagePath(item)} alt={item.title || 'Listing image'} loading="lazy" />
          <div class="card-content">
            <h3>{item.title}</h3>
            <!-- Skill Rate -->
            <p class="rate">{formatRate(item)}</p>
            <p class="description">{item.description.length > 80 ? item.description.substring(0, 80) + '...' : item.description}</p>
          </div>
        </div>
      </div>
    {/each}
  </div>
{/if}

<style>
  .loading, .error, .no-results {
    text-align: center;
    margin: 40px 20px;
    font-size: 18px;
    color: #666;
  }

  .spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #6a1b9a;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin: 0 auto 10px;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
    width: 100%;
    max-width: 1200px; /* <- Keep grid nicely centered */
    margin: 0 auto;
    padding: 20px 0;
    box-sizing: border-box;
  }

  .result-card-link {
    text-decoration: none;
    color: inherit;
    display: block;
    background: #fff;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .result-card-link:hover,
  .result-card-link:focus {
    transform: translateY(-5px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
    outline: none;
  }

  .result-card {
    display: flex;
    flex-direction: column;
  }

  .result-image {
    width: 100%;
    height: 180px;
    object-fit: cover;
  }

  .card-content {
    padding: 15px;
  }

  .card-content h3 {
    font-size: 1.1rem;
    margin: 0 0 8px;
    color: #333;
  }

  .rate {
    font-size: 1rem;
    font-weight: bold;
    color: #6a1b9a;
    margin-bottom: 8px;
  }


  .description {
    font-size: 0.85rem;
    color: #555;
    margin-top: 8px;
  }
</style>