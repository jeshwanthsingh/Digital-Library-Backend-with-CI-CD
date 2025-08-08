<script>
    import { afterUpdate, onMount, tick } from 'svelte';
    import { sendMessage } from '../../stores/messagingStore.js';

    export let conversation;
    export let currentUser;
    export let messages;
    export let messagesLoading;
    export let messagesError;

    let newMessageContent = '';
    let isSending = false;
    let messageListElement; // For auto-scrolling
    let scrolledToBottomInitially = false;

    $: conversationId = conversation ? conversation.conversation_id : null;
    $: chatPartner = conversation && currentUser ? getChatPartner(conversation, currentUser) : null;
    $: listing = conversation ? conversation.listing : null;

    function getChatPartner(conv, user) {
        if (!conv || !user || !conv.user1 || !conv.user2 || typeof user.user_id === 'undefined') {
            return null;
        }
        return conv.user1.user_id === user.user_id ? conv.user2 : conv.user1;
    }

    async function handleSendMessage() {
        if (!newMessageContent.trim() || !conversationId || !currentUser) return;
        isSending = true;
        const token = localStorage.getItem('access_token');
        if (!token) {
            console.error("Auth token missing, cannot send message.");
            alert("Your session may have expired. Please log in again.");
            isSending = false;
            // Consider a more robust way to handle auth failure, e.g., redirecting via a store or event
            if (typeof window !== 'undefined') window.location.href = '/login';
            return;
        }

        try {
            await sendMessage(conversationId, newMessageContent.trim(), token);
            newMessageContent = '';
            await tick(); // Wait for DOM to update
            scrollToBottom(true); // Force scroll after sending a message
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message. Please try again.');
        } finally {
            isSending = false;
        }
    }

    function scrollToBottom(force = false) {
        if (messageListElement && messageListElement.scrollHeight > messageListElement.clientHeight) {
            const isScrolledNearBottom = messageListElement.scrollHeight - messageListElement.scrollTop - messageListElement.clientHeight < 100; // User is within 100px of the bottom
            if (force || isScrolledNearBottom) {
                messageListElement.scrollTop = messageListElement.scrollHeight;
                // console.log('[scrollToBottom] Scrolled. Forced:', force, 'NearBottom:', isScrolledNearBottom);
            } else {
                // console.log('[scrollToBottom] Did NOT scroll. Forced:', force, 'NearBottom:', isScrolledNearBottom);
            }
        }
    }

    onMount(async () => { // Add async here
        await tick(); // Ensure DOM is fully rendered
        if (messageListElement && messages && messages.length > 0) {
             scrollToBottom(true); // Force scroll on mount if there are messages
        }
        scrolledToBottomInitially = true;
        // console.log('[onMount] Completed. scrolledToBottomInitially set to true.');
    });

    // afterUpdate is called after the DOM has been updated
    afterUpdate(() => {
        // console.log('[afterUpdate] Triggered. scrolledToBottomInitially:', scrolledToBottomInitially, 'Messages length:', messages ? messages.length : 'null');
        if (scrolledToBottomInitially && messageListElement && messages && messages.length > 0) {
            // Don't force scroll; let scrollToBottom decide based on user's current scroll position
            scrollToBottom();
        }
    });

</script>

<svelte:head>
    <title>Chat with {chatPartner ? chatPartner.username : (conversationId ? 'User' : 'Loading...')} - Agora</title>
</svelte:head>

