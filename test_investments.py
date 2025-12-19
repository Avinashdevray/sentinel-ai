import requests
import json

API_BASE_URL = "http://localhost:8000"

def test_investments():
    # Login as demo
    login_resp = requests.post(f"{API_BASE_URL}/api/login", json={"username": "demo", "password": "demo123"})
    if login_resp.status_code != 200:
        print("Login failed")
        return
    
    token = login_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get Account
    acc_resp = requests.get(f"{API_BASE_URL}/api/accounts", headers=headers)
    account_number = acc_resp.json()["accounts"][0]["account_number"]
    
    # Test Gold Price
    price_resp = requests.get(f"{API_BASE_URL}/api/market/gold-price")
    print(f"Gold Price: {price_resp.json()}")
    
    # Buy Gold
    buy_gold_resp = requests.post(f"{API_BASE_URL}/api/invest/gold/buy", json={
        "account_number": account_number,
        "grams": 1.0,
        "price_per_gram": 75.0 # USD approx
    }, headers=headers)
    print(f"Buy Gold Response: {buy_gold_resp.json()}")
    
    # Buy Mutual Fund
    buy_mf_resp = requests.post(f"{API_BASE_URL}/api/invest/mutual-funds/buy", json={
        "account_number": account_number,
        "fund_name": "Test Fund",
        "amount": 100.0,
        "is_sip": False
    }, headers=headers)
    print(f"Buy MF Response: {buy_mf_resp.json()}")
    
    # Check Holdings
    holdings_resp = requests.get(f"{API_BASE_URL}/api/invest/holdings", headers=headers)
    print(f"Holdings: {holdings_resp.json()}")

if __name__ == "__main__":
    test_investments()
