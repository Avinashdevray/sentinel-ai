from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import jwt
import hashlib
import uuid
import json
import asyncio
import random

app = FastAPI(title="DummyBank API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

# In-memory database
users_db = {}
accounts_db = {}
transactions_db = []
investments_db = {}  # {user_id: {"gold_grams": 0.0, "mutual_funds": []}}

# Pydantic Models
class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    username: str
    password: str

class Account(BaseModel):
    account_number: str
    account_type: str
    balance: float
    user_id: str

class Transaction(BaseModel):
    from_account: str
    to_account: str
    amount: float
    description: Optional[str] = None

class Deposit(BaseModel):
    account_number: str
    amount: float

class Withdrawal(BaseModel):
    account_number: str
    amount: float
    description: Optional[str] = None

class GoldPurchase(BaseModel):
    account_number: str
    grams: float
    price_per_gram: float

class MutualFundPurchase(BaseModel):
    account_number: str
    fund_name: str
    amount: float
    is_sip: bool

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Initialize some dummy data
def init_dummy_data():
    # Create demo user
    user_id = str(uuid.uuid4())
    users_db[user_id] = {
        "user_id": user_id,
        "username": "demo",
        "email": "demo@dummybank.com",
        "password": hash_password("demo123"),
        "full_name": "Demo User"
    }
    
    # Initialize investments for demo user
    investments_db[user_id] = {"gold_grams": 0.0, "mutual_funds": []}
    
    # Create demo account
    account_number = "ACC" + str(uuid.uuid4())[:8].upper()
    accounts_db[account_number] = {
        "account_number": account_number,
        "account_type": "Savings",
        "balance": 5000.00,
        "user_id": user_id,
        "created_at": datetime.utcnow()
    }
    
    # Add some transactions
    transactions_db.append({
        "transaction_id": str(uuid.uuid4()),
        "from_account": "SYSTEM",
        "to_account": account_number,
        "amount": 5000.00,
        "description": "Initial deposit",
        "timestamp": datetime.utcnow(),
        "type": "credit"
    })

init_dummy_data()

# WebSocket Endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Routes
@app.get("/")
def read_root():
    return {"message": "Welcome to DummyBank API", "version": "1.0.0"}

@app.post("/api/register")
def register(user: UserRegister):
    for u in users_db.values():
        if u["username"] == user.username:
            raise HTTPException(status_code=400, detail="Username already exists")
    
    user_id = str(uuid.uuid4())
    users_db[user_id] = {
        "user_id": user_id,
        "username": user.username,
        "email": user.email,
        "password": hash_password(user.password),
        "full_name": user.full_name
    }
    investments_db[user_id] = {"gold_grams": 0.0, "mutual_funds": []}
    
    account_number = "ACC" + str(uuid.uuid4())[:8].upper()
    accounts_db[account_number] = {
        "account_number": account_number,
        "account_type": "Savings",
        "balance": 0.0,
        "user_id": user_id,
        "created_at": datetime.utcnow()
    }
    
    token = create_token(user_id)
    return {
        "message": "User registered successfully",
        "token": token,
        "user_id": user_id,
        "account_number": account_number
    }

@app.post("/api/login")
def login(user: UserLogin):
    for u in users_db.values():
        if u["username"] == user.username and u["password"] == hash_password(user.password):
            token = create_token(u["user_id"])
            return {
                "message": "Login successful",
                "token": token,
                "user_id": u["user_id"],
                "username": u["username"]
            }
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/accounts")
def get_accounts(user_id: str = Depends(verify_token)):
    user_accounts = [acc for acc in accounts_db.values() if acc["user_id"] == user_id]
    return {"accounts": user_accounts}

@app.get("/api/account/{account_number}")
def get_account(account_number: str, user_id: str = Depends(verify_token)):
    if account_number not in accounts_db:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account = accounts_db[account_number]
    if account["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {"account": account}

@app.get("/api/transactions/{account_number}")
def get_transactions(account_number: str, user_id: str = Depends(verify_token)):
    if account_number not in accounts_db:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account = accounts_db[account_number]
    if account["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    account_transactions = [
        t for t in transactions_db 
        if t["from_account"] == account_number or t["to_account"] == account_number
    ]
    
    return {"transactions": account_transactions}

@app.post("/api/deposit")
async def deposit(deposit: Deposit, user_id: str = Depends(verify_token)):
    if deposit.account_number not in accounts_db:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account = accounts_db[deposit.account_number]
    if account["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if deposit.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    
    accounts_db[deposit.account_number]["balance"] += deposit.amount
    
    transaction = {
        "transaction_id": str(uuid.uuid4()),
        "from_account": "CASH",
        "to_account": deposit.account_number,
        "amount": deposit.amount,
        "description": "Cash deposit",
        "timestamp": datetime.utcnow(),
        "type": "credit"
    }
    transactions_db.append(transaction)
    
    await manager.broadcast(json.dumps({"type": "balance_update", "account": deposit.account_number}))
    
    return {
        "message": "Deposit successful",
        "new_balance": accounts_db[deposit.account_number]["balance"],
        "transaction": transaction
    }

@app.post("/api/withdraw")
async def withdraw(withdrawal: Withdrawal, user_id: str = Depends(verify_token)):
    if withdrawal.account_number not in accounts_db:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account = accounts_db[withdrawal.account_number]
    if account["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if withdrawal.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    
    if account["balance"] < withdrawal.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    accounts_db[withdrawal.account_number]["balance"] -= withdrawal.amount
    
    transaction = {
        "transaction_id": str(uuid.uuid4()),
        "from_account": withdrawal.account_number,
        "to_account": "CASH",
        "amount": withdrawal.amount,
        "description": withdrawal.description or "Cash withdrawal",
        "timestamp": datetime.utcnow(),
        "type": "debit"
    }
    transactions_db.append(transaction)
    
    await manager.broadcast(json.dumps({"type": "balance_update", "account": withdrawal.account_number}))
    
    return {
        "message": "Withdrawal successful",
        "new_balance": accounts_db[withdrawal.account_number]["balance"],
        "transaction": transaction
    }

@app.post("/api/transfer")
async def transfer(transaction: Transaction, user_id: str = Depends(verify_token)):
    if transaction.from_account not in accounts_db:
        raise HTTPException(status_code=404, detail="Source account not found")
    
    # Allow transfer to external/unknown accounts for simulation, but check valid if internal
    # if transaction.to_account not in accounts_db:
    #     raise HTTPException(status_code=404, detail="Destination account not found")
    
    from_account = accounts_db[transaction.from_account]
    if from_account["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    
    if from_account["balance"] < transaction.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # Perform transfer
    accounts_db[transaction.from_account]["balance"] -= transaction.amount
    
    # If to_account is internal, credit it
    if transaction.to_account in accounts_db:
        accounts_db[transaction.to_account]["balance"] += transaction.amount
    
    transaction_record = {
        "transaction_id": str(uuid.uuid4()),
        "from_account": transaction.from_account,
        "to_account": transaction.to_account,
        "amount": transaction.amount,
        "description": transaction.description or "Transfer",
        "timestamp": datetime.utcnow(),
        "type": "transfer"
    }
    transactions_db.append(transaction_record)
    
    await manager.broadcast(json.dumps({"type": "balance_update", "account": transaction.from_account}))
    if transaction.to_account in accounts_db:
        await manager.broadcast(json.dumps({"type": "balance_update", "account": transaction.to_account}))
    
    return {
        "message": "Transfer successful",
        "new_balance": accounts_db[transaction.from_account]["balance"],
        "transaction": transaction_record
    }

@app.get("/api/user/profile")
def get_profile(user_id: str = Depends(verify_token)):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id].copy()
    user.pop("password")
    return {"user": user}

# Investment Routes
@app.get("/api/market/gold-price")
def get_gold_price():
    # Mock real-time price change
    base_price = 6500.00 # per gram
    variation = random.uniform(-50, 50)
    current_price = base_price + variation
    return {"price": round(current_price, 2), "currency": "INR"}

@app.get("/api/invest/holdings")
def get_holdings(user_id: str = Depends(verify_token)):
    if user_id not in investments_db:
        investments_db[user_id] = {"gold_grams": 0.0, "mutual_funds": []}
    return {"holdings": investments_db[user_id]}

@app.post("/api/invest/gold/buy")
async def buy_gold(purchase: GoldPurchase, user_id: str = Depends(verify_token)):
    if purchase.account_number not in accounts_db:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account = accounts_db[purchase.account_number]
    if account["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    total_cost = purchase.grams * purchase.price_per_gram
    
    if account["balance"] < total_cost:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # Deduct balance
    accounts_db[purchase.account_number]["balance"] -= total_cost
    
    # Add Gold
    if user_id not in investments_db:
        investments_db[user_id] = {"gold_grams": 0.0, "mutual_funds": []}
    
    investments_db[user_id]["gold_grams"] += purchase.grams
    
    transaction = {
        "transaction_id": str(uuid.uuid4()),
        "from_account": purchase.account_number,
        "to_account": "GOLD_VAULT",
        "amount": total_cost,
        "description": f"Bought {purchase.grams}g Gold",
        "timestamp": datetime.utcnow(),
        "type": "debit"
    }
    transactions_db.append(transaction)
    
    await manager.broadcast(json.dumps({"type": "balance_update", "account": purchase.account_number}))
    
    return {
        "message": "Gold purchased successfully",
        "new_balance": accounts_db[purchase.account_number]["balance"],
        "holdings": investments_db[user_id]
    }

@app.post("/api/invest/mutual-funds/buy")
async def buy_mutual_fund(purchase: MutualFundPurchase, user_id: str = Depends(verify_token)):
    if purchase.account_number not in accounts_db:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account = accounts_db[purchase.account_number]
    if account["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if account["balance"] < purchase.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # Deduct balance
    accounts_db[purchase.account_number]["balance"] -= purchase.amount
    
    # Add Mutual Fund
    if user_id not in investments_db:
         investments_db[user_id] = {"gold_grams": 0.0, "mutual_funds": []}
    
    investments_db[user_id]["mutual_funds"].append({
        "fund_name": purchase.fund_name,
        "amount": purchase.amount,
        "date": datetime.utcnow(),
        "is_sip": purchase.is_sip
    })
    
    transaction = {
        "transaction_id": str(uuid.uuid4()),
        "from_account": purchase.account_number,
        "to_account": "MF_HOUSE",
        "amount": purchase.amount,
        "description": f"Invested in {purchase.fund_name}",
        "timestamp": datetime.utcnow(),
        "type": "debit"
    }
    transactions_db.append(transaction)

    await manager.broadcast(json.dumps({"type": "balance_update", "account": purchase.account_number}))
    
    return {
        "message": "Investment successful",
        "new_balance": accounts_db[purchase.account_number]["balance"],
        "holdings": investments_db[user_id]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)