import { writable } from 'svelte/store';

// Store for listing details
export const currentListing = writable(null);
export const listingLoading = writable(false);
export const listingError = writable(null);

// Base API URL
const API_BASE_URL = typeof window !== 'undefined' ? window.location.origin + '/api' : '/api';

// Function to fetch listing details
export async function fetchListingDetails(id) {
  if (!id) return;
  
  try {
    listingLoading.set(true);
    listingError.set(null);
    
    const response = await fetch(`${API_BASE_URL}/listings/${id}`);
    
    if (!response.ok) {
      throw new Error(`Failed to load listing with status: ${response.status}`);
    }
    
    const data = await response.json();
    currentListing.set(data);
    
  } catch (error) {
    console.error(`Error loading listing ${id}:`, error);
    listingError.set(error.message || 'Failed to load listing details');
    currentListing.set(null);
  } finally {
    listingLoading.set(false);
  }
}
