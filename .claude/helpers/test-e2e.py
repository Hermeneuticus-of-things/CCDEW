#!/usr/bin/env python3
"""
Hermes Autonomous End-to-End Test
"""

import subprocess
import sys
import time

def test_hermes_e2e():
    print("=== E2E TEST: Hermes Autonomous Agent ===")
    
    # Run a simple task: list conversations
    print("\n1. Running task: 'List my Telegram conversations'")
    result = subprocess.run(
        ["node", "/home/think/CCDEW/.claude/helpers/hermes-autonomous.cjs", 
         "List my Telegram conversations"],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode == 0:
        output = result.stdout
        if "conversations_list" in output or "Telegram" in output or "SUCCESS" in output:
            print("✓ Task completed successfully")
            print(f"Output length: {len(output)} chars")
            return True
        else:
            print("✗ Unexpected output")
            print("=== STDOUT ===")
            print(output[:500])
            print("=== STDERR ===")
            print(result.stderr[:500])
            return False
    else:
        print("✗ Command failed")
        print("STDERR:", result.stderr)
        return False

if __name__ == "__main__":
    import os
    # Ensure we're in the right directory
    os.chdir("/home/think/CCDEW")
    
    success = test_hermes_e2e()
    print("\n=== TEST RESULT ===")
    print("SUCCESS" if success else "FAILED")
    sys.exit(0 if success else 1)