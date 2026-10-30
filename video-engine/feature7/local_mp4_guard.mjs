/**
 * Feature7 shared defense-in-depth for offline FFmpeg analysis sources.
 * This is not an authorization check: callers must use a frozen, tenant-
 * approved, integrity-verified private MP4 snapshot from their own worker.
 * FFmpeg's demuxer and protocol whitelist must also be restricted by callers.
 */
import fs from 'node:fs';
import path from 'node:path';

export function verifiedLocalMp4Path(sourcePath, ErrorType=Error){
  const check=(ok,msg)=>{if(!ok)throw new ErrorType(msg);};
  check(typeof sourcePath==='string' && sourcePath.length<=4096 &&
    path.isAbsolute(sourcePath),'Absolute private MP4 path required');
  const before=fs.lstatSync(sourcePath);
  check(before.isFile() && !before.isSymbolicLink() && before.size>12 && before.size<=128*1024*1024,
    'Private analysis requires a regular MP4, not a link');
  const fd=fs.openSync(sourcePath,
    fs.constants.O_RDONLY|(fs.constants.O_NOFOLLOW??0));
  try{
    const current=fs.fstatSync(fd);
    check(current.isFile() && current.dev===before.dev &&
      current.ino===before.ino && current.size===before.size,
    'Private MP4 changed before inspection');
    const signature=Buffer.alloc(8);
    check(fs.readSync(fd,signature,0,8,0)===8 &&
      signature.toString('ascii',4,8)==='ftyp',
    'Private analysis requires MP4 bytes');
  }finally{fs.closeSync(fd);}
  return fs.realpathSync(sourcePath);
}
