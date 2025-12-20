# 🚀 Quick Test Guide - Localhost:8501

## Before You Start

Make sure your banking website is running on port 8501:
```bash
# Check if something is running on port 8501
lsof -i :8501

# If it's a Streamlit app, start it with:
streamlit run your_app.py --server.port 8501
```

---

## Test Execution

### 1. Start Backend (Terminal 1)
```bash
cd /Users/avinashdevray/finagent_sentinel
python3 start.py
```

**Look for this output:**
```
✅ Successfully connected to: http://localhost:8501
📄 Page Title: [Your Banking Site Title]
```

### 2. Start Frontend (Terminal 2)
```bash
cd /Users/avinashdevray/finagent_sentinel/frontend
npm run dev
```

### 3. Open Dashboard
Navigate to: `http://localhost:3000`

### 4. Test Task
Try this simple task first:
```
Navigate to the homepage and tell me what you see
```

---

## What Changed?

| Component | Old Value | New Value |
|-----------|-----------|-----------|
| **Target URL** | `http://localhost:8001` | `http://localhost:8501` |
| **Verification** | None | Page title printed to console |
| **Risk Keywords** | 7 keywords | 15 keywords (added: submit, execute, finalize, etc.) |

---

## Quick Debugging

### If agent can't connect:
```bash
# Check if port 8501 is accessible
curl http://localhost:8501

# Or open in browser
open http://localhost:8501
```

### If agent can't find buttons:
1. Open browser DevTools (F12)
2. Inspect the button element
3. Note the button text, ID, or class
4. Share with me to update selectors

### Check logs:
- **Backend logs:** Terminal where you ran `python3 start.py`
- **Frontend logs:** Browser console (F12 → Console tab)
- **Agent logs:** Right panel in the dashboard

---

## Expected Console Output

```
🔵 Launching Chromium...
✅ Successfully connected to: http://localhost:8501
📄 Page Title: My Banking App
🎯 Starting task: Navigate to the homepage and tell me what you see
📸 Captured screenshot of http://localhost:8501
🧠 Analyzing screenshot with Gemini Vision...
💡 Decision: wait | Risk: LOW | Reasoning: Page loaded successfully
```

---

## Need Help?

If you see errors, check:
1. ✅ Is localhost:8501 running?
2. ✅ Does it load in a regular browser?
3. ✅ Are there any console errors?

Share the error message and I'll help debug!
