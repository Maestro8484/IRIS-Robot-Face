"""
fix_nordicBlue_iris.py
Hue-shifts hazel/iris.png +140 degrees (brown -> blue) and saves to nordicBlue/iris.png.
Run from the 240x240 directory:
    python fix_nordicBlue_iris.py
Or from anywhere with full paths already set below.
Requires: pip install Pillow numpy
"""

import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
    import colorsys
except ImportError:
    print("Missing deps. Run: pip install Pillow numpy")
    sys.exit(1)

BASE = Path(__file__).parent
SRC  = BASE / "hazel" / "iris.png"
DST  = BASE / "nordicBlue" / "iris.png"
HUE_SHIFT_DEGREES = 140

if not SRC.exists():
    print(f"ERROR: Source not found: {SRC}")
    sys.exit(1)

if not DST.parent.exists():
    print(f"ERROR: Destination directory missing: {DST.parent}")
    sys.exit(1)

print(f"Source:    {SRC}")
print(f"Dest:      {DST}")
print(f"Hue shift: +{HUE_SHIFT_DEGREES} degrees")

img = Image.open(SRC).convert("RGBA")
print(f"Image:     {img.size[0]}x{img.size[1]} {img.mode}")

data = np.array(img, dtype=np.float32)
r  = data[..., 0] / 255.0
g  = data[..., 1] / 255.0
b  = data[..., 2] / 255.0
a  = data[..., 3]

# Convert to HSV, shift hue, convert back
h, s, v = np.vectorize(colorsys.rgb_to_hsv)(r, g, b)
h = (h + HUE_SHIFT_DEGREES / 360.0) % 1.0
nr, ng, nb = np.vectorize(colorsys.hsv_to_rgb)(h, s, v)

out = np.stack([nr * 255, ng * 255, nb * 255, a], axis=-1).astype(np.uint8)
result = Image.fromarray(out, "RGBA")
result.save(DST, format="PNG")

size_kb = DST.stat().st_size / 1024
print(f"Saved:     {DST}  ({size_kb:.1f} KB)")
print()
print("Next steps:")
print("  1. Inspect nordicBlue/iris.png visually (should be blue-toned fiber texture)")
print("  2. Run tablegen:")
print("     python tablegen.py ..\\..\\..\\src\\eyes\\240x240 nordicBlue\\config.eye")
print("  3. Upload via PlatformIO")
