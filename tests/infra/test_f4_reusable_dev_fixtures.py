"""No-network negative and reuse checks for persistent DEV fixtures."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e2e"))
import f4_reusable_dev_fixtures as m

UID = "11111111-1111-4111-8111-111111111111"
EMAIL = m.ACCOUNTS[0][1]
ROW = {"id":UID, "email":EMAIL, "role":"authenticated",
       "app_metadata":{"rgai_test_account":True,"rgai_env":"DEV","rgai_fixture":m.MARK}}


class ReusableFixturesTests(unittest.TestCase):
    def test_only_protected_dev_dispatch(self):
        with self.assertRaises(RuntimeError):
            m.preflight({})
        self.assertEqual(m.shop_id(UID), m.shop_id(UID))
        self.assertNotEqual(m.shop_id(UID), m.shop_id("22222222-2222-4222-8222-222222222222"))

    def test_unmarked_foreign_or_elevated_identity_refused(self):
        self.assertEqual(m.verify_account(ROW, EMAIL, UID), UID)
        for changed in ({**ROW,"app_metadata":{}},
                        {**ROW,"email":"different@example.invalid"},
                        {**ROW,"role":"service_role"},
                        {**ROW,"app_metadata":{**ROW["app_metadata"],"rgai_env":"PROD"}}):
            with self.assertRaises(RuntimeError):
                m.verify_account(changed, EMAIL, UID)

    def test_existing_account_rotates_only_exact_marked_identity(self):
        with patch.object(m,"admin",return_value=ROW) as call, patch.object(m,"sign_in",return_value={"fixture":"jwt"}):
            self.assertEqual(m.provision("test-key",{EMAIL:UID},EMAIL)[0],UID)
            self.assertEqual([x.args[1] for x in call.call_args_list],["/"+UID]*3)
            self.assertEqual(call.call_args_list[1].kwargs["method"],"PUT")
            self.assertGreater(len(call.call_args_list[1].kwargs["data"]["password"]),32)
        with patch.object(m,"admin",return_value={**ROW,"app_metadata":{}}) as call:
            with self.assertRaises(RuntimeError):
                m.provision("test-key",{EMAIL:UID},EMAIL)
            self.assertEqual(call.call_count,1)

    def test_pending_approval_never_inserts_shop(self):
        with patch.object(m,"validate_memberships",return_value=False), patch.object(m,"read_shop",return_value=[]), patch.object(m,"user_call",return_value={"status":"PENDING"}) as call:
            with self.assertRaisesRegex(RuntimeError,"NORMAL_ONBOARDING_APPROVAL_REQUIRED"):
                m.provision_shop({},m.expected_shop("a","Synthetic Boutique A",UID))
            self.assertEqual(call.call_count,1)
            self.assertEqual(call.call_args.args[1],"/rest/v1/rpc/retail_onboarding_status")

    def test_unexpected_membership_denied(self):
        with patch.object(m,"memberships",return_value=[{"shop_id":UID,"role":"OWNER","active":True}]):
            with self.assertRaises(RuntimeError):
                m.validate_memberships({},m.shop_id(UID))

    def test_existing_exact_shop_read_only(self):
        shop=m.expected_shop("a","Synthetic Boutique A",UID)
        with patch.object(m,"validate_memberships",return_value=True), patch.object(m,"read_shop",return_value=[shop]), patch.object(m,"user_call") as call:
            m.provision_shop({},shop)
            call.assert_not_called()

    def test_approved_normal_shop_insert_uses_only_signed_bearer(self):
        shop=m.expected_shop("a","Synthetic Boutique A",UID)
        with patch.object(m,"validate_memberships",side_effect=[False,True]), patch.object(m,"read_shop",side_effect=[[],[shop]]), patch.object(m,"user_call",return_value={"status":"APPROVED"}) as call:
            m.provision_shop({"Authorization":"Bearer fixture"},shop)
            self.assertEqual(call.call_count,2)
            self.assertEqual(call.call_args.args[0],{"Authorization":"Bearer fixture","Prefer":"return=minimal"})
            self.assertEqual(call.call_args.args[1],"/rest/v1/shops")
            self.assertEqual(call.call_args.kwargs["data"]["id"],shop["id"])
