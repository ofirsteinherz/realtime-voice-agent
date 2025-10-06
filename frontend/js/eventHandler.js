/**
 * EventHandler - OpenAI Realtime API Event Processing
 * Handles all incoming events from the OpenAI Realtime API
 */
class EventHandler {
    constructor(uiManager, services, state) {
        this.ui = uiManager;
        this.services = services;
        this.state = state;
        this.rtcManager = null; // Will be set by main.js
        this.lastUserMessageTime = null; // Track when user message was committed
        this.currentResponseStartTime = null; // Track when AI response started
    }

    /**
     * Set RTC manager reference
     * @param {RTCManager} rtcManager - RTC manager instance
     */
    setRTCManager(rtcManager) {
        this.rtcManager = rtcManager;
    }

    /**
     * Main event router - dispatches events to appropriate handlers
     * @param {Object} event - Event from OpenAI Realtime API
     */
    handleEvent(event) {
        // Log all events to console
        console.log(`[${new Date().toLocaleTimeString()}] EVENT: ${event.type}`, event);

        // Add to debug display for non-delta events
        if (!event.type.includes('.delta')) {
            this.ui.addDebug(`Event: ${event.type}`);
        }

        // Route to specific handler
        switch (event.type) {
            // Session events
            case 'session.created':
                return this.handleSessionCreated(event);
            case 'session.updated':
                return this.handleSessionUpdated(event);

            // Response events
            case 'response.created':
                return this.handleResponseCreated(event);
            case 'response.done':
                return this.handleResponseDone(event);

            // Output item events
            case 'response.output_item.added':
                return this.handleOutputItemAdded(event);

            // Text output events
            case 'response.output_text.delta':
                return this.handleOutputTextDelta(event);
            case 'response.output_text.done':
                return this.handleOutputTextDone(event);

            // Audio transcript events
            case 'response.output_audio_transcript.delta':
                return this.handleAudioTranscriptDelta(event);
            case 'response.output_audio_transcript.done':
                return this.handleAudioTranscriptDone(event);

            // Audio events
            case 'response.output_audio.delta':
                return this.handleAudioDelta(event);
            case 'response.output_audio.done':
                return this.handleAudioDone(event);
            case 'response.audio.delta':
                return this.handleResponseAudioDelta(event);
            case 'response.audio.done':
                return this.handleResponseAudioDone(event);

            // Content part events
            case 'response.content_part.added':
                return this.handleContentPartAdded(event);
            case 'response.content_part.done':
                return this.handleContentPartDone(event);

            // Output audio buffer events
            case 'output_audio_buffer.started':
                return this.handleOutputAudioBufferStarted(event);
            case 'output_audio_buffer.done':
                return this.handleOutputAudioBufferDone(event);

            // Legacy audio transcript
            case 'response.audio_transcript.delta':
                return this.handleLegacyAudioTranscriptDelta(event);

            // Function call events
            case 'response.function_call_arguments.delta':
                return this.handleFunctionCallArgsDelta(event);
            case 'response.function_call_arguments.done':
                return this.handleFunctionCallArgsDone(event);

            // Input audio events
            case 'input_audio_buffer.speech_started':
                return this.handleSpeechStarted(event);
            case 'input_audio_buffer.speech_stopped':
                return this.handleSpeechStopped(event);
            case 'input_audio_buffer.committed':
                return this.handleAudioCommitted(event);

            // Conversation item events
            case 'conversation.item.input_audio_transcription.delta':
                return this.handleUserTranscriptDelta(event);
            case 'conversation.item.input_audio_transcription.completed':
            case 'conversation.item.input_audio_transcription.done':
                return this.handleUserTranscriptDone(event);
            case 'conversation.item.added':
                return this.handleConversationItemAdded(event);
            case 'conversation.item.created':
                return this.handleConversationItemCreated(event);

            // Error events
            case 'error':
                return this.handleError(event);

            // Unhandled events
            default:
                if (!event.type.includes('.delta')) {
                    console.log('Unhandled event:', event.type, event);
                }
        }
    }

