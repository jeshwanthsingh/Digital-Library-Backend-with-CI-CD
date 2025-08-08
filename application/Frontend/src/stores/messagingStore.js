import { writable } from 'svelte/store';
import { push } from 'svelte-spa-router'; // Import push for navigation
import { isAuthenticated, user, setAuthenticated, setUser } from './authStore.js'; // Import auth store and setters

// Store for the list of conversations for the current user
export const conversations = writable([]);
export const conversationsLoading = writable(false);
export const conversationsError = writable(null);

// Store for the currently active conversation and its messages
export const activeConversation = writable(null);
export const messages = writable([]);
export const messagesLoading = writable(false);
export const messagesError = writable(null);

// Base API URL
const API_BASE_URL = typeof window !== 'undefined' ? window.location.origin + '/api' : '/api';

// Helper function to handle 401 Unauthorized responses
async function handleUnauthorized(response) {
    if (response.status === 401) {
        console.warn('Authentication failed: Token invalid or expired. Redirecting to login.');
        // Clear authentication state
        setAuthenticated(false);
        setUser(null);
        localStorage.removeItem('access_token');
        // Redirect to login page
        push('/login');
        // Throw an error to stop further processing in the calling function
        throw new Error('Unauthorized: Please log in again.');
    }
    // If not 401, proceed with normal error handling
    const errorData = await response.json();
    const errorMessage = errorData.detail || response.statusText;
    throw new Error(`API Error: ${errorMessage}`);
}


// Function to load conversations for the current user
export async function loadConversations(token) {
    conversationsLoading.set(true);
    conversationsError.set(null);
    try {
        const response = await fetch(`${API_BASE_URL}/messages/conversations`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) {
            await handleUnauthorized(response); // Handle 401 or other errors
        }
        const data = await response.json();
        conversations.set(data);
    } catch (error) {
        console.error('Error loading conversations:', error);
        conversationsError.set(error.message);
    } finally {
        conversationsLoading.set(false);
    }
}

