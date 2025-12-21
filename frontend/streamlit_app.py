import streamlit as st
import requests
import json
import websocket
import threading
import time
from datetime import datetime
import pandas as pd
import altair as alt
import random

# Configuration
API_BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"
USD_TO_INR = 84.00

# Page configuration
st.set_page_config(
    page_title="DummyBank",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .balance {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2ecc71;
    }
    .account-number {
        font-size: 1.2rem;
        color: #7f8c8d;
    }
    .investment-card {
        background-color: #fff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .gold-price {
        font-size: 2rem;
        color: #f1c40f;
        font-weight: bold;
    }
    .risk-meter-high {
        color: #e74c3c;
        font-weight: bold;
    }
    .risk-meter-moderate {
        color: #f39c12;
        font-weight: bold;
    }
    .risk-meter-low {
        color: #2ecc71;
        font-weight: bold;
    }
    .biller-icon {
        font-size: 2rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'ws_connected' not in st.session_state:
    st.session_state.ws_connected = False
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()

def api_request(endpoint, method="GET", data=None):
    """Make API request with authentication"""
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = f"Status code: {response.status_code}"
            st.error(f"Error: {error_detail}")
            return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None
    
def get_user_profile():
    return api_request("/api/user/profile")

def update_user_profile(data):
    return api_request("/api/user/profile", "PUT", data)

# WebSocket Helper (Simplified for Streamlit)
def convert_currency(amount_usd):
    return amount_usd * USD_TO_INR

def format_currency(amount, currency="USD"):
    if currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"₹{convert_currency(amount):,.2f}"

def login_page():
    """Login page"""
    st.markdown("<h1 class='main-header'>🏦 DummyBank</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Your Trusted Banking Partner</h3>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            username = st.text_input("Username", value="demo")
            password = st.text_input("Password", type="password", value="demo123")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                response = api_request("/api/login", "POST", {
                    "username": username,
                    "password": password
                })
                
                if response:
                    st.session_state.token = response["token"]
                    st.session_state.user_id = response["user_id"]
                    st.session_state.username = response["username"]
                    st.success("Login successful!")
                    st.rerun()
        
        st.info("💡 Demo credentials: username=demo, password=demo123")
    
    with tab2:
        st.subheader("Create New Account")
        with st.form("register_form"):
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_full_name = st.text_input("Full Name")
            new_mobile = st.text_input("Mobile Number")
            new_password = st.text_input("Password", type="password")
            new_password_confirm = st.text_input("Confirm Password", type="password")
            submit_register = st.form_submit_button("Register", use_container_width=True)
            
            if submit_register:
                if new_password != new_password_confirm:
                    st.error("Passwords do not match!")
                elif not all([new_username, new_email, new_full_name, new_password]):
                    st.error("Please fill all fields!")
                else:
                    response = api_request("/api/register", "POST", {
                        "username": new_username,
                        "email": new_email,
                        "full_name": new_full_name,
                        "mobile_number": new_mobile,
                        "password": new_password
                    })
                    
                    if response:
                        st.session_state.token = response["token"]
                        st.session_state.user_id = response["user_id"]
                        st.session_state.username = new_username
                        st.success("Registration successful!")
                        st.rerun()

def dashboard_page():
    """Main dashboard"""
    # Fetch latest profile for greeting
    profile_data = get_user_profile()
    display_name = st.session_state.username
    if profile_data and "user" in profile_data:
        display_name = profile_data["user"].get("full_name") or st.session_state.username

    st.markdown(f"<h1 class='main-header'>Welcome back, {display_name}! 👋</h1>", unsafe_allow_html=True)
    
    # Get accounts
    accounts_data = api_request("/api/accounts")
    
    if accounts_data and accounts_data.get("accounts"):
        accounts = accounts_data["accounts"]
        
        # Display accounts
        st.subheader("Your Accounts")
        
        currency_view = st.radio("Currency View", ["INR", "USD"], horizontal=True)
        
        for account in accounts:
            with st.container():
                st.markdown(f"<div class='card'>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown(f"**Account Number:** {account['account_number']}")
                    st.markdown(f"**Type:** {account['account_type']}")
                
                with col2:
                    balance_display = format_currency(account['balance'], currency_view)
                    st.markdown(f"<div class='balance'>{balance_display}</div>", unsafe_allow_html=True)
                
                with col3:
                    st.markdown("**Status:** ✅ Active")
                st.markdown("</div>", unsafe_allow_html=True)
        
        st.divider()
        
        # Quick actions
        st.subheader("Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            with st.form("deposit_form"):
                st.markdown("### 💰 Deposit")
                account_number = st.selectbox("Select Account", [acc["account_number"] for acc in accounts], key="deposit_acc")
                amount = st.number_input(f"Amount ({currency_view})", min_value=0.01, step=0.01, key="deposit_amt")
                
                if st.form_submit_button("Deposit", use_container_width=True):
                    # Convert to USD for backend if INR selected
                    amount_usd = amount / USD_TO_INR if currency_view == "INR" else amount
                    
                    response = api_request("/api/deposit", "POST", {
                        "account_number": account_number,
                        "amount": amount_usd
                    })
                    
                    if response:
                        st.success(f"✅ Deposited {format_currency(amount_usd, currency_view)}! New balance: {format_currency(response['new_balance'], currency_view)}")
                        time.sleep(1)
                        st.rerun()
        
        with col2:
            with st.form("withdraw_form"):
                st.markdown("### 💸 Withdraw")
                account_number = st.selectbox("Select Account", [acc["account_number"] for acc in accounts], key="withdraw_acc")
                amount = st.number_input(f"Amount ({currency_view})", min_value=0.01, step=0.01, key="withdraw_amt")
                
                if st.form_submit_button("Withdraw", use_container_width=True):
                     # Convert to USD for backend if INR selected
                    amount_usd = amount / USD_TO_INR if currency_view == "INR" else amount

                    response = api_request("/api/withdraw", "POST", {
                        "account_number": account_number,
                        "amount": amount_usd
                    })
                    
                    if response:
                        st.success(f"✅ Withdrew {format_currency(amount_usd, currency_view)}! New balance: {format_currency(response['new_balance'], currency_view)}")
                        time.sleep(1)
                        st.rerun()
        
        with col3:
            st.markdown("### 🔄 Transfer")
            
            # Favorites (Outside Form)
            st.write("Favorites:")
            col_fav1, col_fav2 = st.columns(2)
            
            # Directly update the widget key 'to_acc_input'
            if col_fav1.button("❤️ Mom", use_container_width=True):
                st.session_state.to_acc_input = "ACCMOM123"
            if col_fav2.button("💙 Dad", use_container_width=True):
                st.session_state.to_acc_input = "ACCDAD456"

            with st.form("transfer_form"):
                from_account = st.selectbox("From Account", [acc["account_number"] for acc in accounts], key="from_acc")
                
                # Input key matches the one we updated above
                to_account = st.text_input("To Account Number", key="to_acc_input")
                
                amount = st.number_input(f"Amount ({currency_view})", min_value=0.01, step=0.01, key="transfer_amt")
                description = st.text_input("Description (optional)", key="transfer_desc")
                
                if st.form_submit_button("Transfer", use_container_width=True):
                    # Use the widget value directly
                    final_to_account = to_account
                    if not final_to_account:
                        st.error("Please enter a destination account number.")
                    else:
                        # Convert to USD for backend if INR selected
                        amount_usd = amount / USD_TO_INR if currency_view == "INR" else amount

                        response = api_request("/api/transfer", "POST", {
                            "from_account": from_account,
                            "to_account": final_to_account,
                            "amount": amount_usd,
                            "description": description
                        })
                        
                        if response:
                            st.success(f"✅ Transferred {format_currency(amount_usd, currency_view)}! New balance: {format_currency(response['new_balance'], currency_view)}")
                            time.sleep(1)
                            st.rerun()
        
        st.divider()
        
        # Recent transactions
        st.subheader("Recent Transactions")
        
        if accounts:
            account_for_transactions = accounts[0]["account_number"]
            transactions_data = api_request(f"/api/transactions/{account_for_transactions}")
            
            if transactions_data and transactions_data.get("transactions"):
                transactions = sorted(
                    transactions_data["transactions"],
                    key=lambda x: x["timestamp"],
                    reverse=True
                )[:10]
                
                for trans in transactions:
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 2])
                    
                    with col1:
                        timestamp = datetime.fromisoformat(trans["timestamp"].replace("Z", "")) 
                        st.write(timestamp.strftime("%Y-%m-%d %H:%M"))
                    
                    with col2:
                        st.write(trans["description"])
                    
                    with col3:
                        amt_display = format_currency(trans['amount'], currency_view)
                        if trans["to_account"] == account_for_transactions:
                            st.markdown(f"<span style='color: green;'>+{amt_display}</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<span style='color: red;'>-{amt_display}</span>", unsafe_allow_html=True)
                    
                    with col4:
                        st.tag = st.write(f"Type: {trans['type']}")
                    
                    st.divider()
            else:
                st.info("No transactions yet")

def bill_payments_page():
    """Bill Payments Page"""
    st.markdown("<h1 class='main-header'>🧾 Bill Payments</h1>", unsafe_allow_html=True)
    
    # Get user accounts for payment
    accounts_data = api_request("/api/accounts")
    if not accounts_data or not accounts_data.get("accounts"):
        st.error("No accounts found. Please contact support.")
        return
    accounts = accounts_data["accounts"]
    
    # Categories
    st.subheader("Categories")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='biller-icon'>💡</div>", unsafe_allow_html=True)
        if st.button("Utilities", key="cat_util", use_container_width=True):
            st.session_state.bill_cat = "Utilities"
    with col2:
        st.markdown("<div class='biller-icon'>💳</div>", unsafe_allow_html=True)
        if st.button("Credit Cards", key="cat_cc", use_container_width=True):
            st.session_state.bill_cat = "Credit Cards"
    with col3:
        st.markdown("<div class='biller-icon'>🛡️</div>", unsafe_allow_html=True)
        if st.button("Insurance", key="cat_ins", use_container_width=True):
            st.session_state.bill_cat = "Insurance"
    with col4:
        st.markdown("<div class='biller-icon'>📺</div>", unsafe_allow_html=True)
        if st.button("Subscriptions", key="cat_sub", use_container_width=True):
            st.session_state.bill_cat = "Subscriptions"
            
    selected_cat = st.session_state.get("bill_cat", "Utilities")
    st.markdown(f"### Pay {selected_cat}")
    
    # Mock Billers
    billers = {
        "Utilities": ["BESCOM (Electricity)", "BWSSB (Water)", "Indane Gas", "Mahanagar Gas"],
        "Credit Cards": ["HDFC Bank CC", "SBI Card", "ICICI Bank CC", "Amex"],
        "Insurance": ["LIC", "HDFC Life", "ICICI Prudential", "Star Health"],
        "Subscriptions": ["Netflix", "Amazon Prime", "Hotstar", "Spotify"]
    }
    
    # Auto-fill logic based on category
    # Fetch real user profile for mobile number
    profile_data = get_user_profile()
    real_mobile = "1234567890" # Default fallback
    if profile_data and "user" in profile_data:
        real_mobile = profile_data["user"].get("mobile_number", "1234567890")

    user_consumer_data = {
        "Utilities": real_mobile,
        "Credit Cards": "4321 8765 2109 5678",
        "Insurance": "POL-98765432",
        "Subscriptions": "user@subscription.com"
    }

    st.markdown("### Quick Pay")
    col_search, col_pay = st.columns([1, 2])
    
    with col_search:
        biller_name = st.selectbox("Select Biller", billers.get(selected_cat, []))
        
        # Auto-fill default value
        default_consumer_id = user_consumer_data.get(selected_cat, "")
        consumer_id = st.text_input("Consumer Number / Policy No / Mobile", value=default_consumer_id)
        
        # Fetch Bill button
        if st.button("Fetch Bill", use_container_width=True):
            if consumer_id:
                st.session_state.fetched_bill = True
                # Mock bill amounts based on biller
                bill_amounts = {
                    "BESCOM (Electricity)": random.randint(800, 2500),
                    "BWSSB (Water)": random.randint(300, 800),
                    "Indane Gas": random.randint(600, 1200),
                    "Mahanagar Gas": random.randint(500, 1500),
                    "HDFC Bank CC": random.randint(5000, 25000),
                    "SBI Card": random.randint(3000, 20000),
                    "ICICI Bank CC": random.randint(4000, 22000),
                    "Amex": random.randint(8000, 35000),
                    "LIC": random.randint(2000, 8000),
                    "HDFC Life": random.randint(1500, 6000),
                    "ICICI Prudential": random.randint(1800, 7000),
                    "Star Health": random.randint(2500, 9000),
                    "Netflix": 649,
                    "Amazon Prime": 1499,
                    "Hotstar": 1499,
                    "Spotify": 119
                }
                st.session_state.bill_amount = bill_amounts.get(biller_name, 500.0)
                st.session_state.due_date = "2025-12-25"
            else:
                st.error("Please enter Consumer Number first")
        
        # Show fetched bill details
        if st.session_state.get('fetched_bill', False):
            st.success("✅ Bill Fetched Successfully!")
            st.info(f"**Bill Amount:** ₹{st.session_state.bill_amount:,.2f}")
            st.info(f"**Due Date:** {st.session_state.due_date}")
        
    with col_pay:
             with st.form("bill_pay_form"):
                st.write(f"Paying **{biller_name}**")
                pay_account = st.selectbox("Pay From", [acc["account_number"] for acc in accounts], format_func=lambda x: f"{x} (Bal: ₹{convert_currency(next((a['balance'] for a in accounts if a['account_number'] == x), 0)):,.2f})")
                
                # Use fetched amount or allow manual entry
                if st.session_state.get('fetched_bill', False):
                    bill_amount = st.number_input("Bill Amount (₹)", min_value=1.0, value=float(st.session_state.bill_amount))
                else:
                    bill_amount = st.number_input("Bill Amount (₹)", min_value=1.0, value=500.0)
                
                if st.form_submit_button("Pay Bill", use_container_width=True):
                     if not consumer_id:
                         st.error("Please enter Consumer Number")
                     else:
                        # Convert approx INR to USD logic again
                        amount_usd = bill_amount / USD_TO_INR
                        response = api_request("/api/withdraw", "POST", {
                            "account_number": pay_account,
                            "amount": amount_usd,
                            "description": f"Bill Payment: {biller_name} - {consumer_id}"
                        })
                        
                        if response:
                            st.success(f"✅ Paid ₹{bill_amount:.2f} to {biller_name}!")
                            st.balloons()
                            # Clear fetched bill
                            st.session_state.fetched_bill = False
                            time.sleep(2)
                            st.rerun()

def profile_page():
    """User Profile Page"""
    st.markdown("<h1 class='main-header'>👤 My Profile</h1>", unsafe_allow_html=True)
    
    profile_data = get_user_profile()
    if profile_data and "user" in profile_data:
        user = profile_data["user"]
        
        with st.container():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.image("https://img.icons8.com/color/480/user-male-circle--v1.png", width=150)

            
            with col2:
                st.subheader("Personal Details")
                
                with st.form("profile_update_form"):
                    full_name = st.text_input("Full Name", value=user.get("full_name", ""))
                    email = st.text_input("Email", value=user.get("email", ""))
                    mobile = st.text_input("Mobile Number", value=user.get("mobile_number", ""))
                    
                    if st.form_submit_button("Update Profile", use_container_width=True):
                        # Move response variable initialization here
                        response = None
                        response = update_user_profile({
                            "full_name": full_name,
                            "email": email,
                            "mobile_number": mobile
                        })
                        
                        if response:
                            st.success("✅ Profile Updated Successfully!")
                            time.sleep(1)
                            st.rerun()
                            
            st.markdown("</div>", unsafe_allow_html=True)
            
        # Account Details Section
        st.subheader("Account Details")
        accounts_data = api_request("/api/accounts")
        if accounts_data and accounts_data.get("accounts"):
             for account in accounts_data["accounts"]:
                st.info(f"🏦 Account Number: **{account['account_number']}** ({account['account_type']})")


def investment_page():
    """Investment Page"""
    st.markdown("<h1 class='main-header'>📈 Investments</h1>", unsafe_allow_html=True)
    
    # Get user accounts for payment
    accounts_data = api_request("/api/accounts")
    if not accounts_data or not accounts_data.get("accounts"):
        st.error("No accounts found. Please contact support.")
        return
    accounts = accounts_data["accounts"]
    
    # Get Holdings
    holdings_data = api_request("/api/invest/holdings")
    holdings = holdings_data.get("holdings", {}) if holdings_data else {}
    
    st.sidebar.markdown("### Your Portfolio")
    st.sidebar.markdown(f"**Gold:** {holdings.get('gold_grams', 0):.2f} g")
    mf_count = len(holdings.get('mutual_funds', []))
    st.sidebar.markdown(f"**Mutual Funds:** {mf_count} Active")

    tab1, tab2 = st.tabs(["🟡 Digital Gold", "📊 Mutual Funds"])
    
    # --- Digital Gold Section ---
    with tab1:
        st.subheader("Buy Digital Gold")
        
        # Live Price Ticker
        price_data = api_request("/api/market/gold-price")
        if price_data:
            current_price = price_data["price"]
            st.metric(label="Current Gold Price (per gram)", value=f"₹{current_price:,.2f}", delta=f"{random.uniform(-50, 50):.2f}")
        else:
            st.error("Could not fetch gold price")
            current_price = 6500.00

        with st.container():
            st.markdown("<div class='investment-card'>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            with col1:
                buy_mode = st.radio("Buy By", ["Amount (₹)", "Weight (grams)"])
                
                pay_account = st.selectbox("Pay From", [acc["account_number"] for acc in accounts], format_func=lambda x: f"{x} (Bal: ₹{convert_currency(next((a['balance'] for a in accounts if a['account_number'] == x), 0)):,.2f})")
                
                if buy_mode == "Amount (₹)":
                    amount_inr = st.number_input("Enter Amount (₹)", min_value=100.0)
                    grams = amount_inr / current_price
                    st.info(f"You will get approx: {grams:.4f} grams")
                else:
                    grams = st.number_input("Enter Grams", min_value=0.01)
                    amount_inr = grams * current_price
                    st.info(f"Total Cost: ₹{amount_inr:,.2f}")
                
                terms = st.checkbox("I agree to the Terms & Conditions")
                
                if st.button("Buy Gold", disabled=not terms, use_container_width=True):
                    if not terms:
                        st.error("Please accept T&C")
                    else:
                        # Convert INR cost to USD for checking balance
                        cost_usd = amount_inr / USD_TO_INR
                        
                        # Direct purchase without confirmation modal
                        response = api_request("/api/invest/gold/buy", "POST", {
                            "account_number": pay_account,
                            "grams": grams,
                            "price_per_gram": cost_usd / grams
                        })
                        
                        if response:
                            st.success(f"✅ Successfully bought {grams:.4f}g Gold for ₹{amount_inr:,.2f}!")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()

            with col2:
                st.image("https://img.icons8.com/color/480/gold-bars.png", caption="99.9% Pure Digital Gold", width=200)
                st.markdown("""
                *   ✅ **24K Pure Gold**
                *   ✅ **Secure Storage**
                *   ✅ **Instant Liquidity**
                """)
            st.markdown("</div>", unsafe_allow_html=True)

    # --- Mutual Funds Section ---
    with tab2:
        st.subheader("Mutual Funds Marketplace")
        
        search = st.text_input("🔍 Search Funds", placeholder="e.g. HDFC, SBI, Axis...")
        
        # Dummy Mutual Funds Data
        funds = [
            {"name": "HDFC Top 100 Fund", "risk": "High", "return": "15.4%", "category": "Equity"},
            {"name": "SBI Bluechip Fund", "risk": "Moderate", "return": "12.1%", "category": "Hybrid"},
            {"name": "Axis Small Cap Fund", "risk": "High", "return": "22.5%", "category": "Equity"},
            {"name": "ICICI Prudential Liquid Fund", "risk": "Low", "return": "6.8%", "category": "Debt"},
        ]
        
        if search:
            funds = [f for f in funds if search.lower() in f["name"].lower()]
        
        for fund in funds:
            with st.expander(f"{fund['name']} - {fund['category']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    risk_class = f"risk-meter-{fund['risk'].lower()}"
                    st.markdown(f"Risk: <span class='{risk_class}'>{fund['risk']}</span>", unsafe_allow_html=True)
                    st.markdown(f"3Y Return: **{fund['return']}**")
                    
                    # Riskometer Visual
                    st.progress(0.9 if fund['risk'] == "High" else 0.5 if fund['risk'] == "Moderate" else 0.2)
                    st.caption("Riskometer")
                    
                    st.download_button("📄 Download Scheme Document", "Dummy PDF Content", file_name=f"{fund['name']}_SID.pdf")

                with col2:
                    st.write("Fund Manager: John Doe")
                    st.write("NAV: ₹45.23")
                
                with col3:
                    invest_type = st.radio(f"Invest In {fund['name']}", ["SIP", "Lump Sum"], key=f"type_{fund['name']}")
                    invest_amt_inr = st.number_input(f"Amount (₹) for {fund['name']}", min_value=500.0, key=f"amt_{fund['name']}")
                    pay_acc_mf = st.selectbox(f"Pay From for {fund['name']}", [acc["account_number"] for acc in accounts], key=f"pay_{fund['name']}")
                    
                    if st.button(f"Invest Now {fund['name']}"):
                         # Convert to USD
                        amt_usd = invest_amt_inr / USD_TO_INR
                        
                        response = api_request("/api/invest/mutual-funds/buy", "POST", {
                            "account_number": pay_acc_mf,
                            "fund_name": fund['name'],
                            "amount": amt_usd,
                            "is_sip": invest_type == "SIP"
                        })
                        
                        if response:
                            st.balloons()
                            st.success(f"Successfully invested in {fund['name']}!")
                            time.sleep(2)
                            st.rerun()

def main():
    """Main application"""
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/bank-building.png", width=100)
        st.title("DummyBank")
        st.divider()
        
        if st.session_state.token:
            st.success(f"Logged in as: {st.session_state.username}")
            
            nav = st.radio("Navigation", ["Dashboard", "Bill Payments", "Investments", "Profile"])
            
            st.divider()
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.token = None
                st.session_state.user_id = None
                st.session_state.username = None
                st.rerun()
            
        else:
            st.info("Please login to access your account")
            nav = "Login"
    
    # Main content
    if st.session_state.token:
        if nav == "Dashboard":
            dashboard_page()
        elif nav == "Investments":
            investment_page()
        elif nav == "Bill Payments":
            bill_payments_page()
        elif nav == "Profile":
            profile_page()
    else:
        login_page()

if __name__ == "__main__":
    main()