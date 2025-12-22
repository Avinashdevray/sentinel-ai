import os
import json
import re
from typing import Dict, Any
from pathlib import Path
from langchain_google_vertexai import ChatVertexAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

from app.models import AgentAction, ActionType, RiskLevel
from app.guardian_prompts import GUARDIAN_SYSTEM_PROMPT, QUICKLOAN_WORKFLOW_PROMPT

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

### 2. RISK ASSESSMENT PROTOCOL (CRITICAL - "THE CONSCIOUS PAUSE")
You are the first line of defense. You MUST correctly identify High-Risk vs Low-Risk actions.

**HIGH RISK - ONLY FINAL TRANSACTION ACTIONS:**
* Actions that IMMEDIATELY execute a financial transaction or money movement
* **Keywords that indicate FINAL action:** "Buy", "Pay Now", "Transfer", "Withdraw", "Send Money", "Purchase", "Execute Trade", "Complete Payment", "Confirm Purchase"
* **Logic:** If clicking this button will IMMEDIATELY deduct money or complete a transaction, `risk_level` is "HIGH"
* **Examples:** 
  - "Buy Gold" button on payment page → HIGH
  - "Pay Now" button → HIGH
  - "Transfer Funds" button → HIGH
  - "Confirm Purchase" button → HIGH

**LOW RISK - ALL PREPARATORY ACTIONS:**
* Login, navigation, typing data, selecting options, clicking "Next", "Continue", "Submit" (for forms)
* **Includes:** Logging in, entering amounts, clicking investment cards, navigating to payment pages, filling forms
* **Keywords that are LOW risk:** "Login", "Sign In", "Next", "Continue", "Submit" (form submission), "Invest in Gold" (navigation), "Enter Amount"
* **Logic:** If the action is preparing for a transaction but NOT executing it, `risk_level` is "LOW"
* **Examples:**
  - "Login" button → LOW
  - Typing username/password → LOW
  - Clicking "Invest in Gold" card (navigation) → LOW
  - Entering amount in a field → LOW
  - "Submit" button on a form (not payment) → LOW
  - "Continue" or "Next" buttons → LOW

**CRITICAL DISTINCTION:**
- Clicking a card/button to NAVIGATE to an investment page = LOW RISK
- Clicking the FINAL "Buy" or "Pay" button on that page = HIGH RISK

### 3. NAVIGATION & PATIENCE
* **Loading States:** If you see a spinner, a "Loading..." overlay, skeleton UI, or disabled buttons, you MUST return `action: "wait"`.
* **Popups/Modals:** If a promotional popup obscures the main content, your action is to close it (look for 'X', 'Close', or 'No Thanks') unless it's critical to the task.
* **Task Completion:** If the screen shows "Success", "Transaction Complete", or a receipt, return `action: "done"`.

### 4. GUARDIAN ANGEL PROTOCOL (FOR LOAN/TRAP SITES)
When the user asks for a loan or visits a potential trap site (like QuickLoan Pro), you switch to Guardian Angel mode.
You MUST follow the specific workflow defined in the prompt.
- Detect false urgency timers (Timer resets = Fake)
- Detect drip pricing (Hidden fees)
- Detect forced continuity (Terms & Conditions)
- Pause for User Approval on HIGH/CRITICAL risks (Checkout, Virtual Card generation)

{GUARDIAN_SYSTEM_PROMPT}

If the task involves "QuickLoan" or "get me a loan":
{QUICKLOAN_WORKFLOW_PROMPT}


### 4. PLAYWRIGHT COMPATIBILITY RULES (CRITICAL)
**SELECTOR PRIORITY ORDER (use in this order):**
1. **text= (most reliable):** `text=Login`, `text=Buy Gold`
2. **:has-text() with button:** `button:has-text("Login")`, `button:has-text("Buy")`
3. **Attribute selectors:** `button[type="submit"]`, `input[type="number"]`
4. **ID/Class (only if stable):** `#login-btn`, `.buy-btn`

**IMPORTANT:** Always prefer `text=` over `:has-text()` for better reliability.

**Examples:**
- ✅ GOOD: `text=Login`, `text=Buy Gold`, `text=Continue`
- ✅ GOOD: `button:has-text("Login")` (fallback)
- ❌ AVOID: Complex CSS selectors like `.css-1234`, `.MuiButton-root`
- ❌ NO: `:contains()` (not supported by Playwright)
- ❌ NO: XPath unless absolutely necessary

### 5. COMMON BANK DASHBOARD PATTERNS
When you see a dashboard with cards/buttons:
* **Login form (CRITICAL - READ CAREFULLY):** If you see a login form with username and password fields already filled:
  1. **MANDATORY FIRST STEP:** Click on the password field (`#login-password` or `input[type="password"]`) to ensure focus
  2. **MANDATORY SECOND STEP:** Use action "press" with value "Enter" to submit
  3. **DO NOT click the Login button directly** - this often fails due to JavaScript handlers
  4. **Only if above fails:** Try `button[type="submit"]` as last resort
* **"Invest in Gold" button:** Try `text=Invest in Gold`, `#invest-gold-btn`, `.gold-card` → LOW RISK (navigation)
* **Amount input:** Try `input[type="number"]`, `[placeholder*="amount"]`, `#amount` → LOW RISK
* **Buy/Pay buttons:** Try `text=Buy Gold`, `text=Pay Now`, `.buy-btn` → HIGH RISK (final action)
* **Card-based buttons:** Look for clickable cards with class `.action-card` or specific IDs → LOW RISK (navigation)

