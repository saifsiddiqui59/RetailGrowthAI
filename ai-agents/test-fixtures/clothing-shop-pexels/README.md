# Thread & Loom — cross-feature clothing test shop (discovery catalog)

`manifest.json` has two real Pexels photo pages and two real Pexels clip pages. Anyone working on Features #2/#3/#4/#5/#7 can read it as a **shared offline input fixture**. Neither model release, retailer garment ownership, imported bytes nor hosted tenant permissions are present.

## Import genuine Pexels files using their official SDK

```bash
node ai-agents/test-fixtures/clothing-shop-pexels/import-official-pexels.mjs --plan
# In your separately authorized test environment, NOT a PR/CI secret:
npm install --no-save pexels@1.2.1
PEXELS_API_KEY=your-own-pexels-api-key node ai-agents/test-fixtures/clothing-shop-pexels/import-official-pexels.mjs --import
```

The importer uses **actual** `pexels/pexels-javascript` `createClient`, `client.photos.show({id})` and `client.videos.show({id})` and downloads exact bytes from allowlisted Pexels CDN only. It checks type, signature, size and SHA256, writing locally to an ignored `downloaded-private-review-required/` folder, plus a receipt. It is not executed by CI or this developer session: no Pexels API credential or network connection is available. A Pexels API key is free to request from Pexels. Follow the API terms and original Pexels license.

**Important**: Original downloaded stock photos/videos remain atmosphere/B-roll candidates and are **not** approved product/model/brand imagery. Before real customer tests, ensure current license, person/trademark releases if required and a real signed-in shop owner's separate private tenant storage approval. The script does not upload or change Supabase, merge PRs, start GPUs, or call paid providers. Never substitute synthetic test credentials as proof of a real shop login.
