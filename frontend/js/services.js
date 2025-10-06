/**
 * Services - Backend API Communication
 * Handles all backend API calls for tools, moderation, and conversation persistence
 */
class Services {
    /**
     * Fetch available tools from backend
     * @returns {Promise<Object>} Tools configuration
     */
    async fetchTools() {
        try {
            const response = await fetch('/tools');
            const data = await response.json();
            console.log('Tools fetched:', data.tools);
            return data;
        } catch (error) {
            console.error('Error fetching tools:', error);
            throw error;
        }
    }

    /**
     * Execute a tool call on the backend
     * @param {string} name - Tool name
     * @param {Object} args - Tool arguments
     * @param {string} sessionId - Current session ID
     * @returns {Promise<Object>} Execution result
     */
    async executeToolCall(name, args, sessionId) {
        try {
            const response = await fetch('/execute-tool', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    arguments: args,
                    session_id: sessionId
                })
            });

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || 'Tool execution failed');
            }

            console.log('Tool execution result:', result.result);
            return result;
        } catch (error) {
            console.error('Error executing tool:', error);
            throw error;
        }
    }

    /**
     * Moderate text content for security issues
     * @param {string} text - Text to moderate
     * @param {string} sessionId - Session ID for logging moderation attempts
     * @returns {Promise<Object|null>} Moderation result or null on error
     */
    async moderateText(text, sessionId) {
        try {
            const response = await fetch('/moderate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    session_id: sessionId
                })
            });

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error moderating text:', error);
            return null;
        }
    }

    /**
     * Save conversation to backend
     * @param {string} sessionId - Session ID
     * @param {string|null} customerId - Customer ID (if detected)
     * @param {Array} messages - Conversation messages
     * @returns {Promise<Object>} Save result
     */
    async saveConversation(sessionId, customerId, messages) {
        if (!sessionId) {
            console.warn('Cannot save conversation: no session_id');
            return { success: false, error: 'No session ID' };
        }

        try {
            const response = await fetch('/save-conversation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    customer_id: customerId,
                    messages: messages
                })
            });

            const result = await response.json();

            if (result.success) {
                console.log(`💾 Conversation saved: ${result.message_count} messages, customer: ${result.customer_id}`);
            } else {
                console.error('Failed to save conversation:', result.error);
            }

            return result;
        } catch (error) {
            console.error('Error saving conversation:', error);
            return { success: false, error: error.message };
        }
    }
}