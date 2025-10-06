/**
 * UIManager - User Interface Management
 * Handles all UI updates, transcript display, tool calls, security indicators, and status
 */
class UIManager {
    constructor() {
        // DOM elements
        this.elements = {
            status: document.getElementById('status'),
            playBtn: document.getElementById('playBtn'),
            stopBtnImg: document.getElementById('stopBtnImg'),
            transcript: document.getElementById('transcript'),
            debug: document.getElementById('debug'),
            textInput: document.getElementById('textInput'),
            sendBtn: document.getElementById('sendBtn'),
            muteBtn: document.getElementById('muteBtn'),
            toggleToolsBtn: document.getElementById('toggleToolsBtn'),
            langBtn: document.getElementById('langBtn')
        };

        // UI state
        this.conversationItems = {}; // Maps item_id to {element, previous_item_id, role}
        this.pendingTextMessageElement = null; // Temporary storage for text messages
        this.isToolCallsHidden = false;
    }

    /**
     * Update status badge
     * @param {string} status - Status text
     * @param {string} className - CSS class (disconnected/connected/listening/speaking)
     */
    updateStatus(status, className) {
        this.elements.status.textContent = status;
        this.elements.status.className = `status-badge ${className}`;
    }

    /**
     * Add debug message
     * @param {string} message - Debug message
     */
    addDebug(message) {
        const timestamp = new Date().toLocaleTimeString();
        this.elements.debug.textContent = `[${timestamp}] ${message}`;
        console.log(message);
    }

    /**
     * Show connection controls (stop button, enable inputs)
     */
    showConnectedState() {
        this.elements.playBtn.style.display = 'none';
        this.elements.stopBtnImg.style.display = 'block';
        this.elements.textInput.disabled = false;
        this.elements.sendBtn.disabled = false;
        this.elements.muteBtn.disabled = false;
        this.elements.toggleToolsBtn.disabled = false;
        this.elements.langBtn.disabled = true; // Disable language during session
    }

    /**
     * Show disconnected controls (play button, disable inputs)
     */
    showDisconnectedState() {
        this.elements.playBtn.style.display = 'block';
        this.elements.stopBtnImg.style.display = 'none';
        this.elements.textInput.disabled = true;
        this.elements.sendBtn.disabled = true;
        this.elements.muteBtn.disabled = true;
        this.elements.toggleToolsBtn.disabled = true;
        this.elements.langBtn.disabled = false; // Re-enable language selection
    }

    /**
     * Update mute button state
     * @param {boolean} isMuted - Whether microphone is muted
     */
    updateMuteButton(isMuted) {
        if (isMuted) {
            this.elements.muteBtn.textContent = '🔇 Unmute';
            this.elements.muteBtn.classList.add('muted');
        } else {
            this.elements.muteBtn.textContent = '🎤 Mute';
            this.elements.muteBtn.classList.remove('muted');
        }
    }

    /**
     * Update language button
     * @param {string} language - Current language (en/he)
     */
    updateLanguageButton(language) {
        if (language === 'he') {
            this.elements.langBtn.textContent = '🇮🇱 HE';
        } else {
            this.elements.langBtn.textContent = '🇺🇸 EN';
        }
    }

    /**
     * Toggle tool calls visibility
     * @returns {boolean} New hidden state
     */
    toggleToolCalls() {
        this.isToolCallsHidden = !this.isToolCallsHidden;

        // Get all tool call elements
        const toolCallElements = document.querySelectorAll('.message.tool-call');

        // Toggle visibility
        toolCallElements.forEach(element => {
            element.style.display = this.isToolCallsHidden ? 'none' : 'flex';
        });

        // Update button
        if (this.isToolCallsHidden) {
            this.elements.toggleToolsBtn.textContent = '🔧 Show Tools';
            this.elements.toggleToolsBtn.classList.add('tools-hidden');
            this.addDebug('Tool calls hidden');
        } else {
            this.elements.toggleToolsBtn.textContent = '🔧 Hide Tools';
            this.elements.toggleToolsBtn.classList.remove('tools-hidden');
            this.addDebug('Tool calls visible');
        }

        return this.isToolCallsHidden;
    }

