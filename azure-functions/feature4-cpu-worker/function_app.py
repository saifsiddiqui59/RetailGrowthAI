"""Feature4 native CPU worker candidate, NOT in existing v1 Azure ZIP.

Release must package F4 HyperFrames/Node/FFmpeg and verified service-only
backend dependencies in a separate reviewed artifact. This source alone
does not provision queues or activate a cloud Function App.
"""
import os
import azure.functions as func
from admin_store import AdminStore

app = func.FunctionApp()

# F2→F4 CPU queue/timer are NOT indexed at all until a reviewed worker
# deployment explicitly enables the worker. The default existing DEV package
# does not require the new queue, migration or CPU cost.
if os.environ.get("RETAIL_FEATURE4_CPU_WORKER_ENABLED") == "true":
    def _feature4_cpu_dependencies():
        from private_media import PrivateMedia
        from queue_adapter import AzureFeature4CpuQueue
        origin = os.environ["RETAIL_SUPABASE_URL"]
        secret = os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"]
        connection = os.environ["RETAIL_STORAGE"]
        return (AdminStore(origin, secret),
                PrivateMedia(origin, secret),
                AzureFeature4CpuQueue(connection))

    @app.queue_trigger(
        arg_name="message", queue_name="retail-feature4-cpu-render",
        connection="RETAIL_STORAGE")
    def feature4_cpu_render_message(message: func.QueueMessage):
        from tenant_store import canonical_uuid
        from feature4_worker_handoff import process_feature4_cpu_render
        admin, media, _ = _feature4_cpu_dependencies()
        job_id = canonical_uuid(message.get_body().decode("ascii", "strict"))
        # A malformed queue message is never interpreted as a worker grant.
        process_feature4_cpu_render(job_id, admin, media)

    @app.queue_trigger(
        arg_name="message", queue_name="retail-feature4-cpu-render-poison",
        connection="RETAIL_STORAGE")
    def feature4_cpu_poison_message(message: func.QueueMessage):
        from recovery_runtime import record_feature4_cpu_poison
        admin, _, _ = _feature4_cpu_dependencies()
        # No job status or credit mutation from a possibly malformed payload.
        record_feature4_cpu_poison(admin, message.get_body())

    @app.timer_trigger(
        schedule="0 */2 * * * *", arg_name="timer", run_on_startup=False)
    def feature4_cpu_dispatch_timer(timer: func.TimerRequest):
        from recovery_runtime import reconcile_feature4_cpu
        admin, _, queue = _feature4_cpu_dependencies()
        reconcile_feature4_cpu(admin, queue)
