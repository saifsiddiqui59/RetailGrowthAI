import test from 'node:test'
import assert from 'node:assert/strict'
import {createPrivateTraceRequestGate} from '../../frontend/src/features/voiceover/voiceover-trace-request-gate.mjs'

test('a private trace response cannot outlive shop/workflow/rights scope',()=>{
  const gate=createPrivateTraceRequestGate()
  gate.setScope('shop-A:campaign-A:workflow-A:source-A:enabled')
  const first=gate.begin('shop-A:campaign-A:workflow-A:source-A:enabled')
  assert.equal(gate.valid(first,first.scope),true)
  gate.setScope('shop-B:campaign-A:workflow-A:source-A:enabled')
  assert.equal(gate.valid(first,first.scope),false)
  const second=gate.begin('shop-B:campaign-A:workflow-A:source-A:enabled')
  assert.equal(gate.valid(second,second.scope),true)
  gate.setScope('shop-B:campaign-A:workflow-A:source-A:disabled')
  assert.equal(gate.valid(second,second.scope),false)
})
test('overlapping reads and reader replacement invalidate stale success and error',()=>{
  const gate=createPrivateTraceRequestGate()
  const old=gate.begin('shop:campaign:workflow:source:enabled')
  const newer=gate.begin(old.scope)
  assert.equal(gate.valid(old,old.scope),false)
  assert.equal(gate.valid(newer,newer.scope),true)
  gate.invalidate()
  assert.equal(gate.valid(newer,newer.scope),false)
  assert.equal(gate.valid({scope:newer.scope,generation:999},newer.scope),false)
  assert.throws(()=>gate.setScope(''))
})
