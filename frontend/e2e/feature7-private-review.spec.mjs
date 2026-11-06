/**
 * Feature7 ACTUAL Chromium browser QA, isolated inside existing mocked frontend E2E.
 * Imports the real committed F7 modules (no fake DOM, no duplicate editor).
 * Does not mount hosted Feature4, authenticate JWT, grant retailer rights, render,
 * access customer media, or call paid APIs. Hashes are review hints, NOT approval.
 */
import {test,expect} from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
import {fileURLToPath} from 'node:url'

const origin='http://127.0.0.1:5173'
const moduleDir=path.resolve(path.dirname(fileURLToPath(import.meta.url)),
  '../../video-engine/feature7')
const allowed=new Set([
  'autobroll_semantics.mjs','sha256_sync.mjs','review_actions.mjs',
  'caption_corrections.mjs','reviewer_panel.mjs','reviewer_panel.css'
])
const html=String.raw`<!doctype html><html lang="en"><head>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Feature7 isolated review-only browser test</title>
<link rel="stylesheet" href="/__f7/reviewer_panel.css"/>
</head><body><main id="review"></main><script type="module">
import {proposeUploadedFootageEdits} from '/__f7/autobroll_semantics.mjs';
import {mountFeature7ReviewPanel} from '/__f7/reviewer_panel.mjs';
const query=new URLSearchParams(location.search);
const role=query.get('role')==='VIEWER'?'VIEWER':'EDITOR';
const shop='browser-offline-shop',campaign='browser-test';
const draft={shop_id:shop,campaign_id:campaign,duration_seconds:15,
 scenes:[{asset_id:'offline_video_a',asset_type:'video',source_feature:'retailer',
 duration:15,start:0}]};
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
const evidence=[{asset_id:'offline_video_a',
 local_media_verified:'LOCAL_BYTES_VERIFIED',
 source_sha256:'a'.repeat(64),source_duration_seconds:20}];
const cap={version:'feature7_autoclip_autobroll_caption_projection_v1',
 shop_id:shop,asset_id:'offline_video_a',approved:false,renderable:false,
 human_review_required:true,actual_timeline_duration_ms:14940,
 feature4_caption_track:[{start:1,duration:.8,text:'Hello world'}]};
window.__reviewRequests=[];window.__captionRequests=[];
window.__reviewDeferred=[];window.__captionDeferred=[];
window.__url=URL.createObjectURL(new Blob(['test-only-no-audio'],{type:'video/mp4'}));
const app=mountFeature7ReviewPanel({target:document.getElementById('review'),
 draft,proposal:plan,media_evidence:evidence,reviewer_view:reviewer,
 trusted_media_object_urls:{offline_video_a:window.__url},
 caption_correction_input:{shop_id:shop,asset_id:'offline_video_a',
 source_sha256:'a'.repeat(64),preview_sha256:'b'.repeat(64),
 caption_projection:cap},
 onReviewRequest:p=>{
   window.__reviewRequests.push(p);
   return new Promise((resolve,reject)=>window.__reviewDeferred.push({resolve,reject}));
 },
 onCaptionReviewRequest:p=>{
   window.__captionRequests.push(p);
   return new Promise((resolve,reject)=>window.__captionDeferred.push({resolve,reject}));
 }});
window.__snapshot=()=>app.getReviewSnapshot();
window.__dispose=()=>{app.destroy();URL.revokeObjectURL(window.__url)};
window.__ready=true;
</script></body></html>`

async function openReviewer(page,{role='EDITOR',width=390}={}){
  await page.setViewportSize({width,height:844})
  const browserErrors=[]
  page.on('pageerror',e=>browserErrors.push(e.message))
  await page.route(origin+'/__f7/**',async route=>{
    const url=new URL(route.request().url())
    if(url.pathname==='/__f7/review')
      return route.fulfill({status:200,contentType:'text/html; charset=utf-8',body:html})
    const name=url.pathname.slice('/__f7/'.length)
    if(!allowed.has(name))throw new Error('Unexpected Feature7 browser module '+name)
    const ext=name.endsWith('.css')?'text/css':'text/javascript'
    return route.fulfill({status:200,contentType:ext+'; charset=utf-8',
      body:fs.readFileSync(path.join(moduleDir,name),'utf8')})
  })
  await page.goto('/__f7/review?role='+role)
  await page.waitForFunction(()=>window.__ready===true)
  expect(browserErrors).toEqual([])
  return browserErrors
}

