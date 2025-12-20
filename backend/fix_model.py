#!/usr/bin/env python3
"""
Quick fix: Update brain.py to use models available with your API key
"""
import os
import sys

# Read the current brain.py
brain_file = "/Users/avinashdevray/finagent_sentinel/backend/app/brain.py"

with open(brain_file, 'r') as f:
    content = f.read()

# Replace gemini-1.5-pro with gemini-2.0-flash-exp (which is available)
content = content.replace('model="gemini-1.5-pro"', 'model="gemini-2.0-flash-exp"')
content = content.replace('gemini-1.5-pro', 'gemini-2.0-flash-exp')
content = content.replace('model="gemini-1.5-flash"', 'model="gemini-1.5-flash-8b"')
content = content.replace('gemini-1.5-flash', 'gemini-1.5-flash-8b')

# Write back
with open(brain_file, 'w') as f:
    f.write(content)

print("✅ Updated brain.py to use gemini-2.0-flash-exp")
print("   Fallback: gemini-1.5-flash-8b")
