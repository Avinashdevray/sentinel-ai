# FinAgent Sentinel - Quick Reference

## 🎯 Project Overview

**Vision-based AI Agent** that navigates banking websites using Gemini 1.5 Pro with human-in-the-loop safety controls.

## 📋 Quick Commands

### Initial Setup (One Time)
```bash
./setup.sh
# Then edit backend/.env with your GOOGLE_API_KEY
```

### Running the Application

**Terminal 1 - Backend + Bank:**
```bash
python start.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access:**
- Dashboard: http://localhost:3000
- API: http://localhost:8000
- Bank: http://localhost:8001

## 🧪 Test Task Examples

### Basic Login
```
Login with username 'demo' and password 'password'
```

### Full Investment Flow (Triggers Approval)
```
Login with username 'demo' and password 'password', then invest 500 rupees in gold
```

### Navigation Only
```
Login as demo/password and navigate to the gold investment page
```

## 🔑 Key Files

### Backend
- `backend/app/brain.py` - Gemini Vision AI integration
- `backend/app/agent.py` - LangGraph state machine
- `backend/app/main.py` - FastAPI WebSocket server
- `backend/.env` - **ADD YOUR API KEY HERE**

### Frontend
- `frontend/src/App.jsx` - Main dashboard
- `frontend/src/components/SafetyModal.jsx` - Approval UI
- `frontend/src/components/LiveLog.jsx` - Real-time logs

### Bank App
- `bank_app/index.html` - Login (demo/password)
- `bank_app/dashboard.html` - Account view
- `bank_app/gold.html` - Investment page (triggers HIGH risk)

## 🎨 Architecture

```
┌─────────────┐
│   Frontend  │ ← WebSocket → ┌──────────────┐
│  Dashboard  │               │   FastAPI    │
└─────────────┘               │   Backend    │
                              └──────┬───────┘
                                     │
                              ┌──────▼───────┐
                              │  LangGraph   │
                              │    Agent     │
                              └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
              ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
              │ Navigator │   │   Brain   │   │  Executor │
              │ (Capture) │   │ (Gemini)  │   │(Playwright)│
              └───────────┘   └───────────┘   └───────────┘
                                     │
                              ┌──────▼───────┐
                              │Safety Valve  │
                              │ HIGH? → Pause│
                              └──────────────┘
```

## 🛡️ Safety Flow

1. Agent analyzes screenshot with Gemini
2. Gemini returns action + risk level
3. If risk = HIGH:
   - Pause execution
   - Send screenshot to frontend
   - Wait for human approval
4. If approved → continue
5. If rejected → abort task

## 🔧 Customization

### Add More High-Risk Keywords
Edit `backend/app/brain.py`:
```python
"Mark ANY action involving 'Pay', 'Buy', 'Transfer', 'Withdraw', 'Send' as HIGH risk"
```

### Change Retry Limit
Edit `backend/app/agent.py`:
```python
max_retries: int = 3  # Change this value
```

### Adjust Screenshot Size
Edit `backend/app/utils.py`:
```python
resize_image_if_needed(image_bytes, max_size=1024)  # Change max_size
```

## 📊 WebSocket Message Types

### Client → Server
- `TASK` - Start new task
- `APPROVAL` - Approve/reject high-risk action

### Server → Client
- `LOG` - Agent log message
- `APPROVAL_REQ` - Request approval (with screenshot)
- `COMPLETE` - Task finished
- `ERROR` - Task failed
- `STATUS` - Connection status

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "API key not found" | Edit `backend/.env` |
| WebSocket won't connect | Check backend is on port 8000 |
| Browser won't launch | Run `playwright install chromium` |
| Agent stuck in loop | Check logs, may need better selectors |
| Frontend blank | Check console, ensure npm install ran |

## 📈 Performance Tips

1. **Reduce screenshot size** - Lower `max_size` in utils.py
2. **Increase wait times** - Add delays in agent.py for slow pages
3. **Use headless mode** - Change `headless=True` in agent.py
4. **Limit retries** - Lower `max_retries` to fail faster

## 🎓 Learning Resources

- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **Gemini Vision**: https://ai.google.dev/gemini-api/docs/vision
- **Playwright**: https://playwright.dev/python/
- **FastAPI WebSockets**: https://fastapi.tiangolo.com/advanced/websockets/

## 📝 Demo Credentials

**Dummy Bank:**
- Username: `demo`
- Password: `password`

**Test Flow:**
1. Login → Dashboard (₹50,000 balance)
2. Click "Invest in Gold"
3. Enter amount (min ₹100)
4. Click "Buy Gold" ← **HIGH RISK** (triggers approval)

## 🚀 Next Steps

1. ✅ Setup complete
2. ✅ Add API key to `.env`
3. ✅ Run `python start.py`
4. ✅ Run `cd frontend && npm run dev`
5. ✅ Open http://localhost:3000
6. ✅ Try the test task!

---

**Happy Hacking! 🎉**
