import test from 'node:test'
import assert from 'node:assert/strict'
import { createTraceStore } from '../../frontend/src/features/testing/trace-store.mjs'

const SHOP = '11111111-1111-4111-8111-111111111111'
const JOB = '22222222-2222-4222-8222-222222222222'
const JOB2 = '55555555-5555-4555-8555-555555555555'
const ID = '33333333-3333-4333-8333-333333333333'
const timestamp = '2026-11-18T07:30:00+00:00'
const sourceRow = () => ({
  id: ID, shop_id: SHOP, job_id: JOB, feature: 'F2',
  operation: 'planning.complete', status: 'SUCCEEDED', attempt: 1,
  elapsed_ms: 123, metadata: { generated_days: 7, planner_mode: 'dev_mock' },
  recorded_at: timestamp,
})
const reply = (rows, job = JOB) => ({
  shop_id: SHOP, job_id: job, source: 'trusted_backend_persisted',
  events: rows,
})
const web = data => ({ ok: true, status: 200, json: async () => data })
const store = fetchImpl => createTraceStore({
  supabaseUrl: 'https://test.supabase.co',
  publishableKey: 'sb_publishable_fake_test',
  tokenProvider: async () => 'signed-test-user-jwt',
  fetchImpl,
})
const deny = async row => {
  const s = store(async () => web(reply([row])))
  await assert.rejects(() => s.listWorkerSpans(SHOP, [JOB]),
    /inconsistent tenant or source/)
}

test('valid signed F2 and F4 terminal source rows remain readable without a model', async () => {
  const good = sourceRow()
  const rows = await store(async () => web(reply([good]))).listWorkerSpans(SHOP, [JOB])
  assert.deepEqual(rows, [good])
  const f4 = {
    ...sourceRow(), feature: 'F4', operation: 'render.complete',
    metadata: {
      codec: 'h264/aac', video_width: 1080,
      video_height: 1920, duration_seconds: 30,
    },
  }
  assert.deepEqual(await store(async () => web(reply([f4])))
    .listWorkerSpans(SHOP, [JOB]), [f4])
})

test('forged fields, time, IDs, operation statuses and private metadata fail closed', async () => {
  const good = sourceRow()
  const bad = [
    { ...good, id: 'not-a-uuid' },
    { ...good, id: undefined },
    { ...good, extra_private_token: 'must-not-escape-to-ui' },
    { ...good, recorded_at: 'invalid' },
    { ...good, recorded_at: '2099-00-99T00:00:00Z' },
    { ...good, recorded_at: null },
    { ...good, feature: 'constructor', operation: 'name', status: 'Object' },
    { ...good, feature: 'F4', operation: 'planning.complete' },
    { ...good, operation: 'planning.failed' },
    { ...good, operation: 'planning.denied', status: 'SUCCEEDED' },
    { ...good, operation: 'render.complete' },
    { ...good, metadata: null },
    { ...good, metadata: [] },
    { ...good, metadata: { generated_days: 7 } },
    { ...good, metadata: { ...good.metadata, ignored: 'extra' } },
    { ...good, metadata: { generated_days: 6, planner_mode: 'dev_mock' } },
    { ...good, metadata: { generated_days: 7, planner_mode: 'future' } },
  ]
  for (const row of bad) await deny(row)

  const f4 = {
    ...good, feature: 'F4', operation: 'render.complete',
    metadata: {
      codec: 'h264/aac', video_width: 1080,
      video_height: 1920, duration_seconds: 30,
    },
  }
  for (const patch of [
    { video_width: 720 },
    { codec: 'h265/aac' },
    { duration_seconds: 12 },
    { duration_seconds: 30.21 },
    { extra_private: true },
  ]) await deny({ ...f4, metadata: { ...f4.metadata, ...patch } })

  const denied = {
    ...good, operation: 'planning.denied', status: 'DENIED', metadata: {},
  }
  assert.deepEqual(await store(async () => web(reply([denied])))
    .listWorkerSpans(SHOP, [JOB]), [denied])
  await deny({ ...denied, metadata: { generated_days: 7 } })
})

test('duplicate source IDs fail within one RPC and across separately signed jobs', async () => {
  const good = sourceRow()
  const duplicate = { ...good, attempt: 2 }
  await assert.rejects(
    () => store(async () => web(reply([good, duplicate]))).listWorkerSpans(SHOP, [JOB]),
    /inconsistent tenant or source/,
  )
  const twoJobs = store(async (_url, init) => {
    const job = JSON.parse(init.body).p_job_id
    return web(reply([{ ...good, job_id: job }], job))
  })
  await assert.rejects(
    () => twoJobs.listWorkerSpans(SHOP, [JOB, JOB2]),
    /inconsistent tenant or source/,
  )
})
