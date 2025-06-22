#!/usr/bin/env python3
"""
Test Database Explorer Table Visibility
"""

import sys
sys.path.append('/home/invisa/Desktop/my_grad_streamlit/src')

from enhanced_db_explorer import get_tables

print("🔍 Tables visible in Database Explorer:")
print("=" * 40)

tables = get_tables()
for i, table in enumerate(tables, 1):
    print(f"{i:2d}. {table}")

print(f"\n✅ Total tables visible: {len(tables)}")
