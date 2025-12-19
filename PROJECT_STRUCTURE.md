#!/usr/bin/env python3
"""
DummyBank API Test Script
This script tests all the API endpoints
"""

import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60 + "\n")

def print_response(response):
    """Pretty print API response"""
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_api():
    """Test all API endpoints"""
    
    print_section("DummyBank API Test Suite")
    print(f"Testing API at: {API_BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Test 1: Root endpoint
    print_section("1. Testing Root Endpoint")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print_response(response)
    except Exception as e:
        print(f"❌ Error: {e}\n")
        print("Make sure the backend is running: cd backend && python main.py")
        return
    
    # Test 2: Login
    print_section("2. Testing Login (Demo User)")
    login_data = {
        "username": "demo",
        "password": "demo123"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/login", json=login_data)
        print_response(response)
        
        if response.status_code == 200:
            token = response.json()["token"]
            user_id = response.json()["user_id"]
            print(f"✅ Login successful!")
            print(f"Token: {token[:20]}...")
        else:
            print("❌ Login failed!")
            return
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return
    
    # Headers for authenticated requests
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 3: Get User Profile
    print_section("3. Testing Get User Profile")
    try:
        response = requests.get(f"{API_BASE_URL}/api/user/profile", headers=headers)
        print_response(response)
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Test 4: Get Accounts
    print_section("4. Testing Get Accounts")
    try:
        response = requests.get(f"{API_BASE_URL}/api/accounts", headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            accounts = response.json()["accounts"]
            if accounts:
                account_number = accounts[0]["account_number"]
                initial_balance = accounts[0]["balance"]
                print(f"✅ Found {len(accounts)} account(s)")
                print(f"Using account: {account_number}")
                print(f"Initial balance: ${initial_balance:.2f}\n")
            else:
                print("❌ No accounts found!")
                return
        else:
            return
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return
    
    # Test 5: Get Account Details
    print_section("5. Testing Get Account Details")
    try:
        response = requests.get(f"{API_BASE_URL}/api/account/{account_number}", headers=headers)
        print_response(response)
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Test 6: Deposit
    print_section("6. Testing Deposit")
    deposit_data = {
        "account_number": account_number,
        "amount": 500.00
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/deposit", json=deposit_data, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            new_balance = response.json()["new_balance"]
            print(f"✅ Deposit successful!")
            print(f"New balance: ${new_balance:.2f}\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Test 7: Withdraw
    print_section("7. Testing Withdrawal")
    withdraw_data = {
        "account_number": account_number,
        "amount": 200.00
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/withdraw", json=withdraw_data, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            new_balance = response.json()["new_balance"]
            print(f"✅ Withdrawal successful!")
            print(f"New balance: ${new_balance:.2f}\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Test 8: Get Transactions
    print_section("8. Testing Get Transactions")
    try:
        response = requests.get(f"{API_BASE_URL}/api/transactions/{account_number}", headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            transactions = response.json()["transactions"]
            print(f"✅ Found {len(transactions)} transaction(s)\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Test 9: Register New User
    print_section("9. Testing User Registration")
    register_data = {
        "username": f"testuser_{datetime.now().timestamp()}",
        "email": "testuser@example.com",
        "full_name": "Test User",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/register", json=register_data)
        print_response(response)
        
        if response.status_code == 200:
            new_token = response.json()["token"]
            new_account = response.json()["account_number"]
            print(f"✅ Registration successful!")
            print(f"New account: {new_account}\n")
            
            # Test 10: Transfer (using new account)
            print_section("10. Testing Transfer")
            
            # First, deposit to new account
            deposit_new = {
                "account_number": new_account,
                "amount": 1000.00
            }
            headers_new = {"Authorization": f"Bearer {new_token}"}
            requests.post(f"{API_BASE_URL}/api/deposit", json=deposit_new, headers=headers_new)
            
            # Now transfer to original account
            transfer_data = {
                "from_account": new_account,
                "to_account": account_number,
                "amount": 100.00,
                "description": "Test transfer"
            }
            
            response = requests.post(f"{API_BASE_URL}/api/transfer", json=transfer_data, headers=headers_new)
            print_response(response)
            
            if response.status_code == 200:
                print(f"✅ Transfer successful!\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Summary
    print_section("Test Summary")
    print("✅ All tests completed!")
    print("Check the responses above for any errors.")
    print("\nYou can now access:")
    print("  • API Docs: http://localhost:8000/docs")
    print("  • Streamlit: http://localhost:8501")
    print("  • HTML App: http://localhost:8080")
    print()

if __name__ == "__main__":
    test_api()