#!/usr/bin/env python3
"""
Test script to verify Vertex AI connection
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.brain import VisionBrain
import base64

def test_vertex_ai():
    print("Testing Vertex AI connection...")
    
    try:
        # Initialize brain
        print("1. Initializing VisionBrain...")
        brain = VisionBrain()
        print("✅ Brain initialized successfully!")
        
        # Create a simple test image (1x1 pixel PNG)
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        print("2. Testing screenshot analysis...")
        action = brain.analyze_screenshot(
            screenshot_base64=test_image_b64,
            task="Test task",
            current_url="http://test.com"
        )
        
        print(f"✅ Got response: {action}")
        print(f"   Action: {action.action}")
        print(f"   Reasoning: {action.reasoning}")
        print(f"   Risk Level: {action.risk_level}")
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_vertex_ai()
    sys.exit(0 if success else 1)
