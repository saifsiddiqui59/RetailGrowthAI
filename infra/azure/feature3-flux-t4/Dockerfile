# Reproducible source recipe for a SINGLE, manual FLUX.2 Klein 4B run.
# No model weights, licensed retailer images, Azure tokens or secrets in image.
# CUDA image tag validated in public PyTorch registry; pin digest before paid release.
FROM pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    DIFFUSERS_OFFLINE=1 \
    HF_HOME=/tmp/rgai-hf \
    MPLCONFIGDIR=/tmp/rgai-mpl \
    HOME=/tmp
WORKDIR /opt/retailgrowthai
# No Git-based requirements or model downloads at build time.
RUN python -m pip install --no-cache-dir \
    "diffusers==0.37.1" \
    "transformers==4.57.3" \
    "accelerate==1.12.0" \
    "safetensors==0.7.0" \
    "huggingface-hub==0.36.0" \
    "Pillow==13.0.0"
COPY poster-engine/ /opt/retailgrowthai/poster-engine/
# Linux coreutils watchdog kills hung CUDA kernels after a bounded wall time.
# Azure Container Apps Job replicaTimeout must ALSO be <= 900s on deployment.
RUN test -x /usr/bin/timeout
# Current GPU Container Apps runtime disallows root.
USER 10001:10001
ENTRYPOINT ["/usr/bin/timeout", "--signal=TERM", "--kill-after=15s", "900s", "python", "/opt/retailgrowthai/poster-engine/flux_t4_container_entrypoint.py"]
CMD ["--weights", "/mnt/private/models/FLUX.2-klein-4B", "--approval", "/mnt/private/models/approval-manifest.json", "--request", "/mnt/private/jobs/input.json", "--output", "/mnt/private/jobs/unreviewed-output"]
