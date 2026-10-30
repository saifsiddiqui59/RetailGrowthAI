# Feature #5 F5-13 — private review JSON file identity (2026-10-30)

**Status:** IN PROGRESS / source-only, not DONE.

This branch hardens the existing offline CUDA/ComfyUI pre-build review input. The bounded manifest reader now opens a no-follow, regular, single-linked file descriptor, verifies stable inode/device/size/mtime/ctime before and after reading, checks its original pathname again, and rejects linked or swapped review files even if bytes match. CPU-only synthetic tests exercise symlink, hardlink and same-byte pathname substitution.

**Task-manager handoff:** F5-13; owner Feature5/Runtime; dependency ID `F5-OCI`; required output is an independently reviewed immutable CUDA base/wheel inventory, license/SBOM and actual built OCI digest with compatible ABI. Acceptance requires approved source/weights/legal manifests, exact-head 4/4 CI, coordinator integration and fresh main 4/4 CI. This code does not supply an actual image digest, verify a GPU runtime, approve licenses or close the task. Coordinator may record reviewed IN PROGRESS evidence only, not DONE.

No GPU, network, Docker, Azure, Supabase, paid models, PROD, customer media, user samples or WineShopPOS changes.
