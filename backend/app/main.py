from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from typing import Dict
from app.agent import FinAgentGraph
from app.models import WebSocketMessage, TaskRequest, ApprovalResponse
from app.voice import router as voice_router
import uuid
from concurrent.futures import ThreadPoolExecutor
import threading
import time

app = FastAPI(title="FinAgent Sentinel API")

# Include voice router
app.include_router(voice_router)

# Session state constants
SESSION_STATE_ACTIVE = "active"
SESSION_STATE_DISCONNECTED = "disconnected"
SESSION_STATE_EXPIRED = "expired"

# Session timeout configuration
GRACE_PERIOD = 300  # 5 minutes before cleanup
CLEANUP_INTERVAL = 60  # Check every minute

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active sessions with metadata
# Structure: {
#   session_id: {
#     "agent": FinAgentGraph,
#     "state": GraphState,
#     "status": str,
#     "waiting_for_approval": bool,
#     "connection_state": "active" | "disconnected" | "expired",
#     "disconnect_time": float | None,
#     "task_logs": list[str]
#   }
# }
active_sessions: Dict[str, dict] = {}
executor = ThreadPoolExecutor(max_workers=4)


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        # Don't call accept() here - it's already been accepted
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)


manager = ConnectionManager()


async def run_agent_task(session_id: str, task: str, start_url: str):
    """
    Run the agent (async version - no longer needs thread)
    """
    try:
        session = active_sessions[session_id]
        agent = session["agent"]
        
        # Define a callback to send messages in real-time
        async def send_log(message: str):
            """Send a log message to the frontend immediately"""
            # Track log in session for persistence
            if session_id in active_sessions:
                active_sessions[session_id]["task_logs"].append(message)
            
            message_data = {
                "type": "LOG",
                "data": {"message": message},
                "session_id": session_id
            }
            print(f"📤 Sending LOG message: {message}")  # Debug
            await manager.send_message(session_id, message_data)
        
        # Run the agent with the callback (now async!)
        final_state = await agent.run(task, start_url, message_callback=send_log)
        
        # Store the final state
        session["state"] = final_state
        session["status"] = final_state["status"]
        
        # Messages are now sent in real-time via callback, no need to send them here
        
        # Check if we need approval
        if final_state["status"] == "PAUSED":
            # Send approval request
            await manager.send_message(
                session_id,
                {
                    "type": "APPROVAL_REQ",
                    "data": {
                        "screenshot": final_state["screenshot"],
                        "action": final_state["next_action"],
                        "current_url": final_state["current_url"]
                    },
                    "session_id": session_id
                }
            )
            
            # Wait for approval (will be handled by WebSocket message)
            session["waiting_for_approval"] = True
            
        elif final_state["status"] == "DONE":
            await manager.send_message(
                session_id,
                {
                    "type": "COMPLETE",
                    "data": {"message": "Task completed successfully!"},
                    "session_id": session_id
                }
            )
            
        elif final_state["status"] == "ERROR":
            await manager.send_message(
                session_id,
                {
                    "type": "ERROR",
                    "data": {"message": "Task failed. Check logs for details."},
                    "session_id": session_id
                }
            )
    
    except Exception as e:
        asyncio.run_coroutine_threadsafe(
            manager.send_message(
                session_id,
                {
                    "type": "ERROR",
                    "data": {"message": f"Agent error: {str(e)}"},
                    "session_id": session_id
                }
            ),
            loop
        ).result()





async def cleanup_expired_sessions():
    """
    Background task to clean up sessions that have been disconnected
    for longer than the grace period.
    """
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL)
        
        current_time = time.time()
        sessions_to_delete = []
        
        for session_id, session in active_sessions.items():
            if session.get("connection_state") == SESSION_STATE_DISCONNECTED:
                disconnect_time = session.get("disconnect_time", 0)
                
                # Check if grace period has expired
                if current_time - disconnect_time > GRACE_PERIOD:
                    sessions_to_delete.append(session_id)
                    print(f"🗑️ Cleaning up expired session: {session_id}")
        
        # Clean up expired sessions
        for session_id in sessions_to_delete:
            session = active_sessions[session_id]
            
            # Cleanup browser
            if session.get("agent"):
                try:
                    agent = session["agent"]
                    if hasattr(agent, 'browser') and agent.browser:
                        await agent.browser.close()
                    if hasattr(agent, 'playwright') and agent.playwright:
                        await agent.playwright.stop()
                except Exception as e:
                    print(f"Error cleaning up browser for session {session_id}: {e}")
            
            # Delete session
            del active_sessions[session_id]


