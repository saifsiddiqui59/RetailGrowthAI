# RetailGrowthAI — Global GitHub Top-100 Relevance Audit

**Snapshot:** 2026-10-26. **Method:** connected GitHub repository search query `stars:>90000 fork:false archived:false sort:stars-desc`, first 100 results by GitHub star ranking. The ranking is time-sensitive and describes *popularity*, not quality, safety or relevance. First-page positions verified against an independent public GitHub rankings tracker. This audit covers all 100 names below; candidates outside this global list were separately reviewed. No implementation, model installation or Azure paid operation occurred.

## Highest-value discoveries within global 100

| Repo | Observed global rank | Best RetailGrowthAI reuse | License/guard |
| --- | ---: | --- | --- |
| [ComfyUI](https://github.com/Comfy-Org/ComfyUI) | 70 | Deploy an isolated GPU workflow engine for supported Hunyuan 1.5 / LTX / Wan and graphical/photo/video generation; use JSON job API, private isolated input/output, model-specific backend; do not duplicate existing auth, queue or billing | GPL-3.0. SaaS hosting/distribution/integrated derivative specifics need license review. Model checkpoint licenses separate. Do not expose ComfyUI publicly or invoke paid partner nodes |
| [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | 81 | Compare full isolated MIT Docker app with importing select script/media/TTS/subtitle modules into current FFmpeg | MIT project source, third-party assets/provider terms separately verify |
| [shadcn/ui](https://github.com/shadcn-ui/ui) | 90 | Reuse well-designed React components for responsive Creative Studio, templates, menus, editable properties, notification center | MIT; verify React 19 + Vite and styling budget |
| [n8n](https://github.com/n8n-io/n8n) | 28 | Study automation UX/workflow patterns for campaigns and approvals | **Sustainable Use License** restricts commercially exposed SaaS/embedding without separate terms; do not transplant engine |
| [Transformers](https://github.com/huggingface/transformers) | 52 | Model support for generation/review/captioning as needed | Framework package != free model weights/GPU |
| [Dify](https://github.com/langgenius/dify) | 56 | Study prompt workflows and human review | **Dify custom license** restricts multi-tenant use without approval; avoid SaaS source adoption |
| [Firecrawl](https://github.com/firecrawl/firecrawl) | 34 | Research competitor/product-page parsing only under explicit permissions | AGPL-3.0; scraping content is not licensed stock footage |

Other filtered top-100 projects: Ollama (#44), AUTOMATIC1111 (#53), Langflow (#59), and browser-use (#98) solve secondary or already-covered needs; none should replace Part 1's deployed queue + FFmpeg, Part 2's official OAuth, Part 3's separate Wan provider, or Supabase JWT/RLS/ledger.

## Highly relevant projects **outside** global top 100

| Repo | Role | Verified source license/status | Next evidence |
| --- | --- | --- | --- |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | HTML/CSS scripted motion graphics for premium offers, typography, reusable ad templates without diffusion GPU | Apache-2.0; CLI HTML→MP4 | Team A offline render: portrait 30s, memory/CPU/ffprobe, brand typography |
| [OpenCut-app/OpenCut](https://github.com/OpenCut-app/OpenCut) | Web video timeline editor; clip ordering/trimming/preview UI | MIT, undergoing core rewrite; older classic archive | Team B UI comparison, import complexity/mobile save/restore; do not reuse unstable new API before proof |
| [huggingface/diffusers](https://github.com/huggingface/diffusers) | Direct model pipeline serving option instead of ComfyUI for narrow paid GPU worker | Apache-2.0 code, individual checkpoint licenses separate | Team A compare 5s T2V/I2V workload ComfyUI vs Diffusers after approval |
| [modelscope/FunClip](https://github.com/modelscope/FunClip) | Subtitle-aligned automated clipping for uploaded *existing* footage | MIT code; model & media licenses separately | Team C recorded voice/footage benchmark and Hindi/English quality |
| [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) | Full agentic video-production alternative to MoneyPrinterTurbo | AGPL-3.0; avoid incorporation without legal approval | Team A architecture comparison only |
| [tryonlabs/opentryon](https://github.com/tryonlabs/opentryon) | Clothing-specific virtual try-on and video model registry; differentiator for fashion retailers | CC BY-NC 4.0 — not automatically usable in commercial SaaS | Study research only, licensing permission needed for commercial code reuse |

## Suggested integration architecture

RetailGrowthAI existing secure Supabase JWT/RLS/quotas -> Azure durable outbox/claim-fenced job -> choose either **(a) FFmpeg / MoneyPrinterTurbo standard video composition**, **(b) HyperFrames animation composition**, or **(c) private ComfyUI or Diffusers GPU worker for true T2V/I2V** -> ffprobe + private media upload -> existing review/download -> existing disabled-until-approved Part 2 publishing. **Do not deploy all alternatives by default.**

### Incremental priorities

1. **Team A:** Compare ComfyUI isolated/offline JSON workflow and current Part 3 provider APIs; no paid GPU/model download. Preserve current Wan branch. Compare MPT whole Docker versus module ports. Add one HyperFrames CPU-only motion typography benchmark (no renderer replacement by default).
2. **Team B:** Prototype published React Konva/Fabric poster canvas and select shadcn/ui components; optionally study OpenCut's editor as a separate timeline spike.
3. **Team C:** Assess FunClip/PySceneDetect/faster-whisper for merchant-owned clips, licensed stock data and provenance. Do not use yt-dlp/Firecrawl as rights substitutes.
4. **Final Coordinator:** Source-license and weight-license matrix; cost/VRAM/quality acceptance; self-hosted GPU idle/scaling behavior; preserve #249 ingress blocker; insist on independent 4/4 CI, signed tenant-private media, no hosted/provider activation without owner approval.

## Complete 100-repo scan (snapshot)

| Rank | Repository | RetailGrowthAI assessment |
| ---: | --- | --- |
| 1 | [codecrafters-io/build-your-own-x](https://github.com/codecrafters-io/build-your-own-x) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 2 | [sindresorhus/awesome](https://github.com/sindresorhus/awesome) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 3 | [public-apis/public-apis](https://github.com/public-apis/public-apis) | C: REFERENCE — API discovery, not verified royalty-free asset rights |
| 4 | [freeCodeCamp/freeCodeCamp](https://github.com/freeCodeCamp/freeCodeCamp) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 5 | [EbookFoundation/free-programming-books](https://github.com/EbookFoundation/free-programming-books) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 6 | [openclaw/openclaw](https://github.com/openclaw/openclaw) | Coordinator: REFERENCE — broad agent host security/complexity |
| 7 | [morluto/rea](https://github.com/morluto/rea) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 8 | [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 9 | [nilbuild/developer-roadmap](https://github.com/nilbuild/developer-roadmap) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 10 | [jwasham/coding-interview-university](https://github.com/jwasham/coding-interview-university) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 11 | [awesome-selfhosted/awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 12 | [vinta/awesome-python](https://github.com/vinta/awesome-python) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 13 | [obra/superpowers](https://github.com/obra/superpowers) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 14 | [mattpocock/skills](https://github.com/mattpocock/skills) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 15 | [affaan-m/ECC](https://github.com/affaan-m/ECC) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 16 | [practical-tutorials/project-based-learning](https://github.com/practical-tutorials/project-based-learning) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 17 | [996icu/996.ICU](https://github.com/996icu/996.ICU) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 18 | [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 19 | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 20 | [torvalds/linux](https://github.com/torvalds/linux) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 21 | [trimstray/the-book-of-secret-knowledge](https://github.com/trimstray/the-book-of-secret-knowledge) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 22 | [react/react](https://github.com/react/react) | B: EXISTING — frontend already React 19; no framework replacement |
| 23 | [TheAlgorithms/Python](https://github.com/TheAlgorithms/Python) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 24 | [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 25 | [anomalyco/opencode](https://github.com/anomalyco/opencode) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 26 | [vuejs/vue](https://github.com/vuejs/vue) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 27 | [ossu/computer-science](https://github.com/ossu/computer-science) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 28 | [n8n-io/n8n](https://github.com/n8n-io/n8n) | Coordinator: REFERENCE — Sustainable Use License prevents unlicensed SaaS embedding |
| 29 | [DigitalPlatDev/FreeDomain](https://github.com/DigitalPlatDev/FreeDomain) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 30 | [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) | C: RESTRICT — no independent rights to copyrighted video |
| 31 | [tensorflow/tensorflow](https://github.com/tensorflow/tensorflow) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 32 | [trekhleb/javascript-algorithms](https://github.com/trekhleb/javascript-algorithms) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 33 | [massgravel/Microsoft-Activation-Scripts](https://github.com/massgravel/Microsoft-Activation-Scripts) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 34 | [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) | C: REFERENCE — AGPL; web crawling is not licensed stock sourcing |
| 35 | [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 36 | [microsoft/vscode](https://github.com/microsoft/vscode) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 37 | [microsoft/markitdown](https://github.com/microsoft/markitdown) | C: OPTIONAL — ingestion of uploaded business documents |
| 38 | [avelino/awesome-go](https://github.com/avelino/awesome-go) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 39 | [ohmyzsh/ohmyzsh](https://github.com/ohmyzsh/ohmyzsh) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 40 | [Significant-Gravitas/AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) | Coordinator: REFERENCE — agent workflow ideas; not a drop-in replacement |
| 41 | [jackfrued/Python-100-Days](https://github.com/jackfrued/Python-100-Days) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 42 | [CyC2018/CS-Notes](https://github.com/CyC2018/CS-Notes) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 43 | [getify/You-Dont-Know-JS](https://github.com/getify/You-Dont-Know-JS) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 44 | [ollama/ollama](https://github.com/ollama/ollama) | A: OPTIONAL — local text copy/planning inference; not T2V/I2V |
| 45 | [521xueweihan/HelloGitHub](https://github.com/521xueweihan/HelloGitHub) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 46 | [anthropics/skills](https://github.com/anthropics/skills) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 47 | [flutter/flutter](https://github.com/flutter/flutter) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 48 | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 49 | [github/gitignore](https://github.com/github/gitignore) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 50 | [twbs/bootstrap](https://github.com/twbs/bootstrap) | B: SKIP — avoid adding second design system |
| 51 | [f/prompts.chat](https://github.com/f/prompts.chat) | A: REFERENCE — prompts/inspiration; check content rights |
| 52 | [huggingface/transformers](https://github.com/huggingface/transformers) | A: SUPPORT — Apache-2.0 model infrastructure, not a video model itself |
| 53 | [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) | B: ALTERNATE — static image workflows; complex dependencies |
| 54 | [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 55 | [jlevy/the-art-of-command-line](https://github.com/jlevy/the-art-of-command-line) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 56 | [langgenius/dify](https://github.com/langgenius/dify) | Coordinator: REFERENCE — modified Apache terms restrict multi-tenant usage |
| 57 | [Snailclimb/JavaGuide](https://github.com/Snailclimb/JavaGuide) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 58 | [open-webui/open-webui](https://github.com/open-webui/open-webui) | Coordinator: REFERENCE — model chat UI, not retail campaign UI |
| 59 | [langflow-ai/langflow](https://github.com/langflow-ai/langflow) | Coordinator: REFERENCE — workflow graph; potential duplication of agents |
| 60 | [clash-verge-rev/clash-verge-rev](https://github.com/clash-verge-rev/clash-verge-rev) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 61 | [anthropics/claude-code](https://github.com/anthropics/claude-code) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 62 | [Genymobile/scrcpy](https://github.com/Genymobile/scrcpy) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 63 | [farion1231/cc-switch](https://github.com/farion1231/cc-switch) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 64 | [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | A: LOW — would duplicate planner orchestration |
| 65 | [airbnb/javascript](https://github.com/airbnb/javascript) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 66 | [x1xhlol/system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 67 | [vercel/next.js](https://github.com/vercel/next.js) | B: SKIP — migration from Vite has no demonstrated value |
| 68 | [yangshun/tech-interview-handbook](https://github.com/yangshun/tech-interview-handbook) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 69 | [Shubhamsaboo/awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) | Coordinator: REFERENCE — useful example catalog, not runtime code |
| 70 | [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) | A: HIGH — model workflow backend; GPU required; GPL-3.0 review |
| 71 | [github/spec-kit](https://github.com/github/spec-kit) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 72 | [iptv-org/iptv](https://github.com/iptv-org/iptv) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 73 | [ytdl-org/youtube-dl](https://github.com/ytdl-org/youtube-dl) | C: RESTRICT — media extraction != licensed footage |
| 74 | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | B: REFERENCE — design guidance, not production editor |
| 75 | [ripienaar/free-for-dev](https://github.com/ripienaar/free-for-dev) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 76 | [microsoft/PowerToys](https://github.com/microsoft/PowerToys) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 77 | [golang/go](https://github.com/golang/go) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 78 | [garrytan/gstack](https://github.com/garrytan/gstack) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 79 | [labuladong/fucking-algorithm](https://github.com/labuladong/fucking-algorithm) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 80 | [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 81 | [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | A: HIGH — complete automated videos or MIT module reuse |
| 82 | [excalidraw/excalidraw](https://github.com/excalidraw/excalidraw) | B: IDEAS — sketch editor; not production retail image compositor |
| 83 | [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | A: OPTIONAL — low-cost LLM backend; not a video generator |
| 84 | [krahets/hello-algo](https://github.com/krahets/hello-algo) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 85 | [openai/codex](https://github.com/openai/codex) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 86 | [Chalarangelo/30-seconds-of-code](https://github.com/Chalarangelo/30-seconds-of-code) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 87 | [kubernetes/kubernetes](https://github.com/kubernetes/kubernetes) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 88 | [rustdesk/rustdesk](https://github.com/rustdesk/rustdesk) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 89 | [react/react-native](https://github.com/react/react-native) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 90 | [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | B: HIGH — MIT UI components for preview/editor/admin |
| 91 | [Hack-with-Github/Awesome-Hacking](https://github.com/Hack-with-Github/Awesome-Hacking) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 92 | [electron/electron](https://github.com/electron/electron) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 93 | [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) | B: REFERENCE — design-system templates |
| 94 | [nodejs/node](https://github.com/nodejs/node) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 95 | [microsoft/generative-ai-for-beginners](https://github.com/microsoft/generative-ai-for-beginners) | Coordinator: REFERENCE — training material only |
| 96 | [rust-lang/rust](https://github.com/rust-lang/rust) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 97 | [justjavac/free-programming-books-zh_CN](https://github.com/justjavac/free-programming-books-zh_CN) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 98 | [browser-use/browser-use](https://github.com/browser-use/browser-use) | C: RESTRICT — browser automation; do not replace official publishing or crawl unlicensed media |
| 99 | [2dust/v2rayN](https://github.com/2dust/v2rayN) | No direct reusable capability prioritized; general development/reference ecosystem or unrelated scope |
| 100 | [godotengine/godot](https://github.com/godotengine/godot) | A: LOW — real-time graphics engine, excessive for 30-sec reels |

## Important guardrails

- Internal testing does not automatically waive licenses for a future commercial multi-tenant SaaS. GitHub repository code license and model weights/stock/voices each require separate verification.
- GPU model generation is not free even when ComfyUI or Diffusers is free; Azure quotas/VRAM, spin-up times, batch utilization and tenant isolation must be benchmarked.
- Never route shop photos directly to public ComfyUI or to paid nodes without verified consent and private staging.
- This GitHub scan is research only, not evidence the code has been installed, compiled or accepted. Existing Part 1 cloud 30-second FFmpeg success stands; Azure ingress P0 #249 is still open.
