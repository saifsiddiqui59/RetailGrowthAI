# F4 native sealed ZIP offline import and function-index gate

Protected DEV private-trigger run #45089361586 failed to index all three private CPU queue/timer functions, despite passing service-role and queue checks. Do not automatically retry the same privileged activation.

Before another Azure publish, run the approved native artifact's complete SHA256/manifest verifier and then a new offline import proof on the exact ZIP: unzip under a short-lived private runner directory and use Python 3.11 `-S` with only the package's bundled dependencies. With the private-worker flag OFF, the app must expose zero functions. With the flag ON, it must expose exactly the three F4 private functions. Both probes use no Supabase service key, Azure connection string, customer JWT, queues, paid models or browser traffic. A startup/import error fails before upload, and diagnostic details are kept out of GitHub logs.

This proof is **not** hosted Azure indexing or real two-shop/MP4 E2E. Only after independent protected rollback checks succeed may the DEV package be restaged and a bounded private-only activation considered. Original API CPU_RENDER, GPU, PROD, WineShopPOS and Issue #249/Y1 remain unchanged.
