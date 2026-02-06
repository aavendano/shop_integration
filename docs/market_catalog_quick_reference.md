# Market and Catalog - Quick Reference Guide

## Common Operations

### 1. Create a Market

#### Via Django Admin

1. Navigate to `/admin/shopify_models/market/`
2. Click "Add Market"
3. Fill in:
   - Name: "United States"
   - Handle: "us"
   - Currency: "USD"
   - Enabled: ✓
4. Click "Save"
5. ✅ Market automatically syncs to Shopify

#### Via Python/Shell

```python
from shopify_models.models import Market
from shopify_models.sync import sync_market

market = Market.objects.create(
    name="United States",
    handle="us",
    enabled=True,
    currency="USD"
)
sync_market(market)
print(f"Market synced: {market.shopify_id}")
```

### 2. Create a Catalog

#### Via Django Admin (Recommended)

1. Navigate to `/admin/shopify_models/catalog/`
2. Click "Add Catalog"
3. Fill in:
   - Title: "US Retail Catalog"
   - Status: "ACTIVE"
   - Market: Select from dropdown
   - Publication: Leave blank (auto-created)
   - Price List: Leave blank (auto-created)
4. Click "Save"
5. ✅ Catalog, Publication, and PriceList automatically sync to Shopify

#### Via Python/Shell

```python
from shopify_models.models import Catalog, Market
from shopify_models.sync import sync_catalog

market = Market.objects.get(handle="us")

catalog = Catalog.objects.create(
    title="US Retail Catalog",
    status="ACTIVE",
    market=market
)

# Auto-create dependencies and sync
sync_catalog(catalog, create_dependencies=True)
print(f"Catalog synced: {catalog.shopify_id}")
print(f"Publication: {catalog.publication.shopify_id}")
print(f"PriceList: {catalog.price_list.shopify_id}")
```

### 3. Publish Product to Catalog

#### Via Python/Shell

```python
from shopify_models.models import Product, Catalog

product = Product.objects.get(handle="my-product")
catalog = Catalog.objects.get(title="US Retail Catalog")

# Publish product to catalog
product.update_catalog_availability(catalog, is_available=True)
print(f"Product '{product.title}' published to '{catalog.title}'")

# Verify
print(f"Product catalogs: {list(product.catalogs.all())}")
```

### 4. Unpublish Product from Catalog

```python
from shopify_models.models import Product, Catalog

product = Product.objects.get(handle="my-product")
catalog = Catalog.objects.get(title="US Retail Catalog")

# Unpublish product from catalog
product.update_catalog_availability(catalog, is_available=False)
print(f"Product '{product.title}' unpublished from '{catalog.title}'")
```

### 5. List Products in a Catalog

```python
from shopify_models.models import Catalog

catalog = Catalog.objects.get(title="US Retail Catalog")
products = catalog.products.all()

print(f"Products in '{catalog.title}':")
for product in products:
    print(f"  - {product.title} ({product.shopify_id})")
```

### 6. List Catalogs for a Product

```python
from shopify_models.models import Product

product = Product.objects.get(handle="my-product")
catalogs = product.catalogs.all()

print(f"Catalogs for '{product.title}':")
for catalog in catalogs:
    print(f"  - {catalog.title} ({catalog.market.name if catalog.market else 'No Market'})")
```

### 7. Create Publication and PriceList Manually

```python
from shopify_models.models import Publication, PriceList
from shopify_models.sync import sync_publication, sync_price_list

# Create Publication
publication = Publication.objects.create(auto_publish=False)
sync_publication(publication)

# Create PriceList
price_list = PriceList.objects.create(
    name="Custom Pricing",
    currency="USD"
)
sync_price_list(price_list)

# Use in Catalog
catalog = Catalog.objects.create(
    title="Custom Catalog",
    status="ACTIVE",
    publication=publication,
    price_list=price_list
)
sync_catalog(catalog, create_dependencies=False)
```

### 8. Update Market

```python
from shopify_models.models import Market
from shopify_models.sync import sync_market

market = Market.objects.get(handle="us")
market.name = "United States of America"
market.save()

# Sync changes to Shopify
sync_market(market)
```

### 9. Bulk Publish Products to Catalog

```python
from shopify_models.models import Product, Catalog

catalog = Catalog.objects.get(title="US Retail Catalog")
products = Product.objects.filter(product_type="Electronics")

for product in products:
    try:
        product.update_catalog_availability(catalog, is_available=True)
        print(f"✓ Published: {product.title}")
    except Exception as e:
        print(f"✗ Failed: {product.title} - {e}")
```

### 10. Check Sync Status

```python
from shopify_models.models import Market, Catalog, Publication, PriceList

# Check if synced to Shopify
market = Market.objects.get(handle="us")
print(f"Market synced: {market.shopify_id is not None}")

catalog = Catalog.objects.get(title="US Retail Catalog")
print(f"Catalog synced: {catalog.shopify_id is not None}")
print(f"Publication synced: {catalog.publication.shopify_id is not None}")
print(f"PriceList synced: {catalog.price_list.shopify_id is not None}")
```

## Django Shell Commands

### Open Django Shell

```bash
source venv/bin/activate
python manage.py shell
```

### Quick Test

```python
from shopify_models.models import Market, Catalog, Product
from shopify_models.sync import sync_market, sync_catalog

# Create and sync market
market = Market.objects.create(name="Test Market", handle="test", currency="USD")
sync_market(market)

# Create and sync catalog
catalog = Catalog.objects.create(title="Test Catalog", status="ACTIVE", market=market)
sync_catalog(catalog, create_dependencies=True)

# Get a product and publish it
product = Product.objects.first()
if product and product.shopify_id:
    product.update_catalog_availability(catalog, is_available=True)
    print(f"Success! Product '{product.title}' published to '{catalog.title}'")
```

## Troubleshooting

### Error: "No active Shopify session found"

**Solution**: Ensure you have an active session in the `accounts_session` table.

### Error: "Product has no shopify_id"

**Solution**: Export the product to Shopify first using `product.export_to_shopify()`

### Error: "Catalog publication is not synced with Shopify"

**Solution**: Sync the catalog again with `sync_catalog(catalog, create_dependencies=True)`

### Error: "Market sync failed: ..."

**Solution**: Check the error message for specific field issues. Common issues:

- Handle already exists
- Invalid currency code
- Missing required fields

## Best Practices

1. **Always use Django Admin for initial setup** - it automatically handles sync
2. **Check shopify_id before operations** - ensure objects are synced before using them
3. **Use create_dependencies=True** - when creating catalogs programmatically
4. **Handle exceptions** - wrap sync operations in try-except blocks
5. **Test in development** - verify sync works before production use
6. **Monitor logs** - check Django logs for sync errors and warnings

## API Rate Limits

Shopify has API rate limits. If you're bulk syncing:

- Add delays between operations
- Use batch operations when available
- Monitor for rate limit errors

```python
import time

for product in products:
    try:
        product.update_catalog_availability(catalog, is_available=True)
        time.sleep(0.5)  # 500ms delay
    except Exception as e:
        print(f"Error: {e}")
```
