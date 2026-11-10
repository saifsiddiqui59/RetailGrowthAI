/**
 * Feature7 immutable, private, per-job MP4 snapshot for CPU media analysis.
 *
 * First verify the registered original, then copy exact bytes through an
 * O_NOFOLLOW file descriptor into a 0700 scratch directory, probe the copy,
 * and invoke an internal synchronous analysis callback against the SNAPSHOT.
 * Re-probe the original and delete every staged byte even on exceptions.
 *
 * This narrows media path/hash TOCTOU within Feature7. It does NOT implement
 * a PostgreSQL row lock, cloud object generation precondition or durable DB
 * rights authorization. Production coordinator must bind media generation and
 * current tenant rights to an actual transaction/lease before publishing.
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import {verifyPrivateVideo,resolveApprovedLocalVideo} from './media_preflight.mjs';

export class MediaSnapshotError extends Error {}
const check=(condition,msg)=>{if(!condition)throw new MediaSnapshotError(msg);};
const MAX_ITEMS=12,MAX_TOTAL_BYTES=256*1024*1024;
const KEY=/^[A-Za-z0-9_-]{1,120}$/;

function frozenCopy(source,dest,expectedSha,maxBytes){
  const fd=fs.openSync(source,fs.constants.O_RDONLY|(fs.constants.O_NOFOLLOW??0));
  let out;
  try {
    const before=fs.fstatSync(fd);
    check(before.isFile()&&before.size>12&&before.size<=maxBytes,
      'Invalid source size or type during immutable snapshot');
    out=fs.openSync(dest,
      fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|
        (fs.constants.O_NOFOLLOW??0),0o600);
    const hasher=crypto.createHash('sha256');
    const chunk=Buffer.allocUnsafe(256*1024);
    let remaining=before.size,position=0;
    while(remaining>0){
      const n=fs.readSync(fd,chunk,0,Math.min(chunk.length,remaining),position);
      check(n>0,'Truncated private source during snapshot');
      hasher.update(chunk.subarray(0,n));
      let written=0;
      while(written<n){
        const count=fs.writeSync(out,chunk,written,n-written);
        check(count>0,'Short private snapshot write');
        written+=count;
      }
      position+=n;remaining-=n;
    }
    fs.fsyncSync(out);
    const after=fs.fstatSync(fd);
    check(after.size===before.size&&after.ino===before.ino&&
      after.mtimeMs===before.mtimeMs&&after.ctimeMs===before.ctimeMs,
      'Private source changed during snapshot copy');
    check(hasher.digest('hex')===expectedSha,'Private snapshot digest mismatch');
  }finally{
    if(out!==undefined)fs.closeSync(out);
    fs.closeSync(fd);
  }
}

export function withVerifiedPrivateVideoSnapshots({
  shop_id,root,media,max_total_bytes=MAX_TOTAL_BYTES,analyze
}={}){
  check(typeof shop_id==='string'&&KEY.test(shop_id)&&
    typeof root==='string'&&path.isAbsolute(root)&&
    Array.isArray(media)&&media.length>0&&media.length<=MAX_ITEMS&&
    typeof analyze==='function'&&
    Number.isSafeInteger(max_total_bytes)&&max_total_bytes>0&&
    max_total_bytes<=MAX_TOTAL_BYTES,
    'Trusted scoped snapshot callback required');
  const seen=new Set();
  let total=0;
  // Each record must originate from the already-validated current media
  // rights loader; never pass browser-supplied grants.
  const approved=media.map(item=>{
    check(item&&item.grant&&item.grant.shop_id===shop_id&&
      typeof item.relative_path==='string'&&
      !seen.has(item.relative_path),'Duplicate or foreign private snapshot');
    seen.add(item.relative_path);
    const info=verifyPrivateVideo({shop_id,asset_id:item.asset_id,
      grant:item.grant,root,relative_path:item.relative_path,
      expected_sha256:item.expected_sha256});
    total+=info.bytes;
    check(total<=max_total_bytes,'Cumulative private analysis budget exceeded');
    return {item,info};
  });
  const scratch=fs.mkdtempSync(path.join(os.tmpdir(),'rg-f7-private-snapshot-'));
  fs.chmodSync(scratch,0o700);
  try{
    for(const {item,info} of approved){
      const relative=item.relative_path;
      const dest=path.resolve(scratch,relative);
      check(dest.startsWith(scratch+path.sep),'Invalid snapshot destination');
      fs.mkdirSync(path.dirname(dest),{recursive:true,mode:0o700});
      const original=resolveApprovedLocalVideo({root,relative_path:relative});
      frozenCopy(original,dest,info.sha256,info.bytes);
      // The analysis owns no write access to its verified input. Mode 0400
      // prevents accidental in-place transforms in normal worker execution;
      // rehashing after analysis below is essential because the same OS
      // process could still chmod its own file.
      fs.chmodSync(dest,0o400);
      const independent=verifyPrivateVideo({shop_id,asset_id:item.asset_id,
        grant:item.grant,root:scratch,relative_path:relative,
        expected_sha256:info.sha256});
      check(independent.sha256===info.sha256 &&
        independent.duration_seconds===info.duration_seconds &&
        independent.video_codec===info.video_codec,
      'Snapshot differs from original verified media');
    }
    const result=analyze(scratch);
    // The analysis is deliberately synchronous. A Promise/async callback
    // would outlive the private scratch directory and rights snapshot.
    check(!result||typeof result.then!=='function',
      'Asynchronous snapshot callback is prohibited');
    for(const {item,info} of approved){
      // A trusted synchronous callback could accidentally alter the scratch
      // MP4 even when the original remains byte-identical. Reject its result
      // rather than returning advisory evidence from no-longer-pinned bytes.
      const scratchAgain=verifyPrivateVideo({shop_id,asset_id:item.asset_id,
        grant:item.grant,root:scratch,relative_path:item.relative_path,
        expected_sha256:info.sha256});
      check(scratchAgain.bytes===info.bytes &&
        scratchAgain.duration_seconds===info.duration_seconds,
      'Private frozen snapshot changed during review analysis');
      const again=verifyPrivateVideo({shop_id,asset_id:item.asset_id,
        grant:item.grant,root,relative_path:item.relative_path,
        expected_sha256:info.sha256});
      check(again.bytes===info.bytes &&
        again.duration_seconds===info.duration_seconds,
      'Private source changed during review');
    }
    return result;
  }finally{
    fs.rmSync(scratch,{recursive:true,force:true,maxRetries:2});
  }
}
