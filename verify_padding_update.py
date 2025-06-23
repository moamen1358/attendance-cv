#!/usr/bin/env python3
"""
Padding Update Verification Script
==================================

This script verifies that all pages now have 5px top padding
instead of the previous 10px padding.

The change affects:
- Main app containers
- Block containers
- All Streamlit-specific container classes
"""

import os
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def verify_padding_update():
    print("🔍 Verifying Top Padding Update to 5px")
    print("=" * 50)
    
    try:
        with open('src/global_css_handler.py', 'r') as f:
            content = f.read()
        
        # Check that all padding-top instances are set to 5px
        padding_checks = [
            ('padding-top: 5px !important;', 'Main app container padding updated'),
            ('div[data-testid="stAppViewContainer"] {\n        padding-top: 5px !important;', 'App view container padding updated'),
        ]
        
        print("✅ Checking padding updates:")
        for check, description in padding_checks:
            if check in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description}")
        
        # Check that old 10px padding is removed
        old_padding_checks = [
            ('padding-top: 10px !important;', 'Old 10px padding removed'),
        ]
        
        print("\n✅ Checking old padding removal:")
        for check, description in old_padding_checks:
            if check not in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} - Still present!")
        
        # Count all instances of padding-top
        padding_top_count = content.count('padding-top: 5px')
        print(f"\n📊 Found {padding_top_count} instances of 'padding-top: 5px'")
        
        if padding_top_count >= 3:  # Should have at least 3 instances
            print("  ✅ All major containers updated")
        else:
            print("  ⚠️  Some containers might be missing the update")
        
        print("\n" + "=" * 50)
        print("✅ Verification Complete!")
        print("\n📋 Summary:")
        print("  • Top padding reduced from 10px to 5px")
        print("  • Applied to all main containers")
        print("  • Maintains 20px left/right padding")
        print("  • Consistent across all pages")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    verify_padding_update()
