#!/usr/bin/env python3
"""Deterministic ORIGINAL synthetic music bed for Feature4 local mixing tests.

No third-party sample packs, copyright songs, music API, AI provider or cloud.
Generated original tones/percussion ONLY. This is NOT a viral song, real
voiceover, licensed commercial stock track or authenticated tenant audio.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import argparse
import json
import math
import random
import struct
import wave

RATE=48000
NOTES=(164.81,196.0,220.0,246.94,293.66,261.63,174.61,220.0)
def synth_frame(time,sample_index,length):
    # Original deterministic instrument sequence, with no borrowed melody.
    phase=(time*1.47)%1
    idx=int(time*1.47)
    root=NOTES[(idx//4)%len(NOTES)]
    pulse=math.exp(-11*phase)
    note=0.12*(math.sin(2*math.pi*root*time)*pulse +
               0.3*math.sin(2*math.pi*root*2.013*time)*pulse)
    kick=0.21*math.exp(-31*phase)*math.sin(
        2*math.pi*(45+45*math.exp(-26*phase))*time)
    eighth=(time*2.94)%1
    noise=(random.Random(sample_index//2+673).random()*2-1)
    hat=0.045*math.exp(-60*eighth)*noise
    pad=0.07*(math.sin(2*math.pi*82.4*time)+
              math.sin(2*math.pi*123.47*time))*0.5
    fade=min(1,time/0.25,max(0,length-time)/0.35)
    sample=max(-0.77,min(0.77,(note+kick+hat+pad)*fade))
    return int(sample*32767)
def write_original_audio(output,seconds):
    if seconds not in (5,15,30,60):
        raise ValueError("Only bounded 5,15,30,60 second technical music beds")
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():
        raise RuntimeError("Refusing to overwrite a previously generated audio original")
    with wave.open(str(output),"wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        for start in range(0,seconds*RATE,2048):
            block=bytearray()
            for index in range(start,min(start+2048,seconds*RATE)):
                block.extend(struct.pack("<h",synth_frame(index/RATE,index,seconds)))
            f.writeframesraw(block)
    original=output.read_bytes()
    return {"schema":"retailgrowth.feature2-original-music-test.v1",
            "filename":output.name,"sha256":sha256(original).hexdigest(),
            "duration_seconds":seconds,"sample_rate":RATE,"channels":1,
            "encoding":"PCM_S16LE","origin":"ORIGINAL_ALGORITHMIC_NOT_SAMPLED",
            "test_only":True,"contains_real_speech":False,
            "commercial_music_license_reviewed":False,
            "tenant_private_imported":False,"can_publish":False}
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",required=True)
    parser.add_argument("--seconds",type=int,default=30)
    a=parser.parse_args()
    root=Path(a.output_dir).resolve()
    result=write_original_audio(root/("feature2-original-test-bed-"+str(a.seconds)+"s.wav"),a.seconds)
    (root/"original-audio-provenance.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
