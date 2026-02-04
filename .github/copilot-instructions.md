# Copilot / AI Agent Guide for Shop Manager (brief)

Purpose: help an AI coding agent be immediately productive in this repo by summarizing the architecture, common workflows, patterns, and concrete examples you can run or modify. ✅

## Quick summary

- Django monorepo that implements an ETL-style product parsing + Shopify sync.
- Key apps: `products_parsing` (ETL), `shopify_models` (Django models for shop data), `suppliers` (UI for uploads), `accounts` (Shop + Session objects), `prices` (contextual pricing).
- Frontend/apps: `shop-app` (Shopify app assets), `shop-manager-app` (shopify app extensions).

## Where to start (files to read)

- Architecture overview: `docs/PRODUCT_PARSING_ARCHITECTURE.md` (read first) 🔍
- ETL engine: `products_parsing/parser/engine.py`
- Provider config loader & schema: `products_parsing/config/loader.py` and `products_parsing/config/provider_mapping.schema.json`
- Provider example: `products_parsing/config/providers/nalpac.json`
- Transform registry & built-ins: `products_parsing/transforms/registry.py` and `products_parsing/transforms/core.py`
- Persistence adapter (Django): `products_parsing/adapters/django_adapter.py`
- Pipeline entrypoints: `products_parsing/pipeline.py` and `products_parsing/__init__.py`
- Supplier upload flow (how UI triggers the pipeline): `suppliers/views.py`
- Shopify GraphQL client / session: `shopify_models/graphql.py` and `accounts/models.py` (look for `Session` model with `token` and `site`).

## Essential concepts & patterns (do not change lightly)

- The system uses a canonical product schema (v1 or v2). Provider JSONs map source fields → canonical fields.
- Transforms are declared in provider JSONs and implemented in Python via `@register_transform(name)` in `products_parsing/transforms`.
- Provider JSONs are validated by `load_provider_config` — follow shape in `products_parsing/config/provider_mapping.schema.json` and `loader.py`.
- Persistence uses an adapter (`django_adapter.persist_records`) that resolves by `variants.supplier_sku` by default (or other `unique_identifier` passed into `run_pipeline`).
- Error handling: provider config `error_policy` can be `continue` (default) or `fail` (raise on transform errors). See `ParseReport` in `products_parsing/parser/errors.py`.

## Common tasks & concrete examples

- Run dev server:
  - Activate venv, install requirements: `pip install -r requirements.txt`.
  - Run: `python manage.py migrate && python manage.py runserver`

- Run the parsing pipeline manually (example):
  - Open Django shell: `python manage.py shell` and run:

```python
from products_parsing.pipeline import load_records_from_json, run_pipeline
from accounts.models import Session
records = load_records_from_json('sample_data/nal-product-attributes-main-preselect-minimal.csv')
session = Session.objects.first()  # used by adapters/graph clients
summary, report = run_pipeline(records, 'products_parsing/config/providers/nalpac.json', session)
print(summary, report.error_count)
```

- Run tests:
  - Django test runner: `python manage.py test` (or `python -m pytest` if you prefer pytest).
  - Target a single module: `python manage.py test products_parsing.tests.test_parser_v2`.

- Add a new transform:
  - Implement a function and decorate with `@register_transform('name')` in any module under `products_parsing/transforms`.
  - Tests: add a small unit test under `products_parsing/tests/test_transforms.py`.

- Add a new provider:
  - Create `products_parsing/config/providers/<code>.json` (use `nalpac.json` as a template).
  - `Supplier.code` must match the filename used by the `suppliers` UI to locate the JSON.
  - Validate by calling `products_parsing.config.loader.load_provider_config(path)` in shell.

## Debugging tips & gotchas

- Unknown transform name → KeyError from registry; check `products_parsing/transforms` for registration names.
- Mapping `destination` paths use dotted paths and numeric indices (e.g., `variants.0.supplier_sku` or `images.2.src`) handled by the parser engine.
- `schema_version` toggles v1/v2 canonical shapes; ensure provider JSON sets the expected `schema_version`.
- The `Session` object expected by the GraphQL client includes `token` and `site` (see `accounts.models.Session`).
- Default DB is local `db.sqlite3` — tests and development expect sqlite unless changed in `shop_manager/settings.py`.

## Files you will likely modify as an AI agent

- `products_parsing/transforms/*` (add transforms)
- `products_parsing/config/providers/*.json` (mappings)
- `products_parsing/pipeline.py` or `adapters/django_adapter.py` only if you change persistence behavior — check tests and `docs/PRODUCT_PARSING_ARCHITECTURE.md` first.

## Tests to run for changes

- For transforms: `python manage.py test products_parsing.tests.test_transforms`
- For provider config and parser: `python manage.py test products_parsing.tests.test_parser_v2`
- For end-to-end import: use the Supplier upload UI or run the pipeline in shell with a real `Session`.

---

If anything above is unclear or you want more examples (e.g., a runnable script for local debug), say which area you want expanded and I will update this file. 💬
