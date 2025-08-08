<script>
  import { push } from 'svelte-spa-router';
  import { isAuthenticated } from '../../stores/authStore.js'; // Import auth store
  import { get } from 'svelte/store'; // To get store value non-reactively

  export let sellerUser; // e.g., { user_id: 'xxx', username: 'SellerName' }
  export let listingId;  // e.g., '123'
  export let listingTitle; // e.g., 'Vintage Lamp'

  let isLoading = false; // To disable button during API call

  async function initiateContact() {
    if (!sellerUser || !sellerUser.user_id || !listingId || !listingTitle) {
      console.error('Seller user, listing ID, or listing title is missing.');
      alert('Cannot initiate contact: essential information missing.');
      return;
    }

    if (!get(isAuthenticated)) {
      alert('Please log in to contact the seller.');
      push('/login'); // Redirect to login
      return;
    }

    const parsedRecipientId = parseInt(sellerUser.user_id, 10);
    const parsedListingId = parseInt(listingId, 10);

    if (isNaN(parsedRecipientId) || isNaN(parsedListingId)) {
      console.error('Invalid seller ID or listing ID format.');
      alert('Cannot initiate contact: Invalid ID format.');
      return;
    }

    isLoading = true;
    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Authentication token not found. Please log in again.');
      isLoading = false;
      push('/login');
      return;
    }

    const initialMessage = `I'm interested in your listing: "${listingTitle}" (ID: ${parsedListingId}). Is it available?`;
    const API_BASE_URL = typeof window !== 'undefined' ? window.location.origin + '/api' : '/api';

    try {
      const response = await fetch(`${API_BASE_URL}/messages/initiate_conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          recipient_id: parsedRecipientId,
          listing_id: parsedListingId,
          initial_message: initialMessage
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.conversation_id) {
          push(`/messages/${data.conversation_id}`);
        } else {
          console.error('Conversation ID not found in response:', data);
          alert('Failed to start conversation. Please try again.');
        }
      } else {
        const errorData = await response.json().catch(() => ({ message: 'Failed to process error response' }));
        console.error('Failed to initiate conversation:', response.status, errorData);
        alert(`Error contacting seller: ${errorData.detail || response.statusText}`);
      }
    } catch (error) {
      console.error('Error during initiateContact:', error);
      alert('An unexpected error occurred. Please try again.');
    } finally {
      isLoading = false;
    }
  }
</script>

<button
  class="contact-seller-button"
  on:click={initiateContact}
  disabled={!sellerUser || !listingId || !listingTitle || isLoading}
>
  {#if isLoading}
    Contacting...
  {:else}
    Contact {sellerUser?.username || 'Seller'}
  {/if}
</button>

<style>
  .contact-seller-button {
    padding: 10px 20px;
    font-size: 16px;
    font-weight: 500;
    border-radius: 5px;
    border: none;
    background-color: #6a1b9a; /* Primary purple */
    color: white;
    cursor: pointer;
    transition: background-color 0.2s ease-in-out, opacity 0.2s ease-in-out;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    line-height: 1.5; /* Ensure text is vertically centered */
  }

  .contact-seller-button:hover:not(:disabled) {
    background-color: #5a0f8a; /* Darker purple on hover */
  }

  .contact-seller-button:disabled {
    background-color: #b39dba; /* Lighter, muted purple */
    color: #f3e5f5; /* Very light text for disabled state */
    cursor: not-allowed;
    opacity: 0.8;
  }

  /* If you want to add an icon or spinner later, this can be useful */
  .contact-seller-button svg {
    margin-right: 8px;
  }
</style>