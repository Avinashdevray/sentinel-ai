import { useState, useEffect } from 'react';
import { useWebSocket } from './hooks/useSocket';
import { LiveLog } from './components/LiveLog';
import { SafetyModal } from './components/SafetyModal';
import VoiceRecorder from './components/VoiceRecorder';
import './App.css';

const WS_URL = 'ws://localhost:8000/ws';

function App() {
    const { isConnected, messages, sessionId, sendMessage, clearMessages } = useWebSocket(WS_URL);
    const [taskInput, setTaskInput] = useState('');
    const [startUrl, setStartUrl] = useState('https://unreckoned-tommy-briefly.ngrok-free.dev');
    const [isRunning, setIsRunning] = useState(false);
    const [logMessages, setLogMessages] = useState([]);
    const [showApprovalModal, setShowApprovalModal] = useState(false);
    const [approvalData, setApprovalData] = useState(null);
    const [taskStatus, setTaskStatus] = useState('idle'); // idle, running, paused, complete, error

    // Process incoming WebSocket messages
    useEffect(() => {
        if (messages.length === 0) return;

        const latestMessage = messages[messages.length - 1];
        console.log('📨 Received message:', latestMessage); // Debug log

        switch (latestMessage.type) {
            case 'LOG':
                console.log('📝 Adding log message:', latestMessage.data.message); // Debug log
                setLogMessages(prev => [...prev, latestMessage.data.message]);
                break;

            case 'SESSION_RESTORED':
                console.log('🔄 Session restored:', latestMessage.data);
                // Restore task status
                if (latestMessage.data.status) {
                    setTaskStatus(latestMessage.data.status.toLowerCase());
                }
                // Show restoration notification
                setLogMessages(prev => [...prev, '🔄 Session restored - reconnected successfully']);
                // If waiting for approval, show modal
                if (latestMessage.data.waiting_for_approval) {
                    setShowApprovalModal(true);
                    setTaskStatus('paused');
                }
                break;

            case 'SESSION_EXPIRED':
                console.log('⚠️ Session expired');
                setLogMessages(prev => [...prev, '⚠️ Previous session expired - starting fresh']);
                setTaskStatus('idle');
                setIsRunning(false);
                break;

            case 'APPROVAL_REQ':
                setShowApprovalModal(true);
                setApprovalData(latestMessage.data);
                setTaskStatus('paused');
                setLogMessages(prev => [...prev, '⏸️ Task paused - waiting for approval']);
                break;

            case 'COMPLETE':
                setIsRunning(false);
                setTaskStatus('complete');
                setLogMessages(prev => [...prev, latestMessage.data.message]);
                break;

            case 'ERROR':
                setIsRunning(false);
                setTaskStatus('error');
                setLogMessages(prev => [...prev, `❌ Error: ${latestMessage.data.message}`]);
                break;

            case 'STATUS':
                setLogMessages(prev => [...prev, latestMessage.data.message]);
                break;
        }
    }, [messages]);

    const handleStartTask = () => {
        if (!taskInput.trim()) {
            alert('Please enter a task');
            return;
        }

        if (!isConnected) {
            alert('Not connected to server. Please wait...');
            return;
        }

        // Clear previous logs
        setLogMessages([]);
        setIsRunning(true);
        setTaskStatus('running');

        // Send task to backend
        sendMessage({
            type: 'TASK',
            data: {
                task: taskInput,
                start_url: startUrl
            }
        });
    };

    const handleApprove = () => {
        sendMessage({
            type: 'APPROVAL',
            data: {
                decision: 'APPROVE'
            }
        });
        setShowApprovalModal(false);
        setApprovalData(null);
        setTaskStatus('running');
    };

    const handleReject = () => {
        sendMessage({
            type: 'APPROVAL',
            data: {
                decision: 'REJECT'
            }
        });
        setShowApprovalModal(false);
        setApprovalData(null);
        setIsRunning(false);
        setTaskStatus('idle');
    };

    const getStatusBadge = () => {
        switch (taskStatus) {
            case 'running':
                return <span className="status-badge status-running">🔄 Running</span>;
            case 'paused':
                return <span className="status-badge status-paused">⏸️ Awaiting Approval</span>;
            case 'complete':
                return <span className="status-badge status-complete">✅ Complete</span>;
            case 'error':
                return <span className="status-badge status-error">❌ Error</span>;
            default:
                return <span className="status-badge status-idle">⚪ Idle</span>;
        }
    };

    return (
        <div className="app">
            <header className="app-header">
                <div className="header-content">
                    <h1 className="app-title">
                        <span className="title-icon">🤖</span>
                        FinAgent Sentinel
                    </h1>
                    <p className="app-subtitle">Autonomous Financial AI Agent with Vision</p>
                </div>
                <div className="header-status">
                    <div className={`connection-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
                        <span className="indicator-dot"></span>
                        {isConnected ? 'Connected' : 'Disconnected'}
                    </div>
                    {sessionId && <span className="session-id">Session: {sessionId.slice(0, 8)}</span>}
                </div>
            </header>

            <div className="main-container">
                <div className="left-panel">
                    <div className="control-panel">
                        <h2 className="panel-title">🎯 Task Control</h2>

                        <div className="form-group">
                            <label htmlFor="start-url">Bank URL</label>
                            <input
                                id="start-url"
                                type="text"
                                value={startUrl}
                                onChange={(e) => setStartUrl(e.target.value)}
                                placeholder="https://unreckoned-tommy-briefly.ngrok-free.dev"
                                disabled={isRunning}
                                className="input-field"
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="task-input">Task Description</label>
                            <div className="task-input-container">
                                <textarea
                                    id="task-input"
                                    value={taskInput}
                                    onChange={(e) => setTaskInput(e.target.value)}
                                    placeholder="Example: Login and invest 500 rupees in gold (or speak in Hindi/Tamil/other Indian languages)"
                                    disabled={isRunning}
                                    className="textarea-field"
                                    rows={4}
                                />
                                <VoiceRecorder
                                    onTranscript={(text, language) => {
                                        setTaskInput(text);
                                        console.log(`🎤 Voice input detected (${language}): ${text}`);
                                    }}
                                />
                            </div>
                        </div>

                        <button
                            onClick={handleStartTask}
                            disabled={isRunning || !isConnected}
                            className="btn-start"
                        >
                            {isRunning ? '⏳ Running...' : '🚀 Start Task'}
                        </button>

                        <div className="status-section">
                            <h3>Status</h3>
                            {getStatusBadge()}
                        </div>

                        <div className="info-box">
                            <h4>💡 Quick Tips</h4>
                            <ul>
                                <li>Be specific with your task description</li>
                                <li>The agent will pause before high-risk actions</li>
                                <li>Review screenshots carefully before approving</li>
                                <li>You can abort at any time</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <div className="right-panel">
                    <LiveLog messages={logMessages} />
                </div>
            </div>

            <SafetyModal
                isOpen={showApprovalModal}
                onApprove={handleApprove}
                onReject={handleReject}
                data={approvalData}
            />
        </div>
    );
}

export default App;
