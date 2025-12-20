import os
import json
import re
from typing import Dict, Any
from pathlib import Path
from langchain_google_vertexai import ChatVertexAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv
from app.models import AgentAction, ActionType, RiskLevel

# Load environment variables
load_dotenv()


class VisionBrain:
    """
    The Vision-Language Model brain that analyzes screenshots
    and decides what actions to take using Vertex AI
    """
    
    def __init__(self):
        """Initialize the Vertex AI Gemini model"""
        # Get project ID and location from environment
        project_id = os.getenv("VERTEX_AI_PROJECT", "gigshield")
        location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        
        print(f"🔑 Initializing Vertex AI Gemini...")
        print(f"   Project: {project_id}")
        print(f"   Location: {location}")
        
        # Initialize Vertex AI
        try:
            import vertexai
            vertexai.init(project=project_id, location=location)
            
            # Use ChatVertexAI with gemini-2.5-pro
            self.llm = ChatVertexAI(
                model_name="gemini-2.5-pro",
                project=project_id,
                location=location,
                temperature=0.1,
            )
            print(f"✅ Successfully initialized Vertex AI gemini-2.5-pro")
        except Exception as e:
            print(f"❌ Failed to initialize Vertex AI: {e}")
            print(f"   Make sure:")
            print(f"   1. Vertex AI API is enabled")
            print(f"   2. Billing is enabled on project: {project_id}")
            print(f"   3. You have proper authentication")
            raise ValueError(
                f"Failed to initialize Vertex AI.\\n"
                f"Error: {str(e)}\\n"
                f"Enable Vertex AI: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com"
            )
        
        self.system_prompt = """You are FinAgent Sentinel, an advanced autonomous web automation agent specializing in financial workflows.
Your core function is to visually analyze web page screenshots and generate precise, executable Playwright instructions to complete a user's objective.

### 1. VISUAL ANALYSIS & SELECTOR STRATEGY (CRITICAL)
Modern banking sites use dynamic/obfuscated CSS (e.g., "css-1234"). DO NOT rely solely on simple classes/IDs.
Prioritize selectors in this specific order of reliability:
1.  **Text Content:** If a button says "Login", use `button:has-text("Login")` or `text=Login`.
2.  **Accessibility Roles:** If an input has a label "Username", use `[placeholder="Username"]` or `[aria-label="Username"]`.
3.  **Specific Attributes:** `input[type="password"]`, `button[type="submit"]`.
4.  **CSS Classes/IDs:** Only use these if they look semantic and stable (e.g., `#login-btn`, `.login-btn`, `#invest-gold-btn`). AVOID dynamic strings like `.css-x7y8`.

### 2. RISK ASSESSMENT PROTOCOL ("THE CONSCIOUS PAUSE")
You are the first line of defense. You MUST identify High-Risk actions.
* **HIGH RISK:** Any action that moves money, commits to a purchase, or finalizes a transaction.
    * **Logic:** If clicking this button results in a financial deduction, `risk_level` is "HIGH".
    * **Keywords:** "Pay", "Transfer", "Buy", "Invest", "Confirm", "Submit Payment", "Send", "Purchase", "Submit", "Execute", "Finalize", "Complete Transaction", "Withdraw", "Deposit", "Send Money".
* **LOW RISK:** Navigation, typing data (even amounts), clicking "Next", "Continue", login buttons, or selecting options.

### 3. NAVIGATION & PATIENCE
* **Loading States:** If you see a spinner, a "Loading..." overlay, skeleton UI, or disabled buttons, you MUST return `action: "wait"`.
* **Popups/Modals:** If a promotional popup obscures the main content, your action is to close it (look for 'X', 'Close', or 'No Thanks') unless it's critical to the task.
* **Task Completion:** If the screen shows "Success", "Transaction Complete", or a receipt, return `action: "done"`.

### 4. PLAYWRIGHT COMPATIBILITY RULES
* **YES:** Use `:has-text()` for text matching: `button:has-text("Login")`
* **YES:** Use `text=` for exact text: `text=Login`
* **YES:** Use attribute selectors: `button[type="submit"]`, `.login-btn`, `#invest-gold-btn`
* **NO:** `:contains()` pseudo-classes (not supported by Playwright)
* **NO:** XPath unless absolutely necessary
* **PREFER:** Readable selectors. `button:has-text("Sign In")` is better than `.btn-primary`.

### 5. COMMON BANK DASHBOARD PATTERNS
When you see a dashboard with cards/buttons:
* **"Invest in Gold" button:** Try `#invest-gold-btn`, `text=Invest in Gold`, `.gold-card`, or `.action-card:has-text("Invest in Gold")`
* **Login button:** Try `button:has-text("Login")`, `.login-btn`, or `button[type="submit"]`
* **Amount input:** Try `input[type="number"]`, `[placeholder*="amount"]`, `#amount`, or `input[placeholder*="Amount"]`
* **Submit/Buy buttons:** Try `button:has-text("Buy")`, `button:has-text("Confirm")`, `.buy-btn`, or `#buy-btn`
* **Card-based buttons:** Look for clickable cards with class `.action-card` or specific IDs

### 6. STRICT JSON OUTPUT FORMAT
You must output PURE JSON. No markdown, no "Here is the JSON", no backticks.
Format:
{
    "action": "click" | "type" | "wait" | "done" | "navigate",
    "selector": "The Playwright-compatible selector string (null for wait/done)",
    "value": "The EXACT text to type (only for 'type' action, else null)",
    "reasoning": "A concise, step-by-step logic for your decision (e.g., 'Found Amount field, typing 500')",
    "risk_level": "HIGH" | "LOW",
    "confidence": 0.0 to 1.0 (Float)
}

EXAMPLES:
- Login button: {"action": "click", "selector": "button:has-text('Login')", "reasoning": "Clicking login button to proceed", "risk_level": "LOW", "confidence": 0.95}
- Invest in Gold: {"action": "click", "selector": "#invest-gold-btn", "reasoning": "Clicking gold investment card", "risk_level": "LOW", "confidence": 0.9}
- Submit button: {"action": "click", "selector": "button[type='submit']", "reasoning": "Submitting the form", "risk_level": "LOW", "confidence": 0.9}
- Username field: {"action": "type", "selector": "#username", "value": "demo", "reasoning": "Entering username", "risk_level": "LOW", "confidence": 0.9}
- Buy button: {"action": "click", "selector": "button:has-text('Buy Gold')", "reasoning": "Executing purchase - requires approval", "risk_level": "HIGH", "confidence": 0.85}
- Loading spinner visible: {"action": "wait", "selector": null, "reasoning": "Page is loading, waiting for completion", "risk_level": "LOW", "confidence": 0.8}
"""
    
    def analyze_screenshot(self, screenshot_base64: str, task: str, current_url: str = "") -> AgentAction:
        """
        Analyze a screenshot and determine the next action using Vertex AI Gemini.
        Includes robust JSON parsing with markdown stripping.
        
        Args:
            screenshot_base64: Base64 encoded screenshot
            task: The task the agent is trying to accomplish
            current_url: Current page URL for context
            
        Returns:
            AgentAction object with the next action to take
        """
        try:
            from langchain.schema import HumanMessage
            import re
            
            # Construct the prompt
            user_prompt = f"""{self.system_prompt}

USER TASK: {task}
CURRENT URL: {current_url}

Analyze the image and provide the JSON response."""
            
            # Create message with image
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": user_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{screenshot_base64}"
                        }
                    }
                ]
            )
            
            # Get response from Gemini
            response = self.llm.invoke([message])
            content = response.content.strip()
            
            print(f"🤖 Gemini response: {content[:200]}...")  # Print first 200 chars
            
            # ROBUST JSON PARSING: Strip markdown code blocks
            if "```" in content:
                # Match ```json ... ``` or ``` ... ```
                pattern = r"```(?:json)?(.*?)```"
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    content = match.group(1).strip()
            
            # Parse JSON
            action_dict = json.loads(content)
            
            # SAFETY: Double-check risk level based on keywords
            # Expanded keywords to match different banking sites (including localhost:8501)
            high_risk_keywords = [
                "buy", "pay", "transfer", "confirm", "invest", "purchase", "send money",
                "submit", "execute", "finalize", "withdraw", "deposit", "complete",
                "send", "transaction", "payment"
            ]
            selector_str = str(action_dict.get("selector", "")).lower()
            reasoning_str = str(action_dict.get("reasoning", "")).lower()
            
            if any(keyword in selector_str or keyword in reasoning_str for keyword in high_risk_keywords):
                action_dict["risk_level"] = "HIGH"
                print(f"⚠️  Risk override: Detected high-risk keyword in selector/reasoning")
            
            # Validate and create AgentAction
            action = AgentAction(
                action=ActionType(action_dict["action"]),
                selector=action_dict.get("selector"),
                value=action_dict.get("value"),
                reasoning=action_dict["reasoning"],
                risk_level=RiskLevel(action_dict["risk_level"]),
                confidence=action_dict.get("confidence", 0.5)
            )
            
            return action
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"📄 Response was: {content}")
            # Return a safe fallback action
            return AgentAction(
                action=ActionType.WAIT,
                reasoning=f"JSON parsing failed. Model returned invalid format. Retrying...",
                risk_level=RiskLevel.LOW,
                confidence=0.0
            )
        except Exception as e:
            print(f"❌ CRITICAL ERROR in analyze_screenshot: {e}")
            import traceback
            traceback.print_exc()
            return AgentAction(
                action=ActionType.WAIT,
                reasoning=f"System error: {str(e)}",
                risk_level=RiskLevel.LOW,
                confidence=0.0
            )


# Singleton instance
_brain_instance = None

def get_brain() -> VisionBrain:
    """Get or create the singleton brain instance"""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = VisionBrain()
    return _brain_instance
