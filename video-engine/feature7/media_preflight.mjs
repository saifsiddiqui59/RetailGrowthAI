/**
 * Feature7 isolated private MP4 preflight (NO HTTP upload, no tenant auth).
 *
 * Caller MUST have already authenticated the user and obtained the *server's*
 * current RLS/rights snapshot; untrusted browser metadata is never a grant.
 * This module verifies exact staged local bytes, stream shape and asset lineage.
 * No media is modified; no URL is fetched.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';

export class FootagePreflightError extends Error {}

const requireCheck = (ok, msg) => {
  if (!ok) throw new FootagePreflightError(msg);
};
const SHA = /^[0-9a-f]{64}$/;
const KEY = /^[A-Za-z0-9_-]{1,120}$/;
const MAX_BYTES = 128 * 1024 * 1024;

function secureLocalFile(root, relativePath) {
  requireCheck(typeof root === 'string' && path.isAbsolute(root), 'Private media root must be absolute');
  requireCheck(typeof relativePath === 'string' && relativePath.length <= 220 &&
    !path.isAbsolute(relativePath) && !relativePath.includes('\\') &&
    /^[A-Za-z0-9._/-]+$/.test(relativePath) &&
    relativePath.split('/').every(x => x !== '..' && x !== '.' && x !== ''),
  'Invalid private relative path');
  const realRoot = fs.realpathSync(root);
  const requested = path.resolve(realRoot, relativePath);
  const st = fs.lstatSync(requested);
  requireCheck(st.isFile() && !st.isSymbolicLink() && st.size > 0 &&
    st.size <= MAX_BYTES, 'Invalid, linked, empty or oversized file');
  const realFile = fs.realpathSync(requested);
  requireCheck(realFile.startsWith(realRoot + path.sep), 'Private media escape');
  return {realFile, st};
}

export function verifyPrivateVideo({shop_id, asset_id, grant, root, relative_path, expected_sha256,
  ffprobe_bin='ffprobe'}={}) {
  requireCheck(typeof shop_id==='string' && KEY.test(shop_id) &&
    typeof asset_id==='string' && KEY.test(asset_id), 'Invalid tenant/media identifiers');
  requireCheck(grant && grant.shop_id===shop_id && grant.asset_id===asset_id &&
    grant.issued_by==='trusted_server' && grant.source==='retailer_upload' &&
    grant.active===true && grant.rights_status==='APPROVED' &&
    grant.media_type==='video' && grant.mime_type==='video/mp4' &&
    grant.relative_path===relative_path &&
    grant.sha256===expected_sha256 && SHA.test(expected_sha256),
  'Missing same-tenant private MP4 approval or integrity');
  requireCheck(typeof relative_path==='string' && relative_path.toLowerCase().endsWith('.mp4'),
    'Unsupported upload container');
  const {realFile,st}=secureLocalFile(root,relative_path);
  // MP4 cannot be verified by file suffix alone.
  const h=Buffer.alloc(12);
  const fd=fs.openSync(realFile,'r');
  try {requireCheck(fs.readSync(fd,h,0,12,0)===12 && h.toString('ascii',4,8)==='ftyp',
    'Invalid MP4 signature');} finally {fs.closeSync(fd);}
  const bytes=fs.readFileSync(realFile); // bounded by MAX_BYTES before read
  const computed=crypto.createHash('sha256').update(bytes).digest('hex');
  requireCheck(computed===expected_sha256,'Media bytes SHA256 differs from approved grant');
  const p=spawnSync(ffprobe_bin,['-v','error','-show_entries',
    'format=duration,size:stream=codec_type,codec_name,width,height,sample_rate,channels',
    '-of','json',realFile],{encoding:'utf8',timeout:10000,maxBuffer:256*1024});
  requireCheck(!p.error && p.status===0,'Private ffprobe failed');
  let parsed;
  try {parsed=JSON.parse(p.stdout);}catch {throw new FootagePreflightError('Invalid ffprobe response');}
  const vids=(parsed.streams??[]).filter(s=>s.codec_type==='video');
  const audios=(parsed.streams??[]).filter(s=>s.codec_type==='audio');
  const duration=Number(parsed.format?.duration);
  requireCheck(vids.length===1 && audios.length<=1 &&
    ['h264','hevc'].includes(vids[0].codec_name) &&
    Number.isInteger(vids[0].width) && Number.isInteger(vids[0].height) &&
    vids[0].width>0 && vids[0].width<=3840 &&
    vids[0].height>0 && vids[0].height<=3840 &&
    Number.isFinite(duration) && duration>=0.5 && duration<=600,
    'Unsupported or unsafe video streams');
  requireCheck(audios.every(a=>['aac','mp3','opus'].includes(a.codec_name) &&
    Number(a.channels)>=1 && Number(a.channels)<=2),
  'Unsupported or unsafe audio streams');
  return Object.freeze({
    shop_id,asset_id,relative_path,sha256:computed,bytes:st.size,
    duration_seconds:duration,width:vids[0].width,height:vids[0].height,
    video_codec:vids[0].codec_name,has_audio:audios.length===1,
    audio_codec:audios[0]?.codec_name??null,read_only:true,
    validation:'LOCAL_BYTES_VERIFIED'
  });
}

// Consumed only by the server-side, tightly scoped worker. Never return raw
// realFile in a customer response or trust a browser-supplied CLI path.
export function resolveApprovedLocalVideo({root,relative_path}) {
  return secureLocalFile(root,relative_path).realFile;
}
