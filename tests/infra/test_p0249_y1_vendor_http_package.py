"""Offline archive and import-isolation guard regression tests."""
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"ops/p0249-y1-cutover"))
import vendor_http_package as v
from prepare_http_only import ORIGINAL,strip_only_background_triggers
class VendorTests(unittest.TestCase):
    def test_source_and_dependencies_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); deps=p/"deps"; deps.mkdir()
            (deps/"fake.py").write_text("x=1")
            source=p/"source.zip"; out=p/"out.zip"
            with ZipFile(source,"w") as z:
                z.writestr(v.MEMBER,strip_only_background_triggers(ORIGINAL.read_bytes()))
                z.writestr("function_app.py","app=None")
            v.build(source,deps,out)
            with ZipFile(out) as z:
                self.assertEqual(z.read("function_app.py"),b"app=None")
                self.assertEqual(z.read(v.PREFIX+"fake.py"),b"x=1")
    def test_path_guard(self):
        for n in ("../bad","/abs","a/../b","a\\b","a//b","C:/bad"):
            self.assertFalse(v.safe_name(n))
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); deps=p/"deps"; deps.mkdir()
            (deps/"bad").symlink_to(p/"missing")
            with ZipFile(p/"s.zip","w") as z:
                z.writestr(v.MEMBER,strip_only_background_triggers(ORIGINAL.read_bytes()))
            with self.assertRaisesRegex(ValueError,"SYMLINK"):
                v.build(p/"s.zip",deps,p/"o.zip")
            self.assertFalse((p/"o.zip").exists())
