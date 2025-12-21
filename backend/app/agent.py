import asyncio
import base64
import time
from typing import TypedDict, Annotated, Literal, Optional
from langgraph.graph import StateGraph, END
from playwright.async_api import async_playwright, Page, Browser
from app.brain import get_brain
from app.models import AgentAction, ActionType, RiskLevel
from app.utils import encode_image_to_base64, resize_image_if_needed
from app.validator import LogicValidator
from app.exceptions import InsufficientFundsError, InvalidAmountError, BalanceExtractionError
import operator


class GraphState(TypedDict):
    """State for the LangGraph agent"""
    messages: Annotated[list[str], operator.add]
    screenshot: str
    next_action: dict
    status: Literal["RUNNING", "PAUSED", "DONE", "ERROR"]
    current_url: str
    task: str
    retry_count: int
    max_retries: int
    page_handle: object  # Will store the Playwright page
    browser_handle: object  # Will store the browser instance
    message_callback: object  # Callback function to send messages in real-time
    tried_login_methods: list  # Track which login methods have been tried
    extracted_balance: Optional[str]  # Balance extracted from page for validation
    validation_passed: bool  # Whether validation passed


class FinAgentGraph:
    """
    LangGraph-based agent that uses vision to navigate websites
    """
    
    def __init__(self):
        self.brain = get_brain()
        self.validator = LogicValidator()
        self.graph = self._build_graph()
        self.playwright = None
        self.browser = None
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("navigator", self.navigator_node)
        workflow.add_node("brain", self.brain_node)
        workflow.add_node("logic_validator", self.logic_validator_node)  # NEW: Validator node
        workflow.add_node("safety_valve", self.safety_valve_node)
        workflow.add_node("executor", self.executor_node)
        
        # Set entry point
        workflow.set_entry_point("navigator")
        
        # Add edges
        workflow.add_edge("navigator", "brain")
        workflow.add_edge("brain", "logic_validator")  # NEW: Brain -> Validator
        
        # Conditional edges from validator
        workflow.add_conditional_edges(
            "logic_validator",
            self.route_from_validator,
            {
                "safety_valve": "safety_valve",  # Validation passed
                "error": END  # Validation failed
            }
        )
        
        # Conditional edges from safety_valve
        workflow.add_conditional_edges(
            "safety_valve",
            self.route_from_safety,
            {
                "executor": "executor",
                "pause": END,
                "done": END
            }
        )
        
        # Conditional edges from executor
        workflow.add_conditional_edges(
            "executor",
            self.route_from_executor,
            {
                "navigator": "navigator",  # Retry loop
                "done": END,
                "error": END
            }
        )
        
        return workflow.compile()
    
    async def _send_message(self, state: GraphState, message: str):
        """Helper to send a message both to state and via callback (async version)"""
        state["messages"].append(message)
        if state.get("message_callback"):
            try:
                await state["message_callback"](message)
            except Exception as e:
                print(f"Error sending message via callback: {e}")
    
    async def navigator_node(self, state: GraphState) -> GraphState:
        """
        Node 1: Navigate and capture screenshot
        """
        try:
            page = state.get("page_handle")
            
            if page is None:
                # First run - initialize browser
                await self._send_message(state, "🚀 Initializing browser...")
                return state
            
            # Memory optimization: Keep only last 20 messages
            if len(state["messages"]) > 20:
                state["messages"] = state["messages"][-20:]
            
            # Capture screenshot
            screenshot_bytes = await page.screenshot(full_page=False)
            resized = resize_image_if_needed(screenshot_bytes, max_size=1024)
            screenshot_b64 = encode_image_to_base64(resized)
            
            # Store only current screenshot (don't accumulate)
            state["screenshot"] = screenshot_b64
            
            # Update current URL
            state["current_url"] = page.url
            
            await self._send_message(state, f"📸 Captured screenshot of {page.url}")
            
            return state
            
        except Exception as e:
            state["status"] = "ERROR"
            await self._send_message(state, f"❌ Navigator error: {str(e)}")
            return state
    
    async def brain_node(self, state: GraphState) -> GraphState:
        """
        Node 2: Analyze screenshot with Vision AI
        """
        try:
            await self._send_message(state, "🧠 Analyzing screenshot with Gemini Vision...")
            
            # Get recent action history for context (last 3 actions)
            recent_actions = []
            if state.get("next_action"):
                prev_action = state["next_action"]
                action_desc = f"{prev_action.get('action')} on {prev_action.get('selector') or prev_action.get('value')}"
                recent_actions.append(f"Previous action: {action_desc}")
            
            action = self.brain.analyze_screenshot(
                screenshot_base64=state["screenshot"],
                task=state["task"],
                current_url=state["current_url"],
                recent_actions=recent_actions
            )
            
            # Check if this is the same action as last time (stuck in loop)
            prev_action = state.get("next_action") or {}
            current_action_type = action.action.value
            current_selector = action.selector
            current_value = action.value
            
            prev_action_type = prev_action.get("action")
            prev_selector = prev_action.get("selector")
            prev_value = prev_action.get("value")
            
            # Detect repeated actions (both click and press)
            is_repeated_action = False
            if current_action_type == prev_action_type:
                if current_action_type == "click" and current_selector == prev_selector:
                    # Same click action repeated
                    is_repeated_action = True
                elif current_action_type == "press" and current_value == prev_value:
                    # Same press action repeated
                    is_repeated_action = True
            
            if is_repeated_action:
                state["retry_count"] += 1
                await self._send_message(state, f"⚠️ Repeated action detected: {current_action_type} on {current_selector or current_value} (attempt {state['retry_count']})")
                
                # If we've repeated the same action 2+ times, force a wait to let page update
                if state["retry_count"] >= 2:
                    await self._send_message(state, "🔄 Breaking loop: Forcing wait for page to update")
                    action = AgentAction(
                        action=ActionType.WAIT,
                        selector=None,
                        value=None,
                        reasoning="Breaking out of repeated action loop - waiting for page to update",
                        risk_level=RiskLevel.LOW,
                        confidence=0.8
                    )
                    state["retry_count"] = 0  # Reset after forcing wait
            else:
                # Different action - reset retry count
                state["retry_count"] = 0
            
            state["next_action"] = action.model_dump()
            await self._send_message(state,
                f"💡 Decision: {action.action.value} | "
                f"Risk: {action.risk_level.value} | "
                f"Reasoning: {action.reasoning}"
            )
            
            return state
            
        except Exception as e:
            state["status"] = "ERROR"
            await self._send_message(state, f"❌ Brain error: {str(e)}")
            return state
    
    async def logic_validator_node(self, state: GraphState) -> GraphState:
        """
        Node 2.5: NEURO-SYMBOLIC LOGIC VALIDATOR
        
        This node performs deterministic validation of financial actions:
        1. Extracts balance from page (if needed)
        2. Validates transaction amounts
        3. Checks affordability constraints
        4. Calculates percentage-based amounts
        
        This is the "Spock" layer - pure logic, no AI guessing.
        """
        try:
            action = state["next_action"]
            action_type = action.get("action")
            
            # Skip validation for non-financial actions
            if action_type in ["wait", "done", "navigate"]:
                state["validation_passed"] = True
                await self._send_message(state, "✓ Non-financial action - validation skipped")
                return state
            
            # Check if this is a financial action
            if not self.validator.is_financial_action(action):
                state["validation_passed"] = True
                await self._send_message(state, "✓ Non-financial action - validation skipped")
                return state
            
            await self._send_message(state, "🔍 Validating financial transaction...")
            
            # Extract balance from page (if not already extracted)
            page = state.get("page_handle")
            if page and not state.get("extracted_balance"):
                try:
                    balance_str = await self.validator.extract_balance_from_page(page)
                    state["extracted_balance"] = balance_str
                    await self._send_message(state, f"💰 Extracted balance: {balance_str}")
                except BalanceExtractionError as e:
                    # Balance extraction failed - this might be okay for non-payment pages
                    await self._send_message(state, f"⚠️ Could not extract balance: {str(e)}")
                    # Continue without validation if we can't find balance
                    state["validation_passed"] = True
                    return state
            
            # Extract transaction amount from action
            amount = self.validator.extract_amount_from_action(action)
            
            if amount is None:
                # No amount found - might be a navigation action
                state["validation_passed"] = True
                await self._send_message(state, "✓ No transaction amount detected - validation skipped")
                return state
            
            await self._send_message(state, f"💵 Transaction amount: {amount}")
            
            # Check if amount is percentage-based
            value_str = str(action.get("value", ""))
            if "%" in value_str or "percent" in value_str.lower():
                try:
                    calculated_amount = self.validator.calculate_dynamic_amount(
                        action,
                        state["extracted_balance"]
                    )
                    await self._send_message(
                        state,
                        f"📊 Calculated {value_str} = {calculated_amount:.2f}"
                    )
                    amount = calculated_amount
                except Exception as e:
                    state["status"] = "ERROR"
                    await self._send_message(state, f"❌ Percentage calculation failed: {str(e)}")
                    state["validation_passed"] = False
                    return state
            
            # Validate affordability
            if state.get("extracted_balance"):
                try:
                    is_affordable, balance_decimal, amount_decimal = self.validator.validate_affordability(
                        state["extracted_balance"],
                        amount
                    )
                    
                    if is_affordable:
                        state["validation_passed"] = True
                        await self._send_message(
                            state,
                            f"✅ Validation passed: {amount_decimal} ≤ {balance_decimal}"
                        )
                    else:
                        # This shouldn't happen as validate_affordability raises exception
                        state["status"] = "ERROR"
                        state["validation_passed"] = False
                        await self._send_message(state, "❌ Affordability check failed")
                        
                except InsufficientFundsError as e:
                    state["status"] = "ERROR"
                    state["validation_passed"] = False
                    await self._send_message(
                        state,
                        f"❌ INSUFFICIENT FUNDS: Required {e.required_amount:.2f}, "
                        f"Available {e.available_balance:.2f}"
                    )
                    return state
                    
                except InvalidAmountError as e:
                    state["status"] = "ERROR"
                    state["validation_passed"] = False
                    await self._send_message(state, f"❌ INVALID AMOUNT: {str(e)}")
                    return state
            else:
                # No balance available - proceed with caution
                state["validation_passed"] = True
                await self._send_message(
                    state,
                    "⚠️ Balance not available - proceeding without affordability check"
                )
            
            return state
            
        except Exception as e:
            state["status"] = "ERROR"
            state["validation_passed"] = False
            await self._send_message(state, f"❌ Validation error: {str(e)}")
            return state
    
    async def safety_valve_node(self, state: GraphState) -> GraphState:
        """
        Node 3: CRITICAL - Safety check before execution
        """
        try:
            action = state["next_action"]
            risk_level = action.get("risk_level")
            action_type = action.get("action")
            
            # Check if action is DONE
            if action_type == "done":
                state["status"] = "DONE"
                await self._send_message(state, "✅ Task completed successfully!")
                return state
            
            # Check risk level
            if risk_level == "HIGH":
                state["status"] = "PAUSED"
                await self._send_message(state, "⚠️ HIGH RISK ACTION DETECTED - Pausing for human approval")
                return state
            
            # Low risk - proceed
            await self._send_message(state, "✓ Low risk action - proceeding")
            return state
            
        except Exception as e:
            state["status"] = "ERROR"
            await self._send_message(state, f"❌ Safety valve error: {str(e)}")
            return state
    
    async def executor_node(self, state: GraphState) -> GraphState:
        """
        Node 4: Execute the action
        """
        try:
            page = state.get("page_handle")
            action = state["next_action"]
            action_type = action.get("action")
            selector = action.get("selector")
            value = action.get("value")
            
            await self._send_message(state, f"⚡ Executing: {action_type}")
            
            if action_type == "click":
                # Try multiple selector strategies for better reliability
                selectors_to_try = [selector]
                
                # Add fallback selectors for common patterns
                if "login" in selector.lower() or "submit" in selector.lower():
                    selectors_to_try.extend([
                        "button[type='submit']",
                        "text=Login",
                        "button:has-text('Login')"
                    ])
                
                clicked = False
                last_error = None
                
                for sel in selectors_to_try:
                    try:
                        await page.wait_for_selector(sel, timeout=5000)
                        await page.click(sel)
                        await self._send_message(state, f"✓ Clicked: {sel}")
                        state["retry_count"] = 0
                        clicked = True
                        
                        # CRITICAL: Auto-press Enter after clicking password field on login-like pages
                        current_url = page.url.lower()
                        url_path = current_url.split('/')[-1] if '/' in current_url else ''
                        is_login_page = (
                            url_path == '' or  # Root page
                            url_path == 'login' or
                            'login' in current_url or
                            'signin' in current_url or
                            'auth' in current_url or
                            current_url.endswith('/')  # Root with trailing slash
                        )
                        
                        if "password" in sel.lower() and is_login_page:
                            await asyncio.sleep(0.3)  # Brief pause to ensure focus
                            await page.keyboard.press("Enter")
                            await self._send_message(state, "✓ Auto-pressed Enter after password field click")
                            await asyncio.sleep(1)  # Wait for form submission
                        
                        break
                    except Exception as e:
                        last_error = e
                        continue
                
                if not clicked:
                    raise last_error if last_error else Exception(f"Could not find element: {selector}")
                
            elif action_type == "type":
                await page.wait_for_selector(selector, timeout=5000)
                await page.fill(selector, value)
                await self._send_message(state, f"✓ Typed '{value}' into: {selector}")
                state["retry_count"] = 0
                await asyncio.sleep(0.3)  # Brief pause after typing
                
            elif action_type == "press":
                # Press a key (e.g., Enter)
                await page.keyboard.press(value)
                await self._send_message(state, f"✓ Pressed key: {value}")
                
                # Track that we've tried pressing Enter (for login fallback)
                if value == "Enter" and "press_enter" not in state.get("tried_login_methods", []):
                    tried_methods = state.get("tried_login_methods", [])
                    tried_methods.append("press_enter")
                    state["tried_login_methods"] = tried_methods
                
                state["retry_count"] = 0
                # Wait for form submission to complete
                await asyncio.sleep(1)
                
            elif action_type == "wait":
                await self._send_message(state, "⏳ Waiting for page to load...")
                await asyncio.sleep(1)
                state["retry_count"] = 0
                
            elif action_type == "navigate":
                url = value
                page.goto(url)
                state["messages"].append(f"✓ Navigated to: {url}")
                state["retry_count"] = 0
            
            # Wait a bit for page to update
            time.sleep(1)
            
            return state
            
        except Exception as e:
            state["retry_count"] += 1
            state["messages"].append(
                f"⚠️ Execution error (attempt {state['retry_count']}/{state['max_retries']}): {str(e)}"
            )
            
            if state["retry_count"] >= state["max_retries"]:
                state["status"] = "ERROR"
                state["messages"].append("❌ Max retries exceeded")
            
            return state
    
    def route_from_validator(self, state: GraphState) -> str:
        """Route from validator based on validation result"""
        if state.get("status") == "ERROR" or not state.get("validation_passed", True):
            return "error"
        else:
            return "safety_valve"
    
    def route_from_safety(self, state: GraphState) -> str:
        """Route from safety valve based on status"""
        status = state.get("status")
        
        if status == "PAUSED":
            return "pause"
        elif status == "DONE":
            return "done"
        else:
            return "executor"
    
    def route_from_executor(self, state: GraphState) -> str:
        """Route after execution with intelligent login fallback"""
        if state["status"] == "DONE":
            return "done"
        elif state["status"] == "ERROR":
            return "error"
        else:
            # Check if we're stuck on login with repeated press Enter
            page = state.get("page_handle")
            tried_methods = state.get("tried_login_methods", [])
            
            # If we've tried press_enter and we're still seeing press action, move to next method
            if (state.get("next_action", {}).get("action") == "press" and 
                "press_enter" in tried_methods and 
                page):
                
                # Method 2: Click password field + Press Enter
                if "password_field_enter" not in tried_methods:
                    self._send_message(state, "🔄 Method 1 failed. Trying Method 2: Focus password field + Enter")
                    tried_methods.append("password_field_enter")
                    state["tried_login_methods"] = tried_methods
                    
                    password_selectors = ["#login-password", "input[type='password']", "[name='password']"]
                    for sel in password_selectors:
                        try:
                            page.wait_for_selector(sel, timeout=2000)
                            page.click(sel)
                            self._send_message(state, f"✓ Focused: {sel}")
                            time.sleep(0.5)
                            page.keyboard.press("Enter")
                            self._send_message(state, "✓ Pressed Enter in password field")
                            state["retry_count"] = 0
                            time.sleep(2)
                            return "navigator"
                        except:
                            continue
                
                # Method 3: Click submit button
                elif "click_submit" not in tried_methods:
                    self._send_message(state, "🔄 Method 2 failed. Trying Method 3: Click submit button")
                    tried_methods.append("click_submit")
                    state["tried_login_methods"] = tried_methods
                    
                    submit_selectors = [
                        "button[type='submit']",
                        "text=Login",
                        "button:has-text('Login')",
                        ".btn-primary"
                    ]
                    for sel in submit_selectors:
                        try:
                            page.wait_for_selector(sel, timeout=2000)
                            page.click(sel)
                            self._send_message(state, f"✓ Clicked submit: {sel}")
                            state["retry_count"] = 0
                            time.sleep(2)
                            return "navigator"
                        except:
                            continue
                
                # All methods failed
                else:
                    self._send_message(state, "❌ All login methods exhausted")
                    state["status"] = "ERROR"
                    return "error"
            
            return "navigator"  # Continue to next iteration
    
    async def initialize_browser(self, start_url: str) -> tuple[Browser, Page]:
        """
        Initialize Playwright browser (async version)
        
        Supports: chromium (default), firefox, webkit (Safari), chrome
        Set BROWSER_TYPE env variable to change: export BROWSER_TYPE=firefox
        """
        import os
        
        self.playwright = await async_playwright().start()
        
        # Get browser type from environment variable (default: chromium)
        browser_type = os.getenv("BROWSER_TYPE", "chromium").lower()
        
        # Launch the appropriate browser
        if browser_type == "firefox":
            print("🦊 Launching Firefox...")
            self.browser = await self.playwright.firefox.launch(headless=False)
        elif browser_type == "webkit":
            print("🧭 Launching WebKit (Safari)...")
            self.browser = await self.playwright.webkit.launch(headless=False)
        elif browser_type == "chrome":
            print("🌐 Launching Google Chrome...")
            self.browser = await self.playwright.chromium.launch(
                headless=False,
                channel="chrome"  # Use installed Chrome
            )
        else:  # Default: chromium
            print("🔵 Launching Chromium...")
            self.browser = await self.playwright.chromium.launch(headless=False)
        
        context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        await page.goto(start_url)
        await asyncio.sleep(2)  # Wait for initial load
        
        # Verify connectivity - print page title
        try:
            page_title = await page.title()
            print(f"✅ Successfully connected to: {start_url}")
            print(f"📄 Page Title: {page_title}")
        except Exception as e:
            print(f"⚠️  Warning: Could not retrieve page title: {e}")
        
        return self.browser, page
    
    def cleanup_browser(self):
        """Clean up browser resources"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    async def run(self, task: str, start_url: str, message_callback=None) -> GraphState:
        """
        Run the agent to complete a task (async version)
        
        Args:
            task: The task to accomplish
            start_url: Starting URL
            message_callback: Optional callback function to send messages in real-time
            
        Returns:
            Final state
        """
        # Initialize browser
        browser, page = await self.initialize_browser(start_url)
        
        # Initial state
        initial_state = GraphState(
            messages=[],
            screenshot=None,
            next_action={},  # Changed from None to {} to prevent NoneType errors
            status="RUNNING",
            current_url=start_url,
            task=task,
            retry_count=0,
            max_retries=3,
            page_handle=page,
            browser_handle=browser,
            message_callback=message_callback,  # Store callback in state
            tried_login_methods=[],  # Track login methods
            extracted_balance=None,  # Balance for validation
            validation_passed=True  # Default to true
        )
        
        try:
            # Run the graph with increased recursion limit
            final_state = await self.graph.ainvoke(
                initial_state,
                config={"recursion_limit": 150}  # Increased for longer tasks
            )
            
            # Only cleanup if task is complete or errored, NOT if paused for approval
            if final_state["status"] in ["DONE", "ERROR"]:
                await browser.close()
                await self.playwright.stop()
            
            return final_state
        except Exception as e:
            # On error, cleanup
            await browser.close()
            await self.playwright.stop()
            raise e
    
    async def resume(self, state: GraphState) -> GraphState:
        """
        Resume execution after approval (async version)
        
        Args:
            state: Current state to resume from
            
        Returns:
            Updated state
        """
        # Change status back to RUNNING
        state["status"] = "RUNNING"
        await self._send_message(state, "✅ Approval received - resuming execution")
        
        # Continue from executor node
        try:
            # Execute the approved action
            state = await self.executor_node(state)
            
            # If successful, continue the loop
            if state["status"] != "ERROR":
                # Continue navigating
                while state["status"] == "RUNNING":
                    state = await self.navigator_node(state)
                    if state["status"] == "ERROR":
                        break
                    
                    state = await self.brain_node(state)
                    if state["status"] == "ERROR":
                        break
                    
                    state = await self.safety_valve_node(state)
                    if state["status"] in ["PAUSED", "DONE", "ERROR"]:
                        break
                    
                    state = await self.executor_node(state)
                    if state["status"] in ["DONE", "ERROR"]:
                        break
            
            return state
        except Exception as e:
            state["status"] = "ERROR"
            await self._send_message(state, f"❌ Resume error: {str(e)}")
            return state
