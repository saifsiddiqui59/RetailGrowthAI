import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createRetailClient } from '../../frontend/src/lib/supabase.js'

function storage() {
  const items = new Map()
  return {
    getItem: (k) => items.get(k) || null,
    setItem: (k, v) => items.set(k, v),
    removeItem: (k) => items.delete(k),
  }
}
const uid = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
function fixture(fetchImpl, clock = () => 1_000_000) {
  return createRetailClient({ url: 'https://retailgrowthai-dev.example.supabase.co',
    key: 'sb_publishable_example', storage: storage(), fetchImpl, clock })
}
function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

test('browser REST calls carry user bearer token and NEVER service-role credentials', async () => {
  const calls = []
  const api = fixture(async (url, options) => {
    calls.push({ url, options })
    if (url.includes('/auth/v1/token')) return json({ access_token: 'user-access', refresh_token: 'user-refresh', expires_in: 3600 })
    if (url.includes('/rest/v1/shop_memberships')) return json([{ shop_id: 's1', role: 'OWNER', active: true }])
    if (url.includes('/rest/v1/shops')) return json([{ id: 's1', name: 'Business A' }])
    throw Error('Unexpected request: ' + url)
  })
  await api.signIn('user@example.test', 'password123')
  const shops = await api.listShops()
  assert.equal(shops.length, 1)
  assert.equal(shops[0].membership.role, 'OWNER')
  for (const call of calls.filter((c) => c.url.includes('/rest/v1/'))) {
    assert.equal(call.options.headers.Authorization, 'Bearer user-access')
    assert.equal(call.options.headers.apikey, 'sb_publishable_example')
    assert.doesNotMatch(JSON.stringify(call), /service.role|service_role|secret_key/i)
  }
})
test('business profile PATCH ignores forged shop_id and rejects invisible zero-row update', async () => {
  let patch
  const api = fixture(async (url, options) => {
    if (url.includes('/auth/v1/token')) return json({ access_token: 'at', refresh_token: 'rt', expires_in: 3600 })
    if (url.includes('/rest/v1/business_profiles')) {
      patch = { url, options }
      return json([])
    }
    throw Error('unexpected')
  })
  await api.signIn('u@example.test', 'secret12')
  await assert.rejects(() => api.updateBusinessProfile('real-shop', {
    shop_id: 'forged-other-shop', business_name: 'Changed', owner_user_id: uid, role: 'OWNER',
  }), /not found or you do not have edit permission/)
  assert.equal(new URL(patch.url).searchParams.get('shop_id'), 'eq.real-shop')
  assert.equal(JSON.parse(patch.options.body).shop_id, undefined)
  assert.equal(JSON.parse(patch.options.body).role, undefined)
})
test('expires access tokens through one refresh and drops invalidated sessions', async () => {
  const calls = []
  let clock = 1_000_000
  const api = fixture(async (url) => {
    calls.push(url)
    if (url.includes('grant_type=password')) return json({ access_token: 'expired', refresh_token: 'refresh', expires_in: 1 })
    if (url.includes('grant_type=refresh_token')) return json({ access_token: 'fresh', refresh_token: 'refresh-new', expires_in: 3600 })
    if (url.includes('/auth/v1/user')) return json({ id: uid })
    throw Error('unexpected ' + url)
  }, () => clock)
  await api.signIn('u@example.test', 'secret12')
  clock += 2000
  assert.equal((await api.getUser()).id, uid)
  assert.equal(calls.filter((url) => url.includes('grant_type=refresh_token')).length, 1)
  assert.equal(api.getStoredSession().access_token, 'fresh')
  await api.signOut()
  assert.equal(api.getStoredSession(), null)
  await assert.rejects(() => api.getUser(), /Sign in before accessing shop data/)
})
test('unconfigured client refuses all network/auth requests', async () => {
  const api = createRetailClient({ url: '', key: '', storage: storage() })
  assert.equal(api.configured, false)
  await assert.rejects(() => api.signIn('a', 'b'), /not configured/)
})


const mediaShop = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
const uploadUuid = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'
const recordedMedia = 'cccccccc-cccc-4ccc-8ccc-cccccccccccc'
function pngFile() {
  const bytes = new Uint8Array(256)
  bytes.set([137, 80, 78, 71, 13, 10, 26, 10])
  return new Blob([bytes], { type: 'image/png' })
}

