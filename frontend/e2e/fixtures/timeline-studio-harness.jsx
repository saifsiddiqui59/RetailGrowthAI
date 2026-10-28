// Test-only Vite-resolved module: never mounted by the production router.
import React from 'react'
import { createRoot } from 'react-dom/client'
import VideoStudio from '../../src/features/video/VideoStudio.jsx'

export function mountFeature4({shop,approved}) {
  const holder=document.createElement('div')
  holder.id='feature4-offline-test'
  document.getElementById('root')?.setAttribute('hidden','')
  document.body.appendChild(holder)
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

}
