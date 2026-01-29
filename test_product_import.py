#!/usr/bin/env python
"""
Test script for product import functionality.
This script simulates uploading a CSV file and running the product parsing pipeline.
"""
import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.insert(0, '/home/alejandro/shop-app/shop_integration')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop_manager.settings')
django.setup()

from suppliers.models import Supplier
from products_parsing.pipeline import load_records_from_json, run_pipeline
from shopify_sync.models import Session as ShopifySession

def test_product_import():
    """Test the product import functionality with the Nalpac CSV file."""
    
    print("=" * 80)
    print("PRODUCT IMPORT TEST")
    print("=" * 80)
    
    # Get the Nalpac supplier
    try:
        supplier = Supplier.objects.get(code='nalpac')
        print(f"\n✓ Found supplier: {supplier.name} (code: {supplier.code})")
    except Supplier.DoesNotExist:
        print("\n✗ ERROR: Nalpac supplier not found in database")
        return
    
    # Check for CSV file
    csv_path = Path('/home/alejandro/shop-app/shop_integration/nal-product-attributes-main-preselect-minimal.csv')
    if not csv_path.exists():
        print(f"\n✗ ERROR: CSV file not found at {csv_path}")
        return
    print(f"✓ Found CSV file: {csv_path}")
    
    # Check for config file
    config_path = Path('/home/alejandro/shop-app/shop_integration/products_parsing/config/providers/nalpac.json')
    if not config_path.exists():
        print(f"\n✗ ERROR: Config file not found at {config_path}")
        return
    print(f"✓ Found config file: {config_path}")
    
    # Get Shopify session
    session = ShopifySession.objects.first()
    if not session:
        print("\n✗ ERROR: No Shopify session found in database")
        print("   Please create a Shopify session first")
        return
    print(f"✓ Found Shopify session: {session}")
    
    # Load records from CSV
    print(f"\n📄 Loading records from CSV...")
    try:
        records = load_records_from_json(str(csv_path))
        record_count = len(list(records)) if hasattr(records, '__len__') else 'unknown'
        print(f"✓ Loaded records from CSV (count: {record_count})")
        
        # Reload records since we consumed the iterator
        records = load_records_from_json(str(csv_path))
    except Exception as e:
        print(f"\n✗ ERROR loading records: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Run the parsing pipeline
    print(f"\n🔄 Running parsing pipeline...")
    try:
        summary, report = run_pipeline(
            records=records,
            config_path=str(config_path),
            session=session
        )
        
        print("\n" + "=" * 80)
        print("IMPORT RESULTS")
        print("=" * 80)
        print(f"\n✓ Import completed successfully!")
        print(f"\n📊 Summary:")
        print(f"   - Products Created: {summary.products_created}")
        print(f"   - Products Updated: {summary.products_updated}")
        print(f"   - Variants Created: {summary.variants_created}")
        print(f"   - Variants Updated: {summary.variants_updated}")
        print(f"   - Images Created: {summary.images_created}")
        print(f"   - Images Updated: {summary.images_updated}")
        print(f"   - Metafields Created: {summary.metafields_created}")
        print(f"   - Metafields Updated: {summary.metafields_updated}")
        print(f"   - Errors: {len(report.errors)}")
        
        if report.errors:
            print(f"\n⚠️  Errors encountered:")
            for i, error in enumerate(report.errors[:5], 1):  # Show first 5 errors
                print(f"   {i}. {error}")
            if len(report.errors) > 5:
                print(f"   ... and {len(report.errors) - 5} more errors")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n✗ ERROR during import: {str(e)}")
        import traceback
        traceback.print_exc()
        return

if __name__ == '__main__':
    test_product_import()
