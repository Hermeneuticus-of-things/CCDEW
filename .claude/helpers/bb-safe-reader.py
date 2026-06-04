#!/usr/bin/env python3
"""
BetterBird Safe Cache Reader v4 - READ-ONLY
Folosește copie temporară /tmp, NICIODATĂ profilul live.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
from bb_readonly import get_safe_profile_path, cleanup_safe_copy

PROFILE = get_safe_profile_path()
print(f"✓ Using safe read-only copy: {PROFILE}")
print(f"  Original BB profile is PROTECTED and untouched.")

# ... restul logică cache reader folosește PROFILE în loc de profilul live ...
# După terminare:
# cleanup_safe_copy(PROFILE)
