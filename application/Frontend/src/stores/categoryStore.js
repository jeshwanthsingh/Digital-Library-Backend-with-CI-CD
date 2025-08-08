import { writable } from 'svelte/store';

// Store for categories data
export const categories = writable([]);
export const categoriesLoading = writable(false);
export const categoriesError = writable(null);

// Base API URL
const API_BASE_URL = typeof window !== 'undefined' ? window.location.origin + '/api' : '/api';

// Function to load categories, accepts optional isSkill parameter
export async function loadCategories(isSkill = null) {
  try {
    categoriesLoading.set(true);
    categoriesError.set(null);

    let url = `${API_BASE_URL}/categories`;
    if (isSkill !== null) {
      url += `?is_skill=${isSkill}`; // Append is_skill parameter
    }
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to load categories with status: ${response.status}`);
    }
    
    const data = await response.json();
    categories.set(data);
    
  } catch (error) {
    console.error('Error loading categories:', error);
    categoriesError.set(error.message || 'Failed to load categories');
  } finally {
    categoriesLoading.set(false);
  }
}
