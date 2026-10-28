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
 assert.equal((await client.listMediaAssetsKeysetPage(shop,first.nextCursor)).items.length,0)
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