// Function to load messages for a specific conversation
export async function loadMessages(conversationId, token) {
    console.log(`[messagingStore loadMessages - ${conversationId}] Called. Setting messagesLoading to true.`);
    messagesLoading.set(true);
    messagesError.set(null);
    try {
        console.log(`[messagingStore loadMessages - ${conversationId}] Attempting fetch.`);
        const response = await fetch(`${API_BASE_URL}/messages/conversations/${conversationId}/messages`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        console.log(`[messagingStore loadMessages - ${conversationId}] Fetch response status: ${response.status}`);

        if (!response.ok) {
            console.log(`[messagingStore loadMessages - ${conversationId}] Response not OK (${response.status}). Calling handleUnauthorized.`);
            await handleUnauthorized(response); // This will throw if not OK
            // The function might not proceed past here if handleUnauthorized throws and is caught below.
        }
        console.log(`[messagingStore loadMessages - ${conversationId}] Response OK. Attempting response.json().`);
        const data = await response.json();
        console.log(`[messagingStore loadMessages - ${conversationId}] Fetched data, messages count: ${data ? data.length : 'null/undefined'}. Setting messages store.`);
        messages.set(data);
        console.log(`[messagingStore loadMessages - ${conversationId}] messages.set(data) completed.`);
    } catch (error) {
        console.error(`[messagingStore loadMessages - ${conversationId}] Error caught in try block:`, error.message);
        messagesError.set(error.message);
    } finally {
        console.log(`[messagingStore loadMessages - ${conversationId}] Finally block. Setting messagesLoading to false.`);
        messagesLoading.set(false);
    }
}

// Function to find an existing conversation with a user or create a new one
export async function initiateOrOpenConversationWithUser(otherUserId, token) {
    const { get } = await import('svelte/store'); // Dynamically import get
    const authUser = get(user); // authUserStore is named 'user' in this file's imports

    if (!authUser || !authUser.user_id) {
        console.error('Error: Current user not available to initiate conversation.');
        conversationsError.set('Current user not available. Please log in.');
        push('/login'); // Redirect to login if user is not found
        throw new Error('Current user not available.');
    }

    const currentUserId = authUser.user_id;

    if (currentUserId === otherUserId) {
        console.warn('Attempting to start a conversation with oneself.');
        conversationsError.set('Cannot start a conversation with yourself.');
        // Optionally, prevent further action or allow backend to handle
        // For now, let's throw an error to prevent API call
        throw new Error('Cannot start a conversation with yourself.');
    }

    console.log(`[messagingStore initiateOrOpenConversationWithUser] Initiating with otherUserId: ${otherUserId}, currentUserId: ${currentUserId}`);
    try {
        // Call createConversation, which should handle returning existing or new.
        // The backend POST /messages/conversations should ideally be idempotent for (user1_id, user2_id) pair
        // or have specific logic to find_or_create.
        const conversation = await createConversation(currentUserId, otherUserId, null, token);
        
        // After creating/fetching, set it as active and navigate
        if (conversation && conversation.conversation_id) {
            activeConversation.set(conversation); // Set it active
            // The navigation should ideally happen in the component after this returns.
            // But to ensure consistency, we can also push here.
            // push(`/messages/${conversation.conversation_id}`); // Navigation handled by MessagingWrapper
            return conversation;
        } else {
            throw new Error('Failed to initiate or open conversation: No conversation ID returned.');
        }
    } catch (error) {
        console.error('Error in initiateOrOpenConversationWithUser:', error);
        conversationsError.set(error.message || 'Failed to start or open conversation.');
        // The error might have already been handled by createConversation (like 401)
        // Re-throw to allow component to potentially display it.
        throw error;
    }
}

// Function to create a new conversation
export async function createConversation(user1Id, user2Id, listingId = null, token) {
    conversationsLoading.set(true); // Indicate loading while creating
    conversationsError.set(null);
    try {
        const response = await fetch(`${API_BASE_URL}/messages/conversations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ user1_id: user1Id, user2_id: user2Id, listing_id: listingId })
        });
        if (!response.ok) {
            await handleUnauthorized(response); // Handle 401 or other errors
        }
        const newConversation = await response.json();
        // Add the new conversation to the existing list (or update if it was an existing one returned)
        // A more robust approach would check if the conversation already exists in the store
        // For simplicity now, we'll just add it, assuming the backend handles returning existing
        // A better backend might return 200 with existing, 201 with new.
        // Let's assume backend returns the conversation object whether new or existing.
        // We might need to update the store more intelligently later.
        // For now, let's just reload conversations after creating/getting one.
        // This is less efficient but simpler for now.
        // Alternatively, check if the returned conversation ID exists in the store and update or add.

        // Simple approach: Reload all conversations after creating/getting one
        // await loadConversations(token); // This might cause issues if called from within loadConversations

        // Better approach: Check if the conversation is already in the store.
        // If it is, update it (e.g., if a message was sent).
        // If not, add it.
        conversations.update(convs => {
            const existingIndex = convs.findIndex(c => c.conversation_id === newConversation.conversation_id);
            if (existingIndex > -1) {
                // Update existing conversation in the list (e.g., updated_at, last message snippet)
                // This requires the backend to return enough info in the Conversation schema
                // For now, a simple replacement might suffice if backend returns full Conversation
                convs[existingIndex] = newConversation;
                return convs;
            } else {
                // Add new conversation to the list
                return [...convs, newConversation];
            }
        });


        return newConversation; // Return the newly created/retrieved conversation
    } catch (error) {
        console.error('Error creating conversation:', error);
        conversationsError.set(error.message);
        throw error; // Re-throw to allow components to handle
    } finally {
        conversationsLoading.set(false);
    }
}

// Function to send a new message
export async function sendMessage(conversationId, content, token) {
    messagesLoading.set(true); // Indicate loading while sending
    messagesError.set(null);
    try {
        const response = await fetch(`${API_BASE_URL}/messages/conversations/${conversationId}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ content: content })
        });
        if (!response.ok) {
             await handleUnauthorized(response); // Handle 401 or other errors
        }
        const newMessage = await response.json();
        // Add the new message to the active conversation's messages
        messages.update(msgs => [...msgs, newMessage]);

        // Optional: Update the corresponding conversation in the conversations list
        // to show the latest message snippet and updated_at time in the inbox view
        conversations.update(convs => {
            const conversationIndex = convs.findIndex(c => c.conversation_id === conversationId);
            if (conversationIndex > -1) {
                // Assuming the backend returns the updated conversation object or we can construct it
                // For now, let's just update the updated_at time and add the message to the messages array within the conversation object in the list
                // This requires the Conversation schema to include a messages list (which it does)
                const updatedConvo = { ...convs[conversationIndex] };
                updatedConvo.messages = [...(Array.isArray(updatedConvo.messages) ? updatedConvo.messages : []), newMessage]; // Add new message to the conversation object in the list
                updatedConvo.updated_at = newMessage.created_at; // Update updated_at to the new message's timestamp
                convs[conversationIndex] = updatedConvo;
            }
            return convs;
        });


        return newMessage; // Return the newly created message
    } catch (error) {
        console.error(`Error sending message in conversation ${conversationId}:`, error);
        messagesError.set(error.message);
        throw error; // Re-throw to allow components to handle
    } finally {
        messagesLoading.set(false);
    }
}