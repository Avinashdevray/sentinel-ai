# 🚀 Vertex AI Setup - Final Steps

## ✅ **Code Updated!**

Your FinAgent Sentinel now uses **Vertex AI** instead of the standard Gemini API!

---

## 📋 **Complete These 3 Steps:**

### **Step 1: Enable Vertex AI API**

Visit this URL and click "Enable":
```
https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=gigshield
```

Or run in terminal:
```bash
# If you have gcloud CLI installed
gcloud services enable aiplatform.googleapis.com --project=gigshield
```

---

### **Step 2: Set Up Authentication**

#### **Option A: Using gcloud CLI** (Recommended)

1. **Install gcloud CLI** (if not installed):
   ```bash
   # For Mac
   brew install --cask google-cloud-sdk
   
   # Or download from:
   # https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate:**
   ```bash
   gcloud auth application-default login
   ```

3. **Set project:**
   ```bash
   gcloud config set project gigshield
   ```

#### **Option B: Using Service Account** (Alternative)

1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts?project=gigshield
2. Click "Create Service Account"
3. Name: `finagent-sentinel`
4. Grant role: **Vertex AI User**
5. Click "Create Key" → JSON
6. Download the JSON file
7. Save it as: `/Users/avinashdevray/finagent_sentinel/backend/service-account.json`
8. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/Users/avinashdevray/finagent_sentinel/backend/service-account.json"
   ```

---

### **Step 3: Update Project ID (if needed)**

If your project ID is NOT `gigshield`, update `.env`:

```bash
cd /Users/avinashdevray/finagent_sentinel
nano backend/.env
```

Change `VERTEX_AI_PROJECT=gigshield` to your actual project ID.

---

## 🚀 **Start the Backend**

Once authentication is set up:

```bash
cd /Users/avinashdevray/finagent_sentinel/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## ✅ **Verify It's Working**

You should see:
```
🔑 Initializing Vertex AI Gemini...
   Project: gigshield
   Location: us-central1
✅ Successfully initialized Vertex AI gemini-1.5-flash
```

---

## 🎯 **Then Test!**

1. Open: http://localhost:3000
2. Enter task:
   ```
   Login with username 'demo' and password 'password', then invest 500 rupees in gold
   ```
3. Click "Start Task"
4. **IT WILL WORK!** 🎉

---

## 💰 **Benefits of Vertex AI:**

✅ **Higher quotas** - No more 429 errors  
✅ **Uses your $300 credits**  
✅ **Better for production**  
✅ **More reliable**  
✅ **Same billing account**  

---

## ❓ **Troubleshooting**

### **"Vertex AI API not enabled"**
- Visit: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
- Click "Enable"
- Wait 2-3 minutes

### **"Authentication error"**
- Make sure you completed Step 2
- Try: `gcloud auth application-default login`
- Or use service account method

### **"Project not found"**
- Update `VERTEX_AI_PROJECT` in `.env` to your actual project ID
- Find it at: https://console.cloud.google.com/

---

## 🎉 **You're Almost There!**

Just complete the 3 steps above and your agent will work immediately!

**No more quota issues!** 🚀
