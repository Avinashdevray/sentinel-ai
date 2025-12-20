# FinAgent Sentinel - Technical Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                    (React + Vite Dashboard)                     │
│                      http://localhost:3000                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ WebSocket (ws://localhost:8000/ws)
                             │ Bidirectional Real-time Communication
┌────────────────────────────▼────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│                   (WebSocket Server + API)                      │
│                      http://localhost:8000                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Connection Manager                         │  │
│  │  - Session Management                                   │  │
│  │  - Message Routing                                      │  │
│  │  - Approval Flow Coordination                           │  │
│  └────────────────────┬────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────▼────────────────────────────────────┐  │
│  │              FinAgent Graph (LangGraph)                 │  │
│  │                                                          │  │
│  │   ┌──────────┐    ┌──────────┐    ┌──────────────┐    │  │
│  │   │Navigator │───▶│  Brain   │───▶│Safety Valve  │    │  │
│  │   │  Node    │    │   Node   │    │    Node      │    │  │
│  │   └──────────┘    └──────────┘    └──────┬───────┘    │  │
│  │        ▲                                  │             │  │
│  │        │                                  ▼             │  │
│  │        │                           ┌─────────────┐     │  │
│  │        │                           │ Risk Check  │     │  │
│  │        │                           │ HIGH? LOW?  │     │  │
│  │        │                           └──────┬──────┘     │  │
│  │        │                                  │             │  │
│  │        │              ┌───────────────────┼─────┐      │  │
│  │        │              │ LOW               │HIGH │      │  │
│  │        │              ▼                   ▼     │      │  │
│  │   ┌────┴──────┐  ┌──────────┐      ┌─────────┐│      │  │
│  │   │ Executor  │◀─│  Resume  │◀─────│  PAUSE  ││      │  │
│  │   │   Node    │  │  After   │      │  & Wait ││      │  │
│  │   └───────────┘  │ Approval │      └─────────┘│      │  │
│  │                  └──────────┘                  │      │  │
│  │                                                 │      │  │
│  └─────────────────────────────────────────────────┼──────┘  │
│                                                     │         │
└─────────────────────────────────────────────────────┼─────────┘
                                                      │
                                    Send APPROVAL_REQ to Frontend
                                    Wait for APPROVE/REJECT
                                                      │
