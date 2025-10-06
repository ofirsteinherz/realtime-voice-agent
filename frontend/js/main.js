/**
 * Main.js - Application Entry Point
 * Initializes and coordinates all modules, manages global state
 */

// ============================================================================
// GLOBAL STATE
// ============================================================================

const AppState = {
    session: {
        id: null,
        isActive: false,
        language: 'he' // Default to Hebrew
    },
    connection: {
        isConnected: false,
        isMuted: false
    },
    ui: {
        isToolCallsHidden: false
    },
    buffers: {
        transcripts: {},
        functionArgs: {},
        functionItems: {}
    },
    conversation: {
        customerId: null,
        messages: []
    }
};

// ============================================================================
// MODULE INSTANCES
// ============================================================================

let rtcManager = null;
let uiManager = null;
let eventHandler = null;
let services = null;

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Initialize app on page load
 */
window.addEventListener('DOMContentLoaded', () => {
    // Initialize character (defined in character.js)
    initCharacter();

    // Initialize modules
    uiManager = new UIManager();
    services = new Services();
    eventHandler = new EventHandler(uiManager, services, AppState);

    // Set initial UI state
    uiManager.updateStatus('Offline', 'disconnected');
    uiManager.updateLanguageButton(AppState.session.language);

    // Setup text input event listeners
    setupTextInputListeners();

    console.log('App initialized');
});

/**
 * Setup text input event listeners
 */
function setupTextInputListeners() {
    const textInput = document.getElementById('textInput');

    // Allow sending with Enter (but Shift+Enter for new lines)
    textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey && !textInput.disabled) {
            e.preventDefault();
            sendTextMessage();
        }
    });

    // Auto-resize textarea
    textInput.addEventListener('input', () => {
        textInput.style.height = 'auto';
        textInput.style.height = Math.min(textInput.scrollHeight, 150) + 'px';
    });
}

// ============================================================================
// CONNECTION CONTROL
// ============================================================================

/**
 * Start voice chat session
 */
async function start() {
    try {
        uiManager.updateStatus('Initializing...', 'connected');
        uiManager.addDebug('Creating peer connection...');

        // Create RTC manager
        rtcManager = new RTCManager();

        // Set rtcManager reference in event handler
        eventHandler.setRTCManager(rtcManager);

        // Initialize connection with event handler
        await rtcManager.initialize(
            AppState.session.language,
            (event) => {
                eventHandler.handleEvent(event);
            }
        );

        // Wait for data channel to be ready, then configure tools
        const waitForDataChannel = setInterval(async () => {
            if (rtcManager.isReady()) {
                clearInterval(waitForDataChannel);
                
                try {
                    // Fetch and configure tools
                    const toolsData = await services.fetchTools();
                    
                    const sessionUpdateEvent = {
                        type: 'session.update',
                        session: {
                            type: 'realtime',
                            tools: toolsData.tools,
                            tool_choice: 'auto'
                        }
                    };
                    
                    rtcManager.send(sessionUpdateEvent);
                    uiManager.addDebug('Sent session.update with tools');
                    console.log('Tools configured:', toolsData.tools);
                } catch (error) {
                    console.error('Error configuring tools:', error);
                    uiManager.addDebug('Warning: Could not configure tools');
                }
                
                // Update UI state
                uiManager.updateStatus('Online', 'connected');
                uiManager.showConnectedState();
                AppState.session.isActive = true;
                AppState.connection.isConnected = true;
            }
        }, 100);

    } catch (error) {
        console.error('Error starting:', error);
        alert('Error: ' + error.message);
        stop();
    }
}

/**
 * Stop voice chat session
 */
function stop() {
    uiManager.addDebug('Stopping...');

    // Cleanup RTC manager
    if (rtcManager) {
        rtcManager.cleanup();
        rtcManager = null;
    }

    // Update UI state
    uiManager.showDisconnectedState();
    uiManager.updateStatus('Offline', 'disconnected');
    uiManager.addDebug('Stopped');

    // Reset state
    AppState.session.isActive = false;
    AppState.session.id = null;
    AppState.connection.isConnected = false;
    AppState.connection.isMuted = false;
    AppState.conversation.customerId = null;
    AppState.conversation.messages = [];
    AppState.buffers.transcripts = {};
    AppState.buffers.functionArgs = {};
    AppState.buffers.functionItems = {};

    // Reset mute button state
    uiManager.updateMuteButton(false);
}

/**
 * Handle page unload - cleanup
 */
window.addEventListener('beforeunload', () => {
    if (rtcManager) {
        stop();
    }
});

// ============================================================================
// CONTROL FUNCTIONS
// ============================================================================

/**
 * Toggle microphone mute
 */
function toggleMute() {
    if (!rtcManager) {
        return;
    }

    const isMuted = rtcManager.toggleMute();
    AppState.connection.isMuted = isMuted;
    uiManager.updateMuteButton(isMuted);

    if (isMuted) {
        uiManager.addDebug('Microphone muted');
    } else {
        uiManager.addDebug('Microphone unmuted');
    }
}

/**
 * Toggle language between English and Hebrew
 */
function toggleLanguage() {
    if (AppState.session.isActive) {
        return; // Can't change language during active session
    }

    // Toggle language
    if (AppState.session.language === 'en') {
        AppState.session.language = 'he';
        uiManager.addDebug('Language switched to Hebrew');
    } else {
        AppState.session.language = 'en';
        uiManager.addDebug('Language switched to English');
    }

    uiManager.updateLanguageButton(AppState.session.language);
}

/**
 * Toggle tool calls visibility
 */
function toggleToolCalls() {
    AppState.ui.isToolCallsHidden = uiManager.toggleToolCalls();
}

/**
 * Download conversation logs
 */
function downloadLogs() {
    if (window.conversationLogger) {
        window.conversationLogger.downloadLogs();
        uiManager.addDebug('Logs downloaded');
    } else {
        alert('Logger not available');
    }
}

// ============================================================================
// MESSAGE HANDLING
// ============================================================================

/**
 * Send text message to AI
 */
async function sendTextMessage() {
    const text = uiManager.getInputText();
    
    if (!text || !rtcManager || !rtcManager.isReady()) {
        return;
    }

    // Store timestamp when message is sent
    const messageTimestamp = new Date().toISOString();

    // Create conversation.item.create event
    const itemCreateEvent = {
        type: 'conversation.item.create',
        item: {
            type: 'message',
            role: 'user',
            content: [
                {
                    type: 'input_text',
                    text: text
                }
            ]
        }
    };

    // Send the event
    rtcManager.send(itemCreateEvent);
    uiManager.addDebug(`Sent text message: ${text}`);

    // Create message UI element with timestamp (will be linked when item_id arrives)
    const messageElement = uiManager.createPendingTextMessage(text, messageTimestamp);

    // Moderate text asynchronously (non-blocking)
    services.moderateText(text, AppState.session.id).then(moderationResult => {
        if (moderationResult && messageElement.parentElement) {
            uiManager.addSecurityIndicator(messageElement, moderationResult);
        }
    }).catch(err => {
        console.error('Error moderating text:', err);
    });

    // Trigger AI response
    const responseCreateEvent = {
        type: 'response.create'
    };
    rtcManager.send(responseCreateEvent);
    uiManager.addDebug('Triggered response.create');

    // Clear input
    uiManager.clearInput();
}