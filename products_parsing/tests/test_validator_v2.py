import unittest

from products_parsing.canonical.schema_v2 import CanonicalProduct, CanonicalVariant
from products_parsing.services.validator import CanonicalValidator


class ValidatorV2Tests(unittest.TestCase):
    def test_validator_reports_missing_required_fields(self):
        validator = CanonicalValidator(required_fields=("title", "variants.0.supplier_sku"))
        product = CanonicalProduct()
        issues = validator.validate(product)
        paths = {issue.path for issue in issues}
        self.assertIn("title", paths)
        self.assertIn("variants.0.supplier_sku", paths)

    def test_validator_accepts_valid_variant(self):
        validator = CanonicalValidator(required_fields=("title",))
        product = CanonicalProduct(
            title="Product",
            variants=[CanonicalVariant(supplier_sku="sku-1", quantity=2)],
        )
        issues = validator.validate(product)
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
