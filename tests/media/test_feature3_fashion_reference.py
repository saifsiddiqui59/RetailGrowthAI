"""Real Pillow bytes, simulated tenant claims: realistic *illustrative* kurti fixture.

NO actual customer media, commercial image rights or real AI try-on is asserted.
All approvals below are in-memory test doubles, not hosted authorization.
"""
import sys
from io import BytesIO
from pathlib import Path
from copy import deepcopy
from uuid import uuid4, uuid5, NAMESPACE_URL
import unittest

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
from fashion_reference_v1 import (
    FashionReferenceDenied, prepare_fashion_references, resolve_first_frame,
    plan_virtual_try_on,
)

def image_bytes(kind):
    im=Image.new("RGB",(720,1080), "#E8DECB" if kind=="garment" else "#CCC0B2")
    draw=ImageDraw.Draw(im)
    if kind=="garment":
        # Kurti: A-line tunic, elbow-length sleeves, round neck, gold embroidery.
        draw.polygon([(245,120),(475,120),(520,630),(600,780),(560,900),
                      (160,900),(120,780),(200,630)],fill="#2B6978")
        draw.ellipse((317,95,403,177),fill="#E8DECB")
        for y in range(310,770,50):
            draw.arc((320,y,400,y+35),0,180,fill="#DFAE55",width=6)
            draw.line([(353,y+10),(363,y+23)],fill="#FFE59F",width=4)
    else:
        draw.ellipse((280,75,445,260),fill="#8F6D58")
        draw.polygon([(258,280),(470,280),(510,850),(212,850)],fill="#635B84")
    b=BytesIO();im.save(b,"PNG");return b.getvalue()


