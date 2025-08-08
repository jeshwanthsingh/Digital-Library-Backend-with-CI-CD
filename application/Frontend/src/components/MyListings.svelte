<script>
  import { onMount } from 'svelte';
  import { push } from 'svelte-spa-router'; // For navigation
  import { isAuthenticated } from '../stores/authStore.js'; // To check auth status

  let listings = [];
  let isLoading = true;
  let error = null;
  let currentIsAuthenticated = false;

  onMount(async () => {
    const unsubscribeAuth = isAuthenticated.subscribe(value => {
      currentIsAuthenticated = value;
    });
    unsubscribeAuth(); // Immediately unsubscribe after getting current value

    if (!currentIsAuthenticated) {
      console.log('MyListings.svelte: User not authenticated. Redirecting to login.');
      push('/login');
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      error = 'Authentication token not found. Please log in.';
      isLoading = false;
      push('/login');
      return;
    }

    try {
      const response = await fetch('/api/listings/my-listings', { // Corrected URL
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.status === 401) {
        push('/login'); // Token might be invalid or expired
        return;
      }
      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: 'Failed to fetch listings. Server returned an error.' }));
        console.error("Backend validation error details:", errData.detail); // Log the detailed error
        let detailMessage = errData.detail;
        if (typeof detailMessage === 'object') {
            detailMessage = JSON.stringify(detailMessage, null, 2); // Stringify for better readability
        }
        throw new Error(detailMessage || `Server error: ${response.status}`);
      }
      listings = await response.json();
    } catch (e) {
      console.error('Error fetching my listings:', e);
      error = e.message;
    } finally {
      isLoading = false;
    }
  });

  function handleEdit(listingId) {
    // TODO: Implement navigation to an edit page, e.g., /listings/edit/${listingId} or /my-listings/edit/${listingId}
    console.log('Edit listing:', listingId);
    push(`/listings/edit/${listingId}`); // Example route
  }

  async function handleDelete(listingId) {
    if (!confirm('Are you sure you want to delete this listing? This action cannot be undone.')) {
      return;
    }
    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Authentication token not found. Please log in.');
      push('/login');
      return;
    }
    try {
      const response = await fetch(`/api/listings/${listingId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.status === 401) {
        push('/login'); return;
      }
      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: 'Failed to delete listing.' }));
        throw new Error(errData.detail || `Server error: ${response.status}`);
      }
      listings = listings.filter(l => l.listing_id !== listingId);
      alert('Listing deleted successfully.');
    } catch (e) {
      console.error('Error deleting listing:', e);
      alert(`Failed to delete listing: ${e.message}`);
    }
  }

  function formatStatus(status) {
    if (!status) return 'N/A';
    return status.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
  }
</script>

<main class="my-listings-container">
  <h1>My Listings</h1>

  {#if isLoading}
    <p>Loading your listings...</p>
  {:else if error}
    <p class="error-message">Error: {error}</p>
  {:else if listings.length === 0}
    <p>You haven't posted any listings yet.</p>
    <a href="/post" class="link-button">Post an Item</a>
    <a href="/post-skill" class="link-button">Post a Skill</a>
  {:else}
    <div class="listings-grid">
      {#each listings as listing (listing.listing_id)}
        <div class="listing-card status-{listing.status}">
          <h3>{listing.title}</h3>
          <p class="status">Status: <strong>{formatStatus(listing.status)}</strong></p>
          
          {#if listing.status === 'rejected' || listing.status === 'needs_changes'}
            {#if listing.admin_notes}
              <div class="admin-notes">
                <h4>Admin Feedback:</h4>
                <p>{listing.admin_notes}</p>
              </div>
            {/if}
          {/if}

          <!-- Other listing details can be added here as needed -->
          <p>Price: ${listing.price !== null ? listing.price.toFixed(2) : 'N/A'}</p>
          {#if listing.is_skill_sharing}
            <p>Rate: ${listing.rate ? listing.rate.toFixed(2) : 'N/A'} {listing.rate_type}</p>
          {/if}
          <p class="timestamps">Created: {new Date(listing.created_at).toLocaleDateString()}</p>
          {#if listing.updated_at}
            <p class="timestamps">Last Updated: {new Date(listing.updated_at).toLocaleDateString()}</p>
          {/if}

          <div class="actions">
            <button on:click={() => handleEdit(listing.listing_id)} class="edit-button">Edit</button>
            <button on:click={() => handleDelete(listing.listing_id)} class="delete-button">Delete</button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</main>

<style>
  .my-listings-container {
    max-width: 1000px;
    margin: 2rem auto;
    padding: 1rem;
    font-family: system-ui, sans-serif;
  }
  h1 {
    text-align: center;
    margin-bottom: 2rem;
    color: #333;
  }
  .listings-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
  }
  .listing-card {
    background-color: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    display: flex;
    flex-direction: column;
  }
  .listing-card h3 {
    margin-top: 0;
    margin-bottom: 0.75rem;
    color: #444;
  }
  .status {
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
  }
  .status strong {
    font-weight: 600;
  }
  .admin-notes {
    background-color: #f9f9f9;
    border: 1px dashed #ccc;
    border-radius: 4px;
    padding: 0.75rem;
    margin-top: 0.5rem;
    margin-bottom: 1rem;
    font-size: 0.9rem;
  }
  .admin-notes h4 {
    margin-top: 0;
    margin-bottom: 0.25rem;
    font-size: 0.95rem;
    color: #555;
  }
  .timestamps {
    font-size: 0.8rem;
    color: #777;
    margin-top: 0.25rem;
  }
  .actions {
    margin-top: auto; /* Pushes actions to the bottom */
    padding-top: 1rem;
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
  }
  .actions button {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background-color 0.2s ease;
  }
  .edit-button {
    background-color: #2196F3; /* Blue */
    color: white;
  }
  .edit-button:hover {
    background-color: #1976D2;
  }
  .delete-button {
    background-color: #f44336; /* Red */
    color: white;
  }
  .delete-button:hover {
    background-color: #d32f2f;
  }
  .error-message {
    color: #d32f2f;
    text-align: center;
  }
  .link-button {
    display: inline-block;
    margin: 0.5rem;
    padding: 0.6rem 1.2rem;
    background-color: #6a1b9a;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    transition: background-color 0.3s ease;
  }
  .link-button:hover {
    background-color: #5a0f8a;
  }

  /* Status-specific styling examples */
  .status-pending_approval .status strong { color: #FFC107; /* Amber */ }
  .status-approved .status strong { color: #4CAF50; /* Green */ }
  .status-rejected .status strong { color: #f44336; /* Red */ }
  .status-needs_changes .status strong { color: #FF9800; /* Orange */ }
  .status-available .status strong { color: #00BCD4; /* Cyan - for older 'available' if any */ }
  .status-sold .status strong { color: #757575; /* Grey */ }

  .status-rejected { border-left: 5px solid #f44336; }
  .status-needs_changes { border-left: 5px solid #FF9800; }
  .status-pending_approval { border-left: 5px solid #FFC107; }
  .status-approved { border-left: 5px solid #4CAF50; }

</style>