test('private upload verifies bytes, user JWT, tenant path and registration RPC', async () => {
  const requests = []
  const client = createRetailClient({
    url: 'https://rg.example.supabase.co', key: 'sb_publishable_demo',
    storage: storage(), uuidFactory: () => uploadUuid,
    fetchImpl: async (url, options) => {
      requests.push({ url, options })
      if (url.includes('/auth/v1/token')) {
        return json({ access_token: 'user-access', refresh_token: 'user-refresh', expires_in: 3600 })
      }
      if (url.includes('/storage/v1/object/')) return json({ Key: 'private' }, 201)
      if (url.includes('/rest/v1/rpc/register_uploaded_image')) return json(recordedMedia)
      throw Error('unexpected URL ' + url)
    },
  })
  await client.signIn('editor@example.test', 'password123')
  const media = await client.uploadImageAsset(mediaShop, {
    file: pngFile(), licenseName: 'owned',
    attribution: 'Original product photograph created by our own team',
    confirmedRights: true,
  })
  assert.equal(media.id, recordedMedia)
  const upload = requests.find(entry => entry.url.includes('/storage/v1/object/'))
  assert.equal(upload.url, 'https://rg.example.supabase.co/storage/v1/object/retailgrowth-media/' +
    mediaShop + '/uploads/' + uploadUuid + '.png')
  assert.equal(upload.options.method, 'POST')
  assert.equal(upload.options.redirect, 'error')
  assert.equal(upload.options.headers.Authorization, 'Bearer user-access')
  assert.equal(upload.options.headers['x-upsert'], 'false')
  assert.equal(upload.options.body.type, 'image/png')
  const rpc = requests.find(entry => entry.url.includes('/rest/v1/rpc/'))
  assert.equal(rpc.options.headers.Authorization, 'Bearer user-access')
  assert.deepEqual(JSON.parse(rpc.options.body), {
    p_shop_id: mediaShop,
    p_object_path: mediaShop + '/uploads/' + uploadUuid + '.png',
    p_license_name: 'owned', p_license_url: null,
    p_attribution: 'Original product photograph created by our own team',
  })
  assert.doesNotMatch(JSON.stringify(rpc), /service.role|service_role|sb_secret_/i)
})

test('invalid ownership assertion, file signature and license URL prevent upload', async () => {
  let calls = 0
  const client = createRetailClient({
    url: 'https://rg.example.supabase.co', key: 'sb_publishable_demo',
    storage: storage(), uuidFactory: () => uploadUuid,
    fetchImpl: async (url) => {
      calls++
      if (url.includes('/auth/v1/token')) {
        return json({ access_token: 'user-access', refresh_token: 'refresh', expires_in: 3600 })
      }
      throw new Error('unauthorized network call ' + url)
    },
  })
  await client.signIn('editor@example.test', 'password123')
  const originalCalls = calls
  const base = { file: pngFile(), licenseName: 'owned',
    attribution: 'Original image created and owned by us', confirmedRights: true }
  await assert.rejects(() => client.uploadImageAsset(mediaShop, { ...base, confirmedRights: false }), /confirm/)
  await assert.rejects(() => client.uploadImageAsset('not-a-shop-id', base), /business/)
  await assert.rejects(() => client.uploadImageAsset(mediaShop, {
    ...base, licenseName: 'commercial', licenseUrl: 'http://not-secure.test/evidence',
  }), /HTTPS/)
  const corrupted = new Blob([new Uint8Array(256)], { type: 'image/png' })
  await assert.rejects(() => client.uploadImageAsset(mediaShop, { ...base, file: corrupted }), /bytes/)
  assert.equal(calls, originalCalls)
})

test('server-denied metadata registration never claims upload success', async () => {
  const client = createRetailClient({
    url: 'https://rg.example.supabase.co', key: 'sb_publishable_demo',
    storage: storage(), uuidFactory: () => uploadUuid,
    fetchImpl: async (url) => {
      if (url.includes('/auth/v1/token')) {
        return json({ access_token: 'user-access', refresh_token: 'user-refresh', expires_in: 3600 })
      }
      if (url.includes('/storage/v1/object/')) return json({ Key: 'private' }, 201)
      if (url.includes('/rest/v1/rpc/')) return json(null)
      throw Error('unexpected')
    },
  })
  await client.signIn('editor@example.test', 'password123')
  await assert.rejects(() => client.uploadImageAsset(mediaShop, {
    file: pngFile(), licenseName: 'owned', confirmedRights: true,
    attribution: 'Created by the brand photography team',
  }), /registration was denied/)
})


