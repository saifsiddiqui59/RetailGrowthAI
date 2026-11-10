"""One genuine Hunyuan sample brief, not pre-rendered media.

The 5-second, 480p portrait prompt is intentionally text-to-video so that
reviewers do not need to transfer customer/product photos across regions.
A generated clip MUST be produced by the separately licensed Hunyuan runner,
then ffprobed, hashed, stored privately and HUMAN reviewed.
"""
from .contracts import MotionSpec

FASHION_BRIEF_ID = "fashion-kurti-boutique-20261026"
FASHION_PROMPT = (
    "Cinematic full-body fashion commercial, one adult Indian female fashion "
    "model wearing a premium deep-red embroidered festive kurti and matching "
    "trousers, walking slowly and naturally toward the camera through an "
    "elegant luxury Indian boutique. The same consistent red fabric, detailed "
    "gold embroidered pattern and complete sleeves remain accurate throughout "
    "the shot. Natural human gait, coherent face and hands, realistic fabric "
    "folds and gentle dupatta movement. Warm chandelier lighting, polished "
    "beige marble floor, premium clothing displays softly out of focus in "
    "the background. Stable eye-level camera moving slightly backward, "
    "photorealistic commercial cinematography, continuous single take, "
    "no cuts, no subtitles, no watermarks."
)


def fashion_motion_spec(*, shop_id: str, job_id: str) -> MotionSpec:
    """Create one server-authoritative T2V spec; never user-supplied identity."""
    return MotionSpec(
        job_id=job_id, shop_id=shop_id, prompt=FASHION_PROMPT,
        mode="text", resolution="480p", aspect_ratio="9:16",
        duration_seconds=5, fps=24, seed=20261026,
    )
