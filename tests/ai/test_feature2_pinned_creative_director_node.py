"""Feature2 pinned MIT Creative Director regression gate (offline CPU, no providers).

This runs the ORIGINAL Node assertions extracted from #551 on every mandatory
Python CI pass; otherwise isolated ai-agents/creative-director/tests would not
run in the root Part1 workflow. No model weights, network or Azure required.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest

DIRECTOR = Path(__file__).resolve().parents[2] / "ai-agents" / "creative-director"
TESTS = (
    "tests/test-director.js",
    "tests/test-caption-preview.js",
    "tests/test-consumer-compat.js",
    "tests/test-diwali-offline-e2e.js",
    "tests/test-feature3-demo-interoperability.js",
    "tests/test-feature4-feature5-fixture.js",
    "tests/test-handoff-approval.js",
    "tests/test-unified-output.js",
    "upstream/scripts/test-explainer-cues.js",
    "upstream/scripts/test-explainer-plan.js",
    "upstream/scripts/test-explainer-scene.js",
)


@pytest.mark.parametrize("relative_path", TESTS)
def test_pinned_creative_director_original_node_assertions(relative_path: str) -> None:
    node = shutil.which("node")
    assert node is not None, "Node must be installed for the pinned MIT source gate"
    path = DIRECTOR / relative_path
    assert path.is_file(), f"Missing Creative Director test: {relative_path}"
    # This original integration assertion consumes an already compiled JSON
    # bundle on stdin. Generate it from the SAME pinned director and its
    # completely synthetic, source-only brief; never silently pass empty stdin.
    payload = None
    if relative_path == "tests/test-unified-output.js":
        make_payload = (
            "const {verifiedBrief,authoredCandidate}="
            "require('./tests/fixtures/diwali-premium-fixture');"
            "const {compile}=require('./director');"
            "const request=verifiedBrief(30);"
            "const candidate=authoredCandidate(30);"
            "const shop='11111111-1111-4111-8111-111111111111';"
            "const media='33333333-3333-4333-8333-333333333333';"
            "request.shop_id=shop;"
            "request.campaign_id='22222222-2222-4222-8222-222222222222';"
            "request.approved_offers[0].shop_id=shop;"
            "request.media_grants[0].shop_id=shop;"
            "request.media_grants[0].id=media;"
            "candidate.scenes.forEach(s=>s.shots.forEach(shot=>{"
            "shot.reference_asset_id=media;}));"
            "const bundle=compile(request,candidate);"
            "process.stdout.write(JSON.stringify({bundle,verified_brief:request,"
            "reviewer_id:'44444444-4444-4444-8444-444444444444'}));"
        )
        generated = subprocess.run(
            [node, "-e", make_payload],
            cwd=DIRECTOR, capture_output=True, text=True, timeout=45,
            check=False, env={"PATH": __import__("os").environ.get("PATH", "")},
        )
        assert generated.returncode == 0, (
            f"Synthetic pinned compiler failed: {generated.stderr[-2000:]}"
        )
        assert generated.stdout.strip(), "Synthetic compiler emitted no JSON"
        payload = generated.stdout
    output = subprocess.run(
        [node, str(path)],
        input=payload,
        cwd=DIRECTOR,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
        env={"PATH": __import__("os").environ.get("PATH", "")},
    )
    assert output.returncode == 0, (
        f"{relative_path} failed with exit {output.returncode}\n"
        f"STDOUT:\n{output.stdout[-3000:]}\nSTDERR:\n{output.stderr[-3000:]}"
    )
