# IRIS Mouth Expression GIF Catalog

Reference collection for IRIS TFT mouth expressions (ILI9341 320×240, drawn in C++ via Arduino GFX).

Each section covers one expression index. Links are browsable GIF library pages.
Lottie/GIF downloads from LottieFiles are the best option for offline reference.

---

## TFT Expression Index Map

| Index | Name | Color | Notes |
|-------|------|-------|-------|
| 0 | NEUTRAL | Cyan | Near-flat shallow upward curve |
| 1 | HAPPY | Yellow + blush | Wide arc, cheek circles |
| 2 | CURIOUS | Cyan | Asymmetric smirk, flat left / rising right |
| 3 | ANGRY | Red | Downward frown arc |
| 4 | SLEEPY | Purple | Drooping sine + ZZZ glyphs |
| 5 | SURPRISED | White | Thick hollow oval ("O" mouth) |
| 6 | SAD | Blue | Deep frown + vertical quiver lines |
| 7 | CONFUSED | Magenta | Squiggly multi-period sine (~2.7 cycles) |
| 8 | SLEEP/OFF | (black) | Blank screen — used during sleep animation |
| 9 | SILLY | Yellow + pink | Wide grin + protruding tongue, blush circles |

---

## GIF Library Sources

### Robot / Emoji Face Collections
- GIPHY Robot Face: https://giphy.com/explore/robot-face
- GIPHY Animated Emoji: https://giphy.com/explore/animated-emoji
- GIPHY Emoji Face: https://giphy.com/explore/emoji-face
- Tenor Robot Face: https://tenor.com/search/robot-face-gifs
- Tenor Facial Expressions: https://tenor.com/search/facial-expression-gifs

### Expression-Specific
- GIPHY Angry Emoji: https://giphy.com/explore/angry-emoji
- GIPHY Shocked/Surprised Emoji: https://giphy.com/explore/shocked-emoji
- GIPHY Sad Face Emoji: https://giphy.com/explore/sad-face-emoji

### Downloadable Animation Packs (GIF + Lottie JSON)
- LottieFiles Mouth Animations: https://lottiefiles.com/free-animations/mouth
- LottieFiles Expression Animations: https://lottiefiles.com/free-animations/expression
- LottieFiles Face Expression Animations: https://lottiefiles.com/free-animations/face-expression
- IconScout Robot Face Emoji Animations: https://iconscout.com/lottie-animations/robot-face-emoji
- IconScout Robot Emoji Packs (484 packs): https://iconscout.com/lottie-animation-packs/robot-emoji
- Vecteezy Cartoon Mouth Emotion: https://www.vecteezy.com/free-vector/cartoon-mouth-emotion
- Freepik Robot Emotions: https://www.freepik.com/free-photos-vectors/robot-emotions
- Dreamstime Robot Mouth Expressions: https://www.dreamstime.com/illustration/robot-mouth-expressions.html

---

## Per-Expression Reference Notes

### 0 - NEUTRAL
Thin flat-ish line, slight upward curve. Search: "neutral face emoji gif", "expressionless face gif".
Lottie: look for "neutral expression face" on LottieFiles.

### 1 - HAPPY
Big smile, blush cheeks. Search: "happy face emoji gif", "smiley face animated gif".
Lottie: "happy emoji animation", "smile face lottie".

### 2 - CURIOUS
One-sided smirk / raised-corner mouth. Search: "smirk face gif", "curious face animation".
Lottie: "smirk emoji gif".

### 3 - ANGRY
Downward frown (inverted arc). Search: "angry face emoji gif", "mad emoji animated".
GIPHY: https://giphy.com/explore/angry-emoji

### 4 - SLEEPY
Wavy drooping mouth with ZZZ. Search: "sleepy face gif", "tired emoji animated", "zzz face gif".
Lottie: "sleepy emoji animation", "tired face lottie".

### 5 - SURPRISED
Open "O" oval mouth, wide. Search: "surprised face emoji gif", "shocked emoji animated", "gasping face".
GIPHY: https://giphy.com/explore/shocked-emoji

### 6 - SAD
Deep frown with tears. Search: "sad face emoji gif", "crying face animation", "sad mouth gif".
GIPHY: https://giphy.com/explore/sad-face-emoji

### 7 - CONFUSED
Squiggly / zigzag mouth. Search: "confused face emoji gif", "thinking face animated", "wavy mouth gif".

### 8 - SLEEP/OFF
Blank screen — no reference needed.

### 9 - SILLY
Big grin + large protruding tongue + exaggerated blush. Search: "tongue out face gif",
"silly face emoji animated", "sticking out tongue emoji gif", "bleh face animation".
Lottie: "tongue emoji animation", "silly face lottie".

---

## Downloading for Local Preview

To add GIFs to this directory for webUI preview use, download files and name them:
```
0_neutral.gif
1_happy.gif
2_curious.gif
3_angry.gif
4_sleepy.gif
5_surprised.gif
6_sad.gif
7_confused.gif
9_silly.gif
```

If hosted in this directory (exposed via Flask static route or symlink), the WebUI
Emotion Display table can reference them as preview thumbnails.

**LottieFiles download steps:**
1. Open expression page (links above)
2. Click the animation
3. Click "Download" → select "GIF"
4. Save to this directory with the naming convention above

---

## Implementation Notes

TFT expressions are rendered as vector primitives (arcs, beziers, sine waves, filled circles)
via Arduino GFX library at 320×240. The GIFs in this catalog are visual REFERENCE only;
they cannot be played directly on the ILI9341 without a GIF decoder + frame streaming layer.

For future animated expressions on the TFT, the approach would be:
1. Convert GIF frames to RGB565 bitmap arrays (via ImageMagick or Python Pillow)
2. Store in PROGMEM or SPIFFS on Teensy
3. Add a new mouthTFTShowAnimated(idx, frame) function to mouth_tft.cpp
4. Add a frame timer alongside the mouth idle/sleep system

The SILLY expression (index 9) was designed to match a cartoon tongue-out face:
wide grin arc, exaggerated blush circles, large filled pink ellipse for the tongue
with a darker center groove line.
