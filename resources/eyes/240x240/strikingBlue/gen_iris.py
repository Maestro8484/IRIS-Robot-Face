"""
gen_iris.py v2 — strikingBlue iris texture (512x128 PNG)
Redesigned from reference photos of real human blue iris + striking illustrated iris.

Texture convention (M4_Eyes polar mapping):
  Row   0  = outer iris edge (limbal ring)
  Row 127  = inner iris edge (near pupil)
  Col 0-511 = 0-360 degrees around the iris

Design targets (from reference images):
  - Dense radial fiber weave with HIGH contrast: bright white-blue ridges + dark navy crypts
  - Outer zone: muted steel-blue/gray-blue limbal ring
  - Mid-outer: vivid cerulean/azure with complex overlapping fiber texture
  - Inner zone: discrete irregular amber/golden PATCHES (not a smooth ring) - sunflower effect
  - Pupil border: dark navy transition

Run from this directory:
    python gen_iris.py
Requires: pip install Pillow numpy
"""

import math
import numpy as np
from PIL import Image, ImageFilter

W, H = 512, 128


def fiber(ang, r):
    """
    Multi-octave inharmonic fiber basis. Returns 0..1.
    Using inharmonic frequencies so the pattern doesn't look mechanically periodic.
    Includes radial twist (r-dependent phase) so fibers arc slightly.
    """
    # Primary large spokes - 37 is an odd prime, avoids aliasing
    f1 = math.sin(ang * 37  + r * 2.7)
    # Secondary fibers
    f2 = math.sin(ang * 83  - r * 4.1)
    # Fine fiber texture
    f3 = math.sin(ang * 167 + r * 1.9)
    # Very fine grain
    f4 = math.sin(ang * 293 - r * 3.3)
    # Large-scale crypt divisions (~11 major crypts)
    f5 = math.sin(ang * 11  + r * 6.2)
    # Diagonal cross-fiber (makes it look woven not just radial)
    f6 = math.sin(ang * 53  + r * 12.0)

    raw = f1 * 0.32 + f2 * 0.24 + f3 * 0.18 + f4 * 0.12 + f5 * 0.09 + f6 * 0.05
    return raw * 0.5 + 0.5   # 0..1


def amber_spot(ang):
    """
    Discrete irregular amber patches using product of inharmonic sinusoids.
    Produces 7-10 spots per revolution, irregularly spaced (looks natural).
    Returns 0..1, sharply peaked at spot centres.
    """
    # Product of two close-but-not-harmonic frequencies creates beating pattern
    # that produces irregular-seeming spot spacing
    s = math.sin(ang * 9) * math.cos(ang * 7 + 0.9)
    # Only keep positive peaks, sharpen them
    s = max(0.0, s) ** 1.6
    # Second cluster of smaller spots at different positions
    s2 = math.sin(ang * 13 + 1.1) * math.cos(ang * 11 - 0.4)
    s2 = max(0.0, s2) ** 2.2 * 0.55
    return min(1.0, s + s2)


def highlight_spark(ang, r):
    """
    Small bright reflective highlights scattered in mid-iris.
    Returns 0..1, near-zero most of the time.
    """
    h = math.sin(ang * 23 + r * 7) * math.cos(ang * 17 - r * 5)
    return max(0.0, h - 0.75) * 4.0   # only very high peaks survive


