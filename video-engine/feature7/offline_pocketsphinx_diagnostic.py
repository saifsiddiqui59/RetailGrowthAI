"""OPTIONAL genuine offline CPU ASR *benchmark*, never a production provider.

Uses system-installed CMU PocketSphinx native engine/model (NOT a newly
implemented recognizer). PocketSphinx accuracy must be measured on real voice
against a human transcript before considering it as any fallback. WhisperX
remains the proposed production CPU aligner. No network, GPU, model install
or customer upload/approval rights are provided by this diagnostic.
"""
from __future__ import annotations
import ctypes as ct
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess

SHA = re.compile(r"^[a-f0-9]{64}$")
TOKENS = re.compile(r"[a-z0-9]+(?:['’][a-z0-9]+)*")
ROOT = Path("/usr/share/pocketsphinx/model/en-us")

class CpuAsrBenchmarkError(ValueError):
    pass

def _words(text):
    return TOKENS.findall(text.casefold())

def word_error_rate(reference, hypothesis):
    a, b = _words(reference), _words(hypothesis)
    if not a or not b or len(a) > 3000 or len(b) > 3000:
        raise CpuAsrBenchmarkError("A human reference and bounded hypothesis are required")
    row = list(range(len(b) + 1))
    for i, token in enumerate(a, 1):
        newer = [i]
        for j, other in enumerate(b, 1):
            newer.append(min(newer[-1] + 1, row[j] + 1,
                             row[j-1] + (token != other)))
        row = newer
    return {"reference_words": len(a), "recognized_words": len(b),
            "word_edits": row[-1], "word_error_rate": round(row[-1] / len(a), 4)}

