#!/usr/bin/env python3
"""Offline licensed synthetic clothing visuals for testing REAL RetailGrowthAI engines.

Creates original vector-style fashion illustrations. Does NOT simulate a hosted
tenant, use unknown stock assets, or copy commercial fashion imagery.
"""
from pathlib import Path
import json
import math
import struct
import wave
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "frontend/src/features/campaigns/fixtures/sample-campaign.json"
OUT = ROOT / "demo/out"
ASSETS = OUT / "assets"
PALETTE = [
    ("#EBE4D9", "#8A514A", "#D5B0A5", "SOFT STRUCTURE"),
    ("#E3EAE7", "#41675F", "#ABC1B8", "EASY LAYERS"),
    ("#F2DFD0", "#B06B43", "#DCAF89", "WEEKEND EDIT"),
]

def rgb(hexvalue):
    return tuple(int(hexvalue[n:n+2], 16) for n in (1,3,5))

def font(size, bold=False):
    from PIL import ImageFont
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)

def garment(d, kind, accent, shadow):
    # Stylized, ORIGINAL geometry. These are illustrations, not product photos.
    cx=360
    if kind == 0:  # tucked-in shirt
        outer=[(cx-107,326),(cx-196,383),(cx-230,545),(cx-153,571),
               (cx-123,481),(cx-122,761),(cx+128,761),(cx+124,481),
               (cx+154,572),(cx+234,548),(cx+197,388),(cx+107,326),
               (cx+52,349),(cx+28,403),(cx-29,403),(cx-54,349)]
        d.polygon([(x+15,y+18) for x,y in outer],fill=shadow)
        d.polygon(outer,fill=accent)
        d.line([(cx,405),(cx,744)],fill="#F3E8DF",width=5)
        for y in (462,539,616):d.ellipse((cx-4,y-4,cx+4,y+4),fill="#EED6CA")
        d.line([(cx-108,383),(cx-67,459),(cx-123,474)],fill="#B57F73",width=5)
        d.line([(cx+107,383),(cx+67,459),(cx+123,474)],fill="#B57F73",width=5)
    elif kind==1:  # linen coat + neutral trousers
        for side in (-1,1):
            x=cx+side*55
            points=[(x,585),(x+side*114,585),(x+side*89,867),(x+side*59,930),
                    (x+side*2,930),(x+side*18,721)]
            d.polygon(points,fill="#B3A998")
        coat=[(cx-115,312),(cx-201,382),(cx-208,757),(cx-66,757),
              (cx,536),(cx+66,757),(cx+208,757),(cx+201,382),(cx+115,312)]
        d.polygon([(x+16,y+20) for x,y in coat],fill="#B8C9C3")
        d.polygon(coat,fill=accent)
        d.polygon([(cx-101,315),(cx-20,444),(cx-64,650)],fill="#79968B")
        d.polygon([(cx+101,315),(cx+20,444),(cx+64,650)],fill="#79968B")
        d.line([(cx-114,586),(cx-190,631)],fill="#C9DAD4",width=5)
        d.line([(cx+114,586),(cx+190,631)],fill="#C9DAD4",width=5)
        d.ellipse((cx-7,592,cx+7,606),fill="#F6F0E5")
    else:  # sundress
        upper=[(cx-83,329),(cx-173,393),(cx-126,547),(cx+126,547),
               (cx+173,393),(cx+83,329),(cx+60,375),(cx-60,375)]
        skirt=[(cx-125,539),(cx+125,539),(cx+255,920),(cx-255,920)]
        d.polygon([(x+13,y+16) for x,y in skirt],fill="#D9B89B")
        d.polygon(skirt,fill=accent)
        d.polygon(upper,fill=accent)
        d.line([(cx-126,543),(cx+125,543)],fill="#EDC39E",width=6)
        for delta in (-105,-54,54,105):
            d.line([(cx+delta//2,554),(cx+delta,902)],fill="#DFB38E",width=4)
        d.line([(cx-60,371),(cx-28,410),(cx,371),(cx+28,410),(cx+60,371)],
               fill="#F7E5D7",width=5)

def card(number, entry):
    bg,cloth,detail,label=entry
    im=Image.new("RGB",(720,1280),rgb(bg))
    d=ImageDraw.Draw(im)
    # Editorial art board with restrained paper grain, framing, and faux studio light.
    d.rounded_rectangle((45,205,675,1025),radius=36,fill="#FBF7F0")
    for n in range(34):
        x=43+n*19
        d.line([(x,208),(x-75,1023)],fill=bg,width=2)
    d.ellipse((-100,260,340,770),fill=detail)
    d.ellipse((426,640,915,1190),fill=bg)
    d.rounded_rectangle((81,252,639,984),radius=26,fill="#F8F4ED")
    d.ellipse((132,842,590,958),fill="#D3D0CA")
    garment(d,number,cloth,detail)
    d.text((64,64),"EVERYDAY EDIT",fill="#343835",font=font(41,True))
    d.text((65,128),"A thoughtful wardrobe. Your way.",fill="#62625B",font=font(23))
    d.line((64,173,655,173),fill=cloth,width=5)
    d.text((67,1070),label,fill="#4B4844",font=font(31,True))
    d.text((67,1134),"Original illustrated fashion concept",fill="#69675F",font=font(19))
    im.save(ASSETS/f"look{number+1}.jpg",quality=94,subsampling=0)

def sound():
    path=ASSETS/"original-demo-melody.wav"
    sample_rate=22050
    duration=30
    notes=(261.63,329.63,392.00,329.63,293.66,392.00,440.0,392.0)
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sample_rate)
        # Simple original procedural 8-note motif; no borrowed track.
        for chunk_start in range(0,sample_rate*duration,4096):
            data=bytearray()
            for i in range(chunk_start,min(chunk_start+4096,sample_rate*duration)):
                t=i/sample_rate
                beat=int(t*2)%len(notes)
                f=notes[beat]
                pos=(t*2)%1
                envelope=min(1,pos*12)*min(1,(1-pos)*5)
                v=(math.sin(2*math.pi*f*t)*0.12+
                   math.sin(2*math.pi*f*2*t)*0.045)*envelope
                v+=0.025*math.sin(2*math.pi*130.81*t)
                data+=struct.pack("<h",int(max(-1,min(1,v))*32767))
            w.writeframesraw(data)
    return path

def main():
    ASSETS.mkdir(parents=True,exist_ok=True)
    campaign=json.loads(FIXTURE.read_text(encoding="utf-8"))
    day=campaign["days"][0]
    for i,entry in enumerate(PALETTE):card(i,entry)
    sound()
    ids=[x["asset_id"] for x in day["instagram"]["reel"]["storyboard"]]
    rights={"commercial_use":True,"license":"owned",
      "source":"demo/clothing/generate.py (original procedural illustrations)",
      "evidence":"Fully authored programmatic silhouettes, no external images"}
    manifest={"shop_id":campaign["shop_id"],"assets":{
      asset_id:{"kind":"image","path":f"look{i+1}.jpg","rights":rights}
      for i,asset_id in enumerate(ids)}}
    manifest["assets"]["original_demo_audio"]={
      "kind":"audio","path":"original-demo-melody.wav",
      "rights":{"commercial_use":True,"license":"owned",
        "source":"demo/clothing/generate.py","evidence":"Original procedural sound, not a licensed commercial recording"}}
    day["instagram"]["reel"]["music_asset_id"]="original_demo_audio"
    (OUT/"campaign.json").write_text(json.dumps(campaign,indent=2),encoding="utf-8")
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    (OUT/"linkedin_post.txt").write_text(day["linkedin"]["post_text"]+"\n\n"+
      " ".join(day["linkedin"]["hashtags"])+"\n",encoding="utf-8")
    (OUT/"instagram_caption.txt").write_text(day["instagram"]["caption"]+"\n",encoding="utf-8")
    (OUT/"README.txt").write_text(
      "RetailGrowthAI REAL ENGINE OFFLINE TEST — Clothing campaign / Day 1\n"
      "Source: frozen seven-day clothing fixture, original locally generated illustrations.\n"
      "Poster: actual poster-engine/render.py; video: actual video-engine/render.py.\n"
      "No Azure backend, Supabase user session, external stock photo, provider AI or publishing tested.\n"
      "Video: vertical 30 seconds, H.264/AAC with original procedural test music.\n"
      "Artwork is deliberately synthetic and NOT a photographed clothing product.\n",
      encoding="utf-8")
    print(json.dumps({"generated_media":[str(p) for p in ASSETS.glob("*")],
      "day":day["topic"],"caption":day["instagram"]["caption"]}))

if __name__=="__main__":
    main()
