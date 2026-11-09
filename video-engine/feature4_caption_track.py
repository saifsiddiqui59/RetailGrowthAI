"""Strict timecode validation. Feature2 owns text; Feature4 never infers speech."""
import math

def checked_caption_cues(cues, duration):
    if type(duration) is not int or duration not in (15,30,60):
        raise ValueError("Supported Reel duration required")
    if type(cues) is not list or not 1 <= len(cues) <= 60:
        raise ValueError("Expected 1-60 approved timed cues")
    output=[]
    prior_ms=0
    for c in cues:
        if type(c) is not dict or set(c) != {"start","duration","text"}:
            raise ValueError("Unknown or missing reviewed caption fields")
        start,span,text=c["start"],c["duration"],c["text"]
        if (type(start) not in (int,float) or type(span) not in (int,float)
            or not math.isfinite(start) or not math.isfinite(span)
            or start < 0 or span < .2 or span > 6
            or start != round(start, 3) or span != round(span, 3)
            or round(start * 1000) < prior_ms
            or round(start * 1000) + round(span * 1000) > duration * 1000):
            raise ValueError("Overlapping, invalid or out-of-Reel subtitle timing")
        if (type(text) is not str or text != text.strip()
            or not 1 <= len(text) <= 90 or "<" in text or ">" in text
            or any(ord(x)<32 or ord(x)==127 for x in text)):
            raise ValueError("Unapproved/unreadable subtitle text")
        output.append({"start":round(start,3),"duration":round(span,3),"text":text})
        prior_ms=round(start * 1000) + round(span * 1000)
    return output