    /**
     * Create and store a pending text message element
     * @param {string} text - Message text
     * @returns {HTMLElement} Created message element
     */
    createPendingTextMessage(text, timestamp = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user';
        
        // Store timestamp for ordering
        if (timestamp) {
            messageDiv.dataset.timestamp = timestamp;
        }

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';
        messageBubble.textContent = text;

        messageContent.appendChild(messageBubble);
        messageDiv.appendChild(messageContent);

        this.pendingTextMessageElement = messageDiv;
        return messageDiv;
    }

    /**
     * Link pending text message to item_id
     * @param {string} itemId - Conversation item ID
     * @param {string} previousItemId - Previous item ID for ordering
     */
    linkPendingTextMessage(itemId, previousItemId) {
        if (this.pendingTextMessageElement) {
            this.pendingTextMessageElement.id = 'transcript-' + itemId;
            this.insertMessageInOrder(
                this.pendingTextMessageElement,
                itemId,
                previousItemId,
                'user'
            );
            this.pendingTextMessageElement = null;
        }
    }

    /**
     * Update or create transcript message
     * @param {string} itemId - Item ID
     * @param {string} text - Message text
     * @param {string} role - Message role (user/assistant)
     */
    updateTranscript(itemId, text, role = 'assistant', timestamp = null) {
        let element = document.getElementById('transcript-' + itemId);

        if (!element) {
            // Create new element
            element = document.createElement('div');
            element.id = 'transcript-' + itemId;
            element.className = `message ${role}`;
            
            // Store timestamp in data attribute for ordering
            if (timestamp) {
                element.dataset.timestamp = timestamp;
            }

            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';

            const messageBubble = document.createElement('div');
            messageBubble.className = 'message-bubble';

            messageContent.appendChild(messageBubble);
            element.appendChild(messageContent);

            // Get ordering info
            const itemInfo = this.conversationItems[itemId];
            const previousItemId = itemInfo ? itemInfo.previous_item_id : null;

            // Insert in proper order based on timestamp
            this.insertMessageInOrder(element, itemId, previousItemId, role);
        }

        // Update text content
        const messageBubble = element.querySelector('.message-bubble');
        if (messageBubble) {
            messageBubble.textContent = text;
        }

        this.scrollToBottom();
    }

    /**
     * Insert message in correct order based on timestamp
     * @param {HTMLElement} element - Message element
     * @param {string} itemId - Item ID
     * @param {string} previousItemId - Previous item ID (for tracking only)
     * @param {string} role - Message role
     */
    insertMessageInOrder(element, itemId, previousItemId, role) {
        // Store in tracking map
        this.conversationItems[itemId] = {
            element: element,
            previous_item_id: previousItemId,
            role: role
        };

        // Get timestamp from element if available (stored in data attribute)
        const elementTimestamp = element.dataset.timestamp;
        
        if (!elementTimestamp) {
            // No timestamp, append at end (fallback)
            this.elements.transcript.appendChild(element);
            this.scrollToBottom();
            return;
        }

        // Find correct position based on timestamp
        const allMessages = Array.from(this.elements.transcript.children);
        let insertBefore = null;

        for (const msg of allMessages) {
            const msgTimestamp = msg.dataset.timestamp;
            if (msgTimestamp && elementTimestamp < msgTimestamp) {
                insertBefore = msg;
                break;
            }
        }

        if (insertBefore) {
            this.elements.transcript.insertBefore(element, insertBefore);
        } else {
            this.elements.transcript.appendChild(element);
        }

        this.scrollToBottom();
    }

