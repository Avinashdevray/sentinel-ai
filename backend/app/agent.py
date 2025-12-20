import asyncio
import time
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from playwright.sync_api import sync_playwright, Page, Browser
from app.brain import get_brain
from app.models import AgentAction, ActionType, RiskLevel
from app.utils import encode_image_to_base64, resize_image_if_needed
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


class FinAgentGraph:
    """
    LangGraph-based agent that uses vision to navigate websites
    """
    
    def __init__(self):
        self.brain = get_brain()
        self.graph = self._build_graph()
        self.playwright = None
        self.browser = None
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("navigator", self.navigator_node)
        workflow.add_node("brain", self.brain_node)
        workflow.add_node("safety_valve", self.safety_valve_node)
        workflow.add_node("executor", self.executor_node)
        
        # Set entry point
        workflow.set_entry_point("navigator")
        
        # Add edges
        workflow.add_edge("navigator", "brain")
        workflow.add_edge("brain", "safety_valve")
        
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
    
    def navigator_node(self, state: GraphState) -> GraphState:
        """
        Node 1: Navigate and capture screenshot
        """
        try:
            page = state.get("page_handle")
            
            if page is None:
                # First run - initialize browser
                state["messages"].append("🚀 Initializing browser...")
                return state
            
            # Wait for page to be stable
            time.sleep(1)
            
            # Capture screenshot
            screenshot_bytes = page.screenshot(full_page=False)
            resized = resize_image_if_needed(screenshot_bytes, max_size=1024)
            screenshot_b64 = encode_image_to_base64(resized)
            
            state["screenshot"] = screenshot_b64
            state["current_url"] = page.url
            state["messages"].append(f"📸 Captured screenshot of {page.url}")
            
            return state
            
        except Exception as e:
            state["status"] = "ERROR"
            state["messages"].append(f"❌ Navigator error: {str(e)}")
            return state
    
    def brain_node(self, state: GraphState) -> GraphState:
        """
        Node 2: Analyze screenshot with Vision AI
        """
        try:
            state["messages"].append("🧠 Analyzing screenshot with Gemini Vision...")
            
            action = self.brain.analyze_screenshot(
                screenshot_base64=state["screenshot"],
                task=state["task"],
                current_url=state["current_url"]
            )
            
            state["next_action"] = action.model_dump()
            state["messages"].append(
                f"💡 Decision: {action.action.value} | "
                f"Risk: {action.risk_level.value} | "
                f"Reasoning: {action.reasoning}"
            )
            
            return state
            
        except Exception as e:
            state["status"] = "ERROR"
            state["messages"].append(f"❌ Brain error: {str(e)}")
            return state
    
    def safety_valve_node(self, state: GraphState) -> GraphState:
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
                state["messages"].append("✅ Task completed successfully!")
                return state
            
            # Check risk level
            if risk_level == "HIGH":
                state["status"] = "PAUSED"
                state["messages"].append(
                    "⚠️ HIGH RISK ACTION DETECTED - Pausing for human approval"
                )
                return state
            
            # Low risk - proceed
            state["messages"].append("✓ Low risk action - proceeding")
            return state
            
        except Exception as e:
            state["status"] = "ERROR"
            state["messages"].append(f"❌ Safety valve error: {str(e)}")
            return state
    
    def executor_node(self, state: GraphState) -> GraphState:
        """
        Node 4: Execute the action
        """
        try:
            page = state.get("page_handle")
            action = state["next_action"]
            action_type = action.get("action")
            selector = action.get("selector")
            value = action.get("value")
            
            state["messages"].append(f"⚡ Executing: {action_type}")
            
            if action_type == "click":
                # Wait for element and click
                page.wait_for_selector(selector, timeout=5000)
                page.click(selector)
                state["messages"].append(f"✓ Clicked: {selector}")
                state["retry_count"] = 0  # Reset retry count on success
                
            elif action_type == "type":
                page.wait_for_selector(selector, timeout=5000)
                page.fill(selector, value)
                state["messages"].append(f"✓ Typed '{value}' into: {selector}")
                state["retry_count"] = 0
                
            elif action_type == "wait":
                state["messages"].append("⏳ Waiting for page to stabilize...")
                time.sleep(2)
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
        """Route from executor - retry loop or end"""
        status = state.get("status")
        
        if status == "ERROR":
            return "error"
        elif status == "DONE":
            return "done"
        else:
            # Continue the loop
            return "navigator"
    
    def initialize_browser(self, start_url: str) -> tuple[Browser, Page]:
        """
        Initialize Playwright browser
        
        Supports: chromium (default), firefox, webkit (Safari), chrome
        Set BROWSER_TYPE env variable to change: export BROWSER_TYPE=firefox
        """
        import os
        
        self.playwright = sync_playwright().start()
        
        # Get browser type from environment variable (default: chromium)
        browser_type = os.getenv("BROWSER_TYPE", "chromium").lower()
        
        # Launch the appropriate browser
        if browser_type == "firefox":
            print("🦊 Launching Firefox...")
            self.browser = self.playwright.firefox.launch(headless=False)
        elif browser_type == "webkit":
            print("🧭 Launching WebKit (Safari)...")
            self.browser = self.playwright.webkit.launch(headless=False)
        elif browser_type == "chrome":
            print("🌐 Launching Google Chrome...")
            self.browser = self.playwright.chromium.launch(
                headless=False,
                channel="chrome"  # Use installed Chrome
            )
        else:  # Default: chromium
            print("🔵 Launching Chromium...")
            self.browser = self.playwright.chromium.launch(headless=False)
        
        context = self.browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        page.goto(start_url)
        time.sleep(2)  # Wait for initial load
        
        # Verify connectivity - print page title
        try:
            page_title = page.title()
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
    
    def run(self, task: str, start_url: str) -> GraphState:
        """
        Run the agent graph
        
        Args:
            task: The task to accomplish
            start_url: Starting URL
            
        Returns:
            Final state
        """
        # Initialize browser
        browser, page = self.initialize_browser(start_url)
        
        # Initial state
        initial_state = GraphState(
            messages=[],
            screenshot="",
            next_action={},
            status="RUNNING",
            current_url=start_url,
            task=task,
            retry_count=0,
            max_retries=3,
            page_handle=page,
            browser_handle=browser
        )
        
        try:
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            return final_state
        finally:
            # Note: Don't cleanup here if we need to resume
            pass
    
    def resume(self, state: GraphState) -> GraphState:
        """
        Resume execution after approval
        
        Args:
            state: Current state to resume from
            
        Returns:
            Updated state
        """
        # Change status back to RUNNING
        state["status"] = "RUNNING"
        state["messages"].append("✅ Approval received - resuming execution")
        
        # Continue from executor node
        try:
            # Execute the approved action
            state = self.executor_node(state)
            
            # If successful, continue the loop
            if state["status"] != "ERROR":
                # Continue navigating
                while state["status"] == "RUNNING":
                    state = self.navigator_node(state)
                    if state["status"] == "ERROR":
                        break
                    
                    state = self.brain_node(state)
                    if state["status"] == "ERROR":
                        break
                    
                    state = self.safety_valve_node(state)
                    if state["status"] in ["PAUSED", "DONE", "ERROR"]:
                        break
                    
                    state = self.executor_node(state)
                    if state["status"] in ["DONE", "ERROR"]:
                        break
            
            return state
        except Exception as e:
            state["status"] = "ERROR"
            state["messages"].append(f"❌ Resume error: {str(e)}")
            return state
