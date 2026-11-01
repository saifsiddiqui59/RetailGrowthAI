"""Feature #3 server-only catalog-to-React projection.

This is a pure function, not a deployed Supabase read/API. Caller must obtain
rows from current tenant-authorized DB/RLS and inject current server-side
model/rights and shop-private media authorizers. Never accept browser rows,
shop IDs or image URLs as proof of access.
"""
from __future__ import annotations

import re
from model_library_v2 import ModelLibraryDenied, checked_model_for_use, _uuid

_ASSET = re.compile(r'^[a-zA-Z0-9_-]{1,100}$')


def approved_model_picker_items(*, models, requesting_shop_id,
                                authorize_model_use, resolve_private_media,
                                max_items=50):
    """Return minimal, scoped metadata matching feature3-approved-models.mjs.

    authorize_model_use(shop_id, model_id, purpose, image_sha256) -> bool
    resolve_private_media(shop_id, model_receipt) -> {
       'authorized': True, 'private': True, 'requesting_shop_id': shop_id,
       'image_sha256': sha, 'media_asset_id': registered media ID
    }
    The existing authenticated host separately supplies decoded, protected
    pixels by that registered ID. None are fetched or signed here.
    """
    shop_id = _uuid(requesting_shop_id)
    if (not isinstance(models, (list, tuple)) or
        not callable(authorize_model_use) or
        not callable(resolve_private_media) or
        type(max_items) is not int or not 1 <= max_items <= 100):
        raise ModelLibraryDenied('Server-authorized bounded catalog required')
    ready, seen = [], set()
    for model in models[:500]:
        # The catalog may contain one malformed legacy or untrusted row.
        # Skip that entry without denying the entire otherwise authorized
        # model picker or attempting a private-media resolution.
        if not isinstance(model, dict):
            continue
        try:
            reference = checked_model_for_use(
                model=model, requesting_shop_id=shop_id, usage='poster',
                authorize_use=authorize_model_use,
            )
        except ModelLibraryDenied:
            continue
        if reference['model_id'] in seen:
            continue
        receipt = resolve_private_media(shop_id, reference)
        if (not isinstance(receipt, dict) or
            receipt.get('authorized') is not True or
            receipt.get('private') is not True or
            receipt.get('requesting_shop_id') != shop_id or
            receipt.get('image_sha256') != reference['image_sha256'] or
            not isinstance(receipt.get('media_asset_id'), str) or
            not _ASSET.fullmatch(receipt['media_asset_id'])):
            # Deny this entry. We cannot assume a model grant also
            # registers private preview media for the requesting tenant.
            continue
        label = model.get('label')
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= 64:
            continue
        seen.add(reference['model_id'])
        ready.append({
            'schema': 'retailgrowth.model-library.v1',
            'model_id': reference['model_id'],
            'owner_shop_id': model['owner_shop_id'],
            'scope': model['scope'],
            'status': 'APPROVED', 'synthetic_adult': True,
            'image_sha256': reference['image_sha256'],
            'media_asset_id': receipt['media_asset_id'],
            'label': label.strip(),
            'license_id': model.get('license_id'),
            'attribution': reference['attribution'],
            'approved_uses': ['poster'],
        })
        if len(ready) >= max_items:
            break
    return ready
