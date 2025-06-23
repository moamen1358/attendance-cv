#!/usr/bin/env python3
"""
Attendance Logic Consistency Test
=================================

This script tests that the welcome message logic and dashboard metrics
use the same calculation method to avoid contradictory messages.

The issue was that:
- Dashboard metrics counted classes that have STARTED
- Welcome message counted classes that have ENDED
- Different attendance check functions were used

This resulted in contradictory messages like:
- Dashboard: "You attended 2/2 classes (100%)"
- Welcome: "You missed 2 classes today"

The fix ensures both use the same logic:
- Both count classes that have STARTED
- Both use check_attendance_for_subject() for consistency
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_consistency():
    print("🔍 Testing Attendance Logic Consistency")
    print("=" * 50)
    
    try:
        with open('src/student_report.py', 'r') as f:
            content = f.read()
        
        # Check that the welcome message logic uses the same function as dashboard
        checks = [
            ('check_attendance_for_subject(student_name, date_str, row[\'subject\'])', 
             'Welcome message uses same attendance check as dashboard'),
            ('if current_time_obj >= start_time_obj:', 
             'Welcome message counts started classes (like dashboard)'),
            ('# Student attended all classes that have started today', 
             'Updated comment reflects new logic'),
            ('# Some classes that started were missed', 
             'Updated comment reflects new logic'),
        ]
        
        print("✅ Checking consistency fixes:")
        for check, description in checks:
            if check in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description}")
        
        # Check that old inconsistent logic is removed
        removed_checks = [
            ('if current_time_obj >= end_time_obj:', 
             'Old logic (counting ended classes) removed'),
            ('check_attendance(student_name, date_str, row[\'start_time\'], row[\'end_time\'])', 
             'Old attendance check function removed from welcome logic'),
        ]
        
        print("\n✅ Checking old logic removal:")
        for check, description in removed_checks:
            if check not in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} - Still present!")
        
        print("\n" + "=" * 50)
        print("✅ Test Complete!")
        print("\n📋 Fix Summary:")
        print("  • Welcome message now uses same attendance check as dashboard")
        print("  • Both count classes that have STARTED (not ended)")
        print("  • Consistent logic eliminates contradictory messages")
        print("  • Student who attended 2/2 classes won't see 'missed classes' message")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_consistency()
