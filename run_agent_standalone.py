#!/usr/bin/env python3
"""
Standalone agent runner - bypasses FastAPI to avoid Playwright async conflict
Run this to test the agent without the async loop issue
"""
import sys
sys.path.insert(0, '/Users/avinashdevray/finagent_sentinel/backend')

from app.agent import FinAgentGraph

def main():
    task = input("Enter task (or press Enter for default): ").strip()
    if not task:
        task = "login and invest 500 rupees in gold"
    
    start_url = input("Enter start URL (or press Enter for default): ").strip()
    if not start_url:
        start_url = "https://unreckoned-tommy-briefly.ngrok-free.dev"
    
    print(f"\n🚀 Starting task: {task}")
    print(f"🌐 URL: {start_url}\n")
    
    agent = FinAgentGraph()
    
    # Run agent with live message printing
    def print_message(msg):
        print(f"  {msg}")
    
    final_state = agent.run(task, start_url, message_callback=print_message)
    
    print(f"\n✅ Final Status: {final_state['status']}")
    print(f"📊 Total messages: {len(final_state['messages'])}")

if __name__ == "__main__":
    main()
