import { test, expect } from '@playwright/test'
const SHOP='11111111-1111-4111-8111-111111111111'
async function mount(page, approved=false) {
 await page.goto('/')
 await page.evaluate(async ({shop,approved}) => {
  const fixture = await import('/e2e/fixtures/timeline-studio-harness.jsx')
  fixture.mountFeature4({shop,approved})
 },{shop:SHOP,approved})
 await expect(page.getByRole('heading',{name:'Professional Video Studio'})).toBeVisible()
}

test('real adapted Timeline Studio split/undo/redo and renderer-safe submission',async ({page})=>{
 await page.setViewportSize({width:1440,height:900})
 await mount(page)
 await expect(page.getByRole('region',{name:'Professional multi-track video timeline'})).toBeVisible()
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(3)
 // Select source scene: this seeks playhead to the center of its clip.
 await page.getByRole('button',{name:/Scene 1:/}).click()
 await page.getByRole('button',{name:'Split video at playhead'}).click()
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(4)
 await page.getByRole('button',{name:'Undo timeline edit'}).click()
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(3)
 await page.getByRole('button',{name:'Redo timeline edit'}).click()
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(4)
 await page.getByRole('button',{name:'Submit authorized render'}).click()
 await expect.poll(()=>page.evaluate(()=>window.__feature4Renders.length)).toBe(1)
 const plan=await page.evaluate(()=>window.__feature4Renders[0])
 expect(plan.version).toBe('rg_video_v2')
 expect(plan.scenes).toHaveLength(4)
 expect(plan.scenes.reduce((s,c)=>s+c.duration,0)).toBe(15)
 expect(plan.shop_id).toBe(SHOP)
})

test('mobile duplicate replays approved visual within the same fixed duration and supports undo/redo',async ({page})=>{
 await page.setViewportSize({width:390,height:844})
 await mount(page)
 const duplicate=page.getByRole('button',{name:'Duplicate selected clip with two half-length replays'})
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(3)
 await page.getByRole('button',{name:/Scene 1:/}).click()
 await expect(duplicate).toBeEnabled()
 await duplicate.click()
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(4)
 await page.getByRole('button',{name:'Undo timeline edit'}).click()
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(3)
 await page.getByRole('button',{name:'Redo timeline edit'}).click()
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(4)
 await page.getByRole('button',{name:'Submit authorized render'}).click()
 await expect.poll(()=>page.evaluate(()=>window.__feature4Renders.length)).toBe(1)
 const plan=await page.evaluate(()=>window.__feature4Renders[0])
 expect(plan.version).toBe('rg_video_v2')
 expect(plan.scenes).toHaveLength(4)
 expect(plan.scenes.reduce((sum,scene)=>sum+scene.duration,0)).toBe(15)
 expect(plan.scenes[0].asset_id).toBe(plan.scenes[1].asset_id)
 expect(plan.shop_id).toBe(SHOP)
 const viewport=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}))
 expect(viewport.scroll).toBeLessThanOrEqual(viewport.width+2)
})

test('approved Feature2 scene copy locked, creative read-only, no invented sale',async ({page})=>{
 await page.setViewportSize({width:390,height:844})
 await mount(page,true)
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(3)
 await expect(page.getByRole('button',{name:'Split video at playhead'})).toBeDisabled()
 await expect(page.getByRole('button',{name:'Duplicate selected clip with two half-length replays'})).toBeDisabled()
 await expect(page.getByLabel('Final call to action')).toBeDisabled()
 await expect(page.getByLabel('Animated headline').first()).toBeDisabled()
 await page.getByRole('button',{name:'Submit authorized render'}).click()
 await expect.poll(()=>page.evaluate(()=>window.__feature4Renders.length)).toBe(1)
 const plan=await page.evaluate(()=>window.__feature4Renders[0])
 expect(plan.scenes[2].offer).toBe('20% OFF')
 expect(plan.cta).toBe('Visit our store')
 const viewport=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}))
 expect(viewport.scroll).toBeLessThanOrEqual(viewport.width+2)
})

