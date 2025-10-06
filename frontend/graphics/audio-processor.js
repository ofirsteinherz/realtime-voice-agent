class AudioStreamProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        // Match docs example: ~20ms at 24kHz = 480 samples
        this.bufferSize = Math.floor(sampleRate * 0.02) || 480;
        this.buffer = new Float32Array(this.bufferSize);
        this.bufferIndex = 0;
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];
        
        if (input.length > 0) {
            const inputChannel = input[0];
            
            for (let i = 0; i < inputChannel.length; i++) {
                this.buffer[this.bufferIndex++] = inputChannel[i];
                
                // When buffer is full, send it
                if (this.bufferIndex >= this.bufferSize) {
                    // Send the buffer to the main thread
                    this.port.postMessage({
                        audioData: this.buffer.slice()
                    });
                    
                    // Reset buffer
                    this.bufferIndex = 0;
                }
            }
        }
        
        // Keep processor alive
        return true;
    }
}

registerProcessor('audio-stream-processor', AudioStreamProcessor);