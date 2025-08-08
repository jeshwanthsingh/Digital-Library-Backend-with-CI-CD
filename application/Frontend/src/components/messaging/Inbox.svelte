<script>
    import { createEventDispatcher } from 'svelte';
    import { push } from 'svelte-spa-router'; // Retain for other potential direct navigation, though not used in goToConversation now

    export let conversations;
    export let currentUser;
    export let conversationsLoading;
    export let conversationsError;

    const dispatch = createEventDispatcher();

    function selectConversation(conversation) {
        dispatch('select', conversation);
    }

    function getOtherParticipant(conversation) {
        if (!currentUser) {
            console.warn("getOtherParticipant: currentUser prop is not available.");
            return null;
        }
        if (!conversation || !conversation.user1 || !conversation.user2) {
            console.warn("getOtherParticipant: conversation object or its users are invalid.", conversation);
            return null;
        }
        if (conversation.user1.user_id === currentUser.user_id) {
            return conversation.user2;
        } else if (conversation.user2.user_id === currentUser.user_id) {
            return conversation.user1;
        }
        console.warn("getOtherParticipant: currentUser is not part of the conversation.", currentUser, conversation);
        return null;
    }

    function formatTime(isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true });
    }
</script>

<svelte:head>
    <title>Inbox - Agora SFSU Marketplace</title>
</svelte:head>

{#if conversationsLoading}
    <p class="loading-message">Loading conversations...</p>
{:else if conversationsError}
    <p class="error-message">Error loading conversations: {conversationsError}</p>
{:else if !conversations || conversations.length === 0}
    <p class="no-conversations-message">No conversations yet. Start a new one by contacting a seller on a listing!</p>
{:else}
    <ul class="conversation-list">
        {#each conversations as conversation (conversation.conversation_id)}
            {@const otherUser = getOtherParticipant(conversation)}
            <li class="conversation-item">
                <div
                    class="conversation-item-content"
                    on:click={() => selectConversation(conversation)}
                    on:keypress={(e) => e.key === 'Enter' && selectConversation(conversation)}
                    role="link"
                    tabindex="0"
                >
                    <div class="conversation-info">
                        <h3>{otherUser ? otherUser.username : 'Unknown User'}</h3>
                        {#if conversation.listing}
                            <p class="listing-title">Regarding: {conversation.listing.title}</p>
                        {/if}
                        {#if conversation.messages && conversation.messages.length > 0}
                            {@const lastMessage = conversation.messages[conversation.messages.length - 1]}
                            <p class="last-message-snippet">
                                {lastMessage.sender_id === currentUser.user_id ? 'You: ' : ''}{lastMessage.content.substring(0, 40)}{lastMessage.content.length > 40 ? '...' : ''}
                            </p>
                        {/if}
                    </div>
                    <div class="last-message-time">
                        {formatTime(conversation.updated_at)}
                    </div>
                </div>
            </li>
        {/each}
    </ul>
{/if}

<style>
    .conversation-list {
        list-style: none;
        padding: 0;
        margin: 0; /* Reset margin as parent container (MessagingWrapper) will handle overall padding */
    }

    .conversation-item {
        background-color: var(--card-bg-color, #fff);
        border: 1px solid var(--border-color-light, #e9ecef);
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        transition: box-shadow 0.2s ease-in-out, transform 0.2s ease-in-out;
        overflow: hidden; /* Ensures content respects border-radius */
    }

    .conversation-item:hover {
        box-shadow: 0 5px 15px rgba(0,0,0,0.07);
        transform: translateY(-3px);
    }
    
    .conversation-item:last-child {
        margin-bottom: 0;
    }

    .conversation-item-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 1.25rem; /* Slightly more padding */
        cursor: pointer;
        transition: background-color 0.2s ease;
    }

    .conversation-item-content:hover,
    .conversation-item-content:focus {
        background-color: var(--hover-bg-color-light, #f8f9fa); /* Lighter hover for content */
        outline: none;
    }
    .conversation-item:focus-within { /* Style parent when content is focused for accessibility */
        box-shadow: 0 0 0 2px var(--primary-color-focus, #007bff40), 0 5px 15px rgba(0,0,0,0.07);
        transform: translateY(-3px);
    }


    .conversation-info {
        flex-grow: 1;
        margin-right: 1rem;
        overflow: hidden;
    }

    .conversation-info h3 {
        margin: 0 0 0.3rem 0;
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-color-strong, #212529);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .listing-title {
        margin: 0 0 0.25rem 0;
        font-size: 0.9rem;
        font-weight: 500;
        color: var(--primary-color, #007bff); /* Use primary color for listing titles */
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .last-message-snippet {
        margin: 0;
        font-size: 0.9rem;
        color: var(--text-color-secondary, #6c757d);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .last-message-time {
        font-size: 0.8rem;
        color: var(--text-color-muted, #868e96);
        flex-shrink: 0;
        white-space: nowrap;
        padding-left: 0.5rem; /* Add some space if snippet is long */
    }

    /* Consistent Loading/Error/Empty Messages */
    .loading-message, .error-message, .no-conversations-message {
        text-align: center;
        padding: 2.5rem 1.5rem;
        font-size: 1.05rem;
        margin: 1rem 0;
        border-radius: 6px;
    }

    .loading-message {
        color: var(--text-color-medium, #555);
    }

    .error-message {
        color: var(--error-color, #b22222); /* Darker red for better readability */
        background-color: var(--error-bg-color, #f8d7da);
        border: 1px solid var(--error-border-color, #f5c6cb);
    }

    .no-conversations-message {
        color: var(--text-color-medium, #555);
        background-color: var(--background-color-soft, #f9f9f9); /* Similar to messaging container bg */
        border: 1px dashed var(--border-color-soft, #ddd);
    }

    /* Define CSS variables in a global scope (e.g., App.svelte or a theme.css) for consistency */
    /* Example variables (these would ideally be global):
    :root {
        --card-bg-color: #fff;
        --border-color-light: #e9ecef;
        --hover-bg-color-light: #f8f9fa;
        --primary-color: #007bff;
        --primary-color-focus: rgba(0, 123, 255, 0.25);
        --text-color-strong: #212529;
        --text-color-secondary: #6c757d;
        --text-color-muted: #868e96;
        --text-color-medium: #555;
        --error-color: #b22222;
        --error-bg-color: #f8d7da;
        --error-border-color: #f5c6cb;
        --background-color-soft: #f9f9f9;
        --border-color-soft: #ddd;
    }
    */
</style>