def iris_pixel(y, x):
    r   = y / (H - 1)          # 0 = outer limbal, 1 = inner (near pupil)
    ang = x / W * 2.0 * math.pi

    fb  = fiber(ang, r)         # 0..1
    amb = amber_spot(ang)       # 0..1
    spr = highlight_spark(ang, r)  # 0..1

    # ------------------------------------------------------------------
    # Zone 1: Limbal ring (outer edge, rows 0-5)
    # ------------------------------------------------------------------
    if r < 0.042:
        # Dark steel-blue/navy.  Slight fiber variation for texture.
        v = fb * 0.18 + 0.82
        R = int(22  * v)
        G = int(50  * v)
        B = int(112 * v)

    # ------------------------------------------------------------------
    # Zone 2: Outer iris  (rows ~5-22)
    # Muted blue-gray/slate with emerging fiber texture
    # ------------------------------------------------------------------
    elif r < 0.175:
        t = (r - 0.042) / 0.133
        # Base: steel-blue, lightens slightly inward
        bR = int(45  + t * 15)   # 45-60
        bG = int(100 + t * 35)   # 100-135
        bB = int(175 + t * 25)   # 175-200

        # Moderate fiber contrast
        ridge = fb * 55          # bright ridges
        crypt = (1 - fb) * 30   # dark valleys
        fn    = (fiber(ang * 1.7, r) - 0.5) * 18  # cross-fiber

        R = int(np.clip(bR + ridge * 0.22 - crypt * 0.18 + fn * 0.10, 0, 255))
        G = int(np.clip(bG + ridge * 0.45 - crypt * 0.30 + fn * 0.25, 0, 255))
        B = int(np.clip(bB + ridge * 0.50 - crypt * 0.12 + fn * 0.45, 0, 255))

    # ------------------------------------------------------------------
    # Zone 3: Main striking iris  (rows ~22-82)
    # Vivid cerulean/azure — heavy fiber contrast, bright ridge + dark crypt
    # This is the centrepiece. High contrast so fibers read clearly at 240px.
    # ------------------------------------------------------------------
    elif r < 0.645:
        t = (r - 0.175) / 0.470
        # Base cerulean, shifts very slightly warmer inward
        bR = int(32  + t * 22)   # 32-54
        bG = int(112 + t * 55)   # 112-167
        bB = int(215 + t * 15)   # 215-230

        # HIGH contrast fiber: ridges nearly white-blue, crypts deep navy
        ridge  = fb * 80          # 0-80 brighter
        crypt  = (1 - fb) * 72   # 0-72 darker
        fn     = (fiber(ang * 1.9, r * 1.3) - 0.5) * 28   # fine cross-texture ±14
        fn2    = (fiber(ang * 0.43, r * 2.1) - 0.5) * 18  # large slow variation

        # Spark highlights (bright pinpoints in mid-iris like light off fibers)
        spark  = spr * 70

        R = int(np.clip(bR + ridge*0.30 - crypt*0.25 + fn*0.14 + fn2*0.10 + spark*0.35, 0, 255))
        G = int(np.clip(bG + ridge*0.60 - crypt*0.42 + fn*0.32 + fn2*0.22 + spark*0.60, 0, 255))
        B = int(np.clip(bB + ridge*0.55 - crypt*0.10 + fn*0.48 + fn2*0.35 + spark*0.80, 0, 255))

    # ------------------------------------------------------------------
    # Zone 4: Sunflower / amber transition  (rows ~82-108)
    # Discrete amber PATCHES on blue background (not a smooth ring).
    # Amber spots at irregular angular positions; blue fills the gaps.
    # ------------------------------------------------------------------
    elif r < 0.845:
        t = (r - 0.645) / 0.200   # 0..1 within zone

        # Amber patches grow inward: spot_weight peaks mid-zone
        spot_w = amb * (0.5 + t * 0.7)   # amber gets stronger as we go inward
        spot_w = min(1.0, spot_w)

        # Blue fill between spots
        blue_R, blue_G, blue_B = 38, 105, 200
        # Vivid amber/golden
        amb_R,  amb_G,  amb_B  = 225, 148, 22

        # Fiber still visible in this zone but secondary to colour
        fv = (fb - 0.5) * 28

        bR = int(blue_R + spot_w * (amb_R - blue_R))
        bG = int(blue_G + spot_w * (amb_G - blue_G))
        bB = int(blue_B + spot_w * (amb_B - blue_B))

        R = int(np.clip(bR + fv * (1 - spot_w) * 0.35, 0, 255))
        G = int(np.clip(bG + fv * (1 - spot_w) * 0.30, 0, 255))
        B = int(np.clip(bB - fv * spot_w * 0.20,        0, 255))

    # ------------------------------------------------------------------
    # Zone 5: Pupil border  (rows ~108-127)
    # Amber → deep navy transition
    # ------------------------------------------------------------------
    else:
        t = (r - 0.845) / 0.155   # 0..1

        # Amber fades out as we approach pupil
        spot_w = amb * max(0.0, 1 - t * 1.8)

        sR, sG, sB = 220, 140, 20    # amber
        eR, eG, eB = 12,  28,  75    # deep navy

        bR = int(sR + t * (eR - sR))
        bG = int(sG + t * (eG - sG))
        bB = int(sB + t * (eB - sB))

        # Blend amber spots
        bR = int(bR * (1 - spot_w) + 220 * spot_w)
        bG = int(bG * (1 - spot_w) + 140 * spot_w)
        bB = int(bB * (1 - spot_w) + 20  * spot_w)

        fv = (fb - 0.5) * 14 * (1 - t)
        R  = int(np.clip(bR + fv * 0.25, 0, 255))
        G  = int(np.clip(bG + fv * 0.35, 0, 255))
        B  = int(np.clip(bB + fv * 0.45, 0, 255))

    return (R, G, B)


if __name__ == "__main__":
    print("Generating strikingBlue iris texture v2 (512x128)...")
    buf = np.zeros((H, W, 3), dtype=np.uint8)
    for y in range(H):
        for x in range(W):
            buf[y, x] = iris_pixel(y, x)
        if y % 16 == 0:
            print(f"  row {y}/{H}")

    img = Image.fromarray(buf, "RGB")
    # Gentle blur smooths single-pixel staircase without destroying fiber sharpness
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    img.save("iris.png", format="PNG")
    print(f"Saved iris.png ({img.size[0]}x{img.size[1]})")
    print("Next: python ../tablegen.py ..\\..\\..\\..\\.\\src\\eyes\\240x240 config.eye")
