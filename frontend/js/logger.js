/**
 * Logger - File-based debugging logger
 * Logs message ordering and timing information to help debug ordering issues
 */
class Logger {
    constructor() {
        this.logs = [];
        this.sessionId = null;
    }

    /**
     * Set session ID for logging
     */
    setSessionId(sessionId) {
        this.sessionId = sessionId;
        this.log('SESSION', `Started session: ${sessionId}`);
    }

    /**
     * Log an event
     */
    log(type, message, data = null) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            type,
            message,
            data: data ? JSON.stringify(data, null, 2) : null
        };
        
        this.logs.push(logEntry);
        
        // Also log to console with color coding
        const prefix = `[${timestamp}] [${type}]`;
        console.log(`%c${prefix} ${message}`, this.getColorForType(type), data || '');
    }

    /**
     * Get color for log type
     */
    getColorForType(type) {
        const colors = {
            'SESSION': 'color: blue; font-weight: bold',
            'USER_COMMITTED': 'color: green; font-weight: bold',
            'USER_TRANSCRIPT': 'color: green',
            'AI_START': 'color: purple; font-weight: bold',
            'AI_TRANSCRIPT': 'color: purple',
            'FUNCTION_CALL': 'color: orange',
            'SAVE': 'color: red; font-weight: bold',
            'ERROR': 'color: red; background: yellow'
        };
        return colors[type] || 'color: gray';
    }

    /**
     * Download logs as a file
     */
    downloadLogs() {
        const content = this.logs.map(log => {
            const dataStr = log.data ? `\n${log.data}` : '';
            return `[${log.timestamp}] [${log.type}] ${log.message}${dataStr}`;
        }).join('\n\n');

        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversation-log-${this.sessionId || 'unknown'}-${Date.now()}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * Send logs to backend for saving
     */
    async sendToBackend() {
        try {
            const response = await fetch('/save-logs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    logs: this.logs
                })
            });
            
            if (response.ok) {
                console.log('Logs saved to backend');
            }
        } catch (error) {
            console.error('Failed to save logs to backend:', error);
        }
    }

    /**
     * Clear logs
     */
    clear() {
        this.logs = [];
        console.log('Logs cleared');
    }
}

// Create global logger instance
window.conversationLogger = new Logger();