import { useState, useEffect, useRef } from 'react';

const SESSION_STORAGE_KEY = 'finagent_session_id';

export function useWebSocket(url) {
    const [isConnected, setIsConnected] = useState(false);
    const [messages, setMessages] = useState([]);
    const [sessionId, setSessionId] = useState(null);
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const isReconnectingRef = useRef(false);

    const connect = () => {
        try {
            const ws = new WebSocket(url);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log('WebSocket connected');
                setIsConnected(true);

                // Check if we have a stored session to reconnect to
                const storedSessionId = localStorage.getItem(SESSION_STORAGE_KEY);

                if (storedSessionId && !isReconnectingRef.current) {
                    console.log('🔄 Attempting to reconnect to session:', storedSessionId);
                    isReconnectingRef.current = true;

                    // Send reconnection request
                    ws.send(JSON.stringify({
                        type: 'RECONNECT',
                        data: { session_id: storedSessionId }
                    }));
                }
                // If no stored session, backend will create new one automatically
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('Received:', data);

                // Handle session ID
                if (data.session_id) {
                    if (!sessionId || sessionId !== data.session_id) {
                        setSessionId(data.session_id);
                        localStorage.setItem(SESSION_STORAGE_KEY, data.session_id);
                        console.log('💾 Session ID saved to localStorage:', data.session_id);
                    }
                }

                // Handle session restoration
                if (data.type === 'SESSION_RESTORED') {
                    console.log('✅ Session restored successfully');
                    isReconnectingRef.current = false;

                    // Restore logs if available
                    if (data.data.logs && data.data.logs.length > 0) {
                        // Add restored logs as individual messages
                        data.data.logs.forEach(log => {
                            setMessages(prev => [...prev, {
                                type: 'LOG',
                                data: { message: log },
                                session_id: data.session_id
                            }]);
                        });
                    }
                }

                // Handle session expiry
                if (data.type === 'SESSION_EXPIRED') {
                    console.log('⚠️ Session expired, clearing localStorage');
                    localStorage.removeItem(SESSION_STORAGE_KEY);
                    setSessionId(null);
                    isReconnectingRef.current = false;
                }

                setMessages((prev) => [...prev, data]);
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected');
                setIsConnected(false);

                // Attempt to reconnect after 3 seconds
                reconnectTimeoutRef.current = setTimeout(() => {
                    console.log('Attempting to reconnect...');
                    connect();
                }, 3000);
            };
        } catch (error) {
            console.error('Failed to connect:', error);
        }
    };

    useEffect(() => {
        connect();

        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [url]);

    const sendMessage = (message) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
        } else {
            console.error('WebSocket is not connected');
        }
    };

    const clearMessages = () => {
        setMessages([]);
    };

    return {
        isConnected,
        messages,
        sessionId,
        sendMessage,
        clearMessages
    };
}
