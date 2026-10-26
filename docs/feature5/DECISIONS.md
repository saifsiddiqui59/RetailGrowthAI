# Feature #5 isolated decisions

- Primary research/adapter candidate: Tencent **HunyuanVideo 1.5**, local official CLI with optional future Diffusers backend; never dynamically fetch unreviewed weights.
- Do not activate Tencent under the community license without commercial/legal and territory review; hosted Indian SaaS does **not** automatically imply unrestricted worldwide access.
- Keep previously implemented Alibaba Wan on Part3 integration branch as an alternative provider behind the coordinator's contract. No second live paid provider.
- 480p, 5-second, 24-fps bounded output profile is a conservative **proposed** profile; not asserted verified by actual inference. Dimensions/probe acceptance require real pinned-model test.
- Premium disabled at three gates: worker flag, license approval, GPU budget approval. Existing approval + quota reservation required in DB before claim. No browser/provider key exposure, no public inference endpoint, no LangGraph or new DB schema.
- Feature4 alone handles reliable offer text, brand logo, music, transitions and final export. Feature5 preserves original assets and indicates human quality review required.
