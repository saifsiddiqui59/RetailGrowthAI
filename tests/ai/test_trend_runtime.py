from datetime import datetime, timezone
from ai_agents.trend_runtime import run_daily_collection
from ai_agents.seasonal_calendar import verified_event_rows

NOW = datetime(2026, 10, 26, 10, tzinfo=timezone.utc)

class Store:
    def __init__(self):
        self.days = set()
        self.snapshot = None
    def load(self, region):
        assert region == "IN"
        return self.snapshot
    def claim_day(self, region, day):
        if (region, day) in self.days: return False
        self.days.add((region, day))
        return True
    def save(self, region, snapshot):
        self.snapshot = snapshot


def test_atomic_day_claim_avoids_duplicate_collection_and_false_success():
    store = Store()
    calls = []
    first = run_daily_collection(NOW, store, environ={"RETAIL_TRENDS_GOOGLE_RSS_ENABLED": "1"},
        get=lambda url, *, timeout: (calls.append(url) or b"<rss><channel></channel></rss>"))
    second = run_daily_collection(NOW, store, environ={"RETAIL_TRENDS_GOOGLE_RSS_ENABLED": "1"},
        get=lambda url, *, timeout: (_ for _ in ()).throw(AssertionError("must not call")))
    assert len(calls) == 1
    assert first["state"] == "incomplete"  # empty RSS is incomplete, no invented trends
    assert second["state"] == "cached"
    assert second["snapshot"] == first["snapshot"]


def test_seasonal_source_is_opt_in_and_requires_government_evidence():
    rows = [
        {"event_id": "festival-x", "event": "A documented event",
         "date": "2026-11-01", "official_source_url": "https://dopt.gov.in/verified-release",
         "source_reviewed_at": "2026-10-25", "verification": "reviewed", "category": "clothing"},
        {"event": "Fake festival", "date": "2026-11-01",
         "official_source_url": "https://fake.example", "verification": "reviewed"},
        {"event": "Unreviewed", "date": "2026-11-01",
         "official_source_url": "https://dopt.gov.in/file", "verification": "pending"},
    ]
    items = verified_event_rows(rows, NOW)
    assert len(items) == 1 and items[0]["event"] == "A documented event"
    assert verified_event_rows([], NOW) == []


def test_verified_events_flow_into_ranked_tenant_recommendations_without_invented_dates():
    from ai_agents.trend_intelligence import collect, recommendations
    approved = [{
        "event_id": "event-reviewed-1",
        "event": "Saree fashion festival",
        "date": "2026-11-01",
        "official_source_url": "https://dopt.gov.in/verified-release",
        "source_reviewed_at": "2026-10-25",
        "verification": "reviewed",
        "category": "clothing",
        "language": "mr-IN",
    }]
    snapshot = collect(NOW, environ={}, festival_records=approved)
    assert snapshot["sources"][-1]["status"] == "ok"
    assert len(snapshot["trends"]) == 1
    assert snapshot["trends"][0]["event_date"] == "2026-11-01"
    ranking = recommendations(snapshot, {
        "category": "clothing", "city": "Pune", "language": "mr-IN",
        "products": ["saree"],
    }, NOW)
    assert ranking[0]["event_date"] == "2026-11-01"
    assert ranking[0]["evidence_url"].startswith("https://dopt.gov.in/")
    assert ranking[0]["approval_status"] == "DRAFT"
    fake = [{**approved[0], "official_source_url": "https://fake.gov.in.evil.com/festival"}]
    rejected = collect(NOW, environ={}, festival_records=fake)
    assert rejected["trends"] == []
    assert rejected["sources"][-1]["status"] == "incomplete"


def test_calendar_dates_without_recent_verified_review_are_never_promoted():
    base = {
        "event_id": "event-1", "event": "Saree fashion festival",
        "date": "2026-11-01", "official_source_url": "https://dopt.gov.in/file",
        "verification": "reviewed", "category": "clothing",
    }
    assert verified_event_rows([{**base, "source_reviewed_at": "bad"}], NOW) == []
    assert verified_event_rows([{**base, "source_reviewed_at": "2027-01-01"}], NOW) == []
    assert verified_event_rows([{**base, "source_reviewed_at": "2025-01-01"}], NOW) == []
