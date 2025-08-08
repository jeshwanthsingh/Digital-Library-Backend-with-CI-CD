<script>
  import { onMount } from 'svelte';
  import {
    searchQuery,
    selectedCategory,
    selectedCondition,
    minPrice,
    maxPrice,
    isSkillSharing, // Import the store
    performSearch,
    clearActiveFilters // <-- Add this
  } from '../stores/searchStore.js'; // Import search stores
  import {
    categories,
    loadCategories
  } from '../stores/categoryStore.js'; // Import category store
  // --- Import constants ---
  import { conditionOptions } from '../lib/constants.js'; // Only import conditionOptions

  // Helper: Get skill categories from backend categories (is_skill_category) - REMOVED

  // --- searchType prop removed ---

  // Categories are now loaded in App.svelte
  // onMount(() => {
  //   if ($categories.length === 0) {
  //     loadCategories();
  //   }
  // });

  // --- Remove local conditionOptions definition ---
  // const conditionOptions = [...]; // REMOVED

  // Trigger search when filters change or button clicked
  function handleSearch() {
    // Always perform item search
    console.log('ItemSearchForm: Calling performSearch with is_skill_sharing:', false);
    performSearch({ is_skill_sharing: false });
  }

  // Debounce function
  let debounceTimer;
  function debouncedSearch() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      handleSearch();
    }, 500);
  }

  // --- Reactive statement to clear incompatible filters when type changes --- REMOVED

  let showAdvancedFilters = false; // State for the "More Filters" toggle

  function toggleAdvancedFilters() {
    showAdvancedFilters = !showAdvancedFilters;
  }

  // Reactive variable to check if any item-specific filters are active
  $: areFiltersActive = $searchQuery !== '' ||
                         $selectedCategory !== 0 ||
                         $selectedCondition !== '' ||
                         $minPrice !== '' ||
                         $maxPrice !== '';
</script>

<div class="search-form">
  <!-- Search Text Input - Item Placeholder -->
  <input
    class="search-input text-input"
    type="text"
    placeholder="Search items..."
    bind:value={$searchQuery}
    on:input={debouncedSearch}
  />

  <!-- Category Dropdown - Item Categories -->
  <select class="search-input category-select" bind:value={$selectedCategory} on:change={handleSearch}>
    <option value={0}>All { $isSkillSharing ? 'Skill' : 'Item' } Categories</option>
    {#each $categories as category}
      <option value={category.category_id}>{category.name}</option>
    {/each}
  </select>

  {#if !$isSkillSharing}
    <button class="more-filters-button" on:click={toggleAdvancedFilters}>
      {showAdvancedFilters ? 'Hide' : 'More'} Filters
    </button>
  {/if}

  <!-- Item Filters (Advanced) -->
  {#if !$isSkillSharing && showAdvancedFilters}
    <!-- Condition Dropdown -->
    <select class="search-input condition-select" bind:value={$selectedCondition} on:change={handleSearch}>
      {#each conditionOptions as option}
        <option value={option.value}>{option.label}</option>
      {/each}
    </select>

    <!-- Price Inputs -->
    <div class="price-inputs">
      <input
        class="search-input price-input"
        type="number"
        placeholder="Min $"
        bind:value={$minPrice}
        on:input={debouncedSearch}
        min="0"
      />
      <span>-</span>
      <input
        class="search-input price-input"
        type="number"
        placeholder="Max $"
        bind:value={$maxPrice}
        on:input={debouncedSearch}
        min="0"
      />
    </div>
  {/if}

  {#if areFiltersActive}
    <button class="clear-filters-button" on:click={clearActiveFilters}>Clear Filters</button>
  {/if}
  <button class="search-button" on:click={handleSearch}>Search</button>
</div>

<style>
  /* Styles remain the same */
  .search-form {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 10px;
  width: 100%; /* <--- ADD THIS */
  padding: 15px; /* keep */
  background-color: #f0e6f6;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}


  .search-input {
    padding: 10px 12px; /* Slightly smaller padding */
    font-size: 15px; /* Slightly smaller font */
    border-radius: 5px;
    border: 1px solid #ccc; /* Lighter border */
    background-color: #ffffff;
    color: #4a4a4a;
    box-sizing: border-box; /* Include padding in width */
  }

  .search-input:focus {
      border-color: #6a1b9a;
      outline: none;
      box-shadow: 0 0 0 2px rgba(106, 27, 154, 0.2);
  }

  .text-input {
    flex-grow: 1; /* Allow text input to take more space */
    min-width: 200px; /* Minimum width */
  }

  .category-select, .condition-select {
    min-width: 150px; /* Minimum width for selects */
    cursor: pointer;
  }

  .price-inputs {
      display: flex;
      align-items: center;
      gap: 5px;
  }

  .price-input {
    width: 80px; /* Fixed width for price inputs */
    -moz-appearance: textfield; /* Hide spinners in Firefox */
  }
  .price-input::-webkit-outer-spin-button,
  .more-filters-button {
    padding: 8px 15px;
    font-size: 14px;
    border-radius: 5px;
    border: 1px solid #8c5ba6; /* A slightly lighter purple for the border */
    background-color: #faf6fd; /* A very light purple background */
    color: #6a1b9a; /* Main purple for text, matching other elements */
    cursor: pointer;
    transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
    /* Optional: margin if needed depending on layout next to other elements */
    /* margin-left: 5px; */
  }

  .more-filters-button:hover {
    background-color: #e9d8f2; /* A slightly darker light purple on hover */
    border-color: #6a1b9a; /* Main purple border on hover */
    color: #5a0f8a; /* Darker purple text on hover */
  }

  .clear-filters-button {
    padding: 8px 15px;
    font-size: 14px;
    border-radius: 5px;
    border: 1px solid #ccad8f; /* A distinct but complementary color */
    background-color: #fffaf0; /* A light, neutral color */
    color: #bf874c; /* Text color that matches the border */
    cursor: pointer;
    transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
  }

  .clear-filters-button:hover {
    background-color: #f5efdf; /* Slightly darker on hover */
    border-color: #bf874c;
    color: #a9713c;
  }

  .price-input::-webkit-inner-spin-button {
    -webkit-appearance: none; /* Hide spinners in Chrome/Safari */
    margin: 0;
  }


  .search-button {
    padding: 10px 20px; /* Slightly smaller padding */
    font-size: 16px;
    border-radius: 5px;
    border: none;
    background-color: #6a1b9a;
    color: white;
    margin-left: 10px; /* Keep margin? Review layout */
    cursor: pointer;
    transition: background-color 0.3s;
  }

  .search-button:hover {
    background-color: #5a0f8a;
  }
</style>