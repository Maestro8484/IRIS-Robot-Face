"""
gen_iris.py — Generate strikingBlue iris texture (512x128 PNG)
Texture convention (M4_Eyes polar mapping):
  Row   0  = outer iris edge (limbal ring, dark navy)
  Row 127  = inner iris edge (near pupil, sunflower amber ring)
  Col   0  = 12-o-clock, wrapping clockwise to 511

Design:
  Rows   0– 5: Limbal ring — deep navy/indigo
  Rows   5–28: Outer iris  — vivid royal blue
  Rows  28–88: Main iris   — striking azure/cerulean with dense radial fibers
  Rows  88–108: Sunflower ring — blue→warm amber (central heterochromia)
  Rows 108–127: Pupil border — amber→dark navy transition

Run from this directory:
    python gen_iris.py
Requires: pip install Pillow numpy
"""

import math
import numpy as np
from PIL import Image, ImageFilter

W, H = 512, 128


def iris_texture():
    buf = np.zeros((H, W, 3), dtype=np.float32)

    for y in range(H):
        r = y / (H - 1)  # 0 = outer limbal, 1 = inner (near pupil)

        for x in range(W):
            ang = x / W * 2.0 * math.pi  # 0..2pi

            # --- multi-frequency fiber basis ---
            # 42 major radial spokes (sunflower petal count analogy)
            f1 = math.sin(ang * 42 + r * 3.1)        # primary spokes
            f2 = math.sin(ang * 105 - r * 4.7)       # secondary fibers
            f3 = math.sin(ang * 230 + r * 2.3)       # fine grain
            # slow gentle warp so fibers curve slightly rather than dead-straight
            fw = math.sin(ang * 7  + r * 6.0) * 0.04

            spoke  = (f1 * 0.5 + 0.5) + fw          # 0..1  (dominant)
            fiber  = (f2 * 0.5 + 0.5)               # 0..1
            grain  = (f3 * 0.5 + 0.5)               # 0..1
            combo  = spoke * 0.60 + fiber * 0.30 + grain * 0.10

            # --- zone coloring ---

            if r < 0.045:
                # Limbal ring: deep indigo-navy
                v = combo * 0.12 + 0.88
                R = int(10 * v)
                G = int(24 * v)
                B = int(82 * v)

            elif r < 0.22:
                # Outer iris: bright royal blue, fibers visible
                t = (r - 0.045) / 0.175
                bR, bG, bB = 28 + int(t*14), 88 + int(t*38), 200 + int(t*22)
                dk = (1 - spoke) * 48       # dark valleys
                lt = fiber * 22             # light ridges
                fn = (grain - 0.5) * 10    # fine ±5
                R = int(np.clip(bR - dk*0.25 + lt*0.12 + fn*0.1, 0, 255))
                G = int(np.clip(bG - dk*0.45 + lt*0.38 + fn*0.3, 0, 255))
                B = int(np.clip(bB - dk*0.10 + lt*0.50 + fn*0.5, 0, 255))

            elif r < 0.69:
                # Main striking iris: vivid azure/cerulean — showpiece zone
                t = (r - 0.22) / 0.47
                # colour brightens slightly toward the sunflower ring
                bR = 32 + int(t*22)          # 32..54
                bG = 118 + int(t*58)         # 118..176
                bB = 218 + int(t*18)         # 218..236

                # strong spoke contrast gives the "sunflower radiating" look
                dk = (1 - spoke) * 65        # 0..65
                lt = spoke * 32              # 0..32
                sec = (fiber - 0.5) * 22    # ±11
                fn  = (grain - 0.5) * 12    # ±6

                R = int(np.clip(bR + lt*0.28 - dk*0.22 + sec*0.18 + fn*0.08, 0, 255))
                G = int(np.clip(bG + lt*0.55 - dk*0.40 + sec*0.45 + fn*0.28, 0, 255))
                B = int(np.clip(bB + lt*0.38 - dk*0.08 + sec*0.38 + fn*0.48, 0, 255))

            elif r < 0.845:
                # Sunflower / golden ring (central heterochromia)
                t = (r - 0.69) / 0.155   # 0..1 within band
                # vivid blue → warm amber/golden
                sR, sG, sB = 50,  155, 235   # start (blue)
                eR, eG, eB = 168, 120,  32   # end   (amber-gold)
                bR = int(sR + t*(eR-sR))
                bG = int(sG + t*(eG-sG))
                bB = int(sB + t*(eB-sB))
                # lighter texture in this band — keep amber feel dominant
                tex = (combo - 0.5) * 18 * (1 - t*0.6)
                R = int(np.clip(bR + tex*0.55, 0, 255))
                G = int(np.clip(bG + tex*0.38, 0, 255))
                B = int(np.clip(bB - tex*0.30, 0, 255))

            else:
                # Pupil border: amber → deep navy transition
                t = (r - 0.845) / 0.155
                sR, sG, sB = 168, 120,  32
                eR, eG, eB = 14,   38, 110
                bR = int(sR + t*(eR-sR))
                bG = int(sG + t*(eG-sG))
                bB = int(sB + t*(eB-sB))
                tex = (combo - 0.5) * 12 * (1 - t*0.8)
                R = int(np.clip(bR + tex*0.3, 0, 255))
                G = int(np.clip(bG + tex*0.45, 0, 255))
                B = int(np.clip(bB + tex*0.55, 0, 255))

            buf[y, x] = [R, G, B]

    return buf.astype(np.uint8)


if __name__ == "__main__":
    print("Generating strikingBlue iris texture...")
    data = iris_texture()
    img  = Image.fromarray(data, "RGB")
    # very slight blur smooths pixel staircase without losing fiber detail
    img  = img.filter(ImageFilter.GaussianBlur(0.6))
    img.save("iris.png", format="PNG")
    print(f"Saved iris.png ({img.size[0]}x{img.size[1]})")
