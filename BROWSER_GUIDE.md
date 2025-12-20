# 🌐 Browser Configuration Guide

## Available Browsers

Your FinAgent Sentinel now supports **4 different browsers**:

| Browser | Code | Description |
|---------|------|-------------|
| 🔵 **Chromium** | `chromium` | Default, lightweight |
| 🦊 **Firefox** | `firefox` | Mozilla Firefox |
| 🧭 **WebKit** | `webkit` | Safari engine (Mac only) |
| 🌐 **Chrome** | `chrome` | Google Chrome (if installed) |

---

## How to Change Browser

### **Option 1: Edit .env File** (Recommended)

Edit `/Users/avinashdevray/finagent_sentinel/backend/.env`:

```env
# Change this line:
BROWSER_TYPE=firefox

# Or use:
# BROWSER_TYPE=webkit
# BROWSER_TYPE=chrome
# BROWSER_TYPE=chromium
```

Then **restart the backend** (it will auto-reload).

---

### **Option 2: Environment Variable** (Temporary)

Set the environment variable before starting:

```bash
# For Firefox
export BROWSER_TYPE=firefox
cd /Users/avinashdevray/finagent_sentinel/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Browser Features Comparison

### **Chromium** (Default)
- ✅ Lightweight
- ✅ Fast
- ✅ Best Playwright support
- ❌ Looks like a "test browser"

### **Firefox** 
- ✅ Real browser experience
- ✅ Good privacy
- ✅ Familiar UI
- ⚠️  Slightly slower

### **WebKit** (Safari)
- ✅ Native Mac experience
- ✅ Best for Mac users
- ✅ Apple ecosystem
- ❌ Mac only

### **Chrome**
- ✅ Most popular browser
- ✅ Full Google integration
- ✅ Familiar to most users
- ⚠️  Requires Chrome installed

---

## Quick Test

1. **Edit `.env`** and set `BROWSER_TYPE=firefox`
2. **Restart backend** (auto-reloads)
3. **Start a task** in the dashboard
4. **Watch Firefox open** instead of Chromium!

---

## Troubleshooting

### "Browser not found"
If you get an error, install the browser:

```bash
cd /Users/avinashdevray/finagent_sentinel/backend
source venv/bin/activate

# Install Firefox
playwright install firefox

# Install WebKit
playwright install webkit

# Chrome uses system installation
```

### "Channel not found" (Chrome)
Make sure Google Chrome is installed on your system. If not, use `chromium` instead.

---

## Current Setup

Your current configuration:
- **Default**: Chromium
- **Location**: `backend/.env`
- **Change**: Edit `BROWSER_TYPE=` line

---

**Enjoy testing with different browsers!** 🚀
