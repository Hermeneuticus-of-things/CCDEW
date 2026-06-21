#!/usr/bin/env python3
"""
Hermes Autonomous Test - Quick check
"""

import subprocess
import sys

def test_hermes():
    print("=== Testing Hermes Autonomous Agent ===")
    
    # Test 1: Check if script runs
    print("\n1. Running script...")
    result = subprocess.run(
        ["node", "/home/think/CCDEW/.claude/helpers/hermes-autonomous.cjs", "Test task"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✓ Script runs successfully")
    else:
        print("✗ Script failed")
        print(result.stderr)
        return False
    
    # Test 2: Check memory file creation
    print("\n2. Checking memory file...")
    if os.path.exists("/home/think/.hermes/memories/autonomous.json"):
        print("✓ Memory file created")
    else:
        print("✗ Memory file not found")
        return False
    
    # Test 3: Check if OpenCode bash works
    print("\n3. Testing OpenCode bash integration...")
    result = subprocess.run(
        ["opencode", "bash", "-c", "echo 'Hello from OpenCode'"],
        capture_output=True,
        text=True
    )
    if "Hello from OpenCode" in result.stdout:
        print("✓ OpenCode bash works")
    else:
        print("✗ OpenCode bash failed")
        print(result.stderr)
        return False
    
    # Test 4: Check Hermes tools
    print("\n4. Testing Hermes tools...")
    result = subprocess.run(
        ["opencode", "hermes_conversations_list"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✓ Hermes tools accessible")
    else:
        print("✗ Hermes tools not accessible")
        return False
    
    print("\n=== ALL TESTS PASSED! ===")
    return True

if __name__ == "__main__":
    import os
    success = test_hermes()
    sys.exit(0 if success else 1)