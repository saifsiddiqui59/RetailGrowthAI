import test from 'node:test';
import assert from 'node:assert/strict';
import { DEV_PROJECT_REF,verifyPreflight } from './dev-db-preflight.mjs';
import { scopedFeature2Plan, FEATURE2_FILE,OTHER_FEATURE_FILE } from './feature2_scoped_dev_release_plan.mjs';
const now='2026-10-27T06:40:00.000Z';
const all=verifyPreflight().local;
const remote=(applied=all.slice(0,21))=>({project_ref:DEV_PROJECT_REF,captured_at:now,applied});

test('Feature2 exact hosted prefix selects only the reviewed AI ledger; excludes Feature3',()=>{
  const p=scopedFeature2Plan(remote(),{now});
  assert.equal(p.project_ref,DEV_PROJECT_REF);
  assert.equal(p.reviewed_applied_versions,21);
  assert.equal(p.source_file,FEATURE2_FILE);
  assert.equal(p.other_pending_version_remains_unapplied,OTHER_FEATURE_FILE.slice(0,14));
  assert.match(p.source_sha256,/^[a-f0-9]{64}$/);
  assert.equal(p.authorized_to_apply,false);
  assert.equal(p.actual_hosted_sql_execution,false);
  assert.equal(p.backup_restore_verified,false);
});

test('Fail closed for wrong project, fabricated freshness, gaps, drift, applied Feature3, surprise remote',()=>{
  assert.throws(()=>scopedFeature2Plan({...remote(),project_ref:'wrong'},{now}),/Only exact/);
  assert.throws(()=>scopedFeature2Plan({...remote(),captured_at:'2026-10-01T00:00:00Z'},{now}),/fresh/);
  assert.throws(()=>scopedFeature2Plan(remote(all.slice(0,20)),{now}),/21 applied/);
  assert.throws(()=>scopedFeature2Plan(remote(all.slice(0,22)),{now}),/21 applied/);
  assert.throws(()=>scopedFeature2Plan(remote([...all.slice(0,20),all[22]]),{now}),/diverges/);
  assert.throws(()=>scopedFeature2Plan(remote([...all.slice(0,21),{version:'20990101000000',name:'surprise'}]),{now}),/diverges/);
});
