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

    def test_irregular_arm_names_are_never_returned_or_authorized(self):
        example = ("/subscriptions/abc/resourceGroups/private-secret/providers/"
                   "Microsoft.Storage/storageAccounts/retailprivate/blobsErvices/default/"
                   "containers/internal?password=secret")
        typ = classify_resource_type(example)
        self.assertEqual(typ, "microsoft.storage/storageaccounts/blobservices/containers-irregular-name")
        for secret in ("private-secret", "retailprivate", "password", "internal"):
            self.assertNotIn(secret, typ)

    def test_unexpected_microsoft_provider_type_is_safe_metadata_only(self):
        resource = ("/subscriptions/sensitive-id/resourceGroups/private-rg/providers/"
                    "Microsoft.Resources/deployments/customer-deploy")
        kind = classify_resource_type(resource)
        self.assertEqual(kind, "unexpected-microsoft.resources/deployments")
        for sensitive in ("sensitive-id", "private-rg", "customer-deploy"):
            self.assertNotIn(sensitive, kind)

        irregular = ("/subscriptions/sensitive-id/providers/Microsoft.Insights/"
                     "components/private-secret?token=never-log")
        kind = classify_resource_type(irregular)
        self.assertEqual(kind, "unexpected-microsoft.insights/components-irregular-name")
        self.assertNotIn("never-log", kind)

    def test_malformed_and_unknown_id_categories_are_fixed(self):
        cases = {
            "": "missing-id",
            "https://fake.example/abc": "missing-provider",
            "/providers/evil.provider/sites/customer": "unrecognized-resource-type",
            "/providers/Microsoft.Web/sites": "malformed-provider-shape",
            "/providers/Microsoft.Web/sites/customer/config": "malformed-provider-shape",
            "/providers/Microsoft.Web/sites/private-name/config/web/extra": "malformed-provider-shape",
            "/providers/Microsoft.Web/sites/private-name/config/weird?token=secret": "microsoft.web/sites/config-irregular-name",
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
