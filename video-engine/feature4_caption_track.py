"""Strict timecode validation. Feature2 owns text; Feature4 never infers speech."""
import math
import unicodedata

# Automatic Unicode directional layout remains supported for real scripts.
# Explicit bidi-override/isolate characters could visually spoof approved copy.
_BIDI_OVERRIDE = frozenset({"RLO","LRO","RLE","LRE","PDF","RLI","LRI","FSI","PDI"})


def caption_font_px(text, width):
    """Deterministic approved-text density preset, without editing the words."""
    if (type(text) is not str or not 1 <= len(text) <= 90
            or type(width) is not int or width not in (540, 1080)):
        raise ValueError("Unsupported reviewed caption typography")
    divisor = 19 if len(text) <= 45 else 23 if len(text) <= 70 else 28
    return max(18, width // divisor)


def _unrenderable_or_spoofed(text):
    if not any(unicodedata.category(ch)[0] in "LNS" for ch in text):
        return True
    return any(
        unicodedata.bidirectional(ch) in _BIDI_OVERRIDE
        or ch in ("\u200b", "\u2060", "\ufeff", "\u00ad", "\u200e", "\u200f")
        or (unicodedata.category(ch) in ("Cc","Cf","Cs","Co","Zl","Zp")
            and ch not in ("\u200c", "\u200d"))
        for ch in text
    )


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
            or _unrenderable_or_spoofed(text)):
            raise ValueError("Unapproved/unreadable subtitle text")
        output.append({"start":round(start,3),"duration":round(span,3),"text":text})
        prior_ms=round(start * 1000) + round(span * 1000)
    return output
