<script>
  import { createEventDispatcher } from 'svelte';
  import { user as authUserStore } from '../../stores/authStore.js'; // To get current user's token

  const dispatch = createEventDispatcher();

  let searchQuery = '';
  let searchResults = [];
  let isLoading = false;
  let error = null;
  let searchPerformed = false;

  const API_BASE_URL = typeof window !== 'undefined' ? window.location.origin + '/api' : '/api';

  async function performSearch() {
    if (!searchQuery.trim()) {
      searchResults = [];
      searchPerformed = false;
      return;
    }
    isLoading = true;
    error = null;
    searchPerformed = true;
    const token = localStorage.getItem('access_token');

    if (!token) {
      error = "Authentication token not found. Please log in.";
      isLoading = false;
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/users/search?q=${encodeURIComponent(searchQuery)}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        const data = await response.json();
        searchResults = data.filter(u => u.user_id !== $authUserStore?.user_id); // Exclude self
      } else {
        const errData = await response.json();
        error = errData.detail || `Error searching users: ${response.status}`;
        searchResults = [];
      }
    } catch (e) {
      console.error("User search failed:", e);
      error = "User search request failed. Please try again.";
      searchResults = [];
    } finally {
      isLoading = false;
    }
  }

  function selectUser(user) {
    dispatch('userSelected', user);
  }

  function clearSearch() {
    searchQuery = '';
    searchResults = [];
    error = null;
    searchPerformed = false;
  }
</script>

<div class="user-search-container">
  <h3>Start a New Conversation</h3>
  <div class="search-input-group">
    <input type="text" bind:value={searchQuery} placeholder="Search by username or email..." on:input={performSearch} />
    {#if searchQuery}
      <button class="clear-button" on:click={clearSearch} aria-label="Clear search">&times;</button>
    {/if}
  </div>

  {#if isLoading}
    <p class="loading-message">Searching...</p>
  {/if}

  {#if error}
    <p class="error-message">{error}</p>
  {/if}

  {#if searchPerformed && !isLoading && searchResults.length === 0 && !error}
    <p class="no-results-message">No users found matching "{searchQuery}".</p>
  {/if}

  {#if searchResults.length > 0}
    <ul class="results-list">
      {#each searchResults as user (user.user_id)}
        <li on:click={() => selectUser(user)} on:keydown={e => e.key === 'Enter' && selectUser(user)} tabindex="0">
          {user.username}
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .user-search-container {
    padding: 1rem;
    border: 1px solid #ddd;
    border-radius: 5px;
    background-color: #fff;
  }
  .search-input-group {
    display: flex;
    margin-bottom: 1rem;
  }
  input[type="text"] {
    flex-grow: 1;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 3px 0 0 3px;
  }
  .clear-button {
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-left: none;
    background-color: #f0f0f0;
    cursor: pointer;
    border-radius: 0 3px 3px 0;
  }
  .results-list {
    list-style: none;
    padding: 0;
    margin: 0;
    max-height: 200px;
    overflow-y: auto;
  }
  .results-list li {
    padding: 0.75rem;
    border-bottom: 1px solid #eee;
    cursor: pointer;
  }
  .results-list li:last-child {
    border-bottom: none;
  }
  .results-list li:hover, .results-list li:focus {
    background-color: #f0f0f0;
  }
  .loading-message, .error-message, .no-results-message {
    padding: 0.5rem;
    text-align: center;
  }
  .error-message {
    color: red;
  }
</style>