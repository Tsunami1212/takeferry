"""Redraw the bundled synthetic assets with Pillow and FFmpeg (optional)."""
from __future__ import annotations

import array
import math
import random
import subprocess
import tempfile
import wave
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "takeferry" / "data" / "rainy-door"
WIDTH, HEIGHT, FPS = 252, 448, 16


def frame(time, motion):
    im = Image.new("RGB", (WIDTH, HEIGHT))
    d = ImageDraw.Draw(im)
    for y in range(HEIGHT):
        v = int(15 * y / HEIGHT)
        d.line((0, y, WIDTH, y), fill=(13 + v, 29 + v, 41 + v))
    d.polygon([(0, 0), (67, 43), (67, 353), (0, 416)], fill=(27, 51, 61))
    d.polygon([(0, 416), (67, 353), (252, 350), (252, 448), (0, 448)], fill=(42, 58, 63))
    for x in [30, 95, 157, 222]:
        d.line((x, 448, 139 + (x - 139) // 4, 349), fill=(57, 77, 78), width=1)
    d.rectangle((100, 59, 226, 350), fill=(75, 67, 57))
    d.rectangle((107, 67, 219, 350), fill=(37, 47, 46))
    d.rectangle((115, 73, 211, 346), outline=(83, 79, 63), width=2)
    d.rectangle((113, 69, 115, 346), fill=(192, 151, 97))
    d.rectangle((174, 208, 196, 212), fill=(167, 141, 97))
    d.polygon([(100, 350), (217, 347), (241, 358), (91, 364)], fill=(113, 101, 77))
    for i in range(28):
        x = (i * 47 + int(time * 38)) % 65
        y = (i * 93 + int(time * 230)) % 340
        d.line((x, y, x - 3, y + 13), fill=(77, 115, 130))
    turn = min(1.0, max(0.0, (time - 2) * 3))
    walk = min(time, 1.65)
    x = 81 + int(10 * walk)
    y = 145
    d.ellipse((x - 29, 353, x + 35, 367), fill=(25, 42, 48))
    d.polygon([(x - 14, y+97), (x + 20, y+97), (x+17, 356), (x+2, 356), (x, y+137), (x-8,356), (x-21,356)], fill=(22, 37, 47))
    d.polygon([(x-17,y+39),(x+11,y+34),(x+29,y+71),(x+20,y+131),(x-31,y+131),(x-28,y+66)], fill=(81, 105, 111))
    d.line((x+9,y+43,x+25,y+74,x+16,y+102), fill=(122,145,143), width=4)
    d.polygon([(x+4,y+97),(x+28,y+92),(x+32,y+107),(x+8,y+113)], fill=(213,190,146))
    d.line((x+5,y+98,x+20,y+103,x+28,y+94), fill=(146,124,93))
    d.ellipse((x-16,y-1,x+17,y+40), fill=(36,44,49))
    face = x + 10 - round(turn * 15)
    d.ellipse((face-7,y+9,face+8,y+34), fill=(189,152,111))
    nose = face+9-round(turn*20)
    d.polygon([(face,y+12),(nose,y+23),(face,y+25)], fill=(190,153,112))
    d.arc((x-17,y-3,x+18,y+34), 178, 348, fill=(163,150,119), width=2)
    if turn > .5:
        d.point((face-4,y+16), fill=(34,40,43))
    factor = 1 + motion * time / 5
    if motion:
        box_w, box_h = WIDTH / factor, HEIGHT / factor
        left, top = (WIDTH-box_w)*.48, (HEIGHT-box_h)*.46
        im = im.crop((int(left), int(top), int(left+box_w), int(top+box_h))).resize((WIDTH,HEIGHT), Image.Resampling.BICUBIC)
    return im


def sound(path):
    rng = random.Random(27)
    sample_rate = 16000
    samples = array.array("h")
    last = 0.0
    for n in range(5 * sample_rate):
        t = n / sample_rate
        last = .74 * last + .26 * rng.uniform(-1, 1)
        key = max(0.0, t - 2)
        ring = .11 * math.exp(-16*key) * math.sin(key * 2 * math.pi * 1800) if t >= 2 else 0
        samples.append(int(32767*(last*.23 + ring)))
    with wave.open(str(path), "wb") as f:
        f.setparams((1, 2, sample_rate, 0, "NONE", "uncompressed"))
        f.writeframes(samples.tobytes())


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    frame(2.5, 0).crop((50,125,149,250)).resize((198,250)).save(DATA / "identity.png")
    frame(0, 0).crop((147,45,250,195)).resize((206,300)).save(DATA / "lighting.png")
    with tempfile.TemporaryDirectory() as temporary:
        wav = Path(temporary) / "rain.wav"
        sound(wav)
        for name, motion in [("locked", 0), ("push", .24), ("slow-push", .12)]:
            command = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{WIDTH}x{HEIGHT}", "-framerate", str(FPS), "-i", "-",
                       "-i", str(wav), "-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p",
                       "-c:a", "aac", "-b:a", "48k", "-movflags", "+faststart", str(DATA / (name + ".mp4"))]
            with subprocess.Popen(command, stdin=subprocess.PIPE) as proc:
                for i in range(5*FPS):
                    proc.stdin.write(frame(i/FPS, motion).tobytes())
                proc.stdin.close()
                if proc.wait():
                    raise RuntimeError("FFmpeg did not finish writing the example.")
    frames = []
    for i in range(25):
        panel = Image.new("RGB", (390,370), (17,28,35))
        for k, (label, motion) in enumerate([("01 / LOCKED",0), ("02 / PUSH",.24)]):
            x = 8 + k*195
            panel.paste(frame(i/5,motion).resize((180,320)), (x,30))
            ImageDraw.Draw(panel).text((x,9),label,fill=(225,222,204))
        ImageDraw.Draw(panel).text((8,353),"RAIN AT THE DOOR    /    FIXTURE PLAYBACK",fill=(167,188,192))
        frames.append(panel)
    frames[0].save(ROOT / "examples" / "rainy-door" / "preview.gif", save_all=True,
                   append_images=frames[1:], duration=200, loop=0)


if __name__ == "__main__":
    main()
