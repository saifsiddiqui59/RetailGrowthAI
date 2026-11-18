import test from 'node:test'
import assert from 'node:assert/strict'
import {createRetailClient} from '../../frontend/src/lib/supabase.js'

const shop='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
const other='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'
const row=i=>({id:'a1000000-0000-4000-8000-'+String(i+100).padStart(12,'0'),
 shop_id:shop,source:'UPLOAD',license_name:'owned',mime_type:'image/png',
 created_at:new Date(Date.UTC(2026,9,28,12,0)-i*1000).toISOString()})
const response=body=>new Response(JSON.stringify(body),{status:200,headers:{'Content-Type':'application/json'}})
test('shop JWT keyset pages preserve 100-record boundary when newer uploads arrive',async()=>{
 let rows=Array.from({length:101},(_,i)=>row(i)),calls=[]
 const client=createRetailClient({url:'https://rg.test.example',key:'sb_publishable_test',
  storage:null,clock:()=>1000000,
  fetchImpl:async(url,opts)=>{
   if(url.includes('/auth/v1/token'))return response({access_token:'retailer-jwt',refresh_token:'r',expires_in:3600})
   calls.push({url,opts});return response(rows)
  }})
 await client.signIn('retailer@example.invalid','sample')
 await assert.rejects(()=>client.listMediaAssetsKeysetPage('not-uuid'),/scope/)
 await assert.rejects(()=>client.listMediaAssetsKeysetPage(shop,{id:shop,created_at:'invalid'}),/cursor/)
 assert.equal(calls.length,0)
 const first=await client.listMediaAssetsKeysetPage(shop)
 assert.equal(first.items.length,100)
 assert.deepEqual(first.nextCursor,{id:row(99).id,created_at:row(99).created_at})
 assert.equal(new URL(calls[0].url).searchParams.get('limit'),'101')
 assert.equal(new URL(calls[0].url).searchParams.has('offset'),false)
 assert.equal(calls[0].opts.headers.Authorization,'Bearer retailer-jwt')
 rows=[row(100)]
 const second=await client.listMediaAssetsKeysetPage(shop,first.nextCursor)
 assert.deepEqual(second.items.map(x=>x.id),[row(100).id])
 assert.equal(second.nextCursor,null)
 const filter=new URL(calls[1].url).searchParams.get('or')
 assert.ok(filter.includes('created_at.lt.'+row(99).created_at))
 assert.ok(filter.includes('id.lt.'+row(99).id))
 rows=[{...row(100),shop_id:other}]
 await assert.rejects(()=>client.listMediaAssetsKeysetPage(shop,first.nextCursor),/verified/)
 // Never accept an apparently valid page if the last lookahead row is foreign.
 rows=[row(100),{...row(101),shop_id:other}]
 await assert.rejects(()=>client.listMediaAssetsKeysetPage(shop,first.nextCursor),/verified/)
 // A mixed-tenant response is invalid even if the foreign row would otherwise
 // have been omitted from the displayed, filtered 100-record page.
 rows=[row(100),{...row(101),shop_id:other},row(102)]
 await assert.rejects(()=>client.listMediaAssetsKeysetPage(shop,first.nextCursor),/verified/)
 rows=[row(98)]
 await assert.rejects(()=>client.listMediaAssetsKeysetPage(shop,first.nextCursor),/boundary/)
 rows=[row(100),row(99)]
 await assert.rejects(()=>client.listMediaAssetsKeysetPage(shop,first.nextCursor),/ordering/)
 rows=[{...row(100),created_at:'wrong'}]
 await assert.rejects(()=>client.listMediaAssetsKeysetPage(shop,first.nextCursor),/verified/)
 rows=Array.from({length:102},(_,i)=>row(i))
 await assert.rejects(()=>client.listMediaAssetsKeysetPage(shop),/verified/)
 assert.equal(calls.every(x=>x.opts.headers.apikey==='sb_publishable_test'),true)
})


test('keyset keeps PostgreSQL microsecond ordering and rejects normalized dates and reversed rows',async()=>{
 let records=[]
 const calls=[]
 const client=createRetailClient({url:'https://rg.test.example',key:'sb_publishable_test',
  storage:null,clock:()=>1000000,fetchImpl:async(url)=>{
   if(url.includes('/auth/v1/token'))return response({access_token:'retailer-jwt',refresh_token:'r',expires_in:3600})
   calls.push(url)
   return response(records)
  }})
 await client.signIn('retailer@example.invalid','sample')
 const at=n=>'2026-10-28T12:00:00.'+String(n).padStart(6,'0')+'Z'
 const record=(id,micro)=>({...row(id),created_at:at(micro)})
 const cursor={id:record(300,4).id,created_at:at(4)}
 records=[record(301,3),record(302,2),record(303,1)]
 // These IDs increase while creation timestamps decrease within ONE millisecond.
 const page=await client.listMediaAssetsKeysetPage(shop,cursor)
 assert.deepEqual(page.items.map(x=>x.id),records.map(x=>x.id))
 assert.equal(page.nextCursor,null)
 assert.ok(calls[0].includes(encodeURIComponent('created_at.lt.'+at(4))))
 records=[record(301,1),record(302,3)]
 await assert.rejects(()=>client.listMediaAssetsKeysetPage(shop,cursor),/ordering/)
 records=[record(301,5)]
 await assert.rejects(()=>client.listMediaAssetsKeysetPage(shop,cursor),/boundary/)
 records=[record(301,1)]
 await assert.rejects(()=>client.listMediaAssetsKeysetPage(shop,{
   id:record(300,4).id,created_at:'2026-02-31T12:00:00.000004Z'
 }),/cursor/)
 records=[{...record(301,1),created_at:'2026-10-28T24:00:00Z'}]
 await assert.rejects(()=>client.listMediaAssetsKeysetPage(shop,cursor),/verified/)
})

test('201 same-second assets page as 100, 100 and 1 without duplicates',async()=>{
 const at=n=>'2026-10-28T12:00:00.'+String(n).padStart(6,'0')+'Z'
 const all=Array.from({length:201},(_,i)=>({...row(i+1),created_at:at(201-i)}))
 const pages=[all.slice(0,101),all.slice(100,201),all.slice(200)]
 let count=0
 const client=createRetailClient({url:'https://rg.test.example',key:'sb_publishable_test',
  storage:null,clock:()=>1000000,fetchImpl:async(url)=>{
   if(url.includes('/auth/v1/token'))return response({access_token:'retailer-jwt',refresh_token:'r',expires_in:3600})
   return response(pages[count++]||[])
  }})
 await client.signIn('retailer@example.invalid','sample')
 const loaded=[]
 let cursor=null
 for(let i=0;i<3;i++){
  const page=await client.listMediaAssetsKeysetPage(shop,cursor)
  loaded.push(...page.items.map(x=>x.id))
  cursor=page.nextCursor
  assert.equal(page.items.length,i===2?1:100)
  assert.equal(Boolean(cursor),i<2)
 }
 assert.equal(count,3)
 assert.equal(new Set(loaded).size,201)
 assert.deepEqual(loaded,all.map(x=>x.id))
})
