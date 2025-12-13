import { useResearchStore } from '../stores/useResearchStore';

const WS_URL = 'ws://localhost:8000'; // Proxied via Vite in dev

class WebSocketSync {
    constructor() {
        this.chatWs = null;
        this.canvasWs = null;
        this.reconnectAttempts = 0;
    }

    connect() {
        this.chatWs = new WebSocket(`${WS_URL}/ws/chat`);
        this.canvasWs = new WebSocket(`${WS_URL}/ws/canvas`);

        this.setupChatWs();
        this.setupCanvasWs();
    }

    setupChatWs() {
        this.chatWs.onopen = () => {
            console.log('Chat WS Connected');
            useResearchStore.getState().setConnected(true);
            this.reconnectAttempts = 0;
        };

        this.chatWs.onclose = () => {
            console.log('Chat WS Closed');
            useResearchStore.getState().setConnected(false);
            this.reconnect();
        };
    }

    setupCanvasWs() {
        // Handle canvas/telemetry events
        this.canvasWs.onmessage = (event) => {
            const data = JSON.parse(event.data);
            // Handle incoming events (e.g., remote updates)
            console.log("Canvas Event:", data);
        };
    }

    reconnect() {
        if (this.reconnectAttempts < 5) {
            this.reconnectAttempts++;
            setTimeout(() => this.connect(), 2000 * this.reconnectAttempts);
        }
    }

    // API

    streamChat(prompt, context, useCloud, onToken, onDone) {
        if (!this.chatWs || this.chatWs.readyState !== WebSocket.OPEN) {
            console.error("Chat WS not ready");
            return;
        }

        // Listen for this specific stream
        const handler = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'token') {
                onToken(data.content);
            } else if (data.type === 'done') {
                this.chatWs.removeEventListener('message', handler);
                onDone();
            }
        };

        this.chatWs.addEventListener('message', handler);

        this.chatWs.send(JSON.stringify({
            prompt,
            context,
            use_cloud: useCloud
        }));
    }

    sendTelemetry(workspace, type, data) {
        // Send via POST for durability or Queue via WS
        // For now, simpler to use fetch for telemetry to hit the specific API endpoint
        fetch('/api/telemetry/event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ workspace, event_type: type, data })
        }).catch(e => console.error("Telemetry failed", e));
    }
}

export const wsSync = new WebSocketSync();
