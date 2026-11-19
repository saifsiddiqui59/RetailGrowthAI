"""Do not report invented CPU throughput, RAM or hourly rates as real."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
    "video-engine"/"feature7"))
from cpu_stt_benchmark_report import aggregate_real_cpu_benchmarks,CpuBenchmarkInvalid

def sample(marker,duration,wall,rss):
    return {"version":"feature7_faster_whisper_cpu_transcript_v1",
       "engine":"SYSTRAN/faster-whisper",
       "word_timestamps_from_actual_model":True,
       "approved":False,"renderable":False,
       "word_accuracy_benchmarked":False,
       "peak_rss_is_process_high_watermark":True,
       "verified_input_sha256":marker*64,
       "source_audio_duration_seconds":duration,
       "actual_decode_wall_seconds":wall,
       "process_peak_rss_bytes":rss}

class CpuAggregateTests(unittest.TestCase):
    def test_aggregates_metrics_but_does_not_pretend_real_fixture_execution(self):
        # Representative TEST-ONLY accounting fixture, NOT a benchmark result.
        rows=[sample("a",10,3,512*1024**2),
              sample("b",20,9,615*1024**2)]
        out=aggregate_real_cpu_benchmarks(rows)
        self.assertEqual(out["job_count"],2)
        self.assertEqual(out["measured_cpu_realtime_factor"],.4)
        self.assertEqual(out["largest_process_peak_rss_bytes"],615*1024**2)
        self.assertFalse(out["model_word_error_rate_verified"])
        self.assertFalse(out["concurrent_cpu_jobs_tested"])
        self.assertIsNone(out["approximate_inference_only_usd"])

    def test_cost_requires_operator_supplied_hourly_rate(self):
        rows=[sample("a",10,3,200000000),
              sample("b",20,9,200000001)]
        out=aggregate_real_cpu_benchmarks(rows,operator_cpu_hourly_usd=1.5)
        self.assertEqual(out["approximate_inference_only_usd"],.005)
        self.assertFalse(out["includes_idle_storage_queue_network_overhead"])

    def test_rejects_mocks_duplicate_sources_unknown_rss_and_invalid_cost(self):
        first=sample("a",10,3,200000000)
        second=sample("b",20,9,200000001)
        attempts=[
            ([first],None),
            ([first,first],None),
            ([first,{**second,"process_peak_rss_bytes":None}],None),
            ([first,{**second,"word_timestamps_from_actual_model":False}],None),
            ([first,{**second,"approved":True}],None),
            ([first,{**second,"verified_input_sha256":"x"*64}],None),
            ([first,second],float("nan")),
            ([first,second],-2),
            ([first,second],"free")
        ]
        for rows,price in attempts:
            with self.subTest(rows=rows,price=price):
                with self.assertRaises(CpuBenchmarkInvalid):
                    aggregate_real_cpu_benchmarks(
                       rows,operator_cpu_hourly_usd=price)

if __name__=="__main__":
    unittest.main()