class FashionKurtiReferenceTests(unittest.TestCase):
    def setUp(self):
        self.shop=str(uuid4());self.other=str(uuid4())
        self.garment=str(uuid4());self.upload_object=str(uuid4())
        self.model_asset=str(uuid4())
        self.model_id=str(uuid5(NAMESPACE_URL, "sample-approved-synthetic-adult-kurti-model"))
        self.tryon=str(uuid4());self.job=str(uuid4())
        self.images={"garment":image_bytes("garment"),
                     "model":image_bytes("model"),
                     "tryon":image_bytes("model")}
        from hashlib import sha256
        self.blobs={
            self.garment:self.images["garment"],
            self.model_asset:self.images["model"],
            self.tryon:self.images["tryon"],
        }
        self.rows={
            self.garment:self.row(self.garment,"UPLOAD",
                f"{self.shop}/uploads/{self.upload_object}.png"),
            self.model_asset:self.row(self.model_asset,"UPLOAD",
                f"{self.shop}/model-library/{self.model_id}/{sha256(self.images['model']).hexdigest()}.png"),
            self.tryon:self.row(self.tryon,"GENERATED",
                f"{self.shop}/feature3/gpu/{self.job}/{sha256(self.images['tryon']).hexdigest()}.png"),
        }
        self.grants={id:{"authorized":True,"shop_id":self.shop,"asset_id":id,
            "approval_state":"APPROVED","license_verified":True,
            "rights_revoked":False,"rights_revision":3} for id in self.rows}
        self.model_data={
            "model_id":self.model_id,"owner_shop_id":self.shop,
            "media_asset_id":self.model_asset,"status":"APPROVED",
            "rights_verified":True,"synthetic_adult":True,
            "approved_uses":["poster","video_reference","try_on"],
            "image_sha256":sha256(self.images["model"]).hexdigest(),
            "rights_revision":3,"source_kind":"retailer_licensed",
            "label":"Approved studio model reference","pose":"front",
            "license_id":"REVIEWED-COMMERCIAL","attribution":"Studio-owned test model",
        }
        self.review={
            "shop_id":self.shop,"source_asset_id":self.garment,
            "output_asset_id":self.tryon,"model_asset_id":self.model_asset,
            "inference_verified":True,"output_sha256":sha256(self.images["tryon"]).hexdigest(),
            "review_revision":2,"reviewer_confirmation":True,
            "checks":{x:True for x in
                ("color","pattern","neckline","sleeves","length","embroidery")},
            "notes":"Manually verified source identity and six garment details",
        }
        self.info={
            "sku":"KURTI-TEAL-001","garment_type":"kurti",
            "shape":"A-line","base_color":"#2B6978",
            "pattern":"Plain teal with embroidery",
            "neckline":"Round neckline","sleeves":"Elbow-length sleeves",
            "length":"Knee length","embroidery":"Gold floral chest embroidery",
        }
        self.product_revision=2
        self.calls=[]
    def row(self, id, source, path):
        from hashlib import sha256
        raw=({"garment":self.images["garment"],
              "model":self.images["model"],
              "tryon":self.images["tryon"]}[
                  "garment" if id==self.garment else
                  "model" if id==self.model_asset else "tryon"])
        return {
            "id":id,"shop_id":self.shop,"storage_bucket":"retailgrowth-media",
            "object_path":path,"mime_type":"image/png","source":source,
            "license_name":"owned","license_url":None,
            "attribution":"Original studio-controlled kurti fixture",
            "image_sha256":sha256(raw).hexdigest(),
        }
    def readers(self):
        def media(shop,id):
            self.calls.append(("media",shop,id))
            return self.rows.get(id)
        def grant(shop,id,purpose):
            self.calls.append(("grant",shop,id,purpose))
            return self.grants.get(id)
        def read(shop,id,path):
            self.calls.append(("bytes",shop,id))
            if self.rows[id]["object_path"]!=path: raise RuntimeError("bad private key")
            return self.blobs[id]
        return dict(read_asset=media,authorize_asset=grant,
                    read_private_bytes=read,
                    read_garment_metadata=lambda shop,id:{
                        "shop_id":self.shop,"media_asset_id":self.garment,
                        "status":"APPROVED","approval_revision":self.product_revision,
                        "garment":self.info},
                    read_model=lambda shop,id:self.model_data,
                    read_review=lambda shop,id:self.review)
    @staticmethod
    def worker_claim(shop, source_ids, fingerprint):
        return (isinstance(source_ids, tuple) and bool(source_ids) and
                isinstance(fingerprint, str) and len(fingerprint)==64)

    def prepare(self, **overrides):
        args=dict(shop_id=self.shop,garment_asset_id=self.garment,
                  purpose="image_to_video",**self.readers())
        args.update(overrides)
        return prepare_fashion_references(**args)

    def test_real_png_bytes_and_garment_exact_source_as_first_frame(self):
        bundle=self.prepare()
        self.assertNotEqual(self.upload_object,self.garment)
        self.assertEqual(bundle["sources"]["first_frame"]["source_asset_id"],self.garment)
        self.assertEqual(bundle["sources"]["garment"]["dimensions"],[720,1080])
        self.assertEqual(bundle["garment"]["sku"],"KURTI-TEAL-001")
        self.assertIn("embroidery",bundle["garment"])
        self.assertEqual(bundle["output_approved"],False)
        self.assertEqual(bundle["gpu_authorized"],False)
        self.assertNotIn("storage_key",str(bundle))
        self.assertNotIn("signedURL",str(bundle))
        self.assertNotIn("image_bytes",str(bundle))
        worker=resolve_first_frame(expected_manifest=bundle,current_readers=self.readers(), verify_worker_job=self.worker_claim)
        self.assertEqual(worker["image_bytes"],self.blobs[self.garment])
        self.assertEqual(worker["dimensions"],[720,1080])
        self.assertFalse(worker["gpu_authorized"])
    def test_feature2_4_consume_metadata_not_private_image_bytes(self):
        for consumer in ("creative_direction","editing"):
            package=self.prepare(purpose=consumer)
            self.assertEqual(package["purpose"],consumer)
            self.assertEqual(package["preservation"]["no_embroidered_motif_redraw"],True)
            with self.assertRaises(FashionReferenceDenied):
                resolve_first_frame(expected_manifest=package,
                                    current_readers=self.readers(), verify_worker_job=self.worker_claim)

    def test_model_and_vton_plan_never_generate_paid_output(self):
        package=self.prepare(model_asset_id=self.model_asset,model_id=self.model_id)
        task=plan_virtual_try_on(manifest=package)
        self.assertEqual(package["model"]["pose"],"front")
        self.assertEqual(package["model"]["license_id"],"REVIEWED-COMMERCIAL")
        self.assertEqual(task["category"],"tops")
        self.assertEqual(task["garment_asset_id"],self.garment)
        self.assertEqual(task["model_asset_id"],self.model_asset)
        self.assertEqual(task["status"],"BLOCKED_PROVIDER_APPROVAL")
        self.assertFalse(task["generation_executed"])
        self.assertEqual(package["sources"]["first_frame"]["source_asset_id"],self.garment)
    def test_reviewed_generated_tryon_requires_real_inference_and_six_human_checks(self):
        p=self.prepare(model_asset_id=self.model_asset,model_id=self.model_id,
                       try_on_asset_id=self.tryon)
        self.assertEqual(p["sources"]["first_frame"]["source_asset_id"],self.tryon)
        self.assertEqual(p["try_on_review"]["state"],"HUMAN_REVIEW_PASSED")
        self.assertFalse(p["try_on_review"]["publish_approved"])
        self.review["inference_verified"]=False
        with self.assertRaises(FashionReferenceDenied):
            self.prepare(model_asset_id=self.model_asset,model_id=self.model_id,
                         try_on_asset_id=self.tryon)
        self.review["inference_verified"]=True
        self.review["checks"]["embroidery"]=False
        with self.assertRaises(FashionReferenceDenied):
            self.prepare(model_asset_id=self.model_asset,model_id=self.model_id,
                         try_on_asset_id=self.tryon)

    def test_video_reference_uses_must_be_explicit_unique_string_array(self):
        # Transport coercion must not turn a substring or mapping key into
        # independently reviewed video_reference permission.
        invalid = (
            "video_reference", {"video_reference": True},
            ("video_reference",), {"video_reference"}, None, [],
            ["poster"], ["video_reference", "video_reference"],
            ["video_reference", "unknown"], ["video_reference", True],
            ["video_reference", {"poster": True}],
            ["video_reference", "poster", "try_on", "poster"],
        )
        original = self.model_data["approved_uses"]
        try:
            for uses in invalid:
                self.model_data["approved_uses"] = uses
                with self.subTest(uses=repr(uses)):
                    with self.assertRaises(FashionReferenceDenied):
                        self.prepare(model_asset_id=self.model_asset,
                                     model_id=self.model_id)
            for uses in (["video_reference"],
                         ["poster", "video_reference"],
                         ["poster", "try_on", "video_reference"]):
                self.model_data["approved_uses"] = uses
                with self.subTest(uses=repr(uses)):
                    bundle = self.prepare(model_asset_id=self.model_asset,
                                          model_id=self.model_id)
                    self.assertFalse(bundle["gpu_authorized"])
                    self.assertEqual(bundle["model"]["model_id"], self.model_id)
        finally:
            self.model_data["approved_uses"] = original

    def test_revoked_model_and_foreign_image_deny(self):
        with self.assertRaises(FashionReferenceDenied):
            self.prepare(shop_id=self.other)
        self.grants[self.garment]["rights_revoked"]=True
        with self.assertRaises(FashionReferenceDenied):
            self.prepare()
        self.grants[self.garment]["rights_revoked"]=False
        self.model_data["status"]="REVOKED"
        with self.assertRaises(FashionReferenceDenied):
            self.prepare(model_asset_id=self.model_asset,model_id=self.model_id)

    def test_change_model_or_garment_after_bundle_invalidates_worker(self):
        manifest=self.prepare(model_asset_id=self.model_asset,model_id=self.model_id)
        self.model_data["rights_revision"]=4
        with self.assertRaises(FashionReferenceDenied):
            resolve_first_frame(expected_manifest=manifest,current_readers=self.readers(), verify_worker_job=self.worker_claim)
        self.model_data["rights_revision"]=3
        self.grants[self.garment]["rights_revision"]=4
        with self.assertRaises(FashionReferenceDenied):
            resolve_first_frame(expected_manifest=manifest,current_readers=self.readers(), verify_worker_job=self.worker_claim)
        self.grants[self.garment]["rights_revision"]=3
        self.product_revision=3
        with self.assertRaises(FashionReferenceDenied):
            resolve_first_frame(expected_manifest=manifest,current_readers=self.readers(), verify_worker_job=self.worker_claim)

    def test_original_storage_uuid_path_must_still_match_registered_original(self):
        self.rows[self.garment]["object_path"]=(f"{self.shop}/uploads/" +
            "non-uuid.png")
        with self.assertRaises(FashionReferenceDenied): self.prepare()
        self.rows[self.garment]["object_path"]=(f"{self.shop}/uploads/" +
            str(uuid4()) + ".webp")
        with self.assertRaises(FashionReferenceDenied): self.prepare()
        self.rows[self.garment]["object_path"]=(f"{self.shop}/uploads/" +
            str(uuid4()) + "/traversal.png")
        with self.assertRaises(FashionReferenceDenied): self.prepare()

    def test_private_bytes_mutation_and_malformed_path_fail(self):
        self.rows[self.garment]["object_path"]=f"{self.other}/uploads/{self.upload_object}.png"
        with self.assertRaises(FashionReferenceDenied):self.prepare()
        self.rows[self.garment]["object_path"]=f"{self.shop}/uploads/{self.upload_object}.png"
        self.blobs[self.garment]=self.blobs[self.model_asset]
        with self.assertRaises(FashionReferenceDenied):self.prepare()

    def test_forged_commercial_metadata_and_unreviewed_fixture_denied(self):
        self.rows[self.garment]["fixture_only"]=True
        with self.assertRaises(FashionReferenceDenied):self.prepare()
        self.rows[self.garment].pop("fixture_only")
        self.grants[self.garment]["approval_state"]="PENDING_REVIEW"
        with self.assertRaises(FashionReferenceDenied):self.prepare()
        self.grants[self.garment]["approval_state"]="APPROVED"
        self.info["embroidery"]=""
        with self.assertRaises(FashionReferenceDenied):self.prepare()
        self.info["embroidery"]="Gold floral chest embroidery"
        self.info["base_color"]="teal"
        with self.assertRaises(FashionReferenceDenied):self.prepare()

    def test_final_first_frame_rejects_transient_private_path_before_byte_read(self):
        # Feature5's standalone first-frame reader is an independent consumer
        # of the same private source authority as Feature3's worker packet.
        # A second row read after the lease must never fetch a substituted
        # foreign, public, traversal, or wrong-role Storage object.
        for tryon in (False, True):
            for mutation in (
                {"object_path":f"{self.other}/uploads/{self.upload_object}.png"},
                {"object_path":"https://external.invalid/private.png"},
                {"object_path":f"{self.shop}/uploads/../secret.png"},
                {"storage_bucket":"public-media"},
                {"source":"UPLOAD" if tryon else "GENERATED"},
                {"shop_id":self.other},
                {"id":str(uuid4())},
            ):
                with self.subTest(tryon=tryon, mutation=mutation):
                    self.setUp()
                    target=self.tryon if tryon else self.garment
                    manifest=(self.prepare(
                        model_asset_id=self.model_asset,model_id=self.model_id,
                        try_on_asset_id=self.tryon) if tryon else self.prepare())
                    readers=self.readers()
                    original_row=readers["read_asset"]
                    original_bytes=readers["read_private_bytes"]
                    calls=[0]
                    byte_paths=[]
                    def changed_row(shop,asset):
                        row=original_row(shop,asset)
                        if asset==target:
                            calls[0]+=1
                            if calls[0]==2:
                                return {**row,**mutation}
                        return row
                    def tracked_bytes(shop,asset,path):
                        byte_paths.append(path)
                        return original_bytes(shop,asset,path)
                    readers["read_asset"]=changed_row
                    readers["read_private_bytes"]=tracked_bytes
                    with self.assertRaises(FashionReferenceDenied):
                        resolve_first_frame(
                            expected_manifest=manifest,current_readers=readers,
                            verify_worker_job=self.worker_claim)
                    self.assertEqual(calls[0],2)
                    # First manifest pass may read original sources, but the
                    # substituted second-row path must never be fetched.
                    self.assertEqual(len(byte_paths),3 if tryon else 1)
                    self.assertNotIn(mutation.get("object_path","not-a-path"),
                                     byte_paths)

    def test_final_first_frame_rechecks_typed_rights_before_private_byte_read(self):
        # A transient revocation or bool/float revision cannot be repaired by
        # a later clean callback: deny the current final-byte read itself.
        for invalid in (True,1.0,"3",None):
            with self.subTest(revision=repr(invalid)):
                self.setUp()
                manifest=self.prepare()
                readers=self.readers()
                original=readers["authorize_asset"]
                original_bytes=readers["read_private_bytes"]
                seen=[0]
                byte_reads=[]
                def changed_grant(shop,asset,purpose):
                    value=original(shop,asset,purpose)
                    if asset==self.garment:
                        seen[0]+=1
                        if seen[0]==2:
                            return {**value,"rights_revision":invalid}
                    return value
                def tracked_bytes(shop,asset,path):
                    byte_reads.append(path)
                    return original_bytes(shop,asset,path)
                readers["authorize_asset"]=changed_grant
                readers["read_private_bytes"]=tracked_bytes
                with self.assertRaises(FashionReferenceDenied):
                    resolve_first_frame(expected_manifest=manifest,
                                        current_readers=readers,
                                        verify_worker_job=self.worker_claim)
                self.assertEqual(seen[0],2)
                self.assertEqual(len(byte_reads),1)

    def test_worker_without_durable_claim_is_denied_before_private_delivery(self):
        original=self.prepare()
        with self.assertRaises(FashionReferenceDenied):
            resolve_first_frame(expected_manifest=original,current_readers=self.readers(),
                                verify_worker_job=lambda *_:False)
        with self.assertRaises(FashionReferenceDenied):
            resolve_first_frame(expected_manifest=original,current_readers=self.readers(),
                                verify_worker_job=None)

    def test_worker_rejects_malicious_changed_manifest_or_stale_output_review(self):
        original=self.prepare(model_asset_id=self.model_asset,model_id=self.model_id,
                              try_on_asset_id=self.tryon)
        self.review["review_revision"]+=1
        with self.assertRaises(FashionReferenceDenied):
            resolve_first_frame(expected_manifest=original,current_readers=self.readers(), verify_worker_job=self.worker_claim)
        edited=deepcopy(original)
        edited["sources"]["first_frame"]["sha256"]="0"*64
        with self.assertRaises(FashionReferenceDenied):
            resolve_first_frame(expected_manifest=edited,current_readers=self.readers(), verify_worker_job=self.worker_claim)

if __name__=="__main__":unittest.main()
