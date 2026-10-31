"""Feature7 offline CPU benchmark aggregation, never an approval/cost quote.

Consumes actual per-job local Faster-Whisper metric receipts from trusted
private worker runs. Does not run cloud inference, download models, assume a
price, or synthesize a customer quality score from protocol test fixtures.
"""
from __future__ import annotations
from statistics import median
import math

class CpuBenchmarkInvalid(ValueError):
    pass

def aggregate_real_cpu_benchmarks(rows, *, operator_cpu_hourly_usd=None):
    if not isinstance(rows,list) or not 2<=len(rows)<=100:
        raise CpuBenchmarkInvalid("At least two independent real CPU jobs required")
    if operator_cpu_hourly_usd is not None and (
        type(operator_cpu_hourly_usd) not in (int,float) or
        not math.isfinite(operator_cpu_hourly_usd) or
        operator_cpu_hourly_usd<0 or operator_cpu_hourly_usd>100):
        raise CpuBenchmarkInvalid("Use an explicitly supplied finite hourly rate")
    durations,wall,memory=[],[],[]
    ids=set()
    for row in rows:
        if not isinstance(row,dict) or \
            row.get("version")!="feature7_faster_whisper_cpu_transcript_v1" or \
            row.get("engine")!="SYSTRAN/faster-whisper" or \
            row.get("word_timestamps_from_actual_model") is not True or \
            row.get("approved") is not False or \
            row.get("renderable") is not False or \
            row.get("word_accuracy_benchmarked") is not False or \
            row.get("peak_rss_is_process_high_watermark") is not True:
            raise CpuBenchmarkInvalid("Only unapproved real-model CPU worker metrics")
        values=(row.get("source_audio_duration_seconds"),
                row.get("actual_decode_wall_seconds"),
                row.get("process_peak_rss_bytes"))
        if not all(type(v) in (int,float) and math.isfinite(v) and v>0
                   for v in values):
            raise CpuBenchmarkInvalid("Actual duration, wall time and RSS needed")
        unique=row.get("verified_input_sha256")
        if not isinstance(unique,str) or len(unique)!=64 or \
           any(c not in '0123456789abcdef' for c in unique) or unique in ids:
            raise CpuBenchmarkInvalid("Distinct independently measured audio sources required")
        ids.add(unique)
        durations.append(values[0]);wall.append(values[1]);memory.append(values[2])
    total_audio=sum(durations)
    total_cpu_wall=sum(wall)
    result={
      "schema":"feature7_cpu_stt_benchmark_summary_v1",
      "job_count":len(rows),"distinct_audio_sources":len(ids),
      "aggregate_audio_seconds":round(total_audio,3),
      "aggregate_cpu_wall_seconds":round(total_cpu_wall,3),
      "measured_cpu_realtime_factor":round(total_cpu_wall/total_audio,4),
      "median_job_cpu_seconds":round(median(wall),3),
      "largest_process_peak_rss_bytes":int(max(memory)),
      "concurrent_cpu_jobs_tested":False,
      "model_word_error_rate_verified":False,
      "model_pronunciation_verified":False,
      "customer_accepted":False,
      "approximate_inference_only_usd":None
    }
    if operator_cpu_hourly_usd is not None:
        result["approximate_inference_only_usd"]=round(
            total_cpu_wall*operator_cpu_hourly_usd/3600,6)
        result["operator_cpu_hourly_usd"]=operator_cpu_hourly_usd
        result["includes_idle_storage_queue_network_overhead"]=False
    return result