def _sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def benchmark_local_pocketsphinx(*, video_path, expected_sha256,
                                 human_reference_text, model_root=ROOT,
                                 max_word_error_rate=.25):
    """Run native decoder on actual WAV PCM; no stub transcript accepted."""
    src, root = Path(video_path), Path(model_root)
    if not src.is_absolute() or not root.is_absolute() or not isinstance(
        expected_sha256, str) or not SHA.fullmatch(expected_sha256):
        raise CpuAsrBenchmarkError("Trusted absolute media/model root and SHA256 required")
    source_st = src.lstat()
    if not stat.S_ISREG(source_st.st_mode) or stat.S_ISLNK(source_st.st_mode) or not (
        1000 < source_st.st_size < 128*1024*1024):
        raise CpuAsrBenchmarkError("Unsafe or oversized local media")
    if _sha(src) != expected_sha256:
        raise CpuAsrBenchmarkError("Source byte integrity mismatch")
    if not (isinstance(human_reference_text, str) and
            1 <= len(human_reference_text) <= 20000 and
            0 <= max_word_error_rate <= 1):
        raise CpuAsrBenchmarkError("Bounded human transcription and threshold required")
    paths = [root/"en-us", root/"en-us.lm.bin", root/"cmudict-en-us.dict"]
    if not all(x.exists() and not x.is_symlink() for x in paths):
        raise CpuAsrBenchmarkError("Preinstalled PocketSphinx English weights missing")
    try:
        # Strongly bounded extraction. Never writes WAV or human content to disk.
        pcm = subprocess.run(
            ["ffmpeg", "-hide_banner", "-v", "error", "-nostdin",
             "-i", str(src), "-vn", "-t", "120", "-ac", "1", "-ar", "16000",
             "-f", "s16le", "pipe:1"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45
        ).stdout
        if not (32000 <= len(pcm) <= 120*16000*2):
            raise CpuAsrBenchmarkError("Invalid decoded source speech duration")
        sph = ct.CDLL("libsphinxbase.so.3")
        ps = ct.CDLL("libpocketsphinx.so.3")
        ps.ps_args.restype = ct.c_void_p
        sph.cmd_ln_init.restype = ct.c_void_p
        ps.ps_init.restype = ct.c_void_p
        ps.ps_init.argtypes = [ct.c_void_p]
        ps.ps_start_utt.restype = ct.c_int
        ps.ps_start_utt.argtypes = [ct.c_void_p]
        ps.ps_process_raw.restype = ct.c_int
        ps.ps_process_raw.argtypes = [ct.c_void_p, ct.POINTER(ct.c_int16),
                                     ct.c_size_t, ct.c_int, ct.c_int]
        ps.ps_end_utt.restype = ct.c_int
        ps.ps_end_utt.argtypes = [ct.c_void_p]
        ps.ps_get_hyp.restype = ct.c_char_p
        ps.ps_get_hyp.argtypes = [ct.c_void_p, ct.c_void_p, ct.c_void_p]
        ps.ps_seg_iter.restype = ct.c_void_p
        ps.ps_seg_iter.argtypes = [ct.c_void_p, ct.c_void_p]
        ps.ps_seg_next.restype = ct.c_void_p
        ps.ps_seg_next.argtypes = [ct.c_void_p]
        ps.ps_seg_word.restype = ct.c_char_p
        ps.ps_seg_word.argtypes = [ct.c_void_p]
        ps.ps_seg_frames.argtypes = [ct.c_void_p, ct.POINTER(ct.c_int),
                                     ct.POINTER(ct.c_int)]
        ps.ps_free.argtypes = [ct.c_void_p]
        conf = sph.cmd_ln_init(
            ct.c_void_p(0), ct.c_void_p(ps.ps_args()), ct.c_int(1),
            ct.c_char_p(b"-hmm"), ct.c_char_p(str(paths[0]).encode()),
            ct.c_char_p(b"-lm"), ct.c_char_p(str(paths[1]).encode()),
            ct.c_char_p(b"-dict"), ct.c_char_p(str(paths[2]).encode()),
            ct.c_void_p(0))
        if not conf:
            raise CpuAsrBenchmarkError("Cannot initialize local decoder config")
        decoder = ps.ps_init(ct.c_void_p(conf))
        if not decoder:
            raise CpuAsrBenchmarkError("Cannot initialize native recognizer")
        try:
            samples = (ct.c_int16 * (len(pcm)//2)).from_buffer_copy(pcm)
            if ps.ps_start_utt(decoder) != 0 or ps.ps_process_raw(
                decoder, samples, len(samples), 0, 1) < 0 or ps.ps_end_utt(decoder) != 0:
                raise CpuAsrBenchmarkError("Genuine native ASR failed")
            hypothesis = ps.ps_get_hyp(decoder, None, None)
            if not hypothesis:
                raise CpuAsrBenchmarkError("No recognizable human words")
            spoken = hypothesis.decode("utf-8")
            # Native model emits frame-indexed lexical segments. These are
            # genuine *hypothesis* times, not forced human-SRT alignment.
            segments = []
            seg = ps.ps_seg_iter(decoder, None)
            while seg:
                st, en = ct.c_int(), ct.c_int()
                ps.ps_seg_frames(seg, ct.byref(st), ct.byref(en))
                text = ps.ps_seg_word(seg).decode("utf-8")
                if text not in ("<s>", "</s>", "<sil>", "[NOISE]"):
                    segments.append({
                        "word": re.sub(r"\\(\\d+\\)$", "", text),
                        "start_ms": max(0, st.value*10),
                        "end_ms": (en.value+1)*10
                    })
                seg = ps.ps_seg_next(seg)
        finally:
            ps.ps_free(decoder)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise CpuAsrBenchmarkError("Optional local PocketSphinx CPU unavailable") from exc
    if _sha(src) != expected_sha256:
        raise CpuAsrBenchmarkError("Source changed while decoding")
    score = word_error_rate(human_reference_text, spoken)
    return {
        "provider": "PocketSphinx native English CPU (diagnostic only)",
        "genuine_cpu_inference_executed": True, "hypothesis": spoken,
        **score, "meets_accuracy_threshold": score["word_error_rate"] <= max_word_error_rate,
        "no_gpu": True, "no_remote_model_calls": True,
        "recognized_word_frame_times": segments,
        "timing_source": "POCKETSPHINX_NATIVE_10MS_HYPOTHESIS",
        "word_level_alignment_verified": False,
        "model_weights_commercial_use_cleared": False,
        "customer_captioning_enabled": False,
        "release_approved": False,
    }