    /**
     * Session created event
     */
    handleSessionCreated(event) {
        this.state.session.id = event.session.id;
        this.state.conversation.customerId = null; // Reset for new session
        this.state.conversation.messages = []; // Reset conversation
        console.log('Session created:', this.state.session.id);
        console.log('Session config:', event.session);
        
        // Log session start
        if (window.conversationLogger) {
            window.conversationLogger.setSessionId(this.state.session.id);
        }
    }

    /**
     * Session updated event
     */
    handleSessionUpdated(event) {
        console.log('Session updated:', event.session);
    }

    /**
     * Response created event
     */
    handleResponseCreated(event) {
        this.ui.updateStatus('Processing...', 'connected');
        this.currentResponseStartTime = new Date().toISOString();
        
        // Log AI response start
        if (window.conversationLogger) {
            window.conversationLogger.log('AI_START', 'AI response started', {
                response_id: event.response?.id,
                timestamp: this.currentResponseStartTime
            });
        }
    }

    /**
     * Response done event
     */
    handleResponseDone(event) {
        this.ui.updateStatus('Listening...', 'listening');
    }

    /**
     * Output item added event - track function call items
     */
    handleOutputItemAdded(event) {
        if (event.item && event.item.type === 'function_call') {
            const itemId = event.item.id;
            const callId = event.item.call_id;
            const functionName = event.item.name;

            console.log('Function call item added:', {
                item_id: itemId,
                call_id: callId,
                name: functionName
            });

            this.state.buffers.functionItems[itemId] = {
                name: functionName,
                call_id: callId
            };
        }
    }

    /**
     * Output text delta - accumulate and display text responses
     */
    handleOutputTextDelta(event) {
        console.log('📝 Text Delta:', {
            content_index: event.content_index,
            delta: event.delta,
            item_id: event.item_id,
            output_index: event.output_index
        });

        const itemId = event.item_id;
        if (itemId) {
            if (!this.state.buffers.transcripts[itemId]) {
                this.state.buffers.transcripts[itemId] = '';
            }
            this.state.buffers.transcripts[itemId] += event.delta;
            this.ui.updateTranscript(itemId, this.state.buffers.transcripts[itemId], 'assistant');
        }
    }

    /**
     * Output text done - save final text
     */
    handleOutputTextDone(event) {
        console.log('✅ Text Done:', {
            content_index: event.content_index,
            text: event.text,
            item_id: event.item_id,
            output_index: event.output_index
        });

        if (event.text) {
            this.saveConversationMessage({
                timestamp: new Date().toISOString(),
                role: 'assistant',
                type: 'text',
                content: event.text,
                item_id: event.item_id
            });
        }
    }

    /**
     * Audio transcript delta - accumulate and display
     */
    handleAudioTranscriptDelta(event) {
        console.log('🎤 Audio Transcript Delta:', {
            content_index: event.content_index,
            delta: event.delta,
            item_id: event.item_id,
            output_index: event.output_index
        });

        const itemId = event.item_id;
        if (itemId) {
            if (!this.state.buffers.transcripts[itemId]) {
                this.state.buffers.transcripts[itemId] = '';
            }
            this.state.buffers.transcripts[itemId] += event.delta;
            // Pass timestamp for UI ordering
            this.ui.updateTranscript(
                itemId,
                this.state.buffers.transcripts[itemId],
                'assistant',
                this.currentResponseStartTime
            );
        }
    }

    /**
     * Audio transcript done - save final transcript
     */
    handleAudioTranscriptDone(event) {
        console.log('✅ Audio Transcript Done:', {
            content_index: event.content_index,
            transcript: event.transcript,
            item_id: event.item_id,
            output_index: event.output_index
        });

        if (event.transcript) {
            const timestamp = this.currentResponseStartTime || new Date().toISOString();
            
            // Log AI transcript completion
            if (window.conversationLogger) {
                window.conversationLogger.log('AI_TRANSCRIPT', 'AI transcript completed', {
                    item_id: event.item_id,
                    timestamp: timestamp,
                    current_time: new Date().toISOString(),
                    delay_ms: new Date() - new Date(timestamp),
                    transcript: event.transcript
                });
            }
            
            this.saveConversationMessage({
                timestamp: timestamp,
                role: 'assistant',
                type: 'audio_transcript',
                content: event.transcript,
                item_id: event.item_id
            });
        }
    }