test('new shop uses insert-minimal until AFTER INSERT owner membership becomes readable', async () => {
  const created = 'dddddddd-dddd-4ddd-8ddd-dddddddddddd'
  const sent = []
  let inserted = false
  const client = createRetailClient({
    url: 'https://rg.example.supabase.co', key: 'sb_publishable_unauthorized',
    storage: storage(), uuidFactory: () => created,
    fetchImpl: async (url, options) => {
      sent.push({ url, options })
      if (url.includes('/auth/v1/token')) return json({
        access_token: 'test-user-jwt', refresh_token: 'refresh', expires_in: 3600,
      })
      if (url.includes('/auth/v1/user')) return json({ id: uid })
      if (url.includes('/rest/v1/shops') && options.method === 'POST') {
        assert.equal(options.headers.Prefer, 'return=minimal')
        assert.equal(options.headers.Authorization, 'Bearer test-user-jwt')
        assert.ok(!new URL(url).searchParams.has('select'))
        assert.deepEqual(JSON.parse(options.body), {
          id: created, owner_user_id: uid, name: 'Test Boutique',
          slug: 'test-boutique', timezone: 'Asia/Kolkata',
        })
        inserted = true
        return new Response(null, { status: 201 })
      }
      if (url.includes('/rest/v1/shops') && options.method === 'GET') {
        assert.ok(inserted, 'owner member trigger must have executed before shop is queried')
        assert.equal(new URL(url).searchParams.get('id'), 'eq.' + created)
        return json([{ id: created, name: 'Test Boutique', slug: 'test-boutique', timezone: 'Asia/Kolkata' }])
      }
      throw Error('Unexpected network request ' + url)
    },
  })
  await client.signIn('test@example.invalid','random-private-password')
  const shop = await client.createShop({ name: 'Test Boutique', slug: 'test-boutique' })
  assert.equal(shop.id, created)
  assert.equal(sent.filter(x => x.url.includes('/rest/v1/shops')).length, 2)
})

test('shop onboarding refuses invisible membership without granting broader SELECT', async () => {
  const created = 'dddddddd-dddd-4ddd-8ddd-dddddddddddd'
  const client = createRetailClient({
    url: 'https://rg.example.supabase.co', key: 'sb_publishable_only',
    storage: storage(), uuidFactory: () => created,
    fetchImpl: async (url, options) => {
      if (url.includes('/auth/v1/token')) return json({
        access_token: 'signed', refresh_token: 'refresh', expires_in: 3600,
      })
      if (url.includes('/auth/v1/user')) return json({id: uid})
      if (options.method === 'POST') return new Response(null,{status:201})
      return json([])
    },
  })
  await client.signIn('owner@example.invalid','private')
  await assert.rejects(() => client.createShop({name:'Boutique',slug:'boutique'}), /access verification is pending/)
})

test('OWNER subscription overview reads tenant RLS row only with user token; cannot edit', async () => {
  const shop = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  const requests = []
  const api = fixture(async (url, options) => {
    requests.push({ url, options })
    if (url.includes('/auth/v1/token')) return json({
      access_token: 'user-owner-jwt', refresh_token: 'refresh-owner', expires_in: 3600,
    })
    if (url.includes('/rest/v1/shop_subscriptions')) return json([{
      shop_id: shop, plan_code: 'TRIAL', status: 'TRIAL',
      valid_until: '2026-10-30T00:00:00Z',
    }])
    throw Error('Unexpected request ' + url)
  })
  await api.signIn('owner@example.invalid', 'test-password')
  const state = await api.getShopSubscription(shop)
  assert.equal(state.plan_code, 'TRIAL')
  const call = requests.find(x => x.url.includes('/rest/v1/shop_subscriptions'))
  assert.equal(call.options.method, 'GET')
  assert.equal(call.options.headers.Authorization, 'Bearer user-owner-jwt')
  assert.equal(call.options.headers.apikey, 'sb_publishable_example')
  assert.equal(new URL(call.url).searchParams.get('shop_id'), 'eq.' + shop)
  assert.doesNotMatch(JSON.stringify(call), /sb_secret_|service_role/i)
  await assert.rejects(() => api.getShopSubscription('forged-id'), /Invalid selected business/)
  assert.equal(requests.filter(x => x.url.includes('/rest/v1/shop_subscriptions')).length, 1)
})
test('non-owner subscription row invisibility stays a null result, not an upgrade', async () => {
  const shop = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  const api = fixture(async (url) => {
    if (url.includes('/auth/v1/token')) return json({
      access_token: 'viewer-jwt', refresh_token: 'viewer-refresh', expires_in: 3600,
    })
    if (url.includes('/rest/v1/shop_subscriptions')) return json([])
    throw Error('Unexpected request')
  })
  await api.signIn('viewer@example.invalid', 'password')
  assert.equal(await api.getShopSubscription(shop), null)
})

