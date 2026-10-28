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

test('approved Feature2 scene copy locked, creative read-only, no invented sale',async ({page})=>{
 await page.setViewportSize({width:390,height:844})
 await mount(page,true)
 await expect(page.locator('[data-timeline-segment-track="image"]')).toHaveCount(3)
 await expect(page.getByRole('button',{name:'Split video at playhead'})).toBeDisabled()
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
 await page.getByLabel('Timeline zoom').fill('4')
 const widthAfter=await page.locator('.f4-ts-timeline-content').evaluate(el=>el.getBoundingClientRect().width)
 expect(widthAfter).toBeGreaterThan(widthBefore)
 const state=await scroll.evaluate(el=>({view:el.clientWidth,scroll:el.scrollWidth}))
 expect(state.scroll).toBeGreaterThan(state.view)
 const body=await page.evaluate(()=>({view:innerWidth,scroll:document.documentElement.scrollWidth}))
 expect(body.scroll).toBeLessThanOrEqual(body.view+2)
})
