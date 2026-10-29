"""Optional ACTUAL Chromium/Playwright interaction for F7 review-only UI.

This is an independent local browser QA using committed Feature7 JS modules
served only on 127.0.0.1. It is not a hosted retailer login, JWT/RLS, real ASR,
customer media preview, F4 mount or commercial accessibility certification.
Skipped if Chromium or Python Playwright are not installed on the runner.
"""
from __future__ import annotations

import http.server
from pathlib import Path
import shutil
import threading
import unittest
from urllib.parse import urlsplit

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright=None

ROOT=Path(__file__).resolve().parents[2]
CHROME=shutil.which("chromium") or shutil.which("chromium-browser")

HTML=r"""<!doctype html><html lang="en"><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Private Feature7 reviewer — offline browser contract</title>
<link rel="stylesheet" href="/video-engine/feature7/reviewer_panel.css">
</head><body><main id="review"></main>
<script type="module">
import {proposeUploadedFootageEdits} from '/video-engine/feature7/autobroll_semantics.mjs';
import {mountFeature7ReviewPanel} from '/video-engine/feature7/reviewer_panel.mjs';
const query=new URLSearchParams(location.search);
const role=query.get('role')==='VIEWER'?'VIEWER':'EDITOR';
const shop='browser-offline-shop',campaign='browser-test';
const draft={shop_id:shop,campaign_id:campaign,duration_seconds:15,
 scenes:[{asset_id:'offline_video_a',asset_type:'video',source_feature:'retailer',duration:15,start:0}]};
const words=[{word:'Hello',startMs:1000,endMs:1300},
 {word:'world.',startMs:1400,endMs:1800}];
const plan=proposeUploadedFootageEdits({shop_id:shop,campaign_id:campaign,draft,
 footage:[{scene_index:0,asset_id:'offline_video_a',source_duration_seconds:20,
 has_audio:true,transcription_status:'verified_server',
 transcript_sha256:'a'.repeat(64),words,broll_candidates:[]}],
 grants:[{asset_id:'offline_video_a',shop_id:shop,issued_by:'trusted_server',
 source:'retailer_upload',rights_status:'APPROVED',active:true,
 media_type:'video',has_audio:true}]});
const reviewer={shop_id:shop,campaign_id:campaign,reviewer_id:'local-reviewer',
 active_membership:true,role,revision:3};
const evidence=[{asset_id:'offline_video_a',local_media_verified:'LOCAL_BYTES_VERIFIED',
 source_sha256:'a'.repeat(64),source_duration_seconds:20}];
const cap={version:'feature7_autoclip_autobroll_caption_projection_v1',
 shop_id:shop,asset_id:'offline_video_a',approved:false,renderable:false,
 human_review_required:true,actual_timeline_duration_ms:14940,
 feature4_caption_track:[{start:1,duration:.8,text:'Hello world'}]};
window.__reviewRequests=[];window.__captionRequests=[];
window.__reviewDeferred=[];window.__captionDeferred=[];
const deferred=query.get('async')==='1';
window.__url=URL.createObjectURL(new Blob(['test-only-no-audio'],{type:'video/mp4'}));
const app=mountFeature7ReviewPanel({target:document.getElementById('review'),
 draft,proposal:plan,media_evidence:evidence,reviewer_view:reviewer,
 trusted_media_object_urls:{'offline_video_a':window.__url},
 caption_correction_input:{shop_id:shop,asset_id:'offline_video_a',
 source_sha256:'a'.repeat(64),preview_sha256:'b'.repeat(64),
 caption_projection:cap},
 onReviewRequest:p=>{
   window.__reviewRequests.push(p);
   if(deferred)return new Promise((resolve,reject)=>window.__reviewDeferred.push({resolve,reject}));
 },
 onCaptionReviewRequest:p=>{
   window.__captionRequests.push(p);
   if(deferred)return new Promise((resolve,reject)=>window.__captionDeferred.push({resolve,reject}));
 }});
window.__snapshot=()=>app.getReviewSnapshot();
window.__dispose=()=>{app.destroy();URL.revokeObjectURL(window.__url)};
window.__ready=true;
</script></body></html>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_GET(self):
        if urlsplit(self.path).path=="/feature7-local-review-browser":
            encoded=HTML.encode("utf-8")
            self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(encoded)));self.end_headers()
            self.wfile.write(encoded)
            return
        return super().do_GET()
    def log_message(self,*args):pass

@unittest.skipUnless(sync_playwright and CHROME,
                     "Real local Chromium + Python Playwright not provisioned")
class Feature7ActualBrowserReviewQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=http.server.ThreadingHTTPServer(("127.0.0.1",0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.url=f"http://127.0.0.1:{cls.server.server_address[1]}/feature7-local-review-browser"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.thread.join(timeout=8);cls.server.server_close()

    def test_editor_keyboard_mobile_and_one_shot_caption_request(self):
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,executable_path=CHROME,
                                      args=["--no-sandbox"])
            try:
                page=browser.new_page(viewport={"width":390,"height":844})
                page.goto(self.url,wait_until="networkidle")
                page.wait_for_function("window.__ready===true")
                self.assertEqual(page.get_by_role("heading",name="Review AI video edits").count(),1)
                button=page.get_by_role("button",name="Request human approval")
                self.assertTrue(button.is_enabled())
                button.click()
                self.assertEqual(page.evaluate("window.__reviewRequests.length"),0)
                checkbox=page.get_by_role("checkbox",
                    name="I have reviewed the selected clip and original speech audio.")
                checkbox.focus();page.keyboard.press("Space")
                self.assertTrue(checkbox.is_checked())
                button.focus();page.keyboard.press("Enter")
                self.assertTrue(button.is_disabled())
                self.assertEqual(page.evaluate("window.__reviewRequests.length"),1)
                self.assertFalse(page.evaluate("window.__reviewRequests[0].approved"))
                textarea=page.get_by_role("textbox",name="Corrected caption text")
                textarea.fill("Hello retailer")
                page.get_by_role("button",name="Save caption suggestion").click()
                page.get_by_role("checkbox",
                  name="I checked the corrected words against the actual speaker.").check()
                caption=page.get_by_role("button",name="Request caption correction review")
                caption.click()
                self.assertEqual(page.evaluate("window.__captionRequests.length"),1)
                self.assertTrue(caption.is_disabled())
                self.assertFalse(page.evaluate("window.__captionRequests[0].approved"))
                self.assertFalse(page.evaluate("window.__snapshot().approved"))
                self.assertLessEqual(
                    page.evaluate("document.documentElement.scrollWidth"),
                    400,"Unexpected oversized mobile review panel")
                page.evaluate("window.__dispose()")
                self.assertEqual(page.locator("video[src]").count(),0)
            finally:browser.close()

    def test_viewer_cannot_make_edit_or_caption_requests(self):
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,executable_path=CHROME,
                                      args=["--no-sandbox"])
            try:
                page=browser.new_page(viewport={"width":375,"height":812})
                page.goto(self.url+"?role=VIEWER",wait_until="networkidle")
                page.wait_for_function("window.__ready===true")
                self.assertTrue(page.get_by_role("button",name="Request human approval").is_disabled())
                self.assertTrue(page.get_by_role("textbox",name="Corrected caption text").is_disabled())
                self.assertTrue(page.get_by_role("button",name="Request caption correction review").is_disabled())
                self.assertEqual(page.evaluate("window.__reviewRequests.length"),0)
                self.assertEqual(page.evaluate("window.__captionRequests.length"),0)
            finally:browser.close()


    def test_stale_async_failure_cannot_reopen_new_review_on_mobile(self):
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,executable_path=CHROME,
                                      args=["--no-sandbox"])
            try:
                page=browser.new_page(viewport={"width":390,"height":844})
                page.goto(self.url+"?async=1",wait_until="networkidle")
                page.wait_for_function("window.__ready===true")
                approval=page.get_by_role("button",name="Request human approval")
                confirm=page.get_by_role("checkbox",
                    name="I have reviewed the selected clip and original speech audio.")
                confirm.check();approval.click()
                self.assertEqual(page.evaluate("window.__reviewRequests.length"),1)
                self.assertTrue(approval.is_disabled())
                page.get_by_role("combobox",name="Choose uploaded source scene").dispatch_event("change")
                self.assertTrue(approval.is_disabled(),
                    "Changing selected scene must not double-submit an unchanged review")
                page.get_by_role("slider",name="Adjust video trim start").evaluate(
                    "(el)=>{el.value='1';el.dispatchEvent(new Event('input',{bubbles:true}))}")
                self.assertTrue(approval.is_enabled())
                confirm.check();approval.click()
                self.assertEqual(page.evaluate("window.__reviewRequests.length"),2)
                page.evaluate("window.__reviewDeferred[0].reject(new Error('old failure'))")
                page.wait_for_timeout(30)
                self.assertTrue(approval.is_disabled(),
                    "Old async failure must not unlock the newer pending request")
                page.evaluate("window.__reviewDeferred[1].reject(new Error('current failure'))")
                page.get_by_text("Request failed. No approval was recorded.").wait_for()
                self.assertTrue(approval.is_enabled())
                self.assertFalse(page.evaluate("window.__snapshot().approved"))
                page.evaluate("window.__dispose()")
            finally:browser.close()

if __name__=="__main__":unittest.main()
