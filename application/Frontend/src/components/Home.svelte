<script>
  import { onMount } from 'svelte';
  import ItemSearchForm from './ItemSearchForm.svelte'; // Import the new item-specific search form
  import ItemResults from './ItemResults.svelte'; // Import the new item-specific results component
  import PromoCard from './PromoCard.svelte';
  import {
    results,
    totalResults,
    isLoading,
    searchError,
    resetSearchContext // Import the new function
  } from '../stores/searchStore.js';
  import { loadCategories } from '../stores/categoryStore.js'; // Import category loader

  onMount(() => {
    console.log("Home Mounted - Resetting context to ITEMS (false)"); // <-- ADD THIS LOG
    resetSearchContext(false); // Reset context to items on mount
    // Optional: If you want URL filters to apply on direct load/refresh to Home:
    // applyUrlFilters(); // You would also need to import applyUrlFilters
    loadCategories(false);    // Load ONLY item categories
  });
</script>

<div class="page-container">
  <aside class="sidebar">
    <PromoCard />
  </aside>

  <!-- Main Content -->
  <main class="main-content">
    <div class="center-content">
      <section class="search-bar">
        <ItemSearchForm></ItemSearchForm>

      </section>

      <section class="results-info">
        <span>{$totalResults} items found</span>
      </section>

      <section class="search-results">
        <ItemResults results={$results} loading={$isLoading} error={$searchError} />
      </section>
    </div>
  </main>
</div>

<style>
.page-container {
  display: flex;
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
  padding: 0;
}

.sidebar {
  flex: 0 0 20px;
  top: 100px;
  padding: 0;
  background: none;
}

/* Main Content */
.main-content {
  flex: 1 1 auto;
  display: flex;
}

.center-content {
  margin: 0 auto;
  width: 100%;
  max-width: 1100px;
  padding: 20px 20px; /* nice breathing space */
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.search-bar,
.results-info,
.search-results {
  width: 100%;
}

.results-info {
  text-align: center;
  font-size: 18px;
  color: #6a1b9a;
}

.search-results {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
}

@media (max-width: 1200px) {
  .sidebar {
    display: none;
  }
  .page-container {
    padding: 0 10px;
  }
}

  </style>
