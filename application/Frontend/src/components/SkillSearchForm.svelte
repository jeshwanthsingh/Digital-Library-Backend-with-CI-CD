<script>
  import { onMount } from 'svelte';
  import {
    searchQuery,
    selectedCategory,
    // selectedCondition, // Removed
    // minPrice, // Removed
    // maxPrice, // Removed
    isSkillSharing, // Import the store
    performSearch
  } from '../stores/searchStore.js'; // Import search stores
  import {
    categories,
    loadCategories
  } from '../stores/categoryStore.js'; // Import category store
  // --- Import constants ---
  import { skillCategories } from '../lib/constants.js'; // Only import skillCategories

  // Helper: Get skill categories from backend categories (is_skill_category)
  $: skillCategoryOptions = $categories.filter(cat => cat.is_skill_category);

  // --- searchType prop removed ---

  // Categories are now loaded in App.svelte
  // onMount(() => {
  //   if ($categories.length === 0) {
  //     loadCategories();
  //   }
  // });

  // --- Remove local conditionOptions definition --- REMOVED

  // Trigger search when filters change or button clicked
  function handleSearch() {
    // Always perform skill search
    console.log('SkillSearchForm: Calling performSearch with is_skill_sharing:', true);
    performSearch({ is_skill_sharing: true });
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

</script>

<div class="search-form">
  <!-- Search Text Input - Skill Placeholder -->
  <input
    class="search-input text-input"
    type="text"
    placeholder="Search skills..."
    bind:value={$searchQuery}
    on:input={debouncedSearch}
  />

  <!-- Category Dropdown - Skill Categories -->
  {#if !$isSkillSharing}
    <select class="search-input category-select" bind:value={$selectedCategory} on:change={handleSearch}>
      <option value={0}>All { $isSkillSharing ? 'Skill' : 'Item' } Categories</option>
      {#each skillCategoryOptions as category}
        <option value={category.category_id}>{category.name}</option>
      {/each}
    </select>
  {/if}

  <!-- Item Filters - REMOVED -->

  <!-- Placeholder for Skill-Specific Filters (Optional) -->
  <!-- Example: Add Format filter if needed later -->
  <!-- <select class="search-input format-select" bind:value={$selectedFormat} on:change={handleSearch}> -->
    <!-- <option value="">Any Format</option> -->
    <!-- {#each formats as format} <option value={format}>{format}</option> {/each} -->
  <!-- </select> -->

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

  .category-select {
    min-width: 150px; /* Minimum width for selects */
    cursor: pointer;
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