    /**
     * Store conversation item metadata
     * @param {string} itemId - Item ID
     * @param {string} previousItemId - Previous item ID
     * @param {string} role - Message role
     */
    storeConversationItem(itemId, previousItemId, role) {
        this.conversationItems[itemId] = {
            element: null, // Will be created on first delta
            previous_item_id: previousItemId,
            role: role
        };
    }

    /**
     * Create tool call UI element
     * @param {string} callId - Function call ID
     * @param {string} functionName - Function name
     * @param {Object} args - Function arguments
     * @returns {HTMLElement} Tool call element
     */
    createToolCallElement(callId, functionName, args) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message tool-call';
        messageDiv.id = 'tool-call-' + callId;

        // Apply current visibility state
        if (this.isToolCallsHidden) {
            messageDiv.style.display = 'none';
        }

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';

        // Calling section
        const callingSection = document.createElement('div');
        callingSection.className = 'tool-call-section';

        const callingHeader = document.createElement('div');
        callingHeader.className = 'tool-call-header';
        callingHeader.innerHTML = `<span class="icon">🔧</span><span>Calling ${functionName}</span>`;

        const callingCode = document.createElement('pre');
        callingCode.className = 'tool-call-code';
        callingCode.textContent = `${functionName}(${this.formatJSON(args)})`;

        callingSection.appendChild(callingHeader);
        callingSection.appendChild(callingCode);

        // Result section (will be populated later)
        const resultSection = document.createElement('div');
        resultSection.className = 'tool-call-section tool-call-result';
        resultSection.style.display = 'none';

        const resultHeader = document.createElement('div');
        resultHeader.className = 'tool-call-header';
        resultHeader.innerHTML = '<span class="icon">✅</span><span>Result</span>';

        const resultCode = document.createElement('pre');
        resultCode.className = 'tool-call-code';

        resultSection.appendChild(resultHeader);
        resultSection.appendChild(resultCode);

        messageBubble.appendChild(callingSection);
        messageBubble.appendChild(resultSection);
        messageContent.appendChild(messageBubble);
        messageDiv.appendChild(messageContent);

        this.elements.transcript.appendChild(messageDiv);
        this.scrollToBottom();

        return messageDiv;
    }

    /**
     * Update tool call result
     * @param {string} callId - Function call ID
     * @param {string} result - Execution result
     */
    updateToolCallResult(callId, result) {
        const toolCallElement = document.getElementById('tool-call-' + callId);
        if (!toolCallElement) {
            console.error('Tool call element not found:', callId);
            return;
        }

        const resultSection = toolCallElement.querySelector('.tool-call-result');
        const resultCode = resultSection.querySelector('.tool-call-code');

        // Try to parse result as JSON for better formatting
        let formattedResult;
        try {
            const parsed = JSON.parse(result);
            formattedResult = this.formatJSON(parsed);
        } catch (e) {
            // Not JSON, use as-is
            formattedResult = result;
        }

        resultCode.textContent = formattedResult;
        resultSection.style.display = 'block';

        this.scrollToBottom();
    }

    /**
     * Add security indicator to message (delegates to SecurityUI)
     * @param {HTMLElement} messageElement - Message element
     * @param {Object} moderationResult - Moderation result
     */
    addSecurityIndicator(messageElement, moderationResult) {
        SecurityUI.addIndicator(messageElement, moderationResult);
    }

    /**
     * Format JSON for display
     * @param {Object} obj - Object to format
     * @param {number} indent - Indentation spaces
     * @returns {string} Formatted JSON
     */
    formatJSON(obj, indent = 2) {
        return JSON.stringify(obj, null, indent);
    }

    /**
     * Scroll transcript to bottom
     */
    scrollToBottom() {
        this.elements.transcript.scrollTop = this.elements.transcript.scrollHeight;
    }

    /**
     * Clear input field
     */
    clearInput() {
        this.elements.textInput.value = '';
    }

    /**
     * Get input text
     * @returns {string} Trimmed input text
     */
    getInputText() {
        return this.elements.textInput.value.trim();
    }
}