test('F7 actual mobile Chromium: keyboard approval and caption edits stay review-only',
 async({page})=>{
  await openReviewer(page)
  await expect(page.getByRole('heading',{name:'Review AI video edits'})).toBeVisible()
  const approve=page.getByRole('button',{name:'Request human approval'})
  await approve.click()
  expect(await page.evaluate(()=>window.__reviewRequests.length)).toBe(0)
  const confirm=page.getByRole('checkbox',{
    name:'I have reviewed the selected clip and original speech audio.'})
  await confirm.focus()
  await page.keyboard.press('Space')
  await expect(confirm).toBeChecked()
  await approve.focus();await page.keyboard.press('Enter')
  await expect(approve).toBeDisabled()
  expect(await page.evaluate(()=>window.__reviewRequests.length)).toBe(1)
  const editor=page.getByRole('textbox',{name:'Corrected caption text'})
  await editor.fill('Hello retailer')
  await page.getByRole('button',{name:'Save caption suggestion'}).click()
  await page.getByRole('checkbox',{
    name:'I checked the corrected words against the actual speaker.'}).check()
  const captions=page.getByRole('button',{name:'Request caption correction review'})
  await captions.click()
  await expect(captions).toBeDisabled()
  expect(await page.evaluate(()=>window.__captionRequests.length)).toBe(1)
  expect(await page.evaluate(()=>window.__reviewRequests[0].approved)).toBe(false)
  expect(await page.evaluate(()=>window.__captionRequests[0].approved)).toBe(false)
  expect(await page.evaluate(()=>window.__snapshot().approved)).toBe(false)
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=400)).toBe(true)
  await page.evaluate(()=>window.__dispose())
})

test('F7 actual Chromium: VIEWER cannot submit approval or caption changes',
 async({page})=>{
  await openReviewer(page,{role:'VIEWER',width:375})
  await expect(page.getByRole('button',{name:'Request human approval'})).toBeDisabled()
  await expect(page.getByRole('textbox',{name:'Corrected caption text'})).toBeDisabled()
  await expect(page.getByRole('button',{name:'Request caption correction review'})).toBeDisabled()
  expect(await page.evaluate(()=>window.__reviewRequests.length)).toBe(0)
  expect(await page.evaluate(()=>window.__captionRequests.length)).toBe(0)
  await page.evaluate(()=>window.__dispose())
})

test('F7 actual Chromium: stale async errors cannot re-open a newer review',
 async({page})=>{
  await openReviewer(page)
  const confirm=page.getByRole('checkbox',{
    name:'I have reviewed the selected clip and original speech audio.'})
  const approve=page.getByRole('button',{name:'Request human approval'})
  await confirm.check();await approve.click()
  expect(await page.evaluate(()=>window.__reviewRequests.length)).toBe(1)
  const slider=page.getByRole('slider',{name:'Adjust video trim start'})
  await slider.evaluate(el=>{el.value='1';el.dispatchEvent(new Event('input',{bubbles:true}))})
  await expect(approve).toBeEnabled()
  await confirm.check();await approve.click()
  expect(await page.evaluate(()=>window.__reviewRequests.length)).toBe(2)
  await page.evaluate(()=>window.__reviewDeferred[0].reject(new Error('old failure')))
  await expect(approve).toBeDisabled()
  await page.evaluate(()=>window.__reviewDeferred[1].resolve(false))
  await expect(approve).toBeEnabled()
  await expect(page.getByText('Request rejected by trusted host. No approval was recorded.')).toBeVisible()
  expect(await page.evaluate(()=>window.__snapshot().approved)).toBe(false)
  await page.evaluate(()=>window.__dispose())
})

test('F7 actual Chromium: unmount stops retained callbacks and host revokes blob URL',
 async({page})=>{
  await openReviewer(page,{width:360})
  await expect(page.getByRole('region',{name:'Feature 7 media editing review'})).toBeVisible()
  await expect(page.getByRole('combobox',{name:'Caption to correct'})).toBeVisible()
  await page.evaluate(()=>{
    const root=document.querySelector('.rgai-f7-review')
    window.__retained=[...root.querySelectorAll('button'),
      root.querySelector('input[type=range]')]
  })
  expect(await page.evaluate(()=>fetch(window.__url).then(x=>x.ok,()=>false))).toBe(true)
  await page.evaluate(()=>window.__dispose())
  expect(await page.evaluate(()=>fetch(window.__url).then(x=>x.ok,()=>false))).toBe(false)
  await page.evaluate(()=>{
    for(const button of window.__retained.filter(x=>x.tagName==='BUTTON'))button.click()
    const slider=window.__retained.at(-1)
    slider.value='1';slider.dispatchEvent(new Event('input',{bubbles:true}))
  })
  expect(await page.evaluate(()=>window.__reviewRequests.length)).toBe(0)
  expect(await page.evaluate(()=>window.__captionRequests.length)).toBe(0)
  expect(await page.evaluate(()=>window.__snapshot().approved)).toBe(false)
})