test('read-only shop-wide draft month requires JWT, shop/date filters, rejects foreign rows and oversize',async()=>{
  const shop='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  const cross='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'
  const calls=[]
  let response=[]
  const api=fixture(async(url,options)=>{
    calls.push({url,options})
    if(url.includes('/auth/v1/token'))return json({access_token:'user-access',refresh_token:'user-refresh',expires_in:3600})
    if(url.includes('/rest/v1/campaign_days'))return json(response)
    throw new Error('Unexpected request '+url)
  })
  await api.signIn('test@example.test','secret12')
  await assert.rejects(()=>api.listShopCalendarMonth(shop,'2026-13'),/Invalid/)
  assert.equal(calls.filter(c=>c.url.includes('campaign_days')).length,0)
  assert.deepEqual(await api.listShopCalendarMonth(shop,'2026-12'),[])
  const call=calls.find(c=>c.url.includes('campaign_days'))
  const params=new URL(call.url).searchParams
  assert.equal(params.get('shop_id'),'eq.'+shop)
  assert.equal(params.get('and'),'(scheduled_date.gte.2026-12-01,scheduled_date.lt.2027-01-01)')
  assert.equal(params.get('limit'),'201')
  assert.equal(call.options.headers.Authorization,'Bearer user-access')
  assert.ok(!JSON.stringify(call).includes('service_role'))
  response=[{shop_id:cross}]
  await assert.rejects(()=>api.listShopCalendarMonth(shop,'2026-12'),/could not be verified/)
  response=Array(201).fill({shop_id:shop})
  await assert.rejects(()=>api.listShopCalendarMonth(shop,'2026-12'),/could not be verified/)
})

test('private registered upload preview fetches binary with caller JWT only and validates byte signature',async()=>{
  const shop='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  const asset='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'
  const upload='cccccccc-cccc-4ccc-8ccc-cccccccccccc'
  const requests=[]
  const png=new Uint8Array(256)
  png.set([137,80,78,71,13,10,26,10])
  let bytes=png
  let row={id:asset,shop_id:shop,storage_bucket:'retailgrowth-media',
    object_path:shop+'/uploads/'+upload+'.png',
    mime_type:'image/png',source:'UPLOAD',license_name:'owned'}
  const api=fixture(async(url,options)=>{
    requests.push({url,options})
    if(url.includes('/auth/v1/token')) return json({access_token:'user-access',refresh_token:'user-refresh',expires_in:3600})
    if(url.includes('/rest/v1/media_assets')) return json([row])
    if(url.includes('/storage/v1/object/authenticated/'))return new Response(bytes,{
      headers:{'Content-Type':'image/png','Content-Length':String(bytes.byteLength)}})
    throw Error('Unexpected '+url)
  })
  await api.signIn('owner@example.test','password123')
  const result=await api.downloadPrivateImage(shop,asset)
  assert.equal(result.blob.type,'image/png')
  assert.equal(result.blob.size,256)
  assert.equal(result.filename,'retailgrowth-image-'+asset.slice(0,8)+'.png')
  const storageCall=requests.find(x=>x.url.includes('/storage/v1/object/authenticated/'))
  assert.equal(storageCall.options.headers.Authorization,'Bearer user-access')
  assert.ok(storageCall.url.endsWith(shop+'/uploads/'+upload+'.png'))
  assert.equal(storageCall.options.redirect,'error')
  assert.doesNotMatch(storageCall.url,/object\/public|object\/sign/)
  row={...row,shop_id:'dddddddd-dddd-4ddd-8ddd-dddddddddddd'}
  const before=requests.filter(x=>x.url.includes('/storage/v1/object/authenticated/')).length
  await assert.rejects(()=>api.downloadPrivateImage(shop,asset),/not registered or authorized/)
  assert.equal(requests.filter(x=>x.url.includes('/storage/v1/object/authenticated/')).length,before)
  row={...row,shop_id:shop}
  bytes=new Uint8Array(256)
  await assert.rejects(()=>api.downloadPrivateImage(shop,asset),/signature is invalid/)
})