<div class="message-thread-content">
    {#if listing}
        <a href={`/listing/${listing.listing_id}`} class="listing-context-link">
            <div class="listing-context">
                <span class="listing-context-label">Regarding:</span>
                <span class="listing-context-title">{listing.title}</span>
                {#if listing.price}
                <span class="listing-context-price">${listing.price.toFixed(2)}</span>
                {/if}
            </div>
        </a>
    {/if}

    {#if messagesLoading}
        <p class="loading-message">Loading messages...</p>
    {:else if messagesError}
        <p class="error-message">Error loading messages: {messagesError.message || messagesError}</p>
    {:else if !messages || messages.length === 0}
        <p class="no-messages-prompt">No messages yet. Be the first to say hello!</p>
    {:else}
        <div class="message-list" bind:this={messageListElement} role="log" aria-live="polite">
            {#each messages as message (message.message_id)}
                {@const isSentByCurrentUser = currentUser && message.sender_id === currentUser.user_id}
                <div class="message-item-wrapper {isSentByCurrentUser ? 'sent-wrapper' : 'received-wrapper'}">
                    {#if !isSentByCurrentUser && chatPartner}
                        <div class="avatar-placeholder" title={chatPartner.username?.substring(0,1).toUpperCase() || 'U'}>
                            {chatPartner.username?.substring(0,1).toUpperCase() || 'P'}
                        </div>
                    {/if}
                    <div class="message-item {isSentByCurrentUser ? 'sent' : 'received'}">
                        <div class="message-bubble">
                            {#if !isSentByCurrentUser && chatPartner}
                                <p class="message-sender">{chatPartner.username || 'Participant'}</p>
                            {/if}
                            <p class="message-content"dir="auto">{message.content}</p>
                            <span class="message-time">{new Date(message.created_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true })}</span>
                        </div>
                    </div>
                 </div>
            {/each}
        </div>
    {/if}

    <form class="message-input-area" on:submit|preventDefault={handleSendMessage}>
        <textarea
            bind:value={newMessageContent}
            placeholder="Type your message here..."
            rows="1"
            disabled={isSending || !currentUser || !conversationId}
            on:keypress={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } }}
            aria-label="Message input"
        ></textarea>
        <button type="submit" disabled={isSending || !newMessageContent.trim() || !currentUser || !conversationId} aria-label="Send message">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-send-fill" viewBox="0 0 16 16">
              <path d="M15.964.686a.5.5 0 0 0-.65-.65L.767 5.855H.766l-.452.18a.5.5 0 0 0-.082.887l.41.26.001.002 4.995 3.178 3.178 4.995.002.002.26.41a.5.5 0 0 0 .886-.083l6-15Zm-1.833 1.89L6.637 10.07l-.215-.338a.5.5 0 0 0-.154-.154l-.338-.215 7.494-7.494 1.178-.471-.47 1.178Z"/>
            </svg>
        </button>
    </form>
</div>

<style>
    .message-thread-content {
        display: flex;
        flex-direction: column;
        /* Removed height: calc(100vh - ...), as the wrapper handles layout. Let content flow. */
        /* This component should fill the space given by its parent. */
        padding: 0; /* Padding is now on MessagingWrapper */
        width: 100%;
    }

    .listing-context-link {
        text-decoration: none;
        color: inherit;
        display: block; /* Make the whole area clickable */
        margin-bottom: 1rem;
    }
    .listing-context {
        padding: 0.75rem 1rem;
        background-color: var(--background-color-subtle, #f8f9fa);
        border-radius: 6px;
        border: 1px solid var(--border-color-soft, #e9ecef);
        text-align: left;
        font-size: 0.9rem;
        color: var(--text-color-secondary, #555);
        transition: background-color 0.2s ease;
    }
    .listing-context:hover {
        background-color: var(--background-color-subtle-hover, #e9ecef);
    }
    .listing-context-label {
        font-weight: 500;
        color: var(--text-color-medium, #333);
    }
    .listing-context-title {
        font-weight: 600;
        color: var(--primary-color, #007bff);
        margin-left: 0.25rem;
    }
    .listing-context-price {
        font-weight: 500;
        color: var(--text-color-success, #28a745);
        margin-left: 0.75rem;
        background-color: var(--background-color-price, #e6ffed);
        padding: 0.1rem 0.4rem;
        border-radius: 4px;
        font-size: 0.85rem;
    }


    .message-list {
        flex-grow: 1;
        overflow-y: auto;
        padding: 0.5rem 1rem; /* Reduced padding slightly */
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.75rem; /* Space between message items */
        /* Removed border, handled by wrapper or if we want card-like look */
        background-color: var(--chat-bg-color, #fff); /* Slightly off-white chat background */
        border-radius: 8px; /* If not full-bleed in wrapper */
        /* Consider a subtle border if needed: border: 1px solid var(--border-color-soft, #e9ecef); */
    }

    .message-item-wrapper {
        display: flex;
        align-items: flex-end; /* Align avatar with bottom of bubble */
        gap: 0.5rem; /* Space between avatar and bubble */
        max-width: 80%; /* Prevent messages from taking full width */
    }

    .message-item-wrapper.sent-wrapper {
        margin-left: auto; /* Push sent messages to the right */
        flex-direction: row-reverse; /* Keep bubble structure consistent */
    }
    .message-item-wrapper.received-wrapper {
        margin-right: auto; /* Push received messages to the left */
    }

    .avatar-placeholder {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background-color: var(--avatar-bg-color, #6a1b9a); /* Theme color for avatar */
        color: var(--avatar-text-color, white);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.9rem;
        flex-shrink: 0; /* Prevent shrinking */
        text-transform: uppercase;
        margin-bottom: 5px; /* Align with typical bubble shape */
    }


    .message-item { /* This is now an inner flex container for the bubble */
        display: flex; /* To align content within if needed */
    }

    .message-bubble {
        padding: 0.6rem 1rem;
        border-radius: 18px; /* More rounded bubbles */
        word-wrap: break-word;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        line-height: 1.5;
    }

    .message-item.sent .message-bubble {
        background-color: var(--sent-bubble-bg, #007bff); /* Primary action color */
        color: var(--sent-bubble-text, white);
        border-bottom-right-radius: 6px;
    }

    .message-item.received .message-bubble {
        background-color: var(--received-bubble-bg, #e9ecef); /* Light grey, more contrast */
        color: var(--received-bubble-text, #212529);
        border-bottom-left-radius: 6px;
    }

    .message-sender {
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
        color: var(--sender-name-color, #555); /* Default for received */
    }
    .message-item.sent .message-sender { /* Not typically shown for 'You' */
       display: none;
    }


    .message-content {
        margin: 0;
        font-size: 0.95rem;
        white-space: pre-wrap; /* Preserve line breaks and spaces */
    }

    .message-time {
        display: block;
        font-size: 0.7rem;
        text-align: right;
        margin-top: 0.3rem;
        opacity: 0.8;
    }
    .message-item.sent .message-time {
        color: var(--sent-time-color, rgba(255, 255, 255, 0.8));
    }
    .message-item.received .message-time {
        color: var(--received-time-color, #6c757d);
    }

    .message-input-area {
        display: flex;
        align-items: flex-end; /* Align button with bottom of textarea if it grows */
        padding: 0.75rem 0; /* Padding top/bottom only, side padding by wrapper */
        border-top: 1px solid var(--border-color-light, #dee2e6);
        background-color: var(--input-area-bg, #f8f9fa); /* Subtle background for input area */
        margin-top: auto; /* Pushes to bottom if content above is short */
    }

    .message-input-area textarea {
        flex-grow: 1;
        padding: 0.6rem 0.9rem;
        border: 1px solid var(--border-color-input, #ced4da);
        border-radius: 20px; /* Pill shape */
        margin-right: 0.5rem;
        font-size: 0.95rem;
        resize: none;
        min-height: 40px; /* Approx 1 line with padding */
        max-height: 100px; /* Approx 3-4 lines */
        overflow-y: auto;
        line-height: 1.4;
        background-color: var(--input-bg, #fff);
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .message-input-area textarea:focus {
        outline: none;
        border-color: var(--primary-color, #007bff);
        box-shadow: 0 0 0 0.2rem var(--primary-color-focus, rgba(0,123,255,.25));
    }


    .message-input-area button {
        padding: 0; /* Reset padding */
        width: 40px; /* Fixed width for icon button */
        height: 40px; /* Fixed height for icon button */
        background-color: var(--primary-color, #007bff);
        color: white;
        border: none;
        border-radius: 50%; /* Circular button */
        cursor: pointer;
        transition: background-color 0.2s ease, transform 0.1s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0; /* Prevent shrinking */
    }

    .message-input-area button svg {
        width: 20px;
        height: 20px;
    }

    .message-input-area button:hover:not(:disabled) {
        background-color: var(--primary-dark-color, #0056b3);
        transform: scale(1.05);
    }

    .message-input-area button:active:not(:disabled) {
        transform: scale(0.95);
    }

    .message-input-area button:disabled {
        background-color: var(--button-disabled-bg, #adb5bd);
        cursor: not-allowed;
        opacity: 0.7;
    }

    /* Consistent Status Messages */
    .loading-message, .error-message, .no-messages-prompt {
        text-align: center;
        padding: 2rem 1rem;
        font-size: 1rem;
        margin: 1rem auto;
        border-radius: 6px;
        max-width: 90%;
    }
    .loading-message { color: var(--text-color-medium, #555); }
    .error-message {
        color: var(--error-color, #b22222);
        background-color: var(--error-bg-color, #f8d7da);
        border: 1px solid var(--error-border-color, #f5c6cb);
    }
    .no-messages-prompt {
        color: var(--text-color-subtle, #6c757d);
        background-color: var(--background-color-soft, #f9f9f9);
        border: 1px dashed var(--border-color-soft, #ddd);
    }

    /*
    Consider global CSS variables for colors:
    :root {
      --primary-color: #007bff;
      --primary-dark-color: #0056b3;
      --primary-color-focus: rgba(0,123,255,.25);
      --sent-bubble-bg: #007bff;
      --sent-bubble-text: white;
      --sent-time-color: rgba(255, 255, 255, 0.8);
      --received-bubble-bg: #e9ecef;
      --received-bubble-text: #212529;
      --received-time-color: #6c757d;
      --avatar-bg-color: #6f42c1; // Example for general avatar
      --avatar-text-color: white;
      --avatar-received-bg-color: #6c757d;
      --avatar-received-text-color: white;
      --sender-name-color: #495057;
      --chat-bg-color: #f4f6f8; // A very light grey for the chat area background
      --input-area-bg: #ffffff;
      --input-bg: #ffffff;
      --border-color-light: #dee2e6;
      --border-color-input: #ced4da;
      --border-color-soft: #e9ecef;
      --text-color-medium: #555;
      --text-color-secondary: #555;
      --text-color-subtle: #6c757d;
      --error-color: #b22222;
      --error-bg-color: #f8d7da;
      --error-border-color: #f5c6cb;
      --background-color-soft: #f9f9f9;
      --background-color-subtle: #f8f9fa;
      --background-color-subtle-hover: #e9ecef;
      --text-color-success: #28a745;
      --background-color-price: #e6ffed;
      --button-disabled-bg: #adb5bd;
    }
    */
</style>