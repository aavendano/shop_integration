#!/usr/bin/env python
"""
Test script to debug catalog and price list creation
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/alejandro/shop-app/shop_integration')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_manager.settings')
django.setup()

from accounts.models import Session
from prices.services import get_or_create_catalog_and_price_list

# Get session
session = Session.objects.first()
if not session:
    print("ERROR: No session found")
    sys.exit(1)

print(f"Session site: {session.site}")
print(f"Session token: {session.token[:20]}...")
print()

print("Testing get_or_create_catalog_and_price_list()...")
print()

try:
    catalog_id, price_list_id, created = get_or_create_catalog_and_price_list(session)
    
    print(f"Result:")
    print(f"  Catalog ID: {catalog_id}")
    print(f"  Price List ID: {price_list_id}")
    print(f"  Created: {created}")
    
    if catalog_id and price_list_id:
        print("\n✅ SUCCESS!")
        print(f"\nAdd these to your .env:")
        print(f"CATALOG_ID='{catalog_id}'")
        print(f"PRICE_LIST_ID='{price_list_id}'")
    else:
        print("\n❌ FAILED - Check logs above for errors")
        
except Exception as e:
    print(f"\n❌ EXCEPTION: {str(e)}")
    import traceback
    traceback.print_exc()
