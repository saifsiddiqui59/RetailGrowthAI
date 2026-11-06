# Kokoro ONNX authentic reused code

GitHub: https://github.com/thewh1teagle/kokoro-onnx at commit `3596b26764286a7de9d90c363e988d50578918e5`, PyPI `kokoro-onnx==0.6.1`, MIT. Actual unchanged upstream `examples/save.py` and MIT LICENSE included. Feature2 `feature2_kokoro_local.synthesize_local` imports the REAL upstream `kokoro_onnx.Kokoro` class and invokes `create(text, voice, speed, lang)` directly; it does NOT recreate or fake ONNX model inference.

Model from official release `model-files-v1.1`:
- `kokoro-v1.0.int8.onnx` 114119327 bytes SHA-256 `ae315a79b623f244700e4afb9246c46a26066782e049ba174bf3ba433970ee9c`
- `voices-v1.0.bin` 28214398 bytes SHA-256 `bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d`

Model files are Apache-2.0 by original `hexgrad/Kokoro-82M` card; do not assume voice/phonemizer dependency licensing reviewed. Weight bytes are NOT committed and must be present in an operator-created read-only local model cache; verification fails closed before inference on mismatched SHA, no per-request downloads. CPU-only ONNX provider. This v1.0 model has **English US/UK only** supported voice allowlist; do not advertise native Indian English, Hindi or Marathi from it. For those, require a separately approved compatible engine or Azure Speech with explicit paid consent.
