"""Use ACTUAL Feature3 pinned MIT model/garment stills for F5 GPU-OFF tests.

Do not use this fixture path in a hosted customer worker. In particular a
fictional model pose and separate shirt photo are NOT evidence that the model
wears that shirt; no paid request, renderer authorization or tenant permission
is created. The real Feature3 private-rights/lease resolver remains mandatory.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha1, sha256
from io import BytesIO
import os
from pathlib import Path
import stat
import tempfile

from PIL import Image

from .wan22_motion_adapter import WanCompatibilityError
from .infra.feature35_comfy_api_graphs import wan22_ti2v_5b, offline_graph_validate

ROOT=Path(__file__).resolve().parents[1]
PINNED="10140178cdb198ff17ad7b226c432bd63d732fc2"
ASSETS={
    "model_posture.jpg":"72a86a60280976ce5c73db9525d9648b54d1126a",
    "garment_front.jpg":"878fde8857f58862723f85d7f8bd723c65a8e498",
}
LICENSE_SHA="d246e4160c1d8c59bc9e99a90b095ec42ee5cec5"
TARGET=(704,1280)


def _git_blob(data):
    return sha1(("blob "+str(len(data))+"\0").encode()+data).hexdigest()


def _raw_original(root, name, sha, maximum):
    f=root/name
    if f.is_symlink() or not f.is_file():
        raise WanCompatibilityError("Untrusted Feature3 demo fixture path")
    before=f.stat(follow_symlinks=False)
    if (not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or
        not 0<before.st_size<=maximum):
        raise WanCompatibilityError("Invalid Feature3 original file identity")
    raw=f.read_bytes()
    after=f.stat(follow_symlinks=False)
    if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(
            after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):
        raise WanCompatibilityError("Feature3 source changed during read")
    if _git_blob(raw)!=sha:
        raise WanCompatibilityError("Feature3 original image/license Git SHA differs")
    return raw


@contextmanager
def stage_feature3_mit_fashion_test_input(*, fixture_dir, scratch_parent,
                                          source_manifest, validate_f3_manifest,
                                          verify_f3_image):
    """One test-only private first-frame, based on F3 real source-verified JPEG.

    Caller passes genuine F3 validators, NOT custom client-controlled checks.
    Produces immutable provenance and a Comfy GRAPH for structural tests only.
    Never overwrites any existing job output or makes provider HTTP calls.
    """
    if not callable(validate_f3_manifest) or not callable(verify_f3_image):
        raise WanCompatibilityError("Real Feature3 source verification required")
    try:
        m=validate_f3_manifest(source_manifest)
    except (KeyError,ValueError,TypeError) as exc:
        raise WanCompatibilityError("Invalid original Feature3 demo manifest") from exc
    if (type(m) is not dict or
        m.get("source_repository")!="Prompt-Haus/OpenVTO" or
        m.get("source_commit")!=PINNED or
        m.get("tenant_private") is not False or
        m.get("rights_approved_for_customer_publishing") is not False or
        m.get("virtual_tryon_generated_by_retailgrowth") is not False or
        m.get("feature5")!={"first_frame":"model_posture.jpg",
                            "garment":"garment_front.jpg",
                            "mode":"IMAGE_TO_VIDEO_INPUT_TEST_ONLY",
                            "provider_call_authorized":False,
                            "cost_reservation_authorized":False}):
        raise WanCompatibilityError("Source cannot be promoted to F5 production rights")
    rows={x.get("file"):x for x in m.get("assets",[]) if type(x) is dict}
    if (len(rows)!=3 or set(ASSETS)-set(rows) or
        rows["model_posture.jpg"].get("role")!="fictional_adult_model" or
        rows["garment_front.jpg"].get("role")!="synthetic_garment"):
        raise WanCompatibilityError("Missing original F3 model and garment references")
    root=Path(fixture_dir)
    if root.is_symlink() or not root.is_dir():
        raise WanCompatibilityError("Original F3 demo fixture directory absent")
    originals={}
    checks={}
    license_bytes=_raw_original(root,"LICENSE-OpenVTO.txt",LICENSE_SHA,8*1024)
    if not license_bytes.startswith(b"MIT License"):
        raise WanCompatibilityError("Feature3 MIT license notice missing")
    for name, gitsha in ASSETS.items():
        row=rows[name]
        if row.get("git_blob_sha1")!=gitsha:
            raise WanCompatibilityError("Wrong Feature3 original source identity")
        raw=_raw_original(root,name,gitsha,3*1024*1024)
        try:
            report=verify_f3_image(row,raw)
        except (KeyError,TypeError,ValueError) as exc:
            raise WanCompatibilityError("Feature3 original pixels rejected") from exc
        if (type(report) is not dict or report.get("sha256")!=sha256(raw).hexdigest()
            or report.get("file")!=name or report.get("git_blob_sha1")!=gitsha):
            raise WanCompatibilityError("Feature3 source verifier returned wrong evidence")
        originals[name]=raw
        checks[name]=report

    parent=Path(scratch_parent)
    if parent.is_symlink() or not parent.is_dir():
        raise WanCompatibilityError("Private F5 scratch parent required")
    with tempfile.TemporaryDirectory(prefix="f5-f3-mit-demo-",dir=parent) as td:
        dest=Path(td)
        os.chmod(dest,0o700)
        with Image.open(BytesIO(originals["model_posture.jpg"])) as original:
            rgb=original.convert("RGB")
            rgb.thumbnail(TARGET,Image.Resampling.LANCZOS)
            fitted=Image.new("RGB",TARGET,(24,24,24))
            fitted.paste(rgb,((TARGET[0]-rgb.width)//2,
                              (TARGET[1]-rgb.height)//2))
            stage=BytesIO()
            fitted.save(stage,format="PNG",optimize=True)
        path=dest/"feature3_mit_model_test_only.png"
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        try:
            with os.fdopen(fd,"wb") as stream:
                stream.write(stage.getvalue())
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        os.chmod(path,0o600)
        graph=wan22_ti2v_5b(prompt=(
            "OFFLINE STRUCTURAL TEST ONLY: fixed fictional adult model reference. "
            "The separate garment photograph is NOT shown as worn by this person. "
            "No real generated fashion footage, retailer approval or paid motion."
        ),seed=42,approved_input_file=path.name,width=704,height=1280,
                            frames=121,fps=24,output_prefix="rgai/feature5_demo_only")
        offline_graph_validate(graph)
        proof={
            "schema":"retailgrowth.feature5.real-f3-mit-demo-input.v1",
            "source_feature":"feature3",
            "source_commit":PINNED,
            "model_image_sha256":checks["model_posture.jpg"]["sha256"],
            "garment_image_sha256":checks["garment_front.jpg"]["sha256"],
            "source_model_git_blob_sha1":ASSETS["model_posture.jpg"],
            "source_garment_git_blob_sha1":ASSETS["garment_front.jpg"],
            "staged_first_frame_sha256":sha256(path.read_bytes()).hexdigest(),
            "staged_dimensions":[704,1280],
            "source_garment_is_separate_from_model":True,
            "model_wears_retailer_garment_verified":False,
            "actual_vton_inference_performed":False,
            "actual_wan_inference_performed":False,
            "requires_real_feature3_private_rights_reader":True,
            "provider_call_permitted":False,
            "cost_reservation_authorized":False,
            "publish_approved":False,
            "gpu_started":False,
        }
        yield path,graph,proof
