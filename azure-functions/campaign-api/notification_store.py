"""Service-role-only notification SQL RPC client. No direct browser access."""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from admin_store import backend_headers
from tenant_store import StorageUnavailable, canonical_uuid


class NotificationStore:
    def __init__(self, origin, secret, transport=None):
        if not isinstance(origin, str) or not origin.startswith("https://") or not secret:
            raise ValueError("server-only Supabase configuration required")
        self.origin, self.secret = origin.rstrip("/"), secret
        self.transport = transport or urlopen

    def _rpc(self, action, params):
        if action not in ("claim_notifications", "notification_recipients", "confirm_notification"):
            raise ValueError("unsupported email queue RPC")
        request = Request(self.origin + "/rest/v1/rpc/" + action,
            method="POST", data=json.dumps(params).encode(),
            headers={**backend_headers(self.secret),
                     "Accept": "application/json", "Content-Type": "application/json"})
        try:
            with self.transport(request, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, OSError, ValueError) as exc:
            raise StorageUnavailable("notification database unavailable") from exc

    def claim_notifications(self, limit):
        result = self._rpc("claim_notifications", {"p_limit": limit})
        if not isinstance(result, list):
            raise StorageUnavailable("invalid notification claim result")
        return result

    def notification_recipients(self, event_id, token):
        return self._rpc("notification_recipients",
                         {"p_event_id": canonical_uuid(event_id), "p_token": canonical_uuid(token)})

    def confirm_notification(self, event_id, token, success, error):
        result = self._rpc("confirm_notification",
                           {"p_event_id": canonical_uuid(event_id),
                            "p_token": canonical_uuid(token),
                            "p_success": bool(success), "p_error": error})
        if type(result) is not bool:
            raise StorageUnavailable("invalid notification confirmation result")
        return result