    /**
     * Audio delta event
     */
    handleAudioDelta(event) {
        console.log('🔊 Audio Delta:', {
            content_index: event.content_index,
            delta_length: event.delta ? event.delta.length : 0,
            item_id: event.item_id,
            output_index: event.output_index
        });
    }

    /**
     * Audio done event
     */
    handleAudioDone(event) {
        console.log('✅ Audio Done:', {
            content_index: event.content_index,
            item_id: event.item_id,
            output_index: event.output_index
        });
    }

    /**
     * Response audio delta - update status
     */
    handleResponseAudioDelta(event) {
        // Audio is handled by WebRTC track, just update status
        if (!this.ui.elements.status.className.includes('speaking')) {
            this.ui.updateStatus('Speaking...', 'speaking');
        }
    }

    /**
     * Response audio done
     */
    handleResponseAudioDone(event) {
        this.ui.updateStatus('Listening...', 'listening');
    }

    /**
     * Content part added event
     */
    handleContentPartAdded(event) {
        console.log('Content part added:', event);
    }

    /**
     * Content part done event
     */
    handleContentPartDone(event) {
        console.log('Content part done:', event);
    }

    /**
     * Output audio buffer started
     */
    handleOutputAudioBufferStarted(event) {
        console.log('Output audio buffer started');
    }

    /**
     * Output audio buffer done
     */
    handleOutputAudioBufferDone(event) {
        console.log('Output audio buffer done');
    }

    /**
     * Legacy audio transcript delta (fallback)
     */
    handleLegacyAudioTranscriptDelta(event) {
        const itemId = event.item_id;
        if (itemId) {
            if (!this.state.buffers.transcripts[itemId]) {
                this.state.buffers.transcripts[itemId] = '';
            }
            this.state.buffers.transcripts[itemId] += event.delta;
            this.ui.updateTranscript(itemId, this.state.buffers.transcripts[itemId]);
        }
    }

    /**
     * Function call arguments delta - accumulate
     */
    handleFunctionCallArgsDelta(event) {
        console.log('🔧 Function Call Args Delta:', {
            call_id: event.call_id,
            delta: event.delta,
            item_id: event.item_id,
            output_index: event.output_index
        });

        const callId = event.call_id;
        if (callId) {
            if (!this.state.buffers.functionArgs[callId]) {
                this.state.buffers.functionArgs[callId] = '';
            }
            this.state.buffers.functionArgs[callId] += event.delta;
        }
    }

    /**
     * Function call arguments done - execute tool
     */
    async handleFunctionCallArgsDone(event) {
        console.log('✅ Function Call Args Done:', {
            call_id: event.call_id,
            arguments: event.arguments,
            item_id: event.item_id,
            output_index: event.output_index
        });

        // Get function info
        const functionInfo = this.state.buffers.functionItems[event.item_id];
        if (functionInfo) {
            let parsedArgs;
            try {
                parsedArgs = JSON.parse(event.arguments);
            } catch (e) {
                console.error('Failed to parse tool arguments:', e);
                parsedArgs = {};
            }

            // Auto-detect customer_id
            if (!this.state.conversation.customerId && parsedArgs.customer_id) {
                this.state.conversation.customerId = parsedArgs.customer_id;
                console.log('Auto-detected customer_id:', this.state.conversation.customerId);
            }

            // Save function call
            const timestamp = this.currentResponseStartTime || new Date().toISOString();
            
            // Log function call
            if (window.conversationLogger) {
                window.conversationLogger.log('FUNCTION_CALL', 'Function call executed', {
                    function_name: functionInfo.name,
                    call_id: event.call_id,
                    item_id: event.item_id,
                    timestamp: timestamp,
                    current_time: new Date().toISOString(),
                    arguments: parsedArgs
                });
            }
            
            this.saveConversationMessage({
                timestamp: timestamp,
                role: 'assistant',
                type: 'function_call',
                function_name: functionInfo.name,
                arguments: parsedArgs,
                call_id: event.call_id,
                item_id: event.item_id
            });

            // Execute tool call
            await this.executeToolCall(event, this.rtcManager);
        }
    }