test('zoom changes actual track geometry, and narrow viewport uses internal horizontal scrolling',async ({page})=>{
 await page.setViewportSize({width:390,height:844})
 await mount(page)
 const scroll=page.getByLabel('Scrollable video tracks')
 const widthBefore=await page.locator('.f4-ts-timeline-content').evaluate(el=>el.getBoundingClientRect().width)
 await page.getByLabel('Timeline zoom').focus()
 await page.keyboard.press('End')
 const widthAfter=await page.locator('.f4-ts-timeline-content').evaluate(el=>el.getBoundingClientRect().width)
 expect(widthAfter).toBeGreaterThan(widthBefore)
 const state=await scroll.evaluate(el=>({view:el.clientWidth,scroll:el.scrollWidth}))
 expect(state.scroll).toBeGreaterThan(state.view)
 const body=await page.evaluate(()=>({view:innerWidth,scroll:document.documentElement.scrollWidth}))
 expect(body.scroll).toBeLessThanOrEqual(body.view+2)
})

test('reviewed 2-second scene SFX appears in its real audio track and survives v2 submission',async ({page})=>{
 await page.setViewportSize({width:1440,height:900})
 await mount(page)
 const effect=page.getByLabel('Reviewed scene sound effect · first 2 seconds')
 await expect(effect).toHaveCount(3)
 await effect.nth(1).selectOption('licensed_scene_fx')
 await expect(page.locator('.f4-ts-row').filter({hasText:'SCENE SFX'})
   .locator('[data-timeline-segment-track="audio"]')).toHaveCount(1)
 await page.getByRole('button',{name:'Submit authorized render'}).click()
 await expect.poll(()=>page.evaluate(()=>window.__feature4Renders.length)).toBe(1)
 const plan=await page.evaluate(()=>window.__feature4Renders[0])
 expect(plan.scenes[1].sfx_asset_id).toBe('licensed_scene_fx')
 expect(plan.music_asset_id).toBe(null)
})
test('Feature2 approved sound design remains read-only; no unapproved SFX injection',async ({page})=>{
 await page.setViewportSize({width:390,height:844})
 await mount(page,true)
 await expect(page.getByLabel('Reviewed scene sound effect · first 2 seconds').first()).toBeDisabled()
 await expect(page.getByLabel('Final call to action')).toBeDisabled()
})

test('authorized full-Reel narration is visible and survives authenticated-intent draft',async ({page})=>{
 await page.setViewportSize({width:1440,height:900})
 await mount(page)
 await page.getByLabel('Approved full-Reel narration').selectOption('licensed_scene_fx')
 await expect(page.locator('.f4-ts-row').filter({hasText:'NARRATION'})
   .locator('[data-timeline-segment-track="audio"]')).toHaveCount(1)
 await page.getByRole('button',{name:'Submit authorized render'}).click()
 await expect.poll(()=>page.evaluate(()=>window.__feature4Renders.length)).toBe(1)
 const plan=await page.evaluate(()=>window.__feature4Renders[0])
 expect(plan.voiceover_asset_id).toBe('licensed_scene_fx')
 expect(plan.version).toBe('rg_video_v2')
})

test('keyboard timeline undo and redo work without reauthoring approved copy',async ({page})=>{
 await page.setViewportSize({width:390,height:844})
 await mount(page)
 await page.getByRole('button',{name:/Scene 1:/}).click()
 await page.getByRole('button',{name:'Split video at playhead'}).click()
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(4)
 await page.getByRole('button',{name:'Undo timeline edit'}).focus()
 await page.keyboard.press('Control+z')
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(3)
 await page.getByRole('button',{name:'Redo timeline edit'}).focus()
 await page.keyboard.press('Control+Shift+z')
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(4)
 const scroll=await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)
 expect(scroll).toBeLessThanOrEqual(2)
})

test('focused timeline jogs one or ten *preview* frames without editing approved content',async ({page})=>{
 await page.setViewportSize({width:390,height:844})
 await mount(page)
 const tracks=page.getByRole('region',{name:'Scrollable video tracks'})
 const timecode=page.getByRole('textbox',{name:'Playhead timecode'})
 await tracks.focus()
 await expect(timecode).toHaveValue('00:00:00:00')
 await page.keyboard.press('ArrowRight')
 await expect(timecode).toHaveValue('00:00:00:01')
 await page.keyboard.press('Shift+ArrowRight')
 await expect(timecode).toHaveValue('00:00:00:11')
 await page.keyboard.press('ArrowLeft')
 await expect(timecode).toHaveValue('00:00:00:10')
 await page.keyboard.press('ArrowLeft')
 await expect(timecode).toHaveValue('00:00:00:09')
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(3)
 await page.getByRole('button',{name:'Submit authorized render'}).click()
 await expect.poll(()=>page.evaluate(()=>window.__feature4Renders.length)).toBe(1)
 const result=await page.evaluate(()=>window.__feature4Renders[0])
 expect(result.scenes).toHaveLength(3)
 expect(result.scenes.reduce((sum,scene)=>sum+scene.duration,0)).toBe(15)
 expect(result.shop_id).toBe(SHOP)
})

