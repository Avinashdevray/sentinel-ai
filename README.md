# FinAgent Sentinel 🤖

**Autonomous Financial AI Agent with Vision-Language Models**

A production-grade monorepo demonstrating an AI agent that uses Gemini 1.5 Pro Vision to navigate banking websites with human-in-the-loop safety controls.

## 🎯 Features

- **Vision-First Navigation**: Uses Gemini 1.5 Pro to "see" and understand web UIs through screenshots
- **Zero-Trust Safety**: Implements "Conscious Pause" mechanism for high-risk financial actions
- **Resilient Execution**: LangGraph-based cyclic state machine with automatic retry logic
- **Real-time Monitoring**: WebSocket-based dashboard with live agent logs
- **Human Approval Flow**: Interactive modal for reviewing and approving high-risk actions

## 📁 Project Structure

```
finagent-sentinel/
├── backend/              # Python FastAPI + Agent Logic
│   ├── app/
│   │   ├── main.py      # WebSocket Server
│   │   ├── brain.py     # Gemini Vision Interface
│   │   ├── agent.py     # LangGraph State Machine
│   │   ├── models.py    # Pydantic Schemas
│   │   └── utils.py     # Helper Functions
│   ├── .env             # API Keys
│   └── requirements.txt
├── frontend/            # React + Vite Dashboard
│   ├── src/
│   │   ├── App.jsx      # Main Dashboard
│   │   ├── components/
│   │   │   ├── LiveLog.jsx
│   │   │   └── SafetyModal.jsx
│   │   └── hooks/
│   │       └── useSocket.js
│   └── package.json
├── bank_app/            # Dummy Bank (Target)
│   ├── index.html       # Login Page
│   ├── dashboard.html   # Account Summary
│   └── gold.html        # Investment Page
└── start.py             # Startup Script
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Google API Key (for Gemini)

### 1. Setup Backend

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Configure API key
# Edit backend/.env and add your GOOGLE_API_KEY
```

### 2. Setup Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install
```

### 3. Run the Application

**Terminal 1 - Start Backend & Bank App:**
```bash
# From project root
python start.py
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
```

**Open your browser:**
- Frontend Dashboard: http://localhost:3000
- Backend API: http://localhost:8000
- Dummy Bank: http://localhost:8001

## 🎮 Usage

1. **Open the Dashboard** at http://localhost:3000
2. **Enter a task**, for example:
   ```
   Login with username 'demo' and password 'password', 
   then invest 500 rupees in gold
   ```
3. **Click "Start Task"** and watch the agent work
4. **Review the approval modal** when it pauses before the "Buy Gold" action
5. **Approve or Reject** the high-risk action

## 🧠 How It Works

### Vision-Based Navigation

The agent uses Gemini 1.5 Pro to analyze screenshots instead of parsing HTML:

```python
# brain.py
action = analyze_screenshot(
    screenshot_base64=screenshot,
    task="Invest 500 in Gold",
    current_url="http://localhost:8001/gold.html"
)
# Returns: {"action": "click", "selector": "#pay-btn", "risk_level": "HIGH"}
```

### State Machine Flow

```
Navigator → Brain → Safety Valve → Executor
    ↑                                   ↓
    └───────────── Retry Loop ──────────┘
```

1. **Navigator**: Captures screenshot
2. **Brain**: Analyzes with Gemini Vision
3. **Safety Valve**: Checks risk level
   - HIGH → Pause & request approval
   - LOW → Continue to executor
4. **Executor**: Performs action
   - Success → Loop back to Navigator
   - Error → Retry with backoff

### Safety Mechanism

```python
# agent.py - Safety Valve Node
if action.risk_level == "HIGH":
    state["status"] = "PAUSED"
    # Send approval request to frontend
    # Wait for human decision
```

## 🔧 Configuration

### Environment Variables

Edit `backend/.env`:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
BANK_URL=http://localhost:8001
```

### Customizing Risk Detection

Edit the prompt in `backend/app/brain.py`:

```python
# Mark additional keywords as HIGH risk
"Mark ANY action involving 'Pay', 'Buy', 'Transfer', 'Withdraw' as HIGH risk"
```

## 📊 Architecture Decisions

### Why Playwright Sync API?

- Simpler debugging within LangGraph nodes
- Linear execution flow easier to reason about
- Sufficient for proof-of-concept

### Why LangGraph?

- Built-in state management
- Cyclic graphs for retry logic
- Easy to visualize and debug

### Why WebSockets?

- Real-time bidirectional communication
- Instant approval flow
- Live log streaming

## 🛡️ Safety Features

1. **Risk Classification**: AI automatically identifies high-risk actions
2. **Screenshot Review**: Human sees exactly what the agent sees
3. **Explicit Approval**: Large, clear approve/reject buttons
4. **Abort Anytime**: User can reject and stop the task
5. **Session Isolation**: Each task runs in isolated browser context

## 🐛 Troubleshooting

**Issue**: "GOOGLE_API_KEY not found"
- **Solution**: Edit `backend/.env` and add your API key

**Issue**: Frontend can't connect to WebSocket
- **Solution**: Ensure backend is running on port 8000

**Issue**: Playwright browser not launching
- **Solution**: Run `playwright install chromium`

**Issue**: Agent gets stuck in retry loop
- **Solution**: Check the live logs for error details, may need to adjust selectors

## 📝 Example Tasks

```
# Simple login
Login with username 'demo' and password 'password'

# Navigation task
Go to the dashboard and click on 'Invest in Gold'

# Complete flow (will trigger approval)
Login as demo/password, navigate to gold investment, and invest 1000 rupees

# Multi-step task
Login, check the balance, then invest 25% of balance in gold
```

## 🎨 Frontend Features

- **Dark Theme**: Modern, easy on the eyes
- **Split Screen**: Control panel + live logs
- **Color-Coded Logs**: Visual feedback for different event types
- **Approval Modal**: Full-screen review interface
- **Connection Status**: Real-time WebSocket status indicator

## 🔮 Future Enhancements

- [ ] Multi-agent orchestration
- [ ] Voice command interface
- [ ] Session replay/recording
- [ ] Custom risk policies
- [ ] Integration with real banking APIs (with proper auth)
- [ ] Natural language task parsing
- [ ] Screenshot annotation with bounding boxes

## 📄 License

MIT License - Feel free to use for learning and hackathons!

## 🙏 Acknowledgments

- Google Gemini for Vision AI
- LangChain/LangGraph for agent framework
- Playwright for browser automation
- FastAPI for WebSocket server

---

**Built for the FinAgent Sentinel Hackathon** 🏆

For questions or issues, please open a GitHub issue.
