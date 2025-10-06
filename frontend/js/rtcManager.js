/**
 * RTCManager - WebRTC Connection Management
 * Handles peer connections, data channels, audio tracks, and SDP negotiation
 */
class RTCManager {
    constructor() {
        this.peerConnection = null;
        this.dataChannel = null;
        this.audioElement = null;
        this.localAudioTrack = null;
        
        // Character animation
        this.characterAudioContext = null;
        this.characterAnalyser = null;
        this.characterDataArray = null;
        
        // Event handler callback
        this.onMessageCallback = null;
    }

    /**
     * Initialize WebRTC connection
     * @param {string} language - Selected language (en/he)
     * @param {Function} onMessage - Callback for data channel messages
     */
    async initialize(language, onMessage) {
        this.onMessageCallback = onMessage;
        
        try {
            // Check if mediaDevices is available
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error(
                    'Microphone access requires HTTPS or localhost.\n\n' +
                    'Please access this page via:\n' +
                    '• http://localhost:8000\n' +
                    '• http://127.0.0.1:8000\n' +
                    '• https://your-domain.com (in production)'
                );
            }

            // Create peer connection
            this.peerConnection = new RTCPeerConnection();

            // Setup audio playback
            await this.setupAudioPlayback();

            // Setup microphone
            await this.setupMicrophone();

            // Setup data channel
            this.setupDataChannel();

            // Negotiate SDP
            await this.negotiateSDP(language);

            return true;
        } catch (error) {
            console.error('Error initializing RTC:', error);
            throw error;
        }
    }

    /**
     * Setup audio playback from remote stream
     */
    async setupAudioPlayback() {
        // Create audio element for remote audio
        this.audioElement = document.createElement('audio');
        this.audioElement.autoplay = true;

        // Handle remote audio track
        this.peerConnection.ontrack = (e) => {
            console.log('Received remote audio track');
            this.audioElement.srcObject = e.streams[0];

            // Setup audio analysis for AI voice (character lip-sync)
            this.characterAudioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.characterAnalyser = this.characterAudioContext.createAnalyser();
            this.characterAnalyser.fftSize = 512;
            const aiAudioSource = this.characterAudioContext.createMediaStreamSource(e.streams[0]);
            aiAudioSource.connect(this.characterAnalyser);
            this.characterDataArray = new Uint8Array(this.characterAnalyser.frequencyBinCount);

            console.log('AI audio analysis setup complete');
        };

        // Track audio playback state for character animation
        this.audioElement.onplay = () => {
            console.log('▶️ AI AUDIO PLAYING - Starting character animation');
            setCharacterListening(true, this.characterAnalyser, this.characterDataArray);
        };

        this.audioElement.onended = () => {
            console.log('⏹️ AI AUDIO ENDED - Stopping character animation');
            setCharacterListening(false, null, null);
        };

        this.audioElement.onpause = () => {
            console.log('⏸️ AI AUDIO PAUSED - Stopping character animation');
            setCharacterListening(false, null, null);
        };
    }

    /**
     * Setup microphone audio input
     */
    async setupMicrophone() {
        console.log('Requesting microphone access...');
        
        const mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                sampleRate: 24000,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });

        console.log('Microphone access granted');
        this.localAudioTrack = mediaStream.getTracks()[0];
        this.peerConnection.addTrack(this.localAudioTrack);
    }

    /**
     * Setup data channel for events
     */
    setupDataChannel() {
        this.dataChannel = this.peerConnection.createDataChannel('oai-events');

        this.dataChannel.onopen = () => {
            console.log('Data channel opened');
        };

        this.dataChannel.onclose = () => {
            console.log('Data channel closed');
        };

        this.dataChannel.onerror = (error) => {
            console.error('Data channel error:', error);
        };

        this.dataChannel.onmessage = (e) => {
            if (this.onMessageCallback) {
                const event = JSON.parse(e.data);
                this.onMessageCallback(event);
            }
        };
    }

    /**
     * Negotiate SDP with backend
     * @param {string} language - Selected language
     */
    async negotiateSDP(language) {
        console.log('Creating offer...');
        const offer = await this.peerConnection.createOffer();
        await this.peerConnection.setLocalDescription(offer);

        console.log('Sending SDP to server...');
        const sdpResponse = await fetch(`/session?language=${language}`, {
            method: 'POST',
            body: offer.sdp,
            headers: {
                'Content-Type': 'application/sdp',
            },
        });

        if (!sdpResponse.ok) {
            const errorText = await sdpResponse.text();
            throw new Error(`Session creation failed: ${errorText}`);
        }

        const answerSdp = await sdpResponse.text();
        console.log('Received SDP answer from server');

        const answer = {
            type: 'answer',
            sdp: answerSdp,
        };
        await this.peerConnection.setRemoteDescription(answer);

        console.log('WebRTC connection established');
    }

    /**
     * Send event through data channel
     * @param {Object} event - Event object to send
     */
    send(event) {
        if (this.dataChannel && this.dataChannel.readyState === 'open') {
            this.dataChannel.send(JSON.stringify(event));
            return true;
        }
        console.warn('Data channel not ready');
        return false;
    }

    /**
     * Toggle microphone mute state
     * @returns {boolean} New mute state
     */
    toggleMute() {
        if (!this.localAudioTrack) {
            return false;
        }

        this.localAudioTrack.enabled = !this.localAudioTrack.enabled;
        return !this.localAudioTrack.enabled; // Return true if muted
    }

    /**
     * Check if data channel is ready
     * @returns {boolean}
     */
    isReady() {
        return this.dataChannel && this.dataChannel.readyState === 'open';
    }

    /**
     * Cleanup all resources
     */
    cleanup() {
        console.log('Cleaning up RTC resources...');

        // Stop character animation
        setCharacterListening(false, null, null);

        // Close audio context
        if (this.characterAudioContext) {
            this.characterAudioContext.close();
            this.characterAudioContext = null;
        }

        // Close data channel
        if (this.dataChannel) {
            this.dataChannel.close();
            this.dataChannel = null;
        }

        // Stop local audio track
        if (this.localAudioTrack) {
            this.localAudioTrack.stop();
            this.localAudioTrack = null;
        }

        // Close peer connection
        if (this.peerConnection) {
            this.peerConnection.close();
            this.peerConnection = null;
        }

        // Clean up audio element
        if (this.audioElement) {
            this.audioElement.srcObject = null;
            this.audioElement = null;
        }

        console.log('RTC cleanup complete');
    }
}