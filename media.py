import asyncio, os, random, subprocess, textwrap, requests
import edge_tts
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps
FONT = os.getenv("FONT_PATH", "font.ttf")

def sh(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode: raise RuntimeError(f"{a[0]} failed: {r.stderr[-400:]}")

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

def tts(text, voice, out):
    asyncio.run(edge_tts.Communicate(text, voice).save(out))

def footage(query, portrait, out):
    key = os.getenv("PEXELS_API_KEY")
    if not key: return False
    try:
        r = requests.get("https://api.pexels.com/videos/search", headers={"Authorization": key}, timeout=30,
                         params={"query": query, "orientation": "portrait" if portrait else "landscape", "per_page": 8}).json()
        random.shuffle(r.get("videos", []))
        for v in r.get("videos", []):
            f = [x for x in v["video_files"] if x["file_type"] == "video/mp4" and 700 <= (x.get("width") or 0) <= 1920]
            if f:
                open(out, "wb").write(requests.get(f[0]["link"], timeout=120).content); return True
    except Exception:
        pass
    return False

def scene(i, sc, ch, W, H, work):
    a = f"{work}/{i}.mp3"; tts(sc["narration"], ch["voice"], a)
    d = dur(a) + 0.25
    clip = f"{work}/{i}_src.mp4"
    src = ["-stream_loop", "-1", "-i", clip] if footage(sc["visual"], H > W, clip) else \
          ["-f", "lavfi", "-i", f"color=c=0x16213e:s={W}x{H}:d={d:.2f}"]
    w = sc["narration"].split(); chunks = [" ".join(w[k:k + 4]) for k in range(0, len(w), 4)]
    step = d / len(chunks)
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30"
    for k, c in enumerate(chunks):  # burned-in captions, 4 words at a time
        tf = f"{work}/{i}_{k}.txt"; open(tf, "w", encoding="utf-8").write(c)
        vf += (f",drawtext=fontfile={FONT}:textfile={tf}:fontsize={H // 28}:fontcolor=white:borderw=4:bordercolor=black"
               f":x=(w-text_w)/2:y=h*0.7:enable='between(t,{k * step:.2f},{(k + 1) * step:.2f})'")
    out = f"{work}/{i}.mp4"
    sh("ffmpeg", "-y", *src, "-i", a, "-t", f"{d:.2f}", "-vf", vf, "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
       "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "44100", out)
    return out

def thumb(src, text, out):
    sh("ffmpeg", "-y", "-ss", "0.5", "-i", src, "-frames:v", "1", out + ".png")
    im = ImageEnhance.Brightness(ImageOps.fit(Image.open(out + ".png").convert("RGB"), (1280, 720))).enhance(0.6)
    d, f = ImageDraw.Draw(im), ImageFont.truetype(FONT, 130)
    lines = textwrap.wrap(text.upper(), 12); y = 360 - len(lines) * 75
    for l in lines:
        d.text((640, y), l, font=f, fill="#FFE600", anchor="ma", stroke_width=8, stroke_fill="black"); y += 150
    im.save(out, "JPEG", quality=92)

def build(ch, pkg, work):
    W, H = (1920, 1080) if ch["fmt"] == "long" else (1080, 1920)
    parts = [scene(i, s, ch, W, H, work) for i, s in enumerate(pkg["scenes"])]
    lst = f"{work}/list.txt"
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    out = f"{work}/final.mp4"
    sh("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out)
    th = f"{work}/thumb.jpg"; thumb(parts[0], pkg["thumb_text"], th)
    return out, th
