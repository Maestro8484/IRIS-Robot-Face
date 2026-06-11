#!/usr/bin/env python3
"""Resort CHANGELOG.md sections into chronological order."""
import re, sys

CHANGELOG = r'C:\Users\SuperMaster\Documents\PlatformIO\IRIS-Robot-Face\CHANGELOG.md'

with open(CHANGELOG, 'r', encoding='utf-8') as f:
    text = f.read()

# Split on lines starting with "## " (top-level section headers)
split_re = re.compile(r'(?m)^## ')
spans = [m.start() for m in split_re.finditer(text)]

preamble = text[:spans[0]] if spans else text
sections = []
for i, start in enumerate(spans):
    end = spans[i+1] if i+1 < len(spans) else len(text)
    sections.append(text[start:end])

print(f"Preamble: {len(preamble)} chars  |  Sections: {len(sections)}")

def get_key(title):
    t = title.strip()

    # Pre-numbered batch sessions
    if t.startswith('Batch 1A'): return (0, 1)
    if t.startswith('Batch 1B'): return (0, 2)
    if t.startswith('Batch 1C'): return (0, 3)

    # Unlabeled session (2026-05-02, between S45 and S46)
    if t.startswith('Unlabeled session'): return (45, 5)

    # S54-era Pico servo subsections and hardware evolution summary
    if t.startswith('servo-pico Pico W update'): return (55, 3)
    if t.startswith('Pico W servo-pico overhaul'): return (55, 4)
    if t.startswith('Servo Controller Hardware Evolution'): return (58, 5)

    # TS40 / HW / CDX / Codex review cluster (all 2026-05-29, between S72 and S73)
    if t.startswith('TS40-S2'): return (72, 50)
    if t.startswith('TS40-S1'): return (72, 60)
    if t.startswith('HW-004'): return (72, 70)
    if t.startswith('CODEX SECONDARY-CODER SESSION'): return (72, 80)
    if t.startswith('CDX-1'): return (72, 81)
    if t.startswith('CDX-2'): return (72, 82)
    if t.startswith('CDX-3'): return (72, 83)
    if t.startswith('CDX-4'): return (72, 84)
    if t.startswith('CDX-5'): return (72, 85)
    if 'sysmap.json Tracking Backfill' in t: return (72, 86)
    if t.startswith('Claude Review of Codex Session'): return (72, 90)

    # S### with optional sub-label
    m = re.match(r'^S(\d+)', t)
    if m:
        num = int(m.group(1))
        sub = 0
        if re.match(r'^S\d+b\b', t):
            sub = 1
        elif re.match(r'^S\d+c\b', t):
            sub = 2
        elif re.match(r'^S\d+d\b', t):
            sub = 3
        elif ' H-docs' in t:
            sub = 1
        elif ' cont.' in t:
            if 'POST Hardening' in t:
                sub = 1
            elif 'Stale' in t:
                sub = 2
            else:
                sub = 1
        return (num, sub)

    print(f"  WARNING no key: {t[:70]}", file=sys.stderr)
    return (9999, 0)

# Build (key, original_index, content) triples
keyed = []
for i, s in enumerate(sections):
    title = s.split('\n')[0][3:].strip()  # drop leading '## '
    key = get_key(title)
    keyed.append((key, i, s))

# Stable sort: primary = computed key, secondary = original index
keyed.sort(key=lambda x: (x[0], x[1]))

print("\nSorted order:")
for key, orig_i, s in keyed:
    line = f"  {str(key):<12}  {s.split(chr(10))[0][:80]}"
    print(line.encode('ascii', errors='replace').decode('ascii'))

new_text = preamble + ''.join(s for _, _, s in keyed)

with open(CHANGELOG, 'w', encoding='utf-8') as f:
    f.write(new_text)

print(f"\nWrote {len(new_text)} chars to CHANGELOG.md")
