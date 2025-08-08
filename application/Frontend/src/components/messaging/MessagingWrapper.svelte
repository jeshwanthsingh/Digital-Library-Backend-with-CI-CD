<script>
  import { onMount, onDestroy } from 'svelte';
  import { get, writable } from 'svelte/store';
  import { push } from 'svelte-spa-router';
  import { isAuthenticated, user as authUserStore } from '../../stores/authStore.js';
  import Inbox from './Inbox.svelte';
  import MessageThread from './MessageThread.svelte';
  import UserSearch from './UserSearch.svelte'; // Import UserSearch
  import {
      conversations,
      conversationsLoading,
      conversationsError,
      loadConversations,
      messages,
      messagesLoading,
      messagesError,
      loadMessages,
      sendMessage,
      activeConversation,
      initiateOrOpenConversationWithUser // Import the new function
  } from '../../stores/messagingStore.js';

  export let params = {};
  const API_BASE_URL = typeof window !== 'undefined' ? window.location.origin + '/api' : '/api';

  let unsubscribeAuth, unsubscribeActiveConversation, unsubscribeAuthUser;
  let instanceId = ''; // To be set in onMount for instance-specific logging
  let showUserSearch = false; // State for showing user search
  let userSelectionError = writable(null); // Store for errors during user selection/conversation initiation

  // Reactive logging
  $: {
    if (instanceId) { // Only log if instanceId is set
      console.log(`[MW Reactive Log - ${instanceId}] params.conversation_id: ${params ? params.conversation_id : 'undefined'}, $activeConversation ID: ${$activeConversation ? $activeConversation.conversation_id : 'null'}, $conversationsLoading: ${$conversationsLoading}, showUserSearch: ${showUserSearch}`);
    }
  }

  async function handleConversationParamChange(convIdParam) {
    console.log(`[MW handleConvParamChange - ${instanceId}] Triggered. convIdParam: ${convIdParam}. Current $activeConv ID: ${$activeConversation ? $activeConversation.conversation_id : 'null'}`);
    const token = localStorage.getItem('access_token');
    const authenticated = get(isAuthenticated);
    userSelectionError.set(null); // Clear any previous user selection errors

    if (!authenticated || !token) {
        console.log(`[MW handleConvParamChange - ${instanceId}] Not authenticated/no token. Redirecting to login.`);
        activeConversation.set(null);
        conversations.set([]);
        messages.set([]);
        showUserSearch = false; // Ensure user search is hidden
        if (typeof window !== 'undefined' && window.location.pathname !== '/login') push('/login');
        return;
    }

    if (convIdParam) {
        showUserSearch = false; // Navigating to a conversation, hide user search
        if ($activeConversation && $activeConversation.conversation_id === convIdParam) {
            console.log(`[MW handleConvParamChange - ${instanceId}] Conv ${convIdParam} already active.`);
            return;
        }
        console.log(`[MW handleConvParamChange - ${instanceId}] Loading conversation: ${convIdParam}`);
        try {
            const response = await fetch(`${API_BASE_URL}/messages/conversations/${convIdParam}`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (response.ok) {
                const conversationData = await response.json();
                console.log(`[MW handleConvParamChange - ${instanceId}] Fetched conv ${convIdParam}. Setting active.`);
                activeConversation.set(conversationData);
            } else {
                console.error(`[MW handleConvParamChange - ${instanceId}] Failed to fetch conv ${convIdParam}: ${response.status}. Clearing active, redirecting to inbox.`);
                activeConversation.set(null);
                if (response.status === 401) {
                    if (typeof window !== 'undefined' && window.location.pathname !== '/login') push('/login');
                } else if (typeof window !== 'undefined' && window.location.pathname !== '/messages' && window.location.pathname !== '/messages/') {
                    push('/messages');
                }
            }
        } catch (error) {
            console.error(`[MW handleConvParamChange - ${instanceId}] Error fetching conv ${convIdParam}:`, error);
            activeConversation.set(null);
            if (typeof window !== 'undefined' && window.location.pathname !== '/messages' && window.location.pathname !== '/messages/') push('/messages');
        }
    } else { // No convIdParam, should be inbox view (or user search if active)
        console.log(`[MW handleConvParamChange - ${instanceId}] No convIdParam. Ensuring inbox view (or user search).`);
        if ($activeConversation !== null) {
            console.log(`[MW handleConvParamChange - ${instanceId}] Clearing existing active conversation.`);
            activeConversation.set(null);
        }
        // Do not automatically hide user search here, it's controlled by its own logic
        if (!showUserSearch && !$conversationsLoading && get(conversations).length === 0 && authenticated && token) {
            console.log(`[MW handleConvParamChange - ${instanceId}] Loading conversations for inbox (not in user search).`);
            loadConversations(token);
        } else if ((!authenticated || !token) && typeof window !== 'undefined' && window.location.pathname !== '/login') {
            console.log(`[MW handleConvParamChange - ${instanceId}] No convIdParam, but not authenticated. Redirecting to login.`);
            push('/login');
        }
    }
  }

  // Reactive call to handleConversationParamChange when params (from router) change.
  $: if (instanceId && typeof params !== 'undefined') { // Ensure instanceId is set before reacting
    console.log(`[MW Reactive $:params - ${instanceId}] params changed:`, JSON.stringify(params));
    if (params.conversation_id) { // If navigating to a specific conversation, hide user search
        showUserSearch = false;
    }
    handleConversationParamChange(params.conversation_id);
  }

  onMount(() => {
    instanceId = Math.random().toString(36).substring(2, 9);
    console.log(`[MW onMount - ${instanceId}] Mounted. Initial params:`, JSON.stringify(params));

    unsubscribeAuth = isAuthenticated.subscribe(authStatus => {
        console.log(`[MW isAuthenticated.subscribe - ${instanceId}] Auth status: ${authStatus}`);
        if (authStatus) {
            userSelectionError.set(null); // Clear errors on auth change
            if (!showUserSearch) {
                if (!params || typeof params.conversation_id === 'undefined') {
                    console.log(`[MW isAuthenticated.subscribe - ${instanceId}] Auth true, no conv ID, not in user search. Ensuring inbox.`);
                    handleConversationParamChange(null);
                } else {
                    console.log(`[MW isAuthenticated.subscribe - ${instanceId}] Auth true, conv ID ${params.conversation_id} present, not in user search. Reactive handler should manage.`);
                    handleConversationParamChange(params.conversation_id); // Re-evaluate with auth
                }
            }
        } else {
            console.log(`[MW isAuthenticated.subscribe - ${instanceId}] Logged out. Clearing state, redirecting.`);
            activeConversation.set(null);
            conversations.set([]);
            messages.set([]);
            showUserSearch = false; // Hide user search on logout
            if (typeof window !== 'undefined' && window.location.pathname !== '/login') push('/login');
        }
    });

    unsubscribeActiveConversation = activeConversation.subscribe(newActiveConvo => {
        console.log(`[MW activeConversation.subscribe - ${instanceId}] Active convo changed: ${newActiveConvo ? newActiveConvo.conversation_id : 'null'}`);
        const token = localStorage.getItem('access_token');
        if (newActiveConvo && newActiveConvo.conversation_id) {
            showUserSearch = false; // Active conversation means we are not in user search mode
            userSelectionError.set(null); // Clear errors
            if (get(isAuthenticated) && token) {
                loadMessages(newActiveConvo.conversation_id, token);
            } else {
                 console.warn(`[MW activeConversation.subscribe - ${instanceId}] Auth/token issue. Cannot load messages. Redirecting.`);
                 if (typeof window !== 'undefined' && window.location.pathname !== '/login') push('/login');
            }
        } else {
            messages.set([]);
            const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';
            if (!showUserSearch && params && params.conversation_id && currentPath.includes(`/messages/${params.conversation_id}`)) {
                 console.log(`[MW activeConversation.subscribe - ${instanceId}] Active convo null, URL for thread ${params.conversation_id}, not in user search. Navigating to /messages.`);
                 if (currentPath !== '/messages' && currentPath !== '/messages/') {
                    // push('/messages');
                 }
            }
        }
    });
    unsubscribeAuthUser = authUserStore.subscribe(_ => {});
  });

  onDestroy(() => {
    console.log(`[MW onDestroy - ${instanceId}] Unmounted. Params:`, JSON.stringify(params));
    if (unsubscribeAuth) unsubscribeAuth();
    if (unsubscribeActiveConversation) unsubscribeActiveConversation();
    if (unsubscribeAuthUser) unsubscribeAuthUser();
  });

  function selectConversation(conversation) {
    console.log(`[MW selectConversation - ${instanceId}] Selected: ${conversation.conversation_id}. Current param: ${params ? params.conversation_id : 'undefined'}`);
    showUserSearch = false; // Selecting a conversation hides user search
    userSelectionError.set(null);
    if (!params || params.conversation_id !== conversation.conversation_id) {
        push(`/messages/${conversation.conversation_id}`);
    } else {
        handleConversationParamChange(conversation.conversation_id);
    }
  }

  function backToInbox() {
    console.log(`[MW backToInbox - ${instanceId}] Clicked. Current param: ${params ? params.conversation_id : 'undefined'}`);
    userSelectionError.set(null); // Clear any errors when going back
    if (showUserSearch) {
        showUserSearch = false;
        if (!$activeConversation) {
          const token = localStorage.getItem('access_token');
          if (get(isAuthenticated) && token && !$conversationsLoading && get(conversations).length === 0) {
              loadConversations(token);
          }
        }
        return;
    }
    if (params && typeof params.conversation_id !== 'undefined' && params.conversation_id !== null) {
        push('/messages');
    } else {
        activeConversation.set(null);
        const token = localStorage.getItem('access_token');
        if (get(isAuthenticated) && token && !$conversationsLoading && get(conversations).length === 0) {
            loadConversations(token);
        }
    }
  }

  async function handleSend(text) {
    if ($activeConversation && $activeConversation.conversation_id && $authUserStore) {
      const token = localStorage.getItem('access_token');
      if (get(isAuthenticated) && token) {
        try {
          await sendMessage($activeConversation.conversation_id, text, token);
        } catch (error) { console.error(`[MW handleSend - ${instanceId}] Send error:`, error); }
      } else { push('/login'); }
    }
  }

  function getChatPartnerName(conversation, currentUser) {
    if (!conversation || !currentUser || !conversation.user1 || !conversation.user2) return 'participant';
    return conversation.user1.user_id === currentUser.user_id ? (conversation.user2.username || 'participant') : (conversation.user1.username || 'participant');
  }

  function startNewMessage() {
    showUserSearch = true;
    activeConversation.set(null);
    userSelectionError.set(null);
    if (params && params.conversation_id) {
      push('/messages');
    }
  }

  async function handleUserSelected(event) {
    const selectedUser = event.detail;
    console.log(`[MW handleUserSelected - ${instanceId}] User selected:`, selectedUser);
    userSelectionError.set(null); // Clear previous errors

    if (!selectedUser || !selectedUser.user_id) {
        console.error(`[MW handleUserSelected - ${instanceId}] Invalid selected user data.`);
        userSelectionError.set("Invalid user selected. Please try again.");
        return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
        console.error(`[MW handleUserSelected - ${instanceId}] No access token found. Redirecting to login.`);
        userSelectionError.set("Authentication error. Please log in again.");
        push('/login');
        return;
    }

    showUserSearch = false; // Hide search UI optimistically

    try {
        const conversation = await initiateOrOpenConversationWithUser(selectedUser.user_id, token);
        if (conversation && conversation.conversation_id) {
            console.log(`[MW handleUserSelected - ${instanceId}] Conversation ${conversation.conversation_id} ready. Navigating.`);
            // The activeConversation store should be set by initiateOrOpenConversationWithUser
            // The reactive $:params should handle hiding userSearch if navigation occurs.
            push(`/messages/${conversation.conversation_id}`);
        } else {
            console.error(`[MW handleUserSelected - ${instanceId}] Failed to get a valid conversation object.`);
            userSelectionError.set("Could not start or find conversation. Please try again.");
            // Optionally, reshow user search or navigate to inbox
            // For now, rely on backToInbox or re-initiating search if needed.
        }
    } catch (error) {
        console.error(`[MW handleUserSelected - ${instanceId}] Error initiating conversation:`, error);
        userSelectionError.set(error.message || "An error occurred while starting the conversation.");
        // If error, user might want to try searching again or go to inbox.
        // Keeping showUserSearch = false might be okay, or set it back to true if that's preferred UX.
        // For now, it stays false, user can click "New Message" again.
    }
  }
</script>

{#key `${params.conversation_id}-${showUserSearch}`}
<div class="messaging-container" data-instance-id={instanceId}>
  {#if $conversationsLoading || $messagesLoading && !showUserSearch}
    <p class="loading-message">Loading messages...</p>
  {:else if $conversationsError && !showUserSearch}
    <p class="error-message">Error loading conversations: {$conversationsError}</p>
  {:else if $messagesError && !showUserSearch}
     <p class="error-message">Error loading messages: {$messagesError}</p>
  {:else if showUserSearch}
    <div>
      <button class="back-button" on:click={backToInbox}>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-arrow-left-short" viewBox="0 0 16 16">
           <path fill-rule="evenodd" d="M12 8a.5.5 0 0 1-.5.5H5.707l2.147 2.146a.5.5 0 0 1-.708.708l-3-3a.5.5 0 0 1 0-.708l3-3a.5.5 0 1 1 .708.708L5.707 7.5H11.5a.5.5 0 0 1 .5.5z"/>
        </svg>
        Back to Inbox
      </button>
      <UserSearch on:userSelected={handleUserSelected} />
    </div>
  {:else if $activeConversation}
    <div class="thread-view">
       <button class="back-button" on:click={backToInbox}>
         <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-arrow-left-short" viewBox="0 0 16 16">
           <path fill-rule="evenodd" d="M12 8a.5.5 0 0 1-.5.5H5.707l2.147 2.146a.5.5 0 0 1-.708.708l-3-3a.5.5 0 0 1 0-.708l3-3a.5.5 0 1 1 .708.708L5.707 7.5H11.5a.5.5 0 0 1 .5.5z"/>
         </svg>
         Back to Inbox
       </button>
       {#if $authUserStore && $activeConversation.user1 && $activeConversation.user2}
         <h2 class="section-title">Chat with {getChatPartnerName($activeConversation, $authUserStore)}</h2>
       {:else}
         <h2 class="section-title">Chat</h2>
       {/if}
       {#if $authUserStore}
         <MessageThread
            conversation={$activeConversation}
            currentUser={$authUserStore}
            messages={$messages}
            messagesLoading={$messagesLoading}
            messagesError={$messagesError}
          />
       {:else}
           <p>Loading chat interface...</p>
       {/if}
    </div>
  {:else} <!-- Neither active conversation nor user search, so show Inbox -->
    <div class="inbox-header">
      <h2 class="section-title">Inbox</h2>
      <button class="new-message-button" on:click={startNewMessage}>New Message</button>
    </div>
    {#if $authUserStore}
      <Inbox
        conversations={$conversations}
        currentUser={$authUserStore}
        conversationsLoading={$conversationsLoading}
        conversationsError={$conversationsError}
        on:select={e => selectConversation(e.detail)} />
    {:else}
      <p>Loading user information...</p>
    {/if}
  {/if}
</div>
{/key}

<style>
  .messaging-container {
    max-width: 900px;
    margin: 2rem auto;
    padding: 1.5rem;
    background-color: #f9f9f9; /* Light grey background, adjust to your theme */
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }

  .thread-view {
    display: flex;
    flex-direction: column;
  }

  .back-button {
    display: inline-flex; /* Changed to inline-flex for better alignment of icon and text */
    align-items: center;
    background-color: var(--primary-color, #007bff); /* Use CSS var or default blue */
    color: white;
    padding: 0.6rem 1.2rem;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 0.95rem;
    font-weight: 500;
    margin-bottom: 1.5rem;
    transition: background-color 0.2s ease;
    align-self: flex-start; /* Align button to the left */
  }

  .back-button svg {
    margin-right: 0.5rem; /* Space between icon and text */
  }

  .back-button:hover {
    background-color: var(--primary-dark-color, #0056b3); /* Darker shade on hover */
  }

  .section-title {
    font-size: 1.75rem;
    color: var(--text-color-dark, #333); /* Adjust to your theme */
    margin-bottom: 1.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--primary-light-color, #e0e0e0); /* Light border */
  }

  .inbox-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem; /* Matches section-title bottom margin */
  }

  .inbox-header .section-title {
    margin-bottom: 0; /* Remove bottom margin as it's handled by inbox-header */
  }

  .new-message-button {
    background-color: var(--accent-color, #28a745); /* Example: Green, adjust to your theme */
    color: white;
    padding: 0.6rem 1.2rem;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 0.95rem;
    font-weight: 500;
    transition: background-color 0.2s ease;
  }

  .new-message-button:hover {
    background-color: var(--accent-dark-color, #1e7e34); /* Darker shade on hover */
  }

  .loading-message, .error-message {
    text-align: center;
    padding: 2rem;
    font-size: 1.1rem;
  }

  .loading-message {
    color: var(--text-color-medium, #555);
  }

  .error-message {
    color: var(--error-color, #d9534f); /* A common error color (reddish) */
    background-color: var(--error-bg-color, #f2dede);
    border: 1px solid var(--error-border-color, #ebccd1);
    border-radius: 4px;
  }

  /* Consider adding global styles or variables for colors (e.g., in App.svelte or a main.css)
     --primary-color: #yourPrimaryColor;
     --primary-dark-color: #yourPrimaryDarkColor;
     --primary-light-color: #yourPrimaryLightColor;
     --text-color-dark: #yourDarkTextColor;
     --text-color-medium: #yourMediumTextColor;
     --error-color: #yourErrorColor;
     --error-bg-color: #yourErrorBgColor;
     --error-border-color: #yourErrorBorderColor;
     --accent-color: #yourAccentColor;
     --accent-dark-color: #yourAccentDarkColor;
  */
</style>