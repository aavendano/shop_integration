

## Installation


2. Add `'shopify_sync',` to `INSTALLED_APPS`
3. Create a new `shopify_sync.Session` in Django admin or shell, enter your Shopify admin API token and site name.

Where to get these fields:

- **API Token**: In the Shopify admin, this is caleld "API Key Password".
- **Site name**: If your domain is http://my-site.myshopify.com your site name is my-site.

This package supports Python 3.X and Django>=4.2

## How to use

First we will get some of the products from Shopify

```py
from shopify_sync.models import Product, Session
session = Session.objects.first()  # Assuming you have just one that you made previously
products = Product.objects.sync_all(session, query="For bar")
```

`sync_all` passes all kwargs to the `shopify_resource.find` so we can
then sync only the items that shopify returns from that search. Now we have all
of the `products` stored locally. Now to update from Django

```py
product = Product.objects.first()
product.title = "New Bar Foo"
product.save(push=True)
```

The `save` method on the objects also accepts the optional argument `push`
which will push the updated model that is locally to Shopify. Now if a product
was edited on shopify through some means other than this Django app, we will
not have the current updated model. For this we need to sync

```py
changed_product.sync()
```

The `changed_product` will get a local copy of the shopify_resource and then
do a `.reload()` on it so that we make a request to shopify. Then we sync
that back with our database.


## Product Parsing - How to use

The `product_parsing` module allows you to import products from external sources (CSV or JSON) and sync them to Shopify using a configuration file to map fields.

### 1. The Configuration File
You need a JSON configuration file to tell the parser how to read your data. This file defines `mappings` between your source data columns and our internal schema.

Example `config.json`:
```json
{
  "provider_id": "my_vendor",
  "mappings": [
    {
      "source": "Vendor SKU", 
      "destination": "identifiers.sku",
      "transforms": [{"name": "trim"}]
    },
    {
      "source": "Item Cost", 
      "destination": "pricing.cost",
      "transforms": [{"name": "parse_price"}]
    }
  ]
}
```

- **source**: The column header in your CSV or key in your JSON.
- **destination**: Where it goes in our system (e.g., `identifiers.sku`, `pricing.cost`).
- **transforms**: Optional list of actions to clean up data (e.g., `trim` removes whitespace, `parse_price` converts "$10.00" to numbers).

### 2. Loading and Running

Here is how you can use the pipeline in a script or Django shell:

```python
from product_parsing import load_records_from_json, run_pipeline
from shopify_sync.models import Session

# 1. Get your Shopify session
session = Session.objects.first()

# 2. Load your raw data (supports .json or .csv)
records = load_records_from_json("path/to/products.csv")

# 3. Run the pipeline
# This parses the data using your config and syncs it to the database
summary, report = run_pipeline(
    records=records,
    config_path="path/to/config.json",
    session=session
)

print(f"Created: {summary.created}, Updated: {summary.updated}")
```

## How to publish a new version

Use [commitizen](https://commitizen-tools.github.io/commitizen/commands/bump/) via the [bin/publish.sh](bin/publish.sh) script.

```sh
./bin/publish.sh
```

## Contributing

This project is in maintenance mode. Please do not post feature requests unless you intend to both implement them in a merge request and generally help maintain the project. A great first step would be a merge request to update base packages and ensure we are compatible with new Django versions.
