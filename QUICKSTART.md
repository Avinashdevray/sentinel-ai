# 🚀 Quick Start Guide

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

## 3-Step Setup

### 1. Install Dependencies

**Option A: Using start script (Recommended)**
```bash
./start.sh
```
The script will automatically:
- Create a virtual environment
- Install all dependencies
- Start both backend and frontend
- Display access URLs

**Option B: Manual Installation**
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
pip install -r requirements.txt
```

### 2. Start the Services

**If you used start.sh:** Services are already running! Skip to step 3.

**Manual start:**

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Streamlit Frontend:**
```bash
cd frontend
streamlit run streamlit_app.py
```

**Terminal 3 - Static HTML Frontend (Optional):**
```bash
cd static
python -m http.server 8080
```

### 3. Access the Application

- **Streamlit App:** http://localhost:8501
- **HTML App:** http://localhost:8080
- **API Docs:** http://localhost:8000/docs

## Demo Login
- **Username:** `demo`
- **Password:** `demo123`

## Stop the Services

```bash
./stop.sh
```

Or manually:
```bash
# Find and kill processes
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:8501 | xargs kill -9  # Streamlit
```

## Using Docker (Alternative)

```bash
docker-compose up -d
```

Access points:
- Backend: http://localhost:8000
- Streamlit: http://localhost:8501
- Static: http://localhost:8080

Stop:
```bash
docker-compose down
```

## Testing the API

### Using cURL

**Login:**
```bash
curl -X POST "http://localhost:8000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}'
```

**Get Accounts (replace TOKEN):**
```bash
curl -X GET "http://localhost:8000/api/accounts" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Deposit:**
```bash
curl -X POST "http://localhost:8000/api/deposit" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"account_number":"ACC12345678","amount":100.00}'
```

### Using Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/login",
    json={"username": "demo", "password": "demo123"}
)
token = response.json()["token"]

# Get accounts
headers = {"Authorization": f"Bearer {token}"}
accounts = requests.get("http://localhost:8000/api/accounts", headers=headers)
print(accounts.json())
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
lsof -ti:8000 | xargs kill -9
```

### Module Not Found
```bash
# Reinstall dependencies
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### Connection Refused
- Make sure backend is running on port 8000
- Check if API_BASE_URL in frontend matches your backend URL

## Next Steps

1. ✅ Login with demo credentials
2. 💰 Try depositing money
3. 💸 Try withdrawing money
4. 🔄 Try transferring between accounts
5. 📊 View transaction history
6. 👤 Create a new account (Register)

## Need Help?

- Check the full README.md for detailed documentation
- Visit API documentation at http://localhost:8000/docs
- Check logs in the `logs/` directory

---

Happy Banking! 🏦