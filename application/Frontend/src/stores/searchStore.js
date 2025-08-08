import { writable, derived, get } from 'svelte/store';

// --- Writable Stores for Individual Filters ---
export const searchQuery = writable('');
export const selectedCategory = writable(0); // 0 means "All Categories"
export const selectedCondition = writable(''); // '' means "Any Condition"
export const minPrice = writable(''); // Empty string means no min price
export const maxPrice = writable(''); // Empty string means no max price
export const isSkillSharing = writable(null); // true=skills, false=items, null=all (initially)

// --- Writable Stores for Results & State ---
export const results = writable([]);
export const totalResults = writable(0);
export const isLoading = writable(false);
export const searchError = writable(null);

// --- Derived Store for API/URL Parameters ---
// Recalculates whenever any filter store changes
export const searchParams = derived(
  [searchQuery, selectedCategory, selectedCondition, minPrice, maxPrice, isSkillSharing],
  ([$searchQuery, $selectedCategory, $selectedCondition, $minPrice, $maxPrice, $isSkillSharing]) => {
    const params = new URLSearchParams();
    if ($searchQuery) params.append('q', $searchQuery);
    if ($selectedCategory !== 0) params.append('category_id', $selectedCategory);

    // Only include item-specific filters if not explicitly searching for skills
    if ($isSkillSharing !== true) {
      if ($selectedCondition) params.append('item_condition', $selectedCondition);
      if ($minPrice && !isNaN(parseFloat($minPrice))) params.append('min_price', parseFloat($minPrice));
      if ($maxPrice && !isNaN(parseFloat($maxPrice))) params.append('max_price', parseFloat($maxPrice));
    }

    // Add the main skill filter if it's set (true or false)
    if ($isSkillSharing !== null) {
      params.append('is_skill_sharing', $isSkillSharing);
    }
    console.log('Derived searchParams updated:', params.toString());
    return params;
  }
);

// --- API Configuration ---
const API_BASE_URL = typeof window !== 'undefined' ? window.location.origin + '/api' : '/api';

// --- Core Search Function ---
// Performs search using the current state derived from searchParams
export async function performSearch(updateUrl = true) {
  try {
    let currentSearchParams;
    const unsubscribe = searchParams.subscribe(value => { currentSearchParams = value; });
    unsubscribe(); // Get current value and unsubscribe

    console.log('Performing search with params:', currentSearchParams.toString());

    isLoading.set(true);
    searchError.set(null);

    const response = await fetch(`${API_BASE_URL}/search?${currentSearchParams.toString()}`);

    if (!response.ok) throw new Error(`Search failed with status: ${response.status}`);

    const data = await response.json();
    results.set(data.results);
    totalResults.set(data.total);

    // Update URL after successful search if requested
    if (updateUrl && typeof window !== 'undefined') {
      const url = new URL(window.location);
      url.search = currentSearchParams.toString();
      window.history.replaceState({}, '', url);
    }

  } catch (error) {
    console.error('Error performing search:', error);
    searchError.set(error.message || 'Failed to load search results');
    results.set([]); // Clear results on error
    totalResults.set(0);
  } finally {
    isLoading.set(false);
  }
}

// --- Context Reset Function ---
// Call this from page components (Home, SkillSharing) on mount
// Sets the skill context and resets all other filters.
export function resetSearchContext(skillContext) { // skillContext = true (skills), false (items)
  console.log(`Resetting search context for: ${skillContext ? 'Skills' : 'Items'}`);

  // 1. Set the primary context
  isSkillSharing.set(skillContext);

  // 2. Reset all other filters to defaults
  searchQuery.set('');
  selectedCategory.set(0);
  selectedCondition.set(''); // Will be ignored by derived store if skillContext is true
  minPrice.set('');        // Will be ignored by derived store if skillContext is true
  maxPrice.set('');        // Will be ignored by derived store if skillContext is true

  // 3. Optionally clear previous results immediately
  results.set([]);
  totalResults.set(0);
  searchError.set(null);

  // 4. Trigger a search for the new context
  // Pass updateUrl=false because the URL should reflect the page context, not empty filters yet
  // Explicitly pass the skillContext to ensure the correct filter is applied immediately
  performSearch(false); // updateUrl = false. searchParams will be derived from the store values set above.
}

// --- Function to Clear Active Filters (without changing context) ---
export function clearActiveFilters() {
  const currentSkillContext = get(isSkillSharing);
  console.log(`Clearing active filters for context: ${currentSkillContext === true ? 'Skills' : (currentSkillContext === false ? 'Items' : 'All/None')}`);

  searchQuery.set('');
  selectedCategory.set(0); // "All Categories"

  // Only reset item-specific filters if not in skill-sharing mode,
  // or if context is null (though usually forms are specific)
  if (currentSkillContext !== true) {
    selectedCondition.set(''); // "Any Condition"
    minPrice.set('');
    maxPrice.set('');
  }
  // If we were in a skill context, those specific filters (if any existed) would be reset by the generic ones above.
  // For now, this is fine as skill search is simpler.

  // Clear results and trigger a new search
  // results.set([]); // performSearch will update these
  // totalResults.set(0);
  // searchError.set(null);

  performSearch(); // Re-run search, update URL by default
}

// --- Initialization from URL (Optional - for deep linking) ---
// This can be called *after* resetSearchContext if you want to allow
// loading specific filters from the URL even within a context.
export function applyUrlFilters() {
    if (typeof window === 'undefined') return;
    console.log('Applying filters from URL (if any)...');
    const urlParams = new URLSearchParams(window.location.search);

    // Only apply filters from URL if they exist, otherwise keep defaults from reset
    if (urlParams.has('q')) searchQuery.set(urlParams.get('q'));
    if (urlParams.has('category_id')) selectedCategory.set(Number(urlParams.get('category_id')));

    // Apply item-specific filters only if relevant to current context
    const currentSkillContext = get(isSkillSharing);
    if (currentSkillContext !== true) {
        if (urlParams.has('item_condition')) selectedCondition.set(urlParams.get('item_condition'));
        if (urlParams.has('min_price')) minPrice.set(urlParams.get('min_price'));
        if (urlParams.has('max_price')) maxPrice.set(urlParams.get('max_price'));
    }
    // Note: isSkillSharing is already set by resetSearchContext, URL param for it is handled implicitly

    // Re-run search if URL had specific filters
    if (urlParams.toString().length > 0 && urlParams.get('is_skill_sharing') === null) { // Avoid re-search if only skill filter was in URL
        console.log('URL contained filters, re-running search.');
        performSearch(false); // Perform search with URL filters, don't update URL again
    }
}