┌─────────────────────────────────────────────────────▼─────────┐
│                    BROWSER AUTOMATION                         │
│                    (Playwright Sync API)                      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Screenshot  │  │   Click      │  │    Type      │      │
│  │   Capture    │  │   Element    │  │   Text       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└────────────────────────────┬──────────────────────────────────┘
                             │ HTTP Requests
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TARGET WEBSITE                             │
│                   (Dummy Bank Application)                      │
│                    http://localhost:8001                        │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Login Page   │─▶│  Dashboard   │─▶│  Gold Page   │         │
│  │ (index.html) │  │(dashboard.   │  │ (gold.html)  │         │
│  │              │  │     html)    │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘

                             ▲
                             │ Vision Analysis
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    GEMINI 1.5 PRO VISION                        │
│                   (Google Generative AI)                        │
│                                                                 │
│  Input: Base64 Screenshot + Task Description                   │
│  Output: {                                                      │
│    "action": "click|type|wait|done",                           │
│    "selector": "CSS selector",                                 │
│    "reasoning": "Why this action",                             │
│    "risk_level": "HIGH|LOW",                                   │
│    "confidence": 0.0-1.0                                       │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Task Initiation
```
User → Frontend → WebSocket → Backend
  {
    "type": "TASK",
    "data": {
      "task": "Login and invest 500 in gold",
      "start_url": "http://localhost:8001"
    }
  }
```

### 2. Agent Loop (Continuous)
```
Navigator → Capture Screenshot → Base64 Encode
    ↓
Brain → Send to Gemini Vision → Analyze UI → Return Action
    ↓
Safety Valve → Check Risk Level
    ↓
    ├─ LOW → Executor → Perform Action → Back to Navigator
    │
    └─ HIGH → PAUSE → Send to Frontend
                ↓
          User Reviews Screenshot
                ↓
          APPROVE or REJECT
                ↓
          Resume or Abort
```

### 3. Approval Flow
```
Backend → Frontend
  {
    "type": "APPROVAL_REQ",
    "data": {
      "screenshot": "base64_image",
      "action": {
        "action": "click",
        "selector": "#pay-btn",
        "reasoning": "Executing purchase",
        "risk_level": "HIGH"
      },
      "current_url": "http://localhost:8001/gold.html"
    }
  }

Frontend → Backend
  {
    "type": "APPROVAL",
    "data": {
      "decision": "APPROVE" | "REJECT"
    }
  }
```

## State Machine

```
┌─────────────────────────────────────────────────────────┐
│                    GraphState                           │
├─────────────────────────────────────────────────────────┤
│ messages: List[str]          # Execution log            │
│ screenshot: str              # Current page (base64)    │
│ next_action: dict            # Planned action           │
│ status: RUNNING|PAUSED|DONE|ERROR                       │
│ current_url: str             # Current page URL         │
│ task: str                    # User's task description  │
│ retry_count: int             # Failed attempts          │
│ max_retries: int = 3         # Retry limit              │
│ page_handle: Page            # Playwright page object   │
│ browser_handle: Browser      # Playwright browser       │
└─────────────────────────────────────────────────────────┘
```

## Node Responsibilities

### Navigator Node
- **Input**: Current state
- **Actions**:
  - Wait for page stability
  - Capture full-page screenshot
  - Resize image for API efficiency
  - Encode to base64
- **Output**: State with screenshot

### Brain Node
- **Input**: State with screenshot
- **Actions**:
  - Construct prompt with task + screenshot
  - Call Gemini Vision API
  - Parse JSON response
  - Validate action structure
- **Output**: State with next_action

### Safety Valve Node
- **Input**: State with next_action
- **Actions**:
  - Check action.risk_level
  - If HIGH: Set status to PAUSED, return
  - If LOW: Continue to executor
  - If action is "done": Set status to DONE
- **Output**: State with updated status

### Executor Node
- **Input**: State with next_action
- **Actions**:
  - Execute action (click/type/wait/navigate)
  - Handle errors with retry logic
  - Update retry counter
  - Wait for page updates
- **Output**: State with execution result

## Risk Classification

### HIGH Risk Actions
- Keywords: "Pay", "Buy", "Purchase", "Transfer", "Send", "Withdraw"
- Selectors containing: "pay", "buy", "confirm", "submit-payment"
- Any action on financial transaction pages

### LOW Risk Actions
- Navigation clicks
- Form field inputs (non-financial)
- Reading/viewing pages
- Wait actions

## Error Handling

### Retry Strategy
```python
if error:
    retry_count += 1
    if retry_count < max_retries:
        return to Navigator  # Try again
    else:
        status = ERROR
        return END
```

### Common Errors
1. **Element Not Found**: Retry with fresh screenshot
2. **Timeout**: Wait action, then retry
3. **JSON Parse Error**: Return safe wait action
4. **API Error**: Log and pause for manual intervention

## Security Features

1. **Session Isolation**: Each task runs in separate browser context
2. **Screenshot Verification**: Human sees exact agent view
3. **Explicit Approval**: No auto-execution of high-risk actions
4. **Abort Capability**: User can reject at any time
5. **Audit Trail**: All actions logged in real-time

## Performance Optimizations

1. **Image Resizing**: Screenshots resized to 1024px max
2. **Headless Browser**: Can run without GUI (set headless=True)
3. **Connection Pooling**: WebSocket reuses connections
4. **Lazy Loading**: Browser only launches when needed

## Scalability Considerations

### Current (Proof of Concept)
- Single agent per session
- Synchronous Playwright
- In-memory state

### Future (Production)
- Multi-agent orchestration
- Async Playwright for concurrency
- Redis for state persistence
- Queue-based task distribution
- Horizontal scaling with load balancer

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React + Vite | User interface |
| Communication | WebSockets | Real-time bidirectional |
| Backend | FastAPI | API server |
| Agent Framework | LangGraph | State machine |
| Vision AI | Gemini 1.5 Pro | Screenshot analysis |
| Browser Automation | Playwright | Web interaction |
| Validation | Pydantic | Type safety |
| Target | HTML/CSS/JS | Demo bank app |

## File Size Breakdown

```
Total Project Size: ~50KB (excluding dependencies)

Backend:
  - main.py: ~8KB (WebSocket server)
  - agent.py: ~10KB (LangGraph state machine)
  - brain.py: ~5KB (Gemini integration)
  - models.py: ~2KB (Pydantic schemas)
  - utils.py: ~2KB (Helper functions)

Frontend:
  - App.jsx: ~6KB (Main component)
  - App.css: ~8KB (Styling)
  - SafetyModal.jsx: ~3KB (Approval UI)
  - LiveLog.jsx: ~2KB (Log display)
  - useSocket.js: ~2KB (WebSocket hook)

Bank App:
  - index.html: ~3KB (Login)
  - dashboard.html: ~4KB (Dashboard)
  - gold.html: ~5KB (Investment)
```

---

**Architecture designed for:**
- ✅ Clarity and maintainability
- ✅ Safety and human oversight
- ✅ Resilience and error recovery
- ✅ Real-time user feedback
- ✅ Easy debugging and monitoring