test('approved direction still permits keyboard preview jogging without editing',async ({page})=>{
 await mount(page,true)
 const tracks=page.getByRole('region',{name:'Scrollable video tracks'})
 const timecode=page.getByRole('textbox',{name:'Playhead timecode'})
 await tracks.focus()
 await page.keyboard.press('ArrowRight')
 await expect(timecode).toHaveValue('00:00:00:01')
 await expect(page.getByRole('button',{name:'Undo timeline edit'})).toBeDisabled()
 await expect(page.getByRole('button',{name:'Split video at playhead'})).toBeDisabled()
})

test('editing after a successful render hides stale signed MP4 rather than displaying old footage',async({page})=>{
  await page.route('https://example.invalid/**',route=>route.abort())
  await page.goto('/')
  await page.evaluate(async()=>{
    const {mountFeature4}=await import('/e2e/fixtures/timeline-studio-harness.jsx')
    mountFeature4({shop:'11111111-1111-4111-8111-111111111111',
      approved:false,seedCompletedRender:true})
  })
  await expect(page.getByRole('heading',{name:'Professional Video Studio'})).toBeVisible()
  // Previous approved output must not automatically represent a fresh draft.
  await expect(page.getByLabel('Signed private rendered video')).toHaveCount(0)
  await page.getByRole('button',{name:'Submit authorized render'}).click()
  await expect.poll(()=>page.evaluate(()=>window.__feature4Renders.length)).toBe(1)
  await expect(page.getByLabel('Signed private rendered video')).toBeVisible()
  await page.getByLabel('Animated headline').first().fill('New approved edit')
  await expect(page.getByLabel('Signed private rendered video')).toHaveCount(0)
  await expect(page.getByRole('button',{name:'Submit authorized render'})).toBeEnabled()
})

test('approved spoken subtitle lane shows precise Feature2 timing, cannot be edited',async ({page})=>{
 await page.setViewportSize({width:390,height:844})
 await mount(page,true)
 const transcript=page.getByLabel('Approved spoken subtitles')
 await expect(transcript).toBeVisible()
 await expect(transcript.locator('[data-timeline-segment-track="caption"]')).toHaveCount(3)
 await expect(transcript).toContainText('Reviewed spoken intro')
 await expect(transcript).toContainText('Exactly reviewed offer')
 await expect(page.getByRole('button',{name:'Split video at playhead'})).toBeDisabled()
 const widths=await transcript.locator('[data-timeline-segment-track="caption"]').first()
   .evaluate(el=>({left:el.style.getPropertyValue('--caption-left'),
                   width:el.style.getPropertyValue('--caption-width')}))
 expect(widths.left).toBe('1.6666666666666667%')
 expect(widths.width).toBe('6.666666666666667%')
})

test('owner-rejected successful MP4 is never surfaced as an acceptable Reel',async({page})=>{
  await page.goto('/')
  await page.evaluate(async()=>{
    const {mountFeature4}=await import('/e2e/fixtures/timeline-studio-harness.jsx')
    mountFeature4({shop:'11111111-1111-4111-8111-111111111111',
      approved:false,seedCompletedRender:true,seedOwnerRejectedRender:true})
  })
  await expect(page.getByRole('heading',{name:'Professional Video Studio'})).toBeVisible()
  await page.getByRole('button',{name:'Submit authorized render'}).click()
  await expect.poll(()=>page.evaluate(()=>window.__feature4Renders.length)).toBe(1)
  await expect(page.getByRole('alert')).toContainText('Owner rejected this Reel')
  await expect(page.getByLabel('Signed private rendered video')).toHaveCount(0)
  await expect(page.getByRole('button',{name:'Download authorized MP4'})).toHaveCount(0)
})

