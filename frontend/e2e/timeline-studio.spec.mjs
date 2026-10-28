import { test, expect } from '@playwright/test'
const SHOP='11111111-1111-4111-8111-111111111111'
async function mount(page, approved=false) {
 await page.goto('/')
 await page.evaluate(async ({shop,approved})=>{
  const React=await import('react')
  const {createRoot}=await import('react-dom/client')
  const {default: VideoStudio}=await import('/src/features/video/VideoStudio.jsx')
  const holder=document.createElement('div')
  holder.id='feature4-offline-test'
  document.body.replaceChildren(holder)
  const media=[
    {id:'photo1',kind:'image',authorized:true,shop_id:shop},
    {id:'motion1',kind:'video',authorized:true,shop_id:shop},
    {id:'poster1',kind:'poster',authorized:true,shop_id:shop}
  ]
  const approvedPlan=approved?{
    version:'creative_direction_v1',source_feature:'feature2',approved:true,
    shop_id:shop,campaign_id:'campaign1',approval_id:'approval1',
    review_hash:'a'.repeat(64),duration_seconds:30,template:'cinematic',
    cta:'Visit our store',music_asset_id:null,
    scenes:[{duration:10,asset_id:'photo1',headline:'Approved kurti',
      transition:'fade',animation_preset:'subtle_zoom'},
    {duration:10,asset_id:'motion1',headline:'Approved walking model',
      transition:'cut',animation_preset:'fade'},
    {duration:10,asset_id:'poster1',headline:'20% OFF',
      offer:'20% OFF',transition:'fade',animation_preset:'fade'}]
  }:null
  window.__feature4Renders=[]
  createRoot(holder).render(React.createElement(VideoStudio,{
   shopId:shop,mediaAssets:media,musicAssets:[],creativeDirection:approvedPlan,
   onRender:async plan => {window.__feature4Renders.push(plan)}
  }))
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
