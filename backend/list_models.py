#!/usr/bin/env python3
"""
List available Vertex AI models
"""
import os
import sys
from pathlib import Path

# Set credentials
service_account_path = Path(__file__).parent / "service-account.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(service_account_path)

import vertexai
from vertexai.preview.generative_models import GenerativeModel

# Initialize
vertexai.init(project="gigshield", location="us-central1")

print("Checking available models...")
print("\nTrying different model names:")

models_to_try = [
    "gemini-pro",
    "gemini-pro-vision", 
    "gemini-1.5-pro",
    "gemini-1.5-pro-001",
    "gemini-1.5-pro-002",
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
]

for model_name in models_to_try:
    try:
        model = GenerativeModel(model_name)
        response = model.generate_content("Hello")
        print(f"✅ {model_name} - WORKS!")
    except Exception as e:
        print(f"❌ {model_name} - {str(e)[:100]}")
