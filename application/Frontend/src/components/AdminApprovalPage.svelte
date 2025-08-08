<script>
  import { onMount } from 'svelte';
  import { isAuthenticated, user as authUserStore } from '../stores/authStore.js';
  import { push } from 'svelte-spa-router';
  import { get } from 'svelte/store';

  let pendingListings = [];
  let isLoading = true;
  let error = null;

  onMount(async () => {
    const auth = get(isAuthenticated);
    const user = get(authUserStore);

    if (!auth || !user?.is_admin) {
      push('/login'); // Redirect if not authenticated or not an admin
      return;
    }
    await fetchPendingListings();
  });

  async function fetchPendingListings() {
    isLoading = true;
    error = null;
    const token = localStorage.getItem('access_token');
    if (!token) {
      error = 'Authentication token not found.';
      isLoading = false;
      push('/login');
      return;
    }

    try {
      const response = await fetch('/api/admin/listings/pending', {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.status === 401) {
        push('/login');
        return;
      }
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        let detailMessage = errData.detail || `Server error: ${response.status}`;
        if (typeof detailMessage === 'object') {
            detailMessage = JSON.stringify(detailMessage, null, 2);
        }
        throw new Error(detailMessage);
      }
      pendingListings = await response.json();
    } catch (e) {
      console.error('Error fetching pending listings:', e);
      error = e.message;
    } finally {
      isLoading = false;
    }
  }

  async function handleApprove(listingId) {
    const token = localStorage.getItem('access_token');
    if (!confirm(`Are you sure you want to approve listing ID: ${listingId}?`)) return;

    try {
      const response = await fetch(`/api/admin/listings/${listingId}/approve`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Failed to approve listing. Status: ${response.status}`);
      }
      alert('Listing approved successfully!');
      // Refresh list
      await fetchPendingListings();
    } catch (e) {
      console.error('Error approving listing:', e);
      alert(`Error: ${e.message}`);
    }
  }

  // Placeholder for reject/needs-changes later
  async function handleReject(listingId) {
    const notes = window.prompt(`Please enter a reason for rejecting listing ID: ${listingId}`);
    if (notes === null) return; // User cancelled the prompt

    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Authentication error. Please log in again.');
      push('/login');
      return;
    }

    try {
      const response = await fetch(`/api/admin/listings/${listingId}/reject`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ admin_notes: notes }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Failed to reject listing. Status: ${response.status}`);
      }
      alert('Listing rejected successfully!');
      await fetchPendingListings(); // Refresh the list
    } catch (e) {
      console.error('Error rejecting listing:', e);
      alert(`Error: ${e.message}`);
    }
  }
  async function handleNeedsChanges(listingId) {
    const notes = window.prompt(`Please enter the changes required for listing ID: ${listingId}`);
    if (notes === null) return; // User cancelled the prompt

    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Authentication error. Please log in again.');
      push('/login');
      return;
    }

    try {
      const response = await fetch(`/api/admin/listings/${listingId}/needs-changes`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ admin_notes: notes }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Failed to mark listing as 'needs changes'. Status: ${response.status}`);
      }
      alert('Listing marked as "needs changes" successfully!');
      await fetchPendingListings(); // Refresh the list
    } catch (e) {
      console.error('Error marking listing as "needs changes":', e);
      alert(`Error: ${e.message}`);
    }
  }

</script>

<main class="admin-approval-container">
  <h1>Pending Listings for Approval</h1>

  {#if isLoading}
    <p>Loading pending listings...</p>
  {:else if error}
    <p class="error-message">Error: {error}</p>
  {:else if pendingListings.length === 0}
    <p>No listings are currently pending approval.</p>
  {:else}
    <div class="listings-grid">
      {#each pendingListings as listing (listing.listing_id)}
        <div class="listing-card">
          <h3>{listing.title}</h3>
          <p><strong>ID:</strong> {listing.listing_id}</p>
          <p><strong>Seller:</strong> {listing.seller.username} (ID: {listing.seller.user_id})</p>
          <p><strong>Status:</strong> {listing.status}</p>
          <p><strong>Description:</strong> {listing.description.substring(0, 100)}{listing.description.length > 100 ? '...' : ''}</p>
          <p><strong>Price:</strong> ${listing.price !== null ? listing.price.toFixed(2) : 'N/A (Skill)'}</p>
          {#if listing.is_skill_sharing}
            <p><strong>Rate:</strong> ${listing.rate ? listing.rate.toFixed(2) : 'N/A'} {listing.rate_type || ''}</p>
          {/if}
          <div class="actions">
            <button class="approve-btn" on:click={() => handleApprove(listing.listing_id)}>Approve</button>
            <button class="reject-btn" on:click={() => handleReject(listing.listing_id)}>Reject</button>
            <button class="needs-changes-btn" on:click={() => handleNeedsChanges(listing.listing_id)}>Needs Changes</button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</main>

<style>
  .admin-approval-container { max-width: 1200px; margin: 2rem auto; padding: 1rem; }
  .error-message { color: red; }
  .listings-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }
  .listing-card { border: 1px solid #ccc; border-radius: 8px; padding: 1rem; background: #f9f9f9; }
  .listing-card h3 { margin-top: 0; }
  .actions { margin-top: 1rem; display: flex; gap: 0.5rem; }
  .actions button { padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; }
  .approve-btn { background-color: #4CAF50; color: white; }
  .reject-btn { background-color: #f44336; color: white; }
  .needs-changes-btn { background-color: #ff9800; color: white; }
</style>