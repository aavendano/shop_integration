from decimal import Decimal

from django.test import TestCase, override_settings

from products_parsing.adapters.django_adapter import PersistOptions, persist_records
from products_parsing.canonical.schema_v2 import (
    CanonicalImage,
    CanonicalProduct,
    CanonicalVariant,
)
from shopify_models.models import Image, InventoryItem, InventoryLevel, Product, Variant


@override_settings(PROVIDER_CURRENCY="USD", SHOPIFY_DEFAULT_LOCATION="gid://shopify/Location/1")
class DjangoAdapterTests(TestCase):
    def _persist(self, record, unique_identifier="handle"):
        options = PersistOptions(session=None, unique_identifier=unique_identifier)
        return persist_records([record], options)

    def test_upsert_product_by_handle_updates_existing(self):
        Product.objects.create(
            title="Old",
            description="Old",
            vendor="Vendor",
            product_type="Type",
            tags="tag",
            handle="existing-handle",
        )

        record = CanonicalProduct(
            title="New",
            description="New desc",
            vendor="Vendor",
            product_type="Type",
            tags="tag",
            handle="existing-handle",
        )

        summary = self._persist(record, unique_identifier="handle")

        self.assertEqual(summary.products_updated, 1)
        self.assertEqual(summary.products_created, 0)
        product = Product.objects.get(handle="existing-handle")
        self.assertEqual(product.title, "New")
        self.assertEqual(product.description, "New desc")

    def test_upsert_product_by_supplier_sku_updates_existing(self):
        product = Product.objects.create(
            title="Old",
            description="Old",
            vendor="Vendor",
            product_type="Type",
            tags="tag",
            handle="old-handle",
        )
        Variant.objects.create(
            product=product,
            supplier_sku="SKU-1",
            title="Var",
            price=Decimal("9.00"),
            grams=0,
        )

        record = CanonicalProduct(
            title="Updated",
            description="Updated desc",
            vendor="Vendor",
            product_type="Type",
            tags="tag",
            handle="updated-handle",
            variants=[CanonicalVariant(supplier_sku="SKU-1")],
        )

        summary = self._persist(record, unique_identifier="variants.supplier_sku")

        self.assertEqual(summary.products_updated, 1)
        self.assertEqual(summary.products_created, 0)
        product.refresh_from_db()
        self.assertEqual(product.title, "Updated")
        self.assertEqual(product.handle, "updated-handle")

    def test_variants_update_or_create_by_supplier_sku(self):
        product = Product.objects.create(
            title="Prod",
            description="Desc",
            vendor="Vendor",
            product_type="Type",
            tags="tag",
            handle="prod-handle",
        )
        Variant.objects.create(
            product=product,
            supplier_sku="SKU-1",
            title="Old Var",
            price=Decimal("5.00"),
            grams=0,
        )

        record = CanonicalProduct(
            title="Prod",
            handle="prod-handle",
            variants=[
                CanonicalVariant(
                    supplier_sku="SKU-1",
                    title="New Var",
                    price=Decimal("7.00"),
                    grams=10,
                )
            ],
        )

        summary = self._persist(record, unique_identifier="handle")

        self.assertEqual(summary.variants_updated, 1)
        self.assertEqual(summary.variants_created, 0)
        variant = Variant.objects.get(product=product, supplier_sku="SKU-1")
        self.assertEqual(variant.title, "New Var")
        self.assertEqual(variant.price, Decimal("7.00"))
        self.assertEqual(variant.grams, 10)

    def test_variant_created_when_no_supplier_sku(self):
        record = CanonicalProduct(
            title="Prod",
            handle="prod-handle",
            variants=[CanonicalVariant(title="No SKU", price=Decimal("3.00"), grams=1)],
        )

        summary = self._persist(record, unique_identifier="handle")

        self.assertEqual(summary.variants_created, 1)
        self.assertEqual(Variant.objects.count(), 1)
        self.assertIsNone(Variant.objects.first().supplier_sku)

    def test_images_update_or_create_by_src(self):
        product = Product.objects.create(
            title="Prod",
            description="Desc",
            vendor="Vendor",
            product_type="Type",
            tags="tag",
            handle="prod-handle",
        )
        Image.objects.create(product=product, src="http://img", position=1)

        record = CanonicalProduct(
            title="Prod",
            handle="prod-handle",
            images=[CanonicalImage(src="http://img", position=2)],
        )

        summary = self._persist(record, unique_identifier="handle")

        self.assertEqual(summary.images_updated, 1)
        self.assertEqual(summary.images_created, 0)
        image = Image.objects.get(product=product, src="http://img")
        self.assertEqual(image.position, 2)

    def test_inventory_item_and_level_are_upserted(self):
        record = CanonicalProduct(
            title="Prod",
            handle="prod-handle",
            variants=[
                CanonicalVariant(
                    supplier_sku="SKU-1",
                    price=Decimal("2.50"),
                    grams=2,
                    quantity=5,
                    cost=Decimal("1.25"),
                )
            ],
        )

        self._persist(record, unique_identifier="handle")

        variant = Variant.objects.get(supplier_sku="SKU-1")
        inventory_item = InventoryItem.objects.get(variant=variant)
        self.assertEqual(inventory_item.source_quantity, 5)
        self.assertEqual(inventory_item.unit_cost_amount, Decimal("1.25"))
        self.assertEqual(inventory_item.unit_cost_currency, "USD")

        inventory_level = InventoryLevel.objects.get(inventory_item=inventory_item)
        self.assertEqual(inventory_level.quantities, {"available": 5})
        self.assertTrue(inventory_level.sync_pending)