test('media pages use bounded tenant-JWT reads, stable order and fail-closed response shape', async () => {
  const shop='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  const foreign='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'
  const requests=[]
  let rows=[]
  const api=fixture(async (url,options)=>{
    if(url.includes('/auth/v1/token')) return json({access_token:'media-user-jwt',refresh_token:'refresh',expires_in:3600})
    if(url.includes('/rest/v1/media_assets')) {requests.push({url,options});return json(rows)}
    throw Error('Unexpected request '+url)
  })
  await api.signIn('owner@example.test','secret')
  await assert.rejects(()=>api.listMediaAssetsPage('invalid',0),/Invalid media page scope/)
  await assert.rejects(()=>api.listMediaAssetsPage(shop,-100),/Invalid media page scope/)
  await assert.rejects(()=>api.listMediaAssetsPage(shop,1),/Invalid media page scope/)
  assert.equal(requests.length,0)
  const makeRow=i=>({id:'a1000000-0000-4000-8000-'+String(i).padStart(12,'0'),
    shop_id:shop,source:'UPLOAD',license_name:'owned',mime_type:'image/png'})
  rows=Array.from({length:101},(_,i)=>makeRow(i+1))
  const first=await api.listMediaAssetsPage(shop)
  assert.equal(first.items.length,100)
  assert.equal(first.nextOffset,100)
  const u=new URL(requests[0].url)
  assert.equal(u.searchParams.get('shop_id'),'eq.'+shop)
  assert.equal(u.searchParams.get('order'),'created_at.desc,id.desc')
  assert.equal(u.searchParams.get('limit'),'101')
  assert.equal(u.searchParams.get('offset'),'0')
  assert.equal(requests[0].options.headers.Authorization,'Bearer media-user-jwt')
  assert.doesNotMatch(JSON.stringify(requests[0]),/sb_secret_|service_role|object\/public/)
  rows=[makeRow(101),{...makeRow(102),shop_id:foreign}]
  const second=await api.listMediaAssetsPage(shop,100)
  assert.equal(second.items.length,1)
  assert.equal(second.nextOffset,null)
  assert.equal(new URL(requests[1].url).searchParams.get('offset'),'100')
  rows=Array.from({length:102},(_,i)=>makeRow(i+1))
  await assert.rejects(()=>api.listMediaAssetsPage(shop,200),/could not be verified/)
  rows={error:'unexpected'}
  await assert.rejects(()=>api.listMediaAssetsPage(shop,200),/could not be verified/)
})


test('retailer inbox RPC requires exact JWT/shop/page scope and rejects foreign results',async()=>{
  const shop='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
  const other='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'
  const requests=[]
  let reply={shop_id:shop,matching_total:1,unread_total:1,checked_at:'2026-10-28T11:00:00Z',
    items:[{id:5,shop_id:shop,category:'video',severity:'info',
      title:'Reel rendering completed',detail:'Server verified',created_at:'2026-10-28T11:00:00Z',read_at:null}]}
  const api=fixture(async(url,options)=>{
    if(url.includes('/auth/v1/token'))return json({access_token:'user-retail-jwt',refresh_token:'refresh',expires_in:3600})
    if(url.includes('/rest/v1/rpc/retail_retailer_inbox')){requests.push({url,options});return json(reply)}
    if(url.includes('/rest/v1/rpc/retail_retailer_set_inbox_read')){requests.push({url,options});return json({shop_id:shop,id:5,read:true})}
    throw Error('Unexpected call '+url)
  })
  await api.signIn('owner@example.invalid','secret')
  await assert.rejects(()=>api.listRetailerInbox(other,'all','all',100,0),/Invalid retailer inbox scope/)
  await assert.rejects(()=>api.listRetailerInbox(shop,'bad'),/Invalid retailer inbox scope/)
  await assert.rejects(()=>api.listRetailerInbox(shop,'all','all',20,-1),/Invalid retailer inbox scope/)
  assert.equal(requests.length,0)
  const data=await api.listRetailerInbox(shop,'unread','video',20,0)
  assert.equal(data.items.length,1)
  const call=requests[0]
  assert.equal(call.options.headers.Authorization,'Bearer user-retail-jwt')
  assert.equal(call.options.headers.apikey,'sb_publishable_example')
  assert.deepEqual(JSON.parse(call.options.body),{
    p_shop_id:shop,p_view:'unread',p_category:'video',p_limit:20,p_offset:0})
  assert.doesNotMatch(JSON.stringify(call),/sb_secret_|service_role/)
  reply={...reply,items:[{...reply.items[0],shop_id:other}]}
  await assert.rejects(()=>api.listRetailerInbox(shop),/could not be verified/)
  reply={...reply,items:Array(21).fill(reply.items[0])}
  await assert.rejects(()=>api.listRetailerInbox(shop),/could not be verified/)
  const wrote=await api.setRetailerInboxRead(shop,5,true)
  assert.deepEqual(wrote,{shop_id:shop,id:5,read:true})
  assert.equal(requests[requests.length-1].options.headers.Authorization,'Bearer user-retail-jwt')
  await assert.rejects(()=>api.setRetailerInboxRead(shop,5,false),/was not confirmed/)
  await assert.rejects(()=>api.setRetailerInboxRead('wrong',5,true),/Invalid retailer inbox update/)
  await assert.rejects(()=>api.setRetailerInboxRead(shop,0,true),/Invalid retailer inbox update/)
})

