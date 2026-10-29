#!/usr/bin/env python3
"""Only actual Kokoro ONNX model weights can produce this human voice sample.

--plan prints provenance without installing, downloading or writing anything.
--run requires verified local 114 MB official ONNX + 28 MB official voices.
No mock, silent PCM, Azure, private tenant or paid service can be mistaken
for Kokoro inference success.
"""
import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
try:
    import resource  # Linux process RSS includes native ONNX Runtime allocations
except ImportError:
    resource=None

from ai_agents.feature2_kokoro_local import (
    MODEL_NAME,VOICES_NAME,MODEL_SHA,VOICES_SHA,synthesize_local
)

EXAMPLES={
    "diwali":"Explore beautiful festive kurtis this Diwali. Visit our boutique for our new collection.",
    "boutique":"Discover elegant cotton kurtis and timeless styling at our boutique.",
    "restaurant":"Enjoy our freshly prepared weekend specials at the restaurant.",
}
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--plan",action="store_true")
    parser.add_argument("--run",action="store_true")
    parser.add_argument("--model-dir",default=None)
    parser.add_argument("--output-dir",default=None)
    parser.add_argument("--example",choices=tuple(EXAMPLES),default="diwali")
    parser.add_argument("--voice",choices=("af_heart","af_sarah","am_adam",
                                            "bf_emma","bm_george"),default="af_heart")
    parser.add_argument("--mp3",action="store_true")
    parser.add_argument("--worker-hourly-usd",type=float,default=None,
                        help="Operator-verified CPU worker USD/hour, optional")
    args=parser.parse_args()
    if args.plan==args.run:parser.error("Choose exactly one of --plan or --run")
    if args.worker_hourly_usd is not None and (
        not math.isfinite(args.worker_hourly_usd) or
        not 0<args.worker_hourly_usd<=100):
        parser.error("A finite, externally verified positive worker rate is required")
    if args.plan:
        print(json.dumps({"actual_inference_executed":False,"upstream":"thewh1teagle/kokoro-onnx",
            "mode":"CPU", "model_file":MODEL_NAME,"model_sha256":MODEL_SHA,
            "voices_file":VOICES_NAME,"voices_sha256":VOICES_SHA,
            "weights_downloaded_by_this_tool":False}))
        return
    if not args.model_dir or not args.output_dir:
        parser.error("--run requires --model-dir and --output-dir")
    out=Path(args.output_dir)
    if out.exists() and any(out.iterdir()):
        parser.error("Output directory must be fresh/empty to avoid overwriting customer media")
    out.mkdir(mode=0o700,parents=True,exist_ok=True)
    os.chmod(out,0o700)
    os.environ["RETAIL_FEATURE2_KOKORO_CPU_ENABLED"]="true"
    lang="en-gb" if args.voice.startswith(("bf_","bm_")) else "en-us"
    t0=time.perf_counter()
    cpu0=time.process_time()
    result=synthesize_local(text=EXAMPLES[args.example],voice_id=args.voice,
                            lang=lang,speed="normal",cache_dir=args.model_dir)
    if result["test_only"] or not result["actual_inference_verified"]:
        raise RuntimeError("No real Kokoro CPU inference proof")
    wav_path=out/"kokoro-cpu-original.wav"
    wav_path.write_bytes(result.pop("audio_wav"))
    os.chmod(wav_path,0o600)
    cpu_seconds=round(time.process_time()-cpu0,3)
    elapsed_seconds=round(time.perf_counter()-t0,3)
    peak_rss=(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
              if resource is not None and sys.platform.startswith("linux") else None)
    report={**result,"source_original_text_sha256":sha256(EXAMPLES[args.example].encode()).hexdigest(),
            "benchmark_elapsed_seconds":elapsed_seconds,
            "process_cpu_seconds":cpu_seconds,
            "peak_process_rss_kib_linux":peak_rss,
            "realtime_factor":round(result["cpu_elapsed_seconds"]/result["duration_seconds"],3),
            "synthesis_concurrency_limit":1,
            "compute_cost_basis":"Operator rate times single-worker measured elapsed; storage and idle cost excluded",
            "estimated_worker_compute_usd":(
                round(elapsed_seconds*args.worker_hourly_usd/3600,7)
                if args.worker_hourly_usd is not None else None),
            "output_wav":str(wav_path),"word_transcript_accuracy":"NOT_VERIFIED",
            "human_quality":"NOT_REVIEWED",
            "free_provider_api_cost_usd":0,
            "local_compute_and_storage_cost_usd":"NOT_MEASURED",
            "price_usd_per_worker_hour_operator_supplied":args.worker_hourly_usd}
    if args.mp3:
        dest=out/"kokoro-cpu-original.mp3"
        subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
                        "-y","-i",str(wav_path),"-vn","-codec:a","libmp3lame",
                        "-b:a","128k",str(dest)],timeout=90,check=True)
        os.chmod(dest,0o600)
        report["mp3_sha256"]=sha256(dest.read_bytes()).hexdigest()
        report["output_mp3"]=str(dest)
        mp3_probe=subprocess.run(["ffprobe","-v","error","-show_entries",
          "stream=codec_name:format=duration","-of","json",str(dest)],
          capture_output=True,text=True,timeout=15,check=True)
        mp3_info=json.loads(mp3_probe.stdout)
        if not any(st.get("codec_name")=="mp3" for st in mp3_info.get("streams",[])) \
            or float(mp3_info.get("format",{}).get("duration",0))<=0:
            raise RuntimeError("Optional Kokoro MP3 codec/duration evidence missing")
        report["mp3_duration_seconds"]=float(mp3_info["format"]["duration"])
    # Actual audio inspection using ffprobe, not assuming WAV success.
    probe=subprocess.run(["ffprobe","-v","error","-show_entries",
                          "stream=codec_name,sample_rate,channels",
                          "-of","json",str(wav_path)],
                         capture_output=True,text=True,timeout=15,check=True)
    codecs=json.loads(probe.stdout).get("streams",[])
    if len(codecs)!=1 or codecs[0].get("codec_name")!="pcm_s16le" or \
       codecs[0].get("sample_rate")!="24000":
        raise RuntimeError("Original Kokoro PCM speech fails ffprobe")
    (out/"kokoro-cpu-receipt.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":"REAL_LOCAL_KOKORO_CPU_WAV_GENERATED",
                      "sha256":report["audio_sha256"],
                      "seconds":report["duration_seconds"],
                      "inference_seconds":report["cpu_elapsed_seconds"],
                      "output_wav":report["output_wav"]}))
if __name__=="__main__": main()
