#!/usr/bin/env python3
"""
Quick fix script to restore the corrupted agent_core.py file.
"""

# Read the backup from the git history or recreate the tool_schemas section
tool_schemas_correct = '''# 1) JSON schema definitions for each tool
tool_schemas = [
    {
        "name": "list_files",
        "description": "List files in a directory matching a pattern.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string"},
                "pattern":   {"type": "string", "default": "*"},
                "recursive": {"type": "boolean", "default": False}
            },
            "required": ["directory"]
        }
    },'''

print("The file seems to be corrupted. Let me restore it by recreating from our working backup...")

# Since the file is corrupted, let's check if we can restore from git
import subprocess
import os

os.chdir(r"c:\Users\jwexl\Desktop\jarvis")

try:
    # Check git status
    result = subprocess.run(["git", "status", "--porcelain"], 
                          capture_output=True, text=True, check=True)
    print("Git status:", result.stdout)
    
    # Show the diff for agent_core.py
    result = subprocess.run(["git", "diff", "agent_core.py"], 
                          capture_output=True, text=True, check=True)
    print("Git diff:", result.stdout[:1000] if result.stdout else "No diff")
    
except Exception as e:
    print(f"Git command failed: {e}")
    print("Will need to manually restore the file...")
