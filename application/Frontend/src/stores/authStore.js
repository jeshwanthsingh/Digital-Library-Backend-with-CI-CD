import { writable } from 'svelte/store';

const USER_STORAGE_KEY = 'authUser';
const TOKEN_STORAGE_KEY = 'access_token';

// Helper to get item from localStorage and parse JSON
const getStoredUser = () => {
  const stored = localStorage.getItem(USER_STORAGE_KEY);
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch (e) {
      console.error('Error parsing stored user data from localStorage:', e);
      localStorage.removeItem(USER_STORAGE_KEY); // Remove invalid data
      return null;
    }
  }
  return null;
};

// Initialize isAuthenticated based on presence of access_token in localStorage
export const isAuthenticated = writable(localStorage.getItem(TOKEN_STORAGE_KEY) !== null);

// Initialize user store from localStorage or to null if not found/invalid
export const user = writable(getStoredUser());

// Function to set the authenticated user's information, store it, and update auth status
// This function becomes the primary way to set the application's auth state.
export function setUser(userData) {
  if (userData && userData.token) {
    // Store user object and token
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(userData));
    localStorage.setItem(TOKEN_STORAGE_KEY, userData.token);
    user.set(userData);
    isAuthenticated.set(true);
  } else {
    // Clear user object and token (handles logout or setting user to null)
    localStorage.removeItem(USER_STORAGE_KEY);
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    user.set(null);
    isAuthenticated.set(false);
  }
}

// Function to handle user logout
export function logoutUser() {
  setUser(null); // This will clear storage, update user store, and set isAuthenticated to false
  // Optionally, redirect to login page if this store should handle routing:
  // import { push } from 'svelte-spa-router';
  // push('/login');
}

// Function to explicitly set authentication status.
// Note: setUser now also handles isAuthenticated. Direct calls to setAuthenticated
// should be reviewed, as setUser provides a more comprehensive state update.
export function setAuthenticated(value) {
  isAuthenticated.set(value);
  // If explicitly setting isAuthenticated to false, ensure user data is also cleared.
  if (!value) {
      localStorage.removeItem(USER_STORAGE_KEY);
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      user.set(null);
  }
}