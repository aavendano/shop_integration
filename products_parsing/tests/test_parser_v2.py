import unittest

from products_parsing.config.loader import MappingRule, ProviderConfig, TransformSpec
from products_parsing.parser.engine import parse_records


class ParserV2Tests(unittest.TestCase):
    def test_parse_records_builds_v2_schema(self):
        config = ProviderConfig(
            provider_id="demo",
            mappings=[
                MappingRule(source="Title", destination="title"),
                MappingRule(
                    source="SKU",
                    destination="variants.0.supplier_sku",
                    transforms=[TransformSpec(name="trim")],
                ),
                MappingRule(
                    source="Qty",
                    destination="variants.0.quantity",
                    transforms=[TransformSpec(name="parse_int")],
                ),
                MappingRule(
                    source="Image",
                    destination="images.0.src",
                ),
                MappingRule(
                    source="Meta",
                    destination="metadata.extra",
                ),
            ],
            schema_version="v2",
        )
        records = [{"Title": "Test", "SKU": "  abc ", "Qty": "5", "Image": "http://img", "Meta": "ok"}]

        parsed = list(parse_records(records, config))
        self.assertEqual(len(parsed), 1)
        product = parsed[0]

        self.assertEqual(product.title, "Test")
        self.assertEqual(product.variants[0].supplier_sku, "abc")
        self.assertEqual(product.variants[0].quantity, 5)
        self.assertEqual(product.images[0].src, "http://img")
        self.assertEqual(product.metadata["extra"], "ok")


if __name__ == "__main__":
    unittest.main()
