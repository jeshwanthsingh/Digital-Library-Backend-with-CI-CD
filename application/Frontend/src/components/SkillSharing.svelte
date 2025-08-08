<script>
  import { onMount } from 'svelte';
  import { push } from 'svelte-spa-router';
  import SkillSearchForm from './SkillSearchForm.svelte'; // Import the new skill-specific search form
  import SkillResults from './SkillResults.svelte'; // Import the new skill-specific results component
  import {
    results,
    totalResults,
    isLoading,
    searchError,
    resetSearchContext // Import the new function
  } from '../stores/searchStore.js';
  import { loadCategories } from '../stores/categoryStore.js'; // Import category loader

  onMount(() => {
    console.log("SkillSharing Mounted - Resetting context to SKILLS (true)"); // <-- ADD THIS LOG
    resetSearchContext(true); // Reset context to skills on mount
    // Optional: If you want URL filters to apply on direct load/refresh to Skill Sharing:
    // applyUrlFilters(); // You would also need to import applyUrlFilters
    loadCategories(true);   // Load ONLY skill categories
  });

  function goToAddSkill() {
    // Uncomment when form is ready
    // push('/post-skill');
    alert('Navigate to Add Skill form (Not implemented yet)');
  }
</script>

<!-- Main Content -->
<section class="skill-sharing-container">
  <h2>Explore Skill Sharing</h2>

  <SkillSearchForm></SkillSearchForm>
 
  <div class="results-header">
    <div class="results-count">
      {$totalResults} skills found
    </div>
    <!-- <button class="add-skill-button" on:click={goToAddSkill}>
      Add Your Skill
    </button> -->
  </div>

  <SkillResults results={$results} loading={$isLoading} error={$searchError}></SkillResults> 
</section>

<style>
.skill-sharing-container {
  max-width: 1200px;
  margin: 40px auto;
  padding: 20px;
}

.skill-sharing-container h2 {
  font-size: 2rem;
  margin-bottom: 20px;
  color: #4a4a4a;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.results-count {
  font-size: 18px;
  color: #6a1b9a;
}

.add-skill-button {
  padding: 10px 20px;
  background-color: #ffc107;
  color: #4a4a4a;
  border: none;
  border-radius: 5px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.add-skill-button:hover {
  background-color: #ffb300;
}
</style>