**CRITICAL LOGIN RULE:** NEVER click the Login button directly when credentials are pre-filled. ALWAYS click password field first, then press Enter. This is the ONLY reliable method.

### 6. STRICT JSON OUTPUT FORMAT
You must output PURE JSON. No markdown, no "Here is the JSON", no backticks.

Format:
{
    "action": "click" | "type" | "press" | "wait" | "done" | "navigate",
    "selector": "The Playwright-compatible selector string (null for wait/done/press)",
    "value": "The EXACT text to type (for 'type') OR key name to press (for 'press', e.g., 'Enter')",
    "reasoning": "Brief explanation of why this action",
    "risk_level": "LOW" | "MEDIUM" | "HIGH"
}

**CRITICAL LOGIN EXAMPLE:**
When you see a pre-filled login form, your FIRST action must be:
{
    "action": "click",
    "selector": "input[type='password']",
    "value": null,
    "reasoning": "Clicking password field to ensure focus before submitting login form",
    "risk_level": "LOW"
}

Then on the NEXT turn (after screenshot), output:
{
    "action": "press",
    "selector": null,
    "value": "Enter",
    "reasoning": "Submitting login form by pressing Enter with password field focused",
    "risk_level": "LOW"
}

**DO NOT output click on Login button for pre-filled forms!**

EXAMPLES:
- Press Enter to login: {"action": "press", "selector": null, "value": "Enter", "reasoning": "Submitting login form by pressing Enter with password field focused", "risk_level": "LOW", "confidence": 0.95}
- Login button: {"action": "click", "selector": "text=Login", "reasoning": "Clicking login button to proceed", "risk_level": "LOW", "confidence": 0.95}
- Invest in Gold card: {"action": "click", "selector": "text=Invest in Gold", "reasoning": "Clicking gold investment card to navigate", "risk_level": "LOW", "confidence": 0.9}
- Submit form: {"action": "click", "selector": "button[type='submit']", "reasoning": "Submitting the login form", "risk_level": "LOW", "confidence": 0.9}
- Username field: {"action": "type", "selector": "#username", "value": "demo", "reasoning": "Entering username", "risk_level": "LOW", "confidence": 0.9}
- Amount field: {"action": "type", "selector": "input[type='number']", "value": "500", "reasoning": "Entering investment amount", "risk_level": "LOW", "confidence": 0.9}
- Buy button: {"action": "click", "selector": "text=Buy Gold", "reasoning": "FINAL ACTION: Executing purchase - requires approval", "risk_level": "HIGH", "confidence": 0.85}
- Pay button: {"action": "click", "selector": "text=Pay Now", "reasoning": "FINAL ACTION: Completing payment - requires approval", "risk_level": "HIGH", "confidence": 0.9}
- Loading spinner visible: {"action": "wait", "selector": null, "reasoning": "Page is loading, waiting for completion", "risk_level": "LOW", "confidence": 0.8}
"""
    
    def analyze_screenshot(self, screenshot_base64: str, task: str, current_url: str = "", recent_actions: list = None) -> AgentAction:
        """
        Analyze a screenshot and determine the next action using Vertex AI Gemini.
        Includes robust JSON parsing with markdown stripping.
        
        Args:
            screenshot_base64: Base64 encoded screenshot
            task: The task the agent is trying to accomplish
            current_url: Current page URL for context
            recent_actions: List of recent actions taken (for context)
            
        Returns:
            AgentAction object with the next action to take
        """
        try:
            from langchain.schema import HumanMessage
            import re
            
            # Add recent actions to prompt if available
            action_context = ""
            if recent_actions:
                action_context = "\n\nRECENT ACTIONS TAKEN:\n" + "\n".join(recent_actions)
                action_context += "\n\n⚠️ IMPORTANT: Do NOT repeat the same action. If you just clicked something, the page should have changed. Look for new elements or fields that appeared."
            
            # Construct the prompt
            user_prompt = f"""{self.system_prompt}

USER TASK: {task}
CURRENT URL: {current_url}{action_context}

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
            # Only FINAL transaction actions are high risk
            # Focus on button text and explicit action reasoning
            
            selector_str = str(action_dict.get("selector", "")).lower()
            reasoning_str = str(action_dict.get("reasoning", "")).lower()
            action_type = action_dict.get("action", "")
            
            # Only check for high-risk keywords in button clicks
            if action_type == "click":
                # High-risk button text patterns (must be in selector)
                high_risk_button_patterns = [
                    "buy gold", "buy now", "pay now", "pay ", "transfer funds",
                    "withdraw", "send money", "purchase now", "confirm purchase",
                    "complete payment", "execute trade", "finalize"
                ]
                
                # Check if selector contains high-risk button text
                is_high_risk_button = any(pattern in selector_str for pattern in high_risk_button_patterns)
                
                # Also check reasoning for explicit "FINAL ACTION" marker or high-risk intent
                is_final_action = "final action" in reasoning_str.lower() or "executing purchase" in reasoning_str.lower()
                
                if is_high_risk_button or is_final_action:
                    action_dict["risk_level"] = "HIGH"
                    print(f"⚠️  Risk override: Detected high-risk transaction button")
                else:
                    # Ensure it stays LOW risk for preparatory actions
                    if action_dict.get("risk_level") == "HIGH":
                        # Check if it's actually a preparatory action
                        low_risk_indicators = [
                            "login", "sign in", "navigate", "clicking", "entering",
                            "typing", "filling", "selecting", "checkbox", "agree"
                        ]
                        if any(indicator in reasoning_str for indicator in low_risk_indicators):
                            action_dict["risk_level"] = "LOW"
                            print(f"✓ Risk downgrade: Detected preparatory action")

            
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
