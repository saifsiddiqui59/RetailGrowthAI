import test from 'node:test'
import assert from 'node:assert/strict'
import {validInboxTime,verifyRetailerInbox} from '../../frontend/src/features/dashboard/retailer-inbox-model.mjs'

const SHOP='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
const OTHER='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'
const first={id:1,shop_id:SHOP,category:'video',severity:'info',
 title:'Video rendering completed',detail:'The recorded render completed.',
 created_at:'2026-10-28T11:00:00.123456+00:00',read_at:null}
const sample=()=>({shop_id:SHOP,checked_at:'2026-10-28T11:30:00+00:00',
 matching_total:1,unread_total:1,items:[{...first}]})
const denied=reply=>assert.throws(()=>verifyRetailerInbox(SHOP,reply),/could not be verified/)

test('Postgres UTC and offset timestamps accept leap calendar and six-digit precision',()=>{
 for(const value of ['2026-10-28T11:30:00+00:00','2026-10-28T11:30:00.123456Z',
  '2028-02-29T23:59:59+05:30','2026-10-28T09:00:00.1-04:00']){
  assert.equal(validInboxTime(value),true,value)
 }
 for(const value of ['2026-02-29T11:00:00Z','2026-02-31T11:00:00Z',
  '2026-04-31T11:00:00Z','2026-10-28T24:00:00Z','2026-10-28T12:60:00Z',
  '2026-10-28T12:00:60Z','2026-10-28T11:30:00+24:00',
  '2026-10-28T11:30:00.1234567Z','2026-10-28','not-a-date',null]){
  assert.equal(validInboxTime(value),false,String(value))
 }
})
test('read RPC accepts safe, bounded current-shop fields and strips no secrets into the page',()=>{
 const result=verifyRetailerInbox(SHOP,sample())
 assert.deepEqual(result,sample())
 assert.equal(result.items[0].shop_id,SHOP)
 const mixed={...sample(),items:[{...first,read_at:'2026-10-28T11:05:00.000001Z'}],unread_total:0}
 assert.equal(verifyRetailerInbox(SHOP,mixed).items[0].read_at,mixed.items[0].read_at)
 assert.equal(verifyRetailerInbox(SHOP,mixed,'all','video',20).items.length,1)
 assert.throws(()=>verifyRetailerInbox(SHOP,mixed,'unread','video',20),/could not be verified/)
})
test('inbox fails closed on foreign records, duplicates, extra tokens and forged counts',()=>{
 const base=sample()
 const bad=[
  {...base,shop_id:OTHER},
  {...base,token:'hidden'},
  {...base,checked_at:'2026-02-31T11:00:00Z'},
  {...base,matching_total:-1},
  {...base,matching_total:0},
  {...base,unread_total:1.2},
  {...base,items:[{...first,shop_id:OTHER}]},
  {...base,items:[{...first,access_token:'do-not-cache'}]},
  {...base,items:[{...first,read_at:'wrong'}]},
  {...base,items:[{...first,created_at:'2026-02-30T11:00:00Z'}]},
  {...base,items:[{...first,read_at:123}]},
  {...base,items:[{...first,category:'other'}]},
  {...base,items:[{...first,severity:'critical'}]},
  {...base,items:[{...first,title:''}]},
  {...base,items:[{...first,detail:'x'.repeat(241)}]},
  {...base,items:[{...first,id:0}]},
  {...base,items:[first,{...first}],matching_total:2},
  {...base,items:Array(21).fill(first),matching_total:21}
 ]
 for(const x of bad)denied(x)
 assert.throws(()=>verifyRetailerInbox(SHOP,{...base,items:[{...first,category:'video'}]},'all','poster'),/could not be verified/)
 assert.throws(()=>verifyRetailerInbox(SHOP,base,'unread','video',0),/could not be verified/)
 assert.throws(()=>verifyRetailerInbox('not-shop',base),/could not be verified/)
})
