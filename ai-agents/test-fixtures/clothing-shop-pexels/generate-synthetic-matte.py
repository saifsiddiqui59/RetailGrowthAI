#!/usr/bin/env python3
"""Create real reproducible 1080x1920 RGB PNG for OFFLINE F4/F5 input decoding.

No network, Pillow, model generation or permissions. This is merely a
stylized garment silhouette; never a real apparel photo, human model,
commercial license, signed source, retailer SKU or deployable asset.
"""
from __future__ import annotations
from pathlib import Path
from hashlib import sha256
import argparse
import json
import struct
import zlib

W,H=1080,1920
def chunk(kind,payload):
    return struct.pack(">I",len(payload))+kind+payload+struct.pack(">I",zlib.crc32(kind+payload)&0xffffffff)
def pixel(x,y):
    shade=max(0,round(235-30*y/H))
    bg=(shade,max(0,shade-9),max(0,shade-25))
    waist=160+int(max(y-700,0)*0.07)
    body=500<=y<1520 and abs(x-540)<waist
    sleeves=510<=y<1000 and (225<=x<350+int((y-510)*0.12) or
         730-int((y-510)*0.12)<x<=855)
    if not body and not sleeves:return bg
    if y<602 and (x-540)**2+(y-524)**2<88**2:return bg
    if 750<=y<1320 and abs(x-540)<118 and ((x//30+y//39)%7==0):
        return (197,156,76)
    return (126+int(y/130)%9,29,46)
def original_png():
    compressor=zlib.compressobj(6)
    packed=[]
    for y in range(H):
        row=bytearray(b"\0")
        for x in range(W):row.extend(pixel(x,y))
        block=compressor.compress(bytes(row))
        if block:packed.append(block)
    packed.append(compressor.flush())
    note=b"Description\0Original retailgrowth test matte; not real licensed fashion media"
    return (b"\x89PNG\r\n\x1a\n"+
            chunk(b"IHDR",struct.pack(">IIBBBBB",W,H,8,2,0,0,0))+
            chunk(b"tEXt",note)+chunk(b"IDAT",b"".join(packed))+
            chunk(b"IEND",b""))
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args()
    root=Path(args.output_dir).resolve()
    root.mkdir(parents=True,exist_ok=True)
    data=original_png()
    target=root/"feature2-synthetic-first-frame.png"
    if target.exists() and target.read_bytes()!=data:
        raise RuntimeError("Cannot overwrite untrusted existing original")
    if not target.exists():target.write_bytes(data)
    meta={
        "schema":"retailgrowth.synthetic-motion-input.v1",
        "filename":target.name,"sha256":sha256(data).hexdigest(),
        "width":W,"height":H,
        "fixture_only":True,"source":"Python standard library original geometry",
        "real_fashion_photo":False,"human_model_present":False,
        "approved_garment_identity":False,"private_asset_id":None,
        "licensed_stock_source":False,"paid_motion_authorized":False,
        "can_publish":False
    }
    (root/"source-provenance.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps(meta,sort_keys=True))
if __name__=="__main__":main()
