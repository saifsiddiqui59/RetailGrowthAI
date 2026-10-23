"""Azure Queue host/producer contract: no mixed raw/base64 message encoding."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HOST=ROOT/"azure-functions"/"campaign-api"/"host.json"
ADAPTER=ROOT/"azure-functions"/"campaign-api"/"queue_adapter.py"

def test_queue_trigger_extension_bundle_matches_runtime():
    host=json.loads(HOST.read_text())
    assert host["extensionBundle"] == {
        "id": "Microsoft.Azure.Functions.ExtensionBundle",
        "version": "[4.0.0, 5.0.0)",
    }
    assert host["version"]=="2.0"
    assert host["functionTimeout"]=="00:20:00"

def test_raw_uuid_queue_transport_has_explicit_none_decoder():
    host=json.loads(HOST.read_text())
    assert host["extensions"]["queues"]["messageEncoding"]=="none"
    assert host["extensions"]["queues"]["maxDequeueCount"]==8
    source=ADAPTER.read_text()
    assert "self.client.send_message(campaign_id)" in source
    assert "TextBase64EncodePolicy" not in source
    assert 'QUEUE_NAME = "retail-campaign-planning"' in source
    assert 'queue_name="retail-reel-render"' in source