    /**
     * Execute tool call
     */
    async executeToolCall(event, rtcManager) {
        try {
            const callId = event.call_id;
            const itemId = event.item_id;
            const argumentsStr = event.arguments;

            console.log('Handling tool call:', {
                call_id: callId,
                item_id: itemId,
                arguments: argumentsStr
            });

            // Get function info
            const functionInfo = this.state.buffers.functionItems[itemId];
            if (!functionInfo) {
                console.error('Function call info not found for item:', itemId);
                return;
            }

            const functionName = functionInfo.name;

            // Parse arguments
            let parsedArgs;
            try {
                parsedArgs = JSON.parse(argumentsStr);
            } catch (e) {
                console.error('Failed to parse tool arguments:', e);
                parsedArgs = {};
            }

            // Create tool call UI
            const toolCallElement = this.ui.createToolCallElement(callId, functionName, parsedArgs);

            // Execute tool on backend
            const result = await this.services.executeToolCall(
                functionName,
                parsedArgs,
                this.state.session.id
            );

            // Update UI with result
            this.ui.updateToolCallResult(callId, result.result);

            // Save function result
            const timestamp = this.currentResponseStartTime || new Date().toISOString();
            
            // Log function result
            if (window.conversationLogger) {
                window.conversationLogger.log('FUNCTION_CALL', 'Function result received', {
                    function_name: functionName,
                    call_id: callId,
                    timestamp: timestamp,
                    current_time: new Date().toISOString(),
                    result_preview: JSON.stringify(result.result).substring(0, 100)
                });
            }
            
            this.saveConversationMessage({
                timestamp: timestamp,
                role: 'function',
                type: 'function_result',
                function_name: functionName,
                result: result.result,
                call_id: callId
            });

            // Send result back to OpenAI
            const functionOutputEvent = {
                type: 'conversation.item.create',
                item: {
                    type: 'function_call_output',
                    call_id: callId,
                    output: result.result
                }
            };
            
            rtcManager.send(functionOutputEvent);
            console.log('Sent function output to OpenAI');
            
            // Trigger the AI to respond with the function result
            const responseCreateEvent = {
                type: 'response.create'
            };
            rtcManager.send(responseCreateEvent);
            console.log('Triggered response.create after function call');

        } catch (error) {
            console.error('Error handling tool call:', error);
            this.ui.updateStatus('Error: ' + error.message, 'disconnected');
        }
    }

    /**
     * Speech started event
     */
    handleSpeechStarted(event) {
        console.log('Speech detected!');
        this.ui.updateStatus('Listening...', 'listening');
    }

    /**
     * Speech stopped event
     */
    handleSpeechStopped(event) {
        console.log('Speech stopped - AI should respond now');
        this.ui.updateStatus('Processing...', 'connected');
    }

    /**
     * Audio buffer committed event
     */
    handleAudioCommitted(event) {
        console.log('Audio buffer committed');
        this.lastUserMessageTime = new Date().toISOString();
        
        // Log user message commit
        if (window.conversationLogger) {
            window.conversationLogger.log('USER_COMMITTED', 'User audio committed (message sent)', {
                item_id: event.item_id,
                timestamp: this.lastUserMessageTime,
                previous_item_id: event.previous_item_id
            });
        }
    }

    /**
     * User input transcript delta
     */
    handleUserTranscriptDelta(event) {
        console.log('🎙️ User Input Transcript Delta:', {
            content_index: event.content_index,
            delta: event.delta,
            item_id: event.item_id
        });

        const itemId = event.item_id;
        if (itemId) {
            if (!this.state.buffers.transcripts[itemId]) {
                this.state.buffers.transcripts[itemId] = '';
            }
            this.state.buffers.transcripts[itemId] += event.delta;
            // Pass timestamp for UI ordering
            this.ui.updateTranscript(
                itemId,
                this.state.buffers.transcripts[itemId],
                'user',
                this.lastUserMessageTime
            );
        }
    }

