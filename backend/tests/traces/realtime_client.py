"""
WebRTC client for testing the Realtime agent
Note: OpenAI Realtime API requires audio track in offer, even for text-only usage
"""
import asyncio
import json
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaStreamTrack
from av import AudioFrame
import httpx
import numpy as np


class SilentAudioTrack(MediaStreamTrack):
    """
    Silent audio track required by OpenAI Realtime API
    Generates minimal silent audio to satisfy API requirements
    """
    kind = "audio"
    
    def __init__(self):
        super().__init__()
        self.counter = 0
    
    async def recv(self):
        """Generate silent audio frame"""
        self.counter += 1
        
        # 20ms of silence at 24kHz (matches frontend config)
        samples = 480  # 24000 Hz * 0.02 seconds
        pts = self.counter * samples
        
        # Create silent audio frame
        frame = AudioFrame(format='s16', layout='mono', samples=samples)
        for p in frame.planes:
            p.update(bytes(samples * 2))  # 2 bytes per sample for s16
        
        frame.pts = pts
        frame.sample_rate = 24000
        frame.time_base = 1 / 24000
        
        # Sleep to simulate realtime
        await asyncio.sleep(0.02)
        
        return frame


class RealtimeClient:
    """WebRTC client for text-only testing"""
    
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
        self.pc = None
        self.data_channel = None
        self.events = []
        self.current_response = ""
        self.response_ready = asyncio.Event()
        self.tools_called = []
        self.channel_open = asyncio.Event()
        self.function_call_items = {}  # Track function call items
        self.pending_tool_calls = set()  # Track pending tool executions
        self.tool_execution_done = asyncio.Event()
        self.tools_in_current_response = False  # Track if current response has tools
        
    async def connect(self):
        """Connect to the agent"""
        self.pc = RTCPeerConnection()
        self.data_channel = self.pc.createDataChannel('oai-events')
        
        @self.data_channel.on('message')
        def on_message(message):
            event = json.loads(message)
            self.events.append(event)
            self._handle_event(event)
        
        @self.data_channel.on('open')
        async def on_open():
            await self._configure_tools()
            self.channel_open.set()
        
        # Add silent audio track (required by Realtime API)
        self.pc.addTrack(SilentAudioTrack())
        
        # Create and send offer
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{self.server_url}/session?language=en',  # Use English for tests
                content=self.pc.localDescription.sdp,
                headers={'Content-Type': 'application/sdp'},
                timeout=30.0
            )
            answer_sdp = response.text
            answer = RTCSessionDescription(sdp=answer_sdp, type='answer')
            await self.pc.setRemoteDescription(answer)
        
        # Wait for data channel to be ready
        await asyncio.wait_for(self.channel_open.wait(), timeout=10.0)
    
    async def _configure_tools(self):
        """Send session.update with tools"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{self.server_url}/tools')
            tools_data = response.json()
        
        session_update = {
            'type': 'session.update',
            'session': {
                'type': 'realtime',
                'tools': tools_data['tools'],
                'tool_choice': 'auto'
            }
        }
        self.data_channel.send(json.dumps(session_update))
    
    def _handle_event(self, event):
        """Handle incoming events"""
        event_type = event.get('type')
        
        # Capture text responses from audio transcript
        if event_type == 'response.output_audio_transcript.delta':
            delta = event.get('delta', '')
            if delta:
                self.current_response += delta
        
        elif event_type == 'response.output_audio_transcript.done':
            transcript = event.get('transcript', '')
            if transcript:
                self.current_response = transcript
        
        # Also capture text-only responses
        elif event_type == 'response.output_text.delta':
            delta = event.get('delta', '')
            if delta:
                self.current_response += delta
        
        elif event_type == 'response.output_text.done':
            text = event.get('text', '')
            if text:
                self.current_response = text
        
        # Track function call items
        elif event_type == 'response.output_item.added':
            if event.get('item', {}).get('type') == 'function_call':
                item_id = event.get('item', {}).get('id')
                call_id = event.get('item', {}).get('call_id')
                function_name = event.get('item', {}).get('name')
                self.function_call_items[item_id] = {
                    'name': function_name,
                    'call_id': call_id
                }
                # Mark that current response has tools
                self.tools_in_current_response = True
        
        # Handle tool calls
        elif event_type == 'response.function_call_arguments.done':
            item_id = event.get('item_id')
            call_id = event.get('call_id')
            args = event.get('arguments', '{}')
            
            # Get function info
            function_info = self.function_call_items.get(item_id)
            if function_info:
                function_name = function_info['name']
                self.tools_called.append({
                    'name': function_name,
                    'arguments': json.loads(args),
                    'call_id': call_id
                })
                
                # Track pending tool call
                self.pending_tool_calls.add(call_id)
                
                # Execute tool call asynchronously
                asyncio.create_task(self._handle_tool_call(call_id, function_name, args))
        
        # Response complete
        elif event_type == 'response.done':
            # Don't set response_ready if this response had tools - wait for the follow-up response with actual text
            if self.tools_in_current_response:
                # Tools were executed, don't mark response as ready yet
                # The tool handler will trigger a new response which will contain the actual text
                self.tools_in_current_response = False
            elif not self.pending_tool_calls:
                # No tools in this response and no pending calls - response is ready
                self.response_ready.set()
    
    async def _handle_tool_call(self, call_id: str, function_name: str, arguments_str: str):
        """Execute tool and send result back to agent"""
        try:
            # Parse arguments
            arguments = json.loads(arguments_str)
            
            print(f"  🔧 Calling tool: {function_name}({arguments})")
            
            # Execute tool via backend
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{self.server_url}/execute-tool',
                    json={
                        'name': function_name,
                        'arguments': arguments
                    },
                    timeout=30.0
                )
                result = response.json()
            
            if not result.get('success'):
                print(f"  ❌ Tool execution failed: {result.get('error')}")
                self.pending_tool_calls.discard(call_id)
                return
            
            print(f"  ✅ Tool result: {result['result'][:100]}..." if len(str(result['result'])) > 100 else f"  ✅ Tool result: {result['result']}")
            
            # Send result back to agent
            function_output_event = {
                'type': 'conversation.item.create',
                'item': {
                    'type': 'function_call_output',
                    'call_id': call_id,
                    'output': result['result']
                }
            }
            self.data_channel.send(json.dumps(function_output_event))
            
            # Clear accumulated response before triggering new response
            self.current_response = ""
            
            # Trigger new response
            response_create_event = {'type': 'response.create'}
            self.data_channel.send(json.dumps(response_create_event))
            
            # Remove from pending
            self.pending_tool_calls.discard(call_id)
            
        except Exception as e:
            print(f"  ❌ Error handling tool call: {e}")
            import traceback
            traceback.print_exc()
            self.pending_tool_calls.discard(call_id)
    
    async def send_message(self, text: str):
        """Send text message and wait for response"""
        # Ensure channel is open
        if not self.channel_open.is_set():
            raise RuntimeError("Data channel is not open")
        
        self.response_ready.clear()
        self.current_response = ""
        self.tools_in_current_response = False
        
        # Send message
        item_create = {
            'type': 'conversation.item.create',
            'item': {
                'type': 'message',
                'role': 'user',
                'content': [{'type': 'input_text', 'text': text}]
            }
        }
        self.data_channel.send(json.dumps(item_create))
        
        # Trigger response
        response_create = {'type': 'response.create'}
        self.data_channel.send(json.dumps(response_create))
        
        # Wait for response
        await asyncio.wait_for(self.response_ready.wait(), timeout=30.0)
        
        return self.current_response
    
    async def close(self):
        """Close connection"""
        if self.data_channel:
            self.data_channel.close()
        if self.pc:
            await self.pc.close()