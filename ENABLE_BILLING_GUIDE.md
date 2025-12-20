# 💳 Enable Billing for Gemini API - Step-by-Step Guide

## 🎯 **Why Enable Billing?**

✅ **Unlimited API quota** - No more 429 errors  
✅ **Very cheap** - ~$0.01 for 100 requests  
✅ **$300 free credits** - Google Cloud gives you $300 to start  
✅ **Production-ready** - No interruptions  
✅ **Higher rate limits** - Millions of requests per day  

**Cost Example:**
- 1,000 agent tasks = ~$1-2
- Your testing today would have cost ~$0.50

---

## 📋 **Step-by-Step Instructions**

### **Step 1: Go to Google Cloud Console**

Open this link in your browser:
```
https://console.cloud.google.com/
```

Sign in with the **same Google account** you used to create your API key.

---

### **Step 2: Create or Select a Project**

1. Click the **project dropdown** at the top (next to "Google Cloud")
2. Either:
   - **Select existing project** (if you have one)
   - **Click "New Project"** to create one
3. If creating new:
   - Name: `finagent-sentinel` (or any name)
   - Click **"Create"**
   - Wait ~30 seconds for creation

---

### **Step 3: Enable Billing**

#### **Option A: If you see "Activate" button**
1. Look for **"Activate"** or **"Free Trial"** button at the top
2. Click it
3. Follow the prompts to set up billing

#### **Option B: Manual setup**
1. Go to: https://console.cloud.google.com/billing
2. Click **"Link a billing account"** or **"Create billing account"**
3. Fill in:
   - Country
   - Payment method (credit/debit card)
   - Billing address
4. **Important:** You get **$300 free credits** for 90 days!
5. Click **"Start my free trial"**

---

### **Step 4: Enable Generative AI API**

1. Go to: https://console.cloud.google.com/apis/library
2. Search for: **"Generative Language API"**
3. Click on **"Generative Language API"**
4. Click **"Enable"**
5. Wait ~30 seconds for activation

---

### **Step 5: Verify Billing is Active**

1. Go to: https://console.cloud.google.com/billing
2. You should see:
   - ✅ Billing account linked
   - ✅ $300 free credits available
   - ✅ Current usage: $0.00

---

### **Step 6: Get a New API Key (Optional but Recommended)**

Since your current keys are quota-limited, create a fresh one:

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click **"Create Credentials"** → **"API Key"**
3. Copy the new API key
4. Click **"Restrict Key"** (recommended):
   - **API restrictions** → Select **"Generative Language API"**
   - Click **"Save"**

**OR** use the simpler method:

1. Go to: https://aistudio.google.com/app/apikey
2. Click **"Create API Key"**
3. Select your **billing-enabled project**
4. Copy the key

---

### **Step 7: Update Your .env File**

Edit `/Users/avinashdevray/finagent_sentinel/backend/.env`:

```env
GOOGLE_API_KEY=your_new_billing_enabled_key_here
BANK_URL=http://localhost:8001
BROWSER_TYPE=chrome
```

---

### **Step 8: Restart Backend**

```bash
# Kill old backend (if running)
lsof -ti:8000 | xargs kill -9

# Start fresh backend
cd /Users/avinashdevray/finagent_sentinel/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## ✅ **Verification**

After setup, verify everything works:

1. **Check billing status:**
   - Go to: https://console.cloud.google.com/billing
   - Should show: Active billing account

2. **Check API status:**
   - Go to: https://console.cloud.google.com/apis/dashboard
   - Should show: Generative Language API enabled

3. **Test your agent:**
   - Open: http://localhost:3000
   - Run a task
   - Should work without quota errors!

---

## 💰 **Pricing Information**

### **Gemini 1.5 Flash (Recommended for your agent)**
- **Input:** $0.000075 per 1K characters
- **Output:** $0.0003 per 1K characters

### **Example Costs:**
| Usage | Approximate Cost |
|-------|------------------|
| 100 agent tasks | $0.50 - $1.00 |
| 1,000 agent tasks | $5.00 - $10.00 |
| 10,000 agent tasks | $50.00 - $100.00 |

### **Your Free Credits:**
- **$300 free** for 90 days
- Enough for **30,000 - 60,000 agent tasks**!

---

## 🛡️ **Set Up Budget Alerts (Recommended)**

Protect yourself from unexpected charges:

1. Go to: https://console.cloud.google.com/billing/budgets
2. Click **"Create Budget"**
3. Set:
   - **Budget amount:** $10 (or your preference)
   - **Alert threshold:** 50%, 90%, 100%
   - **Email notifications:** Your email
4. Click **"Finish"**

You'll get emails when you hit 50%, 90%, and 100% of your budget!

---

## 🔒 **Security Best Practices**

### **1. Restrict Your API Key:**
- Go to: https://console.cloud.google.com/apis/credentials
- Click on your API key
- Under **"API restrictions"**:
  - Select **"Restrict key"**
  - Choose **"Generative Language API"**
- Under **"Application restrictions"** (optional):
  - Select **"IP addresses"**
  - Add your server IP
- Click **"Save"**

### **2. Monitor Usage:**
- Check: https://console.cloud.google.com/apis/dashboard
- Review costs: https://console.cloud.google.com/billing

### **3. Set Quotas:**
- Go to: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
- Set custom limits if needed

---

## ❓ **Troubleshooting**

### **"Billing account not found"**
- Make sure you completed Step 3
- Wait 5-10 minutes for propagation
- Refresh the page

### **"API not enabled"**
- Complete Step 4
- Wait 2-3 minutes
- Try creating API key again

### **"Still getting quota errors"**
- Make sure you're using the **new API key** from the billing-enabled project
- Old keys won't automatically get higher quotas
- Restart your backend after updating .env

### **"Credit card declined"**
- Google requires a valid payment method
- They won't charge you during free trial
- Use a different card if needed

---

## 📞 **Support Links**

- **Billing Console:** https://console.cloud.google.com/billing
- **API Dashboard:** https://console.cloud.google.com/apis/dashboard
- **Pricing Calculator:** https://cloud.google.com/products/calculator
- **Support:** https://cloud.google.com/support

---

## 🎉 **After Setup**

Once billing is enabled:

1. ✅ **No more quota errors**
2. ✅ **Unlimited testing**
3. ✅ **Production-ready**
4. ✅ **$300 free credits**
5. ✅ **Peace of mind**

---

## 🚀 **Quick Start After Billing**

```bash
# 1. Update .env with new API key
# 2. Restart backend
cd /Users/avinashdevray/finagent_sentinel/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Open dashboard
open http://localhost:3000

# 4. Test your agent!
```

---

**Good luck! You'll have unlimited quota in about 10 minutes!** 🎯
