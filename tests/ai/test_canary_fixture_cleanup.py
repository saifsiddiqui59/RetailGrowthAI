"""Tenant-safe test fixture cleanup checks cover generated MP4 as well as PNG."""
from pathlib import Path
from uuid import uuid4
import importlib.util
import pytest

root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("retail_dev_canary_cleanup",
    root/"tests"/"e2e"/"retail_dev_canary_once.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
SHOP=str(uuid4())

def asset(path,mime="image/png",source="UPLOAD",shop=SHOP):
    return {"storage_bucket":"retailgrowth-media","object_path":shop+"/"+path,
            "mime_type":mime,"source":source}

def test_cleanup_accepts_only_shop_scoped_test_png_and_generated_mp4():
    sample=[asset("uploads/"+str(uuid4())+".png"),
            asset("renders/"+str(uuid4())+"/"+str(uuid4())+".mp4",
                  "video/mp4","GENERATED")]
    paths=m.validate_private_test_paths(sample,SHOP)
    assert len(paths)==2
    assert all(p.startswith(SHOP+"/") for p in paths)

@pytest.mark.parametrize("bad",[
    lambda:asset("renders/r.mp4"),
    lambda:asset("uploads/foo.png","video/mp4","UPLOAD"),
    lambda:asset("uploads/foo.png","image/png","GENERATED"),
    lambda:asset("uploads/../foreign.png"),
    lambda:asset("uploads/a.png",shop=str(uuid4())),
    lambda:{**asset("uploads/a.png"),"storage_bucket":"other-project-media"},
    lambda:{**asset("uploads/a.png"),"object_path":"https://outside.example/secret"},
])
def test_cleanup_rejects_unexpected_paths_or_assets(bad):
    with pytest.raises(RuntimeError):
        m.validate_private_test_paths([bad()],SHOP)

def test_cleanup_never_lists_unbounded_media():
    with pytest.raises(RuntimeError):
        m.validate_private_test_paths([asset("uploads/x.png")]*9,SHOP)
