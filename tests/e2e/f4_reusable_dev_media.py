#!/usr/bin/env python3
"""Prepare only owned synthetic PNG fixtures on the two retained DEV shops.
No campaign, render, approval, new user/shop, paid inference or deletion.
"""
import os
import struct
import sys
import uuid
import zlib
from urllib.parse import urlencode
from urllib.request import Request
from urllib.error import HTTPError

import f4_reusable_dev_fixtures as fixtures

CONFIRM = "OWNER-AUTHORIZED-DEV-F4-MEDIA-FIXTURES"
BUCKET = "retailgrowth-media"
ATTRIBUTION = "Original synthetic RetailGrowthAI DEV fixture; generated from geometric RGB patterns."
FIELDS = "id,shop_id,created_by,storage_bucket,object_path,mime_type,source,license_name,license_url,attribution"


def require(condition, category):
    fixtures.require(condition, category)


def png(slot):
    require(slot in ("a", "b"), "UNKNOWN_FIXTURE_SLOT")
    width, height = 480, 800
    colors = ((35, 86, 130), (230, 170, 70)) if slot == "a" else ((90, 45, 110), (65, 180, 155))
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows.extend(colors[(x // 80 + y // 100) % 2])
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(bytes(rows))) + chunk(b"IEND", b""))


def object_path(shop_id):
    sid = fixtures.canonical(shop_id)
    return sid + "/uploads/" + str(uuid.uuid5(uuid.NAMESPACE_URL, fixtures.MARK + ":media:v1:" + sid)) + ".png"


def expected_metadata(shop):
    return {"shop_id": shop["id"], "created_by": shop["owner_user_id"],
            "storage_bucket": BUCKET, "object_path": object_path(shop["id"]),
            "mime_type": "image/png", "source": "UPLOAD", "license_name": "owned",
            "license_url": None, "attribution": ATTRIBUTION}


def metadata(bearer, expected):
    rows = fixtures.user_call(bearer, "/rest/v1/media_assets?" + urlencode({
        "storage_bucket": "eq." + BUCKET, "object_path": "eq." + expected["object_path"],
        "select": FIELDS, "limit": 2}))
    require(isinstance(rows, list) and len(rows) <= 1, "AMBIGUOUS_MEDIA")
    return rows


def storage(bearer, path, data=None):
    # Only the fixed DEV host, exact canonical paths and signed retailer JWT.
    sid = path.split("/")[0]
    require(path == object_path(sid), "UNSAFE_MEDIA_PATH")
    require(set(bearer) == {"apikey", "Authorization"} and bearer["apikey"] == fixtures.helper.PUBLIC
            and bearer["Authorization"].startswith("Bearer "), "SIGNED_RETAILER_REQUIRED")
    prefix = "/storage/v1/object/" if data is not None else "/storage/v1/object/authenticated/"
    headers = dict(bearer)
    if data is not None:
        headers.update({"Content-Type": "image/png", "x-upsert": "false"})
    request = Request(fixtures.helper.SUPABASE + prefix + BUCKET + "/" + path,
                      data=data, headers=headers, method="POST" if data is not None else "GET")
    try:
        with fixtures.helper.NO_REDIRECT_OPENER.open(request, timeout=25) as response:
            return response.status, response.read(2 * 1024 * 1024)
    except HTTPError as response:
        try:
            return response.code, b""
        finally:
            response.close()


def own_media(bearer, shop, slot):
    expected = expected_metadata(shop)
    raw = png(slot)
    rows = metadata(bearer, expected)
    status, body = storage(bearer, expected["object_path"])
    if status == 200:
        require(body == raw, "EXISTING_MEDIA_BYTES_MISMATCH")
    else:
        # Storage may report absent objects as 400 or 404. Require an exact
        # signed own-folder list showing absence before a new non-upsert POST.
        require(not rows and status in (400, 404), "OWN_MEDIA_READ_FAILED")
        name = expected["object_path"].rsplit("/", 1)[1]
        items = fixtures.user_call(bearer, "/storage/v1/object/list/" + BUCKET,
            method="POST", data={"prefix": shop["id"] + "/uploads", "limit": 2, "search": name})
        require(items == [], "MEDIA_ABSENCE_NOT_PROVEN")
        code, _ = storage(bearer, expected["object_path"], raw)
        require(code in (200, 201), "UPLOAD_FAILED_OR_UNCERTAIN")
        require(storage(bearer, expected["object_path"]) == (200, raw), "UPLOAD_BYTES_UNVERIFIED")
    if not rows:
        asset = fixtures.user_call(bearer, "/rest/v1/rpc/register_uploaded_image", method="POST",
            data={"p_shop_id": shop["id"], "p_object_path": expected["object_path"],
                  "p_license_name": "owned", "p_license_url": None, "p_attribution": ATTRIBUTION})
        fixtures.canonical(asset)
        rows = metadata(bearer, expected)
        require(len(rows) == 1 and rows[0].get("id") == asset, "REGISTRATION_READBACK_FAILED")
    require(len(rows) == 1 and isinstance(rows[0], dict), "MEDIA_METADATA_UNVERIFIED")
    asset_id = fixtures.canonical(rows[0].get("id"))
    require(rows[0] == {"id": asset_id, **expected}, "MEDIA_METADATA_MISMATCH")
    return expected


def main():
    env = dict(os.environ)
    require(env.get("RGAI_F4_MEDIA_CONFIRM") == CONFIRM, "MEDIA_CONFIRM_REQUIRED")
    env["RGAI_REUSABLE_FIXTURES_CONFIRM"] = fixtures.CONFIRM
    key = fixtures.preflight(env)
    existing = fixtures.inventory(key)
    require(set(existing) == {email for _, email, _ in fixtures.ACCOUNTS}, "RETAINED_ACCOUNTS_REQUIRED")
    subjects = []
    try:
        for slot, email, name in fixtures.ACCOUNTS:
            uid, bearer = fixtures.provision(key, existing, email)
            shop = fixtures.expected_shop(slot, name, uid)
            subjects.append((slot, bearer, shop))
            require(fixtures.validate_memberships(bearer, shop["id"]) and
                    fixtures.read_shop(bearer, shop["id"]) == [shop], "RETAINED_SHOP_REQUIRED")
            state = fixtures.user_call(bearer, "/rest/v1/rpc/retail_onboarding_status", method="POST", data={})
            require(isinstance(state, dict) and state.get("status") == "APPROVED", "NORMAL_ONBOARDING_REQUIRED")
        require(subjects[0][2]["id"] != subjects[1][2]["id"], "DISTINCT_SHOPS_REQUIRED")
        for i in range(2):
            require(fixtures.read_shop(subjects[i][1], subjects[1-i][2]["id"]) == [], "FOREIGN_SHOP_VISIBLE")
        assets = [own_media(bearer, shop, slot) for slot, bearer, shop in subjects]
        for i in range(2):
            bearer = subjects[i][1]
            foreign = assets[1-i]
            require(metadata(bearer, foreign) == [], "FOREIGN_MEDIA_METADATA_VISIBLE")
            status, _ = storage(bearer, foreign["object_path"])
            require(status in (400, 403, 404), "FOREIGN_MEDIA_BYTES_NOT_DENIED")
        print("F4_TWO_SHOP_OWNED_SYNTHETIC_MEDIA=PASS", flush=True)
    finally:
        for _, bearer, _ in subjects:
            fixtures.user_call(bearer, "/auth/v1/logout?scope=local", method="POST", expected=(200, 204))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("F4_TWO_SHOP_OWNED_SYNTHETIC_MEDIA=FAILED_OR_BLOCKED", file=sys.stderr)
        raise SystemExit(2)
