// Test-only Vite-resolved module: never mounted by the production router.
import React from 'react'
import { createRoot } from 'react-dom/client'
import VideoStudio from '../../src/features/video/VideoStudio.jsx'

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
