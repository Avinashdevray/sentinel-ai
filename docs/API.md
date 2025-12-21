# API Reference

## WebSocket API

### Connection

Connect to the WebSocket server at `ws://localhost:8000/ws`

### Client → Server Events

#### Start Task
```json
{
  "type": "start_task",
  "task": "Login and invest 500 rupees in gold",
  "start_url": "http://localhost:8501"
}
```

#### Approve Action
```json
{
  "type": "approve"
}
```

#### Reject Action
```json
{
  "type": "reject"
}
```

### Server → Client Events

#### Log Message
```json
{
  "type": "log",
  "message": "🧠 Analyzing screenshot with Gemini Vision..."
}
```

#### Approval Request
```json
{
  "type": "approval_request",
  "action": {
    "action": "click",
    "selector": "text=Buy Gold",
    "value": null,
    "reasoning": "FINAL ACTION: Executing purchase - requires approval",
    "risk_level": "HIGH",
    "confidence": 0.85
  },
  "screenshot": "data:image/png;base64,iVBORw0KG..."
}
```

#### Task Complete
```json
{
  "type": "task_complete",
  "status": "DONE"
}
```

#### Session Restored
```json
{
  "type": "session_restored",
  "session_id": "abc-123-def-456"
}
```

#### Session Expired
```json
{
  "type": "session_expired",
  "session_id": "abc-123-def-456"
}
```

---

## REST API

### Voice Transcription

**Endpoint:** `POST /api/voice/transcribe`

**Request:**
```bash
curl -X POST http://localhost:8000/api/voice/transcribe \
  -F "audio=@recording.wav"
```

**Response:**
```json
{
  "text": "लॉगिन करें और सोने में पांच सौ रुपये निवेश करें",
  "language": "hi",
  "segments": [
    {
      "id": 0,
      "seek": 0,
      "start": 0.0,
      "end": 3.5,
      "text": " लॉगिन करें और सोने में पांच सौ रुपये निवेश करें",
      "tokens": [...],
      "temperature": 0.0,
      "avg_logprob": -0.25,
      "compression_ratio": 1.2,
      "no_speech_prob": 0.01
    }
  ]
}
```

**Supported Languages:**
- English (en)
- Hindi (hi)
- Tamil (ta)
- Telugu (te)
- Bengali (bn)
- Marathi (mr)
- Gujarati (gu)
- Kannada (kn)
- Malayalam (ml)
- Punjabi (pa)
- And 89+ more languages

---

## Python API

### Agent Initialization

```python
from app.agent import FinAgentGraph

# Create agent
agent = FinAgentGraph()

# Run task
final_state = await agent.run(
    task="Login and invest 500 in gold",
    start_url="http://localhost:8501",
    message_callback=send_message_to_client
)
```

### Validator Usage

```python
from app.validator import LogicValidator
from decimal import Decimal

validator = LogicValidator()

# Validate affordability
is_affordable, balance, amount = validator.validate_affordability(
    balance_str="₹10,000.50",
    amount=500
)

# Calculate percentage
calculated = validator.calculate_dynamic_amount(
    action={"value": "25%"},
    balance_str="₹10,000"
)
# Returns: Decimal('2500')
```

### TTS Usage

```python
from app.tts import speak_completion

# Speak message (macOS only)
await speak_completion("Task completed successfully")
```

---

## Error Codes

| Code | Message | Description |
|------|---------|-------------|
| 503 | Whisper model not available | Whisper model failed to load |
| 500 | Transcription failed | Error during audio transcription |
| 400 | Invalid audio format | Uploaded file is not valid audio |
| 401 | Unauthorized | Missing or invalid API key |
| 429 | Rate limit exceeded | Too many requests |

---

## Rate Limits

- **Voice Transcription:** 60 requests/minute
- **WebSocket Connections:** 10 concurrent connections per IP
- **Vertex AI:** Subject to Google Cloud quotas

---

## Data Models

### AgentAction

```python
class AgentAction(BaseModel):
    action: ActionType  # click, type, press, wait, done, navigate
    selector: Optional[str] = None
    value: Optional[str] = None
    reasoning: str
    risk_level: RiskLevel  # LOW, MEDIUM, HIGH
    confidence: float = 0.5
```

### GraphState

```python
class GraphState(TypedDict):
    messages: list[str]
    screenshot: str
    next_action: dict
    status: Literal["RUNNING", "PAUSED", "DONE", "ERROR"]
    current_url: str
    task: str
    retry_count: int
    max_retries: int
    page_handle: object
    browser_handle: object
    message_callback: object
    tried_login_methods: list
    extracted_balance: Optional[str]
    validation_passed: bool
    last_high_risk_action: Optional[dict]
    high_risk_executed: bool
```

---

## Configuration

### Environment Variables

```bash
# Required
VERTEX_AI_PROJECT=your-project-id
VERTEX_AI_LOCATION=us-central1

# Optional
BROWSER_TYPE=chromium  # chromium, firefox, webkit, chrome
SESSION_GRACE_PERIOD=300  # seconds
```

### Browser Configuration

```python
# Set browser type
import os
os.environ["BROWSER_TYPE"] = "firefox"

# Supported browsers:
# - chromium (default)
# - firefox
# - webkit (Safari)
# - chrome (requires Chrome installed)
```
