<script>
  import { onMount, onDestroy } from 'svelte'; // Import onMount and onDestroy
  import Router from 'svelte-spa-router'; // Router is the default export
  import { push, pop, replace, loc } from 'svelte-spa-router'; // Import loc store and navigation functions
  import { get } from 'svelte/store'; // Import get

  import DisclaimerBanner from './components/DisclaimerBanner.svelte';
  import Header from './components/Header.svelte';
  import Navigation from './components/Navigation.svelte';
  import Home from './components/Home.svelte';
  import ListingDetail from './components/ListingDetail.svelte';
  import AboutPage from './components/AboutPage.svelte';
  import Post from './components/Post.svelte';
  import Login from './components/Login.svelte';
  import Register from './components/Register.svelte';
  import PostSkill from './components/PostSkill.svelte';
  import SkillSharing from './components/SkillSharing.svelte';
  import MessagingWrapper from './components/messaging/MessagingWrapper.svelte';
  import TeamMemberDetail from './components/TeamMemberDetail.svelte';
  import MyListings from './components/MyListings.svelte';
  import EditListing from './components/EditListing.svelte';
  import AdminApprovalPage from './components/AdminApprovalPage.svelte';
  import ForgotPassword from './components/ForgotPassword.svelte'; // Import ForgotPassword
  import Footer from './components/Footer.svelte';
  import { loadCategories } from './stores/categoryStore.js';
  import { isAuthenticated, user as authUserStore, setAuthenticated, setUser } from './stores/authStore.js';

  // Define your Google Analytics Measurement ID
  const GA_MEASUREMENT_ID = 'G-2FQ3ST39P5';

  let unsubscribeLoc; // To store the unsubscribe function for the loc store

  // Load categories once when the app starts
  onMount(async () => {
    loadCategories();

    // Base API URL
    const API_BASE_URL = typeof window !== 'undefined' ? window.location.origin + '/api' : '/api';

    const token = localStorage.getItem('access_token');

    if (token) {
        try {
            const userResponse = await fetch(`${API_BASE_URL}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (userResponse.ok) {
                const userData = await userResponse.json();
                setAuthenticated(true);
                setUser(userData);
                console.log('App: User authenticated via token on mount.');
            } else if (userResponse.status === 401) {
                console.warn('App: Token invalid or expired. Clearing auth state.');
                setAuthenticated(false);
                setUser(null);
                localStorage.removeItem('access_token');
            } else {
                console.error('App: Failed to fetch user data:', userResponse.statusText);
                setAuthenticated(false);
                setUser(null);
                localStorage.removeItem('access_token');
            }
        } catch (error) {
            console.error('App: Error during user data fetch:', error);
            setAuthenticated(false);
            setUser(null);
            localStorage.removeItem('access_token');
        }
    } else {
        console.log('App: No token found on mount.');
        setAuthenticated(false);
        setUser(null);
    }

    // --- Google Analytics SPA Page View Tracking ---
    // Check if the gtag function is available (loaded from index.html)
    if (typeof window.gtag === 'function') {
        // Subscribe to route changes using the 'loc' store from svelte-spa-router
        unsubscribeLoc = loc.subscribe((currentLocation) => {
            if (currentLocation && currentLocation.location) { // Check if currentLocation and location property exist
                const path = currentLocation.location;    // The new path from the loc store
                const title = document.title;           // Current document title

                // Send a page_view event to Google Analytics
                window.gtag('config', GA_MEASUREMENT_ID, {
                    page_path: path,
                    page_title: title,
                });
                console.log(`Google Analytics: Pageview sent for path: ${path}, title: ${title}`);
            }
        });
    } else {
        console.warn('Google Analytics: gtag function not found. SPA Pageviews not tracked.');
    }
    // --- End of Google Analytics SPA Tracking ---
  });

  onDestroy(() => {
    // Unsubscribe from the loc store when the component is destroyed to prevent memory leaks
    if (unsubscribeLoc) {
      unsubscribeLoc();
    }
  });
  
  // Define routes
  const routes = {
    '/': Home,
    '/listings/:id': ListingDetail,
    '/listings/edit/:id': EditListing,
    '/about': AboutPage,
    '/team/:memberId': TeamMemberDetail,
    '/post' : Post,
    '/login': Login,
    '/register': Register,
    '/skill-sharing': SkillSharing,
    '/messages': MessagingWrapper,
    '/messages/:conversation_id': MessagingWrapper,
    '/post-skill': PostSkill,
    '/my-listings': MyListings,
    '/admin/approve-listings': AdminApprovalPage,
    '/forgot-password': ForgotPassword // Add route for ForgotPassword
  };
  
  // Define a route guard function
  function beforeSend(detail) {
    console.log('[ROUTER GUARD CALLED] beforeSend triggered. Detail:', detail); // ADD THIS TOP-LEVEL LOG
    const { location } = detail;
    const protectedRoutes = ['/post', '/post-skill', '/my-listings', '/messages'];
    const protectedPrefixes = ['/listings/edit', '/admin'];

    const isRouteProtectedExact = protectedRoutes.includes(location);
    const isRouteProtectedPrefix = protectedPrefixes.some(prefix => location.startsWith(prefix));

    if (isRouteProtectedExact || isRouteProtectedPrefix) {
      const authenticated = get(isAuthenticated);
      console.log(`Route guard for ${location}: Route is protected. Current auth state: ${authenticated}`);
      if (!authenticated) {
        console.error(`[CRITICAL GUARD CHECK] User NOT authenticated for protected route ${location}. Auth state: ${authenticated}. Attempting redirect to /login and returning FALSE.`);
        // Perform the redirect. The `return false` will prevent the current navigation to the protected route.
        // The push to '/login' will trigger a new navigation cycle for the '/login' route.
        replace('/login'); // Use replace to avoid polluting history with the protected route attempt
        return false; // Explicitly block navigation
      }
      // User is authenticated, allow navigation to the protected route
      console.log(`User IS authenticated for protected route ${location}. Allowing navigation.`);
      return true;
    }

    // Route is not protected
    console.log(`Route guard for ${location}: Route is not protected. Navigation allowed. Returning true.`);
    return true;
  }

  // Navigation functions
  function goToListing(id) { push(`/listings/${id}`); }
  function goToAbout() { push('/about'); }
  function goToHome() { push('/'); }
  function goToPost() { push('/post'); }
  function goToLogin() { push('/login'); }
  function goToRegister() { push('/register'); }
  function goToSkillSharing() { push('/skill-sharing'); }
  function goToPostSkill() { push('/post-skill'); }
</script>

<Header />
<Navigation />

<main>
  <Router {routes} {beforeSend} />
</main>

<Footer />

<style>
  :global(body) {
    overflow-x: hidden;
    font-family: Arial, sans-serif;
    background-color: #f9f9f9;
    margin: 0;
    padding: 0;
    color: #4a4a4a;
  }
  
  main {
    max-width: 1600px;
    margin: 0 auto;
    width: 100%;
  }
</style>
