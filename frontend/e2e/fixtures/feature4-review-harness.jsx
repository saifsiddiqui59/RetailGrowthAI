// Test-only component harness: no production mount, real Auth, or cloud access.
import React from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import CreativePlanReview from '../../src/features/video/CreativePlanReview.jsx'

export function mountReview({shop, campaign, plan, hash, review, role='OWNER', approved=false}) {
  const holder=document.createElement('div')
  document.getElementById('root')?.setAttribute('hidden','')
  document.body.appendChild(holder)
  let state=approved?'APPROVED':'DRAFT'
  const user={id:'a9000000-0000-4000-8000-000000000001'}
  const row=()=>({id:plan,shop_id:shop,campaign_id:campaign,
    proposal_sha256:hash,review_sha256:state==='APPROVED'?review:null,
    state,proposal:{cta:'Visit our synthetic boutique',
      scenes:[{duration:30,headline:'Synthetic owned-media fixture'}]}})
  window.__f4ReviewCalls=[]
  const client={
    getAccessToken:async()=> 'fixture-signed-test-only',
    listFeature4CreativePlans:async s=>{if(s!==shop)throw Error('Foreign fixture');return [row()]},
    listFeature4SourceDays:async()=>[],
    reviewFeature4CreativePlan:async (s,p,h)=>{
      if(s!==shop||p!==plan||h!==hash||role==='VIEWER')throw Error('Denied fixture')
      window.__f4ReviewCalls.push([s,p,h])
      state='APPROVED'
      return {shop_id:shop,approval_id:plan,review_hash:review,status:'APPROVED'}
    },
  }
  const query=new QueryClient({defaultOptions:{queries:{retry:false}}})
  createRoot(holder).render(<QueryClientProvider client={query}>
    <CreativePlanReview client={client} user={user} shopId={shop} role={role}/>
  </QueryClientProvider>)
}
