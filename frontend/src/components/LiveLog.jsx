import React from 'react';

export function LiveLog({ messages }) {
    const logContainerRef = React.useRef(null);

    // Auto-scroll to bottom when new messages arrive
    React.useEffect(() => {
        if (logContainerRef.current) {
            logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
    }, [messages]);

    const getLogStyle = (message) => {
        const text = message.toLowerCase();
        if (text.includes('error') || text.includes('❌')) {
            return 'log-error';
        } else if (text.includes('warning') || text.includes('⚠️')) {
            return 'log-warning';
        } else if (text.includes('success') || text.includes('✅') || text.includes('✓')) {
            return 'log-success';
        } else if (text.includes('approval') || text.includes('paused')) {
            return 'log-approval';
        }
        return 'log-info';
    };

    return (
        <div className="live-log">
            <div className="log-header">
                <h3>🔍 Live Agent Log</h3>
                <span className="log-count">{messages.length} events</span>
            </div>
            <div className="log-container" ref={logContainerRef}>
                {messages.length === 0 ? (
                    <div className="log-empty">
                        <p>Waiting for agent activity...</p>
                    </div>
                ) : (
                    messages.map((msg, index) => (
                        <div key={index} className={`log-entry ${getLogStyle(msg)}`}>
                            <span className="log-timestamp">
                                {new Date().toLocaleTimeString()}
                            </span>
                            <span className="log-message">{msg}</span>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
