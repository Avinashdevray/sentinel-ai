from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from typing import Dict
from app.agent import FinAgentGraph
from app.models import WebSocketMessage, TaskRequest, ApprovalResponse
import uuid
from concurrent.futures import ThreadPoolExecutor
import threading

app = FastAPI(title="FinAgent Sentinel API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active sessions
active_sessions: Dict[str, dict] = {}
executor = ThreadPoolExecutor(max_workers=4)


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
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



@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "FinAgent Sentinel API is running"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for agent communication
    """
    session_id = str(uuid.uuid4())
    await manager.connect(websocket, session_id)
    
    # Initialize session
    active_sessions[session_id] = {
        "agent": FinAgentGraph(),
        "state": None,
        "status": "IDLE",
        "waiting_for_approval": False
    }
    
    try:
        await websocket.send_json({
            "type": "STATUS",
            "data": {"message": "Connected to FinAgent Sentinel", "session_id": session_id},
            "session_id": session_id
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "TASK":
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
        manager.disconnect(session_id)
        
        # Cleanup session
        if session_id in active_sessions:
            session = active_sessions[session_id]
            if session.get("agent"):
                try:
                    session["agent"].cleanup_browser()
                except:
                    pass
            del active_sessions[session_id]
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "ERROR",
            "data": {"message": f"Server error: {str(e)}"},
            "session_id": session_id
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
