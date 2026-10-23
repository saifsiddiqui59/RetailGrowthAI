import test from 'node:test'
import assert from 'node:assert/strict'
import { DEFAULT_VIDEO_ENGINE, PREMIUM_VIDEO_STATUS, premiumVideoChoices,
         validatePremiumRequest } from '../../frontend/src/features/premium-video/premium-video-model.mjs'

const DID = '123e4567-e89b-42d3-a456-426614174004'
const AID = '123e4567-e89b-42d3-a456-426614174005'

test('FFmpeg is always the default and premium cannot be selected by default', () => {
  assert.equal(DEFAULT_VIDEO_ENGINE, 'ffmpeg')
  assert.equal(PREMIUM_VIDEO_STATUS, 'AWAITING_PROVIDER_AND_CREDIT_APPROVAL')
  const choices = premiumVideoChoices()
  assert.equal(choices[0].available, true)
  assert.equal(choices[1].available, false)
})

test('frontend feature flag alone is never an entitlement', () => {
  assert.equal(premiumVideoChoices({ featureEnabled:true })[1].available, false)
  assert.equal(premiumVideoChoices({ featureEnabled:true, endpointReady:true })[1].available, false)
  assert.equal(premiumVideoChoices({ featureEnabled:true, entitlement:true })[1].available, false)
})

test('disabled premium request is rejected even with a valid UUID', () => {
  assert.throws(() => validatePremiumRequest({
    day_id:DID,mode:'text',resolution:'720P',duration_seconds:5,input_asset_id:null,
  }), /not activated/)
})

test('fully approved contract only admits valid premium input options', () => {
  const gate = { entitlement:true, endpointReady:true, featureEnabled:true }
  const input = { day_id:DID,mode:'text',resolution:'720P',duration_seconds:5,input_asset_id:null }
  assert.deepEqual(validatePremiumRequest(input, gate), input)
  for (const candidate of [
    { ...input, day_id:'../escape' },
    { ...input, duration_seconds:0 },
    { ...input, duration_seconds:3.5 },
    { ...input, resolution:'4K' },
    { ...input, mode:'image', input_asset_id:null },
    { ...input, mode:'text', input_asset_id:AID },
  ]) {
    assert.throws(() => validatePremiumRequest(candidate, gate), /Invalid premium video/)
  }
  assert.equal(validatePremiumRequest({ ...input, mode:'image', input_asset_id:AID }, gate)
               .input_asset_id, AID)
})