@app.on_event("startup")
async def startup_event():
    """Start background tasks on app startup"""
    asyncio.create_task(cleanup_expired_sessions())


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "FinAgent Sentinel API is running"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for agent communication
    Supports session reconnection via RECONNECT message
    """
    # Create temporary session ID
    session_id = str(uuid.uuid4())
    
    # Accept connection first
    await websocket.accept()
    
    # Add to connection manager
    await manager.connect(websocket, session_id)
    
    # Initialize new session (may be replaced if RECONNECT message received)
    active_sessions[session_id] = {
        "agent": FinAgentGraph(),
        "state": None,
        "status": "IDLE",
        "waiting_for_approval": False,
        "connection_state": SESSION_STATE_ACTIVE,
        "disconnect_time": None,
        "task_logs": []
    }
    
    print(f"✨ New session created: {session_id}")
    
    # Send initial connection message
    await websocket.send_json({
        "type": "STATUS",
        "data": {"message": "Connected to FinAgent Sentinel", "session_id": session_id},
        "session_id": session_id
    })
    
    try:
        # Main message loop
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "RECONNECT":
                # Handle reconnection request
                old_session_id = data.get("data", {}).get("session_id")
                
                if old_session_id and old_session_id in active_sessions:
                    old_session = active_sessions[old_session_id]
                    
                    # Check if session is still valid
                    if old_session.get("connection_state") == SESSION_STATE_EXPIRED:
                        await websocket.send_json({
                            "type": "SESSION_EXPIRED",
                            "data": {"message": "Session has expired. Please start a new session."},
                            "session_id": session_id
                        })
                    else:
                        # Replace temporary session with old session
                        print(f"🔄 Reconnecting to existing session: {old_session_id}")
                        
                        # Clean up temporary session
                        if session_id in active_sessions:
                            del active_sessions[session_id]
                        manager.disconnect(session_id)
                        
                        # Restore old session
                        session_id = old_session_id
                        old_session["connection_state"] = SESSION_STATE_ACTIVE
                        old_session["disconnect_time"] = None
                        manager.active_connections[session_id] = websocket
                        
                        # Send session restored message
                        await websocket.send_json({
                            "type": "SESSION_RESTORED",
                            "data": {
                                "message": "Session restored successfully",
                                "session_id": session_id,
                                "status": old_session.get("status", "IDLE"),
                                "waiting_for_approval": old_session.get("waiting_for_approval", False),
                                "logs": old_session.get("task_logs", [])
                            },
                            "session_id": session_id
                        })
                        
                        # If waiting for approval, resend approval request
                        if old_session.get("waiting_for_approval") and old_session.get("state"):
                            state = old_session["state"]
                            await websocket.send_json({
                                "type": "APPROVAL_REQ",
                                "data": {
                                    "screenshot": state.get("screenshot"),
                                    "action": state.get("next_action"),
                                    "current_url": state.get("current_url")
                                },
                                "session_id": session_id
                            })
                else:
                    # Session not found
                    await websocket.send_json({
                        "type": "SESSION_EXPIRED",
                        "data": {"message": "Session not found. Using new session."},
                        "session_id": session_id
                    })
            
            elif message_type == "TASK":
                # Start a new task
                task = data["data"]["task"]
                start_url = data["data"].get("start_url", "http://localhost:8501")
                
                await websocket.send_json({
                    "type": "LOG",
                    "data": {"message": f"🎯 Starting task: {task}"},
                    "session_id": session_id
                })
                
                # Run agent as async task (no thread needed!)
                asyncio.create_task(run_agent_task(session_id, task, start_url))
            
            elif message_type == "APPROVAL":
                # Handle approval response
                decision = data["data"]["decision"]
                session = active_sessions.get(session_id)
                
                if not session or not session.get("waiting_for_approval"):
                    await websocket.send_json({
                        "type": "ERROR",
                        "data": {"message": "No pending approval request"},
                        "session_id": session_id
                    })
                    continue
                
                if decision == "APPROVE":
                    await websocket.send_json({
                        "type": "LOG",
                        "data": {"message": "✅ Action approved by user"},
                        "session_id": session_id
                    })
                    
                    # Resume execution in background
                    session["waiting_for_approval"] = False
                    
                    # Create async resume task
                    async def resume_task():
                        agent = session["agent"]
                        state = session["state"]
                        
                        # Resume the agent (now async)
                        final_state = await agent.resume(state)
                        session["state"] = final_state
                        session["status"] = final_state["status"]
                        
                        # Check final status and send appropriate message
                        if final_state["status"] == "DONE":
                            await manager.send_message(
                                session_id,
                                {
                                    "type": "COMPLETE",
                                    "data": {"message": "Task completed successfully!"},
                                    "session_id": session_id
                                }
                            )
                            # Cleanup browser
                            if final_state["status"] in ["DONE", "ERROR"]:
                                await agent.cleanup_browser()
                        elif final_state["status"] == "ERROR":
                            await manager.send_message(
                                session_id,
                                {
                                    "type": "ERROR",
                                    "data": {"message": "Task failed after approval"},
                                    "session_id": session_id
                                }
                            )
                            await agent.cleanup_browser()
                    
                    # Run as async task
                    asyncio.create_task(resume_task())
                    
                elif decision == "REJECT":
                    await websocket.send_json({
                        "type": "LOG",
                        "data": {"message": "❌ Action rejected by user - aborting task"},
                        "session_id": session_id
                    })
                    
                    session["waiting_for_approval"] = False
                    session["status"] = "ABORTED"
                    
                    # Cleanup
                    agent = session["agent"]
                    agent.cleanup_browser()
                    
                    await websocket.send_json({
                        "type": "COMPLETE",
                        "data": {"message": "Task aborted by user"},
                        "session_id": session_id
                    })
            
            elif message_type == "PING":
                await websocket.send_json({
                    "type": "PONG",
                    "data": {},
                    "session_id": session_id
                })
    
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected for session: {session_id}")
        manager.disconnect(session_id)
        
        # Mark session as disconnected instead of deleting
        if session_id in active_sessions:
            session = active_sessions[session_id]
            session["connection_state"] = SESSION_STATE_DISCONNECTED
            session["disconnect_time"] = time.time()
            print(f"⏳ Session {session_id} marked as disconnected. Grace period: {GRACE_PERIOD}s")
    
    except Exception as e:
        import traceback
        print(f"❌ WebSocket error for session {session_id}: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        try:
            await websocket.send_json({
                "type": "ERROR",
                "data": {"message": f"Server error: {str(e)}"},
                "session_id": session_id
            })
        except:
            pass  # Connection might already be closed


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