test('signed Feature3 immutable model-original upload preserves actual PNG SHA and does not auto-approve',async()=>{
 const {createHash}=await import('node:crypto')
 const model='dddddddd-dddd-4ddd-8ddd-dddddddddddd'
 const calls=[]
 const client=createRetailClient({
  url:'https://rg.example.supabase.co',key:'sb_publishable_demo',storage:storage(),
  fetchImpl:async(url,options)=>{
   calls.push({url,options})
   if(url.includes('/auth/v1/token'))return json({
    access_token:'signed-owner-jwt',refresh_token:'refresh',expires_in:3600})
   if(url.includes('/storage/v1/object/'))return json({Key:'private'},201)
   throw Error('Unexpected Feature3 original transport')
  },
 })
 await client.signIn('retailer@example.invalid','fictional-test-password')
 const png=pngFile()
 const sha=createHash('sha256').update(new Uint8Array(await png.arrayBuffer())).digest('hex')
 const result=await client.uploadModelOriginal(mediaShop,{
  modelId:model,file:png,licenseName:'owned',
  attribution:'Original fictional adult model created by our team',
  confirmedRights:true,
 })
 assert.equal(result.image_sha256,sha)
 assert.equal(result.registered,false)
 assert.equal(result.rights_verified,false)
 assert.equal(result.object_path,mediaShop+'/model-library/'+model+'/'+sha+'.png')
 const uploads=calls.filter(x=>x.url.includes('/storage/v1/object/'))
 assert.equal(uploads.length,1)
 assert.equal(uploads[0].options.headers.Authorization,'Bearer signed-owner-jwt')
 assert.equal(uploads[0].options.headers['x-upsert'],'false')
 assert.equal(calls.filter(x=>x.url.includes('/rest/v1/rpc')).length,0)
})
test('Feature3 original upload refuses unsupported file, missing rights or foreign UUID before network',async()=>{
 const client=createRetailClient({url:'https://rg.example.supabase.co',
  key:'sb_publishable_demo',storage:storage(),
  fetchImpl:async(url)=>{if(url.includes('/auth/v1/token'))return json({
    access_token:'signed-owner',refresh_token:'ref',expires_in:3600})
    throw Error('Unauthorised network access')},
 })
 await client.signIn('editor@example.invalid','fictional-test-password')
 const model='dddddddd-dddd-4ddd-8ddd-dddddddddddd'
 const opts={modelId:model,file:pngFile(),licenseName:'owned',
  attribution:'Self-created fictional adult fashion model',confirmedRights:true}
 await assert.rejects(client.uploadModelOriginal(mediaShop,{...opts,confirmedRights:false}))
 await assert.rejects(client.uploadModelOriginal('wrong-shop',opts))
 await assert.rejects(client.uploadModelOriginal(mediaShop,{...opts,modelId:'bad-model'}))
 await assert.rejects(client.uploadModelOriginal(mediaShop,{...opts,file:new Blob([new Uint8Array(150)],{type:'image/png'})}))
 await assert.rejects(client.uploadModelOriginal(mediaShop,{...opts,licenseName:'commercial',licenseUrl:'http://example.invalid'}))
})
