#!/usr/bin/env python3
"""
Check if Hermes Autonomous environment is ready
"""

import subprocess
import sys
import os

def check_command(cmd, description):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ {description}: OK")
        return True
    else:
        print(f"✗ {description}: FAILED")
        print(f"  Error: {result.stderr}")
        return False

def check_file_exists(path):
    exists = os.path.exists(path)
    print(f"  {'✓' if exists else '✗'} File exists: {path}")
    return exists

def main():
    print("=== Hermes Autonomous Environment Check ===\n")
    
    checks = [
        ("OpenCode Desktop running", "ps aux | grep -i 'opencode' | grep -v grep | wc -l > /dev/null"),
        ("Hermes MCP configured", "opencode hermes_conversations_list 2>&1 | grep -q 'conversations_list'"),
        ("Python 3.6+", "python3 --version"),
        ("Node.js installed", "node --version"),
        ("Script exists", "test -f /home/think/CCDEW/.claude/helpers/hermes-autonomous.cjs"),
        ("Memory dir exists", "test -d /home/think/.hermes/memories"),
        ("Memory file exists", "test -f /home/think/.hermes/memories/autonomous.json"),
        ("Scripts dir exists", "test -d /home/think/.hermes/scripts")
    ]
    
    all_passed = True
    for desc, cmd in checks:
        if not check_command(desc, cmd):
            all_passed = False
    
    print("\n=== SUMMARY ===")
    if all_passed:
        print("✅ Environment ready for Hermes Autonomous!")
    else:
        print("❌ Some checks failed. Please fix before running.")
    
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()