test('OpenReel frame timecode enters exact frames, seeks, and splits authorized clips',async({page})=>{
 await page.setViewportSize({width:390,height:844})
 await mount(page)
 const input=page.getByRole('textbox',{name:'Playhead timecode'})
 await expect(input).toHaveValue('00:00:00:00')
 await input.fill('00:00:02:15')
 await input.press('Enter')
 await expect(input).toHaveValue('00:00:02:15')
 await page.getByRole('button',{name:'Split video at playhead'}).click()
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(4)
 await page.getByRole('button',{name:'Undo timeline edit'}).click()
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(3)
 await input.focus()
 await input.press('ArrowUp')
 await expect(input).toHaveValue('00:00:02:16')
 await input.press('Escape')
 await expect(input).toHaveValue('00:00:02:16')
 await input.fill('00:00:00:30')
 await input.press('Enter')
 await expect(input).toHaveAttribute('aria-invalid','true')
 await expect(page.getByRole('alert')).toContainText('valid')
 expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(2)
})

test('OpenReel real clip navigation and snapping control work on mobile without reauthoring media',async({page})=>{
 await page.setViewportSize({width:390,height:844})
 await mount(page)
 const next=page.getByRole('button',{name:'Next scene cut'})
 const previous=page.getByRole('button',{name:'Previous scene cut'})
 await expect(previous).toBeDisabled()
 await expect(next).toBeEnabled()
 await next.click()
 await expect(page.getByRole('textbox',{name:'Playhead timecode'})).toHaveValue('00:00:05:00')
 await expect(page.getByRole('button',{name:/Scene 2:/})).toHaveClass(/is-selected/)
 await previous.click()
 await expect(page.getByRole('textbox',{name:'Playhead timecode'})).toHaveValue('00:00:00:00')
 await expect(page.getByRole('button',{name:'Split video at playhead'})).toBeDisabled()
 await page.getByRole('button',{name:/Scene 1:/}).click()
 await expect(page.getByRole('button',{name:'Split video at playhead'})).toBeEnabled()
 const snap=page.getByRole('checkbox',{name:'Snap to scene cuts and grid'})
 await expect(snap).toBeChecked()
 await snap.uncheck()
 await expect(snap).not.toBeChecked()
 await page.getByRole('button',{name:'Submit authorized render'}).click()
 await expect.poll(()=>page.evaluate(()=>window.__feature4Renders.length)).toBe(1)
 const out=await page.evaluate(()=>window.__feature4Renders[0])
 expect(out.scenes).toHaveLength(3)
 expect(out.duration_seconds).toBe(15)
 expect(out.shop_id).toBe('11111111-1111-4111-8111-111111111111')
 expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(2)
})


test('actual React Timeline Studio shows measured same-shop audio beats and frame-seeks without overflow',async({page})=>{
 await page.setViewportSize({width:390,height:844})
 await page.goto('/')
 await page.evaluate(async ()=>{
   const {mountFeature4BeatLane}=await import('/e2e/fixtures/timeline-studio-harness.jsx')
   mountFeature4BeatLane({shop:'11111111-1111-4111-8111-111111111111'})
 })
 const lane=page.getByLabel('Proposed music beat positions; server verification required')
 await expect(lane).toBeVisible()
 await expect(lane.getByRole('button')).toHaveCount(4)
 await lane.getByRole('button',{name:'Seek to proposed beat 2 at 3.500s'}).click()
 await expect(page.getByRole('textbox',{name:'Playhead timecode'})).toHaveValue('00:00:03:12')
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)
 expect(overflow).toBeLessThanOrEqual(2)
})
test('real React beat lane never renders unapproved or foreign-shop audio markers',async({page})=>{
 await page.goto('/')
 await page.evaluate(async ()=>{
   const {mountFeature4BeatLane}=await import('/e2e/fixtures/timeline-studio-harness.jsx')
   mountFeature4BeatLane({shop:'11111111-1111-4111-8111-111111111111',authorized:false})
 })
 await expect(page.getByRole('region',{name:'Professional multi-track video timeline'})).toBeVisible()
 await expect(page.getByLabel('Proposed music beat positions; server verification required')).toHaveCount(0)
 await expect(page.getByRole('textbox',{name:'Playhead timecode'})).toHaveValue('00:00:00:00')
})


