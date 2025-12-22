# Guardian Angel Startup Guide

## 1. Prerequisites
- Python 3.9+
- Node.js 16+
- Google Cloud Vertex AI API Key (Gemini)

## 2. Architecture
The system consists of three parts:
1. **Frontend (React)**: User interface for chat and loan requests.
2. **Backend (FastAPI)**: Agent logic, Gemini interactions, and Voice/TTS processing.
3. **Trap Site (HTML)**: A simulated malicious website ("QuickLoan Pro") to test the Guardian Angel.

## 3. Running the System

### Step 1: Start the Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 2: Start the Frontend
```bash
cd frontend
npm install
npm run dev
```
(Runs on http://localhost:3000)

### Step 3: Start the Trap Site
```bash
cd trap_site
python3 -m http.server 8081
```
(Runs on http://localhost:8081)

## 4. Testing the Guardian Angel Workflow

The "Guardian Angel" is a special mode that activates when the agent detects a loan or financial site.

**Test Scenario:**
1. Open the Frontend.
2. Click the Microphone or type:
   > "Go to http://localhost:8081 and get me a loan"
3. **Watch the Agent:**
   - It will visit the site and warn you about the **Fake Timer**.
   - It will proceed to checkout.
   - It will **STOP** and ask for approval before payment (Warning: **Hidden Fees detected**).
   - It will proceed to the Trial Page.
   - It will **STOP** and ask for approval to **"Protect with Virtual Card"** (Warning: **Roach Motel detected**).
   - Upon approval, it will **automatically fill** the form with a mock Virtual Card and complete the transaction.

## 5. Troubleshooting
- If the agent gets stuck, check the backend logs.
- If audio doesn't play, ensure your system volume is up (macOS `afplay` is used).
