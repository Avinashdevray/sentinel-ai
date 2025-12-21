import { useState, useRef } from 'react';
import { Mic, Square } from 'lucide-react';

export default function VoiceRecorder({ onTranscript }) {
    const [isRecording, setIsRecording] = useState(false);
    const [error, setError] = useState('');
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            mediaRecorderRef.current = new MediaRecorder(stream);
            chunksRef.current = [];

            mediaRecorderRef.current.ondataavailable = (e) => {
                chunksRef.current.push(e.data);
            };

            mediaRecorderRef.current.onstop = async () => {
                const audioBlob = new Blob(chunksRef.current, { type: 'audio/wav' });
                await sendAudioToBackend(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorderRef.current.start();
            setIsRecording(true);
            setError('');
        } catch (err) {
            console.error('Microphone error:', err);
            setError('Microphone access denied');
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    };

    const sendAudioToBackend = async (audioBlob) => {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');

        try {
            const response = await fetch('http://localhost:8000/api/voice/transcribe', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Transcription failed');
            }

            const data = await response.json();
            console.log(`🎤 Detected language: ${data.language}`);
            onTranscript(data.text, data.language);
        } catch (err) {
            console.error('Transcription error:', err);
            setError('Failed to transcribe audio');
        }
    };

    return (
        <div className="voice-recorder">
            <button
                onClick={isRecording ? stopRecording : startRecording}
                className={`voice-button ${isRecording ? 'recording' : ''}`}
                title={isRecording ? 'Stop recording' : 'Start voice input (supports Hindi, Tamil, Telugu, and more)'}
            >
                {isRecording ? <Square size={20} /> : <Mic size={20} />}
            </button>
            {isRecording && <span className="recording-indicator">Recording...</span>}
            {error && <span className="error-text">{error}</span>}
        </div>
    );
}
