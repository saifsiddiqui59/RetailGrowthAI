# RetailGrowthAI - AI Development Instructions

Before starting any development task, read:

1. docs/PROJECT_STATE.md
2. docs/NEXT_TASK.md
3. docs/DECISIONS.md
4. docs/WORK_LOG.md
5. docs/ARCHITECTURE.md
6. docs/INTERFACES_V1.md
7. docs/PARALLEL_WORK.md

Rules:
- Continue existing work; do not restart completed tasks.
- Reuse suitable WineShopPOS components.
- Never modify WineShopPOS production resources.
- Keep RetailGrowthAI DEV and PROD isolated.
- Use Git Bash in VS Code.
- Use npm for JavaScript and uv for Python.
- Prefer low-cost Azure and Supabase architecture.
- Do not implement Postiz or Razorpay.
- Implement platform integrations in Part 2.
- Implement Wan video integration in Part 3.
- Test security and tenant isolation throughout.

After each completed development task:
- Update PROJECT_STATE.md.
- Update NEXT_TASK.md.
- Append a summary to WORK_LOG.md.
- Document any new architecture decision.
- Run appropriate tests.
- Commit and push using scripts/checkpoint.sh.
- Record blockers and unverified work honestly.

Parallel development rules:
- Work on the allocated feature branch and path ownership from docs/PARALLEL_WORK.md.
- Never make incompatible API/schema changes without the coordinator changing docs/INTERFACES_V1.md.
- Only the coordinator integrates to main and edits shared contracts; worker chats send branch PRs.
- The coordinator must update all project documentation after integration.

GitHub Actions automation:
- Read docs/CI_AUTOMATION.md before claiming builds/tests passed.
- Every branch push or PR runs the Part 1 CI jobs; inspect the actual GitHub Actions run and logs after pushing.
- Fix failures only inside your owned branch/files; do not bypass or disable a failing test to obtain green CI.
- The coordinator owns .github/workflows/**; worker chats must propose CI changes rather than modify it directly.