    /**
     * User input transcript done - moderate and save
     */
    async handleUserTranscriptDone(event) {
        console.log('✅ User Input Transcript Done:', {
            content_index: event.content_index,
            transcript: event.transcript,
            item_id: event.item_id
        });

        if (event.transcript) {
            const itemId = event.item_id;

            // Moderate transcript
            const moderationResult = await this.services.moderateText(event.transcript);
            if (moderationResult) {
                const messageElement = document.getElementById('transcript-' + itemId);
                if (messageElement) {
                    this.ui.addSecurityIndicator(messageElement, moderationResult);
                }
            }

            // Save user message
            const timestamp = this.lastUserMessageTime || new Date().toISOString();
            
            // Log user transcript completion
            if (window.conversationLogger) {
                window.conversationLogger.log('USER_TRANSCRIPT', 'User transcript completed', {
                    item_id: event.item_id,
                    timestamp: timestamp,
                    current_time: new Date().toISOString(),
                    delay_ms: new Date() - new Date(timestamp),
                    transcript: event.transcript
                });
            }
            
            this.saveConversationMessage({
                timestamp: timestamp,
                role: 'user',
                type: 'audio_transcript',
                content: event.transcript,
                item_id: event.item_id
            });
        }
    }

    /**
     * Conversation item added event
     */
    handleConversationItemAdded(event) {
        console.log('Conversation item added:', event.item);

        const item = event.item;
        const itemId = item.id;
        const previousItemId = event.previous_item_id;
        const role = item.role;

        // Handle pending text message
        if (role === 'user' && item.type === 'message') {
            this.ui.linkPendingTextMessage(itemId, previousItemId);

            // Save user text message
            if (item.content && item.content.length > 0) {
                const textContent = item.content.find(c => c.type === 'input_text' || c.type === 'text');
                if (textContent && textContent.text) {
                    this.saveConversationMessage({
                        timestamp: new Date().toISOString(),
                        role: 'user',
                        type: 'text',
                        content: textContent.text,
                        item_id: itemId
                    });
                }
            }
            return;
        }

        // Store metadata for other items (will be created on first delta)
        this.ui.storeConversationItem(itemId, previousItemId, role);
    }

    /**
     * Conversation item created event
     */
    handleConversationItemCreated(event) {
        console.log('Conversation item created:', event.item);
    }

    /**
     * Error event
     */
    handleError(event) {
        console.error('Error event:', event.error);
        const errorMessage = event.error?.message || JSON.stringify(event.error);
        this.ui.updateStatus('Error: ' + errorMessage, 'disconnected');
    }

    /**
     * Save conversation message
     */
    saveConversationMessage(message) {
        this.state.conversation.messages.push(message);

        // Sort messages by timestamp before saving to ensure chronological order
        const sortedMessages = [...this.state.conversation.messages].sort((a, b) => {
            return new Date(a.timestamp) - new Date(b.timestamp);
        });

        // Log save operation with detailed ordering info
        if (window.conversationLogger) {
            window.conversationLogger.log('SAVE', `Saving ${sortedMessages.length} messages`, {
                just_added: {
                    role: message.role,
                    type: message.type,
                    timestamp: message.timestamp,
                    content_preview: message.content?.substring(0, 50) || message.function_name || 'N/A'
                },
                message_order: sortedMessages.map((m, idx) => ({
                    index: idx,
                    role: m.role,
                    type: m.type,
                    timestamp: m.timestamp,
                    content_preview: m.content?.substring(0, 30) || m.function_name || 'N/A'
                }))
            });
        }

        // Auto-save to backend with sorted messages
        this.services.saveConversation(
            this.state.session.id,
            this.state.conversation.customerId,
            sortedMessages
        );
    }
}