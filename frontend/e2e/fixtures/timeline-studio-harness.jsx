// Test-only Vite-resolved module: never mounted by the production router.
import React from 'react'
import { createRoot } from 'react-dom/client'
import VideoStudio from '../../src/features/video/VideoStudio.jsx'
import TimelineStudioSurface from '../../src/features/video/TimelineStudioSurface.jsx'

export function mountFeature4({shop,approved,seedCompletedRender=false,seedOwnerRejectedRender=false}) {
  const holder=document.createElement('div')
  holder.id='feature4-offline-test'
  document.getElementById('root')?.setAttribute('hidden','')
  document.body.appendChild(holder)
  const media=[
    {id:'photo1',kind:'image',authorized:true,shop_id:shop},
    {id:'motion1',kind:'video',authorized:true,shop_id:shop},
    {id:'poster1',kind:'poster',authorized:true,shop_id:shop}
  ]
  const licensedAudio=[
    {id:'licensed_scene_fx',kind:'audio',authorized:true,shop_id:shop,title:'Licensed short whoosh'}
  ]
  const approvedPlan=approved?{
    version:'creative_direction_v1',source_feature:'feature2',approved:true,
    shop_id:shop,campaign_id:'campaign1',approval_id:'approval1',
    review_hash:'a'.repeat(64),duration_seconds:30,template:'cinematic',
    voiceover_asset_id:'licensed_scene_fx',
    script:{source_feature:'feature2',approved:true,approval_id:'approval1',
      transcript:[{start:.5,duration:2,text:'Reviewed spoken intro'},
        {start:10,duration:2,text:'Exactly reviewed offer'},
        {start:27,duration:2,text:'Visit our store'}]},
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
   shopId:shop,mediaAssets:media,musicAssets:licensedAudio,creativeDirection:approvedPlan,
   ...(seedCompletedRender ? {
     renderStatus: {status:'SUCCEEDED',shop_id:shop,job_id:'test-old-job',
       ...(seedOwnerRejectedRender ? {visual_quality_status:'OWNER_REJECTED'} : {})},
     signedVideoUrl: 'https://example.invalid/previous-approved-result.mp4'
   } : {}),
   onRender:async plan => {window.__feature4Renders.push(plan)}
  }))

}


// Isolated read-only beat-lane harness; no hidden server/media rights shortcuts.
export function mountFeature4BeatLane({shop, authorized=true,approvedDirection=false}) {
  const holder=document.createElement('div')
  holder.id='feature4-beat-lane-e2e'
  document.getElementById('root')?.setAttribute('hidden','')
  document.body.appendChild(holder)
  const scenes=Array.from({length:3},(_,i)=>({
    start:i*5,duration:5,headline:['Intro look','Garment closeup','End editorial'][i],
    asset_id:'photo1',animation_preset:'subtle_zoom',transition:'fade',
  }))
  const draft={
    version:'rg_video_v2',shop_id:shop,mode:'music_sync',template:'cinematic',
    duration_seconds:15,output:{width:540,height:960,fps:24},scenes,
    cta:'Stock editorial sample',music_asset_id:'music01',voiceover_asset_id:null,
    beats:[1,3.5,7.125,10.5],
  }
  const audio=[{
    id:'music01',kind:'audio',shop_id:authorized?shop:'foreign',
    authorized:true,title:'Original rhythm test track',
  }]
  const media=[{id:'photo1',kind:'image',authorized:true,shop_id:shop}]
  import('../../src/features/video/TimelineStudioSurface.jsx').then(({default: TimelineStudioSurface})=>{
    createRoot(holder).render(React.createElement(TimelineStudioSurface,{
      draft,mediaAssets:media,musicAssets:audio,selectedSceneIndex:0,
      approvedDirection,onChange:()=>{},onSelectScene:()=>{},
    }))
  })
}


// Race-only Playwright harness. Two isolated synthetic shops, no API or real
// media rights. Changing the owner/draft while dragging must discard the
// original pointer-up event before any unreviewed edit reaches onChange.
export function mountFeature4ResizeRace({shop}) {
  const holder = document.createElement('div')
  holder.id = 'feature4-resize-race'
  document.getElementById('root')?.setAttribute('hidden', '')
  document.body.appendChild(holder)
  const root = createRoot(holder)
  window.__feature4ResizeWrites = []
  const render = (currentShop, approved = false) => {
    const scenes = Array.from({length:3}, (_, i) => ({
      start:i*5, duration:5, headline:['Intro','Product','End card'][i],
      asset_id:'photo1', animation_preset:'fade', transition:'cut',
    }))
    const draft = {
      version:'rg_video_v2', mode:'media', shop_id:currentShop,
      duration_seconds:15, template:'cinematic',
      output:{width:540,height:960,fps:24},scenes,
      cta:'Test only',music_asset_id:null,voiceover_asset_id:null,
    }
    const media = [{id:'photo1',kind:'image',authorized:true,shop_id:currentShop}]
    root.render(React.createElement(React.Fragment,null,
      React.createElement('output',{'data-testid':'f4-resize-active-shop'},currentShop),
      React.createElement(TimelineStudioSurface,{
        draft,mediaAssets:media,musicAssets:[],approvedDirection:approved,
        selectedSceneIndex:0,onSelectScene:()=>{},
        onChange:next=>window.__feature4ResizeWrites.push(next),
      })))
  }
  window.__feature4ResizeChangeContext = render
  render(shop)
}


// Deferred network-ACK race harness: fake same-shop status but NO cloud API.
// A late old-shop render completion must not unlock another tenant's preview.
export function mountFeature4RenderRace({shop}) {
  const holder = document.createElement('div')
  holder.id = 'feature4-render-race'
  document.getElementById('root')?.setAttribute('hidden','')
  document.body.appendChild(holder)
  const root = createRoot(holder)
  window.__feature4RaceRequests = []
  let activeShop = shop
  let direction = null
  const render = (currentShop=activeShop, currentDirection=direction) => {
    activeShop = currentShop
    direction = currentDirection
    const assets = [{id:'photo1',kind:'image',authorized:true,shop_id:currentShop}]
    root.render(React.createElement(VideoStudio,{
      shopId:currentShop, mediaAssets:assets, musicAssets:[],
      creativeDirection:direction,
      renderStatus:{shop_id:currentShop,status:'SUCCEEDED',job_id:'synthetic-job'},
      signedVideoUrl:'https://example.invalid/signed-fixture.mp4',
      onRender:plan => new Promise((resolve,reject) => {
        window.__feature4RaceRequests.push({plan,resolve,reject})
      }),
    }))
  }
  window.__feature4RaceSwitchShop = nextShop => render(nextShop)
  window.__feature4RaceSetDirection = nextDirection => render(activeShop, nextDirection)
  window.__feature4RaceSettle = (index, reject=false) => {
    const pending = window.__feature4RaceRequests[index]
    if (!pending) throw Error('Missing synthetic pending job')
    if (reject) pending.reject(Error('Stale shop media permission denial'))
    else pending.resolve()
  }
  render(shop)
}
