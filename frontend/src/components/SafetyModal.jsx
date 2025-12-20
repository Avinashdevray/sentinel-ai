import React from 'react';

export function SafetyModal({ isOpen, onApprove, onReject, data }) {
    if (!isOpen || !data) return null;

    const { screenshot, action, current_url } = data;

    return (
        <div className="modal-overlay">
            <div className="modal-container">
                <div className="modal-header">
                    <h2>⚠️ High-Risk Action Detected</h2>
                    <p className="modal-subtitle">Human approval required before proceeding</p>
                </div>

                <div className="modal-content">
                    <div className="action-details">
                        <div className="detail-row">
                            <span className="detail-label">Action Type:</span>
                            <span className="detail-value action-type">{action?.action?.toUpperCase()}</span>
                        </div>
                        <div className="detail-row">
                            <span className="detail-label">Target:</span>
                            <span className="detail-value">{action?.selector || 'N/A'}</span>
                        </div>
                        <div className="detail-row">
                            <span className="detail-label">Reasoning:</span>
                            <span className="detail-value">{action?.reasoning}</span>
                        </div>
                        <div className="detail-row">
                            <span className="detail-label">Current URL:</span>
                            <span className="detail-value url-text">{current_url}</span>
                        </div>
                        <div className="detail-row">
                            <span className="detail-label">Risk Level:</span>
                            <span className="detail-value risk-high">🔴 HIGH</span>
                        </div>
                    </div>

                    <div className="screenshot-container">
                        <p className="screenshot-label">Current Page View:</p>
                        <div className="screenshot-wrapper">
                            <img
                                src={`data:image/png;base64,${screenshot}`}
                                alt="Current page screenshot"
                                className="screenshot-image"
                            />
                            <div className="screenshot-overlay">
                                <div className="target-indicator">
                                    Target Element: {action?.selector}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="warning-box">
                        <p>⚠️ <strong>Warning:</strong> This action may involve financial transactions or sensitive operations. Please review carefully before approving.</p>
                    </div>
                </div>

                <div className="modal-actions">
                    <button
                        className="btn-reject"
                        onClick={onReject}
                    >
                        ❌ ABORT TASK
                    </button>
                    <button
                        className="btn-approve"
                        onClick={onApprove}
                    >
                        ✅ APPROVE & CONTINUE
                    </button>
                </div>
            </div>
        </div>
    );
}