test('stale caption resize aborts across synthetic shop switch or approval lock',async ({page})=>{
 await page.setViewportSize({width:1280,height:850})
 await page.goto('/')
 await page.evaluate(async shop=>{
   const fixture=await import('/e2e/fixtures/timeline-studio-harness.jsx')
   fixture.mountFeature4ResizeRace({shop})
 },SHOP)
 await expect(page.getByTestId('f4-resize-active-shop')).toHaveText(SHOP)
 const endHandle=page.locator('.caption-segment').first()
   .locator('.caption-resize-handle.is-end')
 const fireDown=async pointerId=>endHandle.dispatchEvent('pointerdown',{
   pointerId,button:0,isPrimary:true,clientX:100,clientY:100
 })
 const fireUp=async pointerId=>page.evaluate(id=>{
   window.dispatchEvent(new PointerEvent('pointerup',{
     pointerId:id,button:0,isPrimary:true,clientX:150,clientY:100,bubbles:true
   }))
 },pointerId)
 const OTHER='44444444-4444-4444-8444-444444444444'
 await fireDown(21)
 await page.evaluate(other=>window.__feature4ResizeChangeContext(other),OTHER)
 await expect(page.getByTestId('f4-resize-active-shop')).toHaveText(OTHER)
 await fireUp(21)
 expect(await page.evaluate(()=>window.__feature4ResizeWrites.length)).toBe(0)
 // Same tenant, but freshly approved direction becomes immutable mid-drag.
 await fireDown(22)
 await page.evaluate(other=>window.__feature4ResizeChangeContext(other,true),OTHER)
 await expect(page.getByRole('button',{name:'Split video at playhead'})).toBeDisabled()
 await fireUp(22)
 expect(await page.evaluate(()=>window.__feature4ResizeWrites.length)).toBe(0)
 // Explicit pointer cancel must also prevent a late synthetic pointer-up.
 await page.evaluate(other=>window.__feature4ResizeChangeContext(other,false),OTHER)
 await expect(page.getByTestId('f4-resize-active-shop')).toHaveText(OTHER)
 await fireDown(23)
 await page.evaluate(()=>{
   window.dispatchEvent(new PointerEvent('pointercancel',{
     pointerId:23,isPrimary:true,bubbles:true
   }))
 })
 await fireUp(23)
 expect(await page.evaluate(()=>window.__feature4ResizeWrites.length)).toBe(0)
})


test('timeline frame seek actually targets current signed preview without changing authorized draft', async ({page}) => {
  // Source-only DOM seek regression. A synthetic currentTime accessor lets
  // Playwright inspect the intended seek without downloading private media.
  await page.addInitScript(() => {
    Object.defineProperty(HTMLMediaElement.prototype, 'currentTime', {
      configurable: true,
      get() { return this.__feature4TestTime ?? 0 },
      set(value) { this.__feature4TestTime = value },
    })
  })
  await page.goto('/')
  await page.evaluate(async () => {
    const { mountFeature4 } = await import('/e2e/fixtures/timeline-studio-harness.jsx')
    mountFeature4({
      shop:'11111111-1111-4111-8111-111111111111',
      approved:false, seedCompletedRender:true,
    })
  })
  await expect(page.getByRole('heading',{name:'Professional Video Studio'})).toBeVisible()
  await page.getByRole('button',{name:'Submit authorized render'}).click()
  await expect.poll(() => page.evaluate(() => window.__feature4Renders.length)).toBe(1)
  const video = page.getByLabel('Signed private rendered video')
  await expect(video).toBeVisible()
  const timecode = page.getByRole('textbox',{name:'Playhead timecode'})
  await timecode.fill('00:00:06:12')
  await timecode.press('Enter')
  await expect(timecode).toHaveValue('00:00:06:12')
  await expect.poll(() => video.evaluate(node => node.currentTime)).toBe(6.5)
  await page.getByRole('button',{name:/Scene 2:/}).click()
  await expect(timecode).toHaveValue('00:00:07:15')
  await expect.poll(() => video.evaluate(node => node.currentTime)).toBe(7.5)
  // Frame navigation is preview-only and cannot silently rewrite the output.
  expect(await page.evaluate(() => window.__feature4Renders.length)).toBe(1)
  await page.getByLabel('Animated headline').first().fill('New review-required edit')
  await expect(video).toHaveCount(0)
})
