"""ARM what-if diagnostics never expose source IDs or accidentally authorize."""
import unittest

from scripts.deploy.feature4_cpu_whatif_type import classify_resource_type


class F4CpuWhatifTypeTests(unittest.TestCase):
    def test_exact_child_types_without_names(self):
        cases = {
            "/subscriptions/111/resourceGroups/rg-retailgrowth-dev/providers/Microsoft.Web/sites/rgai-dev-f4cpu-d4e5ddbd/config/web": "microsoft.web/sites/config",
            "/subscriptions/111/resourceGroups/rg-retailgrowth-dev/providers/Microsoft.Web/serverfarms/rgai-dev-f4cpu-plan": "microsoft.web/serverfarms",
            "/subscriptions/111/resourceGroups/rg-retailgrowth-dev/providers/Microsoft.Storage/storageAccounts/account/blobServices/default/containers/sensitive-private-name": "microsoft.storage/storageaccounts/blobservices/containers",
        }
        for source, expected in cases.items():
            with self.subTest(expected=expected):
                classified = classify_resource_type(source)
                self.assertEqual(classified, expected)
                for secret in ("rg-retailgrowth-dev", "sensitive-private-name", "rgai-dev-f4cpu"):
                    self.assertNotIn(secret, classified)

    def test_malformed_and_unknown_id_categories_are_fixed(self):
        cases = {
            "": "missing-id",
            "https://fake.example/abc": "missing-provider",
            "/providers/evil.provider/sites/customer": "unrecognized-resource-type",
            "/providers/Microsoft.Web/sites": "malformed-provider-shape",
            "/providers/Microsoft.Web/sites/customer/config": "malformed-provider-shape",
            "/providers/Microsoft.Web/sites/private-name/config/web/extra": "malformed-provider-shape",
            "/providers/Microsoft.Web/sites/private-name/config/weird?token=secret": "malformed-resource-name",
        }
        for value, expected in cases.items():
            with self.subTest(expected=expected):
                observed = classify_resource_type(value)
                self.assertEqual(observed, expected)
                self.assertNotIn("secret", observed)
        self.assertEqual(classify_resource_type("x" * 2049), "oversized-id")
        self.assertEqual(classify_resource_type(None), "missing-id")


if __name__ == "__main__":
    unittest.main()
